# Ad-hoc SQL Scripts

<!-- TODO (template users): Update database path if not using var/app.sqlite3.
     Delete scratch.example.sql and add your own scripts as needed. -->

Scratch space for SQL experimentation and one-off scripts.

## Contents

| Script                                     | Description                    |
| ------------------------------------------ | ------------------------------ |
| [reset.sql](reset.sql)                     | Reset database (drop/recreate) |
| [scratch.example.sql](scratch.example.sql) | Template for ad-hoc queries    |

## Usage

```bash
# Run a script against the dev database
sqlite3 var/app.sqlite3 < scripts/sql/scratch.sql

# Reset the database (drops everything, re-applies schema)
sqlite3 var/app.sqlite3 < scripts/sql/reset.sql

# Interactive SQLite session
sqlite3 var/app.sqlite3
```

## Getting Started

```bash
# Copy the example scratch file to create your own
cp scripts/sql/scratch.example.sql scripts/sql/scratch.sql
# scratch.sql is gitignored — safe for personal experimentation
```

## Guidelines

- Scratch files (`scratch*.sql`) are **gitignored** — they won't be committed
- For reusable queries, use `db/queries/` instead
- For schema changes, create a migration in `db/migrations/`
- For test fixtures, use `tests/integration/sql/`

## See Also

- [db/](../../db/) — Schema, migrations, seeds, and reusable queries
- [tests/integration/sql/](../../tests/integration/sql/) — SQL test fixtures
- [var/](../../var/) — Runtime database files
