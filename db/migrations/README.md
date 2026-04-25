# Database Migrations

<!-- TODO (template users): Choose a naming convention (sequential or
     timestamp) and stick with it. Delete the example migration and add
     your own. Update this README if you adopt a migration framework. -->

Schema migration files for version-controlled database changes.

## Naming Convention

**Sequential (default for solo/small teams):**

```text
001_create_users_table.sql
002_add_email_to_users.sql
```

**Timestamp (recommended for teams/parallel branches):**

```text
20260204143052_create_users_table.sql
20260204151030_add_email_to_users.sql
```

> **Tip:** Use timestamps (`YYYYMMDDHHMMSS_`) when multiple developers may
> create migrations on separate branches to avoid merge conflicts.

## Writing Migrations

Each migration file should:

1. Be **idempotent** when possible (use `IF NOT EXISTS`, `IF EXISTS`)
2. Include both the **change** and a comment describing the purpose
3. Be ordered so they can be applied sequentially from a clean schema
4. Never modify a previously-applied migration — create a new one instead

## Usage

```bash
# Apply a single migration
sqlite3 var/app.sqlite3 < db/migrations/001_create_users_table.sql

# Apply all migrations in order
for f in db/migrations/*.sql; do sqlite3 var/app.sqlite3 < "$f"; done
```

## See Also

- [db/schema.sql](../schema.sql) — Canonical schema (should match all migrations applied)
- [db/seeds/](../seeds/) — Seed data (applied after migrations)
- [001_example_migration.sql](001_example_migration.sql) — Example migration
- [ADR 027](../../docs/adr/027-database-strategy.md) — Raw SQL database strategy
