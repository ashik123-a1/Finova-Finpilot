# FinTechathon 2026: SME Finance Copilot — System Architecture & Data Pipelines

**Document Version:** 1.0.0 (Master Release)  
**Track:** Topic E — SME Finance Copilot  
**Architecture Paradigm:** Local-First, Zero-Float Deterministic Finance, Multi-Tenant Hybrid AI

---

## 1. High-Level Architectural Topology

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                CLIENT TIERS & USER INTERFACES                          │
│                                                                                        │
│   ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐   │
│   │   Executive Dashboard  │  │   Financial AI Copilot │  │  Cyber-Fintech Voice   │   │
│   │   & Multi-Shop Cockpit │  │   Conversational HUD   │  │  Autonomous HUD Console│   │
│   └───────────┬────────────┘  └───────────┬────────────┘  └───────────┬────────────┘   │
└───────────────┼───────────────────────────┼───────────────────────────┼────────────────┘
                │                           │                           │
                ▼                           ▼                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI APPLICATION GATEWAY LAYER                         │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ Middleware Stack: CORS, GZip, Request ID, Content-Security-Policy (CSP)        │   │
│   ├────────────────────────────────────────────────────────────────────────────────┤   │
│   │ Authentication & Tenant Isolation: HMAC Token Verifier & Role Enforcement      │   │
│   ├────────────────────────────────────────────────────────────────────────────────┤   │
│   │ Router Subsystems:                                                             │   │
│   │  - /api/auth       - /api/business     - /api/finance      - /api/documents    │   │
│   │  - /api/crm        - /api/inventory    - /api/loans        - /api/notifications│   │
│   │  - /api/reports    - /api/models       - /api/voice        - /api/admin        │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
└───────────────────────────────────────────┼────────────────────────────────────────────┘
                                            │
                ┌───────────────────────────┴───────────────────────────┐
                ▼                                                       ▼
┌──────────────────────────────────────┐    ┌────────────────────────────────────────┐
│       DETERMINISTIC FINANCE &        │    │        HYBRID AI & RAG COGNITIVE       │
│          CREDIT RISK CORE            │    │               SUBSYSTEM                │
│                                      │    │                                        │
│ ┌──────────────────────────────────┐ │    │ ┌────────────────────────────────────┐ │
│ │ Zero-Float Arithmetic Engine     │ │    │ │ 11-Domain Intent Classifier        │ │
│ │ (Integer Minor Currency Units)   │ │    │ │ (EN, Bengali, Simplified Chinese)  │ │
│ └──────────────────────────────────┘ │    │ └────────────────────────────────────┘ │
│ ┌──────────────────────────────────┐ │    │ ┌────────────────────────────────────┐ │
│ │ Credit Underwriting & DSCR       │ │    │ │ Intent-Gated Vector Retrieval      │ │
│ │ (1.25x Bank Benchmark Evaluator) │ │    │ │ (Domain Filtering: Loan vs Tax)    │ │
│ └──────────────────────────────────┘ │    │ └────────────────────────────────────┘ │
│ ┌──────────────────────────────────┐ │    │ ┌────────────────────────────────────┐ │
│ │ Cash Runway & ARIMA Forecasting  │ │    │ │ Grounded Ledger Analytics Synthesizer││
│ │ (Daily Burn Rate & Alerts)       │ │    │ │ (5-Stage Turnaround Modeling)      │ │
│ └──────────────────────────────────┘ │    │ └────────────────────────────────────┘ │
│ ┌──────────────────────────────────┐ │    │ ┌────────────────────────────────────┐ │
│ │ Report Exporters (CSV & PDF)     │ │    │ │ Consequential Action Barrier       │ │
│ │ (Formula-Injection Sanitizer)    │ │    │ │ (Two-Step Cryptographic Token)     │ │
│ └──────────────────────────────────┘ │    │ └────────────────────────────────────┘ │
└──────────────────┬───────────────────┘    └───────────────────┬────────────────────┘
                   │                                            │
                   └─────────────────────┬──────────────────────┘
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              LOCAL-FIRST PERSISTENCE LAYER                             │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ SQLite 3 Relational Engine with Write-Ahead Logging (PRAGMA journal_mode=WAL)  │   │
│   ├────────────────────────────────────────────────────────────────────────────────┤   │
│   │ 50 Normalized Relational Tables (Users, Businesses, Shops, Ledgers, Documents) │   │
│   ├────────────────────────────────────────────────────────────────────────────────┤   │
│   │ Disaster Recovery: Automated WAL-Safe Snapshots with SHA-256 Manifests         │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Principles

### 1. Local-First & 100% Offline Edge Resilience
The entire application is self-contained. It operates fully without third-party cloud infrastructure, SaaS dependencies, or mandatory external API access. When network access is absent, deterministic rule-based algorithms, vector embeddings, and OCR extractions execute locally.

### 2. Zero-Float Accounting & Precision Finance
In strict compliance with banking standards, all financial figures are modeled in integer minor units (e.g. cents, poisha, fen). Floating-point arithmetic (`float`) is barred from ledger storage, eliminating floating-point rounding errors. Formatted output is derived at the presentation layer using the enterprise's configured currency profile.

### 3. Strict Multi-Tenant Isolation
Tenant isolation is enforced server-side on every request:
* Authentication tokens encode `user_id` signed via HMAC SHA-256.
* Database models bind every resource to a `business_id` and subordinate `shop_id`.
* Every query enforces `WHERE business_id = :authorized_bid`. Cross-tenant queries targeting foreign IDs trigger HTTP 403 Forbidden.

### 4. Consequential Action Authorization Barriers
Autonomous financial AI is prohibited from directly modifying production ledgers or executing credit commitments without human-in-the-loop authorization. When an action intent is detected (e.g. *"Record an expense of $500"*), the system generates a single-use cryptographically signed confirmation token. The transaction remains in a staged, non-committed state until the user reviews and confirms.

---

## 3. Data Flow Pipelines

### Pipeline A: Financial AI Copilot Loss Recovery & Strategy
```
[User Query]
     │
     ▼
[Adversarial Prompt-Injection Guardrail] ──(Detected Attack)──► [Immediate Refusal Mode]
     │
     ▼ (Clean Query)
[11-Domain Intent Classifier] ──► Identifies Intent: "business_loss_recovery"
     │
     ▼
[Tenant-Isolated DB Analytics Extractor]
  ├── Query: Total Revenue (minor units) & Transaction Count
  ├── Query: Total Expenses (minor units) & Transaction Count
  ├── Query: Category Breakdown (Rent, Salary, Utilities)
  ├── Query: Unpaid Receivables ($89,382.50 across 44 invoices)
  └── Query: Stock Asset Valuation ($2,448,570.00 across 41 SKUs)
     │
     ▼
[Intent-Gated Document Filter]
  └── Suppresses unrelated loan sanction letters for operational questions
     │
     ▼
[Deterministic Turnaround Synthesizer]
  ├── Section 1: Current Financial Position (Reconciled actuals)
  ├── Section 2: Evidence-Backed Findings (Fixed overhead concentration)
  ├── Section 3: Prioritized 3-Phase Action Plan (Days 1–15, 16–45, 46–90)
  ├── Section 4: Quantified Scenarios (5% cut = +$243k; 10% sales = +$152k)
  └── Section 5: Recommended Next Steps
     │
     ▼
[Client Response (Markdown Rendered)]
```

### Pipeline B: Smart OCR Document Ingestion & Human Review
```
[Physical Invoice Upload (PDF / Image)]
     │
     ▼
[MIME-Type & Magic Byte Validation]
     │
     ▼
[Text Extraction Engine (RegEx & OCR Pattern Matching)]
     │
     ▼
[Document Staged in 'requires_review' Status]
     │
     ▼
[Accountant Review Screen (/app/documents)]
     │
     ▼
[Human-in-the-Loop Confirmation] ──(Approved)──► [Atomic Ledger Posting in DB]
```
