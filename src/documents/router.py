"""
Dynamic Document-to-Form Router.
Orchestrates the entire ingest pipeline:
Upload -> Validation -> Hash Deduplication -> OCR -> Classification -> Extraction -> Validation -> Dynamic Form Selection.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from src.database.models import (
    Document,
    DocumentClassification,
    DocumentExtraction,
    DocumentProcessingJob,
    utc_now,
)
from src.documents.validator import (
    compute_file_hash,
    validate_file_content,
    check_for_duplicate_document,
    save_uploaded_file,
)
from src.documents.classifier import DocumentClassifier
from src.documents.extractor import RapidOcrEngine, StructuredDocumentExtractor, BaseOcrProvider
from src.documents.schemas import DocumentType, FormRoutingResult


class DocumentPipelineRouter:
    """Manages document ingest and automatic form routing."""

    def __init__(self, ocr_provider: Optional[BaseOcrProvider] = None) -> None:
        self.ocr_provider = ocr_provider or RapidOcrEngine()

    def process_and_route(
        self,
        session: Session,
        business_id: int,
        shop_id: int,
        file_bytes: bytes,
        original_filename: str,
        user_id: Optional[int] = None,
    ) -> FormRoutingResult:
        """
        Executes end-to-end processing pipeline and outputs structured routing result.
        """
        # 1. Validation & Hash
        ext, mime_type = validate_file_content(file_bytes, original_filename)
        file_hash = compute_file_hash(file_bytes)

        # 2. Duplicate Detection
        existing_doc = check_for_duplicate_document(session, shop_id, file_hash)
        if existing_doc:
            # Document already processed or uploaded
            classification = existing_doc.classification
            extraction = existing_doc.extraction
            pred_type = (
                DocumentType(classification.predicted_doc_type)
                if classification
                else DocumentType.UNKNOWN
            )
            confidence = classification.confidence_score if classification else 0.0
            norm_vals = json.loads(extraction.normalized_data_json) if (extraction and extraction.normalized_data_json) else {}
            confidences = json.loads(extraction.field_confidences_json) if (extraction and extraction.field_confidences_json) else {}
            val_errors = json.loads(extraction.validation_errors_json) if (extraction and extraction.validation_errors_json) else []

            return FormRoutingResult(
                document_id=existing_doc.id,
                file_hash=file_hash,
                predicted_doc_type=pred_type,
                classification_confidence=confidence,
                target_form=self._map_doc_type_to_form(pred_type),
                requires_user_review=True,
                review_reasons=["Duplicate document previously uploaded in this shop."],
                normalized_values=norm_vals,
                raw_extracted_values=norm_vals,
                field_confidences=confidences,
                validation_errors=val_errors,
                is_duplicate=True,
            )

        # 3. Store file securely
        saved_path = save_uploaded_file(
            file_bytes, business_id, shop_id, original_filename, file_hash, ext
        )

        # 4. Create Document record in DB
        doc = Document(
            business_id=business_id,
            shop_id=shop_id,
            original_filename=original_filename,
            stored_path=str(saved_path),
            file_hash_sha256=file_hash,
            file_size_bytes=len(file_bytes),
            mime_type=mime_type,
            detected_language="en",
            status="processing",
            created_by=user_id,
        )
        session.add(doc)
        session.flush()

        # Create idempotent processing job
        job_token = f"job-{doc.id}-{file_hash[:12]}"
        job = DocumentProcessingJob(
            document_id=doc.id,
            job_status="running",
            idempotent_token=job_token,
            started_at=utc_now(),
        )
        session.add(job)
        session.flush()

        # 5. Execute OCR
        ocr_out = self.ocr_provider.extract_text_and_blocks(str(saved_path))
        doc.detected_language = ocr_out.detected_language

        # 6. Classification
        pred_type, cls_confidence, raw_probs = DocumentClassifier.classify_text(ocr_out.full_text)
        classification = DocumentClassification(
            document_id=doc.id,
            predicted_doc_type=pred_type.value,
            confidence_score=cls_confidence,
            classifier_model_version="rule_tfidf_v1",
            raw_predictions_json=json.dumps(raw_probs),
        )
        session.add(classification)

        # 7. Structured Extraction & Math Audit
        extracted_vals, field_confidences, val_errors = StructuredDocumentExtractor.extract_fields(
            ocr_out, pred_type
        )

        extraction = DocumentExtraction(
            document_id=doc.id,
            raw_ocr_text=ocr_out.full_text,
            raw_ocr_blocks_json=json.dumps([b.dict() for b in ocr_out.blocks]),
            structured_data_json=json.dumps(extracted_vals),
            normalized_data_json=json.dumps(extracted_vals),
            field_confidences_json=json.dumps(field_confidences),
            validation_errors_json=json.dumps(val_errors),
            extraction_model_version="rapidocr_pipeline_v1",
        )
        session.add(extraction)

        # 8. Dynamic Form Routing & Review Decision
        target_form = self._map_doc_type_to_form(pred_type)
        review_reasons = []

        if pred_type == DocumentType.UNKNOWN:
            review_reasons.append("Document classification confidence is low or unrecognized.")
        if cls_confidence < 0.85:
            review_reasons.append(f"Classification confidence ({cls_confidence:.2f}) below auto-post threshold (0.85).")
        if val_errors:
            review_reasons.extend(val_errors)
        if field_confidences.get("total_amount_minor", 0.0) < 0.80:
            review_reasons.append("Total amount extracted with low confidence.")

        requires_review = len(review_reasons) > 0
        doc.status = "review_required" if requires_review else "classified"
        job.job_status = "completed"
        job.completed_at = utc_now()

        session.flush()

        return FormRoutingResult(
            document_id=doc.id,
            file_hash=file_hash,
            predicted_doc_type=pred_type,
            classification_confidence=cls_confidence,
            target_form=target_form,
            requires_user_review=requires_review,
            review_reasons=review_reasons,
            normalized_values=extracted_vals,
            raw_extracted_values=extracted_vals,
            field_confidences=field_confidences,
            validation_errors=val_errors,
            is_duplicate=False,
        )

    @staticmethod
    def _map_doc_type_to_form(doc_type: DocumentType) -> str:
        mapping = {
            DocumentType.SALES_RECEIPT: "sales_form",
            DocumentType.PURCHASE_INVOICE: "purchase_form",
            DocumentType.EXPENSE_RECEIPT: "expense_form",
            DocumentType.PAYMENT_RECEIPT: "payment_form",
            DocumentType.UNKNOWN: "manual_review_form",
        }
        return mapping.get(doc_type, "manual_review_form")
