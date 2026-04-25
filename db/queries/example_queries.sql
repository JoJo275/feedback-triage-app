-- =============================================================================
-- Example Reusable Queries
-- =============================================================================
-- Named, reusable SQL queries for application use.
--
-- These can be loaded by the application at startup (e.g., using aiosql,
-- yesql, or a simple file reader) and called by name.
--
-- Naming convention: use -- name: <query_name> comments if using a query
-- loader library, or just organize by section for manual use.
--
-- TODO (template users): Replace these examples with your actual queries
--   or delete this file. Organize into subdirectories by domain if the
--   query count grows (e.g., queries/users/, queries/reports/).
-- =============================================================================

-- ── List queries ─────────────────────────────────────────────

-- name: get_all_users
-- Get all active users, most recent first
SELECT id, name, email, created_at
FROM users
WHERE is_active = 1
ORDER BY created_at DESC;

-- name: get_all_users_paginated
-- Paginated user listing (pass :limit and :offset)
SELECT id, name, email, created_at
FROM users
WHERE is_active = 1
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset;

-- ── Lookup queries ───────────────────────────────────────────

-- name: get_user_by_id
SELECT id, name, email, is_active, created_at, updated_at
FROM users
WHERE id = :user_id;

-- name: get_user_by_email
SELECT id, name, email, is_active, created_at, updated_at
FROM users
WHERE email = :email;

-- ── Search queries ───────────────────────────────────────────

-- name: search_users_by_name
-- Case-insensitive prefix search
SELECT id, name, email, created_at
FROM users
WHERE name LIKE :search || '%'
ORDER BY name;

-- ── Count / Aggregate queries ────────────────────────────────

-- name: count_active_users
SELECT COUNT(*) AS active_count FROM users WHERE is_active = 1;

-- name: count_all_users
SELECT COUNT(*) AS total_count FROM users;

-- ── Write queries ────────────────────────────────────────────
-- TODO (template users): Adapt INSERT/UPDATE/DELETE queries to your schema.

-- name: create_user!
-- Insert a new user. Returns the new row via RETURNING (SQLite 3.35+).
INSERT INTO users (name, email)
VALUES (:name, :email)
RETURNING id, name, email, created_at;

-- name: update_user!
-- Update a user's name and email. Bumps updated_at.
UPDATE users
SET name       = :name,
    email      = :email,
    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE id = :user_id
RETURNING id, name, email, updated_at;

-- name: deactivate_user!
-- Soft-delete: mark a user inactive rather than removing the row.
UPDATE users
SET is_active  = 0,
    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE id = :user_id;

-- name: delete_user!
-- Hard-delete: permanently remove a user row.
-- Prefer deactivate_user! for audit-trail-friendly workflows.
DELETE FROM users WHERE id = :user_id;
