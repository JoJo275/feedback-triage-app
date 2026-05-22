# Production Readiness

!!! danger "Commercial Product Gate"
    This document defines what must be true before the project should be treated as a paid, professional product.
    A feature being implemented is not the same as the system being production-ready.

## Purpose

This document defines production-readiness expectations for the product. It covers:

- Reliability.
- Observability.
- Security.
- Data safety.
- Release safety.
- Background job/workflow operations.
- Email delivery.
- Performance and capacity.
- Incident response.
- Cost monitoring.

## Related Documents

- [`../tooling.md`](../tooling.md) — complete tool inventory.
- [`../design/tool-decisions.md`](../design/tool-decisions.md) — rationale for tool choices.
- [`../design/frontend-architecture.md`](../design/frontend-architecture.md) — frontend architecture.
- [`../design/background-processing-architecture.md`](../design/background-processing-architecture.md) — worker/workflow ownership.
- [`../workflows.md`](../workflows.md) — CI workflow inventory.
- [`../development/developer-commands.md`](../development/developer-commands.md) — command catalog.

## Readiness Levels

| Level | Meaning | Required Standard |
| --- | --- | --- |
| Local development | Works on developer machine. | Manual testing is acceptable; data loss is acceptable. |
| Internal alpha | Usable by the developer/team. | Basic tests, migrations, logs, and recoverable local workflows. |
| Private beta | Usable by invited users. | Error monitoring, smoke tests, backups, rate limits, and basic support path. |
| Paid production | Usable by paying customers. | Operational monitoring, incident response, job visibility, cost alerts, uptime checks, security hygiene. |
| Commercial scale | Ready for broader traffic and support commitments. | Load tests, tracing, on-call, status page, runbooks, SLOs, feature flags, spend governance. |

## Production-Readiness Summary

| Area | Minimum Before Private Beta | Minimum Before Paid Production | Notes |
| --- | --- | --- | --- |
| CI quality gates | Lint, typecheck, backend tests, frontend tests. | Add e2e smoke tests and migration checks. | `task check` should be trustworthy. |
| Error monitoring | Basic Sentry integration. | Frontend + backend + worker error monitoring with release tags. | Sentry before OpenTelemetry. |
| Logging | Structured backend logs. | Correlated request/job/workflow logs. | Logs must include workspace/request/job IDs where safe. |
| Database | Alembic migrations and test DB workflow. | Backups, restore test, migration rollback plan. | PostgreSQL is source of truth. |
| Background work | Manual/local proof. | Job/workflow monitoring, retries, dead-letter/failure review. | Temporal/Celery must not fail silently. |
| Redis | Local/dev usage clear. | Rate-limit/cache keys documented and monitored. | Avoid unbounded key growth. |
| Email | Provider integration works. | Delivery failures tracked; templates reviewed; unsubscribe rules where relevant. | Transactional email is not optional. |
| Auth/security | Basic auth works. | Rate limits, secure reset flow, secrets scanning, dependency audit. | Password reset must not leak account existence. |
| API robustness | Unit/integration tests. | Schemathesis on critical OpenAPI endpoints. | Especially auth and public submission endpoints. |
| Performance | Manual smoke checks. | k6 checks for critical flows. | Load test before broad commercial traffic. |
| Uptime | Manual deploy checks. | Synthetic uptime checks. | Probe from outside app boundary. |
| Release safety | CI passes before deploy. | Feature flags for risky launches; rollback plan. | Deployment and exposure should be separate. |
| Cost | Manual review. | Budget alerts and service-level cost review. | Required before adding always-on workers/services. |
| Incident response | Personal notes. | Runbooks, escalation path, customer comms plan. | Required for paying users. |

## Architecture Readiness

### Required Service Ownership

| System | Production Responsibility |
| --- | --- |
| Next.js or Vite/React | Frontend app shell, routes, UI, client interactions. |
| FastAPI | API boundary, auth, permissions, business logic, workflow/task entrypoints. |
| PostgreSQL | Permanent source-of-truth data. |
| Redis | Cache, rate limits, short-lived counters, temporary locks. |
| Temporal | Durable multi-step business workflows. |
| Celery | Short independent background tasks, if adopted. |
| RabbitMQ | Celery broker only, if adopted. |
| Email provider | Transactional email delivery. |
| Sentry | Error visibility. |
| OpenTelemetry | Distributed traces/metrics when needed. |

### Production Anti-Patterns

Do not ship paid production with:

- No external error monitoring.
- No database backup/restore plan.
- No tested migration path.
- No rate limits on auth/public submission endpoints.
- No visibility into failed jobs/workflows.
- No smoke test for core user flows.
- No cost alerting after adding always-on services.
- No rollback plan.
- No documented handling for user data deletion/export requests.

## Launch Gates

### Private Beta Gate

Before private beta:

- [ ] Backend tests pass in CI.
- [ ] Frontend tests pass in CI.
- [ ] TypeScript typecheck passes.
- [ ] ESLint passes.
- [ ] Ruff passes.
- [ ] mypy passes for backend package.
- [ ] Alembic migrations apply cleanly from empty DB.
- [ ] Dashboard smoke flow works.
- [ ] Password reset flow works.
- [ ] Email provider is configured for non-local environment.
- [ ] Basic Sentry/error monitoring is configured.
- [ ] Public feedback/auth endpoints have rate limits or a documented temporary exception.
- [ ] PostgreSQL backups are enabled or documented by host.
- [ ] Secrets are not committed and gitleaks passes.
- [ ] Privacy/data-handling page exists if real users sign up.

### Paid Production Gate

Before charging customers:

- [ ] Sentry captures frontend, backend, and worker errors.
- [ ] Critical Playwright smoke tests run in CI or pre-release.
- [ ] Synthetic uptime checks exist for health and critical routes.
- [ ] Database backup and restore process has been tested.
- [ ] Migration rollback/forward-fix strategy is documented.
- [ ] Redis key patterns and TTLs are documented.
- [ ] Background job/workflow failure handling is documented.
- [ ] Failed jobs/workflows are inspectable by admin/operator.
- [ ] Email delivery failures are logged and actionable.
- [ ] Cost alerts are enabled for infrastructure and external providers.
- [ ] Basic incident runbook exists.
- [ ] Customer support/contact path exists.
- [ ] Terms/privacy/data retention docs are present enough for the app's data use.
- [ ] Feature flags or rollout controls exist for high-risk features.

### Commercial Scale Gate

Before broad commercial traffic:

- [ ] k6 load scenarios exist for auth, dashboard, feedback submission, and inbox flows.
- [ ] Schemathesis checks run against critical OpenAPI endpoints.
- [ ] OpenTelemetry tracing exists across API and workers if incidents require correlation.
- [ ] On-call/incident routing exists.
- [ ] Public status page or incident communication path exists.
- [ ] Runbooks cover database outage, email outage, worker failure, and deploy rollback.
- [ ] Service-level cost ownership exists.
- [ ] Data export/deletion workflows are implemented or documented.
- [ ] Security review has been performed for auth, permissions, tenancy, and public inputs.

## Observability Plan

### Phase 1: Error Visibility

Adopt Sentry first.

Minimum tags:

- `environment`
- `release`
- `service`
- `route`
- `workspace_id` when safe and non-sensitive
- `user_id` when safe and non-sensitive
- `job_id` or `workflow_id` for worker failures

Capture:

- Frontend exceptions.
- Backend unhandled exceptions.
- Worker task failures.
- Temporal workflow/activity failures.
- Email provider integration failures.

### Phase 2: Structured Logs

Backend logs should include:

- request ID
- method/path/status
- duration
- user/workspace context where safe
- job/workflow IDs
- external provider status

Avoid logging:

- passwords
- reset tokens
- session tokens
- API keys
- full email contents
- sensitive user submissions beyond what is necessary for debugging

### Phase 3: Tracing and Metrics

Adopt OpenTelemetry when the system has enough services that logs/errors are not enough.

Use tracing for:

- Next.js request to FastAPI.
- FastAPI endpoint to database.
- FastAPI endpoint to Redis.
- FastAPI start-workflow call.
- Temporal workflow/activity execution.
- Celery task execution if adopted.
- Email provider calls.

## Background Processing Readiness

### Temporal Requirements

Before using Temporal for production workflows:

- [ ] Workflow names are stable and documented.
- [ ] Activity functions are idempotent.
- [ ] Retry policies are explicit.
- [ ] Timeouts are explicit.
- [ ] User-visible status is stored in PostgreSQL where needed.
- [ ] Workflow failures are visible in monitoring.
- [ ] Long-running workflows can be inspected.
- [ ] Workflows accept IDs, not large payloads.

### Celery + RabbitMQ Requirements

Before using Celery/RabbitMQ for production tasks:

- [ ] RabbitMQ queues are named by task class.
- [ ] Retry behavior is explicit.
- [ ] Task time limits are set.
- [ ] Tasks are idempotent.
- [ ] Failure path is logged and alertable.
- [ ] Queue depth is monitored.
- [ ] Worker liveness is monitored.
- [ ] RabbitMQ is not used for cache/rate limits.

### Redis Requirements

Before using Redis in production:

- [ ] Key naming convention is documented.
- [ ] Every cache/rate-limit/lock key has a TTL unless intentionally persistent.
- [ ] Redis memory behavior/eviction policy is understood.
- [ ] Cache misses fall back correctly to PostgreSQL.
- [ ] Rate-limit behavior returns useful errors.
- [ ] Locks cannot permanently deadlock the app.

## Email Readiness

### Required Email Flows

- [ ] Password reset.
- [ ] Email verification, if signups require verification.
- [ ] Workspace invite.
- [ ] Security/account change notification.
- [ ] Weekly/report emails only after reporting is production-ready.

### Password Reset Rules

- Do not reveal whether the email exists.
- Store hashed reset tokens, not raw tokens.
- Use short expiration, usually 15–30 minutes.
- Mark token used after successful reset.
- Rate-limit reset requests by email/IP/account.
- Send plain-text and HTML email versions.
- Log delivery attempt metadata, not the token.

### Template Ownership

Default:

```text
Jinja2 templates in source control
```

Adopt MJML when:

- Email layout becomes hard to maintain in plain HTML.
- Reports/onboarding emails need responsive components.
- Cross-client rendering consistency becomes important.

Adopt provider templates only when:

- Governance exists for provider-side edits.
- Template IDs and variables are versioned in docs/code.
- Code review is not required for every copy/layout change.

## Security Readiness

### Baseline Checks

- [ ] Bandit runs on Python code.
- [ ] pip-audit runs for Python dependencies.
- [ ] gitleaks runs before push/CI.
- [ ] CodeQL runs in GitHub code scanning.
- [ ] OpenSSF Scorecard runs periodically.
- [ ] Container scans run with Trivy/Grype.
- [ ] SBOM is generated with Syft for releases.

### Application Security Requirements

- [ ] Auth endpoints are rate-limited.
- [ ] Public submission endpoints are rate-limited.
- [ ] CSRF/CORS/session strategy is documented.
- [ ] Workspace/tenant authorization is tested.
- [ ] Admin-only endpoints are tested.
- [ ] Password reset does not leak account existence.
- [ ] Secrets are environment-managed.
- [ ] User-supplied HTML/content is escaped or sanitized.
- [ ] Audit logs exist for destructive actions.

## Database Readiness

Before paid production:

- [ ] PostgreSQL is the source of truth for product data.
- [ ] Alembic migration history is clean.
- [ ] New migrations are reviewed.
- [ ] Migrations are tested against a realistic database snapshot when possible.
- [ ] Backups are enabled.
- [ ] Restore procedure is tested.
- [ ] Destructive migrations require manual review.
- [ ] Seed/test data is separated from production data.
- [ ] Data retention/deletion rules are documented.

## Performance Readiness

### Critical Flows to Measure

- Login.
- Dashboard load.
- Total Signals summary endpoint.
- Feedback inbox list.
- Feedback item detail.
- Public feedback submission.
- Password reset request.
- Dashboard layout save.

### Suggested Initial Targets

These are starting targets, not formal SLOs:

| Metric | Target |
| --- | --- |
| API p95 latency for dashboard summary | < 500 ms under normal load |
| Dashboard first usable render | < 2.5 s on typical broadband |
| Error rate for core API routes | < 1% before beta, much lower before paid production |
| Password reset request response | < 1 s, email may send async |
| Background workflow failure visibility | 100% of failures recorded/inspectable |

### Load Testing with k6

Add k6 scenarios for:

- Auth/login flow.
- Dashboard summary endpoint.
- Inbox listing with filters.
- Public feedback submission.
- Password reset request.

Use k6 to detect regressions, not to prove infinite scale.

## API Robustness Readiness

Use Schemathesis when the OpenAPI schema is stable enough to test.

Minimum targets:

- Auth-adjacent endpoints.
- Public feedback submission.
- Dashboard summary endpoints.
- Feedback create/update endpoints.
- Workspace/user permission-sensitive endpoints.

Schemathesis should complement, not replace, deterministic API tests.

## Release Readiness

### Pull Request Gate

A PR should not merge unless relevant checks pass:

- Python lint/format.
- Python typecheck.
- Python tests.
- Frontend lint.
- Frontend typecheck.
- Frontend tests.
- Docs build if docs changed.
- Container build if runtime changed.
- Security scans where applicable.

### Release Gate

A release should not deploy broadly unless:

- Migrations are reviewed.
- Rollback/forward-fix path is known.
- Feature flags are ready for high-risk behavior.
- Playwright critical smoke tests pass.
- Error monitoring release metadata is configured.
- Cost impact of new services is understood.

## Incident Response

### Minimum Incident Runbooks

- API outage.
- Database connection failure.
- Failed migration.
- Email delivery outage.
- Redis outage.
- Temporal workflow failure backlog.
- Celery/RabbitMQ queue backlog, if adopted.
- Bad deploy rollback.
- Cost spike.
- Security secret exposure.

### Incident Workflow

```text
Alert fires
→ classify severity
→ identify affected users/workspaces
→ mitigate or rollback
→ communicate if customer-facing
→ preserve logs/metadata
→ write post-incident notes
→ create corrective tasks
```

## Cost Readiness

### Always-On Cost Risks

The following can increase infrastructure cost because they may run as separate services:

- Next.js server.
- FastAPI server.
- PostgreSQL.
- Redis.
- Temporal service/cloud.
- Temporal worker.
- RabbitMQ.
- Celery worker.
- Sentry/error monitoring.
- Email provider.
- Uptime/status tools.

### Required Cost Controls

Before broad commercial traffic:

- [ ] Monthly budget target is documented.
- [ ] Budget alerts are enabled.
- [ ] Each always-on service has a reason to exist.
- [ ] Worker counts/concurrency are documented.
- [ ] Email provider pricing is understood.
- [ ] AI/classification cost controls exist if AI workflows are added.
- [ ] Expensive endpoints have rate limits.
- [ ] Logs/traces are sampled or retained according to budget.

## Feature Flag Readiness

Feature flags should be used for:

- High-risk dashboard editor changes.
- New background processing paths.
- New AI classification flows.
- New billing/paid-plan behavior.
- New public submission flows.
- Gradual rollout by workspace/user segment.

Feature flags should not become permanent configuration sprawl.

Every flag should have:

- owner
- description
- default value
- rollout plan
- removal date or review date

## Public Status and Customer Communication

Add public status tooling when customers depend on uptime.

Minimum policy:

- Define when an incident becomes customer-visible.
- Define who writes updates.
- Define update frequency during incidents.
- Define post-incident summary expectations.

Before a status page exists, maintain at least a private incident log.

## Production Readiness Adoption Order

Recommended order:

1. Stabilize CI checks and core tests.
2. Add Sentry/error monitoring.
3. Add Redis for rate limits/cache where needed.
4. Add critical Playwright smoke tests.
5. Add database backup/restore procedure.
6. Add first production-safe email flow.
7. Add Temporal for first durable workflow.
8. Add Celery/RabbitMQ only if a separate short-task workload justifies it.
9. Add synthetic uptime checks.
10. Add cost monitoring/budget alerts.
11. Add Schemathesis for critical OpenAPI endpoints.
12. Add k6 capacity scenarios.
13. Add feature flags for high-risk rollout.
14. Add OpenTelemetry when distributed debugging requires it.
15. Add on-call/status page when customers require it.

## Final Gate

The product is not paid-production-ready until the following are true:

- Real user data is protected.
- Critical flows are tested.
- Errors are visible.
- Database state is backed up and recoverable.
- Background work cannot silently fail.
- Abuse-prone endpoints are rate-limited.
- Releases can be rolled back or forward-fixed.
- Operational costs are visible.
- Customer-impacting incidents have a response path.
