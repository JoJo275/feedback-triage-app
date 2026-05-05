# v2.0 — Error catalog

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> See also: [`api.md`](api.md), [`security.md`](security.md),
> [`copy-style-guide.md`](copy-style-guide.md).

This file is the single source of truth for **how the API
reports errors** and **what error codes are allowed**. Every
4xx response from `/api/v1/*` follows the same envelope and
uses a code from the table below. Adding a new code requires
updating this file in the same PR.

---

## Envelope

Every non-2xx JSON response from `/api/v1/*` returns this exact
shape, with `Content-Type: application/json`:

```json
{
  "error": {
    "code": "type_other_required",
    "message": "Please describe the type when choosing 'Other.'",
    "details": { "field": "type_other" }
  }
}
```

Rules:

- `error.code` is a stable machine-readable string,
  `snake_case`, ASCII only. **Codes never change once shipped**;
  if a meaning changes, allocate a new code and deprecate the
  old one in this file.
- `error.message` is a short, human-readable sentence safe to
  show end-users. Tone follows
  [`copy-style-guide.md`](copy-style-guide.md): plain, direct,
  no blame, no jargon. **Never include PII** (no email
  addresses, no IDs of other workspaces, no internal paths).
- `error.details` is optional. Allowed shapes:
  - `{ "field": "<name>" }` — single-field validation errors
  - `{ "fields": { "<name>": "<message>", ... } }` — multi-field
  - `{ "retry_after_seconds": <int> }` — rate-limit responses
  - `{ "expires_at": "<ISO 8601>" }` — token-expired responses
- `5xx` responses are minimal: `{ "error": { "code":
  "internal_error", "message": "Something went wrong. Please
  try again." } }`. No stack traces, no SQL, no stack frames.

---

## HTTP-status policy

| Status | Used for                                                                       |
| ------ | ------------------------------------------------------------------------------ |
| 400    | Malformed request (bad JSON, missing required field, type mismatch)            |
| 401    | Not authenticated; cookie missing/expired/invalid                              |
| 403    | Authenticated but action forbidden (demo write, role insufficient)             |
| 404    | Resource not found **or** cross-tenant ([`security.md`](security.md))          |
| 409    | State conflict (note edit window expired, slug taken, status transition denied) |
| 410    | Resource gone permanently (revoked invitation that was previously valid)       |
| 422    | Field-level validation error                                                   |
| 429    | Rate limit hit                                                                 |
| 500    | Unexpected server error                                                        |
| 503    | Feature flag off (`FEATURE_AUTH=false` returns 503 on `/login` and `/api/v1/auth/*`) |

**Cross-tenant rule:** any access to a resource that exists but
belongs to another workspace returns **404, not 403**. This is
enforced by `tests/api/test_isolation.py` (Phase 1 canary, file not yet created)
and is the canary test for [`security.md`](security.md).

---

## Canonical error codes

Codes are grouped by surface. Every code listed here is in active
use by at least one route. Removing a code requires verifying
that no test or client depends on it.

### Auth (`/api/v1/auth/*`)

| Code                          | HTTP | When                                                               |
| ----------------------------- | ---- | ------------------------------------------------------------------ |
| `auth_required`               | 401  | No session cookie or session expired                               |
| `invalid_credentials`         | 401  | Login: email + password do not match (no enumeration — same code if email is unknown) |
| `email_not_verified`          | 403  | Login succeeded but `email_verified_at IS NULL`                    |
| `account_locked`              | 403  | Five failed logins within the rate-limit window                    |
| `verification_token_invalid` | 410  | Verification token unknown or already used                         |
| `verification_token_expired`  | 410  | Verification token TTL expired                                     |
| `password_reset_token_invalid` | 410 | Reset token unknown or already used                                |
| `password_reset_token_expired` | 410 | Reset token TTL expired                                            |
| `password_too_weak`           | 422  | Signup / reset: password fails policy ([`auth.md`](auth.md))       |
| `feature_disabled`            | 503  | `FEATURE_AUTH=false` and a v2 auth route was hit                   |

### Workspace (`/api/v1/workspaces/*`)

| Code                          | HTTP | When                                                               |
| ----------------------------- | ---- | ------------------------------------------------------------------ |
| `workspace_not_found`         | 404  | Slug missing or user has no membership in it (cross-tenant)        |
| `workspace_slug_taken`        | 409  | Create: slug already exists                                        |
| `workspace_slug_immutable`    | 409  | PATCH attempted to change `slug`                                   |
| `role_insufficient`           | 403  | Action requires `owner` and caller is `team_member`                |
| `demo_read_only`              | 403  | Any write attempted in a workspace where `is_read_only = true`     |
| `invitation_invalid`          | 410  | Invitation token unknown / consumed                                |
| `invitation_expired`          | 410  | Invitation TTL expired                                             |
| `invitation_email_mismatch`   | 403  | Accepting an invitation with a different signed-in email           |

### Feedback (`/api/v1/feedback/*`)

| Code                          | HTTP | When                                                               |
| ----------------------------- | ---- | ------------------------------------------------------------------ |
| `feedback_not_found`          | 404  | ID missing **or** in another workspace (cross-tenant)              |
| `type_other_required`         | 422  | `type=other` with empty `type_other` ([`ui.md`](ui.md))            |
| `source_other_required`       | 422  | `source=other` with empty `source_other`                           |
| `pain_level_out_of_range`     | 422  | `pain_level` not in 1..5                                           |
| `priority_invalid`            | 422  | `priority` not in `priority_enum`                                  |
| `status_transition_invalid`   | 409  | Disallowed transition (e.g. `closed → in_progress`)                |
| `note_edit_window_expired`    | 409  | PATCH/DELETE on a note older than 15 minutes                       |
| `note_not_owner`              | 403  | PATCH/DELETE on a note authored by another user                    |
| `tag_not_found`               | 404  | Attaching a tag that does not exist in this workspace              |
| `tag_name_taken`              | 409  | Creating a tag whose `(workspace_id, name)` already exists         |
| `submitter_not_found`         | 404  | Attaching a submitter that does not exist in this workspace        |

### Public submission (`/api/v1/public/feedback`)

| Code                          | HTTP | When                                                               |
| ----------------------------- | ---- | ------------------------------------------------------------------ |
| `workspace_not_public`        | 404  | Target workspace does not exist or has no public form              |
| `rate_limited`                | 429  | Public-form rate limit hit (`details.retry_after_seconds`)         |
| `payload_too_large`           | 413  | Body exceeds 64 KB                                                 |

### Generic

| Code                          | HTTP | When                                                               |
| ----------------------------- | ---- | ------------------------------------------------------------------ |
| `validation_error`            | 422  | Pydantic validation error not covered by a more specific code      |
| `bad_request`                 | 400  | Malformed JSON / missing required field at the parser level        |
| `internal_error`              | 500  | Catch-all                                                          |

---

## Implementation note

A single FastAPI exception handler maps `HTTPException` subclasses
plus `pydantic.ValidationError` into the envelope above. Routes
raise typed exceptions like `WorkspaceNotFound`, never bare
`HTTPException(404)`, so the error code is the source of truth and
the HTTP status is derived from it.

The mapping table lives in `src/feedback_triage/errors.py`. Adding
a code means updating this file **and** that module in the same PR.
