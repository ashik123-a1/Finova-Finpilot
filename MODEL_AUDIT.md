# SME Finance Copilot — AI Model Inventory & Technical Readiness Audit

**Audit Date:** 2026-10-18  
**Auditor:** Senior ML Research Engineer & Competition Evaluation Lead  
**Scope:** Repository `F:\china project`  
**Standard:** Competition Technical Due Diligence & Reproducibility Standard  

---

## 1. Executive Summary

This audit assesses the implementation, weights provenance, training datasets, and empirical evidence for all AI/ML components declared in the SME Finance Copilot.

> [!IMPORTANT]
> A critical rule in ML evaluation: **Never assume a model is trained or production-ready merely because it has an entry in a database registry or configuration file.**
> Below is the factual, unexaggerated status of each component prior to Phase 1.5 evaluation.

---

## 2. Component-by-Component Technical Inventory

### Model 1: Document Classifier
- **Registry Entry:** `Heuristic-TFIDF-Classifier` (v1.0.0)
- **Actual Implementation Status:** **Partially Implemented (Heuristic Rule Baseline)**
- **Code Location:** `src/documents/classifier.py` (`DocumentClassifier`)
- **Algorithm & Library:**
  - Hand-engineered keyword weighting dictionary across English and Bengali terms (`KEYWORD_WEIGHTS`).
  - Softmax-like probability normalization over accumulated keyword hits.
  - No external ML weights file; implemented using pure Python standard library (`re`).
- **Weights Provenance:** Hand-crafted keyword priority weights (0.1 to 3.5). No statistical weights learned from a training corpus.
- **Training Dataset:** None (Rule-based).
- **Existing Evidence:** Informal keyword check in `tests/test_document_pipeline.py`.
- **Known Limitations:**
  - Cannot generalize to out-of-vocabulary document layouts or novel phrasing.
  - Lacks learned n-gram representations or TF-IDF matrix transforms.
  - Softmax normalization uses arbitrary heuristic sum as denominator.
- **Phase 1.5 Objective:** Train and benchmark a true statistical baseline (TF-IDF + Logistic Regression / Multinomial Naive Bayes) on stratified synthetic document text against the heuristic rule classifier.

---

### Model 2: OCR & Structured Field Extractor
- **Registry Entry:** `RapidOCR-Parser-Pipeline` (v1.0.0)
- **Actual Implementation Status:** **Implemented (Pretrained Deep Learning + Rule Parsing)**
- **Code Location:** `src/documents/extractor.py` (`RapidOcrEngine`, `StructuredDocumentExtractor`)
- **Algorithm & Library:**
  - Text Detection & Recognition: `rapidocr-onnxruntime` (PP-OCRv4 ONNX model architectures: DBNet for detection + SVTR/CRNN for recognition).
  - Key-Value Extraction: Deterministic regex token parsers and math cross-auditing (`quantity * unit_price == line_total`).
- **Weights Provenance:** Pretrained ONNX model weights bundled within the `rapidocr_onnxruntime` library. No custom fine-tuning performed on SME receipts.
- **Training Dataset:** Pretrained on large-scale public OCR datasets (PaddleOCR synthetic and natural scene text).
- **Existing Evidence:** Functional execution test in `tests/test_document_pipeline.py` with mock OCR text.
- **Known Limitations:**
  - Pretrained recognizer has lower accuracy on complex Bengali cursive and low-contrast thermal paper.
  - Regex-based field extraction is brittle to noisy OCR output (e.g. `O` vs `0`, broken decimal points).
- **Phase 1.5 Objective:** Empirically measure Character Error Rate (CER), Word Error Rate (WER), Field-level Exact Match, and Total Reconciliation Rate on a standardized test collection across English, Bengali, and bilingual receipts.

---

### Model 3: Cash-Flow Forecaster
- **Registry Entry:** `Holt-Winters-Exponential-Smoothing-Baseline` (v1.0.0)
- **Actual Implementation Status:** **Implemented (Statistical Moving Average + Scikit-Learn Ridge Regression)**
- **Code Location:** `src/ai/forecaster.py` (`CashFlowForecaster`)
- **Algorithm & Library:**
  - Baseline 1: Rolling window moving average with normal distribution bounds ($\pm 1.28 \sigma$ for 80% CI).
  - Baseline 2: `sklearn.linear_model.Ridge(alpha=1.0)` with 7-day autoregressive lag features and iterative multi-step rollout.
- **Weights Provenance:** Fitted dynamically on-the-fly during inference on historical daily net cash time-series. No pre-saved weights file.
- **Training Dataset:** Generated relational financial ledger history (`cash_movements` table, 180 days history).
- **Existing Evidence:** Unit test verifying array output dimensions; no backtesting metrics recorded.
- **Known Limitations:**
  - Ridge regression multi-step iterative forecasting suffers from error compounding over 30-day horizons.
  - Moving average ignores weekly/monthly calendar seasonality.
  - Gaussian confidence intervals assume stationary homoskedastic variance.
- **Phase 1.5 Objective:** Implement rigorous chronological rolling-origin backtesting (zero future leakage), evaluate MAE, RMSE, MASE, and empirical coverage of 80% confidence intervals against Naive and Seasonal Naive baselines.

---

### Model 4: Loan Matching & Credit Risk Engine
- **Registry Entry:** `Transparent-Rule-DSCR-Evaluator` (v1.0.0)
- **Actual Implementation Status:** **Implemented (Deterministic Policy Rules Engine)**
- **Code Location:** `src/ai/loan_risk.py` (`TransparentLoanRiskEngine`)
- **Algorithm & Library:**
  - Pure deterministic financial policy engine.
  - Computes Debt Service Coverage Ratio (DSCR), debt-to-income ratio, Reducing-Balance EMI, and maximum safe borrowing capacity.
  - Explicitly tagged `is_synthetic_demo = True`.
- **Weights Provenance:** Explicit financial thresholds (Healthy DSCR $\ge 1.25$, Max EMI/Income $\le 0.40$).
- **Training Dataset:** Not an ML trained model; deterministic financial underwriting logic.
- **Existing Evidence:** Unit tested in `tests/test_finance_calculator.py`.
- **Known Limitations:**
  - Does not model stochastic borrower default probability.
  - Must not be presented to judges as a validated credit-bureau default model.
- **Phase 1.5 Objective:** Verify boundary cases, affordability constraints, and stress scenarios using independent hand-verified test vectors.

---

### Model 5: Customer Segmentation
- **Registry Entry:** `RFM-Rule-Segmenter` (v1.0.0)
- **Actual Implementation Status:** **Implemented (Rule-based RFM + Scikit-Learn KMeans)**
- **Code Location:** `src/ai/segmentation.py` (`CustomerSegmentationEngine`)
- **Algorithm & Library:**
  - Rule-based Recency, Frequency, Monetary (RFM) thresholds.
  - `sklearn.cluster.KMeans(n_clusters=4, random_state=42)` on z-score normalized RFM vectors.
- **Weights Provenance:** Rule boundaries for RFM; KMeans cluster centroids fitted on customer spend records.
- **Training Dataset:** 1,620 customer records in `sme_finance.db`.
- **Existing Evidence:** Unit test verifying execution.
- **Known Limitations:**
  - Optimal cluster count ($k=4$) not validated via elbow curve or silhouette analysis.
- **Phase 1.5 Objective:** Compute empirical cluster validation metrics (Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz Score) on the 1,620 database customers.

---

### Model 6: Demand & Pricing Recommendation
- **Registry Entry:** `Safety-Stock-Reorder-Point-Estimator` (v1.0.0)
- **Actual Implementation Status:** **Placeholder in Registry (Not Implemented as Dedicated Class)**
- **Code Location:** Entry in `model_versions` table; no corresponding `src/ai/pricing_demand.py` file existed in Phase 1.
- **Algorithm & Library:** Intended inventory-aware demand estimator using normal distribution safety stock ($z \cdot \sigma_L$).
- **Weights Provenance:** None.
- **Training Dataset:** None.
- **Existing Evidence:** None.
- **Phase 1.5 Objective:** Implement `src/ai/pricing_demand.py` with inventory safety stock, reorder point formulas, and price elasticity simulation; evaluate profit impact against naive baseline reordering.

---

### Model 7: AI Assistant Deterministic Guardrail
- **Registry Entry:** N/A (Safety Guardrail Layer)
- **Actual Implementation Status:** **Implemented**
- **Code Location:** `src/ai/guardrails.py` (`AiAssistantGuardrail`)
- **Algorithm & Library:** Regex entity extractor + deterministic interception via `FinancialCalculator`.
- **Existing Evidence:** Unit tested in `tests/test_model_registry.py`.
- **Phase 1.5 Objective:** Conduct an ablation study comparing unconstrained LLM responses vs Guardrail-enforced deterministic responses on financial calculation prompts.

---

## 3. Image Dataset Audit
- **Claimed in Initial Scope Target:** 5,000 synthetic images.
- **Actual Existing on Disk:** **10 synthetic document images** in `storage/synthetic_images/` with manifest `dataset_manifest.json`.
- **Assessment:** The tooling works, but only a 10-image smoke test was generated in Phase 1.
- **Action Required:** Generate a validated, balanced evaluation dataset of 120 images with complete ground-truth annotations to enable true statistical validation without fabricating a 5,000-image dataset claim.
