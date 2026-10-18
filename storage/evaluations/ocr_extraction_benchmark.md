# Large-Scale OCR & Field Extraction Benchmark Report
**Dataset Archive:** `storage/datasets/ocr_receipts/` (1,000 images, 1,000 annotations)  
**Evaluated Stratified Subset:** 70 images across all 7 quality tiers and 3 language sets.

## 1. Overall System Metrics
| Metric Dimension | Measured Score | Evaluation Standard |
| :--- | :---: | :--- |
| **Character Error Rate (CER)** | **49.76%** | Levenshtein edit distance on full text |
| **Word Error Rate (WER)** | **48.43%** | Token-level edit distance |
| **Date Field Exact Match** | **87.1%** | Normalized DD/MM/YYYY match |
| **Total Amount Exact Match** | **90.0%** | Exact minor unit match vs ground truth |
| **Invoice Number Exact Match** | **54.3%** | Alphanumeric invoice code extraction |
| **Document Classification Accuracy** | **41.4%** | Categorization from raw OCR output |
| **Arithmetic Reconciliation Rate** | **45.7%** | Line-item sum vs extracted total consistency |

## 2. Performance Breakdown by Language
| Language | Character Error Rate (CER) | Word Error Rate (WER) | Samples Evaluated |
| :--- | :---: | :---: | :---: |
| **BN** | 61.18% | 67.71% | 24 |
| **BILINGUAL** | 50.25% | 48.54% | 23 |
| **EN** | 37.37% | 28.21% | 23 |

## 3. Performance Breakdown by Optical Degradation Category
| Degradation Category | CER (%) | WER (%) | Samples | Optical Impact |
| :--- | :---: | :---: | :---: | :--- |
| **Blur** | 54.23% | 68.23% | 10 | Simulated blur distortion |
| **Rotated** | 49.44% | 50.56% | 10 | Simulated rotated distortion |
| **Low Light** | 46.18% | 35.28% | 10 | Simulated low_light distortion |
| **Faded Thermal** | 52.14% | 50.99% | 10 | Simulated faded_thermal distortion |
| **Shadow** | 47.99% | 41.32% | 10 | Simulated shadow distortion |
| **Cropped** | 46.86% | 43.12% | 10 | Simulated cropped distortion |
| **Clean** | 51.5% | 49.54% | 10 | High clarity |

> [!NOTE]
> **Prediction Traceability:** All individual image predictions, extracted fields, and errors are saved in `storage/evaluations/ocr_predictions.jsonl`.
