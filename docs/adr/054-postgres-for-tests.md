# ADR 054: Postgres for Tests (No SQLite)

## Status

Accepted

## Context

A common shortcut is to run tests against SQLite for speed. SQLite and
Postgres differ on:

- Native enum types (Postgres has them; SQLite does not).
- `CHECK` constraint enforcement nuances.
- Datetime-with-timezone semantics.
- Trigger syntax and behaviour.
- `RETURNING`, `ON CONFLICT`, JSON operators.

Production-shaped bugs hide in those gaps.

## Decision

The test suite runs against a real PostgreSQL 16 instance. The CI
workflow provisions a Postgres service container; local runs use the
`docker compose` `db` service.

Each test runs inside its own transaction OR uses a `truncate_all_tables()`
fixture between tests. Either pattern keeps tests isolated without
recreating the schema.

The Playwright e2e smoke suite uses the same Postgres backend behind the
running app.

## Alternatives Considered

### SQLite

**Rejected because:** dialect parity is the entire point of database
testing. SQLite would silently pass tests that production Postgres
rejects (or vice versa).

### Per-test database creation (`createdb` then `dropdb`)

**Rejected because:** orders of magnitude slower than truncate. Use only
when the test needs schema-level isolation.

## Consequences

### Positive

- Migrations are exercised by the test setup path.
- Native enums, CHECKs, and triggers are real in tests.
- Production-shaped bugs surface in CI, not in production.

### Negative

- CI cold start is slower than SQLite. Acceptable.
- Local test runs require `task up` first.
