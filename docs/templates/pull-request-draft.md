<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: wip/2026-05-05-scratch -->
<!--
  Suggested PR title (conventional commit format — type: description):

    feat(v2): close Phase 1 (Alpha) — auth, tenancy, email, FEATURE_AUTH gate

  Available prefixes:
    feat:     — new feature or capability
    fix:      — bug fix
    docs:     — documentation only
    chore:    — maintenance, no production code change
    refactor: — code restructuring, no behavior change
    test:     — adding or updating tests
    ci:       — CI/CD workflow changes
    style:    — formatting, no logic change
    perf:     — performance improvement
    build:    — build system or dependency changes
    revert:   — reverts a previous commit
-->

<!-- Suggested labels: v2.0, phase-1, auth, tenancy, email, docs, schema-migration -->

<!--
  ╔══════════════════════════════════════════════════════════════╗
  ║  This PR description is for HUMAN REVIEWERS.                 ║
  ║                                                              ║
  ║  Release automation (release-please) reads individual        ║
  ║  commit messages on main — not this description.             ║
  ║  Write commits with conventional format (feat:, fix:, etc.)  ║
  ║  and include (#PR) or (#issue) references in each commit.    ║
  ║                                                              ║
  ║  This template captures: WHY you made changes, HOW to test   ║
  ║  them, and WHAT reviewers should focus on.                   ║
  ╚══════════════════════════════════════════════════════════════╝
-->

## Description

Lands every Phase 1 (Alpha) slice from
[`docs/project/spec/v2/implementation.md`](../../docs/project/spec/v2/implementation.md)
on a single integration branch and closes the phase. The shortest
path to *"a user can sign up, get a workspace, and see an empty
inbox in their browser"* is now real, gated behind
`FEATURE_AUTH=false` in production until Phase 2 ratifies the
surface.

**What changes you made:**

- **PR 1.3a — `refactor(models)`** — `models.py` split into a
  package; v2 enums (`UserRole`, `WorkspaceRole`, `EmailStatus`,
  `EmailPurpose`) added as `StrEnum`s.
- **PR 1.3b — `feat(db)` Migration A** — single Alembic revision
  adding `users`, `sessions`, `*_tokens`, `workspaces`,
  `workspace_memberships`, `workspace_invitations`,
  `auth_rate_limits`, `email_log`, plus native Postgres enums and
  the additive (nullable) `feedback_item.workspace_id` column.
  Hand-reviewed; round-trips up/down/up.
- **PR 1.4 — `feat(auth)`** — Argon2id hashing, session
  create/renew/revoke, hashed verify/reset/invite token mint and
  consume, `CurrentUser` / `RequireSession` / `RequireRole` deps,
  Argon2 startup warm-up.
- **PR 1.5 — `feat(tenancy)`** — `WorkspaceContext` resolved from
  `<slug>`, role policies, and the canary
  `tests/api/test_isolation.py` (six initial cases — **404 never
  403**).
- **PR 1.6 — `feat(email)`** — `httpx`-based Resend client per
  ADR 061 (fail-soft, in-process retry, `email_log` rows), four
  templates (`verification`, `verification_already`,
  `password_reset`, `invitation`), `RESEND_DRY_RUN=1` test mode.
- **PR 1.7 — `feat(api)`** — `/api/v1/auth/*` JSON endpoints +
  `/login`, `/signup`, `/forgot-password`, `/reset-password`,
  `/verify-email`, `/invitations/<token>` page routes.
  No-enumeration responses on signup and forgot-password verified
  by `tests/api/auth/test_no_enumeration.py`.
- **PR 1.8 — `feat(api)`** — workspaces, memberships, and
  invitations endpoints + `/w/<slug>/dashboard` empty-state page.
- **PR 1.9 — `feat(config)` (Phase 1 close)** — `FEATURE_AUTH`
  env flag short-circuits the auth surface with 503 (JSON for
  `/api/v1/auth/*`, "coming soon" HTML for the page routes);
  sidebar partial rendered inside authenticated shells; theme
  switcher dormant but wired to `data-theme` and persisted to
  `localStorage` (FOUC-free initial paint; dark-mode CSS tokens
  already exist; full activation is Phase 4).
- **Docs** — every PR row in the v2 implementation ledger now has
  an in-page jump anchor. New "Programming security checklist"
  section in `docs/project/spec/v2/security.md` covering secrets,
  injection, deserialization, auth/session, tenancy, headers,
  crypto, supply chain, frontend, data, and a "refuse on review"
  list.

**Why you made them:**

Phase 1 in the v2 plan is the spine the rest of the rewrite hangs
off. Splitting it across nine commits keeps each slice
review-honest; landing them as one PR keeps the integration
boundary explicit. The auth surface stays dormant in production
behind `FEATURE_AUTH=false` until we deliberately flip the flag at
the alpha → beta boundary.

## Related Issue

N/A — tracked by the v2 phase plan in
[`docs/project/spec/v2/implementation.md`](../../docs/project/spec/v2/implementation.md).
Phase 1 closed 2026-05-06 in that file.

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [x] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [x] 🔧 Refactor (no functional changes) — PR 1.3a models split
- [x] 🧪 Test update

## How to Test

**Steps:**

1. Pull the branch, run `uv sync`, then `task up` to start
   Postgres.
2. `uv run alembic upgrade head` — Migration A applies cleanly on
   a fresh DB; `alembic downgrade -1 && alembic upgrade head`
   round-trips.
3. With `FEATURE_AUTH=true` (the dev default), boot the app and
   walk the signup flow: `/signup` → check the `email_log` table
   for the verification row (`RESEND_DRY_RUN=1` is on by default,
   so no network call) → grab the synthetic token → visit
   `/verify-email?token=...` → `/login` → land on
   `/w/<slug>/dashboard`.
4. Set `FEATURE_AUTH=false` in `.env`, restart, and confirm
   `POST /api/v1/auth/signup` returns 503 JSON and `GET /login`
   renders the "coming soon" page (also 503).
5. Click the **Theme** button in the dashboard sidebar; the
   `data-theme` attribute on `<html>` flips and persists across
   reloads via `localStorage`. (Visual dark-mode QA is Phase 4.)

**Test command(s):**

```powershell
# Full unit + API suite
uv run pytest -m "not e2e"

# Phase 1 verification commands from the plan
uv run pytest tests/api/test_isolation.py -v
uv run pytest tests/api/test_feature_auth_flag.py -v
task build:css
uv run alembic upgrade head

# Optional Playwright smoke (requires browsers installed)
uv run pytest -m e2e tests/e2e/test_signup_flow.py
```

Local run on 2026-05-06: **159 passed, 3 skipped, 4 deselected**;
`task check` green.

**Screenshots / Demo (if applicable):**

N/A — empty-state dashboard + auth forms ship without visual
polish; the styled pass arrives in Phase 4.

## Risk / Impact

**Risk level:** Medium

**What could break:**

- **Migration A** is the largest schema change in the v1 → v2
  jump. Additive only (the `NOT NULL` flip on
  `feedback_item.workspace_id` is deferred to Migration B in PR
  2.1 per ADR 062), but reviewers should still walk every table,
  every native enum, every `CHECK length(...)`, every FK
  `ON DELETE`, and every `BEFORE UPDATE` trigger.
- **`FEATURE_AUTH=false` middleware is global.** If the predicate
  is wrong it could 503 a non-auth route. The 18 cases in
  `tests/api/test_feature_auth_flag.py` cover the gated paths,
  the non-auth paths (`/health`, `/api/v1/feedback`), and the
  enabled-mode preservation.
- **Argon2 parameters.** Real hashing is on the critical path; a
  miss tuned parameter set would regress login latency on Railway.
  Numbers are documented in `auth/hashing.py` and the warm-up
  hook fires once per cold boot.
- **Cross-tenant canary** (`test_isolation.py`) is the **#1 v2
  guarantee** — any change that turns a 404 into a 200 fails the
  build by design.

**Rollback plan:**

- Runtime: redeploy with `FEATURE_AUTH=false` (the gate is the
  kill switch; no schema rollback needed).
- Schema: `alembic downgrade -1` rolls Migration A back. No data
  has migrated yet — `feedback_item.workspace_id` is nullable
  through Migration A and only flips in PR 2.1.

## Dependencies (if applicable)

**Depends on:** Phase 0 (already on `main`, ratified 2026-05-04
with ADR 061).

**Blocked by:** Nothing.

Blocks PR 2.1 (`feat(db): migration B`) and the rest of Phase 2.

## Breaking Changes / Migrations (if applicable)

- [x] Config changes required
- [x] Data migration needed
- [x] API changes (document below)
- [x] Dependency changes

**Details:**

- **New env vars:** `FEATURE_AUTH`, `SECURE_COOKIES`,
  `APP_BASE_URL`, `RESEND_API_KEY`, `RESEND_FROM_ADDRESS`,
  `RESEND_DRY_RUN`, `RESEND_TIMEOUT_SECONDS`,
  `RESEND_MAX_RETRIES`. Defaults are dev-safe; production must
  set `SECURE_COOKIES=true`, `RESEND_DRY_RUN=0`, and a real
  `RESEND_API_KEY` (enforced by the `_require_*_in_production`
  model validators in `config.py`).
- **Data migration:** Migration A
  (`alembic/versions/<rev>_v2_a_auth_tenancy_email_log.py`).
  Hand-reviewed; additive only.
- **New API surface:** `/api/v1/auth/*`, `/api/v1/workspaces`,
  `/api/v1/memberships`, `/api/v1/invitations`. No existing
  `/api/v1/feedback` shape changed.
- **Dependency changes:** `argon2-cffi` added; `httpx` already
  present; `uv.lock` regenerated.

Production cutover sequence (when Phase 2 is also ready and we
flip the flag):

1. Deploy with `FEATURE_AUTH=false` first to land Migration A
   without exposing the auth pages.
2. Set `SECURE_COOKIES=true`, `RESEND_DRY_RUN=0`,
   `RESEND_API_KEY=...`, `APP_BASE_URL=...` in Railway.
3. Flip `FEATURE_AUTH=true` and redeploy.

## Checklist

- [x] My code follows the project's style guidelines (ruff + mypy
      strict)
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in hard-to-understand
      areas (middleware ordering, gate predicate, Argon2 warm-up,
      no-enumeration posture)
- [x] I have made corresponding changes to the documentation
      (implementation ledger, security checklist, PR-section
      anchors)
- [x] No new warnings (or explained in Additional Notes)
- [x] I have added tests that prove my fix is effective or that
      my feature works (159 passed total; 18 new gate tests; 6
      cross-tenant isolation canaries)
- [x] Relevant tests pass locally
- [x] No security concerns introduced (or flagged for review) —
      new "Programming security checklist" section in
      `v2/security.md` documents the rules this PR was written
      against
- [x] No performance regressions expected — Argon2 warm-up runs
      only when `FEATURE_AUTH=true`

## Reviewer Focus (Optional)

- **Migration A** (`alembic/versions/<rev>_v2_a_*.py`) — every
  table, every native enum, every CHECK, every FK `ON DELETE`,
  every `updated_at` trigger.
- **Cross-tenant canary** (`tests/api/test_isolation.py`) — the
  six cases must all assert 404 (never 403, never 200) and never
  echo a foreign workspace's row id.
- **Gate predicate**
  ([`src/feedback_triage/auth/feature_flag.py`](../../src/feedback_triage/auth/feature_flag.py))
  — confirm the path set is exhaustive and that the middleware
  only mounts when `FEATURE_AUTH=false`.
- **No-enumeration posture**
  (`tests/api/auth/test_no_enumeration.py`) — signup-with-existing
  and forgot-password give identical responses for known and
  unknown addresses.
- **Cookie attributes** — every `Set-Cookie` for the session
  comes from `auth/cookies.py`. Grep for stray `set_cookie` call
  sites before approving.

## Additional Notes

- The PR ledger in
  [`docs/project/spec/v2/implementation.md`](../../docs/project/spec/v2/implementation.md)
  now has clickable jump points; each row links to the matching
  PR section via an in-page anchor.
- The Phase 1 verification block at the bottom of that file
  records the run from 2026-05-06 (159 passed, isolation 6
  passed, css built, alembic at head, `task check` green).
- Phase 2 (Beta) — Migration B + feedback CRUD on the v2 schema
  + inbox/list/detail pages — is unblocked.
