"""
Document Classification Module.
Classifies SME financial documents across Bengali, English, and Mixed formats.
Supports sales receipts, supplier invoices, expense bills, and payment receipts.
"""

from __future__ import annotations

import re
from typing import Tuple, Dict, Any
from src.documents.schemas import DocumentType


class DocumentClassifier:
    """
    Modular classifier with explainable keyword-weighting and statistical feature matching.
    Provides confidence scores and full class probability distributions.
    """

    # Keyword indicators with relative importance weights
    KEYWORD_WEIGHTS = {
        DocumentType.SALES_RECEIPT: {
            "cash memo": 3.0,
            "sales receipt": 3.0,
            "sales invoice": 2.5,
            "bill to customer": 2.5,
            "customer copy": 2.0,
            "pos receipt": 3.0,
            "sold to": 2.0,
            "ক্যাশ মেমো": 3.5,
            "বিক্রয় রসিদ": 3.5,
            "গ্রাহক কপি": 2.5,
            "নগদ রসিদ": 2.5,
        },
        DocumentType.PURCHASE_INVOICE: {
            "purchase invoice": 3.5,
            "tax invoice": 3.0,
            "supplier invoice": 3.5,
            "commercial invoice": 3.0,
            "bill of supply": 2.5,
            "challan": 2.0,
            "purchase order ref": 2.5,
            "চালান": 3.5,
            "ক্রয় চালান": 3.5,
            "সরবরাহকারী": 2.5,
            "ভেন্ডর বিল": 3.0,
        },
        DocumentType.EXPENSE_RECEIPT: {
            "expense voucher": 3.5,
            "debit voucher": 3.0,
            "petty cash": 3.0,
            "rent receipt": 3.5,
            "utility bill": 3.5,
            "electricity bill": 3.0,
            "salary slip": 3.0,
            "office supplies": 2.0,
            "ভাউচার": 3.0,
            "খরচ বিল": 3.5,
            "বাড়ি ভাড়া": 3.5,
            "বিদ্যুৎ বিল": 3.5,
            "বেতন": 3.0,
        },
        DocumentType.PAYMENT_RECEIPT: {
            "payment receipt": 3.5,
            "money receipt": 3.5,
            "payment voucher": 3.0,
            "received with thanks": 3.0,
            "bank deposit slip": 3.5,
            "acknowledgment receipt": 2.5,
            "টাকা প্রাপ্তি রসিদ": 3.5,
            "পেমেন্ট রসিদ": 3.5,
            "জমা স্লিপ": 3.5,
        },
    }

    @classmethod
    def classify_text(cls, text: str) -> Tuple[DocumentType, float, Dict[str, float]]:
        """
        Classifies OCR text into a document type.
        Returns: (predicted_type, confidence_score, probabilities_dict)
        """
        if not text or len(text.strip()) < 5:
            return DocumentType.UNKNOWN, 0.0, {t.value: 0.0 for t in DocumentType}

        text_lower = text.lower()
        raw_scores: Dict[DocumentType, float] = {
            DocumentType.SALES_RECEIPT: 0.1,
            DocumentType.PURCHASE_INVOICE: 0.1,
            DocumentType.EXPENSE_RECEIPT: 0.1,
            DocumentType.PAYMENT_RECEIPT: 0.1,
        }

        # Accumulate keyword weights
        for doc_type, keywords in cls.KEYWORD_WEIGHTS.items():
            for kw, weight in keywords.items():
                if kw in text_lower:
                    raw_scores[doc_type] += weight

        # Check total presence of numbers and line items
        has_items = bool(re.search(r"\b(qty|quantity|pcs|পরিমাণ|দর|দাম|rate|price)\b", text_lower))
        if has_items:
            raw_scores[DocumentType.SALES_RECEIPT] += 1.0
            raw_scores[DocumentType.PURCHASE_INVOICE] += 1.0

        total_score = sum(raw_scores.values())
        if total_score <= 0.5:
            return DocumentType.UNKNOWN, 0.3, {t.value: 0.2 for t in DocumentType}

        # Normalize probabilities (Softmax-like)
        probabilities = {
            doc_type.value: round(score / total_score, 4)
            for doc_type, score in raw_scores.items()
        }
        probabilities[DocumentType.UNKNOWN.value] = round(
            max(0.0, 1.0 - max(probabilities.values())), 4
        )

        best_type = max(raw_scores, key=raw_scores.get)
        best_prob = probabilities[best_type.value]

        # If highest confidence is too weak (< 0.45), classify as UNKNOWN
        if best_prob < 0.45:
            return DocumentType.UNKNOWN, round(best_prob, 2), probabilities

        return best_type, round(best_prob, 2), probabilities
