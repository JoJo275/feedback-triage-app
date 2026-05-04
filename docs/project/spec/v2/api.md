# v2.0 — API Changes

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).

All routes return JSON envelopes consistent with v1.0
(`items`/`total`/`skip`/`limit` for lists). All datetimes are ISO
8601 UTC with `Z`. All write routes return the canonical
representation of the affected resource.

The active workspace is resolved from the `X-Workspace-Slug` header
on every authenticated JSON call; on public/anonymous routes it is
encoded in the URL prefix `/api/v1/w/<slug>/...`. See
[`multi-tenancy.md`](multi-tenancy.md).

---

## Auth

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

State machine + TTLs + rate limits live in [`auth.md`](auth.md).

---

## Workspaces & members

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

---

## Feedback (workspace-scoped)

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

---

## Public, anonymous

| Method | Path                                       | Notes |
| ------ | ------------------------------------------ | ----- |
| POST   | `/api/v1/w/{slug}/feedback`                | public submission; no cookie required; `source` defaults to `web_form`; honeypot field rejected if filled |
| GET    | `/api/v1/w/{slug}/roadmap`                 | only items where `published_to_roadmap = true` |
| GET    | `/api/v1/w/{slug}/changelog`               | only items where `published_to_changelog = true` |

Public submission rate limit: 10 / IP / hour and 30 / workspace /
hour, recorded in `auth_rate_limits` with `bucket_key` like
`pubsubmit:ip:1.2.3.4` and `pubsubmit:ws:<workspace_id>`.

---

## Submitters & tags

| Method | Path                              | Notes |
| ------ | --------------------------------- | ----- |
| GET    | `/api/v1/submitters`              | list, with `q` (matches name + email), `skip`, `limit` |
| GET    | `/api/v1/submitters/{id}`         | detail incl. recent feedback |
| PATCH  | `/api/v1/submitters/{id}`         | edit name / internal notes |
| GET    | `/api/v1/tags`                    | list |
| POST   | `/api/v1/tags`                    | create |
| PATCH  | `/api/v1/tags/{id}`               | rename / recolor |
| DELETE | `/api/v1/tags/{id}`               | delete + cascade `feedback_tags` |

---

## Dashboard / insights

| Method | Path                              | Notes |
| ------ | --------------------------------- | ----- |
| GET    | `/api/v1/dashboard/summary`       | `{ counts: {...}, intake_30d: [...] }`; cached per-workspace 60s |
| GET    | `/api/v1/insights/top-tags`       | top N tags by feedback count, with sparkline |
| GET    | `/api/v1/insights/pain-by-tag`    | mean pain_level per tag |
| GET    | `/api/v1/insights/status-mix`     | counts per status |

---

## Health

`/health` and `/ready` are unchanged from v1.0 and remain
unauthenticated.

---

## Search

v2.0 search is `WHERE description ILIKE '%' || :q || '%'` against
`feedback_item.description`. Bound parameter, not interpolated.
`pg_trgm` + a GIN index is the obvious upgrade and is deferred to
v2.1 — its own migration with a single index.

---

## Versioning posture

`/api/v1/*` paths from v1.0 keep their shape. v2.0 is **additive**;
no v1.0 endpoint changes its envelope. A `/api/v2/` namespace is not
introduced for v2.0. The one behavioural change to a v1.0 endpoint
is `POST /api/v1/feedback`: it is workspace-scoped via
`X-Workspace-Slug`, with the `signalnest-legacy` workspace as the
implicit fallback during the v2.0-alpha → v2.0-final window. After
v2.0-final the implicit fallback is removed and the header becomes
required. See [`rollout.md`](rollout.md).

---

## Cross-references

- [`schema.md`](schema.md) — tables backing every endpoint.
- [`auth.md`](auth.md) — auth state machine, cookie semantics.
- [`multi-tenancy.md`](multi-tenancy.md) — the `X-Workspace-Slug`
  contract and the `WorkspaceContext` dependency.
- [`security.md`](security.md) — rate limits, content limits, CSRF
  posture.
