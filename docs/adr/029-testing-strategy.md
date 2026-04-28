# ADR 029: Testing Strategy

## Status

Accepted

Refines [ADR 006: pytest for testing](006-pytest-for-testing.md) for
this project's runtime stack. Cross-references
[ADR 054](054-postgres-for-tests.md) (Postgres in tests) and
[ADR 048](048-session-per-request.md) (the session-lifecycle canary).

## Context

[ADR 006](006-pytest-for-testing.md) established pytest as the testing
framework. This ADR addresses the higher-level questions ADR 006 did
not: how tests are organised, what coverage expectations exist, how the
test matrix works, and where the boundaries are between test
categories.

### Forces

- Tests must run fast in local development (seconds, not minutes).
- CI must validate across Python 3.11–3.13 to match the support matrix.
- Coverage must be measured and enforced to prevent silent regressions.
- Integration tests may need real resources (the Postgres database) that
  fast feedback tests must not depend on.
- The runtime stack (FastAPI + SQLModel + Postgres) and the
  Playwright-driven e2e smoke suite introduce specific patterns the
  template-era version of this ADR did not cover.

The template-era version split tests by directory (`tests/unit/`,
`tests/integration/`) with a 80% coverage floor. We keep most of that
shape but adapt it: this app's logic is overwhelmingly "validate input
→ run a query → serialize output", so the meaningful boundaries are
"API tests against a real DB" vs "browser e2e", not "unit vs
integration".

## Decision

### Three layers, gated by markers

| Layer | Where | How it runs | Marker |
| --- | --- | --- | --- |
| API | `tests/test_*.py` | `httpx.TestClient` against the FastAPI app, real Postgres backing it | (none — default) |
| End-to-end smoke | `tests/e2e/test_*.py` | Playwright driving the same app | `@pytest.mark.e2e` |
| Slow / opt-in | anywhere | runs on `task test:slow` only | `@pytest.mark.slow` |
| Integration (optional) | `tests/integration/` | real external services beyond Postgres | `@pytest.mark.integration` |

`task test` excludes `e2e` and `slow`. CI's `test.yml` and
`coverage.yml` also exclude `e2e` (no browser available). The
Playwright suite runs via `task test:e2e` locally and through a
dedicated CI job once it exists. The `integration` marker is kept for
one-off cases that need services beyond Postgres (a future webhook
smoke, etc.); it is not the default routing marker for DB-backed tests.

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

If a session is leaked across requests, the GET will return the
pre-PATCH state and the test goes red. **Fix the lifecycle, do not
patch the test.**

### conftest hierarchy

The same fixture-scoping pattern from the template carries forward:

- [`tests/conftest.py`](../../tests/conftest.py) — root fixtures
  (engine, FastAPI app instance, marker registration).
- [`tests/e2e/conftest.py`](../../tests/e2e/conftest.py) — Playwright
  browser/page fixtures.

### Coverage

`pytest-cov` against `src/feedback_triage`:

- **Branch coverage** enabled.
- **Threshold** `fail_under = 85` (raised from the template's 80%
  because the runtime is small and well-defined).
- **Excluded** from measurement: `tests/`, `scripts/`, `tools/`,
  `attic/`, generated `_version.py`.
- **Excluded lines:** `pragma: no cover`, `TYPE_CHECKING` blocks,
  `__main__` guards, `NotImplementedError`.
- **Path mapping** ensures CI (site-packages) and local (`src/`)
  coverage data merge correctly.

Coverage runs the full non-e2e suite; the fast `test.yml` job is for
PR feedback only.

### Test-matrix posture

CI runs the API suite on Python 3.11, 3.12, 3.13 via
`actions/setup-python` plus `uv sync`. The matrix is **not** driven by
Hatch envs (see [ADR 055](055-uv-as-project-manager.md)). Local matrix
runs use:

```bash
uv run --python 3.12 pytest
```

uv installs the toolchain on demand.

### Pytest configuration

In [`pyproject.toml`](../../pyproject.toml):

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

- `strict_markers` catches marker typos at collection time.
- `strict_config` catches invalid pytest config keys.
- `filterwarnings = ["error::DeprecationWarning"]` turns deprecation
  warnings into errors so they surface before upstream libraries
  remove deprecated APIs.

## Alternatives Considered

### Unit / integration directory split with mocked DB sessions

Have a `tests/unit/` for fast no-I/O tests with mocked sessions, and
`tests/integration/` for everything that touches Postgres. This was the
template's posture.

**Rejected because:** the app's logic is overwhelmingly "validate
input → run a query → serialize output". Mocking the DB session in
"unit" tests duplicates `httpx.TestClient` coverage and leaves the
most likely failure mode (SQL or schema bugs) untested. We keep the
`integration` marker available but it is not the default routing
boundary.

### Flat test directory (no subdirectories at all)

**Considered.** We mostly do this, with `tests/e2e/` carved out
because Playwright fixtures are heavyweight and shouldn't load on
every API run.

### SQLite for tests, Postgres only in CI

**Rejected because:** dialect parity is the entire point. See
[ADR 054](054-postgres-for-tests.md).

### Per-test database creation (`createdb` / `dropdb`)

**Rejected because:** orders of magnitude slower than SAVEPOINT or
TRUNCATE. Reach for it only when a test demands schema-level
isolation, which v1.0 never does.

### tox for the test matrix

**Rejected because:** `uv run --python 3.X pytest` already does
matrix runs against any installed-on-demand interpreter. Adding tox
duplicates env management and conflicts with the uv-based workflow
([ADR 055](055-uv-as-project-manager.md)).

### 100% coverage requirement

**Rejected because:** perverse incentive (testing trivial code,
`# pragma: no cover` spam). 85% is high enough to catch regressions
without forcing the team to test boilerplate.

### No coverage threshold

**Rejected because:** automated enforcement prevents gradual erosion.
A PR-review-only floor relies on reviewer attention.

## Consequences

### Positive

- Failures look like production failures: real SQL, real enums, real
  constraints.
- The session-canary catches the most common FastAPI ORM bug class on
  every CI run.
- One clear gate (`task test`) for fast feedback; one clear gate
  (`task test:e2e`) for browser-level checks.
- `strict_markers` and `strict_config` catch configuration errors.
- Deprecation warnings surfaced as errors before they become breaking
  changes.
- conftest.py hierarchy provides fixture scoping (root → e2e).

### Negative

- Local test runs require `task up` (Postgres). Documented in the
  README and Taskfile help.
- CI cold start is slower than a SQLite-only suite. Mitigated by
  service-container caching in the workflow.
- Multi-version matrix increases CI run time (~3× for 3 versions).
  Mitigated by parallel jobs.

### Mitigations

- The marker boundary is simple (`@pytest.mark.e2e` for browser tests,
  `@pytest.mark.slow` for opt-in long runs, otherwise default API tier).
- Coverage threshold is configurable in `pyproject.toml` if a phase
  legitimately needs a different floor.
- CI matrix runs in parallel; wall-clock time stays reasonable.

## Implementation

- [`pyproject.toml`](../../pyproject.toml) — `[tool.pytest.ini_options]`,
  `[tool.coverage.*]`
- [`tests/`](../../tests/) — API tests
- [`tests/e2e/`](../../tests/e2e/) — Playwright smoke
- [`Taskfile.yml`](../../Taskfile.yml) — `test`, `test:e2e`, `test:slow`
- [`.github/workflows/test.yml`](../../.github/workflows/test.yml) — CI
  test matrix (3.11–3.13)
- [`.github/workflows/coverage.yml`](../../.github/workflows/coverage.yml) — CI
  coverage reporting

## See also

- [ADR 006](006-pytest-for-testing.md) — pytest as the framework
- [ADR 048](048-session-per-request.md) — session-per-request invariant
- [ADR 054](054-postgres-for-tests.md) — Postgres for tests
- [ADR 055](055-uv-as-project-manager.md) — uv replaces Hatch envs
- [pytest documentation](https://docs.pytest.org/)
- [coverage.py configuration](https://coverage.readthedocs.io/en/latest/config.html)
