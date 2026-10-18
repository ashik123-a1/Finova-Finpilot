"""
SQLAlchemy Declarative Models for SME Finance Copilot.
All financial amounts are stored as integer minor units (BigInteger) to prevent floating-point errors.
All timestamps are stored in UTC.
Multi-tenant isolation is supported via business_id and shop_id on all operational entities.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    Float,
)
from sqlalchemy.orm import relationship

from src.database.connection import Base


def utc_now() -> datetime:
    """Returns current datetime in UTC timezone."""
    return datetime.now(timezone.utc)


# ==============================================================================
# 1. Identity & Business Structure
# ==============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    memberships = relationship("BusinessMembership", back_populates="user", cascade="all, delete-orphan")


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    registration_number = Column(String(100), nullable=True)
    tax_id = Column(String(100), nullable=True)
    business_type = Column(String(100), nullable=False, default="grocery")  # e.g., grocery, retail, restaurant, pharmacy
    currency = Column(String(10), nullable=False, default="BDT")
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    shops = relationship("Shop", back_populates="business", cascade="all, delete-orphan")
    memberships = relationship("BusinessMembership", back_populates="business", cascade="all, delete-orphan")


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    branch_code = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    business = relationship("Business", back_populates="shops")
    memberships = relationship("BusinessMembership", back_populates="shop")

    __table_args__ = (
        Index("idx_shops_business_active", "business_id", "is_active"),
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)  # owner, manager, accountant, staff
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)


class BusinessMembership(Base):
    __tablename__ = "business_memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=True, index=True)  # Null if enterprise-wide
    role_code = Column(String(50), nullable=False, default="staff")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="memberships")
    business = relationship("Business", back_populates="memberships")
    shop = relationship("Shop", back_populates="memberships")

    __table_args__ = (
        Index("idx_membership_user_business_shop", "user_id", "business_id", "shop_id"),
    )


# ==============================================================================
# 2. Suppliers and Customers
# ==============================================================================

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    payment_terms_days = Column(Integer, default=30, nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_suppliers_shop_name", "shop_id", "name"),
    )


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    credit_limit_minor = Column(BigInteger, default=0, nullable=False)
    balance_minor = Column(BigInteger, default=0, nullable=False)  # Positive means customer owes shop
    segment = Column(String(50), default="regular", nullable=False)  # VIP, Regular, Occasional, Inactive
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_customers_shop_phone", "shop_id", "phone"),
    )


# ==============================================================================
# 3. Products and Inventory
# ==============================================================================

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False)
    barcode = Column(String(100), nullable=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    unit_of_measure = Column(String(20), default="pcs", nullable=False)
    cost_price_minor = Column(BigInteger, nullable=False)
    selling_price_minor = Column(BigInteger, nullable=False)
    current_stock = Column(Integer, default=0, nullable=False)
    min_stock_alert = Column(Integer, default=5, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    inventory_movements = relationship("InventoryMovement", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_products_shop_sku", "shop_id", "sku", unique=True),
        Index("idx_products_shop_category", "shop_id", "category"),
    )


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_number = Column(String(100), nullable=False)
    order_date = Column(DateTime, default=utc_now, nullable=False)
    expected_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="draft", nullable=False)  # draft, sent, received, cancelled
    total_amount_minor = Column(BigInteger, default=0, nullable=False)
    notes = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    movement_type = Column(String(50), nullable=False)  # purchase_receipt, sale_delivery, stock_adjustment, transfer_in, transfer_out
    reference_type = Column(String(50), nullable=True)  # sale, purchase, stock_adjustment
    reference_id = Column(Integer, nullable=True)
    quantity_change = Column(Integer, nullable=False)  # positive for receipt, negative for issue
    resulting_stock = Column(Integer, nullable=False)
    unit_cost_minor = Column(BigInteger, nullable=False)
    movement_date = Column(DateTime, default=utc_now, nullable=False)
    notes = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    product = relationship("Product", back_populates="inventory_movements")

    __table_args__ = (
        Index("idx_inv_movements_shop_product_date", "shop_id", "product_id", "movement_date"),
    )


class StockAdjustment(Base):
    __tablename__ = "stock_adjustments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(50), nullable=False)  # breakage, spoilage, theft, count_correction
    quantity_adjusted = Column(Integer, nullable=False)
    cost_impact_minor = Column(BigInteger, default=0, nullable=False)
    adjusted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    adjustment_date = Column(DateTime, default=utc_now, nullable=False)
    notes = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


# ==============================================================================
# 4. Financial Records: Sales, Purchases, Expenses, Payments
# ==============================================================================

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(100), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    sale_date = Column(DateTime, default=utc_now, nullable=False, index=True)
    subtotal_minor = Column(BigInteger, default=0, nullable=False)
    discount_minor = Column(BigInteger, default=0, nullable=False)
    tax_minor = Column(BigInteger, default=0, nullable=False)
    total_amount_minor = Column(BigInteger, default=0, nullable=False)
    paid_amount_minor = Column(BigInteger, default=0, nullable=False)
    payment_status = Column(String(50), default="paid", nullable=False)  # paid, partial, unpaid
    payment_method = Column(String(50), default="cash", nullable=False)  # cash, card, mobile_banking, credit
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sales_shop_date", "shop_id", "sale_date"),
        Index("idx_sales_shop_invoice", "shop_id", "invoice_number", unique=True),
    )


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    item_description = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price_minor = Column(BigInteger, nullable=False)
    discount_minor = Column(BigInteger, default=0, nullable=False)
    line_total_minor = Column(BigInteger, nullable=False)

    sale = relationship("Sale", back_populates="items")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    invoice_number = Column(String(100), nullable=False)
    purchase_date = Column(DateTime, default=utc_now, nullable=False, index=True)
    subtotal_minor = Column(BigInteger, default=0, nullable=False)
    tax_minor = Column(BigInteger, default=0, nullable=False)
    shipping_minor = Column(BigInteger, default=0, nullable=False)
    total_amount_minor = Column(BigInteger, default=0, nullable=False)
    paid_amount_minor = Column(BigInteger, default=0, nullable=False)
    payment_status = Column(String(50), default="paid", nullable=False)  # paid, partial, unpaid
    payment_method = Column(String(50), default="bank_transfer", nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_purchases_shop_date", "shop_id", "purchase_date"),
    )


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    item_description = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_cost_minor = Column(BigInteger, nullable=False)
    line_total_minor = Column(BigInteger, nullable=False)

    purchase = relationship("Purchase", back_populates="items")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    expense_category = Column(String(100), nullable=False)  # rent, utilities, salary, supplies, marketing, maintenance, other
    expense_date = Column(DateTime, default=utc_now, nullable=False, index=True)
    amount_minor = Column(BigInteger, nullable=False)
    payment_method = Column(String(50), default="cash", nullable=False)
    payee = Column(String(255), nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_expenses_shop_date", "shop_id", "expense_date"),
        Index("idx_expenses_category", "shop_id", "expense_category"),
    )


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_type = Column(String(50), nullable=False)  # customer_inflow, supplier_outflow, expense_outflow, loan_disbursement, loan_repayment
    reference_type = Column(String(50), nullable=True)  # sale, purchase, expense, loan_schedule
    reference_id = Column(Integer, nullable=True)
    payment_date = Column(DateTime, default=utc_now, nullable=False, index=True)
    amount_minor = Column(BigInteger, nullable=False)
    payment_method = Column(String(50), default="cash", nullable=False)
    notes = Column(Text, nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_payments_shop_date", "shop_id", "payment_date"),
    )


class Receivable(Base):
    __tablename__ = "receivables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    due_date = Column(DateTime, nullable=False, index=True)
    total_amount_minor = Column(BigInteger, nullable=False)
    outstanding_amount_minor = Column(BigInteger, nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, partial, overdue, settled, written_off
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_receivables_shop_status_due", "shop_id", "status", "due_date"),
    )


class CashMovement(Base):
    __tablename__ = "cash_movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    movement_type = Column(String(50), nullable=False)  # inflow, outflow
    source_type = Column(String(50), nullable=False)  # sale, purchase, expense, owner_equity, owner_draw, loan
    source_id = Column(Integer, nullable=True)
    amount_minor = Column(BigInteger, nullable=False)
    running_balance_minor = Column(BigInteger, nullable=False)
    movement_date = Column(DateTime, default=utc_now, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_cash_movements_shop_date", "shop_id", "movement_date"),
    )


# ==============================================================================
# 5. Document Intelligence
# ==============================================================================

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    file_hash_sha256 = Column(String(64), nullable=False, index=True)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    detected_language = Column(String(50), default="en", nullable=False)  # en, bn, bn-en
    status = Column(String(50), default="uploaded", nullable=False)  # uploaded, classified, extracted, review_required, approved, posted, rejected, failed
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    classification = relationship("DocumentClassification", uselist=False, back_populates="document", cascade="all, delete-orphan")
    extraction = relationship("DocumentExtraction", uselist=False, back_populates="document", cascade="all, delete-orphan")
    review = relationship("DocumentReview", uselist=False, back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_docs_shop_hash", "shop_id", "file_hash_sha256"),
    )


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, default=1, nullable=False)
    image_path = Column(String(500), nullable=False)
    width_px = Column(Integer, nullable=True)
    height_px = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    document = relationship("Document", back_populates="pages")


class DocumentClassification(Base):
    __tablename__ = "document_classifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_doc_type = Column(String(50), nullable=False)  # sales_receipt, purchase_invoice, expense_receipt, payment_receipt, unknown
    confidence_score = Column(Float, nullable=False)
    classifier_model_version = Column(String(100), default="rule_tfidf_v1", nullable=False)
    raw_predictions_json = Column(Text, nullable=True)  # Detailed probability distribution
    created_at = Column(DateTime, default=utc_now, nullable=False)

    document = relationship("Document", back_populates="classification")


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_ocr_text = Column(Text, nullable=True)
    raw_ocr_blocks_json = Column(Text, nullable=True)  # Bounding boxes and tokens
    structured_data_json = Column(Text, nullable=True)  # Parsed key-value pairs
    normalized_data_json = Column(Text, nullable=True)  # Minor-unit converted fields
    field_confidences_json = Column(Text, nullable=True)  # Confidence score per field
    validation_errors_json = Column(Text, nullable=True)  # Array of validation discrepancies
    extraction_model_version = Column(String(100), default="rapidocr_pipeline_v1", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    document = relationship("Document", back_populates="extraction")


class DocumentReview(Base):
    __tablename__ = "document_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, approved, corrected, rejected
    original_values_json = Column(Text, nullable=True)
    corrected_values_json = Column(Text, nullable=True)
    decision_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="review")


class DocumentProcessingJob(Base):
    __tablename__ = "document_processing_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    job_status = Column(String(50), default="queued", nullable=False)  # queued, running, completed, failed, retrying
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    idempotent_token = Column(String(100), unique=True, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=True, index=True)
    chunk_index = Column(Integer, nullable=False, default=0)
    chunk_text = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    embedding_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    document = relationship("Document", backref="chunks")
    business = relationship("Business")
    shop = relationship("Shop")

    __table_args__ = (
        Index("idx_doc_chunks_biz", "business_id"),
        Index("idx_doc_chunks_shop", "shop_id"),
        Index("idx_doc_chunks_doc", "document_id"),
    )


# ==============================================================================
# 6. Loans and Financial Planning (Explicitly Synthetic Demos)
# ==============================================================================

class DemoBank(Base):
    __tablename__ = "demo_banks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    contact_info = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, default=True, nullable=False)  # Always True for demo safety
    created_at = Column(DateTime, default=utc_now, nullable=False)

    products = relationship("LoanProduct", back_populates="bank", cascade="all, delete-orphan")


class LoanProduct(Base):
    __tablename__ = "loan_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bank_id = Column(Integer, ForeignKey("demo_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    min_amount_minor = Column(BigInteger, nullable=False)
    max_amount_minor = Column(BigInteger, nullable=False)
    min_tenure_months = Column(Integer, nullable=False)
    max_tenure_months = Column(Integer, nullable=False)
    annual_interest_rate_bps = Column(Integer, nullable=False)  # Basis points (e.g., 900 = 9.00%)
    interest_calc_type = Column(String(50), default="reducing_balance", nullable=False)  # reducing_balance, flat_rate
    processing_fee_bps = Column(Integer, default=100, nullable=False)  # 100 bps = 1.00%
    eligibility_criteria_json = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    bank = relationship("DemoBank", back_populates="products")
    rules = relationship("LoanRule", back_populates="product", cascade="all, delete-orphan")


class LoanRule(Base):
    __tablename__ = "loan_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("loan_products.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_name = Column(String(100), nullable=False)
    rule_condition_json = Column(Text, nullable=False)  # e.g., min_monthly_revenue, min_operation_months
    min_credit_score = Column(Integer, default=600, nullable=False)
    max_dscr_threshold = Column(Float, default=1.25, nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    product = relationship("LoanProduct", back_populates="rules")


class LoanScenario(Base):
    __tablename__ = "loan_scenarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("loan_products.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_amount_minor = Column(BigInteger, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    calculated_emi_minor = Column(BigInteger, nullable=False)
    total_interest_minor = Column(BigInteger, nullable=False)
    total_payment_minor = Column(BigInteger, nullable=False)
    dscr_ratio = Column(Float, nullable=False)
    recommendation_status = Column(String(50), nullable=False)  # eligible, borderline, ineligible
    rationale = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_id = Column(Integer, ForeignKey("demo_banks.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("loan_products.id", ondelete="RESTRICT"), nullable=False, index=True)
    applicant_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    application_number = Column(String(100), unique=True, nullable=False)
    requested_amount_minor = Column(BigInteger, nullable=False)
    approved_amount_minor = Column(BigInteger, default=0, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    status = Column(String(50), default="draft", nullable=False)  # draft, submitted, under_review, approved, rejected
    evaluation_notes = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


# ==============================================================================
# 7. AI, Automation, and Evaluation
# ==============================================================================

class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    target_metric = Column(String(50), nullable=False)  # daily_cashflow, weekly_sales, stockout_risk
    forecast_date_start = Column(DateTime, nullable=False)
    forecast_date_end = Column(DateTime, nullable=False)
    model_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True)
    predictions_json = Column(Text, nullable=False)
    lower_bound_json = Column(Text, nullable=True)
    upper_bound_json = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_forecasts_shop_metric", "shop_id", "target_metric"),
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)  # cashflow, inventory, pricing, debt_management
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    action_payload_json = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, viewed, accepted, dismissed
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class AutomatedTask(Base):
    __tablename__ = "automated_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(String(50), nullable=False)  # invoice_processing, low_stock_alert, receivable_reminder, cashflow_forecast
    schedule_cron = Column(String(50), default="0 0 * * *", nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active, paused, running, completed
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    config_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # document_posting, loan_submission, large_expense, stock_writeoff
    entity_id = Column(Integer, nullable=False)
    requested_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, approved, rejected
    requested_at = Column(DateTime, default=utc_now, nullable=False)
    acted_at = Column(DateTime, nullable=True)
    reason = Column(Text, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="info", nullable=False)  # info, warning, action_required, system
    is_read = Column(Boolean, default=False, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(50), nullable=False)  # tabular_relational, document_images, ocr_benchmark, cashflow_time_series
    record_count = Column(Integer, default=0, nullable=False)
    metadata_json = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(100), nullable=False, index=True)  # document_classification, ocr_extraction, cashflow_forecast, loan_risk, customer_segmentation
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    architecture_description = Column(Text, nullable=False)
    feature_schema_json = Column(Text, nullable=True)
    hyperparameters_json = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    evaluations = relationship("EvaluationRun", back_populates="model_version", cascade="all, delete-orphan")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    run_timestamp = Column(DateTime, default=utc_now, nullable=False)
    metrics_json = Column(Text, nullable=False)  # Precision, recall, F1, MAE, RMSE, etc.
    parameters_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_synthetic_benchmark = Column(Boolean, default=True, nullable=False)

    model_version = relationship("ModelVersion", back_populates="evaluations")
    dataset = relationship("Dataset")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    input_hash = Column(String(64), nullable=False, index=True)
    input_payload_json = Column(Text, nullable=False)
    output_payload_json = Column(Text, nullable=False)
    latency_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # create_sale, post_document, adjust_stock, approve_loan
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    old_values_json = Column(Text, nullable=True)
    new_values_json = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    __table_args__ = (
        Index("idx_audit_logs_shop_action", "shop_id", "action", "created_at"),
    )
