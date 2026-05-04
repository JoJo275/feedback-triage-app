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

## Phase 0 — Pre-v2

Pre-conditions for any v2 work to land.

### Deliverables

- [ ] v1.0 ratified — every Must item from
      [`../spec-v1.md`](../spec-v1.md) green and shipped.
- [ ] All v2.0 spec files reviewed
      ([`../spec-v2.md`](../spec-v2.md), [`README.md`](README.md),
      every file in this directory).
- [ ] ADRs 058, 059, 060 accepted (already done).
- [ ] `mkdocs.yml` nav references the v2/ split.

### DoD

`task check` is green on `main`. The v2 spec is reachable from
`docs/index.md`.

---

## Phase 1 — Alpha (auth + tenancy + Tailwind shell)

The shortest path to *"a user can sign up, get a workspace, and see
an empty inbox in their browser."*

### Deliverables — Must

- [ ] **Tailwind plumbing.** `tailwind.config.cjs`,
      `static/css/input.css`, `scripts/build_css.py`,
      `task setup:css`, `task build:css`, `task watch:css`. CI step
      added to `task check`. ([`css.md`](css.md))
- [ ] **Schema migration #1 (auth + tenancy).** Tables: `users`,
      `sessions`, `email_tokens`, `workspaces`,
      `workspace_memberships`, `workspace_invitations`. Native
      enums for `platform_role`, `workspace_role`, `token_kind`.
      Indexes from [`schema.md`](schema.md). One Alembic revision,
      hand-reviewed.
- [ ] **`feedback_item` retrofit (additive).** Add `workspace_id`
      with backfill into a `signalnest-legacy` workspace; not yet
      `NOT NULL`. Tracked under ADR 062.
- [ ] **Auth module.** `auth/hashing.py` (Argon2id),
      `auth/sessions.py` (cookie create / rolling renewal /
      revoke), `auth/tokens.py` (verify, reset, invite),
      `auth/deps.py` (`CurrentUser`, `RequireSession`).
- [ ] **Tenancy module.** `tenancy/context.py`
      (`WorkspaceContext` from `<slug>` path param + role check),
      `tenancy/policies.py`.
- [ ] **Email client (fail-soft stub).** `email/client.py` with a
      Resend HTTP client and a `dry_run` mode used in tests.
      Templates: verify-email, reset-password, accept-invitation.
- [ ] **API endpoints.** All `/api/v1/auth/*`,
      `/api/v1/workspaces` (POST + GET), `/api/v1/memberships`,
      `/api/v1/invitations`. See [`api.md`](api.md).
- [ ] **Page routes.** `/`, `/login`, `/signup`,
      `/forgot-password`, `/reset-password`, `/verify-email`,
      `/invitations/<token>`, `/w/<slug>/dashboard` (empty state),
      `/styleguide` ([ADR 056](../../../adr/056-style-guide-page.md)).
- [ ] **Cross-tenant canary tests.**
      `tests/api/test_isolation.py` — every read/write in another
      workspace must return 404 not 403, and must never echo
      another workspace's row.
- [ ] **ADR 061** (Resend fail-soft) merged before any path
      depending on Resend lands.

### Deliverables — Should

- [ ] Sidebar navigation rendered (links exist; targets may be
      placeholder pages).
- [ ] Theme switcher dormant but wired to `data-theme` (FD
      defers).

### DoD

- `task check` green.
- A new dev can run `task up && task migrate && task seed && task
  dev`, sign up at `http://localhost:8000/signup`, and land on the
  dashboard empty state.
- `tests/api/test_isolation.py` has at least 6 cases covering
  feedback, submitters, tags, notes, memberships, and invitations
  (cross-workspace 404, never 200).

### Verification

```text
uv run pytest -m "not e2e"          # all unit + API tests green
uv run pytest tests/api/test_isolation.py -v
uv run pytest -m e2e tests/e2e/test_signup_flow.py
task build:css && test -s src/feedback_triage/static/css/app.css
uv run alembic upgrade head
```

---

## Phase 2 — Beta (triage workflow + public submit)

Make a workspace useful: capture, classify, prioritize.

### Deliverables — Must

- [ ] **Schema migration #2 (workflow).** `feedback_item`:
      `ALTER COLUMN workspace_id SET NOT NULL`; extend `status_enum`
      with `needs_info`, `accepted`, `in_progress`, `shipped`,
      `spam`, `closed`; rename `rejected → closed` via data
      migration; add `priority` enum + column; add columns
      `published_to_roadmap`, `published_to_changelog`,
      `release_note`. Tracked under ADRs 062 + 063.
- [ ] **Tags + notes + submitters tables.** From
      [`schema.md`](schema.md). Native enums for any new fields.
- [ ] **Inbox page** with summary cards, filter bar, search, table
      ([`pages.md`](pages.md#inbox)).
- [ ] **Feedback list page** (same shell, no default status
      filter).
- [ ] **Feedback detail page** with timeline, internal notes, tags
      editor, publishing toggles ([`pages.md`](pages.md#feedback-detail)).
- [ ] **Public submission form** at `/w/<slug>/submit` with
      honeypot + rate limit ([`security.md`](security.md)).
      Submissions create or link a `submitter` row when an email is
      present.
- [ ] **Settings page** v1: workspace info, members, tags, public-
      submit toggle.
- [ ] **ADR 063** (status enum extension + `rejected` removal) and
      **ADR 064** (pain-vs-priority dual-field rationale) merged.

### Deliverables — Should

- [ ] Submitters list & detail pages.
- [ ] Stale-item highlighting on Inbox (> 14 days in `new` /
      `needs_info`).
- [ ] axe-core accessibility check in the e2e smoke suite.

### DoD

- A workspace owner can: invite a member, the member accepts;
  either of them can submit a feedback item, tag it, set a
  priority, transition it through every status, leave a note, and
  see it on the management roadmap and changelog.
- The public submission form, in another browser session, creates
  a row visible inside the workspace.
- All cross-tenant canaries still pass; new ones added for tags,
  notes, submitters, publish flags.

### Verification

```text
uv run pytest -m "not e2e"
uv run pytest -m e2e
uv run alembic upgrade head
uv run alembic downgrade -1 && uv run alembic upgrade head   # round-trip
```

---

## Phase 3 — Final (close the loop)

Make the workflow visible to the people who sent the feedback.

### Deliverables — Must

- [ ] **Resend integration end-to-end.** Status-change emails on
      `shipped` (and any other status in the configured notify-
      list). Fail-soft: status change succeeds even if Resend is
      down. ADR 061 plumbing exercised by integration tests.
- [ ] **Public roadmap** at `/w/<slug>/roadmap/public` reading
      `published_to_roadmap = true`.
- [ ] **Public changelog** at `/w/<slug>/changelog/public` reading
      `status = 'shipped' AND published_to_changelog = true`.
- [ ] **Management roadmap** kanban (`planned` /`in_progress` /
      `shipped`) with publish toggles.
- [ ] **Management changelog** with editable release-note field.
- [ ] **Dashboard** filled out: summary cards, intake sparkline,
      top tags, recent activity.
- [ ] **Privacy + Terms pages** linked from the landing footer.

### Deliverables — Should

- [ ] **Insights page** v1: top tags, status mix donut, pain
      histogram (inline SVG, no library).
- [ ] **Status-change emails** for transitions other than
      `shipped` if configured.

### Deliverables — Nice

- [ ] **Mini demo (FU1)** on the landing page.

### DoD

- Marking an item `shipped` in a workspace causes:
  - the item appears on `/w/<slug>/changelog/public` if
    `published_to_changelog`;
  - if the submitter has an email, a Resend email is sent (or
    logged-as-failed without rolling back the transaction);
  - an `email_log` row records the attempt.
- v2.0 spec is flipped to **Ratified**;
  [`../../../index.md`](../../../index.md) and
  [`README.md`](../../../../README.md) updated to point at v2.0;
  [`../../../../.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md)
  updated.

### Verification

```text
uv run pytest -m "not e2e"
uv run pytest -m e2e tests/e2e/test_inbox_smoke.py tests/e2e/test_public_submit.py
RESEND_DRY_RUN=1 uv run pytest tests/unit/test_email_client.py
task check
```

---

## Phase 4 — Polish

Everything below is opportunistic. None blocks ratification, but
shipping any of these requires no follow-on schema changes.

### Deliverables — Nice

- [ ] **Dark mode (FD).** `data-theme="dark"` toggle, persisted
      per user.
- [ ] **Styleguide preset themes.** Four presets from
      [ADR 056](../../../adr/056-style-guide-page.md) wired up,
      visible only on `/styleguide`.
- [ ] **Resend webhook** for delivery / bounce events (if Resend
      adds it within v2.0 timeline).
- [ ] **Custom favicon + wordmark refresh.** Designed mark
      replaces the placeholder.

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
- [ ] CSP header configured on every HTML response (no `unsafe-
      inline` for scripts; nonce-based).

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
