# Railway Setup Runbook — Feedback Triage App

Step-by-step runbook for standing up the Railway side of Phase 7. This
is the **operator's checklist** — what to click, what to paste, what to
hand back to me so I can continue iterating on Phase 7 and beyond.

For the *why* behind these choices (cost, sleep, pool sizing, healthcheck
semantics, release flow), read [`deployment-notes.md`](deployment-notes.md)
first. This file is the literal "do these things in this order" companion.

> **Status (2026-04-28):** in-repo Phase 7 work is done — `Containerfile`
> is digest-pinned, the GHCR build pipeline and Trivy/Grype scan
> workflows are wired up. The remaining Phase 7 [Must] items all live
> in the Railway dashboard and need a human with an account.

---

## What is Railway, in 30 seconds

Railway is a PaaS that builds an OCI image from your repo (or your
`Containerfile`), runs it as a long-lived service, and bills per second
of CPU/RAM/egress against a monthly credit. Think "Heroku, but you can
also bring a `Containerfile`, and the database is a one-click plugin."

Relevant primitives for this project:

| Concept | What it means here |
| --- | --- |
| **Project** | Logical grouping. One project for the whole app. |
| **Service** | A long-running process. We have **two**: the FastAPI web service (this repo), and the managed **Postgres** plugin. |
| **Plugin** | Managed addon. Postgres 16 is a plugin; attaching it injects `DATABASE_URL` into linked services. |
| **Environment** | Named copy of a project (e.g. `production`). v1.0 uses one — `production` — and treats local Docker Compose as "staging". |
| **Pre-Deploy Command** | A one-shot container Railway runs *against the new image* before swapping traffic. Where `alembic upgrade head` lives. Failure aborts the deploy; old version keeps serving. |
| **Healthcheck** | HTTP probe Railway runs against the new container before it accepts traffic. Must hit `/health` (liveness), not `/ready` (DB-touching). |
| **App Sleeping / Serverless** | Idle services suspend; first request after sleep cold-starts in ~1–3s. The single biggest cost lever for this stack. |
| **Hard Usage Limit** | Per-project cap. If billed usage hits it, the project stops. The difference between a \$7 month and a \$700 surprise. |

---

## Prerequisites

Have these ready before clicking anything in Railway:

- A GitHub account with **admin or write** access to
  `JoJo275/feedback-triage-app`. Railway needs to install its GitHub App
  on the repo to enable continuous deploy.
- A payment method on the Railway account (Hobby plan, ~$5/mo).
  Railway will not run a long-lived service on the free trial credit.
- Decide on a **public service name** before creating it. Railway uses
  it to build the default URL (`<service>.up.railway.app`). Suggested:
  `feedback-triage` (lowercase, hyphenated).

---

## One-Time Setup — Click Path

Do these in order. Each step has a "what good looks like" check at the
end so you can tell whether it actually took.

### 1. Create the Railway project

1. Sign in to <https://railway.com>.
2. **New Project → Deploy from GitHub repo**.
3. Authorize the Railway GitHub App against
   `JoJo275/feedback-triage-app`. Grant access to the single repo, not
   the whole org.
4. When Railway asks "what should we build?", the repo's
   [`railway.toml`](../../railway.toml) pins the builder to
   `DOCKERFILE` with `dockerfilePath = "Containerfile"`. Railpack does
   **not** auto-detect `Containerfile` (only literal `Dockerfile`), so
   without this config Railway falls back to Python autodetect and
   fails with `No start command detected`. The spec mandates the
   multi-stage Containerfile per
   [Container Hardening](spec/spec-v1.md#container-hardening-must).

✅ **Check:** the project dashboard shows one service whose source is
`JoJo275/feedback-triage-app @ main` and whose builder is `Dockerfile`
(Railway's label for any OCI build).

### 2. Add Postgres

1. In the project, **+ New → Database → Add PostgreSQL**.
2. Wait for the plugin to provision (typically <60s). It exposes
   `DATABASE_URL`, `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`,
   `PGDATABASE`.
3. **Link the plugin to the web service**: open the web service →
   **Variables → Reference Variable → Postgres → `DATABASE_URL`**. This
   is the only env var you need to wire by hand; Railway auto-injects
   the rest if linked.

✅ **Check:** the web service's **Variables** panel shows
`DATABASE_URL` resolving to a `${{ Postgres.DATABASE_URL }}` reference,
not a hand-pasted string.

### 3. Set service variables

In **web service → Variables**, add:

| Key | Value |
| --- | --- |
| `APP_ENV` | `production` |
| `LOG_LEVEL` | `INFO` |
| `CORS_ALLOWED_ORIGINS` | *(leave empty)* |
| `PAGE_SIZE_DEFAULT` | `20` |
| `PAGE_SIZE_MAX` | `100` |

Do **not** set `PORT` (Railway injects it) and do **not** hand-paste
`DATABASE_URL` (the reference from step 2 handles it).

> **Driver scheme gotcha:** Railway sometimes injects `DATABASE_URL` as
> `postgres://...` rather than `postgresql+psycopg://...`. The app
> normalizes this in `config.py` per
> [`deployment-notes.md`](deployment-notes.md#required-environment-variables);
> no manual edit needed. If a deploy fails on URL parsing, that
> normalization is the first thing to check.

✅ **Check:** all five vars listed, plus the linked `DATABASE_URL`
reference. Total of six entries.

### 4. Wire the deploy lifecycle

[`railway.toml`](../../railway.toml) at the repo root owns the deploy
lifecycle: pre-deploy command, healthcheck path/timeout, and restart
policy. **Leave the dashboard fields blank** so there is exactly one
source of truth — anything typed into **Settings → Deploy** wins over
`railway.toml` and creates drift.

In **web service → Settings → Deploy**, confirm:

| Field | Value |
| --- | --- |
| **Branch** | `main` |
| **Build Command** | *(empty)* |
| **Pre-Deploy Command** | *(empty — set by `railway.toml`)* |
| **Start Command** | *(empty — image's `CMD` handles it)* |
| **Healthcheck Path** | *(empty — set by `railway.toml`)* |
| **Healthcheck Timeout** | *(empty — set by `railway.toml`)* |
| **Restart Policy** | *(empty — set by `railway.toml`)* |

The values that `railway.toml` actually sets:

- `preDeployCommand = "alembic upgrade head"`
- `healthcheckPath = "/health"`
- `healthcheckTimeout = 5`
- `restartPolicyType = "ON_FAILURE"` with `restartPolicyMaxRetries = 3`

> **Why `/health`, not `/ready`:** liveness probes restart the
> container on failure; readiness probes just stop traffic. A DB blip
> against `/ready` would cause restart loops. See
> [spec — Health and readiness](spec/spec-v1.md#health-and-readiness).

✅ **Check:** the next deploy log shows a "Pre-deploy" step running
`alembic upgrade head` *before* the "Healthcheck" step. If you ever
need to change one of these knobs, edit `railway.toml` in a PR — do
not paste a value into the dashboard.

### 5. Enable App Sleeping

In **web service → Settings → Serverless**:

- Toggle **App Sleeping** **on**.
- Idle timeout: default (Railway picks ~10 minutes).

This is the single biggest cost lever. Don't skip it. See
[`deployment-notes.md` — Cost Controls](deployment-notes.md#cost-controls).

✅ **Check:** service status flips to `Sleeping` after ~10 minutes of
no traffic; first request after that takes 1–3s and then it's hot
again.

### 6. Set the hard usage limit *before* the first real deploy

In **Project → Settings → Usage**:

- **Hard limit:** `$10`
- **Alert threshold:** `$6`

Per [`deployment-notes.md`](deployment-notes.md#cost-controls), do this
**before** continuous deploy starts cooking — a misconfigured loop in
the first hour should fail closed, not become a bill.

✅ **Check:** the Usage page shows `$10.00` as the hard cap and an alert
configured at `$6.00`.

### 7. Trigger the first real deploy

Either push any commit to `main` or click **Deploy** on the service.

Watch for:

1. Build logs show `docker build` against `Containerfile`. If they show
   Nixpacks instead, go back to step 1 and force the builder to
   Dockerfile.
2. Pre-deploy logs show `alembic upgrade head` creating the
   `feedback_item` table and applying revision `0001`.
3. Healthcheck against `/health` returns `200` within 5s.
4. Traffic swaps to the new container.

✅ **Check (smoke):**

```bash
APP=https://<your-service>.up.railway.app
curl -sf "$APP/health"                 # 200, '{"status":"ok"}'
curl -sf "$APP/ready"                  # 200 once DB is reachable
curl -sf "$APP/api/v1/feedback"        # 200, envelope shape
curl -sf "$APP/api/v1/docs" -o /dev/null && echo "docs ok"
curl -sf "$APP/" -o /dev/null && echo "html ok"
```

All five must pass to close Phase 7's DoD. If any fail, capture the
deploy log and hand it back to me — see "Information I need" below.

### 8. (Optional, [Should]) Wire GHCR pulls

Railway can build from source (what we just configured) **or** pull a
pre-built image from a registry. The repo already builds and pushes to
`ghcr.io/jojo275/feedback-triage-app` on every merge to `main` and on
tag (see [`.github/workflows/container-build.yml`](../../.github/workflows/container-build.yml)).
Switching Railway to pull from GHCR instead of building locally saves
build minutes and gives a single image hash deployed in CI and on
Railway. Worth doing once the GHCR push is green for a few merges; not
required to close Phase 7.

If/when we flip this:

1. Make the GHCR package public, or generate a Railway-scoped PAT with
   `read:packages` and store it as a Railway image registry credential.
2. In **Service → Settings → Source**, switch from **GitHub Repo** to
   **Docker Image** and point at
   `ghcr.io/jojo275/feedback-triage-app:latest`.
3. Keep the same Pre-Deploy Command, healthcheck, and env vars.

---

## What I Need to Continue Phase 7+

I (Copilot) cannot click in the Railway dashboard, see your billing, or
read deploy logs unless you paste them. To unblock the rest of Phase 7
and start Phase 8, hand back **all** of the following in one batch:

### Phase 7 close-out

- [ ] **Public service URL** — the `https://<...>.up.railway.app` (or
      custom domain). Goes in the README header per
      [spec — README Sections to Include](spec/spec-v1.md#readme-sections-to-include-must).
- [ ] **Confirmation each step 1–7 above is green**, ideally as a
      copy-paste of the seven `✅ Check` lines with "done" or the actual
      observed value.
- [ ] **First deploy log excerpt** — specifically the Build, Pre-Deploy,
      and Healthcheck sections. Redact secrets. ~50 lines is plenty.
- [ ] **Output of the five smoke `curl`s** from step 7. If any failed,
      include the failing response body and status.
- [ ] **Postgres connection limit** — from the Postgres plugin's
      Connect tab, the value of `max_connections`. The spec assumes ~20
      and sizes the pool accordingly; if Railway's default has changed,
      I'll need to revisit `pool_size` / `max_overflow` in
      [`deployment-notes.md`](deployment-notes.md#pool-sizing-math).

### Phase 8 inputs (collect while you're in there)

- [ ] **Three screenshots** of the running app — list page at `/`, new
      item form at `/new`, detail page at `/feedback/{id}`. PNG, ~1280px
      wide. Drop them in `docs/screenshots/`. I'll wire the README.
- [ ] **Confirmation that `task seed` ran successfully against
      production** (or that you'd rather seed manually via the UI). Per
      Phase 8, ~20 demo items covering every `Source` and `Status`.
- [ ] **GHCR package visibility** — public or private? Affects the
      README badge and the optional flip in step 8 above.

### Optional but useful

- [ ] **A custom domain** if you want one (e.g. `feedback.<yourname>.dev`).
      Adds a CNAME setup step but makes the README link nicer.
      **Status (May 2026):** `signalnest.app` is the chosen custom
      domain (Cloudflare Registrar). Wiring procedure and Cloudflare
      configuration live in
      [`docs/notes/domain-and-cloudflare.md`](../notes/domain-and-cloudflare.md);
      purchase notes in
      [`docs/notes/buying-a-domain.md`](../notes/buying-a-domain.md).
- [ ] **Railway project ID** — for the `docs/known-issues.md` runbook,
      so future-me has a stable identifier to reference without leaking
      the URL.

Without the items in **Phase 7 close-out**, Phase 7's Definition of Done
literally cannot be checked — the DoD requires "the deployed Railway
URL serves `/`, `/api/v1/feedback`, `/api/v1/docs`, `/health`, and
`/ready` correctly," which I can only verify from the URL plus your
smoke output.

---

## Common Failure Modes & Fixes

The ones you're most likely to hit on first deploy.

### "Healthcheck failed" but the app looks fine in logs

The container is up but `/health` isn't responding within Railway's
timeout. Almost always one of:

- Uvicorn bound to `127.0.0.1` instead of `0.0.0.0`. Our `CMD` already
  uses `0.0.0.0`; if you overrode the start command, undo it.
- Healthcheck path typo (`/healthz`, `/healthcheck`). Must be exactly
  `/health`.
- App is using more than the timeout to import. Bump healthcheck
  timeout to `10s` temporarily; if that fixes it, profile imports — do
  **not** leave it at 10s.

### "alembic: command not found" in Pre-Deploy

The image installed the wheel into `--system` Python (correct), but the
shell PATH doesn't include the install directory. Workaround in the
Pre-Deploy field: `python -m alembic upgrade head`. If this happens,
flag it — the spec says `alembic upgrade head` should just work, and a
PATH bug in the image is worth fixing in the `Containerfile` rather
than papering over in Railway.

### Postgres connection refused on first request

Plugin not linked, or `DATABASE_URL` was hand-pasted with a stale value.
Re-do step 2 — use the **Reference Variable** picker, never paste.

### Driver scheme error: "dialect 'postgres' not supported"

Railway injected `postgres://...` and the normalization in `config.py`
isn't running. Likely cause: `APP_ENV` is not set, or the config loader
short-circuits before normalizing. Capture the stack trace and hand it
back; I'll fix it in `src/feedback_triage/config.py`.

### Cold-start timeouts on first reviewer click

App was sleeping; Uvicorn import + Alembic check is taking >5s. Two
fixes:

- Disable App Sleeping during demos (re-enable after).
- Trim cold-start work — the boot path should not touch the DB. If it
  does, that's a bug, not a Railway tuning issue.

### Deploy succeeded but the wrong commit is live

Railway and the GitHub `main` branch can diverge if Railway's GitHub
App lost permission. **Service → Settings → Source → Reconnect** and
confirm the latest commit SHA matches `git rev-parse origin/main`.

---

## When to Tear It Down

If the demo period ends:

1. **Project → Settings → Danger Zone → Delete Project** — kills
   service, plugin, env vars, and stops billing in one click.
2. Railway keeps deleted-project metadata for 30 days; you can restore
   without redoing setup if you change your mind.
3. The GHCR image stays put — that's GitHub's, not Railway's. Delete
   from `Packages` on the repo if you want it gone too.

Do **not** just "pause" the project to stop billing — Postgres still
accrues storage cost while paused. Deletion is the only zero-cost
state.

---

## Related Docs

- [`spec/spec-v1.md`](spec/spec-v1.md) — canonical spec; Container Hardening,
  Health and Readiness, Release Flow live here.
- [`deployment-notes.md`](deployment-notes.md) — *why* of every choice
  in this runbook (cost math, pool sizing, sleep tradeoffs).
- [`implementation.md`](implementation.md#phase-7--container--deployment)
  — Phase 7 deliverables and DoD this runbook is closing out.
- [`../known-issues.md`](../known-issues.md) — track Railway-specific
  bugs here, not in the spec.
