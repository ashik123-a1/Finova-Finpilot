"""
Competition Evaluation Metrics Engine for SME Finance Copilot.
Implements exact, reproducible metrics for Classification, OCR/Extraction,
Time-Series Forecasting, and Clustering Stability.
"""

from __future__ import annotations

import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    silhouette_score as sk_silhouette_score,
    davies_bouldin_score as sk_davies_bouldin_score,
    calinski_harabasz_score as sk_calinski_harabasz_score,
)


# ==============================================================================
# 1. Classification Metrics
# ==============================================================================

def compute_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Computes Accuracy, Macro-F1, per-class Precision, Recall, F1, Support,
    and the complete Confusion Matrix.
    """
    if not y_true or not y_pred:
        raise ValueError("Ground truth and prediction lists cannot be empty.")
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")

    if labels is None:
        labels = sorted(list(set(y_true) | set(y_pred)))

    acc = float(accuracy_score(y_true, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    p_class, r_class, f1_class, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

    per_class_metrics = {}
    for i, label in enumerate(labels):
        per_class_metrics[label] = {
            "precision": round(float(p_class[i]), 4),
            "recall": round(float(r_class[i]), 4),
            "f1": round(float(f1_class[i]), 4),
            "support": int(support[i]),
        }

    return {
        "sample_count": len(y_true),
        "accuracy": round(acc, 4),
        "macro_precision": round(float(p_macro), 4),
        "macro_recall": round(float(r_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "labels": labels,
        "per_class": per_class_metrics,
        "confusion_matrix": cm,
    }


# ==============================================================================
# 2. OCR and Field Extraction Metrics
# ==============================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes exact edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Character Error Rate (CER) = LevenshteinDistance(ref, hyp) / len(ref)."""
    ref_len = len(reference)
    if ref_len == 0:
        return 0.0 if len(hypothesis) == 0 else 1.0
    dist = levenshtein_distance(reference, hypothesis)
    return round(float(dist / ref_len), 4)


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Word Error Rate (WER) using tokenized words."""
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    # Word-level Levenshtein
    n, m = len(ref_words), len(hyp_words)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + 1)

    return round(float(dp[n][m] / n), 4)


def field_exact_match_rate(targets: List[Any], predictions: List[Any]) -> float:
    """Computes exact match percentage across field extractions."""
    if not targets:
        return 0.0
    matches = sum(1 for t, p in zip(targets, predictions) if str(t).strip().lower() == str(p).strip().lower())
    return round(float(matches / len(targets)), 4)


# ==============================================================================
# 3. Time-Series Forecasting Metrics
# ==============================================================================

def mean_absolute_error(y_true: List[float], y_pred: List[float]) -> float:
    """MAE = mean(|y_true - y_pred|)."""
    arr_t = np.array(y_true, dtype=float)
    arr_p = np.array(y_pred, dtype=float)
    return round(float(np.mean(np.abs(arr_t - arr_p))), 2)


def root_mean_squared_error(y_true: List[float], y_pred: List[float]) -> float:
    """RMSE = sqrt(mean((y_true - y_pred)^2))."""
    arr_t = np.array(y_true, dtype=float)
    arr_p = np.array(y_pred, dtype=float)
    return round(float(np.sqrt(np.mean((arr_t - arr_p) ** 2))), 2)


def mean_absolute_scaled_error(
    y_train: List[float],
    y_test: List[float],
    y_pred: List[float],
    seasonality: int = 1,
) -> float:
    """
    Mean Absolute Scaled Error (MASE) - Hyndman & Koehler (2006).
    Scale-independent metric comparing model forecast errors against in-sample naive error.
    MASE < 1 means model outperforms naive in-sample persistence forecast.
    """
    y_tr = np.array(y_train, dtype=float)
    y_te = np.array(y_test, dtype=float)
    y_pr = np.array(y_pred, dtype=float)

    # In-sample naive errors: |y_t - y_{t-s}|
    if len(y_tr) <= seasonality:
        scale = 1.0
    else:
        diffs = np.abs(y_tr[seasonality:] - y_tr[:-seasonality])
        scale = float(np.mean(diffs))

    if scale <= 1e-6:
        scale = 1.0

    test_mae = float(np.mean(np.abs(y_te - y_pr)))
    return round(float(test_mae / scale), 4)


def empirical_ci_coverage(
    y_true: List[float],
    lower_bounds: List[float],
    upper_bounds: List[float],
) -> float:
    """
    Calculates percentage of ground-truth points that fall strictly within
    the estimated confidence bounds: [lower, upper].
    """
    if not y_true:
        return 0.0
    covered = sum(
        1 for y, low, high in zip(y_true, lower_bounds, upper_bounds) if low <= y <= high
    )
    return round(float(covered / len(y_true)), 4)


# ==============================================================================
# 4. Clustering Stability Metrics
# ==============================================================================

def evaluate_clustering_stability(X: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
    """
    Evaluates Silhouette score, Davies-Bouldin index, and Calinski-Harabasz score.
    Higher Silhouette & Calinski-Harabasz is better. Lower Davies-Bouldin is better.
    """
    unique_labels = set(labels)
    if len(unique_labels) < 2 or len(unique_labels) >= len(X):
        return {"silhouette_score": 0.0, "davies_bouldin_index": 99.0, "calinski_harabasz_score": 0.0}

    sil = float(sk_silhouette_score(X, labels))
    db = float(sk_davies_bouldin_score(X, labels))
    ch = float(sk_calinski_harabasz_score(X, labels))

    return {
        "silhouette_score": round(sil, 4),
        "davies_bouldin_index": round(db, 4),
        "calinski_harabasz_score": round(ch, 2),
    }
