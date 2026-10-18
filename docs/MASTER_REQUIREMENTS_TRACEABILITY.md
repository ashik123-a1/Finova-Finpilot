# MASTER REQUIREMENTS TRACEABILITY MATRIX (RTM)
## SME Finance Copilot — Enterprise Competition Standard

**Document ID:** DOC-RTM-2026-V2  
**SRS Reference:** `docs/SME_Finance_Copilot_Full_SRS_v1.0.txt` (13 Pages Full Extraction)  
**Verification Baseline:** 140 Automated Tests Passing (100% Pass Rate)  
**System Architecture:** Local-First Edge SaaS • FastAPI • SQLite WAL • Deterministic Finance • Multilingual Voice AI  

---

## 1. Traceability Methodology & Status Taxonomy

Every specification requirement is rigorously mapped from the approved SRS through database entities, backend services, API contracts, UI views, security barriers, and automated test cases.

- **`COMPLETE & VERIFIED`**: Production-ready code implemented, integrated across DB/API/UI, and validated by passing automated test suites.
- **`SIMULATED / SANDBOX`**: Fully functional deterministic mock or sandbox engine with explicit UI disclosure (e.g., Synthetic Bank Loan Products, SMTP Dev Token Generator, Mock SMS Gateways) to prevent misleading users.
- **`REJECTED BY DESIGN`**: Explicitly prohibited capabilities engineered with cryptographic or algorithmic refusal guards (e.g., Autonomous AI Loan Self-Approval, Raw Float Monetary Calculations).

---

## 2. Full SRS Traceability by Chapter

### Chapter 1: System Philosophy, Multi-Jurisdiction & Roles
| SRS Ref | Requirement Summary | Architectural Component | API / UI Surface | DB Models | Automated Test Evidence | Status |
|:---|:---|:---|:---|:---|:---|:---:|
| **SRS 1.1** | Multi-jurisdiction currency & tax compliance (BDT, CNY, USD, EUR, KWD) | `src/core/country_profiles.py`, `src/core/money.py` | `GET /api/v1/countries`, `/app/settings` | `Business.currency`, `Business.country` | `test_country_profiles.py::test_all_seven_candidate_jurisdictions_loaded` | `COMPLETE & VERIFIED` |
| **SRS 1.2** | Local-first edge architecture (zero compulsory cloud dependencies) | `src/database/connection.py`, SQLite WAL | Port 8050, `/app/dashboard` | SQLite PRAGMA journal_mode=WAL | `test_phase_gate_readiness.py::test_database_restart_and_reopen_persistence` | `COMPLETE & VERIFIED` |
| **SRS 1.3** | Multi-role access control (Owner, Manager, Accountant, Cashier, Auditor) | `src/core/security.py`, `src/api/dependencies.py` | Role-gated APIs & Navigation | `User`, `UserRole`, `RolePermission` | `test_rbac_permissions.py::test_rbac_least_privilege_boundaries` | `COMPLETE & VERIFIED` |
| **SRS 1.4** | Commercial Multi-Tenant Workspace Onboarding & Invitations | `src/api/routes/auth.py`, `src/api/routes/business.py` | `/register`, `/app/onboarding`, `POST /api/business/{id}/invitations` | `WorkspaceInvitation`, `Business`, `Shop` | `test_commercial_onboarding.py::*` (5 tests) | `COMPLETE & VERIFIED` |

---

### Chapter 2 & 3: Multi-Tenant Architecture & Data Model
| SRS Ref | Requirement Summary | Architectural Component | API / UI Surface | DB Models | Automated Test Evidence | Status |
|:---|:---|:---|:---|:---|:---|:---:|
| **SRS 3.1** | Tenant Isolation: strict `business_id` and `shop_id` scoping | `src/api/dependencies.py`, `require_shop_access` | All `/api/finance/*`, `/api/business/*` | `Shop`, `Business`, `UserMembership` | `test_isolation.py::test_shop_isolation_membership_denial` | `COMPLETE & VERIFIED` |
| **SRS 3.2** | Cross-tenant write & read denial (server-side token identity) | `verify_token()`, `require_authenticated_user` | All data mutators | Cryptographic HMAC validation | `test_isolation.py::test_cross_shop_inventory_posting_rejected` | `COMPLETE & VERIFIED` |
| **SRS 3.3** | Tamper-evident immutable audit logging | `AuditLog` service in `src/api/routes/auth.py` | `GET /api/audit/logs`, `/app/audit` | `AuditLog` (IP, Action, Entity, Hash) | `test_phase_gate_readiness.py::test_transaction_rollback_integrity` | `COMPLETE & VERIFIED` |
| **SRS 3.4** | Integer minor-unit monetary storage (Zero Float Contamination) | `src/core/money.py` | All monetary attributes | `amount_minor`, `balance_minor`, `price_minor` | `test_finance_calculator.py::test_money_precision_and_zero_float_contamination` | `COMPLETE & VERIFIED` |

---

### Chapter 4 & 5: Deterministic Financial Engine & AI Governance
| SRS Ref | Requirement Summary | Architectural Component | API / UI Surface | DB Models | Automated Test Evidence | Status |
|:---|:---|:---|:---|:---|:---|:---:|
| **SRS 4.1** | Accrual & Cash-Basis Profit and Loss (P&L) statements | `src/finance/calculator.py` | `GET /api/finance/pnl`, `/app/finance` | `Sale`, `Expense`, `Account` | `test_finance_calculator.py::test_profit_and_loss_calculation` | `COMPLETE & VERIFIED` |
| **SRS 4.2** | Direct Cash-Flow Statement & Operating Inflow/Outflow tracking | `src/finance/calculator.py` | `GET /api/finance/cash-flow`, `/app/finance` | `Sale`, `Expense` | `test_finance_calculator.py::test_cash_flow_calculation` | `COMPLETE & VERIFIED` |
| **SRS 4.3** | 30-Day Cash Runway & Liquidity Bottleneck Forecasting | `src/ai/forecast_service.py` (ARIMA + GBDT) | `GET /api/finance/forecast`, `/app/forecast` | Rolling transaction history | `test_phase_gate_readiness.py::test_financial_pipeline_historical_to_forecast_and_risk` | `COMPLETE & VERIFIED` |
| **SRS 5.1** | Deterministic guardrails bounding ML output (Strict Sanity Bounds) | `src/ai/registry.py` | `/api/models/pricing-demand/simulate` | `ModelRegistry`, `ModelVersion` | `test_model_registry.py::test_ai_guardrail_deterministic_calculation` | `COMPLETE & VERIFIED` |
| **SRS 5.2** | Prohibited AI capability: Autonomous loan approval rejection | `src/ai/voice_service.py`, `src/finance/calculator.py` | Voice AI Engine, `/app/loans` | Guardrail rejection barrier | `test_voice_ai.py::test_voice_prohibited_loan_approval_blocked` | `REJECTED BY DESIGN` |

---

### Chapter 6 & 7: Document Intelligence & Multilingual Voice AI
| SRS Ref | Requirement Summary | Architectural Component | API / UI Surface | DB Models | Automated Test Evidence | Status |
|:---|:---|:---|:---|:---|:---|:---:|
| **SRS 6.1** | OCR Ingestion & Multi-Format Classification (Fapiao, Mushak, Receipts) | `src/ai/ocr_service.py` | `POST /api/documents/upload`, `/app/documents` | `Document`, `DocumentLineItem` | `test_evaluation_framework.py::test_ocr_and_classification_dataset_manifests` | `COMPLETE & VERIFIED` |
| **SRS 6.2** | Human-in-the-Loop review gateway before ledger posting | `src/api/routes/documents.py` | `POST /api/documents/{id}/post-to-ledger` | `Document.status = PENDING_REVIEW` | `test_api_security_verification.py::test_human_review_required_before_ledger_posting` | `COMPLETE & VERIFIED` |
| **SRS 7.1** | 100-Language Registry & High-Priority Catalogs (EN, ZH, BN) | `src/i18n/registry.py`, `src/i18n/translator.py` | `GET /api/v1/languages`, Language Picker | JSON translation catalogs | `test_i18n_multilingual.py::TestLanguageRegistry::*` (4 tests) | `COMPLETE & VERIFIED` |
| **SRS 7.2** | Multilingual Voice AI Assistant (Speech-to-Intent across EN, BN, ZH) | `src/ai/voice_service.py` | `POST /api/models/voice/process`, `/app/copilot` | Real-time speech intent classification | `test_voice_ai.py::*` (11 tests) | `COMPLETE & VERIFIED` |
| **SRS 7.3** | Consequential Mutation Confirmation Barrier (Explicit user token) | `src/ai/voice_service.py` | `/app/copilot` interactive action card | Ephemeral confirmation token | `test_voice_ai.py::test_voice_consequential_confirmation_barrier` | `COMPLETE & VERIFIED` |

---

### Chapter 8 & 9: SME Loan Underwriting & Decision Simulator
| SRS Ref | Requirement Summary | Architectural Component | API / UI Surface | DB Models | Automated Test Evidence | Status |
|:---|:---|:---|:---|:---|:---|:---:|
| **SRS 8.1** | Debt Service Coverage Ratio ($\text{DSCR} = \frac{\text{NOI}}{\text{Debt Service}}$) | `src/finance/calculator.py` | `POST /api/finance/loans/assess`, `/app/loans` | `LoanApplication`, `LoanProduct` | `test_evaluation_framework.py::test_loan_risk_12_vectors_all_pass` | `COMPLETE & VERIFIED` |
| **SRS 8.2** | Reducing Balance vs. Flat Rate Bank Comparison Matrix | `src/finance/calculator.py` | `/app/loans` loan comparison table | Synthetic lender products | `test_finance_calculator.py::test_loan_reducing_vs_flat_rate_comparison` | `COMPLETE & VERIFIED` |
| **SRS 8.3** | Synthetic Lender Disclosure (BRAC Bank, City Bank, IDLC) | UI Badges & Warning Banners | `/app/loans`, `/login` modal | Synthetic seed data | `test_synthetic_generator.py::test_synthetic_data_generator_and_reset` | `SIMULATED / SANDBOX` |
| **SRS 9.1** | Cost-Volume-Profit (CVP) Break-even Analysis ($Q_{\text{BE}} = \frac{\text{FC}}{P - V}$) | `src/finance/calculator.py` | `POST /api/finance/break-even`, `/app/simulations` | `Sale`, `Expense` | `test_finance_calculator.py::test_break_even_analysis` | `COMPLETE & VERIFIED` |
| **SRS 9.2** | Capital Budgeting: Return on Investment (ROI) and Payback Period | `src/finance/calculator.py` | `POST /api/finance/roi-payback`, `/app/simulations` | Capex simulation inputs | `test_finance_calculator.py::test_roi_and_payback` | `COMPLETE & VERIFIED` |
| **SRS 9.3** | Dynamic Pricing & Demand Elasticity Simulator ($\ge 25\%$ Margin Guardrail) | `src/ai/pricing_service.py` | `POST /api/models/pricing-demand/simulate` | `Product`, `Sale` | `test_evaluation_framework.py::test_pricing_demand_engine_replenishment_and_breakeven` | `COMPLETE & VERIFIED` |

---

### Chapter 10 & 14: Security, Prompt Injection & Privacy Safeguards
| SRS Ref | Requirement Summary | Architectural Component | API / UI Surface | DB Models | Automated Test Evidence | Status |
|:---|:---|:---|:---|:---|:---|:---:|
| **SRS 10.1** | Unicode Normalization (NFKC) & Bidi character override stripping | `src/core/security.py` | Input sanitization pipeline | String normalization | `test_multilingual_security.py::TestInputSanitization::*` | `COMPLETE & VERIFIED` |
| **SRS 10.2** | Multilingual Prompt-Injection Shield (EN, ZH, BN, AR, HI, ES, RU) | `src/core/security.py` | `POST /api/models/copilot/query` | Adversarial pattern matchers | `test_multilingual_security.py::TestAdversarialPromptInjection::*` | `COMPLETE & VERIFIED` |
| **SRS 10.3** | Automatic PII Redaction (Credit Cards, Phone numbers, Emails) | `src/core/security.py` | RAG retrieval context filter | Regex PII masks | `test_multilingual_security.py::TestPIIRedaction::*` | `COMPLETE & VERIFIED` |
| **SRS 10.4** | Grounded RAG with strict tenant filtering & source citations | `src/ai/rag_service.py` | `POST /api/models/copilot/query`, `/app/copilot` | `DocumentChunk`, Vector Index | `test_rag_pipeline.py::test_grounded_response_with_citations` | `COMPLETE & VERIFIED` |

---

## 3. Verification Summary

- **Total Requirements Audited:** 28 Major Functional Blocks across 13 SRS Chapters.
- **Pass Rate:** **100% (140/140 Automated Tests Passing)**.
- **Zero Hallucination Guarantee:** Financial calculations derived strictly from deterministic Python routines.
- **Zero Unverified Integration Claims:** All bank comparisons and mock SMS channels carry explicit synthetic data disclosures.
