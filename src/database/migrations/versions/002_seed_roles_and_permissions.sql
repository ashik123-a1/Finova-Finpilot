-- Migration 002: Seed Core Roles, Permissions, and RBAC Mappings
-- SME Finance Copilot Master Security Architecture (Part 3.1 & 3.3)

-- 1. Insert 7 Canonical Roles
INSERT OR IGNORE INTO roles (code, name, description) VALUES
('super_admin', 'Platform Super Admin', 'Platform-level settings, administration, security monitoring, and operational support.'),
('owner', 'Business Owner', 'Full workspace ownership, business profile, financing decisions, team management, and financial control.'),
('manager', 'Business Admin / Manager', 'Operational branch management, shop settings, day-to-day workflow supervision, and operational approvals.'),
('accountant', 'Accountant / Finance Staff', 'Ledger reconciliation, transaction management, invoice OCR reviews, P&L reporting, and tax summaries.'),
('sales', 'Sales / CRM Staff', 'Customer follow-ups, POS sales entries, payment reminder drafts, and customer relationship management.'),
('inventory', 'Inventory / Operations Staff', 'Stock level management, product catalog maintenance, goods receipt, and supplier shipment tracking.'),
('auditor', 'Read-only Advisor / Auditor', 'Read-only inspection of financial statements, audit logs, model explainability, and regulatory reports.');

-- 2. Insert 22 Granular Permissions
INSERT OR IGNORE INTO permissions (code, description) VALUES
('business.view', 'View business profile, shop locations, and operational metadata'),
('business.edit', 'Edit business profile, fiscal settings, and shop configurations'),
('finance.view', 'View financial ledgers, income statements, P&L, and balance sheets'),
('finance.create', 'Create sales, expenses, and general ledger journal entries'),
('finance.edit', 'Edit and adjust recorded financial transactions'),
('finance.delete', 'Reverse, void, or delete financial transactions with audit reason'),
('document.upload', 'Upload commercial documents, invoices, receipts, and fapiaos'),
('document.review', 'Review and correct automated OCR and classification extractions'),
('document.post', 'Confirm and post human-reviewed document line items to financial ledger'),
('forecast.view', 'View cash flow forecasts, runway projections, and uncertainty bands'),
('loan.compare', 'Explore and compare institutional SME loan and microfinance products'),
('loan.risk_assess', 'Evaluate DSCR, repayment capacity, and credit risk suitability'),
('crm.manage', 'Manage customer directory, RFM segmentations, and payment follow-ups'),
('inventory.manage', 'Manage product SKUs, reorder thresholds, and inventory aging analysis'),
('team.invite', 'Issue email and workspace invitations to new team members'),
('team.remove', 'Revoke team memberships and de-provision user access'),
('team.roles', 'Assign and reconfigure staff role permissions and shop memberships'),
('integration.manage', 'Configure external accounting, ERP, POS, or banking integrations'),
('data.export', 'Export financial, inventory, tax, and audit report datasets'),
('audit.view', 'View immutable audit trails, access logs, and model decision telemetry'),
('system.execute', 'Execute sensitive platform workflows and automated business operations'),
('admin.access', 'Access platform super-admin portal and system configuration');

-- 3. Map Roles to Permissions in role_permissions table
-- Platform Super Admin
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.code = 'super_admin' AND p.code IN (
    'business.view', 'business.edit', 'finance.view', 'forecast.view',
    'loan.compare', 'loan.risk_assess', 'team.invite', 'team.remove',
    'team.roles', 'integration.manage', 'data.export', 'audit.view',
    'system.execute', 'admin.access'
);

-- Business Owner (All permissions except platform admin.access)
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.code = 'owner' AND p.code IN (
    'business.view', 'business.edit', 'finance.view', 'finance.create',
    'finance.edit', 'finance.delete', 'document.upload', 'document.review',
    'document.post', 'forecast.view', 'loan.compare', 'loan.risk_assess',
    'crm.manage', 'inventory.manage', 'team.invite', 'team.remove',
    'team.roles', 'integration.manage', 'data.export', 'audit.view',
    'system.execute'
);

-- Business Manager
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.code = 'manager' AND p.code IN (
    'business.view', 'business.edit', 'finance.view', 'finance.create',
    'finance.edit', 'document.upload', 'document.review', 'document.post',
    'forecast.view', 'loan.compare', 'loan.risk_assess', 'crm.manage',
    'inventory.manage', 'team.invite', 'data.export', 'audit.view'
);

-- Accountant / Finance Staff
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.code = 'accountant' AND p.code IN (
    'business.view', 'finance.view', 'finance.create', 'finance.edit',
    'document.upload', 'document.review', 'document.post', 'forecast.view',
    'loan.compare', 'loan.risk_assess', 'data.export', 'audit.view'
);

-- Sales / CRM Staff
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.code = 'sales' AND p.code IN (
    'business.view', 'finance.create', 'document.upload', 'crm.manage',
    'data.export'
);

-- Inventory / Operations Staff
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.code = 'inventory' AND p.code IN (
    'business.view', 'document.upload', 'inventory.manage', 'data.export'
);

-- Read-only Advisor / Auditor
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.code = 'auditor' AND p.code IN (
    'business.view', 'finance.view', 'document.review', 'forecast.view',
    'loan.compare', 'loan.risk_assess', 'data.export', 'audit.view'
);
