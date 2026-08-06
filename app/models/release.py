"""
Release module: a checklist of standard release gates per Transfer.
Each item has a status/date/responsible so overall Release Progress
can be computed the same way Preparation Progress is.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, IDMixin
from app.config import SimpleStatus, OverallStatus

DEFAULT_RELEASE_ITEMS = [
    "Preparation Complete Review",
    "Final Inspection",
    "Customer / OEM Sign-off",
    "Logistics & Shipment Readiness",
    "Final Release Approval",
]


class ReleaseChecklist(Base, IDMixin, TimestampMixin):
    __tablename__ = "release_checklists"

    transfer_id = Column(Integer, ForeignKey("transfers.id"), nullable=False, unique=True)
    released = Column(String(8), default="No")   # Yes/No flag once fully released
    release_date = Column(Date)
    released_by = Column(String(128))
    comments = Column(Text)

    transfer = relationship("Transfer", back_populates="release")
    items = relationship(
        "ReleaseItem", back_populates="checklist",
        cascade="all, delete-orphan", order_by="ReleaseItem.id",
    )

    @property
    def overall_status(self) -> str:
        if not self.items:
            return OverallStatus.NOT_STARTED.value
        statuses = [i.status for i in self.items]
        if all(s == SimpleStatus.APPROVED.value for s in statuses):
            return OverallStatus.COMPLETED.value
        if all(s == SimpleStatus.NOT_STARTED.value for s in statuses):
            return OverallStatus.NOT_STARTED.value
        return OverallStatus.ONGOING.value

    @property
    def progress_percent(self) -> float:
        if not self.items:
            return 0.0
        done = sum(1 for i in self.items if i.status == SimpleStatus.APPROVED.value)
        return round(done / len(self.items) * 100, 1)


class ReleaseItem(Base, IDMixin, TimestampMixin):
    __tablename__ = "release_items"

    checklist_id = Column(Integer, ForeignKey("release_checklists.id"), nullable=False)
    name = Column(String(256), nullable=False)
    status = Column(String(32), default=SimpleStatus.NOT_STARTED.value)
    responsible = Column(String(128))
    due_date = Column(Date)
    completion_date = Column(Date)
    comments = Column(Text)

    checklist = relationship("ReleaseChecklist", back_populates="items")
