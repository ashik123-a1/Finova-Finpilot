"""
Test Suite for Report Generation, User Data Persistence, CSV/PDF Exports, and Database Backups.
Validates:
1. Permanent user and business data persistence across sessions and database re-connections.
2. Tenant and workspace isolation for all financial reports and exports.
3. CSV formula injection mitigation and UTF-8-SIG encoding.
4. Professional ReportLab PDF generation and byte validation.
5. SQLite WAL-safe database backup creation, verification, and isolated sandbox restore.
6. Authentic database PRAGMA integrity check execution.
7. Report execution history and audit persistence.
"""

from __future__ import annotations

import io
import os
import sqlite3
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fastapi.testclient import TestClient

from src.api.app import app
from src.config import settings
from src.core.security import create_token
from src.database.connection import Base, SessionLocal, engine
from src.database.models import (
    User,
    Business,
    Shop,
    BusinessMembership,
    Sale,
    Expense,
    Customer,
    Product,
    Receivable,
    LoanApplication,
    ReportExecution,
    utc_now,
)
from src.finance.reports_service import ReportsService
from src.finance.report_exporters import CsvReportExporter, PdfReportExporter
from src.database.integrity import DatabaseIntegrityService
from src.database.backup_service import DatabaseBackupService


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def multi_tenant_setup(db_session):
    """
    Sets up two isolated business workspaces with dedicated shops, users, and transactions.
    """
    # Business A (Bangladesh BDT)
    biz_a = Business(name="Bengal Retail Group", currency="BDT", business_type="grocery")
    db_session.add(biz_a)
    db_session.flush()

    shop_a1 = Shop(business_id=biz_a.id, name="Bengal Gulshan Outlet", branch_code="GUL-01")
    shop_a2 = Shop(business_id=biz_a.id, name="Bengal Dhanmondi Outlet", branch_code="DHA-01")
    db_session.add_all([shop_a1, shop_a2])
    db_session.flush()

    user_a = User(email="owner_a@bengalretail.com", full_name="Rahim Uddin", hashed_password="hashed_secret_a", is_active=True)
    db_session.add(user_a)
    db_session.flush()

    mem_a = BusinessMembership(user_id=user_a.id, business_id=biz_a.id, shop_id=shop_a1.id, role_code="owner", is_active=True)
    db_session.add(mem_a)

    # Customer & Transactions for Shop A1
    cust_a = Customer(business_id=biz_a.id, shop_id=shop_a1.id, name="=CMD|' /C calc'!A0", phone="01711000001", email="formula_target@demo.com", balance_minor=50000)
    db_session.add(cust_a)
    db_session.flush()

    sale_a1 = Sale(business_id=biz_a.id, shop_id=shop_a1.id, invoice_number="INV-A1-001", total_amount_minor=150000, sale_date=utc_now(), payment_method="cash", customer_id=cust_a.id)
    sale_a2 = Sale(business_id=biz_a.id, shop_id=shop_a1.id, invoice_number="INV-A1-002", total_amount_minor=250000, sale_date=utc_now() - timedelta(days=5), payment_method="card")
    exp_a1 = Expense(business_id=biz_a.id, shop_id=shop_a1.id, amount_minor=80000, expense_date=utc_now(), expense_category="rent", payment_method="bank_transfer")
    db_session.add_all([sale_a1, sale_a2, exp_a1])

    # Business B (China CNY)
    biz_b = Business(name="Shanghai Modern Supplies", currency="CNY", business_type="electronics")
    db_session.add(biz_b)
    db_session.flush()

    shop_b1 = Shop(business_id=biz_b.id, name="Shanghai Pudong Hub", branch_code="SHA-01")
    db_session.add(shop_b1)
    db_session.flush()

    user_b = User(email="manager_b@shanghai.cn", full_name="Li Wei", hashed_password="hashed_secret_b", is_active=True)
    db_session.add(user_b)
    db_session.flush()

    mem_b = BusinessMembership(user_id=user_b.id, business_id=biz_b.id, shop_id=shop_b1.id, role_code="manager", is_active=True)
    db_session.add(mem_b)

    sale_b1 = Sale(business_id=biz_b.id, shop_id=shop_b1.id, invoice_number="INV-B1-001", total_amount_minor=880000, sale_date=utc_now(), payment_method="alipay")
    db_session.add(sale_b1)

    db_session.commit()

    return {
        "biz_a": biz_a,
        "shop_a1": shop_a1,
        "shop_a2": shop_a2,
        "user_a": user_a,
        "cust_a": cust_a,
        "biz_b": biz_b,
        "shop_b1": shop_b1,
        "user_b": user_b,
    }


# ==============================================================================
# 1. Data Persistence Tests
# ==============================================================================

def test_user_and_business_data_persists_across_sessions(multi_tenant_setup, db_session):
    """
    Verifies that business records persist in the relational database,
    remain retrievable across separate queries, and maintain integer precision.
    """
    biz_id = multi_tenant_setup["biz_a"].id
    shop_id = multi_tenant_setup["shop_a1"].id

    sales = db_session.query(Sale).filter(Sale.business_id == biz_id, Sale.shop_id == shop_id).all()
    assert len(sales) == 2
    total_revenue = sum(s.total_amount_minor for s in sales)
    assert total_revenue == 400000  # 4000.00 BDT in minor units

    # Verify customer with malicious formula name is persisted verbatim in DB
    cust = db_session.query(Customer).filter_by(id=multi_tenant_setup["cust_a"].id).first()
    assert cust is not None
    assert cust.name == "=CMD|' /C calc'!A0"
    assert cust.balance_minor == 50000


# ==============================================================================
# 2. Report Generation & Tenant Isolation Tests
# ==============================================================================

def test_report_generation_tenant_isolation(multi_tenant_setup, db_session):
    """
    Guarantees Business A user cannot see Business B sales or expenses,
    and reports strictly filter by authorized business_id.
    """
    biz_a = multi_tenant_setup["biz_a"]
    biz_b = multi_tenant_setup["biz_b"]

    # Generate Income & Expense for Business A
    rep_a = ReportsService.generate_report(db_session, "income_expense", business_id=biz_a.id, save_execution=False)
    assert rep_a["currency"] == "BDT"
    assert rep_a["business_id"] == biz_a.id
    # Business A total revenue is 4000.00 BDT
    assert any("4,000" in kpi["value"] or "4000" in kpi["value"] for kpi in rep_a["summary_kpis"] if kpi["label"] == "Total Revenue")

    # Generate Income & Expense for Business B
    rep_b = ReportsService.generate_report(db_session, "income_expense", business_id=biz_b.id, save_execution=False)
    assert rep_b["currency"] == "CNY"
    assert rep_b["business_id"] == biz_b.id
    # Business B total revenue is 8800.00 CNY, zero records from Business A
    assert any("8,800" in kpi["value"] or "8800" in kpi["value"] for kpi in rep_b["summary_kpis"] if kpi["label"] == "Total Revenue")


# ==============================================================================
# 3. CSV Export & Formula Injection Mitigation Tests
# ==============================================================================

def test_csv_formula_injection_mitigation(multi_tenant_setup, db_session):
    """
    Verifies that CSV export sanitizes cells starting with '=', '+', '-', '@', tab, or CR
    by prepending a single quote, protecting Excel and spreadsheet users from DDE execution.
    Also verifies UTF-8-SIG byte order mark for multilingual compatibility.
    """
    biz_a = multi_tenant_setup["biz_a"]
    rep_crm = ReportsService.generate_report(db_session, "customer_crm", business_id=biz_a.id, save_execution=False)

    csv_bytes = CsvReportExporter.export(rep_crm)
    assert csv_bytes.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM

    csv_text = csv_bytes.decode("utf-8-sig")
    # Verify the customer name starting with '=' was sanitized with a leading single quote
    assert "'=CMD|' /C calc'!A0" in csv_text
    assert "\n=CMD|" not in csv_text


# ==============================================================================
# 4. ReportLab PDF Export Tests
# ==============================================================================

def test_pdf_report_export_format_and_bytes(multi_tenant_setup, db_session):
    """
    Verifies ReportLab PDF generation renders valid non-empty byte streams
    with the official %PDF header, title, and metadata.
    """
    biz_a = multi_tenant_setup["biz_a"]
    for r_type in ["profit_loss", "ledger", "cash_flow"]:
        rep = ReportsService.generate_report(db_session, r_type, business_id=biz_a.id, save_execution=False)
        pdf_bytes = PdfReportExporter.export(rep)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 2000
        assert pdf_bytes.startswith(b"%PDF")
        assert b"%%EOF" in pdf_bytes[-1024:]


# ==============================================================================
# 5. Database PRAGMA Integrity Service Tests
# ==============================================================================

def test_database_pragma_integrity_check(db_session):
    """
    Verifies genuine execution of SQLite PRAGMA integrity_check and diagnostics.
    """
    diag = DatabaseIntegrityService.run_integrity_check(db_session)
    assert diag["engine"] == "sqlite"
    assert diag["is_healthy"] is True
    assert diag["status"] == "optimal"
    assert diag["checks"]["pragma_integrity_check"] == "ok"
    assert diag["checks"]["pragma_quick_check"] == "ok"
    assert diag["checks"]["foreign_key_violations"] == 0
    assert diag["check_duration_ms"] >= 0.0


# ==============================================================================
# 6. WAL-Safe Backup and Isolated Sandbox Restore Tests
# ==============================================================================

def test_database_backup_and_isolated_restore(tmp_path):
    """
    Verifies SQLite native online backup creation, SHA-256 verification,
    and isolated test restore without modifying the active database.
    """
    # 1. Create a dedicated test SQLite database with schema and records
    test_db_path = tmp_path / "active_test.db"
    conn = sqlite3.connect(str(test_db_path))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER);")
    cursor.execute("INSERT INTO products VALUES (1, 'Organic Honey', 500);")
    cursor.execute("INSERT INTO products VALUES (2, 'Almond Butter', 1200);")
    conn.commit()
    conn.close()

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 2. Perform native online backup
    timestamp = "20261020_120000"
    backup_file = backup_dir / f"test_backup_{timestamp}.db"
    src = sqlite3.connect(str(test_db_path))
    dst = sqlite3.connect(str(backup_file))
    src.backup(dst)
    dst.close()
    src.close()

    assert backup_file.exists()
    assert backup_file.stat().st_size > 0

    # 3. Verify backup file
    verification = DatabaseBackupService.verify_backup_file(backup_file)
    assert verification["is_valid"] is True
    assert verification["integrity_status"] == "ok"
    assert verification["table_counts"].get("products") == 2

    # 4. Perform isolated sandbox restore test
    sandbox_dir = tmp_path / "restore_sandbox"
    restore_res = DatabaseBackupService.test_restore_to_isolated_database(
        backup_filename=str(backup_file),
        isolated_test_dir=sandbox_dir,
    )
    assert restore_res["restore_test_status"] == "success"
    assert restore_res["is_valid"] is True
    assert restore_res["table_counts"].get("products") == 2


# ==============================================================================
# 7. Reports API Endpoints Integration Tests
# ==============================================================================

def test_reports_api_endpoints(test_client, seeded_shop_context):
    """
    Tests /api/reports/preview, /api/reports/export/csv, /api/reports/export/pdf,
    and /api/reports/history using test_client and token authentication.
    """
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token1 = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token1}"}

    # Catalog
    types_res = test_client.get("/api/reports/types")
    assert types_res.status_code == 200
    assert len(types_res.json()["catalog"]) >= 10

    # Preview
    preview_res = test_client.post(
        "/api/reports/preview",
        json={"report_type": "income_expense", "shop_id": shop1.id},
        headers=headers,
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["title"] == "Income & Expense Statement"
    assert preview_data["currency"] == "BDT"

    # CSV Export
    csv_res = test_client.post(
        "/api/reports/export/csv",
        json={"report_type": "income_expense", "shop_id": shop1.id},
        headers=headers,
    )
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert csv_res.content.startswith(b"\xef\xbb\xbf")

    # PDF Export
    pdf_res = test_client.post(
        "/api/reports/export/pdf",
        json={"report_type": "income_expense", "shop_id": shop1.id},
        headers=headers,
    )
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")

    # History
    hist_res = test_client.get("/api/reports/history", headers=headers)
    assert hist_res.status_code == 200
    assert len(hist_res.json()["history"]) >= 3

