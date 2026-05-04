# v2.0 — Performance budgets

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> See also: [`api.md`](api.md), [`ui.md`](ui.md),
> [`railway-optimization.md`](railway-optimization.md),
> [`observability.md`](observability.md).

This file defines **the numeric performance budgets** for v2.0 —
latency, page weight, JS bundle size, and cache TTLs. A change
that exceeds any budget needs a budget-update PR (this file plus
the offending code).

---

## Latency targets (server-side)

Measured at the `duration_ms` field in [`observability.md`](observability.md),
P95 over a rolling 24h window in production.

| Surface                              | P50    | P95    | Hard cap |
| ------------------------------------ | ------ | ------ | -------- |
| `GET /api/v1/feedback?...` (list)    | 120 ms | 350 ms | 1500 ms  |
| `GET /api/v1/feedback/{id}` (detail) | 80 ms  | 250 ms | 1000 ms  |
| `PATCH /api/v1/feedback/{id}`        | 100 ms | 300 ms | 1000 ms  |
| `GET /api/v1/dashboard/summary`      | 80 ms  | 200 ms | 800 ms   |
| `POST /api/v1/auth/login`            | 250 ms | 450 ms | 1500 ms  |
| `POST /api/v1/public/feedback`       | 150 ms | 400 ms | 1500 ms  |
| `GET /healthz`                       | 5 ms   | 20 ms  | 100 ms   |

`POST /api/v1/auth/login` is allowed a higher floor because
Argon2id hashing is intentionally expensive ([`auth.md`](auth.md)).
We tune the Argon2id cost so a single hash takes **120–180 ms**
on Railway's hobby tier; never below 80 ms, never above 250 ms.

Hard caps are circuit-breaker thresholds: a request exceeding the
hard cap is logged as WARNING and counts against the 5xx-spike
alert. We **do not** kill the request; user-facing timeouts are
client-side.

---

## Dashboard cache

`GET /api/v1/dashboard/summary` is the only read-heavy aggregate
endpoint. It uses a **per-workspace in-memory TTL cache**:

- TTL: **60 seconds**.
- Cache key: `(workspace_id, user_role)` — owners and team_members
  get the same answer; demo workspaces are read-only so the role
  has no effect on the result, but we key by it for safety.
- Implementation: `cachetools.TTLCache` in
  `src/feedback_triage/services/dashboard_cache.py`.
- Invalidation: TTL only. Writes to feedback **do not** bust the
  cache; users see fresh numbers within 60s, which is acceptable
  for a triage dashboard. This is the single trade-off this file
  documents — anyone seeing "stale dashboard" must understand
  that 60s is the floor.

Memory bound: 1 entry per workspace × max 200 workspaces in v2.0
× ~2 KB per entry = ~400 KB worst case. Below
[`railway-optimization.md`](railway-optimization.md) memory budget.

---

## Public-page caching

`GET /` (landing) and `GET /styleguide` are static-ish HTML; both
ship with:

```
Cache-Control: public, max-age=300, stale-while-revalidate=600
```

5 minutes fresh, 10 minutes stale-while-revalidate. The mini demo
on the landing page is fully client-side, so no server contract.

`POST /api/v1/public/feedback` is **never cached**:

```
Cache-Control: no-store
```

---

## Static assets

`/static/*` are served by FastAPI's `StaticFiles`. Filenames are
hash-suffixed at build time (`app.7f3a2c.css`) so we can cache
aggressively:

```
Cache-Control: public, max-age=31536000, immutable
```

The HTML references the hashed name through a small `asset(name)`
helper; renaming an asset is a one-line template change.

---

## Page weight

Per page, on first load (uncompressed bytes; gzip cuts ~70%):

| Asset class                        | Budget | Hard cap |
| ---------------------------------- | ------ | -------- |
| HTML                               | 25 KB  | 50 KB    |
| CSS (single shared `app.css`)      | 60 KB  | 100 KB   |
| Per-page JS (`<page>.js`)          | 8 KB   | 15 KB    |
| Shared JS (`api.js` + `toast.js`)  | 6 KB   | 10 KB    |
| Total JS per page                  | 15 KB  | 25 KB    |
| Images (per-page, total)           | 100 KB | 250 KB   |
| Web fonts                          | 0 KB   | 0 KB     |

**No web fonts.** The whole stack uses system fonts via the
`font-sans` / `font-mono` Tailwind utilities. Adding a custom font
needs an ADR.

**No JS bundler.** Every page-level JS file is its own static
asset. Tree-shaking is the developer's job, not a tool's.

---

## Database query budgets

These are review heuristics, not enforced limits:

- A request handler issues **≤ 5 queries** in the common case.
- A request that issues > 10 queries gets flagged in review.
- N+1 patterns are a blocker. Use `selectinload` /
  `joinedload` in SQLAlchemy.
- Pagination is **mandatory** on every list endpoint
  ([`api.md`](api.md)). Default `limit=50`, max `limit=200`.

---

## Background jobs

| Job                                        | Frequency           | Budget   |
| ------------------------------------------ | ------------------- | -------- |
| Session GC (delete expired sessions)       | every 1 hour        | < 5 sec  |
| Token GC (verification + reset expirations) | every 1 hour       | < 5 sec  |
| Demo workspace reset                       | every 24 hours, 03:00 UTC | < 30 sec |
| `email_log` retention prune (90 days)      | every 24 hours      | < 10 sec |

Cron is **Railway's built-in scheduler**, not an in-process
APScheduler ([`rollout.md`](rollout.md)). Each job is a
`scripts/<name>.py` invoked as a Railway cron.

---

## Out of scope (v2.0)

- CDN. Static assets are served from the FastAPI process; that's
  acceptable at v2.0 traffic levels.
- HTTP/2 push. Railway's edge handles the protocol negotiation.
- Service workers, offline mode, PWA install.
- Image optimization pipeline. Images are committed pre-optimized
  (PNG / SVG); no `<picture>` / `srcset` per-DPR variants in v2.0.
