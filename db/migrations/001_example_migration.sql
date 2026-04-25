-- =============================================================================
-- Migration 001: Create initial schema
-- =============================================================================
-- Date:    2026-01-01
-- Author:  Template
--
-- Usage:
--   sqlite3 var/app.sqlite3 < db/migrations/001_example_migration.sql
--
-- TODO (template users): Replace the example migration below with your
--   actual initial schema, or delete this file and create your own.
--   Remember to keep db/schema.sql in sync with the cumulative effect
--   of all migrations.
-- =============================================================================

-- ── UP (apply) ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    email      TEXT    NOT NULL UNIQUE,
    is_active  INTEGER NOT NULL DEFAULT 1,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email     ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- ── DOWN (rollback) ──────────────────────────────────────────
-- Keep rollback SQL here for reference, even if you apply it manually.
--
-- DROP INDEX IF EXISTS idx_users_is_active;
-- DROP INDEX IF EXISTS idx_users_email;
-- DROP TABLE IF EXISTS users;
