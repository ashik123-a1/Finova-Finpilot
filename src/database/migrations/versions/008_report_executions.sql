-- Migration 008: Report generation history and persistent metadata tracking
-- Enables auditable, tenant-isolated report execution logs and export tracking.

CREATE TABLE IF NOT EXISTS report_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_uuid VARCHAR(64) NOT NULL UNIQUE,
    report_type VARCHAR(100) NOT NULL,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER REFERENCES shops(id) ON DELETE CASCADE,
    requested_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    filters_json TEXT NOT NULL DEFAULT '{}',
    format VARCHAR(20) NOT NULL DEFAULT 'preview',
    file_path VARCHAR(500),
    file_size_bytes INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'completed',
    summary_metrics_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_biz_type ON report_executions(business_id, report_type);
CREATE INDEX IF NOT EXISTS idx_reports_uuid ON report_executions(report_uuid);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON report_executions(created_at);
