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

    # Keyword indicators with relative importance weights (Multilingual: EN, BN, ZH, AR, ES, HI)
    KEYWORD_WEIGHTS = {
        DocumentType.SALES_RECEIPT: {
            # English
            "cash memo": 3.0,
            "cashmemo": 3.0,
            "sales receipt": 3.0,
            "salesreceipt": 3.0,
            "sales invoice": 2.5,
            "salesinvoice": 2.5,
            "bill to customer": 2.5,
            "customer copy": 2.0,
            "pos receipt": 3.0,
            "sold to": 2.0,
            # Bengali
            "ক্যাশ মেমো": 3.5,
            "ক্যাশমেমো": 3.5,
            "বিক্রয় রসিদ": 3.5,
            "বিক্রয় রসিদ": 3.5,
            "বিক্রয়": 2.0,
            "বিক্রয়": 2.0,
            "গ্রাহক কপি": 2.5,
            "নগদ রসিদ": 2.5,
            # Chinese
            "销售发票": 3.5,
            "普通发票": 3.0,
            "收银小票": 3.5,
            "销售清单": 3.0,
            "销售收据": 3.5,
            "结账单": 2.5,
            # Arabic
            "فاتورة مبيعات": 3.5,
            "إيصال بيع": 3.5,
            "إيصال نقدي": 3.0,
            "سند قبض مبيعات": 3.0,
            # Spanish
            "recibo de venta": 3.5,
            "ticket de venta": 3.5,
            "factura simplificada": 3.0,
            # Hindi
            "बिक्री रसीद": 3.5,
            "कैश मेमो": 3.5,
            "बिक्री बिल": 3.0,
        },
        DocumentType.PURCHASE_INVOICE: {
            # English
            "purchase invoice": 3.5,
            "purchaseinvoice": 3.5,
            "tax invoice": 3.0,
            "taxinvoice": 3.0,
            "supplier invoice": 3.5,
            "commercial invoice": 3.0,
            "bill of supply": 2.5,
            "challan": 2.0,
            "purchase order ref": 2.5,
            "deed of sale": 4.0,
            "deed": 3.0,
            "sale deed": 3.5,
            "consideration": 3.0,
            "agreement": 3.0,
            "procurement agreement": 3.5,
            # Bengali
            "চালান": 3.5,
            "ক্রয় চালান": 3.5,
            "ক্রয় চালান": 3.5,
            "ক্রয়": 2.0,
            "ক্রয়": 2.0,
            "সরবরাহকারী": 2.5,
            "ভেন্ডর বিল": 3.0,
            "দলিল": 3.5,
            "চুক্তি": 3.0,
            "বিক্রয় দলিল": 4.0,
            # Chinese
            "增值税专用发票": 3.5,
            "采购发票": 3.5,
            "进项发票": 3.5,
            "采购订单": 3.0,
            "供货发票": 3.0,
            # Arabic
            "فاتورة ضريبية": 3.5,
            "فاتورة مشتريات": 3.5,
            "فاتورة شراء": 3.5,
            "فاتورة مورد": 3.0,
            # Spanish
            "factura de compra": 3.5,
            "factura proveedor": 3.5,
            "albarán": 2.5,
            # Hindi
            "खरीद चालान": 3.5,
            "कर चालान": 3.5,
            "टैक्स इनवॉइस": 3.0,
        },
        DocumentType.EXPENSE_RECEIPT: {
            # English
            "expense voucher": 3.5,
            "expensevoucher": 3.5,
            "petty expense": 3.5,
            "pettyexpense": 3.5,
            "expense receipt": 3.5,
            "expensereceipt": 3.5,
            "debit voucher": 3.0,
            "debit slip": 3.0,
            "petty cash": 3.0,
            "rent receipt": 3.5,
            "utility bill": 3.5,
            "electricity bill": 3.0,
            "desco": 3.5,
            "utility": 3.0,
            "salary slip": 3.0,
            "office supplies": 2.0,
            # Bengali
            "ভাউচার": 3.0,
            "দোকান খরচ": 3.5,
            "খরচ": 2.5,
            "খরচ বিল": 3.5,
            "বাড়ি ভাড়া": 3.5,
            "বিদ্যুৎ বিল": 3.5,
            "বেতন": 3.0,
            # Chinese
            "费用报销单": 3.5,
            "支出凭单": 3.5,
            "日常报销": 3.0,
            "差旅费": 3.0,
            "水电费收据": 3.5,
            "房租收据": 3.5,
            # Arabic
            "سند صرف": 3.5,
            "سند صرف نفقات": 3.5,
            "مصروفات تشغيلية": 3.0,
            "فاتورة خدمات": 3.0,
            "إيصال إيجار": 3.5,
            # Spanish
            "comprobante de gasto": 3.5,
            "recibo de gastos": 3.5,
            "vale de caja": 3.0,
            "recibo de alquiler": 3.5,
            # Hindi
            "खर्च वाउचर": 3.5,
            "व्यय रसीद": 3.5,
            "किराया रसीद": 3.5,
            "बिजली बिल": 3.0,
        },
        DocumentType.PAYMENT_RECEIPT: {
            # English
            "payment receipt": 3.5,
            "paymentreceipt": 3.5,
            "money receipt": 3.5,
            "moneyreceipt": 3.5,
            "payment voucher": 3.0,
            "received with thanks": 3.0,
            "bank deposit slip": 3.5,
            "acknowledgment receipt": 2.5,
            "loan sanction": 4.0,
            "sanction letter": 4.0,
            "credit facility": 3.5,
            "loan": 3.0,
            # Bengali
            "টাকা প্রাপ্তি রসিদ": 3.5,
            "টাকা জমার রসিদ": 3.5,
            "পেমেন্ট রসিদ": 3.5,
            "জমা স্লিপ": 3.5,
            # Chinese
            "收款收据": 3.5,
            "收款凭单": 3.5,
            "交款单": 3.0,
            "付款确认书": 3.0,
            "银行汇款凭条": 3.5,
            # Arabic
            "سند قبض": 3.5,
            "إيصال دفع": 3.5,
            "إيصال استلام نقدية": 3.5,
            "إشعار تحويل بنكي": 3.0,
            # Spanish
            "recibo de pago": 3.5,
            "comprobante de pago": 3.5,
            "justificante de pago": 3.0,
            # Hindi
            "भुगतान रसीद": 3.5,
            "जमा रसीद": 3.5,
            "पेमेंट रसीद": 3.5,
            "बैंक जमा पर्ची": 3.0,
        },
    }

    _model = None
    _model_loaded = False

    @classmethod
    def _get_model(cls) -> Any:
        """Lazily loads the trained statistical model pipeline if available."""
        if not cls._model_loaded:
            cls._model_loaded = True
            try:
                from pathlib import Path
                import joblib
                model_path = Path("storage/models/document_classifier.joblib")
                if model_path.exists():
                    cls._model = joblib.load(model_path)
            except Exception:
                cls._model = None
        return cls._model

    @classmethod
    def classify_text(cls, text: str) -> Tuple[DocumentType, float, Dict[str, float]]:
        """
        Classifies OCR text into a document type using statistical model when available,
        with graceful fallback to explainable keyword-weighting.
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
        rule_type = max(raw_scores, key=raw_scores.get)
        rule_has_match = (total_score > 0.5)

        # Normalize probabilities (Softmax-like)
        rule_probabilities = {
            doc_type.value: round(score / total_score, 4)
            for doc_type, score in raw_scores.items()
        }
        rule_probabilities[DocumentType.UNKNOWN.value] = round(
            max(0.0, 1.0 - max(rule_probabilities.values())), 4
        )
        rule_conf = rule_probabilities[rule_type.value]

        # Use statistical model if available
        model = cls._get_model()
        if model is not None:
            try:
                probs = model.predict_proba([text])[0]
                classes = model.classes_
                prob_dict = {str(c): round(float(p), 4) for c, p in zip(classes, probs)}
                for t in DocumentType:
                    if t.value not in prob_dict:
                        prob_dict[t.value] = 0.0

                best_class = str(model.predict([text])[0])
                stat_conf = float(max(probs))

                # Combine confidence: if rule agrees with statistical model, boost confidence
                if rule_has_match and rule_type.value == best_class:
                    final_conf = max(stat_conf, rule_conf)
                elif rule_has_match and rule_conf >= 0.70:
                    best_class = rule_type.value
                    final_conf = rule_conf
                else:
                    final_conf = stat_conf

                if final_conf < 0.45 or best_class == DocumentType.UNKNOWN.value:
                    return DocumentType.UNKNOWN, round(final_conf, 2), prob_dict

                try:
                    return DocumentType(best_class), round(final_conf, 2), prob_dict
                except ValueError:
                    return DocumentType.UNKNOWN, round(final_conf, 2), prob_dict
            except Exception:
                pass  # Fall back to heuristic rule classifier

        if not rule_has_match or rule_conf < 0.45:
            return DocumentType.UNKNOWN, 0.30, rule_probabilities

        return rule_type, round(rule_conf, 2), rule_probabilities

    @classmethod
    def predict(cls, text: str) -> Tuple[DocumentType, float, Dict[str, float]]:
        """Convenience alias for classify_text."""
        return cls.classify_text(text)

    @classmethod
    def classify(cls, text: str) -> Tuple[DocumentType, float, Dict[str, float]]:
        """Convenience alias for classify_text."""
        return cls.classify_text(text)

