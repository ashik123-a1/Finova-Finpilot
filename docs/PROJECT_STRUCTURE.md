# FinTechathon 2026: SME Finance Copilot — Repository Directory Architecture

```text
sme-finance-copilot/                               # Competition submission root directory
├── README.md                                      # Executive overview, architecture, test badges & quickstart
├── .gitignore                                     # Excludes secrets (.env), SQLite binaries, WAL files & private caches
├── .env.example                                   # Secure environment variable configuration template
├── pyproject.toml                                 # Python packaging, toolchain configurations & pytest settings
├── requirements.txt                               # Pinned backend dependencies (FastAPI, SQLAlchemy, ReportLab, etc.)
├── start.bat                                      # 1-Click Windows launch script (Uvicorn on port 8050)
├── share_online.bat                               # Optional encrypted public tunnel launcher for live evaluation
├── sme_finance.db                                 # Primary SQLite database with WAL mode enabled (163,000+ records)
│
├── docs/                                          # Formal technical & competition documentation
│   ├── ARCHITECTURE.md                            # Comprehensive system architecture & data pipeline flow
│   ├── DATABASE.md                                # Database schema, 8 migrations, WAL mode & recovery protocol
│   ├── API_REFERENCE.md                           # Exhaustive API reference for all 18 backend service routers
│   ├── SECURITY.md                                # Security posture, RBAC matrices, HMAC tokens & threat modeling
│   ├── TESTING.md                                 # Canonical 50 numbered test cases (TC-01..TC-50) & 220 test audit
│   ├── INSTRUCTION_BOOK.md                        # Complete local installation, execution & troubleshooting manual
│   ├── PROJECT_STRUCTURE.md                       # Screenshot-style terminal visual tree with # comments
│   ├── DEPLOYMENT.md                              # Local-first execution, production ASGI flags & container guide
│   ├── AI_COPILOT.md                              # 11-category financial intent routing & loss turnaround mechanics
│   ├── REPORTS_AND_BACKUPS.md                     # Authorized CSV/PDF export & isolated disaster recovery guide
│   └── KNOWN_LIMITATIONS.md                       # Transparent disclosure of simulated and non-implemented areas
│
├── src/                                           # Production source code
│   ├── __init__.py                                # Top-level package marker
│   ├── config.py                                  # Application configuration, currency profiles & security defaults
│   │
│   ├── ai/                                        # Autonomous Financial AI & RAG Subsystem
│   │   ├── __init__.py                            # AI package marker
│   │   ├── rag_service.py                         # 11-intent classifier, grounded ledger extractor & RAG orchestrator
│   │   └── voice_service.py                       # Real-time Voice AI processor with consequential action safeguards
│   │
│   ├── api/                                       # FastAPI REST API & WebSocket Application Layer
│   │   ├── __init__.py                            # API package marker
│   │   ├── app.py                                 # FastAPI application entrypoint, middleware & lifecycle events
│   │   ├── dependencies.py                        # Dependency injection (signed HMAC session tokens, DB sessions)
│   │   └── routes/                                # Domain-specific API endpoint routers
│   │       ├── __init__.py                        # Router aggregator
│   │       ├── auth.py                            # Authentication, 1-click demo logins, registration & logout
│   │       ├── business.py                        # Multi-tenant workspace creation, onboarding & shop switching
│   │       ├── finance.py                         # General ledger, revenue/expense analytics, daily cash streams
│   │       ├── documents.py                       # Secure document upload, OCR extraction & ledger posting
│   │       ├── crm.py                             # Customer management, RFM segmentation & WhatsApp dunning
│   │       ├── inventory.py                       # SKU catalog, stock movement audit, reorders & PO drafting
│   │       ├── notifications.py                   # Persistent notification stream, unread counts & mark-as-read
│   │       ├── reports.py                         # Authorized financial statements export (CSV & PDF formats)
│   │       ├── models.py                          # Copilot query routing & AI model registry telemetry
│   │       ├── voice.py                           # Multilingual voice intent processing & action confirmations
│   │       ├── i18n.py                            # Translation catalog lookup & dynamic currency conversion
│   │       └── admin.py                           # Platform Admin Portal HUD (Super Admin authorization boundary)
│   │
│   ├── core/                                      # Core Banking & International Profiles
│   │   ├── __init__.py                            # Core package marker
│   │   ├── calculator.py                          # Zero-float financial math, interest amortization & DSCR engine
│   │   └── country_profiles.py                    # Multi-jurisdiction rules (Bangladesh, China, Kuwait, etc.)
│   │
│   ├── crm/                                       # Customer Relationship & Receivables Intelligence
│   │   ├── __init__.py                            # CRM package marker
│   │   └── rfm.py                                 # Recency, Frequency, Monetary (RFM) VIP customer segmentation
│   │
│   ├── database/                                  # Database Layer & Schema Migrations
│   │   ├── __init__.py                            # Database package marker
│   │   ├── connection.py                          # SQLAlchemy engine setup & SQLite WAL-mode session lifecycle
│   │   ├── models.py                              # 50 normalized relational ORM models (Tenant-isolated)
│   │   ├── backup_service.py                      # WAL-safe database backup creation & isolated restoration
│   │   ├── integrity.py                           # PRAGMA integrity check & foreign key constraint auditing
│   │   ├── seed.py                                # Idempotent demo persona & historical ledger seed data
│   │   └── migrations/                            # Forward-only database migration runner
│   │       ├── runner.py                          # Migration version tracker table & checksum validation
│   │       └── versions/                          # Numbered SQL migration files
│   │           ├── 001_initial_schema.sql         # Core users, businesses, shops, sales, expenses, inventory
│   │           ├── 002_seed_roles_and_permissions.sql # 7 roles and 22 fine-grained permissions
│   │           ├── 003_document_chunks_rag.sql    # Vector embedding chunk storage & RAG index
│   │           ├── 004_workspace_invitations.sql  # Enterprise workspace invitations & password resets
│   │           ├── 005_notification_enhancements.sql # Persistent user notifications stream
│   │           ├── 006_crm_inventory_campaigns.sql   # RFM customer segmentation & discount campaigns
│   │           ├── 007_user_language_preference.sql  # User profile preferred localization persistence
│   │           └── 008_report_executions.sql      # Audit trail for generated CSV & PDF exports
│   │
│   ├── documents/                                 # Smart Document Pipeline (OCR & Classification)
│   │   ├── __init__.py                            # Documents package marker
│   │   ├── classifier.py                          # Multi-jurisdictional invoice/receipt document classifier
│   │   ├── extractor.py                           # RegEx/OCR invoice field extraction (NBR Mushak 6.3, Fapiao)
│   │   └── poster.py                              # Human-in-the-loop approved transaction ledger posting
│   │
│   ├── evaluation/                                # Model Registry & Accuracy Benchmarking
│   │   ├── __init__.py                            # Evaluation package marker
│   │   ├── benchmark.py                           # ARIMA forecasting & DSCR model accuracy benchmark suite
│   │   └── registry.py                            # Model versioning, active champion routing & fallback flags
│   │
│   ├── finance/                                   # Financial Reporting & Loan Packet Services
│   │   ├── __init__.py                            # Finance package marker
│   │   ├── pdf_packet.py                          # Official Credit Underwriting Packet PDF generator
│   │   ├── report_exporters.py                    # CSV (formula-injection safe) and PDF report builders
│   │   └── reports_service.py                     # Report generation orchestrator & file persistence
│   │
│   ├── i18n/                                      # Multilingual Internationalization Engine
│   │   ├── __init__.py                            # i18n package marker
│   │   ├── translator.py                          # Multi-locale catalog loader (EN, Bengali, Chinese)
│   │   └── locales/                               # Exhaustive translation dictionaries
│   │       ├── en.json                            # English canonical string catalog
│   │       ├── bn.json                            # Bengali (বাংলা) complete localized dictionary
│   │       ├── zh.json                            # Simplified Chinese (简体中文) complete dictionary
│   │       ├── ar.json                            # Arabic regional fallback dictionary
│   │       ├── hi.json                            # Hindi regional fallback dictionary
│   │       └── es.json                            # Spanish regional fallback dictionary
│   │
│   └── web/                                       # Server-Rendered Glassmorphism Fintech UI
│       ├── router.py                              # Jinja2 template routes & multi-tier locale resolution
│       ├── static/                                # Static web assets (CSS, JS, Images, Videos)
│       │   ├── css/theme.css                      # Cyber-fintech glassmorphism styling & animations
│       │   ├── js/app.js                          # Client-side reactivity, chart rendering & notifications
│       │   ├── js/voice_controller.js             # Web Speech API audio controller & HUD visualizer
│       │   └── images/                            # Theme backgrounds, architectural blueprints & icons
│       └── templates/                             # Jinja2 HTML templates
│           ├── base.html                          # Root shell (meta tags, preloader, fonts, toast alerts)
│           ├── landing.html                       # Futuristic landing page with live execution sandbox
│           ├── login.html                         # Login portal with 7 1-click selectable demo personas
│           ├── register.html                      # Commercial SME merchant registration flow
│           └── app/                               # Authenticated merchant portal views
│               ├── layout.html                    # Unified portal shell (header, sidebar, shop switcher)
│               ├── dashboard.html                 # Executive financial cockpit (live KPIs & daily stream)
│               ├── finance.html                   # General ledger, revenue/expense CRUD & transaction log
│               ├── forecast.html                  # Cash runway projection, daily burn rate & ARIMA trends
│               ├── loans.html                     # Interactive loan calculator, DSCR underwriting & PDF packet
│               ├── documents.html                 # Smart OCR document upload, preview & staging review
│               ├── customers.html                 # CRM customer directory, RFM tiers & WhatsApp dunning
│               ├── inventory.html                 # SKU warehouse management, stock valuation & PO drafting
│               ├── copilot.html                   # Financial AI Copilot chat with loss turnaround scenarios
│               ├── voice.html                     # Futuristic Cyber-Fintech real-time voice HUD console
│               ├── reports.html                   # Authorized financial statement export & database backup
│               ├── audit.html                     # Tamper-evident cryptographic audit log inspector
│               ├── settings.html                  # Shop settings, currency selector & user permissions
│               └── admin.html                     # Platform Admin Portal HUD (Super Admin view)
│
├── tests/                                         # Comprehensive Automated Regression Test Suite
│   ├── conftest.py                                # Test fixtures (isolated in-memory DB, auth client, seeded shops)
│   ├── test_ai_copilot_intelligence.py            # AI intent classification, loss recovery, scenarios, guardrails
│   ├── test_rag_pipeline.py                       # Vector embeddings, tenant isolation, prompt injection defense
│   ├── test_api_integration.py                    # End-to-end API routes, financial calculations & OCR pipeline
│   ├── test_api_security_verification.py          # Auth header forgery, path traversal, division by zero
│   ├── test_auth_and_rbac.py                      # Registration, 7 demo personas, role permission boundaries
│   ├── test_commercial_onboarding.py              # Commercial onboarding, workspace invites, password resets
│   ├── test_country_profiles.py                   # 7 international jurisdictions & Kuwait 3-decimal precision
│   ├── test_crm_and_inventory.py                  # RFM segmentation, aging receivables, low-stock reorder
│   ├── test_dashboard.py                          # Live dashboard KPIs, daily sales/expense trend reconciliation
│   ├── test_i18n_and_voice.py                     # Multilingual catalogs completeness & voice action barriers
│   ├── test_isolation.py                          # Shop-level membership isolation & cross-shop posting denial
│   ├── test_loan_and_dscr_module.py               # Loan EMI precision, DSCR underwriting & PDF packet download
│   ├── test_master_completion_phase.py            # 6-step onboarding wizard & 7 demo personas end-to-end
│   ├── test_multilingual_security.py              # XSS injection defense, locale normalization, currency API
│   ├── test_notifications.py                      # Persistent notification stream, unread counts & mark-all-read
│   ├── test_phase_gate_readiness.py               # Foreign key enforcement, atomic rollbacks & restart persistence
│   ├── test_rbac_permissions.py                   # Least privilege boundaries & shop permission enforcement
│   ├── test_report_generation_and_storage.py      # Persistence across restarts, CSV injection defense, backups
│   ├── test_synthetic_generator.py                # Realistic multi-shop synthetic ledger generator & reset
│   ├── test_voice_ai.py                           # Voice intent parsing, what-if simulation & confirmation barriers
│   └── test_web_ui.py                             # Landing page, login, 13 portal views, language switcher
│
├── scripts/                                       # Operational, Verification & Seeding Scripts
│   ├── seed_rag_documents.py                      # Seed statutory VAT, tax, and loan agreements for RAG retrieval
│   ├── seed_demo_bank_products.py                 # Seed Tier-1 commercial bank loan products and interest rate cards
│   └── db_backup.py                               # CLI utility for WAL-safe backup creation & integrity checks
│
├── var/                                           # Runtime Data & Exports (Strictly Excluded from Git)
│   ├── backups/                                   # Local WAL-safe database backups (.db) & SHA-256 manifests (.json)
│   │   ├── .gitkeep                               # Retains directory structure in repository
│   │   ├── sme_backup_20261020_105146.db          # Verified SQLite backup snapshot (23.46 MB, 163,054 records)
│   │   └── manifest_20261020_105146.json          # SHA-256 integrity manifest & table record count breakdown
│   └── exports/                                   # Generated CSV & PDF financial statement reports
│       └── .gitkeep                               # Retains directory structure in repository
│
├── reports/                                       # Independent Evaluation & Audit Reports
│   ├── release_audit.md                           # Final release audit across all 18 modules (PASS classifications)
│   ├── test_report.md                             # Exhaustive 220-test execution report with exact terminal logs
│   ├── dependency_inventory.md                    # Verified dependency inventory & software versions
│   ├── reproducibility_report.md                  # Clean-checkout reproducibility & local installation audit
│   ├── cleanup_manifest.md                        # File hygiene, scratch scripts inventory & quarantine status
│   └── deliverables_checklist.md                  # FinTechathon 2026 deliverables compliance checklist
│
└── submission/                                    # Competition Submission Deliverables Package
    ├── README.md                                  # Submission overview, competition track & executive brief
    ├── deliverables_checklist.md                  # Formal compliance verification checklist
    ├── demo_script.md                             # 10-step judge walkthrough demo script with talking points
    ├── presentation_script.md                     # Timed 5-minute English speaker script
    ├── technical_documentation.pdf                # Formal technical documentation PDF (ReportLab generated)
    ├── security_self_assessment.pdf               # Formal security & threat assessment PDF (ReportLab generated)
    ├── presentation.pdf                           # Pitch deck presentation slide deck PDF
    ├── presentation.pptx                          # Editable pitch deck presentation slide deck PPTX
    └── execution_evidence/                        # Genuine sanitized execution evidence
        ├── copilot_loss_recovery_verified.png     # Browser evidence: English loss recovery turnaround response
        └── copilot_loss_recovery_bengali_verified.png # Browser evidence: Bengali localized loss recovery response
```
