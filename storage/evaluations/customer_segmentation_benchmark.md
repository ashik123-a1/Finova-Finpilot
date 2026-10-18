# Customer Segmentation & Cluster Stability Benchmark Report
**Total Customers Analyzed:** 1,620 records  

## 1. Rule-Based RFM Segment Distribution

| Segment | Count | Share (%) | Strategic SME Action |
| :--- | :---: | :---: | :--- |
| **Occasional** | 536 | 33.1% | Welcome promotions & cross-sell bundles |
| **Regular** | 904 | 55.8% | Loyalty point programs & routine replenishment reminders |
| **At-Risk** | 14 | 0.9% | Targeted win-back discounts before attrition |
| **VIP** | 165 | 10.2% | Priority VIP services & exclusive product previews |
| **Dormant** | 1 | 0.1% | Re-engagement surveys & win-back campaigns |

## 2. Unsupervised KMeans Cluster Stability (k=2 to k=6)

| Clusters (k) | Silhouette Score (Higher is Better) | Davies-Bouldin (Lower is Better) | Calinski-Harabasz (Higher is Better) |
| :---: | :---: | :---: | :---: |
| **k = 2** | **0.2854** | 1.3556 | 662.7 |
| **k = 3** | **0.3060** | 1.1381 | 711.9 |
| **k = 4** | **0.2989** | 1.0616 | 749.6 |
| **k = 5** | **0.2786** | 1.1388 | 683.1 |
| **k = 6** | **0.2654** | 1.1538 | 661.5 |

> [!TIP]
> **Optimal Cluster Count:** `k = 3` (Peak Silhouette: `0.3060`). k=3 achieves optimal trade-off between cluster separation and cohesion. Higher k values fragment natural spend tiers without increasing actionable insight.