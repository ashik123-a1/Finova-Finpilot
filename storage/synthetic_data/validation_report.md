# SME Finance Copilot — Dataset Validation & Integrity Audit Report
**Audit Timestamp:** 2026-10-18T03:13:31.730630+00:00  
**Overall Audit Status:** `PASS`  
**Total Database Records Audited:** **17,428**  

## 1. Table Record Distribution

| Database Table           |   Record Count |
|--------------------------|----------------|
| approvals                |              0 |
| audit_logs               |             27 |
| automated_tasks          |              0 |
| business_memberships     |             27 |
| businesses               |             18 |
| cash_movements           |          9,720 |
| customers                |          1,620 |
| datasets                 |              0 |
| demo_banks               |              4 |
| document_classifications |              0 |
| document_extractions     |              0 |
| document_pages           |              0 |
| document_processing_jobs |              0 |
| document_reviews         |              0 |
| documents                |              0 |
| evaluation_runs          |              0 |
| expenses                 |            270 |
| forecasts                |             27 |
| inventory_movements      |          1,449 |
| loan_applications        |              0 |
| loan_products            |             16 |
| loan_rules               |              0 |
| loan_scenarios           |             81 |
| model_versions           |              0 |
| notifications            |              0 |
| payments                 |              0 |
| permissions              |              0 |
| predictions              |              0 |
| products                 |          1,080 |
| purchase_items           |            471 |
| purchase_orders          |              0 |
| purchases                |            135 |
| receivables              |             70 |
| recommendations          |             27 |
| role_permissions         |              0 |
| roles                    |              0 |
| sale_items               |            978 |
| sales                    |            540 |
| schema_migrations        |              1 |
| shops                    |             27 |
| stock_adjustments        |            540 |
| suppliers                |            270 |
| users                    |             30 |

## 2. Referential Integrity & Foreign Key Audit
> [!NOTE]
> Foreign key integrity verification passed with **0 violations**.

## 3. Financial Mathematical Consistency
> [!NOTE]
> 100% of checked Sales and Purchase transactions balance with line item totals.

## 4. Scenario Coverage Across SME Sectors
| Industry Sector   |   Active Businesses |
|-------------------|---------------------|
| clothing          |                   2 |
| electronics       |                   2 |
| grocery           |                   2 |
| manufacturing     |                   2 |
| online_seller     |                   2 |
| pharmacy          |                   2 |
| restaurant        |                   2 |
| service           |                   2 |
| wholesale         |                   2 |
