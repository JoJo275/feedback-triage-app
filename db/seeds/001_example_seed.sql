-- =============================================================================
-- Seed 001: Example seed data
-- =============================================================================
-- Populates the database with initial/development data.
--
-- Usage:
--   sqlite3 var/app.sqlite3 < db/seeds/001_example_seed.sql
--
-- Guidelines:
--   - Seeds should be idempotent (safe to run multiple times)
--   - Use INSERT OR IGNORE / INSERT OR REPLACE for idempotency
--   - Keep production seeds separate from dev/test seeds
--   - Number seeds in the order they should be applied
--
-- TODO (template users): Replace the example data below with your actual
--   seed data, or delete this file if you don't need seed data.
-- =============================================================================

-- ── Example: Seed users ──────────────────────────────────────
INSERT OR IGNORE INTO users (name, email) VALUES
    ('Alice Admin', 'alice@example.com'),
    ('Bob Builder', 'bob@example.com'),
    ('Carol Contributor', 'carol@example.com');
