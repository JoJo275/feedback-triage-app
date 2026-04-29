<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: chore/fork-bring-up -->
<!--
  Suggested PR title (conventional commit format — type: description):

    chore: fork bring-up — feedback-triage-app skeleton through Phase 6 + Railway runbook

  Available prefixes:
    feat:     — new feature or capability
    fix:      — bug fix
    docs:     — documentation only
    chore:    — maintenance, no production code change
    refactor: — code restructuring, no behavior change
    test:     — adding or updating tests
    ci:       — CI/CD workflow changes
    style:    — formatting, no logic change
    perf:     — performance improvement
    build:    — build system or dependency changes
    revert:   — reverts a previous commit
-->

<!--
  ╔══════════════════════════════════════════════════════════════╗
  ║  This PR description is for HUMAN REVIEWERS.                 ║
  ║                                                              ║
  ║  Release automation (release-please) reads individual        ║
  ║  commit messages on main — not this description.             ║
  ║  Write commits with conventional format (feat:, fix:, etc.)  ║
  ║  and include (#PR) or (#issue) references in each commit.    ║
  ║                                                              ║
  ║  This template captures: WHY you made changes, HOW to test   ║
  ║  them, and WHAT reviewers should focus on.                   ║
  ╚══════════════════════════════════════════════════════════════╝
-->

## Description

Initial bring-up of `feedback-triage-app` after forking from
`simple-python-boilerplate`. Lands the FastAPI + PostgreSQL skeleton
through Phase 6 (Playwright smoke), wires up the deployment runbook for
Railway (Phase 7), and restores the `fta-*` console scripts as
project-bound wrappers around the retained dev tooling.

**What changed:**

- **Pre-Phase fork:** archived the template package to [attic/](attic/), scaffolded
  [src/feedback_triage/](src/feedback_triage/), retargeted [pyproject.toml](pyproject.toml), [Taskfile.yml](Taskfile.yml),
  [Containerfile](Containerfile), [docker-compose.yml](docker-compose.yml), workflows, README, ADRs, and
  [.env.example](.env.example) for the new project.
- **Build/env:** migrated from `pip install -e .` to `uv sync --frozen`
  across CI and pre-commit; Hatchling + `hatch-vcs` retained as the build
  backend (per ADR 016).
- **Phase 1–2:** core FastAPI app factory, settings via
  `pydantic-settings`, SQLModel/SQLAlchemy session-per-request, Alembic
  migration `0001_create_feedback_item` with native enums + CHECK
  constraints + `BEFORE UPDATE` trigger.
- **Phase 3:** `/api/v1/feedback` CRUD with envelope-based list responses,
  explicit `response_model=` on every route, ISO-8601 UTC datetimes.
- **Phase 4:** static HTML pages (list / new / detail) served via
  `StaticFiles` with vanilla JS + Fetch — no Jinja, no bundler.
- **Phase 5:** global exception handlers, request-ID middleware, and
  structured logging that propagates the request ID through every record.
- **Phase 6:** Playwright smoke suite under `tests/e2e/`, gated behind
  `@pytest.mark.e2e` and the `task test:e2e` runner.
- **Phase 7 prep:** Railway runbook in [docs/](docs/) covering pre-deploy
  migrations, env-var surface, and cost guardrails.
- **ADRs:** drafted 045–055 (project-specific) and rewrote inherited
  014 / 025 / 027 / 029 / 031 to reflect the FastAPI + Postgres stack.
- **Console scripts:** restored [`src/feedback_triage/entry_points.py`](src/feedback_triage/entry_points.py)
  with the 19 `fta-*` wrappers (script helpers + dashboard) targeting
  the editable install — the wheel still ships only the FastAPI app.

**Why:**

The template gave us CI, ADRs, docs scaffolding, and dev tooling for free;
the app code, schema, and deployment story all needed to be authored from
the spec ([docs/project/spec/spec.md](docs/project/spec/spec.md)). Landing Pre-Phase through Phase 6
in one branch keeps the rewrite atomic — every surface (spec, ADRs,
README, CI, Containerfile, tests) moves together so reviewers can verify
internal consistency in a single pass.

## Related Issue

N/A — initial fork bring-up; tracked against the implementation plan in
[docs/project/implementation.md](docs/project/implementation.md).

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [x] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [x] 🔧 Refactor (no functional changes)
- [x] 🧪 Test update

## How to Test

**Steps:**

1. `uv sync` — installs the project + dev/test extras into `.venv`.
2. `task up` — boots the Postgres 16 container via Compose.
3. `task migrate` — applies `0001_create_feedback_item`.
4. `task dev` — FastAPI on `http://localhost:8000`; visit `/api/v1/docs`
   and the `/`, `/new`, `/feedback/{id}` HTML pages.
5. `task check` — runs ruff + mypy (strict) + pytest API suite.
6. `task test:e2e` — Playwright smoke against the running app.
7. (Optional) `fta-env-doctor`, `fta-repo-doctor`, `fta-dashboard` — sanity
   check the restored console scripts.

**Test command(s):**

```bash
uv sync
task up && task migrate
task check
task test:e2e
```

**Screenshots / Demo (if applicable):**

N/A — UI is intentionally minimal vanilla HTML/JS; see [docs/project/spec/spec.md](docs/project/spec/spec.md)
"Frontend" section for the rendered shape.

## Risk / Impact

**Risk level:** High — first commit of the application; everything below
the fork point is greenfield code on a still-empty `main` history.

**What could break:**

- Railway deploy: pre-deploy `alembic upgrade head` must run before the
  app boots (runbook documents this; Phase 7 has not yet been exercised
  against a live Railway project).
- Session-per-request: the canary test
  `test_patch_then_get_returns_fresh_state` is the contract; if anyone
  reintroduces a module-global `Session`, that test must catch it.
- Native Postgres enums: schema changes that touch `source_enum` /
  `status_enum` need hand-written Alembic ops — autogenerate misses them.
- `fta-*` scripts only resolve in an editable checkout; running them from
  a wheel install will exit with the documented error message.

**Rollback plan:** Revert this PR. The repository has no published
release tag yet and no production deployment, so rollback is purely a
git operation.

## Dependencies (if applicable)

**Depends on:** N/A — first feature PR on the fork.

**Blocked by:** N/A.

## Breaking Changes / Migrations (if applicable)

- [x] Config changes required — copy [.env.example](.env.example) to `.env` and set
  `POSTGRES_PASSWORD` / `DATABASE_URL` before first boot.
- [x] Data migration needed — `alembic upgrade head` creates the
  `feedback_item` table, native enums, CHECK constraints, and the
  `updated_at` trigger.
- [x] API changes — establishes `/api/v1/feedback` (no prior surface to
  break).
- [x] Dependency changes — replaces the template's runtime stack with
  `fastapi[standard]`, `sqlmodel`, `psycopg[binary]`, `alembic`,
  `pydantic-settings`. `uv.lock` is committed.

**Details:**

See [docs/project/spec/spec.md](docs/project/spec/spec.md) §"Configuration & Environment Variables"
for the env-var surface and §"Data Model" for the schema.

## Checklist

- [x] My code follows the project's style guidelines (ruff + mypy strict)
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [x] No new warnings (or explained in Additional Notes)
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] Relevant tests pass locally (or explained in Additional Notes)
- [x] No security concerns introduced (or flagged for review)
- [x] No performance regressions expected (or flagged for review)

## Reviewer Focus (Optional)

Please pay close attention to:

1. **[alembic/versions/0001_create_feedback_item.py](alembic/versions/0001_create_feedback_item.py)** — the autogenerated
   diff was hand-edited to add the native enum types, CHECK constraints,
   and `BEFORE UPDATE` trigger. Verify those weren't lost on rebase.
2. **[src/feedback_triage/database.py](src/feedback_triage/database.py)** — `get_db` is the only place
   commit/rollback lives; no sessions on `app.state` or module globals.
3. **[src/feedback_triage/routes/feedback.py](src/feedback_triage/routes/feedback.py)** — every route declares an
   explicit `response_model=`; list endpoint returns the
   `{items, total, skip, limit}` envelope, not a bare array.
4. **ADR rewrites** (014, 025, 027, 029, 031) — confirm they reflect the
   FastAPI + Postgres stack rather than the template's defaults.

## Additional Notes

- The template's `spb` / `spb-version` / `spb-doctor` core entry points
  were intentionally **not** ported: they delegated to `cli.py` and
  `engine.py` modules that don't exist in `feedback_triage`. The app is
  launched via `uvicorn feedback_triage.main:app` or `task dev`.
- [attic/](attic/) is read-only reference material; nothing in the live tree
  imports from it.
- `uv.lock` is committed and CI uses `uv sync --frozen`; lock drift will
  fail the build.
