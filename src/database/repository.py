"""
Repository Layer for SME Finance Copilot.
Abstracts all database access behind clean domain repositories.
Enforces multi-tenant shop isolation, atomic transactions, and parameterized queries.
Allows frictionless migration between SQLite and PostgreSQL.
"""

from __future__ import annotations

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc

from src.database.models import (
    User,
    Business,
    Shop,
    BusinessMembership,
    Customer,
    Supplier,
    Product,
    PurchaseOrder,
    InventoryMovement,
    StockAdjustment,
    Sale,
    SaleItem,
    Purchase,
    PurchaseItem,
    Expense,
    Payment,
    Receivable,
    CashMovement,
    Document,
    DocumentPage,
    DocumentClassification,
    DocumentExtraction,
    DocumentReview,
    DocumentProcessingJob,
    DemoBank,
    LoanProduct,
    LoanScenario,
    LoanApplication,
    Dataset,
    ModelVersion,
    EvaluationRun,
    AuditLog,
    utc_now,
)
from src.core.exceptions import ShopAccessDeniedError, ResourceNotFoundError

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic base repository for CRUD operations with shop isolation."""

    def __init__(self, model_class: Type[T], session: Session) -> None:
        self.model_class = model_class
        self.session = session

    def get_by_id(self, entity_id: int) -> Optional[T]:
        return self.session.get(self.model_class, entity_id)

    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        stmt = select(self.model_class).limit(limit).offset(offset)
        return list(self.session.scalars(stmt).all())

    def add(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)
        self.session.flush()


class ShopIsolatedRepository(BaseRepository[T]):
    """Enforces shop-level isolation on queries and inserts."""

    def get_by_id_isolated(self, entity_id: int, shop_id: int) -> Optional[T]:
        stmt = select(self.model_class).where(
            and_(
                self.model_class.id == entity_id,
                self.model_class.shop_id == shop_id,
            )
        )
        return self.session.scalars(stmt).first()

    def list_by_shop(self, shop_id: int, limit: int = 100, offset: int = 0) -> List[T]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.shop_id == shop_id)
            .order_by(desc(self.model_class.id))
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt).all())


class ProductRepository(ShopIsolatedRepository[Product]):
    def __init__(self, session: Session) -> None:
        super().__init__(Product, session)


class SaleRepository(ShopIsolatedRepository[Sale]):
    def __init__(self, session: Session) -> None:
        super().__init__(Sale, session)

    def create_sale_with_items(
        self,
        sale_data: Dict[str, Any],
        items_data: List[Dict[str, Any]],
        update_inventory: bool = True,
    ) -> Sale:
        """
        Creates a sale and its line items inside an atomic transaction.
        Updates stock levels and generates inventory movements if requested.
        """
        sale = Sale(**sale_data)
        self.session.add(sale)
        self.session.flush()

        for item_dict in items_data:
            item = SaleItem(sale_id=sale.id, **item_dict)
            self.session.add(item)

            if update_inventory and item.product_id:
                product = self.session.get(Product, item.product_id)
                if product:
                    # Enforce shop isolation
                    if product.shop_id != sale.shop_id:
                        raise ShopAccessDeniedError("Product does not belong to the sale shop.")
                    product.current_stock -= item.quantity
                    product.updated_at = utc_now()

                    # Record movement
                    movement = InventoryMovement(
                        business_id=sale.business_id,
                        shop_id=sale.shop_id,
                        product_id=product.id,
                        movement_type="sale_delivery",
                        reference_type="sale",
                        reference_id=sale.id,
                        quantity_change=-item.quantity,
                        resulting_stock=product.current_stock,
                        unit_cost_minor=product.cost_price_minor,
                        movement_date=sale.sale_date,
                        notes=f"Auto posted from Sale {sale.invoice_number}",
                        is_synthetic=sale.is_synthetic,
                    )
                    self.session.add(movement)

        # Record payment / receivable if applicable
        if sale.paid_amount_minor > 0:
            payment = Payment(
                business_id=sale.business_id,
                shop_id=sale.shop_id,
                payment_type="customer_inflow",
                reference_type="sale",
                reference_id=sale.id,
                payment_date=sale.sale_date,
                amount_minor=sale.paid_amount_minor,
                payment_method=sale.payment_method,
                notes=f"Payment for Sale {sale.invoice_number}",
                document_id=sale.document_id,
                is_synthetic=sale.is_synthetic,
            )
            self.session.add(payment)

        outstanding = sale.total_amount_minor - sale.paid_amount_minor
        if outstanding > 0 and sale.customer_id:
            # Create receivable
            due_date = sale.sale_date  # default, will be adjusted by terms
            receivable = Receivable(
                business_id=sale.business_id,
                shop_id=sale.shop_id,
                sale_id=sale.id,
                customer_id=sale.customer_id,
                due_date=due_date,
                total_amount_minor=outstanding,
                outstanding_amount_minor=outstanding,
                status="pending",
                is_synthetic=sale.is_synthetic,
            )
            self.session.add(receivable)
            # Update customer balance
            customer = self.session.get(Customer, sale.customer_id)
            if customer:
                customer.balance_minor += outstanding

        self.session.flush()
        return sale


class PurchaseRepository(ShopIsolatedRepository[Purchase]):
    def __init__(self, session: Session) -> None:
        super().__init__(Purchase, session)

    def create_purchase_with_items(
        self,
        purchase_data: Dict[str, Any],
        items_data: List[Dict[str, Any]],
        update_inventory: bool = True,
    ) -> Purchase:
        """Creates a purchase and updates inventory & payments atomically."""
        purchase = Purchase(**purchase_data)
        self.session.add(purchase)
        self.session.flush()

        for item_dict in items_data:
            item = PurchaseItem(purchase_id=purchase.id, **item_dict)
            self.session.add(item)

            if update_inventory and item.product_id:
                product = self.session.get(Product, item.product_id)
                if product:
                    if product.shop_id != purchase.shop_id:
                        raise ShopAccessDeniedError("Product does not belong to the purchase shop.")
                    product.current_stock += item.quantity
                    # Weighted average or latest cost update
                    product.cost_price_minor = item.unit_cost_minor
                    product.updated_at = utc_now()

                    movement = InventoryMovement(
                        business_id=purchase.business_id,
                        shop_id=purchase.shop_id,
                        product_id=product.id,
                        movement_type="purchase_receipt",
                        reference_type="purchase",
                        reference_id=purchase.id,
                        quantity_change=item.quantity,
                        resulting_stock=product.current_stock,
                        unit_cost_minor=item.unit_cost_minor,
                        movement_date=purchase.purchase_date,
                        notes=f"Auto posted from Purchase {purchase.invoice_number}",
                        is_synthetic=purchase.is_synthetic,
                    )
                    self.session.add(movement)

        if purchase.paid_amount_minor > 0:
            payment = Payment(
                business_id=purchase.business_id,
                shop_id=purchase.shop_id,
                payment_type="supplier_outflow",
                reference_type="purchase",
                reference_id=purchase.id,
                payment_date=purchase.purchase_date,
                amount_minor=purchase.paid_amount_minor,
                payment_method=purchase.payment_method,
                notes=f"Disbursement for Purchase {purchase.invoice_number}",
                document_id=purchase.document_id,
                is_synthetic=purchase.is_synthetic,
            )
            self.session.add(payment)

        self.session.flush()
        return purchase


class ExpenseRepository(ShopIsolatedRepository[Expense]):
    def __init__(self, session: Session) -> None:
        super().__init__(Expense, session)

    def create_expense(self, expense_data: Dict[str, Any]) -> Expense:
        expense = Expense(**expense_data)
        self.session.add(expense)
        self.session.flush()

        # Record payment outflow
        payment = Payment(
            business_id=expense.business_id,
            shop_id=expense.shop_id,
            payment_type="expense_outflow",
            reference_type="expense",
            reference_id=expense.id,
            payment_date=expense.expense_date,
            amount_minor=expense.amount_minor,
            payment_method=expense.payment_method,
            notes=f"Expense: {expense.expense_category} - {expense.description or ''}",
            document_id=expense.document_id,
            is_synthetic=expense.is_synthetic,
        )
        self.session.add(payment)
        self.session.flush()
        return expense


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def log_action(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        business_id: Optional[int] = None,
        shop_id: Optional[int] = None,
        user_id: Optional[int] = None,
        old_values: Optional[str] = None,
        new_values: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            business_id=business_id,
            shop_id=shop_id,
            user_id=user_id,
            old_values_json=old_values,
            new_values_json=new_values,
            ip_address=ip_address,
        )
        self.session.add(log)
        self.session.flush()
        return log
