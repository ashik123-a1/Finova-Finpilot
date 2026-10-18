# SME Finance Copilot — Comprehensive Ablation Study Report
This report isolates and measures the precise empirical contribution of each subsystem layer.

## 1. Document Pipeline Layer Ablation (N=100 Test Examples)
| Pipeline Stage | Structured Field Capture | Form Routing Accuracy | Arithmetic Audit | Unverified Corruptions Saved |
| :--- | :---: | :---: | :---: | :---: |
| **Stage 0: Raw OCR Only** | 0.0% | 0.0% | 0.0% | **10** |
| **Stage 1: OCR + Classifier** | 0.0% | 100.0% | 0.0% | **10** |
| **Stage 2: OCR + Classifier + Regex Extraction (No Math Audit)** | 100.0% | 100.0% | 0.0% | **10** |
| **Stage 3 (Full System): OCR + Classifier + Regex + Math Audit** | 100.0% | 100.0% | 100.0% | **0** |

> [!NOTE]
> Adding regex entity extraction increases structured capture from 0% to 100%, but only the **Stage 3 Arithmetic Audit** catches corrupted documents where line items do not sum to total.

## 2. Document Routing Policy: Blind Auto-Post vs. Confidence Gating (N=100 Documents)
| Routing Policy | Auto-Posted Count | Routed to Review | Corrupted Transactions in Ledger | Ledger Error Rate | Safety Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Policy A: Blind Auto-Post (No Gating)** | 100 | 0 | 7 | **7.0%** | `CRITICAL RISK` |
| **Policy B (Active System): Confidence-Gated Review (Threshold >= 0.85 & 0 Math Errors)** | 73 | 27 | 0 | **0.0%** | `ZERO CONTAMINATION` |

> [!IMPORTANT]
> The confidence-gated policy completely eliminates ledger contamination (0.0% error rate), safely redirecting all anomalous/noisy documents to the user review queue.

## 3. Cash-Flow Forecasting Algorithmic Progression (459 Chronological Folds)
| Model Hierarchy | MASE | MAE (BDT) | RMSE (BDT) | Empirical 80% CI Coverage | Relative Error vs Naive |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Model 0: Naive Persistence (Last Day)** | **0.998** | ৳14,469.30 | ৳16,910.44 | N/A | **0.0%** |
| **Model 1: Seasonal Naive (Last Week)** | **0.989** | ৳14,428.53 | ৳17,337.73 | N/A | **-0.9%** |
| **Model 2: 7-Day Rolling Moving Average** | **0.770** | ৳11,183.69 | ৳13,288.90 | 67.8% | **-22.7%** |
| **Model 3 (Active System): Autoregressive Ridge (Lagged + DOW + L2)** | **0.743** | ৳10,793.82 | ৳12,835.38 | 73.5% | **-25.4%** |

> [!TIP]
> Upgrading to Autoregressive Ridge achieves a **25.4% error reduction** over Naive persistence while delivering 73.5% empirical coverage on confidence bounds.

## 4. Financial AI Assistant: Heuristic Drift vs. Deterministic Guardrails (12 Scenarios)
- **Evidence Type:** `RULE_VERIFICATION_DETERMINISTIC`
- **Unconstrained Float Drift Rate:** `41.7%`
- **Guardrail Integer Drift Rate:** `0.0%` (Bit-exact reproducibility)
- **Regulatory DSCR Compliance Check:** `100.0%` (Strict enforcement of Bangladesh Bank 1.25x covenant)

| Loan Amount | Monthly EMI | Total Interest | DSCR | Guardrail Approved? | Float Drift (Minor Units) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| ৳500,000.00 | ৳22,842.37 | ৳48,216.88 | 4.67x | **Approved** | 0 cents |
| ৳700,000.00 | ৳32,463.23 | ৳79,117.52 | 1.22x | **Rejected** | 1 cents |
| ৳1,000,000.00 | ৳45,684.74 | ৳96,433.76 | 0.49x | **Rejected** | 0 cents |
| ৳200,000.00 | ৳17,490.30 | ৳9,883.60 | -1.14x | **Rejected** | 1 cents |
| ৳300,000.00 | ৳26,235.44 | ৳14,825.28 | 5.72x | **Approved** | 0 cents |
| ৳100,000.00 | ৳8,745.15 | ৳4,941.80 | -1.46x | **Rejected** | 1 cents |
