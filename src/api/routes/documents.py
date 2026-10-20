"""
Document Processing and Routing API Routes.
Provides secure upload, OCR extraction, form routing, human-review gating, and ledger posting.
"""

from __future__ import annotations

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from pydantic import BaseModel
from src.database.connection import get_db
from src.database.models import User, Document, Shop, DocumentClassification, DocumentExtraction, utc_now
from src.api.dependencies import get_current_user, verify_shop_access_dependency
from src.documents.router import DocumentPipelineRouter
from src.documents.poster import DocumentPostingService
from src.documents.schemas import FormRoutingResult, DocumentReviewConfirmation
from src.core.exceptions import DuplicateDocumentError, DocumentProcessingError

router = APIRouter(prefix="/documents", tags=["Documents"])
pipeline_router = DocumentPipelineRouter()

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "application/pdf",
    "application/octet-stream",  # Fallback for binary test uploads
}


@router.post("/upload", response_model=FormRoutingResult)
async def upload_document(
    shop_id: int = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Uploads a financial document, validates size and MIME type, runs OCR,
    classifies document type, performs mathematical validation, and returns
    routing instructions with human-review requirement gating.
    """
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found.")

    # MIME type validation
    if file.content_type and file.content_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. Allowed types: PNG, JPEG, WEBP, PDF.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file uploaded.")

    # Size validation
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed upload size of 10MB ({len(file_bytes)} bytes).",
        )

    try:
        routing_result = pipeline_router.process_and_route(
            session=db,
            business_id=shop.business_id,
            shop_id=shop.id,
            file_bytes=file_bytes,
            original_filename=file.filename or "receipt.png",
            user_id=user.id,
        )
        if routing_result.requires_user_review:
            try:
                from src.api.routes.notifications import create_persistent_notification
                reasons = ", ".join(routing_result.review_reasons) if routing_result.review_reasons else "Confidence checks required"
                create_persistent_notification(
                    db=db,
                    user_id=user.id,
                    business_id=shop.business_id,
                    shop_id=shop.id,
                    title="Document OCR Flagged for Review",
                    message=f"Document '{file.filename}' flagged for human verification ({reasons}).",
                    notification_type="ocr_review",
                    severity="warning",
                    action_url=f"/app/documents?doc_id={routing_result.document_id}",
                    dedup_key=f"ocr_review_{routing_result.document_id}"
                )
            except Exception:
                pass
        db.commit()
        return routing_result
    except DuplicateDocumentError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DocumentProcessingError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/confirm-post")
def confirm_and_post_document(
    confirmation: DocumentReviewConfirmation,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Commits reviewed and confirmed document figures into operational financial tables.
    Enforces idempotency: rejects duplicate postings of already-committed documents with 409 Conflict.
    """
    doc = db.get(Document, confirmation.document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    verify_shop_access_dependency(shop_id=doc.shop_id, user=user, db=db)

    # Idempotency check: Guard against duplicate posting
    if doc.status == "posted":
        raise DuplicateDocumentError(
            "Document has already been posted to financial ledger."
        )

    try:
        result = DocumentPostingService.post_confirmed_document(
            session=db,
            confirmation=confirmation,
            user_id=user.id,
        )
        if result.get("status") == "already_posted":
            db.rollback()
            raise DuplicateDocumentError(
                "Document has already been posted to financial ledger."
            )
        try:
            from src.api.routes.notifications import create_persistent_notification
            create_persistent_notification(
                db=db,
                user_id=user.id,
                business_id=doc.business_id,
                shop_id=doc.shop_id,
                title="Document Ledger Entry Committed",
                message=f"Document #{doc.id} posted to financial ledger as {confirmation.confirmed_doc_type}.",
                notification_type="ledger_posted",
                severity="success",
                action_url="/app/finance",
                dedup_key=f"doc_posted_{doc.id}"
            )
        except Exception:
            pass
        db.commit()
        return result
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


class ManualDocumentEntryRequest(BaseModel):
    shop_id: int
    doc_type: str
    counterparty: str
    total_amount: float
    reference_number: Optional[str] = None
    date: Optional[str] = None
    notes: Optional[str] = None


@router.post("/manual-entry")
def manual_document_entry(
    payload: ManualDocumentEntryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Direct manual ledger entry gateway bypassing optical OCR.
    Enables recording invoices, utility bills, and payment vouchers manually.
    """
    verify_shop_access_dependency(shop_id=payload.shop_id, user=user, db=db)
    shop = db.get(Shop, payload.shop_id)
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found.")

    clean_type = payload.doc_type.lower().strip()
    total_minor = int(round(payload.total_amount * 100))
    counterparty = payload.counterparty.strip()

    norm_vals = {
        "doc_type": clean_type,
        "supplier_name": counterparty,
        "customer_name": counterparty,
        "payee": counterparty,
        "vendor_name": counterparty,
        "total_amount_minor": total_minor,
        "subtotal_minor": total_minor,
        "amount_minor": total_minor,
        "paid_amount_minor": total_minor,
        "invoice_number": payload.reference_number or f"MAN-{int(utc_now().timestamp())}",
        "transaction_date": payload.date,
        "notes": payload.notes,
    }

    doc = Document(
        business_id=shop.business_id,
        shop_id=shop.id,
        uploader_user_id=user.id,
        original_filename=f"manual_entry_{clean_type}.pdf",
        stored_file_path="",
        file_hash_sha256=f"manual_{user.id}_{int(utc_now().timestamp())}_{total_minor}",
        file_size_bytes=0,
        mime_type="application/json",
        status="uploaded",
    )
    db.add(doc)
    db.flush()

    classification = DocumentClassification(
        document_id=doc.id,
        predicted_doc_type=clean_type,
        confidence_score=1.0,
        classifier_model_version="manual_entry_v1",
    )
    db.add(classification)

    extraction = DocumentExtraction(
        document_id=doc.id,
        raw_ocr_text=f"Direct Manual Entry: {counterparty} - {payload.total_amount}",
        structured_data_json=json.dumps(norm_vals),
        normalized_data_json=json.dumps(norm_vals),
        field_confidences_json=json.dumps({"total_amount": 1.0, "counterparty": 1.0}),
        validation_errors_json="[]",
        extraction_model_version="manual_entry_v1",
    )
    db.add(extraction)
    db.flush()

    confirmation = DocumentReviewConfirmation(
        document_id=doc.id,
        confirmed_doc_type=clean_type,
        final_values=norm_vals,
        decision_action="approve_and_post",
        reviewer_notes=payload.notes or "Direct manual ledger posting via Web UI",
    )

    post_res = DocumentPostingService.post_confirmed_document(
        session=db,
        confirmation=confirmation,
        user_id=user.id,
    )
    try:
        from src.api.routes.notifications import create_persistent_notification
        create_persistent_notification(
            db=db,
            user_id=user.id,
            business_id=shop.business_id,
            shop_id=shop.id,
            title="Manual Ledger Entry Recorded",
            message=f"Manual ledger entry for {counterparty} recorded ({clean_type}, total {payload.total_amount}).",
            notification_type="ledger_posted",
            severity="info",
            action_url="/app/finance",
            dedup_key=f"manual_posted_{doc.id}"
        )
    except Exception:
        pass
    db.commit()

    return {
        "status": "success",
        "document_id": doc.id,
        "display_id": f"DOC-2026-{doc.id:03d}",
        "doc_type": clean_type,
        "total_amount": payload.total_amount,
        "counterparty": counterparty,
        "posted_record": post_res.get("created_record"),
    }


@router.get("/list/all")
def list_shop_documents(
    shop_id: int = Query(...),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists documents processed for a shop with pagination and enriched extraction summaries."""
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)

    query = db.query(Document).filter(Document.shop_id == shop_id)
    if status_filter and isinstance(status_filter, str):
        query = query.filter(Document.status == status_filter)

    total_count = query.count()
    offset = (page - 1) * limit
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    docs = (
        query.order_by(desc(Document.id))
        .offset(offset)
        .limit(limit)
        .all()
    )

    doc_items = []
    for d in docs:
        norm = {}
        val_errors = []
        if d.review and d.review.corrected_values_json:
            try:
                norm = json.loads(d.review.corrected_values_json)
            except Exception:
                norm = {}
        elif d.extraction and d.extraction.normalized_data_json:
            try:
                norm = json.loads(d.extraction.normalized_data_json)
            except Exception:
                norm = {}
        elif d.extraction and d.extraction.structured_data_json:
            try:
                norm = json.loads(d.extraction.structured_data_json)
            except Exception:
                norm = {}

        if d.review and d.review.status == "approved":
            val_errors = []
        elif d.extraction and d.extraction.validation_errors_json:
            try:
                val_errors = json.loads(d.extraction.validation_errors_json)
            except Exception:
                val_errors = []

        vendor = (
            norm.get("vendor_name")
            or norm.get("supplier_name")
            or norm.get("customer_name")
            or norm.get("payee")
            or norm.get("payer_or_payee")
            or "General Commercial Trade"
        )
        total_minor = norm.get("total_amount_minor") or norm.get("amount_minor") or 0
        total = round(total_minor / 100.0, 2)

        doc_type_val = d.classification.predicted_doc_type if d.classification else "unknown"
        conf_val = d.classification.confidence_score if d.classification else 0.0
        conf_pct = round(conf_val * 100, 1) if conf_val <= 1.0 else round(conf_val, 1)

        doc_items.append({
            "id": d.id,
            "display_id": f"DOC-2026-{d.id:03d}",
            "filename": d.original_filename,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else "",
            "mime_type": d.mime_type,
            "file_size_bytes": d.file_size_bytes,
            "classification": doc_type_val,
            "confidence": conf_pct,
            "vendor": vendor,
            "total": total,
            "total_minor": total_minor,
            "normalized_values": norm,
            "validation_errors": val_errors,
        })

    return {
        "shop_id": shop_id,
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "total_pages": total_pages,
        "documents": doc_items,
    }


# Backwards compatibility alias for /documents/list without /all
@router.get("/list")
def list_shop_documents_legacy(
    shop_id: int = Query(...),
    status: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Legacy endpoint returning flat list of top 50 documents."""
    clean_status = status if isinstance(status, str) else None
    return list_shop_documents(
        shop_id=shop_id,
        status_filter=clean_status,
        page=1,
        limit=50,
        user=user,
        db=db,
    )["documents"]


@router.get("/{document_id}")
def get_document_details(
    document_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves complete details for a specific document including OCR output,
    classification confidence, extraction payload, and human review decisions.
    Enforces tenant isolation by verifying the user has access to the document's shop.
    """
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    verify_shop_access_dependency(shop_id=doc.shop_id, user=user, db=db)

    classification = doc.classification
    extraction = doc.extraction
    review = doc.review

    return {
        "id": doc.id,
        "business_id": doc.business_id,
        "shop_id": doc.shop_id,
        "filename": doc.original_filename,
        "status": doc.status,
        "mime_type": doc.mime_type,
        "file_size_bytes": doc.file_size_bytes,
        "content_hash": doc.file_hash_sha256,
        "created_at": doc.created_at.isoformat() if doc.created_at else "",
        "classification": {
            "predicted_doc_type": classification.predicted_doc_type,
            "confidence_score": classification.confidence_score,
            "classification_method": classification.classifier_model_version,
        } if classification else None,
        "extraction": {
            "raw_ocr_text": extraction.raw_ocr_text,
            "structured_data": json.loads(extraction.structured_data_json) if extraction and extraction.structured_data_json else {},
            "normalized_data": json.loads(extraction.normalized_data_json) if extraction and extraction.normalized_data_json else {},
            "field_confidences": json.loads(extraction.field_confidences_json) if extraction and extraction.field_confidences_json else {},
            "validation_errors": json.loads(extraction.validation_errors_json) if extraction and extraction.validation_errors_json else [],
            "extraction_model_version": extraction.extraction_model_version if extraction else None,
        } if extraction else None,
        "review": {
            "status": review.status,
            "reviewer_user_id": review.reviewer_user_id,
            "decision_notes": review.decision_notes,
            "reviewed_at": review.reviewed_at.isoformat() if review and review.reviewed_at else None,
        } if review else None,
        "is_posted": doc.status == "posted",
    }

