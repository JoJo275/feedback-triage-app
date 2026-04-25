# Database Seeds

<!-- TODO (template users): Replace seed file examples with your actual
     domain tables. Update naming conventions if you prefer timestamps. -->

Seed files for populating the database with initial or test data.

## Purpose

Seeds provide repeatable baseline data for:

- **Development** — Realistic sample data for local testing
- **CI** — Known fixtures for integration tests
- **Demos** — Data for showcasing features

## Naming Convention

```text
001_seed_users.sql          # Sequential (default)
002_seed_categories.sql
```

## Usage

```bash
# Apply seeds to development database
sqlite3 var/app.sqlite3 < db/seeds/001_example_seed.sql

# Apply all seeds in order
for f in db/seeds/*.sql; do sqlite3 var/app.sqlite3 < "$f"; done
```

## Guidelines

- Seeds should be **idempotent** — safe to run multiple times (`INSERT OR IGNORE`)
- Keep seeds **small** — enough data to be useful, not a full dataset
- Include **referential data first** (e.g., roles before users)
- Use **sequential numbering** to control execution order
- Never put production/real data in seed files

## See Also

- [db/schema.sql](../schema.sql) — Schema that seeds depend on
- [db/migrations/](../migrations/) — Schema changes applied before seeds
- [001_example_seed.sql](001_example_seed.sql) — Example seed file
