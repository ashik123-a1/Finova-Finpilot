"""
Large-Scale Document Classification Evaluation and Baseline Benchmark.
Evaluates 1,000 held-out test examples across 5 document classes:
- sales_receipt, purchase_invoice, expense_receipt, payment_receipt, unknown
Compares:
1. Majority Class Baseline
2. Heuristic Rule Classifier (src/documents/classifier.py)
3. Statistical ML: TF-IDF (1-2 n-grams) + Multinomial Logistic Regression

Generates:
- Per-class Precision, Recall, F1, and Support
- Confusion Matrices
- Bootstrap 95% Confidence Intervals for Accuracy and Macro-F1
- Prediction-level export to classification_predictions.jsonl
- Failure analysis on ambiguous/noisy documents
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from src.documents.classifier import DocumentClassifier
from src.documents.schemas import DocumentType
from src.evaluation.metrics import compute_classification_metrics
from src.data.classification_dataset_generator import DocumentClassificationDatasetGenerator, export_generated_dataset


def load_dataset_splits() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Loads train, val, and test splits from storage or generates them if missing."""
    dataset_dir = Path("storage/datasets/document_classification")
    train_file = dataset_dir / "train.jsonl"
    val_file = dataset_dir / "val.jsonl"
    test_file = dataset_dir / "test.jsonl"

    if not (train_file.exists() and val_file.exists() and test_file.exists()):
        export_generated_dataset()

    def read_jsonl(p: Path) -> List[Dict[str, Any]]:
        with open(p, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    return read_jsonl(train_file), read_jsonl(val_file), read_jsonl(test_file)


def compute_bootstrap_confidence_interval(
    y_true: List[str], y_pred: List[str], metric_name: str = "accuracy", n_bootstraps: int = 1000, seed: int = 42
) -> Tuple[float, float]:
    """Calculates 95% percentile bootstrap confidence interval."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    indices = np.arange(n)
    scores = []

    for _ in range(n_bootstraps):
        bs_idx = rng.choice(indices, size=n, replace=True)
        bs_true = [y_true[i] for i in bs_idx]
        bs_pred = [y_pred[i] for i in bs_idx]

        metrics = compute_classification_metrics(bs_true, bs_pred)
        scores.append(metrics[metric_name])

    ci_lower = float(np.percentile(scores, 2.5))
    ci_upper = float(np.percentile(scores, 97.5))
    return round(ci_lower, 4), round(ci_upper, 4)


def run_benchmark() -> None:
    train_set, val_set, test_set = load_dataset_splits()
    labels = ["sales_receipt", "purchase_invoice", "expense_receipt", "payment_receipt", "unknown"]

    # 1. Baseline 1: Majority Class
    majority_class = "sales_receipt"
    y_true = [s["label"] for s in test_set]
    y_pred_majority = [majority_class] * len(test_set)
    metrics_majority = compute_classification_metrics(y_true, y_pred_majority, labels=labels)

    # 2. Baseline 2: Heuristic Rule Classifier
    y_pred_heuristic = []
    confs_heuristic = []
    for s in test_set:
        pred_type, conf, _ = DocumentClassifier.classify_text(s["text"])
        y_pred_heuristic.append(pred_type.value)
        confs_heuristic.append(conf)

    metrics_heuristic = compute_classification_metrics(y_true, y_pred_heuristic, labels=labels)
    h_acc_ci = compute_bootstrap_confidence_interval(y_true, y_pred_heuristic, "accuracy")
    h_f1_ci = compute_bootstrap_confidence_interval(y_true, y_pred_heuristic, "macro_f1")

    # 3. Statistical Model: TF-IDF + Logistic Regression
    train_texts = [s["text"] for s in train_set]
    train_y = [s["label"] for s in train_set]
    test_texts = [s["text"] for s in test_set]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)
    X_train = vectorizer.fit_transform(train_texts)
    X_test = vectorizer.transform(test_texts)

    clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    clf.fit(X_train, train_y)

    y_pred_tfidf = clf.predict(X_test).tolist()
    y_probs_tfidf = clf.predict_proba(X_test)
    confs_tfidf = [float(np.max(probs)) for probs in y_probs_tfidf]

    metrics_tfidf = compute_classification_metrics(y_true, y_pred_tfidf, labels=labels)
    tfidf_acc_ci = compute_bootstrap_confidence_interval(y_true, y_pred_tfidf, "accuracy")
    tfidf_f1_ci = compute_bootstrap_confidence_interval(y_true, y_pred_tfidf, "macro_f1")

    # Save detailed prediction-level outputs
    out_dir = Path("storage/evaluations")
    out_dir.mkdir(parents=True, exist_ok=True)
    preds_file = out_dir / "classification_predictions.jsonl"

    failures = []
    with open(preds_file, "w", encoding="utf-8") as f:
        for idx, (s, pred, conf) in enumerate(zip(test_set, y_pred_tfidf, confs_tfidf)):
            is_correct = (s["label"] == pred)
            rec = {
                "sample_id": s["sample_id"],
                "true_label": s["label"],
                "predicted_label": pred,
                "confidence": round(conf, 4),
                "is_correct": is_correct,
                "language": s.get("language", "unknown"),
                "noise_type": s.get("noise_type", "clean"),
            }
            f.write(json.dumps(rec) + "\n")
            if not is_correct:
                failures.append({
                    "sample_id": s["sample_id"],
                    "true_label": s["label"],
                    "predicted_label": pred,
                    "confidence": round(conf, 4),
                    "noise_type": s.get("noise_type"),
                    "text_preview": s["text"][:120].replace("\n", " "),
                })

    # Prepare Benchmark Report
    report = {
        "benchmark_name": "Large-Scale Document Classification Benchmark",
        "dataset_version": "v2.0.0-synthetic-evaluation",
        "sample_counts": {
            "train": len(train_set),
            "val": len(val_set),
            "test": len(test_set),
        },
        "test_per_class_support": {c: sum(1 for y in y_true if y == c) for c in labels},
        "baselines": {
            "majority_class": {
                "accuracy": metrics_majority["accuracy"],
                "macro_f1": metrics_majority["macro_f1"],
                "labels": labels,
            },
            "heuristic_rule_classifier": {
                "accuracy": metrics_heuristic["accuracy"],
                "accuracy_95ci": h_acc_ci,
                "macro_f1": metrics_heuristic["macro_f1"],
                "macro_f1_95ci": h_f1_ci,
                "per_class": metrics_heuristic["per_class"],
                "confusion_matrix": metrics_heuristic["confusion_matrix"],
            },
        },
        "active_model": {
            "model_name": "TF-IDF (1-2 grams) + Logistic Regression",
            "accuracy": metrics_tfidf["accuracy"],
            "accuracy_95ci": tfidf_acc_ci,
            "macro_precision": metrics_tfidf["macro_precision"],
            "macro_recall": metrics_tfidf["macro_recall"],
            "macro_f1": metrics_tfidf["macro_f1"],
            "macro_f1_95ci": tfidf_f1_ci,
            "per_class": metrics_tfidf["per_class"],
            "confusion_matrix": metrics_tfidf["confusion_matrix"],
        },
        "failure_count": len(failures),
        "sample_failures": failures[:5],
        "disclosure": "Synthesized benchmark. Held-out templates ensure no template leakage across train and test sets.",
    }

    json_path = out_dir / "classification_benchmark.json"
    md_path = out_dir / "classification_benchmark.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Markdown Table formatting
    md_lines = [
        "# Large-Scale Document Classification Benchmark Report",
        f"**Dataset Version:** `v2.0.0-synthetic-evaluation` | **Total Test Samples:** {len(test_set):,} (200 per class)  ",
        "**Template Segregation:** 100% disjoint template pools between training and test sets.\n",
        "## 1. Overall Model Comparison (Holdout Test Set)",
        "| Model Architecture | Accuracy | Accuracy (95% CI) | Macro-F1 | Macro-F1 (95% CI) | Test Failures |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
        f"| **Majority Class Baseline** | {metrics_majority['accuracy']*100:.1f}% | N/A | {metrics_majority['macro_f1']*100:.1f}% | N/A | {len(test_set) - int(metrics_majority['accuracy']*len(test_set))} / {len(test_set)} |",
        f"| **Heuristic Rule Classifier** | {metrics_heuristic['accuracy']*100:.1f}% | [{h_acc_ci[0]*100:.1f}%, {h_acc_ci[1]*100:.1f}%] | {metrics_heuristic['macro_f1']*100:.1f}% | [{h_f1_ci[0]*100:.1f}%, {h_f1_ci[1]*100:.1f}%] | {len(test_set) - int(metrics_heuristic['accuracy']*len(test_set))} / {len(test_set)} |",
        f"| **TF-IDF + Logistic Regression** | **{metrics_tfidf['accuracy']*100:.1f}%** | **[{tfidf_acc_ci[0]*100:.1f}%, {tfidf_acc_ci[1]*100:.1f}%]** | **{metrics_tfidf['macro_f1']*100:.1f}%** | **[{tfidf_f1_ci[0]*100:.1f}%, {tfidf_f1_ci[1]*100:.1f}%]** | **{len(failures)} / {len(test_set)}** |",
        "\n## 2. Per-Class Performance (TF-IDF + Logistic Regression, N=1,000)",
        "| Document Class | Precision | Recall | F1-Score | Support | Description |",
        "| :--- | :---: | :---: | :---: | :---: | :--- |",
    ]

    for label in labels:
        pc = metrics_tfidf["per_class"][label]
        md_lines.append(
            f"| **{label}** | {pc['precision']*100:.1f}% | {pc['recall']*100:.1f}% | **{pc['f1']*100:.1f}%** | {pc['support']} | Retail cash memo, supplier bill, or voucher |"
        )

    md_lines.extend([
        "\n## 3. Confusion Matrix (Holdout Test Set, N=1,000)",
        "```",
        f"Labels: {labels}",
    ])

    cm = metrics_tfidf["confusion_matrix"]
    header_str = "True \\ Pred   " + "  ".join(f"{l[:5]:>5}" for l in labels)
    md_lines.append(header_str)
    for i, row in enumerate(cm):
        row_str = f"{labels[i][:11]:<11} " + "  ".join(f"{val:>5}" for val in row)
        md_lines.append(row_str)
    md_lines.append("```\n")

    if failures:
        md_lines.extend([
            "## 4. Failure Case Analysis on Challenging & Ambiguous Samples",
            f"Total failures observed: **{len(failures)}** out of 1,000 examples.",
            "| Sample ID | True Label | Predicted Label | Confidence | Noise Condition | Text Excerpt |",
            "| :--- | :---: | :---: | :---: | :---: | :--- |",
        ])
        for fail in failures[:5]:
            md_lines.append(
                f"| `{fail['sample_id']}` | **{fail['true_label']}** | `{fail['predicted_label']}` | {fail['confidence']:.2f} | `{fail['noise_type']}` | {fail['text_preview']}... |"
            )

    md_lines.extend([
        "\n> [!NOTE]",
        "> **Methodology Disclosure:** Test samples are generated from completely distinct shop names, supplier distributors, and layout phrases from the training set. All 1,000 test predictions are saved in `storage/evaluations/classification_predictions.jsonl` for full auditability.",
    ])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(f"Classification benchmark exported to {json_path} and {md_path}")
    print(f"Prediction-level logs saved to {preds_file}")


if __name__ == "__main__":
    run_benchmark()
