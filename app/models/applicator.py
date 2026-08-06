from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, IDMixin


class Applicator(Base, IDMixin, TimestampMixin):
    """Used when Transfer.activity == Stamping."""
    __tablename__ = "applicators"

    part_number_id = Column(Integer, ForeignKey("part_numbers.id"), nullable=False, unique=True)

    pe = Column(String(128))
    urgency = Column(String(16))
    applicator_required = Column(String(8))   # Yes/No
    applicator = Column(String(128))
    crimping_specification = Column(String(256))
    terminal = Column(String(128))
    wire_section = Column(String(64))
    number_of_parts = Column(Integer, default=0)
    required_approvals = Column(String(256))
    applicator_available_location = Column(String(128))
    crimping_request = Column(String(128))
    comments = Column(Text)

    part_number = relationship("PartNumber", back_populates="applicator")


class CounterPart(Base, IDMixin, TimestampMixin):
    """Used when Transfer.activity == Molding."""
    __tablename__ = "counter_parts"

    part_number_id = Column(Integer, ForeignKey("part_numbers.id"), nullable=False, unique=True)

    pe = Column(String(128))
    counter_part = Column(String(128))
    terminal = Column(String(128))
    crimping = Column(String(128))
    terminal_request = Column(String(128))
    status = Column(String(32))
    comments = Column(Text)

    part_number = relationship("PartNumber", back_populates="counter_part")
