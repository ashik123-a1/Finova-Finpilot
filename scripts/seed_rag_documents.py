"""
Seeds realistic commercial documents and indexes vector chunks for RAG Copilot.
Enforces multi-tenant isolation by binding chunks strictly to Business #19 (Bismillah Store).
"""

from __future__ import annotations

import json
from src.database.connection import SessionLocal
from src.database.models import Business, Shop, Document, DocumentClassification, DocumentExtraction
from src.ai.rag_service import RagService


def seed_demo_rag_documents():
    with SessionLocal() as session:
        # Find business #19 or first business
        biz = session.query(Business).filter_by(id=19).first() or session.query(Business).first()
        if not biz:
            print("No business found in database.")
            return

        shop = session.query(Shop).filter_by(business_id=biz.id).first()
        shop_id = shop.id if shop else None

        print(f"Seeding RAG documents for Business #{biz.id} ({biz.name}), Shop #{shop_id}...")

        sample_docs = [
            {
                "title": "Mushak 6.3 VAT Tax Invoice / 增值税专用发票 - Bengal Packaging Ltd",
                "filename": "Mushak-6.3-INV-2026-08.pdf",
                "content": (
                    "NBR Mushak 6.3 Tax Invoice (জাতীয় রাজস্ব বোর্ড মূসক ৬.৩ চালান / 增值税专用发票). "
                    "Seller: Bengal Packaging Industries Ltd, BIN: 001928374-0101 (纳税人识别号). "
                    "Buyer: Bismillah Store, Road 27 Dhanmondi. Item: Eco Kraft Paper Bags 5000 pcs, Rate: 4.50 BDT, "
                    "Subtotal: 22,500.00 BDT. VAT (15% standard rate / 增值税税率 15%): 3,375.00 BDT. Total Payable: 25,875.00 BDT. "
                    "Payment Terms: 30 days net credit (৩০ দিনের বাকির সুবিধা). Mushak Challan No: CH-2026-9812. Line item status: Verified."
                ),
                "metadata": {"type": "tax_invoice", "vat_rate": "15%", "seller": "Bengal Packaging Industries"},
                "classification": {"type": "purchase_invoice", "confidence": 0.98},
                "extraction": {
                    "invoice_number": "CH-2026-9812",
                    "date": "2026-08-15",
                    "supplier_name": "Bengal Packaging Industries Ltd",
                    "customer_name": "Bismillah Store",
                    "payee": "Bengal Packaging Industries Ltd",
                    "subtotal_minor": 2250000,
                    "tax_minor": 337500,
                    "discount_minor": 0,
                    "total_amount_minor": 2587500,
                    "paid_amount_minor": 2587500,
                    "payment_method": "credit",
                },
            },
            {
                "title": "DESCO Commercial Electricity Utility Bill / ডেসকো বাণিজ্যিক বিদ্যুৎ বিল - Shop 28",
                "filename": "DESCO-Utility-Bill-Sep2026.pdf",
                "content": (
                    "Dhaka Electric Supply Company (DESCO / ডেসকো বিদ্যুৎ বিল) Commercial Tariff Category E. Account No: 8819-2041-09. "
                    "Consumer: Bismillah Store Main Branch. Period: September 2026. Units Consumed: 1,420 kWh. "
                    "Demand Charge: 1,200.00 BDT. Energy Charge: 14,910.00 BDT. VAT (5%): 805.50 BDT. "
                    "Total Net Bill: 16,915.50 BDT. Due Date: 2026-10-25. Status: Auto-debit scheduled."
                ),
                "metadata": {"type": "utility_bill", "utility": "electricity", "provider": "DESCO"},
                "classification": {"type": "expense_receipt", "confidence": 0.96},
                "extraction": {
                    "invoice_number": "BILL-8819-2041-09",
                    "date": "2026-09-30",
                    "supplier_name": "DESCO Electricity Supply",
                    "customer_name": "Bismillah Store",
                    "payee": "DESCO Electricity Supply",
                    "subtotal_minor": 1611000,
                    "tax_minor": 80550,
                    "discount_minor": 0,
                    "total_amount_minor": 1691550,
                    "paid_amount_minor": 1691550,
                    "payment_method": "auto_debit",
                },
            },
            {
                "title": "Supplier Procurement Agreement - Pran Agro Foods Ltd / প্রাণ এগ্রো ফুডস সরবরাহকারী চুক্তি",
                "filename": "Agreement-Pran-Foods-2026.pdf",
                "content": (
                    "Annual Wholesale Distribution Agreement. Supplier: Pran Agro Foods Ltd (প্রাণ এগ্রো ফুডস লিঃ). "
                    "Authorized Retailer: Bismillah Store. "
                    "Payment terms: 15-day revolving credit line with 2% discount for payments cleared within 5 business days "
                    "(১৫ দিনের ঘূর্ণায়মান বাকির শর্তাবলী এবং ৫ দিনের মধ্যে পরিশোধে ২% ছাড়). "
                    "Maximum credit exposure limit: ৳ 500,000 (সর্বোচ্চ বাকির সীমা ৫ লক্ষ টাকা). Minimum weekly order: ৳ 25,000. "
                    "Damaged or expired packaging accepted within 7 days of delivery inspection."
                ),
                "metadata": {"type": "supplier_agreement", "supplier": "Pran Agro Foods", "credit_limit": "500000"},
                "classification": {"type": "purchase_invoice", "confidence": 0.95},
                "extraction": {
                    "invoice_number": "AGR-PRAN-2026",
                    "date": "2026-01-01",
                    "supplier_name": "Pran Agro Foods Ltd",
                    "customer_name": "Bismillah Store",
                    "payee": "Pran Agro Foods Ltd",
                    "subtotal_minor": 50000000,
                    "tax_minor": 0,
                    "discount_minor": 0,
                    "total_amount_minor": 50000000,
                    "paid_amount_minor": 0,
                    "payment_method": "credit",
                },
            },
            {
                "title": "BRAC Bank SME Shonchoy Loan Facility Sanction Letter / ব্র্যাক ব্যাংক এসএমই ঋণ মঞ্জুরিপত্র",
                "filename": "BRAC-SME-Loan-Sanction-Letter.pdf",
                "content": (
                    "BRAC Bank Small & Medium Enterprise Banking Division (ব্র্যাক ব্যাংক এসএমই ঋণ মঞ্জুরিপত্র). "
                    "Borrower: Bismillah Store. Approved Facility: ৳ 800,000 Working Capital Term Loan. "
                    "Annual Interest Rate: 11.5% Reducing Balance. Monthly Installment (EMI): ৳ 37,458 over 24 months. "
                    "Required DSCR covenant: 1.25x minimum debt service coverage (ন্যূনতম ১.২৫ গুণ ডিএসসিআর শর্ত). "
                    "Collateral: Hypothecation of inventory and book debts."
                ),
                "metadata": {"type": "loan_sanction", "lender": "BRAC Bank", "facility_minor": 80000000},
                "classification": {"type": "payment_receipt", "confidence": 0.99},
                "extraction": {
                    "invoice_number": "SME-LN-800K-2026",
                    "date": "2026-06-15",
                    "supplier_name": "BRAC Bank SME Banking",
                    "customer_name": "Bismillah Store",
                    "payee": "BRAC Bank SME Banking",
                    "subtotal_minor": 80000000,
                    "tax_minor": 0,
                    "discount_minor": 0,
                    "total_amount_minor": 80000000,
                    "paid_amount_minor": 80000000,
                    "payment_method": "bank_transfer",
                },
            },
        ]

        total_chunks = 0
        for doc_info in sample_docs:
            # Check or create document entry
            doc = session.query(Document).filter_by(
                business_id=biz.id,
                original_filename=doc_info["filename"]
            ).first()
            if not doc:
                doc = Document(
                    business_id=biz.id,
                    shop_id=shop_id,
                    original_filename=doc_info["filename"],
                    stored_path=f"storage/documents/{doc_info['filename']}",
                    file_hash_sha256=f"hash_{hash(doc_info['filename'])}",
                    file_size_bytes=len(doc_info["content"].encode("utf-8")),
                    mime_type="application/pdf",
                    detected_language="en",
                    status="posted",
                    is_synthetic=True,
                )
                session.add(doc)
                session.flush()

            # Ensure classification exists
            if not doc.classification and "classification" in doc_info:
                cls_data = doc_info["classification"]
                cls_rec = DocumentClassification(
                    document_id=doc.id,
                    predicted_doc_type=cls_data["type"],
                    confidence_score=cls_data["confidence"],
                    classifier_model_version="rule_tfidf_v1",
                    raw_predictions_json="{}",
                )
                session.add(cls_rec)

            # Ensure extraction exists
            if not doc.extraction and "extraction" in doc_info:
                ext_data = doc_info["extraction"]
                ext_rec = DocumentExtraction(
                    document_id=doc.id,
                    raw_ocr_text=doc_info["content"],
                    raw_ocr_blocks_json="[]",
                    structured_data_json=json.dumps(ext_data),
                    normalized_data_json=json.dumps(ext_data),
                    field_confidences_json=json.dumps({"total_amount_minor": 0.95, "supplier_name": 0.95}),
                    validation_errors_json="[]",
                    extraction_model_version="rapidocr_pipeline_v1",
                )
                session.add(ext_rec)

            # Ingest chunks
            chunks_saved = RagService.ingest_document(
                session=session,
                business_id=biz.id,
                shop_id=shop_id,
                document_id=doc.id,
                title=doc_info["title"],
                content=doc_info["content"],
                metadata=doc_info["metadata"],
            )
            total_chunks += chunks_saved

        session.commit()
        print(f"Successfully seeded {len(sample_docs)} documents with {total_chunks} vector chunks!")


if __name__ == "__main__":
    seed_demo_rag_documents()
