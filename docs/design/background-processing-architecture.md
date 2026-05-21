# Background Processing Architecture

!!! danger "Required: Update This File with Every Tool Decision"
    This is a living decision log, not a static proposal.
    Every time a task is assigned (or reassigned) to Temporal, Celery,
    RabbitMQ, or Redis, update the mapping table in this file in the same PR.
    Example: if password reset email moves to Celery, update that row
    immediately and include the ADR/PR reference.

---

## Recommended Ownership Split

| Tool | Role | Use for SignalNest | Do not use for |
| --- | --- | --- | --- |
| Temporal | Durable workflow engine | Multi-step, important business processes: imports, AI classification, onboarding, weekly reports, webhook workflows | Simple throwaway counters/cache/rate limits |
| Celery | Python task queue | Short independent background jobs: send one email, cleanup expired tokens, small notification task | Multi-step workflows with durable progress/history |
| RabbitMQ | Celery broker | Celery task delivery/routing only | Cache, rate limits, permanent state |
| Redis | Fast temporary store | Rate limits, caching, short-lived locks/counters | Source-of-truth records, durable workflow state |

RabbitMQ queues are ordered message collections that deliver messages to consumers, so it is a good fit as a broker for Celery tasks, not as an app cache. Celery's model is a task queue: a client sends a task message through a broker, and dedicated workers consume work from queues. Temporal's model is durable execution: workflows can resume where they left off after crashes, network failures, or outages. Redis is the right fit for distributed rate limits/cache-style temporary state; Redis docs specifically describe using it for per-user, per-API, or per-tenant quotas across distributed service instances.

## The Rule That Prevents Chaos

Use this decision tree:

- Is it a multi-step business process with progress, retries, waiting, or failure recovery?
  - Temporal
- Is it a short independent Python job?
  - Celery
- Is it cache, rate limiting, locks, or temporary counters?
  - Redis
- Is it permanent product data?
  - PostgreSQL
- Is it Celery message delivery?
  - RabbitMQ

## Current Project Task-to-Tool Mapping (Living Table)

This table records what the project currently uses today and what is
recommended when background infrastructure is introduced.

| Task | Current implementation in this project | Assigned background tool | Status | Update trigger / notes |
| --- | --- | --- | --- | --- |
| Password reset email | In-process Resend send with fail-soft `email_log` writes | None yet (Celery candidate) | Shipped (no queue) | Update when first task worker is introduced. |
| Email verification | In-process Resend send with fail-soft `email_log` writes | None yet (Celery candidate) | Shipped (no queue) | Update when first task worker is introduced. |
| Workspace invite email | In-process Resend send with fail-soft `email_log` writes | None yet (Celery candidate) | Shipped (no queue) | Update when first task worker is introduced. |
| Expired reset-token cleanup | Scheduled cleanup job (`scripts/sweep_expired_tokens.py`) | None yet (Celery optional later) | Shipped | Move only if cron reliability/latency becomes a problem. |
| Login/auth rate limiting | Fixed-window counters in PostgreSQL `auth_rate_limits` | None yet (Redis deferred) | Shipped | Move to Redis token bucket when multi-replica pressure or abuse warrants it. |
| Public form rate limiting | Service-level limiter backed by PostgreSQL counters | None yet (Redis deferred) | Shipped | Move to Redis when rate limits must be globally shared across replicas. |
| Dashboard summary cache | In-process cache | None yet (Redis deferred) | Shipped | Move to Redis when horizontal scaling needs shared cache state. |
| CSV import pipeline | Not implemented | Temporal (recommended) | Recommended | Decide at feature kickoff and record ADR/PR link. |
| AI classification pipeline | Not implemented | Temporal (recommended) | Recommended | Decide at feature kickoff and record ADR/PR link. |
| Weekly workspace report workflow | Not implemented | Temporal (recommended) | Recommended | Decide when scheduled reporting ships. |
| Webhook delivery with retries/backoff | Not implemented | Temporal (recommended) | Recommended | Decide when outbound webhook delivery is introduced. |
| Celery task delivery/routing | Not implemented | RabbitMQ (recommended broker) | Recommended | Add when the first Celery task ships. |
| Store signals/users/workspaces/layouts | PostgreSQL source-of-truth tables | PostgreSQL (not a background tool) | Shipped | Keep as source of truth; never move durable records to Redis/RabbitMQ. |

### Current-State Evidence

- v2 baseline explicitly defers Redis and queue workers in
  `docs/project/spec/v2/railway-optimization.md` and
  `docs/project/spec/v2/rollout.md`.
- Auth rate limits are Postgres-backed until Redis is justified
  (`docs/adr/059-auth-model.md`).
- Email delivery uses in-process fail-soft semantics; background queues
  were rejected for v2.0 (`docs/adr/061-resend-email-fail-soft.md`).

## The Danger

The bad version is:

- Some emails in Celery.
- Some emails in Temporal.
- Some imports in Celery.
- Some imports in Temporal.
- Some status in Redis.
- Some status in PostgreSQL.
- No clear reason why.

That will become painful.

The good version is:

- Temporal = workflows
- Celery = simple tasks
- RabbitMQ = Celery transport
- Redis = cache/rate limits
- PostgreSQL = truth

## My Implementation Recommendation

Current baseline in this repo is intentionally no Redis and no separate
queue/worker for v2.0. The sequence below is the recommended adoption
path after explicit approval.

Build it in this order:

1. Redis first for rate limits and simple cache.
2. Celery + RabbitMQ for one simple job: password reset email.
3. Temporal for one serious workflow: CSV import or AI classification pipeline.
4. Add monitoring and job/workflow status pages before adding more task types.

Do not integrate all four at once across the whole app. Prove each tool with one vertical slice.

## Minimum Structure

```text
apps/
  web/       Next.js frontend
  api/       FastAPI API
  worker/    Celery worker
  workflows/ Temporal worker

infra/
  redis/
  rabbitmq/
  temporal/

docs/
  adr/
    001-background-processing-boundaries.md
```

## Strong Recommendation

Write an ADR before implementation.

Decision:
Use Temporal, Celery, RabbitMQ, and Redis with strict responsibilities.

- Temporal: Durable workflows only.
- Celery: Short independent Python tasks only.
- RabbitMQ: Celery broker only.
- Redis: Caching, rate limiting, locks, temporary counters only.
- PostgreSQL: Permanent source of truth.

Final pushback: this is a professional architecture only if you also add observability. At minimum, include structured logs, failed-task alerts, Temporal visibility, Celery worker monitoring, RabbitMQ queue monitoring, and Redis memory/eviction monitoring. Without that, the extra tools mostly add hidden failure modes.
