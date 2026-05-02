# ADR 060: Multi-tenancy — workspaces, memberships, and query-layer scoping

## Status

Accepted

## Context

v2.0 promotes SignalNest from a single-table CRUD app to a
**B2B SaaS feedback-triage tool**. The user model committed to in the
session [`docs/project/spec/todo.md`](../project/spec/todo.md)
distinguishes:

- **Admin** — the project author. Cross-workspace access.
- **Workspace owner** — person/company using SignalNest. Owns one
  workspace.
- **Team member** — invited by a workspace owner.
- **Demo user** — read-only access to a seeded demo workspace.
- **Public submitter** — anonymous; no account.
- **Submitter / customer** — known by email; row in `submitters`,
  no login.

This requires multi-tenancy: every workspace's feedback, tags,
submitters, and members are isolated. Three implementation options
exist:

1. **Database-per-tenant.** Strongest isolation, operational nightmare
   for a single-Railway-Postgres deployment. Migrations × N
   workspaces.
2. **Schema-per-tenant.** Better than (1), still requires per-tenant
   `search_path` and migration fan-out.
3. **Shared schema, `workspace_id` column on every tenant-scoped
   table.** Standard SaaS pattern. Isolation is the application's
   responsibility (or Postgres Row-Level Security on top).

For v2.0's scale (≤ 100 workspaces in any realistic projection),
shared-schema is the only sane choice. The remaining question is
**how isolation is enforced**:

- **Query-layer scoping.** Every read/write goes through a
  `WorkspaceContext` dependency that injects `WHERE workspace_id =
  :ws_id` (or fails closed). Mistakes are caught by tests.
- **Postgres Row-Level Security (RLS).** Every tenant-scoped table
  enables RLS; a policy reads `current_setting('app.workspace_id')`.
  The application sets this once per request via `SET LOCAL`.
  Mistakes in the application layer are caught by Postgres.

RLS is the stronger guarantee but adds operational complexity:
migrations must enable RLS per table, every connection must set the
GUC, the `admin` role needs a `BYPASSRLS` policy or a separate
session role, and Alembic auto-generation doesn't always handle
policies cleanly. Query-layer scoping is the standard FastAPI/SQLModel
pattern and is enforceable through code review + tests.

## Decision

**Shared schema, `workspace_id` column on every tenant-scoped table,
isolation enforced at the query layer in v2.0. RLS deferred to a
later ADR.**

### Tables (workspace-scoped)

Every tenant-scoped table carries `workspace_id uuid NOT NULL` with
an FK to `workspaces(id) ON DELETE CASCADE` and an index. The
v2.0-tenant-scoped set:

- `feedback_item` (existing, gains `workspace_id`).
- `tags`.
- `feedback_tags` (join table; inherits scope through `feedback_id`).
- `submitters`.
- `feedback_notes`.
- `workspace_invitations`.
- `auth_rate_limits` (per workspace + per email).

**Not** workspace-scoped (cross-tenant or platform-level):

- `users` — a user can belong to multiple workspaces eventually
  (v3.0; v2.0 enforces 1:1 in application logic).
- `sessions`, `email_verification_tokens`, `password_reset_tokens`
  — bound to a user, not a workspace.

### New tables

```sql
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
    workspace_id  uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role          workspace_role_enum NOT NULL,
    joined_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, user_id)
);

CREATE TYPE workspace_role_enum AS ENUM ('owner', 'team_member');

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
    created_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, email) WHERE accepted_at IS NULL AND revoked_at IS NULL
);
```

### Workspace creation flow

- On signup, the user enters a workspace name. A `workspaces` row is
  created with `owner_id = user.id`, slug derived from the name
  (collision-resolved by appending `-2`, `-3`, …).
- The user gets a `workspace_memberships` row with `role='owner'`.
- The signup endpoint (see [ADR 059](059-auth-model.md)) does both in
  the same transaction.

### Workspace context (request scoping)

- The active workspace is selected by URL prefix:
  `/w/<workspace_slug>/...` for all dashboard routes.
  `/api/v1/feedback`, `/api/v1/tags`, etc. accept the slug via the
  `X-Workspace-Slug` header on JSON calls (or `?ws=<slug>` in
  development).
- A `get_current_workspace` FastAPI dependency:
  1. Resolves the slug to a `workspace_id`.
  2. Confirms the requesting user has a `workspace_memberships` row
     for that workspace (or has platform `role='admin'`).
  3. Returns a typed `WorkspaceContext` containing `id`, `slug`, and
     the user's role within it.
- Every CRUD route depends on `WorkspaceContext` and **must** filter
  every query by `workspace_id`. A pytest fixture creates two
  workspaces and seeds rows in both; cross-tenant reads must return
  empty.

### Public submission flow (no workspace context yet)

The public feedback-submission endpoint targets a workspace by slug:
`POST /api/v1/w/<slug>/feedback` (anonymous). The slug is the
public route to that workspace's submission form. The submission UI
lives at `/w/<slug>/submit` and requires no authentication.

### Demo workspace

- One seeded workspace with `is_demo=true`, owned by a `demo` user.
- All `demo` user logins land in this workspace as a `team_member`
  (or a synthetic read-only role; see implementation).
- A nightly cron resets the demo workspace to a known seed.
- `is_demo=true` workspaces are excluded from any future "public
  workspace listing" endpoint.

### Cross-workspace `admin` access

The `admin` user (platform role from
[ADR 059](059-auth-model.md)) bypasses workspace-membership checks
in `get_current_workspace` but **still scopes queries** by the
explicitly-requested workspace slug. Admin doesn't see all
workspaces' data merged; admin can switch between any workspace.

### Migration of v1.0 data

Existing `feedback_item` rows have no `workspace_id`. Migration
strategy:

1. Create a single seed workspace `signalnest-legacy` owned by the
   admin user.
2. Backfill `feedback_item.workspace_id` to that workspace's id.
3. Add the FK + NOT NULL constraint **after** the backfill.
4. The migration runs in a single Alembic revision. Zero downtime is
   not a goal for v2.0 launch; the upgrade window can be a
   maintenance pause.

This decision is captured here rather than as a separate ADR because
it's purely a one-shot v1.0 → v2.0 transition with no ongoing
implications.

### Test fixtures

- `client_w1` / `client_w2`: TestClient instances bound to two
  different workspaces.
- A canary test attempts cross-tenant reads via `client_w1` looking
  up `client_w2`'s feedback id — must 404.
- Every API test that asserts data presence runs the same assertion
  with the second client and asserts absence. This is the multi-
  tenancy equivalent of the v1.0 session-reuse canary.

### Row-Level Security (deferred)

RLS is **not** enabled in v2.0. It is the right defense-in-depth
addition once the query-layer scoping is exercised in production.
A follow-on ADR will:

- Enable RLS on every workspace-scoped table.
- Define a `SET LOCAL app.workspace_id = …` per-request hook in
  `get_db`.
- Add a `BYPASSRLS` capability for the `admin` role's connection.

## Alternatives Considered

### Schema-per-tenant

Per-workspace Postgres schema; `search_path` set per request.

**Rejected because:** Alembic doesn't natively fan migrations across
schemas; every schema change becomes N writes; rollback is harder;
admin cross-workspace queries become unions over schemas. Strict
isolation is a real benefit but doesn't justify the operational cost
at v2.0 scale.

### RLS-from-day-one

Same shared-schema model but RLS enabled in the same migration.

**Rejected because:** the `SET LOCAL` plumbing, the `BYPASSRLS`
admin role, and the Alembic policy management are non-trivial. The
incremental risk of "we forgot a `WHERE workspace_id`" is real but
catchable through tests and code review. RLS becomes a follow-on
hardening pass, not a v2.0 launch blocker.

### Single-workspace v2.0 (defer multi-tenancy)

Build only the data model that supports the author's own use; add
multi-tenancy later.

**Rejected because:** multi-tenancy is the architectural decision
that touches every query. Retrofitting it onto a single-tenant v2.0
later means migrating every table and rewriting every query — a
v3.0-sized rewrite worse than doing it now. The author confirmed
they want the multi-tenant model in v2.0 even at the cost of a
~30 % larger release.

## Consequences

### Positive

- Standard SaaS shared-schema pattern; well-understood and well-
  documented.
- One Postgres, one connection pool, one set of migrations.
- All cross-tenant queries (e.g. `task` admin reports across all
  workspaces) are normal SQL with `WHERE workspace_id IN (…)`.
- The data model already supports a future v3.0 multi-membership
  model (one user in many workspaces) without schema change.

### Negative

- Every tenant-scoped query needs `WHERE workspace_id = :ws_id`. A
  forgotten clause is a tenant-isolation bug.
- Test surface roughly doubles for tenant-scoped routes (every
  positive test runs a cross-tenant negative twin).
- Admin's cross-workspace access is a privileged path that must be
  audited.

### Neutral

- Auth model from [ADR 059](059-auth-model.md) is unchanged; the
  platform user is workspace-agnostic at the auth layer.

### Mitigations

- `WorkspaceContext` is a single FastAPI dependency. Every CRUD
  route declares it; routes that don't depend on it are documented
  exceptions (signup, login, public submission, health).
- A pytest fixture seeds two workspaces by default; the canary
  cross-tenant read test runs in the standard suite.
- Code review: any query against a tenant-scoped table that doesn't
  include `workspace_id` is a red flag. A custom ruff rule or a
  bandit plugin can flag the most common offenders (`session.exec(
  select(Model).where(...))` without `Model.workspace_id ==`) as a
  follow-up.
- RLS adoption is the planned follow-on hardening.

## Implementation

- `src/feedback_triage/workspaces/` — `models.py`, `service.py`,
  `routes.py`, `context.py`, `invitations.py`.
- `src/feedback_triage/dependencies.py` — `get_current_workspace`.
- `alembic/versions/<rev>_add_workspaces_and_scope_existing.py` —
  workspaces, memberships, invitations, and the v1.0 backfill.
- `tests/conftest.py` — `client_w1`, `client_w2`, `seed_workspaces`.
- `tests/test_tenant_isolation.py` — cross-tenant negative-twin
  canary.
- `scripts/seed_demo_workspace.py` — populates the demo workspace.

## References

- [ADR 045: Single-table data model (v1.0)](045-single-table-data-model.md)
- [ADR 048: Session-per-request DB lifecycle](048-session-per-request.md)
- [ADR 059: Auth model — cookie sessions](059-auth-model.md)
- [Postgres Row-Level Security docs](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [`docs/project/spec/spec-v2.md`](../project/spec/spec-v2.md)
