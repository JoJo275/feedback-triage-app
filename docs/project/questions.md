# Project Questions

Open questions about the **Feedback Triage App** and their current
answers. The canonical answer is always
[`spec/spec.md`](spec/spec.md); this file collects the *why* behind the
decisions a reader is most likely to ask about.

---

## Can we use PostgreSQL for this project?

**Yes, and it is the only supported choice.** The spec requires
PostgreSQL 16:

- Native enum types (`source_enum`, `status_enum`) and `CHECK`
  constraints back the validation rules. Pydantic alone does not protect
  against a future second writer, a seed script, or a manual `psql`
  insert.
- Real-world skill: most production Python web apps run on Postgres.
- SQLModel + Alembic are well-documented against Postgres.
- It is the dialect used in tests too — see
  [spec — Test Database Strategy](spec/spec.md#test-database-strategy).
  SQLite is explicitly banned, even for tests, because it lacks `ENUM`
  and behaves differently from Postgres in enough places to let bugs
  through.
- It is what the deployment target (Railway) provides natively.

For a single-table CRUD app, SQLite would technically run locally, but
the moment the spec calls for native enums and CHECK constraints,
Postgres is the only option that lets the same schema run in dev, test,
and production unchanged. See
[`deployment-notes.md`](deployment-notes.md) for why SQLite-in-the-
container also breaks on Railway's ephemeral filesystem.

---

## How does Postgres work if we need a server?

PostgreSQL is a **client/server** database. Unlike SQLite (a single file
the app reads directly), Postgres runs as a separate process the app
talks to over TCP using a connection string:

```env
DATABASE_URL=postgresql+psycopg://feedback:feedback@localhost:5432/feedback
```

The app does not embed the database. It opens connections to it via the
`psycopg` v3 driver.

### Local development

You do **not** install Postgres on your host. Run it in Docker via
`docker-compose.yml`:

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+psycopg://feedback:feedback@db:5432/feedback
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: feedback
      POSTGRES_PASSWORD: feedback
      POSTGRES_DB: feedback
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

Then:

```bash
task up        # docker compose up -d
task migrate   # alembic upgrade head
task seed      # populate demo data
task dev       # FastAPI with auto-reload
```

The named volume `pgdata` keeps data across container restarts.

### Production / deployment

On Railway, attach the **Postgres plugin** to the project. Railway
provisions the database, manages the server process, and injects
`DATABASE_URL` into the FastAPI service. Migrations run via the
pre-deploy command, not on app boot — see
[`deployment-notes.md`](deployment-notes.md#migrations-on-railway).

---

## Can Postgres be local?

**Yes — Docker Compose is the only supported pattern.** The other
options exist but are not recommended:

### 1. Postgres in Docker (required)

- Started by `task up` (`docker compose up -d`).
- Matches the production version (Postgres 16) exactly.
- No host-level installation, easy to wipe and recreate.
- The same compose file is what tests run against.

### 2. Native Postgres install (not recommended)

- Install via the Postgres installer on Windows, Homebrew on macOS, or
  apt on Linux.
- Always running in the background (or set up as a service).
- More host state, more "works on my machine" risk.
- Acceptable only if Docker is unavailable on the dev machine.

### 3. SQLite (banned)

- Banned by the spec for both runtime and tests
  ([Test Database Strategy](spec/spec.md#test-database-strategy)).
- SQLite lacks native enums, behaves differently around `JSON`, and is
  case-insensitive by default. Tests that pass on SQLite can fail on
  Postgres in production.

### Recommendation

Use **Docker Compose with Postgres 16 locally**. It mirrors production,
keeps the host clean, and removes the "works on my machine" risk when
deploying to Railway.

---

## Why no template engine (Jinja)?

The frontend is plain static HTML files served by `StaticFiles`, with
JavaScript calling the JSON API via `fetch()`. No Jinja, no SPA
toolchain. Justifications and the rejected alternatives (progressive
enhancement, server-rendered initial paint, HTMX) are recorded in
[spec — Frontend Delivery Model](spec/spec.md#frontend-delivery-model)
and will be promoted to ADR 051 on fork.

Short version: with three pages and a JS-driven UI, server-side
templating would be templating `{}` placeholders into otherwise-static
HTML. Pure overhead for this scope.

---

## Why sync routes and not `async def`?

Routes are `def`, not `async def`, in v1.0. The DB driver (`psycopg` v3
in sync mode) and SQLAlchemy session are sync. Mixing `async def`
handlers with a sync session forces you to use `run_in_threadpool` for
every DB call, which is the worst of both worlds.

Async will be revisited under Future Improvements if request volume
ever justifies it. For a single-table CRUD app, the workload is not
I/O-bound enough to matter.

---

## Why offset pagination (`skip` / `limit`) and not cursor?

Offset is simpler, matches the UI's "Page N of M" expectation, and is
fine up to ~10k rows. The known weaknesses (deep-page cost, drift on
insert) are documented as the upgrade path: switch to keyset
pagination on `(created_at DESC, id DESC)` if either becomes a real
problem.

See [spec — List](spec/spec.md#list).

---

## Related docs

- [`spec/spec.md`](spec/spec.md) — full project spec (canonical)
- [`deployment-notes.md`](deployment-notes.md) — Railway cost and config
- [`implementation.md`](implementation.md) — phase-by-phase build plan
