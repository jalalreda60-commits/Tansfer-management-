from __future__ import annotations

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, IDMixin
from app.config import TrainingStatus, OverallStatus


class Training(Base, IDMixin, TimestampMixin):
    __tablename__ = "trainings"

    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False, unique=True)

    required = Column(Boolean, default=False, nullable=False)
    planned_calendar_week = Column(String(16))
    duration = Column(String(64))
    invitation_sent = Column(Boolean, default=False)
    status = Column(String(32), default=TrainingStatus.NOT_STARTED.value)
    comments = Column(Text)

    tool = relationship("Tool", back_populates="training")

    @property
    def overall_status(self) -> str:
        if not self.required:
            return OverallStatus.NOT_STARTED.value
        mapping = {
            TrainingStatus.NOT_STARTED.value: OverallStatus.NOT_STARTED.value,
            TrainingStatus.ONGOING.value: OverallStatus.ONGOING.value,
            TrainingStatus.DONE.value: OverallStatus.COMPLETED.value,
        }
        return mapping.get(self.status, OverallStatus.NOT_STARTED.value)
