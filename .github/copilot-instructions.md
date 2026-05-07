# Copilot Instructions

Guidelines for GitHub Copilot when working in this repository.

> **Repository status (May 2026):** v2.0 is **ratified** and is now
> the authoritative spec for all current work
> ([`docs/project/spec/spec-v2.md`](../docs/project/spec/spec-v2.md);
> phase plan in
> [`docs/project/spec/v2/implementation.md`](../docs/project/spec/v2/implementation.md)).
> [`docs/project/spec/spec-v1.md`](../docs/project/spec/spec-v1.md)
> remains the contract for the shipped v1.0 implementation and is
> retained as historical reference. The active package is
> `src/feedback_triage/`; the original boilerplate template lives
> under `attic/` as read-only reference material and is not imported
> by the live tree. `scripts/`, `tools/`, `mkdocs-hooks/`, and
> `.github/workflows/` are retained as general-purpose dev tooling;
> trim only when something proves wrong for this project after a
> green CI run.

---

## How This Project Works

### Overview

**Feedback Triage App** is a small full-stack web application: a FastAPI
backend exposing a JSON API under `/api/v1/`, backed by PostgreSQL 16, with
a frontend of static HTML + vanilla JS served from the same FastAPI process.
The single source of truth for tool configuration is `pyproject.toml`. The
canonical spec is [`docs/project/spec/spec-v1.md`](../docs/project/spec/spec-v1.md).

### Domain / Business Context

The app helps a product team manage incoming customer feedback: create,
list, view, update, and delete `feedback_item` rows with `source`,
`status`, and `pain_level` fields. Single resource, single table, no
auth, no multi-tenancy. Scope is intentionally narrow — see the spec's
**Non-Goals** and **Future Improvements** sections.

### Tech Stack

| Layer       | Choice                                                   |
| ----------- | -------------------------------------------------------- |
| API         | FastAPI (sync routes, `def` not `async def` in v1.0)     |
| ORM         | SQLModel on top of SQLAlchemy 2.x                        |
| Validation  | Pydantic v2 (request/response) + Postgres `CHECK` + enums |
| Database    | PostgreSQL 16 + Alembic migrations                       |
| Frontend    | Static HTML + vanilla JS + Fetch API (no Jinja, no SPA)  |
| Tests       | pytest + httpx TestClient + Playwright (e2e smoke)       |
| Build/env   | uv (env, lockfile, Python install) + hatchling + `hatch-vcs` (build backend, versions from git tags) |
| Tasks       | Task (`Taskfile.yml`)                                    |
| Container   | Multi-stage `Containerfile`, non-root, `HEALTHCHECK /health` |
| Deploy      | Railway, migrations via pre-deploy command               |

### Build & Environment — uv + hatchling

- **Project / env manager:** `uv`. `uv sync` installs from `uv.lock`;
  `uv run <cmd>` runs commands in the project env without manual
  activation; `uv add <pkg>` / `uv remove <pkg>` edits `pyproject.toml`
  and refreshes the lockfile in one step.
- **Lockfile:** `uv.lock` is committed. CI uses `uv sync --frozen`; lock
  drift fails the build.
- **Build backend:** `hatchling` with `hatch-vcs` for git-tag versioning,
  declared in `[build-system]`. uv invokes it on `uv build` and during
  Docker image builds. Do **not** swap the build backend.
- **Production image:** `uv pip install --system --frozen` — no venv
  inside the container.
- **Version** from git tags via `hatch-vcs`. Fallback: `0.0.0+<sha>`.

### Task Runner — Taskfile

Key tasks (run `task` for the full list):

| Task              | What it does                                              |
| ----------------- | --------------------------------------------------------- |
| `task dev`        | FastAPI with auto-reload                                  |
| `task up`/`down`  | `docker compose up/down` (Postgres)                       |
| `task migrate`    | `alembic upgrade head`                                    |
| `task migration`  | `alembic revision --autogenerate -m "..."`                |
| `task seed`       | populate demo data via `scripts/seed.py`                  |
| `task test`       | unit + API tests (pytest)                                 |
| `task test:e2e`   | Playwright smoke suite (gated, opt-in)                    |
| `task lint`       | ruff check                                                |
| `task fmt`        | ruff format                                               |
| `task typecheck`  | mypy                                                      |
| `task check`      | lint + typecheck + test (CI gate)                         |
| `task release`    | `git tag -a vX.Y.Z && git push origin vX.Y.Z`             |

### Pre-commit Hooks

Ruff, mypy, bandit, typos, actionlint, pip-audit, gitleaks, commitizen
(Conventional Commits). Config: `.pre-commit-config.yaml`. Inherited from
the template; trim to what this project actually needs after fork.

### GitHub Actions Workflows

All actions SHA-pinned ([ADR 004](../docs/adr/004-pin-action-shas.md)).
The full template workflow set is retained on the forked project as
general-purpose CI/dev tooling; SHA pins are refreshed at fork time.
Trim only if a specific workflow proves wrong for this project after
first green run. See `docs/workflows.md` and
`.github/workflows/.instructions.md`.

#### Repository guards — single switch policy

Every workflow ships with a three-clause `if:` guard:

```yaml
if: >-
  ${{
    github.repository == 'OWNER/REPO'
    || vars.ENABLE_WORKFLOWS == 'true'
    || vars.ENABLE_<NAME> == 'true'
  }}
```

**Do not replace the `OWNER/REPO` literal with the real slug.** This
project deliberately keeps `OWNER/REPO` so that the only on/off switch
is the `vars.ENABLE_WORKFLOWS` repository variable (already set to
`'true'` on `JoJo275/feedback-triage-app`). Per-workflow overrides
(`vars.ENABLE_<NAME>`) remain available for selectively disabling a
single workflow without touching YAML.

When adding new workflows, copy the same three-clause guard verbatim,
including the `OWNER/REPO` literal. Bulk find-replace passes that
substitute the real slug must be reverted.

### Documentation

MkDocs Material. See `docs/.instructions.md` and `docs/adr/.instructions.md`.
Serve: `uv run mkdocs serve`.

### Key Configuration Files

| File | Controls |
| --- | --- |
| `pyproject.toml` | Project metadata, deps, tool configs |
| `uv.lock` | Pinned dependency graph (committed) |
| `.pre-commit-config.yaml` | Hook definitions and stages |
| `Taskfile.yml` | Task runner shortcuts |
| `mkdocs.yml` | Documentation site config |
| `Containerfile` | Multi-stage container build (non-root, HEALTHCHECK) |
| `docker-compose.yml` | Local Postgres + app |
| `alembic.ini` | Migration config; reads `DATABASE_URL` from env |
| `release-please-config.json` | Release automation |
| `.env.example` | Documented env-var surface |
| `*.code-workspace` | VS Code settings. Use relative paths, not `${workspaceFolder}`. |

### Targeted Instruction Files

| File | Scope |
| --- | --- |
| `.github/workflows/.instructions.md` | Workflow YAML conventions |
| `scripts/.instructions.md` | Script conventions (rules) — see also [`docs/notes/script-conventions.md`](../docs/notes/script-conventions.md) for rationale and recommended additions |
| `docs/.instructions.md` | Documentation conventions |
| `docs/adr/.instructions.md` | ADR creation procedure |
| `tests/.instructions.md` | Test conventions |
| `.github/instructions/python.instructions.md` | Python style, imports, type hints, security |
| `.github/instructions/tests.instructions.md` | pytest conventions, fixtures, coverage |

This file covers **project-wide** rules. Prefer the targeted instruction
file for file-type-specific details.

---

## Working Style

### Spec Is Source of Truth

When in doubt about scope, schema, or a decision, read
[`docs/project/spec/spec-v1.md`](../docs/project/spec/spec-v1.md) before asking.
The spec uses **Must / Should / Nice / Defer** tiers — respect them. Do not
implement Should items before Must is green.

### Keep Related Files in Sync

When updating a file, update dependent files too. The spec, the README, the
ADRs, the OpenAPI shape, and the Playwright smoke tests are linked surfaces
— if one moves, check the others.

### Provide Feedback and Pushback

Push back when a request introduces unnecessary complexity, conflicts with
the spec or an ADR, or has a simpler alternative. Be direct: state the
problem, explain why, suggest an alternative.

### Clean Up Dead Code

Remove dead code when encountered. Grep first to confirm it's unused.
Preserve public API and documented extension points.

### Session Recap

After significant sessions, provide a brief recap: what changed, why,
impact, what to watch for, decisions made. Skip for trivial single-file edits.

### Surface Issues

Proactively flag issues, risks, or anomalies noticed during any session —
even if unrelated to the current task. Keep flags brief: what's wrong, why
it matters, suggested next step.

### Verify Before Finishing

- **Code** — run `task test` (and `task test:e2e` if frontend touched)
- **Workflows** — run `actionlint`
- **Hooks** — `pre-commit run <hook-id> --all-files`
- **SHA-pinned actions** — verify the commit SHA exists upstream
- **Migrations** — every Alembic migration is hand-reviewed after
  autogenerate; never trust the autogenerated diff blind

### Don't Churn

Avoid unnecessary rewrites, renames, or restructurings that don't fix a
bug or deliver a requested feature. Churn creates merge conflicts, pollutes
blame history, and wastes CI minutes.

### Tone

Direct and factual. No filler praise or diplomatic hedging. If something
is broken, say so.

---

## Review Priorities

1. **Spec alignment** — Changes should match `docs/project/spec/spec-v1.md`. If they don't, either update the spec first or push back.
2. **Type hints** — Public functions in `src/feedback_triage/` must be annotated; mypy strict.
3. **Tests** — Changes include or update API tests; UI changes update the Playwright smoke suite if a smoke path is affected.
4. **Security** — Flag hardcoded secrets, `shell=True`, raw SQL string concatenation, `yaml.load()` without `safe_load`, unbounded payloads.
5. **DB invariants** — Session-per-request, no sessions on `app.state` / module globals; migrations hand-reviewed; native enums + CHECK constraints in every schema change.
6. **Imports** — Must work with `src/` layout. `from feedback_triage.X import Y`, never `from src...`.
7. **Docstrings** — Google style on public functions.
8. **New scripts** — Any new file under `scripts/` follows the
   "Read this before creating a new script" checklist at the top of
   [`scripts/.instructions.md`](../scripts/.instructions.md):
   `ExitCode` from `_ui`, `--smoke`, `--quiet`/`--verbose`, `--version`,
   `epilog=` examples, single `_load_env()` helper, shebang +
   executable bit, fail-closed integrity checks for any download.
   Reject the change if any item is missing.

### General Guidance

- Prefer minimal diffs — Ruff handles formatting
- Use `uv run` / `uv sync` for envs, never bare `pip install`
- Don't create `.venv` manually; `uv sync` creates it
- Do not introduce Jinja or a JS bundler without an ADR

---

## Conventions

### Python

- Absolute imports: `from feedback_triage.module import func`
- `from __future__ import annotations` at top of every file
- Type hints on all public functions; mypy strict mode
- Google style docstrings; constants in UPPER_SNAKE_CASE
- `pathlib.Path` over `os.path`; `subprocess.run()` with arg lists (never `shell=True`)
- `tomllib` for TOML; `importlib.metadata` for package introspection
- Routes are `def`, not `async def`, in v1.0 (sync DB driver)

### FastAPI / API

- All JSON routes under `/api/v1/`; HTML page routes (`/`, `/new`, `/feedback/{id}`) and probes (`/health`, `/ready`) stay unversioned
- Every route declares an explicit `response_model=`
- Group routes with `tags=[...]` so `/api/v1/docs` is organized
- List endpoints return an envelope (`items`, `total`, `skip`, `limit`), not a bare array
- `PATCH` for partial updates, `PUT` is not used in v1.0
- Datetimes serialized as ISO 8601 with `Z` suffix, UTC, microsecond precision

### Database

- One `feedback_item` table; do not introduce a second table without an ADR
- Native Postgres enums (`source_enum`, `status_enum`) + DB `CHECK` constraints; never plain strings
- `updated_at` maintained by a `BEFORE UPDATE` trigger, not ORM `onupdate`
- Session-per-request via `get_db`; `expire_on_commit=False`; commit/rollback live in `get_db`, not handlers
- Alembic with `compare_type=True` and `compare_server_default=True`; every migration hand-reviewed
- Use `text` + `CHECK length(...) <= N`, not `varchar(n)`

### Frontend

- Static HTML files served via `StaticFiles`; **no Jinja, no bundler, no SPA framework**
- Vanilla JS + Fetch API for dynamic behavior
- **Semantic HTML.** Use the right tag for what an element *is* (`<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<button>`, `<a>`, `<form>`, `<label>`, `<table>`, `<dialog>`, `<details>`). `<div>` means: generic block container with no semantic meaning — use it only when you need a wrapper for layout/styling and no better tag applies. `<span>` is the same rule inline.
- **Tags carry meaning, classes carry style.** Never style by `id` or `data-*`. Never put `role="button"` on a `<div>` — use `<button>`. ARIA roles are only for cases where no native tag exists.
- Every `<input>` has a paired `<label for="…">`; actions that *do* something are `<button>`, actions that *navigate* are `<a>`.
- Heading levels are sequential (one `<h1>` per page, no skipping levels). Every page has a skip-link to `#main`.
- CSS: tokens (custom properties) for color/spacing/radius; no `!important` outside `prefers-reduced-motion`; `:focus-visible` for focus styles; `rem`/`ch` for sizing. No CSS preprocessor, no Tailwind/Bootstrap import — needs an ADR.
- Same-origin delivery; CSRF is N/A in v1.0 (no cookie auth).
- See [`docs/notes/frontend-conventions.md`](../docs/notes/frontend-conventions.md) for rationale, the full tag-selection table, and the accessibility checklist.

### Testing

- Postgres for tests, never SQLite (dialect parity)
- API tests use httpx TestClient; one transaction per test, truncate fixture between tests
- Playwright smoke suite is gated behind `@pytest.mark.e2e`, run via `task test:e2e`
- The canary test for session reuse is `test_patch_then_get_returns_fresh_state` — keep it green

### Ruff — Linting & Formatting

Ruff handles both linting and formatting as pre-commit hooks. **Write code
that passes on the first try.** Full config in `pyproject.toml` under
`[tool.ruff]`.

Validate before committing:

    uv run ruff check src/ scripts/ tests/    # lint
    uv run ruff format --check src/ scripts/  # format check

Key conventions: double quotes, trailing commas, isort import order
(stdlib → third-party → local), no `print()` in `src/` (T20), pathlib
over os.path (PTH), modern 3.11+ syntax (UP), comprehensions over
`list()`/`dict()` calls (C4), `list.extend()` over append-in-loop (PERF401).
For any specific rule: `ruff rule <CODE>`.

### Bandit — Security Linting

Pre-commit hook. Config in `pyproject.toml` under `[tool.bandit]`.
Validate: `uv run bandit -c pyproject.toml -r src/`

Key rules: no `eval()`/`exec()`, no `pickle` on untrusted data, no
`shell=True`, no hardcoded `/tmp` (use `tempfile`), `yaml.safe_load()`
not `yaml.load()`, parameterized SQL queries.

### Project Structure

- Source: `src/feedback_triage/`
- Tests: `tests/` (API) and `tests/e2e/` (Playwright)
- Scripts: `scripts/`
- Docs: `docs/` · Spec: `docs/project/spec/spec-v1.md` · ADRs: `docs/adr/`

### Git & PRs

- Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `ci:`, `test:`, `refactor:`
- One logical change per commit; PR titles follow conventional format
- Commit message template in `.gitmessage.txt`: `<type>(<scope>): <description>`
  with body sections `Why:`, `What changed:`, `How tested:`

---

## Ignore / Don't Flag

- **E501** — Disabled; don't request rewrapping
- **Generated files** — `*.egg-info/`, `__pycache__/`, `.venv/`
- **Types in tests** — See `tests/.instructions.md`

## Architecture References

- **Spec:** `docs/project/spec/spec-v1.md` (canonical; everything below is cross-reference)
- **ADRs:** `docs/adr/` — stack and process decisions inherited from the template plus project-specific ADRs (045–054, see spec's "ADRs to Write" table)
- **Workflows:** `docs/workflows.md`

Inherited template ADRs that still govern this project: 001 (src/ layout),
002 (pyproject), 003 (separate workflow files), 004 (pin SHAs), 005 (ruff),
006 (pytest), 007 (mypy), 008 (pre-commit), 009 (Conventional Commits),
010 (Dependabot), 016 (Hatch — env-manager half superseded by ADR 055; build-backend half still authoritative), 017 (Task), 018 (bandit), 019 (Containerfile),
020 (MkDocs), 021 (release pipeline), 022 (rebase merge), 023 (branch
protection), 024 (CI gate), 044 (Copilot instructions).

ADRs that need rewriting on fork (still present, wrong content for this project):
014 (no template engine), 025 (container strategy), 027 (database strategy),
029 (testing strategy), 031 (script conventions).

**When numbers here conflict with the docs, the docs win.**

## Common Issues

1. Missing editable install — `uv sync` handles it for the src/ layout; do not run bare `pip install -e .`.
2. Wrong imports — use `feedback_triage`, not `src`.
3. Mutable default arguments — `def func(items=[])` is a bug.
4. Lockfile drift — after editing `pyproject.toml` directly, run `uv lock` and commit `uv.lock` in the same change.
5. Bare `pip install` outside venv — always use `uv` (`uv add`, `uv sync`) or `uv tool` for global tools.
6. Sessions reused across requests — see ADR 048 (to be written) and the canary test.
7. Migrations run from `main.py` on boot — don't; use the Railway pre-deploy command.

## Known Limitations

See [`docs/known-issues.md`](../docs/known-issues.md) for the canonical list.
