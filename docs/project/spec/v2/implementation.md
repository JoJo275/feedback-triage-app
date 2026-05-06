# v2.0 — Implementation plan

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Companion to the v1.0 plan in
> [`../../implementation.md`](../../implementation.md). When the v1.0
> plan and this file disagree about the **v2.0 codebase**, this file
> wins.

This is the operational *how* and *in what order* for v2.0. Spec
files in this directory say what each surface looks like; this file
says when each surface gets built and what "done" means for the
phase.

---

## How to use this doc

- Phases are sequential. Do **not** start phase N+1 until phase N
  is green.
- Each phase has **deliverables**, a **definition of done (DoD)**,
  and **verification steps** (commands you run, output you expect).
- Tier tags from the spec apply: `[Must]` blocks the phase from
  closing; `[Should]` can slip; `[Nice]` is opportunistic.
- A phase is *not* done because the code compiles. It is done when
  every verification step passes on a clean clone.

---

## Phase map

| Phase | Codename | Theme                                      | Gates                                |
| ----- | -------- | ------------------------------------------ | ------------------------------------ |
| 0     | Pre-v2   | Ratify v1.0; merge v2 spec                 | v1.0 Must items green                |
| 1     | Alpha    | Auth + tenancy + Tailwind shell            | A user can sign up, create a workspace, log in. |
| 2     | Beta     | Triage workflow + public submit            | A workspace can ingest and triage feedback end-to-end. |
| 3     | Final    | Roadmap, changelog, insights, emails       | Closed-loop email sent; v2.0 ratified. |
| 4     | Polish   | Dark mode, mini demo, styleguide presets   | Public launch ready.                 |

Brand & visual rules apply across every phase
([`core-idea.md`](core-idea.md), [`css.md`](css.md)).

---

## PR ledger

Each phase ships as a sequence of PR-sized slices. Every slice
has a conventional-commit title, a single focused diff, and runs
`task check` green on its own. **Do not stack two slices into one
PR.**

Click a PR number to jump to its slice below.

| PR  | Title                                                                                                         | Phase | Status |
| --- | ------------------------------------------------------------------------------------------------------------- | ----- | ------ |
| [1.1](#pr-1-1) | `feat(css): tailwind plumbing + four-file architecture + /styleguide stub`                         | 1     | done        |
| [1.2](#pr-1-2) | `docs(adr): draft ADR 062 + ADR 063 + ADR 064`                                                     | 1     | done        |
| [1.3a](#pr-1-3a) | `refactor(models): split models.py into a package + add v2 enums`                                | 1     | done        |
| [1.3b](#pr-1-3b) | `feat(db): migration A — auth, tenancy, email_log tables + native enums`                         | 1     | done        |
| [1.4](#pr-1-4) | `feat(auth): hashing, sessions, tokens, deps + Argon2 startup warm-up`                             | 1     | done        |
| [1.5](#pr-1-5) | `feat(tenancy): WorkspaceContext + policies + cross-tenant 404 canary`                             | 1     | done        |
| [1.6](#pr-1-6) | `feat(email): Resend client (fail-soft) + 4 templates + DRY_RUN test mode`                         | 1     | done        |
| [1.7](#pr-1-7) | `feat(api): /api/v1/auth/* endpoints + page routes for sign-in flow`                               | 1     | done        |
| [1.8](#pr-1-8) | `feat(api): workspaces, memberships, invitations + dashboard empty state`                          | 1     | done        |
| [1.9](#pr-1-9) | `feat(config): FEATURE_AUTH flag + sidebar + theme switcher (dormant) + Phase 1 close`             | 1     | done        |
| [2.1](#pr-2-1) | `feat(db): migration B — backfill, NOT NULL flip, status rename, plus tags/notes/submitters/workflow tables` | 2 | done |
| [2.2](#pr-2-2) | `feat(api): feedback CRUD on the v2 schema + tags/notes/submitters endpoints`                      | 2     | done        |
| [2.3](#pr-2-3) | `feat(pages): inbox + feedback list + feedback detail`                                             | 2     | done        |
| [2.4](#pr-2-4) | `feat(public): public submission form at /w/<slug>/submit + honeypot + rate limit`                 | 2     | not started |
| [2.5](#pr-2-5) | `feat(pages): settings v1 — workspace info, members, tags, public-submit toggle`                   | 2     | not started |
| [2.6](#pr-2-6) | `feat(triage): submitters pages + stale highlighting + axe-core in e2e (Should items + Phase 2 close)` | 2 | not started |
| [3.1](#pr-3-1) | `feat(email): status-change emails end-to-end + status_change.html template`                       | 3     | not started |
| [3.2](#pr-3-2) | `feat(pages): public roadmap + public changelog`                                                   | 3     | not started |
| [3.3](#pr-3-3) | `feat(pages): management roadmap kanban + management changelog editor`                             | 3     | not started |
| [3.4](#pr-3-4) | `feat(pages): dashboard fully populated + privacy + terms + insights v1 + mini demo`               | 3     | not started |
| [3.5](#pr-3-5) | `chore(release): ratify v2.0 — flip docs/index, README, copilot-instructions to v2 + cut v2.0.0 tag` | 3   | not started |
| [4.1](#pr-4-1) | `feat(ui): dark mode (FD) — data-theme="dark" activated + persisted per user`                      | 4     | not started |
| [4.2](#pr-4-2) | `feat(ui): styleguide preset themes (4) wired up on /styleguide`                                   | 4     | not started |
| [4.3](#pr-4-3) | `feat(email): Resend webhook for delivery + bounce events (if available)`                          | 4     | not started |
| [4.4](#pr-4-4) | `feat(brand): custom favicon + wordmark refresh`                                                   | 4     | not started |
| [4.5](#pr-4-5) | `feat(ui): production visual identity — palette, motion, effects (designer-driven)`                | 4     | not started |

**Twenty-six PRs total** — ten for Phase 1, six for Phase 2,
five for Phase 3, five for Phase 4. Phase 1's PR 1.2 is doc-only;
PR 1.3a is a non-migration scaffold split; PR 1.3b and PR 2.1 are
the two hand-reviewed migration PRs that must land in isolation.

---

## Phase 0 — Pre-v2

Pre-conditions for any v2 work to land.

### Deliverables

- [x] v1.0 ratified — every Must item from
      [`../spec-v1.md`](../spec-v1.md) green and shipped.
- [x] All v2.0 spec files reviewed
      ([`../spec-v2.md`](../spec-v2.md), [`README.md`](README.md),
      every file in this directory). Audit pass 2026-05-04.
- [x] ADRs 056–060 accepted.
- [x] **ADR 061 ratified** (2026-05-04) — Resend fail-soft + the
      `email_log` table shape. See
      [`../../../adr/061-resend-email-fail-soft.md`](../../../adr/061-resend-email-fail-soft.md).
      Phase 1 Migration A is now unblocked.
- [x] Phase numbering reconciled across [`adrs.md`](adrs.md),
      [`rollout.md`](rollout.md), and [`../spec-v2.md`](../spec-v2.md).
      Canonical: **Phase 0–4**; Alpha/Beta/Final/Polish are
      codename aliases for Phases 1–4
      ([`glossary.md`](glossary.md)).
- [x] `mkdocs.yml` nav references the v2/ split.

### DoD

- `task check` is green on `main`. ✅
- The v2 spec is reachable from `docs/index.md`. ✅ (via mkdocs nav)
- Spec v2.0 status flipped to **Ratified** in
  [`../spec-v2.md`](../spec-v2.md). ✅ (2026-05-04)
- ADR 061 file exists at
  [`../../../adr/061-resend-email-fail-soft.md`](../../../adr/061-resend-email-fail-soft.md)
  with status **Accepted**. ✅

**Phase 0 closed 2026-05-04.** Phase 1 (Alpha) is now unblocked.

---

## Phase 1 — Alpha (auth + tenancy + Tailwind shell)

The shortest path to *"a user can sign up, get a workspace, and see
an empty inbox in their browser."*

Phase 1 is large enough that it ships as **nine sequential PRs**.
Each PR closes `task check` green on its own, has its own commit
message, and is small enough to review honestly. Do not stack two
slices into one PR; the migration slice in particular must be
hand-reviewed in isolation.

Tier tags from the spec apply to every PR: `[Must]` blocks the
phase from closing; `[Should]` can slip into a later PR within the
same phase; `[Nice]` is opportunistic.

<a id="pr-1-1"></a>

### PR 1.1 — `feat(css): tailwind plumbing + four-file architecture + /styleguide stub`

Pure-frontend, no DB. Stands up the build pipeline and gives every
later page a stylesheet to link to.

**Touches**
- `tailwind.config.cjs` (theme reads tokens via CSS variables)
- `src/feedback_triage/static/css/{tokens,base,layout,components,effects,app}.css`
- `scripts/build_css.py` (cross-platform wrapper around the
  Standalone CLI)
- `Taskfile.yml` — `task setup:css`, `task build:css`,
  `task watch:css`; `task check` invokes `build:css`
- `Containerfile` — new `builder-frontend` stage; `runtime` copies
  only the hashed CSS
- `src/feedback_triage/templates/_base.html` — single
  `<link rel="stylesheet">` with hashed filename
- `src/feedback_triage/templates/styleguide.html` + minimal route
  ([ADR 056](../../../adr/056-style-guide-page.md))
- `tools/tailwindcss(.exe)` — bootstrap binary downloaded by
  `task setup:css`
- `src/feedback_triage/static/css/.gitignore` — ignore `app.*.css`

**Deliverables this PR closes**
- [x] **Tailwind plumbing** — full deliverable from
      [`css.md`](css.md).
- [x] `/styleguide` route exists (empty shell; populated as
      components arrive in later PRs).

**DoD**
- `task setup:css && task build:css` produces a hashed
  `app.<hash>.css` locally.
- `task check` is green on a clean clone.
- Visiting `/styleguide` in a browser renders something — even an
  empty page with the body bg from `tokens.css` proves the wiring.

---

<a id="pr-1-2"></a>

### PR 1.2 — `docs(adr): draft ADR 062 (v1→v2 data migration) + ADR 063 (status enum) + ADR 064 (pain vs priority)`

Documentation-only. Locks the schema choices PR 1.3b, PR 2.1, and
Phase 2 UI will rely on.

**Touches**
- `docs/adr/062-v1-to-v2-data-migration.md` (Status: Accepted)
- `docs/adr/063-status-enum-extension.md` (Status: Accepted)
- `docs/adr/064-pain-vs-priority-dual-fields.md` (Status: Accepted)
- `docs/adr/README.md` — index rows
- `mkdocs.yml` — nav rows
- `docs/project/spec/v2/adrs.md` — flip all three rows from "TBD" to
  "Accepted" with file links
- `docs/project/spec/spec-v2.md` — ADR table status column

**Deliverables this PR closes**
- [x] **ADR 062** drafted and accepted — covers the two-step
      Migration A / Migration B choreography.
- [x] **ADR 063** drafted and accepted — covers the status enum
      extension and `rejected` deprecation path.
- [x] **ADR 064** drafted and accepted — covers the
      pain-vs-priority dual-field rationale.

**DoD**
- All three ADRs follow `docs/adr/template.md` and have explicit
  Decision, Alternatives Considered, and Consequences sections.
- `mkdocs build` is clean (no broken links).

---

<a id="pr-1-3a"></a>

### PR 1.3a — `refactor(models): split models.py into a package + add v2 enums`

Pure scaffold. **No DB changes, no migration.** Splits the current
single-file `src/feedback_triage/models.py` into a `models/`
package so PR 1.3b can land tables one file at a time, and adds
the new native-enum *Python* mirrors (the Postgres types are
created in 1.3b). Existing routes, tests, and the current Alembic
revision keep working unchanged.

**Touches**
- `src/feedback_triage/models/__init__.py` — re-exports
  `FeedbackItem` so `from feedback_triage.models import …`
  callers keep working.
- `src/feedback_triage/models/feedback.py` — moved verbatim from
  the old `models.py` (only the import path changes).
- `src/feedback_triage/models/users.py`, `sessions.py`,
  `tokens.py`, `workspaces.py`, `memberships.py`,
  `invitations.py`, `auth_rate_limits.py`, `email_log.py` —
  empty stub files with module docstrings only. PR 1.3b fills
  them in.
- `src/feedback_triage/enums.py` — adds `UserRole`,
  `WorkspaceRole`, `EmailStatus`, `EmailPurpose` Python
  `StrEnum`s (per ADR 061). The matching Postgres native enum
  types are created in PR 1.3b's migration.
- `tests/` — no test changes; the existing suite is the
  regression check that the package split didn't break imports.

**Deliverables this PR closes**

None of the v2 ledger deliverables are completed by this PR. It
is preparatory scaffolding for PR 1.3b.

**DoD**
- [x] `task check` is green (lint + typecheck + tests).
- [x] `from feedback_triage.models import FeedbackItem` and
  `from feedback_triage.models.feedback import FeedbackItem`
  both resolve.
- [x] The four new enum classes are importable from
  `feedback_triage.enums` and round-trip through `StrEnum`
  (`UserRole("admin")` etc.).
- [x] No new Alembic revisions; `uv run alembic current` is
  unchanged.

---

<a id="pr-1-3b"></a>

### PR 1.3b — `feat(db): migration A — auth, tenancy, email_log tables + native enums`

The single largest schema migration in the v1→v2 jump.
**Hand-reviewed.** Ships as exactly one Alembic revision; PR 2.1
will ship Migration B.

**Touches**
- `alembic/versions/<rev>_v2_a_auth_tenancy_email_log.py`
- `src/feedback_triage/models/users.py`,
  `models/sessions.py`, `models/tokens.py`, `models/workspaces.py`,
  `models/memberships.py`, `models/invitations.py`,
  `models/auth_rate_limits.py`, `models/email_log.py` — bodies
  filled in (the empty modules were created in PR 1.3a).
- `src/feedback_triage/database.py` — pool config
  (`pool_size=5, max_overflow=0` per worker; ADR 048 invariant
  preserved)
- `src/feedback_triage/enums.py` — wires the `UserRole`,
  `WorkspaceRole`, `EmailStatus`, `EmailPurpose` Python enums
  (added in PR 1.3a) to native Postgres enum types
  `user_role_enum`, `workspace_role_enum`, `email_status_enum`,
  `email_purpose_enum` (per ADR 061).
- `tests/api/test_session_per_request.py` — extended canary
  proving the contract holds with the bigger table set

**Deliverables this PR closes**
- [x] **Schema migration #1 (auth + tenancy)** — full deliverable.
- [x] **`feedback_item` retrofit (additive)** — `workspace_id`
      column added nullable. Backfill **and** the `NOT NULL` flip
      are deferred to Migration B (PR 2.1) per ADR 062, which keeps
      Migration A schema-only and trivially reversible.

**DoD**
- `uv run alembic upgrade head` then
  `uv run alembic downgrade -1` then `upgrade head` round-trips
  cleanly on a real Postgres instance.
- Hand-review checklist signed off in PR description: every
  table has a native enum where the spec calls for one, every
  text column has a `CHECK length(...) <= N`, every FK has
  `ON DELETE` semantics declared, every `updated_at` has a
  `BEFORE UPDATE` trigger.
- The session-per-request canary still green.

---

<a id="pr-1-4"></a>

### PR 1.4 — `feat(auth): hashing, sessions, tokens, deps + Argon2 startup warm-up`

Self-contained module. No HTTP routes yet — just the building
blocks.

**Touches**
- `src/feedback_triage/auth/hashing.py` — Argon2id, params tuned
  to 120–180 ms per verify on Hobby
- `src/feedback_triage/auth/sessions.py` — cookie create / rolling
  renewal / revoke
- `src/feedback_triage/auth/tokens.py` — verify / reset / invite
  token mint + consume
- `src/feedback_triage/auth/deps.py` — `CurrentUser`,
  `RequireSession`, `RequireRole`
- `src/feedback_triage/main.py` — startup hook calls
  `argon2.PasswordHasher().hash("warmup")` once
  ([`railway-optimization.md`](railway-optimization.md))
- `tests/unit/auth/test_hashing.py`,
  `test_sessions.py`, `test_tokens.py`

**Deliverables this PR closes**
- [x] **Auth module** — full deliverable.

**DoD**
- Argon2id parameters benchmarked; comment in `hashing.py` records
  the measured per-verify time on dev hardware and on Railway.
- Session cookies have `HttpOnly`, `Secure`, `SameSite=Lax`.
- Token TTLs match [`auth.md`](auth.md).
- Unit tests cover happy path + every failure mode (expired
  token, replayed token, wrong-secret cookie).

---

<a id="pr-1-5"></a>

### PR 1.5 — `feat(tenancy): WorkspaceContext + policies + cross-tenant 404 canary`

Tenancy primitives plus the canary tests that **must exist before
any tenanted route ships in PR 1.7+**.

**Touches**
- `src/feedback_triage/tenancy/context.py` — `WorkspaceContext`
  resolved from `<slug>` path param; raises 404 (never 403) on
  cross-tenant
- `src/feedback_triage/tenancy/policies.py` — role gates
- `tests/api/test_isolation.py` — six initial canary cases (one
  per cross-tenant table the v2 schema introduces). New cases
  added in PR 2.x as new tables land.

**Deliverables this PR closes**
- [x] **Tenancy module** — full deliverable.
- [x] **Cross-tenant canary tests** (initial six cases).

**DoD**
- Every test in `test_isolation.py` asserts **404, never 403**,
  and asserts the response body never echoes another workspace's
  row id.
- A test forcing the policy to incorrectly return 403 fails (i.e.
  the canary actually catches the regression).

---

<a id="pr-1-6"></a>

### PR 1.6 — `feat(email): Resend client (fail-soft) + 4 templates + DRY_RUN test mode`

Self-contained. ADR 061 is already accepted, so this is purely
implementation.

**Touches**
- `src/feedback_triage/email/client.py` — `httpx`-based Resend
  wrapper, in-process retry loop, writes `email_log` rows per
  ADR 061
- `src/feedback_triage/email/templates/{verification,verification_already,password_reset,invitation}.html`
  (Jinja, email-only per ADR 014)
- `src/feedback_triage/config.py` — `RESEND_*` env vars, boot-time
  validation
- `tests/unit/email/test_client.py` — `RESEND_DRY_RUN=1` short-
  circuit + provider-down canary using injected `httpx.ConnectError`
- `tests/api/test_auth_no_enumeration.py` — log-row assert that
  proves the no-enumeration copy is provider-state-independent

**Deliverables this PR closes**
- [x] **Email client (fail-soft stub)** — full deliverable
      (templates listed; `status_change.html` lands in Phase 3).

**DoD**
- Zero live network calls in CI; `RESEND_DRY_RUN=1` is the test
  fixture default.
- Provider-down canary asserts the user-facing flow returns 200
  and the row lands at `status='failed'` after retries.
- `RESEND_API_KEY` missing at boot fails fast with a clear error.

---

<a id="pr-1-7"></a>

### PR 1.7 — `feat(api): /api/v1/auth/* endpoints + page routes for sign-in flow`

Now that auth, tenancy, and email exist, wire the HTTP surface for
the sign-up / sign-in / verify / reset / invitation flows.

**Touches**
- `src/feedback_triage/api/v1/auth.py` — sign-up, log-in, log-out,
  verify-email, request-reset, perform-reset, accept-invitation
- `src/feedback_triage/pages/auth.py` — page routes for `/login`,
  `/signup`, `/forgot-password`, `/reset-password`,
  `/verify-email`, `/invitations/<token>`
- `src/feedback_triage/templates/pages/auth/*.html`
- `src/feedback_triage/static/js/auth.js` — Fetch-API form
  submissions; state-class toggling only
- `tests/api/test_auth_*.py` — flow-level tests for each endpoint
- `tests/e2e/test_signup_flow.py` — Playwright smoke

**Deliverables this PR closes**
- [x] **API endpoints — auth subset** (`/api/v1/auth/*`).
- [x] **Page routes — auth subset** (`/login`, `/signup`,
      `/forgot-password`, `/reset-password`, `/verify-email`,
      `/invitations/<token>`).

**DoD**
- A new dev can run `task up && task migrate && task dev`, hit
  `/signup`, complete the verify-email flow with
  `RESEND_DRY_RUN=1`, log in, and land on a placeholder dashboard.
- `test_auth_no_enumeration.py` passes — sign-up and forgot-
  password give identical responses for known and unknown
  addresses.

---

<a id="pr-1-8"></a>

### PR 1.8 — `feat(api): workspaces, memberships, invitations + dashboard empty state`

Closes the Phase 1 product slice: a workspace exists, members
belong to it, dashboard renders.

**Touches**
- `src/feedback_triage/api/v1/workspaces.py` — POST / GET
- `src/feedback_triage/api/v1/memberships.py`
- `src/feedback_triage/api/v1/invitations.py`
- `src/feedback_triage/pages/dashboard.py` —
  `/w/<slug>/dashboard` empty state
- `src/feedback_triage/templates/pages/dashboard/empty.html`
- `tests/api/test_workspaces.py`, `test_memberships.py`,
  `test_invitations.py` — including new isolation cases appended
  to `test_isolation.py`

**Deliverables this PR closes**
- [x] **API endpoints — workspace subset**
      (`/api/v1/workspaces`, `/memberships`, `/invitations`).
- [x] **Page routes — dashboard subset**
      (`/w/<slug>/dashboard` empty state).

**DoD**
- Sign up → create workspace → see empty dashboard works end to
  end.
- `test_isolation.py` now has cases for memberships and
  invitations on top of PR 1.5's six.

---

<a id="pr-1-9"></a>

### PR 1.9 — `feat(config): FEATURE_AUTH flag + sidebar + theme switcher (dormant) + Phase 1 close`

Should/Nice items + the production-rollout flag. Closes Phase 1.

**Touches**
- `src/feedback_triage/config.py` — `FEATURE_AUTH` env var
- `src/feedback_triage/main.py` — short-circuit auth routes with
  503 when `FEATURE_AUTH=false` ([`auth.md`](auth.md))
- `src/feedback_triage/templates/_partials/sidebar.html`
- `src/feedback_triage/static/js/theme.js` — toggles `data-theme`,
  persists to localStorage; CSS hooks already exist from PR 1.1
  (FD remains a Phase 4 deliverable; this PR just wires the
  switch dormant)
- `tests/api/test_feature_auth_flag.py` — auth routes 503 when
  flag is false

**Deliverables this PR closes**
- [x] **`FEATURE_AUTH` flag** — full deliverable.
- [x] **Sidebar navigation rendered** (Should).
- [x] **Theme switcher dormant but wired to `data-theme`**
      (Should).

**DoD (Phase 1 close)**
- All Must items above checked off.
- `task check` green.
- Production deploy with `FEATURE_AUTH=false` returns 503 from
  `/api/v1/auth/*` and the auth pages render a "coming soon"
  notice; local dev with `FEATURE_AUTH=true` is fully functional.
- `tests/api/test_isolation.py` has at least 6 cases covering
  feedback, submitters (placeholder until Phase 2 adds the
  table), tags (same), notes (same), memberships, and
  invitations (cross-workspace 404, never 200).

---

### Phase 1 — Verification (post PR 1.9)

```text
uv run pytest -m "not e2e"          # all unit + API tests green
uv run pytest tests/api/test_isolation.py -v
uv run pytest -m e2e tests/e2e/test_signup_flow.py
task build:css && test -s src/feedback_triage/static/css/app.*.css
uv run alembic upgrade head
```

**Phase 1 closed 2026-05-06.** Verification run on this date:

- `uv run pytest -m "not e2e"` → **159 passed, 3 skipped, 4
  deselected** (includes the 18 new `test_feature_auth_flag.py`
  cases).
- `uv run pytest tests/api/test_isolation.py -v` → **6 passed, 3
  skipped** (placeholder cases for tags/notes/submitters land in
  PR 2.1 with the schema).
- `task build:css` → wrote `app.de4d3f16a4.css` + manifest.
- `uv run alembic upgrade head` → already at head; no pending
  revisions.
- `task check` → green (ruff + mypy + tests).
- `uv run pytest -m e2e tests/e2e/test_signup_flow.py` runs
  locally with Playwright browsers installed; the smoke suite is
  gated and not part of the default `task check`.

Phase 2 (Beta) is now unblocked.

---

## Phase 2 — Beta (triage workflow + public submit)

Make a workspace useful: capture, classify, prioritize.

## Phase 2 — Beta (triage workflow + public submit)

Make a workspace useful: capture, classify, prioritize.

Phase 2 ships as **six sequential PRs**. Migration B (the
`NOT NULL workspace_id` flip + status rename) is the first PR
because every later PR depends on the new schema; it is
hand-reviewed in isolation.

<a id="pr-2-1"></a>

### PR 2.1 — `feat(db): migration B — backfill, NOT NULL flip, status rename, plus tags/notes/submitters/workflow tables`

The other big migration. Combines Migration B from
[`rollout.md`](rollout.md) with the additional tables Phase 2
needs. **Hand-reviewed.** Ships as **two Alembic revisions** in
the same PR — one for the backfill+flip+rename (per ADR 062), one
for the new-table DDL — so a deploy that fails halfway can roll
forward.

**Touches**
- `alembic/versions/<rev>_v2_b_backfill_flip_rename.py`
- `alembic/versions/<rev>_v2_b2_workflow_tables.py`
- `src/feedback_triage/models/feedback.py` — add workflow columns
  (`type`, `priority`, `published_to_roadmap`,
  `published_to_changelog`, `release_note`, `title`)
- `src/feedback_triage/models/{tags,notes,submitters,feedback_tags}.py`
- `src/feedback_triage/enums.py` — extended `status_enum`
  per ADR 063; new `priority_enum`, `feedback_type_enum`
- `tests/db/test_migration_b_roundtrip.py` — `upgrade → downgrade
  → upgrade` round-trip on a snapshot containing legacy
  `rejected` rows

**Deliverables this PR closes**
- [x] **Schema migration #2 (workflow)** — full deliverable
      (Migration B + status rename).
- [x] **Tags + notes + submitters tables** — full deliverable.

**DoD**
- Round-trip migration test green on a snapshot containing both
  `rejected` rows and rows with `workspace_id IS NULL`.
- Hand-review checklist signed off (same items as PR 1.3b).
- `test_isolation.py` extended with cases for tags, notes,
  submitters.

---

<a id="pr-2-2"></a>

### PR 2.2 — `feat(api): feedback CRUD on the v2 schema + tags/notes/submitters endpoints`

Pure API; no UI yet. Lets PR 2.3+ build pages against a stable
contract.

**Touches**
- `src/feedback_triage/api/v1/feedback.py` — full CRUD on the new
  shape; envelope responses; `PATCH` for partial updates
- `src/feedback_triage/api/v1/tags.py`,
  `api/v1/notes.py`, `api/v1/submitters.py`
- `src/feedback_triage/schemas/` — Pydantic v2 request/response
  models matching [`api.md`](api.md)
- `tests/api/test_feedback_v2.py`,
  `test_tags.py`, `test_notes.py`, `test_submitters.py`

**Deliverables this PR closes**
- (Foundation for PRs 2.3–2.5; no Must items checked off here on
  its own — every endpoint is required by a later page PR.)

**DoD**
- All endpoints return the `{items, total, skip, limit}` envelope
  for lists; explicit `response_model=` everywhere.
- `test_isolation.py` has cases covering every new endpoint.

---

<a id="pr-2-3"></a>

### PR 2.3 — `feat(pages): inbox + feedback list + feedback detail`

The triage UI itself. Three pages, one PR — they share components
and templates and must move together for the styleguide to stay
honest.

**Touches**
- `src/feedback_triage/pages/inbox.py`,
  `pages/feedback_list.py`, `pages/feedback_detail.py`
- `src/feedback_triage/templates/pages/inbox.html`,
  `feedback_list.html`, `feedback_detail.html`
- `src/feedback_triage/templates/_partials/{filter_bar,status_pill,priority_pill,tag_chip,timeline,notes_panel}.html`
- `src/feedback_triage/static/js/inbox.js` (filter bar state),
  `feedback_detail.js` (notes + tag editor)
- `src/feedback_triage/templates/styleguide.html` — populate with
  every component this PR introduces, in every variant + state
- `tests/e2e/test_inbox_smoke.py`,
  `test_feedback_detail_smoke.py`

**Deliverables this PR closes**
- [x] **Inbox page** with summary cards, filter bar, search,
      table.
- [x] **Feedback list page** (same shell, no default status
      filter).
- [x] **Feedback detail page** with timeline, internal notes,
      tags editor, publishing toggles.

**DoD**
- A workspace owner can transition an item through every status
  in the UI and see the timeline update.
- `/styleguide` now demos status pill, priority pill, tag chip,
  filter bar, notes panel, timeline.
- E2E smoke green.

---

<a id="pr-2-4"></a>

### PR 2.4 — `feat(public): public submission form at /w/<slug>/submit + honeypot + rate limit`

The only unauthenticated write surface in v2.0. Security guards
are part of the deliverable, not a follow-up.

**Touches**
- `src/feedback_triage/pages/public_submit.py` — `/w/<slug>/submit`
- `src/feedback_triage/templates/pages/public_submit.html` +
  thank-you locked-string copy ([`copy-style-guide.md`](copy-style-guide.md))
- `src/feedback_triage/api/v1/public/feedback.py` — POST endpoint;
  honeypot field; in-process rate limit per ADR (workspace + IP)
- `src/feedback_triage/services/submitter_link.py` — create or
  link `submitter` row when an email is present
- `tests/api/test_public_submit.py` — happy path, honeypot
  triggered, rate-limit triggered
- `tests/e2e/test_public_submit.py`

**Deliverables this PR closes**
- [ ] **Public submission form** at `/w/<slug>/submit` with
      honeypot + rate limit.

**DoD**
- A submission from an incognito window appears inside the
  workspace inbox.
- Honeypot-tripped submission returns 200 (no enumeration) but
  writes no row.
- Rate-limit-tripped submission returns 429 with the documented
  error envelope.

---

<a id="pr-2-5"></a>

### PR 2.5 — `feat(pages): settings v1 — workspace info, members, tags, public-submit toggle`

Closes the "owner can run a workspace" loop.

**Touches**
- `src/feedback_triage/pages/settings.py`
- `src/feedback_triage/templates/pages/settings/{index,members,tags,public_form}.html`
- `src/feedback_triage/static/js/settings.js`
- `src/feedback_triage/api/v1/workspace_settings.py` — patch
  workspace info, toggle public-submit flag
- `tests/api/test_workspace_settings.py`

**Deliverables this PR closes**
- [ ] **Settings page** v1 — workspace info, members, tags,
      public-submit toggle.

**DoD**
- An owner can rename the workspace, invite a member, create a
  tag, and toggle the public-submit form on/off without leaving
  the page.

---

<a id="pr-2-6"></a>

### PR 2.6 — `feat(triage): submitters pages + stale highlighting + axe-core in e2e (Should items + Phase 2 close)`

Phase 2's Should items, all small enough to ride together. Closes
Phase 2.

**Touches**
- `src/feedback_triage/pages/submitters.py` — list + detail
- `src/feedback_triage/templates/pages/submitters/{list,detail}.html`
- `src/feedback_triage/services/stale_detector.py` —
  `> 14 days in {new, needs_info}` ([`schema.md`](schema.md))
- `src/feedback_triage/templates/_partials/inbox_row.html` — adds
  the stale badge
- `tests/e2e/test_a11y.py` — axe-core integration on inbox,
  detail, settings, public submit

**Deliverables this PR closes**
- [ ] Submitters list & detail pages (Should).
- [ ] Stale-item highlighting on Inbox (Should).
- [ ] axe-core accessibility check in the e2e smoke suite
      (Should).

**DoD (Phase 2 close)**
- All Phase 2 Must items checked off across PRs 2.1–2.5.
- A workspace owner can: invite a member, the member accepts;
  either of them can submit a feedback item, tag it, set a
  priority, transition it through every status, leave a note, and
  see it on the management roadmap and changelog (roadmap +
  changelog land in Phase 3 — until then this verifies via the
  detail page only).
- The public submission form, in another browser session, creates
  a row visible inside the workspace.
- All cross-tenant canaries still pass; new ones added for tags,
  notes, submitters, publish flags.
- axe-core reports zero violations on every page in the smoke
  suite.

---

### Phase 2 — Verification (post PR 2.6)

```text
uv run pytest -m "not e2e"
uv run pytest -m e2e
uv run alembic upgrade head
uv run alembic downgrade -1 && uv run alembic upgrade head   # round-trip
```

---

## Phase 3 — Final (close the loop)

Make the workflow visible to the people who sent the feedback.

Phase 3 ships as **five sequential PRs**. PR 3.1 is the email
integration end-to-end (the riskiest piece because it crosses a
network boundary); PR 3.5 is the spec-ratification PR and must
land last.

<a id="pr-3-1"></a>

### PR 3.1 — `feat(email): status-change emails end-to-end + status_change.html template`

Resend integration in production mode. Fail-soft contract from
ADR 061 is exercised by integration tests for real this time.

**Touches**
- `src/feedback_triage/services/status_change_notifier.py` —
  hooks `feedback_item.status` transitions; resolves submitter
  email; calls `email/client.py`; status change commits even if
  send fails
- `src/feedback_triage/email/templates/status_change.html`
- `src/feedback_triage/config.py` — `EMAIL_NOTIFY_ON_STATUSES`
  env (default `shipped`)
- `tests/api/test_status_change_email.py` — happy path,
  fail-soft, opt-out
- `tests/integration/test_email_log_replay.py` — a `failed` row
  can be re-sent via `task email:replay <id>`
- `scripts/email_replay.py` + `task email:replay`

**Deliverables this PR closes**
- [ ] **Resend integration end-to-end** — full deliverable.
- [ ] **Status-change emails** for transitions other than
      `shipped` if configured (Should).

**DoD**
- Marking an item `shipped` triggers an `email_log` row and a
  Resend call (or `dry_run` short-circuit in tests).
- Provider-down test: status change still commits; row lands at
  `failed`; replay re-sends successfully when the provider is
  back.

---

<a id="pr-3-2"></a>

### PR 3.2 — `feat(pages): public roadmap + public changelog`

The two unauthenticated read surfaces. Same shell, same caching,
different filters.

**Touches**
- `src/feedback_triage/pages/public_roadmap.py` —
  `/w/<slug>/roadmap/public`; filters `published_to_roadmap = true`
- `src/feedback_triage/pages/public_changelog.py` —
  `/w/<slug>/changelog/public`; filters
  `status='shipped' AND published_to_changelog=true`
- `src/feedback_triage/templates/pages/public/{roadmap,changelog}.html`
- `Cache-Control` per [`performance-budgets.md`](performance-budgets.md):
  `public, max-age=300, stale-while-revalidate=600`
- `tests/api/test_public_roadmap.py`,
  `test_public_changelog.py`
- `tests/e2e/test_public_pages_smoke.py`

**Deliverables this PR closes**
- [ ] **Public roadmap** at `/w/<slug>/roadmap/public`.
- [ ] **Public changelog** at `/w/<slug>/changelog/public`.

**DoD**
- Both pages render without authentication.
- A row with `published_to_changelog=false` does not appear on
  the changelog — covered by a test, not just spot-check.

---

<a id="pr-3-3"></a>

### PR 3.3 — `feat(pages): management roadmap kanban + management changelog editor`

The authenticated counterparts to PR 3.2. These are where
owners set the publish flags and edit release notes.

**Touches**
- `src/feedback_triage/pages/roadmap.py` — `/w/<slug>/roadmap`
  kanban (`planned` / `in_progress` / `shipped` columns)
- `src/feedback_triage/pages/changelog.py` —
  `/w/<slug>/changelog` with editable `release_note` per row
- `src/feedback_triage/templates/pages/{roadmap,changelog}.html`
- `src/feedback_triage/templates/_partials/{kanban_card,kanban_column,release_note_editor}.html`
- `src/feedback_triage/static/js/{roadmap,changelog}.js`
- `src/feedback_triage/api/v1/feedback.py` — PATCH endpoints for
  publish flags and `release_note` (if not already present)
- `src/feedback_triage/templates/styleguide.html` — add kanban
  card, column, release-note editor

**Deliverables this PR closes**
- [ ] **Management roadmap** kanban with publish toggles.
- [ ] **Management changelog** with editable release-note field.

**DoD**
- An owner can drag (or button-click) an item between kanban
  columns and the status updates; reduced-motion users see no
  drag animation but the same final state.
- An owner can edit a release note inline and the change
  persists.

---

<a id="pr-3-4"></a>

### PR 3.4 — `feat(pages): dashboard fully populated + privacy + terms + insights v1 + mini demo`

Fills the dashboard from PR 1.8's empty state and lands the
remaining static + Should + Nice surfaces.

**Touches**
- `src/feedback_triage/pages/dashboard.py` — replace empty state
  with the full dashboard
- `src/feedback_triage/services/dashboard_aggregator.py` — backed
  by the per-workspace `cachetools.TTLCache` from
  [`performance-budgets.md`](performance-budgets.md)
- `src/feedback_triage/templates/pages/dashboard/index.html` —
  summary cards, intake sparkline (inline SVG), top tags, recent
  activity
- `src/feedback_triage/pages/legal.py` — `/privacy`, `/terms`
- `src/feedback_triage/templates/pages/legal/{privacy,terms}.html`
- `src/feedback_triage/templates/_partials/footer.html` — link to
  privacy + terms
- `src/feedback_triage/pages/insights.py` — `/w/<slug>/insights`
  v1 (Should): top tags, status mix donut, pain histogram
  (inline SVG, no library)
- `src/feedback_triage/templates/pages/insights.html`
- `src/feedback_triage/static/js/landing_demo.js` — mini demo
  (FU1, Nice); fully client-side, no API contract
- `src/feedback_triage/templates/pages/landing.html` — hooks the
  mini demo in
- `tests/api/test_dashboard_summary.py` — cache-hit / cache-miss
  / 60s TTL semantics
- `tests/e2e/test_dashboard_smoke.py`

**Deliverables this PR closes**
- [ ] **Dashboard** filled out — full deliverable.
- [ ] **Privacy + Terms pages** linked from the landing footer.
- [ ] **Insights page** v1 (Should).
- [ ] **Mini demo (FU1)** on the landing page (Nice).

**DoD**
- Dashboard renders all four sections.
- Privacy + terms reachable from every page footer.
- Insights page renders without a JS chart library.
- Mini demo runs entirely in the browser; viewing it makes no
  API call.

---

<a id="pr-3-5"></a>

### PR 3.5 — `chore(release): ratify v2.0 — flip docs/index, README, copilot-instructions to v2 + cut v2.0.0 tag`

The spec-ratification PR. Documentation + tag only — no code.
**Lands last in Phase 3.**

**Touches**
- `docs/index.md` — point at v2.0 as the active spec
- `README.md` — same
- `.github/copilot-instructions.md` — update the "Repository
  status" header to make v2.0 authoritative; drop the v1.0
  source-of-truth language
- `docs/project/spec/spec-v2.md` — confirm Status row is
  Ratified (already flipped in Phase 0; verify)
- `CHANGELOG.md` — release-please will generate; verify
- Tag: `v2.0.0` via `task release`

**Deliverables this PR closes**
- [ ] **v2.0 spec ratified end-to-end** (the "flip docs to point
      at v2.0" item from the original Phase 3 DoD).

**DoD (Phase 3 close)**
- All Phase 3 Must items checked off across PRs 3.1–3.4.
- Marking an item `shipped` in a workspace causes:
  - the item appears on `/w/<slug>/changelog/public` if
    `published_to_changelog`;
  - if the submitter has an email, a Resend email is sent (or
    logged-as-failed without rolling back the transaction);
  - an `email_log` row records the attempt.
- v2.0 is **Ratified** in spec, README, docs/index, and
  copilot-instructions.
- `task release` cuts `v2.0.0`.

---

### Phase 3 — Verification (post PR 3.5)

```text
uv run pytest -m "not e2e"
uv run pytest -m e2e tests/e2e/test_inbox_smoke.py tests/e2e/test_public_submit.py
RESEND_DRY_RUN=1 uv run pytest tests/unit/test_email_client.py
task check
```

---

## Phase 4 — Polish

Everything below is opportunistic. None blocks ratification —
v2.0 is already shipped at the end of Phase 3. Each Polish item
ships as its own small PR; none has dependencies on the others,
so the order is reader's choice.

<a id="pr-4-1"></a>

### PR 4.1 — `feat(ui): dark mode (FD) — [data-theme="dark"] activated + persisted per user`

**Touches**
- `src/feedback_triage/static/css/tokens.css` — confirm dark
  overrides exist (the CSS hooks landed dormant in PR 1.9)
- `src/feedback_triage/static/js/theme.js` — promote from dormant
  to active
- `src/feedback_triage/api/v1/users.py` — PATCH `theme_preference`
- `src/feedback_triage/models/users.py` — `theme_preference`
  column (Alembic revision in same PR)
- `tests/e2e/test_dark_mode.py`

**Deliverables this PR closes**
- [ ] **Dark mode (FD)** — toggle persisted per user.

---

<a id="pr-4-2"></a>

### PR 4.2 — `feat(ui): styleguide preset themes (4) wired up on /styleguide`

**Touches**
- `src/feedback_triage/templates/styleguide.html` — preset
  switcher
- `src/feedback_triage/static/css/tokens.css` — four
  `[data-theme="preset-*"]` blocks
- `src/feedback_triage/static/js/styleguide.js`
- Per [ADR 056](../../../adr/056-style-guide-page.md), preset
  themes are visible **only** on `/styleguide`; never persisted
  app-wide.

**Deliverables this PR closes**
- [ ] **Styleguide preset themes** — four presets from ADR 056.

---

<a id="pr-4-3"></a>

### PR 4.3 — `feat(email): Resend webhook for delivery + bounce events (if available)`

Gated on Resend actually shipping a webhook within v2.0's
timeline. If they don't, this PR doesn't ship; nothing else
depends on it.

**Touches**
- `src/feedback_triage/api/v1/webhooks/resend.py` — signature
  verification, idempotent updates to `email_log.status`
- `src/feedback_triage/services/email_log_updater.py`
- `tests/api/test_resend_webhook.py`

**Deliverables this PR closes**
- [ ] **Resend webhook** for delivery / bounce events.

---

<a id="pr-4-4"></a>

### PR 4.4 — `feat(brand): custom favicon + wordmark refresh`

Design-driven. Lands when the designed mark is ready.

**Touches**
- `src/feedback_triage/static/img/{favicon.ico,favicon.svg,apple-touch-icon.png,wordmark.svg}`
- `src/feedback_triage/templates/_base.html` — favicon links
- `src/feedback_triage/templates/_partials/{header,footer}.html` —
  swap placeholder wordmark for the real one

**Deliverables this PR closes**
- [ ] **Custom favicon + wordmark refresh.**

---

<a id="pr-4-5"></a>

### PR 4.5 — `feat(ui): production visual identity — palette, motion, effects`

Designer-driven; the project owner picks the final look. Up to
this PR every page has used placeholder tokens from
[`css.md`](css.md). PR 4.5 ratifies the production palette,
motion language, and decorative polish, then promotes the chosen
preset on `/styleguide` to the unmarked default token block.
The four [ADR 056](../../../adr/056-style-guide-page.md)
presets — `production`, `basic`, `unique`, `crazy` — remain on
`/styleguide` for reviewer comparison; one becomes the shipped
identity.

Why this is its own PR: every preceding feature PR has been built
against tokens, not raw values, so changing the visual identity
is a one-block edit to `tokens.css` plus polish in
`effects.css`. No template churn, no JS churn — by design.

**Touches**
- `src/feedback_triage/static/css/tokens.css` — final
  `--color-*`, `--radius-*`, `--shadow-*`, `--motion-*`,
  `--easing-*` values; the four `[data-theme=…]` preset blocks
  retained on `/styleguide`.
- `src/feedback_triage/static/css/effects.css` — production
  transitions, hover polish, any keyframes the designed identity
  calls for (`prefers-reduced-motion` honoured).
- `src/feedback_triage/static/css/components.css` — only if the
  identity needs new sub-states; otherwise unchanged because
  components reference tokens, not raw values.
- `src/feedback_triage/templates/styleguide.html` — wire the
  preset switcher (`<select>` flipping `data-theme` on `<main>`)
  if not already shipped by PR 4.2; document which preset is the
  production default.
- `tailwind.config.cjs` — only if a new token name is added.
- `docs/project/spec/v2/core-idea.md` — update the palette
  section to reflect the chosen production values.
- `docs/adr/065-production-visual-identity.md` — record the
  chosen palette + motion language as a ratified decision
  (template at [`docs/adr/template.md`](../../../adr/template.md)).
- `docs/adr/066-theme-switcher-scope.md` — record that the
  preset switcher stays on `/styleguide` only in v2.0; per-user
  theming is deferred (separate ADR when proposed).

**Deliverables this PR closes**
- [ ] **Production palette ratified** in `tokens.css` and
      mirrored in `core-idea.md`.
- [ ] **Motion + effects** finalised in `effects.css` (transitions,
      keyframes, hover polish) with `prefers-reduced-motion`
      coverage on every animated rule.
- [ ] **Styleguide preset switcher** demonstrates all four
      [ADR 056](../../../adr/056-style-guide-page.md) themes;
      the production default matches one of them (or the
      fifth designed-in-this-PR option).
- [ ] **ADR 065** committed and linked from `css.md`.
- [ ] **ADR 066** committed and linked from `css.md`.
- [ ] **No template diffs** beyond the styleguide — proof that
      the token discipline held.

**DoD**
- `task build:css` produces a visually-final `app.css`.
- Reviewer flips between the four presets on `/styleguide` with
  the switcher; production default is unambiguous.
- Lighthouse accessibility on every shipped page ≥ 95
  (contrast ratios on the chosen palette must clear WCAG AA).
- All [`css.md`](css.md) rules still pass: no `!important`
  outside reduced-motion, no `@apply` outside
  `components.css` / `layout.css`, specificity budget held,
  pills carry icon + text + color (not color alone).
- `docs/project/spec/v2/core-idea.md` palette section matches
  `tokens.css` byte-for-byte on color values.

---

## Cross-cutting checklists

Used at the end of every phase.

### Database

- [ ] Migration is one Alembic revision per logical change.
- [ ] Migration is reversible (`downgrade` implemented and tested
      via round-trip).
- [ ] Native Postgres enums + DB `CHECK` constraints — never plain
      strings.
- [ ] `compare_type=True` and `compare_server_default=True`
      already on; the autogenerated diff is hand-reviewed.

### API

- [ ] Every route declares `response_model=`.
- [ ] List endpoints return the `{items, total, skip, limit}`
      envelope, not a bare array.
- [ ] Routes are `def`, not `async def` (v1.0 inheritance, ADR
      050).
- [ ] Cross-tenant lookups return 404, never 403.

### Frontend

- [ ] Tailwind classes only; no inline `style="..."`.
- [ ] One `<h1>` per page; sequential headings; skip-link present.
- [ ] Pills carry icon + text + color, never color alone.
- [ ] `:focus-visible` styles tied to `--color-focus`.

### Security

- [ ] No secret committed; CI gitleaks pass.
- [ ] Public form has honeypot + rate limit.
- [ ] Cookies: `HttpOnly`, `Secure`, `SameSite=Lax`.
- [ ] CSP header configured on every HTML response. v2.0 ships
      with `script-src 'self'` only — no inline scripts, no nonces,
      no `unsafe-inline`. Every page-level JS file is a separate
      static asset under `static/js/`. ([`security.md`](security.md))

### Tests

- [ ] Postgres for tests, never SQLite.
- [ ] One transaction per test; truncate fixture between tests.
- [ ] `test_patch_then_get_returns_fresh_state` canary still
      green ([`../spec-v1.md`](../spec-v1.md)).
- [ ] `test_isolation.py` cases match the count of cross-tenant
      tables.

### Docs

- [ ] Spec files updated alongside the code.
- [ ] ADRs filed for every new technology / pattern decision.
- [ ] CHANGELOG entry per release-please convention.

---

## Cross-references

- [`../../implementation.md`](../../implementation.md) — v1.0 plan.
- [`schema.md`](schema.md) — DDL.
- [`api.md`](api.md) — endpoints.
- [`auth.md`](auth.md) — auth state machine.
- [`multi-tenancy.md`](multi-tenancy.md) — `WorkspaceContext`
  rules.
- [`security.md`](security.md) — guard rails per phase.
- [`adrs.md`](adrs.md) — TBD ADR list and ordering.
- [`rollout.md`](rollout.md) — deploy & data-migration mechanics.
