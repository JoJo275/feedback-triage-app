-- =============================================================================
-- Teardown test database
-- =============================================================================
-- Drops all test tables and indexes after integration tests.
-- Run after integration tests to leave a clean state.
--
-- Note: For in-memory databases (sqlite3.connect(":memory:")) or tmp_path
-- databases, teardown happens automatically when the connection closes.
-- This file is most useful for persistent test databases (var/test.sqlite3).
--
-- Usage:
--   sqlite3 var/test.sqlite3 < tests/integration/sql/teardown_test_db.sql
--
-- TODO (template users): Update this to match your actual test schema.
--   Every table/index created in setup_test_db.sql should be dropped here.
--   Drop tables in reverse dependency order (children before parents) to
--   avoid foreign key constraint violations.
-- =============================================================================

-- ── Drop indexes (before tables) ─────────────────────────────
DROP INDEX IF EXISTS idx_users_email;
DROP INDEX IF EXISTS idx_users_is_active;

-- ── Drop tables (reverse dependency order) ───────────────────
-- TODO (template users): Add your tables here in reverse dependency order.
--   Tables with foreign keys pointing to other tables should be dropped first.
DROP TABLE IF EXISTS users;

-- ── Reset sequences (optional) ───────────────────────────────
-- SQLite auto-resets AUTOINCREMENT on table drop, but if you use
-- sqlite_sequence explicitly, clean it up:
-- DELETE FROM sqlite_sequence WHERE name = 'users';

-- ── Verify clean state ───────────────────────────────────────
-- After teardown, no application tables should remain.
-- .tables
