-- Migration: 001_initial_schema.sql
-- Description: Creates initial relational schema for SME Finance Copilot
-- Precision: All monetary fields stored in minor integer units (e.g. Poisha/Cents)

-- 1. Identity & Business Structure
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    registration_number VARCHAR(100),
    tax_id VARCHAR(100),
    business_type VARCHAR(100) NOT NULL DEFAULT 'grocery',
    currency VARCHAR(10) NOT NULL DEFAULT 'BDT',
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    branch_code VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT 1,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_shops_business_active ON shops(business_id, is_active);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS business_memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER REFERENCES shops(id) ON DELETE CASCADE,
    role_code VARCHAR(50) NOT NULL DEFAULT 'staff',
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_membership_user_business_shop ON business_memberships(user_id, business_id, shop_id);

-- 2. Suppliers and Customers
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    payment_terms_days INTEGER NOT NULL DEFAULT 30,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_suppliers_shop_name ON suppliers(shop_id, name);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    credit_limit_minor BIGINT NOT NULL DEFAULT 0,
    balance_minor BIGINT NOT NULL DEFAULT 0,
    segment VARCHAR(50) NOT NULL DEFAULT 'regular',
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_customers_shop_phone ON customers(shop_id, phone);

-- 3. Products and Inventory
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    barcode VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL DEFAULT 'pcs',
    cost_price_minor BIGINT NOT NULL,
    selling_price_minor BIGINT NOT NULL,
    current_stock INTEGER NOT NULL DEFAULT 0,
    min_stock_alert INTEGER NOT NULL DEFAULT 5,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_products_shop_sku ON products(shop_id, sku);
CREATE INDEX IF NOT EXISTS idx_products_shop_category ON products(shop_id, category);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    order_number VARCHAR(100) NOT NULL,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expected_date TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    total_amount_minor BIGINT NOT NULL DEFAULT 0,
    notes TEXT,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    movement_type VARCHAR(50) NOT NULL,
    reference_type VARCHAR(50),
    reference_id INTEGER,
    quantity_change INTEGER NOT NULL,
    resulting_stock INTEGER NOT NULL,
    unit_cost_minor BIGINT NOT NULL,
    movement_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_inv_movements_shop_product_date ON inventory_movements(shop_id, product_id, movement_date);

CREATE TABLE IF NOT EXISTS stock_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    reason VARCHAR(50) NOT NULL,
    quantity_adjusted INTEGER NOT NULL,
    cost_impact_minor BIGINT NOT NULL DEFAULT 0,
    adjusted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    adjustment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Documents & Intelligence Pre-Declarations
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    stored_path VARCHAR(500) NOT NULL,
    file_hash_sha256 VARCHAR(64) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    detected_language VARCHAR(50) NOT NULL DEFAULT 'en',
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_docs_shop_hash ON documents(shop_id, file_hash_sha256);

CREATE TABLE IF NOT EXISTS document_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL DEFAULT 1,
    image_path VARCHAR(500) NOT NULL,
    width_px INTEGER,
    height_px INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    predicted_doc_type VARCHAR(50) NOT NULL,
    confidence_score REAL NOT NULL,
    classifier_model_version VARCHAR(100) NOT NULL DEFAULT 'rule_tfidf_v1',
    raw_predictions_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_extractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    raw_ocr_text TEXT,
    raw_ocr_blocks_json TEXT,
    structured_data_json TEXT,
    normalized_data_json TEXT,
    field_confidences_json TEXT,
    validation_errors_json TEXT,
    extraction_model_version VARCHAR(100) NOT NULL DEFAULT 'rapidocr_pipeline_v1',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    reviewer_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    original_values_json TEXT,
    corrected_values_json TEXT,
    decision_notes TEXT,
    reviewed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_processing_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    job_status VARCHAR(50) NOT NULL DEFAULT 'queued',
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    idempotent_token VARCHAR(100) NOT NULL UNIQUE,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 5. Financial Records: Sales, Purchases, Expenses, Payments, Receivables, Cash Movements
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    invoice_number VARCHAR(100) NOT NULL,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    sale_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    subtotal_minor BIGINT NOT NULL DEFAULT 0,
    discount_minor BIGINT NOT NULL DEFAULT 0,
    tax_minor BIGINT NOT NULL DEFAULT 0,
    total_amount_minor BIGINT NOT NULL DEFAULT 0,
    paid_amount_minor BIGINT NOT NULL DEFAULT 0,
    payment_status VARCHAR(50) NOT NULL DEFAULT 'paid',
    payment_method VARCHAR(50) NOT NULL DEFAULT 'cash',
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    notes TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sales_shop_date ON sales(shop_id, sale_date);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sales_shop_invoice ON sales(shop_id, invoice_number);

CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    item_description VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price_minor BIGINT NOT NULL,
    discount_minor BIGINT NOT NULL DEFAULT 0,
    line_total_minor BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    purchase_order_id INTEGER REFERENCES purchase_orders(id) ON DELETE SET NULL,
    invoice_number VARCHAR(100) NOT NULL,
    purchase_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    subtotal_minor BIGINT NOT NULL DEFAULT 0,
    tax_minor BIGINT NOT NULL DEFAULT 0,
    shipping_minor BIGINT NOT NULL DEFAULT 0,
    total_amount_minor BIGINT NOT NULL DEFAULT 0,
    paid_amount_minor BIGINT NOT NULL DEFAULT 0,
    payment_status VARCHAR(50) NOT NULL DEFAULT 'paid',
    payment_method VARCHAR(50) NOT NULL DEFAULT 'bank_transfer',
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    notes TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_purchases_shop_date ON purchases(shop_id, purchase_date);

CREATE TABLE IF NOT EXISTS purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    item_description VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_cost_minor BIGINT NOT NULL,
    line_total_minor BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_purchase_items_purchase ON purchase_items(purchase_id);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    expense_category VARCHAR(100) NOT NULL,
    expense_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount_minor BIGINT NOT NULL,
    payment_method VARCHAR(50) NOT NULL DEFAULT 'cash',
    payee VARCHAR(255),
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    description TEXT,
    approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_expenses_shop_date ON expenses(shop_id, expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(shop_id, expense_category);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    payment_type VARCHAR(50) NOT NULL,
    reference_type VARCHAR(50),
    reference_id INTEGER,
    payment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount_minor BIGINT NOT NULL,
    payment_method VARCHAR(50) NOT NULL DEFAULT 'cash',
    notes TEXT,
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_payments_shop_date ON payments(shop_id, payment_date);

CREATE TABLE IF NOT EXISTS receivables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    due_date TIMESTAMP NOT NULL,
    total_amount_minor BIGINT NOT NULL,
    outstanding_amount_minor BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_receivables_shop_status_due ON receivables(shop_id, status, due_date);

CREATE TABLE IF NOT EXISTS cash_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    movement_type VARCHAR(50) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_id INTEGER,
    amount_minor BIGINT NOT NULL,
    running_balance_minor BIGINT NOT NULL,
    movement_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cash_movements_shop_date ON cash_movements(shop_id, movement_date);

-- 6. Loans and Financial Planning (Demo Banks)
CREATE TABLE IF NOT EXISTS demo_banks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    contact_info TEXT,
    is_synthetic BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id INTEGER NOT NULL REFERENCES demo_banks(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    min_amount_minor BIGINT NOT NULL,
    max_amount_minor BIGINT NOT NULL,
    min_tenure_months INTEGER NOT NULL,
    max_tenure_months INTEGER NOT NULL,
    annual_interest_rate_bps INTEGER NOT NULL,
    interest_calc_type VARCHAR(50) NOT NULL DEFAULT 'reducing_balance',
    processing_fee_bps INTEGER NOT NULL DEFAULT 100,
    eligibility_criteria_json TEXT,
    is_synthetic BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES loan_products(id) ON DELETE CASCADE,
    rule_name VARCHAR(100) NOT NULL,
    rule_condition_json TEXT NOT NULL,
    min_credit_score INTEGER NOT NULL DEFAULT 600,
    max_dscr_threshold REAL NOT NULL DEFAULT 1.25,
    is_synthetic BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES loan_products(id) ON DELETE CASCADE,
    requested_amount_minor BIGINT NOT NULL,
    tenure_months INTEGER NOT NULL,
    calculated_emi_minor BIGINT NOT NULL,
    total_interest_minor BIGINT NOT NULL,
    total_payment_minor BIGINT NOT NULL,
    dscr_ratio REAL NOT NULL,
    recommendation_status VARCHAR(50) NOT NULL,
    rationale TEXT,
    is_synthetic BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    bank_id INTEGER NOT NULL REFERENCES demo_banks(id) ON DELETE RESTRICT,
    product_id INTEGER NOT NULL REFERENCES loan_products(id) ON DELETE RESTRICT,
    applicant_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    application_number VARCHAR(100) NOT NULL UNIQUE,
    requested_amount_minor BIGINT NOT NULL,
    approved_amount_minor BIGINT NOT NULL DEFAULT 0,
    tenure_months INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    evaluation_notes TEXT,
    is_synthetic BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. AI, Automation, and Evaluation
CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    domain VARCHAR(50) NOT NULL,
    record_count INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT,
    is_synthetic BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    architecture_description TEXT NOT NULL,
    feature_schema_json TEXT,
    hyperparameters_json TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_model_versions_task ON model_versions(task_name);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_version_id INTEGER NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    run_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metrics_json TEXT NOT NULL,
    parameters_json TEXT,
    notes TEXT,
    is_synthetic_benchmark BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    target_metric VARCHAR(50) NOT NULL,
    forecast_date_start TIMESTAMP NOT NULL,
    forecast_date_end TIMESTAMP NOT NULL,
    model_version_id INTEGER REFERENCES model_versions(id) ON DELETE SET NULL,
    predictions_json TEXT NOT NULL,
    lower_bound_json TEXT,
    upper_bound_json TEXT,
    is_synthetic BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_forecasts_shop_metric ON forecasts(shop_id, target_metric);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    action_payload_json TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS automated_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,
    schedule_cron VARCHAR(50) NOT NULL DEFAULT '0 0 * * *',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    config_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    requested_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    approver_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acted_at TIMESTAMP,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER REFERENCES shops(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL DEFAULT 'info',
    is_read BOOLEAN NOT NULL DEFAULT 0,
    metadata_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_version_id INTEGER NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    input_hash VARCHAR(64) NOT NULL,
    input_payload_json TEXT NOT NULL,
    output_payload_json TEXT NOT NULL,
    latency_ms REAL NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_predictions_hash ON predictions(input_hash);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER REFERENCES shops(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    old_values_json TEXT,
    new_values_json TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_shop_action ON audit_logs(shop_id, action, created_at);
