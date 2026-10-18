"""
Reproducible Document Classification Evaluator and Baseline Benchmark.
Compares Heuristic Rule Classifier vs Majority Class vs Trained TF-IDF + Logistic Regression.
Generates confusion matrices, per-class F1, and confidence error analysis.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

from src.config import settings
from src.documents.classifier import DocumentClassifier
from src.documents.schemas import DocumentType
from src.evaluation.metrics import compute_classification_metrics
from src.evaluation.data_splitters import DataSplitter


# Labeled Corpus Generator for Empirical Benchmark
# Includes standard, dialectal, Bengali, and challenging ambiguous / corrupted samples
CORPUS_TEMPLATES = {
    DocumentType.SALES_RECEIPT.value: [
        "CASH MEMO {shop} Invoice #: INV-{num} Date: 2026-10-15 Item: Miniket Rice 25kg Qty: 1 Rate: 1850 Total: 1850 Paid: 1850 Cash",
        "SALES INVOICE Customer Copy Sold To: Rahim Mia Bill #: {num} Tangail Handloom Saree BDT 2400 Total: 2400 Paid via Mobile Banking",
        "ক্যাশ মেমো {shop} রসিদ নং: {num} তারিখ: ২০২৬-১০-১২ পণ্য: মিনিকেট চাল পরিমাণ: ১ দর: ১৯০০ টাকা মোট: ১৯০০ নগদ পরিশোধ",
        "POS RECEIPT Bhai Bhai Store Item: Soyabean Oil 5L x1 920.00 Subtotal: 920.00 Grand Total: 920.00 Thank You",
        "ক্যাশ মেমো ঢাকা বিরিয়ানি কাচ্চি বিরিয়ানি ২ প্লেট দর ৪৫০ মোট ৯০০ টাকা পরিশোধিত",
    ],
    DocumentType.PURCHASE_INVOICE.value: [
        "SUPPLIER INVOICE Pran Agro Distributorship Ltd Challan No: CH-{num} Tax Invoice Delivered to: {shop} Sugar 50kg Sack Total: 6500",
        "COMMERCIAL INVOICE Meghna Group Depot Purchase Order Ref: PO-8874 Goods: Edible Oil Barrels Net Payable: 45000 Payment Terms: Net 30",
        "সরবরাহ চালান ভেন্ডর বিল নং: {num} চালান মেসার্স হক ট্রেডার্স পণ্য: আটা ও ময়দা বস্তা মোট মূল্য: ১২৫০০ টাকা",
        "TAX INVOICE Square Pharmaceuticals Depot Bill of Supply To: Modern Pharmacy Medicine Batch Strip Total: 18400 Due: 30 Days",
        "ক্রয় চালান মেসার্স চৌধুরী এন্টারপ্রাইজ পাইকারি সরবরাহ ভাউচার নং {num} ডাল ও মসলা সামগ্রী মোট ৩০৫০০ টাকা",
    ],
    DocumentType.EXPENSE_RECEIPT.value: [
        "EXPENSE VOUCHER Commercial Premises Office Rent Receipt Month: October 2026 Amount: 35000 BDT Paid by: Cheque Approved by: Owner",
        "DEBIT VOUCHER Petty Cash Office Supplies Stationery A4 Paper Toner Cartridge Total: 2400 Paid: Cash",
        "ELECTRICITY BILL DESCO Monthly Power Consumption Bill Account No: 1982736 Amount: 8450 Paid through bKash",
        "খরচ ভাউচার দোকান ঘর ভাড়া রসিদ মাস: অক্টোবর টাকা: ২৫০০০ পরিষদিত",
        "বেতন রসিদ স্টাফ মাসিক বেতন ভাউচার নাম: মো: করিম পদবি: সেলসম্যান টাকা: ১২০০০",
    ],
    DocumentType.PAYMENT_RECEIPT.value: [
        "MONEY RECEIPT Received with thanks from Karim Ullah BDT 15,000 for Sale Invoice settlement Payment Method: Cash Signed by: Cashier",
        "BANK DEPOSIT SLIP Islami Bank Bangladesh Ltd Account Credit: 205018274 Amount: 50,000 In words: Fifty Thousand Taka Only",
        "PAYMENT VOUCHER Supplier Payment Acknowledgment To: ACI Logistics Ref: BILL-102 Amount: 22000 Paid by Bank Transfer",
        "টাকা প্রাপ্তি রসিদ মেসার্স রহমান এন্টারপ্রাইজ জমা গ্রহণ করিলাম টাকা: ২০,০০০ পেমেন্ট মাধ্যম: নগদ",
        "ACKNOWLEDGMENT RECEIPT Customer balance settlement received BDT 4500 via Nagad TrxID: 98J29A",
    ],
    DocumentType.UNKNOWN.value: [
        "General company memorandum regarding upcoming national holiday schedule and office timing.",
        "Product warranty card instructions please keep this leaflet safe for servicing terms and conditions.",
        "অনুরোধ পত্র আগামী রবিবারের সাধারণ সভা সম্পর্কিত বিজ্ঞপ্তি সদস্যবৃন্দের উপস্থিতি কাম্য।",
        "Random noisy unreadable OCR text fragments: @@## %% asdf 98723 kjhsdf ;;-- ===",
        "User manual troubleshooting guide check cable connection before contacting technical helpline.",
    ],
}


def build_evaluation_dataset(samples_per_class: int = 40, seed: int = 42) -> List[Dict[str, Any]]:
    """Generates a balanced, randomized evaluation dataset of document texts."""
    rng = random.Random(seed)
    dataset = []
    sample_id = 1
    shops = ["Bismillah Store", "Al-Madina General Store", "Style Zone", "Care Pharmacy"]

    for doc_class, templates in CORPUS_TEMPLATES.items():
        for i in range(samples_per_class):
            tpl = templates[i % len(templates)]
            shop = rng.choice(shops)
            num = f"{rng.randint(1000, 9999)}"
            text = tpl.replace("{shop}", shop).replace("{num}", num)

            # Add subtle natural perturbations (variations in casing / noise)
            if rng.random() < 0.20 and doc_class != DocumentType.UNKNOWN.value:
                text = text.upper() if rng.random() < 0.5 else text.lower()

            dataset.append({
                "sample_id": sample_id,
                "document_class": doc_class,
                "text": text,
            })
            sample_id += 1

    rng.shuffle(dataset)
    return dataset


class DocumentClassificationEvaluator:
    """Executes comparative evaluation across classification models."""

    @classmethod
    def run_benchmark(cls, seed: int = 42) -> Dict[str, Any]:
        dataset = build_evaluation_dataset(samples_per_class=40, seed=seed)

        # 1. Stratified Partitioning (70% Train, 15% Val, 15% Test)
        train_set, val_set, test_set = DataSplitter.stratified_train_val_test_split(
            samples=dataset,
            target_field="document_class",
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15,
            seed=seed,
        )

        all_classes = [
            DocumentType.SALES_RECEIPT.value,
            DocumentType.PURCHASE_INVOICE.value,
            DocumentType.EXPENSE_RECEIPT.value,
            DocumentType.PAYMENT_RECEIPT.value,
            DocumentType.UNKNOWN.value,
        ]

        y_test_true = [s["document_class"] for s in test_set]

        # ----------------------------------------------------------------------
        # Model 1: Majority Class Baseline
        # ----------------------------------------------------------------------
        train_classes = [s["document_class"] for s in train_set]
        majority_class = max(set(train_classes), key=train_classes.count)
        y_pred_majority = [majority_class] * len(test_set)
        metrics_majority = compute_classification_metrics(y_test_true, y_pred_majority, labels=all_classes)

        # ----------------------------------------------------------------------
        # Model 2: Heuristic Rule Classifier (Current System Implementation)
        # ----------------------------------------------------------------------
        y_pred_heuristic = []
        heuristic_confidences = []
        for s in test_set:
            pred_type, conf, _ = DocumentClassifier.classify_text(s["text"])
            y_pred_heuristic.append(pred_type.value)
            heuristic_confidences.append(conf)

        metrics_heuristic = compute_classification_metrics(y_test_true, y_pred_heuristic, labels=all_classes)

        # ----------------------------------------------------------------------
        # Model 3: Statistical Baseline: TF-IDF + Logistic Regression
        # Trained strictly on Train Split, evaluated on Test Split
        # ----------------------------------------------------------------------
        vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
        X_train_vec = vectorizer.fit_transform([s["text"] for s in train_set])
        y_train = [s["document_class"] for s in train_set]

        clf = LogisticRegression(C=1.0, max_iter=200, random_state=seed)
        clf.fit(X_train_vec, y_train)

        X_test_vec = vectorizer.transform([s["text"] for s in test_set])
        y_pred_tfidf = list(clf.predict(X_test_vec))
        metrics_tfidf = compute_classification_metrics(y_test_true, y_pred_tfidf, labels=all_classes)

        # Confidence error analysis for Heuristic
        confidence_errors = []
        for s, pred, conf in zip(test_set, y_pred_heuristic, heuristic_confidences):
            if pred != s["document_class"]:
                confidence_errors.append({
                    "sample_id": s["sample_id"],
                    "ground_truth": s["document_class"],
                    "predicted": pred,
                    "confidence": conf,
                    "text_preview": s["text"][:80] + "...",
                })

        report = {
            "evaluation_task": "document_classification",
            "seed": seed,
            "dataset": {
                "total_samples": len(dataset),
                "train_samples": len(train_set),
                "val_samples": len(val_set),
                "test_samples": len(test_set),
                "classes": all_classes,
            },
            "models": {
                "majority_class_baseline": {
                    "model_name": f"MajorityClass ({majority_class})",
                    "metrics": metrics_majority,
                },
                "heuristic_rule_classifier": {
                    "model_name": "Heuristic-TFIDF-Classifier (Rule Baseline)",
                    "metrics": metrics_heuristic,
                    "confidence_error_count": len(confidence_errors),
                    "error_examples": confidence_errors[:5],
                },
                "tfidf_logistic_regression": {
                    "model_name": "Trained TF-IDF + Logistic Regression (Statistical ML)",
                    "metrics": metrics_tfidf,
                },
            },
        }

        # Save machine-readable and human-readable reports
        cls._export_reports(report)
        return report

    @classmethod
    def _export_reports(cls, report: Dict[str, Any]) -> None:
        out_dir = settings.STORAGE_DIR / "evaluations"
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "classification_benchmark.json"
        json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        # Markdown Report
        md = [
            "# Document Classification Evaluation & Model Benchmark Report",
            f"**Dataset:** {report['dataset']['total_samples']} samples (Train: {report['dataset']['train_samples']}, Val: {report['dataset']['val_samples']}, Test: {report['dataset']['test_samples']})  ",
            f"**Random Seed:** {report['seed']} | **Classes:** {len(report['dataset']['classes'])}  ",
            "",
            "## 1. Overall Performance Comparison",
            "",
            "| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 | Status |",
            "| :--- | :---: | :---: | :---: | :---: | :---: |",
        ]

        for key, m in report["models"].items():
            met = m["metrics"]
            status = "Trained ML" if "tfidf" in key else ("Rule Baseline" if "heuristic" in key else "Naive Baseline")
            md.append(
                f"| **{m['model_name']}** | {met['accuracy'] * 100:.2f}% | {met['macro_precision'] * 100:.2f}% | {met['macro_recall'] * 100:.2f}% | **{met['macro_f1'] * 100:.2f}%** | `{status}` |"
            )

        md.append("")
        md.append("## 2. Per-Class F1 Breakdown (Current Heuristic vs Trained ML)")
        md.append("")
        md.append("| Document Class | Heuristic F1 | Trained TF-IDF F1 | Support (Test) |")
        md.append("| :--- | :---: | :---: | :---: |")

        h_class = report["models"]["heuristic_rule_classifier"]["metrics"]["per_class"]
        ml_class = report["models"]["tfidf_logistic_regression"]["metrics"]["per_class"]

        for c in report["dataset"]["classes"]:
            h_f1 = h_class[c]["f1"] * 100
            ml_f1 = ml_class[c]["f1"] * 100
            sup = h_class[c]["support"]
            md.append(f"| `{c}` | {h_f1:.1f}% | {ml_f1:.1f}% | {sup} |")

        md.append("")
        md.append("## 3. Confusion Matrix (Current Heuristic Classifier)")
        md.append("```json")
        md.append(json.dumps(report["models"]["heuristic_rule_classifier"]["metrics"]["confusion_matrix"], indent=2))
        md.append("```")

        md_path = out_dir / "classification_benchmark.md"
        md_path.write_text("\n".join(md), encoding="utf-8")
        print(f"Classification benchmark exported to {json_path} and {md_path}")


if __name__ == "__main__":
    rep = DocumentClassificationEvaluator.run_benchmark(seed=42)
    print("Benchmark complete. Models evaluated:", list(rep["models"].keys()))
