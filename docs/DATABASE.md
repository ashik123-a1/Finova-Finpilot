# FinTechathon 2026: SME Finance Copilot — Database Architecture & Migrations

**Document Version:** 1.0.0 (Master Release)  
**Database Engine:** SQLite 3.35+ with Write-Ahead Logging (WAL Mode)  
**ORM:** SQLAlchemy 2.0 (Declarative Base, Strict Foreign Keys, Typed Columns)  
**Total Tables:** 50 normalized relational entities  
**Verified Table Record Count:** 163,054 records preserved

---

## 1. Engine Configuration & Durability Guarantees

The database operates under strict production pragmas applied on every connection:
```sql
PRAGMA journal_mode = WAL;         -- High-concurrency read/write transactions
PRAGMA foreign_keys = ON;          -- Strict relational constraint enforcement
PRAGMA synchronous = NORMAL;       -- Safe crash durability without IO bottleneck
PRAGMA busy_timeout = 5000;        -- Prevents lock contention errors
PRAGMA cache_size = -64000;        -- 64 MB memory cache for analytics acceleration
```

### Zero Floating-Point Precision
To prevent rounding errors and financial discrepancies:
* All monetary columns are stored as 64-bit Signed Integers (`INTEGER`) representing minor units (cents, poisha, fen).
* Example: `$1,525,400.00` is stored as `152540000`.
* Calculations are executed strictly with integer arithmetic.

---

## 2. Relational Schema Hierarchy & Entity Domains

```
                               ┌──────────────┐
                               │    users     │
                               └──────┬───────┘
                                      │ 1:N
                                      ▼
                        ┌───────────────────────────┐
                        │   business_memberships    │
                        └─────────────┬─────────────┘
                                      │ N:1
                                      ▼
                               ┌──────────────┐
                               │  businesses  │
                               └──────┬───────┘
                                      │ 1:N
                                      ▼
                               ┌──────────────┐
                               │    shops     │
                               └──────┬───────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │ 1:N                       │ 1:N                       │ 1:N
          ▼                           ▼                           ▼
   ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
   │    sales     │            │   expenses   │            │   products   │
   └──────┬───────┘            └──────────────┘            └──────┬───────┘
          │ 1:N                                                   │ 1:N
          ▼                                                       ▼
   ┌──────────────┐                                        ┌──────────────┐
   │  sale_items  │                                        │  inventory_  │
   └──────────────┘                                        │  movements   │
                                                           └──────────────┘
```

### Table Domains Breakdown:
1. **Identity & RBAC:** `users`, `roles`, `permissions`, `role_permissions`, `business_memberships`, `workspace_invitations`, `password_reset_tokens`.
2. **Enterprise Workspaces:** `businesses`, `shops`.
3. **General Ledger & Cash Flow:** `sales`, `sale_items`, `purchases`, `purchase_items`, `expenses`, `payments`, `receivables`, `cash_movements`.
4. **Commercial Banking & Credit Underwriting:** `demo_banks`, `loan_products`, `loan_rules`, `loan_scenarios`, `loan_applications`.
5. **Smart Document Pipeline:** `documents`, `document_pages`, `document_classifications`, `document_extractions`, `document_reviews`, `document_processing_jobs`.
6. **CRM & Merchandising:** `customers`, `suppliers`, `customer_communications`, `discount_campaigns`.
7. **Inventory & Warehouse:** `products`, `purchase_orders`, `purchase_order_items`, `inventory_movements`, `stock_adjustments`.
8. **Compliance, Audit & AI:** `audit_logs`, `document_chunks`, `notifications`, `report_executions`, `forecasts`, `recommendations`, `model_versions`.

---

## 3. Forward-Only Migration History

Migrations are executed via `src/database/migrations/runner.py`, tracked in `schema_migrations`:

| Migration File | Version | Scope & Relational Changes |
| :--- | :---: | :--- |
| `001_initial_schema.sql` | 1 | Core relational tables (users, businesses, shops, sales, expenses, inventory) |
| `002_seed_roles_and_permissions.sql`| 2 | Initial RBAC matrix (7 roles, 22 permissions, 80 role-permission bindings) |
| `003_document_chunks_rag.sql` | 3 | RAG vector embedding chunks table with tenant business/shop bindings |
| `004_workspace_invitations_and_recovery.sql` | 4 | Enterprise workspace invitations and cryptographically signed password resets |
| `005_notification_enhancements.sql` | 5 | In-app user notifications with read status and event classifications |
| `006_crm_inventory_campaign_enhancements.sql` | 6 | Customer RFM tiers, discount campaigns, and purchase order tracking |
| `007_user_language_preference.sql` | 7 | Dynamic user-profile localization preferences (`preferred_language`) |
| `008_report_executions.sql` | 8 | Tamper-evident audit log for generated CSV & PDF financial statement reports |

---

## 4. Disaster Recovery & Backup Protocols

### WAL-Safe Backup Strategy
Copying an active SQLite database file directly while in WAL mode can produce a corrupt snapshot if transactions are actively writing to the `-wal` file. The application uses `DatabaseBackupService` (`sqlite3.Connection.backup()`), which executes an atomic page-by-page online backup that cleanly flushes the write-ahead log.

### Create Backup Command
```powershell
python -c "from src.database.backup_service import DatabaseBackupService; print(DatabaseBackupService.create_backup())"
```
*Creates a timestamped snapshot in `var/backups/sme_backup_<timestamp>.db` accompanied by `manifest_<timestamp>.json` containing SHA-256 checksums and exact table row counts.*

### Isolated Test Restore Command
```powershell
python -c "from src.database.backup_service import DatabaseBackupService; print(DatabaseBackupService.verify_and_restore_isolated('var/backups/sme_backup_20261020_105146.db'))"
```
*Restores the snapshot into an isolated sandbox database, performs `PRAGMA integrity_check;`, and verifies table row count equivalence without touching the active production database.*
