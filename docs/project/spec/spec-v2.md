# Feedback Triage App — Spec v2.0 (Draft)

> **Status:** Draft. Not yet authoritative.
> **Predecessor:** [`spec-v1.md`](spec-v1.md) — shipped v1.0 scope (single
> `feedback_item` resource, no auth, sync DB driver, Railway deploy).
> **Goal of v2.0:** capture the next batch of features layered on top of
> the v1.0 baseline. Until this document lands at "Ratified" below,
> `spec-v1.md` remains the single source of truth.
>
> **Reading order:** read `spec-v1.md` first for the platform contract
> (schema, request envelope, validation rules, deploy model). This file
> only documents *changes* and *additions*. Anything not contradicted
> here inherits from v1.0 unchanged.
>
> **Reviewer feedback:** see [`spec-v2-feedback.md`](spec-v2-feedback.md)
> for open critiques and decisions the author still needs to make. Fold
> answers into this file, then delete the feedback doc.

---

## Status

| Field             | Value                                                            |
| ----------------- | ---------------------------------------------------------------- |
| Version           | 2.0                                                              |
| State             | Draft (not ratified)                                             |
| Owner             | TBD                                                              |
| Last reviewed     | TBD                                                              |
| Ratification gate | All v1.0 Must items green + this section flipped to "Ratified"   |

When this document is ratified, update:

- The **Status** row above to `Ratified`.
- [`docs/index.md`](../../index.md) and [`README.md`](../../../README.md)
  to point at v2.0 as the active spec.
- [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
  to reference v2.0 as the authoritative spec.

---

## Requirement Tiers

Same Must / Should / Nice / Defer system as v1.0. See
[`spec-v1.md` — Requirement Tiers](spec-v1.md#requirement-tiers) for the
definitions.

---

## What Is Inherited from v1.0

Unless explicitly overridden in this document, v2.0 inherits **everything**
from v1.0, including:

- `feedback_item` table, native Postgres enums, CHECK constraints, and
  the `BEFORE UPDATE` trigger maintaining `updated_at`.
- Request/response envelopes (`items`/`total`/`skip`/`limit` for lists),
  ISO 8601 UTC datetimes with `Z` suffix.
- Sync FastAPI routes (`def`, not `async def`). **Note:** the draft
  package list below includes `asyncpg`; that conflicts with v1.0 ADR 050
  ("Sync DB driver in v1.0"). See feedback doc item #4.
- Static-HTML + vanilla-JS frontend served from the same FastAPI process.
  **Note:** the draft below proposes replacing this with React/Vite. See
  feedback doc item #2 — that needs an ADR.
- Session-per-request DB lifecycle via `get_db`.
- Postgres-backed pytest suite, gated Playwright smoke suite.
- Railway deploy via GitHub source, `alembic upgrade head` as the
  pre-deploy command.
- Container hardening posture (non-root, `HEALTHCHECK`, multi-stage).

If a v2.0 feature requires changing one of these, document the change
explicitly in the relevant section below and add an ADR.

---

## Out of Scope (Inherited from v1.0)

Unless lifted in this document, the v1.0 deferrals continue to apply.
See [`spec-v1.md` — Future Improvements After v1.0](spec-v1.md#future-improvements-after-v10)
for the full list.

---

## v2.0 Theme

> _One-paragraph summary of what v2.0 is **for**. Examples: "Make the
> tool usable for a small team — add accounts, multi-user feedback
> ownership, and basic auditing." Or: "Improve triage UX — add labels,
> bulk actions, and full-text search." Without a stated theme, scope
> creep is guaranteed._

**Working draft (needs author confirmation):** Make the app usable for
a small multi-user team by adding email-based accounts, per-user
feedback ownership, and a richer triage workflow (notes, tags, statuses).
Stretch goal: a more polished, dashboard-style UI. See feedback doc
item #1 — the Theme has to land before any feature work starts.

---

## Proposed Features

For each feature, capture: **tier**, **why now**, **schema impact**,
**API surface**, **UI surface**, **test impact**, **migration plan**,
and **rollout / rollback notes**. Use the v1.0 spec's section style as
the model.

The draft features below are **sketches**. Each needs to be fleshed out
to v1.0-spec rigor before this document ratifies.

### Feature 1: User accounts and email-based authentication

- **Tier:** Should (core to the v2.0 Theme)
- **Why now:** v1.0 has no concept of a user; every feedback item is
  anonymous and editable by anyone. Multi-user use requires accounts.
- **Schema impact:** new `users`, `email_verification_tokens`,
  `password_reset_tokens` tables. New `feedback.user_id` FK. Migration
  of existing rows (see feedback doc item #7).
- **API surface:** `/api/v1/auth/signup`, `/auth/login`, `/auth/logout`,
  `/auth/verify-email`, `/auth/forgot-password`, `/auth/reset-password`,
  `/auth/me`. Detailed contracts TBD.
- **UI surface:** signup, login, password-reset request, password-reset
  confirm, "verify your email" landing page.
- **Tests:** unit + API tests for the auth state machine; Playwright
  smoke for signup → verify → login → logout.
- **Migration plan:** see feedback doc item #7. Backfill vs. cut-over
  vs. nullable `user_id` is unresolved.
- **Rollout:** TBD. Likely needs a feature flag so the auth layer can
  ship behind a redirect before the UI lands.

### Feature 2: Frontend rewrite (React + Vite + TypeScript + Tailwind)

- **Tier:** TBD — **needs an ADR before being committed to v2.0.**
- **Why now:** the author wants a "polished product-style dashboard"
  beyond what static HTML + vanilla JS supports. Counter-argument in
  feedback doc item #2: auth doesn't require this rewrite, and a
  rewrite is a v3.0-sized effort.
- **Schema impact:** none.
- **API surface:** none directly, but the SPA shell lives under
  `/app/*` served from the FastAPI process via `StaticFiles`.
- **UI surface:** complete replacement of `index.html`, `new.html`,
  `detail.html`. New SPA shell.
- **Tests:** add Vitest + React Testing Library; rewrite Playwright
  smoke against new selectors.
- **Migration plan:** dual-serve old static HTML and new React build
  during cutover; remove old HTML after smoke is green.
- **Rollout:** TBD.

### Feature 3: Triage extensions — notes, tags, statuses

- **Tier:** Nice (depends on Theme — see feedback doc item #8)
- **Why now:** triagers want to annotate feedback ("worked around in
  v1.2") and group it ("UX bugs").
- **Schema impact:** new `feedback_notes`, `feedback_tags`,
  `feedback_statuses`, `feedback_types` tables (or columns on
  `feedback_item` if cardinality is low). Decision pending.
- **API surface:** nested resources under
  `/api/v1/feedback/{id}/notes`, `/tags`. List endpoints take new
  filter params.
- **UI surface:** detail page gains a notes panel and tag chips;
  list page gains tag filters.
- **Tests:** API + Playwright.
- **Migration plan:** purely additive; no v1.0 data churn.
- **Rollout:** straightforward after Feature 1.

### Feature 4: Style guide page with theme demos

- **Tier:** Should (portfolio surface; doubles as a regression check
  for token edits)
- **Why now:** as the component surface grows (auth pages, triage
  extensions), there is no single page that exhibits every component
  in every state. Reviewing each real page for token regressions is
  slow and easy to miss states (focus, disabled, error). The page also
  serves as a portfolio showcase: a reviewer landing on the repo gets
  one URL that demonstrates the whole design system.
- **Decision:** see [ADR 056](../../adr/056-style-guide-page.md).
- **Schema impact:** none.
- **API surface:** none.
- **UI surface:** new static route `GET /styleguide` exhibiting every
  component used by the app, with a four-way theme selector
  (`production` | `basic` | `unique` | `crazy`). The `production`
  theme is the default and is the same theme rendered everywhere
  else; the alternate themes are scoped to
  `html[data-theme="…"] body.styleguide-page` so they cannot leak
  into the live app. Theme tokens live in a separate `themes.css`
  loaded **only** on `/styleguide`. Selection persists to
  `localStorage`.
- **Tests:** one gated `@pytest.mark.e2e` Playwright smoke that loads
  the page and cycles all four themes.
- **Migration plan:** purely additive; no schema or API churn.
- **Rollout:** ship in v2.0-alpha alongside the auth backend; the page
  has no auth requirement.

---

## Naming: SignalNest vs. feedback-triage-app

The product is called **SignalNest** (custom domain `signalnest.app`,
visible in every `<title>`, `<h1>`, the README header, and
`mkdocs.yml`). The repository slug stays `feedback-triage-app` and the
Python package stays `feedback_triage`.

This split is intentional and is captured in
[ADR 057](../../adr/057-brand-vs-repo-naming.md). Short version:
renaming only the repo leaves the package name behind and makes the
inconsistency worse, not better; renaming both is a v3.0-sized
migration that's not worth doing mid-development of v2.0. A future
rename remains possible but must align repo + package + brand at once,
captured as its own ADR superseding 057.

User-facing copy says **SignalNest**. Engineering docs (ADRs, repo
layout, CI configuration, container labels) keep
**feedback-triage-app**. The README header documents both so the
relationship is visible immediately.

---

## Schema Changes

> Diff from v1.0. Tables added, columns added/changed, new enums, new
> indexes, new triggers. Every change requires a hand-reviewed Alembic
> migration.

**Sketch only — full DDL pending. See feedback doc item #6.**

| Table                         | Purpose                                                |
| ----------------------------- | ------------------------------------------------------ |
| `users`                       | Account records (email, password hash, verified flag) |
| `email_verification_tokens`   | Hashed tokens for new-account confirmation             |
| `password_reset_tokens`       | Hashed, single-use, expiring reset tokens              |
| `feedback_notes`              | Internal notes/comments on a feedback item             |
| `feedback_tags`               | Tags / categories                                      |
| `feedback_statuses`           | Workflow statuses (extends v1.0 status enum?)          |
| `feedback_types`              | Bug, feature request, complaint, praise, etc.          |
| `feedback_votes`              | Optional later                                         |
| `audit_logs`                  | Optional later                                         |

For tokens: store **a hash of the token, never the raw token** (matches
v1.0 security posture).

**Open questions:**

- `feedback.user_id` migration strategy (backfill vs. nullable vs.
  cut-over). See feedback doc item #7.
- Whether `feedback_statuses` replaces the v1.0 native `status_enum`
  or coexists with it. v1.0 enforces statuses at the DB; a lookup
  table loses that. See feedback doc item #6.

---

## API Changes

> Diff from v1.0. New endpoints, breaking changes (avoid; if needed,
> introduce `/api/v2/`), modified envelopes.

**Sketch only — endpoint contracts pending.**

- New auth endpoints under `/api/v1/auth/*` (Feature 1).
- New nested resources under `/api/v1/feedback/{id}/notes` and
  `/api/v1/feedback/{id}/tags` (Feature 3).
- `GET /api/v1/feedback` gains `tag`, `type`, `assigned_to` filter
  params.
- `POST /api/v1/feedback` gains an implicit `user_id` from the session.
- No breaking changes to existing v1.0 envelopes; `/api/v2/` is **not**
  introduced for v2.0.

---

## UI Changes

> Diff from v1.0. New pages, new components, behavior changes. Every
> UI change touches the Playwright smoke suite.

**Sketch only — pending Feature 2 ADR.**

If the React rewrite ships:

- New SPA under `/app/*` served from FastAPI `StaticFiles`. Client-side
  router (React Router) handles `/app/inbox`, `/app/feedback/:id`,
  `/app/settings`, `/app/auth/login`, etc.
- The SPA's `index.html` is the fallback for any `/app/*` 404 from the
  server (standard SPA-fallback rule).
- Existing `/`, `/new`, `/feedback/{id}` routes remain for one release,
  then redirect to the SPA equivalents.

If the rewrite is deferred (recommended in feedback doc item #2):

- Two new vanilla-JS pages: `/auth/login`, `/auth/signup`.
- Existing pages gain a header strip showing the logged-in user and a
  logout link.

---

## Migration & Rollout Plan

> How v2.0 ships. Single big-bang release? Phased rollout? Feature
> flags? Backwards compatibility window for the API?

**Proposed phased rollout:**

1. **v2.0-alpha:** auth backend (Feature 1) ships behind a
   `FEATURE_AUTH=false` env flag. Schema migrations run; new endpoints
   exist but the UI is unchanged.
2. **v2.0-beta:** UI for auth ships (login/signup pages or React SPA
   per Feature 2 decision). `FEATURE_AUTH=true` in production.
3. **v2.0:** triage extensions (Feature 3) ship.

**Backwards compatibility:** v1.0 API remains under `/api/v1/`. v2.0 is
additive — no existing endpoints change shape.

---

## Tooling Stack (Proposed)

> Lifted from the original draft. Treat as a **starting point**; each
> non-v1.0 entry needs author confirmation against the feedback doc
> before it's committed.

### Backend

| Item                          | Status vs. v1.0  | Notes                                                                |
| ----------------------------- | ---------------- | -------------------------------------------------------------------- |
| FastAPI                       | ✅ same           | —                                                                    |
| Uvicorn                       | ✅ same           | —                                                                    |
| SQLAlchemy 2.0                | ✅ same           | (already used via SQLModel)                                          |
| Alembic                       | ✅ same           | —                                                                    |
| Pydantic v2                   | ✅ same           | —                                                                    |
| `pydantic-settings`           | ✅ already used   | —                                                                    |
| `passlib[argon2]` or `pwdlib` | 🆕 new            | For password hashing.                                                |
| `python-jose` or `pyjwt`      | 🆕 new            | Only if JWT chosen over cookie sessions. See feedback #5.            |
| `resend`                      | 🆕 new            | Transactional email. See feedback #3 for failure-mode discussion.    |
| `httpx`                       | ✅ test-only       | Already used in test suite.                                          |
| `asyncpg`                     | ⚠ **conflicts**  | v1.0 is sync (ADR 050). See feedback #4.                              |
| `fastapi-users`               | 🆕 optional       | Saves time vs. building auth manually. Decision pending.             |

### Frontend (only if Feature 2 ADR approves the rewrite)

| Item                              | Notes                                                           |
| --------------------------------- | --------------------------------------------------------------- |
| React + Vite                      | Static-build deployment served by FastAPI.                      |
| TypeScript                        | —                                                               |
| Tailwind CSS                      | Replaces v1.0's hand-written CSS tokens.                        |
| React Router                      | Client-side routing under `/app/*`.                             |
| TanStack Query                    | API data fetching/caching.                                      |
| React Hook Form                   | Form state.                                                     |
| Zod + `@hookform/resolvers`       | Frontend validation. See feedback #14 — codegen from OpenAPI is a better choice. |
| Vitest + React Testing Library    | Component tests. See feedback #13.                              |
| `lucide-react`                    | Icons.                                                          |
| shadcn/ui (later)                 | Component library; defer until core works.                      |

### Email + Auth

| Feature                 | Implementation                                                                                |
| ----------------------- | --------------------------------------------------------------------------------------------- |
| Signup                  | FastAPI endpoint + UI form. User created with `is_verified=false`.                            |
| Email confirmation      | Resend email with hashed verification token; expiring link.                                   |
| Password reset          | "Forgot password" endpoint + reset email; single-use token.                                   |
| Login                   | HTTP-only secure cookie session **or** JWT — pick one (see feedback #5).                      |
| Logout                  | Server clears session row / invalidates cookie.                                               |
| Protected pages         | Frontend checks `/api/v1/auth/me`; redirect on 401.                                           |
| Email templates         | Plain HTML or React Email. Keep simple at first.                                              |
| Rate limiting           | DB / IP throttling first; defer Redis. See feedback #5.                                       |
| Token storage           | Postgres rows; raw token never persisted.                                                     |
| Background email jobs   | None. Send synchronously inside the request. See feedback #9 — couples p95 to Resend's p95.   |

### Email-provider comparison

> **Pricing claims dated May 2026.** Re-verify before committing.
> See feedback doc item #11.

| Provider                 | Small-use pricing (May 2026)                                                                                  | Verdict                                              |
| ------------------------ | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Resend                   | Free plan: 3,000 emails/month. Pro from $20/mo for 50,000 emails/mo.                                          | Best DX. Recommended first choice.                   |
| Mailgun                  | Free: 100 messages/day, 1 custom domain, 1 day logs.                                                          | Mature. UX feels sales-heavy.                        |
| Amazon SES               | $0.10 per 1,000 outbound emails. SES free tier: up to 3,000 message charges/month for 12 months.              | Cheapest long-term; AWS setup is annoying.           |
| SendGrid / Twilio Email  | 60-day free trial, 100 emails/day. Essentials from $19.95/month.                                              | Skip for cost-sensitive demo.                        |

### Expected volume

| Scenario                                       | Emails/month  | Likely cost          |
| ---------------------------------------------- | ------------- | -------------------- |
| 20 users sign up, 5 reset passwords            | ~25–50        | $0                   |
| 100 users sign up, 20 reset passwords          | ~120–250      | $0                   |
| 1,000 users sign up, 200 reset passwords       | ~1.2k–2.5k    | $0 (free tier)       |
| 10,000+ active users                           | 10k+          | Paid tier required   |

---

## Deployment

Lowest-cost setup (matches v1.0 spirit — single FastAPI service):

```text
Railway Project
├── Service 1: FastAPI app
│   ├── Serves /api/v1/*
│   ├── Serves built React static files (if Feature 2 approved)
│   └── Sends email through Resend API
└── Service 2: PostgreSQL database
```

Explicitly **not** introduced for v2.0:

- Separate frontend Railway service.
- Redis.
- Celery / background worker.
- WebSockets.
- AI / LLM features.

Each of those is its own ADR if it ever ships.

---

## ADRs to Write for v2.0

> Numbered from the next free slot in [`docs/adr/`](../../adr/).

| # (proposed) | Title                                                                | Resolves          |
| ------------ | -------------------------------------------------------------------- | ----------------- |
| TBD          | Auth model: cookie session vs. JWT                                   | Feedback #5       |
| TBD          | Frontend stack: React rewrite vs. extend static HTML                 | Feedback #2       |
| TBD          | DB driver: stay sync or move to async (`asyncpg` + `AsyncSession`)   | Feedback #4       |
| TBD          | Email provider: Resend (primary), failure-mode and SLA expectations  | Feedback #3       |
| TBD          | `feedback_item.user_id` migration strategy                           | Feedback #7       |
| TBD          | Type generation: OpenAPI → TypeScript vs. hand-written Zod schemas   | Feedback #14      |

---

## Future Improvements After v2.0

> Items considered and explicitly punted to v3.0+.

- WebSockets / live updates.
- AI summarization or clustering of feedback.
- File attachments on feedback items.
- Public voting / customer-portal mode.
- Multi-tenant (organizations / workspaces).
- Audit log (if not shipped in v2.0).

---

## Related Docs

- [`spec-v1.md`](spec-v1.md) — shipped v1.0 spec (canonical until v2.0 ratifies)
- [`spec-v2-feedback.md`](spec-v2-feedback.md) — open critiques and unresolved decisions
- [`../implementation.md`](../implementation.md) — phase plan; needs a v2.0 phase appendix
- [`../questions.md`](../questions.md) — open questions and decisions
- [`../../adr/`](../../adr/) — ADRs governing the platform
