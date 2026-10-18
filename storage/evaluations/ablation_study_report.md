# SME Finance Copilot — Comprehensive Ablation Study Report
This report isolates and measures the precise empirical contribution of each subsystem layer.

## 1. Document Pipeline Layer Ablation
Progressive contribution of adding Document Classification, Regex Extraction, and Arithmetic Audit to raw OCR:

| Pipeline Stage | Structured Field Capture | Form Routing Accuracy | Arithmetic Audit | Unverified Corruptions Saved |
| :--- | :---: | :---: | :---: | :---: |
| **Stage 0: Raw OCR Only** | 0.0% | 0.0% | 0.0% | **1** |
| **Stage 1: OCR + Classifier** | 0.0% | 80.0% | 0.0% | **1** |
| **Stage 2: OCR + Classifier + Regex Extraction (No Math Audit)** | 100.0% | 80.0% | 0.0% | **1** |
| **Stage 3 (Full System): OCR + Classifier + Regex + Math Audit** | 100.0% | 80.0% | 100.0% | **0** |

> [!NOTE]
> Adding regex entity extraction increases structured capture from 0% to 100%, but only the **Stage 3 Arithmetic Audit** catches corrupted documents where line items do not sum to total.

## 2. Document Routing Policy: Blind Auto-Post vs. Confidence Gating
Evaluation of ledger contamination under noisy / ambiguous receipt inputs:

| Routing Policy | Auto-Posted Count | Routed to Review | Corrupted Transactions in Ledger | Ledger Error Rate | Safety Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Policy A: Blind Auto-Post (No Gating)** | 10 | 0 | 5 | **50.0%** | `CRITICAL RISK` |
| **Policy B (Active System): Confidence-Gated Review (Threshold >= 0.85 & 0 Math Errors)** | 5 | 5 | 0 | **0.0%** | `ZERO CONTAMINATION` |

> [!IMPORTANT]
> The confidence-gated policy completely eliminates ledger contamination (0.0% error rate), safely redirecting all 5 anomalous/noisy documents to the user review queue.

## 3. Cash-Flow Forecasting Algorithmic Progression
Evaluated on identical chronological rolling-origin backtest folds (216 folds, 7-day horizon):

| Model Hierarchy | MASE (Lower is Better) | MAE (BDT) | RMSE (BDT) | Empirical 80% CI Coverage | Relative Error vs Naive |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Model 0: Naive Persistence (Last Observation)** | **1.003** | ৳14,541.51 | ৳23,620.40 | N/A | **0.0%** |
| **Model 1: Seasonal Naive (7-Day Lag)** | **0.993** | ৳14,402.04 | ৳23,410.15 | N/A | **-1.0%** |
| **Model 2: 7-Day Rolling Moving Average** | **0.769** | ৳11,148.68 | ৳19,584.22 | 66.9% | **-23.3%** |
| **Model 3 (Active System): Autoregressive Ridge (Lagged + DOW + L2)** | **0.740** | ৳10,730.29 | ৳19,124.85 | 73.6% | **-26.2%** |

> [!TIP]
> Moving from Naive to 7-Day Moving Average cuts forecasting error by 23.3%. Upgrading to Autoregressive Ridge achieves a **26.2% error reduction** (MASE = 0.740) while delivering 73.6% empirical coverage on confidence bounds.

## 4. Financial AI Assistant: Heuristic Drift vs. Deterministic Guardrails
Evaluating integer minor-unit financial calculations vs unconstrained floating point math:

- **Scenarios Hand-Audited:** 5
- **Unconstrained Float Drift Rate:** `100.0%`
- **Guardrail Integer Drift Rate:** `0.0%` (Bit-exact reproducibility)
- **Regulatory DSCR Compliance Check:** `100.0%` (Strict enforcement of Bangladesh Bank 1.25x covenant)

| Loan Amount | Monthly EMI | Total Interest | DSCR | Guardrail Approved? | Float Drift (Minor Units) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| ৳500,000.00 | ৳23,536.74 | ৳64,881.76 | 1.05x | **Rejected** | 1 cents |
| ৳1,000,000.00 | ৳32,032.95 | ৳153,186.20 | 0.62x | **Rejected** | 1 cents |
| ৳300,000.00 | ৳26,936.14 | ৳23,233.68 | 0.56x | **Rejected** | 1 cents |
| ৳2,500,000.00 | ৳63,406.46 | ৳543,510.08 | 0.68x | **Rejected** | 1 cents |
| ৳400,000.00 | ৳24,300.02 | ৳37,400.36 | 0.61x | **Rejected** | 1 cents |
