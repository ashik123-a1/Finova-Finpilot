# SME Finance Copilot — Phase 1: Local Database, Synthetic Data & AI Foundation

An intelligent, local-first financial operating system and AI copilot designed for small and medium-sized enterprises (SMEs).

---

## Key Capabilities (Phase 1)

1. **Local-First Relational Database:**
   - 43 normalized tables covering Identity, Sales, Purchases, Expenses, Payments, Receivables, Inventory Movements, Documents, Demo Banks, and AI Model Registries.
   - Powered by SQLite with Write-Ahead Logging (`WAL` mode), active foreign keys, and atomic multi-table transactions.
   - Built with SQLAlchemy 2.0 and versioned migrations; ready for zero-downtime PostgreSQL migration via `DATABASE_URL`.
2. **Deterministic Financial Safety Engine:**
   - All monetary figures are stored in integer minor units (e.g. Poisha/Cents) with commercial round-half-up (`ROUND_HALF_UP`) rounding.
   - Pure, unit-tested deterministic calculations for Revenue, COGS, Gross/Net Margins, Cash Flow, Receivables Aging (DSO), Inventory Valuation, Reducing-Balance EMI vs. Flat-Rate comparison, Break-even, and ROI.
   - Zero floating-point contamination; AI guardrails strictly prevent hallucination of numerical totals.
3. **Automatic Document-to-Form Routing Pipeline:**
   - End-to-end ingest: Upload validation (file size, magic bytes, SHA-256 deduplication) -> RapidOCR / Layout Parsing -> Classification (Sales Receipt, Supplier Invoice, Expense Receipt, Payment Receipt, Unknown) -> Mathematical cross-validation -> Dynamic Form Selection.
   - Low-confidence or discrepant extractions are automatically routed to interactive review forms before committing to the financial ledger.
   - Idempotent document posting prevents duplicate transactions on retry.
4. **Reproducible Synthetic Relational Dataset Generator (100,000+ Records):**
   - Generates over **160,000+ connected relational records** across 9 diverse SME industry sectors (Grocery, Clothing, Restaurant, Pharmacy, Electronics, Wholesale, Manufacturing, Service, Online Seller).
   - Configurable random seed for exact reproducibility.
   - Validated referential integrity, financial consistency, and safe idempotent reset.
5. **Synthetic Document Image Tooling & Annotation Schema:**
   - Thermal/POS receipt generator supporting English, Bengali (বাংলা), and mixed bilingual documents.
   - Complete COCO/JSON ground-truth annotation export with text bounding boxes, image quality metrics, and train/val/test splits.
6. **Modular AI Model Registry & Baselines:**
   - Database-backed model registry tracking active model versions, hyperparameters, and evaluation benchmark runs across all core AI tasks.

---

## Quickstart & Setup Instructions

### 1. Prerequisites
- **Python 3.11+**
- Git

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Default configuration runs locally out-of-the-box using `./sme_finance.db`.

### 3. Initialize Database & Migrations
Run the database migration script:
```powershell
python scripts/init_db.py
```
This executes versioned migrations in `src/database/migrations/versions/001_initial_schema.sql` and registers default AI model baselines.

### 4. Run Automated Test Suite
Execute the comprehensive PyTest suite:
```powershell
python -m pytest
```
Output: `17 passed` validating foreign keys, multi-tenant isolation, financial math, document pipeline, and synthetic generation.

### 5. Generate the Synthetic Dataset (100,000+ Records)
To generate the full relational dataset:
```powershell
python scripts/generate_synthetic_data.py --target 100000 --seed 42 --reset
```
*Tip: Generation finishes in ~1.5 seconds and populates over 160,000+ verified connected relational records.*

### 6. Validate the Dataset
Audit referential integrity and financial consistency:
```powershell
python scripts/validate_dataset.py
```
Full audit reports are saved to:
- `storage/synthetic_data/validation_report.json`
- `storage/synthetic_data/validation_report.md`

### 7. Generate Sample Synthetic Document Images
To generate 20 sample bilingual receipt images and metadata manifest:
```powershell
python scripts/generate_synthetic_images.py --count 20
```
Output images and manifest are saved to `storage/synthetic_images/`.

### 8. Start the Application & Web Portal
Start the FastAPI server:
```powershell
uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
- **Web Application Portal:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (or `/landing`)
- **Executive Dashboard:** [http://127.0.0.1:8000/app/dashboard](http://127.0.0.1:8000/app/dashboard)
- **1-Click Demo Personas (Owner, Accountant, Cashier, Auditor):** [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login)
- **Interactive Swagger API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **API Health Telemetry:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### Implemented Web Portal Modules (Phase 5):
- **Landing Page (`/landing`):** Modern high-converting UI with live metrics ticker, interactive DSCR sandbox, feature grid, and preloader animations.
- **Authentication & Onboarding (`/login`, `/register`):** Glassmorphic screens with 1-click persona switcher (Owner, Accountant, Cashier, Auditor).
- **Executive Dashboard (`/app/dashboard`):** 30-day revenue vs expense stream chart (Chart.js), net profit, cash runway, and live transactions stream.
- **Financial Ledger & P&L (`/app/finance`):** P&L statements, verified sales & expense ledgers, date range filters, minor-unit formatting, and statutory CSV exports.
- **AI Cash-Flow Forecasting (`/app/forecast`):** Multi-horizon forecasting (7D, 14D, 30D, 60D, 90D), 95% confidence intervals, and automated liquidity runway estimation.
- **Document OCR Hub (`/app/documents`):** Drag-and-drop file upload, magic byte verification, extracted line items reconciliation, and human review approval gateway before posting to general ledger.
- **SME Loans & DSCR Underwriting (`/app/loans`):** Debt Service Coverage Ratio calculator, reducing-balance amortized EMI schedules, and institutional bank comparison matrix (BRAC Bank, City Tara, EBL Shurjo).
- **Inventory & Aging (`/app/inventory`):** Stock valuation, low-stock reorder warnings, and accounts receivable aging buckets (0-30, 31-60, 61-90, 90+ days).
- **Autonomous Financial AI Copilot (`/app/copilot`):** Conversational AI participant grounded in verified SQLite records for debt simulation, tax advisory, and cash diagnosis.
- **Security Audit & Integrity (`/app/audit`):** Tamper-evident audit trail, cryptographic HMAC signature verification, and active model registry benchmarks.
- **Settings & Organization (`/app/settings`):** Multi-shop branch switcher, statutory tax profile, 100-language selector, and local SQLite engine telemetry.

---

## Project Structure

```
F:\china project\
├── .env.example                     # Documented configuration template
├── .gitignore                       # Git exclusion rules
├── README.md                        # Project documentation & run guide
├── ARCHITECTURE.md                  # System architecture & Mermaid ER diagrams
├── API_READINESS_REPORT.md          # Phase 2 API readiness report
├── API_SECURITY_VERIFICATION_REPORT.md # Phase 2.1 API security audit report
├── PHASE_GATE_REPORT.md             # Phase 1 database & model audit gate
├── DATABASE_READINESS_REPORT.md     # Relational database audit report
├── MODEL_READINESS_REPORT.md        # AI model benchmark validation report
├── DATA_QUALITY_REPORT.md           # Synthetic data quality audit
├── FINANCIAL_VALIDATION_REPORT.md   # Deterministic financial math verification
├── pyproject.toml                   # Project metadata & pytest configuration
├── requirements.txt                 # Project dependencies
├── sme_finance.db                   # Local SQLite database (WAL mode, 160,090 rows)
├── assets/                          # Animated SVG preloaders (preserved)
├── src/
│   ├── config.py                    # Typed environment configuration
│   ├── core/                        # Money (integer minor units), security, exceptions
│   ├── database/                    # Connection, models (43 tables), migrations, repositories
│   ├── finance/                     # Deterministic financial calculation engine
│   ├── documents/                   # Document validation, OCR, classification, routing, posting
│   ├── ai/                          # Model registry, forecasting, loan risk, segmentation, guardrails
│   ├── data/                        # Synthetic data generator, validator, image tooling
│   ├── api/                         # FastAPI routes (auth, business, documents, finance, datasets, models, i18n, audit)
│   └── web/                         # Web portal layer (Jinja2 templates, CSS tokens, JS client, images)
│       ├── router.py                # Web page route controller
│       ├── static/css/theme.css     # Glassmorphic dark theme design tokens & animations
│       ├── static/js/app.js         # Client-side API bridge, toast alerts, currency formatting
│       ├── static/images/           # Favicons, background assets, preloader SVGs
│       └── templates/               # HTML templates (landing, auth, app portal layout & modules)
├── storage/                         # Local filesystem storage
│   ├── documents/                   # Uploaded document scans and receipts
│   ├── synthetic_data/              # Dataset validation reports
│   └── synthetic_images/            # Sample synthetic document images & manifests
├── tests/                           # 107 automated unit, security and web tests (100% pass)
└── scripts/                         # CLI utility runners (init_db, generate, validate, images)
```

---

## Security & Multi-Tenant Isolation Notice
All records belong strictly to a `business_id` and `shop_id`. Cross-shop access is enforced and verified at the database query and repository layer, preventing unauthorized visibility or cross-contamination of financial records. Any unauthorized tenant access raises `ShopAccessDeniedError` and returns `403 Forbidden` with clean, stack-trace-free error details. Client identity headers are ignored in favor of signed HMAC session tokens.
