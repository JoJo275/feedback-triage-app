# Post-Launch Checklist

What to verify, monitor, and harden in the first hour / day / week
after pushing a web app to the public internet for the first time.
Pairs with [how-deployment-works.md](how-deployment-works.md) and
[railway-learning.md](railway-learning.md).

> Status (2026-04-30): the live URL
> <https://feedback-triage-app-production.up.railway.app> is up and
> serving 200s on `/health`, `/ready`, `/api/v1/feedback`,
> `/api/v1/docs`, and `/`. This file documents what comes *after* that
> first green deploy.

---

## Hour 0 — Smoke

The minimum bar before walking away:

```powershell
$APP="https://feedback-triage-app-production.up.railway.app"
foreach ($p in '/health','/ready','/api/v1/feedback','/api/v1/docs','/') {
    curl.exe -s -o $null -w "$p  %{http_code}  %{time_total}s`n" "$APP$p"
}
```

All five must be `200`. If any is `5xx`, the deploy is not really done
— go back to [railway-learning.md §2](railway-learning.md#2-the-five-logs-you-will-read-often).

Confirmed locally:

| Path | Status | Response |
| --- | --- | --- |
| `/health` | 200 | `{"status":"ok"}` |
| `/ready` | 200 | `{"status":"ok"}` (touches DB) |
| `/api/v1/feedback` | 200 | `{"items":[],"total":0,"skip":0,"limit":20}` |
| `/api/v1/docs` | 200 | Swagger UI HTML |
| `/` | 200 | App shell HTML |

---

## Hour 1 — Cost & Limits

Before anything organic happens, lock down the worst-case bill:

- [ ] **Hard usage cap** set in Railway → Project → Usage → `$10`. Cannot be
      exceeded; project pauses instead of charging.
- [ ] **Alert threshold** at `$6`. You'll get an email before the cap fires.
- [ ] **App Sleeping** ON (Settings → Serverless). Idle services suspend.
      Cold-start is 1–3s on the first request after sleep — fine for a
      portfolio app.
- [ ] **Replica count** = 1 (Settings → Scale). Multi-region is Pro-plan
      only and not needed for this project.
- [ ] **Postgres backups** — Railway snapshots the volume daily for
      Hobby plan. Verify under Postgres → Backups that at least one
      snapshot exists.

---

## Hour 1 — Security Sweep

- [ ] Secrets visible only in the Variables tab, never in source. Run
      `git grep -i "password\|secret\|token"` on the repo and confirm
      every hit is a placeholder, a test fixture, or a `.env.example`
      key with no value.
- [ ] `.env` is gitignored (`git check-ignore .env` should print `.env`).
- [ ] No `print(settings)` or `logger.info(settings.database_url)` paths
      in `src/` (`git grep "settings.database_url"` should return only
      `database.py` and `alembic/env.py`).
- [ ] HTTPS works: `curl -sI https://<url>` returns `HTTP/2 200`, not a
      certificate warning.
- [ ] `/api/v1/docs` is intentionally public for v1.0 (it's a portfolio
      project). If/when the project gets real users, consider gating it
      behind auth.

---

## Day 1 — Observability

You can't fix what you can't see. Bookmark these tabs:

| Where | What to watch |
| --- | --- |
| Railway → Service → **Metrics** | Memory (steady-state ~80MB; sustained climb = leak), CPU spikes per request, replica restarts. |
| Railway → Service → **HTTP Logs** | Filter `@httpStatus:5*` for app errors; filter `@httpStatus:404` for missing routes; total duration column for slow paths. |
| Railway → Service → **Deploy Logs** | Anything tagged `ERROR`. Healthy steady-state is just the per-request access-log line. |
| Railway → Postgres → **Metrics** | Active connections (should hover ≤ pool_size + max_overflow = 10), slow queries. |
| GitHub → Actions | Every push to `main` should show CI green and a Railway deploy webhook fire. |

**Action items if any of these go red:**

- 5xx burst → check the matching Deploy Log timestamp for a traceback.
- Memory creeping up over hours of idle traffic → suspect a session
  leak (the canary test should be catching this; if it's not, a real
  bug exists).
- Replica restart loop → almost always a healthcheck regression. Roll
  back via Railway → Deployments → previous deploy → "Redeploy."

---

## Day 1 — Functional Verification

Beyond `200 OK`, exercise the actual flows:

```powershell
$APP="https://feedback-triage-app-production.up.railway.app"

# Create
$body = '{"title":"smoke-test","source":"other","pain_level":3}'
$created = curl.exe -s -X POST "$APP/api/v1/feedback" `
    -H "Content-Type: application/json" -d $body | ConvertFrom-Json
$id = $created.id

# Read
curl.exe -s "$APP/api/v1/feedback/$id" | ConvertFrom-Json

# Update
$patch = '{"status":"reviewing"}'
curl.exe -s -X PATCH "$APP/api/v1/feedback/$id" `
    -H "Content-Type: application/json" -d $patch | ConvertFrom-Json

# List
curl.exe -s "$APP/api/v1/feedback?limit=5" | ConvertFrom-Json

# Delete
curl.exe -s -X DELETE "$APP/api/v1/feedback/$id" -o $null -w "%{http_code}`n"
```

A clean run hits the Postgres trigger that auto-bumps `updated_at` on
PATCH — if the returned `updated_at` matches `created_at`, the trigger
isn't firing in production.

---

## Week 1 — Hardening

Things that don't matter on day 0 but matter by day 7:

- [ ] **Custom domain** (optional). If you own one, point a CNAME at
      Railway and let Railway provision the cert. Updates `README.md`.
      **Planned:** `signalnest.app` (Cloudflare Registrar). See
      [`domain-and-cloudflare.md`](domain-and-cloudflare.md) for the
      Cloudflare-side configuration.
- [ ] **Status page or uptime monitor.**
      [UptimeRobot](https://uptimerobot.com/) free tier checks `/health`
      every 5 min and emails on failure. Catches "Railway region went
      down" before you do.
- [ ] **Dependabot alerts** — confirm GitHub → Insights → Dependency
      graph → Dependabot is on, and that the first round of automated
      bump PRs is landing.
- [ ] **GHCR image visibility** — public for portfolio, private for
      anything sensitive. README badge changes accordingly.
- [ ] **Real seed data** — the `task seed` output should hit every
      `Source` and `Status` value, not the `[]` empty list a fresh DB
      shows.
- [ ] **Three screenshots** in `docs/screenshots/` referenced from the
      README — list page, detail page mid-edit, `/api/v1/docs`.
- [ ] **Loom or asciinema demo** linked from the README ([Should]).
      90 seconds, voice-over optional, shows the full create→list→edit
      flow.
- [ ] **Repo description and topics** on GitHub:
      `fastapi`, `postgres`, `sqlmodel`, `playwright`, `railway`.
      Improves discovery; takes 30 seconds.

---

## Week 1 — Lessons-Learned File

Keep a one-page log of every "huh, that broke" moment. They're worth
more than any tutorial:

- 2026-04-30: Railway target port defaulted to 8080, not 8000 (Railway
  injects `PORT=8080`). Symptom: 502 Bad Gateway. Fix: set
  Networking → Public domain → port to 8080. Documented in
  [railway-learning.md §7](railway-learning.md#7-self-quiz--when-you-think-you-understand).
- 2026-04-30: Initial deploy hit `localhost:5432` because `DATABASE_URL`
  reference variable wasn't linked. Symptom: `Connection refused` in
  Deploy Logs. Fix: Variables → Reference Variable → Postgres →
  `DATABASE_URL`. Defended against in code by the
  `_require_remote_db_in_production` validator in `config.py`.

(Add new entries as they happen.)

---

## What "Done" Looks Like

The app is "really" launched, not just deployed, when:

1. **All five smoke endpoints return 200** from a public network
   (not just from your laptop).
2. **A cold cache hit** (after App Sleeping) lands in under 3 seconds.
3. **A round-trip CRUD cycle** through `/api/v1/feedback` succeeds for
   every `Source` and `Status` value.
4. **The README** has a working live-demo link, three screenshots, and
   one architecture diagram.
5. **A reviewer who has never seen the project** can read the README,
   click the demo URL, and understand both *what it does* and *how it
   is built* in under five minutes (this is also Phase 8's DoD in
   `implementation.md`).

Anything past that is iteration, not launch.
