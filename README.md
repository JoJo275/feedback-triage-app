# feedback-triage-app

A small, portfolio-grade FastAPI + PostgreSQL service for triaging
incoming customer feedback. Create, list, view, update, and delete
`feedback_item` rows with `source`, `status`, and `pain_level` fields.

> Status: **pre-v0.1**. The Pre-Phase fork from
> [`simple-python-boilerplate`](https://github.com/JoJo275/simple-python-boilerplate)
> is complete; Phase 1 (project skeleton) is the next milestone. See
> [`docs/project/implementation.md`](docs/project/implementation.md).

- **Live demo:** _added once Phase 7 deploys to Railway_
- **API docs:** _added once Phase 3 completes — will be at_ `<deploy-url>/api/v1/docs`
- **Spec:** [`docs/project/spec/spec.md`](docs/project/spec/spec.md)

## Screenshots

_Added once Phase 4 completes. Stored under_ `docs/screenshots/`.

1. List page with seeded data
2. Detail / edit page mid-edit
3. `/api/v1/docs` Swagger UI

## Features

- Single resource (`feedback_item`) with sources, statuses, and a 1–5
  pain level enforced at the database layer with native enums and CHECK
  constraints.
- JSON CRUD API under `/api/v1/feedback` with offset pagination, filter,
  and sort.
- Static HTML + vanilla JS frontend served from the same origin.
- `/health` (liveness) and `/ready` (DB-aware, 2s timeout) probes.
- Hand-reviewed Alembic migrations with `compare_type` and
  `compare_server_default` enabled.
- Postgres-backed test suite plus a gated Playwright smoke suite.
- Multi-stage hardened container image, non-root, healthcheck-aware.

## Tech Stack

| Layer       | Choice                                                   |
| ----------- | -------------------------------------------------------- |
| API         | FastAPI                                                  |
| ORM         | SQLModel on top of SQLAlchemy 2.x                        |
| Validation  | Pydantic v2 + native Postgres enums + CHECK constraints  |
| Database    | PostgreSQL 16 + Alembic migrations                       |
| Frontend    | Static HTML + vanilla JS + Fetch API                     |
| Tests       | pytest + httpx TestClient + Playwright (e2e smoke)       |
| Build / env | uv (env, lock, Python install) + hatchling + hatch-vcs   |
| Tasks       | Task (`Taskfile.yml`)                                    |
| Container   | Multi-stage `Containerfile`, non-root, `HEALTHCHECK /health` |
| Deploy      | Railway (continuous deploy from `main`)                  |

## Architecture

```mermaid
flowchart LR
    Browser[Browser] -- HTML/CSS/JS --> Static[StaticFiles\n /static/]
    Browser -- fetch JSON --> API["FastAPI\n /api/v1/feedback"]
    API -->|SQLModel session-per-request| DB[(PostgreSQL 16)]
    Probe[/health, /ready/] --> API
```

## Local Setup

Prerequisites: [uv](https://docs.astral.sh/uv/), [Task](https://taskfile.dev/),
[Docker](https://docs.docker.com/get-docker/).

```bash
git clone https://github.com/JoJo275/feedback-triage-app
cd feedback-triage-app
cp .env.example .env                    # then edit POSTGRES_PASSWORD
uv sync                                 # creates .venv from uv.lock
task up                                 # start Postgres
task migrate                            # apply schema (after Phase 2)
task seed                               # demo data (after Phase 2)
task dev                                # FastAPI on http://localhost:8000
```

## Running Tests

```bash
task test       # API + unit suite (excludes e2e)
task test:e2e   # Playwright smoke suite (requires task up + task dev)
task check      # lint + format + typecheck + test (CI gate)
```

## Deployment

Continuous deploy on every merge to `main`. Railway pulls the repo,
runs `alembic upgrade head` as the pre-deploy command, then starts the
container. See [`docs/project/deployment-notes.md`](docs/project/deployment-notes.md)
for the full env-var surface and operational checklist.

## API Reference

OpenAPI / Swagger UI at `/api/v1/docs` once deployed. Do not duplicate
the schema in this README.

## Future Improvements

A trimmed list — the full set lives in
[`docs/project/spec/spec.md#future-improvements`](docs/project/spec/spec.md#future-improvements).

- Authentication and per-user feedback ownership
- Cursor / keyset pagination for large datasets
- Full-text search on title + description
- Duplicate detection on `POST /feedback`
- AI-assisted summarisation of feedback batches

## License

[Apache 2.0](LICENSE).
