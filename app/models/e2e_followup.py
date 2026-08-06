from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, IDMixin
from app.config import MeetingStatus, YesNo, PCNStatus, OverallStatus


class E2EFollowUp(Base, IDMixin, TimestampMixin):
    __tablename__ = "e2e_followups"

    transfer_id = Column(Integer, ForeignKey("transfers.id"), nullable=False, unique=True)

    # --- Kick-off Call ---
    kickoff_calendar_week = Column(String(16))
    kickoff_status = Column(String(32), default=MeetingStatus.NOT_SCHEDULED.value)

    # --- PCN & PPAP Call ---
    pcn_ppap_calendar_week = Column(String(16))
    pcn_ppap_status = Column(String(32), default=MeetingStatus.NOT_SCHEDULED.value)
    pcn_decision = Column(String(8), default=YesNo.NO.value)
    pcn_status = Column(String(32), default=PCNStatus.NOT_SENT.value)
    pcn_action_list = Column(Text)

    # --- SOP Readiness Call ---
    sop_calendar_week = Column(String(16))
    sop_status = Column(String(32), default=MeetingStatus.NOT_SCHEDULED.value)
    sop_link_to_e2e_file = Column(String(512))
    sop_comments = Column(Text)
    sop_open_actions = Column(Text)

    transfer = relationship("Transfer", back_populates="e2e_followup")

    @property
    def overall_status(self) -> str:
        meetings = [self.kickoff_status, self.pcn_ppap_status, self.sop_status]
        if all(m == MeetingStatus.DONE.value for m in meetings):
            return OverallStatus.COMPLETED.value
        if all(m == MeetingStatus.NOT_SCHEDULED.value for m in meetings):
            return OverallStatus.NOT_STARTED.value
        return OverallStatus.ONGOING.value

    @property
    def progress_percent(self) -> float:
        meetings = [self.kickoff_status, self.pcn_ppap_status, self.sop_status]
        done = sum(1 for m in meetings if m == MeetingStatus.DONE.value)
        return round(done / len(meetings) * 100, 1)
