"""
Comprehensive Phase-Gate Readiness Tests for Database & ML Models.
Executes isolated tests covering:
- Isolated Database Lifecycle (Init, Migrations, FKs, Rollback, Reopen)
- Document Ingest -> OCR -> Extraction -> Review -> Idempotent Ledger Posting
- Financial Feature Generation -> ML Forecaster -> Loan Risk Policy Engine
- Minor-Unit Integer Math & Multi-Currency Integrity
"""

import io
import os
import json
import sqlite3
import pytest
from decimal import Decimal
from pathlib import Path
from PIL import Image
from sqlalchemy import create_engine, event, text, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from src.database.connection import Base
from src.database.migrations.runner import apply_migrations
from src.database.models import (
    Business,
    Shop,
    User,
    Product,
    Sale,
    SaleItem,
    Expense,
    Document,
    DocumentClassification,
    DocumentExtraction,
    DocumentReview,
    CashMovement,
    utc_now,
)
from src.documents.schemas import DocumentType, DocumentReviewConfirmation
from src.documents.extractor import MockOcrProvider, StructuredDocumentExtractor, BaseOcrProvider
from src.documents.classifier import DocumentClassifier
from src.documents.router import DocumentPipelineRouter
from src.documents.poster import DocumentPostingService
from src.finance.calculator import FinancialCalculator
from src.ai.forecaster import CashFlowForecaster
from src.ai.loan_risk import TransparentLoanRiskEngine
from src.core.country_profiles import CountryRegistry


@pytest.fixture
def isolated_db_path(tmp_path):
    """Provides a fresh isolated SQLite file path."""
    return str(tmp_path / "test_phase_gate.db")


@pytest.fixture
def isolated_engine(isolated_db_path):
    """Creates a temporary isolated SQLite engine with WAL and FK enforcement."""
    eng = create_engine(f"sqlite:///{isolated_db_path}", echo=False)

    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.close()

    apply_migrations(eng)
    return eng


@pytest.fixture
def isolated_session(isolated_engine):
    """Provides an isolated session committed/cleaned up cleanly."""
    SessionMaker = sessionmaker(bind=isolated_engine, autoflush=False, autocommit=False)
    session = SessionMaker()
    yield session
    session.close()


def test_isolated_db_initialization_and_fk_enforcement(isolated_session, isolated_engine):
    """Test 1: Verify clean initialization, migration table, and FK constraints."""
    # Check migration version
    mig = isolated_session.execute(text("SELECT version FROM schema_migrations;")).fetchall()
    assert len(mig) == 1
    assert mig[0][0] == "001_initial_schema.sql"

    # Attempt to insert orphan child record without parent business
    with pytest.raises(IntegrityError):
        isolated_session.execute(
            text("INSERT INTO shops (business_id, name) VALUES (8888, 'Orphan Shop');")
        )
        isolated_session.flush()
    isolated_session.rollback()


def test_transaction_rollback_integrity(isolated_session):
    """Test 2: Verify that on mid-operation failure, all pending inserts are rolled back."""
    # Insert valid business
    biz = Business(name="Rollback Test SME", currency="BDT", business_type="retail")
    isolated_session.add(biz)
    isolated_session.flush()
    biz_id = biz.id

    # Add a valid shop, followed by an invalid foreign key insert in the same transaction
    shop = Shop(business_id=biz_id, name="Shop Alpha")
    isolated_session.add(shop)
    isolated_session.flush()

    try:
        # Invalid FK insert
        isolated_session.execute(
            text("INSERT INTO shops (business_id, name) VALUES (999999, 'Bad Shop');")
        )
        isolated_session.flush()
    except IntegrityError:
        isolated_session.rollback()

    # Verify that Shop Alpha was rolled back and is not in DB
    found_shop = isolated_session.scalars(select(Shop).where(Shop.name == "Shop Alpha")).first()
    assert found_shop is None


def test_database_restart_and_reopen_persistence(isolated_db_path):
    """Test 3: Verify that closing and reopening the SQLite database preserves all data."""
    # Connect and insert record
    eng1 = create_engine(f"sqlite:///{isolated_db_path}")
    apply_migrations(eng1)
    with sessionmaker(bind=eng1)() as s1:
        biz = Business(name="Persisted SME Co.", currency="USD", business_type="wholesale")
        s1.add(biz)
        s1.commit()
        b_id = biz.id
    eng1.dispose()

    # Reopen database with new engine connection
    eng2 = create_engine(f"sqlite:///{isolated_db_path}")
    with sessionmaker(bind=eng2)() as s2:
        reopened_biz = s2.get(Business, b_id)
        assert reopened_biz is not None
        assert reopened_biz.name == "Persisted SME Co."
        assert reopened_biz.currency == "USD"
    eng2.dispose()


def test_document_pipeline_e2e_and_idempotent_posting(isolated_session):
    """
    Test 4: Full Pipeline:
    Upload -> Mock OCR -> Classification -> Extraction -> Review Confirmation -> Approved Posting -> Idempotent Re-post Guard
    """
    # Seed business and shop
    biz = Business(name="Demo Retailer Ltd", currency="BDT", business_type="grocery")
    isolated_session.add(biz)
    isolated_session.flush()
    shop = Shop(business_id=biz.id, name="Main Grocery Store")
    isolated_session.add(shop)
    user = User(email="manager@grocery.com", hashed_password="hashed_pw", full_name="Shop Manager")
    isolated_session.add(user)
    isolated_session.commit()

    # Route document through pipeline with valid PNG bytes
    router = DocumentPipelineRouter(ocr_provider=MockOcrProvider())
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    file_bytes = buf.getvalue()
    routing_result = router.process_and_route(
        session=isolated_session,
        business_id=biz.id,
        shop_id=shop.id,
        file_bytes=file_bytes,
        original_filename="receipt_2026.png",
        user_id=user.id,
    )
    isolated_session.commit()

    assert routing_result.document_id is not None
    assert routing_result.predicted_doc_type == DocumentType.SALES_RECEIPT
    assert routing_result.normalized_values.get("total_amount_minor") == 90000
    assert routing_result.requires_user_review is True
    assert len(routing_result.review_reasons) > 0

    # Human Review Confirmation
    doc_id = routing_result.document_id
    confirmation = DocumentReviewConfirmation(
        document_id=doc_id,
        confirmed_doc_type=DocumentType.SALES_RECEIPT,
        decision_action="approve_and_post",
        final_values={
            "invoice_number": "INV-2026-9901",
            "date": "2026-10-15",
            "subtotal_minor": 45000,
            "tax_minor": 2250,
            "discount_minor": 0,
            "total_amount_minor": 47250,
            "paid_amount_minor": 47250,
            "payment_method": "cash",
            "items": [
                {
                    "description": "Groceries Basket",
                    "quantity": 1,
                    "unit_price_minor": 45000,
                    "discount_minor": 0,
                    "line_total_minor": 45000,
                }
            ],
        },
        reviewer_notes="Approved verified receipt by store manager.",
    )

    # Post to ledger
    post_res = DocumentPostingService.post_confirmed_document(
        session=isolated_session,
        confirmation=confirmation,
        user_id=user.id,
    )
    isolated_session.commit()
    assert post_res["status"] == "posted"

    # Verify Sale record exists in ledger
    sale = isolated_session.scalars(select(Sale).where(Sale.document_id == doc_id)).first()
    assert sale is not None
    assert sale.invoice_number == "INV-2026-9901"
    assert sale.total_amount_minor == 47250
    assert sale.subtotal_minor == 45000
    assert sale.tax_minor == 2250
    assert len(sale.items) == 1

    # Idempotent re-post guard: attempt to post the same document again
    repost_res = DocumentPostingService.post_confirmed_document(
        session=isolated_session,
        confirmation=confirmation,
        user_id=user.id,
    )
    assert repost_res["status"] == "already_posted"

    # Verify no duplicate sales were created
    sales_count = isolated_session.execute(
        text(f"SELECT COUNT(*) FROM sales WHERE document_id = {doc_id};")
    ).scalar()
    assert sales_count == 1


def test_financial_pipeline_historical_to_forecast_and_risk(isolated_session):
    """
    Test 5: Financial Pipeline:
    Historical Cash Movements -> Feature Generation -> Cash Flow Forecaster -> Loan Risk Policy Engine
    """
    biz = Business(name="Apex Wholesale", currency="BDT", business_type="wholesale")
    isolated_session.add(biz)
    isolated_session.flush()
    shop = Shop(business_id=biz.id, name="Wholesale Depot")
    isolated_session.add(shop)
    isolated_session.flush()

    # Seed 60 days of historical cash movements
    daily_amounts = [50_000_00 + (i % 7) * 5_000_00 for i in range(60)]
    for idx, amt in enumerate(daily_amounts):
        cm = CashMovement(
            business_id=biz.id,
            shop_id=shop.id,
            movement_date=utc_now(),
            movement_type="inflow",
            source_type="sale",
            source_id=idx + 1,
            amount_minor=amt,
            running_balance_minor=amt * (idx + 1),
            is_synthetic=True,
        )
        isolated_session.add(cm)
    isolated_session.commit()

    # 1. Query historical series
    rows = isolated_session.execute(
        text(
            f"SELECT amount_minor FROM cash_movements WHERE shop_id = {shop.id} ORDER BY id ASC;"
        )
    ).fetchall()
    series = [r[0] for r in rows]
    assert len(series) == 60

    # 2. ML & Statistical Forecast
    forecast = CashFlowForecaster.ml_lagged_forecast(series, horizon_days=30, lag_days=7)
    assert len(forecast["point_forecast_minor"]) == 30
    assert len(forecast["lower_bound_80_minor"]) == 30
    assert len(forecast["upper_bound_80_minor"]) == 30
    assert forecast["lower_bound_80_minor"][0] <= forecast["point_forecast_minor"][0] <= forecast["upper_bound_80_minor"][0]

    # 3. Transparent Loan Risk Evaluation
    monthly_rev = sum(series[-30:])
    monthly_exp = int(monthly_rev * 0.65)
    risk_res = TransparentLoanRiskEngine.evaluate_loan_scenario(
        monthly_revenue_minor=monthly_rev,
        monthly_expenses_minor=monthly_exp,
        existing_monthly_debt_minor=10_000_00,
        requested_amount_minor=500_000_00,
        tenure_months=24,
        annual_interest_rate_pct=9.0,
    )
    assert risk_res["recommendation_status"] in ["eligible", "borderline"]
    assert risk_res["dscr_ratio"] > 1.0
    assert len(risk_res["recommendation_reasons"]) > 0
    assert "regulatory_disclaimer" in risk_res


def test_financial_calculator_numerical_integrity_and_boundaries():
    """Test 6: Verify deterministic integer math and edge cases across financial calculator."""
    # 1. P&L with zero revenue
    pl_zero = FinancialCalculator.calculate_profit_and_loss(
        sales_minor=[], cogs_minor=[1000], operating_expenses_minor=[500]
    )
    assert pl_zero.revenue_minor == 0
    assert pl_zero.net_profit_minor == -1500
    assert pl_zero.gross_margin_pct == 0.0

    # 2. P&L standard
    pl = FinancialCalculator.calculate_profit_and_loss(
        sales_minor=[10000_00], cogs_minor=[6000_00], operating_expenses_minor=[2000_00]
    )
    assert pl.revenue_minor == 10000_00
    assert pl.gross_profit_minor == 4000_00
    assert pl.net_profit_minor == 2000_00
    assert pl.gross_margin_pct == 40.0
    assert pl.net_margin_pct == 20.0

    # 3. Loan comparison: Reducing balance vs Flat Rate
    loan = FinancialCalculator.calculate_loan_comparison(
        principal_minor=100_000_00,
        annual_interest_rate_pct=10.0,
        tenure_months=12,
        processing_fee_bps=100,
    )
    # Stated 10% flat rate interest = 10,000.00
    assert loan.flat_total_interest_minor == 10_000_00
    # Reducing balance interest must be strictly less than flat rate interest
    assert loan.reducing_total_interest_minor < loan.flat_total_interest_minor
    # Flat rate penalty is positive
    assert loan.flat_rate_penalty_minor > 0

    # 4. DSCR zero debt service boundary
    dscr_inf = FinancialCalculator.calculate_dscr(
        monthly_net_operating_income_minor=50_000_00,
        monthly_debt_service_minor=0,
    )
    assert dscr_inf == float("inf")

    # 5. Multi-currency precision
    assert CountryRegistry.get_currency_multiplier("BDT") == 100
    assert CountryRegistry.get_currency_multiplier("CNY") == 100
    assert CountryRegistry.get_currency_multiplier("USD") == 100
    assert CountryRegistry.get_currency_multiplier("KWD") == 1000  # 3 decimals
    assert CountryRegistry.get("KW").minor_unit_multiplier == 1000
    assert CountryRegistry.get("BD").minor_unit_multiplier == 100
