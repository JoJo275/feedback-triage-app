# v2.0 — Email Integration

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Authoritative decision record:
> ADR 061 (TBD; see [`../spec-v2.md`](../spec-v2.md#adrs-to-write-for-v20)).

Provider: **Resend**, via the `resend` Python SDK from PyPI.

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

Plain HTML strings in `src/feedback_triage/email/templates/*.html`.
Inline CSS, table-based layout for client compatibility. No
templating engine beyond `str.format` substitution. Content kept
short and transactional.

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

A small `email.send(template_name, to, ctx)` helper in
`src/feedback_triage/email/sender.py` is the single point of
delivery; nothing else calls the Resend SDK directly.

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

- ADR 061 (TBD).
- [`auth.md`](auth.md) — verification / reset / invitation TTLs.
- [`security.md`](security.md) — secret handling for `RESEND_API_KEY`.
- [`rollout.md`](rollout.md) — production DNS prerequisites.
