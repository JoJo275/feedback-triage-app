-- =============================================================================
-- Database Schema — Single Source of Truth
-- =============================================================================
-- This file defines the complete, current schema for the database.
-- It should be kept in sync with the cumulative effect of all migrations.
--
-- Usage:
--   sqlite3 var/app.sqlite3 < db/schema.sql          # Create fresh DB
--   sqlite3 :memory: < db/schema.sql                  # Validate in CI
--
-- Conventions:
--   - Table names: plural, snake_case (e.g., users, order_items)
--   - Column names: snake_case (e.g., created_at, user_id)
--   - Indexes: idx_<table>_<column(s)> (e.g., idx_users_email)
--   - Foreign keys: <singular_table>_id (e.g., user_id)
--
-- TODO (template users): Replace the example tables below with your actual
--   schema. Adjust SQLite pragmas to taste (WAL is recommended).
-- =============================================================================

-- ── SQLite Pragmas (recommended for SQLite projects) ─────────
PRAGMA journal_mode = WAL;           -- Write-Ahead Logging for concurrency
PRAGMA foreign_keys = ON;            -- Enforce FK constraints (off by default!)
PRAGMA busy_timeout = 5000;          -- Wait 5s on locked DB instead of failing
PRAGMA synchronous = NORMAL;         -- Good balance of safety vs speed with WAL

-- ── Example: Users table ─────────────────────────────────────
-- TODO (template users): Replace with your actual tables.
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    email      TEXT    NOT NULL UNIQUE,
    is_active  INTEGER NOT NULL DEFAULT 1,  -- 0 = inactive, 1 = active
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- ── Example: Indexes ─────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_email     ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- ── Schema version tracking (optional) ───────────────────────
-- Tracks which migrations have been applied.
-- TODO (template users): Uncomment if you want manual migration tracking.
-- CREATE TABLE IF NOT EXISTS schema_migrations (
--     version    TEXT    NOT NULL UNIQUE,
--     applied_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
-- );
