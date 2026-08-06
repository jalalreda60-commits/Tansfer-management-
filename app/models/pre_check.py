from __future__ import annotations

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, IDMixin
from app.config import NAOngoingReceived, PrecheckFeedback, OverallStatus


class PreCheck(Base, IDMixin, TimestampMixin):
    __tablename__ = "pre_checks"

    part_number_id = Column(Integer, ForeignKey("part_numbers.id"), nullable=False, unique=True)

    pe_responsible = Column(String(128))
    samples_before = Column(String(16), default=NAOngoingReceived.NA.value)
    pe_requirement = Column(String(16), default=NAOngoingReceived.NA.value)
    measurement_report = Column(String(16), default=NAOngoingReceived.NA.value)
    feedback = Column(String(16), default=PrecheckFeedback.NA.value)
    due_date = Column(Date)
    actions = Column(Text)
    comments = Column(Text)

    part_number = relationship("PartNumber", back_populates="pre_check")

    @property
    def overall_status(self) -> str:
        if self.feedback == PrecheckFeedback.REJECTED.value:
            return OverallStatus.DELAYED.value
        if self.feedback == PrecheckFeedback.ACCEPTED.value:
            return OverallStatus.COMPLETED.value
        if self.feedback == PrecheckFeedback.ONGOING.value:
            return OverallStatus.ONGOING.value
        return OverallStatus.NOT_STARTED.value
