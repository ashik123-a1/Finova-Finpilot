"""
Unit Tests for Database Migrations, Schema Integrity, and Foreign Keys.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.database.models import User, Business, Shop, Product


def test_schema_migrations_table_exists(db_session):
    """Verifies that schema_migrations audit table exists and has versions."""
    res = db_session.execute(text("SELECT version FROM schema_migrations;")).fetchall()
    versions = [r[0] for r in res]
    assert "001_initial_schema.sql" in versions


def test_foreign_key_constraint_enforcement(db_session):
    """Verifies that SQLite PRAGMA foreign_keys = ON rejects orphaned records."""
    # Attempting to insert a shop with a non-existent business_id must fail
    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                "INSERT INTO shops (business_id, name) VALUES (999999, 'Orphaned Shop');"
            )
        )
        db_session.flush()
    db_session.rollback()


def test_cascade_delete(db_session, seeded_shop_context):
    """Verifies that deleting a business cascades to its shops."""
    b1_id = seeded_shop_context["business1"].id
    s1_id = seeded_shop_context["shop1"].id

    # Verify shop exists
    shop = db_session.get(Shop, s1_id)
    assert shop is not None

    # Delete business
    b = db_session.get(Business, b1_id)
    db_session.delete(b)
    db_session.flush()

    # Shop should be automatically deleted via cascade
    assert db_session.get(Shop, s1_id) is None
