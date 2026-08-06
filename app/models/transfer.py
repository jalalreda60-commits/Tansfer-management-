"""
Core hierarchy: Transfer -> Tool -> PartNumber.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, IDMixin
from app.config import OverallStatus


class Transfer(Base, IDMixin, TimestampMixin):
    __tablename__ = "transfers"

    trf_number = Column(String(64), unique=True, nullable=False, index=True)
    planned_transfer_date = Column(Date, nullable=False)
    transfer_type = Column(String(32), nullable=False)   # 1-Step / 2-Step
    activity = Column(String(32), nullable=False)         # Stamping / Molding
    sender_location = Column(String(128), nullable=False)
    receiver_location = Column(String(128), nullable=False)
    technology = Column(String(128), nullable=False)

    tools = relationship(
        "Tool", back_populates="transfer", cascade="all, delete-orphan",
        order_by="Tool.tool_number",
    )
    ptt_approval = relationship(
        "PTTApproval", back_populates="transfer", uselist=False,
        cascade="all, delete-orphan",
    )
    e2e_followup = relationship(
        "E2EFollowUp", back_populates="transfer", uselist=False,
        cascade="all, delete-orphan",
    )
    release = relationship(
        "ReleaseChecklist", back_populates="transfer", uselist=False,
        cascade="all, delete-orphan",
    )
    attachments = relationship(
        "Attachment",
        primaryjoin="and_(Attachment.entity_type=='transfer', "
                    "foreign(Attachment.entity_id)==Transfer.id)",
        cascade="all, delete-orphan", viewonly=False,
    )
    comments = relationship(
        "Comment",
        primaryjoin="and_(Comment.entity_type=='transfer', "
                    "foreign(Comment.entity_id)==Transfer.id)",
        cascade="all, delete-orphan", viewonly=False,
        order_by="Comment.created_at.desc()",
    )
    history = relationship(
        "HistoryLog",
        primaryjoin="and_(HistoryLog.entity_type=='transfer', "
                    "foreign(HistoryLog.entity_id)==Transfer.id)",
        cascade="all, delete-orphan", viewonly=False,
        order_by="HistoryLog.timestamp.desc()",
    )

    # ------------------------------------------------------------------
    # Derived / computed helpers
    # ------------------------------------------------------------------
    @property
    def days_remaining(self) -> int:
        return (self.planned_transfer_date - dt.date.today()).days

    @property
    def all_part_numbers(self):
        parts = []
        for tool in self.tools:
            parts.extend(tool.part_numbers)
        return parts

    def __repr__(self):
        return f"<Transfer {self.trf_number}>"


class Tool(Base, IDMixin, TimestampMixin):
    __tablename__ = "tools"

    transfer_id = Column(Integer, ForeignKey("transfers.id"), nullable=False)
    tool_number = Column(String(64), nullable=False)

    transfer = relationship("Transfer", back_populates="tools")
    part_numbers = relationship(
        "PartNumber", back_populates="tool", cascade="all, delete-orphan",
        order_by="PartNumber.part_number",
    )
    safety_stock = relationship(
        "SafetyStock", back_populates="tool", uselist=False,
        cascade="all, delete-orphan",
    )
    training = relationship(
        "Training", back_populates="tool", uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Tool {self.tool_number}>"


class PartNumber(Base, IDMixin, TimestampMixin):
    __tablename__ = "part_numbers"

    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False)
    part_number = Column(String(64), nullable=False)

    tool = relationship("Tool", back_populates="part_numbers")
    raw_material = relationship(
        "RawMaterial", back_populates="part_number", uselist=False,
        cascade="all, delete-orphan",
    )
    pre_check = relationship(
        "PreCheck", back_populates="part_number", uselist=False,
        cascade="all, delete-orphan",
    )
    applicator = relationship(
        "Applicator", back_populates="part_number", uselist=False,
        cascade="all, delete-orphan",
    )
    counter_part = relationship(
        "CounterPart", back_populates="part_number", uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<PartNumber {self.part_number}>"
