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

### 8. Start the Local API Server
Start the FastAPI server:
```powershell
uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- API Health Status: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- API Root: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### Implemented API Workflows (Phase 2):
- **Health:** `GET /health`, `GET /api/health`, `GET /`
- **Business & Multi-Tenant:** `GET /api/business/list`, `GET /api/business/{business_id}/shops`, `GET /api/business/shops/{shop_id}`
- **Finance Dashboard & Ledger:** `GET /api/finance/summary`, `GET /api/finance/sales`, `GET /api/finance/expenses`, `GET /api/finance/profit-loss`, `GET /api/finance/cash-flow`
- **Forecasting & Loan Intelligence:** `POST /api/finance/forecast`, `GET /api/finance/forecast`, `POST /api/finance/loan-risk-assessment`, `GET /api/finance/loan-products`, `POST /api/finance/loan-comparison`, `POST /api/finance/break-even`
- **Inventory & Receivables:** `GET /api/finance/inventory-summary`, `GET /api/finance/receivables-summary`
- **Document Processing Pipeline:** `POST /api/documents/upload`, `GET /api/documents/{document_id}`, `POST /api/documents/confirm-post`, `GET /api/documents/list`
- **Model Registry & Evaluations:** `GET /api/models/active`, `GET /api/models/evaluations`, `GET /api/models/evaluations/summary`
- **Security & Audit Logs:** `GET /api/audit/logs`
- **Multilingual i18n:** `GET /api/i18n/languages`, `GET /api/i18n/countries`, `GET /api/i18n/translations`, `GET /api/i18n/format/currency`

---

## Project Structure

```
F:\china project\
├── .env.example                     # Documented configuration template
├── .gitignore                       # Git exclusion rules
├── README.md                        # Project documentation & run guide
├── ARCHITECTURE.md                  # System architecture & Mermaid ER diagrams
├── API_READINESS_REPORT.md          # Phase 2 API readiness report
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
│   └── api/                         # FastAPI routes (auth, business, documents, finance, datasets, models, i18n, audit)
├── storage/                         # Local filesystem storage
│   ├── documents/                   # Uploaded document scans and receipts
│   ├── synthetic_data/              # Dataset validation reports
│   └── synthetic_images/            # Sample synthetic document images & manifests
├── tests/                           # 81 automated unit and integration tests (100% pass)
└── scripts/                         # CLI utility runners (init_db, generate, validate, images)
```

---

## Security & Multi-Tenant Isolation Notice
All records belong strictly to a `business_id` and `shop_id`. Cross-shop access is enforced and verified at the database query and repository layer, preventing unauthorized visibility or cross-contamination of financial records. Any unauthorized tenant access raises `ShopAccessDeniedError` and returns `403 Forbidden` with clean, stack-trace-free error details.
