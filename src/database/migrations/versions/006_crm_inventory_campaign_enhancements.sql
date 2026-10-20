-- Migration 006: CRM Customer Enhancements, Communications, Discount Campaigns, and Purchase Order Items
-- Provides relational backing for CRM workflows, omni-channel reminder tracking, discount campaigns, and PO line items.

-- 1. Enhance Customers table with contact & preferences
ALTER TABLE customers ADD COLUMN whatsapp_number VARCHAR(50);
ALTER TABLE customers ADD COLUMN telegram_handle VARCHAR(100);
ALTER TABLE customers ADD COLUMN customer_type VARCHAR(50) DEFAULT 'retail';
ALTER TABLE customers ADD COLUMN opening_balance_minor BIGINT DEFAULT 0;
ALTER TABLE customers ADD COLUMN messaging_consent BOOLEAN DEFAULT 1;
ALTER TABLE customers ADD COLUMN notes TEXT;

-- 2. Customer Communications Log
CREATE TABLE IF NOT EXISTS customer_communications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL, -- whatsapp, sms, telegram, manual_copy
    recipient_contact VARCHAR(100) NOT NULL,
    message_body TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL DEFAULT 'due_reminder', -- due_reminder, vip_discount, payment_receipt, custom
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, awaiting_user_action, queued, provider_accepted, delivered, failed, cancelled
    provider_message_id VARCHAR(255),
    error_message TEXT,
    sent_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cust_comm_shop_customer ON customer_communications(shop_id, customer_id);
CREATE INDEX IF NOT EXISTS idx_cust_comm_created ON customer_communications(created_at);

-- 3. Discount & VIP Offer Campaigns
CREATE TABLE IF NOT EXISTS discount_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_segment VARCHAR(50) NOT NULL DEFAULT 'all', -- vip, regular, at_risk, all, single_customer
    target_customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    discount_type VARCHAR(50) NOT NULL DEFAULT 'percentage', -- percentage, fixed_amount
    discount_value FLOAT NOT NULL,
    min_purchase_amount_minor BIGINT DEFAULT 0,
    eligible_category VARCHAR(100),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    channel VARCHAR(50) NOT NULL DEFAULT 'whatsapp',
    message_template TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, active, completed, cancelled
    recipient_count INTEGER DEFAULT 0,
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_discount_campaigns_shop ON discount_campaigns(shop_id, status);

-- 4. Purchase Order Items
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    item_description VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_cost_minor BIGINT NOT NULL,
    line_total_minor BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_po_items_po_id ON purchase_order_items(purchase_order_id);
