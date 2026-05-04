# v2.0 — Authentication

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Authoritative decision record: [ADR 059](../../../adr/059-auth-model.md).

---

## State machine

```
[anon] --signup--> [unverified] --verify-email--> [verified]
[verified] --login--> [authed] --logout--> [anon]
[authed] --change-password--> [authed] (siblings revoked)
[anon] --forgot-password--> [reset-pending] --reset-password--> [verified]
       (all sessions for user revoked)
[unverified] --resend-verification--> [unverified]   (new token)
```

Notes:

- `[unverified]` users **can** log in (so they can use the app
  immediately) but cannot trigger workspace invitations or change
  workspace settings until verified.
- `change-password` revokes every session **other than** the one the
  request came from.
- `reset-password` revokes **every** session including the active one
  (the assumption is account compromise; user logs in fresh).
- The `demo` user cannot reset passwords or change email — the demo
  password lives in the seed and rotates per release.

---

## Session cookie

| Attribute   | Value                                                                       |
| ----------- | --------------------------------------------------------------------------- |
| Name        | `signalnest_session`                                                        |
| Value       | 256 bits from `secrets.token_urlsafe(32)`. Server stores `sha256(value)`.   |
| `HttpOnly`  | always                                                                      |
| `Secure`    | always in production (env: `SECURE_COOKIES=true`); relaxed for local HTTP   |
| `SameSite`  | `Lax`                                                                       |
| `Path`      | `/`                                                                         |
| `Max-Age`   | `604800` (7 days), sliding — `expires_at` is extended on every request      |

Centralized in `src/feedback_triage/auth/cookies.py`; no other code
sets `Set-Cookie`.

---

## Password storage

- Algorithm: **Argon2id** via [`argon2-cffi`](https://pypi.org/project/argon2-cffi/).
- Parameters: `time_cost=3, memory_cost=64*1024, parallelism=4`
  (~250 ms on a Railway hobby instance).
- Hashes are upgraded automatically on next successful login when
  parameters change (`argon2-cffi`'s `check_needs_rehash`).
- `passlib` is **not** used.

---

## Token TTLs

| Token                          | TTL        | Single-use | On reuse                                       |
| ------------------------------ | ---------- | ---------- | ---------------------------------------------- |
| Session cookie                 | 7 days, sliding | rotated on password change | n/a                            |
| Email verification             | 24 hours   | yes        | `410 Gone`. New token must be requested.        |
| Password reset                 | 1 hour     | yes        | `410 Gone`. **Existing sessions are revoked** when reset is consumed. |
| Workspace invitation           | 7 days     | yes        | `410 Gone`. Inviter can re-issue.               |

All tokens are stored as **SHA-256 of the raw value**. The raw token
travels only in the email link / cookie.

---

## Rate limits

Implemented as Postgres counters in the `auth_rate_limits` table.
Best-effort, not a distributed lock. Bucket keys:

| Trigger                         | Bucket key                                | Limit                  |
| ------------------------------- | ----------------------------------------- | ---------------------- |
| Failed login (per email)        | `login:email:<email>`                     | 5 / 15 min             |
| Failed login (per IP)           | `login:ip:<ip>`                           | 20 / 15 min            |
| Forgot-password request         | `forgot:email:<email>`                    | 3 / hour               |
| Resend verification             | `resend-verify:email:<email>`             | 3 / hour               |
| Public submission (per IP)      | `pubsubmit:ip:<ip>`                       | 10 / hour              |
| Public submission (per ws)      | `pubsubmit:ws:<workspace_id>`             | 30 / hour              |

Above limits → `429 Too Many Requests` with a `Retry-After` header.

---

## Email enumeration posture

- `signup` with an existing email returns the same `201` shape as a
  fresh signup. The duplicate triggers a *"you already have an
  account"* email instead of a verification email.
- `forgot-password` always returns `202` regardless of whether the
  email exists.
- `login` returns `400` *"invalid credentials"* without distinguishing
  no-such-email from wrong-password (only the rate-limit counter
  knows).

---

## Library choices

- `argon2-cffi` — password hashing.
- `secrets` (stdlib) — token generation.
- `itsdangerous` — **not** used; tokens are stored in DB, not signed.
- `fastapi-users` — **rejected** (see ADR 059).
- Email delivery uses Resend ([`email.md`](email.md)).

---

## Cross-references

- [ADR 059 — Auth model](../../../adr/059-auth-model.md)
- [`schema.md`](schema.md) — `users`, `sessions`, `*_tokens`, `auth_rate_limits` tables.
- [`api.md`](api.md) — auth endpoint surface.
- [`security.md`](security.md) — broader security posture.
- [`email.md`](email.md) — verification / reset / invitation delivery.
