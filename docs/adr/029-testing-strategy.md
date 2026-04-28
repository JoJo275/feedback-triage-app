# ADR 029: Testing Strategy

## Status

Accepted

Refines [ADR 006: pytest for testing](006-pytest-for-testing.md) for
this project's runtime stack. Cross-references
[ADR 054](054-postgres-for-tests.md) (Postgres in tests) and
[ADR 048](048-session-per-request.md) (the session-lifecycle canary).

## Context

The template-era version of this ADR described a unit / integration
split, a pytest-hatch matrix, and an 80% coverage floor against the
template's example modules. That posture does not match
`feedback-triage-app`:

- The app has one HTTP surface and one database table; "unit vs
  integration" is mostly an artefact of the test setup, not the code.
- The matrix tool is now `uv`, not Hatch (see
  [ADR 055](055-uv-as-project-manager.md)).
- The runtime stack (FastAPI + SQLModel + Postgres) and the docs
  (Playwright e2e smoke) introduce specific test patterns the template
  ADR did not cover.

## Decision

### Three layers, gated by markers

| Layer | Where | How it runs | Marker |
|---|---|---|---|
| API | `tests/test_*.py` | `httpx.TestClient` against the FastAPI app, real Postgres backing it | (none — default) |
| End-to-end smoke | `tests/e2e/test_*.py` | Playwright driving the same app | `@pytest.mark.e2e` |
| Slow / opt-in | anywhere | runs on `task test:slow` only | `@pytest.mark.slow` |

`task test` excludes `e2e` and `slow`. CI's `test.yml` and `coverage.yml`
also exclude `e2e` (no browser available). The Playwright suite runs
via `task test:e2e` locally and through a dedicated CI job once it
exists.

### Real Postgres, not SQLite

API tests run against a real Postgres 16 instance. Locally that is the
`db` service from `docker-compose.yml`; in CI it is a service container.
Rationale and dialect-parity argument: [ADR 054](054-postgres-for-tests.md).

### Test isolation pattern

A session-scoped `engine` fixture creates a clean schema once per test
session (`alembic upgrade head` against an empty DB). A function-scoped
`db_session` fixture wraps each test in a `SAVEPOINT` and rolls back
after the test, keeping individual tests isolated without recreating
the schema.

The fallback `truncate_all_tables()` fixture exists for tests that
cannot tolerate the SAVEPOINT pattern (e.g. tests that need real
commits to fire the `BEFORE UPDATE` trigger).

### Canary test for session lifecycle

`test_patch_then_get_returns_fresh_state` is the canary for
[ADR 048](048-session-per-request.md). It:

1. Creates a feedback item.
2. Sends `PATCH /api/v1/feedback/{id}` to change `status`.
3. Sends `GET /api/v1/feedback/{id}` and asserts the new `status`.

If a session is leaked across requests, the GET will return the pre-PATCH
state and the test goes red. **Fix the lifecycle, do not patch the
test.**

### Coverage

- `pytest-cov` against `src/feedback_triage`.
- Branch coverage on.
- `fail_under = 85`.
- `tests/`, `scripts/`, `tools/`, `attic/`, and the generated
  `_version.py` are excluded.
- Coverage runs the full non-e2e suite; the fast `test.yml` job is for
  PR feedback only.

### Test-matrix posture

CI runs the API suite on Python 3.11, 3.12, 3.13. The matrix is driven
by `actions/setup-python` plus `uv sync`, not by Hatch envs. Local
matrix runs use `uv run --python 3.X pytest` when a regression is
suspected on a specific minor.

### Pytest configuration

Already in [`pyproject.toml`](../../pyproject.toml):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers --strict-config"
filterwarnings = ["error::DeprecationWarning"]
markers = [
    "e2e: end-to-end Playwright smoke tests (gated, opt-in via task test:e2e)",
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
]
```

`integration` is kept as a marker for one-off cases that need real
external services beyond Postgres (e.g. a future webhook smoke). It is
not the default routing marker for DB-backed tests.

## Alternatives Considered

### Unit / integration split with mocked DB sessions

**Rejected because:** the app's logic is overwhelmingly "validate input
→ run a query → serialize output". Mocking the DB session in "unit"
tests duplicates `httpx.TestClient` coverage and leaves the most
likely failure mode (SQL or schema bugs) untested.

### SQLite for tests, Postgres only in CI

**Rejected because:** dialect parity is the entire point. See
[ADR 054](054-postgres-for-tests.md).

### Per-test database creation (`createdb` / `dropdb`)

**Rejected because:** orders of magnitude slower than SAVEPOINT or
TRUNCATE. Reach for it only when a test demands schema-level isolation,
which v1.0 never does.

### 100% coverage floor

**Rejected because:** perverse incentive (testing trivial code,
`# pragma: no cover` spam). 85% is high enough to catch regressions
without forcing the team to test boilerplate.

## Consequences

### Positive

- Failures look like production failures: real SQL, real enums, real
  constraints.
- The session-canary catches the most common FastAPI ORM bug class on
  every CI run.
- One clear gate (`task test`) for fast feedback; one clear gate
  (`task test:e2e`) for browser-level checks.

### Negative

- Local test runs require `task up` (Postgres). Documented in the
  README and Taskfile help.
- CI cold start is slower than a SQLite-only suite. Mitigated by
  service-container caching in the workflow.

## Implementation

- [`pyproject.toml`](../../pyproject.toml) — `[tool.pytest.ini_options]`,
  `[tool.coverage.*]`
- [`tests/`](../../tests/) — API tests
- [`tests/e2e/`](../../tests/e2e/) — Playwright smoke
- [`Taskfile.yml`](../../Taskfile.yml) — `test`, `test:e2e`, `test:slow`
- [`.github/workflows/test.yml`](../../.github/workflows/test.yml)
- [`.github/workflows/coverage.yml`](../../.github/workflows/coverage.yml)

## See also

- [ADR 006](006-pytest-for-testing.md) — pytest as the framework
- [ADR 048](048-session-per-request.md) — session-per-request invariant
- [ADR 054](054-postgres-for-tests.md) — Postgres for tests
- [ADR 055](055-uv-as-project-manager.md) — uv replaces Hatch envs
