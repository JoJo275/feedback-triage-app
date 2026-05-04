# v2.0 — Railway optimization (cost & resource posture)

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> See also: [`rollout.md`](rollout.md),
> [`performance-budgets.md`](performance-budgets.md),
> [`observability.md`](observability.md).

This file is the **playbook for keeping the Railway bill near
zero** while v2.0 is in alpha/beta and the user base is single
digits. Every choice here is reversible; we'll revisit when real
traffic justifies more spend.

---

## Posture in one sentence

**Run two Railway services (FastAPI + Postgres), nothing else.**
No Redis, no separate worker, no job queue, no CDN, no
preview environments by default.

---

## Service inventory

| Service                 | Plan                  | Sleep      | Notes                                                             |
| ----------------------- | --------------------- | ---------- | ----------------------------------------------------------------- |
| `app` (FastAPI)         | Hobby ($5 credit)     | No         | Single replica, single region. Auto-restart on crash.             |
| `postgres`              | Postgres Hobby        | No         | Managed Postgres 16. Single node.                                 |
| `staging` (preview env) | **Off by default**    | n/a        | Spun up only for the rare PR that needs it; torn down on merge.   |
| Cron jobs               | Built-in scheduler    | n/a        | Free with the `app` service. See [`performance-budgets.md`](performance-budgets.md). |

That's it. **No Redis** (the dashboard cache is in-process —
`cachetools.TTLCache`, see [`performance-budgets.md`](performance-budgets.md)).
**No object-storage service** (backups go to an external S3-compatible
bucket; see "Backups" below).

---

## Resource budgets

### App service

| Knob              | Value                                                                                  |
| ----------------- | -------------------------------------------------------------------------------------- |
| CPU               | Shared (Hobby tier default)                                                            |
| Memory            | **512 MB** target, 1 GB hard ceiling. OOM kills surface as a `CRITICAL` log line.       |
| Workers           | `uvicorn --workers 1` in v2.0. Sync routes; a second worker doubles memory for no real throughput gain at our scale. |
| Restart policy    | `on-failure` with exponential backoff. Five failures in 5 minutes → mark unhealthy.    |
| Healthcheck       | `GET /healthz` every 30s. Two failures → restart.                                      |
| Image size        | < 250 MB compressed (multi-stage `Containerfile`, `python:3.12-slim` base).            |

### Postgres service

| Knob              | Value                                                                                  |
| ----------------- | -------------------------------------------------------------------------------------- |
| Plan              | Hobby                                                                                  |
| Storage           | Start at **1 GB**; bump in 1 GB steps as `pg_database_size` approaches 70%. Alert at 80%. |
| Connections       | Pool size **5** in app, hard ceiling **10**. Hobby Postgres is connection-limited;     |
|                   | one worker × 5 connections is comfortable. SQLAlchemy: `pool_size=5, max_overflow=0`.  |
| Backups           | Railway daily snapshot (built-in). Plus monthly off-platform export (see below).       |

The connection-pool ceiling is the **single biggest cost trap**
on Hobby Postgres — exceeding it stalls requests. The session-per-request
contract in [`copilot-instructions.md`](../../../../.github/copilot-instructions.md)
is non-negotiable: never hold a session on `app.state` or in a
module global.

---

## Sleep policy

We **do not** put the app to sleep on Hobby tier. Reasons:

1. Cold-start adds 2–4s to the first request, which fails our
   P95 budget ([`performance-budgets.md`](performance-budgets.md)).
2. The cron jobs (session GC, demo reset) need a live process.
3. The credit difference between always-on and sleep-when-idle
   is < $1/month at our footprint.

If we ever need to sleep, the threshold is "monthly Railway bill
exceeds $20 and < 10 daily active users." Until then, always-on.

---

## Image-size minimization

The `Containerfile` uses a four-stage build:

1. **`builder-uv`** — installs `uv`, runs `uv sync --frozen` into
   `/app/.venv`. Heavy: includes the full Python dev stack.
2. **`builder-frontend`** — runs the Tailwind Standalone CLI to
   build `static/css/app.css`. Tailwind binary is ~30 MB; it does
   not ship to the runtime image.
3. **`builder-app`** — copies the source tree, runs
   `python -m compileall` to pre-compile bytecode.
4. **`runtime`** — `python:3.12-slim`, copies only `/app/.venv`,
   `/app/src`, `/app/static`, `/app/alembic`, and the entrypoint.
   No build tools, no `uv`, no Tailwind binary, no test suite.
   `USER nonroot`.

**What's banned in `runtime`:**

- `apt install` of anything not strictly needed (no `git`, no
  `vim`, no `curl` — `wget` only if `HEALTHCHECK` insists, but
  prefer `python -c`).
- Test dependencies (`pytest`, `playwright`, `httpx[testing]`).
- Source maps for production CSS. Tailwind builds with
  `--minify` and no source maps.

Target: **runtime image < 250 MB compressed**. Bandwidth and
deploy time both scale with image size on Railway.

---

## Cron jobs and their cost

Cron is free with the app service, but the *frequency* directly
affects compute usage. Budgets from
[`performance-budgets.md`](performance-budgets.md):

| Job                          | Frequency  | Why not more often                                              |
| ---------------------------- | ---------- | --------------------------------------------------------------- |
| Session GC                   | hourly     | Sessions live 7 days; an hour of stale rows is fine.            |
| Token GC                     | hourly     | Verification + reset tokens have ≤ 24h TTLs.                    |
| Demo workspace reset         | 24h, 03:00 UTC | Demo data is meant to look "yesterday-ish"; daily is plenty. |
| `email_log` retention prune  | 24h        | We hold 90 days of email send history; daily prune is enough.   |
| Backup export                | weekly     | See "Backups" below.                                            |

**Forbidden** without an ADR: any cron more frequent than 5
minutes. A 1-minute cron consumes ~720× the wall time of an
hourly one and will reliably eat through Hobby credits.

---

## Backups

Two layers:

1. **Railway daily snapshots** — automatic, retained per
   Railway's policy (currently 7 days on Hobby). This is our
   day-to-day rollback path.
2. **Weekly off-platform export** — a Railway cron runs
   `scripts/backup_export.py`, which `pg_dump`s the database
   (compressed, custom format) and uploads to a cheap external
   S3-compatible bucket (Backblaze B2 is the current target).
   Retention: 12 weekly + 6 monthly.

The off-platform export is the **disaster-recovery path** —
"Railway-account-was-deleted" or "Railway-region-is-down". Cost:
< $1/month for the bucket at v2.0 footprint.

The pre-cutover backup for v1.0 → v2.0 ([`migration-from-v1.md`](migration-from-v1.md))
goes to the same bucket with a distinguishable filename.

---

## Egress

Railway charges for egress beyond the included allotment. Things
that can blow this budget:

- Returning huge JSON arrays unbounded. Mitigated by the
  pagination contract in [`api.md`](api.md) (max `limit=200`).
- Image uploads. **v2.0 does not support uploads.** Submitters
  paste URLs at most.
- Email attachments. We don't send any.
- Backup export weight. The weekly `pg_dump` runs *inside*
  Railway and uploads to B2 — that traffic counts as egress.
  At v2.0 DB size (< 1 GB), it's negligible.

---

## Alert thresholds (cost)

In addition to the operational alerts in
[`observability.md`](observability.md), set Railway's billing
alerts to:

| Threshold                        | Action                                              |
| -------------------------------- | --------------------------------------------------- |
| Monthly cost > $5                | Notice — expected baseline                          |
| Monthly cost > $10               | Investigate — anomaly or growth?                    |
| Monthly cost > $20               | Hard review — re-run this file's choices            |
| Estimated month-end > $30        | Consider sleep policy + reducing replica count      |

---

## Things v2.0 explicitly does **not** do

- **No Redis.** The dashboard cache is in-process. Rate limiting
  is in-process (`asyncio` + `cachetools`); see
  [`security.md`](security.md). If a second app replica is ever
  added, rate limits become per-replica, which is acceptable
  trade-off for v2.0 traffic.
- **No queue / no separate worker.** Email sending is fire-and-forget
  inline with fail-soft semantics ([`email.md`](email.md)).
  Background work is cron-driven, not queue-driven.
- **No CDN.** Static assets are served by FastAPI's `StaticFiles`
  with `Cache-Control: public, max-age=31536000, immutable` on
  hash-suffixed filenames ([`performance-budgets.md`](performance-budgets.md)).
  The browser cache is the CDN.
- **No multi-region.** Single region (whichever Railway defaults
  to). Latency for distant users is acceptable for a B2B triage
  tool.
- **No preview environments by default.** PRs run CI; if a PR
  genuinely needs a live preview, the developer spins one up
  manually and tears it down on merge.

---

## When to revisit this file

- The Hobby plan's resource limits change.
- Daily active users exceed **20**.
- Postgres storage exceeds **3 GB**.
- The connection pool sees > 80% checkout utilization on a
  rolling 24h window.
- Any of the "explicitly does not do" items becomes a recurring
  source of pain.

Until then, the boring two-service setup is correct.
