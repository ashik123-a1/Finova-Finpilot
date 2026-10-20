# FinTechathon 2026: SME Finance Copilot — Financial AI & RAG Engine

**Document Version:** 1.0.0 (Master Release)  
**Cognitive Architecture:** Hybrid Deterministic Finance + Grounded RAG + Local Offline Edge Fallback  
**Multilingual Support:** English (`en`), Bengali (`bn`), Simplified Chinese (`zh`)

---

## 1. Architectural Philosophy: The Autonomous Financial Participant

Unlike generic consumer chatbots that hallucinate plausible-sounding financial metrics, the SME Finance Copilot operates as an **Autonomous Financial Participant**. It enforces strict adherence to three core tenets:
1. **Ledger Grounding:** Every figure cited in advice is derived from authenticated database queries.
2. **Deterministic Computation:** Turnaround scenarios and ratios are calculated using integer math with zero floating-point errors.
3. **Domain-Intent Gating:** Documents (such as commercial loan sanction letters) are only cited when strictly relevant to the user's specific intent.

---

## 2. 11-Domain Intent Taxonomy

The classifier `RagService.classify_financial_intent()` maps incoming queries across English, Bengali, and Chinese into 11 discrete financial intent domains:

| Intent Key | Scope & Typical User Queries | Grounded Actions & Output |
| :--- | :--- | :--- |
| `business_loss_recovery` | *"I am in loss how can I recover?"*, *"ব্যবসা লসে আছে কিভাবে ঘুরে দাঁড়াবো?"*, *"亏损了如何扭亏为盈？"* | 5-stage turnaround plan, fixed overhead breakdown, quantified recovery scenarios. |
| `sales_revenue_growth` | *"How to increase sales?"*, *"বিক্রয় বৃদ্ধি"*, *"增加销售额"* | Daily run-rate analysis, RFM customer tier activation, bundling recommendations. |
| `expense_reduction` | *"How can I cut operating costs?"*, *"খরচ কিভাবে কমাবো?"*, *"削减开支"* | Fixed vs variable cost audit, 5% and 10% overhead reduction models. |
| `pricing_discount_decision`| *"Should I give a 20% discount on wholesale items?"*, *"ছাড় দেওয়া যাবে?"* | Minimum 15.0% contribution margin floor enforcement and erosion warnings. |
| `cash_flow_recovery` | *"I am running out of cash what should I do?"*, *"ক্যাশ সংকট"*, *"资金短缺"* | Daily cash burn rate, cash runway days calculation, liquidity defense protocol. |
| `overdue_receivables` | *"Customers are not paying their invoices"*, *"বাকির টাকা আদায়"*, *"催款"* | Aging receivables breakdown ($89,382.50 across 44 invoices), WhatsApp dunning. |
| `inventory_optimization` | *"Which items are overstocked or low in stock?"*, *"মজুদ স্থিতি"*, *"库存优化"* | Low-stock SKU alerts, stock holding valuation ($2,448,570.00), PO drafting. |
| `loan_suitability` | *"Can I qualify for an SME bank loan?"*, *"ঋণ যোগ্যতা"*, *"申请贷款"* | DSCR coverage against 1.25x benchmark, Net Operating Income (NOI), bank matching. |
| `supplier_purchasing` | *"Supplier price increase, how to handle procurement?"*, *"সরবরাহকারী চুক্তি"* | Contractual MOQ compliance, payment credit term alignment. |
| `document_policy` | *"What are the VAT rates under Mushak 6.3?"*, *"কর চালান"*, *"增值税专用发票"* | NBR commercial invoice rules, tax compliance reconciliation. |
| `general_finance` | *"Financial overview"*, *"ব্যবসার অবস্থা"*, *"财务总览"* | High-level ledger telemetry summary (Revenue, Expenses, Net Profit/Loss). |

---

## 3. The Loss Recovery Turnaround Workflow

When an SME merchant asks how to recover from an operational deficit, the Copilot executes a standardized 5-stage turnaround workflow:

### Stage 1: Current Financial Position
Extracts verified ledger actuals for the user's authorized shop:
* **Operating Revenue:** `$1,525,400.00` (816 verified transactions)
* **Operating Expenses:** `$4,868,176.68` (354 verified entries)
* **Net Operating Loss:** `-$3,342,776.68`
* **Reporting Period:** `2026-04-21` to `2026-10-20` (182 recorded days)
* **Currency:** Configured business currency (`USD` or `BDT`)

### Stage 2: Evidence-Backed Findings (Root Cause & Ledger Audit)
Identifies where capital is trapped and where spending is concentrated based on audited ledger records:
* **Audited Expense Breakdown (100% Denominator Basis):**
  1. Rent: `$2,036,584.89` (41.8% of total expenses, 38 entries)
  2. Salary: `$1,556,184.53` (32.0% of total expenses, 49 entries)
  3. Rent & Utilities: `$606,500.00` (12.5% of total expenses, 83 entries)
  4. Utilities: `$304,319.60` (6.3% of total expenses, 41 entries)
  5. Other Operating Expenses: `$364,587.66` (7.5% of total expenses, 143 entries)
* **Category Overlap & Duplicate Audit:**
  - Consolidated facility & utility spending (`rent` + `utilities` + `Rent & Utilities`) represents **`$2,947,404.49` (60.5% of total expenses)**.
  - Audit detected 82 duplicate voice entries totaling **`$603,000.00`** in `Rent & Utilities` (79 repeated entries of $7,500.00).
  - Payroll is classified as recorded labor expenditure rather than pure fixed overhead, as retail staffing often includes variable hours.
* **Working Capital Assessment (Not Immediately Available Cash):**
  - **Uncollected Receivables:** 44 unpaid customer invoices totaling **`$89,382.50`** (actionable for dunning, not yet collected cash).
  - **Inventory Capital:** 41 SKUs holding **`$2,448,570.00`** in merchandise valuation at cost (**not immediately recoverable cash**).

### Stage 3: Prioritized 3-Phase Action Plan
* **Phase 1: Immediate Cash Protection (Days 1–15):** Mobilize `$89,382.50` in overdue receivables via automated WhatsApp/SMS reminders; reconcile duplicate ledger entries; freeze discretionary spend.
* **Phase 2: Cost Restructuring (Days 16–45):** Renegotiate core commercial overheads (addressing `$2,947,404.49` in facility costs); align staff hours with peak retail foot-traffic.
* **Phase 3: Margin & Revenue Acceleration (Days 46–90):** Prioritize fast-moving high-margin SKUs; bundle slow movers with margin guardrails (>15%).

### Stage 4: Quantified Recovery Scenarios
Presents mathematical models grounded in historical actuals with clear distinction between revenue, expense savings, and net profit:
* **Scenario A (5% Expense Reduction):** Recovers **`$243,408.83`** directly in reduced operating cash outflow (5% of `$4,868,176.68`).
* **Scenario B (10% Sales Volume Growth):** Generates **`$152,540.00`** in **additional top-line revenue** (estimated gross margin contribution: **`$22,651.78`** based on the shop's ~14.8% average gross margin).
* **Scenario C (Combined Turnaround):**
  - **Combined Gross Relief:** **`$395,948.83`** (simple sum of `$243,408.83` expense savings + `$152,540.00` additional top-line revenue).
  - **Estimated Net Operating Deficit Reduction:** **`$266,060.61`** (`$243,408.83` cost savings + `$22,651.78` product margin contribution).
  - *(Audit Investigation Note: The previous figure of `$639,357.66` was traced to an unaligned calculation adding a 10% expense cut of `$486,817.66` to 10% top-line revenue of `$152,540.00` without deducting product costs. It has been corrected to prevent double counting and distinguish top-line revenue from net operating profit.)*
* *(Disclaimer: Scenarios are mathematical models based on historical ledger records and do not constitute guaranteed outcomes.)*

### Stage 5: Recommended Next Steps
Offers proactive follow-ups (e.g. *"Would you like me to inspect your 44 overdue customer invoices or initiate a product gross margin audit?"*).

---

## 4. Intent-Gated Document Retrieval

In prior versions, unconstrained vector cosine similarity caused bank loan sanction letters to be returned as citations for operational deficit questions. The upgraded `RagService.retrieve_context()` enforces domain barriers:
* **Loan Documents:** Only matched when `intent == "loan_suitability"`.
* **Tax/VAT Invoices:** Only matched when `intent == "document_policy"`.
* **Procurement Agreements:** Only matched when `intent == "supplier_purchasing"`.
* **Operational Turnaround Queries:** Suppress external document noise, ensuring zero false-positive citations.

---

## 5. Consequential Action Authorization Barrier

The Copilot is engineered with hard safety boundaries. When the user uses voice or text to command a state-changing financial action:
1. The operation is intercepted before execution.
2. An authorization card renders in the chat UI with the structured JSON payload.
3. The user must click **"Confirm Execution"** to execute the database write.
