# SME Finance Copilot — User Role Model, Registration Policy & RBAC Permissions Matrix

**Specification Source:** Master SRS Section 3 & System Architecture  
**Audit Status:** `VERIFIED COMPLETE`  
**Database Migration:** `002_seed_roles_and_permissions.sql`  
**Automated Verification:** `tests/test_rbac_permissions.py` (3/3 Passed, 100%)  

---

## 1. Executive Summary

The SME Finance Copilot enforces an institutional-grade, multi-tenant Role-Based Access Control (RBAC) architecture. Security is strictly decoupled from client-supplied identity: client headers (`X-User-ID`, `X-Business-ID`, `X-Shop-ID`) are never trusted for authentication or role assignment. All operations require signed HMAC-SHA256 session tokens verified against server-side database records.

---

## 2. Canonical User Roles Model

The platform defines exactly **7 canonical user roles** based on the principle of least privilege:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PLATFORM SUPER ADMIN                            │
│           (Platform Settings, System Health, Audit Telemetry)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Multi-Tenant Barrier
┌───────────────────────────────────▼────────────────────────────────────┐
│                           BUSINESS OWNER                               │
│       (Full Workspace Ownership, P&L, Financing, Team Invitations)     │
└───────┬───────────────────┬───────────────────┬──────────────────┬─────┘
        │                   │                   │                  │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐  ┌───────▼─────┐
│BUSINESS ADMIN │   │  ACCOUNTANT   │   │  SALES / CRM  │  │ INVENTORY / │
│   / MANAGER   │   │/ FINANCE STAFF│   │     STAFF     │  │ OPERATIONS  │
│ (Branch Ops)  │   │ (Ledger & OCR)│   │ (CRM & Sales) │  │(Catalog/Stk)│
└───────────────┘   └───────────────┘   └───────────────┘  └─────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │    READ-ONLY ADVISOR / AUDITOR│
                    │   (Audit Reports, Verification)│
                    └───────────────────────────────┘
```

### Role A: Platform Super Admin (`super_admin`)
- **Responsibilities:** Platform-level configurations, managing authorized administrators, inspecting system health metrics and security anomaly events, monitoring global audit telemetry.
- **Strict Boundary:** Never permits public self-registration. Strictly partitioned from individual business operational ledgers; cannot execute financial transactions or alter business sales data.

### Role B: Business Owner (`owner`)
- **Responsibilities:** Registers the enterprise account, initializes business workspaces, configures country/currency/tax profiles, provisions branches/shops, authorizes financial reports, reviews AI forecasts and financing terms, invites team members, assigns roles, and executes consequential actions.
- **Strict Boundary:** Retains absolute administrative control within their tenant workspace, but cannot access other businesses or platform-wide administration.

### Role C: Business Admin / Manager (`manager`)
- **Responsibilities:** Oversees assigned shop operations, manages branch-level settings, monitors daily sales and expense entries, reviews OCR extractions, and invites operational staff.
- **Strict Boundary:** Cannot delete historical general ledger journals, change ownership, or alter platform-level parameters.

### Role D: Accountant / Finance Staff (`accountant`)
- **Responsibilities:** Full ledger transaction reviews, accounts receivable/payable reconciliation, reviewing raw OCR document extractions, confirming invoice postings to ledgers, and generating P&L/Cash Flow statements.
- **Strict Boundary:** Cannot invite users, delete transactions without audit reason, or modify workspace ownership.

### Role E: Sales / CRM Staff (`sales`)
- **Responsibilities:** Manages customer records, reviews customer order history, monitors RFM segmentations, drafts polite payment reminder messages, and records POS sales transactions.
- **Strict Boundary:** Strictly denied access to sensitive overall business P&L, cash-flow projections, bank loan applications, and general ledger journal reversals.

### Role F: Inventory / Operations Staff (`inventory`)
- **Responsibilities:** Maintains product SKU catalog, updates stock quantities, monitors replenishment thresholds, inspects stock aging indicators, and records incoming supplier shipments.
- **Strict Boundary:** Zero access to financial accounting records, profit/loss statements, customer CRM debt collection, or financing comparisons.

### Role G: Read-only Advisor / Auditor (`auditor`)
- **Responsibilities:** Inspects verifiable financial statements, audit logs, model explainability metrics, and DSCR affordability ratios for bank or tax compliance.
- **Strict Boundary:** 100% read-only access. Strictly prohibited from posting, editing, voiding, or deleting any transaction, customer, product, or document.

---

## 3. Registration and Onboarding Policy

### 3.1 Public Registration
- **Self-Service Sign-Up:** Available at `/register` and `/api/auth/register`.
- **Supported Personas:** Public sign-up creates a new `User`, provisions a new `Business` workspace, creates the primary `Shop` (Main Branch), and assigns the registrant as `owner`.
- **Validation:** Unique email enforcement, PBKDF2-HMAC-SHA256 password hashing (200,000 rounds), business name, default currency, and phone validation.

### 3.2 Staff Member Onboarding (Invitation Workflow)
- **Zero Self-Assigned Privileges:** Staff cannot publicly register directly into an existing business.
- **Invitation Flow:**
  1. An authorized `owner` or `manager` issues an invitation with email, target `shop_id`, and assigned `role_code`.
  2. The system generates a cryptographic, time-limited token.
  3. The invited user accepts the invitation, authenticates, and is granted an active `BusinessMembership`.

### 3.3 Platform Administrator Provisioning
- Super admin accounts can only be provisioned via direct server-side administrative CLI or migration scripts. Public registration endpoints reject any request attempting to create a `super_admin` role.

---

## 4. Multi-Tenant Business & Shop Membership

Every user session operates within an explicit multi-tenant hierarchy:

$$\text{User} \xrightarrow{1:N} \text{BusinessMembership} \xrightarrow{N:1} \text{Business} \xrightarrow{1:M} \text{Shop}$$

- **Enterprise-Wide Access:** When `BusinessMembership.shop_id IS NULL`, the user has authorized access across all shops within that business (typical for Owners and Senior Accountants).
- **Branch-Restricted Access:** When `BusinessMembership.shop_id = X`, the user's effective permissions are strictly confined to Shop $X$ (typical for branch cashiers, sales staff, and shop managers).
- **Cross-Tenant Prevention:** Attempting to query or mutate records from Shop $Y$ using a token authorized only for Shop $X$ triggers a server-side `ShopAccessDeniedError` (HTTP 403 Forbidden) and writes a security audit event.

---

## 5. Granular RBAC Permissions Matrix

The system defines **22 granular permissions** mapped across all 7 user roles:

| Permission Code | Description | Super Admin | Owner | Manager | Accountant | Sales | Inventory | Auditor |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `business.view` | View business profile & locations | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| `business.edit` | Edit business profile & fiscal settings | **ALLOW** | **ALLOW** | **COND** | **DENY** | **DENY** | **DENY** | **DENY** |
| `finance.view` | View P&L, balance sheets & ledgers | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **ALLOW** |
| `finance.create` | Record sales & expense transactions | **DENY** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **DENY** | **DENY** |
| `finance.edit` | Edit or adjust recorded journals | **DENY** | **ALLOW** | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **DENY** |
| `finance.delete` | Reverse or void transactions | **DENY** | **ALLOW** | **DENY** | **DENY** | **DENY** | **DENY** | **DENY** |
| `document.upload` | Upload commercial invoices & receipts | **DENY** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **DENY** |
| `document.review` | Review & correct extracted OCR fields | **DENY** | **ALLOW** | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **ALLOW** |
| `document.post` | Confirm & post invoices to ledger | **DENY** | **ALLOW** | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **DENY** |
| `forecast.view` | View cash-flow forecasts & runway | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **ALLOW** |
| `loan.compare` | Compare SME loan & financing options | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **ALLOW** |
| `loan.risk_assess` | Evaluate DSCR & borrowing capacity | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **ALLOW** |
| `crm.manage` | Manage customers, RFM & reminders | **DENY** | **ALLOW** | **ALLOW** | **DENY** | **ALLOW** | **DENY** | **DENY** |
| `inventory.manage`| Manage catalog, stock & aging | **DENY** | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **ALLOW** | **DENY** |
| `team.invite` | Issue team invitations | **ALLOW** | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **DENY** | **DENY** |
| `team.remove` | Revoke memberships & access | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **DENY** | **DENY** | **DENY** |
| `team.roles` | Assign and modify user roles | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **DENY** | **DENY** | **DENY** |
| `integration.manage` | Configure bank & POS connections | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **DENY** | **DENY** | **DENY** |
| `data.export` | Export financial & audit datasets | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **COND** | **COND** | **ALLOW** |
| `audit.view` | View immutable audit trails | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **ALLOW** |
| `system.execute` | Execute sensitive system workflows | **ALLOW** | **ALLOW** | **DENY** | **DENY** | **DENY** | **DENY** | **DENY** |
| `admin.access` | Access platform super-admin portal | **ALLOW** | **DENY** | **DENY** | **DENY** | **DENY** | **DENY** | **DENY** |

*Legend:*
- **ALLOW**: Granted unconditionally within authorized tenant boundary.
- **DENY**: Prohibited; attempts return HTTP 403 Forbidden.
- **COND (Conditional)**: Allowed only for branch-assigned resources (e.g. Sales can only export customer lists; Inventory can only export stock lists).

---

## 6. Technical Implementation and Test Verification

1. **Database Schema:**
   - Table `roles`: 7 rows.
   - Table `permissions`: 22 rows.
   - Table `role_permissions`: 80 mapped relationships.
2. **Server-Side Security:**
   - `src/core/security.py`: `has_permission(role_code, permission_code)` and `enforce_shop_isolation(user_id, shop_id, memberships, required_permission)`.
3. **Automated Test Results:**
   - `tests/test_rbac_permissions.py::test_database_roles_and_permissions_seeded` -> `PASSED`
   - `tests/test_rbac_permissions.py::test_rbac_least_privilege_boundaries` -> `PASSED`
   - `tests/test_rbac_permissions.py::test_enforce_shop_isolation_with_rbac_permission` -> `PASSED`
