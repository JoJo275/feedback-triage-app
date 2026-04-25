# ADR 027: Raw SQL Database Strategy

## Status

Accepted

## Context

Most Python projects that need persistence choose between an ORM (SQLAlchemy,
Django ORM, Peewee) and raw SQL. This template needs a lightweight, opinioned
database scaffolding that works for any project size and doesn't couple the
template to a specific ORM or database engine.

Key constraints:

- This is a **template** — the database layer must be easy to adopt, replace,
  or remove entirely (`--strip db` in `customize.py`)
- Template users may target SQLite, PostgreSQL, MySQL, or others
- Schema changes must be version-controlled and reviewable in PRs
- No runtime dependency on heavy ORM libraries
- Integration tests need a repeatable way to set up test databases

## Decision

Use **raw SQL files** organized in a `db/` directory at the project root.
No ORM is included by default.

### Directory structure

```
db/
├── schema.sql        # Complete, current schema — the canonical reference
├── migrations/       # Numbered incremental changes (001_, 002_, …)
│   └── 001_example_migration.sql
├── queries/          # Reusable parameterised queries
│   └── example_queries.sql
└── seeds/            # Test/development data
    └── 001_example_seed.sql
```

### Conventions

- **`schema.sql`** is the single source of truth for the current database
  shape. It should always be runnable against an empty database to produce
  the full schema.
- **Migrations** are numbered sequentially (`001_`, `002_`, …) and contain
  forward-only DDL. Each migration should be idempotent where possible
  (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE … ADD COLUMN IF NOT EXISTS`).
- **Seeds** are numbered and provide test/development data. They should be
  re-runnable without duplicating data (`INSERT OR IGNORE`, `ON CONFLICT DO
NOTHING`).
- **Queries** store reusable SQL with parameter placeholders. The template
  doesn't mandate a particular parameter style — use whatever your driver
  expects (`?` for sqlite3, `%s` for psycopg2, etc.).

### Database engine

The template defaults to **SQLite** for zero-setup local development (see
`var/app.example.sqlite3`). Template users are expected to swap this for
their production engine.

## Alternatives Considered

### SQLAlchemy ORM

Full-featured Python ORM with schema definition via Python classes.

**Rejected because:** Heavy dependency for a template; coupling the scaffolding
to SQLAlchemy forces a specific abstraction on all template users. Those who
want it can add it themselves.

### Alembic migrations

SQL migration tool that integrates with SQLAlchemy for auto-generated
migrations.

**Rejected because:** Requires SQLAlchemy as a dependency; adds complexity
that most small-to-medium projects don't need on day one.

### Django ORM

Powerful ORM with built-in migrations.

**Rejected because:** Requires adopting the Django framework; inappropriate for
a generic Python template.

### No database scaffolding

Skip `db/` entirely and let users add their own.

**Rejected because:** Having a conventional directory structure and example
files gives users a starting point and establishes patterns. The `--strip db`
flag in `customize.py` makes removal trivial for users who don't need it.

## Consequences

### Positive

- Zero runtime dependencies — no ORM, no migration framework to install
- Database-engine agnostic — SQL files work with any engine
- Fully reviewable — schema changes are plain-text diffs in PRs
- Easy to remove — `customize.py --strip db` deletes the entire directory
- Low learning curve — SQL is the universal database language

### Negative

- No auto-generated migrations — schema changes must be written by hand
- No Python-level schema validation — type mismatches caught at runtime, not
  by a type checker
- No query builder — complex dynamic queries must be assembled manually

### Mitigations

- The `schema.sql` file serves as a always-runnable reference, reducing
  migration drift
- Integration tests under `tests/integration/sql/` validate SQL files against
  a real database
- Template users who need an ORM can add one and treat `db/` as a migration
  history archive

## Implementation

- [db/schema.sql](../../db/schema.sql) — Canonical schema definition
- [db/migrations/](../../db/migrations/) — Numbered migration files
- [db/queries/](../../db/queries/) — Reusable SQL queries
- [db/seeds/](../../db/seeds/) — Seed data for dev/test
- [var/app.example.sqlite3](../../var/app.example.sqlite3) — Example SQLite database
- [tests/integration/sql/](../../tests/integration/sql/) — SQL integration tests
- [scripts/sql/](../../scripts/sql/) — SQL-related utility scripts

## References

- [db/README.md](../../db/README.md) — Database directory documentation
- [ADR 014](014-no-template-engine.md) — No template engine (related: manual
  customisation philosophy)
