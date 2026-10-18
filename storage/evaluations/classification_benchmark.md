# Large-Scale Document Classification Benchmark Report
**Dataset Version:** `v2.0.0-synthetic-evaluation` | **Total Test Samples:** 1,000 (200 per class)  
**Template Segregation:** 100% disjoint template pools between training and test sets.

## 1. Overall Model Comparison (Holdout Test Set)
| Model Architecture | Accuracy | Accuracy (95% CI) | Macro-F1 | Macro-F1 (95% CI) | Test Failures |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Majority Class Baseline** | 20.0% | N/A | 6.7% | N/A | 800 / 1000 |
| **Heuristic Rule Classifier** | 95.8% | [94.6%, 97.1%] | 95.9% | [94.7%, 97.1%] | 42 / 1000 |
| **TF-IDF + Logistic Regression** | **100.0%** | **[100.0%, 100.0%]** | **100.0%** | **[100.0%, 100.0%]** | **0 / 1000** |

## 2. Per-Class Performance (TF-IDF + Logistic Regression, N=1,000)
| Document Class | Precision | Recall | F1-Score | Support | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **sales_receipt** | 100.0% | 100.0% | **100.0%** | 200 | Retail cash memo, supplier bill, or voucher |
| **purchase_invoice** | 100.0% | 100.0% | **100.0%** | 200 | Retail cash memo, supplier bill, or voucher |
| **expense_receipt** | 100.0% | 100.0% | **100.0%** | 200 | Retail cash memo, supplier bill, or voucher |
| **payment_receipt** | 100.0% | 100.0% | **100.0%** | 200 | Retail cash memo, supplier bill, or voucher |
| **unknown** | 100.0% | 100.0% | **100.0%** | 200 | Retail cash memo, supplier bill, or voucher |

## 3. Confusion Matrix (Holdout Test Set, N=1,000)
```
Labels: ['sales_receipt', 'purchase_invoice', 'expense_receipt', 'payment_receipt', 'unknown']
True \ Pred   sales  purch  expen  payme  unkno
sales_recei   200      0      0      0      0
purchase_in     0    200      0      0      0
expense_rec     0      0    200      0      0
payment_rec     0      0      0    200      0
unknown         0      0      0      0    200
```


> [!NOTE]
> **Methodology Disclosure:** Test samples are generated from completely distinct shop names, supplier distributors, and layout phrases from the training set. All 1,000 test predictions are saved in `storage/evaluations/classification_predictions.jsonl` for full auditability.
