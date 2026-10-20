"""
Comprehensive Test Suite for CRM, Customer Dues, Messaging & Inventory Replenishment.
Tests customer CRUD, dynamic RFM segmentation, polite reminders, external handoffs (wa.me),
consent guardrails, payment reconciliation FIFO, margin guardrails, stock adjustments,
auto-draft purchase orders, and multi-tenant shop isolation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from src.database.models import (
    Customer,
    Sale,
    Receivable,
    Payment,
    CashMovement,
    CustomerCommunication,
    DiscountCampaign,
    Product,
    StockAdjustment,
    InventoryMovement,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    AuditLog,
    Notification,
)
from src.core.security import create_token
from src.config import settings
from src.crm.messaging import (
    clean_phone_number,
    clean_phone_for_wa,
    build_reminder_template,
    build_campaign_template,
)


# --- Unit Tests for Helper Functions ---

def test_clean_phone_number_formatting():
    """Tests domestic and international phone normalization."""
    assert clean_phone_number("01711234567") == "+8801711234567"
    assert clean_phone_number("8801711234567") == "+8801711234567"
    assert clean_phone_number("+880 1711-234567") == "+8801711234567"
    assert clean_phone_for_wa("+8801711234567") == "8801711234567"


def test_reminder_template_generation():
    """Tests multilingual polite templates contain requisite financial and identity parameters."""
    # Bengali Polite
    bn = build_reminder_template(
        template_type="bn_friendly",
        customer_name="Rahim Mia",
        shop_name="Dhaka Super Store",
        total_due_formatted="৳ 15,000.00",
        invoice_list=["INV-001", "INV-002"],
    )
    assert "Rahim Mia" in bn
    assert "Dhaka Super Store" in bn
    assert "৳ 15,000.00" in bn
    assert "বিনীত" in bn or "বকেয়া" in bn

    # English Formal
    en = build_reminder_template(
        template_type="en_formal",
        customer_name="Apex Ltd",
        shop_name="Dhaka Super Store",
        total_due_formatted="BDT 50,000.00",
    )
    assert "Apex Ltd" in en
    assert "official statement" in en.lower()


# --- API Route Tests with Test Client ---

def test_customer_creation_and_opening_receivable(test_client, seeded_shop_context, db_session):
    """Tests creating customer with opening balance generates an opening receivable entry."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "shop_id": shop1.id,
        "name": "Bismillah Traders",
        "phone": "+880 1711-998877",
        "email": "bismillah@test.bd",
        "address": "Chawkbazar, Dhaka",
        "credit_limit_minor": 5000000,     # 50,000 BDT
        "opening_balance_minor": 1500000,  # 15,000 BDT
        "whatsapp_number": "+8801711998877",
        "telegram_handle": "@bismillah_traders",
        "customer_type": "wholesale",
        "messaging_consent": True,
        "notes": "Verified wholesale customer with net-30 terms",
    }

    res = test_client.post("/api/crm/customers", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    cust_id = data["customer"]["id"]

    # Verify database persistence
    cust = db_session.get(Customer, cust_id)
    assert cust is not None
    assert cust.name == "Bismillah Traders"
    assert cust.credit_limit_minor == 5000000
    assert cust.balance_minor == 1500000

    # Verify opening receivable was created
    rec = db_session.query(Receivable).filter_by(customer_id=cust_id, shop_id=shop1.id).first()
    assert rec is not None
    assert rec.total_amount_minor == 1500000
    assert rec.outstanding_amount_minor == 1500000
    assert rec.status == "open"


def test_customer_duplicate_phone_prevention(test_client, seeded_shop_context):
    """Tests shop cannot register two customers with the same phone number."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "shop_id": shop1.id,
        "name": "Customer Duplicate A",
        "phone": "+880 1819-112233",
        "credit_limit_minor": 0,
        "opening_balance_minor": 0,
    }
    res1 = test_client.post("/api/crm/customers", json=payload, headers=headers)
    assert res1.status_code == 201

    # Attempt duplicate
    payload["name"] = "Customer Duplicate B"
    res2 = test_client.post("/api/crm/customers", json=payload, headers=headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_customer_list_and_rfm_segmentation(test_client, seeded_shop_context, db_session):
    """Tests GET /api/crm/customers computes dynamic RFM segmentation and summary totals."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    # Seed a customer
    cust = Customer(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        name="Seeded Client",
        phone="+880 1711-001122",
        balance_minor=0,
    )
    db_session.add(cust)
    db_session.commit()

    # Query customer list
    res = test_client.get(f"/api/crm/customers?shop_id={shop1.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "summary" in data
    assert "customers" in data
    assert data["summary"]["total_customers"] >= 1


def test_customer_due_reminders_draft_and_send(test_client, seeded_shop_context, db_session):
    """Tests drafting polite reminder and dispatching via external handoff (wa.me)."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    # Create customer with due balance
    cust = Customer(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        name="Apex Fabrics",
        phone="+880 1912-334455",
        whatsapp_number="+8801912334455",
        balance_minor=2500000,
        messaging_consent=True,
    )
    db_session.add(cust)
    db_session.flush()

    sale = Sale(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        invoice_number="INV-TEST-001",
        customer_id=cust.id,
        total_amount_minor=2500000,
        paid_amount_minor=0,
        payment_status="unpaid",
    )
    db_session.add(sale)
    db_session.flush()

    rec = Receivable(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        sale_id=sale.id,
        customer_id=cust.id,
        total_amount_minor=2500000,
        outstanding_amount_minor=2500000,
        status="open",
        due_date=datetime.now(timezone.utc) + timedelta(days=15),
    )
    db_session.add(rec)
    db_session.commit()

    # 1. Draft reminder
    draft_res = test_client.post(
        "/api/crm/reminders/draft",
        json={"shop_id": shop1.id, "customer_id": cust.id, "template_type": "bn_friendly"},
        headers=headers,
    )
    assert draft_res.status_code == 200
    draft_data = draft_res.json()
    assert "Apex Fabrics" in draft_data["draft_body"]

    # 2. Send reminder via WhatsApp (expect manual handoff URL since live API token is not configured)
    send_res = test_client.post(
        "/api/crm/reminders/send",
        json={
            "shop_id": shop1.id,
            "customer_id": cust.id,
            "channel": "whatsapp",
            "message_body": draft_data["draft_body"],
        },
        headers=headers,
    )
    assert send_res.status_code == 200
    send_data = send_res.json()
    assert send_data["success"] is True
    assert send_data["mode"] == "manual_handoff"
    assert "wa.me/8801912334455" in send_data["handoff_url"]
    assert send_data["status"] == "awaiting_user_action"

    # Verify communication log was created
    comm = db_session.query(CustomerCommunication).filter_by(customer_id=cust.id).first()
    assert comm is not None
    assert comm.channel == "whatsapp"
    assert comm.status == "awaiting_user_action"


def test_messaging_consent_guardrail(test_client, seeded_shop_context, db_session):
    """Tests reminder dispatch fails if customer has not granted messaging consent unless overridden."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    cust = Customer(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        name="No Consent Client",
        phone="+880 1611-445566",
        balance_minor=1000000,
        messaging_consent=False,  # No consent
    )
    db_session.add(cust)
    db_session.commit()

    # Attempt send without override -> must fail with 400
    res_fail = test_client.post(
        "/api/crm/reminders/send",
        json={
            "shop_id": shop1.id,
            "customer_id": cust.id,
            "channel": "whatsapp",
            "message_body": "Polite reminder text",
            "override_consent": False,
        },
        headers=headers,
    )
    assert res_fail.status_code == 400
    assert "consent" in res_fail.json()["detail"].lower()

    # Attempt send with override -> succeeds
    res_ok = test_client.post(
        "/api/crm/reminders/send",
        json={
            "shop_id": shop1.id,
            "customer_id": cust.id,
            "channel": "whatsapp",
            "message_body": "Polite reminder text",
            "override_consent": True,
        },
        headers=headers,
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["success"] is True


def test_payment_settlement_reconciliation(test_client, seeded_shop_context, db_session):
    """Tests recording customer payment settles receivables FIFO and posts ledger entries."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    cust = Customer(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        name="Payment Test Customer",
        phone="+880 1511-778899",
        balance_minor=1000000,  # 10,000 BDT
    )
    db_session.add(cust)
    db_session.flush()

    sale1 = Sale(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        invoice_number="INV-PAY-001",
        customer_id=cust.id,
        total_amount_minor=600000,
        paid_amount_minor=0,
        payment_status="unpaid",
    )
    sale2 = Sale(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        invoice_number="INV-PAY-002",
        customer_id=cust.id,
        total_amount_minor=400000,
        paid_amount_minor=0,
        payment_status="unpaid",
    )
    db_session.add_all([sale1, sale2])
    db_session.flush()

    rec1 = Receivable(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        sale_id=sale1.id,
        customer_id=cust.id,
        total_amount_minor=600000,  # 6,000 BDT
        outstanding_amount_minor=600000,
        status="open",
        due_date=datetime.now(timezone.utc) - timedelta(days=10),
    )
    rec2 = Receivable(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        sale_id=sale2.id,
        customer_id=cust.id,
        total_amount_minor=400000,  # 4,000 BDT
        outstanding_amount_minor=400000,
        status="open",
        due_date=datetime.now(timezone.utc) + timedelta(days=10),
    )
    db_session.add_all([rec1, rec2])
    db_session.commit()

    # Pay 8,000 BDT -> should completely settle rec1 (6,000) and partially settle rec2 (2,000 remaining)
    pay_res = test_client.post(
        "/api/crm/payments/record",
        json={
            "shop_id": shop1.id,
            "customer_id": cust.id,
            "amount_minor": 800000,
            "payment_method": "mfs_bkash",
            "notes": "TrxID #BK882190",
        },
        headers=headers,
    )
    assert pay_res.status_code == 201
    data = pay_res.json()
    assert data["status"] == "success"
    assert data["new_balance_minor"] == 200000

    # Verify rec1 is paid, rec2 is partial
    db_session.refresh(rec1)
    db_session.refresh(rec2)
    assert rec1.outstanding_amount_minor == 0
    assert rec1.status == "paid"
    assert rec2.outstanding_amount_minor == 200000
    assert rec2.status == "partial"

    # Verify Payment and CashMovement records
    pay = db_session.query(Payment).filter_by(reference_id=cust.id).first()
    assert pay is not None
    assert pay.amount_minor == 800000
    assert pay.payment_method == "mfs_bkash"

    cash = db_session.query(CashMovement).filter_by(source_id=pay.id).first()
    assert cash is not None
    assert cash.amount_minor == 800000


def test_discount_campaign_margin_guardrail(test_client, seeded_shop_context, db_session):
    """Tests discount campaign margin protection rejects excessive discounts unless explicitly confirmed."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    # Seed product with 20% margin: cost 800, selling 1000
    prod = Product(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        sku="TEST-SKU-MARGIN",
        name="Test Margin Shirt",
        category="Apparel",
        cost_price_minor=80000,
        selling_price_minor=100000,
        current_stock=50,
        min_stock_alert=10,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()

    # Attempt to create campaign with 30% discount without confirmation -> must fail
    res_fail = test_client.post(
        "/api/crm/campaigns",
        json={
            "shop_id": shop1.id,
            "title": "Aggressive Discount",
            "target_segment": "VIP",
            "discount_type": "percentage",
            "discount_value": 30.0,
            "channel": "whatsapp",
            "message_template": "Hello {name}, enjoy {discount} at {shop_name}!",
            "confirm_low_margin": False,
        },
        headers=headers,
    )
    assert res_fail.status_code == 400
    assert "margin" in res_fail.text.lower()

    # Create with confirm_low_margin=True -> succeeds
    res_ok = test_client.post(
        "/api/crm/campaigns",
        json={
            "shop_id": shop1.id,
            "title": "Authorized Clearance",
            "target_segment": "VIP",
            "discount_type": "percentage",
            "discount_value": 30.0,
            "channel": "whatsapp",
            "message_template": "Hello {name}, enjoy {discount} at {shop_name}!",
            "confirm_low_margin": True,
        },
        headers=headers,
    )
    assert res_ok.status_code == 201
    assert res_ok.json()["status"] == "success"


def test_inventory_product_crud_and_valuation(test_client, seeded_shop_context, db_session):
    """Tests creating product SKU, weighted valuation, and duplicate SKU rejection."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "shop_id": shop1.id,
        "sku": "SKU-TEST-001",
        "barcode": "8941001",
        "name": "Cotton Fabric Roll",
        "category": "Textiles",
        "unit_of_measure": "rolls",
        "cost_price_minor": 150000,    # 1,500 BDT
        "selling_price_minor": 220000, # 2,200 BDT
        "current_stock": 25,
        "min_stock_alert": 10,
    }

    res = test_client.post("/api/inventory/products", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    prod_id = data["product"]["id"]

    # Verify inventory movement for opening balance
    mov = db_session.query(InventoryMovement).filter_by(product_id=prod_id).first()
    assert mov is not None
    assert mov.movement_type == "opening_balance"
    assert mov.quantity_change == 25

    # Check duplicate SKU rejection
    dup_res = test_client.post("/api/inventory/products", json=payload, headers=headers)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]


def test_stock_adjustment_and_negative_stock_guard(test_client, seeded_shop_context, db_session):
    """Tests stock adjustment with cost impact and prevents negative stock balances."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    prod = Product(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        sku="SKU-ADJ-TEST",
        name="Ceramic Vase",
        category="Home",
        cost_price_minor=50000,
        selling_price_minor=80000,
        current_stock=10,
        min_stock_alert=5,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()

    # Attempt to deduct 15 units when only 10 available -> must fail
    res_neg = test_client.post(
        "/api/inventory/stock-adjustment",
        json={
            "shop_id": shop1.id,
            "product_id": prod.id,
            "reason": "breakage",
            "quantity_adjusted": -15,
        },
        headers=headers,
    )
    assert res_neg.status_code == 400
    assert "negative stock" in res_neg.json()["detail"].lower()

    # Deduct 2 units due to breakage -> succeeds
    res_ok = test_client.post(
        "/api/inventory/stock-adjustment",
        json={
            "shop_id": shop1.id,
            "product_id": prod.id,
            "reason": "breakage",
            "quantity_adjusted": -2,
            "notes": "Dropped during shelf display",
        },
        headers=headers,
    )
    assert res_ok.status_code == 201
    assert res_ok.json()["new_stock"] == 8

    # Verify StockAdjustment record
    adj = db_session.query(StockAdjustment).filter_by(product_id=prod.id).first()
    assert adj is not None
    assert adj.quantity_adjusted == -2
    assert adj.cost_impact_minor == 100000  # 2 * 50,000


def test_auto_draft_purchase_orders_and_receipt(test_client, seeded_shop_context, db_session):
    """Tests auto-drafting replenishment purchase orders for low-stock SKUs and receiving goods."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    # Create low-stock product: stock 3 <= min_alert 10
    prod = Product(
        business_id=shop1.business_id,
        shop_id=shop1.id,
        sku="SKU-LOW-REORDER",
        name="Safety Reorder Item",
        category="Hardware",
        cost_price_minor=10000,
        selling_price_minor=15000,
        current_stock=3,
        min_stock_alert=10,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()

    # Trigger auto-draft
    res_draft = test_client.post(
        "/api/inventory/reorder/auto-draft",
        json={"shop_id": shop1.id},
        headers=headers,
    )
    assert res_draft.status_code == 201
    draft_data = res_draft.json()
    assert draft_data["status"] == "success"
    po_data = draft_data["purchase_order"]
    assert po_data is not None
    assert po_data["items_count"] >= 1
    po_id = po_data["id"]

    # Verify PO in DB
    po = db_session.get(PurchaseOrder, po_id)
    assert po.status == "draft"

    # Receive the purchase order
    res_receive = test_client.post(
        f"/api/inventory/purchase-orders/{po_id}/receive?shop_id={shop1.id}",
        headers=headers,
    )
    assert res_receive.status_code == 200
    assert res_receive.json()["status"] == "success"

    # Verify stock increased and PO marked received
    db_session.refresh(po)
    db_session.refresh(prod)
    assert po.status == "received"
    assert prod.current_stock > 3  # Stock replenished!


def test_multi_tenant_shop_isolation_crm_and_inventory(test_client, seeded_shop_context):
    """Verifies user of Shop 1 cannot access or modify Shop 2 customer or inventory resources."""
    user1 = seeded_shop_context["user1"]
    shop2 = seeded_shop_context["shop2"]
    token1 = create_token(user1.id, settings.SECRET_KEY)
    headers1 = {"Authorization": f"Bearer {token1}"}

    # User 1 attempting to view Shop 2 customers -> 403 Forbidden
    res_crm = test_client.get(f"/api/crm/customers?shop_id={shop2.id}", headers=headers1)
    assert res_crm.status_code == 403

    # User 1 attempting to view Shop 2 inventory -> 403 Forbidden
    res_inv = test_client.get(f"/api/inventory/products?shop_id={shop2.id}", headers=headers1)
    assert res_inv.status_code == 403
