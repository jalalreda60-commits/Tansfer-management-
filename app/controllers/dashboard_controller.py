"""
Aggregates data across all Transfers for the Dashboard: KPI cards,
chart datasets and the recent-activity / due-date / delayed tables.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter

from app.database import get_session
from app.models.transfer import Transfer
from app.models.collab import HistoryLog
from app.config import OverallStatus
from app.controllers.preparation_controller import PreparationController
from app.controllers.release_controller import ReleaseController


class DashboardController:
    def __init__(self):
        self.session = get_session()
        self.prep = PreparationController()
        self.rel = ReleaseController()

    def all_transfers(self):
        return self.session.query(Transfer).all()

    # ------------------------------------------------------------------
    # KPI cards
    # ------------------------------------------------------------------
    def kpis(self) -> dict:
        transfers = self.all_transfers()
        total = len(transfers)

        prep_scores = [self.prep.preparation_progress(t) for t in transfers] or [0]
        rel_scores = [self.rel.release_progress(t) for t in transfers] or [0]

        delayed = sum(1 for t in transfers if self.prep.preparation_status(t) == OverallStatus.DELAYED.value
                      or self.rel.release_status(t) == OverallStatus.DELAYED.value)
        completed = sum(1 for t in transfers if self.rel.release_status(t) == OverallStatus.COMPLETED.value)

        upcoming = sum(1 for t in transfers if 0 <= t.days_remaining <= 14)

        open_actions = 0
        for t in transfers:
            e2e = t.e2e_followup
            if e2e and e2e.pcn_action_list:
                open_actions += len([l for l in e2e.pcn_action_list.splitlines() if l.strip()])
            if e2e and e2e.sop_open_actions:
                open_actions += len([l for l in e2e.sop_open_actions.splitlines() if l.strip()])

        return {
            "total_transfers": total,
            "preparation_progress": round(sum(prep_scores) / len(prep_scores), 1),
            "release_progress": round(sum(rel_scores) / len(rel_scores), 1),
            "delayed_activities": delayed,
            "upcoming_transfers": upcoming,
            "open_actions": open_actions,
            "completed_transfers": completed,
        }

    # ------------------------------------------------------------------
    # Distribution charts
    # ------------------------------------------------------------------
    def by_technology(self) -> dict:
        return dict(Counter(t.technology for t in self.all_transfers()))

    def by_sender_location(self) -> dict:
        return dict(Counter(t.sender_location for t in self.all_transfers()))

    def by_receiver_location(self) -> dict:
        return dict(Counter(t.receiver_location for t in self.all_transfers()))

    def by_transfer_type(self) -> dict:
        return dict(Counter(t.transfer_type for t in self.all_transfers()))

    # ------------------------------------------------------------------
    # Progress charts
    # ------------------------------------------------------------------
    def progress_by_transfer(self) -> list[tuple[str, float]]:
        result = []
        for t in self.all_transfers():
            overall = round((self.prep.preparation_progress(t) + self.rel.release_progress(t)) / 2, 1)
            result.append((t.trf_number, overall))
        return sorted(result, key=lambda x: x[0])

    def progress_by_phase(self) -> dict:
        transfers = self.all_transfers()
        if not transfers:
            return {"Preparation": 0, "Release": 0}
        prep_avg = round(sum(self.prep.preparation_progress(t) for t in transfers) / len(transfers), 1)
        rel_avg = round(sum(self.rel.release_progress(t) for t in transfers) / len(transfers), 1)
        return {"Preparation": prep_avg, "Release": rel_avg}

    def weekly_progress(self, weeks: int = 8) -> list[tuple[str, int]]:
        """Number of completed history actions per ISO week, last N weeks."""
        today = dt.date.today()
        buckets = []
        for i in range(weeks - 1, -1, -1):
            week_date = today - dt.timedelta(weeks=i)
            iso = week_date.isocalendar()
            buckets.append(f"{iso[0]}-W{iso[1]:02d}")

        counts = Counter()
        history_entries = self.session.query(HistoryLog).all()
        for entry in history_entries:
            iso = entry.timestamp.isocalendar()
            key = f"{iso[0]}-W{iso[1]:02d}"
            if key in buckets:
                counts[key] += 1

        return [(b, counts.get(b, 0)) for b in buckets]

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------
    def recent_activities(self, limit: int = 10):
        return self.session.query(HistoryLog).order_by(HistoryLog.timestamp.desc()).limit(limit).all()

    def upcoming_due_dates(self, limit: int = 10):
        today = dt.date.today()
        transfers = [t for t in self.all_transfers() if t.days_remaining >= 0]
        transfers.sort(key=lambda t: t.days_remaining)
        return transfers[:limit]

    def delayed_tasks(self, limit: int = 15):
        rows = []
        for t in self.all_transfers():
            if self.prep.preparation_status(t) == OverallStatus.DELAYED.value:
                rows.append((t.trf_number, "Preparation", self.prep.preparation_status(t)))
            if self.rel.release_status(t) == OverallStatus.DELAYED.value:
                rows.append((t.trf_number, "Release", self.rel.release_status(t)))
        return rows[:limit]
