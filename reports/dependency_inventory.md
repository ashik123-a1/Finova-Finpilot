# FinTechathon 2026: SME Finance Copilot — Dependency Inventory

**Document Version:** 1.0.0 (Master Release)  
**Python Runtime:** 3.11.9 (64-bit)  
**Package Manager:** pip 24.0+ / setuptools

---

## 1. Verified Production Dependencies (`requirements.txt`)

| Package Name | Installed Version | License | Architectural Function |
| :--- | :---: | :---: | :--- |
| `fastapi` | `0.110.0` | MIT | Core ASGI Web Framework & REST API |
| `uvicorn` | `0.29.0` | BSD-3-Clause | High-performance ASGI Web Server |
| `sqlalchemy` | `2.0.29` | MIT | Relational ORM & Database Connection Pool |
| `pydantic` | `2.6.4` | MIT | Data Validation & Request/Response Serialization |
| `jinja2` | `3.1.3` | BSD-3-Clause | Server-Side Glassmorphism Template Rendering |
| `reportlab` | `5.0.1` | BSD | Official Financial Statement & Loan Packet PDF Exporter |
| `python-multipart`| `0.0.9` | Apache-2.0 | Multipart form-data handling for Document OCR Uploads |
| `bcrypt` | `4.1.2` | Apache-2.0 | Cryptographic Password Hashing with Dynamic Salt |
| `httpx` | `0.27.0` | BSD-3-Clause | Outbound HTTP Client for LLM Orchestration & Tests |
| `python-pptx` | `1.0.2` | MIT | Programmatic Pitch Deck Slide Generator |
| `pillow` | `12.1.1` | HPND | Image Processing for OCR Ingestion & Presentation Slides |
| `xlsxwriter` | `3.2.9` | BSD-2-Clause | Excel Export & Amortization Schedule Serialization |

---

## 2. Testing & Quality Assurance Dependencies

| Package Name | Installed Version | License | Architectural Function |
| :--- | :---: | :---: | :--- |
| `pytest` | `9.1.1` | MIT | Automated Regression & Unit Testing Engine |
| `anyio` | `4.12.1` | MIT | Asynchronous Event Loop Testing Harness |
| `selenium` | `4.18.1` | Apache-2.0 | End-to-End Headless Browser Automation & Smoke Testing |
