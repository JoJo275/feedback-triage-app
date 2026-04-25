# Database Queries

<!-- TODO (template users): Replace these examples with your real query
     organization. Delete placeholder files and add your own. -->

Reusable SQL query files for application use.

## Organization

Organize queries by domain or feature area:

- `users/` — User-related queries (CRUD, search, auth)
- `reports/` — Reporting and analytics queries
- `common.sql` — Shared utilities (pagination helpers, audit triggers)

## Naming Conventions

| Pattern               | Example                 | When to use                  |
| --------------------- | ----------------------- | ---------------------------- |
| `get_<entity>.sql`    | `get_user_by_id.sql`    | Single record lookup         |
| `list_<entities>.sql` | `list_active_users.sql` | Multiple record queries      |
| `search_<entity>.sql` | `search_products.sql`   | Full-text or filtered search |
| `count_<entity>.sql`  | `count_orders.sql`      | Aggregate counts             |
| `report_<name>.sql`   | `report_daily.sql`      | Reporting / analytics        |

## Usage

```bash
# Run a query against the dev database
sqlite3 var/app.sqlite3 < db/queries/example_queries.sql
```

```python
# Load at runtime (if using src/simple_python_boilerplate/sql/ instead)
from importlib.resources import files

query = files("simple_python_boilerplate.sql").joinpath("get_user.sql").read_text()
```

## Where Do Queries Go?

| Location                             | Use when                                   |
| ------------------------------------ | ------------------------------------------ |
| `db/queries/`                        | Standalone queries run by scripts or DBA   |
| `src/simple_python_boilerplate/sql/` | Queries shipped with the installed package |

## See Also

- [db/schema.sql](../schema.sql) — Canonical database schema
- [db/migrations/](../migrations/) — Schema change history
- [example_queries.sql](example_queries.sql) — Example query patterns
