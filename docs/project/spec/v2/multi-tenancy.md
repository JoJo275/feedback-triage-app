# v2.0 — Multi-tenancy

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Authoritative decision record:
> [ADR 060](../../../adr/060-multi-tenancy-workspace-scoping.md).

SignalNest is multi-tenant from v2.0. Every workspace's feedback,
tags, submitters, and notes are isolated. Isolation is enforced at
the **query layer**; Postgres Row-Level Security is deferred to a
later ADR as defense-in-depth.

---

## Roles

| Role                 | Account? | Scope                  | What they can do                                                                                  |
| -------------------- | -------- | ---------------------- | ------------------------------------------------------------------------------------------------- |
| Admin                | yes      | platform-wide          | Project author. Can switch into any workspace, see admin-only routes, run maintenance.            |
| Workspace owner      | yes      | one workspace          | Full CRUD on their workspace's feedback, tags, submitters; invite/remove team members; settings.  |
| Team member          | yes      | one workspace          | Full CRUD on the workspace's feedback, tags, notes; cannot manage members or change settings.     |
| Demo user            | yes      | the demo workspace     | **Read-only** access to a seeded workspace via `WorkspaceContext.is_read_only=True`. One shared login. Resets nightly. |
| Submitter / customer | no       | one workspace (linked) | Row in `submitters`. Has email known to the workspace; submitted feedback is grouped by them.     |
| Public submitter     | no       | one workspace (open)   | Anonymous. Submits feedback through a workspace's public form. No persistent identity.            |

Enum spellings (authoritative — [`schema.md`](schema.md)):

- `user_role_enum` (on `users.role`): `{'admin', 'team_member', 'demo'}`
- `workspace_role_enum` (on `workspace_memberships.role`): `{'owner', 'team_member'}`

UI labels capitalize and add a space ("Team member"). Code uses
the snake_case enum values verbatim.

The platform `role` (on `users`) is **separate** from the workspace
role (on `workspace_memberships`). See
[ADR 059](../../../adr/059-auth-model.md) and
[ADR 060](../../../adr/060-multi-tenancy-workspace-scoping.md).

---

## Workspace addressing

- **Dashboard pages**: prefix `/w/<workspace_slug>/` on every URL
  (`/w/acme/inbox`, `/w/acme/feedback/<id>`).
- **Authenticated JSON API**: `/api/v1/<resource>` with the active
  workspace selected via the `X-Workspace-Slug` header. Every
  authenticated `fetch` call from `static/js/api.js` injects this
  header from `<meta name="workspace-slug">` on the page.
- **Public, anonymous routes**: workspace slug encoded in the URL
  prefix `/api/v1/w/<slug>/...` and `/w/<slug>/...`.

---

## `WorkspaceContext` dependency

Every CRUD route declares a FastAPI dependency `get_current_workspace`.
The dependency:

1. Resolves the slug to a `workspace_id`.
2. Confirms the requesting user has a `workspace_memberships` row
   for that workspace (or has platform `role='admin'`).
3. Returns a typed `WorkspaceContext` containing `id`, `slug`, the
   user's role within it (or a synthetic `'admin'` role), and an
   `is_read_only: bool` flag.

```python
@dataclass(frozen=True, slots=True)
class WorkspaceContext:
    id: UUID
    slug: str
    role: WorkspaceRole | Literal["admin"]
    is_read_only: bool   # True for demo users; checked by every write route
```

`is_read_only` is `True` iff `users.role == 'demo'`. Every `POST`,
`PATCH`, `DELETE` route depends on a small
`require_writable(ctx)` helper that raises `403` with
`code=demo_read_only` when the flag is set. Read routes ignore the
flag.

The canary test for cross-tenant isolation lives at
**`tests/api/test_isolation.py`** (single canonical path; older
references to `tests/test_tenant_isolation.py` are stale).

A pytest fixture (`client_w1`, `client_w2`) creates two workspaces
and seeds rows in both; **every** API test that asserts data
presence runs the same assertion with the second client and
asserts absence. This is the v2.0 equivalent of the v1.0
session-reuse canary.

---

## Workspace creation

On signup, the user enters a workspace name. A `workspaces` row is
created with `owner_id = user.id`, slug derived from the name
(collision-resolved by appending `-2`, `-3`, …). The user gets a
`workspace_memberships` row with `role='owner'`. All three writes
happen in the **same** signup transaction.

If `workspace_name` is omitted, the workspace is named
`"<email-localpart>'s workspace"`.

v2.0 enforces **one workspace per user** at the application layer
(signup creates exactly one; users cannot belong to a second). The
schema already supports many-to-many memberships; lifting the 1:1
restriction is a v3.0 concern.

---

## Invitations

Owners invite team members by email:

1. `POST /api/v1/workspaces/{slug}/invitations` with `{ email, role }`.
2. A `workspace_invitations` row is created with a 7-day TTL.
3. The invited address receives an email with a single-use link
   `/invitations/<token>`.
4. The recipient signs in (or signs up; the invitation is keyed by
   email and consumes any matching account). The invitation flips
   to `accepted_at`.

Owners can revoke open invitations
(`DELETE /api/v1/workspaces/{slug}/invitations/{id}`).

---

## Demo workspace

- One seeded workspace with `is_demo=true`, owned by a `demo` user.
- All `demo` user logins land in this workspace as a synthetic
  read-only role.
- A nightly cron resets the demo workspace to a known seed (see
  [`rollout.md`](rollout.md)).
- `is_demo=true` workspaces are excluded from any future "public
  workspace listing" endpoint.

---

## Admin posture

The `admin` user (platform role) bypasses workspace-membership checks
in `get_current_workspace` but **still scopes queries** by the
explicitly-requested workspace slug. Admin doesn't see all
workspaces' data merged; admin can switch between any workspace.

Admin operations that span workspaces (maintenance, demo reset)
live in `scripts/` and run with their own DB session, not through
the request lifecycle.

---

## Tenant-isolation invariants

- Every tenant-scoped table carries `workspace_id uuid NOT NULL` with
  an FK + index.
- Every CRUD route depends on `WorkspaceContext`.
- Every `select(...)` against a tenant-scoped table includes
  `Model.workspace_id == ctx.id`. A code-review red flag and a
  candidate for a custom static-analysis check.
- The cross-tenant canary test
  (`tests/api/test_isolation.py::test_cross_tenant_read_returns_404`)
  must stay green.

---

## Cross-references

- [ADR 060 — Multi-tenancy / workspace scoping](../../../adr/060-multi-tenancy-workspace-scoping.md)
- [`schema.md`](schema.md) — `workspaces`, `workspace_memberships`, `workspace_invitations`.
- [`api.md`](api.md) — workspace + member endpoints.
- [`security.md`](security.md) — tenant-isolation invariants in security context.
