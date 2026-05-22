# Development Framework

!!! danger "Operating Boundary"
    This document defines how tools are used together in day-to-day project delivery.
    It does not replace `../tooling.md`, which is the complete tool inventory.
    It does not replace design docs or ADRs, which record deeper rationale and approved architectural decisions.

!!! note "Status (Migration Target)"
    Most of the stack described in this document is not fully implemented in the current codebase yet.
    This framework describes the planned migration architecture and operating boundaries for incoming work.
    Next.js, Temporal, Celery/RabbitMQ, TanStack Query, Redux Toolkit, Zustand, Zod, MSW,
    Schemathesis, k6, and LaunchDarkly are adopted for migration kickoff, then used only in
    the specific scenarios defined below.

## Purpose

This framework explains how project tools fit together during normal development. It defines:

- Which layer each tool belongs to.
- What role each tool plays.
- Which tool owns which kind of state or behavior.
- How feature work moves from design to implementation to testing to release.
- How frontend, backend, database, background processing, email, docs, CI, and production operations interact.
- What boundaries prevent tool overlap.

The goal is to avoid a repo where every tool can do everything. Each tool should have a specific job.

## Related Documents

- [`../tooling.md`](../tooling.md) — complete tool inventory, commands, status, and boundaries.
- [`../design/tool-decisions.md`](../design/tool-decisions.md) — rationale for major tool choices.
- [`../design/frontend-architecture.md`](../design/frontend-architecture.md) — frontend runtime, state, styling, API, and test strategy.
- [`../design/background-processing-architecture.md`](../design/background-processing-architecture.md) — Temporal, Celery, RabbitMQ, Redis, and worker boundaries.
- [`../design/email-framework.md`](../design/email-framework.md) — MJML, Jinja2, provider-delivery boundaries, and email template workflow.
- [`../operations/production-readiness.md`](../operations/production-readiness.md) — commercial-readiness gates and operational requirements.
- [`developer-commands.md`](developer-commands.md) — command catalog.
- [`../workflows.md`](../workflows.md) — CI workflow inventory.
- [`../adr/README.md`](../adr/README.md) — Architecture Decision Record index.

## Core Development Rules

1. **One tool owns one responsibility.** Do not let queues, caches, workflow engines, frontend stores, and the database become interchangeable.
2. **PostgreSQL is the source of truth.** Redis, RabbitMQ, Temporal, Celery, and frontend stores must not become canonical product data stores.
3. **FastAPI owns backend truth.** Auth, permissions, API contracts, business rules, persistence, and workflow/task entrypoints live in the backend.
4. **React/Next.js own user experience.** The frontend owns interaction, display, routing, form state, and dashboard editing behavior.
5. **TanStack Query owns server state in React.** API-backed data should not be manually copied into Redux/Zustand unless there is a specific reason.
6. **Redux Toolkit owns complex dashboard editor state.** Undo/redo, draft layouts, selected widget state, unsaved changes, and breakpoint layout editing belong there.
7. **Temporal owns durable workflows.** Multi-step business processes with progress, waiting, retries, and recovery belong in Temporal.
8. **Celery owns short independent jobs.** Simple one-step Python tasks may use Celery when throughput/simplicity matters more than workflow history.
9. **RabbitMQ is Celery transport only.** Do not use RabbitMQ for cache, rate limits, or product data.
10. **Redis is temporary shared state only.** Cache, rate limits, locks, and counters belong in Redis; permanent records belong in PostgreSQL.
11. **Migration tools are adopted, but boundaries stay strict.** Use each tool only for the responsibilities defined in this document.
12. **Every migration must keep the app shippable.** Prefer vertical slices over whole-app rewrites.

## Operating Layers

| Layer | Primary tools | Responsibility | Must not own |
| --- | --- | --- | --- |
| Product frontend | React, TypeScript, Next.js | UI, pages, routing, forms, dashboard widgets, user interactions | Backend business rules, database access, durable workflows |
| Frontend server state | TanStack Query, generated OpenAPI types | API reads/mutations, cache invalidation, loading/error state | Local hover state, undo/redo editor history |
| Frontend client state | useState, useReducer, Zustand, Redux Toolkit | UI state, draft state, editor state, app-shell preferences | Server data from FastAPI |
| Styling and UI primitives | CSS variables, Tailwind, shadcn/ui, Radix UI | Design tokens, component styling, accessible primitives | Product data logic, API logic |
| Backend API | FastAPI, Pydantic | API routes, request/response validation, auth, permissions, business rules | Frontend component composition |
| Database | PostgreSQL, SQLModel/SQLAlchemy, Alembic | Durable product data, schema evolution, relational integrity | Temporary counters/cache/workflow transport |
| Background workflows | Temporal | Durable multi-step processes, workflow history, retries, recovery | Simple throwaway counters or cache |
| Background tasks | Celery, RabbitMQ | Short independent Python jobs and task routing | Durable multi-step workflow state |
| Temporary shared state | Redis | Cache, rate limits, locks, temporary counters | Permanent records, durable workflow history |
| Email | Email provider, Jinja2, MJML templates | Transactional email rendering and delivery | User identity source of truth |
| Testing | pytest, Vitest, React Testing Library, Playwright, MSW, Schemathesis, k6 | Correctness, integration, browser behavior, contracts, load validation | Runtime observability or product analytics |
| Security and supply chain | Ruff, mypy, ESLint, Bandit, pip-audit, gitleaks, CodeQL, Syft, Trivy, Grype | Static checks, scanning, SBOMs, dependency hygiene | Runtime incident response |
| Docs and governance | MkDocs, ADRs, tool/design docs | Documentation, rationale, operational guidance | App runtime behavior |
| Release and operations | GitHub Actions, pre-commit, Dependabot, release-please, Sentry, OpenTelemetry, uptime checks, LaunchDarkly feature flags, cost alerts | CI/CD, release safety, production monitoring, incident response | Local-only manual validation |

## Project State Ownership

### Server State

Server state is data owned by the backend/database and shown in the frontend.

Examples:

- Signals.
- Users.
- Workspaces.
- Tags.
- Comments.
- Saved dashboard layouts.
- Analytics summaries.
- Import records.
- Workflow/job status records shown to users or admins.

**Owner:** FastAPI + PostgreSQL.

**Frontend access pattern:** generated OpenAPI types/client + TanStack Query.

Do not copy this data into Redux Toolkit or Zustand as a second source of truth.

### Client UI State

Client UI state is temporary frontend state that exists because the user is interacting with the browser.

Examples:

- Tooltip open/closed.
- Active sparkline point.
- Dropdown open state.
- Current local tab.
- Form field draft values.
- Sidebar collapsed.

**Owner:** `useState`, `useReducer`, or Zustand depending on scope.

### Complex Dashboard Editor State

Dashboard editor state is structured frontend state with multiple actions, history, and draft/persisted versions.

Examples:

- Edit mode.
- Selected widget.
- Dragged/resized widget.
- Draft layout.
- Saved layout snapshot.
- Undo stack.
- Redo stack.
- Breakpoint-specific layouts.
- Unsaved changes.

**Owner:** Redux Toolkit.

### Temporary Shared Backend State

Temporary backend state is fast but disposable state.

Examples:

- Rate-limit counters.
- Dashboard summary cache.
- Short-lived locks.
- Import debounce flags.
- Temporary workflow/task coordination keys.

**Owner:** Redis.

### Durable Business State

Durable product state must be queryable, backed up, migrated, and audited.

Examples:

- Users.
- Workspaces.
- Signals.
- Permissions.
- Billing-related records.
- Dashboard layouts.
- Job/workflow records visible to users/admins.
- Audit logs.

**Owner:** PostgreSQL.

## Tool Role Separations

### FastAPI vs Next.js

| Tool | Role | Use for | Avoid |
| --- | --- | --- | --- |
| FastAPI | Backend API and business logic authority | API routes, auth, permissions, Pydantic schemas, workflow/task entrypoints, database access | Frontend rendering and dashboard interaction state |
| Next.js | Frontend app shell for the migration target | React routing, layouts, loading/error pages, marketing/public app surfaces, app navigation | Core Python business logic, workflow execution, database source-of-truth rules |

Next.js is the target app shell for the migration architecture in this document. Run one steady-state app shell and avoid long-term parallel frontend shells.

### TanStack Query vs Redux Toolkit vs Zustand vs React State

| State type | Tool | Example |
| --- | --- | --- |
| Tiny local UI state | `useState` | Tooltip open, selected tab, local toggle |
| Structured feature-local state | `useReducer` | Local form wizard, complex panel state |
| Small shared UI state | Zustand | Sidebar collapsed, command palette open, density setting |
| Complex dashboard editor state | Redux Toolkit | Undo/redo, layout drafts, selected widget, edit mode |
| Backend/server data | TanStack Query | Signals, workspaces, tags, saved layout, summaries |

Do not use Redux Toolkit as a backend-data cache. Do not use TanStack Query for local drag state. Do not use Zustand and Redux Toolkit for the same state category.

### Temporal vs Celery vs RabbitMQ vs Redis

| Tool | Role | Use for | Avoid |
| --- | --- | --- | --- |
| Temporal | Durable workflow engine | Imports, AI pipelines, onboarding, reports, webhook workflows | Cache, rate limits, raw counters |
| Celery | Short independent task runner | One-step emails, lightweight cleanup, simple notifications | Durable multi-step workflows |
| RabbitMQ | Celery broker | Celery task delivery/routing | Cache, rate limits, product data |
| Redis | Fast temporary store | Cache, rate limits, counters, short locks | Permanent records, workflow history |
| PostgreSQL | Durable source of truth | Product data, audit history, job/workflow status records | Temporary counters/cache |

If a background process could fit either Temporal or Celery, prefer Temporal unless the process is proven to be high-volume, short, independent, and not valuable as workflow history.

### Jinja2 vs MJML vs Provider Templates

| Tool | Role | Use for | Adoption timing |
| --- | --- | --- | --- |
| Jinja2 | Runtime template rendering for dynamic values and plain-text output | Inject reset links, names, workspace names, expiration times, and render `.txt` fallback emails | Active/default |
| MJML | Responsive HTML email layout authoring | Branded HTML email structure: headers, buttons, sections, reports, onboarding, invites | Active/default |
| Provider templates | Provider-managed email templates | Non-code editing and provider-side template governance | Deferred |

Use MJML for source-controlled responsive HTML email layouts. Use Jinja2 to inject runtime values into compiled HTML templates and to render plain-text fallback templates. Provider templates remain deferred until there is an explicit governance process for editing templates outside the codebase.

## Standard Feature Development Workflow

Use this workflow for normal product features.

```text
1. Define the product behavior.
2. Identify source-of-truth data.
3. Decide whether backend, frontend, workflow, cache, or worker code is required.
4. Update or create design/ADR docs if the feature changes architecture.
5. Implement backend model/API changes first when server data is involved.
6. Generate/update frontend API types.
7. Implement frontend UI and state logic.
8. Add tests at the correct layer.
9. Run local quality gates.
10. Open PR and rely on CI to catch regressions.
```

### Feature Checklist

Before implementing, answer:

- Is this data permanent? If yes, model it in PostgreSQL.
- Does the frontend need this data? If yes, expose it through FastAPI and OpenAPI-generated types.
- Is this a background process? If yes, decide Temporal vs Celery.
- Is this a cache/rate-limit/lock? If yes, use Redis.
- Is this complex dashboard editor state? If yes, use Redux Toolkit.
- Is this just a small UI toggle? If yes, use local React state.
- Does this require a schema migration? If yes, add Alembic migration.
- Does this require production observability? If yes, add logs/metrics/errors from the start.

## Backend API Workflow

Use this when adding or changing FastAPI endpoints.

```text
1. Define or update Pydantic request/response schemas.
2. Implement service-layer business logic.
3. Add/update route under the API namespace.
4. Add permission/auth checks.
5. Add database queries through SQLModel/SQLAlchemy session patterns.
6. Add tests with pytest.
7. Regenerate OpenAPI TypeScript types.
8. Update frontend query/mutation code.
9. Run backend and frontend checks.
```

### Expected Commands

```bash
uv sync
task test
task typecheck
npm --prefix web run contracts:generate
npm --prefix web run contracts:check
npm --prefix web run typecheck
```

### API Rules

- FastAPI responses should be explicit Pydantic schemas.
- API errors should be predictable and documented.
- Endpoint behavior should be tested before wiring complex UI.
- Frontend types should be generated, not manually duplicated.
- Breaking API changes should be reflected in frontend tests and docs.

## Database Change Workflow

Use this when changing durable data models.

```text
1. Update SQLModel/SQLAlchemy model.
2. Create Alembic migration.
3. Review generated migration manually.
4. Run migration locally.
5. Run backend tests.
6. Update Pydantic schemas if API contract changes.
7. Regenerate frontend OpenAPI types if API contract changes.
```

### Expected Commands

```bash
task migration m="describe change"
task migrate
task test
npm --prefix web run contracts:generate
```

### Database Rules

- PostgreSQL is the durable source of truth.
- Every schema change requires an Alembic migration.
- Migrations must be reviewable and reversible when practical.
- Redis, RabbitMQ, and Temporal must not replace PostgreSQL for product records.

## Frontend Data Workflow

Use this when showing or mutating backend data in React.

```text
1. Confirm FastAPI endpoint and generated type exist.
2. Add or update API client function if needed.
3. Add TanStack Query query or mutation.
4. Implement loading, empty, error, and success states.
5. Keep local UI state local.
6. Invalidate/refetch related queries after mutations.
7. Add component tests and, if critical, a Playwright flow.
```

### Server-State Rules

- Use TanStack Query for API-backed data.
- Query keys must include workspace/range/filter identifiers when relevant.
- Mutations must invalidate or update affected queries.
- Do not mirror server data into Redux Toolkit without a specific editor/draft reason.

### Example Data Flow

```text
Dashboard page
→ TotalSignalsCard
→ useSignalSummaryQuery(workspaceId, range)
→ generated API client
→ FastAPI /api/v1/workspaces/:id/signals/summary
→ PostgreSQL/Redis
→ JSON response
→ rendered widget
```

## Dashboard Editor Workflow

Use this for customizable dashboard layout editing.

```text
1. Load saved dashboard layout through TanStack Query.
2. User enters edit mode.
3. Redux Toolkit creates draft layout from saved layout.
4. Drag/resize/hide/show actions update draft layout.
5. Undo/redo updates Redux history stacks.
6. Save action sends final layout through TanStack Query mutation.
7. FastAPI validates and persists layout.
8. Query invalidation refreshes saved layout.
9. Redux exits edit mode and clears draft state.
```

### Dashboard Editor State Ownership

| State | Owner |
| --- | --- |
| Saved layout from backend | TanStack Query |
| Draft layout while editing | Redux Toolkit |
| Undo/redo history | Redux Toolkit |
| Selected widget | Redux Toolkit |
| Active hover point on a sparkline | React local state |
| Dashboard density preference | Zustand or backend setting, depending on persistence need |

### Dashboard Editor Rules

- Persisted layout belongs in PostgreSQL.
- Draft editing state belongs in Redux Toolkit.
- Small hover/tooltip state stays local.
- Do not store full signal lists in Redux for layout editing.

## Background Processing Workflow

Background work must be routed through the correct system.

### Temporal Workflow Pattern

Use this for durable multi-step processes.

```text
1. FastAPI receives request.
2. FastAPI validates auth/permissions.
3. FastAPI creates durable record in PostgreSQL when user/admin visibility is needed.
4. FastAPI starts Temporal workflow with record ID, not huge payload.
5. Temporal worker runs workflow and activities.
6. Workflow updates PostgreSQL status/progress.
7. Frontend reads status through FastAPI/TanStack Query.
```

Examples:

- CSV import.
- AI signal classification.
- Weekly workspace report.
- Webhook delivery workflow with retry/backoff.
- Workspace onboarding.

### Celery Task Pattern

Use this for short independent jobs.

```text
1. FastAPI receives request.
2. FastAPI validates auth/permissions and rate limits if needed.
3. FastAPI writes any required durable record to PostgreSQL.
4. FastAPI enqueues Celery task.
5. RabbitMQ routes task message.
6. Celery worker executes task.
7. Worker logs result and optionally updates PostgreSQL status.
```

Examples:

- Send one password reset email.
- Send one verification email.
- Send one invite email.
- Cleanup expired tokens.
- Lightweight notification task.

### Redis Pattern

Use this for fast temporary shared state.

```text
1. FastAPI builds a scoped key.
2. FastAPI reads/increments/sets Redis value with TTL.
3. Request continues or fails fast depending on Redis result.
4. Permanent outcome is still stored in PostgreSQL if required.
```

Examples:

- `rl:password-reset:email:{email}`.
- `rl:public-submit:ip:{ip}`.
- `cache:workspace:{id}:dashboard:last30d`.
- `lock:import:{import_id}`.

## Email Workflow

Transactional email should be reliable, testable, and source-controlled.

```text
1. User triggers email-related flow.
2. FastAPI validates request and creates token/record in PostgreSQL.
3. Redis applies rate limit if relevant.
4. FastAPI enqueues Celery task or starts Temporal workflow depending on process complexity.
5. Worker renders Jinja2 templates with runtime values (compiled MJML HTML when active, plus `.txt` fallback).
6. Worker sends through email provider.
7. Delivery attempt is logged.
8. Failures retry or surface through monitoring.
```

### Email Tool Boundaries

| Tool | Job |
| --- | --- |
| Jinja2 | Runtime value injection and transactional plain-text rendering |
| Email provider | Actual email delivery |
| Celery | Simple one-step email jobs |
| Temporal | Multi-step email/report/onboarding workflows |
| MJML | Source-controlled responsive email HTML layout authoring |
| Provider templates | Provider-managed template editing after governance allows non-code changes |

### Email Rules

- Always provide HTML and plain-text email output.
- Keep dynamic content injection in Jinja2, even when MJML owns the HTML layout.
- Compile MJML source into HTML templates before runtime rendering.
- Do not reveal whether an email exists in password reset responses.
- Store reset/verification token hashes, not raw tokens.
- Rate-limit password reset and verification flows.
- Keep critical templates source-controlled until there is a reason to move them to provider templates.

## Testing Workflow

Testing should match the layer being changed.

| Change type | Required tests/tools |
| --- | --- |
| Backend service logic | pytest |
| API schema/contract behavior | pytest + Schemathesis |
| Database model/migration | pytest + migration run |
| React component | Vitest + React Testing Library |
| Redux reducer/editor logic | Vitest reducer tests |
| API-backed frontend component | Vitest + React Testing Library + MSW |
| Critical browser flow | Playwright |
| Load/latency risk | k6 |
| Security-sensitive Python change | Bandit + tests |
| Dependency/security change | pip-audit, Trivy/Grype, CodeQL as applicable |

### Minimum Local Checks

```bash
task check
npm --prefix web run lint
npm --prefix web run typecheck
npm --prefix web run test
task test:e2e
```

Use `task test:e2e` for critical browser smoke paths, not every small edit.

## Documentation Workflow

Use docs to prevent future tool confusion.

```text
1. Update `tooling.md` when a tool is added, removed, or changes status.
2. Update design docs when architecture boundaries change.
3. Add ADRs for major irreversible or costly decisions.
4. Update developer commands when commands change.
5. Build docs strictly before merging doc-heavy changes.
```

### Expected Commands

```bash
uv run mkdocs build --strict
```

### Documentation Rules

- `tooling.md` is the inventory.
- `tool-decisions.md` explains rationale.
- `frontend-architecture.md` explains frontend state/runtime boundaries.
- `background-processing-architecture.md` explains async/workflow/task boundaries.
- `production-readiness.md` explains commercial operations and release gates.
- ADRs record decisions that should not change casually.

## Release and CI Workflow

CI is the enforcement layer for project discipline.

```text
1. Developer opens PR.
2. GitHub Actions run lint/type/test/build/security checks.
3. Generated artifacts/contracts are checked for drift.
4. Container and docs checks run where applicable.
5. PR is reviewed.
6. Merge triggers release/deploy automation according to configured workflows.
7. Production errors, jobs, uptime, and spend are monitored.
```

### Release Rules

- Do not merge broken checks unless there is an explicit documented exception.
- Do not deploy schema changes without migrations.
- Do not deploy frontend API changes without regenerated types.
- Do not introduce a new always-running service without cost and observability notes.
- Do not introduce a new production dependency without a rollback plan.

## Production Operations Workflow

Production operations should be planned before broad commercial traffic.

```text
1. Instrument application errors with Sentry or equivalent.
2. Add uptime checks for health and critical user journeys.
3. Add logs and alerts for workflow/task failures.
4. Add cost monitoring and budget alerts.
5. Use LaunchDarkly feature flags for high-risk releases.
6. Add incident routing and runbooks when users depend on uptime.
7. Add OpenTelemetry when tracing across API/workers/services becomes necessary.
```

### Operational Ownership

| System | Required production visibility |
| --- | --- |
| FastAPI | Request errors, latency, auth failures, rate-limit hits |
| Next.js frontend | Client errors, route failures, broken critical flows |
| PostgreSQL | Backup status, migration history, connection pressure |
| Redis | Memory, eviction, key TTL behavior, rate-limit anomalies |
| Temporal | Workflow failures, stuck workflows, retry storms |
| Celery | Failed tasks, queue depth, retry loops, worker health |
| RabbitMQ | Queue depth, dead letters, broker health |
| Email provider | Delivery failures, bounce/spam issues |
| CI/CD | Failed checks, deploy failures, release drift |

## Migration Baseline Tooling

These tools are approved for migration kickoff, but each tool still has strict usage boundaries.
They are not interchangeable and should not bleed into each other's responsibilities.

| Tool | Migration status | Use for | Avoid |
| --- | --- | --- | --- |
| Next.js | Approved for migration kickoff | Frontend app shell, routes, layouts, page composition | Backend business logic, workflow execution, direct database ownership |
| Temporal | Approved for migration kickoff | Durable multi-step workflows with retries, waiting, and recovery | Cache, rate limits, short throwaway jobs |
| Celery + RabbitMQ | Approved for migration kickoff | Short independent tasks and async fan-out | Durable multi-step workflows that need workflow history |
| TanStack Query | Approved for migration kickoff | API server-state fetching, caching, and invalidation | Local drag/hover/form UI state |
| Redux Toolkit | Approved for migration kickoff | Dashboard editor drafts, undo/redo, selection, breakpoints | Mirroring backend server state |
| Zustand | Approved for migration kickoff | Small shared UI state | Duplicating Redux editor state or backend server state |
| Zod | Approved for migration kickoff | Runtime validation for forms, URL params, env, and localStorage | Replacing backend Pydantic validation |
| MSW | Approved for migration kickoff | Deterministic frontend API tests and stories | Replacing integration or e2e coverage |
| Schemathesis | Approved for migration kickoff | OpenAPI contract fuzzing for critical API endpoints | Replacing deterministic API tests |
| k6 | Approved for migration kickoff | Load and latency regression checks for critical flows | One-off manual performance guesses |
| LaunchDarkly | Approved for migration kickoff | Feature-flag rollout control and fast rollback for risky releases | Long-lived flag sprawl without owner/removal date |

## Adoption Gates for Deferred Tools

These tools are not part of migration kickoff baseline.
Adopt them only when the trigger condition is met and an owner is assigned.

| Tool | Current status | Adopt when | Why deferred |
| --- | --- | --- | --- |
| Provider-managed email templates | Deferred | Non-code template editing is needed and governance/versioning is documented | Keep core transactional templates reviewable in source control |
| OpenTelemetry backend/collector stack | Deferred | Cross-service incidents require trace correlation beyond Sentry and structured logs | Avoid early operational complexity and telemetry cost |
| Public status page tooling | Deferred | Customer-facing incident communication requires a dedicated public surface | Avoid additional operations overhead before external dependency exists |
| Dedicated incident paging platform | Deferred | On-call rotation and escalation policies require automated paging | Avoid premature process/tooling burden before on-call maturity |
| Additional persistent analytics/search datastores | Deferred | PostgreSQL no longer satisfies latency/scale/query needs for specific workloads | Avoid source-of-truth drift and extra data-pipeline complexity |

## Vertical Slice Implementation Strategy

Prefer slices that prove the architecture end to end.

### Slice 1: Password Reset

```text
Next.js/FastAPI form endpoint
→ Redis rate limit
→ PostgreSQL token record
→ Celery/RabbitMQ email task
→ Jinja2-rendered HTML and text templates (HTML compiled from MJML when active)
→ email provider
→ pytest + Playwright smoke test
```

This validates request handling, rate limiting, task execution, email rendering, and browser flow.

### Slice 2: Total Signals Dashboard Widget

```text
FastAPI summary endpoint
→ PostgreSQL query + optional Redis cache
→ OpenAPI type generation
→ TanStack Query frontend query
→ React widget
→ sparkline tooltip/local state
→ card click to filtered signals list
→ Vitest + Playwright smoke test
```

This validates the frontend/backend API loop.

### Slice 3: Dashboard Editor

```text
saved layout from FastAPI/PostgreSQL
→ TanStack Query load
→ Redux Toolkit draft layout
→ drag/resize/undo/redo
→ save mutation
→ FastAPI validation/persistence
→ Playwright editor smoke test
```

This validates complex client state boundaries.

### Slice 4: Durable Import Workflow

```text
upload/import request
→ FastAPI import record
→ Temporal workflow start
→ activities validate/parse/deduplicate/store
→ PostgreSQL status updates
→ frontend status page/query
→ workflow failure/retry visibility
```

This validates Temporal and workflow observability.

## Anti-Patterns

Avoid these patterns:

- Storing API data in Redux when TanStack Query should own it.
- Storing product data in Redis because it is fast.
- Using RabbitMQ as a cache or rate limiter.
- Using Celery for multi-step business workflows that need history/progress.
- Using Temporal for raw high-frequency throwaway events.
- Duplicating FastAPI/Pydantic schemas manually in frontend TypeScript.
- Running multiple frontend app shells as permanent competitors.
- Using a tool outside its defined boundary just because it is available.
- Treating test coverage percentage as proof of correctness.
- Treating local success as production readiness.
- Letting provider-managed email templates bypass review for critical flows.
- Creating background jobs for every tiny event instead of batching/caching/countering.

## Quick Command Set

| Goal | Command |
| --- | --- |
| Sync Python environment | `uv sync` |
| Start local API dev server | `task dev` |
| Start local DB stack | `task up` |
| Run full project quality gate | `task check` |
| Run backend tests | `task test` |
| Run backend type checks | `task typecheck` |
| Run frontend build | `npm --prefix web run build` |
| Run frontend dev server | `npm --prefix web run dev` |
| Run frontend lint | `npm --prefix web run lint` |
| Run frontend typecheck | `npm --prefix web run typecheck` |
| Run frontend tests | `npm --prefix web run test` |
| Generate frontend API types | `npm --prefix web run contracts:generate` |
| Check generated contract drift | `npm --prefix web run contracts:check` |
| Run e2e smoke tests | `task test:e2e` |
| Build docs strictly | `uv run mkdocs build --strict` |
| Lint GitHub Actions | `uv run actionlint` |

## Final Operating Model

The target development model is:

```text
Design decision
→ documented boundary
→ backend/API contract if needed
→ generated frontend types
→ frontend implementation with correct state owner
→ background workflow/task only if needed
→ tests at the correct layer
→ CI quality gate
→ production monitoring once deployed
```

The most important rule is simple:

```text
Do not choose tools because they can do something.
Choose tools because they own that responsibility in this project.
```
