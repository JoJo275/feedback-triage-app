# SignalNest — Spec v2.0 (Ratified)

> **Status:** Ratified 2026-05-04. Authoritative for all v2.0 work.
> **Predecessor:** [`spec-v1.md`](spec-v1.md). v1.0 remains the
> contract for the running v1.0 codebase; this document is the
> contract for everything built under the v2.0 phases.
>
> **Reading order:** read `spec-v1.md` first for the platform
> contract. This document captures *changes* and *additions* on top
> of v1.0. Anything not contradicted in v2.0 inherits from v1.0
> unchanged.
>
> **Companion docs:** brand and visual brief live in
> [`v2/core-idea.md`](v2/core-idea.md). Topical detail (schema, API,
> auth, multi-tenancy, UI, email, security, rollout, tooling) lives
> in [`v2/`](v2/). This file is the entry point and tracks status,
> theme, headline changes, the feature catalog, ADRs to write, and
> deferrals.

---

## Status

| Field             | Value                                                            |
| ----------------- | ---------------------------------------------------------------- |
| Version           | 2.0                                                              |
| State             | **Ratified (2026-05-04)** — authoritative for v2.0 work          |
| Owner             | JoJo275                                                          |
| Last reviewed     | 2026-05                                                          |
| Ratification gate | Met: v1.0 Must items green; ADR 061 accepted; Phase 0 closed.    |

Follow-on tasks (not blocking — to be picked up alongside Phase 1):

- [`docs/index.md`](../../index.md) and
  [`README.md`](../../../README.md) updated to point at v2.0 as the
  active spec when Phase 1 lands its first PR.
- [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
  updated to reference v2.0 as the authoritative spec at the same
  time.

---

## Theme (one paragraph)

SignalNest is a calm, **multi-tenant** feedback-triage SaaS for
small product teams. v2.0 turns v1.0's single-resource CRUD into a
five-phase workflow — **Intake → Triage → Prioritize → Act → Close
the loop** — wrapped in a workspace-scoped product with email auth,
team invitations, public submission forms, public roadmaps and
changelogs, and an insights surface. Visually it ships as a light
SaaS dashboard (slate / white base, teal primary accent, amber
warning), built with Tailwind utility classes via the Standalone
CLI. Brand details and component shorthand live in
[`v2/core-idea.md`](v2/core-idea.md).

---

## Requirement Tiers

Same Must / Should / Nice / Defer system as v1.0. See
[`spec-v1.md` — Requirement Tiers](spec-v1.md#requirement-tiers).

---

## What Is Inherited from v1.0

Unless explicitly overridden, v2.0 inherits **everything** from v1.0:

- `feedback_item` table, native Postgres enums, CHECK constraints,
  the `BEFORE UPDATE` trigger maintaining `updated_at`.
- Request/response envelopes (`items`/`total`/`skip`/`limit`),
  ISO 8601 UTC datetimes with `Z` suffix.
- **Sync FastAPI routes** (`def`, not `async def`), per
  [ADR 050](../../adr/050-sync-db-driver-v1.md).
- Static-HTML + vanilla-JS frontend served from the same FastAPI
  process. Tailwind is added as the CSS layer per
  [ADR 058](../../adr/058-tailwind-via-standalone-cli.md); this is
  not a JS framework.
- Session-per-request DB lifecycle via `get_db`
  ([ADR 048](../../adr/048-session-per-request.md)).
- Postgres-backed pytest suite, gated Playwright smoke suite.
- Railway deploy, `alembic upgrade head` as the pre-deploy command.
- Container hardening posture (non-root, `HEALTHCHECK`, multi-stage).

---

## Headline Changes from v1.0

v2.0 makes three structural changes to the v1.0 contract:

1. **Authentication.** Every dashboard route requires a logged-in
   user. The public submission endpoint stays anonymous.
   Detail: [`v2/auth.md`](v2/auth.md). Decision:
   [ADR 059](../../adr/059-auth-model.md).
2. **Multi-tenancy.** Every tenant-scoped table gains
   `workspace_id`. Every dashboard URL is prefixed `/w/<slug>/`.
   Cross-tenant data leakage is the **#1 v2.0 risk**.
   Detail: [`v2/multi-tenancy.md`](v2/multi-tenancy.md). Decision:
   [ADR 060](../../adr/060-multi-tenancy-workspace-scoping.md).
3. **Workflow.** The single-resource CRUD becomes a five-phase
   triage flow with new tables, new feedback columns, and an
   extended status enum. Detail:
   [`v2/schema.md`](v2/schema.md), [`v2/api.md`](v2/api.md).

Everything else is additive — no v1.0 endpoint changes shape.

---

## Workflow

| Phase             | v2.0 surfaces                                                              |
| ----------------- | -------------------------------------------------------------------------- |
| Intake            | Public submission form (`/w/<slug>/submit`), authenticated `POST /api/v1/feedback`, mini demo on landing page |
| Triage            | Inbox page, status pills, filter bar, search                               |
| Prioritize        | Tags, priority enum, pain dots, internal notes                             |
| Act               | Roadmap page (Planned / In Progress columns), `published_to_roadmap` flag  |
| Close the loop    | Changelog page (Shipped items), `published_to_changelog` flag, status-change emails to known submitters |

A feature that doesn't slot into a phase doesn't ship in v2.0.

---

## Feature Catalog

Scored on **Portfolio value (PV-port)** × **Product value (PV-prod)**.
Tier is the v1.0 Must / Should / Nice axis. Build order matches the
[rollout plan](v2/rollout.md).

| #   | Feature                                       | PV-port | PV-prod | Tier   | Effort | Build order |
| --- | --------------------------------------------- | ------- | ------- | ------ | ------ | ----------- |
| F1  | User accounts + email auth                    | High    | High    | Must   | L      | 1 (alpha)   |
| F1b | Workspaces + invitations + memberships        | High    | High    | Must   | L      | 1 (alpha)   |
| F4  | Style guide page ([ADR 056](../../adr/056-style-guide-page.md)) | High | Medium | Should | S | 1 (alpha) |
| FT  | Tailwind adoption ([ADR 058](../../adr/058-tailwind-via-standalone-cli.md)) | High | Low | Must | S | 1 (alpha) |
| FU  | Public landing page                           | High    | Low     | Must   | S      | 1 (alpha)   |
| FX  | Inbox rebrand + extended status workflow      | High    | High    | Must   | M      | 2 (beta)    |
| F3a | Tags CRUD (in Settings)                       | Medium  | High    | Must   | S      | 2 (beta)    |
| F3b | Internal notes on feedback                    | Medium  | High    | Should | S      | 2 (beta)    |
| FS  | Submitters page + auto-link by email          | Medium  | High    | Should | M      | 2 (beta)    |
| FP  | Public submission form per workspace          | Medium  | High    | Must   | S      | 2 (beta)    |
| FW  | Settings page (workspace, members, tags)      | Medium  | High    | Must   | M      | 2 (beta)    |
| FY  | Dashboard summary cards + intake sparkline    | High    | Medium  | Should | S      | 3 (final)   |
| FR  | Roadmap page + publish flag                   | High    | Medium  | Should | M      | 3 (final)   |
| FC  | Changelog page + publish flag                 | High    | Medium  | Should | S      | 3 (final)   |
| FI  | Insights page (top tags, trends, pain heat)   | High    | Medium  | Nice   | M      | 3 (final)   |
| FE  | Status-change emails (Resend) — close-the-loop      | Medium  | High    | Must   | S      | 3 (final)   |
| FD  | Dark-mode toggle                              | Medium  | Low     | Nice   | S      | 3 (final)   |
| FU1 | Mini demo on landing (client-side, vanilla)   | High    | Low     | Should | S      | 3 (final)   |

Deferred (with rationale in [Future Improvements](#future-improvements-after-v20)):

- **F2** — React/Vite SPA rewrite. Redundant with FT + FX; XL
  effort, no workflow gain.
- Voting / severity / impact scoring.
- Bulk actions, side drawer, real-time updates.
- File attachments.

---

## Topical Detail (split files in [`v2/`](v2/))

**Brand & product:**

| File                                            | Topic                                                          |
| ----------------------------------------------- | -------------------------------------------------------------- |
| [`v2/core-idea.md`](v2/core-idea.md)            | Brand brief — locked strings, voice, surfaces                  |
| [`v2/business.md`](v2/business.md)              | Target user, value prop, pricing, growth, retention            |

**Architecture & contract:**

| File                                            | Topic                                                          |
| ----------------------------------------------- | -------------------------------------------------------------- |
| [`v2/schema.md`](v2/schema.md)                  | Full DDL: enums, auth tables, tenancy tables, workspace data, `feedback_item` changes |
| [`v2/api.md`](v2/api.md)                        | All endpoints + error envelope                                 |
| [`v2/auth.md`](v2/auth.md)                      | Auth state machine, sessions, tokens, password hashing, `FEATURE_AUTH` |
| [`v2/multi-tenancy.md`](v2/multi-tenancy.md)    | Workspace scoping, roles, `WorkspaceContext`                   |
| [`v2/repo-structure.md`](v2/repo-structure.md)  | Directory layout, module boundaries, naming                    |

**Frontend:**

| File                                            | Topic                                                          |
| ----------------------------------------------- | -------------------------------------------------------------- |
| [`v2/ui.md`](v2/ui.md)                          | Page routes, JS conventions, sidebar order, public submission, JS XSS contract |
| [`v2/pages.md`](v2/pages.md)                    | Per-page catalog: sections, components, copy strings, empty states |
| [`v2/css.md`](v2/css.md)                        | CSS conventions, design tokens, Tailwind config, component vocabulary |

**Cross-cutting:**

| File                                            | Topic                                                          |
| ----------------------------------------------- | -------------------------------------------------------------- |
| [`v2/email.md`](v2/email.md)                    | Resend integration, fail-soft semantics, templates             |
| [`v2/security.md`](v2/security.md)              | Cross-cutting security: rate limits, isolation invariants, CSP, CSRF |
| [`v2/risks.md`](v2/risks.md)                    | Risk register with severity scores and canaries                |
| [`v2/accessibility.md`](v2/accessibility.md)    | a11y floor + axe-core ruleset                                  |
| [`v2/error-catalog.md`](v2/error-catalog.md)    | Error envelope + canonical error codes                         |
| [`v2/observability.md`](v2/observability.md)    | Log fields, request-id, metrics                                |
| [`v2/performance-budgets.md`](v2/performance-budgets.md) | Latency, page weight, JS, cache TTLs                  |
| [`v2/testing-strategy.md`](v2/testing-strategy.md) | Unit / API / e2e matrix, canaries, fixtures                 |
| [`v2/copy-style-guide.md`](v2/copy-style-guide.md) | Locked strings, voice rules, error tone                     |

**Operations:**

| File                                            | Topic                                                          |
| ----------------------------------------------- | -------------------------------------------------------------- |
| [`v2/tooling.md`](v2/tooling.md)                | Backend / frontend / build / test stack                        |
| [`v2/rollout.md`](v2/rollout.md)                | Phased rollout, v1.0 → v2.0 cut-over, deployment, observability, cron |
| [`v2/migration-from-v1.md`](v2/migration-from-v1.md) | User-facing v1 → v2 cut-over notes                        |
| [`v2/railway-optimization.md`](v2/railway-optimization.md) | Railway cost & resource posture                       |
| [`v2/implementation.md`](v2/implementation.md)  | Phase 0–4 build plan with deliverables, DoD, verification     |
| [`v2/adrs.md`](v2/adrs.md)                      | Accepted ADRs and the TBD list with phase gates                |

**Reference:**

| File                                            | Topic                                                          |
| ----------------------------------------------- | -------------------------------------------------------------- |
| [`v2/glossary.md`](v2/glossary.md)              | Term definitions used across all v2 files                      |

---

## ADRs

Five are accepted; four are still to write. The TBD ADRs land in
the same PR as the code that needs them. The numbering scheme used
throughout v2 docs is **Phase 0–4** ([`v2/implementation.md`](v2/implementation.md));
*Alpha / Beta / Final / Polish* in [`v2/rollout.md`](v2/rollout.md)
and [`v2/adrs.md`](v2/adrs.md) are codename aliases for Phases 1–4
([`v2/glossary.md`](v2/glossary.md)).

| #   | Title                                                         | Status      | Phase gate       | Drives           |
| --- | ------------------------------------------------------------- | ----------- | ---------------- | ---------------- |
| 056 | Style guide page (`/styleguide`)                              | ✅ Accepted | 1 (Alpha)        | F4, all UI       |
| 057 | Brand vs. repo naming (SignalNest / `feedback-triage-app`)    | ✅ Accepted | 1 (Alpha)        | branding         |
| 058 | Tailwind via Standalone CLI                                   | ✅ Accepted | 1 (Alpha)        | FT, all UI work  |
| 059 | Auth model — cookie sessions + Argon2id                       | ✅ Accepted | 1 (Alpha)        | F1               |
| 060 | Multi-tenancy / workspace scoping                             | ✅ Accepted | 1 (Alpha)        | F1b              |
| 061 | Email provider (Resend) + fail-soft semantics                 | **Accepted** | **1 (Alpha)** — gates `email_log` DDL in Migration A | FE, F1, F1b |
| 062 | v1.0 → v2.0 data migration (legacy workspace + status rename) | TBD         | 2 (Beta)         | cut-over         |
| 063 | Status enum extension + `rejected` deprecation                | TBD         | 2 (Beta)         | FX               |
| 064 | Pain vs. Priority dual-field rationale                        | TBD         | 2 (Beta)         | FX               |

---

## Future Improvements After v2.0

Items considered and explicitly punted to v3.0+:

- **F2** — React/Vite/TS SPA rewrite. Redundant with FT + FX.
- **Voting / severity / impact** scoring on feedback.
- **Bulk actions, side drawer, keyboard navigation** on the inbox.
- **Real-time updates** (SSE or WebSockets).
- **File attachments** (object storage required).
- **AI clustering / summarization** of inbound feedback.
- **Customer-portal mode** — public-facing feature voting.
- **Multi-workspace per user** (schema already supports it; v2.0
  enforces 1:1 in application logic only).
- **Postgres Row-Level Security** as defense-in-depth on top of
  query-layer scoping (see
  [ADR 060](../../adr/060-multi-tenancy-workspace-scoping.md)).
- **Background email retry queue** with a separate worker.
- **`pg_trgm` GIN-indexed search** on feedback descriptions.
- **Audit log** of all writes per workspace.
- **Billing & paid tiers.**
- **Status-change Slack/Discord webhooks.**
- **API tokens** for programmatic submission from external systems.
- **CSRF token** if a public API key surface or third-party embed is
  ever added (not needed for the v2.0 same-origin SameSite=Lax model).
- **Captcha (hCaptcha)** if honeypot + rate limits prove
  insufficient against public-form abuse.
- **Sentry / Better-Stack** for hosted error tracking.

---

## Related Docs

- [`spec-v1.md`](spec-v1.md) — shipped v1.0 spec (canonical until
  v2.0 ratifies)
- [`v2/core-idea.md`](v2/core-idea.md) — SignalNest brand and visual brief (canonical)
- [`v2/`](v2/) — topical detail files
- [`_archive/`](_archive/) — feedback / pushback / answers from the
  v2.0 design phase (read-only)
- [`../implementation.md`](../implementation.md) — phase plan, with
  v2.0 appendix
- [`../questions.md`](../questions.md) — open questions and decisions
- [`../../adr/`](../../adr/) — ADRs governing the platform
- [`../../notes/frontend-conventions.md`](../../notes/frontend-conventions.md)
