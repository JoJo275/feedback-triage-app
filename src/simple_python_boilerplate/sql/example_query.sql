-- =============================================================================
-- Example query: Get user by ID
-- =============================================================================
-- TODO (template users): Replace with your actual queries or delete this file.
--
-- Usage in Python:
--   from importlib.resources import files
--   query = files("simple_python_boilerplate.sql").joinpath("example_query.sql").read_text()
--   cursor.execute(query, {"user_id": 42})
-- =============================================================================

SELECT id, name, email, is_active, created_at, updated_at
FROM users
WHERE id = :user_id;
