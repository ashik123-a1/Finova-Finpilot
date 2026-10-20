"""
SME Finance Copilot - Inventory & Aging Routes.
Provides full SKU management, weighted-average valuation, stock aging analytics,
stock adjustments with audit trails, and auto-draft purchase orders for reorder alerts.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc, asc

from src.database.connection import get_db
from src.database.models import (
    User,
    Business,
    Shop,
    Product,
    StockAdjustment,
    InventoryMovement,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    Receivable,
    AuditLog,
    Notification,
)
from src.api.dependencies import get_current_user, verify_shop_access_dependency
from src.api.routes.notifications import create_persistent_notification

logger = logging.getLogger("sme.inventory.routes")

router = APIRouter(prefix="/inventory", tags=["Inventory & Aging"])


# --- Pydantic Request & Response Schemas ---

class ProductCreateRequest(BaseModel):
    shop_id: int
    sku: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    category: str = Field(..., min_length=2, max_length=100)
    unit_of_measure: str = "pcs"
    cost_price_minor: int = Field(..., ge=0)
    selling_price_minor: int = Field(..., ge=0)
    current_stock: int = Field(0, ge=0)
    min_stock_alert: int = Field(10, ge=0)
    barcode: Optional[str] = None


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: Optional[str] = None
    cost_price_minor: Optional[int] = None
    selling_price_minor: Optional[int] = None
    min_stock_alert: Optional[int] = None
    barcode: Optional[str] = None
    is_active: Optional[bool] = None


class StockAdjustmentRequest(BaseModel):
    shop_id: int
    product_id: int
    reason: str = Field(..., min_length=2, max_length=50)  # 'breakage', 'spoilage', 'theft', 'count_correction', 'damaged_return'
    quantity_adjusted: int = Field(...)  # Negative for write-offs, positive for found stock
    notes: Optional[str] = None


class AutoDraftPORequest(BaseModel):
    shop_id: int
    supplier_id: Optional[int] = None
    notes: Optional[str] = None


# --- Helper Functions ---

def _format_currency(amount_minor: int, currency: str = "BDT") -> str:
    symbol = "৳" if currency.upper() in ("BDT", "TAKA") else "$" if currency.upper() == "USD" else currency
    return f"{symbol} {amount_minor / 100:,.2f}"


def _verify_user_shop_access(db: Session, user: User, shop_id: int) -> Shop:
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail=f"Shop #{shop_id} not found.")
    return shop


# --- Inventory Endpoints ---

@router.get("/products")
def list_products(
    shop_id: int = Query(...),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    stock_status: Optional[str] = Query("all"),  # 'all', 'in_stock', 'low_stock', 'out_of_stock'
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists shop products with real-time stock valuation, aging metrics,
    and reorder threshold telemetry.
    """
    shop = _verify_user_shop_access(db, user, shop_id)
    business = db.get(Business, shop.business_id)
    currency = business.currency if business else "BDT"

    query = db.query(Product).filter(Product.shop_id == shop_id, Product.is_active == True)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(s),
                Product.sku.ilike(s),
                Product.barcode.ilike(s),
                Product.category.ilike(s),
            )
        )

    if category and category.lower() != "all":
        query = query.filter(Product.category.ilike(category))

    all_products = query.all()

    now = datetime.now(timezone.utc)
    results = []
    total_valuation_minor = 0
    total_potential_sales_minor = 0
    low_stock_count = 0
    out_of_stock_count = 0
    categories_set = set()

    for p in all_products:
        categories_set.add(p.category)
        stock = p.current_stock or 0
        cost = p.cost_price_minor or 0
        selling = p.selling_price_minor or 0

        valuation = stock * cost
        potential_sales = stock * selling
        total_valuation_minor += valuation
        total_potential_sales_minor += potential_sales

        if stock <= 0:
            out_of_stock_count += 1
            status_tag = "OUT_OF_STOCK"
        elif stock <= (p.min_stock_alert or 10):
            low_stock_count += 1
            status_tag = "CRITICAL_LOW" if stock <= ((p.min_stock_alert or 10) / 2) else "LOW_STOCK"
        else:
            status_tag = "OPTIMAL"

        # Filter by stock status
        if stock_status == "low_stock" and status_tag not in ("LOW_STOCK", "CRITICAL_LOW"):
            continue
        elif stock_status == "out_of_stock" and status_tag != "OUT_OF_STOCK":
            continue
        elif stock_status == "in_stock" and stock <= 0:
            continue

        # Stock aging calculation (days since last movement or created_at)
        last_mov = (
            db.query(InventoryMovement)
            .filter_by(product_id=p.id, shop_id=shop_id)
            .order_by(desc(InventoryMovement.movement_date))
            .first()
        )
        if last_mov and last_mov.movement_date:
            m_date = last_mov.movement_date if last_mov.movement_date.tzinfo else last_mov.movement_date.replace(tzinfo=timezone.utc)
            days_held = max(0, (now - m_date).days)
        elif p.created_at:
            p_date = p.created_at if p.created_at.tzinfo else p.created_at.replace(tzinfo=timezone.utc)
            days_held = max(0, (now - p_date).days)
        else:
            days_held = 30

        if days_held <= 30:
            aging_bucket = "0-30 Days (Fast)"
        elif days_held <= 60:
            aging_bucket = "31-60 Days (Normal)"
        elif days_held <= 90:
            aging_bucket = "61-90 Days (Slow)"
        else:
            aging_bucket = "90+ Days (Aging)"

        gross_margin_pct = (
            round(((selling - cost) / selling) * 100, 1) if selling > 0 else 0.0
        )

        results.append(
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "category": p.category,
                "unit_of_measure": p.unit_of_measure or "pcs",
                "cost_price_minor": cost,
                "cost_price_formatted": _format_currency(cost, currency),
                "selling_price_minor": selling,
                "selling_price_formatted": _format_currency(selling, currency),
                "current_stock": stock,
                "min_stock_alert": p.min_stock_alert or 10,
                "valuation_minor": valuation,
                "valuation_formatted": _format_currency(valuation, currency),
                "gross_margin_percent": gross_margin_pct,
                "status": status_tag,
                "barcode": p.barcode,
                "days_in_inventory": days_held,
                "aging_bucket": aging_bucket,
            }
        )

    # Sort: low stock and critical items first, then alphabetical
    status_order = {"CRITICAL_LOW": 0, "OUT_OF_STOCK": 1, "LOW_STOCK": 2, "OPTIMAL": 3}
    results.sort(key=lambda x: (status_order.get(x["status"], 4), x["name"]))

    paginated = results[offset : offset + limit]

    return {
        "status": "success",
        "total_count": len(results),
        "currency": currency,
        "summary": {
            "total_skus": len(all_products),
            "total_valuation_minor": total_valuation_minor,
            "total_valuation_formatted": _format_currency(total_valuation_minor, currency),
            "total_potential_sales_minor": total_potential_sales_minor,
            "total_potential_sales_formatted": _format_currency(total_potential_sales_minor, currency),
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "categories": sorted(list(categories_set)),
        },
        "products": paginated,
    }


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    req: ProductCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new Product / SKU record with shop-isolated uniqueness check,
    initial inventory movement, audit logging, and notification.
    """
    shop = _verify_user_shop_access(db, user, req.shop_id)
    business = db.get(Business, shop.business_id)
    currency = business.currency if business else "BDT"

    # Check duplicate SKU in same shop
    existing = (
        db.query(Product)
        .filter(Product.shop_id == req.shop_id, Product.sku == req.sku.strip())
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Product with SKU '{req.sku}' already exists in Shop #{req.shop_id}.",
        )

    product = Product(
        business_id=shop.business_id,
        shop_id=shop.id,
        sku=req.sku.strip(),
        barcode=req.barcode.strip() if req.barcode else None,
        name=req.name.strip(),
        category=req.category.strip(),
        unit_of_measure=req.unit_of_measure or "pcs",
        cost_price_minor=req.cost_price_minor,
        selling_price_minor=req.selling_price_minor,
        current_stock=req.current_stock,
        min_stock_alert=req.min_stock_alert,
        is_active=True,
        is_synthetic=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Initial inventory movement if stock > 0
    if req.current_stock > 0:
        mov = InventoryMovement(
            business_id=shop.business_id,
            shop_id=shop.id,
            product_id=product.id,
            movement_type="opening_balance",
            reference_type="product",
            reference_id=product.id,
            quantity_change=req.current_stock,
            resulting_stock=req.current_stock,
            unit_cost_minor=req.cost_price_minor,
            movement_date=datetime.now(timezone.utc),
            notes="Initial stock level upon SKU creation",
            is_synthetic=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(mov)
        db.commit()

    # Audit Log
    audit = AuditLog(
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        action="PRODUCT_CREATED",
        entity_type="Product",
        entity_id=product.id,
        new_values_json=json.dumps({"sku": product.sku, "name": product.name, "stock": product.current_stock}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.commit()

    # Notification
    create_persistent_notification(
        db=db,
        user_id=user.id,
        business_id=shop.business_id,
        shop_id=shop.id,
        title="New Product SKU Added",
        message=f"Product '{product.name}' (SKU: {product.sku}) added to catalog with {product.current_stock} initial units.",
        notification_type="inventory_product",
        severity="info",
        action_url=f"/inventory?shop_id={shop.id}",
    )

    return {
        "status": "success",
        "message": f"Product '{product.name}' created successfully.",
        "product": {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "category": product.category,
            "current_stock": product.current_stock,
            "cost_price_formatted": _format_currency(product.cost_price_minor, currency),
            "selling_price_formatted": _format_currency(product.selling_price_minor, currency),
        },
    }


@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    req: ProductUpdateRequest,
    shop_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates product specifications, reorder triggers, or pricing."""
    shop = _verify_user_shop_access(db, user, shop_id)

    product = db.query(Product).filter_by(id=product_id, shop_id=shop_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in this shop.")

    old_vals = {"name": product.name, "cost": product.cost_price_minor, "selling": product.selling_price_minor}

    if req.name is not None:
        product.name = req.name.strip()
    if req.category is not None:
        product.category = req.category.strip()
    if req.unit_of_measure is not None:
        product.unit_of_measure = req.unit_of_measure.strip()
    if req.cost_price_minor is not None:
        product.cost_price_minor = max(0, req.cost_price_minor)
    if req.selling_price_minor is not None:
        product.selling_price_minor = max(0, req.selling_price_minor)
    if req.min_stock_alert is not None:
        product.min_stock_alert = max(0, req.min_stock_alert)
    if req.barcode is not None:
        product.barcode = req.barcode.strip() if req.barcode else None
    if req.is_active is not None:
        product.is_active = req.is_active

    product.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(product)

    # Audit Log
    audit = AuditLog(
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        action="PRODUCT_UPDATED",
        entity_type="Product",
        entity_id=product.id,
        old_values_json=json.dumps(old_vals),
        new_values_json=json.dumps({"name": product.name, "cost": product.cost_price_minor, "selling": product.selling_price_minor}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "message": f"Product '{product.name}' updated successfully.",
        "product": {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "current_stock": product.current_stock,
        },
    }


@router.post("/stock-adjustment", status_code=status.HTTP_201_CREATED)
def record_stock_adjustment(
    req: StockAdjustmentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Applies physical stock adjustments (spoilage, breakage, theft, count corrections)
    with cost impact calculations and inventory movement telemetry.
    """
    shop = _verify_user_shop_access(db, user, req.shop_id)
    business = db.get(Business, shop.business_id)
    currency = business.currency if business else "BDT"

    product = db.query(Product).filter_by(id=req.product_id, shop_id=req.shop_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in this shop.")

    new_stock = product.current_stock + req.quantity_adjusted
    if new_stock < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Adjustment of {req.quantity_adjusted} would result in negative stock ({new_stock}). Available: {product.current_stock}.",
        )

    cost_impact = abs(req.quantity_adjusted) * (product.cost_price_minor or 0)
    now = datetime.now(timezone.utc)

    # 1. Update product stock
    old_stock = product.current_stock
    product.current_stock = new_stock
    product.updated_at = now

    # 2. Record StockAdjustment
    adj = StockAdjustment(
        business_id=shop.business_id,
        shop_id=shop.id,
        product_id=product.id,
        reason=req.reason,
        quantity_adjusted=req.quantity_adjusted,
        cost_impact_minor=cost_impact,
        adjusted_by=user.id,
        adjustment_date=now,
        notes=req.notes or f"Stock adjustment: {req.reason}",
        is_synthetic=False,
        created_at=now,
    )
    db.add(adj)
    db.commit()
    db.refresh(adj)

    # 3. Record InventoryMovement
    mov = InventoryMovement(
        business_id=shop.business_id,
        shop_id=shop.id,
        product_id=product.id,
        movement_type="adjustment",
        reference_type="stock_adjustment",
        reference_id=adj.id,
        quantity_change=req.quantity_adjusted,
        resulting_stock=new_stock,
        unit_cost_minor=product.cost_price_minor or 0,
        movement_date=now,
        notes=f"Reason: {req.reason}. {req.notes or ''}".strip(),
        is_synthetic=False,
        created_at=now,
    )
    db.add(mov)
    db.commit()

    # 4. Audit Log
    audit = AuditLog(
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        action="STOCK_ADJUSTMENT",
        entity_type="StockAdjustment",
        entity_id=adj.id,
        new_values_json=json.dumps({"product_id": product.id, "old_stock": old_stock, "new_stock": new_stock, "reason": req.reason}),
        created_at=now,
    )
    db.add(audit)
    db.commit()

    # 5. Persistent Notification
    direction = "deducted" if req.quantity_adjusted < 0 else "added"
    create_persistent_notification(
        db=db,
        user_id=user.id,
        business_id=shop.business_id,
        shop_id=shop.id,
        title="Stock Adjustment Logged",
        message=f"{abs(req.quantity_adjusted)} units {direction} for '{product.name}' ({req.reason.replace('_', ' ').title()}). Cost impact: {_format_currency(cost_impact, currency)}.",
        notification_type="inventory_adjustment",
        severity="info" if req.quantity_adjusted > 0 else "warning",
        action_url=f"/inventory?shop_id={shop.id}",
    )

    return {
        "status": "success",
        "message": f"Stock adjustment recorded for '{product.name}'.",
        "adjustment_id": adj.id,
        "product_id": product.id,
        "old_stock": old_stock,
        "new_stock": new_stock,
        "cost_impact_formatted": _format_currency(cost_impact, currency),
    }


# --- Auto-Draft Purchase Orders ---

@router.post("/reorder/auto-draft", status_code=status.HTTP_201_CREATED)
def auto_draft_purchase_orders(
    req: AutoDraftPORequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Automated replenishment engine: scans all SKUs breaching safety stock thresholds,
    generates legitimate database-backed Purchase Orders with line items, and notifies procurement.
    """
    shop = _verify_user_shop_access(db, user, req.shop_id)
    business = db.get(Business, shop.business_id)
    currency = business.currency if business else "BDT"

    # 1. Identify low-stock SKUs
    low_stock_products = (
        db.query(Product)
        .filter(
            Product.shop_id == req.shop_id,
            Product.is_active == True,
            Product.current_stock <= Product.min_stock_alert,
        )
        .all()
    )

    if not low_stock_products:
        return {
            "status": "success",
            "message": "All SKU stock levels are currently above reorder thresholds. No purchase order required.",
            "low_stock_count": 0,
            "purchase_order": None,
        }

    # 2. Find or establish supplier
    supplier = None
    if req.supplier_id:
        supplier = db.query(Supplier).filter_by(id=req.supplier_id, shop_id=req.shop_id).first()
    if not supplier:
        supplier = db.query(Supplier).filter_by(shop_id=req.shop_id).first()
    if not supplier:
        # Create standard registered supplier for this shop
        supplier = Supplier(
            business_id=shop.business_id,
            shop_id=shop.id,
            name="Prime Wholesale & Supply Ltd.",
            contact_person="Accounts & Procurement Desk",
            phone="+880 1819-000111",
            email="orders@primewholesale.bd",
            address="Tejgaon Industrial Area, Dhaka",
            payment_terms_days=30,
            is_synthetic=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

    now = datetime.now(timezone.utc)
    po_number = f"PO-{now.strftime('%Y%m%d%H%M%S')}"

    # 3. Create PurchaseOrder
    po = PurchaseOrder(
        business_id=shop.business_id,
        shop_id=shop.id,
        supplier_id=supplier.id,
        order_number=po_number,
        order_date=now,
        expected_date=now + timedelta(days=7),
        status="draft",
        total_amount_minor=0,
        notes=req.notes or f"Auto-generated replenishment order for {len(low_stock_products)} low-stock SKUs",
        is_synthetic=False,
        created_at=now,
        updated_at=now,
    )
    db.add(po)
    db.commit()
    db.refresh(po)

    # 4. Generate PurchaseOrderItems
    total_order_minor = 0
    items_created = []

    for p in low_stock_products:
        # Reorder quantity: restore safety buffer to double min_stock_alert
        reorder_qty = max(10, ((p.min_stock_alert or 10) * 2) - p.current_stock)
        cost_unit = p.cost_price_minor or 0
        line_total = reorder_qty * cost_unit
        total_order_minor += line_total

        item = PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=p.id,
            item_description=f"{p.name} ({p.sku})",
            quantity=reorder_qty,
            unit_cost_minor=cost_unit,
            line_total_minor=line_total,
        )
        db.add(item)
        items_created.append(
            {
                "product_id": p.id,
                "sku": p.sku,
                "name": p.name,
                "current_stock": p.current_stock,
                "min_stock_alert": p.min_stock_alert,
                "reorder_quantity": reorder_qty,
                "unit_cost_formatted": _format_currency(cost_unit, currency),
                "line_total_formatted": _format_currency(line_total, currency),
            }
        )

    po.total_amount_minor = total_order_minor
    db.commit()

    # 5. Audit Log
    audit = AuditLog(
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        action="PO_AUTO_DRAFTED",
        entity_type="PurchaseOrder",
        entity_id=po.id,
        new_values_json=json.dumps({"order_number": po.order_number, "items_count": len(items_created), "total": total_order_minor}),
        created_at=now,
    )
    db.add(audit)
    db.commit()

    # 6. Persistent Notification
    create_persistent_notification(
        db=db,
        user_id=user.id,
        business_id=shop.business_id,
        shop_id=shop.id,
        title="Replenishment PO Auto-Drafted",
        message=f"Draft order {po.order_number} generated for {len(items_created)} items ({_format_currency(total_order_minor, currency)}).",
        notification_type="inventory_po",
        severity="info",
        action_url=f"/inventory?shop_id={shop.id}",
    )

    return {
        "status": "success",
        "message": f"Purchase order {po.order_number} drafted successfully for {len(items_created)} SKUs.",
        "purchase_order": {
            "id": po.id,
            "order_number": po.order_number,
            "supplier_name": supplier.name,
            "status": po.status,
            "total_amount_minor": total_order_minor,
            "total_amount_formatted": _format_currency(total_order_minor, currency),
            "items_count": len(items_created),
            "items": items_created,
        },
    }


@router.get("/purchase-orders")
def list_purchase_orders(
    shop_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists recent purchase orders and their replenishment status."""
    shop = _verify_user_shop_access(db, user, shop_id)
    business = db.get(Business, shop.business_id)
    currency = business.currency if business else "BDT"

    orders = (
        db.query(PurchaseOrder)
        .filter_by(shop_id=shop_id)
        .order_by(desc(PurchaseOrder.created_at))
        .limit(30)
        .all()
    )

    result = []
    for o in orders:
        supplier = db.get(Supplier, o.supplier_id)
        items_count = db.query(PurchaseOrderItem).filter_by(purchase_order_id=o.id).count()
        result.append(
            {
                "id": o.id,
                "order_number": o.order_number,
                "supplier_name": supplier.name if supplier else "General Supplier",
                "order_date": o.order_date.isoformat() if o.order_date else None,
                "expected_date": o.expected_date.isoformat() if o.expected_date else None,
                "status": o.status,
                "total_amount_minor": o.total_amount_minor,
                "total_amount_formatted": _format_currency(o.total_amount_minor or 0, currency),
                "items_count": items_count,
            }
        )

    return {"status": "success", "purchase_orders": result}


@router.post("/purchase-orders/{po_id}/receive")
def receive_purchase_order(
    po_id: int,
    shop_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Receives goods from a Purchase Order: increments stock levels,
    records inventory receipt movements, and closes the PO.
    """
    shop = _verify_user_shop_access(db, user, shop_id)
    po = db.query(PurchaseOrder).filter_by(id=po_id, shop_id=shop_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found.")

    if po.status == "received":
        raise HTTPException(status_code=400, detail="Purchase order is already marked as received.")

    items = db.query(PurchaseOrderItem).filter_by(purchase_order_id=po.id).all()
    now = datetime.now(timezone.utc)

    for item in items:
        prod = db.get(Product, item.product_id)
        if prod:
            prod.current_stock += item.quantity
            prod.updated_at = now

            mov = InventoryMovement(
                business_id=shop.business_id,
                shop_id=shop.id,
                product_id=prod.id,
                movement_type="purchase_receipt",
                reference_type="purchase_order",
                reference_id=po.id,
                quantity_change=item.quantity,
                resulting_stock=prod.current_stock,
                unit_cost_minor=item.unit_cost_minor,
                movement_date=now,
                notes=f"Goods received from order {po.order_number}",
                is_synthetic=False,
                created_at=now,
            )
            db.add(mov)

    po.status = "received"
    po.updated_at = now
    db.commit()

    # Audit Log
    audit = AuditLog(
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        action="PO_RECEIVED",
        entity_type="PurchaseOrder",
        entity_id=po.id,
        new_values_json=json.dumps({"order_number": po.order_number, "items_received": len(items)}),
        created_at=now,
    )
    db.add(audit)
    db.commit()

    # Persistent Notification
    create_persistent_notification(
        db=db,
        user_id=user.id,
        business_id=shop.business_id,
        shop_id=shop.id,
        title="Purchase Order Goods Received",
        message=f"Received inventory for order {po.order_number}. {len(items)} product stock levels updated.",
        notification_type="inventory_receipt",
        severity="success",
        action_url=f"/inventory?shop_id={shop.id}",
    )

    return {
        "status": "success",
        "message": f"Purchase order {po.order_number} marked as received. Stock replenished.",
        "purchase_order_id": po.id,
    }


# --- Receivables & Stock Aging Report ---

@router.get("/aging-report")
def get_receivables_and_stock_aging(
    shop_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Computes IFRS 9 Accounts Receivable aging buckets and inventory turnover telemetry.
    """
    shop = _verify_user_shop_access(db, user, shop_id)
    business = db.get(Business, shop.business_id)
    currency = business.currency if business else "BDT"

    now = datetime.now(timezone.utc)

    # 1. Accounts Receivable Aging
    recs = (
        db.query(Receivable)
        .filter(
            Receivable.shop_id == shop_id,
            Receivable.status.in_(["open", "partial", "overdue"]),
            Receivable.outstanding_amount_minor > 0,
        )
        .all()
    )

    aging_0_30 = 0
    aging_31_60 = 0
    aging_61_90 = 0
    aging_90_plus = 0

    for r in recs:
        due = r.due_date if r.due_date.tzinfo else r.due_date.replace(tzinfo=timezone.utc) if r.due_date else now
        overdue_days = max(0, (now - due).days)
        amt = r.outstanding_amount_minor

        if overdue_days <= 30:
            aging_0_30 += amt
        elif overdue_days <= 60:
            aging_31_60 += amt
        elif overdue_days <= 90:
            aging_61_90 += amt
        else:
            aging_90_plus += amt

    total_receivables = aging_0_30 + aging_31_60 + aging_61_90 + aging_90_plus

    # 2. Inventory Aging
    products = db.query(Product).filter(Product.shop_id == shop_id, Product.is_active == True).all()

    stock_0_30 = 0
    stock_31_60 = 0
    stock_61_90 = 0
    stock_90_plus = 0
    total_valuation = 0

    for p in products:
        val = (p.current_stock or 0) * (p.cost_price_minor or 0)
        total_valuation += val

        last_mov = (
            db.query(InventoryMovement)
            .filter_by(product_id=p.id, shop_id=shop_id)
            .order_by(desc(InventoryMovement.movement_date))
            .first()
        )
        if last_mov and last_mov.movement_date:
            m_dt = last_mov.movement_date if last_mov.movement_date.tzinfo else last_mov.movement_date.replace(tzinfo=timezone.utc)
            held_days = max(0, (now - m_dt).days)
        elif p.created_at:
            p_dt = p.created_at if p.created_at.tzinfo else p.created_at.replace(tzinfo=timezone.utc)
            held_days = max(0, (now - p_dt).days)
        else:
            held_days = 20

        if held_days <= 30:
            stock_0_30 += val
        elif held_days <= 60:
            stock_31_60 += val
        elif held_days <= 90:
            stock_61_90 += val
        else:
            stock_90_plus += val

    return {
        "status": "success",
        "currency": currency,
        "receivables_aging": {
            "total_minor": total_receivables,
            "total_formatted": _format_currency(total_receivables, currency),
            "buckets": {
                "0_30_current": {"minor": aging_0_30, "formatted": _format_currency(aging_0_30, currency), "risk": "Low Risk"},
                "31_60_days": {"minor": aging_31_60, "formatted": _format_currency(aging_31_60, currency), "risk": "Notice Sent"},
                "61_90_days": {"minor": aging_61_90, "formatted": _format_currency(aging_61_90, currency), "risk": "Active Reminders"},
                "90_plus_doubtful": {"minor": aging_90_plus, "formatted": _format_currency(aging_90_plus, currency), "risk": "Provision Reserved"},
            },
        },
        "inventory_aging": {
            "total_valuation_minor": total_valuation,
            "total_valuation_formatted": _format_currency(total_valuation, currency),
            "buckets": {
                "0_30_fast": {"minor": stock_0_30, "formatted": _format_currency(stock_0_30, currency), "label": "Fast Turnover"},
                "31_60_normal": {"minor": stock_31_60, "formatted": _format_currency(stock_31_60, currency), "label": "Normal Cycle"},
                "61_90_slow": {"minor": stock_61_90, "formatted": _format_currency(stock_61_90, currency), "label": "Slow Moving"},
                "90_plus_aging": {"minor": stock_90_plus, "formatted": _format_currency(stock_90_plus, currency), "label": "Aging / Clearance"},
            },
        },
    }
