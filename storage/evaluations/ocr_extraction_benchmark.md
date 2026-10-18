# OCR & Structured Field Extraction Benchmark Report
**Total Samples Evaluated:** 12 images  
**OCR Engine:** RapidOCR (PP-OCRv4 ONNX) + Structured Regex Extractor  

## 1. Overall System Metrics

- **Character Error Rate (CER):** `37.41%`
- **Word Error Rate (WER):** `46.53%`
- **Date Field Exact Match:** `100.00%`
- **Total Amount Exact Match:** `0.00%`
- **Invoice # Exact Match:** `100.00%`
- **Math Reconciliation Success:** `0.00%`
- **True Accuracy (Both Math-Consistent & Value-Correct):** `0.00%`

> [!IMPORTANT]
> **Math Fallacy Gap:** `0.00%` of documents were mathematically consistent internally but had extraction value errors relative to ground truth.
> This proves the critical competition requirement: *Never treat mathematical reconciliation alone as proof of extraction correctness!*

## 2. Performance Breakdown by Language

| Language | Samples | Mean CER | Mean WER | Total Amount EMR |
| :--- | :---: | :---: | :---: | :---: |
| **English (en)** | 4 | 32.16% | 42.10% | 0.00% |
| **Bengali (bn)** | 4 | 44.27% | 49.93% | 0.00% |
| **Mixed (bn_en)** | 4 | 35.79% | 47.55% | 0.00% |

## 3. Performance Breakdown by Image Quality

| Quality Condition | Samples | Mean CER | Mean WER | Total Amount EMR |
| :--- | :---: | :---: | :---: | :---: |
| **Clean Synthetic** | 6 | 37.07% | 46.82% | 0.00% |
| **Degraded (Thermal Fade & Blur)** | 6 | 37.75% | 46.24% | 0.00% |