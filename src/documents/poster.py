"""
Document Financial Posting Service.
Commits confirmed document data to operational financial tables inside atomic transactions.
Enforces idempotency, auditability, and traceability back to source document.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from src.core.exceptions import CopilotException, InconsistentFinancialRecordError
from src.database.models import (
    Document,
    DocumentReview,
    Sale,
    Purchase,
    Expense,
    Payment,
    Customer,
    Supplier,
    utc_now,
)
from src.database.repository import (
    SaleRepository,
    PurchaseRepository,
    ExpenseRepository,
    AuditRepository,
)
from src.documents.schemas import DocumentType, DocumentReviewConfirmation


class DocumentPostingService:
    """Safely commits reviewed document data to financial ledger."""

    @classmethod
    def post_confirmed_document(
        cls,
        session: Session,
        confirmation: DocumentReviewConfirmation,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        doc = session.get(Document, confirmation.document_id)
        if not doc:
            raise CopilotException(f"Document {confirmation.document_id} not found.")

        # Idempotency guard: Prevent duplicate ledger entries
        if doc.status == "posted":
            return {
                "status": "already_posted",
                "message": "Document has already been posted to financial ledger.",
                "document_id": doc.id,
            }

        # Save review audit decision
        review = DocumentReview(
            document_id=doc.id,
            reviewer_user_id=user_id,
            status="approved" if confirmation.decision_action == "approve_and_post" else "rejected",
            original_values_json=doc.extraction.normalized_data_json if doc.extraction else "{}",
            corrected_values_json=json.dumps(confirmation.final_values),
            decision_notes=confirmation.reviewer_notes,
            reviewed_at=utc_now(),
        )
        session.add(review)

        if confirmation.decision_action != "approve_and_post":
            doc.status = "rejected"
            session.flush()
            return {
                "status": "rejected",
                "message": "Document marked as rejected by reviewer.",
                "document_id": doc.id,
            }

        final_vals = confirmation.final_values
        doc_type = confirmation.confirmed_doc_type
        created_entity_info: Dict[str, Any] = {}

        # 1. SALES RECEIPT POSTING
        if doc_type == DocumentType.SALES_RECEIPT:
            sale_repo = SaleRepository(session)
            # Find or create customer if name supplied
            cust_id = None
            cust_name = final_vals.get("customer_name")
            if cust_name:
                cust = (
                    session.query(Customer)
                    .filter_by(shop_id=doc.shop_id, name=cust_name)
                    .first()
                )
                if not cust:
                    cust = Customer(
                        business_id=doc.business_id,
                        shop_id=doc.shop_id,
                        name=cust_name,
                        phone=final_vals.get("customer_phone"),
                    )
                    session.add(cust)
                    session.flush()
                cust_id = cust.id

            sale_date_str = final_vals.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            try:
                sale_date = datetime.strptime(sale_date_str, "%Y-%m-%d")
            except Exception:
                sale_date = utc_now()

            sale_data = {
                "business_id": doc.business_id,
                "shop_id": doc.shop_id,
                "invoice_number": final_vals.get("invoice_number", f"DOC-{doc.id}"),
                "customer_id": cust_id,
                "sale_date": sale_date,
                "subtotal_minor": final_vals.get("subtotal_minor", 0),
                "discount_minor": final_vals.get("discount_minor", 0),
                "tax_minor": final_vals.get("tax_minor", 0),
                "total_amount_minor": final_vals.get("total_amount_minor", 0),
                "paid_amount_minor": final_vals.get("paid_amount_minor", final_vals.get("total_amount_minor", 0)),
                "payment_status": "paid" if final_vals.get("paid_amount_minor", 0) >= final_vals.get("total_amount_minor", 0) else "partial",
                "payment_method": final_vals.get("payment_method", "cash"),
                "document_id": doc.id,
                "created_by": user_id,
            }

            items_data = []
            for it in final_vals.get("items", []):
                items_data.append({
                    "item_description": it.get("description", "Generic Item"),
                    "quantity": it.get("quantity", 1),
                    "unit_price_minor": it.get("unit_price_minor", 0),
                    "discount_minor": it.get("discount_minor", 0),
                    "line_total_minor": it.get("line_total_minor", 0),
                })

            sale = sale_repo.create_sale_with_items(sale_data, items_data, update_inventory=True)
            created_entity_info = {"entity": "sale", "id": sale.id, "invoice_number": sale.invoice_number}

        # 2. PURCHASE INVOICE POSTING
        elif doc_type == DocumentType.PURCHASE_INVOICE:
            purchase_repo = PurchaseRepository(session)
            supp_name = final_vals.get("supplier_name", "General Supplier")
            supp = (
                session.query(Supplier)
                .filter_by(shop_id=doc.shop_id, name=supp_name)
                .first()
            )
            if not supp:
                supp = Supplier(
                    business_id=doc.business_id,
                    shop_id=doc.shop_id,
                    name=supp_name,
                    phone=final_vals.get("supplier_phone"),
                )
                session.add(supp)
                session.flush()

            purch_date_str = final_vals.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            try:
                purch_date = datetime.strptime(purch_date_str, "%Y-%m-%d")
            except Exception:
                purch_date = utc_now()

            purchase_data = {
                "business_id": doc.business_id,
                "shop_id": doc.shop_id,
                "supplier_id": supp.id,
                "invoice_number": final_vals.get("invoice_number", f"BILL-{doc.id}"),
                "purchase_date": purch_date,
                "subtotal_minor": final_vals.get("subtotal_minor", 0),
                "tax_minor": final_vals.get("tax_minor", 0),
                "shipping_minor": final_vals.get("shipping_minor", 0),
                "total_amount_minor": final_vals.get("total_amount_minor", 0),
                "paid_amount_minor": final_vals.get("paid_amount_minor", final_vals.get("total_amount_minor", 0)),
                "payment_status": "paid" if final_vals.get("paid_amount_minor", 0) >= final_vals.get("total_amount_minor", 0) else "partial",
                "payment_method": final_vals.get("payment_method", "bank_transfer"),
                "document_id": doc.id,
                "created_by": user_id,
            }

            items_data = []
            for it in final_vals.get("items", []):
                items_data.append({
                    "item_description": it.get("description", "Supplied Goods"),
                    "quantity": it.get("quantity", 1),
                    "unit_cost_minor": it.get("unit_price_minor", 0),
                    "line_total_minor": it.get("line_total_minor", 0),
                })

            purchase = purchase_repo.create_purchase_with_items(purchase_data, items_data, update_inventory=True)
            created_entity_info = {"entity": "purchase", "id": purchase.id, "invoice_number": purchase.invoice_number}

        # 3. EXPENSE RECEIPT POSTING
        elif doc_type == DocumentType.EXPENSE_RECEIPT:
            expense_repo = ExpenseRepository(session)
            exp_date_str = final_vals.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            try:
                exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
            except Exception:
                exp_date = utc_now()

            expense_data = {
                "business_id": doc.business_id,
                "shop_id": doc.shop_id,
                "expense_category": final_vals.get("category", "other"),
                "expense_date": exp_date,
                "amount_minor": final_vals.get("amount_minor", final_vals.get("total_amount_minor", 0)),
                "payment_method": final_vals.get("payment_method", "cash"),
                "payee": final_vals.get("payee"),
                "description": final_vals.get("description"),
                "document_id": doc.id,
                "created_by": user_id,
            }
            expense = expense_repo.create_expense(expense_data)
            created_entity_info = {"entity": "expense", "id": expense.id, "category": expense.expense_category}

        # 4. PAYMENT RECEIPT POSTING
        elif doc_type == DocumentType.PAYMENT_RECEIPT:
            p_date_str = final_vals.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            try:
                p_date = datetime.strptime(p_date_str, "%Y-%m-%d")
            except Exception:
                p_date = utc_now()

            payment = Payment(
                business_id=doc.business_id,
                shop_id=doc.shop_id,
                payment_type=final_vals.get("payment_type", "customer_inflow"),
                reference_type="document",
                reference_id=doc.id,
                payment_date=p_date,
                amount_minor=final_vals.get("amount_minor", final_vals.get("total_amount_minor", 0)),
                payment_method=final_vals.get("payment_method", "cash"),
                notes=final_vals.get("notes", f"Payment verified from Doc #{doc.id}"),
                document_id=doc.id,
                created_by=user_id,
            )
            session.add(payment)
            session.flush()
            created_entity_info = {"entity": "payment", "id": payment.id}

        # Mark document as posted
        doc.status = "posted"
        AuditRepository(session).log_action(
            action="post_document",
            entity_type="document",
            entity_id=doc.id,
            business_id=doc.business_id,
            shop_id=doc.shop_id,
            user_id=user_id,
            new_values=json.dumps(created_entity_info),
        )
        session.flush()

        return {
            "status": "posted",
            "message": f"Successfully posted {doc_type.value} to ledger.",
            "document_id": doc.id,
            "created_record": created_entity_info,
        }
