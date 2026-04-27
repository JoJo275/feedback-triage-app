# Implementation Plan — Feedback Triage App

Phase-by-phase build plan for delivering v1.0 of the Feedback Triage App.
This is the operational companion to [`spec/spec.md`](spec/spec.md): the
spec says **what** to build, this doc says **in what order** and **how to
know each step is done**.

When the spec and this doc disagree, the spec wins. Update both together.

---

## How to Use This Doc

- Phases are sequential. Do not start Phase N+1 until Phase N is green.
- Each phase has **deliverables**, a **definition of done (DoD)**, and a
  list of **verification steps** (commands you run, output you expect).
- Tier tags from the spec apply: `[Must]` items block the phase from
  closing; `[Should]` items can slip to a follow-up if time forces a cut;
  `[Nice]` is opportunistic.
- A phase is *not* done because the code compiles. It is done when the
  verification steps pass on a clean clone.

---

## Pre-Phase: Fork the Template

Before Phase 1 can start, the surrounding template must be repurposed.

### Deliverables

- [ ] Repository renamed / new repo created as `feedback-triage-app`.
- [ ] `src/simple_python_boilerplate/` removed; replaced with empty
      `src/feedback_triage/__init__.py`.
- [ ] `pyproject.toml` updated:
  - [ ] `name = "feedback-triage-app"`
  - [ ] `[project.scripts]` cleared of `spb-*` entries
  - [ ] description, URLs, classifiers updated
  - [ ] dependencies trimmed to runtime needs (FastAPI, SQLModel,
        Alembic, psycopg[binary], pydantic-settings, uvicorn)
  - [ ] optional groups: `test`, `e2e`, `docs`
- [ ] `tools/dev_tools/`, `mkdocs-hooks/`, `repo_doctor.d/`, `labels/`,
      `experiments/` reviewed and either removed or trimmed.
- [ ] `scripts/` reduced to `seed.py` (placeholder) and any project-
      specific helpers; template `spb-*` scripts removed.
- [ ] `.github/workflows/` trimmed to: CI gate, release pipeline,
      Dependabot auto-merge, e2e smoke. SHA pins refreshed.
- [ ] `.pre-commit-config.yaml` trimmed to hooks this project actually
      uses.
- [ ] `Taskfile.yml` rewritten to the task list in
      [spec — Task Runner](spec/spec.md#task-runner--taskfile).
- [ ] `Containerfile` rewritten per
      [spec — Container Hardening](spec/spec.md#container-hardening-must).
- [ ] ADRs cleaned up:
  - [ ] Template-only ADRs already deleted (036, 040, 041, 042, 043,
        011, 015, 039)
  - [ ] ADRs 014, 025, 027, 029, 031 rewritten for this project
  - [ ] New ADRs 045–054 drafted (see
        [spec — ADRs to Write](spec/spec.md#adrs-to-write))
- [ ] `docs/` cleaned: keep `docs/project/`, ADRs, and a fresh `index.md`
      pointing at the spec; remove template-specific guides.
- [ ] `README.md` replaced with the structure in
      [spec — README Sections to Include](spec/spec.md#readme-sections-to-include-must).

### Definition of Done

- `task lint`, `task typecheck`, and `task test` all pass on a clean
  checkout — even though the test suite is empty, the gates run.
- `hatch shell` enters a working environment.
- `git log` shows a single conventional commit:
  `chore: fork from simple-python-boilerplate template`.

### Verification

```bash
hatch env create
hatch run ruff check .
hatch run mypy src tests   # passes trivially with empty src
task test                  # 0 tests, 0 failures
task lint
git tag                    # no v0/v1 tags yet
```

---

## Phase 1 — Project Skeleton

Wire FastAPI, settings, and Docker Compose Postgres so a "hello world"
endpoint serves over HTTP and can talk to a running database.

### Deliverables `[Must]`

- [ ] `src/feedback_triage/config.py` — `Settings` via `pydantic-settings`,
      reading `DATABASE_URL`, `APP_ENV`, `LOG_LEVEL`, `PORT`,
      `CORS_ALLOWED_ORIGINS`, `PAGE_SIZE_DEFAULT`, `PAGE_SIZE_MAX`.
      Normalize `postgres://` → `postgresql+psycopg://` at load time.
- [ ] `src/feedback_triage/main.py` — `create_app()` factory, CORS
      middleware reading from settings, request-ID middleware, structured
      request-logging middleware.
- [ ] `src/feedback_triage/routes/health.py` — `/health` and `/ready`
      with the 2s readiness timeout per
      [spec](spec/spec.md#health-and-readiness).
- [ ] `docker-compose.yml` — Postgres 16, named `pgdata` volume, healthy
      `depends_on`.
- [ ] `.env.example` matches the spec's env-var surface.
- [ ] `Taskfile.yml` — `task up`, `task down`, `task dev` work.

### Definition of Done

- `task up && task dev` boots the app.
- `curl http://localhost:8000/health` returns `{"status":"ok"}`.
- `curl http://localhost:8000/ready` returns `{"status":"ok"}` while
  Postgres is up, and `503` within 2s after `task down`.
- Every response includes an `X-Request-ID` header.
- Stopping Postgres mid-request triggers a clean readiness failure, not a
  hung request.

### Verification

```bash
task up
task dev &
curl -i http://localhost:8000/health
curl -i http://localhost:8000/ready
task down
sleep 1
curl -m 3 -i http://localhost:8000/ready   # expect 503 within ~2s
```

---

## Phase 2 — Database Schema and Migrations

Define the model, generate the first migration by hand-reviewing
autogenerate, and bring up an empty schema.

### Deliverables `[Must]`

- [ ] `src/feedback_triage/enums.py` — `Source` and `Status` Python enums
      (single source of truth, imported by both models and schemas).
- [ ] `src/feedback_triage/models.py` — `FeedbackItem` SQLModel with
      `text` columns, native enum mapping, `bigint` identity, server
      defaults on `created_at` / `updated_at`.
- [ ] `src/feedback_triage/database.py` — engine, `SessionLocal`,
      `get_db` dependency with commit/rollback wired in (see
      [spec sketch](spec/spec.md#database-session-lifecycle)).
- [ ] `alembic.ini` reading `DATABASE_URL` from env.
- [ ] `alembic/env.py` with `target_metadata = SQLModel.metadata`,
      `compare_type=True`, `compare_server_default=True`.
- [ ] First migration `versions/0001_create_feedback_item.py`,
      hand-reviewed, containing:
  - [ ] `source_enum` and `status_enum` types
  - [ ] `feedback_item` table
  - [ ] All four CHECK constraints (pain_level range, title not blank,
        title max length, description max length)
  - [ ] All three indexes (`created_at DESC`, `status`, `source`)
  - [ ] `set_updated_at()` function and `BEFORE UPDATE` trigger

### Definition of Done

- `task migrate` succeeds against an empty database and is idempotent.
- `\d feedback_item` in `psql` shows every column, type, default,
  CHECK, and index from the spec.
- `\dT+ source_enum` and `\dT+ status_enum` show the expected values.
- A direct `INSERT` violating any CHECK is rejected at the DB level
  (manually verified once via `psql`).

### Verification

```bash
task migrate
docker compose exec db psql -U feedback -d feedback -c "\d feedback_item"
docker compose exec db psql -U feedback -d feedback -c "\dT+ source_enum"
docker compose exec db psql -U feedback -d feedback -c \
  "INSERT INTO feedback_item (title, source, pain_level) VALUES ('', 'email', 1);"
# expect: ERROR: new row violates check constraint "feedback_item_title_not_blank"
```

---

## Phase 3 — CRUD API

Build the JSON API under `/api/v1/feedback`, including validation,
pagination, filtering, sorting, and the canary stale-read test.

### Deliverables `[Must]`

- [ ] `src/feedback_triage/schemas.py` — `FeedbackCreate`,
      `FeedbackUpdate`, `FeedbackResponse`, `FeedbackListEnvelope`.
      Datetime serializer pinned to ISO 8601 + `Z`.
- [ ] `src/feedback_triage/crud.py` — pure DB-layer functions
      (`create_item`, `get_item`, `list_items`, `update_item`,
      `delete_item`). No HTTP concerns.
- [ ] `src/feedback_triage/routes/feedback.py` — handlers under
      `/api/v1/feedback`, every route with explicit `response_model=`
      and `tags=["feedback"]`.
- [ ] `POST /api/v1/feedback` returns `201` and a `Location` header.
- [ ] `GET /api/v1/feedback` returns the envelope shape exactly as
      [specified](spec/spec.md#list).
- [ ] `sort_by` allow-list enforced; invalid value → `422`.
- [ ] `PATCH` performs partial updates only.
- [ ] `DELETE` returns `204`.

### Deliverables `[Should]`

- [ ] OpenAPI tags grouped (`feedback`, `health`).
- [ ] Custom 404 body matches the spec
      (`{"detail":"Feedback item not found"}`).

### Definition of Done

- All API tests in [spec — API Tests](spec/spec.md#api-tests-must) pass,
  including `test_patch_then_get_returns_fresh_state`.
- `/api/v1/docs` renders with grouped tags and concrete request/response
  schemas (no `Any` placeholders).
- `task test` is green.

### Verification

```bash
task test
curl -i -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{"title":"Login is slow","source":"email","pain_level":3}'
# expect 201 + Location: /api/v1/feedback/<id>

curl http://localhost:8000/api/v1/feedback?sort_by=evil
# expect 422
```

---

## Phase 4 — Frontend Pages

Three static HTML pages plus the JS that wires them to the API. No
Jinja, no bundler.

### Deliverables `[Must]`

- [ ] `src/feedback_triage/static/index.html` — list view with filter
      controls.
- [ ] `src/feedback_triage/static/new.html` — create form.
- [ ] `src/feedback_triage/static/detail.html` — edit form.
- [ ] `src/feedback_triage/static/css/styles.css` — neutral palette,
      readable spacing, visible focus rings, WCAG AA contrast.
- [ ] `src/feedback_triage/static/js/index.js`,
      `static/js/new.js`, `static/js/detail.js` — `fetch` against the
      JSON API, render results, handle errors.
- [ ] `src/feedback_triage/routes/pages.py` — unversioned routes (`/`,
      `/new`, `/feedback/{id}`) returning the correct HTML files.
- [ ] `StaticFiles` mounted for `/static`.

### Deliverables `[Should]`

- [ ] Inline form-validation errors (HTML5 + `aria-invalid` on the
      offending field).
- [ ] Filter state preserved in `?status=&source=` query params so a
      reload keeps the user's view.

### Definition of Done

- All three pages load standalone via `task dev`.
- Every input has a `<label>`. Every button is a `<button>`.
- Keyboard-only navigation works on all three pages.
- Lighthouse Accessibility ≥ 90 on each page.
- Manual test: create → list shows new item; edit → detail persists;
  delete → list refreshes.

### Verification

```bash
task dev
# Browser: visit /, /new, /feedback/1
# DevTools → Lighthouse → Accessibility, run on each page
```

---

## Phase 5 — Validation, Error Handling, Logging

Tighten the rough edges from Phases 3–4 into the polished spec
behavior.

### Deliverables `[Must]`

- [ ] Pydantic validators for all rules in
      [spec — Validation Rules](spec/spec.md#validation-rules).
- [ ] Global exception handler returning the documented 404 / 422 / 500
      shapes.
- [ ] `debug=False` in production; stack traces never leak.
- [ ] Request-ID echoed in 4xx/5xx response bodies.
- [ ] Structured request log: method, path, status, duration_ms,
      request_id (JSON when `APP_ENV=production`).

### Definition of Done

- Sending `pain_level=0`, `pain_level=6`, whitespace-only `title`,
  `description` >5000 chars all return `422` with a useful detail.
- Production-mode 500 responses return generic body + log entry with
  full stack trace internally.
- Every log line carries the request ID.

### Verification

```bash
hatch run pytest tests/test_feedback_api.py -k "validation"
APP_ENV=production task dev
# trigger an unhandled error (e.g. patch a route to raise)
# verify response body is generic and logs contain stack trace + request id
```

---

## Phase 6 — Testing

Fill out the API test matrix and bring up the Playwright smoke suite.

### Deliverables `[Must]`

- [ ] `tests/conftest.py` — TestClient fixture, isolated Postgres test
      database, per-test `truncate_all_tables()` fixture.
- [ ] `tests/test_feedback_api.py` — full coverage of
      [spec — API Tests](spec/spec.md#api-tests-must).
- [ ] `tests/e2e/conftest.py` — Playwright fixtures, app + Postgres
      lifecycle, `chromium` only.
- [ ] `tests/e2e/test_feedback_smoke.py` — three smoke specs (create,
      edit, delete).
- [ ] `pytest.ini` (or `[tool.pytest.ini_options]` in `pyproject.toml`)
      registers the `e2e` marker.
- [ ] `task test:e2e` runs the smoke suite against a live stack.

### Definition of Done

- `task test` runs the API suite end to end against Postgres.
- `task test:e2e` runs the three Playwright specs against a live `task
  dev` + `task up` stack and passes consistently (no flake on three
  consecutive runs).
- The canary `test_patch_then_get_returns_fresh_state` is in the suite
  and green.
- Coverage for `src/feedback_triage/` is ≥ 85% (line) excluding the
  `static/` and `__init__.py` files.

### Verification

```bash
task test
task test:e2e
hatch run coverage report --skip-covered --fail-under=85
```

---

## Phase 7 — Container & Deployment

Build the image, deploy to Railway, run migrations as the pre-deploy
command.

### Deliverables `[Must]`

- [ ] `Containerfile` per
      [spec — Container Hardening](spec/spec.md#container-hardening-must)
      — multi-stage, non-root user, `HEALTHCHECK /health`, digest-pinned
      base, `PYTHONDONTWRITEBYTECODE=1` etc.
- [ ] Image builds locally via `docker build .` and runs.
- [ ] Railway service created, Postgres plugin attached.
- [ ] Pre-deploy command set to `alembic upgrade head`.
- [ ] Env vars set per
      [`deployment-notes.md`](deployment-notes.md#required-environment-variables).
- [ ] Healthcheck path set to `/health`.
- [ ] Hard usage limit set in Railway.
- [ ] App-sleeping enabled.

### Deliverables `[Should]`

- [ ] CI workflow builds and pushes the image to GHCR on tag.
- [ ] Container image scanned by `trivy` (or equivalent) in CI; high-
      severity findings fail the build.

### Definition of Done

- The deployed Railway URL serves `/`, `/api/v1/feedback`,
  `/api/v1/docs`, `/health`, and `/ready` correctly.
- A subsequent deploy that adds a column triggers the pre-deploy
  migration and lands without downtime.
- Manual `docker compose down -v && task up && task migrate` rebuild
  reaches a clean working state in under 2 minutes from clone.

### Verification

```bash
docker build -t feedback-triage:local .
docker run --rm -p 8000:8000 -e DATABASE_URL=... feedback-triage:local
# in another shell:
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/feedback

# After Railway deploy:
curl https://<your-railway-url>/health
curl https://<your-railway-url>/api/v1/feedback
```

---

## Phase 8 — Polish & Release

Last-mile work: README, screenshots, demo seed, `v1.0.0` tag.

### Deliverables `[Must]`

- [ ] README with all sections from
      [spec — README Sections to Include](spec/spec.md#readme-sections-to-include-must).
- [ ] Three screenshots checked into `docs/screenshots/` and embedded
      in the README.
- [ ] Mermaid architecture diagram in the README.
- [ ] Live demo URL and `/api/v1/docs` URL in the README header.
- [ ] `task seed` produces ~20 demo items covering every `Source` and
      `Status` value.
- [ ] All ADRs 045–054 written and merged.
- [ ] `CHANGELOG.md` regenerated for `v1.0.0`.

### Deliverables `[Should]`

- [ ] Short Loom or asciinema demo linked from the README.
- [ ] GitHub repo description and topics set
      (`fastapi`, `postgres`, `sqlmodel`, `playwright`, `railway`).

### Definition of Done

- `task release VERSION=v1.0.0` tags, pushes, and triggers
  `release.yml`.
- The GitHub Release page lists conventional-commit notes.
- A reviewer who has never seen the project can read the README, click
  the demo URL, and understand both *what it does* and *how it is
  built* in under 5 minutes.

### Verification

```bash
task check          # lint + typecheck + test
task test:e2e
task release VERSION=v1.0.0
# verify GHCR image, GitHub Release, and Railway deploy
```

---

## Cross-Phase Checklist

Things to keep green continuously, not just at phase boundaries:

- [ ] Every Alembic migration hand-reviewed, never trusted blind.
- [ ] No session reuse across requests (the canary test is the gate).
- [ ] No raw SQL string concatenation; SQLAlchemy parameter binding
      everywhere.
- [ ] No `async def` routes (revisit only via ADR).
- [ ] No Jinja, no JS bundler (revisit only via ADR).
- [ ] All GitHub Actions SHA-pinned.
- [ ] Every PR uses a Conventional Commit title.
- [ ] Pre-commit hooks pass on every commit.

---

## What "Done" Means for v1.0

The project is v1.0-shippable when **all** of the following are true:

1. Every `[Must]` deliverable above is checked.
2. `task check` and `task test:e2e` are green on a clean checkout.
3. Phases 7 and 8 produce a working public Railway URL with seeded data.
4. The README, the spec, and the ADRs do not contradict each other.
5. A reviewer reading only the README can clone, run, and inspect the
   project without asking questions.

Anything beyond that point belongs in
[spec — Future Improvements After v1.0](spec/spec.md#future-improvements-after-v10).

---

## Related docs

- [`spec/spec.md`](spec/spec.md) — canonical spec
- [`questions.md`](questions.md) — open questions and answers
- [`deployment-notes.md`](deployment-notes.md) — Railway operational notes
