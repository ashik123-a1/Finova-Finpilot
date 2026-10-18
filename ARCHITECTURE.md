# SME Finance Copilot — System Architecture & Database Design

This document details the database schema, relational entities, multi-tenant isolation, financial precision standards, document pipeline, and AI foundation for the SME Finance Copilot.

---

## 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Client & Interface Layer"]
        WebUI["Web / POS / Mobile Dashboard"]
        DocUpload["Document / Receipt Capture"]
        AIAdvisor["Natural Language Copilot Chat"]
    end

    subgraph APILayer["FastAPI Gateway & Route Endpoints"]
        AuthRouter["Auth Router (JWT / Session)"]
        DocRouter["Document Processing Router"]
        FinanceRouter["Deterministic Finance Router"]
        DatasetRouter["Dataset & Validation Router"]
        ModelRouter["AI Model Registry Router"]
    end

    subgraph CoreServices["Domain Engine & Business Logic"]
        ShopIsolation["Multi-Tenant Shop Isolation Guard"]
        FinCalc["Deterministic Financial Calculator (Integer Minor Units)"]
        DocPipeline["Document Pipeline (RapidOCR + Layout Routing)"]
        AiGuardrail["AI Assistant Mathematical Guardrail"]
        SyntheticGen["Synthetic Data Generator (100k+ Relational Engine)"]
    end

    subgraph DataStorage["Data & Storage Infrastructure"]
        SQLiteDB[("SQLite Local-First Database (WAL Mode, FKs Enabled)")]
        DocStore["Local Filesystem Document Storage (storage/documents)"]
        ModelStore["Model Registry & Evaluation Store"]
    end

    DocUpload --> DocRouter
    WebUI --> FinanceRouter
    AIAdvisor --> AiGuardrail

    DocRouter --> DocPipeline
    FinanceRouter --> FinCalc
    AiGuardrail --> FinCalc
    DocPipeline --> FinCalc

    DocPipeline --> ShopIsolation
    FinCalc --> ShopIsolation
    SyntheticGen --> ShopIsolation

    ShopIsolation --> SQLiteDB
    DocPipeline --> DocStore
    ModelRouter --> ModelStore
```

---

## 2. Database Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    businesses ||--o{ shops : "operates"
    businesses ||--o{ business_memberships : "has"
    users ||--o{ business_memberships : "belongs_to"
    shops ||--o{ business_memberships : "assigned_to"

    shops ||--o{ customers : "serves"
    shops ||--o{ suppliers : "purchases_from"
    shops ||--o{ products : "inventories"

    shops ||--o{ sales : "records"
    customers ||--o{ sales : "receives"
    sales ||--|{ sale_items : "contains"
    products ||--o{ sale_items : "sold_as"

    shops ||--o{ purchases : "orders"
    suppliers ||--o{ purchases : "fulfills"
    purchases ||--|{ purchase_items : "contains"
    products ||--o{ purchase_items : "received_as"

    shops ||--o{ expenses : "incurs"
    shops ||--o{ payments : "logs"
    shops ||--o{ receivables : "tracks"
    shops ||--o{ inventory_movements : "audits"
    products ||--o{ inventory_movements : "tracks"
    shops ||--o{ cash_movements : "balances"

    shops ||--o{ documents : "uploads"
    documents ||--o| document_classifications : "classified_as"
    documents ||--o| document_extractions : "extracts"
    documents ||--o| document_reviews : "audits"

    demo_banks ||--|{ loan_products : "offers"
    loan_products ||--o{ loan_rules : "enforces"
    shops ||--o{ loan_scenarios : "simulates"
    loan_products ||--o{ loan_scenarios : "configured_with"

    model_versions ||--o{ evaluation_runs : "evaluated_by"
    datasets ||--o{ evaluation_runs : "benchmarked_on"
```

---

## 3. Financial Precision & Minor-Unit Representation

To completely prevent binary IEEE 754 floating-point errors (e.g. `0.1 + 0.2 != 0.3`), all ledger and database balances are stored in **integer minor units** (`BigInteger`):

| Currency | Major Unit | Minor Unit | Minor Multiplier | Example Major | Example Stored Minor Unit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BDT** | Bangladeshi Taka (৳) | Poisha | 100 | `৳ 1,250.50` | `125050` |
| **USD** | US Dollar ($) | Cents | 100 | `$ 45.99` | `4599` |
| **EUR** | Euro (€) | Cents | 100 | `€ 100.00` | `10000` |

### Rounding Policy
All conversions, taxes, and interest accruals apply standard Banker's / Commercial **Round Half Up** (`ROUND_HALF_UP`) via Python's `decimal.Decimal` module before casting to `int`.

---

## 4. Multi-Tenant Shop Isolation Strategy

1. **Authorization Verification:** Every business transaction must reference both `business_id` and `shop_id`.
2. **Access Control:** `enforce_shop_isolation(user_id, target_shop_id, memberships)` verifies that the acting user has an active membership associated with `target_shop_id` or an enterprise-level role before any query or mutation executes.
3. **Cross-Shop Leak Prevention:**
   - Products from Shop A cannot be deducted in a Sale belonging to Shop B.
   - Customers and Suppliers are partitioned by `shop_id`.
   - Automated unit tests (`tests/test_isolation.py`) prove access denial.

---

## 5. Document-to-Form Processing Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as SME Shop Owner / Staff
    participant API as Document Router (/api/documents/upload)
    participant Validator as File Validator & Deduplicator
    participant OCR as RapidOCR Engine
    participant Classifier as Document Classifier
    participant Extractor as Structured Extractor & Math Auditor
    participant Poster as Document Posting Service
    participant DB as SQLite Financial Ledger

    User->>API: Upload photo / scan of receipt
    API->>Validator: Validate file type, size, magic bytes & compute SHA-256
    alt File is duplicate SHA-256
        Validator-->>API: Return existing document (Flagged as duplicate)
    else File is valid & new
        Validator->>API: File saved to storage/documents/...
    end

    API->>OCR: Extract raw text & bounding boxes
    API->>Classifier: Classify doc type (Sales, Purchase, Expense, Payment, Unknown)
    API->>Extractor: Extract invoice #, date, items, subtotal, tax, total
    Extractor->>Extractor: Verify sum(line_items) == subtotal and subtotal + tax - discount == total

    alt Low confidence (<0.85) OR math discrepancy OR Unknown
        API-->>User: Route to interactive review form with flagged warnings
        User->>API: Confirm or adjust extracted fields (/api/documents/confirm-post)
    else High confidence (>=0.85) & Valid
        API-->>User: Present prefilled form for one-click confirmation
        User->>API: Approve (/api/documents/confirm-post)
    end

    API->>Poster: Commit confirmed figures
    Poster->>DB: Atomic transaction (Sale/Purchase/Expense + Inventory + Payments)
    DB-->>Poster: Transaction committed
    Poster-->>User: Confirmation with ledger record ID
```

---

## 6. Migration to Production Cloud / PostgreSQL

The repository design abstracts database access via SQLAlchemy repositories:
- To switch to PostgreSQL: set `DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname` in `.env`.
- To switch document storage to S3/GCS: swap `save_uploaded_file` with an S3 client implementation without modifying domain or financial calculation logic.
