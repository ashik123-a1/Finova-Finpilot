"""
Database Connection and Engine Configuration Module.
Provides SQLite local-first setup with WAL mode, foreign keys, and connection pooling.
Directly switchable to PostgreSQL by updating DATABASE_URL.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from src.config import settings

# Base class for SQLAlchemy declarative models
Base = declarative_base()

# Configure SQLAlchemy Engine
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "timeout": 30,  # Wait up to 30 seconds if DB is locked
    }

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DB_ECHO,
    future=True,
)


# SQLite PRAGMA event listener for foreign keys, WAL mode, and busy timeout
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA busy_timeout = 30000;")
        cursor.close()


# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency provider for FastAPI route endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for scripts, services, and transactions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
