# v2.0 — Email Integration

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Authoritative decision record:
> [ADR 061 (Accepted 2026-05-04)](../../../adr/061-resend-email-fail-soft.md).

Provider: **Resend**, called over plain HTTP via `httpx` (no vendor
SDK — keeps the runtime image lean, per ADR 061).

---

## Failure mode (fail-soft)

Email is sent **synchronously inside the request** but is wrapped in
`try/except`. Failures do **not** roll back the originating
transaction.

| Trigger                       | If Resend fails…                                                                                                       |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Signup → verification email   | User row is committed. UI tells them to use *"resend verification"* if no email arrives. Failure is logged with a correlation id. |
| Forgot-password               | Reset token row is committed. UI shows generic 202. (User can re-request.)                                              |
| Invitation                    | Invitation row is committed. UI shows the invite URL inline so the owner can copy it.                                   |
| Status-change → submitter     | Status change is committed. Email failure is logged; no retry queue in v2.0.                                            |

A background-retry queue (with a separate worker, dead-letter table,
exponential backoff) is a deliberate v3.0 deferral.

---

## Templates

HTML templates in `src/feedback_triage/email/templates/*.html`,
rendered with **Jinja2** (the autoescaping `Environment` from
`jinja2`, already pulled in as a transitive dep of
`fastapi[standard]`). Inline CSS, table-based layout for client
compatibility. Rationale: Jinja autoescapes user-supplied context
(invitee name, workspace name) into HTML attributes safely, where
`str.format` would either silently double-render `{` characters in
inline CSS or require manual `html.escape` at every callsite. Per
[ADR 014](../../../adr/014-no-template-engine.md) Jinja is allowed
**for email only** — application HTML is still hand-written and
served via `StaticFiles`.

Templates needed for v2.0:

- `verification.html` — verify your email
- `verification_already.html` — *"you already have an account"* (sent
  when signup hits an existing email; supports the no-enumeration
  posture from [`auth.md`](auth.md))
- `password_reset.html` — reset your password
- `invitation.html` — *"<inviter> invited you to <workspace>"*
- `status_change.html` — *"your feedback was marked <status>"* (only
  fires for `submitter.email IS NOT NULL` and only on transitions
  to `accepted`, `planned`, `shipped`)

The `EmailClient.send(purpose, to, context, ...)` method in
`src/feedback_triage/email/client.py` is the single point of
delivery — purpose → template + subject mapping lives there, and
nothing else calls the Resend API directly.

---

## Sender addresses

- `noreply@signalnest.app` — verification, reset, invitations.
- `notifications@signalnest.app` — status-change emails.

DNS records (SPF, DKIM, DMARC) are provisioned via Cloudflare and
are the author's responsibility outside the codebase.

---

## Volume snapshot

Estimated v2.0 volume well under 1k emails / month → Resend's free
tier (3,000 / month) covers it indefinitely. Provider comparison
table lives in [`tooling.md`](tooling.md).

---

## Cross-references

- [ADR 061 — Resend email provider + fail-soft](../../../adr/061-resend-email-fail-soft.md).
- [`auth.md`](auth.md) — verification / reset / invitation TTLs.
- [`security.md`](security.md) — secret handling for `RESEND_API_KEY`.
- [`rollout.md`](rollout.md) — production DNS prerequisites.
