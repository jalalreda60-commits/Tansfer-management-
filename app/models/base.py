"""
Declarative base and reusable mixins shared by every model.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import Column, Integer, DateTime

Base = declarative_base()


class TimestampMixin:
    """Adds created_at / updated_at columns, auto-managed."""

    @declared_attr
    def created_at(cls):  # noqa: N805
        return Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):  # noqa: N805
        return Column(
            DateTime,
            default=dt.datetime.utcnow,
            onupdate=dt.datetime.utcnow,
            nullable=False,
        )


class IDMixin:
    id = Column(Integer, primary_key=True, autoincrement=True)
