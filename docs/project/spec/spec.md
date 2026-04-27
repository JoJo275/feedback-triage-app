# Feedback Triage App — Project Guide

> **Grade:** Portfolio-grade — not a throwaway MVP. The scope is small but
> the engineering posture (native enums, DB-level constraints, hand-reviewed
> migrations, structured logging, separate readiness probe, Postgres-backed
> tests) is intentionally one notch above "learning project." That gap is
> the point: a reviewer should be able to read this spec and conclude the
> author would not embarrass themselves shipping a real service.

## Recommended GitHub Repository Title

**`feedback-triage-app`**

---

## Repository Context

This spec lives inside a Python template repository (`simple-python-boilerplate`).
Only files under `docs/project/` describe the Feedback Triage App; everything
else in the repo (CI, scripts, dashboard, ADRs, `src/simple_python_boilerplate/`)
is template scaffolding that will be replaced or removed once the spec is
finalized.

**Plan of record:** finalize this spec → fork/repurpose the template into the
`feedback-triage-app` repository → replace `src/simple_python_boilerplate/`
with `src/feedback_triage/` → trim CI to what this project actually needs.
Until then, do not edit template files in this workspace.

---

## Requirement Tiers

Not every line in this spec is equally important. Tiers below let a reviewer
(and the author) see what is **core to the portfolio claim** vs. what is
**polish** vs. what is **explicitly deferred**.

| Tier         | Meaning                                                                 |
| ------------ | ----------------------------------------------------------------------- |
| **Must**     | Required for v1.0. Ship is blocked without these.                       |
| **Should**   | Strongly recommended; included in v1.0 unless time forces a cut.        |
| **Nice**     | Worth doing if time remains; otherwise documented as Future Improvement. |
| **Defer**    | Explicitly out of scope for v1.0.                                       |

Each major section below tags items with a tier when it is non-obvious.
When in doubt, ship Must first; do not start Should items until Must is green.

---

## Project Summary

**Feedback Triage App** is a small full-stack web application for collecting,
viewing, updating, and managing product feedback items.

The project is built around a **FastAPI backend** that exposes JSON endpoints
and a **simple frontend web app** that consumes those endpoints. The purpose
is to demonstrate practical full-stack engineering — API design, relational
modeling, validation, deployment — at a quality bar that holds up to code
review, not just "it runs."

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

This is not meant to be a complete production SaaS. It is a portfolio-grade
v1.0 release with a deliberately narrow feature set.

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
| title        | string          | Required, max 200 characters (DB: `text` + CHECK)  |
| description  | string \| null  | Optional, free text, max 5000 chars (DB: `text` + CHECK) |
| source       | enum (`Source`) | Required, one of the allowed source values         |
| pain_level   | integer         | 1–5, enforced by `CHECK` constraint                |
| status       | enum (`Status`) | Default `new`, one of the allowed status values    |
| created_at   | timestamptz     | Auto-set on creation (`server_default=func.now()`) |
| updated_at   | timestamptz     | Maintained by DB trigger (see PostgreSQL spec)     |

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
- `X (Twitter)`
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

Use one clean REST resource. **All JSON endpoints are versioned under
`/api/v1/`** (e.g. `/api/v1/feedback`). HTML page routes (`/`, `/new`,
`/feedback/{id}`) are unversioned because they are UI surface, not API
contract.

> **Why version from day one?** Adding `/api/v1` costs five characters
> now and prevents an awkward migration the first time a response shape
> changes. Health and readiness probes (`/health`, `/ready`) stay
> unversioned by convention — platforms expect them at fixed paths.

### Datetime serialization

All `created_at` / `updated_at` fields are serialized as ISO 8601 with a
`Z` suffix and microsecond precision (e.g. `2026-04-27T14:32:11.482910Z`).
Configure Pydantic with a `model_config = ConfigDict(ser_json_timedelta=...)`
and a custom `datetime` serializer that forces UTC and `Z`. Naive
datetimes never cross the API boundary.

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
>
> **Why offset pagination (`skip`/`limit`) and not cursor?** Offset is
> simpler, matches the UI's "Page N of M" expectation, and is fine up to
> ~10k rows. Its known weaknesses \u2014 deep-page cost (`OFFSET 100000` scans
> 100k rows) and result drift when rows are inserted between page loads
> \u2014 are documented as the upgrade path: switch to keyset pagination on
> `(created_at DESC, id DESC)` if either becomes a real problem. Listed
> under Future Improvements; not a v1.0 concern.

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

`GET /ready` — process is alive **and** can reach the database. Executes
`SELECT 1` with a **hard 2-second timeout** (Postgres `statement_timeout`
set on the session, plus a `pool_timeout=2` on the engine for the readiness
endpoint specifically). Returns `503` with `{"status": "degraded"}` on
timeout, connection failure, or pool exhaustion.

> **Why split them?** Liveness and readiness answer different questions.
> A platform restarts on liveness failure; it just stops sending traffic on
> readiness failure. Conflating them causes restart loops when the DB
> hiccups. This is the same convention Kubernetes and most PaaS providers
> use, including Railway.
>
> **Why an explicit timeout?** Without one, `SELECT 1` will block on the
> connection-pool wait, and Railway's healthcheck (default ~30s) will time
> out *its* probe instead of getting a clean `503`. A 2s ceiling fails fast
> and lets the platform make the right routing decision.

### CORS

If the frontend is ever served from a different origin (even
`http://localhost:5173` while iterating on JS, or `127.0.0.1` vs
`localhost`), enable `fastapi.middleware.cors.CORSMiddleware` with an
explicit allow-list driven by an env var (`CORS_ALLOWED_ORIGINS`). Do
**not** use `allow_origins=["*"]` in production. The middleware must
include `PATCH` and `DELETE` in `allow_methods` (FastAPI's defaults
cover them, but be explicit) so browser preflight requests succeed.

### Response models and OpenAPI

[Must] Every route declares an explicit `response_model=` (e.g.
`FeedbackResponse`, `FeedbackListEnvelope`). This is what makes `/docs`
look professional and is the single cheapest credibility win in the API.
Group routes with `tags=["feedback"]` / `tags=["health"]` so the Swagger
UI is organized.

### Idempotency

`POST /feedback` is **not** idempotent in v1.0 — submitting the same body
twice creates two rows. This is intentional: real feedback streams
(emails, support tickets) genuinely contain near-duplicates that a human
should triage. Duplicate detection is listed under Future Improvements.

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

## Frontend Delivery Model

FastAPI serves the frontend as **plain static HTML files** via `StaticFiles`,
plus a few thin route handlers that return the right HTML for `/`, `/new`,
and `/feedback/{id}`. There is no Jinja templating, no Node toolchain, no
bundler, no SPA framework. JavaScript calls the JSON API via `fetch()` from
the same origin and does all rendering client-side.

This is a deliberate choice. With three pages and a JS-driven UI, server-
side templating would template `{}` placeholders into otherwise-static
HTML — pure overhead. Dropping Jinja means one fewer dependency, one fewer
language in the repo, and the "vanilla HTML/CSS/JS" claim in the README is
literally true.

> **When to revisit.** If progressive enhancement (works without JS,
> server-rendered first paint) becomes a goal, swap `StaticFiles` for
> Jinja templates and render the list HTML server-side. That is an
> evening's work and lives under Future Improvements.

Same-origin delivery also means **CSRF is not a concern in v1.0**: no
cookie-based auth, no cross-origin form posts, all writes are JSON via
`fetch()` with `Content-Type: application/json`. Browsers do not auto-
attach credentials to cross-origin JSON requests without explicit
`credentials: 'include'`. Document this in the security checklist; do
not add a CSRF token mechanism.

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

This is enough for v1.0.

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
│       ├── middleware.py      # request-id, structured logging
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── feedback.py    # /api/v1/feedback
│       │   ├── health.py      # /health, /ready
│       │   └── pages.py       # /, /new, /feedback/{id} → serve HTML
│       └── static/
│           ├── index.html
│           ├── new.html
│           ├── detail.html
│           ├── css/styles.css
│           └── js/
│               ├── index.js
│               ├── new.js
│               └── detail.js
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_feedback_api.py
│   └── e2e/
│       ├── conftest.py
│       └── test_feedback_smoke.py
├── scripts/
│   └── seed.py                # populate demo data
├── Containerfile              # multi-stage, non-root, HEALTHCHECK
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

Use one main model: `FeedbackItem`. The full schema, indexes, constraints,
and migration policy live in the next section.

This project works best with a single strong resource. Do not split it into
users, teams, labels, comments, and history tables yet.

---

## PostgreSQL Specification

This is the canonical database spec. The model, the SQLModel class, and the
first Alembic migration must all match it. Postgres 16 is the target.

### Why Postgres 16

- Long-term supported until November 2028.
- Matches the default Railway Postgres template, so dev/prod parity is free.
- Every feature used here (`generated identity`, `timestamptz`, native
  `ENUM`, `CHECK`, `gen_random_uuid()`) is stable in 16.

### Schema overview

One table, two enum types, a small set of indexes, explicit constraints.

```text
schema: public
├── type  source_enum   (email, interview, reddit, support, app_store, twitter, other)
├── type  status_enum   (new, reviewing, planned, rejected)
└── table feedback_item
    ├── id             bigint   PK, identity
    ├── title          varchar(200) NOT NULL
    ├── description    varchar(5000) NULL
    ├── source         source_enum NOT NULL
    ├── pain_level     smallint NOT NULL  CHECK (1..5)
    ├── status         status_enum NOT NULL DEFAULT 'new'
    ├── created_at     timestamptz NOT NULL DEFAULT now()
    └── updated_at     timestamptz NOT NULL DEFAULT now()
```

### `feedback_item` — column-by-column

| Column        | Postgres type    | Nullable | Default            | Notes                                                                        |
| ------------- | ---------------- | -------- | ------------------ | ---------------------------------------------------------------------------- |
| `id`          | `bigint`         | no       | `GENERATED ALWAYS AS IDENTITY` | Primary key. `bigint` over `int` because growing past 2^31 is free insurance. |
| `title`       | `text`           | no       | —                  | Length enforced via `CHECK`, not `varchar(n)` — see note below.              |
| `description` | `text`           | yes      | `NULL`             | Optional free text. Length enforced via `CHECK`.                             |
| `source`      | `source_enum`    | no       | —                  | Native Postgres enum, not a string.                                          |
| `pain_level`  | `smallint`       | no       | —                  | `smallint` is plenty for 1–5; saves bytes vs. `int`.                         |
| `status`      | `status_enum`    | no       | `'new'`            | Native Postgres enum.                                                        |
| `created_at`  | `timestamptz`    | no       | `now()`            | Always UTC. `now()` runs in the DB, not the app.                             |
| `updated_at`  | `timestamptz`    | no       | `now()`            | Bumped by a `BEFORE UPDATE` trigger (see below).                             |

> **Why `text` + `CHECK` instead of `varchar(n)`?** Postgres stores both
> identically; there is no performance difference. `varchar(n)` makes
> raising the limit a metadata-only `ALTER TABLE` in modern Postgres, but
> *lowering* it requires a full rewrite, and `CHECK` constraints are the
> standard idiom in the Postgres community. Using `text` everywhere also
> sidesteps the `varchar` vs `character varying` naming inconsistency in
> tooling output.

> **Why `bigint` identity over UUID?** Sequential IDs are smaller, sort
> naturally, and are easier to debug in URLs and logs. UUIDs are useful when
> IDs are generated client-side or merged across systems; neither applies
> here. If the project ever exposes IDs to untrusted clients and needs
> opacity, switch to UUID v7 in a single migration.

### Constraints

```sql
ALTER TABLE feedback_item
    ADD CONSTRAINT feedback_item_pain_level_range
    CHECK (pain_level BETWEEN 1 AND 5);

ALTER TABLE feedback_item
    ADD CONSTRAINT feedback_item_title_not_blank
    CHECK (length(btrim(title)) > 0);

ALTER TABLE feedback_item
    ADD CONSTRAINT feedback_item_title_max_len
    CHECK (length(title) <= 200);

ALTER TABLE feedback_item
    ADD CONSTRAINT feedback_item_description_max_len
    CHECK (description IS NULL OR length(description) <= 5000);
```

> Enums already enforce membership for `source` and `status`. The two
> `CHECK` constraints close the remaining gaps Pydantic alone cannot
> guarantee against direct SQL inserts or seed scripts.

### Indexes

Index for **the queries you actually run**, not "just in case."

| Index                                 | Columns                          | Why                                           |
| ------------------------------------- | -------------------------------- | --------------------------------------------- |
| `feedback_item_pkey`                  | `id`                             | Primary key (automatic).                      |
| `ix_feedback_item_created_at_desc`    | `(created_at DESC)`              | Default list ordering. The list endpoint sorts by newest first. |
| `ix_feedback_item_status`             | `(status)`                       | Filter by status is a top-level UI control.   |
| `ix_feedback_item_source`             | `(source)`                       | Filter by source is a top-level UI control.   |

Skip these for now:

- A composite `(status, created_at DESC)` index — only worth adding if
  `EXPLAIN ANALYZE` shows the simpler indexes are insufficient at real data
  volumes. Premature.
- Full-text search on `title` / `description` — defer until the optional
  Search feature lands in Future Improvements. Use `tsvector` + GIN then.

> **Why descending on `created_at`?** Postgres can scan a btree in either
> direction, so `ASC` would technically suffice. Declaring `DESC`
> documents the dominant query pattern and lets the planner skip a sort
> on `ORDER BY created_at DESC`.

### `updated_at` strategy

Use a trigger, not application code, to bump `updated_at` on update:

```sql
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER feedback_item_set_updated_at
    BEFORE UPDATE ON feedback_item
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

> **Why a trigger over SQLAlchemy `onupdate`?** A trigger fires for every
> writer, including raw SQL, seed scripts, and a future second service.
> The ORM hook only protects writes that go through the ORM. Triggers are
> ~5 lines and cost nothing.

### Enum migration policy

Postgres enums are schema objects. Adding new values is cheap; renaming or
removing is **not**.

- **Safe:** `ALTER TYPE source_enum ADD VALUE 'discord';`
- **Painful:** removing a value (requires creating a new type, casting,
  swapping, dropping the old type).

Therefore:

- Add new sources/statuses freely.
- Treat removal as a planned migration with a backfill step.
- Never reuse an old value for a different meaning.

### SQLModel / SQLAlchemy mapping

Define the model once; let Alembic's `--autogenerate` derive migrations.

- Use `sqlalchemy.dialects.postgresql.ENUM` with `create_type=False` so the
  enum type is owned by the migration, not by `metadata.create_all()`.
- Define the Python `Enum` classes in `enums.py` and import them in both
  the SQLModel model (`models.py`) and the request schemas (`schemas.py`)
  so there is exactly one source of truth.
- Set `Mapped[str]` style annotations and `mapped_column(...)` for
  forward-compatibility with SQLAlchemy 2.x.

### Database session lifecycle

- One **engine** per process, created at import time in `database.py`.
- One **session per request**, yielded via a `get_db` FastAPI dependency
  with `try / finally: session.close()`. Sessions are **never** reused
  across requests, cached on `app.state`, or stored on a module global.
  This invariant is what makes `expire_on_commit=False` safe (see below).
- `pool_size=5`, `max_overflow=5`, `pool_pre_ping=True`. Pre-ping costs a
  trivial round trip and prevents "server closed the connection
  unexpectedly" errors after Railway puts the DB to sleep.
- Pool sizing rule of thumb: `pool_size * web_workers` ≤ DB max
  connections. Railway's free Postgres allows ~20; with 2 uvicorn workers
  and `pool_size=5, max_overflow=5`, peak is 20. Bump worker count only
  after raising the DB plan.
- Use `SQLALCHEMY_ECHO=false` in production. Echo is a debug-only setting.

```python
# sketch — src/feedback_triage/database.py
engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

def get_db() -> Iterator[Session]:
    """Session-per-request with commit/rollback wired to handler outcome."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

> **Why `expire_on_commit=False` is safe here — and the invariant that
> keeps it safe.** With `expire_on_commit=True` (the default), every
> attribute access on a returned ORM object after `commit()` triggers a
> re-fetch from the session. FastAPI serializes the response *after* the
> handler returns, by which point the session is closed, so serialization
> raises `DetachedInstanceError`. Setting `expire_on_commit=False` keeps
> the loaded attributes usable for serialization.
>
> The catch: with `expire_on_commit=False`, a session that **outlives a
> single request** will serve stale reads — its identity map still holds
> the row state from the last commit even after another request mutates
> the database. The fix is structural, not a config flag: **scope every
> session to exactly one request via `get_db`.** Do not store sessions on
> `app.state`, in module globals, in background-task closures that
> outlive the request, or in a worker pool that fans out work after the
> response has been sent. If a future feature needs a long-lived worker,
> it gets its **own** short-lived session per unit of work via
> `with SessionLocal() as s: ...`, never the request's session.
>
> Tested at the API level: see `test_patch_then_get_returns_fresh_state`
> in the testing plan.

### Transaction boundaries

- One transaction per request. Begin implicitly when the session is used,
  commit at the end of a successful handler, roll back on exception.
- Commit/rollback live in `get_db` (see sketch above), **not** in route
  handlers. Handlers call `session.add(...)` / `session.flush()` and
  return; they never call `session.commit()` themselves.
- `flush()` is fine inside a handler when an autogenerated `id` is needed
  before the response is built (e.g. for the `Location` header on
  `POST /feedback`). The commit still happens once, in `get_db`.
- Never run multi-step write logic without a transaction; partial writes
  are the kind of bug that only shows up in production.

### Concurrency model

- **Local dev:** single uvicorn process with `--reload`.
- **Production (Railway):** `uvicorn feedback_triage.main:app --workers 2
  --host 0.0.0.0 --port $PORT`. Two workers is the minimum to survive a
  single slow request without dropping the next one; more requires
  raising the DB connection cap (see pool sizing above).
- No async DB driver in v1.0. Routes are `def`, not `async def`, because
  SQLModel/SQLAlchemy's sync session is simpler to reason about and the
  workload (a single CRUD table) is not I/O-bound enough to justify
  `asyncpg` + `AsyncSession`. Listed under Future Improvements.

### Migrations (Alembic)

- `alembic.ini` reads `DATABASE_URL` from the environment, never a
  hardcoded URL.
- Configure `target_metadata = SQLModel.metadata` in `alembic/env.py`.
- Configure `compare_type=True` and `compare_server_default=True` so
  `--autogenerate` catches type and default changes.
- Every migration must be **reviewed by hand** after autogeneration.
  Autogenerate misses: enum value adds, index renames, trigger creation,
  data backfills.
- Migrations run as part of app startup in development (`task migrate`)
  and as a **separate one-shot job** in production. Do **not** run them
  inside the web process on Railway — concurrent boots race each other.

#### Running migrations on Railway

Railway has no first-class "release command" hook the way Heroku does, so
pick one of these and document it in the README:

1. **Pre-deploy command (preferred).** In the service settings, set the
   pre-deploy command to `hatch run alembic upgrade head` (or
   `alembic upgrade head` if running from the built image). Railway runs
   it in a one-off container before swapping traffic to the new release.
2. **Manual one-shot via `railway run`.** `railway run -- alembic upgrade
   head` from a developer machine, gated behind a checklist in the
   release runbook. Acceptable for a portfolio project; brittle for a
   real team.
3. **Separate `migrate` service in `railway.toml`** that runs once and
   exits. Heaviest setup; only worth it if migrations grow long enough
   to time out a pre-deploy hook.

Do **not** run `alembic upgrade head` from `main.py` on app startup in
production. Two web workers booting simultaneously will both try to
acquire the migration lock and one will fail.

### Connecting from the app

Connection string format (psycopg v3 driver):

```env
DATABASE_URL=postgresql+psycopg://feedback:feedback@localhost:5432/feedback
```

In production (Railway), use the platform-injected `DATABASE_URL`
directly. Do not hand-construct the URL from individual components.

### Backups and data safety (local dev)

For v1.0, "backups" means: do not lose your demo data on a `docker
compose down -v`.

- `docker-compose.yml` mounts a named volume (`pgdata`) so data survives
  container restarts.
- `task db:dump` → `pg_dump` to `./backups/feedback-YYYYMMDD.sql.gz`.
- `task db:restore FILE=...` → `pg_restore` (or `psql <` for SQL dumps).
- `.gitignore` the `backups/` directory; it is local-only.

Production backups on Railway are handled by the platform (point-in-time
recovery on paid plans). Document this in the README; do not roll your
own.

### Defense-in-depth summary

| Threat                          | Defense                                              |
| ------------------------------- | ---------------------------------------------------- |
| Bad enum value via API          | Pydantic enum + Postgres enum type                   |
| Bad enum value via raw SQL      | Postgres enum type                                   |
| Out-of-range `pain_level`       | Pydantic `Field(ge=1, le=5)` + DB `CHECK`            |
| Empty/whitespace `title`        | Pydantic validator + DB `CHECK length(btrim) > 0`    |
| Oversized payload               | Pydantic `max_length` + `varchar(200/5000)`          |
| Missing `updated_at` bump       | DB trigger (covers ORM + raw SQL + seed scripts)     |
| Schema drift across environments| Alembic, hand-reviewed                               |
| Connection drop after idle      | `pool_pre_ping=True`                                 |
| SQL injection                   | SQLAlchemy parameter binding (no string-built SQL)   |
| Lost demo data                  | Named Docker volume + `pg_dump` task                 |

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
# Leave empty for the default same-origin setup (HTML served by FastAPI).
# Populate only when iterating on a separate frontend dev server, e.g.:
#   CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CORS_ALLOWED_ORIGINS=

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
- **Request-ID middleware** [Must]: assign a UUID to every incoming
  request (or trust an inbound `X-Request-ID` header if present), attach
  it to a `contextvars.ContextVar`, include it in every log record via a
  `logging.Filter`, and echo it back in the response `X-Request-ID`
  header. Without this, debugging a Railway 500 means scrolling through
  interleaved logs from two workers; with it, one grep finds the whole
  request.
- Emit one structured log line per request via FastAPI middleware (method,
  path, status, duration_ms, request_id). JSON output if `APP_ENV=production`,
  human-readable otherwise.
- Do **not** add Sentry, OpenTelemetry, or Prometheus for v1.0. They
  are easy to add later and easy to misconfigure now.

> **Why mention this at all?** Without any logging you will not be able to
> debug a Railway 500. Without a ceiling on observability, scope creeps.
> One middleware and `logging.basicConfig` is the right amount.

---

## Security Checklist (v1.0-appropriate)

No auth means the threat model is small, but a few items are still cheap
and worth doing:

- Parameterized queries only (SQLModel/SQLAlchemy do this by default — do
  not switch to raw f-string SQL).
- `description` length cap to prevent payload abuse.
- CORS allow-list driven by env var, not `*`.
- Strip stack traces from `500` responses (`debug=False` in production).
- Do not log full request bodies (could contain user-pasted secrets).
- **CSRF: not applicable in v1.0.** No cookie-based auth, no cross-origin
  form posts, all writes are JSON via `fetch()`. Adding a CSRF token
  mechanism would be cargo-cult security here. Revisit if/when auth lands.
- Rate limiting is **out of scope** for v1.0 but worth a note in
  `Future Improvements` (`slowapi` is the easy choice).
- `pip-audit` / `bandit` in pre-commit (already in the surrounding
  template).

## Container Hardening [Must]

The `Containerfile` must:

- Use a **multi-stage build** — stage 1 builds the wheel with Hatch, stage
  2 is a slim runtime (`python:3.13-slim`) that `pip install`s the wheel.
  No source tree, no build tools, no `.git` in the final image.
- Run as a **non-root user** (`USER app` after `useradd -m app`). Railway
  does not require it, but it is the bare minimum hardening any reviewer
  will check.
- Declare `EXPOSE 8000` and a `HEALTHCHECK` that hits `/health` (not
  `/ready` — healthcheck failure restarts the container, and a DB blip
  should not).
- Pin the base image by digest (`python:3.13-slim@sha256:...`) for
  reproducibility; refresh with Renovate/Dependabot.
- Set `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`,
  `PIP_NO_CACHE_DIR=1` as ENV.

## Accessibility Floor [Should]

The frontend is HTML and forms; basic accessibility is essentially free:

- Semantic HTML (`<main>`, `<nav>`, `<table>` for the list, `<form>` for
  inputs).
- Every `<input>` / `<select>` has an associated `<label>`.
- Buttons are `<button>`, not `<div onclick=...>`.
- Visible focus rings (do not `outline: none` in CSS without replacement).
- Color contrast meets WCAG AA (lighthouse score ≥ 90 on the
  Accessibility category).
- The Playwright smoke suite drives forms via labels (`page.get_by_label`),
  which doubles as an accessibility check — if it can't find a label, you
  forgot one.

---

## Testing Plan

Test the backend API thoroughly. Add a small **Playwright frontend smoke
suite** to prove the UI is wired to the API. Skip vanilla-JS unit tests —
testing framework-less JS without a runtime is high-friction and the smoke
tests cover the same risks at the right level.

### API Tests [Must]

Write tests for:

- create feedback with valid data → `201` and `Location` header set
- create feedback with invalid `pain_level` → `422`
- create feedback with missing `title` → `422`
- create feedback with whitespace-only `title` → `422`
- create feedback with oversized `description` (>5000 chars) → `422`
- list feedback items → envelope shape verified (`items`, `total`, `skip`, `limit`)
- list with `skip` / `limit` → returns the expected slice and `total`
- list with invalid `sort_by` → `422`
- get one existing feedback item → `200`
- get nonexistent feedback item → `404`
- patch feedback item (single field) → `200` and `updated_at` advances
- patch with empty body → `200` and no fields change, `updated_at` still bumps (trigger fires on every UPDATE)
- **`test_patch_then_get_returns_fresh_state`** — `PATCH` an item in one
  request, `GET` it in the next request, assert the returned state
  matches the patch. This is the canary for the session-reuse / stale-read
  bug; if `expire_on_commit=False` ever leaks across requests, this test
  fails.
- delete feedback item → `204`
- delete missing item → `404`
- filter by `status` and by `source`
- `/health` returns `200` always
- `/ready` returns `200` when DB is reachable
- `/ready` returns `503` within 2s when DB is unreachable (test by
  pointing `DATABASE_URL` at a closed port)

### Frontend Smoke Tests [Must]

Three Playwright specs in `tests/e2e/test_feedback_smoke.py` exercise the
critical UI paths against a running app + Postgres. CI brings up the
stack with `docker compose up -d` and runs the suite via `task test:e2e`.

1. **Create flow:** open `/new`, fill the form, submit, assert redirect
   to `/` and that the new title appears in the list.
2. **Edit flow:** open the most recent item's detail page, change
   `status` from `new` to `reviewing`, save, reload, assert the new
   status persists.
3. **Delete flow:** delete the most recent item from the list page,
   assert it disappears and that reloading does not bring it back.

These three cover "the JS calls the API correctly" without ballooning
into a full E2E suite. If a fourth test feels necessary, it almost
certainly belongs at the API layer instead.

Gate the smoke suite behind a pytest marker (`@pytest.mark.e2e`) so it
does not run by default with `task test`. Run it via `task test:e2e` and
in a dedicated CI job so a flaky browser does not block the unit-test
gate. Use Playwright's `chromium` only for v1.0 — cross-browser is
Future Improvements territory.

### Test Database Strategy

Use a **separate Postgres database** (not SQLite) for tests so dialect
behavior matches production. Two reasonable patterns:

1. A dedicated `feedback_test` database in the same Postgres container,
   recreated per test session.
2. A fresh schema per test using `CREATE SCHEMA test_<uuid>` and rolling
   back at the end.

For v1.0, use option (1) plus a `truncate_all_tables()` fixture that runs
before each test. It is the simplest pattern that still gives test
isolation.

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

- define `Source` and `Status` enums in `enums.py` (single source of truth)
- create `FeedbackItem` SQLModel matching the [Postgres spec](#postgresql-specification)
- create request/response schemas using the same enums
- create database engine, `SessionLocal`, and `get_db` dependency with `pool_pre_ping=True`
- initialize Alembic; configure `compare_type` and `compare_server_default`
- write the first migration **by hand-reviewing autogenerate output**:
  enum types, table, `CHECK` constraints, indexes, and the `updated_at` trigger
- run `task migrate` and verify with `\d feedback_item` in `psql`

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
- good for small v1.0 services
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

## README Sections to Include [Must]

The README is the portfolio surface. A reviewer who never clones the repo
should still be able to judge it from the README alone.

Required sections:

- **Project title and one-line description**
- **Live demo link** (Railway URL) and **`/api/v1/docs` link**
- **Screenshots** [Must] \u2014 at least three, embedded inline:
  1. List page with seeded data
  2. Detail / edit page mid-edit
  3. `/api/v1/docs` Swagger UI
  Stored under `docs/screenshots/`, referenced with relative paths.
- **Features** \u2014 bulleted, matched to actual implemented behavior
- **Tech stack** — short table (FastAPI, SQLModel, Postgres 16, Alembic,
  pytest, Playwright, Hatch, Task, Docker, Railway)
- **Architecture diagram** [Should] — a single Mermaid `flowchart` of
  browser → FastAPI → Postgres, with the static-HTML / JSON-API split
  visible. Mermaid renders natively on GitHub; no image asset needed.
- **Local setup** — `task up && task migrate && task seed && task dev`
  in a copy-paste block. If a reader has to read prose to figure out the
  commands, the README has failed.
- **Running tests** — separate blocks for `task test` and `task test:e2e`
- **Deployment** — Railway-specific notes; link to `docs/deployment-notes.md`
- **API reference** — link to `/api/v1/docs`; do not duplicate it in Markdown
- **Future improvements** — short list, link to spec for full version
- **License**

## Dependency Updates [Must]

Use **Dependabot** (already configured in the surrounding template; carry
it over). Coverage:

- `pip` ecosystem on `pyproject.toml` — weekly, grouped into a single PR
  per week (`groups:` config). Patch + minor auto-merge after CI passes;
  major upgrades wait for human review.
- `github-actions` ecosystem — weekly. Pin updates land as SHA bumps so
  ADR 004 stays honest.
- `docker` ecosystem on the `Containerfile` base image — weekly digest
  refresh.

Do **not** also enable Renovate; pick one. Dependabot is GitHub-native
and the template already has it configured.

## Release Flow [Must]

This project separates **Deploy** (continuous, every merge to `main`) from
**Release** (tag-driven, human-paced). They run on the same commit stream
but answer different questions: deploy = "is the running site fresh?",
release = "what version did we ship and what changed?".

### Branch protection

- `main` is protected. Direct pushes are rejected.
- All changes land via PR. Required checks: the CI gate workflow
  (`task check` matrix) must pass before merge. The e2e smoke
  (`task test:e2e`) is **not** a required check in v1.0 — it is gated
  behind `@pytest.mark.e2e` and run on demand or on a nightly schedule.
- Merge strategy is **rebase** (per ADR 022); no squash, no merge commits.
- Conversation resolution required; stale approvals dismissed on new pushes.

### Deploy: continuous from `main`

Railway is configured with the **GitHub repository** as its source (not
GHCR). Every push to `main` triggers Railway to:

1. Pull the new commit.
2. Build the image from `Containerfile`.
3. Run the **pre-deploy command**: `alembic upgrade head` (against the
   production `DATABASE_URL`, which Railway injects from the Postgres
   plugin). If the migration fails, the deploy aborts and the previous
   container keeps serving traffic.
4. Start the new container. The Railway healthcheck hits `/health`; only
   when it returns 200 does Railway swap traffic over.

So the answer to "do I just merge a PR to `main` and Railway picks it up?"
is **yes, that is exactly the model.** No manual deploy step, no image
promotion, no `task release` required to ship a feature.

### Release: tag-driven, on top of the deploy stream

Releases are bookkeeping, not deployment. They produce two artifacts a
reviewer can inspect:

- a **GitHub Release** with auto-generated notes from Conventional Commits
- a **GHCR image** tagged with the version and commit SHA, for traceability
  and (future) image-promotion workflows

The mechanism is **release-please** running on every push to `main`:

1. release-please opens (or updates) a long-lived **Release PR** that
   bumps the version derived from Conventional Commits and rewrites
   `CHANGELOG.md`. The Release PR sits open while features keep landing —
   it just keeps updating.
2. When you decide a cut is ready, you **merge the Release PR**.
3. Merging the Release PR causes release-please to:
   - create the git tag (`v1.2.3`) on the merge commit,
   - publish the GitHub Release with the generated notes.
4. The tag push triggers `release.yml`, which runs the full CI gate,
   builds the image, and pushes it to GHCR tagged `v1.2.3` and
   `sha-<short-sha>`.
5. **Railway is unaffected by the tag.** The deploy that shipped this
   commit already happened when the underlying feature PRs merged. The
   tag is a label on a commit that is already live.

This is intentional: deploy cadence is decoupled from release cadence,
and rolling back a release does not require re-deploying anything.

### Flow at a glance

```
feat: add filter           ──┐
fix: validate pain_level   ──┤  (PRs merged to main, each one ships immediately)
chore: bump deps           ──┘
                              │
                              ▼
                          main branch ───► Railway: build → migrate → /health → serve
                              │
                              ▼
                  release-please Release PR (open, accumulating changes)
                              │
                              │  (human merges Release PR when ready)
                              ▼
                        tag v1.2.3 created
                              │
                              ▼
                    release.yml: CI gate → GHCR push → GitHub Release
```

### Versioning

- Version is derived from the latest git tag by `hatch-vcs`. There is no
  static `version = "..."` in `pyproject.toml`.
- Untagged builds (every commit on `main` between releases) report
  `0.0.0+<short-sha>`. That is the version Railway is running between cuts.
- No manual version bumps anywhere; release-please owns the tag.
- `task release` exists as an **emergency fallback** (`git tag -a vX.Y.Z`
  + `git push origin vX.Y.Z`) for cases where release-please is unavailable.
  It is not the normal path.

### Configuration checklist

- [ ] Railway service: source = GitHub repo (this repo), branch = `main`.
- [ ] Railway pre-deploy command: `alembic upgrade head`.
- [ ] Railway healthcheck path: `/health`, timeout 5s.
- [ ] `DATABASE_URL` injected by Railway Postgres plugin; app normalizes
      `postgres://` → `postgresql+psycopg://` at startup.
- [ ] GitHub branch protection on `main`: require CI gate, require PR,
      rebase merge, dismiss stale approvals.
- [ ] `release-please-config.json` configured for a Python project.
- [ ] `.github/workflows/release.yml` triggers on `push` of tags matching
      `v*.*.*`, runs full CI, builds image, pushes to
      `ghcr.io/<owner>/feedback-triage-app:v*` and `:sha-*`.

### Hotfixes

A hotfix is just a normal PR. Open it, get review, merge to `main`,
Railway redeploys. If the fix should also bump the version, the next
release-please Release PR will pick up the `fix:` commit and propose a
patch bump.

There is no separate hotfix branch in v1.0 — the project is single-tenant
and rolling forward is acceptable. A hotfix branch model can be added
later if traffic grows.

### Why GHCR images aren't promoted to Railway

GHCR images exist for traceability and for a future "promote a tagged
image to production" workflow. In v1.0 there is only one environment, so
having Railway build directly from the repo is simpler than wiring image
promotion: one source of truth, one build, no skew between the GHCR image
and the running container.

If a staging environment is added later, the natural upgrade path is to
switch Railway to deploy from GHCR tags and have a workflow promote
`sha-*` tags to a `staging` tag and then to a `production` tag.

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

## Future Improvements After v1.0

Only after version 1 is complete, you could add:

- authentication
- labels or categories
- full-text search (`tsvector` + GIN index on `title || description`)
- cursor / keyset pagination keyed on `(created_at, id)`
- async DB driver (`asyncpg` + `AsyncSession`) if request volume warrants
- rate limiting via `slowapi`
- duplicate detection on `POST /feedback`
- comment threads
- attachments
- simple analytics
- export to CSV
- audit history
- AI clustering of similar feedback
- observability stack (Sentry, OpenTelemetry, Prometheus)

These are post-v1.0 enhancements, not current requirements.

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

## ADRs to Write

After forking the template into `feedback-triage-app`, write the following
project-specific ADRs. Each one captures a decision that this spec makes
implicitly; promoting them to numbered ADRs gives reviewers (and future you)
a single page per call to point at when the question comes back.

Numbering picks up after the highest inherited template ADR (044). Adjust
if you renumber on fork.

| #   | Title                                              | Captures                                                                                       |
| --- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 045 | Single-table data model for v1.0                   | One `feedback_item` table, no users/labels/comments. When to split.                            |
| 046 | Native Postgres enums + DB CHECK constraints       | Defense-in-depth over Pydantic-only validation. Enum migration policy.                         |
| 047 | SQLModel over plain SQLAlchemy                     | Boilerplate reduction for single-table CRUD; escape hatch is "it's already SQLAlchemy."        |
| 048 | Session-per-request with `expire_on_commit=False`  | The invariant that prevents stale reads. No sessions on `app.state` / module globals.          |
| 049 | Offset pagination with documented keyset upgrade   | Why `skip`/`limit` for v1.0; the trigger to migrate to keyset on `(created_at DESC, id DESC)`. |
| 050 | Sync DB driver in v1.0 (defer asyncpg)             | Routes are `def`, not `async def`. Conditions under which to revisit.                          |
| 051 | Static HTML + vanilla JS (no Jinja, no SPA)        | Frontend delivery model. PE explicitly rejected for this scope.                                |
| 052 | API versioning under `/api/v1/`                    | Why prefix from day one; what stays unversioned (health, HTML routes).                         |
| 053 | Migrations as Railway pre-deploy command           | Why not on app boot; the three options and which one was picked.                               |
| 054 | Postgres for tests (no SQLite)                     | Dialect-parity over startup speed. The `truncate_all_tables()` fixture pattern.                |

ADRs to **rewrite** (not delete) when forking, because the template versions
exist but encode the wrong decision for this project:

| #   | Title                          | Rewrite focus                                                                                |
| --- | ------------------------------ | -------------------------------------------------------------------------------------------- |
| 014 | No template engine             | Reframe from "template repo has no Jinja" to "feedback-triage-app deliberately ships static HTML." |
| 025 | Container strategy             | Consolidate with 019 or split deliberately; encode multi-stage + non-root + HEALTHCHECK.     |
| 027 | Database strategy              | Replace template-generic content with the Postgres 16 + SQLModel + enums + trigger spec.     |
| 029 | Testing strategy               | Add Postgres-for-tests and the Playwright smoke layer.                                       |
| 031 | Script conventions             | Either rewrite for `scripts/seed.py` etc., or delete if the project has no script surface.   |

Treat this list as the authoritative ADR backlog. Do not start implementing
the project until at least #045\u2013#054 are drafted; the act of writing them
catches spec gaps early.

---

## Final Project Identity

- **Project name:** Feedback Triage App
- **Recommended GitHub repo title:** `feedback-triage-app`

**One-line description:**
A small full-stack web app for collecting, managing, and triaging customer
feedback using FastAPI, PostgreSQL, and vanilla JavaScript.
