# Dependency and Tooling Decision Questionnaire

Use this checklist before adding new dependencies, frameworks, or tooling.
Answer each question with one of: must now, should soon, later, or not needed.

---

## Product Shape

- Is SignalNest mostly a dashboard/inbox SaaS app, or also a public marketing/content site?
- Do you need public pages indexed by search engines?
- Will workspaces have public pages like /w/acme/roadmap or /w/acme/changelog?
- Is the dashboard customizable by every user, or mostly fixed?
- Do users need drag-and-drop widgets in v1, or later?

## Data and State

- What data must persist in the backend?
- What data is temporary UI state only?
- Should filters be stored in the URL so links are shareable?
- Do you need real-time updates?
- Do you need optimistic UI, where the frontend updates before the backend confirms?
- Do you need undo/redo for dashboard editing?
- Do users have per-workspace settings and per-user settings?

## Backend

- Are you committed to Python/FastAPI long term?
- Do you need background jobs for emails, imports, summaries, or scheduled reports?
- Do you need multi-tenant permissions?
- Are you using PostgreSQL in production?
- Do you need file uploads or attachments?

## Frontend

- Do you want the frontend and backend in separate deploys?
- Do you want Next.js routing/layout conventions?
- Are you comfortable learning server/client component boundaries?
- Do you want a mostly static React app that calls FastAPI?
- Will you need advanced SEO?
- Will the app be mostly behind login?

## Testing and Maintenance

- Which user flows must never silently break?
- Do you want CI to block broken builds?
- Are you willing to write Playwright smoke tests?
- Do you want generated TypeScript API types from FastAPI?
- Do you want Storybook for visual component development?
- Do you want strict TypeScript now, or gradually?

## Portfolio Framing

- Which sounds stronger for the portfolio you want?
- Option A: A clean FastAPI + React/Vite SaaS app with tests and CI.
- Option B: A clean FastAPI + Next.js SaaS app with tests, CI, typed API client, and documented architecture.
- For portfolio value, the second is stronger. For speed and lower risk, the first is safer.

## Security and Compliance

- What is your authentication model (session cookies, JWT, SSO), and where is authorization enforced?
- Do you need audit logs for key user actions?
- Do you need role-based access control now, or only ownership checks in v1?
- Will you process PII, payment data, or regulated data that changes dependency choices?
- Do you need dependency allowlists, license checks, and vulnerability gates in CI?

## Performance and Scale

- What are expected p95 latency and throughput targets for v1?
- Which endpoints need caching, and where should cache invalidation live?
- What growth assumptions might force early choices in queueing, storage, or search?
- Do you need full-text search, analytics, or event streams in v1?

## Operations and Deployment

- What environments do you need (local, preview, staging, production), and who can deploy each?
- Do you need zero-downtime migrations and rollback plans?
- Which observability tools are mandatory (structured logs, metrics, tracing, alerts)?
- Do you need feature flags to ship partially complete work safely?

## Team and Developer Experience

- What level of tool complexity can the team realistically maintain?
- Do you want one package manager and one task runner enforced repo-wide?
- Should code generation be introduced now, or after API shape stabilizes?
- Which checks are required locally versus only in CI to keep iteration fast?

## Cost and Vendor Risk

- Which managed services are acceptable for v1 budget and lock-in tolerance?
- Do any tool choices create expensive migration paths later?
- Can critical parts run locally for development without paid cloud dependencies?
