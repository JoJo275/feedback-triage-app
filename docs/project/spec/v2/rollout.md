# v2.0 — Rollout, Deployment, Observability

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).

---

## Phased rollout

Each phase is a single release tag (`v2.0.0-alpha.1`,
`v2.0.0-beta.1`, `v2.0.0`).

### v2.0-alpha — Identity & shell

- **F1** (auth backend) shipped behind `FEATURE_AUTH=false` env flag.
  Schema migrations run; new endpoints exist; UI is unchanged.
- **F1b** (workspaces, memberships, invitations) — schema + API +
  scaffolded routes. v1.0 data is migrated into the
  `signalnest-legacy` workspace.
- **FT** (Tailwind adoption) — `task build:css` runs in CI; existing
  pages re-skinned with utility classes. No layout changes yet.
- **FU** (public landing page) — static, no demo yet.
- **F4** (`/styleguide`) — ships in parallel with the Tailwind
  adoption; doubles as a regression check.

Acceptance: `task check`, `task test:e2e` green; new auth tables
present in production but `/login` returns 503 until the flag flips.

### v2.0-beta — Triage workflow

- `FEATURE_AUTH=true` in production. `/login` and `/signup` open.
- **FX** (Inbox rebrand + extended status workflow) replaces v1.0's
  list page.
- **F3a + F3b** (tags CRUD in Settings, notes on detail page).
- **FS** (Submitters page + auto-link by email).
- **FP** (public submission form per workspace).
- **FW** (Settings page: workspace info, members tab for owners,
  tags CRUD, public form URL).

Acceptance: tenant-isolation canary green; Playwright smoke covers
signup → workspace create → submit feedback (anonymous) → triage
(authed) → tag → note.

### v2.0-final — Outcomes & polish

- **FY** (Dashboard summary cards + intake sparkline).
- **FR** (Roadmap page + `published_to_roadmap` flag).
- **FC** (Changelog page + `published_to_changelog` flag).
- **FI** (Insights page).
- **FE** (status-change emails — only fires for `submitter.email IS
  NOT NULL` and only on transitions to `accepted`, `planned`,
  `shipped`).
- **FD** (dark-mode toggle).
- **FU1** (mini demo on landing page).

Acceptance: all features above pass smoke; `signalnest.app` can be
shared without further explanation.

---

## v1.0 → v2.0 cut-over

A maintenance pause at the v1.0 → v2.0-alpha boundary is acceptable
(zero-downtime is **not** a v2.0 goal). The cut-over migration runs
once; rollback path is a fresh restore from the pre-cutover dump.
Full user-facing companion: [`migration-from-v1.md`](migration-from-v1.md).

Per ADR 062, the cut-over is **two Alembic revisions**, not one,
so a deploy that fails between A and B can roll forward instead
of down (mitigates [`risks.md`](risks.md) E15).

### Migration A — schema-only

1. `CREATE EXTENSION IF NOT EXISTS citext`.
2. Create `users`, `workspaces`, `workspace_memberships`,
   `workspace_invitations`, `sessions`, `email_verification_tokens`,
   `password_reset_tokens`, `submitters`, `tags`, `feedback_tags`,
   `feedback_notes`, `auth_rate_limits`, `email_log`.
3. Insert the synthetic admin `users` row (id, email from
   `ADMIN_BOOTSTRAP_EMAIL`, password hash from
   `ADMIN_BOOTSTRAP_PASSWORD`).
4. Insert the `signalnest-legacy` workspace owned by the admin
   user (the admin user is also the synthetic owner; the spec
   keeps these as the same user, per ADR 062).
5. `ALTER TABLE feedback_item ADD COLUMN workspace_id uuid NULL`
   (nullable, no FK violations possible because no rows yet have
   a value).
6. `ALTER TYPE status_enum ADD VALUE 'needs_info'` ... (six new
   values; `ALTER TYPE ADD VALUE` cannot run inside a transaction
   that also writes data, so this lives in Migration A).
7. Add `feedback_item` columns from [`schema.md`](schema.md)
   (`title`, `submitter_id`, `type`, `priority`, `source_other`,
   `type_other`, `published_to_*`, `release_note`) and CHECK
   constraints.
8. Add indexes.

Deploy A. Application boots; `feedback_item.workspace_id` is
nullable; new rows still write through (defaulting to NULL is
fine because Migration B has not flipped NOT NULL yet, and
v2.0-alpha keeps `FEATURE_AUTH=false` so no production write
traffic creates new feedback through the v2 paths).

### Migration B — backfill + flip

9. `UPDATE feedback_item SET workspace_id = (legacy ws id)
    WHERE workspace_id IS NULL`.
10. Pre-flip assertion (in Python): `SELECT count(*) FROM
    feedback_item WHERE workspace_id IS NULL` must equal 0; the
    migration aborts otherwise.
11. `ALTER COLUMN workspace_id SET NOT NULL`.
12. `UPDATE feedback_item SET status='closed' WHERE status='rejected'`.

Deploy B. The `release-please` PR or a manual tag bumps to
`v2.0.0-alpha.1`. ADRs 062 + 063 cover the data-migration
choreography and the `rejected → closed` decision.

### Backwards compatibility

`/api/v1/*` paths from v1.0 keep their shape. The v1.0
`POST /api/v1/feedback` endpoint becomes workspace-scoped: the
`signalnest-legacy` workspace remains the implicit target until the
header `X-Workspace-Slug` is provided. After v2.0-final this implicit
fallback is **removed** and the endpoint requires the header.

---

## Deployment topology

```text
Railway Project (production)
├── Service 1: SignalNest (FastAPI)
│   ├── Serves /api/v1/* and HTML pages
│   ├── Ships static app.css (Tailwind-built) and static JS
│   ├── Sends email through Resend
│   └── Pre-deploy: alembic upgrade head
├── Service 2: PostgreSQL 16
└── Cron: scripts/sweep_expired_tokens.py + scripts/reset_demo_workspace.py (nightly)
```

Explicitly **not** introduced for v2.0:

- Separate frontend service.
- Redis or any cache.
- Celery / RQ / background workers.
- WebSockets, SSE.
- AI / LLM features.
- Object storage (no file attachments).

Each is its own ADR if it ever ships.

### Required env vars (production)

| Var                       | Purpose                                                              |
| ------------------------- | -------------------------------------------------------------------- |
| `DATABASE_URL`            | Postgres DSN (Railway-injected)                                      |
| `SECRET_KEY`              | Signing key for any future signed value (32+ random bytes)           |
| `RESEND_API_KEY`          | Resend transactional email                                           |
| `BASE_URL`                | `https://signalnest.app`                                             |
| `SECURE_COOKIES`          | `true` in production                                                 |
| `FEATURE_AUTH`            | `false` until v2.0-alpha → v2.0-beta cutover                         |
| `ADMIN_BOOTSTRAP_EMAIL`   | Used once at first deploy to seed the admin user                     |
| `ADMIN_BOOTSTRAP_PASSWORD`| Used once at first deploy to seed the admin user                     |

`.env.example` enumerates every var.

---

## Background work (Railway cron)

v2.0 introduces no long-lived workers. Two scripts run on a
nightly cron:

- `scripts/reset_demo_workspace.py` — wipes and reseeds the demo
  workspace.
- `scripts/sweep_expired_tokens.py` — hard-deletes
  `email_verification_tokens`, `password_reset_tokens`,
  `workspace_invitations`, and `sessions` past their `expires_at`
  by more than 24 h.

If Railway cron is unavailable, the same scripts run locally via
`task cron:nightly` for development.

---

## Observability

Inherited from v1.0. v2.0 adds:

- `request_id` middleware logs the request id on every email send,
  every auth state transition, every cross-tenant access attempt.
- Failed login + failed cross-tenant access counts are emitted as
  structured log events at WARNING level for future alerting.

No metrics backend is introduced; logs to stdout only (Railway
captures them). Adding Sentry/Better-Stack/etc. is a v3.0 concern
and its own ADR.

---

## Cross-references

- [`schema.md`](schema.md) — full DDL for the cut-over.
- [`api.md`](api.md) — endpoint behaviour during the cut-over window.
- [`auth.md`](auth.md) — `FEATURE_AUTH` flag.
- [`tooling.md`](tooling.md) — what runs in CI before each tag.
- [`security.md`](security.md) — secret env vars.
