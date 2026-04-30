# Railway — Learning Notes

A self-paced reference for getting comfortable with Railway as a
PaaS (Platform-as-a-Service). Pairs with
[how-deployment-works.md](how-deployment-works.md), which covers the
mental model. This file is more practical: what knobs exist, how to
read the dashboard, what to do when things break, and — critically —
**what never to put on screen, in screenshots, or in commits**.

> Companion file. The spec and runbooks are still authoritative:
> - [docs/project/spec/spec.md](../project/spec/spec.md)
> - [docs/project/railway-setup.md](../project/railway-setup.md)
> - [docs/project/deployment-notes.md](../project/deployment-notes.md)

---

## 1. Dashboard Map — What Each Tab Does

When you open a service in Railway, the tabs across the top are:

| Tab | What lives here | When you'll touch it |
| --- | --- | --- |
| **Deployments** | Every build + deploy attempt. Click one for Build / Deploy / HTTP / Network Flow logs. | Every failed deploy. |
| **Variables** | Environment variables. Hand-set values *and* reference variables (e.g. `${{ Postgres.DATABASE_URL }}`). | First setup; whenever a config changes. |
| **Metrics** | CPU / RAM / network / replica count over time. | When the app gets slow or you suspect a leak. |
| **Settings** | Source repo, networking (domain + port), scale (replicas, region), build config, deploy config, danger zone. | First setup; rarely after. |

The **project**-level (one level up from a service) has its own tabs:

| Project tab | Why you care |
| --- | --- |
| **Usage** | Hard cost limit + alert thresholds. Set this *before* the first deploy. |
| **Tokens** | Project-scoped API tokens. Don't generate one until you actually need CI access. |
| **Members** | Who can see / break things. Solo project = just you. |

---

## 2. The Five Logs You Will Read Often

Inside one deployment:

| Log | What it shows | Useful for |
| --- | --- | --- |
| **Build Logs** | `docker build` output: each `RUN`, layer caching, image push. | "Why didn't my new dep install?" / "Why is the build slow?" |
| **Deploy Logs** | Pre-deploy command + container `stdout`/`stderr` after start. | "Did migrations run?" / "Did the app crash on import?" |
| **HTTP Logs** | Each request: method, path, status, duration. | "Why is the user seeing 502?" / "Which endpoint is slow?" |
| **Network Flow Logs** | Raw TCP connections in/out of the container. | "Is the edge actually reaching my port?" (the 8000 vs 8080 bug) |
| **Details** | Active config (builder, healthcheck, restart policy, replicas). | Sanity-check that `railway.toml` got applied. |

**Rule of thumb for triage:**
1. App URL returns 502 → check **Network Flow Logs** first (port mismatch?), then **Deploy Logs** (did Uvicorn even start?).
2. App URL returns 500 → **HTTP Logs** for the path, then **Deploy Logs** for the traceback.
3. Build never finishes → **Build Logs**.
4. Deploy says "successful" but URL returns nothing → **Settings → Networking** target port.

---

## 3. The Variables Tab Is Where Most Bugs Live

Three flavors, listed in the order Railway resolves them at deploy time:

1. **Reference variables** — `${{ Postgres.DATABASE_URL }}`. Resolved at
   deploy. If the referenced service doesn't exist, the deploy fails
   loudly. **Use these for anything that another Railway service owns.**
2. **Service variables** — flat strings you typed in. Visible to the
   container as env vars. Use for `APP_ENV`, `LOG_LEVEL`, etc.
3. **Railway-injected** — `PORT`, `RAILWAY_*`. Always present. You
   don't set these.

Common screw-ups:

- Pasting a literal `DATABASE_URL` instead of using a reference. When
  Postgres rotates the password, your service breaks silently.
- Setting `PORT` by hand. Don't. Read whatever Railway injects, or set
  the public-domain target port to match Railway's default (8080).
- Putting secrets into "service variables" expecting them to be hidden
  from the deploy log. They're masked in the UI, but if the app
  `print()`s the value, the deploy log captures it. See §6.
- Drift between dashboard fields and `railway.toml`. Whatever's in the
  dashboard wins. Leave the dashboard fields *blank* for anything
  `railway.toml` controls.

---

## 4. The Pricing Mental Model

Railway bills you for **resources actually used**, per second, against a
monthly cap. Three things drive cost:

| Cost driver | How to control it |
| --- | --- |
| **CPU + RAM seconds** while your container runs | App Sleeping (suspends idle services). Single biggest lever. |
| **Egress bandwidth** (data leaving Railway) | Don't serve large media; gzip JSON; cache static assets at edge later if needed. |
| **Postgres storage + connections** | The plugin's "Hobby" tier is generous; you'll only outgrow it with screenshots-as-blobs or unbounded retention. |

For this project, expected steady-state cost with App Sleeping on and a
hard cap of `$10/mo` is well under `$5/mo`. The hard cap is your
seat-belt: misconfigured loop in the build → project freezes at $10,
not $700.

**Set the hard cap before the first real deploy.** It cannot be undone
retroactively if a runaway loop already burned the credit.

---

## 5. Deployment Lifecycle Reference

Every push to `main` triggers this sequence. If any step fails, traffic
stays on the previous version.

```
1. Source snapshot
   ├─ Railway clones the repo at the pushed commit.
   ├─ Applies .dockerignore (and .containerignore) to the snapshot.
   └─ Hands the trimmed archive to BuildKit.

2. Build
   ├─ Reads railway.toml → builder=DOCKERFILE, dockerfilePath=Containerfile.
   ├─ Runs `docker build` — multi-stage Containerfile.
   ├─ On success: tags image with a content-hash digest, pushes to
   │  Railway's internal registry.
   └─ On failure: deploy aborts here. Old version unaffected.

3. Pre-deploy
   ├─ Railway starts a *one-shot* container from the new image.
   ├─ Runs `alembic upgrade head` (from railway.toml).
   ├─ On success: container exits 0; lifecycle continues.
   └─ On failure: deploy aborts. Old version still running.

4. Start
   ├─ Railway starts the *real* container from the new image.
   ├─ CMD runs: uvicorn on $PORT (Railway-injected, default 8080).
   └─ stdout/stderr now flowing into Deploy Logs.

5. Healthcheck
   ├─ Railway hits GET /health on the new container.
   ├─ Must return 200 within 5s (railway.toml).
   ├─ Up to ~3 retries.
   ├─ On success: traffic swap (step 6).
   └─ On failure: deploy aborts. Old version still running.

6. Traffic swap
   ├─ Railway edge starts forwarding new requests to the new container.
   ├─ Old container drains in-flight requests, then is killed.
   └─ Public URL now serves the new version.
```

The key insight: **failure at any step keeps the old version live.** You
don't get a "broken deploy" serving 502s as long as the previous
deploy was healthy. The only way to hit 502 from a "successful" deploy
is a config mismatch *between* Railway and the container — for example,
the public-domain target port not matching Uvicorn's listen port.

---

## 6. SECURITY — What Never Leaves Your Machine

Read this section. It's the part that turns a portfolio side project
into a public credential leak.

### Treat as secret (never commit, never paste, never screenshot)

| Thing | Why | Where it leaks from |
| --- | --- | --- |
| **`DATABASE_URL`** (full string with password) | Anyone with this gets root on your DB. | `.env` files, Variables-tab screenshots, `print(settings)` in logs. |
| **Postgres user passwords** (`PGPASSWORD`) | Same as above. | Same as above. |
| **Railway API tokens** | Anyone can deploy / delete / read logs as you. | `~/.railway/config.json`, CI secrets exported by accident. |
| **Project / Service IDs** in some contexts | Combined with a token, lets an attacker target your project specifically. | Dashboard URLs in screenshots. Project ID alone is *low* risk. |
| **GitHub PATs scoped to GHCR** | Lets attackers push malicious images to your registry. | `.env`, CI logs, `git config --list`. |
| **Session cookies / browser auth** | Full account takeover if Railway-side. | Screenshots of the Railway tab while you're logged in. |
| **Internal hostnames inside `*.railway.internal`** | Information disclosure; combined with a leaked password, simplifies attack. | Code that logs the hostname; screenshots. |
| **Stack traces from production** containing query strings or row data | May contain user content / PII. | Deploy log screenshots, error tracker dumps. |

### Safe to share publicly

| Thing | Why it's fine |
| --- | --- |
| The public URL (`*.up.railway.app`) | Designed to be public. |
| Your repo URL on GitHub | Already public. |
| The **non-secret** env-var *names* (`APP_ENV`, `LOG_LEVEL`, `PAGE_SIZE_DEFAULT`) | Names ≠ values; values for these are also non-secret. |
| Container image digests (`sha256:…`) | Public on GHCR by design. |
| The fact that you use Railway, Postgres, FastAPI, etc. | Stack disclosure is fine for a portfolio project. |

### Specifically dangerous patterns

These are how leaks usually happen — watch for them in your own work:

1. **Pasting `.env` into a chat or issue.** Never. If you must share a
   config example, copy from `.env.example` and replace any real values
   with placeholders (`changeme`, `<redacted>`).
2. **`logger.info(settings)` or `print(settings)` in source.**
   `Settings.database_url` is `SecretStr` precisely so `repr()` masks
   it — but if you call `.get_secret_value()` and log *that*, you've
   leaked the password into the deploy log. The unit test
   `test_database_url_password_is_masked_in_repr` exists to catch this.
3. **Screenshots of the Variables tab.** Even with values "masked,"
   the order, count, and key names disclose your stack. If you must
   screenshot, crop tightly to the one variable you're discussing and
   blur the value.
4. **Screenshots of the Network Flow Logs that include private IPs
   like `fd12:…` and `10.250.…`.** These are Railway-internal IPv6 /
   IPv4 — not directly attackable from the internet, but they're
   inventory information. Crop or redact for public posts.
5. **Sharing Railway dashboard URLs.** They contain the project ID;
   combined with a stolen token, they tell an attacker exactly where
   to point. Treat dashboard URLs like internal links.
6. **Committing a Railway API token to CI.** If you ever wire CI
   pushes to Railway, store the token as a GitHub Actions *secret*
   (encrypted), reference it via `${{ secrets.RAILWAY_TOKEN }}`,
   never `echo $RAILWAY_TOKEN`.
7. **Public GHCR images that contain `.env` files.** The
   [.containerignore](../../.containerignore) already excludes
   `.env*` — don't override it.
8. **Public Postgres backups.** Railway can dump your DB to a file.
   That file is the database. Treat it like the password file.
9. **Tweeting your `Request ID` from a 502 page.** The request ID
   alone is useless to an attacker, but it's a habit-former: get used
   to *not* posting raw error pages without thinking about it.
10. **Logs from `ALTER USER … PASSWORD`** or any `psql` session.
    Postgres echoes the password into its log file by default. Never
    redirect Postgres logs into a public bucket.

### Rotation recipes — when (not if) something leaks

| If you leaked… | Do this |
| --- | --- |
| `DATABASE_URL` / Postgres password | Railway dashboard → Postgres service → Settings → "Reset Password." Linked services pick up the new value on next deploy. |
| A Railway API token | Project → Tokens → Revoke. Generate a new one only if needed. |
| A GitHub PAT | github.com → Settings → Developer settings → Personal access tokens → Revoke. |
| A GHCR image with embedded secrets | Delete the package version on GHCR; rotate the embedded secret; force a new build with a clean image. |
| A `.env` committed to git | Rotate every value in it; then `git filter-repo` to scrub history; force-push; tell collaborators to re-clone. The rotation matters more than the scrub — assume the value is already harvested. |

---

## 7. Self-Quiz — When You Think You Understand

If you can answer these without looking, you've internalized the model:

1. Where does `${{ Postgres.DATABASE_URL }}` come from, and what
   happens to your service if Postgres rotates the password?
2. Why do we set the public-domain port to `8080` instead of `8000` in
   this project?
3. What's the difference between `/health` and `/ready`, and why does
   Railway's healthcheck point at `/health`?
4. If `alembic upgrade head` fails in pre-deploy, what is the user
   visiting `*.up.railway.app` seeing right now?
5. What would happen if you put `print(settings)` in `main.py` and
   pushed it to `main`?
6. What field, if any, should you type into **Settings → Deploy →
   Pre-Deploy Command** in the Railway dashboard?
7. If your monthly Railway bill suddenly shows `$47`, what's the most
   likely cause and what setting was supposed to prevent it?

Answers, briefly:

1. The Postgres plugin owns it. Resolved at deploy time. Rotated
   password is picked up automatically on next deploy/restart.
2. Railway injects `PORT=8080` into the container; `CMD` honors it via
   `${PORT:-8000}`; therefore Uvicorn listens on 8080 in production.
   The dashboard's target port has to match what the container
   actually listens on.
3. `/health` = liveness, no DB. `/ready` = readiness, touches DB.
   Liveness probe failures restart the container; using `/ready`
   would mean a DB blip restarts the app, masking the real fault.
4. The previous (healthy) deploy. Railway never swaps traffic until
   pre-deploy + healthcheck both pass.
5. `Settings.__repr__` masks the `database_url` field because it's
   `SecretStr`. So `print(settings)` shows `database_url=SecretStr('**********')`
   — safe. But `print(settings.database_url.get_secret_value())` would
   leak the password into the deploy log.
6. Nothing. Leave it blank. `railway.toml` owns it.
7. App Sleeping wasn't enabled, *or* the hard usage cap wasn't set.
   Both should be turned on before the first real deploy.

---

## 8. Further Reading

- Railway docs: <https://docs.railway.com/>
  (Skim "Quick Start," "Deploy from a Dockerfile," "Public Networking,"
  "Variables and Reference Variables," "App Sleeping.")
- The Twelve-Factor App: <https://12factor.net/>
  (The ideology Railway is built around. Read once. The "config in
  environment" and "logs as event streams" chapters are the most
  load-bearing.)
- OWASP Cheat Sheet — Secrets Management:
  <https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html>
  (For the bigger picture beyond just Railway.)
