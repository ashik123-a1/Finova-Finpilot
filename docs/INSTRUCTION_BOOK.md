# FinTechathon 2026: SME Finance Copilot — Local Installation & Instruction Book

**Competition Track:** Topic E — SME Finance Copilot  
**Theme:** AI as an Autonomous Financial Participant  
**Target Environment:** Local-First Architecture (100% Offline Edge Capable)  
**Document Version:** 1.0.0 (Master Evaluation Edition)

---

## 1. System Overview & Evaluation Quickstart

SME Finance Copilot is an enterprise-grade financial operating system designed for emerging market small-and-medium enterprises. It operates 100% locally with zero mandatory cloud dependencies, providing:
* **Autonomous Financial Accounting:** Zero float-loss ledger tracking across multi-shop retail operations.
* **Credit Underwriting & DSCR Risk Engine:** Amortization modeling and instant loan readiness packaging for Tier-1 SME banks.
* **AI Copilot Intelligence:** Grounded financial analytics, 5-stage loss recovery modeling, and margin guardrail defenses.
* **Autonomous Multilingual Voice HUD:** Voice transactions with consequential action authorization barriers.
* **Tamper-Evident Audit Trails:** Cryptographic hash chaining for regulatory compliance.

---

## 2. System Prerequisites

| Component | Minimum Version | Recommended Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Operating System** | Windows 10 / Ubuntu 20.04 / macOS 12 | Windows 11 / Ubuntu 22.04 LTS | Cross-platform host runtime |
| **Python** | Python 3.11.0 | Python 3.11.9 | Core application runtime & AI pipeline |
| **Database Engine** | SQLite 3.35+ (with WAL mode support) | SQLite 3.42+ (Bundled with Python 3.11) | Local-first relational database |
| **Web Browser** | Chrome 110+ / Edge 110+ / Firefox 115+ | Google Chrome or Microsoft Edge | Web Speech API, Glassmorphism UI |
| **Git** | Git 2.30+ | Git 2.40+ | Version control & repository cloning |
| **Optional LLM** | OpenAI API / Local Ollama (Optional) | Deterministic fallback works 100% offline | Advanced conversational synthesis |

> [!NOTE]
> Node.js, npm, and external database servers (e.g. PostgreSQL, Redis) are **NOT required**. The frontend uses high-performance server-rendered HTML with Tailwind CSS and Lucide icons bundled locally, ensuring instantaneous local execution.

---

## 3. Windows 10/11 Step-by-Step Installation (PowerShell)

Open PowerShell as an Administrator or standard user and execute the following sequential commands:

### Step 1: Open the Project Directory
```powershell
cd "F:\china project"
```

### Step 2: Create and Activate Python Virtual Environment
```powershell
# Create isolated Python 3.11 virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

### Step 3: Install Required Dependencies
```powershell
# Upgrade pip and install pinned production dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
```powershell
# Copy the safe template if .env does not already exist
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}
```

### Step 5: Verify Database Migrations & Integrity
```powershell
# Verify that all 8 schema migrations are current and check database health
python -c "from src.database.connection import init_db; init_db()"
```

### Step 6: Execute Automated Test Suite (Verification Gate)
```powershell
# Run the complete test suite (220 tests across 21 test suites)
python -m pytest
```
*Expected output: `220 passed in ~18 seconds (100% pass rate)`.*

### Step 7: Launch the Application Server
```powershell
# Start Uvicorn ASGI production server on port 8050
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8050
```

### Step 8: Open in Browser
Open your browser and navigate to:  
👉 **`http://127.0.0.1:8050`**

---

## 4. Linux / macOS / GitHub Codespaces Installation

For Debian/Ubuntu, macOS, or cloud containers:

```bash
# 1. Clone repository (or enter directory)
cd "sme-finance-copilot"

# 2. Set up virtual environment
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

---

## 5. Pre-Configured Demo Personas & Credentials

For judge convenience, 7 canonical demo accounts are pre-seeded in the local database. You can log in via **1-Click Demo Login** on the login page (`/login`) or use the following credentials:

| Persona | Role Code | Email | Password | Primary Scope & Access |
| :--- | :--- | :--- | :--- | :--- |
| **Business Owner** | `owner` | `demo_owner@smefinance.local` | `DemoPass123!` | Full enterprise access, shop switcher, loss recovery, loan packet |
| **Store Manager** | `manager` | `demo_manager@smefinance.local` | `DemoPass123!` | Daily operations, inventory reorders, customer management |
| **Senior Accountant**| `accountant`| `demo_accountant@smefinance.local` | `DemoPass123!` | General ledger, OCR document reviews, CSV/PDF reports export |
| **Sales Executive** | `sales` | `demo_sales@smefinance.local` | `DemoPass123!` | POS sales, customer RFM tiers, WhatsApp reminder drafting |
| **Inventory Officer**| `inventory` | `demo_inventory@smefinance.local` | `DemoPass123!` | Stock movements, warehouse valuation, purchase order drafting |
| **External Auditor** | `auditor` | `demo_auditor@smefinance.local` | `DemoPass123!` | Read-only compliance audit trails, SHA-256 hash inspection |
| **Super Admin** | `super_admin`| `super_admin@smefinance.local` | `DemoPass123!` | Platform Admin Portal (`/app/admin`), multi-tenant oversight |

---

## 6. Recommended 10-Step Evaluation Workflow

To experience the full capabilities of SME Finance Copilot in 10 minutes:

1. **Landing Page & Execution Sandbox (`/`):**
   - View the interactive execution sandbox displaying real API request/response payloads, OCR document pipeline benchmarks, and voice agent traces.
2. **1-Click Demo Login (`/login`):**
   - Click the **Business Owner** card to authenticate instantly.
3. **Executive Dashboard (`/app/dashboard`):**
   - Observe live financial KPIs for **Bismillah Store** (`$1,525,400.00` revenue, `$4,868,176.68` expenses, `-$3,342,776.68` loss).
   - Check the daily transaction trend and cash runway forecast.
4. **Financial AI Copilot (`/app/copilot`):**
   - Ask the exact failure-mode question from the audit: *"I am in loss how can I recover?"*.
   - Observe the 5-part turnaround plan with quantified scenarios (`+$243,408.83` via 5% cost reduction, `+$152,540.00` via 10% sales lift).
   - Switch language to Bengali (`বাংলা`) or Simplified Chinese (`简体中文`) and observe native localized advice with enterprise currency preserved (`USD`).
5. **Loan Calculator & Credit Underwriting (`/app/loans`):**
   - Test dynamic recalculation of monthly EMI and DSCR.
   - Match loan products across 5 partner commercial banks.
   - Click **"Generate Underwriting Packet"** to download the official PDF.
6. **Smart OCR Document Processing (`/app/documents`):**
   - Inspect pre-uploaded commercial invoices (`Mushak 6.3`).
   - Review the staged line items and verify the human-in-the-loop approval barrier before ledger posting.
7. **CRM & Overdue Receivables Dunning (`/app/customers`):**
   - Inspect the 44 unpaid customer invoices representing `$89,382.50` in uncollected cash.
   - Click **"Draft WhatsApp Reminder"** for an overdue customer to inspect the automated dunning message.
8. **Inventory & Low Stock Alerts (`/app/inventory`):**
   - Review 41 SKUs valued at `$2,448,570.00`.
   - Inspect low-stock alert thresholds and automated purchase-order generation.
9. **Financial Reports & Audit Backups (`/app/reports`):**
   - Export an Income Statement to CSV (with formula-injection mitigation) and PDF.
   - Create an instant WAL-safe database backup in `var/backups/`.
10. **Platform Admin Portal (`/app/admin`):**
    - Log in as `super_admin` to view cross-tenant health metrics and model registry status.

---

## 7. Database Administration & Safety

### Database Engine & Storage
* **Engine:** SQLite 3 with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`).
* **Active File:** `sme_finance.db` (root directory).
* **Backup Directory:** `var/backups/` (strictly excluded from Git).

### Creating a Safe Database Backup
To create a verified backup with SHA-256 manifest:
```powershell
python -c "from src.database.backup_service import DatabaseBackupService; print(DatabaseBackupService.create_backup())"
```

### Performing an Isolated Test Restore
To verify disaster recovery without touching the live production database:
```powershell
python -c "from src.database.backup_service import DatabaseBackupService; print(DatabaseBackupService.verify_and_restore_isolated('var/backups/<backup_filename>.db'))"
```

---

## 8. Troubleshooting & Common Issues

### Issue 1: Port 8050 Already in Use
* **Symptom:** `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8050)`
* **Fix:** Kill the existing uvicorn process or specify another port:
  ```powershell
  # Windows PowerShell: Kill process using port 8050
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8050).OwningProcess | Stop-Process -Force
  
  # Or start on an alternate port:
  python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8055
  ```

### Issue 2: Browser Voice Input Unavailable
* **Symptom:** Microphone button does not start recording.
* **Fix:** Ensure you are using Google Chrome or Microsoft Edge. Web Speech API requires user permission; click "Allow" when the browser prompts for microphone access. If running over network IP instead of `localhost`, Chrome requires HTTPS for speech recognition.

### Issue 3: Missing Dependencies or ModuleNotFoundError
* **Symptom:** `ModuleNotFoundError: No module named 'reportlab'`
* **Fix:** Ensure your virtual environment is activated and re-run:
  ```powershell
  pip install -r requirements.txt
  ```

---

## 9. Test Case Catalogue Cross-Reference

A complete, formal catalogue of **50 Numbered Test Cases (TC-01 through TC-50)** is documented in:  
📄 [`docs/TESTING.md`](file:///F:/china%20project/docs/TESTING.md)

All 220 automated unit, integration, and security tests can be verified at any time with:
```powershell
python -m pytest
```
