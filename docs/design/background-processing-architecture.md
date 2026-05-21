# Background Processing Architecture

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

## Concrete Examples

| Task | Recommended tool |
| --- | --- |
| Password reset email | Celery |
| Email verification | Celery |
| Workspace invite email | Celery |
| Expired reset-token cleanup | Celery or scheduled job |
| Public form rate limit | Redis |
| Login attempt rate limit | Redis |
| Dashboard summary cache | Redis |
| CSV import pipeline | Temporal |
| AI classification pipeline | Temporal |
| Weekly workspace report | Temporal |
| Webhook delivery with retries/backoff | Temporal |
| Workspace onboarding flow | Temporal |
| Store signals/users/workspaces/layouts | PostgreSQL |

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
