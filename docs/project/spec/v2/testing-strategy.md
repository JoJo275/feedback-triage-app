# v2.0 — Testing strategy

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> See also: [`api.md`](api.md), [`security.md`](security.md),
> [`accessibility.md`](accessibility.md),
> [`error-catalog.md`](error-catalog.md).

The test suite is a **three-layer pyramid plus a fixed canary
list**. Every PR must keep the canary list green; everything
else is best-effort.

---

## Layers

### Unit tests — `tests/unit/`

- Pure-Python, no DB, no HTTP, no FastAPI app.
- Targets: pure helpers, validators, password-hashing wrapper,
  log-redaction formatter, error-mapping table, slug generators,
  pagination math.
- Fast (< 1s for the whole layer). Run on every save in dev.

### API tests — `tests/api/`

- httpx `TestClient` against the FastAPI app, hitting Postgres.
- Postgres only, **never SQLite** (dialect parity).
- One transaction per test; truncate fixtures between tests.
- Cover every route in [`api.md`](api.md), every error code in
  [`error-catalog.md`](error-catalog.md), and every state
  transition in [`auth.md`](auth.md).

### End-to-end — `tests/e2e/`

- Playwright, Chromium-only in CI (Firefox/WebKit in nightly).
- Gated behind `@pytest.mark.e2e`; `task test:e2e` runs them.
- Boots the whole app + a fresh Postgres, seeds via
  `scripts/seed.py`, then drives real browsers.
- **Each e2e test injects axe-core** and asserts zero violations
  ([`accessibility.md`](accessibility.md)).

---

## Ship-blocking canaries

These tests must be green in `task check` (the CI gate). If a
canary breaks, the PR is blocked — no merging on red, no
"will fix in follow-up."

| File                                                      | What it asserts                                                                       |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `tests/api/test_isolation.py`                             | Cross-tenant reads/writes return **404 (not 403)**, never echo other workspaces' rows ([`security.md`](security.md), [`multi-tenancy.md`](multi-tenancy.md)) |
| `tests/api/test_session_per_request.py`                   | `PATCH then GET returns fresh state` — the v1 canary, kept ([copilot-instructions](../../../../.github/copilot-instructions.md)) |
| `tests/api/test_demo_read_only.py`                        | Every write to a `is_read_only=true` workspace returns 403 `code=demo_read_only`     |
| `tests/api/test_auth_no_enumeration.py`                   | Login + signup + reset paths cannot be used to enumerate accounts ([`auth.md`](auth.md)) |
| `tests/api/test_feature_auth_flag.py`                     | When `FEATURE_AUTH=false`, `/login` and `/api/v1/auth/*` return 503 `code=feature_disabled` |
| `tests/api/test_error_envelope.py`                        | Every 4xx + 5xx body matches the envelope from [`error-catalog.md`](error-catalog.md) |
| `tests/api/test_status_transitions.py`                    | All allowed transitions succeed; all disallowed return 409                            |
| `tests/api/test_note_edit_window.py`                      | Note PATCH/DELETE allowed within 15 minutes; 409 after                                |
| `tests/api/test_type_other_validation.py`                 | `type=other` requires `type_other` (422 `code=type_other_required`)                  |
| `tests/api/test_pagination.py`                            | List endpoints return the `{items,total,skip,limit}` envelope                         |
| `tests/api/test_rate_limit_public_form.py`                | Public-form rate limit fires at the documented threshold                              |
| `tests/test_logging.py::test_known_headers_are_redacted`  | Redaction contract from [`observability.md`](observability.md)                        |
| `tests/migrations/test_round_trip.py`                     | `alembic upgrade head` + `downgrade base` on a populated DB does not lose constraints |
| `tests/e2e/test_xss_smoke.py`                             | `<script>alert(1)</script>` rendered as text, no script execution                     |
| `tests/e2e/test_a11y_smoke.py`                            | axe-core: zero violations on landing, login, dashboard, inbox, detail, settings       |
| `tests/e2e/test_login_flow.py`                            | Signup → verify-email → login → workspace pick → dashboard                            |
| `tests/e2e/test_public_submit_flow.py`                    | Public form → thank-you → row appears in inbox                                        |

The canary list lives **here**; the test files live in `tests/`.
Adding a canary is a one-PR process — both this file and the test
land together.

---

## Cross-tenant fixture: `client_w1` / `client_w2`

The single most-used API-test fixture set:

```python
@pytest.fixture
def client_w1(db_session) -> TestClient:
    """Authenticated as user_a, scoped to workspace_1."""
    ...

@pytest.fixture
def client_w2(db_session) -> TestClient:
    """Authenticated as user_b, scoped to workspace_2.
    user_b has zero membership in workspace_1."""
    ...
```

Every cross-tenant test reads/writes through `client_w2` against an
ID that belongs to `workspace_1` and asserts a 404 with
`error.code = "*_not_found"`. The fixture is defined in
`tests/conftest.py`; do not re-implement it per-file.

Seed helpers: `tests/factories.py` exposes `make_user()`,
`make_workspace()`, `make_membership()`, `make_feedback()`,
`make_tag()`, `make_note()`. All use Faker with a fixed seed so
canary failures are reproducible.

---

## Round-trip migration test

`tests/migrations/test_round_trip.py`:

1. Spin up a fresh Postgres.
2. `alembic upgrade head`.
3. Insert representative rows in every table (via factories).
4. `alembic downgrade base` — must not raise.
5. `alembic upgrade head` again — must not raise.
6. Re-insert and assert the same rows are accepted.

This is the **only** test that exercises downgrades. Migration
authors don't need to keep every downgrade hand-written; they
do need this round-trip to pass on each PR that adds a revision.

---

## Coverage

- Target: **≥ 85% line coverage** on `src/feedback_triage/`.
- Coverage is measured by `coverage.py` and reported in
  `coverage.xml` + Codecov.
- Coverage is **not a release blocker** — canaries are. We do
  not chase coverage at the cost of meaningful tests.
- Test-only files (`tests/**`) are excluded from coverage.
  Migration files (`alembic/versions/**`) are excluded; they're
  exercised by `test_round_trip.py`.

---

## Test data hygiene

- Fixtures use **fixed UUIDs** so canary failures show diffs
  in test output instead of opaque IDs. The canonical IDs are
  defined in `tests/ids.py`.
- Email addresses use `@example.test` (RFC 6761).
- Passwords use the literal string `"correct horse battery staple"`
  (XKCD reference; passes the password-policy validator).
- Canonical account identity/credential references are centralized in
  [`accounts.md`](accounts.md).

---

## CI invocation

Locally:

```
task test           # unit + api
task test:e2e       # gated, opt-in
task check          # lint + typecheck + test (the gate)
```

In CI, the matrix is:

| Job              | Python       | OS                | Notes                              |
| ---------------- | ------------ | ----------------- | ---------------------------------- |
| `unit-api`       | 3.11, 3.12   | ubuntu-latest     | Postgres 16 service container      |
| `e2e`            | 3.12         | ubuntu-latest     | Playwright Chromium                |
| `migrations`     | 3.12         | ubuntu-latest     | round-trip on Postgres 16          |
| `lint-typecheck` | 3.12         | ubuntu-latest     | ruff + mypy + bandit               |

Nightly adds Firefox + WebKit for e2e, and Postgres 15 + 17 for
the API job (forward / backward compatibility check).

---

## Out of scope (v2.0)

- Mutation testing (mutmut, cosmic-ray).
- Property-based testing beyond a couple of Hypothesis tests on
  the slug generator.
- Visual regression testing (Percy, Chromatic). Manual review
  of `/styleguide` is the floor.
- Load testing. Railway's hobby tier doesn't support meaningful
  load tests; we rely on [`performance-budgets.md`](performance-budgets.md)
  in production.
