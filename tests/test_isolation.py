"""
Security Tests: Multi-Tenant Shop Isolation and Authorization Denial.
Proves that cross-shop access is denied and products/sales cannot cross shop boundaries.
"""

import pytest
from src.core.exceptions import ShopAccessDeniedError
from src.core.security import enforce_shop_isolation
from src.database.models import Product, Sale, SaleItem, Customer
from src.database.repository import SaleRepository, ProductRepository


def test_shop_isolation_membership_denial(seeded_shop_context):
    """Proves that a user without membership in Shop 2 is rejected."""
    user1 = seeded_shop_context["user1"]
    shop2 = seeded_shop_context["shop2"]

    # user1 only has membership in shop1
    user1_memberships = [
        {"user_id": user1.id, "business_id": seeded_shop_context["business1"].id, "shop_id": seeded_shop_context["shop1"].id, "role_code": "owner"}
    ]

    # Attempting to access shop2 must raise ShopAccessDeniedError
    with pytest.raises(ShopAccessDeniedError) as exc_info:
        enforce_shop_isolation(user1.id, shop2.id, user1_memberships)

    assert "Security Alert" in str(exc_info.value)
    assert f"shop {shop2.id}" in str(exc_info.value)


def test_cross_shop_inventory_posting_rejected(db_session, seeded_shop_context):
    """
    Proves that a transaction in Shop 1 cannot deduct inventory from a product belonging to Shop 2.
    """
    s1 = seeded_shop_context["shop1"]
    s2 = seeded_shop_context["shop2"]

    # Create product in Shop 2
    prod2 = Product(
        business_id=s2.business_id,
        shop_id=s2.id,
        sku="SKU-PROD-2",
        name="Shop 2 Secret Product",
        category="general",
        cost_price_minor=10000,
        selling_price_minor=15000,
        current_stock=50,
    )
    db_session.add(prod2)
    db_session.flush()

    sale_repo = SaleRepository(db_session)

    sale_data = {
        "business_id": s1.business_id,
        "shop_id": s1.id,
        "invoice_number": "INV-ISOLATION-TEST",
        "subtotal_minor": 15000,
        "total_amount_minor": 15000,
        "paid_amount_minor": 15000,
        "payment_status": "paid",
        "payment_method": "cash",
    }
    # Malicious or buggy payload attempting to consume Shop 2's product
    items_data = [
        {
            "product_id": prod2.id,
            "item_description": "Shop 2 Product in Shop 1 Sale",
            "quantity": 1,
            "unit_price_minor": 15000,
            "discount_minor": 0,
            "line_total_minor": 15000,
        }
    ]

    with pytest.raises(ShopAccessDeniedError) as exc_info:
        sale_repo.create_sale_with_items(sale_data, items_data, update_inventory=True)

    assert "Product does not belong to the sale shop" in str(exc_info.value)
