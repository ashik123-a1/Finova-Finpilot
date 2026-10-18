# Customer Segmentation & Cluster Stability Benchmark Report
**Total Customers Analyzed:** 1,620 records  

## 1. Rule-Based RFM Segment Distribution

| Segment | Count | Share (%) | Strategic SME Action |
| :--- | :---: | :---: | :--- |
| **VIP** | 1,231 | 76.0% | Priority VIP services & exclusive product previews |
| **Regular** | 372 | 23.0% | Loyalty point programs & routine replenishment reminders |
| **Occasional** | 2 | 0.1% | Welcome promotions & cross-sell bundles |
| **At-Risk** | 14 | 0.9% | Targeted win-back discounts before attrition |
| **Dormant** | 1 | 0.1% | Re-engagement surveys & win-back campaigns |

## 2. Unsupervised KMeans Cluster Stability (k=2 to k=6)

| Clusters (k) | Silhouette Score (Higher is Better) | Davies-Bouldin (Lower is Better) | Calinski-Harabasz (Higher is Better) |
| :---: | :---: | :---: | :---: |
| **k = 2** | **0.2856** | 1.3547 | 662.7 |
| **k = 3** | **0.3060** | 1.1383 | 711.8 |
| **k = 4** | **0.2995** | 1.0640 | 749.7 |
| **k = 5** | **0.2788** | 1.1312 | 683.5 |
| **k = 6** | **0.2653** | 1.1547 | 661.9 |

> [!TIP]
> **Optimal Cluster Count:** `k = 3` (Peak Silhouette: `0.3060`). k=3 achieves optimal trade-off between cluster separation and cohesion. Higher k values fragment natural spend tiers without increasing actionable insight.