"""
Database Migration Runner for SME Finance Copilot.
Manages versioned, reproducible SQL migrations with an audit trail table (schema_migrations).
Works seamlessly on SQLite and PostgreSQL.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.database.connection import engine

logger = logging.getLogger("sme_finance.migrations")
logging.basicConfig(level=logging.INFO)

VERSIONS_DIR = Path(__file__).resolve().parent / "versions"


def init_migrations_table(eng: Engine) -> None:
    """Ensures the schema_migrations audit table exists."""
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP NOT NULL
                );
                """
            )
        )


def get_applied_migrations(eng: Engine) -> set[str]:
    """Retrieves all previously applied migration filenames."""
    init_migrations_table(eng)
    with eng.connect() as conn:
        result = conn.execute(text("SELECT version FROM schema_migrations;"))
        return {row[0] for row in result.fetchall()}


def get_available_migrations() -> List[Tuple[str, Path]]:
    """Returns all migration files in sorted order."""
    if not VERSIONS_DIR.exists():
        return []
    sql_files = sorted(VERSIONS_DIR.glob("*.sql"))
    return [(f.name, f) for f in sql_files]


def apply_migrations(eng: Engine = engine) -> List[str]:
    """
    Applies any pending migrations in alphanumeric order inside transactions.
    Returns list of newly applied migration versions.
    """
    init_migrations_table(eng)
    applied = get_applied_migrations(eng)
    available = get_available_migrations()

    newly_applied = []
    for version_name, file_path in available:
        if version_name not in applied:
            logger.info("Applying migration: %s", version_name)
            sql_content = file_path.read_text(encoding="utf-8")

            with eng.begin() as conn:
                # Execute individual SQL statements (handling SQLite multiple statements)
                # In SQLite, executing statements via raw driver executes script
                raw_conn = conn.connection
                if hasattr(raw_conn, "executescript"):
                    raw_conn.executescript(sql_content)
                else:
                    for stmt in sql_content.split(";"):
                        stmt_clean = stmt.strip()
                        if stmt_clean:
                            conn.execute(text(stmt_clean))

                conn.execute(
                    text(
                        "INSERT INTO schema_migrations (version, applied_at) VALUES (:version, :applied_at)"
                    ),
                    {"version": version_name, "applied_at": datetime.now(timezone.utc)},
                )
            newly_applied.append(version_name)
            logger.info("Successfully applied migration: %s", version_name)

    if not newly_applied:
        logger.info("Database schema is up to date.")
    return newly_applied


if __name__ == "__main__":
    apply_migrations()
