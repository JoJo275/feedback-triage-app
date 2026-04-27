# Deployment Notes — Railway

Practical notes on deploying the **Feedback Triage App** to Railway. This
doc covers the *operational* side of deployment (cost, config, sleep,
limits). For the *what to deploy* side — multi-stage `Containerfile`,
non-root user, `HEALTHCHECK`, image hardening — see the
[Container Hardening section in the spec](spec/spec.md#container-hardening-must).

---

## Deployment Topology

```text
1 Railway project
├── FastAPI web service  (this repo, deployed as a container image)
│   ├── serves /api/v1/*  (JSON API)
│   ├── serves /, /new, /feedback/{id}  (static HTML)
│   ├── serves /health, /ready  (probes)
│   └── serverless / app sleeping enabled
└── Railway Postgres 16
```

One service, one database. No worker, no scheduler, no separate frontend
host. Splitting any of these without an ADR is scope creep.

---

## Filesystem Persistence Warning

Railway container filesystems are ephemeral. Anything written inside the
container disappears on redeploy.

For this app:

- **Bad:** SQLite file inside the app container.
- **Bad:** user uploads inside the app container.
- **Good:** managed Railway Postgres for all persistent feedback data.
- **Good:** external object storage (S3, R2) for files, *if* uploads are
  ever added — listed under Future Improvements.

Use Postgres for persistent feedback data. Do not use local SQLite for the
deployed version; SQLite is also explicitly banned for tests
([spec — Test Database Strategy](spec/spec.md#test-database-strategy)).

---

## Required Environment Variables

Set these in the Railway service settings. Anything marked `(injected)` is
provided by Railway automatically when the Postgres plugin is attached.

| Variable                | Value / source                                         |
| ----------------------- | ------------------------------------------------------ |
| `DATABASE_URL`          | (injected) by the Railway Postgres plugin              |
| `APP_ENV`               | `production`                                           |
| `LOG_LEVEL`             | `INFO`                                                 |
| `PORT`                  | (injected) by Railway                                  |
| `CORS_ALLOWED_ORIGINS`  | empty (same-origin) unless serving from another origin |
| `PAGE_SIZE_DEFAULT`     | `20` (default in `config.py`; override only if needed) |
| `PAGE_SIZE_MAX`         | `100`                                                  |

Do **not** hand-construct `DATABASE_URL` from username / password / host
components on Railway — use the injected value directly. The connection
string format expected by the app is:

```env
postgresql+psycopg://<user>:<password>@<host>:<port>/<db>
```

Railway sometimes injects the URL as `postgres://` (no driver). Normalize
in `config.py` by rewriting the scheme to `postgresql+psycopg://` at load
time; do not require manual editing in the dashboard.

---

## Migrations on Railway

Migrations must run as a **separate one-shot job** before the new release
takes traffic, never from `main.py` on app startup. Two web workers
booting in parallel will race on the migration lock and one will crash.

**Preferred:** set the service's **Pre-Deploy Command** to:

```bash
alembic upgrade head
```

Railway runs the pre-deploy command in a one-off container against the
new image, then swaps traffic to the new release only if it succeeds. If
migrations fail, the old version keeps serving traffic.

Alternatives (see [spec — Running migrations on Railway](spec/spec.md#running-migrations-on-railway)):

1. `railway run -- alembic upgrade head` from a developer machine, gated
   behind a release runbook checklist. Acceptable for a portfolio
   project; brittle for a real team.
2. Separate `migrate` service in `railway.toml` that runs once and
   exits. Heaviest setup; only justified if migrations grow long enough
   to time out a pre-deploy hook.

---

## Web Process Configuration

Start command for the web service:

```bash
uvicorn feedback_triage.main:app --host 0.0.0.0 --port $PORT --workers 2
```

`--workers 2` is the v1.0 default per
[spec — Concurrency model](spec/spec.md#concurrency-model). Two workers
survive a single slow request without dropping the next; one worker
queues every request behind the slowest. If you are running on Railway
Hobby with tight memory limits and the demo is purely portfolio-grade
(no real users), dropping to `--workers 1` is acceptable — note it as a
deviation from the spec's default and revert before claiming production
readiness.

### Pool sizing math

`pool_size * workers ≤ Postgres max_connections`

Railway's default Postgres exposes ~20 connections. With `pool_size=5`,
`max_overflow=5`, and `--workers 2`, peak is **20**, which fits exactly.
Bumping workers requires raising the DB plan first.

---

## Healthchecks

Railway healthchecks should hit `/health`, **not** `/ready`.

- `/health` — liveness only; never touches the DB. A failure means the
  process is wedged and should be restarted.
- `/ready` — readiness; runs `SELECT 1` with a 2s timeout. A failure
  means "stop sending traffic for now" but the process itself is fine.

Conflating them causes restart loops on transient DB blips. See
[spec — Health and readiness](spec/spec.md#health-and-readiness).

Configure Railway:

- **Healthcheck path:** `/health`
- **Healthcheck timeout:** 5s (well above the 2s readiness budget, since
  liveness should be effectively instant)

---

## Cost Controls

Railway charges for resource usage (CPU, memory, storage, egress), not
just traffic. On Hobby, the $5 subscription counts toward usage; if you
exceed $5 in resources, you pay the difference. A running service
consumes CPU and RAM regardless of whether traffic is hitting it.

**Cost-saving goal:** keep the app small, idle, and sleeping when not used.

### 1. Enable Serverless / App Sleeping

Sleeps inactive services. Tradeoff: first request after sleep has a cold-
start delay (typically 1–3s for this app). Fine for portfolio / demo.

**Caution:** outbound traffic prevents sleep. Avoid background loops,
scheduled polling, telemetry, and constant outbound calls. None of these
are in v1.0; do not add them.

### 2. Set a hard usage limit immediately

For a learning / portfolio app:

- Alert at ~$3–$4
- Hard limit at ~$5–$7

A misconfigured loop or runaway worker should not become an expensive bill.

### 3. Resource limits

For this CRUD app:

- 1 replica only
- Low memory limit (256 MB is comfortable)
- Low CPU limit
- Do not horizontally scale

### 4. Keep the database small

- Paginate `GET /api/v1/feedback` (default `limit=20`, max `100`)
- Add indexes only as specified in the spec (`created_at DESC`, `status`,
  `source`)
- Do not store huge text blobs (`description` capped at 5000 chars)
- Do not store files in Postgres
- Seed only a small amount of demo data (~20 rows via `task seed`)

### 5. No expensive background logic

Skip scrapers, scheduled jobs, AI summarization, polling, analytics,
long-running workers, browser automation, file processing. None are in
v1.0; promoting them out of Future Improvements requires an ADR.

---

## Backups

Production backups are handled by Railway (point-in-time recovery on
paid plans). Document this in the README; do not roll your own.

For local dev, the spec defines `task db:dump` / `task db:restore` —
those exist for "do not lose demo data on `docker compose down -v`,"
not for production DR.

---

## Release Flow Summary

Per [spec — Release Flow](spec/spec.md#release-flow-must), this project
separates **Deploy** (continuous, every merge to `main`) from **Release**
(tag-driven via release-please).

**Deploy (every PR merge):**

1. PR merged to `main` (CI gate required, rebase merge, branch protected).
2. Railway — configured with this **GitHub repo** as its source — pulls
   the new commit and builds from `Containerfile`.
3. Railway runs the pre-deploy command (`alembic upgrade head`).
4. Railway starts the new container; healthcheck on `/health` must pass
   before traffic swaps over.

If step 3 fails, the previous container keeps serving. That is the
entire rollback story for v1.0; forward-only migrations are part of the
discipline that makes this safe.

**Release (cadence chosen by humans):**

1. release-please maintains an open Release PR on `main` with the
   computed version bump and `CHANGELOG.md` updates.
2. Merging the Release PR creates the tag (e.g. `v1.0.0`) and publishes
   the GitHub Release with auto-generated notes.
3. The tag triggers `release.yml`, which runs the full CI gate, builds
   the image, and pushes it to GHCR tagged with the version and the
   commit SHA.
4. **Railway is unaffected by the tag** — the deploy that shipped this
   commit already happened when the underlying feature PRs merged.

`task release VERSION=vX.Y.Z` exists only as an emergency fallback for
when release-please is unavailable.

---

## Cheapest Sane Setup

```text
Railway Hobby
├── FastAPI app (this repo)
│   ├── 1 replica, --workers 2  (or --workers 1 for tightest cost)
│   ├── Pre-deploy: alembic upgrade head
│   ├── Healthcheck: /health
│   └── Serverless / app sleeping enabled
└── Railway Postgres 16
```

Configure:

- Hard usage limit
- One replica
- Low CPU / memory limits
- Pre-deploy migrations
- Healthcheck on `/health`
- No cron jobs, no background workers, no AI, no telemetry

---

## Best Practice for This Project

- Build locally first; deploy to Railway only when you want a public demo.
- Use Docker Compose with Postgres 16 locally to mirror production.
- Enable Serverless / App Sleeping.
- Set a hard usage limit before the first deploy, not after.
- Keep everything in one FastAPI service plus Postgres.
- Treat Railway as the demo target, not the source of truth — the
  source of truth is `docs/project/spec/spec.md`.

---

## Related docs

- [`spec/spec.md`](spec/spec.md) — canonical project spec
- [`questions.md`](questions.md) — open questions and their answers
- [`implementation.md`](implementation.md) — phase-by-phase build plan
