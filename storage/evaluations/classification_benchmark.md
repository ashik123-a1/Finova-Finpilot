# Document Classification Evaluation & Model Benchmark Report
**Dataset:** 200 samples (Train: 140, Val: 30, Test: 30)  
**Random Seed:** 42 | **Classes:** 5  

## 1. Overall Performance Comparison

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MajorityClass (expense_receipt)** | 20.00% | 4.00% | 20.00% | **6.67%** | `Naive Baseline` |
| **Heuristic-TFIDF-Classifier (Rule Baseline)** | 100.00% | 100.00% | 100.00% | **100.00%** | `Rule Baseline` |
| **Trained TF-IDF + Logistic Regression (Statistical ML)** | 100.00% | 100.00% | 100.00% | **100.00%** | `Trained ML` |

## 2. Per-Class F1 Breakdown (Current Heuristic vs Trained ML)

| Document Class | Heuristic F1 | Trained TF-IDF F1 | Support (Test) |
| :--- | :---: | :---: | :---: |
| `sales_receipt` | 100.0% | 100.0% | 6 |
| `purchase_invoice` | 100.0% | 100.0% | 6 |
| `expense_receipt` | 100.0% | 100.0% | 6 |
| `payment_receipt` | 100.0% | 100.0% | 6 |
| `unknown` | 100.0% | 100.0% | 6 |

## 3. Confusion Matrix (Current Heuristic Classifier)
```json
[
  [
    6,
    0,
    0,
    0,
    0
  ],
  [
    0,
    6,
    0,
    0,
    0
  ],
  [
    0,
    0,
    6,
    0,
    0
  ],
  [
    0,
    0,
    0,
    6,
    0
  ],
  [
    0,
    0,
    0,
    0,
    6
  ]
]
```