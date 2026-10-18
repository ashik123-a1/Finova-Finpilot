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

from src.database.connection import get_db
from src.database.models import User, Document, Shop
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
        db.commit()
        return result
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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


@router.get("/list/all")
def list_shop_documents(
    shop_id: int = Query(...),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists documents processed for a shop with pagination and optional status filter."""
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)

    query = db.query(Document).filter(Document.shop_id == shop_id)
    if status_filter:
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

    return {
        "shop_id": shop_id,
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "total_pages": total_pages,
        "documents": [
            {
                "id": d.id,
                "filename": d.original_filename,
                "status": d.status,
                "created_at": d.created_at.isoformat() if d.created_at else "",
                "mime_type": d.mime_type,
                "file_size_bytes": d.file_size_bytes,
                "classification": d.classification.predicted_doc_type if d.classification else "unknown",
                "confidence": d.classification.confidence_score if d.classification else 0.0,
            }
            for d in docs
        ],
    }


# Backwards compatibility alias for /documents/list without /all
@router.get("/list")
def list_shop_documents_legacy(
    shop_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Legacy endpoint returning flat list of top 50 documents."""
    return list_shop_documents(shop_id=shop_id, page=1, limit=50, user=user, db=db)["documents"]
