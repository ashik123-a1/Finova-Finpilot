"""
Unit & Integration Tests for Document Ingest, Classification, and Routing Pipeline.
"""

import io
import pytest
from PIL import Image

from src.documents.classifier import DocumentClassifier
from src.documents.schemas import DocumentType, DocumentReviewConfirmation
from src.documents.extractor import StructuredDocumentExtractor, RawOcrOutput, RawOcrBlock, MockOcrProvider
from src.documents.router import DocumentPipelineRouter
from src.documents.poster import DocumentPostingService
from src.database.models import Document, Sale, Purchase, Expense


def create_dummy_png_bytes() -> bytes:
    """Generates valid PNG image bytes for upload validation."""
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_document_classifier_languages():
    """Tests classification across English, Bengali, and Mixed keywords."""
    # 1. English Sales Receipt
    en_text = "CASH MEMO Store XYZ Total Amount: 1,500.00"
    doc_type, conf, probs = DocumentClassifier.classify_text(en_text)
    assert doc_type == DocumentType.SALES_RECEIPT
    assert conf >= 0.70

    # 2. Bengali Purchase Challan
    bn_text = "চালান মেসার্স হক ট্রেডার্স চালান নম্বর: ১২৩৪ সরবরাহকারী"
    doc_type, conf, probs = DocumentClassifier.classify_text(bn_text)
    assert doc_type == DocumentType.PURCHASE_INVOICE
    assert conf >= 0.60

    # 3. Expense Voucher
    exp_text = "OFFICE EXPENSE VOUCHER Rent payment for October"
    doc_type, conf, probs = DocumentClassifier.classify_text(exp_text)
    assert doc_type == DocumentType.EXPENSE_RECEIPT

    # 4. Unknown / Gibberish
    unk_text = "random text without any financial indicators xyz 123"
    doc_type, conf, probs = DocumentClassifier.classify_text(unk_text)
    assert doc_type == DocumentType.UNKNOWN


def test_extraction_mathematical_validation():
    """Verifies that line-item discrepancies are detected and flagged in validation errors."""
    ocr_out = RawOcrOutput(
        full_text=(
            "CASH MEMO\n"
            "Invoice #: INV-999\n"
            "Date: 2026-10-18\n"
            "Item: Rice 10kg, Qty: 1, Rate: 500.00, Total: 500.00\n"
            "Subtotal: 800.00\n"  # Discrepancy! Item total is 500, but subtotal claims 800
            "Total Amount: 800.00\n"
        ),
        blocks=[],
        detected_language="en",
    )
    extracted, confs, val_errors = StructuredDocumentExtractor.extract_fields(
        ocr_out, DocumentType.SALES_RECEIPT
    )

    assert extracted["invoice_number"] == "INV-999"
    assert extracted["date"] == "2026-10-18"
    assert len(val_errors) > 0
    assert any("Math mismatch" in err for err in val_errors)


def test_pipeline_router_and_idempotent_posting(db_session, seeded_shop_context):
    """
    Tests end-to-end pipeline:
    Upload -> Dynamic Form Selection -> Review Confirmation -> Ledger Save -> Idempotency Guard.
    """
    shop1 = seeded_shop_context["shop1"]
    user1 = seeded_shop_context["user1"]
    png_bytes = create_dummy_png_bytes()

    mock_text = (
        "CASH MEMO\n"
        "Invoice #: INV-AUTO-01\n"
        "Date: 2026-10-18\n"
        "Customer: Karim Ullah\n"
        "Item: Sugar 2kg, Qty: 2, Rate: 130.00, Total: 260.00\n"
        "Subtotal: 260.00\n"
        "Total Amount: 260.00\n"
        "Paid: 260.00\n"
        "Payment Method: cash\n"
    )
    router = DocumentPipelineRouter(ocr_provider=MockOcrProvider(mock_text))

    # 1. Process & Route
    routing = router.process_and_route(
        session=db_session,
        business_id=shop1.business_id,
        shop_id=shop1.id,
        file_bytes=png_bytes,
        original_filename="receipt_karim.png",
        user_id=user1.id,
    )

    assert routing.document_id > 0
    assert routing.predicted_doc_type == DocumentType.SALES_RECEIPT
    assert routing.target_form == "sales_form"
    assert routing.normalized_values["invoice_number"] == "INV-AUTO-01"
    assert routing.normalized_values["total_amount_minor"] == 26000  # 260.00 BDT in poisha

    # 2. Confirm and Post to Ledger
    confirmation = DocumentReviewConfirmation(
        document_id=routing.document_id,
        confirmed_doc_type=DocumentType.SALES_RECEIPT,
        final_values=routing.normalized_values,
        decision_action="approve_and_post",
        reviewer_notes="Verified by shop manager",
    )
    post_res = DocumentPostingService.post_confirmed_document(
        session=db_session,
        confirmation=confirmation,
        user_id=user1.id,
    )

    assert post_res["status"] == "posted"
    created_sale_id = post_res["created_record"]["id"]

    # Verify Sale in database
    sale = db_session.get(Sale, created_sale_id)
    assert sale is not None
    assert sale.invoice_number == "INV-AUTO-01"
    assert sale.total_amount_minor == 26000
    assert sale.document_id == routing.document_id

    # 3. Idempotency Test: Attempting to post the same document again must not create duplicate sales
    retry_res = DocumentPostingService.post_confirmed_document(
        session=db_session,
        confirmation=confirmation,
        user_id=user1.id,
    )
    assert retry_res["status"] == "already_posted"

    # Count sales with this document ID (must still be exactly 1)
    sales_count = db_session.query(Sale).filter_by(document_id=routing.document_id).count()
    assert sales_count == 1


def test_multilingual_document_extraction_chinese_fapiao_and_bengali_mushak():
    """Verifies regex and field extraction for Chinese Fapiao and Bengali Mushak-6.3 invoices."""
    # 1. Chinese Fapiao
    fapiao_text = (
        "电子发票 (普通发票)\n"
        "发票代码: 031001900111\n"
        "发票号码: 23442000000012345678\n"
        "开票日期: 2026-04-15\n"
        "购买方名称: 杭州科技有限公司\n"
        "合计金额: ¥ 128,500.00\n"
        "价税合计: ¥ 128,500.00\n"
    )
    ocr_zh = RawOcrOutput(full_text=fapiao_text, blocks=[], detected_language="zh")
    extracted_zh, _, val_errors_zh = StructuredDocumentExtractor.extract_fields(
        ocr_zh, DocumentType.PURCHASE_INVOICE
    )
    assert extracted_zh["invoice_number"] == "23442000000012345678"
    assert extracted_zh["date"] == "2026-04-15"
    assert extracted_zh["total_amount_minor"] == 12850000

    # 2. Bengali Mushak-6.3 VAT Challan
    mushak_text = (
        "গণপ্রজাতন্ত্রী বাংলাদেশ সরকার\n"
        "জাতীয় রাজস্ব বোর্ড\n"
        "কর চালানপত্র (মূসক-৬.৩)\n"
        "চালানপত্র নম্বর: CHALAN-2026-9901\n"
        "তারিখ: 2026-04-15\n"
        "বিক্রেতার নাম: রহিম এন্টারপ্রাইজ\n"
        "মোট মূল্য টাকা: 12,450.50\n"
    )
    ocr_bn = RawOcrOutput(full_text=mushak_text, blocks=[], detected_language="bn")
    extracted_bn, _, val_errors_bn = StructuredDocumentExtractor.extract_fields(
        ocr_bn, DocumentType.PURCHASE_INVOICE
    )
    assert extracted_bn["invoice_number"] == "CHALAN-2026-9901"
    assert extracted_bn["date"] == "2026-04-15"
    assert extracted_bn["total_amount_minor"] == 1245050

