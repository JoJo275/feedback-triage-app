# Background Processing Architecture

!!! danger "Required: Update This File with Every Tool Decision"
    This is a living decision log, not a static proposal.
    Every time a task is assigned (or reassigned) to Temporal, Celery,
    RabbitMQ, or Redis, update the mapping table in this file in the same PR.
    Example: if password reset email moves to Celery, update that row
    immediately and include the ADR/PR reference.

---

## Decision Boundary

The system may use both Temporal and Celery/RabbitMQ, but they must
not overlap casually.

Temporal is used for durable business workflows that require step
history, retries, waiting, progress tracking, or failure recovery.

Celery + RabbitMQ is reserved for short, independent, high-volume tasks
where workflow history is not valuable and throughput is the primary
concern.

Redis is used for cache, rate limits, short-lived locks, and temporary
counters.

PostgreSQL remains the source of truth for product data, job records,
workflow status shown to users/admins, and audit history.

If a background process could be implemented in either Temporal or
Celery, prefer Temporal unless the process is proven to be
high-volume, simple, and throughput-sensitive.

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

Update this table whenever a background task is added, reassigned, or
de-scoped.

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

- Tool-boundary policy is codified in
  [docs/adr/080-use-staged-background-processing-boundaries.md](../adr/080-use-staged-background-processing-boundaries.md).
- v2 baseline explicitly defers Redis and queue workers in
  [docs/project/spec/v2/railway-optimization.md](../project/spec/v2/railway-optimization.md)
  and
  [docs/project/spec/v2/rollout.md](../project/spec/v2/rollout.md).
- Auth rate limits are Postgres-backed until Redis is justified
  ([docs/adr/059-auth-model.md](../adr/059-auth-model.md)).
- Email delivery uses in-process fail-soft semantics; background queues
  were rejected for v2.0
  ([docs/adr/061-resend-email-fail-soft.md](../adr/061-resend-email-fail-soft.md)).

## The Danger of Boundary Drift

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

### Minimum Structure

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

## Do Not Queue Every Tiny Event

Do not create jobs for every tiny thing just because you have background infrastructure.

Bad:

- user views dashboard -> enqueue analytics task
- user hovers chart -> enqueue event task
- each widget render -> enqueue metric task
- each signal count increment -> enqueue task

Better:

- high-frequency counters -> Redis counters or batched DB writes
- analytics events -> batch and aggregate
- dashboard summaries -> Redis cache + scheduled recompute
- important workflows -> Temporal

Redis is the right tool for temporary counters, cache, locks, and rate-limit state; RabbitMQ is not. Redis’s rate-limit guidance focuses on centralized counters/quotas, while RabbitMQ is queue/message delivery.

## Downsides of Using Temporal for Tiny Jobs

| Downside | Meaning |
| --- | --- |
| More conceptual overhead | You think in workflows, activities, task queues, workers, retries. |
| More infrastructure | You need Temporal service/cloud plus worker processes. |
| More verbose than a simple queue | A one-step email task may need more structure than a Celery/RQ task. |
| May be overkill for huge volumes of trivial jobs | Example: millions of tiny fire-and-forget events. |
| Requires good boundaries | Activity code should be idempotent and well-scoped. |

The key is not "short jobs are bad in Temporal." The key is: do not over-model every tiny task as a complicated workflow.

## When Using Temporal for Short Jobs Is Fine

It is fine when the job is still important enough that you care about:

- retry behavior
- visibility
- logs/history
- failure handling
- worker separation
- consistent background-job architecture

Examples:

- send password reset email
- send invite email
- deliver webhook
- recalculate a small workspace metric
- invalidate or rebuild a cache

Temporal Task Queues persist Workflow and Activity Tasks, workers poll when they have capacity, and Temporal supports routing/load balancing across worker processes. That is enough to cover many "background queue" needs without RabbitMQ.

## Critical Reliability Features

Do not just "install Celery and RabbitMQ." Add these from the start:

| Feature | Why it matters |
| --- | --- |
| Job status table | Users/support can see whether a task is pending, running, failed, done. |
| Idempotency keys | Retried tasks do not duplicate emails/imports/actions. |
| Dead-letter queue | Failed jobs are inspectable instead of silently disappearing. |
| Retry limits | Bad jobs do not retry forever. |
| Structured logs | You can debug production failures. |
| Admin-only task view | You can inspect stuck/failed jobs. |
| Alerting | You know when jobs fail. |
| Rate limits | Prevent abuse and cost spikes. |
| Playwright smoke tests | Prevent broken deployed flows. |

For a paid product, I would treat observability as non-optional.
