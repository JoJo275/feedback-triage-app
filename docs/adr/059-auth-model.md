# ADR 059: Authentication model — cookie sessions + Argon2id

## Status

Accepted

## Context

v1.0 has no authentication. v2.0 introduces user accounts, multi-tenant
workspaces (see [ADR 060](060-multi-tenancy-workspace-scoping.md)), and
team-member invitations. Two model families were considered:

1. **Cookie-based server sessions.** Random opaque token issued at
   login, stored in an HTTP-only secure cookie, looked up against a
   `sessions` row in Postgres on every request. Logout revokes the
   row. Trivial to revoke, trivial to rotate, trivial to invalidate
   on password change.
2. **JWT (signed bearer tokens).** Stateless. Token carries claims;
   server verifies signature. Revocation requires either a blacklist
   table (defeats statelessness) or short TTL + refresh tokens
   (introduces a second token model).

For SignalNest's traffic profile (one Postgres, single FastAPI
process, target user count ≪ 10k for v2.0), the supposed scaling
benefit of JWT is irrelevant. The supposed UX benefit (no DB lookup
per request) costs ~0.3 ms when the session row is indexed.
Meanwhile, JWT failure modes — accidentally readable claims,
algorithm-confusion attacks (`alg=none`), expiration handling, refresh
rotation, revocation — are exactly the kind of subtle correctness
problems a small project should not own.

[ADR 050](050-sync-db-driver-v1.md) keeps the sync DB driver. Cookie
sessions need exactly one synchronous DB lookup per request via
`get_db`, which fits the existing session-per-request pattern from
[ADR 048](048-session-per-request.md).

## Decision

**Cookie-based server sessions.** The full state machine and rules:

### Tables

```sql
-- Platform-level user account (one row per real human + the demo user).
CREATE TABLE users (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email           citext NOT NULL UNIQUE,
    password_hash   text   NOT NULL,            -- Argon2id, encoded
    is_verified     boolean NOT NULL DEFAULT false,
    role            user_role_enum NOT NULL DEFAULT 'team_member',
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

-- Active sessions. One row per active login per device.
CREATE TABLE sessions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      text NOT NULL,                 -- SHA-256 of the cookie value
    user_agent      text NULL,
    ip_inet         inet NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    last_seen_at    timestamptz NOT NULL DEFAULT now(),
    expires_at      timestamptz NOT NULL,
    revoked_at      timestamptz NULL
);
CREATE INDEX sessions_token_hash_idx ON sessions (token_hash) WHERE revoked_at IS NULL;
CREATE INDEX sessions_user_id_idx    ON sessions (user_id)    WHERE revoked_at IS NULL;

-- Tokens for email confirmation and password reset.
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

CREATE TYPE user_role_enum AS ENUM ('admin', 'team_member', 'demo');
```

The platform `role` is **separate** from the per-workspace role
(see [ADR 060](060-multi-tenancy-workspace-scoping.md)). `admin` is
the project author with cross-workspace access. `demo` is read-only
across the demo workspace. Everyone else is `team_member` and gets
their permissions from `workspace_memberships`.

### Cookie

- Name: `signalnest_session`.
- Value: 256 bits of `secrets.token_urlsafe(32)`. Server stores
  `sha256(value)` in `sessions.token_hash`; raw token is never
  persisted.
- Attributes: `HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=604800`
  (7 days, sliding window — `expires_at` extended on each request).
- `Secure` is enforced in production (`SECURE_COOKIES=true` env). In
  local dev over HTTP it's relaxed via the same flag.

### Password hashing

- **Argon2id** via [`argon2-cffi`](https://pypi.org/project/argon2-cffi/).
  Parameters: `time_cost=3, memory_cost=64*1024, parallelism=4`
  (~250 ms on a Railway hobby instance — slow enough to deter brute
  force, fast enough to not DoS legit logins).
- Hashes are upgraded automatically on next login if parameters
  change (`argon2-cffi`'s `check_needs_rehash`).
- `passlib` is **not** used. The library is in long-term maintenance
  and `argon2-cffi` direct usage is simpler.

### Token TTLs and behaviour

| Token                        | TTL      | Single-use | On reuse                                      |
| ---------------------------- | -------- | ---------- | --------------------------------------------- |
| Session cookie               | 7 days, sliding | No (rotated on password change) | Existing sessions for the user are revoked when password changes. |
| Email verification           | 24 hours | Yes        | 410 Gone. New token must be requested.        |
| Password reset               | 1 hour   | Yes        | 410 Gone. **Existing sessions are revoked** when reset is consumed. |
| Workspace invitation (ADR 060) | 7 days | Yes        | 410 Gone. Inviter can re-issue.                |

### Endpoints

```
POST /api/v1/auth/signup              { email, password, workspace_name? }  -> 201
POST /api/v1/auth/login               { email, password }                   -> 200 + Set-Cookie
POST /api/v1/auth/logout                                                    -> 204 + clear cookie
POST /api/v1/auth/logout-everywhere                                         -> 204 (revokes all sessions for user)
GET  /api/v1/auth/me                                                        -> { user, memberships }
POST /api/v1/auth/verify-email        { token }                             -> 200
POST /api/v1/auth/resend-verification                                       -> 202 (always, no enumeration)
POST /api/v1/auth/forgot-password     { email }                             -> 202 (always)
POST /api/v1/auth/reset-password      { token, new_password }               -> 200, revokes other sessions
POST /api/v1/auth/change-password     { current_password, new_password }    -> 200, revokes other sessions
```

### Rate limiting

- Login: 5 failures per email **and** per IP per 15 minutes →
  `429 Too Many Requests`. Counters live in Postgres
  (`auth_rate_limits` table) until Redis is justified.
- Password-reset request: 3 per email per hour.
- Verification email resend: 3 per email per hour.
- Counters are best-effort; they're not a distributed lock.

### Email enumeration

- Signup with an existing email returns the **same 202 response** as a
  successful signup. The duplicate triggers a "you already have an
  account" email instead of a verification email.
- `forgot-password` always returns 202 regardless of whether the
  email exists.
- Login distinguishes "no such email" from "wrong password" only in
  the rate-limit counter, not in the response (both return
  `400 Bad Request` with `"invalid credentials"`).

### Library choices

- `argon2-cffi` — password hashing.
- `secrets` (stdlib) — token generation.
- `itsdangerous` — **not** used; tokens are stored in DB, not signed.
- `fastapi-users` — **rejected**. Adoption ties the auth model to
  that library's release cadence and adds a layer between the auth
  state machine and the DB. Hand-rolled is ~400 lines and stays in
  the codebase.
- Email delivery uses Resend (see [ADR 061](061-email-provider-resend.md)).

## Alternatives Considered

### JWT (HS256 or RS256) with refresh tokens

Stateless bearer tokens.

**Rejected because:** revocation costs are real (every meaningful auth
flow — password change, logout, suspension — needs a blacklist or
short TTL + refresh dance), the implementation footprint is bigger,
and the failure modes are subtler. Cookie sessions cost one indexed
DB lookup per request and avoid every JWT-specific footgun.

### `fastapi-users`

Drop-in auth package.

**Rejected because:** ties the auth state machine to a third-party
release cadence; v2.0 needs custom flows (workspace creation on
signup, demo-account login flow, invitation acceptance) that don't
map cleanly to the package's defaults. Hand-rolled wins on
flexibility for ~400 LOC.

### `bcrypt` for passwords

The classic.

**Rejected because:** Argon2id is the OWASP 2025 default and
`argon2-cffi` is well-maintained. bcrypt remains acceptable but
provides no advantage here.

### Magic-link login (passwordless)

Email-only.

**Rejected for v2.0 because:** doubles email delivery dependency
(every login requires Resend), reduces accessibility for users with
flaky email providers, and introduces a second auth path on top of
password login that makes the demo-account flow more complex.
Acceptable as a v3.0 addition.

## Consequences

### Positive

- One auth model, written once, audited once.
- Revocation is `UPDATE sessions SET revoked_at = now()` —
  trivially correct.
- Password change can revoke sibling sessions atomically in the same
  transaction.
- No separate refresh-token model.
- Audit-friendly: `sessions` rows record IP and user-agent.

### Negative

- One DB lookup per authenticated request. Negligible at v2.0 scale;
  must revisit if Postgres becomes the bottleneck.
- Cookie attribute correctness is on us — a misconfigured
  `SameSite=None` without `Secure` is a real footgun. Mitigated by
  centralizing cookie issuance in `auth/cookies.py`.
- Rate-limit counters in Postgres are crude. Acceptable for v2.0; if
  the app sees abuse, swap for Redis token-bucket (its own ADR).

### Neutral

- Demo and admin accounts use the same auth machinery.

### Mitigations

- A single `auth/cookies.py` module sets/clears the cookie; no other
  code touches `Set-Cookie`.
- Integration tests cover every state-machine transition (signup →
  verify, login → logout, forgot → reset, reset revokes other
  sessions, login rate limit, etc.).
- Bandit + ruff custom rules flag direct `Set-Cookie` headers
  outside `auth/cookies.py`.

## Implementation

- `src/feedback_triage/auth/` — module with `cookies.py`, `hashing.py`,
  `tokens.py`, `state_machine.py`, `routes.py`, `dependencies.py`.
- `alembic/versions/<rev>_add_auth_tables.py` — schema migration.
- `tests/test_auth_signup.py`, `test_auth_login.py`,
  `test_auth_password_reset.py`, `test_auth_email_verification.py`,
  `test_auth_rate_limit.py`.
- `tests/e2e/test_auth_smoke.py` — Playwright smoke for signup →
  verify → login → logout.

## References

- [ADR 048: Session-per-request DB lifecycle](048-session-per-request.md)
- [ADR 050: Sync DB driver in v1.0](050-sync-db-driver-v1.md)
- [ADR 060: Multi-tenancy / workspace scoping](060-multi-tenancy-workspace-scoping.md)
- [ADR 061: Email provider — Resend](061-email-provider-resend.md)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Argon2id parameters guidance (OWASP)](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#argon2id)
