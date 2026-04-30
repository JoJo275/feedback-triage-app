# How This Web App Gets To The Internet

A beginner-oriented tour of the production line that turns a `git push`
into a URL strangers can hit. Written in plain English, with the jargon
spelled out the first time it appears.

> Audience: you. New to web ops, comfortable with code, want a mental
> model — not a man page. Skip to the diagram if you already know the
> vocabulary.

---

## The Five-Sentence Summary

1. **You push code to GitHub.**
2. **Railway** (a cloud platform) notices the push, reads `railway.toml`,
   and uses your `Containerfile` to build a **container image** — a
   sealed box containing Python, your app, and its dependencies.
3. Railway runs that box on a Linux machine it owns, attaches the
   managed **Postgres** database to it, and gives it a public URL.
4. When a browser hits the URL, Railway's **edge** terminates HTTPS and
   forwards the request to your container on an internal port.
5. Your **FastAPI** app handles the request, talks to Postgres, returns
   HTML or JSON.

That's it. The rest is detail.

---

## Why Docker / Containers At All?

You're right that "it works on my machine" is the headline reason
containers exist — but that problem has two halves:

| Half | Symptom | What containers fix |
| --- | --- | --- |
| **Dev → Dev** | "Works on Alice's laptop, broken on Bob's." | Same image runs on both laptops. Identical Python, identical libc, identical `psycopg`. |
| **Dev → Prod** | "Works on my laptop, crashes on the server." | The image you tested locally is *literally the same bytes* the server runs. No "I forgot to install X on prod." |

Railway leans hard on the **second** half. Their build server produces
the image, then their runtime server runs that image. Without
containers, Railway would have to guess "is this a Python app? Which
version? Does it need libpq?" — that's the **Railpack autodetect** path,
which is fragile. By giving them a `Containerfile`, you remove every
guess: "here is the exact recipe; build this; run this."

A container is **not** a VM. It's a Linux process tree with its own
filesystem view, sharing the host kernel. Boot is milliseconds, not
seconds. That's why Railway can afford to **sleep** your service when
idle and cold-start it on the next request.

### Why `Containerfile` and not `Dockerfile`?

Same file format, vendor-neutral name. `Dockerfile` is a Docker Inc.
trademark; `Containerfile` is what Podman and the OCI (Open Container
Initiative) standard call it. The contents are byte-identical. Railway
needs `railway.toml` to point at it because Railway's auto-detector
only recognizes the literal filename `Dockerfile`.

---

## The Production Line — One Diagram

```text
┌─────────────────┐    git push      ┌──────────────────┐
│ your laptop     │ ───────────────▶ │ GitHub (main)    │
│ (write code,    │                  └──────────────────┘
│  run tests)     │                          │
└─────────────────┘                          │ webhook
                                             ▼
                                  ┌─────────────────────────┐
                                  │ Railway build server    │
                                  │  reads Containerfile    │
                                  │  Stage 1: build wheel   │
                                  │  Stage 2: install wheel │
                                  │  → produces image:sha   │
                                  └─────────────────────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              │              │              │
                              ▼              ▼              ▼
                   ┌──────────────────┐  ┌──────────┐  ┌──────────┐
                   │ Pre-deploy step  │  │ Health   │  │ Traffic  │
                   │ alembic upgrade  │  │ check    │  │ swap     │
                   │ head             │──│ /health  │──│ old→new  │
                   └──────────────────┘  └──────────┘  └──────────┘
                            │                              │
                            └──────► Postgres ◄────────────┘
                                     (managed plugin)
                                             │
                                             ▼
                                  ┌────────────────────┐
                                  │ Public URL         │
                                  │ *.up.railway.app   │
                                  └────────────────────┘
                                             ▲
                                             │ HTTPS
                                  ┌────────────────────┐
                                  │ User's browser     │
                                  └────────────────────┘
```

Read top-to-bottom: code goes up, image gets built, migrations run,
healthcheck passes, traffic flips, browsers can reach it.

---

## What Each Piece Actually Is

### Railway

A **PaaS** — Platform-as-a-Service. You hand it a repo or an image; it
runs it on a Linux machine it owns and bills you per second of CPU/RAM.
Equivalents: Heroku (the original), Fly.io, Render, Google Cloud Run.

You don't manage:
- The machine (Railway picks one in their fleet).
- The OS (Linux, kept patched by Railway).
- The networking (Railway's edge handles TLS, routing, load balancing).
- The database server process (the Postgres plugin is managed).

You **do** manage:
- The image (your `Containerfile`).
- Environment variables (`DATABASE_URL`, `APP_ENV`, etc.).
- Migrations (`alembic upgrade head` in the pre-deploy step).
- Cost limits (the `$10` hard cap from `railway-setup.md` step 6).

### Service

A **service** is one long-running process on Railway. This project has
two:

| Service | What it is | Image source |
| --- | --- | --- |
| **web** | Your FastAPI app. Built from this repo. | `Containerfile` |
| **postgres** | A managed PostgreSQL 16 server. | Railway's prebuilt image |

The `web` service talks to `postgres` over Railway's private network
using the `DATABASE_URL` reference variable.

### Environment variables

Settings the app reads at startup. Three categories:

| Category | Examples | Where set |
| --- | --- | --- |
| **Injected by Railway** | `PORT`, `RAILWAY_*` | Railway runtime |
| **Linked from another service** | `DATABASE_URL` ← Postgres plugin | "Reference Variable" in dashboard |
| **You set by hand** | `APP_ENV`, `LOG_LEVEL`, `PAGE_SIZE_*` | Variables tab in dashboard |

The app reads them in [src/feedback_triage/config.py](../../src/feedback_triage/config.py)
via Pydantic Settings. Nothing else in the codebase reads `os.environ`
directly — that's deliberate, so the env-var surface is one file.

### `railway.toml`

The deploy contract, committed to the repo. It tells Railway:

- Which builder to use (`DOCKERFILE`, pointing at `Containerfile`).
- What command to run *before* swapping traffic (`alembic upgrade head`).
- Which URL to probe to confirm the app is alive (`/health`, 5s timeout).
- What to do if the container crashes (restart up to 3 times, then give up).

Anything you type into the Railway **dashboard** for these same fields
*overrides* the file. We deliberately leave the dashboard blank so the
file is the only source of truth.

### `Containerfile`

The recipe for building the image. Two stages:

1. **builder** — a temporary container with `uv` and Python build tools.
   Produces a `.whl` (wheel) file: your app, packaged.
2. **runtime** — a fresh slim container. Installs *only* the wheel and
   its runtime dependencies. No build tools, no source tree, no `.git`.
   This is the image Railway runs.

Multi-stage = small, hardened final image. The runtime image is ~150MB;
a single-stage image with `uv` and build tools left in would be 400MB+.

### Postgres plugin

A second container Railway runs alongside yours. Same physical machine,
internal network. Railway exposes it via `DATABASE_URL` — a single
string like `postgresql://user:pw@host:5432/db` that contains
everything `psycopg` needs to connect.

You linked it via **Variables → Reference Variable → Postgres →
DATABASE_URL** in the dashboard. That `${{ Postgres.DATABASE_URL }}`
syntax means "whatever Postgres's URL is right now" — if Railway
rotates the password, your service picks up the new value on next
restart with no code change.

### Healthcheck (`/health`)

Railway hits `GET /health` on the new container before sending real
traffic to it. If it returns `200 OK` within 5 seconds, traffic flips.
If it doesn't, Railway aborts the deploy and keeps the old version
serving. This is what gives you **zero-downtime deploys** for free.

There's also `/ready` — a readiness probe that touches the database.
We deliberately use `/health` (liveness only) for Railway's healthcheck
so a brief Postgres blip doesn't trigger a restart loop. See
[deployment-notes.md](../project/deployment-notes.md) for the full
reasoning.

### Pre-deploy command

A one-shot container Railway runs *against the new image* before any
traffic swap. We use it for `alembic upgrade head` — apply database
migrations. If migrations fail, the deploy aborts and the old version
keeps serving. This is why migrations don't run from `main.py` on
boot: starting the app and migrating the DB are separate concerns
with separate failure modes.

### App Sleeping

Idle services suspend. First request after suspension cold-starts in
1–3s. This is the single biggest cost lever — without it a `$5/mo`
service costs `$20/mo` because it's always running. With it, a
portfolio app costs pennies because it's only awake when someone is
looking at it.

---

## A Day In The Life Of One Request

User clicks "submit feedback" on the form at `/new`.

1. **Browser** sends `POST https://<service>.up.railway.app/api/v1/feedback`
   over HTTPS. Body is JSON.
2. **Railway edge** terminates TLS (decrypts the HTTPS), looks up which
   service owns that hostname, forwards the plain HTTP request to
   the `web` container on its internal port (8000).
3. **Uvicorn** (the ASGI server inside the container) receives the
   request, hands it to FastAPI.
4. **FastAPI** routes it to the handler in
   [src/feedback_triage/routers/feedback.py](../../src/feedback_triage/routers/feedback.py).
5. The handler asks for a database session via the `get_db` dependency.
   `get_db` opens a transaction on the connection pool.
6. **psycopg** sends the SQL `INSERT` over Railway's private network to
   the `postgres` container.
7. Postgres writes the row, returns the new ID.
8. The handler returns a Pydantic model; FastAPI serializes it to JSON.
9. `get_db` commits the transaction and closes the session.
10. The response goes back through Railway's edge to the browser.

Total time: ~50ms if the service is hot, ~1500ms if it just woke up.

---

## Things That Confused Me Too

### "Why are there so many config files?"

Each one belongs to a different tool:

| File | Tool | What it controls |
| --- | --- | --- |
| `pyproject.toml` | Python packaging | Dependencies, package metadata, ruff/mypy/pytest config |
| `uv.lock` | uv | Exact version of every transitive dependency |
| `Containerfile` | Docker/Podman | How to build the image |
| `railway.toml` | Railway | How to deploy the image |
| `docker-compose.yml` | Docker Compose | How to run locally with Postgres |
| `Taskfile.yml` | Task | Shortcuts for common commands |
| `alembic.ini` | Alembic | Database migration config |
| `.env` (gitignored) | Pydantic Settings | Local-dev env vars |

You didn't sign up for all of them — they each solve one problem and
the modern Python web stack happens to use all of them.

### "Why is the database URL a 'reference variable' instead of just pasted in?"

If you paste `postgresql://user:abc123@host/db` into the Variables tab
and Railway rotates Postgres's password tomorrow, your service breaks.
A reference variable says "look up Postgres's URL at deploy time" —
self-healing.

### "What's the difference between a build and a deploy?"

- **Build** — turn source code into an image. Runs on Railway's build
  server. Slow (1–3 minutes). Output is an image with a content hash.
- **Deploy** — take an existing image and run it as a service. Fast
  (10–30s). Includes pre-deploy command + healthcheck + traffic swap.

Every push triggers both. If you redeploy without changing code,
Railway can skip the build (cached image) and just re-run the deploy.

### "Is `0.0.0.0` a real IP?"

In `CMD ["sh", "-c", "uvicorn ... --host 0.0.0.0 ..."]`, `0.0.0.0`
means "listen on every network interface this container has." If you
used `127.0.0.1` (localhost), only processes *inside* the same
container could reach the app — Railway's edge couldn't forward
traffic in. Always `0.0.0.0` for containerized web apps.

---

## Where To Go Next

- [docs/project/railway-setup.md](../project/railway-setup.md) — the
  step-by-step click path.
- [docs/project/deployment-notes.md](../project/deployment-notes.md) —
  the *why* behind cost, pool sizing, healthcheck choice.
- [docs/adr/025-container-strategy.md](../adr/025-container-strategy.md)
  — why `Containerfile`, why multi-stage, why non-root.
- The image attached to this conversation (the deploy log) is the
  feedback loop: every line in it maps to a step in the diagram above.
