"""
Database bootstrap: SQLAlchemy engine, session factory and init helper.
"""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session

from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign-key enforcement on every new SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Session = scoped_session(SessionFactory)


def init_db() -> None:
    """Create all tables (idempotent) and seed nothing else."""
    from app.models import base  # noqa: F401  (ensures metadata is populated)
    base.Base.metadata.create_all(engine)


def get_session():
    """Return the shared scoped session."""
    return Session
