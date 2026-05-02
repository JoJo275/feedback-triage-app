# SignalNest — Spec v2.0 (Draft)

> **Status:** Draft. Not yet authoritative.
> **Predecessor:** [`spec-v1.md`](spec-v1.md) — shipped v1.0 scope
> (single `feedback_item` resource, no auth, sync DB driver, Railway
> deploy). Until this document lands at "Ratified" below, `spec-v1.md`
> remains the single source of truth.
>
> **Reading order:** read `spec-v1.md` first for the platform contract
> (request envelope, validation rules, deploy model). This file
> documents *changes* and *additions* on top of v1.0. Anything not
> contradicted here inherits from v1.0 unchanged.
>
> **Companion brief:** [`core-idea.md`](core-idea.md) holds the brand
> + visual theme; this file holds the technical contract.

---

## Status

| Field             | Value                                                            |
| ----------------- | ---------------------------------------------------------------- |
| Version           | 2.0                                                              |
| State             | Draft (not ratified)                                             |
| Owner             | JoJo275                                                          |
| Last reviewed     | 2026-04                                                          |
| Ratification gate | All v1.0 Must items green + this section flipped to "Ratified"   |

When ratified, update:

- The **Status** row above to `Ratified`.
- [`docs/index.md`](../../index.md) and [`README.md`](../../../README.md)
  to point at v2.0 as the active spec.
- [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
  to reference v2.0 as the authoritative spec.

---

## Theme (one-paragraph summary)

SignalNest is a calm, **multi-tenant** feedback-triage SaaS for
small product teams. v2.0 turns v1.0's single-resource CRUD into a
five-phase workflow — **Intake → Triage → Prioritize → Act → Close
the loop** — wrapped in a workspace-scoped product with email auth,
team invitations, public submission forms, public roadmaps and
changelogs, and an insights surface. Visually it ships as a light
SaaS dashboard (slate / white base, teal primary accent, amber
warning), built with Tailwind utility classes via the Standalone CLI.
Brand details and component shorthand live in
[`core-idea.md`](core-idea.md).

---

## Requirement Tiers

Same Must / Should / Nice / Defer system as v1.0. See
[`spec-v1.md` — Requirement Tiers](spec-v1.md#requirement-tiers).

---

## What Is Inherited from v1.0

Unless explicitly overridden in this document, v2.0 inherits
**everything** from v1.0:

- `feedback_item` table, native Postgres enums, CHECK constraints,
  the `BEFORE UPDATE` trigger maintaining `updated_at`.
- Request/response envelopes (`items`/`total`/`skip`/`limit` for
  lists), ISO 8601 UTC datetimes with `Z` suffix.
- **Sync FastAPI routes** (`def`, not `async def`). v2.0 stays sync
  per [ADR 050](../../adr/050-sync-db-driver-v1.md). The earlier
  draft list of `asyncpg` is dropped.
- Static-HTML + vanilla-JS frontend served from the same FastAPI
  process (no SPA, no React, no bundler). Tailwind is added as the
  CSS layer per [ADR 058](../../adr/058-tailwind-via-standalone-cli.md);
  this is **not** a JS framework.
- Session-per-request DB lifecycle via `get_db`
  ([ADR 048](../../adr/048-session-per-request.md)).
- Postgres-backed pytest suite, gated Playwright smoke suite.
- Railway deploy via GitHub source, `alembic upgrade head` as the
  pre-deploy command.
- Container hardening posture (non-root, `HEALTHCHECK`, multi-stage).

---

## What Changes from v1.0 (Headline)

v2.0 makes three structural changes to the v1.0 contract:

1. **Authentication.** Every dashboard route requires a logged-in
   user ([ADR 059](../../adr/059-auth-model.md)). The public
   submission endpoint stays anonymous.
2. **Multi-tenancy.** Every tenant-scoped table gains
   `workspace_id`. Every dashboard URL is prefixed `/w/<slug>/`.
   Cross-tenant data leakage is the #1 v2.0 risk
   ([ADR 060](../../adr/060-multi-tenancy-workspace-scoping.md)).
3. **Workflow.** The single-resource CRUD becomes a five-phase
   triage flow with new tables (`tags`, `submitters`,
   `feedback_notes`), new feedback columns (`priority`, `type`,
   `source_other`, `type_other`, `submitter_id`,
   `published_to_roadmap`, `published_to_changelog`,
   `target_release`), and an extended status enum.

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

## Roles & Multi-tenancy

Authoritative role mechanics: [ADR 059](../../adr/059-auth-model.md)
and [ADR 060](../../adr/060-multi-tenancy-workspace-scoping.md). The
human-facing role table lives in
[`core-idea.md` — Roles](core-idea.md#roles). Schema is in
[Schema Changes](#schema-changes) below.

Workspace addressing:

- Dashboard routes: `/w/<workspace_slug>/<page>`.
- API routes: `/api/v1/<resource>`, with the active workspace
  resolved from the `X-Workspace-Slug` header (set by every
  dashboard fetch call) or from the URL prefix on public routes.
- Public submission: `/api/v1/w/<slug>/feedback` (POST, anonymous).

---

## Feature Catalog

Scored on **Portfolio value (PV-port)** × **Product value (PV-prod)**.
Tier is the v1.0 Must / Should / Nice axis. Build order matches the
[Migration & Rollout Plan](#migration--rollout-plan).

| #   | Feature                                       | PV-port | PV-prod | Tier   | Effort | Build order |
| --- | --------------------------------------------- | ------- | ------- | ------ | ------ | ----------- |
| F1  | User accounts + email auth                    | High    | High    | Must   | L      | 1 (alpha)   |
| F1b | Workspaces + invitations + memberships        | High    | High    | Must   | L      | 1 (alpha)   |
| F4  | Style guide page (ADR 056)                    | High    | Medium  | Should | S      | 1 (alpha)   |
| FT  | Tailwind adoption + token system (ADR 058)    | High    | Low     | Must   | S      | 1 (alpha)   |
| FX  | Inbox rebrand + extended status workflow      | High    | High    | Must   | M      | 2 (beta)    |
| F3a | Tags CRUD (in Settings)                       | Medium  | High    | Must   | S      | 2 (beta)    |
| F3b | Internal notes on feedback                    | Medium  | High    | Should | S      | 2 (beta)    |
| FS  | Submitters page + auto-link by email          | Medium  | High    | Should | M      | 2 (beta)    |
| FP  | Public submission form per workspace          | Medium  | High    | Must   | S      | 2 (beta)    |
| FY  | Dashboard summary cards + intake sparkline    | High    | Medium  | Should | S      | 3 (final)   |
| FR  | Roadmap page + publish flag                   | High    | Medium  | Should | M      | 3 (final)   |
| FC  | Changelog page + publish flag                 | High    | Medium  | Should | S      | 3 (final)   |
| FI  | Insights page (top tags, trends, pain heat)   | High    | Medium  | Nice   | M      | 3 (final)   |
| FE  | Status-change emails (Resend)                 | Medium  | Medium  | Nice   | S      | 3 (final)   |
| FW  | Settings page (workspace, members, tags)      | Medium  | High    | Must   | M      | 2 (beta)    |
| FU  | Public landing page                           | High    | Low     | Must   | S      | 1 (alpha)   |
| FU1 | Mini demo on landing (client-side, vanilla)   | High    | Low     | Should | S      | 3 (final)   |
| FD  | Dark-mode toggle                              | Medium  | Low     | Nice   | S      | 3 (final)   |

Deferred (with rationale in [Future Improvements](#future-improvements-after-v20)):

- F2 — React/Vite SPA rewrite. Redundant with FT + FX; XL effort, no
  workflow gain.
- Voting / severity / impact scoring.
- Bulk actions, side drawer, real-time updates.
- File attachments.

---

## Schema Changes

Every change is a hand-reviewed Alembic migration with `compare_type`
+ `compare_server_default` set. Native Postgres enums + DB CHECK
constraints (per [ADR 046](../../adr/046-native-pg-enums-and-checks.md))
remain mandatory. Citext is used for case-insensitive emails and
slugs (`CREATE EXTENSION IF NOT EXISTS citext` in the auth migration).

### New enums

```sql
CREATE TYPE user_role_enum AS ENUM ('admin', 'team_member', 'demo');
CREATE TYPE workspace_role_enum AS ENUM ('owner', 'team_member');

-- Extended status enum (replaces v1.0's enum via ALTER TYPE ADD VALUE).
-- v1.0 'rejected' rows are migrated to 'closed' in the same migration.
ALTER TYPE status_enum ADD VALUE 'needs_info';
ALTER TYPE status_enum ADD VALUE 'accepted';
ALTER TYPE status_enum ADD VALUE 'in_progress';
ALTER TYPE status_enum ADD VALUE 'shipped';
ALTER TYPE status_enum ADD VALUE 'closed';
ALTER TYPE status_enum ADD VALUE 'spam';
-- Then UPDATE feedback_item SET status='closed' WHERE status='rejected';
-- 'rejected' is left in the enum for one release for safety, then dropped
-- in v2.1's first migration.

-- Extended source enum.
ALTER TYPE source_enum ADD VALUE 'web_form';

CREATE TYPE type_enum AS ENUM (
    'bug', 'feature_request', 'complaint',
    'praise', 'question', 'other'
);

CREATE TYPE priority_enum AS ENUM ('low', 'medium', 'high', 'critical');
```

### New tables — auth & tenancy

```sql
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE users (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email           citext NOT NULL UNIQUE,
    password_hash   text   NOT NULL,
    is_verified     boolean NOT NULL DEFAULT false,
    role            user_role_enum NOT NULL DEFAULT 'team_member',
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workspaces (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        citext NOT NULL UNIQUE
                CHECK (slug ~ '^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$'),
    name        text NOT NULL CHECK (length(name) BETWEEN 1 AND 60),
    owner_id    uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    is_demo     boolean NOT NULL DEFAULT false,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workspace_memberships (
    workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role         workspace_role_enum NOT NULL,
    joined_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, user_id)
);

CREATE TABLE workspace_invitations (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    email         citext NOT NULL,
    role          workspace_role_enum NOT NULL DEFAULT 'team_member',
    token_hash    text NOT NULL UNIQUE,
    invited_by_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    expires_at    timestamptz NOT NULL,
    accepted_at   timestamptz NULL,
    revoked_at    timestamptz NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX workspace_invitations_open_idx
    ON workspace_invitations (workspace_id, email)
    WHERE accepted_at IS NULL AND revoked_at IS NULL;

CREATE TABLE sessions (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash   text NOT NULL,
    user_agent   text NULL,
    ip_inet      inet NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    expires_at   timestamptz NOT NULL,
    revoked_at   timestamptz NULL
);
CREATE INDEX sessions_token_hash_idx ON sessions (token_hash) WHERE revoked_at IS NULL;
CREATE INDEX sessions_user_id_idx    ON sessions (user_id)    WHERE revoked_at IS NULL;

CREATE TABLE email_verification_tokens (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  text NOT NULL UNIQUE,
    expires_at  timestamptz NOT NULL,
    consumed_at timestamptz NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE password_reset_tokens (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  text NOT NULL UNIQUE,
    expires_at  timestamptz NOT NULL,
    consumed_at timestamptz NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE auth_rate_limits (
    bucket_key   text NOT NULL,           -- e.g. 'login:alice@x.com', 'login:ip:1.2.3.4'
    window_start timestamptz NOT NULL,
    count        integer NOT NULL DEFAULT 0,
    PRIMARY KEY (bucket_key, window_start)
);
```

### New tables — workspace data

```sql
CREATE TABLE submitters (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    email         citext NULL,
    name          text NULL CHECK (length(name) <= 120),
    internal_notes text NULL CHECK (length(internal_notes) <= 4000),
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at  timestamptz NOT NULL DEFAULT now(),
    submission_count integer NOT NULL DEFAULT 0,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, email)
);
CREATE INDEX submitters_workspace_idx ON submitters (workspace_id);

CREATE TABLE tags (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name         text NOT NULL CHECK (length(name) BETWEEN 1 AND 40),
    slug         text NOT NULL CHECK (slug ~ '^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$'),
    color        text NOT NULL DEFAULT 'slate'
                 CHECK (color IN ('slate','teal','amber','rose','indigo','sky','green','violet')),
    created_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, slug)
);

CREATE TABLE feedback_tags (
    feedback_id uuid NOT NULL REFERENCES feedback_item(id) ON DELETE CASCADE,
    tag_id      uuid NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (feedback_id, tag_id)
);

CREATE TABLE feedback_notes (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    feedback_id    uuid NOT NULL REFERENCES feedback_item(id) ON DELETE CASCADE,
    author_user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    body           text NOT NULL CHECK (length(body) BETWEEN 1 AND 4000),
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX feedback_notes_feedback_idx ON feedback_notes (feedback_id, created_at DESC);
```

### Changes to `feedback_item`

```sql
ALTER TABLE feedback_item
    ADD COLUMN workspace_id uuid REFERENCES workspaces(id) ON DELETE CASCADE,
    ADD COLUMN submitter_id uuid REFERENCES submitters(id) ON DELETE SET NULL,
    ADD COLUMN type type_enum NOT NULL DEFAULT 'other',
    ADD COLUMN priority priority_enum NULL,
    ADD COLUMN source_other text NULL CHECK (length(source_other) <= 60),
    ADD COLUMN type_other   text NULL CHECK (length(type_other)   <= 60),
    ADD COLUMN published_to_roadmap   boolean NOT NULL DEFAULT false,
    ADD COLUMN published_to_changelog boolean NOT NULL DEFAULT false,
    ADD COLUMN target_release text NULL CHECK (length(target_release) <= 40),

    -- Free-text fallback only valid when its enum is 'other'.
    ADD CONSTRAINT feedback_source_other_chk
        CHECK ((source = 'other') = (source_other IS NOT NULL)),
    ADD CONSTRAINT feedback_type_other_chk
        CHECK ((type = 'other') = (type_other IS NOT NULL));

-- Backfill from the v1.0 → v2.0 migration script:
--   1. INSERT a single 'signalnest-legacy' workspace owned by the admin user.
--   2. UPDATE feedback_item SET workspace_id = (that workspace).
--   3. ALTER COLUMN workspace_id SET NOT NULL.
--   4. UPDATE feedback_item SET status='closed' WHERE status='rejected'.
CREATE INDEX feedback_workspace_idx ON feedback_item (workspace_id, created_at DESC);
CREATE INDEX feedback_workspace_status_idx ON feedback_item (workspace_id, status);
CREATE INDEX feedback_submitter_idx ON feedback_item (submitter_id) WHERE submitter_id IS NOT NULL;
```

### Open schema decisions

- **Drop `rejected` from `status_enum`?** Plan: leave for one release,
  drop in the v2.1 first migration after confirming zero rows. Tracked
  in [ADR 063 (TBD)](#adrs-to-write-for-v20).
- **`submitters.email NULL` semantics.** A submitter row with NULL
  email represents an anonymous public submission that we still want
  to count. Acceptable; the `UNIQUE (workspace_id, email)` constraint
  permits any number of NULL-email rows per workspace.
- **`tag.color` palette.** Eight named tones map to Tailwind palette
  shades in the frontend. Storing the name rather than the hex keeps
  the dark-mode mapping in CSS, not in DB rows.

---

## API Changes

All routes return JSON envelopes consistent with v1.0
(`items`/`total`/`skip`/`limit` for lists). All datetimes are ISO
8601 UTC with `Z`. All write routes return the canonical
representation of the affected resource.

### Auth

| Method | Path                                  | Auth     | Returns |
| ------ | ------------------------------------- | -------- | ------- |
| POST   | `/api/v1/auth/signup`                 | none     | `201` `{user, workspace}` |
| POST   | `/api/v1/auth/login`                  | none     | `200` `{user, memberships}` + `Set-Cookie` |
| POST   | `/api/v1/auth/logout`                 | session  | `204` + clear cookie |
| POST   | `/api/v1/auth/logout-everywhere`      | session  | `204` |
| GET    | `/api/v1/auth/me`                     | session  | `{user, memberships}` |
| POST   | `/api/v1/auth/verify-email`           | none     | `200` |
| POST   | `/api/v1/auth/resend-verification`    | session or email | `202` (always; no enumeration) |
| POST   | `/api/v1/auth/forgot-password`        | none     | `202` (always) |
| POST   | `/api/v1/auth/reset-password`         | none     | `200`, revokes other sessions |
| POST   | `/api/v1/auth/change-password`        | session  | `200`, revokes other sessions |

Signup body: `{ email, password, workspace_name }`. The signup
transaction creates the user, the workspace, and the owner
membership atomically. If `workspace_name` is omitted, the workspace
is named `"<email-localpart>'s workspace"`.

### Workspaces & members

| Method | Path                                           | Auth                | Returns |
| ------ | ---------------------------------------------- | ------------------- | ------- |
| GET    | `/api/v1/workspaces`                           | session             | list of workspaces the user belongs to |
| GET    | `/api/v1/workspaces/{slug}`                    | session + membership | one workspace |
| PATCH  | `/api/v1/workspaces/{slug}`                    | owner only          | rename, change slug |
| GET    | `/api/v1/workspaces/{slug}/members`            | session + membership | list members |
| POST   | `/api/v1/workspaces/{slug}/invitations`        | owner only          | `{ email, role }` → invitation id, sends email |
| GET    | `/api/v1/workspaces/{slug}/invitations`        | owner only          | open invitations |
| DELETE | `/api/v1/workspaces/{slug}/invitations/{id}`   | owner only          | revoke |
| POST   | `/api/v1/invitations/{token}/accept`           | session             | join workspace |
| DELETE | `/api/v1/workspaces/{slug}/members/{user_id}`  | owner only          | remove member |

### Feedback (workspace-scoped)

All require session + membership (or `admin`) and the
`X-Workspace-Slug` header.

| Method | Path                                    | Notes |
| ------ | --------------------------------------- | ----- |
| GET    | `/api/v1/feedback`                      | filters: `status`, `priority`, `source`, `type`, `tag`, `submitter_id`, `q`, `published_to_roadmap`, `published_to_changelog`, `created_after`, `created_before`, `skip`, `limit` |
| POST   | `/api/v1/feedback`                      | authenticated submission (creates with `source=web_form` by default) |
| GET    | `/api/v1/feedback/{id}`                 | full detail |
| PATCH  | `/api/v1/feedback/{id}`                 | partial update |
| DELETE | `/api/v1/feedback/{id}`                 | hard delete |
| POST   | `/api/v1/feedback/{id}/tags`            | `{ tag_ids: [...] }` — replaces tag set |
| GET    | `/api/v1/feedback/{id}/notes`           | list notes |
| POST   | `/api/v1/feedback/{id}/notes`           | `{ body }` |
| PATCH  | `/api/v1/feedback/{id}/notes/{note_id}` | author only, within 15 min |
| DELETE | `/api/v1/feedback/{id}/notes/{note_id}` | author or workspace owner |

### Public, anonymous

| Method | Path                                       | Notes |
| ------ | ------------------------------------------ | ----- |
| POST   | `/api/v1/w/{slug}/feedback`                | public submission; no cookie required; `source` defaults to `web_form`; honeypot field rejected if filled |
| GET    | `/api/v1/w/{slug}/roadmap`                 | only items where `published_to_roadmap = true` |
| GET    | `/api/v1/w/{slug}/changelog`               | only items where `published_to_changelog = true` |

Public submission rate limit: 10 / IP / hour and 30 / workspace /
hour, recorded in `auth_rate_limits` with `bucket_key` like
`pubsubmit:ip:1.2.3.4` and `pubsubmit:ws:<workspace_id>`.

### Submitters & tags

| Method | Path                              | Notes |
| ------ | --------------------------------- | ----- |
| GET    | `/api/v1/submitters`              | list, with `q` (matches name + email), `skip`, `limit` |
| GET    | `/api/v1/submitters/{id}`         | detail incl. recent feedback |
| PATCH  | `/api/v1/submitters/{id}`         | edit name / internal notes |
| GET    | `/api/v1/tags`                    | list |
| POST   | `/api/v1/tags`                    | create |
| PATCH  | `/api/v1/tags/{id}`               | rename / recolor |
| DELETE | `/api/v1/tags/{id}`               | delete + cascade `feedback_tags` |

### Dashboard / insights

| Method | Path                              | Notes |
| ------ | --------------------------------- | ----- |
| GET    | `/api/v1/dashboard/summary`       | `{ counts: {...}, intake_30d: [...] }`; cached per-workspace 60s |
| GET    | `/api/v1/insights/top-tags`       | top N tags by feedback count, with sparkline |
| GET    | `/api/v1/insights/pain-by-tag`    | mean pain_level per tag |
| GET    | `/api/v1/insights/status-mix`     | counts per status |

### Health

`/health` and `/ready` are unchanged from v1.0 and remain
unauthenticated.

### Search

v2.0 search is `WHERE description ILIKE '%' || :q || '%'` against
`feedback_item.description`. Bound parameter, not interpolated.
`pg_trgm` + a GIN index is the obvious upgrade and is deferred to
v2.1 — its own migration with a single index.

---

## UI Changes

Static HTML + vanilla JS, served by FastAPI's `StaticFiles` and
`HTMLResponse` page routes. Tailwind utility classes are the style
layer ([ADR 058](../../adr/058-tailwind-via-standalone-cli.md)).

### Page routes (HTMLResponse)

| Route                                | Auth         | Notes |
| ------------------------------------ | ------------ | ----- |
| `/`                                  | none / redirect | Marketing landing + mini demo. Logged-in users → `/w/<slug>/dashboard` |
| `/login`, `/signup`                  | none         | |
| `/forgot-password`, `/reset-password`, `/verify-email` | none | |
| `/invitations/<token>`               | maybe-session | accepts after login |
| `/styleguide`                        | none         | ADR 056 |
| `/w/<slug>/dashboard`                | session + member | |
| `/w/<slug>/inbox`                    | session + member | |
| `/w/<slug>/feedback`                 | session + member | |
| `/w/<slug>/feedback/<id>`            | session + member | |
| `/w/<slug>/submitters`               | session + member | |
| `/w/<slug>/submitters/<id>`          | session + member | |
| `/w/<slug>/roadmap`                  | session + member | management view |
| `/w/<slug>/changelog`                | session + member | management view |
| `/w/<slug>/insights`                 | session + member | |
| `/w/<slug>/settings`                 | session + member | members tab is owner-only |
| `/w/<slug>/submit`                   | none         | public submission form |
| `/w/<slug>/roadmap/public`           | none         | |
| `/w/<slug>/changelog/public`         | none         | |

### JS conventions

- One small JS file per page (`static/js/<page>.js`), no bundler.
- A shared `static/js/api.js` wraps `fetch` to inject the
  `X-Workspace-Slug` header (read from `<meta name="workspace-slug">`)
  and to handle 401 → redirect to `/login`.
- A shared `static/js/toast.js` for status messaging.
- Mini demo (`static/js/landing-demo.js`) is fully self-contained,
  no shared imports.

### Accessibility floor

WCAG 2.2 AA targeted; specific rules:

- Every status / priority pill carries **icon + text + color**, never
  color alone.
- All controls have `:focus-visible` styles using the `--color-focus`
  token.
- Modals use `<dialog>` with `.showModal()`; focus trap is the browser's.
- One `<h1>` per page, sequential headings.
- Skip link to `#main` on every page.
- Forms: every `<input>` has a paired `<label for>`; errors are
  announced via `aria-live="polite"`.

---

## Auth State Machine

Authoritative spec: [ADR 059](../../adr/059-auth-model.md). Summary:

```
[anon] --signup--> [unverified] --verify-email--> [verified]
[verified] --login--> [authed] --logout--> [anon]
[authed] --change-password--> [authed] (siblings revoked)
[anon] --forgot-password--> [reset-pending] --reset-password--> [verified]
       (all sessions for user revoked)
[unverified] --resend-verification--> [unverified]   (new token)
```

Cookie: `signalnest_session`, HttpOnly + Secure + SameSite=Lax,
sliding 7-day TTL. Token TTLs: verification 24 h, reset 1 h,
invitation 7 d. All single-use; reuse returns `410 Gone`.

Argon2id for passwords (`argon2-cffi`); `time_cost=3,
memory_cost=64*1024, parallelism=4`.

Rate limits (Postgres-backed, table `auth_rate_limits`):

- Login: 5 failures / email / 15 min and 20 / IP / 15 min.
- Forgot-password: 3 / email / hour.
- Resend-verification: 3 / email / hour.
- Public submission: 10 / IP / hour, 30 / workspace / hour.

---

## Email Integration

Provider: **Resend** (will be ratified in
[ADR 061 (TBD)](#adrs-to-write-for-v20)). `resend` Python SDK from
PyPI.

### Failure mode (fail-soft)

Email is sent **synchronously inside the request** but is wrapped in
`try/except`. Failures do **not** roll back the originating
transaction:

| Trigger                       | If Resend fails…                                          |
| ----------------------------- | ---------------------------------------------------------- |
| Signup → verification email   | User row is committed. UI tells them to use "resend verification" if no email arrives. Failure is logged with a correlation id. |
| Forgot-password               | Reset token row is committed. UI shows generic 202. (User can re-request.) |
| Invitation                    | Invitation row is committed. UI shows the invite URL inline so the owner can copy it. |
| Status-change → submitter     | Status change is committed. Email failure is logged; no retry queue in v2.0. |

This is documented in [ADR 061 (TBD)](#adrs-to-write-for-v20). A
background-retry queue is a deliberate v3.0 deferral.

### Email templates

Plain HTML strings in `src/feedback_triage/email/templates/*.html`.
Inline CSS, table-based layout for client compatibility. No
templating engine beyond `str.format` substitution. Content kept
short and transactional.

### Sender addresses

- `noreply@signalnest.app` — verification, reset, invitations.
- `notifications@signalnest.app` — status-change emails.

DNS (SPF, DKIM, DMARC) provisioned via Cloudflare; the records are
the author's responsibility outside the codebase.

---

## Public Submission Form

Per workspace, at `/w/<slug>/submit`. Fields:

| Field         | Type        | Required | Notes |
| ------------- | ----------- | -------- | ----- |
| Description   | textarea    | yes      | 1–4000 chars |
| Type          | select      | yes      | `type_enum` values; `other` reveals `type_other` |
| Source        | hidden      | —        | always `web_form` |
| Pain level    | radio 1–5   | no       | optional |
| Email         | email       | no       | if provided, links/creates a `submitters` row |
| Name          | text        | no       | only used if email provided |
| Honeypot      | hidden text | —        | empty; non-empty submissions are silently dropped |

Submission UX: success page thanks the user, optionally offers to
follow this feedback by email if they provided one, links back to
the workspace's public roadmap (if any).

---

## Background Work

v2.0 introduces no background workers, no Celery, no Redis. Two
operations need a recurring trigger:

- **Demo workspace reset.** A nightly cron (Railway cron) runs
  `scripts/reset_demo_workspace.py`.
- **Expired-token sweep.** The same cron runs `scripts/sweep_expired_tokens.py`
  to delete `email_verification_tokens` / `password_reset_tokens` /
  `workspace_invitations` / `sessions` past their `expires_at` by
  more than 24 h. Hard delete.

If Railway cron is unavailable the same scripts run locally via
`task cron:nightly` for development.

---

## Observability

Inherited from v1.0. v2.0 adds:

- `request_id` middleware logs the request id on every email send,
  every auth state transition, every cross-tenant access attempt.
- Failed login + failed cross-tenant access counts are emitted as
  structured log events at WARNING level for future alerting.

No metrics backend is introduced; logs to stdout only (Railway
captures them).

---

## Migration & Rollout Plan

Phased ship within the v2.0 release window. Each phase is a single
release tag (`v2.0.0-alpha.1`, `v2.0.0-beta.1`, `v2.0.0`).

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
shared without further explanation needed.

### Cut-over

A maintenance pause at the v1.0 → v2.0-alpha boundary is acceptable
(zero-downtime is not a v2.0 goal). The cut-over migration runs
once; rollback path is a fresh restore from the pre-cutover dump.

### Backwards compatibility

`/api/v1/*` paths from v1.0 keep their shape. The v1.0
`POST /api/v1/feedback` endpoint becomes workspace-scoped: the
`signalnest-legacy` workspace remains the implicit target until the
header `X-Workspace-Slug` is provided. After v2.0-final this implicit
fallback is removed and the endpoint requires the header.

---

## Tooling Stack

### Backend

| Item                          | Status vs. v1.0  | Notes                                                  |
| ----------------------------- | ---------------- | ------------------------------------------------------ |
| FastAPI                       | ✅ same           | sync routes (ADR 050)                                   |
| Uvicorn                       | ✅ same           | —                                                      |
| SQLAlchemy 2.0 / SQLModel     | ✅ same           | —                                                      |
| Alembic                       | ✅ same           | hand-reviewed migrations                                |
| Pydantic v2                   | ✅ same           | —                                                      |
| `pydantic-settings`           | ✅ same           | —                                                      |
| `argon2-cffi`                 | 🆕               | password hashing (ADR 059)                              |
| `resend`                      | 🆕               | transactional email (ADR 061 TBD)                       |
| `psycopg[binary]`             | ✅ same           | sync driver                                             |
| `httpx`                       | ✅ test-only      | —                                                      |

`asyncpg`, `python-jose`/`pyjwt`, `passlib`, `fastapi-users` —
**not** introduced. Decisions:
[ADR 050](../../adr/050-sync-db-driver-v1.md),
[ADR 059](../../adr/059-auth-model.md).

### Frontend / build

| Item                                  | Notes                                                       |
| ------------------------------------- | ----------------------------------------------------------- |
| Tailwind CSS (Standalone CLI binary)  | ADR 058. `task build:css`. No Node, no `package.json`.       |
| Lucide static SVGs                    | hand-exported into `static/img/icons/`                       |
| Playwright (Python)                   | gated `@pytest.mark.e2e` smoke suite                         |

No bundler, no React, no Vite, no TypeScript on the frontend.

### Email-provider snapshot (re-verify before launch)

| Provider         | Free tier (May 2026)                          | Verdict                              |
| ---------------- | --------------------------------------------- | ------------------------------------ |
| **Resend**       | 3,000 emails/month                            | Best DX. Recommended.                |
| Mailgun          | 100/day                                       | Mature; sales-heavy UX.              |
| Amazon SES       | $0.10/1k                                      | Cheapest long-term; AWS overhead.    |
| SendGrid         | 60-day trial then 100/day                     | Skip for cost-sensitive demo.        |

Expected v2.0 volume well under 1k/month → free tier indefinitely.

---

## Deployment

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

---

## ADRs to Write for v2.0

> Numbered from the next free slot in [`docs/adr/`](../../adr/).
> Three are already shipped (058, 059, 060); the rest land alongside
> the relevant phase.

| #     | Title                                                         | Status   | Drives           |
| ----- | ------------------------------------------------------------- | -------- | ---------------- |
| 058   | Tailwind via Standalone CLI                                   | ✅ Accepted | FT, all UI work |
| 059   | Auth model — cookie sessions + Argon2id                       | ✅ Accepted | F1               |
| 060   | Multi-tenancy / workspace scoping                             | ✅ Accepted | F1b              |
| 061   | Email provider (Resend) + fail-soft semantics                 | TBD      | FE, F1, F1b      |
| 062   | v1.0 → v2.0 data migration (legacy workspace + status rename) | TBD      | cut-over         |
| 063   | Status enum extension + `rejected` deprecation                | TBD      | FX               |
| 064   | Pain vs. Priority dual-field rationale                        | TBD      | FX               |

These can land in the same PR as the code that needs them.

---

## Future Improvements After v2.0

Items considered and explicitly punted to v3.0+:

- **F2** — React/Vite/TS SPA rewrite. Redundant with FT + FX.
- **Voting / severity / impact** scoring on feedback.
- **Bulk actions, side drawer, keyboard navigation** on the inbox.
- **Real-time updates** (SSE or WebSockets) when a teammate edits an
  item you're viewing.
- **File attachments** on feedback (object storage required).
- **AI clustering / summarization** of inbound feedback.
- **Customer-portal mode** — public-facing feature voting.
- **Multi-workspace per user** (the schema already supports it; v2.0
  enforces 1:1 in application logic only).
- **Postgres Row-Level Security** as defense-in-depth on top of
  query-layer scoping (deferred per
  [ADR 060](../../adr/060-multi-tenancy-workspace-scoping.md)).
- **Background email retry queue** with a separate worker.
- **`pg_trgm` GIN-indexed search** on feedback descriptions.
- **Audit log** of all writes per workspace.
- **Billing & paid tiers.**
- **Status-change Slack/Discord webhooks.**
- **API tokens** for programmatic submission from external systems.

---

## Related Docs

- [`spec-v1.md`](spec-v1.md) — shipped v1.0 spec (canonical until
  v2.0 ratifies)
- [`core-idea.md`](core-idea.md) — SignalNest brand and visual brief
- [`../implementation.md`](../implementation.md) — phase plan; needs a
  v2.0 phase appendix
- [`../questions.md`](../questions.md) — open questions and decisions
- [`../../adr/`](../../adr/) — ADRs governing the platform
- [`../../notes/frontend-conventions.md`](../../notes/frontend-conventions.md)
