# v2.0 — Risk register

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Companion to [`security.md`](security.md) (engineering controls)
> and [`business.md`](business.md) (product / market risks).

This file is the consolidated, prioritized list of known risks for
v2.0. Each row names the risk, scores its likelihood and impact,
links to the mitigation, and names the canary that detects when the
risk fires.

When a row's mitigation lands, **do not delete the row** — change
its status to **Mitigated** so the trail is preserved.

---

## Severity scale

- **Likelihood** — Low / Med / High (subjective, given current
  controls).
- **Impact** — Low / Med / High (data loss, user trust, downtime,
  security).
- **Severity** = max of the two; ties break to Impact.

---

## Engineering risks

| #   | Risk                                              | L | I | Severity | Mitigation                                                                  | Canary                                            |
| --- | ------------------------------------------------- | - | - | -------- | --------------------------------------------------------------------------- | ------------------------------------------------- |
| E1  | Cross-tenant data leak (read or write)            | L | H | High     | `WorkspaceContext` on every scoped route ([`multi-tenancy.md`](multi-tenancy.md)). RLS deferred but reserved. | `tests/api/test_isolation.py` — cross-tenant returns 404. |
| E2  | Session hijack via stolen cookie                  | L | H | High     | `HttpOnly`, `Secure`, `SameSite=Lax`, rolling renewal, IP+UA logged on issue. | `auth.md` integration test: refused cookie after revoke. |
| E3  | Argon2id parameters too weak / too slow            | L | M | Med      | [ADR 059](../../../adr/059-auth-model.md) pins parameters; benchmark in CI. | Bench script under `scripts/`; alert if > 250ms.  |
| E4  | Public form spam abuse                            | M | M | Med      | Honeypot field + per-IP rate limit + workspace-owner kill switch.           | `tests/api/test_public_submit.py` — non-empty honeypot dropped. |
| E5  | Email provider (Resend) outage                    | L | M | Med      | Fail-soft send ([`email.md`](email.md)); user-facing action still succeeds. | `email_log` row recorded with error.             |
| E6  | Status-change email not sent (silent loss)        | L | M | Med      | Every send writes `email_log` regardless of outcome.                        | Insights surface counts `email_log` failures.     |
| E7  | Alembic autogenerate misses an enum / CHECK       | M | H | High     | Hand-review every migration; round-trip `upgrade`/`downgrade` in CI.        | `task check` runs round-trip.                     |
| E8  | Postgres outage                                    | L | H | High     | `/health` and `/ready` distinguish liveness from DB reachability.           | `task check` requires `/ready` 200.               |
| E9  | Session-per-request invariant violated (sessions reused across requests) | L | H | High | `get_db` is the only DI; no module-level sessions; `expire_on_commit=False`. | `test_patch_then_get_returns_fresh_state` canary ([`../spec-v1.md`](../spec-v1.md)). |
| E10 | CSRF on cookie-auth POST                          | L | M | Med      | `SameSite=Lax` covers v2.0; CSRF token deferred until cross-origin surface exists. | Same-origin only check in middleware test.   |
| E11 | XSS via user-submitted content                    | L | H | High     | Server-rendered HTML escapes by default; CSP blocks inline; ADR 067 to land. | Playwright e2e renders feedback with `<script>`. |
| E12 | Container image runs as root                      | L | M | Med      | `Containerfile` USER non-root; `HEALTHCHECK` configured.                    | container-structure-test runs in CI.              |
| E13 | Secret committed by accident                      | L | H | High     | gitleaks pre-commit hook; CI runs it on PRs.                                | gitleaks step in `task check`.                    |
| E14 | Dependency confusion / supply-chain               | L | M | Med      | `uv.lock` committed; CI uses `--frozen`; pip-audit pre-commit; Dependabot.  | `task check` includes pip-audit.                  |
| E15 | Backfill migration partial-succeeds, leaves NULL `workspace_id` | M | H | High | ADR 062 splits backfill from `NOT NULL` flip; deploy gates on `count(workspace_id IS NULL) = 0`. | Pre-deploy script asserts the count.       |
| E16 | Public roadmap / changelog leaks an unpublished item | L | M | Med   | Every public read filters by `published_*`. Test asserts mixed-state workspace renders only published rows. | `tests/api/test_public_roadmap.py`. |
| E17 | Dark-mode CSS regression vs. light-mode           | M | L | Med      | `/styleguide` renders both modes side-by-side; visual review pre-merge.    | Manual on `/styleguide`; e2e screenshot diff (Phase 4). |

---

## Product / business risks

(Restated from [`business.md`](business.md) for one-stop scanning.
The authoritative version lives there.)

| #   | Risk                                                | L | I | Severity | Mitigation                                                                   |
| --- | --------------------------------------------------- | - | - | -------- | ---------------------------------------------------------------------------- |
| P1  | Author burnout / project pause                      | M | M | Med      | Free tier; no SLA; codebase usable as a personal install indefinitely.       |
| P2  | Trademark conflict on "SignalNest"                  | L | L | Low      | Pre-launch trademark check is a release-gate task.                           |
| P3  | GDPR / data-subject request before legal entity     | L | H | High     | Privacy page commits to a single contact email; deletion is manual SQL.      |
| P4  | Insufficient differentiation vs. Canny / Productboard | M | M | Med    | "Triage step before issue tracker" wedge ([`business.md`](business.md)).      |
| P5  | Resend deliverability tanks (spam folder)           | L | M | Med      | Fail-soft + visible `email_log` failures + monitor manually for first 30d.   |
| P6  | Feature creep before v2.0 ratification              | M | M | Med      | Phase gates in [`implementation.md`](implementation.md); deferral list in [`../spec-v2.md`](../spec-v2.md). |

---

## Operational risks

| #   | Risk                                              | L | I | Severity | Mitigation                                                                  |
| --- | ------------------------------------------------- | - | - | -------- | --------------------------------------------------------------------------- |
| O1  | Railway service deletion / billing lapse          | L | H | High     | One designated payment method; backups exported off-platform monthly.       |
| O2  | Domain hijack / lapse                             | L | H | High     | Domain registrar with 2FA; auto-renew on; expiry calendar reminder.         |
| O3  | Demo workspace pollutes production                | L | L | Low      | Demo workspace is read-only via app logic; nightly reset job (ADR 075).     |
| O4  | Manual deploy mistake (wrong env, missing secret) | M | M | Med      | Railway pre-deploy command runs `alembic upgrade head`; CI required check.  |
| O5  | Logs leak PII (email addresses)                   | L | M | Med      | `middleware.py` request logger redacts known headers; emails not logged at info level. |

---

## Acceptance criteria for ratification

v2.0 cannot flip to **Ratified** while any **High-severity** row
is unmitigated. **Med-severity** rows must have a named mitigation
(not "TBD") and at least one canary, even if the canary is manual.
**Low-severity** rows are tracked but do not gate ratification.

---

## Cross-references

- [`security.md`](security.md) — engineering controls behind E1–E17.
- [`business.md`](business.md) — full context for P1–P6.
- [`rollout.md`](rollout.md) — operational rollout that O1–O5 ride
  on top of.
- [`adrs.md`](adrs.md) — ADRs that close out specific risk rows.
- [`implementation.md`](implementation.md) — phase gates that
  reference this register.
