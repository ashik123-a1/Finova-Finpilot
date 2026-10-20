# FinTechathon 2026: SME Finance Copilot — Financial Reports & Backup Operations

**Document Version:** 1.0.0 (Master Release)  
**Supported Formats:** CSV (Tabular, formula-sanitized), PDF (Executive formatted)  
**Backup Engine:** SQLite Online Backup API with SHA-256 Checksums

---

## 1. Authorized Financial Reporting Subsystem

The application generates verified financial statements directly from underlying database records.

### Supported Report Categories
1. **Income Statement (Profit & Loss):** Operating revenue, cost of goods sold, gross margin, operating expenses by category, net operating profit/loss.
2. **Balance Sheet:** Current assets (cash, receivables, inventory holding valuation), fixed assets, liabilities, and merchant equity.
3. **Trial Balance:** Debit and credit reconciliation across all ledger accounts.
4. **Accounts Receivable Aging:** Unpaid customer invoices categorized into Current, 1–30, 31–60, and 60+ days overdue.
5. **Inventory Valuation & Movement Audit:** SKU stock balances, FIFO asset values, and historical movements.
6. **Tax & VAT Mushak 6.3 Summary:** Input/output tax schedules with statutory tax identification numbers.

### CSV Formula Injection (DDE) Defense
When generating CSV files, the exporter inspects every cell string. Any cell starting with `=, +, -, @, \t, \r` is prefixed with a single quote (`'`), neutralizing spreadsheet formula execution.

---

## 2. WAL-Safe Database Backup Operations

### Creating a System Backup
To create a verified snapshot:
```powershell
python -c "from src.database.backup_service import DatabaseBackupService; print(DatabaseBackupService.create_backup())"
```
* **Storage Location:** `var/backups/sme_backup_<timestamp>.db`
* **Integrity Manifest:** `var/backups/manifest_<timestamp>.json`
* **Recorded Metadata:** Timestamp, creator ID, file size, SHA-256 hash, SQLite integrity check status (`ok`), and table-by-table record counts.

### Performing an Isolated Sandbox Restore
To test disaster recovery without overwriting the live database:
```powershell
python -c "from src.database.backup_service import DatabaseBackupService; print(DatabaseBackupService.verify_and_restore_isolated('var/backups/<backup_file>.db'))"
```
*Restores into `sme_test_restore.db`, verifies that table row counts match the manifest, and confirms zero data corruption.*
