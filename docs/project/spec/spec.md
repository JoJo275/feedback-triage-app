# Feedback Triage App — Project Guide

## Recommended GitHub Repository Title

**`feedback-triage-app`**

---

## Project Summary

**Feedback Triage App** is a small full-stack web application for collecting,
viewing, updating, and managing product feedback items.

The project is built around a **FastAPI backend** that exposes JSON endpoints
and a **simple frontend web app** that consumes those endpoints. The purpose
is to learn practical full-stack SaaS foundations without bloating the project
into a large product.

This project is a stronger portfolio piece than a generic notes or todo API
because it models a real SaaS workflow: collecting customer pain points,
organizing them, and triaging what should happen next.

---

## Core Goal

Build a small but realistic application that teaches:

- backend API design
- database modeling
- request and response handling
- validation
- frontend integration
- CRUD patterns
- testing
- Docker-based local development
- deployment to a cloud platform

---

## Product Idea

The app helps a founder or product team manage incoming feedback.

A user should be able to:

- create a feedback item
- view all feedback items
- open one feedback item in detail
- update its status, source, or pain level
- delete bad, duplicate, or irrelevant items
- filter or sort items in a simple way

This is not meant to be a complete production SaaS. It is an MVP and learning
project.

---

## Recommended Scope

Keep the project intentionally small.

### Include

- FastAPI backend
- PostgreSQL database
- SQLAlchemy or SQLModel models
- Pydantic validation
- frontend web app with HTML, CSS, and JavaScript
- CRUD operations
- pagination on the list endpoint
- basic filtering and sorting
- tests
- Docker
- deployment

### Do Not Include Yet

- authentication
- teams or organizations
- comments
- attachments
- email ingestion
- AI summarization
- voting
- analytics dashboards
- billing
- role permissions

Those would be scope creep for this version.

---

## Recommended Tech Stack

### Backend

- **FastAPI** — API framework
- **PostgreSQL** — relational database
- **SQLModel** — ORM / database layer (Pydantic + SQLAlchemy in one model)
- **Alembic** — database migrations
- **Pydantic** — request and response validation
- **psycopg (v3)** — Postgres driver
- **pytest** + **httpx / TestClient** — API tests

> **Why SQLModel over plain SQLAlchemy?** SQLModel is built by the FastAPI
> author and unifies the ORM model and the Pydantic schema into one class.
> For a single-table CRUD app, that removes a lot of boilerplate. If the
> project ever outgrows it, SQLModel is just SQLAlchemy underneath, so
> migration is straightforward.
>
> **Why Alembic from day one?** `Base.metadata.create_all()` works for the
> first commit and breaks the moment you add a column. Alembic adds ~15
> minutes of setup and saves you from rewriting your schema history later.

### Frontend

- **HTML**
- **CSS**
- **Vanilla JavaScript**
- **Fetch API** for calling the FastAPI backend

### DevOps / Tooling

- **Hatch** — Python environment and build management
- **Task** (Taskfile) — task runner / command shortcuts
- **uv** (optional) — fast resolver, can back Hatch envs via `installer = "uv"`
- **Docker** + **docker-compose** — local Postgres and reproducible app container
- **Railway** — deployment target (or any equivalent host)
- **pre-commit** — ruff, mypy, bandit on every commit

> **Why Hatch?** It manages virtualenvs, build, and version-from-git in one
> tool. It reads `pyproject.toml` directly, so there is no separate
> `requirements.txt` to drift. For a portfolio project it signals that you
> know modern Python packaging rather than just `pip install -r`.
>
> **Why Task?** A `Taskfile.yml` gives you discoverable, named commands
> (`task dev`, `task test`, `task migrate`) that work the same on Windows,
> macOS, and Linux. It is faster to type than long Hatch invocations and
> doubles as living documentation of how to operate the project. Make works
> too, but Make on Windows is awkward; Task is a single Go binary.

### Recommendation on frontend choice

Use **plain HTML/CSS/JS**, not React, for this project.

Why:

- faster to finish
- less setup overhead
- easier to focus on backend learning
- enough to prove you can connect a UI to an API

---

## High-Level Architecture

The app has two main parts:

### 1. Backend API

The backend:

- receives HTTP requests
- validates input
- talks to PostgreSQL
- returns JSON responses

### 2. Frontend Web App

The frontend:

- displays feedback items
- sends create/update/delete requests to the backend
- renders the returned data for the user

### Data Flow

1. User interacts with the frontend
2. Frontend sends request to FastAPI
3. FastAPI validates the request
4. FastAPI reads or writes to PostgreSQL
5. FastAPI returns JSON
6. Frontend updates the interface

---

## Main Resource

The main resource is a **Feedback Item**.

Each feedback item represents one piece of customer or user feedback that
should be reviewed and triaged.

### Suggested Fields

| Field        | Type            | Rules                                              |
| ------------ | --------------- | -------------------------------------------------- |
| id           | integer         | Auto-generated, unique, primary key                |
| title        | string          | Required, max 200 characters                       |
| description  | string \| null  | Optional, free text                                |
| source       | enum (`Source`) | Required, one of the allowed source values         |
| pain_level   | integer         | 1–5, enforced by `CHECK` constraint                |
| status       | enum (`Status`) | Default `new`, one of the allowed status values    |
| created_at   | timestamptz     | Auto-set on creation (`server_default=func.now()`) |
| updated_at   | timestamptz     | Auto-set on update (`onupdate=func.now()`)         |

> **Why enums and a CHECK constraint instead of plain strings?** The spec
> already restricts `source` and `status` to a fixed list. Encoding that as
> a Postgres `ENUM` (or `VARCHAR` + `CHECK`) means the database itself
> rejects bad data, not just Pydantic. Defense in depth: a buggy migration,
> a manual `psql` insert, or a future second client cannot corrupt the
> table.
>
> **Why `timestamptz` instead of `datetime`?** Always store timestamps in
> UTC with timezone information. Naive datetimes silently break the moment
> you deploy across regions or compare to `now()`.

---

## Recommended Allowed Values

### Source

Suggested allowed values:

- `email`
- `interview`
- `reddit`
- `support`
- `app_store`
- `twitter`
- `other`

### Status

Suggested allowed values:

- `new`
- `reviewing`
- `planned`
- `rejected`

These are enough for version 1.

---

## API Endpoints

Use one clean REST resource.

### Create

`POST /feedback`

Creates a new feedback item.

### List

`GET /feedback`

Returns a paginated **envelope** of feedback items:

```json
{
  "items": [ /* FeedbackResponse, ... */ ],
  "total": 137,
  "skip": 0,
  "limit": 20
}
```

> **Why an envelope, not a bare array?** Frontends always need `total` to
> render "Page 2 of 7." Returning a bare array forces a second request or a
> custom header, which both UIs and tests get wrong. Lock the shape now.

Query params:

| Param     | Type    | Default | Allowed values                                   |
| --------- | ------- | ------- | ------------------------------------------------ |
| `skip`    | integer | `0`     | `>= 0`                                           |
| `limit`   | integer | `20`    | `1..100`                                         |
| `status`  | enum    | —       | any `Status` value                               |
| `source`  | enum    | —       | any `Source` value                               |
| `sort_by` | string  | `-created_at` | `created_at`, `pain_level`, `status`, `source` (prefix `-` for descending) |

> **Why an explicit allow-list of sortable fields?** "Sort by anything" is
> a SQL injection / surprise-index risk. Reject anything else with `422`.

### Get One

`GET /feedback/{id}`

Returns a single feedback item.

### Update (partial)

`PATCH /feedback/{id}`

Updates one or more fields of an existing feedback item. All body fields
are optional.

> **Why `PATCH` and not `PUT`?** The spec calls for partial updates (every
> field optional). That is `PATCH` semantics. `PUT` means "replace the
> whole resource" and should require every field. Mixing them is a common
> bug and a frequent interview question — get it right from the start.

### Delete

`DELETE /feedback/{id}`

Deletes a feedback item. Returns `204 No Content`.

### Health and readiness

`GET /health` — process is alive (returns `{"status": "ok"}` without
touching the database).

`GET /ready` — process is alive **and** can reach the database (executes
`SELECT 1`). Returns `503` if the DB is unreachable.

> **Why split them?** Liveness and readiness answer different questions.
> A platform restarts on liveness failure; it just stops sending traffic on
> readiness failure. Conflating them causes restart loops when the DB
> hiccups. This is the same convention Kubernetes and most PaaS providers
> use, including Railway.

### CORS

If the frontend is ever served from a different origin (even
`http://localhost:5173` while iterating on JS, or `127.0.0.1` vs
`localhost`), enable `fastapi.middleware.cors.CORSMiddleware` with an
explicit allow-list driven by an env var (`CORS_ALLOWED_ORIGINS`). Do
**not** use `allow_origins=["*"]` in production.

---

## Example Backend Schemas

Create three main schemas.

### FeedbackCreate

Used when creating a feedback item.

Fields:

- title
- description
- source
- pain_level
- status with default `new`

### FeedbackUpdate

Used when updating a feedback item. All fields optional so partial updates
are easy.

### FeedbackResponse

Used when returning data to the frontend.

Includes:

- id
- title
- description
- source
- pain_level
- status
- created_at
- updated_at

---

## Frontend Pages

Keep the frontend simple.

### 1. Dashboard / Feedback List

Route example: `/`

Shows:

- all feedback items
- title
- source
- pain level
- status
- created date
- edit and delete controls
- filters for status or source

### 2. Create Feedback Page

Route example: `/new`

Shows a form with:

- title
- description
- source
- pain level
- status

### 3. Feedback Detail / Edit Page

Route example: `/feedback/:id`

Shows:

- full feedback item
- editable fields
- save button
- delete button

This is enough for an MVP.

---

## Frontend Behavior

Use JavaScript and the Fetch API for the main interactions.

### Examples

- load all feedback on page load
- submit new feedback with a form
- update an item without a full page reload if convenient
- delete an item and remove it from the UI
- filter the list by status or source

### Recommendation

Keep the UI simple and clear. Do not try to make it look like a polished SaaS
dashboard yet. Functionality matters more than visual ambition for this
version.

---

## Suggested UI Layout

### Feedback List Page

- top header with app name
- create button
- filter dropdowns
- table or card list of feedback items

### Create / Edit Form

- stacked form layout
- clean labels
- textarea for description
- dropdown for source
- dropdown for status
- small numeric input or select for pain level

### Styling Direction

- simple neutral palette
- readable spacing
- clear forms
- responsive layout
- no framework required unless you want Bootstrap

### Recommendation

Using **Bootstrap** is acceptable if you want faster styling.

---

## Suggested Project Structure

```text
feedback-triage-app/
├── src/
│   └── feedback_triage/
│       ├── __init__.py
│       ├── main.py            # FastAPI app factory, routers, middleware
│       ├── config.py          # Settings via pydantic-settings
│       ├── database.py        # engine, session, get_db dependency
│       ├── models.py          # SQLModel tables
│       ├── schemas.py         # request/response Pydantic models
│       ├── enums.py           # Source, Status
│       ├── crud.py            # DB-layer functions
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── feedback.py
│       │   └── health.py
│       ├── templates/
│       │   ├── base.html
│       │   ├── index.html
│       │   ├── new_feedback.html
│       │   └── feedback_detail.html
│       └── static/
│           ├── css/styles.css
│           └── js/
│               ├── index.js
│               ├── new_feedback.js
│               └── feedback_detail.js
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_feedback_api.py
├── scripts/
│   └── seed.py                # populate demo data
├── Containerfile              # or Dockerfile
├── docker-compose.yml
├── pyproject.toml             # deps + Hatch envs (no requirements.txt)
├── Taskfile.yml
├── alembic.ini
├── .env.example
├── .pre-commit-config.yaml
└── README.md
```

> **Why `src/` layout?** It prevents accidentally importing the package
> from the working directory instead of the installed copy. Tests then
> exercise the actual installed code path. This matches the convention
> used in the surrounding workspace template (see ADR 001).
>
> **Why no `requirements.txt`?** Hatch reads dependencies from
> `pyproject.toml` directly. Keeping a second file in sync is a known
> source of drift. If a deploy target needs a flat list, generate it with
> `hatch dep show requirements > requirements.txt` in CI.

---

## Database Model Recommendation

Use one main model.

### FeedbackItem

Suggested fields:

- id
- title
- description
- source
- pain_level
- status
- created_at
- updated_at

This project works best with a single strong resource. Do not split it into
users, teams, labels, comments, and history tables yet.

---

## Validation Rules

Good validation makes the project feel more real.

### Suggested Rules

- `title` is required, non-empty after `.strip()`
- `title` max length 200
- `description` max length 5000 (prevents abusive payloads)
- `pain_level` must be between 1 and 5 inclusive (Pydantic `Field(ge=1, le=5)` **and** Postgres `CHECK`)
- `source` must be one of the allowed values (enum, not string)
- `status` must be one of the allowed values (enum, not string)
- `sort_by` must be one of the allow-listed fields
- `limit` must be between 1 and 100
- invalid data returns `422`
- missing item returns `404`

> **Why both Pydantic and a DB constraint?** Pydantic protects the API
> boundary. The DB constraint protects everything else (migrations,
> direct SQL, future services). They are not redundant; they cover
> different threat models.

---

## Error Handling

Handle these clearly:

### 404

When a feedback item does not exist:

```json
{ "detail": "Feedback item not found" }
```

### 422

Invalid request data should be handled automatically by FastAPI and Pydantic.

### 500

Return a generic message for unexpected errors. Do not leak raw database
errors to the client.

---

## Configuration & Environment Variables

Load config with **`pydantic-settings`** in `src/feedback_triage/config.py`.
Never read `os.environ` ad-hoc throughout the codebase.

### `.env.example`

```env
# Runtime
APP_ENV=development           # development | test | production
LOG_LEVEL=INFO                # DEBUG | INFO | WARNING | ERROR
PORT=8000

# Database
DATABASE_URL=postgresql+psycopg://feedback:feedback@localhost:5432/feedback

# CORS (comma-separated origins; empty = same-origin only)
CORS_ALLOWED_ORIGINS=http://localhost:8000

# Pagination defaults (optional overrides)
PAGE_SIZE_DEFAULT=20
PAGE_SIZE_MAX=100
```

> **Why pydantic-settings?** Strongly typed config with validation at
> startup. A missing or malformed `DATABASE_URL` fails fast on boot
> instead of crashing on the first request.

---

## Seed Data

Provide `scripts/seed.py` that inserts ~20 demo feedback items covering
every `Source` and `Status` value. Wire it into Task as `task seed`.

> **Why?** An empty deployment demos badly. Reviewers (and your future
> self) want to load the public URL and see something. Seed data also
> doubles as a quick way to verify a fresh database after migrations.

---

## Tooling — Hatch + Task

This project uses **Hatch** for Python environments and packaging, and
**Task** as the cross-platform command runner. The two cooperate: Task
shells out to Hatch, never the other way around.

### Why Hatch

- Reads dependencies and tool configs from a single `pyproject.toml`.
- Manages multiple environments (`default`, `test`, `docs`) without manual
  `venv` juggling.
- Builds wheels/sdists for free via `hatchling`; gives you a clean Docker
  install path (`pip install .`) instead of copying source trees.
- Handles versioning from git tags via `hatch-vcs`, which avoids manual
  bumps in two places.
- Aligns with the surrounding workspace template (which is also Hatch-based).

### Why Task

- One discoverable command surface: `task` lists every task with
  descriptions. New contributors do not have to grep your README.
- Cross-platform: a single Go binary that behaves the same on Windows,
  macOS, and Linux. PowerShell users do not have to install Make.
- Task definitions are short YAML, not bash scripts; this matters for a
  Windows-first dev box.
- Plays nicely with pre-commit and CI — the same `task test` command runs
  locally, in hooks, and in GitHub Actions.

### Why not just one of them

- **Hatch alone** works, but its CLI for everyday operations is verbose:
  `hatch run test:cov` vs. `task test`. You will type these dozens of times
  a day.
- **Task alone** does not manage Python environments. You would still
  need venv + pip-tools or uv. That is a second tool either way.
- Together: Hatch owns environments and dependencies, Task owns
  command ergonomics. Each does what it is best at.

### Recommended `Taskfile.yml` commands

| Task              | What it does                                              |
| ----------------- | --------------------------------------------------------- |
| `task dev`        | Run FastAPI with auto-reload via `hatch run uvicorn ...`  |
| `task up`         | `docker compose up -d` (start Postgres)                   |
| `task down`       | `docker compose down`                                     |
| `task migrate`    | `hatch run alembic upgrade head`                          |
| `task migration`  | `hatch run alembic revision --autogenerate -m "..."`      |
| `task seed`       | `hatch run python scripts/seed.py`                        |
| `task test`       | `hatch run test:pytest`                                   |
| `task lint`       | `hatch run ruff check .`                                  |
| `task fmt`        | `hatch run ruff format .`                                 |
| `task typecheck`  | `hatch run mypy src tests`                                |
| `task check`      | runs `lint`, `typecheck`, `test` (CI gate)                |
| `task build`      | `hatch build`                                             |

### When to add `uv`

Optional. If install times bother you, set Hatch's installer to `uv` in
`pyproject.toml`:

```toml
[tool.hatch.envs.default]
installer = "uv"
```

That keeps the workflow identical and makes env creation 5–10x faster.
Do not introduce `uv pip` directly; let Hatch own the env.

---

## Logging & Observability (lightweight)

- Use Python's stdlib `logging` configured once in `main.py`; respect
  `LOG_LEVEL` from settings.
- Emit one structured log line per request via FastAPI middleware (method,
  path, status, duration_ms). JSON output if `APP_ENV=production`,
  human-readable otherwise.
- Do **not** add Sentry, OpenTelemetry, or Prometheus for the MVP. They
  are easy to add later and easy to misconfigure now.

> **Why mention this at all?** Without any logging you will not be able to
> debug a Railway 500. Without a ceiling on observability, scope creeps.
> One middleware and `logging.basicConfig` is the right amount.

---

## Security Checklist (MVP-appropriate)

No auth means the threat model is small, but a few items are still cheap
and worth doing:

- Parameterized queries only (SQLModel/SQLAlchemy do this by default — do
  not switch to raw f-string SQL).
- `description` length cap to prevent payload abuse.
- CORS allow-list driven by env var, not `*`.
- Strip stack traces from `500` responses (`debug=False` in production).
- Do not log full request bodies (could contain user-pasted secrets).
- Rate limiting is **out of scope** for MVP but worth a note in
  `Future Improvements` (`slowapi` is the easy choice).
- `pip-audit` / `bandit` in pre-commit (already in the surrounding
  template).

---

## Testing Plan

Test the backend API thoroughly. Skip vanilla-JS unit tests for the MVP and
add a single Playwright happy-path E2E test only if you have time after
shipping.

> **Why drop `test_feedback_frontend.py`?** Testing vanilla JS without a
> framework is awkward and high-friction. Either commit to a real E2E tool
> (Playwright) or skip frontend tests entirely. Half-doing it produces
> tests nobody runs. Backend tests give you the most coverage per minute.

### API Tests

Write tests for:

- create feedback with valid data → `201` and `Location` header set
- create feedback with invalid `pain_level` → `422`
- create feedback with missing `title` → `422`
- list feedback items → envelope shape verified
- list with `skip` / `limit` → returns the expected slice and `total`
- list with invalid `sort_by` → `422`
- get one existing feedback item → `200`
- get nonexistent feedback item → `404`
- patch feedback item (single field) → `200` and `updated_at` advances
- delete feedback item → `204`
- delete missing item → `404`
- filter by `status` and by `source`
- `/health` returns `200` always
- `/ready` returns `503` when DB is unreachable

### Test Database Strategy

Use a **separate Postgres database** (not SQLite) for tests so dialect
behavior matches production. Two reasonable patterns:

1. A dedicated `feedback_test` database in the same Postgres container,
   recreated per test session.
2. A fresh schema per test using `CREATE SCHEMA test_<uuid>` and rolling
   back at the end.

> **Why not SQLite for tests?** SQLite lacks `ENUM`, has different `JSON`
> semantics, and is case-insensitive by default. Tests that pass on SQLite
> can fail on Postgres in production. Keeping tests on Postgres catches
> these early at the cost of a few seconds of startup.

---

## Suggested Implementation Phases

### Phase 1 — Project Setup

- create project folder with `src/` layout
- create `pyproject.toml` and Hatch environments
- create `Taskfile.yml` with the standard commands (see Tooling)
- install dependencies via `hatch env create`
- set up FastAPI app skeleton
- add `docker-compose.yml` with a Postgres service
- wire pre-commit (ruff, mypy, bandit)

### Phase 2 — Database and Schemas

- define `Source` and `Status` enums
- create `FeedbackItem` SQLModel with constraints
- create request/response schemas
- create database engine and `get_db` session dependency
- initialize Alembic and create the first migration

### Phase 3 — CRUD Layer

- create CRUD functions
- create route handlers
- test API manually in `/docs`

### Phase 4 — Frontend Pages

- create list page
- create create-form page
- create detail/edit page
- connect frontend to backend with Fetch API

### Phase 5 — Validation and Error Handling

- add clean error responses
- validate form input on frontend
- validate all backend rules

### Phase 6 — Testing

- add API endpoint tests
- verify core flows work end to end

### Phase 7 — Deployment

- Dockerize app
- deploy to Railway
- confirm public app and API routes work

### Phase 8 — Polish

- improve README
- clean up UI
- add screenshots
- add deployed URL

---

## Deployment Recommendation

### Railway

Railway is a reasonable option for this project because:

- easy deploy flow
- easy Postgres setup
- good for small MVPs
- simple for portfolio hosting

### Recommended Deployment Setup

- app service
- Postgres database
- environment variables
- public URL for app
- verify frontend and API both work

### Important Note

Do not rely only on deployment. Your README should still explain how to run
the project locally.

> See [`../deployment-notes.md`](../deployment-notes.md) for cost and
> configuration guidance specific to Railway.

---

## README Sections to Include

Your final README should contain:

- project title
- short summary
- features
- tech stack
- screenshots
- API endpoints
- local setup instructions
- Docker instructions
- deployment link
- future improvements

---

## Why This Is a Better Portfolio Project Than a Notes API

A notes API is technically fine, but very generic.

This project is better because it shows:

- domain-specific backend design
- practical SaaS thinking
- frontend and backend integration
- realistic workflow modeling
- cleaner portfolio differentiation

It still teaches the same technical patterns while looking more intentional.

---

## What You Learn From This Project

By finishing this project, you will practice:

- designing REST endpoints
- structuring a backend project
- validating input with Pydantic
- modeling relational data in PostgreSQL
- performing CRUD operations
- connecting a frontend to an API
- writing backend tests
- using Docker for local development
- deploying a full-stack app

---

## Non-Goals

Do not let the project become a bigger product.

This project is not trying to be:

- a full product management suite
- a full CRM
- an enterprise customer feedback platform
- a multi-user SaaS with billing

It is a learning project and portfolio project.

---

## Future Improvements After MVP

Only after version 1 is complete, you could add:

- authentication
- labels or categories
- search
- duplicate detection
- comment threads
- attachments
- simple analytics
- export to CSV
- audit history
- AI clustering of similar feedback

These are post-MVP enhancements, not current requirements.

---

## Final Recommendation

Build this project as:

> A small full-stack customer feedback triage application using FastAPI,
> PostgreSQL, and vanilla JavaScript.

- Keep the scope tight.
- Finish the backend first.
- Then build the frontend on top of it.
- Do not let the project expand into a full SaaS platform yet.

---

## Final Project Identity

- **Project name:** Feedback Triage App
- **Recommended GitHub repo title:** `feedback-triage-app`

**One-line description:**
A small full-stack web app for collecting, managing, and triaging customer
feedback using FastAPI, PostgreSQL, and vanilla JavaScript.
