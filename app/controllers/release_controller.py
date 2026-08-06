"""
Business logic for the Release module: manage the per-transfer checklist
and compute Release Progress (also consumed by the Dashboard).
"""
from __future__ import annotations

import datetime as dt

from app.database import get_session
from app.models.transfer import Transfer
from app.models.release import ReleaseChecklist, ReleaseItem, DEFAULT_RELEASE_ITEMS
from app.config import SimpleStatus, OverallStatus


class ReleaseController:
    def __init__(self):
        self.session = get_session()

    def get_checklist(self, transfer: Transfer) -> ReleaseChecklist:
        if transfer.release is None:
            checklist = ReleaseChecklist()
            for name in DEFAULT_RELEASE_ITEMS:
                checklist.items.append(ReleaseItem(name=name))
            transfer.release = checklist
            self.session.commit()
        return transfer.release

    def update_item(self, item: ReleaseItem, **fields) -> None:
        for key, value in fields.items():
            setattr(item, key, value)
        if item.status == SimpleStatus.APPROVED.value and not item.completion_date:
            item.completion_date = dt.date.today()
        self.session.commit()

    def add_custom_item(self, checklist: ReleaseChecklist, name: str) -> ReleaseItem:
        item = ReleaseItem(name=name)
        checklist.items.append(item)
        self.session.commit()
        return item

    def remove_item(self, item_id: int) -> None:
        item = self.session.get(ReleaseItem, item_id)
        if item:
            self.session.delete(item)
            self.session.commit()

    def finalize_release(self, checklist: ReleaseChecklist, released_by: str, comments: str = "") -> None:
        checklist.released = "Yes"
        checklist.release_date = dt.date.today()
        checklist.released_by = released_by
        checklist.comments = comments
        self.session.commit()

    def release_progress(self, transfer: Transfer) -> float:
        checklist = self.get_checklist(transfer)
        return checklist.progress_percent

    def release_status(self, transfer: Transfer) -> str:
        checklist = self.get_checklist(transfer)
        if checklist.released == "Yes":
            return OverallStatus.COMPLETED.value
        return checklist.overall_status
