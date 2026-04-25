-- Database Reset Script
-- TODO (template users): Update with your actual tables and reset logic.
--
-- WARNING: This will delete all data! Use only in development.
--
-- Usage: sqlite3 var/app.sqlite3 < scripts/sql/reset.sql

-- Drop all tables (add your tables here)
DROP TABLE IF EXISTS users;

-- Recreate schema
.read db/schema.sql

-- Optionally reseed
.read db/seeds/001_example_seed.sql

-- Verify
.tables
