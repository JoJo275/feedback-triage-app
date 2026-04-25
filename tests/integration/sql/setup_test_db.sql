-- =============================================================================
-- Setup test database schema
-- =============================================================================
-- Creates test tables in a fresh SQLite database and seeds baseline test data.
-- Run before integration tests.
--
-- Usage:
--   sqlite3 :memory: < tests/integration/sql/setup_test_db.sql
--   sqlite3 var/test.sqlite3 < tests/integration/sql/setup_test_db.sql
--
-- This file intentionally duplicates db/schema.sql rather than sourcing it,
-- because `.read` is a SQLite CLI command and won't work from application
-- code (e.g., Python's sqlite3.executescript()). Keep both in sync.
--
-- TODO (template users): Replace the example tables below with your actual
--   test schema. Keep this in sync with db/schema.sql.
-- =============================================================================

-- ── Pragmas ──────────────────────────────────────────────────
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;

-- ── Tables ───────────────────────────────────────────────────
-- Must match db/schema.sql. If you change the schema, update both files.
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    email      TEXT    NOT NULL UNIQUE,
    is_active  INTEGER NOT NULL DEFAULT 1,  -- 0 = inactive, 1 = active
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- ── Indexes ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_email     ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- ── Seed test data ───────────────────────────────────────────
-- Includes a mix of active and inactive users for testing filter queries.
-- Uses fixed timestamps so assertions can rely on deterministic ordering.
INSERT OR IGNORE INTO users (id, name, email, is_active, created_at, updated_at) VALUES
    (1, 'Alice Admin',       'alice@example.com',   1, '2026-01-01T00:00:00.000Z', '2026-01-01T00:00:00.000Z'),
    (2, 'Bob Builder',       'bob@example.com',     1, '2026-01-02T00:00:00.000Z', '2026-01-02T00:00:00.000Z'),
    (3, 'Carol Contributor', 'carol@example.com',   1, '2026-01-03T00:00:00.000Z', '2026-01-03T00:00:00.000Z'),
    (4, 'Dave Deactivated',  'dave@example.com',    0, '2026-01-04T00:00:00.000Z', '2026-02-01T00:00:00.000Z');

-- ── Verify ───────────────────────────────────────────────────
-- Quick sanity check: should return 4 rows.
-- SELECT COUNT(*) AS user_count FROM users;
