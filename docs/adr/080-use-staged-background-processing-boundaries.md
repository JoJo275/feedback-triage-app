# ADR 080: Use staged background-processing boundaries for Temporal, Celery, RabbitMQ, and Redis

---

## Status

Accepted

## Context

The project now has explicit background-processing guidance in
`docs/design/background-processing-architecture.md`, but without an ADR
the decision can drift as features land.

At the same time, v2.0's current baseline intentionally avoids extra
infrastructure: no Redis cache tier, no worker queue, no separate
background process by default (`docs/project/spec/v2/railway-optimization.md`
and `docs/project/spec/v2/rollout.md`).

This creates a real risk: teams may introduce Temporal, Celery,
RabbitMQ, or Redis ad hoc per feature, producing overlapping ownership
and inconsistent failure handling.

We need one explicit architecture decision that does both:

1. Preserve the current v2 baseline (in-process + PostgreSQL where
   already shipped).
2. Define strict ownership boundaries for staged adoption of background
   tooling when justified.

## Decision

Adopt a staged boundary model for background processing.

1. **Temporal** is for durable, multi-step workflows with progress,
   retries, waiting, and recovery semantics.
2. **Celery** is for short, independent Python background jobs.
3. **RabbitMQ** is used only as Celery transport/broker.
4. **Redis** is for temporary state only (rate limits, cache,
   short-lived counters/locks).
5. **PostgreSQL** remains source of truth for durable product data.

Operational constraints:

- Current v2.0 baseline stays as-is: no queue/worker/Redis requirement
  until explicitly justified by load/feature scope.
- `docs/design/background-processing-architecture.md` is the living
  mapping document.
- When adding or reassigning any background task, update
  [Current Project Task-to-Tool Mapping (Living Table)](../design/background-processing-architecture.md#current-project-task-to-tool-mapping-living-table)
  in the same PR.
- Any assignment/reassignment for Temporal/Celery/RabbitMQ/Redis must
  update that mapping table in the same PR, with a reference to the
  implementing ADR/PR.
- New background infrastructure must ship with observability
  (structured logs, failure alerts, queue/workflow visibility).

## Decision Boundary

The system may use both Temporal and Celery/RabbitMQ, but they must
not overlap casually.

**Temporal** is used for durable business workflows that require step
history, retries, waiting, progress tracking, or failure recovery.

**Celery + RabbitMQ** is reserved for short, independent, high-volume
tasks where workflow history is not valuable and throughput is the
primary concern.

**Redis** is used for cache, rate limits, short-lived locks, and temporary
counters.

**PostgreSQL** remains the source of truth for product data, job records,
workflow status shown to users/admins, and audit history.

If a background process could be implemented in either **Temporal** or
**Celery**, prefer **Temporal** unless the process is proven to be high-volume,
simple, and throughput-sensitive.

## Alternatives Considered

### Ad hoc tool selection per feature

Allow each feature PR to pick any background tool without central
boundaries.

**Rejected because:** It creates inconsistent retry semantics, unclear
ownership, and hard-to-debug production behavior.

### Temporal + Redis only (no Celery/RabbitMQ)

Use Temporal for all async work and Redis for temporary state,
without introducing Celery/RabbitMQ.

**Rejected because:** High-volume, low-priority background jobs become
tedious to model and operate as durable workflows. A short-task queue
fits that workload better, while Temporal stays focused on multi-step
workflow orchestration.

### Celery-first for all background work

Use Celery for everything (including long-running orchestration) and
defer Temporal indefinitely.

**Rejected because:** Durable, multi-step workflow state and recovery
are not Celery's primary model; this blurs task queue vs workflow
orchestration boundaries.

### Keep all work synchronous/in-process indefinitely

Never adopt dedicated background tooling.

**Rejected because:** Some future workloads (imports, AI pipelines,
webhook delivery/backoff) require durable workflow semantics and
operational control not provided by purely in-process execution.

## Consequences

### Positive

- Prevents mixed ownership across Temporal/Celery/Redis/PostgreSQL.
- Keeps v2 baseline simple while enabling a clear migration path.
- Gives contributors one canonical place to record task assignments.

### Negative

- Adds process overhead: assignment changes must update docs in the
  same PR.
- Introduces governance work before shipping worker infrastructure.

### Neutral

- Existing v2 shipped behavior remains unchanged today.
- Current auth email fail-soft flow and Postgres-backed rate limiting
  stay in place.

### Mitigations

- Keep the mapping table explicit and status-tagged (shipped vs
  recommended).
- Require observability before adding new worker/workflow types.
- Revisit assignments via focused ADRs when feature scope changes.

## Implementation

- [docs/design/background-processing-architecture.md](../design/background-processing-architecture.md) - living tool-boundary and task-mapping document.
- [Current Project Task-to-Tool Mapping (Living Table)](../design/background-processing-architecture.md#current-project-task-to-tool-mapping-living-table) - update this section whenever a background task is added or reassigned.
- [docs/tooling.md](../tooling.md) - tooling inventory entries for Temporal/Celery/RabbitMQ/Redis.
- [docs/project/spec/v2/railway-optimization.md](../project/spec/v2/railway-optimization.md) - current no-Redis/no-worker baseline.
- [docs/project/spec/v2/rollout.md](../project/spec/v2/rollout.md) - deferred worker/cache scope in rollout.
- [docs/adr/059-auth-model.md](059-auth-model.md) - Postgres-backed rate limits until Redis is justified.
- [docs/adr/061-resend-email-fail-soft.md](061-resend-email-fail-soft.md) - in-process email fail-soft; queue explicitly rejected for v2.0.
- [src/feedback_triage/services/rate_limit.py](../../src/feedback_triage/services/rate_limit.py) - current Postgres-backed fixed-window rate limiter.
- [src/feedback_triage/email/client.py](../../src/feedback_triage/email/client.py) - current in-process email send/retry flow.
- [src/feedback_triage/auth/tokens.py](../../src/feedback_triage/auth/tokens.py) - current token validation and expiry enforcement path.

## References

- [Background Processing Architecture](../design/background-processing-architecture.md)
- [ADR 059](059-auth-model.md)
- [ADR 061](061-resend-email-fail-soft.md)
- [Temporal docs](https://docs.temporal.io/)
- [Celery docs](https://docs.celeryq.dev/)
- [RabbitMQ docs](https://www.rabbitmq.com/docs)
- [Redis docs](https://redis.io/docs/latest/)
