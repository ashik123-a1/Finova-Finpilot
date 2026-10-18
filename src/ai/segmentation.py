"""
Customer Segmentation Engine for SMEs.
Implements explainable rule-based RFM (Recency, Frequency, Monetary) segmentation
with optional KMeans unsupervised clustering baseline.
"""

from __future__ import annotations

from typing import List, Dict, Any
import numpy as np
from sklearn.cluster import KMeans


class CustomerSegmentationEngine:
    """Classifies SME customers into actionable retention and marketing segments."""

    @classmethod
    def segment_customer_rfm(
        cls,
        days_since_last_purchase: int,
        total_orders_count: int,
        total_spent_minor: int,
        avg_basket_minor: int,
    ) -> Dict[str, Any]:
        """
        Rule-based RFM segmentation with clear business logic and suggested actions.
        """
        # Thresholds tailored for retail/SME
        if days_since_last_purchase > 90:
            segment = "Dormant"
            strategy = "Re-engagement discount campaign or survey to identify attrition reasons."
            priority = "low"
        elif days_since_last_purchase > 60:
            segment = "At-Risk"
            strategy = "Targeted win-back offer or reminder before customer goes dormant."
            priority = "high"
        elif total_spent_minor >= 500_000 and total_orders_count >= 10:  # e.g., > 5,000 BDT
            segment = "VIP"
            strategy = "Priority customer service, exclusive previews, loyalty appreciation."
            priority = "high"
        elif total_orders_count >= 5:
            segment = "Regular"
            strategy = "Cross-sell relevant inventory, loyalty points incentives."
            priority = "medium"
        else:
            segment = "Occasional"
            strategy = "Follow-up SMS, introductory bundles to encourage repeat purchase."
            priority = "medium"

        return {
            "segment": segment,
            "recommended_strategy": strategy,
            "action_priority": priority,
            "metrics": {
                "days_since_last_purchase": days_since_last_purchase,
                "total_orders_count": total_orders_count,
                "total_spent_minor": total_spent_minor,
                "avg_basket_minor": avg_basket_minor,
            },
        }

    @classmethod
    def cluster_customers_kmeans(
        cls, customer_records: List[Dict[str, Any]], n_clusters: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Unsupervised KMeans clustering baseline on normalized RFM vectors.
        """
        if len(customer_records) < n_clusters:
            # Fall back to rule-based
            return [
                {
                    **c,
                    **cls.segment_customer_rfm(
                        c.get("days_since_last_purchase", 0),
                        c.get("total_orders_count", 0),
                        c.get("total_spent_minor", 0),
                        c.get("avg_basket_minor", 0),
                    ),
                }
                for c in customer_records
            ]

        # Prepare feature matrix: [recency, frequency, monetary]
        features = np.array([
            [
                float(c.get("days_since_last_purchase", 0)),
                float(c.get("total_orders_count", 0)),
                float(c.get("total_spent_minor", 0)),
            ]
            for c in customer_records
        ])

        # Normalize features (z-score)
        mean_vals = np.mean(features, axis=0)
        std_vals = np.std(features, axis=0)
        std_vals[std_vals == 0] = 1.0  # Avoid div-by-zero
        normalized_features = (features - mean_vals) / std_vals

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(normalized_features)

        results = []
        for i, c in enumerate(customer_records):
            rule_seg = cls.segment_customer_rfm(
                c.get("days_since_last_purchase", 0),
                c.get("total_orders_count", 0),
                c.get("total_spent_minor", 0),
                c.get("avg_basket_minor", 0),
            )
            results.append({
                **c,
                "rule_segment": rule_seg["segment"],
                "kmeans_cluster": int(cluster_labels[i]),
                "recommended_strategy": rule_seg["recommended_strategy"],
            })

        return results
