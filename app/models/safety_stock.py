from __future__ import annotations

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, IDMixin
from app.config import OverallStatus


class SafetyStock(Base, IDMixin, TimestampMixin):
    __tablename__ = "safety_stocks"

    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False, unique=True)

    required = Column(Boolean, default=False, nullable=False)
    start_calendar_week = Column(String(16))   # e.g. "2026-W05"
    number_of_weeks = Column(Integer, default=0)
    required_quantity = Column(Integer, default=0)
    current_built_quantity = Column(Integer, default=0)
    finish_calendar_week = Column(String(16))

    tool = relationship("Tool", back_populates="safety_stock")

    @property
    def progress_percent(self) -> float:
        if not self.required or not self.required_quantity:
            return 0.0
        pct = (self.current_built_quantity or 0) / self.required_quantity * 100
        return round(min(pct, 100.0), 1)

    @property
    def status(self) -> str:
        if not self.required:
            return OverallStatus.NOT_STARTED.value
        pct = self.progress_percent
        if pct >= 100:
            return OverallStatus.COMPLETED.value
        if pct <= 0:
            return OverallStatus.NOT_STARTED.value
        return OverallStatus.ONGOING.value
