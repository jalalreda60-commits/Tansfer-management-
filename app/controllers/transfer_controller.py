"""
Business logic for the Transfers module: CRUD on Transfer/Tool/PartNumber,
search & filtering, duplication, and the generic comment/attachment/history
helpers reused by every other controller.
"""
from __future__ import annotations

import datetime as dt
import shutil
import os

from sqlalchemy import or_

from app.database import get_session
from app.models.transfer import Transfer, Tool, PartNumber
from app.models.collab import Attachment, Comment, HistoryLog
from app.models.ptt_approval import PTTApproval
from app.models.e2e_followup import E2EFollowUp
from app.models.release import ReleaseChecklist, ReleaseItem, DEFAULT_RELEASE_ITEMS
from app.config import ATTACHMENTS_DIR


class TransferController:
    def __init__(self):
        self.session = get_session()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def list_transfers(self, search: str = "", filters: dict | None = None):
        query = self.session.query(Transfer)
        if search:
            like = f"%{search}%"
            query = query.filter(or_(
                Transfer.trf_number.ilike(like),
                Transfer.technology.ilike(like),
                Transfer.sender_location.ilike(like),
                Transfer.receiver_location.ilike(like),
            ))
        filters = filters or {}
        if filters.get("transfer_type"):
            query = query.filter(Transfer.transfer_type == filters["transfer_type"])
        if filters.get("activity"):
            query = query.filter(Transfer.activity == filters["activity"])
        if filters.get("technology"):
            query = query.filter(Transfer.technology == filters["technology"])
        if filters.get("sender_location"):
            query = query.filter(Transfer.sender_location == filters["sender_location"])
        if filters.get("receiver_location"):
            query = query.filter(Transfer.receiver_location == filters["receiver_location"])
        return query.order_by(Transfer.planned_transfer_date.asc()).all()

    def get_transfer(self, transfer_id: int) -> Transfer | None:
        return self.session.get(Transfer, transfer_id)

    def create_transfer(self, data: dict, tools: list[dict]) -> Transfer:
        transfer = Transfer(
            trf_number=data["trf_number"],
            planned_transfer_date=data["planned_transfer_date"],
            transfer_type=data["transfer_type"],
            activity=data["activity"],
            sender_location=data["sender_location"],
            receiver_location=data["receiver_location"],
            technology=data["technology"],
        )
        for tool_data in tools:
            tool = Tool(tool_number=tool_data["tool_number"])
            for pn in tool_data.get("part_numbers", []):
                tool.part_numbers.append(PartNumber(part_number=pn))
            transfer.tools.append(tool)

        # Create default related sub-records so every screen has something
        # to display without extra null-checks.
        transfer.ptt_approval = PTTApproval()
        transfer.e2e_followup = E2EFollowUp()
        checklist = ReleaseChecklist()
        for name in DEFAULT_RELEASE_ITEMS:
            checklist.items.append(ReleaseItem(name=name))
        transfer.release = checklist

        self.session.add(transfer)
        self.session.commit()
        self.log_history("transfer", transfer.id, "Created",
                          f"Transfer {transfer.trf_number} created.")
        return transfer

    def update_transfer(self, transfer_id: int, data: dict) -> Transfer:
        transfer = self.get_transfer(transfer_id)
        for field in ("trf_number", "planned_transfer_date", "transfer_type",
                      "activity", "sender_location", "receiver_location", "technology"):
            if field in data:
                setattr(transfer, field, data[field])
        self.session.commit()
        self.log_history("transfer", transfer.id, "Updated", "Transfer details updated.")
        return transfer

    def delete_transfer(self, transfer_id: int) -> None:
        transfer = self.get_transfer(transfer_id)
        if transfer:
            trf_number = transfer.trf_number
            self.session.delete(transfer)
            self.session.commit()
            self.log_history("transfer", transfer_id, "Deleted", f"Transfer {trf_number} deleted.")

    def duplicate_transfer(self, transfer_id: int) -> Transfer:
        original = self.get_transfer(transfer_id)
        new_number = f"{original.trf_number}-COPY"
        suffix = 1
        existing_numbers = {t.trf_number for t in self.session.query(Transfer.trf_number).all()}
        while new_number in existing_numbers:
            suffix += 1
            new_number = f"{original.trf_number}-COPY{suffix}"

        tools_payload = [
            {"tool_number": t.tool_number,
             "part_numbers": [p.part_number for p in t.part_numbers]}
            for t in original.tools
        ]
        data = {
            "trf_number": new_number,
            "planned_transfer_date": original.planned_transfer_date,
            "transfer_type": original.transfer_type,
            "activity": original.activity,
            "sender_location": original.sender_location,
            "receiver_location": original.receiver_location,
            "technology": original.technology,
        }
        new_transfer = self.create_transfer(data, tools_payload)
        self.log_history("transfer", new_transfer.id, "Duplicated",
                          f"Duplicated from {original.trf_number}.")
        return new_transfer

    # ------------------------------------------------------------------
    # Tools / Part Numbers (edit existing transfer's structure)
    # ------------------------------------------------------------------
    def add_tool(self, transfer_id: int, tool_number: str, part_numbers: list[str]) -> Tool:
        transfer = self.get_transfer(transfer_id)
        tool = Tool(tool_number=tool_number)
        for pn in part_numbers:
            tool.part_numbers.append(PartNumber(part_number=pn))
        transfer.tools.append(tool)
        self.session.commit()
        self.log_history("transfer", transfer_id, "Updated", f"Tool {tool_number} added.")
        return tool

    def remove_tool(self, tool_id: int) -> None:
        tool = self.session.get(Tool, tool_id)
        if tool:
            transfer_id = tool.transfer_id
            self.session.delete(tool)
            self.session.commit()
            self.log_history("transfer", transfer_id, "Updated", "Tool removed.")

    def add_part_number(self, tool_id: int, part_number: str) -> PartNumber:
        tool = self.session.get(Tool, tool_id)
        pn = PartNumber(part_number=part_number)
        tool.part_numbers.append(pn)
        self.session.commit()
        return pn

    def remove_part_number(self, part_number_id: int) -> None:
        pn = self.session.get(PartNumber, part_number_id)
        if pn:
            self.session.delete(pn)
            self.session.commit()

    # ------------------------------------------------------------------
    # Attachments / Comments / History (generic, entity_type driven)
    # ------------------------------------------------------------------
    def add_attachment(self, entity_type: str, entity_id: int, source_path: str) -> Attachment:
        os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
        filename = os.path.basename(source_path)
        stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
        dest_name = f"{entity_type}_{entity_id}_{stamp}_{filename}"
        dest_path = os.path.join(ATTACHMENTS_DIR, dest_name)
        shutil.copy2(source_path, dest_path)

        attachment = Attachment(entity_type=entity_type, entity_id=entity_id,
                                 file_name=filename, file_path=dest_path)
        self.session.add(attachment)
        self.session.commit()
        self.log_history(entity_type, entity_id, "Attachment Added", filename)
        return attachment

    def list_attachments(self, entity_type: str, entity_id: int):
        return self.session.query(Attachment).filter_by(
            entity_type=entity_type, entity_id=entity_id).order_by(Attachment.uploaded_at.desc()).all()

    def delete_attachment(self, attachment_id: int) -> None:
        att = self.session.get(Attachment, attachment_id)
        if att:
            try:
                if os.path.exists(att.file_path):
                    os.remove(att.file_path)
            except OSError:
                pass
            self.session.delete(att)
            self.session.commit()

    def add_comment(self, entity_type: str, entity_id: int, text: str, author: str = "user") -> Comment:
        comment = Comment(entity_type=entity_type, entity_id=entity_id, text=text, author=author)
        self.session.add(comment)
        self.session.commit()
        self.log_history(entity_type, entity_id, "Comment Added", text[:120])
        return comment

    def list_comments(self, entity_type: str, entity_id: int):
        return self.session.query(Comment).filter_by(
            entity_type=entity_type, entity_id=entity_id).order_by(Comment.created_at.desc()).all()

    def log_history(self, entity_type: str, entity_id: int, action: str, details: str = "") -> None:
        entry = HistoryLog(entity_type=entity_type, entity_id=entity_id, action=action, details=details)
        self.session.add(entry)
        self.session.commit()

    def list_history(self, entity_type: str, entity_id: int):
        return self.session.query(HistoryLog).filter_by(
            entity_type=entity_type, entity_id=entity_id).order_by(HistoryLog.timestamp.desc()).all()

    # ------------------------------------------------------------------
    # Distinct values for filter dropdowns
    # ------------------------------------------------------------------
    def distinct_values(self, column) -> list[str]:
        rows = self.session.query(column).distinct().all()
        return sorted({r[0] for r in rows if r[0]})
