# v2.0 — Schema Changes

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).

Every change here ships as a hand-reviewed Alembic migration with
`compare_type` + `compare_server_default` set. Native Postgres enums
+ DB CHECK constraints (per
[ADR 046](../../../adr/046-native-pg-enums-and-checks.md)) remain
mandatory. Citext is used for case-insensitive emails and slugs
(`CREATE EXTENSION IF NOT EXISTS citext` in the auth migration).

---

## New enums

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

---

## New tables — auth & tenancy

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

---

## New tables — workspace data

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

---

## Changes to `feedback_item`

```sql
ALTER TABLE feedback_item
    ADD COLUMN workspace_id uuid REFERENCES workspaces(id) ON DELETE CASCADE,
    ADD COLUMN submitter_id uuid REFERENCES submitters(id) ON DELETE SET NULL,
    ADD COLUMN title text NULL CHECK (title IS NULL OR length(title) BETWEEN 1 AND 120),
    ADD COLUMN type type_enum NOT NULL DEFAULT 'other',
    ADD COLUMN priority priority_enum NULL,
    ADD COLUMN source_other text NULL CHECK (length(source_other) <= 60),
    ADD COLUMN type_other   text NULL CHECK (length(type_other)   <= 60),
    ADD COLUMN published_to_roadmap   boolean NOT NULL DEFAULT false,
    ADD COLUMN published_to_changelog boolean NOT NULL DEFAULT false,
    ADD COLUMN release_note text NULL CHECK (release_note IS NULL OR length(release_note) <= 280),

    -- Free-text fallback only valid when its enum is 'other'.
    ADD CONSTRAINT feedback_source_other_chk
        CHECK ((source = 'other') = (source_other IS NOT NULL)),
    ADD CONSTRAINT feedback_type_other_chk
        CHECK ((type = 'other') = (type_other IS NOT NULL));

-- v1.0 → v2.0 backfill choreography (see ADR 062 + rollout.md):
--   Migration A (schema-only):
--     1. CREATE workspaces table (and friends).
--     2. INSERT a single 'signalnest-legacy' workspace owned by
--        the synthetic admin user.
--     3. ADD COLUMN workspace_id (NULLABLE).
--   Migration B (data + flip):
--     4. UPDATE feedback_item SET workspace_id = (legacy ws id).
--     5. ALTER COLUMN workspace_id SET NOT NULL.
--     6. UPDATE feedback_item SET status='closed' WHERE status='rejected'.
-- A and B ship as separate Alembic revisions so a deploy that
-- fails between them can roll forward, not down.
CREATE INDEX feedback_workspace_idx ON feedback_item (workspace_id, created_at DESC);
CREATE INDEX feedback_workspace_status_idx ON feedback_item (workspace_id, status);
CREATE INDEX feedback_submitter_idx ON feedback_item (submitter_id) WHERE submitter_id IS NOT NULL;
CREATE INDEX feedback_stale_idx
    ON feedback_item (workspace_id, created_at)
    WHERE status IN ('new', 'needs_info');
```

---

## Open schema decisions

- **Drop `rejected` from `status_enum`?** Plan: leave for one release,
  drop in the v2.1 first migration after confirming zero rows.
  Tracked in ADR 063 (TBD; see [`../spec-v2.md`](../spec-v2.md#adrs-to-write-for-v20)).
- **`submitters.email NULL` semantics.** A submitter row with NULL
  email represents an anonymous public submission that we still want
  to count. Acceptable; the `UNIQUE (workspace_id, email)` constraint
  permits any number of NULL-email rows per workspace.
- **`tag.color` palette.** Eight named tones map to Tailwind palette
  shades in the frontend. Storing the name rather than the hex keeps
  the dark-mode mapping in CSS, not in DB rows.
- **`email_log` table — pending ADR 061.** [`core-idea.md`](core-idea.md),
  [`business.md`](business.md), [`risks.md`](risks.md), and
  [`implementation.md`](implementation.md) all reference an
  `email_log` table (best-effort send status, error code, retried
  flag, recipient domain). The DDL is **not yet in this file** — it
  lands with [ADR 061](adrs.md#adr-061--email-provider-resend--fail-soft-semantics)
  ("Email provider (Resend) + fail-soft semantics"), which owns the
  table's exact shape. Add the `CREATE TABLE email_log (…)` block
  to this file in the same PR that ratifies ADR 061. Until then,
  treat `email_log` references in sibling docs as **forward
  references**, not contradictions.

> **Cross-doc check (next sweep):** the per-IP rate limit referenced
> in `core-idea.md` and `business.md` is **already covered** in
> [`security.md`](security.md#public-submission-abuse) and
> [`auth.md`](auth.md#rate-limits), and the supporting
> `auth_rate_limits` table is already in this file. No action there
> — only `email_log` is the genuine gap.

---

## Cross-references

- [`api.md`](api.md) — endpoint contracts that exercise these tables.
- [`multi-tenancy.md`](multi-tenancy.md) — the `workspace_id` invariant.
- [`auth.md`](auth.md) — token tables in detail.
- [`rollout.md`](rollout.md) — v1.0 → v2.0 migration script.
- [ADR 046 — Native PG enums + CHECK](../../../adr/046-native-pg-enums-and-checks.md)
- [ADR 060 — Multi-tenancy / workspace scoping](../../../adr/060-multi-tenancy-workspace-scoping.md)
