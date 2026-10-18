"""
PyTest Configuration and Shared Fixtures.
Provides isolated in-memory or temporary SQLite test databases.
"""

from __future__ import annotations

import os
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database.connection import Base
from src.database.migrations.runner import apply_migrations
from src.api.app import app
from src.database.connection import get_db
from src.database.models import User, Business, Shop, BusinessMembership
from src.core.security import hash_password


@pytest.fixture(scope="session")
def test_engine():
    """Session-scoped SQLite test engine with foreign keys enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.close()

    # Apply all migrations to in-memory DB
    apply_migrations(engine)
    return engine


@pytest.fixture
def db_session(test_engine):
    """Function-scoped database session wrapped in a transaction rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)
    session = session_factory()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def test_client(db_session):
    """FastAPI test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_shop_context(db_session):
    """Seeds two distinct businesses and shops for testing multi-tenant isolation."""
    # User 1 (Shop 1 Owner)
    user1 = User(
        email="owner_shop1@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Owner One",
        is_active=True,
    )
    # User 2 (Shop 2 Owner)
    user2 = User(
        email="owner_shop2@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Owner Two",
        is_active=True,
    )
    db_session.add_all([user1, user2])
    db_session.flush()

    # Business 1 & Shop 1
    b1 = Business(name="Business One", business_type="grocery")
    db_session.add(b1)
    db_session.flush()
    s1 = Shop(business_id=b1.id, name="Shop One Main")
    db_session.add(s1)
    db_session.flush()

    # Business 2 & Shop 2
    b2 = Business(name="Business Two", business_type="pharmacy")
    db_session.add(b2)
    db_session.flush()
    s2 = Shop(business_id=b2.id, name="Shop Two Main")
    db_session.add(s2)
    db_session.flush()

    # Memberships
    m1 = BusinessMembership(user_id=user1.id, business_id=b1.id, shop_id=s1.id, role_code="owner")
    m2 = BusinessMembership(user_id=user2.id, business_id=b2.id, shop_id=s2.id, role_code="owner")
    db_session.add_all([m1, m2])
    db_session.flush()

    return {
        "user1": user1,
        "user2": user2,
        "business1": b1,
        "business2": b2,
        "shop1": s1,
        "shop2": s2,
    }
