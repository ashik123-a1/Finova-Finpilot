# FinTechathon 2026: SME Finance Copilot — Complete API Reference

**Base URL:** `http://127.0.0.1:8050/api`  
**Authentication Scheme:** `Authorization: Bearer <HMAC_SESSION_TOKEN>` or cookie `sme_auth_token`  
**Data Format:** `application/json` (Standard REST) & `multipart/form-data` (Document Uploads)

---

## 1. Authentication Router (`/api/auth`)

### `POST /api/auth/register`
* **Description:** Register a new merchant user and enterprise business.
* **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "Rahim Uddin",
    "business_name": "Rahim Enterprise",
    "currency": "BDT",
    "country_code": "BD"
  }
  ```
* **Response:** HTTP 201 Created with JWT/session token and user identity.

### `POST /api/auth/login`
* **Description:** Standard username/password login.
* **Request Body:** `{"email": "...", "password": "..."}`
* **Response:** HTTP 200 OK with `access_token` and Sets `sme_auth_token` cookie.

### `POST /api/auth/demo-login`
* **Description:** 1-Click login for the 7 canonical competition demo personas.
* **Request Body:** `{"persona": "owner | manager | accountant | sales | inventory | auditor | super_admin"}`
* **Response:** HTTP 200 OK with session credentials and role-specific redirect URL.

### `GET /api/auth/me`
* **Description:** Retrieves current authenticated session user, role, and authorized business/shop list.
* **Headers:** `Authorization: Bearer <token>`
* **Response:** HTTP 200 with user profile and business memberships array.

---

## 2. Business & Shop Router (`/api/business`)

### `POST /api/business/onboard`
* **Description:** Creates an enterprise workspace with subordinate retail shops.
* **Request Body:** `{"name": "...", "tax_id": "...", "currency": "USD", "shops": [{"name": "..."}]}`

### `GET /api/business/shops`
* **Description:** Lists all active shops belonging to the authenticated merchant's business.

### `POST /api/business/switch-shop`
* **Description:** Switches the active operational shop context and updates session cookie.

---

## 3. General Ledger & Finance Router (`/api/finance`)

### `GET /api/finance/summary`
* **Description:** Live database-backed financial summary (Revenue, Expenses, Profit/Loss, Margin, Runway).
* **Parameters:** `business_id` (optional), `shop_id` (optional), `start_date`, `end_date`.
* **Response (Sample):**
  ```json
  {
    "total_revenue": "1,525,400.00 USD",
    "total_expenses": "4,868,176.68 USD",
    "net_profit": "-3,342,776.68 USD",
    "is_loss": true,
    "currency": "USD",
    "sales_count": 816,
    "expense_count": 354,
    "period_days": 182
  }
  ```

### `GET /api/finance/sales` & `POST /api/finance/sales`
* **Description:** Query paginated sales transactions or record a new sales invoice.

### `GET /api/finance/expenses` & `POST /api/finance/expenses`
* **Description:** Query paginated expense ledger entries or record operational expenses.

### `GET /api/finance/cash-flow/forecast`
* **Description:** Time-series cash runway projection and daily net cash burn rate.

---

## 4. Smart Document OCR Router (`/api/documents`)

### `POST /api/documents/upload`
* **Description:** Uploads an invoice or receipt image/PDF with MIME-type and path traversal validation.
* **Form Data:** `file: <binary>`, `shop_id: 28`.
* **Response:** HTTP 201 Created with document metadata.

### `POST /api/documents/{id}/extract`
* **Description:** Executes text OCR extraction and parses vendor, invoice number, tax ID, and line items into draft status (`requires_review`).

### `POST /api/documents/{id}/post-ledger`
* **Description:** Human-in-the-loop approval step that atomically posts reviewed document line items into production ledger tables (`sales` or `expenses`).

---

## 5. CRM & Receivables Router (`/api/crm`)

### `GET /api/crm/customers` & `POST /api/crm/customers`
* **Description:** List customer directory with RFM segmentation tiers or register a new client profile.

### `GET /api/crm/receivables`
* **Description:** Detailed accounts receivable aging breakdown (Current, 1–30, 31–60, 60+ days past due).

### `POST /api/crm/reminders/draft`
* **Description:** Drafts a personalized WhatsApp / SMS collection message for overdue invoices.

---

## 6. Inventory & Warehouse Router (`/api/inventory`)

### `GET /api/inventory/items` & `POST /api/inventory/items`
* **Description:** Query SKU catalog with stock counts and asset valuation, or create new inventory items.

### `GET /api/inventory/reorder-suggestions`
* **Description:** Identifies SKUs where `current_stock <= min_stock_alert` and calculates restock quantity.

### `POST /api/inventory/purchase-orders`
* **Description:** Generates automated purchase-order drafts for replenishment.

---

## 7. Commercial Loans & Underwriting Router (`/api/loans`)

### `POST /api/loans/underwrite`
* **Description:** Evaluates loan eligibility against banking DSCR benchmark (1.25x minimum).
* **Request Body:**
  ```json
  {
    "principal": 500000,
    "annual_interest_rate": 9.0,
    "tenure_months": 24,
    "monthly_net_income": 35000
  }
  ```
* **Response:** EMI, total interest, DSCR ratio, and underwriting verdict.

### `GET /api/loans/packet/download`
* **Description:** Generates and streams official Credit Underwriting Packet PDF with cryptographic verification hash.

---

## 8. AI Copilot & Voice Subsystem (`/api/models`)

### `POST /api/models/copilot/query`
* **Description:** RAG-grounded Financial AI Copilot. Classifies 11 financial intents, extracts live database analytics, and generates 5-stage turnaround advice.
* **Request Body:** `{"query": "I am in loss how can I recover?", "business_id": 19, "shop_id": 28}`
* **Response:**
  ```json
  {
    "answer": "### 1. Current Financial Position...",
    "security_alert": false,
    "citations": [],
    "has_evidence": false,
    "verified_metrics": { ... },
    "generation_mode": "deterministic_rule_based"
  }
  ```

### `POST /api/models/voice/process`
* **Description:** Multilingual voice command processor with two-step consequential action confirmation barrier.

---

## 9. Reports & Backups Router (`/api/reports`)

### `POST /api/reports/generate`
* **Description:** Generates Income Statement, Balance Sheet, or Trial Balance in CSV or PDF.
* **Request Body:** `{"report_type": "income_statement", "format": "pdf | csv", "shop_id": 28}`

### `GET /api/reports/{id}/download`
* **Description:** Secure download of generated financial statement file.

---

## 10. Platform Admin Portal (`/api/admin`)

### `GET /api/admin/overview`
* **Description:** High-level platform health, cross-tenant telemetry, and model registry metrics (Restricted to `super_admin`).
