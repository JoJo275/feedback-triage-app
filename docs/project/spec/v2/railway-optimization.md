# v2.0 — Railway optimization (cost & resource posture)

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> See also: [`rollout.md`](rollout.md),
> [`performance-budgets.md`](performance-budgets.md),
> [`observability.md`](observability.md).

This file is the **playbook for keeping the Railway bill at or
under the $5 Hobby subscription's included credit** while v2.0 is
in alpha/beta and the user base is single digits. Every choice
here is reversible; we'll revisit when real traffic justifies
more spend.

**Cost target:** stay within the **$5/month Hobby credit**. The
subscription pays for usage; we are aiming for usage to fit
inside it without overage.

---

## Posture in one sentence

**Run two Railway services (FastAPI + Postgres), nothing else.**
No Redis, no separate worker, no job queue, no CDN, no
preview environments by default.

---

## Service inventory

| Service                 | Plan                  | Sleep                  | Notes                                                             |
| ----------------------- | --------------------- | ---------------------- | ----------------------------------------------------------------- |
| `app` (FastAPI)         | Hobby ($5 credit)     | **On (serverless)**    | Single replica, single region. Auto-restart on crash. Sleep stays on while cold-start P95 is acceptable; flip off if it becomes user-visible. |
| `postgres`              | Postgres Hobby        | n/a                    | Managed Postgres 16. Single node. **5 GB volume** — enormous headroom for v2.0 footprint (see Storage below). |
| `staging` (preview env) | **Off by default**    | n/a                    | Spun up only for the rare PR that needs it; torn down on merge.   |
| Cron jobs               | Built-in scheduler    | n/a                    | Free with the `app` service. **Verify cron behavior with sleep ON** — see Sleep policy. |

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
| Memory            | **~700 MB** target with 2 workers, 1 GB hard ceiling. OOM kills surface as a `CRITICAL` log line. Argon2id verify uses ~32 MB transient memory per hash; 2 workers comfortably absorb a small login burst. |
| Workers           | `uvicorn --workers 2` in v2.0. Two workers cover concurrent Argon2id verifies during login bursts and give a single-tenant deploy a small amount of head-of-line resilience. Drop to 1 only if memory pressure becomes an issue. |
| Restart policy    | `on-failure` with exponential backoff. Five failures in 5 minutes → mark unhealthy.    |
| Healthcheck       | `GET /healthz` every 30s. Two failures → restart.                                      |
| Image size        | < 250 MB compressed (multi-stage `Containerfile`, `python:3.12-slim` base).            |

### Postgres service

| Knob              | Value                                                                                  |
| ----------------- | -------------------------------------------------------------------------------------- |
| Plan              | Hobby                                                                                  |
| Storage           | **5 GB volume provisioned** — huge headroom. v2.0's working set (workspaces + feedback_items + email_log + sessions) is well under 100 MB through the alpha/beta phases. Alert at 70 % only if growth ever becomes non-trivial. |
| Connections       | Pool size **5 per worker** = 10 connections in steady state, hard ceiling **15** (room for cron + migration overlap). SQLAlchemy: `pool_size=5, max_overflow=0` per worker. Hobby Postgres connection limit is the cost trap; respect it. |
| Backups           | Railway daily snapshot (built-in). Plus monthly off-platform export (see below).       |

The connection-pool ceiling is the **single biggest cost trap**
on Hobby Postgres — exceeding it stalls requests. The session-per-request
contract in [`copilot-instructions.md`](../../../../.github/copilot-instructions.md)
is non-negotiable: never hold a session on `app.state` or in a
module global.

### Storage — 5 GB on $5 Hobby

5 GB is comfortable for v2.0. Reference points:

- v1.0 single-table footprint at hundreds of feedback rows: < 5 MB.
- v2.0 schema (workspaces, users, sessions, tokens, memberships,
  invitations, feedback_item, submitters, tags, notes, email_log)
  with single-tenant alpha traffic: ~50–100 MB through year one.
- The largest growth surface is `email_log`, which is bounded by
  the 90-day prune ([ADR 061](../../../adr/061-resend-email-fail-soft.md)).

Meaning: **storage is not what threatens the $5 ceiling**. Compute
wall-time and egress are. Don't pre-shrink the volume — the cost
delta is negligible and headroom matters when Migration B runs.

---

## Sleep policy

**Current posture: Railway serverless / sleep is ON.** Empirically
cold-start has been imperceptible at v1.0 footprint, and sleep is
the single biggest lever for staying inside the $5 Hobby credit.

### Why we keep it on

1. We're targeting the $5 Hobby credit, not a P95-budget for a
   paying customer. A 1–2 s cold-start once an hour is acceptable
   for an alpha/beta tool with single-digit DAU.
2. Empirical cold-start has been "barely noticeable" — keep that
   measurement honest by re-checking after Phase 1 lands.
3. The compute saved by sleeping overnight + weekends is the
   majority of monthly wall-time at this scale.

### What v2.0 adds to cold-start

Vs v1.0, expect ~200–500 ms more first-request latency from a cold
worker. Sources:

| Adds at cold start                                          | Approx |
| ----------------------------------------------------------- | ------ |
| `argon2-cffi` native-lib load + first-verify self-test      | 50–200 ms |
| `httpx` client init for Resend                              | 30–80 ms  |
| Auth + tenancy + email module imports                       | 50–150 ms |
| Jinja env init for email templates                          | 20–50 ms  |
| Extra SQLModel metadata (more tables in registry)           | 30–80 ms  |

The two cold-start cases that *might* become user-visible:

- **First sign-in after a cold boot.** Argon2id verify is
  intentionally slow (~150–300 ms) and pays the native-lib load
  on its first call — so the first login of a wake cycle can feel
  ~400–600 ms slower than the second. Mitigation if it becomes a
  complaint: a tiny `argon2.PasswordHasher().hash("warmup")` call
  in the FastAPI startup hook to pay the cost on boot, not on a
  user request.
- **Cron jobs hitting a sleeping app.** Verify Railway's behavior:
  do scheduled crons wake the service or skip while asleep? Test
  this once after Phase 1 deploy with the session-GC job. If it
  skips, either (a) flip sleep off, or (b) make the cron tolerate
  missed windows (session GC and email_log prune already do).

### When to turn sleep OFF

Flip serverless off if **any** of:

- Cold-start P95 on the first request after wake exceeds 3 s
  (sustained, not a one-off).
- A real user reports the wake delay.
- A cron job is silently missed because the app was asleep, and
  rewriting the cron to be miss-tolerant is more work than
  paying for always-on.
- Monthly bill is comfortably *under* $5 with sleep on, and
  always-on still fits the credit.

Flipping sleep off is a Railway service-setting toggle, not a
code change. Always reversible.

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

| Threshold                                  | Action                                              |
| ------------------------------------------ | --------------------------------------------------- |
| Estimated month-end usage > **$5 credit**  | **Hard cap reached** — first lever: confirm sleep is on; second lever: drop to 1 worker; third lever: re-run this file's choices. |
| Monthly cost > $10                         | Anomaly — investigate. Likely cause: sleep got disabled, or a runaway cron, or unbounded list endpoint egress. |
| Monthly cost > $20                         | Hard review — v2.0 has outgrown Hobby; either upgrade plan deliberately or cut scope. |
| Estimated month-end > $30                  | Stop. Identify the regression before continuing.    |

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

- The Hobby plan's $5 credit no longer fits a normal-traffic month.
- The Hobby plan's resource limits change.
- Daily active users exceed **20**.
- Postgres storage exceeds **3 GB** (still well under the 5 GB
  volume — just a heads-up trigger to plan ahead).
- The connection pool sees > 80 % checkout utilization on a
  rolling 24 h window.
- Cold-start P95 after a sleep wake exceeds 3 s sustained, **or**
  a user reports the wake delay.
- Any of the "explicitly does not do" items becomes a recurring
  source of pain.

Until then, the boring two-service setup is correct.
