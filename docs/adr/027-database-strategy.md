# ADR 027: Database Strategy — SQLModel + PostgreSQL + Alembic

## Status

Superseded by ADRs [046](046-postgres-enums-and-check-constraints.md),
[047](047-sqlmodel-over-sqlalchemy.md), [048](048-session-per-request.md),
[049](049-offset-pagination.md), [050](050-sync-db-driver-v1.md), and
[054](054-postgres-for-tests.md).

> **Note on this file:** the original (template-era) decision was that
> the template would ship a `db/` directory of **raw SQL files and no
> ORM**, deliberately staying database-engine agnostic. That posture
> doesn't fit `feedback-triage-app`, which has one concrete schema and
> targets PostgreSQL specifically. The historical context is preserved
> below because it explains the trade-offs we considered when picking
> a real ORM. The live decisions are split across six successor ADRs
> listed in the redirect table at the bottom.

---

## Original (template-era) Context

Most Python projects that need persistence choose between an ORM
(SQLAlchemy, Django ORM, Peewee) and raw SQL. The template needed a
lightweight, opinionated database scaffolding that worked for any
project size and didn't couple the template to a specific ORM or
database engine.

Constraints at template time:

- The repository was a template — the database layer had to be easy
  to adopt, replace, or remove entirely.
- Template users might target SQLite, PostgreSQL, MySQL, or others.
- Schema changes had to be version-controlled and reviewable in PRs.
- No runtime dependency on heavy ORM libraries.
- Integration tests needed a repeatable way to set up test databases.

## Original Decision

Use **raw SQL files** organised in a `db/` directory at the project
root. No ORM included by default.

### Original directory structure

```text
db/
├── schema.sql         # Complete, current schema — canonical reference
├── migrations/        # Numbered incremental changes (001_, 002_, …)
├── queries/           # Reusable parameterised queries
└── seeds/             # Test/development data
```

### Original conventions

- **`schema.sql`** was the single source of truth for the current
  database shape, runnable against an empty database.
- **Migrations** numbered sequentially, forward-only DDL, idempotent
  where possible (`CREATE TABLE IF NOT EXISTS`, etc.).
- **Seeds** numbered, re-runnable without duplicating data
  (`INSERT OR IGNORE`, `ON CONFLICT DO NOTHING`).
- **Queries** stored reusable SQL with parameter placeholders; the
  driver chose the parameter style (`?`, `%s`, etc.).
- **SQLite default** for zero-setup local development; users were
  expected to swap for their production engine.

## Original Alternatives Considered (still informative)

### SQLAlchemy ORM

Full-featured Python ORM with schema definition via Python classes.

**Rejected (at template time) because:** heavy dependency for a
template; coupling scaffolding to SQLAlchemy forced an abstraction on
all template users. Those who wanted it could add it themselves.

> **Post-fork:** SQLAlchemy 2.x is now the foundation, layered under
> SQLModel. See [ADR 047](047-sqlmodel-over-sqlalchemy.md).

### Alembic migrations

SQL migration tool that integrates with SQLAlchemy for auto-generated
migrations.

**Rejected (at template time) because:** required SQLAlchemy as a
dependency; added complexity most small-to-medium template users
didn't need on day one.

> **Post-fork:** Alembic is now the migration tool, with
> `compare_type=True` and `compare_server_default=True`. Every
> migration is hand-reviewed after autogenerate. See
> [ADR 053](053-migrations-as-pre-deploy-command.md).

### Django ORM

**Rejected because:** required adopting the Django framework;
inappropriate for a generic Python template — and still inappropriate
for this project, which uses FastAPI.

### No database scaffolding

**Rejected (at template time) because:** a conventional starting
structure was useful as an example.

## Why this is now Superseded

`feedback-triage-app` is a single-purpose product with a single table
and a fixed database engine. The constraints that justified raw SQL +
engine-agnostic scaffolding are gone:

- **One engine** (Postgres 16). Native enums and `CHECK` constraints
  give us schema-level integrity that SQLite couldn't enforce. See
  [ADR 046](046-postgres-enums-and-check-constraints.md).
- **One schema.** A single `feedback_item` table; no scaffolding to
  generalise. See [ADR 045](045-single-table-data-model.md).
- **An ORM justifies its weight.** SQLModel gives us Pydantic-typed
  rows and SQLAlchemy's escape hatches in one library. See
  [ADR 047](047-sqlmodel-over-sqlalchemy.md).

The decisions are split across six smaller ADRs that each address one
question:

| Question | ADR |
| --- | --- |
| ORM choice (SQLModel vs plain SQLAlchemy) | [047](047-sqlmodel-over-sqlalchemy.md) |
| Schema integrity (enums + CHECK constraints) | [046](046-postgres-enums-and-check-constraints.md) |
| Session lifecycle | [048](048-session-per-request.md) |
| Sync vs async driver | [050](050-sync-db-driver-v1.md) |
| Pagination strategy | [049](049-offset-pagination.md) |
| Test database (SQLite vs Postgres) | [054](054-postgres-for-tests.md) |

The template-era `db/` directory does not exist in this project; schema
lives in `src/feedback_triage/models.py` and `alembic/versions/*.py`.

## Consequences (post-fork)

### Positive

- Schema integrity enforced by the database, not just by Python code.
- Type-safe row access via SQLModel.
- Migrations are reviewable, repeatable, and run as a pre-deploy step
  rather than from process startup.

### Negative

- Coupled to PostgreSQL (intentional). Switching engines is a real
  project, not a config change.
- ORM weight on the dependency tree (intentional trade-off for type
  safety and maintainability).

## See also

- [`docs/project/spec/spec.md`](../project/spec/spec.md) — schema
  contract
- [Alembic configuration](../../alembic.ini) — once Phase 2 lands
- All six successor ADRs listed in the redirect table above
