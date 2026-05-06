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

---

## Programming security checklist (code-review surface)

A running list of code-level practices reviewers and Copilot must
keep watch on. These are the things a tired author lands by
accident; an in-repo checklist is cheaper than a CVE.

### Secrets and credentials in code

- **Never commit secrets.** No API keys, DB passwords, signing
  keys, JWT secrets, OAuth tokens, SSH keys, `.pem`/`.key` files,
  service-account JSON, webhook signing secrets, or seeded test
  passwords that match a real account anywhere on disk.
- **Read secrets via `pydantic-settings` only.** No new
  `os.environ[...]` reads outside `config.py`. New secret env vars
  are typed as `SecretStr` so `repr(settings)` and Pydantic
  validation errors don't leak them.
- **No secrets in URLs.** `DATABASE_URL` aside (which is the
  driver's contract), do not pass secrets in query strings — they
  end up in access logs, Referer headers, and browser history.
- **No secrets in log lines, exception messages, or error
  responses.** Tokens, passwords, session cookies, full email
  addresses on success paths, and Resend `provider_id` for failed
  sends are all redacted (see "Logging hygiene" above).
- **No secrets in test fixtures committed to the repo.** Use
  `RESEND_DRY_RUN=1`, fake Argon2 params, or generate per-test
  keys in `conftest.py`. The only "password" string allowed in
  the repo is the Argon2 warm-up literal `"warmup"`.
- **`.env` is git-ignored;** `.env.example` is the documented
  surface and contains placeholders only.
- **`gitleaks` runs in pre-commit** and on every PR; a hit blocks
  merge. Rotate any secret that ever lands in a commit, even on a
  branch you immediately delete — git history on a fork or a CI
  artifact is enough to leak it.
- **If a secret leaks: rotate first, write the postmortem
  second.** Order matters.

### Injection-class flaws

- **SQL:** SQLModel/SQLAlchemy with bound parameters everywhere.
  No `f"SELECT ... {value}"`, no `.format()` into raw SQL, no
  `text("... " + var + " ...")`. The one ILIKE search uses a
  bound `:q`. ruff `S608`, bandit `B608`, and code review all
  watch this.
- **Shell:** `subprocess.run([...], shell=False)` with an arg
  list, never `shell=True`, never string concatenation into a
  command. ruff `S602`/`S603`/`S605`/`S607` enforce this.
- **OS commands and paths:** `pathlib.Path` over `os.path`;
  reject `..` and absolute paths in any user-supplied filename
  before joining; resolve and assert the result stays under the
  intended root.
- **Template injection:** Jinja autoescape stays on. Never
  `Markup(user_input)` or `{{ value | safe }}` on user-controlled
  data. Email templates render with autoescape too — display
  names go through `e()`.
- **HTML in JSON responses:** API responses are `application/
  json`; never embed user content into a raw HTML fragment that a
  consumer might `innerHTML` without escaping. The frontend uses
  `textContent` and `setAttribute`, never `innerHTML` for
  user-controlled values.
- **Open redirect:** any `?next=` / `?redirect=` parameter is
  validated against a same-origin allowlist before issuing a 302.
  Reject absolute URLs and protocol-relative `//evil.example`.

### Deserialization and parsing

- **No `pickle` on untrusted bytes.** Period.
- **YAML:** `yaml.safe_load(...)` only. `yaml.load(...)` is
  banned (bandit `B506`).
- **JSON size limits.** FastAPI request bodies are bounded by
  Pydantic field constraints; uploads (when introduced) get an
  explicit `Content-Length` cap. Unbounded JSON is a DoS vector.
- **No `eval` / `exec` / `compile` on user input.** Including
  fancy "expression evaluators" — they always grow into RCE.
- **`tomllib` for TOML, `defusedxml` for XML** if XML ever
  appears (no XML in v2.0).

### Authentication and session handling

- **Argon2id** with the parameters baked into `auth/hashing.py`;
  any change is benchmarked and an ADR records the new numbers.
- **`secrets.token_urlsafe(32)`** for every random token (session,
  verification, reset, invitation). Never `random.*`,
  `uuid.uuid4()`, or `hashlib.md5(time.time())`-style nonsense.
- **Hash tokens at rest.** Sessions and verification/reset/invite
  tokens live in the DB as SHA-256 of the raw value; the raw
  string only crosses the wire once.
- **Single-use tokens** are marked consumed transactionally; reuse
  returns 410 Gone, not 200.
- **Constant-time comparison** for any secret check that doesn't
  go through a hash verifier — `hmac.compare_digest`, never `==`.
- **Cookie attributes are set in one place** (`auth/cookies.py`);
  no other module calls `response.set_cookie`.

### Authorization and tenancy

- **Every tenant-scoped query filters on `workspace_id`.** Missing
  the predicate is the #1 v2.0 risk; `tests/api/test_isolation.py`
  is the canary and must stay green.
- **404, never 403** on cross-tenant access — exposing "this row
  exists in another workspace" is itself a leak.
- **Role checks use `RequireRole(...)` deps**, not ad-hoc `if`s
  inside handlers. Centralised checks are auditable.
- **Don't trust the client.** `user_id`, `workspace_id`, and role
  are read off the session, never off the request body or query
  string.

### HTTP surface and headers

- **CSP, HSTS, `nosniff`, `Referrer-Policy`, `Permissions-Policy`,
  `frame-ancestors 'none'`** are set in middleware; do not silence
  them on a per-route basis.
- **CORS:** explicit allowlist via `cors_allowed_origins`; no
  wildcard with credentials, ever.
- **Methods:** mutating endpoints are `POST` / `PATCH` / `DELETE`,
  never `GET`. `GET` must be safe and idempotent.
- **Rate-limited endpoints** (login, signup, forgot-password,
  public submit) keep their limits even when "just refactoring"
  the route — the limit is part of the contract.

### Cryptography

- **Use the standard library** (`hashlib`, `hmac`, `secrets`) and
  vetted libs (`argon2-cffi`). No hand-rolled crypto, no MD5/SHA1
  for security purposes (SHA-256+ only).
- **Don't invent your own auth tokens** — JWTs, signed cookies,
  and stateful sessions all have well-trodden pitfalls; we use
  stateful sessions on purpose (ADR 059).

### Dependencies and supply chain

- **`uv.lock` is committed**, CI uses `--frozen`, lock drift
  fails the build.
- **`pip-audit` + Dependabot** flag known CVEs daily.
- **GitHub Actions are SHA-pinned** ([ADR 004](../../../adr/004-pin-action-shas.md));
  never `@v3` or a moving tag.
- **No `curl | bash`** in scripts, Containerfiles, or CI. Every
  download is checksum-verified or signature-verified.
- **Do not vendor random snippets from Stack Overflow / a model
  / an issue tracker without reading them.** Especially anything
  that touches subprocess, eval, deserialization, or crypto.

### Frontend specifics

- **Never `innerHTML` a string built from user input.** Use
  `textContent` for text and `setAttribute` for attributes; build
  trees with `document.createElement`.
- **No `eval(...)`, `new Function(...)`, or
  `setTimeout("string", ...)`.** Pass functions, never strings.
- **No third-party CDN for runtime assets.** Tailwind is built at
  image-build time; JS is same-origin under `/static/js/`.
  Adding a CDN needs an ADR (CSP and supply-chain implications).
- **Forms post JSON via `fetch` to same-origin endpoints**;
  cookies are `SameSite=Lax`, so cross-site form POSTs cannot
  authenticate.

### Data handling

- **Validate at the boundary, enforce at the database.** Pydantic
  v2 + Postgres `CHECK` + native enums + FKs. Both layers must
  agree; if they diverge, the bug is the Pydantic layer.
- **Don't log PII you don't need.** Email addresses are logged on
  failure paths only; passwords and tokens never.
- **Errors don't leak structure.** Production responses use
  generic copy ("Invalid email or password.") regardless of which
  half failed; stack traces never reach the client.
- **Tenants don't appear in URLs as integer IDs.** Workspace
  routes use the slug; integer enumeration is a recon vector.

### Things to refuse on review

If you see any of these in a diff, push back and require a
rewrite — they are not "polishable later":

1. A new `os.environ[...]` outside `config.py`.
2. A raw SQL string with `+` or f-string interpolation.
3. `subprocess.run(..., shell=True)` or
   `subprocess.run(some_string)`.
4. `yaml.load(...)` without `Loader=SafeLoader`.
5. `pickle.loads(...)` on anything that crossed a network.
6. `innerHTML = userInput` / `dangerouslySetInnerHTML`.
7. A new endpoint without a Pydantic request model.
8. A tenant-scoped query missing the `workspace_id` predicate.
9. A cookie set outside `auth/cookies.py`.
10. A committed `.env`, `.pem`, `*.key`, or fixture password that
    matches a real account.

### Verification commands

Run before opening a PR:

```text
uv run ruff check src/ scripts/ tests/
uv run bandit -c pyproject.toml -r src/
uv run mypy src/
uv run pip-audit
pre-commit run gitleaks --all-files
uv run pytest tests/api/test_isolation.py -v
```

A green run is necessary, not sufficient. The checklist above is
the part the tooling can't catch.
