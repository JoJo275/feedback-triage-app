# ADR 050: Sync DB Driver in v1.0 (Defer asyncpg)

## Status

Proposed

## Context

FastAPI supports both sync and async route handlers. The choice cascades
into driver selection (`psycopg` v3 sync vs. `asyncpg`), session
construction, and dependency wiring.

Async only pays off when:

- The handler waits on multiple I/O operations concurrently, **or**
- The deployment is bound by per-process concurrency (e.g. one
  container, hundreds of slow requests).

Neither is true for a small CRUD service on Railway with a short
request/response cycle and a single dominant downstream (Postgres).

## Decision

v1.0 routes are written as `def`, not `async def`. The DB layer uses
`psycopg` v3 in **sync** mode behind SQLAlchemy 2.x. SQLModel sessions
are sync.

FastAPI runs sync handlers on a threadpool, which is appropriate for
short DB-bound work. There is no measurable benefit to `async def +
asyncpg` at this scope and several costs (mixing sync + async session
lifecycles, harder testing, different dependency contract).

Revisit when **either**:

1. Sustained concurrency exceeds what the threadpool can serve cleanly
   (visible as queueing in /ready latency), or
2. A handler grows a real `await` workload (calling an external API
   alongside the DB).

## Alternatives Considered

### `async def` everything from day one

**Rejected because:** more rope, less benefit at this scope. Common
source of mixed-mode bugs.

### `async def` only on a subset of routes

**Rejected because:** mixing modes requires careful session-handling and
testing. Pick one for v1.0.

## Consequences

### Positive

- One mental model. Simple test fixtures.
- `TestClient` works without async ceremony.

### Negative

- If the project ever needs concurrent external I/O per request, the
  switch is non-trivial. Explicitly accepted.
