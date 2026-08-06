from __future__ import annotations

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, IDMixin
from app.config import NAOngoingDone, OverallStatus


class RawMaterial(Base, IDMixin, TimestampMixin):
    __tablename__ = "raw_materials"

    part_number_id = Column(Integer, ForeignKey("part_numbers.id"), nullable=False, unique=True)

    subgroup = Column(String(16), default=NAOngoingDone.NA.value)
    setup = Column(String(16), default=NAOngoingDone.NA.value)
    rm_order = Column(String(16), default=NAOngoingDone.NA.value)
    rm_availability = Column(String(16), default=NAOngoingDone.NA.value)
    due_date = Column(Date)
    comment = Column(Text)

    part_number = relationship("PartNumber", back_populates="raw_material")

    @property
    def fields(self):
        return [self.subgroup, self.setup, self.rm_order, self.rm_availability]

    @property
    def overall_status(self) -> str:
        vals = self.fields
        if all(v == NAOngoingDone.DONE.value or v == NAOngoingDone.NA.value for v in vals) and \
                any(v == NAOngoingDone.DONE.value for v in vals):
            return OverallStatus.COMPLETED.value
        if all(v == NAOngoingDone.NA.value for v in vals):
            return OverallStatus.NOT_STARTED.value
        if any(v == NAOngoingDone.ONGOING.value for v in vals):
            return OverallStatus.ONGOING.value
        return OverallStatus.NOT_STARTED.value

    @property
    def progress_percent(self) -> float:
        vals = [v for v in self.fields if v != NAOngoingDone.NA.value]
        if not vals:
            return 0.0
        done = sum(1 for v in vals if v == NAOngoingDone.DONE.value)
        return round(done / len(vals) * 100, 1)
