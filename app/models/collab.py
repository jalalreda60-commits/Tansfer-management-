"""
Generic, polymorphic models that can be attached to ANY entity
(transfer, tool, part_number, ...) via (entity_type, entity_id) columns.
This avoids one attachments/comments/history table per entity type.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models.base import Base, IDMixin


class Attachment(Base, IDMixin):
    __tablename__ = "attachments"

    entity_type = Column(String(32), nullable=False)   # 'transfer', 'tool', ...
    entity_id = Column(Integer, nullable=False)
    file_name = Column(String(256), nullable=False)
    file_path = Column(String(1024), nullable=False)
    uploaded_by = Column(String(128), default="user")
    uploaded_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)


class Comment(Base, IDMixin):
    __tablename__ = "comments"

    entity_type = Column(String(32), nullable=False)
    entity_id = Column(Integer, nullable=False)
    author = Column(String(128), default="user")
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)


class HistoryLog(Base, IDMixin):
    __tablename__ = "history_logs"

    entity_type = Column(String(32), nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(String(64), nullable=False)     # Created / Updated / Deleted ...
    details = Column(Text)
    timestamp = Column(DateTime, default=dt.datetime.utcnow, nullable=False)


class Notification(Base, IDMixin):
    __tablename__ = "notifications"

    entity_type = Column(String(32))
    entity_id = Column(Integer)
    level = Column(String(16), default="info")   # info / warning / critical
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    is_read = Column(Integer, default=0)   # 0/1 boolean for wider SQLite compat
