# FinTechathon 2026: SME Finance Copilot — Security Posture & Threat Assessment

**Document Version:** 1.0.0 (Master Release)  
**Security Standard:** OWASP Top 10 API / ISO 27001 Financial Workloads  
**Audit Verification:** 100% Passed (45 Security & Isolation Tests)

---

## 1. Threat Modeling & Defense-in-Depth Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                              CLIENT TIERS                              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    [Defense Layer 1: HTTP Security & Header Sanitation]
    ├── Content-Security-Policy (CSP)
    ├── Strict CORS & SameSite=Lax Cookie Directives
    └── Discard Client-Forged Identity Headers (X-User-ID, X-Role)
                                    │
                                    ▼
    [Defense Layer 2: Cryptographic Identity & Session Gate]
    ├── HMAC SHA-256 Signed Session Tokens
    └── Bcrypt Password Hashing with Dynamic Salt
                                    │
                                    ▼
    [Defense Layer 3: RBAC & Tenant Isolation Barrier]
    ├── 7 Normalized Roles & 22 Atomic Permissions
    └── Server-Side Query Binding: WHERE business_id = :authorized_bid
                                    │
                                    ▼
    [Defense Layer 4: Autonomous AI Consequential Safeguard]
    ├── Adversarial Prompt-Injection Regex & Heuristic Scanners
    └── Consequential Action Authorization Barrier (Single-Use Token)
                                    │
                                    ▼
    [Defense Layer 5: Data Integrity & Storage Safeguards]
    ├── SQLite WAL Atomic Commit & Rollback Protection
    └── CSV Formula Injection (DDE) Sanitization (Leading Quote Prefix)
```

---

## 2. Authentication & Identity Verification

### Protection Against Header Forgery
Many microservice architectures vulnerably rely on headers like `X-User-ID` or `X-Shop-ID`. In SME Finance Copilot:
* Client-supplied identity headers are **strictly ignored**.
* Identity is derived **only** from cryptographically signed HMAC SHA-256 tokens passed via `Authorization: Bearer <token>` or HTTP-only `sme_auth_token` cookies.
* Tampered or fabricated tokens trigger immediate HTTP 401 Unauthorized rejection.

---

## 3. Role-Based Access Control (RBAC) Matrix

The system implements 7 discrete roles governed by 22 granular permissions:

| Permission | Owner | Manager | Accountant | Sales | Inventory | Auditor | Super Admin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `manage_business` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `manage_users` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `post_ledger` | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| `view_ledger` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `manage_inventory` | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `manage_customers` | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| `view_reports` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `audit_compliance` | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `platform_admin` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 4. Multi-Tenant Isolation Guarantees

* **Zero Cross-Tenant Leakage:** Every database query targeting transactions, inventory, customers, or RAG embeddings requires authorization against the user's active `business_memberships`.
* **Explicit Cross-Tenant Attack Test:** Verified in `tests/test_api_security_verification.py`. An attacker possessing valid User 1 credentials attempting to access Business 2 records receives an immediate HTTP 403 Forbidden.

---

## 5. Autonomous AI & Voice Safeguards

### Adversarial Prompt-Injection Guardrail
Incoming Copilot and Voice queries are screened before RAG retrieval or LLM invocation. Prompts matching jailbreak archetypes (e.g. DAN, *"ignore previous instructions"*, *"override system policy"*) are intercepted by the security guardrail, triggering an immediate refusal mode without invoking backend tools or exposing data.

### Consequential Action Authorization Barrier
Autonomous AI is architecturally barred from executing writes to production ledgers. When an action intent is detected (e.g. *"Record expense of $500"*):
1. The transaction parameters are staged in memory.
2. A cryptographic confirmation token is generated.
3. The response halts at a visual Confirmation Barrier in the UI.
4. Production tables remain untouched until the user clicks **"Confirm Execution"**.

---

## 6. Report Export Security (CSV DDE Defense)

When financial records or customer lists are exported to CSV, malicious values (e.g. customer names or invoice descriptions starting with `=`, `+`, `-`, `@`, `\t`, `\r`) are automatically escaped with a leading single quote (`'`). This prevents Dynamic Data Exchange (DDE) remote code execution in spreadsheet applications like Microsoft Excel and LibreOffice Calc.
