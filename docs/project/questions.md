# Project Questions

Open questions about the Feedback Triage App and their current answers.

---

## Can we use PostgreSQL for this project?

**Yes, and it is the recommended choice.** The spec already calls for
PostgreSQL, and it is the right fit for this app:

- Relational model maps cleanly to a single `FeedbackItem` table.
- Real-world skill: most production Python web apps use Postgres.
- Strong typing, constraints, and indexes help enforce validation rules
  (e.g. `pain_level` between 1 and 5, `status` enum).
- SQLAlchemy / SQLModel + Alembic migrations are well-documented against
  Postgres.
- It is what the deployment target (Railway) provides natively.

For a single-table CRUD MVP, SQLite would technically work and is easier to
start with. The reason to still pick Postgres:

- Avoids a second migration later when you deploy.
- The deployed Railway environment has an ephemeral filesystem, so a SQLite
  file inside the container would be lost on redeploy. See
  [`deployment-notes.md`](deployment-notes.md).

---

## How would Postgres work if we need a server?

PostgreSQL is a **client/server** database. Unlike SQLite (a single file
read directly by the app), Postgres runs as a separate process the app
talks to over TCP using a connection string:

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/feedback
```

The app does not embed the database. It opens connections to it.

### Local development

You do **not** need to install Postgres directly on your machine. Run it in
Docker via `docker-compose.yml`:

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
docker compose up
```

The named volume `pgdata` keeps data across container restarts.

### Production / deployment

On Railway, add the **Postgres template** to the project. Railway provisions
the database, manages the server process, and exposes a `DATABASE_URL`
environment variable that the FastAPI service reads at startup. No separate
server to manage.

---

## Can Postgres be local?

**Yes — three reasonable options, in order of recommendation:**

### 1. Postgres in Docker (recommended)

- Started by `docker compose up`.
- Matches the production version exactly.
- No host-level installation, easy to wipe and recreate.
- One command to start; the app's `depends_on` ensures the DB is up.

### 2. Native Postgres install

- Install via the Postgres installer on Windows, Homebrew on macOS, or apt
  on Linux.
- Always running in the background (or set up as a service).
- More setup, more state on your machine, but no Docker overhead.

### 3. SQLite for very early prototyping

- Allowed only as a temporary stand-in while you scaffold the app.
- Useful if you want to verify routes and templates before plumbing Docker.
- Switch to Postgres before writing real schema/migrations — keeping both
  long-term means handling SQL dialect differences (enums, JSON types,
  case sensitivity) and is not worth it.

### Recommendation

Use **Docker Compose with Postgres locally**. It mirrors production, keeps
your host clean, and removes the "works on my machine" risk when you
deploy to Railway.

---

## Related docs

- [`spec/spec.md`](spec/spec.md) — full project spec
- [`deployment-notes.md`](deployment-notes.md) — Railway cost and config notes
