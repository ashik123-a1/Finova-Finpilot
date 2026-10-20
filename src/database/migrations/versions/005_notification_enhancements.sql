-- Migration 005: Notification Enhancements & Audit Schema
-- Adds severity, action_url, read_at, and dedup_key with query performance indexes.

ALTER TABLE notifications ADD COLUMN severity VARCHAR(50) DEFAULT 'info';
ALTER TABLE notifications ADD COLUMN action_url VARCHAR(255);
ALTER TABLE notifications ADD COLUMN read_at TIMESTAMP;
ALTER TABLE notifications ADD COLUMN dedup_key VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_user_created ON notifications(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_dedup ON notifications(dedup_key);
