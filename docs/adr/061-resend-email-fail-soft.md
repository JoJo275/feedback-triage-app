# ADR 061: Email provider (Resend) + fail-soft semantics + `email_log` table

## Status

Accepted (2026-05-04). Phase gate: **Alpha** — every code path that
sends mail (account verification, password reset, workspace
invitation, status-change notification) blocks on this ADR; Phase 1
**Migration A** creates the `email_log` table defined here.

## Context

v2.0 introduces email-bearing flows for the first time
([`v2/email.md`](../project/spec/v2/email.md),
[`v2/auth.md`](../project/spec/v2/auth.md)):

- **Account verification** on sign-up.
- **Password reset** on the forgot-password flow.
- **Workspace invitation** when an owner invites a teammate.
- **Status-change notification** to the original submitter when a
  team member moves a feedback item between workflow states (Phase 3).

Email is on the critical path of "can a user even use the product?"
(verification gates login under `auth.email_verified_required = true`)
but is *not* the action itself. The product contract is **"the
user-facing action succeeds; the email is best-effort logged."** A
deliverability outage at the provider must not break sign-up, must
not leak provider state into the response, and must leave a forensic
trail an operator can replay.

We need to lock four decisions before any sending code lands:

1. **Provider** — which transactional email provider.
2. **Fail-soft semantics** — what happens when the provider returns
   5xx, 429, network timeout, or a 4xx that is not an auth error.
3. **`email_log` table shape** — what gets persisted, indexed, and
   shown to operators (and not to end-users).
4. **Test strategy** — how unit and integration tests avoid hitting
   the provider while still exercising the logging path.

## Decision

### 1. Provider — **Resend**

Resend is the email provider for v2.0. Tested API wrapper lives at
`src/feedback_triage/email/client.py`; HTML templates live at
`src/feedback_triage/email/templates/` (Jinja for email only —
**not** for app HTML, per ADR 014).

**Configuration (Railway secrets, never logged):**

```env
RESEND_API_KEY=re_xxx               # secret
RESEND_FROM_ADDRESS=no-reply@signalnest.app
RESEND_DRY_RUN=0                    # 1 in test, 0 everywhere else
RESEND_TIMEOUT_SECONDS=5
RESEND_MAX_RETRIES=2                # in-process; not a queue
```

`RESEND_API_KEY` is required when `FEATURE_AUTH=true` and
`RESEND_DRY_RUN=0`. App boot fails fast with a clear error if
either is missing.

### 2. Fail-soft semantics

Every send is wrapped in a try/except that maps provider outcomes
to one of four `email_log.status` values:

| Outcome                                 | `status`     | App behavior                                  |
| --------------------------------------- | ------------ | --------------------------------------------- |
| 2xx from Resend                         | `sent`       | The user-facing flow succeeds; row written.   |
| 4xx auth error (401, 403)               | `failed`     | Logged with `error_code`; raise on boot only — never on a request thread (would let provider misconfig break sign-up). The user-facing flow still succeeds. |
| 4xx validation (422 — bad address)      | `failed`     | Row written; user-facing flow still succeeds; surface "we could not send mail to that address" only on the verify-email resend path. |
| 4xx rate limit (429)                    | `retrying`   | Sleep + retry up to `RESEND_MAX_RETRIES`; on final failure, write `failed`. |
| 5xx / network timeout / connection err  | `retrying`   | Same as 429.                                  |
| Everything else                         | `failed`     | Row written; flow still succeeds; alarm fires via `email_log` lag check. |

**Critical invariant:** the user-visible response body **never**
references provider state. No "your verification email is on its
way" if we know it failed; the auth.md no-enumeration copy already
reads "If an account exists, you'll receive an email" — that copy
is provider-state-independent by design.

Retries are **in-process only**. v2.0 does not introduce a queue.
If three attempts fail, the row stays at `failed` and the operator
re-runs `task email:replay <email_log_id>` (Phase 3 deliverable).

### 3. `email_log` table shape

Created by **Migration A** (Phase 1 schema migration), per
[`v2/schema.md`](../project/spec/v2/schema.md) and
[`v2/migration-from-v1.md`](../project/spec/v2/migration-from-v1.md):

```sql
CREATE TYPE email_status_enum  AS ENUM ('queued', 'sent', 'retrying', 'failed');
CREATE TYPE email_purpose_enum AS ENUM (
  'verification',
  'password_reset',
  'invitation',
  'status_change'
);

CREATE TABLE email_log (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    UUID        NULL REFERENCES workspaces(id) ON DELETE SET NULL,
  user_id         UUID        NULL REFERENCES users(id)      ON DELETE SET NULL,
  to_address      TEXT        NOT NULL CHECK (length(to_address) <= 320),
  purpose         email_purpose_enum NOT NULL,
  template        TEXT        NOT NULL CHECK (length(template) <= 64),
  subject         TEXT        NOT NULL CHECK (length(subject) <= 256),
  status          email_status_enum NOT NULL DEFAULT 'queued',
  provider_id     TEXT        NULL CHECK (length(provider_id) <= 128),  -- Resend message id
  error_code      TEXT        NULL CHECK (length(error_code) <= 64),
  error_detail    TEXT        NULL CHECK (length(error_detail) <= 1024),
  attempt_count   SMALLINT    NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  sent_at         TIMESTAMPTZ NULL,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX email_log_workspace_idx ON email_log (workspace_id, created_at DESC);
CREATE INDEX email_log_status_idx    ON email_log (status, created_at DESC)
  WHERE status IN ('queued', 'retrying', 'failed');
CREATE INDEX email_log_purpose_idx   ON email_log (purpose, created_at DESC);
```

Notes:

- `workspace_id` and `user_id` are nullable because verification
  sends predate either record being committed (we log on best-effort
  even when the row is for a not-yet-verified user). Where a row
  exists, the FK is set.
- `to_address` is stored as plaintext for forensic replay; PII
  retention is governed by [`v2/security.md`](../project/spec/v2/security.md)
  (90 days, then nightly purge job — Phase 3 Should).
- Body is **not** stored. Templates are content-addressable by name
  and revision via git; replay re-renders from the current template.
- Partial index on non-terminal statuses keeps the operator
  "stuck queue" query cheap.
- `updated_at` is bumped by a `BEFORE UPDATE` trigger, same
  pattern as `feedback_item` (project-wide convention).

### 4. Test strategy

- **Unit tests** set `RESEND_DRY_RUN=1` via the standard test
  fixture. The client's `send()` short-circuits before the HTTP
  call but still writes the `email_log` row with
  `status='sent'` and `provider_id='dry-run-<uuid>'`. Tests assert
  on the row.
- **Integration tests** that exercise auth flows use the same
  fixture; `tests/api/test_auth_no_enumeration.py` asserts the
  response body is identical whether or not a user exists, *and*
  that an `email_log` row exists in the existing-user case but
  not in the unknown-address case.
- **Provider-down canary** — a single test injects a fake client
  that raises `httpx.ConnectError`; flow must still return 200 and
  the row must land at `status='failed'` after retries.
- **No live network calls in CI**, ever. `RESEND_DRY_RUN=0` is set
  only on Railway environments.

## Alternatives Considered

### Postmark

Comparable deliverability and a slightly cleaner template console.

**Rejected because:** Resend's pricing tier is friendlier at our
scale (3,000 emails/month free vs Postmark's 100/month free), the
SDK is plain HTTP (we can avoid a vendor SDK entirely), and the
DX of one-shot transactional sends is closer to the contract we
want.

### SendGrid

Industry default.

**Rejected because:** heavier API surface than we need, historical
deliverability issues with shared IPs at the free tier, and the
SDK pulls more transitive deps than we want in the runtime image.

### SMTP-direct (e.g. Gmail relay, AWS SES SMTP)

Cheapest possible path.

**Rejected because:** SMTP error semantics are looser than HTTP
JSON, retry/backoff is harder to reason about, and we'd have to
own warming and reputation. Out of scope for v2.0.

### Hard-fail on provider error

"If we can't send mail, the action fails."

**Rejected because:** it makes Resend a single point of failure
for sign-up. A 30-second Resend incident would translate to a
30-second sign-up outage. Fail-soft + replay is the standard
contract for transactional mail.

### Background queue (Celery / RQ / Postgres-backed)

Decouple send from request thread.

**Rejected for v2.0 because:** adds a worker process, a broker,
and operational overhead the project explicitly defers
([`v2/risks.md`](../project/spec/v2/risks.md) — RZ defer-queue).
In-process retries cover the failure modes we actually see at our
scale; revisit if `email_log.status='retrying'` ever exceeds 1 %
of sends sustained over 24h.

## Consequences

### Positive

- Sign-up, reset, and invite flows are decoupled from provider
  uptime — Resend can be down and users still get accounts.
- `email_log` gives operators a single table to grep when a user
  reports "I never got the email" — the row is either there
  (deliverability problem) or it isn't (app-side bug).
- DRY_RUN mode means the test suite exercises the logging path
  without the network, which is both faster and CI-safe.
- Cost is bounded — Resend's free tier covers the foreseeable
  pre-launch volume, and the partial index keeps stuck-queue
  queries cheap as the table grows.

### Negative

- Two more enums + one more table to migrate. Migration A is the
  single largest schema migration in the v1 → v2 jump.
- A failed verification email is a soft failure the user only
  notices when they try to log in. The "resend verification"
  affordance on the login page is now mandatory, not optional —
  see [`v2/auth.md`](../project/spec/v2/auth.md).
- `to_address` retention is a real PII surface. The 90-day purge
  job is Phase 3; until then operators must treat the table as
  sensitive.

### Neutral

- We could swap providers (Postmark, SES) by reimplementing
  `email/client.py`. The `email_log` shape is provider-agnostic.

### Mitigations

- The boot-time check on `RESEND_API_KEY` catches the most
  common deploy mistake (forgot to set the secret) before any
  request ever hits the app.
- An ops alarm (Phase 3 deliverable) fires if
  `count(*) WHERE status IN ('retrying','failed') AND created_at > now() - interval '15 minutes'`
  exceeds a threshold.
- The PII retention job is tracked as a Phase 3 Must in
  [`v2/implementation.md`](../project/spec/v2/implementation.md).

## Implementation

Phase 1 deliverables (paths planned, files not yet created):

- `src/feedback_triage/email/client.py` — Resend HTTP wrapper, retry loop, `email_log` writes
- `src/feedback_triage/email/templates/` — Jinja templates (`verification.html`, `verification_already.html`, `password_reset.html`, `invitation.html`, `status_change.html` Phase 3)
- `tests/api/test_auth_no_enumeration.py` — DRY_RUN + log-row asserts

Existing references:

- [docs/project/spec/v2/email.md](../project/spec/v2/email.md) — full surface
- [docs/project/spec/v2/schema.md](../project/spec/v2/schema.md) — `email_log` columns and indexes
- [docs/project/spec/v2/migration-from-v1.md](../project/spec/v2/migration-from-v1.md) — Migration A includes `email_log`

## References

- [Resend HTTP API](https://resend.com/docs/api-reference)
- [`v2/auth.md`](../project/spec/v2/auth.md) — no-enumeration copy that the fail-soft contract enables
- [`v2/security.md`](../project/spec/v2/security.md) — PII retention
- [`v2/risks.md`](../project/spec/v2/risks.md) — RZ (defer queue), RA (provider risk)
- [ADR 014](014-no-template-engine.md) — why Jinja is allowed for email only
