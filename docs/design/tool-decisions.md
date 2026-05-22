# Tool Decisions

!!! danger "Decision Boundary"
    This document explains why major tools are used, planned, deferred, or rejected.
    It does not replace `tooling.md`, which is the command-oriented tool inventory.
    It should be updated when a tool changes project architecture, runtime cost, deployment shape, or day-to-day workflow.

## Purpose

This document records the rationale behind major tool choices for the project. It answers:

- Why this tool belongs in the project.
- What problem it solves.
- What it must not replace.
- What would cause the decision to be revisited.
- Which tools overlap and how boundaries are enforced.

## Related Documents

- [`../tooling.md`](../tooling.md) — complete tool inventory, commands, status, and boundaries.
- [`background-processing-architecture.md`](background-processing-architecture.md) — Temporal, Celery, RabbitMQ, Redis, and worker ownership.
- [`frontend-architecture.md`](frontend-architecture.md) — frontend runtime, state, API, and component architecture.
- [`production-readiness.md`](production-readiness.md) — commercial-readiness gates and operational requirements.
- [`../adr/README.md`](../adr/README.md) — formal Architecture Decision Records.

## Decision Principles

1. **Use one tool for one job.** Avoid overlapping responsibilities unless the boundary is explicit.
2. **Prefer stable foundations over speculative dependencies.** Add specialized tools when they solve a named problem.
3. **Keep source-of-truth data in PostgreSQL.** Do not let cache, queue, workflow, or frontend state become canonical product state.
4. **Separate server state from client state.** API-backed data belongs in server-state tooling; UI draft state belongs in client-state tooling.
5. **Make commercial-readiness explicit.** Production tools must have an adoption gate, cost expectation, and operational owner.
6. **Preserve Python backend value.** FastAPI remains the backend authority unless a formal ADR replaces it.
7. **Do not run duplicate architectures indefinitely.** Planned migrations must include a retirement path for the old tool.

## Current Decision Summary

| Area | Decision | Status | Rationale | Revisit Trigger |
| --- | --- | --- | --- | --- |
| Python environment | Use `uv` as Python environment and lockfile manager. | Active | Fast, reproducible Python dependency management. | Revisit only if packaging workflow becomes incompatible with `uv`. |
| Python build backend | Use `hatchling` + `hatch-vcs`. | Active | Clean build backend with versioning from git tags. | Revisit if release/versioning requirements outgrow tag-based versioning. |
| Command runner | Use `Taskfile.yml`. | Active | Makes common workflows discoverable and repeatable. | Revisit if commands become too complex and need scripts. |
| Backend API | Keep FastAPI as backend API/business-logic layer. | Active | Strong Python fit, explicit API boundary, Pydantic/OpenAPI integration, existing app investment. | Revisit only if project intentionally becomes all-TypeScript/Node. |
| Database | Use PostgreSQL as production source of truth. | Active | Durable relational data model for users, workspaces, signals, layouts, and audit records. | Revisit only for specific analytics/search workloads that exceed relational fit. |
| ORM | Use SQLModel / SQLAlchemy 2.x. | Active | Typed ORM patterns and SQLAlchemy migration compatibility. | Revisit if ORM layer causes unacceptable complexity or performance issues. |
| Migrations | Use Alembic for schema changes. | Active | Reviewable, versioned database evolution. | Revisit only if DB stack changes. |
| API contracts | Use `openapi-typescript` for generated frontend API types. | Active | Reduces frontend/backend API drift. | Add full client generation if handwritten API wrappers become inconsistent. |
| Frontend runtime | Vite + React is active; Next.js is planned as a possible app-shell migration. | Mixed | Vite is working now; Next.js may provide stronger app route/layout conventions for v2. | Requires ADR before migration. |
| Frontend language | Use TypeScript. | Active | Stronger contracts for component props, API data, widget layouts, and editor state. | Do not revisit; only adjust strictness. |
| Server-state management | Adopt TanStack Query. | Planned | Prevents scattered fetch/loading/error/cache logic in React. | Revisit if Next.js server data patterns fully replace client query needs. |
| Complex editor state | Adopt Redux Toolkit for dashboard editor state. | Planned | Undo/redo, draft layouts, selected widget, breakpoints, and unsaved changes justify structured state. | Revisit if editor state remains small enough for `useReducer`. |
| Shared small UI state | Keep Zustand planned, not default. | Planned | Useful for small cross-component UI state if Redux is too heavy for app-shell state. | Do not adopt if Redux Toolkit already owns the same state. |
| Runtime validation | Use Zod selectively. | Planned | Best for forms, URL params, env values, and localStorage data. | Do not duplicate every Pydantic schema manually. |
| Styling | Use CSS variables/design tokens as the stable foundation. | Active | Centralizes color, radius, spacing, density, and semantic values. | Revisit only if a full design-system package is introduced. |
| Utility CSS | Tailwind is planned. | Planned | Speeds dashboard styling if adopted with clear token rules. | Requires frontend styling ADR before broad use. |
| UI primitives | shadcn/ui + Radix are planned. | Planned | Accessible primitives and copy-owned components without monolithic lock-in. | Revisit if visual identity becomes too generic or component source becomes hard to maintain. |
| Durable workflows | Temporal is planned. | Planned | Best fit for multi-step durable workflows with retries, progress, and recovery. | Adopt after first durable workflow is designed. |
| Simple task queue | Celery + RabbitMQ are planned. | Planned | Reserved for short independent Python jobs, especially high-volume small jobs. | Adopt only if workload justifies separate task queue. |
| Cache/rate limits | Redis is planned. | Planned | Correct place for rate limits, cache, locks, and temporary counters. | Adopt before public forms/auth flows need throttling. |
| Email templates | Use Jinja2 for backend-owned transactional emails. | Active | Simple source-controlled HTML/text templates fit FastAPI. | Add MJML when email layouts become complex. |
| MJML | Keep planned, not immediate. | Planned | Useful for complex responsive email layouts. | Adopt when plain HTML email templates become hard to maintain. |
| Provider templates | Defer. | Deferred | Provider-managed templates reduce deploys but weaken code review/auditability. | Adopt only with governance around provider-side template changes. |
| Error monitoring | Adopt Sentry before broad production traffic. | Planned | Fastest path to production exception visibility. | Revisit vendor if cost, privacy, or telemetry requirements change. |
| Tracing | Defer OpenTelemetry until distributed debugging needs it. | Planned | Valuable after multiple services/workers exist. | Adopt when cross-service trace correlation becomes necessary. |
| Load testing | Use k6 for release/capacity checks. | Planned | Repeatable latency and capacity validation. | Adopt after stable critical flows exist. |
| Contract fuzzing | Use Schemathesis for OpenAPI-driven API checks. | Planned | Finds API contract and edge-case failures. | Adopt once API schema is stable enough to test against. |

## Frontend Runtime Decision

### Current State

Vite + React is active for migrated v2 React pages. It is the current frontend build/runtime pipeline.

### Planned Option

Next.js is a planned option for a stronger app-shell architecture. If adopted, it should provide:

- File-based routing.
- Nested layouts.
- Loading and error boundaries.
- A cleaner split between public pages, auth pages, and authenticated app pages.
- A stronger portfolio-grade frontend framework story.

### Decision Boundary

Next.js must not become a second backend authority. If adopted:

- Next.js owns frontend routing, layouts, and React app shell.
- FastAPI remains backend source of truth for auth, permissions, business rules, workflows, and data access.
- PostgreSQL remains canonical product data storage.

### Adoption Gate

Adopt Next.js only after an ADR answers:

1. Does Vite remain for any surface, or is it retired from the main product app?
2. How will Next.js call FastAPI?
3. How will generated OpenAPI types be consumed?
4. How will auth/session boundaries work?
5. What routes move first?
6. What tests prove the migration did not break core flows?

## State Management Decision

### State Categories

| State Type | Owner | Examples |
| --- | --- | --- |
| Server state | TanStack Query | Signals, users, workspaces, tags, saved dashboard layout, dashboard summary data. |
| Local UI state | `useState` | Tooltip point, dropdown open, small tab selection, local input value. |
| Structured local state | `useReducer` | Feature-local multi-action state that does not need global access. |
| Complex editor state | Redux Toolkit | Dashboard draft layout, undo/redo, selected widget, breakpoint layout, unsaved changes. |
| Small shared UI state | Zustand, if needed | Sidebar collapsed, command palette open, density preference. |
| Runtime validation | Zod | Forms, URL params, env parsing, localStorage payloads. |

### Boundary Rules

- Do not put API/server data in Redux if TanStack Query can own it.
- Do not use Zustand and Redux for the same state.
- Do not use TanStack Query for transient hover/drag/tooltip state.
- Do not use Zod as a replacement for backend Pydantic validation.
- Do not use `useState` for undo/redo-heavy state graphs.

## Background Processing Decision

### Default Rule

- Temporal owns durable workflows.
- Celery owns short independent Python tasks.
- RabbitMQ is Celery's broker only.
- Redis owns cache, rate limits, locks, and temporary counters.
- PostgreSQL owns permanent product data and user-visible job/workflow records.

### Tool Boundary Table

| Workload | Tool |
| --- | --- |
| CSV import pipeline | Temporal |
| AI classification/summarization pipeline | Temporal |
| Weekly workspace report workflow | Temporal |
| Webhook delivery with durable retry history | Temporal |
| Password reset email | Celery, unless included in a larger workflow |
| Email verification | Celery, unless included in a larger workflow |
| Workspace invite email | Celery, unless included in a larger workflow |
| Expired token cleanup | Celery or scheduled job |
| Public feedback rate limit | Redis |
| Dashboard summary cache | Redis |
| Import lock | Redis, backed by PostgreSQL records when correctness matters |
| Job/workflow audit record | PostgreSQL |

### Overlap Rule

If a process could be implemented in either Temporal or Celery, prefer Temporal when the process has:

- Multiple steps.
- Business-state transitions.
- User-visible progress.
- Waiting/timers.
- Failure recovery requirements.
- Long-running execution.

Use Celery when the work is:

- Short.
- Independent.
- Python-native.
- High-volume enough that workflow history is not useful.
- Operationally simpler as a task queue.

## Email Decision

### Current Choice

Use source-controlled Jinja2 templates for transactional email.

### Why

- Fits FastAPI/Python backend ownership.
- Keeps templates reviewable in Git.
- Supports HTML and plain-text output.
- Avoids provider lock-in early.

### When MJML Becomes Worth It

Adopt MJML when email templates require:

- Complex responsive layouts.
- Multi-section branded emails.
- Reusable email components.
- Weekly reports or rich onboarding emails.
- Cross-client rendering consistency beyond simple templates.

### When Provider Templates Become Worth It

Adopt provider templates only if:

- Non-developers need to edit approved email copy/layout.
- Provider previews/versioning become valuable.
- Governance exists for provider-side changes.
- Template IDs and variables are versioned in code/docs.

## Testing Decision

| Layer | Tool | Purpose |
| --- | --- | --- |
| Python unit/integration | pytest | Backend service, API, DB, permission tests. |
| Python coverage | pytest-cov | Coverage visibility, not correctness guarantee. |
| Python lint/format | Ruff | Fast lint/format baseline. |
| Python type safety | mypy | Static typing for backend package. |
| Frontend lint | ESLint | JS/TS/React linting and hook safety. |
| Frontend typecheck | TypeScript | Compile-time contract checks. |
| Frontend unit/component | Vitest + React Testing Library | Component and reducer behavior. |
| API mocking | MSW | Deterministic API states in tests/dev/stories. |
| Browser flows | Playwright | Critical user journeys. |
| API contract fuzzing | Schemathesis | OpenAPI edge cases and contract mismatch discovery. |
| Load checks | k6 | Latency and capacity regression testing. |

## Security and Supply Chain Decision

Security tooling is active and should remain layered:

- Bandit: Python code-pattern scanning.
- pip-audit: Python dependency vulnerability inventory.
- gitleaks: secret scanning.
- CodeQL: semantic code scanning.
- OpenSSF Scorecard: repository posture.
- Syft: SBOM generation.
- Trivy/Grype: container vulnerability scanning.

No single security tool replaces the others. Each has a different scope.

## Adoption Gates for Planned Tools

| Tool | Adoption Gate |
| --- | --- |
| Next.js | ADR approved; first route migration plan written; tests defined. |
| TanStack Query | First typed API data flow is implemented. |
| Redux Toolkit | Dashboard editor state reaches undo/redo or multi-breakpoint complexity. |
| Zustand | A small shared UI state need exists outside Redux editor state. |
| Zod | First form/URL/env/localStorage boundary needs runtime validation. |
| Tailwind | Styling ADR defines token usage and class conventions. |
| shadcn/ui + Radix | First accessible dialog/menu/popover/tooltip primitive is needed. |
| Temporal | First durable multi-step workflow is designed. |
| Celery + RabbitMQ | First short independent task class justifies separate task queue. |
| Redis | Rate limits, cache, locks, or counters become required. |
| MSW | Frontend tests need deterministic API success/error/empty states. |
| Schemathesis | API schema is stable enough for contract fuzzing. |
| k6 | Critical flows are stable enough for repeatable load checks. |
| Sentry | Production-like environment serves real users/testers. |
| OpenTelemetry | Cross-service trace correlation becomes necessary. |
| Feature flags | High-risk feature rollout requires exposure control. |
| Status page | Commercial customers need incident communication. |
| Cost alerts | New paid/always-on services are introduced. |

## Explicit Non-Decisions

These choices are not final until an ADR is written:

- Whether Next.js fully replaces Vite for the product frontend.
- Whether Tailwind becomes the default styling method.
- Whether Celery/RabbitMQ are adopted before Temporal or only after throughput evidence.
- Which email provider becomes the long-term transactional email vendor.
- Which feature flag provider or self-hosted pattern is used.
- Which uptime/status page vendor is used.
- Which observability backend receives OpenTelemetry data.

## Rejected or Deferred Approaches

| Approach | Decision | Reason |
| --- | --- | --- |
| All-Next.js backend replacing FastAPI | Rejected for now | Existing Python backend/scripts and API ownership remain valuable. |
| RabbitMQ for cache/rate limits | Rejected | RabbitMQ is message transport, not a cache/rate-limit store. |
| Redis as permanent source of truth | Rejected | Redis is ephemeral operational state, not canonical product storage. |
| Provider-managed email templates by default | Deferred | Source-controlled templates are more reviewable early. |
| MJML for first simple transactional emails | Deferred | Jinja2 HTML/text templates are enough until email layouts become complex. |
| Redux for all state | Rejected | Server data belongs in TanStack Query; local UI state stays local. |
| Zustand as dashboard editor state owner | Rejected for complex editor | Undo/redo and layout graph complexity justify Redux Toolkit. |
| OpenTelemetry before Sentry | Deferred | Error triage should come before full distributed tracing. |

## Review Cadence

Review this document when:

- A planned tool becomes active.
- A runtime service is added.
- Monthly infrastructure costs change materially.
- A new commercial-readiness requirement is introduced.
- A major migration begins or ends.
- Tool boundaries are violated repeatedly.
