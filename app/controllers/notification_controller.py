"""
Scans the database for overdue activities and upcoming transfer dates,
creating Notification rows (deduplicated) that feed the Notification Center.
"""
from __future__ import annotations

import datetime as dt

from app.database import get_session
from app.models.transfer import Transfer
from app.models.collab import Notification
from app.config import SimpleStatus


class NotificationController:
    def __init__(self):
        self.session = get_session()

    def scan_and_generate(self) -> int:
        """Run all overdue/upcoming checks; returns number of new notifications."""
        created = 0
        today = dt.date.today()
        transfers = self.session.query(Transfer).all()

        for transfer in transfers:
            # Upcoming transfer date (<=7 days) reminder
            days_left = (transfer.planned_transfer_date - today).days
            if 0 <= days_left <= 7:
                msg = f"Transfer {transfer.trf_number} is planned in {days_left} day(s)."
                created += self._create_if_new("transfer", transfer.id, msg, "warning")
            elif days_left < 0 and (not transfer.release or transfer.release.released != "Yes"):
                msg = f"Transfer {transfer.trf_number} passed its planned date and is not released."
                created += self._create_if_new("transfer", transfer.id, msg, "critical")

            # PTT overdue
            ptt = transfer.ptt_approval
            if ptt:
                if ptt.internal_due_date and ptt.internal_due_date < today and \
                        ptt.internal_status != SimpleStatus.APPROVED.value:
                    msg = f"PTT Internal Approval overdue for {transfer.trf_number}."
                    created += self._create_if_new("transfer", transfer.id, msg, "critical")
                for oem in ptt.oem_approvals:
                    if oem.due_date and oem.due_date < today and oem.status not in ("Approved",):
                        msg = f"OEM Approval ({oem.oem_name}) overdue for {transfer.trf_number}."
                        created += self._create_if_new("transfer", transfer.id, msg, "critical")

            # Raw material / pre-check overdue
            for tool in transfer.tools:
                for pn in tool.part_numbers:
                    if pn.raw_material and pn.raw_material.due_date and \
                            pn.raw_material.due_date < today and pn.raw_material.overall_status != "Completed":
                        msg = (f"Raw Material follow-up overdue for part {pn.part_number} "
                               f"({transfer.trf_number}).")
                        created += self._create_if_new("part_number", pn.id, msg, "warning")
                    if pn.pre_check and pn.pre_check.due_date and \
                            pn.pre_check.due_date < today and pn.pre_check.overall_status not in ("Completed",):
                        msg = f"Pre-check overdue for part {pn.part_number} ({transfer.trf_number})."
                        created += self._create_if_new("part_number", pn.id, msg, "warning")

        return created

    def _create_if_new(self, entity_type: str, entity_id: int, message: str, level: str) -> int:
        existing = self.session.query(Notification).filter_by(
            entity_type=entity_type, entity_id=entity_id, message=message).first()
        if existing:
            return 0
        note = Notification(entity_type=entity_type, entity_id=entity_id,
                             message=message, level=level)
        self.session.add(note)
        self.session.commit()
        return 1

    def list_unread(self):
        return self.session.query(Notification).filter_by(is_read=0).order_by(
            Notification.created_at.desc()).all()

    def list_all(self, limit: int = 100):
        return self.session.query(Notification).order_by(
            Notification.created_at.desc()).limit(limit).all()

    def mark_read(self, notification_id: int) -> None:
        note = self.session.get(Notification, notification_id)
        if note:
            note.is_read = 1
            self.session.commit()

    def mark_all_read(self) -> None:
        for note in self.list_unread():
            note.is_read = 1
        self.session.commit()

    def clear_all(self) -> None:
        self.session.query(Notification).delete()
        self.session.commit()
