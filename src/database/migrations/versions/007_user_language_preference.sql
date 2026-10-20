-- Migration 007: User language preference persistence
-- Adds preferred_language column to users table with safe fallback to English ('en')

ALTER TABLE users ADD COLUMN preferred_language VARCHAR(10) DEFAULT 'en';
