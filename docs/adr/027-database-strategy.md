# ADR 027: Database Strategy — SQLModel + PostgreSQL + Alembic

## Status

Superseded by ADRs [046](046-postgres-enums-and-check-constraints.md),
[047](047-sqlmodel-over-sqlalchemy.md), [048](048-session-per-request.md),
[049](049-offset-pagination.md), [050](050-sync-db-driver-v1.md), and
[054](054-postgres-for-tests.md).

## Why this ADR exists

This file was inherited from the `simple-python-boilerplate` template,
where it argued for **raw SQL files in a `db/` directory and no ORM**.
That decision is incompatible with `feedback-triage-app`, which uses
SQLModel + SQLAlchemy 2.x + PostgreSQL 16 + Alembic.

Rather than rewrite this single ADR to cover the whole new database
stack, the decisions are split across six smaller ADRs that each
address one question:

| Question | ADR |
|---|---|
| ORM choice (SQLModel vs plain SQLAlchemy) | [047](047-sqlmodel-over-sqlalchemy.md) |
| Schema integrity (enums + CHECK constraints) | [046](046-postgres-enums-and-check-constraints.md) |
| Session lifecycle | [048](048-session-per-request.md) |
| Sync vs async driver | [050](050-sync-db-driver-v1.md) |
| Pagination strategy | [049](049-offset-pagination.md) |
| Test database (SQLite vs Postgres) | [054](054-postgres-for-tests.md) |

Migrations are managed by Alembic with `compare_type=True` and
`compare_server_default=True`; every migration is hand-reviewed after
autogenerate. See [ADR 053](053-migrations-as-pre-deploy-command.md)
for how migrations run in deployment.

## Original (template-era) text — for history only

> Use raw SQL files organized in a `db/` directory at the project root.
> No ORM is included by default. The template defaults to SQLite for
> zero-setup local development.

That decision is moot post-fork. The `db/` directory does not exist
in this project; schema lives in `src/feedback_triage/models.py` and
`alembic/versions/*.py`.

## See also

- [`docs/project/spec/spec.md`](../project/spec/spec.md) — schema
  contract
- [Alembic configuration](../../alembic.ini) — once Phase 2 lands
