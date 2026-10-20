# Finova Finpilot: SME Finance Copilot 🚀
### Autonomous AI as a Financial Participant | FinTechathon 2026 — Topic E (International Track)

[![Python 3.11](https://img.shields.io/badge/Python-3.11.9-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite WAL](https://img.shields.io/badge/SQLite-WAL_Mode-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-224%2F224_Passed-10B981?style=for-the-badge&logo=pytest&logoColor=white)](docs/TESTING.md)
[![Security](https://img.shields.io/badge/Security-RBAC_%26_DDE_Safe-6366F1?style=for-the-badge&logo=shield&logoColor=white)](docs/SECURITY.md)
[![Edge AI](https://img.shields.io/badge/Edge_AI-100%25_Offline_Ready-F59E0B?style=for-the-badge&logo=openai&logoColor=white)](docs/AI_COPILOT.md)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

---

## 📌 Executive Overview

**Finova Finpilot** (SME Finance Copilot) is a local-first, zero-float autonomous financial operating system built specifically for emerging-market micro, small, and medium enterprises (MSMEs). 

Across developing regions, more than 400 million small merchants lack full-time accountants, CFOs, or institutional credit access. Traditional accounting software is **purely passive**—it logs history but offers zero forward guidance. Generic AI chatbots fail by hallucinating financial figures and citing irrelevant contracts.

Finova Finpilot acts as an **Autonomous Financial Participant**:
1. **Zero-Float Precision Accounting:** Stores every transaction in 64-bit integer minor currency units, eliminating floating-point rounding errors.
2. **Deterministic Loss Recovery Engine:** Diagnoses operating deficits from live ledgers, identifies fixed overhead bottlenecks, and calculates quantified turnaround scenarios.
3. **Institutional Credit Underwriting (DSCR):** Computes real-time amortization schedules, evaluates Debt Service Coverage Ratios against commercial banking standards (1.25x benchmark), and generates official **Credit Underwriting Packet PDFs**.
4. **Autonomous Voice AI HUD:** Real-time speech interaction with a cryptographic two-step **Consequential Action Authorization Barrier** preventing unauthorized ledger writes.
5. **Local-First & 100% Offline Capable:** Self-contained SQLite WAL engine running completely on edge hardware without mandatory cloud lock-in.

---

## 📸 Visual Product Tour & Genuine Execution Evidence

Every screenshot below captures the real, unmocked application executing on the local-first engine:

### 1. Financial AI Copilot — Deterministic Turnaround (English & Bengali)
| 🤖 English Loss Recovery & Turnaround Scenarios | 🌐 Native Multilingual AI Turnaround (Bengali) |
| :---: | :---: |
| ![Copilot English Recovery](submission/execution_evidence/copilot_loss_recovery_verified.png) | ![Copilot Bengali Recovery](submission/execution_evidence/copilot_loss_recovery_bengali_verified.png) |
| *Root-cause diagnosis, audited 100% expense breakdown, duplicate voice entry detection, and Scenarios A/B/C* | *Identical underlying ledger calculations preserved across Bengali, English, and Chinese locales* |

### 2. Operational Control & Topic E Simulated Sandbox
| 📊 Executive Financial Cockpit & Ledger | 🔬 Topic E Simulated Sandbox & Agent Trace |
| :---: | :---: |
| ![Executive Dashboard](submission/execution_evidence/dashboard_executive_cockpit_verified.png) | ![Sandbox Agent Execution Evidence](submission/execution_evidence/sandbox_agent_execution_evidence_verified.png) |
| *Real-time cash runway, revenue/expense trends, and zero-float ledger reconciliation* | *Operational API request/response payloads and AI agent tool-calling execution traces* |

### 3. Institutional Credit Underwriting & Loan Calculator
| 🏛️ Commercial Credit Underwriting (DSCR 1.25x Benchmark) |
| :---: |
| ![DSCR Loan Calculator](submission/execution_evidence/dscr_underwriting_packet_verified.png) |
| *Real-time amortization schedule, debt-service coverage ratio assessment, and 1-click Bank Underwriting Packet PDF generator* |

---

## ⚡ 10-Minute Local Quickstart (Windows PowerShell)

### Step 1: Open Terminal & Activate Environment
```powershell
cd "F:\china project"
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Pinned Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Run Automated Verification Suite (224 Tests)
```powershell
python -m pytest
```
*Expected verification: `224 passed in ~20 seconds (100% pass rate)`.*

### Step 4: 1-Click Server Launch
```powershell
.\start.bat
```
Open your browser and navigate to: **`http://127.0.0.1:8050`**

<details>
<summary><b>📖 Expand to view complete Cross-Platform Installation & Troubleshooting Guide (Linux / macOS / Docker / Codespaces)</b></summary>

### Linux / macOS / GitHub Codespaces Setup
```bash
# 1. Clone repository (or enter directory)
git clone https://github.com/ashik123-a1/Finova-Finpilot.git
cd "Finova-Finpilot"

# 2. Set up Python 3.11 virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Prepare environment configuration
cp .env.example .env

# 5. Initialize database
python -c "from src.database.connection import init_db; init_db()"

# 6. Run regression tests
pytest

# 7. Start application server
uvicorn src.api.app:app --host 0.0.0.0 --port 8050
```

### Troubleshooting Common Issues
* **Port 8050 in Use:** Run `netstat -ano | findstr :8050` (Windows) or `lsof -i :8050` (Linux) and terminate the orphaned process, or launch on an alternative port: `uvicorn src.api.app:app --port 8051`.
* **Database Locked:** Finova Finpilot uses SQLite WAL mode. Ensure the database file `sme_finance.db` is not opened in exclusive lock mode by external database GUI viewers during test runs.
* **Tesseract OCR Optional Fallback:** If Tesseract is not installed locally, the system automatically falls back to deterministic rule-based OCR tokenizers with 100% test passing.

*(For the complete step-by-step manual, inspect [`docs/INSTRUCTION_BOOK.md`](docs/INSTRUCTION_BOOK.md))*

</details>

---

## 👥 7 Selectable Demo Personas

On the login page (`http://127.0.0.1:8050/login`), evaluators can authenticate in **1-Click** across 7 canonical personas:

| Persona | Role Code | Credentials | Authorized Scope |
| :--- | :--- | :--- | :--- |
| **Business Owner** | `owner` | `demo_owner@smefinance.local` / `DemoPass123!` | Complete enterprise control, loss recovery, loan packet |
| **Store Manager** | `manager` | `demo_manager@smefinance.local` / `DemoPass123!` | Daily shop operations, inventory reorders, sales |
| **Senior Accountant** | `accountant`| `demo_accountant@smefinance.local` / `DemoPass123!` | General ledger, OCR document reviews, CSV/PDF reports |
| **Sales Executive** | `sales` | `demo_sales@smefinance.local` / `DemoPass123!` | POS sales, customer RFM tiers, WhatsApp dunning |
| **Inventory Officer** | `inventory` | `demo_inventory@smefinance.local` / `DemoPass123!` | Stock movements, warehouse valuation, purchase orders |
| **External Auditor** | `auditor` | `demo_auditor@smefinance.local` / `DemoPass123!` | Read-only compliance audit trails, SHA-256 hash inspection |
| **Super Admin** | `super_admin`| `super_admin@smefinance.local` / `DemoPass123!` | Platform Admin Portal (`/app/admin`), multi-tenant health |

---

## 🧪 Testing & Verification Summary

The system is validated through a canonical catalogue of **50 Numbered Test Cases (TC-01..TC-50)** across 21 test files:

| Focus Area | Test File | Tests | Pass Rate | Status |
| :--- | :--- | :---: | :---: | :---: |
| **AI Intent Routing & Loss Turnaround** | `tests/test_ai_copilot_intelligence.py` | 13 | 100% | **PASS** |
| **RAG Embeddings & Tenant Isolation** | `tests/test_rag_pipeline.py` | 14 | 100% | **PASS** |
| **API Endpoints & OCR Processing** | `tests/test_api_integration.py` | 10 | 100% | **PASS** |
| **API Security & Path Traversal** | `tests/test_api_security_verification.py` | 19 | 100% | **PASS** |
| **Auth & 7 Demo Personas** | `tests/test_auth_and_rbac.py` | 9 | 100% | **PASS** |
| **Commercial Onboarding & Invites** | `tests/test_commercial_onboarding.py` | 5 | 100% | **PASS** |
| **7 Country Profiles & Currency** | `tests/test_country_profiles.py` | 7 | 100% | **PASS** |
| **CRM RFM & Inventory Restocking** | `tests/test_crm_and_inventory.py` | 13 | 100% | **PASS** |
| **Dashboard KPIs & Ledger Reconcile**| `tests/test_dashboard_live_kpi.py` | 8 | 100% | **PASS** |
| **Multilingual Voice AI & Safeguards**| `tests/test_i18n_and_voice.py` / `test_voice_ai.py` | 29 | 100% | **PASS** |
| **Loan Calculator, DSCR & PDF Packet**| `tests/test_loan_and_dscr_module.py` | 7 | 100% | **PASS** |
| **Persistence, CSV Injection & Backups**| `tests/test_report_generation_and_storage.py` | 7 | 100% | **PASS** |
| **Web UI, Navigation & Portals** | `tests/test_web_ui.py` | 7 | 100% | **PASS** |
| **Other Core Security & Integrity** | Remaining 8 test suites | 76 | 100% | **PASS** |
| **TOTAL REGRESSION SUITE** | **21 Test Suites** | **224** | **100%** | **224/224 PASS** |

<details>
<summary><b>🧪 Expand to view all 50 Canonical Test Cases & QA Matrix (TC-01 to TC-50)</b></summary>

| ID | Module / Feature | Objective | Required Role | Automated Test Reference | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-01** | Core / Health | Verify `/health` returns operational status & DB connection | Public | `test_api_integration.py` | **PASS** |
| **TC-02** | Auth / Register | Register new SME merchant with auto-assigned `owner` role | Public | `test_auth_and_rbac.py` | **PASS** |
| **TC-03** | Auth / Login | Authenticate merchant with bcrypt hash & issue HMAC token | Public | `test_auth_and_rbac.py` | **PASS** |
| **TC-04** | Auth / Session | Verify HMAC SHA-256 session token validation & expiry | User | `test_auth_and_rbac.py` | **PASS** |
| **TC-05** | RBAC / Admin | Verify Super Admin access to `/app/admin` & tenant controls | Super Admin | `test_auth_and_rbac.py` | **PASS** |
| **TC-06** | RBAC / Auditor | Enforce read-only boundary for auditor role (block write ops) | Auditor | `test_rbac_permissions.py` | **PASS** |
| **TC-07** | Tenant Isolation | Block merchant in Shop A from accessing inventory of Shop B | Owner | `test_isolation.py` | **PASS** |
| **TC-08** | Ledger / Integer | Verify zero floating-point drift in 64-bit integer minor math | Accountant | `test_finance_calculator.py` | **PASS** |
| **TC-09** | Ledger / Income | Record sales transaction and verify positive ledger balance | Accountant | `test_api_integration.py` | **PASS** |
| **TC-10** | Ledger / Expense | Record operational expense and verify category mapping | Accountant | `test_api_integration.py` | **PASS** |
| **TC-11** | Ledger / Reconcile | Verify arithmetic invariant: `Revenue - Expenses == Net Profit` | Accountant | `test_dashboard_live_kpi.py` | **PASS** |
| **TC-12** | Cash Runway | Calculate burn rate and operational cash runway in days | Manager | `test_api_integration.py` | **PASS** |
| **TC-13** | Cash Alert | Trigger automated warning banner when runway drops < 30 days | Owner | `test_notifications.py` | **PASS** |
| **TC-14** | Loan / EMI | Calculate monthly amortization payments with decimal precision | Owner | `test_loan_and_dscr_module.py` | **PASS** |
| **TC-15** | Loan / DSCR | Verify DSCR computation against standard 1.25x bank benchmark | Owner | `test_loan_and_dscr_module.py` | **PASS** |
| **TC-16** | Loan / Packet PDF | Generate downloadable commercial credit underwriting packet | Owner | `test_loan_and_dscr_module.py` | **PASS** |
| **TC-17** | OCR / Upload | Upload invoice image/PDF and stage for accountant review | Accountant | `test_document_pipeline.py` | **PASS** |
| **TC-18** | OCR / Extract | Extract vendor, date, line items, and VAT registration tokens | Accountant | `test_document_pipeline.py` | **PASS** |
| **TC-19** | OCR / Post | Review, approve, and post verified OCR receipt to ledger | Accountant | `test_phase_gate_readiness.py` | **PASS** |
| **TC-20** | CRM / Customer | Create customer record with tax ID and contact information | Sales | `test_crm_and_inventory.py` | **PASS** |
| **TC-21** | CRM / RFM | Segment customers into Champions, Loyal, and At-Risk tiers | Sales | `test_crm_and_inventory.py` | **PASS** |
| **TC-22** | CRM / Receivables | Query overdue customer receivables ($89,382.50 across 44 inv) | Sales | `test_crm_and_inventory.py` | **PASS** |
| **TC-23** | CRM / Dunning | Generate simulated polite/firm WhatsApp collection reminders | Sales | `test_crm_and_inventory.py` | **PASS** |
| **TC-24** | Inventory / CRUD | Add product SKU, reorder point, unit cost, and retail price | Inventory | `test_crm_and_inventory.py` | **PASS** |
| **TC-25** | Inventory / Alert | Trigger low-stock restock indicator when quantity < reorder | Inventory | `test_crm_and_inventory.py` | **PASS** |
| **TC-26** | Inventory / Valuation| Calculate inventory asset holding valuation ($2,448,570.00) | Inventory | `test_crm_and_inventory.py` | **PASS** |
| **TC-27** | Inventory / PO | Auto-generate purchase order draft for depleted inventory SKUs | Inventory | `test_crm_and_inventory.py` | **PASS** |
| **TC-28** | AI / Intent Classify| Classify queries across 11 financial domains (EN / BN / ZH) | User | `test_ai_copilot_intelligence.py` | **PASS** |
| **TC-29** | AI / Loss Recovery | Execute 5-stage turnaround workflow on operational deficit | Owner | `test_ai_copilot_intelligence.py` | **PASS** |
| **TC-30** | AI / Expense Audit | Audit 100% expense breakdown and flag facility overlaps | Owner | `test_ai_copilot_intelligence.py` | **PASS** |
| **TC-31** | AI / Scenarios | Model Scenario A ($243k cut) & Scenario B ($152k revenue) | Owner | `test_ai_copilot_intelligence.py` | **PASS** |
| **TC-32** | AI / Margin Floor | Enforce 15.0% gross margin floor on discount advice | Owner | `test_ai_copilot_intelligence.py` | **PASS** |
| **TC-33** | AI / RAG Gating | Restrict bank loan citations to loan-specific questions | User | `test_rag_pipeline.py` | **PASS** |
| **TC-34** | AI / Offline Edge | Fall back to local embedded intelligence when offline | User | `test_rag_pipeline.py` | **PASS** |
| **TC-35** | Voice / Intent | Transcribe and parse voice commands to structured actions | User | `test_voice_ai.py` | **PASS** |
| **TC-36** | Voice / Barrier | Halt consequential writes at cryptographic 2-step barrier | User | `test_voice_ai.py` | **PASS** |
| **TC-37** | i18n / English | Verify English UI strings, date formats, and currency signs | User | `test_i18n_multilingual.py` | **PASS** |
| **TC-38** | i18n / Bengali | Verify Bengali বাংলা translations and local number formatting | User | `test_i18n_multilingual.py` | **PASS** |
| **TC-39** | i18n / Chinese | Verify Simplified Chinese 简体中文 catalog and layouts | User | `test_i18n_multilingual.py` | **PASS** |
| **TC-40** | Currency Precision | Support 2-decimal USD/BDT and 3-decimal Kuwaiti Dinar (KWD)| User | `test_country_profiles.py` | **PASS** |
| **TC-41** | Notifications | Deduplicate unread event notifications and mark as read | User | `test_notifications.py` | **PASS** |
| **TC-42** | Security / Tokens | Ignore client-supplied `X-User-ID` or `X-Role` headers | Public | `test_api_security_verification.py`| **PASS** |
| **TC-43** | Security / Prompt | Neutralize adversarial prompt injections (DAN, overrides) | User | `test_rag_pipeline.py` | **PASS** |
| **TC-44** | Security / DDE | Sanitize CSV export formula injection prefixes (`=`, `+`, `-`, `@`)| User | `test_report_generation_and_storage.py`| **PASS** |
| **TC-45** | Security / Traversal| Block directory path traversal attempts (`../`) on files | User | `test_api_security_verification.py`| **PASS** |
| **TC-46** | Backup / WAL | Take online non-blocking SQLite snapshot under write load | Super Admin | `test_report_generation_and_storage.py`| **PASS** |
| **TC-47** | Backup / Integrity | Verify SHA-256 cryptographic manifest on backup archives | Super Admin | `test_report_generation_and_storage.py`| **PASS** |
| **TC-48** | Reports / PDF | Export formatted Balance Sheet and P&L financial reports | Accountant | `test_report_generation_and_storage.py`| **PASS** |
| **TC-49** | Sandbox Simulator | Load simulated transaction telemetry for Topic E testing | User | `test_synthetic_generator.py` | **PASS** |
| **TC-50** | Audit Log Trail | Record immutable SHA-256 audit entry for security actions | Auditor | `test_api_integration.py` | **PASS** |

*(For the complete test execution report and reproduction commands, inspect [`docs/TESTING.md`](docs/TESTING.md))*

</details>

---

## 🤖 The AI Copilot: Solving Real SME Turnarounds

When a merchant facing losses asks: *"I am in loss how can I recover?"*, Finova Finpilot executes an 11-domain intent classifier grounded in live ledger records:

```
[Merchant: "I am in loss how can I recover?"]
                     │
                     ▼
### 1. Current Financial Position
- Operating Revenue: 1,525,400.00 USD (816 verified transactions)
- Operating Expenses: 4,868,176.68 USD (354 verified entries)
- Net Operating Loss: -3,342,776.68 USD
- Reporting Period: 2026-04-21 to 2026-10-20 (182 recorded days)
- Currency: USD (Configured enterprise business currency)

### 2. Evidence-Backed Findings (Root Cause & Ledger Audit)
- Audited Expense Breakdown (by Recorded Ledger Classification):
  1. Rent: 2,036,584.89 USD (41.8% of total, 38 entries)
  2. Salary: 1,556,184.53 USD (32.0% of total, 49 entries)
  3. Rent & Utilities: 606,500.00 USD (12.5% of total, 83 entries)
  4. Utilities: 304,319.60 USD (6.3% of total, 41 entries)
  5. Other Operating Expenses: 364,587.66 USD (7.5% of total, 143 entries)
  *(Percentage denominator: 100.0% of total verified operating expenses of $4,868,176.68)*
- Category Overlap & Duplicate Findings:
  - Categories 'rent', 'utilities', and hybrid 'Rent & Utilities' represent overlapping occupancy costs totaling $2,947,404.49 (60.5% of all expenses).
  - Ledger audit detected 82 duplicate entries totaling $603,000.00 in 'Rent & Utilities' (including 79 identical entries of $7,500.00).
  - Payroll ($1,556,184.53, 32.0%) may include variable retail staffing; classification as pure fixed overhead is not supported without contract verification.
- Working Capital Assessment (Not Immediately Available Cash):
  - Trapped Liquidity: 44 unpaid customer invoices representing $89,382.50 in uncollected accounts receivable (not yet collected cash).
  - Inventory Holding: 41 SKUs holding $2,448,570.00 in merchandise valuation at cost (inventory is not immediately recoverable cash).

### 3. Prioritized 3-Phase Action Plan
1. Immediate Cash Defense (Days 1–15): Mobilize $89,382.50 in overdue receivables via automated WhatsApp dunning and reconcile duplicate ledger entries.
2. Cost Restructuring (Days 16–45): Renegotiate commercial rent/utilities and align staff hours with peak retail foot-traffic.
3. Margin Acceleration (Days 46–90): Shift merchandising to fast-moving high-margin SKUs; bundle slow movers with margin floors (>15%).

### 4. Quantified Turnaround Scenarios (Mathematical Models)
- Scenario A (5% Expense Cut): Recovers $243,408.83 in reduced cash outflow (5% of $4,868,176.68).
- Scenario B (10% Sales Volume Growth): Generates $152,540.00 in additional top-line revenue (estimated gross margin contribution: ~$22,651.78 at ~14.8% gross margin).
- Scenario C (Combined Dual Turnaround): 
  - Combined gross relief: $395,948.83 (simple sum of $243,408.83 expense savings + $152,540.00 additional revenue).
  - Estimated net loss reduction: $266,060.61 ($243,408.83 savings + $22,651.78 margin contribution).
  *(Audit Investigation Note: The previous figure of $639,357.66 was traced to an unaligned calculation adding 10% expense cuts to 10% gross revenue without deducting COGS, and has been corrected.)*
*(Disclaimer: Scenarios are mathematical models based on historical ledger records and do not constitute guaranteed outcomes.)*

### 5. Recommended Next Steps
"Would you like me to inspect your 44 overdue customer invoices or initiate a product gross margin audit?"
```

<details>
<summary><b>🤖 Expand to view 11-Domain Intent Taxonomy & Guardrail Specification</b></summary>

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

*(For full AI architecture and voice action safeguards, see [`docs/AI_COPILOT.md`](docs/AI_COPILOT.md))*

</details>

---

## 🔒 Security Posture & Known Limitations

* **Zero Header Forgery:** Client-supplied headers (`X-User-ID`, `X-Role`) are completely ignored. Identity is derived strictly from signed HMAC SHA-256 tokens.
* **Adversarial Prompt-Injection Defense:** Jailbreak patterns (DAN, system overrides) are blocked before RAG retrieval.
* **Consequential Action Barrier:** Autonomous voice/AI transactions halt at two-step authorization barriers requiring cryptographic user confirmation before modifying the ledger.
* **CSV Formula Injection (DDE) Defense:** Exported CSV cells starting with `=`, `+`, `-`, `@` are automatically escaped with leading single quotes.
* **WAL-Safe Disaster Recovery:** Automated online backups (`var/backups/`) generate verified SQLite snapshots (`23.46 MB`, 163,054 records) with SHA-256 integrity manifests.

<details>
<summary><b>⚠️ Expand to view Transparent Engineering Disclosures & Known Limitations</b></summary>

### Honest Engineering Disclosures
1. **Simulated Commercial Banking APIs:** While real Debt Service Coverage Ratios (DSCR), amortization schedules, and loan application packets are fully generated in PDF format, communication with commercial banks (e.g., BRAC Bank, City Bank) runs via a sandbox simulator. Live institutional banking integration requires production Open Banking credentials.
2. **Synthetic Data Disclosure:** The pre-populated demonstration database contains 163,000+ realistic synthetic transactions, invoices, and audit logs. This data is rigorously structured to test enterprise scale but does not represent actual commercial entities.
3. **Hardware-Dependent Web Speech API:** Voice input relies on the browser's native `SpeechRecognition` Web API. If the browser or environment lacks microphone access, the system provides full keyboard and audio fallback.
4. **Offline RAG Embeddings:** In offline mode, the system utilizes local cosine keyword heuristics and vector representations. External cloud LLM providers (e.g. OpenAI, DeepSeek) are strictly optional and can be toggled via environment flags without breaking local operations.

*(For detailed disclosures, see [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md))*

</details>

---

## 🏛️ Technical Architecture & Repository Topology

*(Moved to this technical section for in-depth architectural inspection)*

### System Architecture Topology

```mermaid
flowchart TD
    classDef client fill:#0f172a,stroke:#0ea5e9,stroke-width:2px,color:#fff;
    classDef gateway fill:#1e293b,stroke:#6366f1,stroke-width:2px,color:#fff;
    classDef core fill:#022c22,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef ai fill:#311042,stroke:#a855f7,stroke-width:2px,color:#fff;
    classDef storage fill:#1c1917,stroke:#f59e0b,stroke-width:2px,color:#fff;

    subgraph CLIENTS [" Client Tiers (Glassmorphism Web & Voice HUD) "]
        UI["Executive Dashboard & Cockpit"]:::client
        COPILOT["Financial AI Copilot Chat"]:::client
        VOICE["Autonomous Voice AI HUD"]:::client
    end

    subgraph GATEWAY [" FastAPI ASGI Application Gateway "]
        AUTH["HMAC SHA-256 Auth & RBAC Guard"]:::gateway
        ROUTERS["18 Domain Service Routers"]:::gateway
    end

    subgraph CORE [" Deterministic Finance & Underwriting Core "]
        LEDGER["Zero-Float Integer Ledger Engine"]:::core
        DSCR["Credit Underwriting & DSCR Engine (1.25x)"]:::core
        EXPORTERS["ReportLab PDF & Safe CSV Exporters"]:::core
    end

    subgraph AI_SUBSYSTEM [" Hybrid AI & RAG Subsystem "]
        INTENT["11-Domain Intent Classifier (EN / BN / ZH)"]:::ai
        RAG["Intent-Gated Document Vector Retriever"]:::ai
        TURNAROUND["5-Stage Turnaround Scenario Modeler"]:::ai
        BARRIER["Consequential Action Confirmation Barrier"]:::ai
    end

    subgraph PERSISTENCE [" Local-First Persistence Layer "]
        DB[("SQLite 3 Database (WAL Mode)<br/>50 Relational Entities | 163,000+ Records")]:::storage
        BACKUP["WAL-Safe Online Backups & SHA-256 Manifests"]:::storage
    end

    CLIENTS --> AUTH
    AUTH --> ROUTERS
    ROUTERS --> LEDGER
    ROUTERS --> DSCR
    ROUTERS --> INTENT
    INTENT --> RAG
    INTENT --> TURNAROUND
    VOICE --> BARRIER
    BARRIER -.->|Authorized Confirmation| LEDGER
    LEDGER --> DB
    DSCR --> EXPORTERS
    DB --> BACKUP
```

### Compact Visual Project Tree

```text
Finova-Finpilot/                                   # Competition submission root directory
├── README.md                                      # Executive overview, architecture, test badges & quickstart
├── .gitignore                                     # Excludes secrets (.env), SQLite binaries & private caches
├── .env.example                                   # Secure environment variable configuration template
├── pyproject.toml                                 # Python packaging, toolchain configurations & pytest settings
├── requirements.txt                               # Pinned backend dependencies (FastAPI, SQLAlchemy, ReportLab)
├── start.bat                                      # 1-Click Windows launch script (Uvicorn on port 8050)
├── share_online.bat                               # Optional encrypted public tunnel launcher for live evaluation
├── sme_finance.db                                 # Primary SQLite database with WAL mode (163,000+ records)
│
├── docs/                                          # Technical, architecture & competition documentation
│   ├── ARCHITECTURE.md                            # Comprehensive system architecture & data pipeline flow
│   ├── DATABASE.md                                # Database schema, 8 migrations, WAL mode & recovery protocol
│   ├── API_REFERENCE.md                           # Exhaustive API reference for all 18 backend service routers
│   ├── SECURITY.md                                # Security posture, RBAC matrices, HMAC tokens & threat model
│   ├── TESTING.md                                 # Canonical 50 numbered test cases (TC-01..TC-50) & 224 test audit
│   ├── INSTRUCTION_BOOK.md                        # Complete local installation, execution & troubleshooting manual
│   ├── PROJECT_STRUCTURE.md                       # Full screenshot-style terminal tree with # comments
│   ├── DEPLOYMENT.md                              # Local-first execution, production ASGI flags & container guide
│   ├── AI_COPILOT.md                              # 11-category financial intent routing & loss turnaround mechanics
│   ├── REPORTS_AND_BACKUPS.md                     # Authorized CSV/PDF export & isolated disaster recovery guide
│   └── KNOWN_LIMITATIONS.md                       # Transparent disclosure of simulated and non-implemented areas
│
├── src/                                           # Production application source code
│   ├── ai/                                        # 11-intent classifier, grounded ledger extractor & Voice AI
│   ├── api/                                       # FastAPI gateway, dependency injection & 18 REST routers
│   ├── core/                                      # Zero-float banking math, amortization & 7 country profiles
│   ├── crm/                                       # Customer RFM segmentation & WhatsApp receivables dunning
│   ├── database/                                  # 50 ORM models, WAL backup service & 8 SQL migrations
│   ├── documents/                                 # Smart OCR document upload, classification & review staging
│   ├── finance/                                   # Institutional Loan Packet PDF generator & CSV/PDF exporters
│   ├── i18n/                                      # Multilingual engine (English, Bengali বাংলা, Chinese 简体中文)
│   └── web/                                       # Glassmorphism frontend templates & cyber-fintech static assets
│
├── tests/                                         # 21 test suites containing 224 passing automated tests
├── var/                                           # Backups (.db + SHA-256 manifests) & exports (Git-ignored)
├── reports/                                       # Release audit, 224-test execution report & dependency inventory
└── submission/                                    # Competition deliverables, PDFs, presentation deck & evidence
```

<details>
<summary><b>📂 Expand to view Complete Annotated Directory Tree & File Catalog (docs/PROJECT_STRUCTURE.md)</b></summary>

```text
Finova-Finpilot/                                   # Root project folder
├── .env.example                                   # Configuration template (JWT secrets, port, SQLite DB path)
├── .gitignore                                     # Clean repository exclusions (venv/, *.db-wal, *.pyc, var/)
├── README.md                                      # Primary competition overview & execution instructions
├── pyproject.toml                                 # Python packaging, pytest settings & dependencies
├── requirements.txt                               # Explicit package pins (FastAPI, SQLAlchemy, ReportLab, etc.)
├── share_online.bat                               # Cloudflare quick-tunnel launcher for remote jury evaluation
├── sme_finance.db                                 # Operational SQLite database (163,000+ pre-seeded records)
├── start.bat                                      # 1-Click production ASGI launcher
│
├── docs/                                          # Formal Competition Documentation (12 Dedicated Books)
│   ├── AI_COPILOT.md                              # Cognitive architecture, intent mapping & loss recovery math
│   ├── API_REFERENCE.md                           # Exhaustive 18-router REST API catalog with sample payloads
│   ├── ARCHITECTURE.md                            # Comprehensive topology, sequence flows & design tenets
│   ├── DATABASE.md                                # 50-table schema, 8 migrations & WAL recovery protocols
│   ├── DEPLOYMENT.md                              # Local edge execution, systemd & containerized blueprints
│   ├── INSTRUCTION_BOOK.md                        # Master setup, local runtime & troubleshooting playbook
│   ├── KNOWN_LIMITATIONS.md                       # Transparent engineering disclosures & future roadmap
│   ├── PROJECT_STRUCTURE.md                       # Complete visual source-tree map with inline annotations
│   ├── REPORTS_AND_BACKUPS.md                     # WAL-safe disaster recovery, CSV sanitation & PDF reports
│   ├── SECURITY.md                                # Threat models, RBAC privilege matrix & anti-tamper rules
│   └── TESTING.md                                 # 50 canonical test cases catalogue & 224-test audit trail
│
├── src/                                           # Application Source Engine
│   ├── ai/                                        # Artificial Intelligence & Cognitive Services
│   │   ├── copilot_service.py                     # Financial conversation manager & dialogue memory
│   │   ├── loss_recovery_engine.py                # Deterministic turnaround scenario modeler (Scenarios A/B/C)
│   │   ├── rag_service.py                         # Intent-gated vector search & ledger context extractor
│   │   └── voice_service.py                       # Voice AI parsing, action barriers & confirmation tokens
│   ├── api/                                       # Application Gateway & REST Endpoints
│   │   ├── app.py                                 # FastAPI initialization, middleware & static mounting
│   │   ├── dependencies.py                        # HMAC auth token validation & tenant workspace context
│   │   └── routes/                                # 18 Domain-Specific REST Routers
│   │       ├── admin.py                           # Super Admin platform oversight & health audits
│   │       ├── ai.py                              # Copilot chat and intent endpoints
│   │       ├── auth.py                            # Login, registration & demo persona session dispatch
│   │       ├── crm.py                             # Customer management & receivables collection
│   │       ├── dashboard.py                       # High-performance KPI aggregation queries
│   │       ├── documents.py                       # OCR upload and document review queue
│   │       ├── finance.py                         # Double-entry ledger postings and reconciliations
│   │       ├── inventory.py                       # Product inventory, movements & purchase orders
│   │       ├── loans.py                           # DSCR credit underwriting & bank packet export
│   │       ├── notifications.py                   # Real-time event notifications & read states
│   │       ├── reports.py                         # Financial statement generation (P&L, Balance Sheet)
│   │       ├── voice.py                           # Real-time speech input & action barrier execution
│   │       └── web.py                             # HTML template rendering for browser users
│   ├── core/                                      # Mathematical & Multi-Jurisdictional Foundation
│   │   ├── currency.py                            # Multi-currency decimal rules (USD, BDT, CNY, KWD)
│   │   ├── exceptions.py                          # Domain-specific error codes and HTTP mappings
│   │   ├── financial_math.py                      # Zero-float integer arithmetic & EMI calculation
│   │   └── security.py                            # HMAC SHA-256 signing & CSV formula neutralization
│   ├── crm/                                       # Customer Relationship Management Subsystem
│   │   ├── dunning_service.py                     # Automated polite/firm reminder generation
│   │   └── rfm_service.py                         # Recency-Frequency-Monetary segmentation engine
│   ├── database/                                  # Data Access & Persistence Layer
│   │   ├── backup_service.py                      # Hot WAL backup snapshotting & SHA-256 integrity
│   │   ├── connection.py                          # Engine, sessionmaker & WAL PRAGMA configuration
│   │   ├── migrations/                            # 8 Schema migrations (V1 to V8)
│   │   └── models/                                # 50 Declarative SQLAlchemy Relational Entities
│   ├── documents/                                 # OCR & Computer Vision Subsystem
│   │   ├── ocr_engine.py                          # Multi-pass Tesseract OCR & regex tokenizers
│   │   └── staging_service.py                     # Document quarantine, review & ledger posting
│   ├── finance/                                   # Credit Underwriting & Institutional Reporting
│   │   ├── dscr_service.py                        # Debt Service Coverage Ratio evaluation (1.25x)
│   │   ├── packet_generator.py                    # ReportLab Bank Underwriting Packet PDF builder
│   │   └── statement_service.py                   # P&L, Cash Flow & Balance Sheet statement compiler
│   ├── i18n/                                      # Multilingual Localization Engine
│   │   ├── catalogs/                              # en.json (English), bn.json (বাংলা), zh.json (中文)
│   │   └── translator.py                          # Dynamic key lookup & pluralization formatter
│   └── web/                                       # Frontend Presentation Layer
│       ├── static/                                # Cyber-fintech CSS, Vanilla JS modules & brand assets
│       └── templates/                             # Jinja2 templates (Dashboard, Copilot, Admin, Loans)
│
├── tests/                                         # Test Automation & Verification Engine (224 Tests)
│   ├── conftest.py                                # Test database fixtures, mock clients & seeds
│   ├── test_ai_copilot_intelligence.py            # AI intent classification & turnaround math
│   ├── test_api_integration.py                   # End-to-end endpoint verification
│   ├── test_api_security_verification.py          # Threat defense & header injection tests
│   ├── test_auth_and_rbac.py                      # Authentication & role-based access checks
│   ├── test_commercial_onboarding.py              # Self-serve merchant registration
│   ├── test_country_profiles.py                   # Multi-currency precision tests
│   ├── test_crm_and_inventory.py                  # RFM & stock restock automation
│   ├── test_dashboard_live_kpi.py                 # KPI aggregation & ledger sync
│   ├── test_document_pipeline.py                  # OCR extraction & verification
│   ├── test_i18n_and_voice.py                     # Multilingual strings & voice action barrier
│   ├── test_loan_and_dscr_module.py               # Loan underwriting & DSCR math
│   ├── test_multilingual_security.py              # XSS & character encoding security
│   ├── test_rag_pipeline.py                       # Vector retrieval & prompt injection
│   └── test_voice_ai.py                           # Voice intent extraction & confirmation barrier
│
└── submission/                                    # FinTechathon 2026 Deliverables Package
    ├── README.md                                  # Submission manifest & judging orientation
    ├── demo_script.md                             # 10-Minute live evaluation demonstration script
    ├── presentation.pdf                           # Final pitch deck presentation (PDF format)
    ├── presentation.pptx                          # Final pitch deck presentation (PowerPoint format)
    ├── presentation_script.md                     # Timed 5-minute competitive pitch script
    ├── security_self_assessment.pdf               # Comprehensive cybersecurity evaluation
    ├── technical_documentation.pdf                # Consolidated system technical manual
    └── execution_evidence/                        # Verified high-resolution screenshots
        ├── copilot_loss_recovery_verified.png     # Real AI loss recovery calculation
        ├── copilot_loss_recovery_bengali_verified.png # Native Bengali AI turnaround
        ├── dashboard_executive_cockpit_verified.png # Live financial dashboard
        ├── dscr_underwriting_packet_verified.png  # Credit underwriting loan calculator
        └── sandbox_agent_execution_evidence_verified.png # Simulated API & agent execution trace
```

</details>

---

## 📚 Complete Documentation Index

| Documentation File | Description |
| :--- | :--- |
| 📘 [`docs/INSTRUCTION_BOOK.md`](docs/INSTRUCTION_BOOK.md) | Comprehensive step-by-step local setup, execution, and troubleshooting guide |
| 🧪 [`docs/TESTING.md`](docs/TESTING.md) | Canonical 50 numbered test cases (TC-01..TC-50) and QA methodology |
| 🏗️ [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | High-level topology, local-first principles, and end-to-end data flows |
| 🗄️ [`docs/DATABASE.md`](docs/DATABASE.md) | Relational schema (50 tables), 8 migrations, WAL mode, and restore guide |
| 🔌 [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) | Exhaustive REST API reference across 18 backend service routers |
| 🛡️ [`docs/SECURITY.md`](docs/SECURITY.md) | Security posture, threat modeling, RBAC matrices, and guardrails |
| 📂 [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) | Full screenshot-style visual terminal directory tree with `#` comments |
| 🤖 [`docs/AI_COPILOT.md`](docs/AI_COPILOT.md) | 11-intent taxonomy, loss turnaround workflow, and offline synthesis |
| 🚀 [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Production ASGI flags, container readiness, and Cloudflare tunnels |
| 📊 [`docs/REPORTS_AND_BACKUPS.md`](docs/REPORTS_AND_BACKUPS.md) | Financial statement generation and WAL-safe disaster recovery |
| ⚠️ [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md) | Honest disclosures of synthetic data and hardware-dependent voice |
| 📦 [`submission/README.md`](submission/README.md) | Master competition submission package and presentation overview |

---

## 🏆 FinTechathon 2026 Submission Package

All formal deliverables have been compiled into the [`submission/`](submission/) directory:
* 📄 **Technical Documentation PDF:** [`submission/technical_documentation.pdf`](submission/technical_documentation.pdf)
* 🛡️ **Security Self-Assessment PDF:** [`submission/security_self_assessment.pdf`](submission/security_self_assessment.pdf)
* 📊 **Presentation Pitch Deck PDF:** [`submission/presentation.pdf`](submission/presentation.pdf)
* 📽️ **Presentation Pitch Deck PPTX:** [`submission/presentation.pptx`](submission/presentation.pptx)
* 🎤 **Timed 5-Minute Speaker Script:** [`submission/presentation_script.md`](submission/presentation_script.md)
* 🎬 **10-Minute Live Demo Script:** [`submission/demo_script.md`](submission/demo_script.md)
* 📸 **Genuine Execution Evidence:** [`submission/execution_evidence/`](submission/execution_evidence/)

---
**Developed with Precision for FinTechathon 2026**
