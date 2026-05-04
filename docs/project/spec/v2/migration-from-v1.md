# v2.0 — Migrating from v1.0

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> See also: [`rollout.md`](rollout.md), [`schema.md`](schema.md),
> [`auth.md`](auth.md). Tracks ADR 062.

This is the **user-facing companion to ADR 062**. ADR 062 covers
the technical migration choreography; this file covers what an
existing v1.0 user sees on first contact with v2.0.

---

## What changes

| For a v1.0 user…             | …on first v2.0 visit, they see…                                          |
| ---------------------------- | ------------------------------------------------------------------------ |
| The deployed URL             | The new landing page (`/`), not the old inbox                            |
| Their bookmarked `/feedback` | A redirect to `/login`, then on to `/w/signalnest-legacy/feedback`       |
| Their bookmarked `/feedback/{id}` | After login, a redirect to `/w/signalnest-legacy/feedback/{id}`     |
| Old API calls to `/api/v1/feedback` | Same path, still works; auth is now required (cookie or 401)      |
| The site name                | `SignalNest` (was unbranded `feedback-triage-app`)                       |

There is **no zero-downtime cut-over** ([`rollout.md`](rollout.md)).
The v1.0 → v2.0-alpha boundary is a brief maintenance pause; the
old app is taken offline, the migrations in
[`rollout.md`](rollout.md) run, the v2.0 image is deployed.

---

## The legacy workspace

Every v1.0 row has been moved to one synthetic workspace:

- Slug: `signalnest-legacy`
- Display name: `SignalNest (legacy)`
- Owner: a synthetic admin user, email taken from the
  `ADMIN_BOOTSTRAP_EMAIL` env var
- `is_read_only`: `false` (it's a real working workspace, not
  a demo)

After the cut-over, that admin user logs in once, sets a real
password (the bootstrap password forces a reset on first sign-in),
verifies their email, and invites real team members. Each v1.0
user that signs up post-migration goes through the standard
signup flow; their **email is not pre-provisioned** unless the
admin manually invites them.

---

## What v1.0 users have to do

The minimum, to keep working in v2.0:

1. Visit the site. They land on `/`.
2. Click **Sign in**. v1.0 had no auth, so they don't have an
   account yet — they click **Create account** instead.
3. Sign up with their email + password. (Self-serve sign up
   creates a *new* personal workspace, not membership in the
   legacy workspace.)
4. To access the v1.0 data, they ask the admin to invite them
   to `signalnest-legacy`.
5. The admin invites them (`/w/signalnest-legacy/settings/members`),
   they accept the invitation, they're in.

This is friction — but it's friction we accept once, at v1.0 →
v2.0, and never again.

### The shortcut for the solo developer

In practice, v2.0 ships from a one-person fork. The "v1.0 user"
is *the same person* as the admin. Their migration is:

1. Cut-over runs.
2. They sign in as the admin (with the bootstrap password →
   forced reset → real password).
3. They verify their email.
4. They open `/w/signalnest-legacy/feedback` and find every v1.0
   row, intact, with `workspace_id` backfilled.

---

## Status enum rename: `rejected` → `closed`

In v1.0 there was a `rejected` status. In v2.0 there isn't —
the closest replacement is `closed`. Migration B
([`rollout.md`](rollout.md)) does:

```sql
UPDATE feedback_item SET status = 'closed' WHERE status = 'rejected';
```

Rationale: ADR 063. *Rejected* sounds adversarial; *closed* is
neutral and includes the "we considered it and won't act" case
plus the "we shipped it under another item" case.

If you bookmarked `?status=rejected` in v1.0, the URL silently
filters to `status=closed` after migration. Old links don't 404;
they just behave as the new equivalent.

---

## URLs that change

| v1.0 URL                          | v2.0 URL                                                                |
| --------------------------------- | ----------------------------------------------------------------------- |
| `/feedback`                       | `/w/<slug>/feedback`                                                    |
| `/feedback/{id}`                  | `/w/<slug>/feedback/{id}`                                               |
| `/feedback/new`                   | `/w/<slug>/feedback/new` *(authenticated)* or `/f/<slug>` *(public)*    |
| `/api/v1/feedback`                | Same path — but requires auth + `X-Workspace-Slug` header               |
| `/api/v1/feedback/{id}`           | Same path — same auth requirement                                       |
| (none)                            | `/login`, `/signup`, `/verify`, `/reset`, `/w/<slug>/dashboard`         |

The unauthenticated v1.0 page routes (`/feedback`, `/feedback/{id}`)
are kept as **redirect stubs**: they 302 to the corresponding v2.0
path under the legacy workspace, for one minor version (until
v2.1.0). This keeps `/feedback/{id}` bookmarks alive long enough
for users to update them.

After v2.1.0, the redirect stubs are removed and the old paths
return 404.

---

## Cookies and sessions

v1.0 had no cookies. Therefore there is **nothing to invalidate**
on the v2.0 side at cut-over — no v1.0 user has a v2.0 session.
The first time a user touches v2.0, they go through `/login` and
get a fresh session cookie ([`auth.md`](auth.md)).

The `Secure` + `HttpOnly` + `SameSite=Lax` flags are set on every
session cookie from day one, so there's no transition policy
needed.

---

## Data the migration does **not** touch

- **Feedback `created_at` / `updated_at` timestamps** are
  preserved exactly. Reordering by date in v2.0 matches v1.0.
- **Pain levels** are preserved 1:1.
- **Source values** are preserved (the v1.0 `source_enum` is a
  subset of v2.0's, no rewrites needed).
- **IDs** are preserved. A v1.0 link `/feedback/abc-123` lands
  on the same row in v2.0.

---

## Data the migration **does** add

- `workspace_id` (set to the legacy workspace, NOT NULL).
- `title` (NULL — v1.0 never had a title; users fill these in
  over time as they triage).
- `submitter_id` (NULL — v1.0 had no submitter table).
- `priority` (NULL — opt-in field; v1.0 had no priority).
- `type` (NULL — opt-in; v1.0 had no type).
- `published_to_roadmap` / `published_to_changelog` (FALSE).
- `release_note` (NULL).

NULL is acceptable on every added column. None of them are
required by the v2.0 UI; they degrade gracefully.

---

## Rollback

If Migration A or B fails, the rollback is **restore the
pre-cutover dump** taken automatically by the deploy script
into a fresh Postgres, point the app at it, redeploy v1.0.
There is no in-place downgrade migration; ADR 062 explicitly
chose dump-restore over reversible Alembic for this single
cut-over.

The pre-cutover dump is named `pre-v2-cutover-YYYYMMDD-HHMM.sql.gz`
and is uploaded to the configured S3-compatible bucket
([`railway-optimization.md`](railway-optimization.md)).

---

## Out of scope

- Bulk-importing the v1.0 user list as pre-provisioned v2.0
  accounts. (We'd need passwords; we don't have them. Users
  sign up themselves.)
- A v1.0 → v2.0 data export tool for self-hosted users.
  v2.0 is single-tenant SignalNest-hosted.
- A grace period of running v1.0 and v2.0 side by side.
  The cut-over is one-way.
