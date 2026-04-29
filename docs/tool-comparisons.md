# Tool Comparisons

Why this project picked the tools it did, with the alternatives we
considered. For the formal decisions and dates, see the
[ADR index](adr/README.md). This page is the prose summary that
makes the trade-offs visible at a glance.

---

## Project / environment manager — `uv` over `poetry`, `pip-tools`, and `hatch envs`

| Dimension | uv | poetry | pip-tools | hatch envs |
| --- | --- | --- | --- | --- |
| Speed (cold sync) | seconds | tens of seconds | minute+ | tens of seconds |
| Lockfile committed? | Yes (`uv.lock`) | Yes (`poetry.lock`) | Yes (`requirements*.txt`) | No |
| Manages Python toolchains | Yes (downloads on demand) | Optional (pyenv) | No | No |
| Build-backend opinion | Backend-agnostic; we keep `hatchling` | Bundled (`poetry-core`) | N/A | Bundled (`hatchling`) |
| `--frozen` for CI | Yes | Yes | implicit | partial |
| PEP 621 metadata | Native | Migrating | Hand-rolled | Native |
| Single-binary CLI | Yes (Rust) | Python | Python | Python |

**Decision** — `uv` (see [ADR 055](adr/055-uv-as-project-manager.md)). It
is dramatically faster, manages Python toolchains itself, keeps the
build backend choice ours, and reads `pyproject.toml` directly. We
keep `hatchling` + `hatch-vcs` for the build backend role only — see
[ADR 016](adr/016-hatchling-and-hatch.md).

---

## Build backend — `hatchling` over `setuptools`, `flit`, `poetry-core`, `pdm-backend`

`hatchling` is small, PEP-621-native, and integrates cleanly with
`hatch-vcs` for git-tag versioning. The other backends each have
strengths but pull in ecosystem opinions we don't need (notably,
`poetry-core` ties versioning to the poetry CLI, and setuptools is
heavier than the project requires).

---

## Task runner — `Task` over `make`, `nox`, `invoke`, `just`

Decision: [`Task`](https://taskfile.dev/) (Go binary, YAML config). See
[ADR 017](adr/017-task-runner.md).

- `make` — fragile on Windows; tab-indentation hostility.
- `nox` / `tox` — they're test-matrix runners, not generic shortcuts.
  We use `uv run --python 3.X pytest` for matrix runs instead.
- `invoke` — Python-only; pulls a runtime dep into a CLI surface.
- `just` — strong contender; `Task` won on YAML readability and
  preexisting team familiarity.

---

## Web framework — `FastAPI` over `Flask`, `Django`, `Starlette` raw

FastAPI is the best fit for "small JSON API + tiny static frontend":
Pydantic v2 integration, automatic OpenAPI, and a thin enough surface
that we can run sync routes against a sync DB driver in v1.0
(see [ADR 050](adr/050-sync-db-driver-v1.md)).

- `Flask` — fine, but no Pydantic integration; OpenAPI requires extra
  glue.
- `Django` — vastly oversized for a single-table CRUD app.
- `Starlette` raw — what FastAPI is built on; we'd reinvent the
  request/response model.

---

## ORM — `SQLModel` over plain `SQLAlchemy 2.x`, `peewee`, `pony`, `tortoise`

Decision: [`SQLModel`](https://sqlmodel.tiangolo.com/), see
[ADR 047](adr/047-sqlmodel-over-sqlalchemy.md).

- `SQLAlchemy 2.x` — `SQLModel` is a thin layer on top of it; we get
  Pydantic-typed models for free without losing SQLAlchemy's escape
  hatches.
- `peewee` / `pony` — small ecosystems, weaker Postgres feature
  coverage (enums, partial indexes).
- `tortoise` — async-first; we want sync routes in v1.0.

---

## Database — `PostgreSQL 16` over `SQLite`, `MySQL`

Postgres for production *and* tests
([ADR 054](adr/054-postgres-for-tests.md)). Native enums + `CHECK`
constraints + per-row triggers all live in the schema, where they
belong. SQLite cannot enforce those, and dialect mismatch in tests
masks real bugs. MySQL is fine but offers no features we need that
Postgres doesn't.

---

## Frontend — static HTML + vanilla JS over `Jinja`, `htmx`, React/Vue

Decision: [ADR 051](adr/051-static-html-vanilla-js.md). The app has
three pages and a Fetch-API list view. A SPA framework or even a
template engine would be more code than the feature it implements.
htmx was a strong contender; we keep it as a future option but don't
ship it for v1.0.

---

## Tests — `pytest + httpx` over `unittest`, `requests`-against-live-server

`pytest` for the framework ([ADR 006](adr/006-pytest-for-testing.md)),
`httpx.TestClient` to drive the FastAPI app in-process. Real Postgres
under the test process (no SQLite, no mocks of the DB session). See
[ADR 029](adr/029-testing-strategy.md).

---

## Linter / formatter — `Ruff` over `flake8 + isort + black + pyupgrade`

[`Ruff`](https://docs.astral.sh/ruff/) is one Rust binary that
replaces all of them, with the same rule semantics. See
[ADR 005](adr/005-ruff-for-linting-formatting.md).

---

## Type checker — `mypy` over `pyright`, `pyre`, `ty`

`mypy` strict mode against `src/feedback_triage`
([ADR 007](adr/007-mypy-for-type-checking.md)). `pyright` is faster
but its strictness flags don't map 1:1 with mypy's; we'd lose CI
parity with what most contributors run locally. `ty` (astral) is
promising and may revisit before v1.0.

---

## Container build / runtime — `uv pip install --system` over a venv-in-image

A venv inside a container is the worst of both worlds: extra layers,
extra activation logic, no isolation benefit (the container *is* the
isolation). We install the wheel system-wide in the runtime stage. See
[ADR 025](adr/025-container-strategy.md).

---

## Migrations — `Alembic` over `yoyo`, `dbmate`, ad-hoc SQL

Alembic is the standard with SQLAlchemy + SQLModel, supports
`compare_type=True` and `compare_server_default=True`, and produces a
hand-reviewable diff for every schema change. Migrations run as a
Railway pre-deploy command, not from `main.py` — see
[ADR 053](adr/053-migrations-as-pre-deploy-command.md).

---

## CI runner — `GitHub Actions` over `CircleCI`, `GitLab CI`, `Buildkite`

The repo lives on GitHub; using anything else introduces credential
plumbing we don't need. All third-party actions are SHA-pinned
([ADR 004](adr/004-pin-action-shas.md)).

---

## Release automation — `release-please` over `semantic-release`, manual

`release-please` reads our Conventional Commit history
([ADR 009](adr/009-conventional-commits.md)) and proposes the next
version bump as a PR. We keep the human-in-the-loop step deliberately;
fully automated tag-on-merge has bitten us in past projects.

---

## See also

- [ADR index](adr/README.md) — formal decisions
- [tooling.md](tooling.md) — every tool, what it does, where it's
  configured
- [workflows.md](workflows.md) — CI workflows that run these tools
