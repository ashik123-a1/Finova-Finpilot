"""
Document Processing and Routing API Routes.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User, Document, Shop
from src.api.dependencies import get_current_user, verify_shop_access_dependency
from src.documents.router import DocumentPipelineRouter
from src.documents.poster import DocumentPostingService
from src.documents.schemas import FormRoutingResult, DocumentReviewConfirmation

router = APIRouter(prefix="/documents", tags=["Documents"])
pipeline_router = DocumentPipelineRouter()


@router.post("/upload", response_model=FormRoutingResult)
async def upload_document(
    shop_id: int = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Uploads a financial document, runs OCR, classifies type, validates fields,
    and returns dynamic form routing instructions.
    """
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

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
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm-post")
def confirm_and_post_document(
    confirmation: DocumentReviewConfirmation,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Commits reviewed and confirmed document figures into operational financial tables.
    """
    doc = db.get(Document, confirmation.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    verify_shop_access_dependency(shop_id=doc.shop_id, user=user, db=db)

    try:
        result = DocumentPostingService.post_confirmed_document(
            session=db,
            confirmation=confirmation,
            user_id=user.id,
        )
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list")
def list_shop_documents(
    shop_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists documents processed for a shop."""
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    docs = (
        db.query(Document)
        .filter_by(shop_id=shop_id)
        .order_by(Document.id.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": d.id,
            "filename": d.original_filename,
            "status": d.status,
            "created_at": d.created_at.isoformat(),
            "mime_type": d.mime_type,
            "classification": d.classification.predicted_doc_type if d.classification else "unknown",
            "confidence": d.classification.confidence_score if d.classification else 0.0,
        }
        for d in docs
    ]
