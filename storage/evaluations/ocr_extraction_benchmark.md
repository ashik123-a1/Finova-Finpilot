# Large-Scale OCR & Field Extraction Benchmark Report
**Dataset Archive:** `storage/datasets/ocr_receipts/` (1,000 images, 1,000 annotations)  
**Evaluated Stratified Subset:** 70 images across all 7 quality tiers and 3 language sets.

## 1. Overall System Metrics
| Metric Dimension | Measured Score | Evaluation Standard |
| :--- | :---: | :--- |
| **Character Error Rate (CER)** | **50.49%** | Levenshtein edit distance on full text |
| **Word Error Rate (WER)** | **52.48%** | Token-level edit distance |
| **Date Field Exact Match** | **97.1%** | Normalized DD/MM/YYYY match |
| **Total Amount Exact Match** | **100.0%** | Exact minor unit match vs ground truth |
| **Invoice Number Exact Match** | **84.3%** | Alphanumeric invoice code extraction |
| **Document Classification Accuracy** | **40.0%** | Categorization from raw OCR output |
| **Arithmetic Reconciliation Rate** | **31.4%** | Line-item sum vs extracted total consistency |

## 2. Performance Breakdown by Language
| Language | Character Error Rate (CER) | Word Error Rate (WER) | Samples Evaluated |
| :--- | :---: | :---: | :---: |
| **BN** | 62.59% | 72.26% | 24 |
| **BILINGUAL** | 50.13% | 51.91% | 23 |
| **EN** | 38.24% | 32.41% | 23 |

## 3. Performance Breakdown by Optical Degradation Category
| Degradation Category | CER (%) | WER (%) | Samples | Optical Impact |
| :--- | :---: | :---: | :---: | :--- |
| **Blur** | 58.37% | 94.16% | 10 | Simulated blur distortion |
| **Rotated** | 48.99% | 49.75% | 10 | Simulated rotated distortion |
| **Low Light** | 46.49% | 37.69% | 10 | Simulated low_light distortion |
| **Faded Thermal** | 53.2% | 52.16% | 10 | Simulated faded_thermal distortion |
| **Shadow** | 48.34% | 43.08% | 10 | Simulated shadow distortion |
| **Cropped** | 46.8% | 43.96% | 10 | Simulated cropped distortion |
| **Clean** | 51.28% | 46.54% | 10 | High clarity |

> [!NOTE]
> **Prediction Traceability:** All individual image predictions, extracted fields, and errors are saved in `storage/evaluations/ocr_predictions.jsonl`.
