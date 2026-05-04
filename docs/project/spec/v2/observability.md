# v2.0 — Observability

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> See also: [`security.md`](security.md), [`rollout.md`](rollout.md),
> [`performance-budgets.md`](performance-budgets.md).

This file defines the **logging, metrics, and request-tracing
contract** for v2.0. It's intentionally minimal: stdout JSON logs,
a request-id header, and a small set of operational metrics.
No APM vendor, no tracing backend, no log aggregator beyond what
Railway gives us for free.

---

## Logging

### Format

- All logs go to **stdout as one JSON object per line**.
- Logger: stdlib `logging` with a custom JSON formatter
  (`src/feedback_triage/logging.py`). Do not pull in `structlog`
  — would need an ADR.
- Log lines never span multiple lines. Tracebacks are rendered
  into a single `exc` string field.

### Required fields

Every line has:

| Field         | Type    | Notes                                                  |
| ------------- | ------- | ------------------------------------------------------ |
| `ts`          | string  | ISO 8601 UTC, `Z` suffix, microsecond precision        |
| `level`       | string  | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL`    |
| `msg`         | string  | Short human-readable message                           |
| `logger`      | string  | Logger name (typically the module path)                |
| `request_id`  | string? | Set on requests; `null` for boot/cron logs             |
| `route`       | string? | FastAPI route template (e.g. `/api/v1/feedback/{id}`)  |
| `method`      | string? | HTTP method                                            |
| `status`      | int?    | Response status                                        |
| `duration_ms` | int?    | Request duration in ms (rounded to int)                |
| `user_id`     | string? | Authenticated user UUID (when known)                   |
| `workspace_id`| string? | Active workspace UUID (when known)                     |
| `error_code`  | string? | When an error envelope is returned, the code           |
| `exc`         | string? | Traceback string (only on ERROR/CRITICAL)              |

### Level taxonomy

- **DEBUG** — local-only. Disabled in production via `LOG_LEVEL=INFO`.
- **INFO** — normal operations. One per request, one per migration
  step, one per cron run. Successful auth events.
- **WARNING** — recoverable: rate limit hits, fail-soft email
  failures, validation errors that hit the same field repeatedly.
- **ERROR** — request failed with 5xx, background job failed,
  Resend returned non-2xx after retries.
- **CRITICAL** — process-level failures (DB pool exhausted,
  config invalid at boot). Always alert.

### Redaction

The JSON formatter **redacts known headers** before emitting:

- `Cookie`, `Set-Cookie`, `Authorization`, `X-Api-Key` → replaced
  with `"<redacted>"`.
- Any field name matching `password`, `password_hash`, `token`,
  `secret`, `cookie`, `set-cookie`, `authorization` (case-insensitive)
  is redacted recursively in nested dicts.
- Email addresses in `msg` are **not** redacted; addresses are
  considered identifiers in this system, not secrets. Passwords
  and tokens are.

This contract is asserted by `tests/test_logging.py::test_known_headers_are_redacted`
(claim from [`risks.md`](risks.md) O5).

---

## Request id

- Middleware reads `X-Request-Id` from the incoming request; if
  absent or malformed, generates a new UUIDv4.
- The id is stored in a `contextvars.ContextVar` for the request
  lifetime so log lines emitted by handlers + the DB layer carry
  it automatically.
- The same id is set as `X-Request-Id` on the response.
- The middleware lives at
  `src/feedback_triage/middleware/request_id.py`.

This is the only piece of "tracing" v2.0 ships. Distributed tracing
(OpenTelemetry, Jaeger, etc.) is explicitly deferred.

---

## Metrics

v2.0 does **not** expose a Prometheus endpoint. We rely on log
queries against the structured fields above. The deliberately
small set of "operational counters" is:

| Counter / gauge               | Source                                                   |
| ----------------------------- | -------------------------------------------------------- |
| Request rate per route        | Aggregating log lines by `route`                         |
| P50 / P95 request latency     | `duration_ms` percentile per `route`                     |
| 5xx rate                      | `status >= 500` count                                    |
| Auth failure rate             | `error_code in (invalid_credentials, account_locked)`    |
| Email send failures           | `logger=feedback_triage.email and level=WARNING`         |
| Background-job duration       | One INFO line per cron run with `duration_ms`            |
| DB pool checkouts in flight   | SQLAlchemy `pool` event listener emits a gauge log line  |

If we need real metrics later, we add an ADR; the structured-log
shape is designed so a metrics exporter could be bolted on without
touching call sites.

---

## Alerts

Railway has email alerts on deploy failure and crash loops; those
are on. Beyond that, v2.0 ships with **two app-level alerts**:

1. **5xx spike**: more than 5 `status >= 500` lines in any
   1-minute window. Action: page the on-call (which is just the
   solo developer in v2.0).
2. **Auth-failure spike**: more than 50 `error_code=invalid_credentials`
   lines from a single IP in any 5-minute window. Action: review,
   tighten the auth rate limiter ([`security.md`](security.md))
   if it's a real attack.

Both are implemented as scheduled queries against Railway's log
search; configuration lives in `tools/ops/alerts.md` (not in this
repo as code).

---

## Out of scope (v2.0)

- APM / distributed tracing.
- Per-tenant dashboards.
- User-session replay (Sentry-style).
- A separate metrics database (Prometheus, InfluxDB, etc.).
- Sentry-style error grouping. Errors are searched in the log
  stream by `error_code` + `route`.
