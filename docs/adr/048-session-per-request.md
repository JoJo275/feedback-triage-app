# ADR 048: Session-per-Request with `expire_on_commit=False`

## Status

Proposed

## Context

A common FastAPI bug is an ORM session reused across requests, parked on
`app.state`, a module-level global, or accidentally cached by a closure.
The first request commits, the second request sees stale attribute
caches, and a `PATCH` followed by a `GET` returns the pre-PATCH values.
The bug is easy to ship and hard to spot in code review.

`expire_on_commit=True` (SQLAlchemy default) compounds the problem:
after commit, attributes are marked stale, and the next `.refresh()`-
free access can re-query in surprising ways.

## Decision

- A new SQLAlchemy session is created **per request** by the FastAPI
  `get_db()` dependency.
- Sessions are configured with `expire_on_commit=False`. Returned ORM
  objects keep their attribute values after commit, which is the shape
  callers expect.
- Commit and rollback live inside the `get_db()` dependency, not in
  individual route handlers. Handlers raise; the dependency rolls back.
- **No** session is ever stored on `app.state`, a module-level global,
  a class attribute, or a closure that outlives the request.

A canary test, `test_patch_then_get_returns_fresh_state`, guards this
invariant. If it ever goes red, fix the lifecycle, do not patch the
test.

## Alternatives Considered

### Long-lived session reused across requests

**Rejected because:** stale reads, identity-map bleed, and concurrency
hazards.

### `expire_on_commit=True` (the default)

**Rejected because:** every commit invalidates ORM attributes and
forces re-loads or `.refresh()` calls. Surprising for a small CRUD app.

### Async session per request

**Deferred** — the v1.0 routes are sync (`def`, not `async def`) per
ADR 050. Revisit when a real async dependency lands.

## Consequences

### Positive

- One predictable lifecycle for every request.
- The canary test makes regressions loud.

### Negative

- `expire_on_commit=False` means callers must not assume a returned
  object reflects another transaction's writes. Acceptable for
  request-scoped use.
