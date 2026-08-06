"""
PTT Approval: Step 1 (internal) lives on PTTApproval itself,
Step 2 (OEM) is a one-to-many list of OEMApproval rows.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, IDMixin
from app.config import SimpleStatus, OEMStatus, OverallStatus


class PTTApproval(Base, IDMixin, TimestampMixin):
    __tablename__ = "ptt_approvals"

    transfer_id = Column(Integer, ForeignKey("transfers.id"), nullable=False, unique=True)

    # --- Step 1: Internal Approval ---
    internal_status = Column(String(32), default=SimpleStatus.NOT_STARTED.value)
    internal_responsible = Column(String(128))
    internal_due_date = Column(Date)
    internal_approval_date = Column(Date)
    internal_comments = Column(Text)

    transfer = relationship("Transfer", back_populates="ptt_approval")
    oem_approvals = relationship(
        "OEMApproval", back_populates="ptt_approval",
        cascade="all, delete-orphan", order_by="OEMApproval.oem_name",
    )

    @property
    def overall_status(self) -> str:
        """Roll up internal + all OEM approvals into one status."""
        statuses = [self.internal_status] + [o.status for o in self.oem_approvals]
        if not statuses:
            return OverallStatus.NOT_STARTED.value
        if any(s == OEMStatus.REJECTED.value for s in statuses):
            return OverallStatus.DELAYED.value
        if all(s in (SimpleStatus.APPROVED.value, OEMStatus.APPROVED.value) for s in statuses):
            return OverallStatus.COMPLETED.value
        if all(s == SimpleStatus.NOT_STARTED.value or s == OEMStatus.NOT_STARTED.value
               for s in statuses):
            return OverallStatus.NOT_STARTED.value
        return OverallStatus.ONGOING.value

    @property
    def progress_percent(self) -> float:
        steps = [self.internal_status] + [o.status for o in self.oem_approvals]
        if not steps:
            return 0.0
        done = sum(1 for s in steps if s in (SimpleStatus.APPROVED.value, OEMStatus.APPROVED.value))
        return round(done / len(steps) * 100, 1)


class OEMApproval(Base, IDMixin, TimestampMixin):
    __tablename__ = "oem_approvals"

    ptt_approval_id = Column(Integer, ForeignKey("ptt_approvals.id"), nullable=False)
    oem_name = Column(String(128), nullable=False)
    status = Column(String(32), default=OEMStatus.NOT_STARTED.value)
    due_date = Column(Date)
    approval_date = Column(Date)
    comments = Column(Text)

    ptt_approval = relationship("PTTApproval", back_populates="oem_approvals")
