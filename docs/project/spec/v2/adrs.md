# v2.0 — ADRs to write

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Filing conventions: [`../../../adr/.instructions.md`](../../../adr/.instructions.md).

This file is the *to-do list of architectural decisions for v2.0*.
It tracks which ADRs are accepted, which are still TBD, and what
each TBD must answer before its corresponding phase can close.

When an ADR ships, **delete its row from the TBD section here** and
move it to the Accepted section. Don't leave stale entries.

---

## Accepted (already merged)

| #   | Title                                       | Phase enabled    |
| --- | ------------------------------------------- | ---------------- |
| 056 | Style guide page (`/styleguide`)            | Alpha            |
| 057 | Brand vs. repo naming (SignalNest / `feedback-triage-app`) | Alpha |
| 058 | Tailwind via Standalone CLI                 | Alpha            |
| 059 | Auth model — cookie sessions + Argon2id     | Alpha            |
| 060 | Multi-tenancy / workspace scoping           | Alpha            |

---

## TBD (must land alongside or before their phase)

Order is intentional: each ADR below depends only on the ones
above it.

### ADR 061 — Email provider (Resend) + fail-soft semantics

**Phase gate:** Alpha. Anything that sends an email (verify
account, password reset, accept invitation) blocks on this.

Must answer:

- Why Resend over Postmark / SendGrid / SMTP-direct (cost,
  deliverability, simplicity).
- Failure modes — what happens when Resend returns 5xx, 429,
  network timeout. The product contract is **"the user-facing
  action succeeds; the email is best-effort logged."**
- The `email_log` table shape (status, error code, retried).
- Test strategy — `RESEND_DRY_RUN=1` short-circuits the HTTP call
  in unit / integration tests.
- Secret management — `RESEND_API_KEY` is a Railway secret; never
  in git, never in logs.
- Templates — plain text first, optional minimal HTML; templates
  live at `src/feedback_triage/email/templates/`.
- Out of scope for v2.0 — webhook ingest, suppression list,
  unsubscribe link (not legally required for transactional mail in
  the project's jurisdictions; revisit before any marketing
  email).

Drives: F1, F1b, FE.
Companion file: [`email.md`](email.md).

### ADR 062 — v1.0 → v2.0 data migration

**Phase gate:** Beta. The `NOT NULL workspace_id` migration cannot
ship until this is decided.

Must answer:

- The migration path: create one `signalnest-legacy` workspace +
  one synthetic owner user, backfill every existing
  `feedback_item.workspace_id` to it, **then** flip `NOT NULL`.
- The backfill is one Alembic revision; it is split from the
  schema-only revision so a deploy that fails halfway can roll
  forward.
- Status-enum migration: rename `rejected → closed` via data
  migration before the new enum value is committed (Postgres
  enum-rename is awkward; the path is `ALTER TYPE ... ADD VALUE`
  for the new states + `UPDATE … SET status = 'closed' WHERE
  status = 'rejected'`).
- Decision on *whether to drop the legacy `rejected` value*. ADR
  063 covers the actual `ALTER TYPE`; this ADR covers the
  data-migration choreography.

Drives: cut-over.
Companion file: [`rollout.md`](rollout.md).

### ADR 063 — Status enum extension + `rejected` deprecation

**Phase gate:** Beta. Cannot ship the inbox until status enum is
final.

Must answer:

- The exact final set: `new`, `needs_info`, `reviewing`,
  `accepted`, `planned`, `in_progress`, `shipped`, `closed`,
  `spam`.
- Whether `rejected` is removed from the enum or kept as an alias.
  Recommendation: remove. PG does not support `DROP VALUE`; the
  practical path is "stop emitting `rejected`" plus a `CHECK`
  preventing it; the enum value itself stays in the type
  definition forever.
- Lifecycle diagram (which transitions are allowed, which are
  not). E.g. `spam` is terminal; `closed` is reversible.
- UI mapping — the colors / icons / labels per status, mirrored
  from [`core-idea.md`](core-idea.md#status-workflow).

Drives: FX.

### ADR 064 — Pain vs. priority — dual fields rationale

**Phase gate:** Beta. Lock the choice before UI is built.

Must answer:

- Why two fields, not one. Submitter-set pain (1–5) is data;
  team-set priority (Low / Medium / High / Critical) is decision.
  Collapsing them creates either a popularity contest or a
  customer-blame problem.
- Why pain stays 1–5 and not a freeform integer or a slider.
- Why priority is an enum and not a numeric score.
- UI implications already captured in
  [`core-idea.md`](core-idea.md#pain-level-vs-priority) and
  [`pages.md`](pages.md#feedback-detail).

Drives: FX, dashboard, insights.

---

## Recommended ADRs (file when relevant)

These are not v2.0 ratification gates, but each one is a real
decision that someone will eventually rediscover the hard way if
not written down.

| #   | Title (proposed)                                              | When                                    |
| --- | ------------------------------------------------------------- | --------------------------------------- |
| 065 | Rate-limit posture — public submission form                   | Before the public form ships (Beta).    |
| 066 | Content limits — feedback description / note length, image upload posture | Before the public form ships.   |
| 067 | CSP / security headers configuration                          | Before public launch.                   |
| 068 | Cookie + session lifetime tuning + rolling renewal policy     | After Resend (Final), before launch.    |
| 069 | Inline-SVG charting — when (if ever) to swap for a library    | Before any v3 chart ask.                |
| 070 | Background-job posture (cron vs. queue) for stale-item / cleanup | Before scheduled work lands.         |
| 071 | Audit log surface — what writes to log, what reads it         | Before paid tier.                       |
| 072 | Public-roadmap caching strategy                                | Before any "real" external traffic.    |
| 073 | Domain handling — workspace-on-subpath vs. custom domains     | Before paid tier.                       |
| 074 | Privacy & data-retention policy                                | Before public launch.                   |
| 075 | Demo-workspace reset job                                      | Before demo user goes live (Final).     |

---

## Authoring rules (reminder)

- One ADR per decision. If a single PR introduces two unrelated
  decisions, file two ADRs.
- ADRs are immutable once Accepted. Supersession is a new ADR that
  links back.
- Prefer **decided** over **comprehensive**. An ADR is the
  smallest writeup that lets a future reader avoid re-relitigating.
- Cross-link the relevant spec file ([`schema.md`](schema.md),
  [`api.md`](api.md), [`auth.md`](auth.md), …) so the ADR doesn't
  re-state what the spec already says.

---

## Cross-references

- [`../../../adr/.instructions.md`](../../../adr/.instructions.md) — ADR creation procedure.
- [`implementation.md`](implementation.md) — phase plan referencing these IDs.
- [`../spec-v2.md`](../spec-v2.md) — ADRs table (the canonical
  short version).
