# v2.0 — Security

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).

Cross-cutting security posture for v2.0. Topics that have a
dedicated home (auth state machine, multi-tenancy invariants) link
out rather than duplicate. Aligned with the OWASP Top 10 categories
called out in `.github/copilot-instructions.md`.

---

## Threat model summary

| # | Threat                                              | Primary defense                                              | Where                                |
| - | --------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------ |
| 1 | Cross-tenant data leakage                           | `WorkspaceContext` dependency + canary tests                 | [`multi-tenancy.md`](multi-tenancy.md) |
| 2 | Credential stuffing / brute-force login             | Argon2id + per-email/per-IP rate limits                      | [`auth.md`](auth.md)                 |
| 3 | Session hijack                                      | HttpOnly+Secure+SameSite=Lax cookie; SHA-256-hashed token store | [`auth.md`](auth.md)              |
| 4 | Email enumeration                                   | Identical 202 responses for signup-with-existing and forgot-password | [`auth.md`](auth.md)         |
| 5 | Token reuse / replay                                | Single-use tokens, hashed at rest, 410 Gone on reuse         | [`auth.md`](auth.md)                 |
| 6 | XSS in user-submitted content                       | Strict template escaping; CSP header                         | this file                            |
| 7 | CSRF on state-changing endpoints                    | SameSite=Lax cookie + same-origin fetch; CSRF token planned for cross-origin (deferred) | this file |
| 8 | Public-form abuse / spam                            | Honeypot + per-IP/per-workspace rate limits                  | this file + [`auth.md`](auth.md)     |
| 9 | SQL injection                                       | Bound parameters everywhere; no string-concatenated SQL      | this file                            |
| 10| Secret exposure                                     | `pydantic-settings` from env; no secrets in repo             | this file                            |

---

## Tenant isolation invariants

Restated from [`multi-tenancy.md`](multi-tenancy.md) because tenant
isolation is the **#1 v2.0 risk**:

- Every tenant-scoped table carries `workspace_id uuid NOT NULL`
  with FK + index.
- Every CRUD route depends on `WorkspaceContext`.
- Every `select(...)` against a tenant-scoped table includes
  `Model.workspace_id == ctx.id`.
- A canary test (`tests/api/test_isolation.py`) attempts cross-
  tenant reads and asserts 404. **Failing this test fails the
  build.**

Defense-in-depth via Postgres RLS is deferred to a follow-on ADR
([ADR 060](../../../adr/060-multi-tenancy-workspace-scoping.md)
discussion).

---

## Authentication & session security

Full details in [`auth.md`](auth.md). Headlines:

- Password hashing: Argon2id (`time_cost=3, memory_cost=64*1024,
  parallelism=4`).
- Session token: 256 bits of `secrets.token_urlsafe(32)`; only the
  SHA-256 lives in the DB.
- Cookie: `HttpOnly; Secure; SameSite=Lax; Max-Age=604800`.
- Centralized in `auth/cookies.py`; no other code sets `Set-Cookie`.

---

## Rate limits

Catalogued in [`auth.md`](auth.md). Stored in
`auth_rate_limits`. Verdict: best-effort, not a distributed lock.
Acceptable for v2.0 single-instance Railway deployment; if abuse
emerges or horizontal scaling lands, swap for Redis token-bucket
(its own ADR).

---

## Public submission abuse

The public submission form is the only unauthenticated **write**
endpoint. Defenses:

- Honeypot field: a hidden `<input name="website">` styled
  `display:none`. Bots fill it; humans don't. Non-empty value →
  silently `202` and the row is dropped.
- Per-IP rate limit: 10 / hour.
- Per-workspace rate limit: 30 / hour (so one bad actor can't
  exhaust a workspace).
- Hard content limits at the schema layer (description ≤ 4000,
  email ≤ 254, name ≤ 120). Enforced both in Pydantic and in DB
  CHECK constraints.

Captcha is **not** introduced for v2.0. If the honeypot + rate
limits prove insufficient, hCaptcha is the planned next step (its
own ADR).

---

## CSRF posture

State-changing endpoints accept JSON over `fetch` from the same
origin. The session cookie is `SameSite=Lax`, which blocks cross-
site cookie use on cross-site `<form>` POSTs (the classic CSRF
vector) while permitting same-origin XHR.

A bespoke CSRF token (double-submit cookie) is **not** added in
v2.0 because:

- The frontend is same-origin.
- Cookies are `SameSite=Lax`.
- No third-party site can `fetch(...)` with credentials due to
  CORS (no `Access-Control-Allow-Origin: <origin> + Access-
  Control-Allow-Credentials: true` is configured).

If a public API key surface or a third-party embed is ever added, a
CSRF token becomes mandatory. Tracked as a Future Improvement in
[`../spec-v2.md`](../spec-v2.md#future-improvements-after-v20).

---

## Content security policy

A baseline CSP is sent on every HTML response:

```
Content-Security-Policy:
  default-src 'self';
  img-src 'self' data:;
  style-src 'self';
  script-src 'self';
  object-src 'none';
  base-uri 'self';
  frame-ancestors 'none';
  form-action 'self';
```

No inline scripts, no inline styles. Tailwind generates a single
external `app.css`. The mini demo's JS lives in `static/js/landing-
demo.js` — same-origin.

Headers also set:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  (production only)
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

These headers are added by middleware in
`src/feedback_triage/middleware.py`.

---

## Input validation

Two layers, both required, both must agree:

1. **Pydantic v2 models** at the FastAPI request boundary. Reject
   bad types, bad lengths, bad enum values with `422`.
2. **Postgres CHECK constraints + native enums + FKs.** A bug in
   layer 1 still can't write a row that violates layer 2.

The `(source = 'other') = (source_other IS NOT NULL)` constraint is
a worked example: free-text only allowed when the enum is `other`,
enforced in both the Pydantic validator and the DB CHECK.

---

## SQL injection

- All queries go through SQLModel/SQLAlchemy with bound parameters.
- The one ILIKE search uses a bound `:q` parameter, never string
  interpolation.
- Raw SQL in migrations is reviewed by hand; no parameter ever
  comes from request data in a migration.

ruff `S608` (hardcoded SQL expression) and bandit `B608` are
enabled in pre-commit.

---

## Secrets and configuration

- All secrets read from environment via `pydantic-settings`.
  Required in production: `DATABASE_URL`, `SECRET_KEY`,
  `RESEND_API_KEY`, `SECURE_COOKIES`, `BASE_URL`.
- `.env.example` enumerates every var with a placeholder; no real
  values committed.
- `gitleaks` runs in pre-commit; `bandit` flags hardcoded secret
  patterns.
- Railway holds production secrets; local dev reads from `.env`.

---

## Logging hygiene

- Request logs include `request_id` but never include the request
  body.
- Auth events log `user_id` and IP, **never** passwords or tokens.
- The `email.send` helper logs `template_name` and recipient
  domain (not full address) on success; full address on failure
  (so the operator can re-send manually if needed).
- Cross-tenant access attempts log a structured WARNING.

---

## Dependencies

- `uv lock` is committed; `uv sync --frozen` enforces the lock in
  CI.
- `pip-audit` runs in pre-commit and a daily Dependabot pass
  surfaces upstream advisories.
- Adding a dep that has a known critical CVE fails the gate.

---

## Cross-references

- [`auth.md`](auth.md) — full auth detail.
- [`multi-tenancy.md`](multi-tenancy.md) — full tenant-isolation
  detail.
- [`api.md`](api.md) — endpoint surface.
- [`ui.md`](ui.md) — public form, honeypot.
- [ADR 059 — Auth model](../../../adr/059-auth-model.md)
- [ADR 060 — Multi-tenancy](../../../adr/060-multi-tenancy-workspace-scoping.md)
