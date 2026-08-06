"""
Business logic for the Preparation module (sections 3.1 -> 3.7 of the spec).
Each sub-record is created lazily (get-or-create) so the UI never has to
worry about None relationships.
"""
from __future__ import annotations

from app.database import get_session
from app.models.transfer import Transfer, Tool, PartNumber
from app.models.ptt_approval import PTTApproval, OEMApproval
from app.models.safety_stock import SafetyStock
from app.models.raw_material import RawMaterial
from app.models.pre_check import PreCheck
from app.models.e2e_followup import E2EFollowUp
from app.models.applicator import Applicator, CounterPart
from app.models.training import Training
from app.config import Activity, OverallStatus
from app.utils.calendar_week import add_weeks_to_cw


class PreparationController:
    def __init__(self):
        self.session = get_session()

    # ------------------------------------------------------------------
    # Get-or-create helpers
    # ------------------------------------------------------------------
    def get_ptt(self, transfer: Transfer) -> PTTApproval:
        if transfer.ptt_approval is None:
            transfer.ptt_approval = PTTApproval()
            self.session.commit()
        return transfer.ptt_approval

    def add_oem(self, ptt: PTTApproval, oem_name: str) -> OEMApproval:
        oem = OEMApproval(oem_name=oem_name)
        ptt.oem_approvals.append(oem)
        self.session.commit()
        return oem

    def remove_oem(self, oem_id: int) -> None:
        oem = self.session.get(OEMApproval, oem_id)
        if oem:
            self.session.delete(oem)
            self.session.commit()

    def get_safety_stock(self, tool: Tool) -> SafetyStock:
        if tool.safety_stock is None:
            tool.safety_stock = SafetyStock()
            self.session.commit()
        return tool.safety_stock

    def get_raw_material(self, part_number: PartNumber) -> RawMaterial:
        if part_number.raw_material is None:
            part_number.raw_material = RawMaterial()
            self.session.commit()
        return part_number.raw_material

    def get_pre_check(self, part_number: PartNumber) -> PreCheck:
        if part_number.pre_check is None:
            part_number.pre_check = PreCheck()
            self.session.commit()
        return part_number.pre_check

    def get_e2e(self, transfer: Transfer) -> E2EFollowUp:
        if transfer.e2e_followup is None:
            transfer.e2e_followup = E2EFollowUp()
            self.session.commit()
        return transfer.e2e_followup

    def get_applicator(self, part_number: PartNumber) -> Applicator:
        if part_number.applicator is None:
            part_number.applicator = Applicator()
            self.session.commit()
        return part_number.applicator

    def get_counter_part(self, part_number: PartNumber) -> CounterPart:
        if part_number.counter_part is None:
            part_number.counter_part = CounterPart()
            self.session.commit()
        return part_number.counter_part

    def get_training(self, tool: Tool) -> Training:
        if tool.training is None:
            tool.training = Training()
            self.session.commit()
        return tool.training

    def uses_applicator(self, transfer: Transfer) -> bool:
        return transfer.activity == Activity.STAMPING.value

    # ------------------------------------------------------------------
    # Generic save (used by dynamic forms: assign attrs then commit)
    # ------------------------------------------------------------------
    def save(self, obj) -> None:
        self.session.add(obj)
        self.session.commit()

    def compute_finish_cw(self, safety_stock: SafetyStock) -> str:
        if not safety_stock.start_calendar_week or not safety_stock.number_of_weeks:
            return ""
        return add_weeks_to_cw(safety_stock.start_calendar_week, safety_stock.number_of_weeks)

    # ------------------------------------------------------------------
    # Preparation progress roll-up for one Transfer (used by Dashboard too)
    # ------------------------------------------------------------------
    def preparation_progress(self, transfer: Transfer) -> float:
        scores = []

        if transfer.ptt_approval:
            scores.append(transfer.ptt_approval.progress_percent)
        if transfer.e2e_followup:
            scores.append(transfer.e2e_followup.progress_percent)

        for tool in transfer.tools:
            if tool.safety_stock and tool.safety_stock.required:
                scores.append(tool.safety_stock.progress_percent)
            if tool.training and tool.training.required:
                scores.append(100.0 if tool.training.overall_status == OverallStatus.COMPLETED.value else
                               (50.0 if tool.training.overall_status == OverallStatus.ONGOING.value else 0.0))
            for pn in tool.part_numbers:
                if pn.raw_material:
                    scores.append(pn.raw_material.progress_percent)
                if pn.pre_check:
                    scores.append(100.0 if pn.pre_check.overall_status == OverallStatus.COMPLETED.value else
                                   (50.0 if pn.pre_check.overall_status == OverallStatus.ONGOING.value else 0.0))

        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 1)

    def preparation_status(self, transfer: Transfer) -> str:
        progress = self.preparation_progress(transfer)
        if progress >= 100:
            return OverallStatus.COMPLETED.value
        if progress <= 0:
            return OverallStatus.NOT_STARTED.value
        # Overdue check: any due date in the past with not-approved status -> delayed
        if self.has_overdue_items(transfer):
            return OverallStatus.DELAYED.value
        return OverallStatus.ONGOING.value

    def has_overdue_items(self, transfer: Transfer) -> bool:
        import datetime as dt
        today = dt.date.today()
        ptt = transfer.ptt_approval
        if ptt:
            if ptt.internal_due_date and ptt.internal_due_date < today and \
                    ptt.internal_status != "Approved":
                return True
            for oem in ptt.oem_approvals:
                if oem.due_date and oem.due_date < today and oem.status not in ("Approved",):
                    return True
        for tool in transfer.tools:
            for pn in tool.part_numbers:
                if pn.raw_material and pn.raw_material.due_date and \
                        pn.raw_material.due_date < today and pn.raw_material.overall_status != "Completed":
                    return True
                if pn.pre_check and pn.pre_check.due_date and \
                        pn.pre_check.due_date < today and pn.pre_check.overall_status not in ("Completed",):
                    return True
        return False
