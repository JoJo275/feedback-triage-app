# Full React Migration Plan (Project-Wide)

> Status: proposed implementation plan.
> Owner: v2 frontend track.
> Scope: migrate all user-facing pages from server-rendered HTML + vanilla JS to a React frontend, while keeping FastAPI + Postgres as the backend.

## Why this exists

The current v2 contract ships static HTML + vanilla JS for page rendering.
This document defines a concrete migration plan for a full React frontend,
including sequencing, risk controls, and rollback gates.

This is intentionally staged so we avoid a big-bang rewrite.

## Decision gate first

Before coding starts, file and accept a new ADR to supersede the v2 deferment
of a full React rewrite (F2 in spec-v2).

Required ADR outcomes:

- confirm React adoption scope (full SPA vs hybrid)
- confirm build toolchain and deployment model
- confirm whether any pages remain server-rendered for SEO/caching reasons
- confirm data-fetching and state-management approach

Without this decision gate, this plan is reference-only.

## Goals

- Migrate authenticated app pages to React with parity on behavior and access control.
- Migrate public pages to React without weakening cache headers, SEO basics, or rate-limit posture.
- Preserve current API contracts where possible; add endpoint shape only when needed.
- Keep tenant isolation guarantees unchanged.
- Keep release risk low through phased rollout and dual-run validation.

## Non-goals

- No backend framework rewrite.
- No database engine change.
- No auth model replacement.
- No new workflow scope unrelated to migration parity.

## Target architecture

- Backend: FastAPI remains system of record for APIs, auth/session cookies, and DB access.
- Frontend: React + TypeScript + Vite built assets served by FastAPI static mounts.
- Routing:
  - React Router for in-app navigation.
  - Existing URL contract retained (`/w/<slug>/...`) to avoid deep-link breakage.
- Data layer:
  - `fetch` wrapper with typed request/response contracts.
  - query cache for list/detail pages (TanStack Query preferred).
- Styling:
  - continue current token system and Tailwind pipeline; no visual reset during migration.

## Migration strategy (strangler pattern)

## Phase 0 - Prereqs and guardrails

Deliverables:

- ADR accepted for full React migration.
- React app scaffold under `src/feedback_triage/static/app/` (or agreed frontend root).
- Build integration: Vite output served by FastAPI.
- CI jobs for React lint, typecheck, unit tests, and build.

Verification:

- `task check` remains green.
- bundle builds in CI and local dev.

Exit criteria:

- foundation merged without replacing any existing production page.

## Phase 1 - Shared app shell and primitives

Deliverables:

- React app shell with authenticated layout parity (sidebar/header/footer).
- shared components for status pills, cards, tables, modal, filters.
- typed API client and error-envelope normalizer.
- route-level auth/tenant context loader.

Verification:

- visual parity snapshots for shell components.
- unit tests for API client and error normalization.

Exit criteria:

- app shell can render a dashboard placeholder behind existing auth cookies.

## Phase 2 - Authenticated workflow pages

Suggested migration order:

1. Dashboard
2. Inbox
3. Roadmap
4. Changelog
5. Submitters
6. Insights
7. Settings

Deliverables per page:

- React route with parity controls and same URL path.
- parity tests for filters, sorting, pagination, and mutations.
- telemetry hooks for fetch/mutation failures.

Verification:

- Playwright parity tests for each migrated page.
- tenant-isolation API canaries still pass.

Exit criteria:

- all authenticated pages run in React by default behind a feature flag.

## Phase 3 - Public pages and marketing surface

Pages:

- landing page
- public submit page
- public roadmap
- public changelog

Deliverables:

- React implementations preserving existing cache headers and copy contracts.
- no regression in anonymous submit flow, honeypot behavior, and rate limits.

Verification:

- API tests for public submission unchanged and green.
- response headers validated for public roadmap/changelog cache contracts.

Exit criteria:

- all public pages migrated or intentionally retained server-rendered by ADR choice.

## Phase 4 - Legacy decommission

Deliverables:

- remove dead vanilla page scripts and unused templates.
- remove no-longer-used template routes while preserving API routes.
- docs/spec updates to reflect new frontend architecture.

Verification:

- grep confirms removed assets have no live references.
- no route regressions in smoke/e2e matrix.

Exit criteria:

- no production path depends on legacy vanilla page scripts.

## API and contract workstream

Expected API gaps to close during migration:

- ensure all page data used in templates has stable JSON endpoints.
- normalize error handling so React can consistently map envelope codes.
- add missing preference endpoints where UI state should be server-backed.

Rules:

- keep `/api/v1/` compatibility unless version bump is explicitly approved.
- do not break existing enum values and status semantics.

## Data and state strategy

- Server state: query cache keyed by workspace slug + resource + filter params.
- UI state: local component state, URL search params, or localStorage only for non-critical presentation preferences.
- Persisted layout/preferences should move to server-backed APIs where practical.

## Testing and quality gates

Minimum gate before default-on rollout:

- Python API suite: green
- React unit suite: green
- React typecheck/lint: green
- Playwright e2e smoke for all migrated routes: green
- a11y smoke (axe) on migrated routes: green

Recommended commands (final names to be wired in Taskfile):

```bash
task test
task test:e2e
task lint
task typecheck
task web:test
task web:lint
task web:typecheck
task web:build
```

## Rollout and rollback

Rollout:

- feature flag by page group (`react_dashboard`, `react_inbox`, etc.)
- canary workspace allowlist first
- observe error rate and page load metrics before widening

Rollback:

- flip feature flags to restore legacy page handlers
- retain legacy scripts/templates until full-production stability window passes

## Risks and mitigations

1. Route parity regressions.
   - Mitigation: dual-run tests and explicit parity checklist per page.
2. Tenant-scoping regressions in client-side data access.
   - Mitigation: central workspace-scoped API client + strict integration tests.
3. Performance regressions from bundle growth.
   - Mitigation: route-level code splitting and bundle budgets in CI.
4. CSS drift between old and new pages.
   - Mitigation: preserve tokens and component vocabulary during migration.

## Definition of done (full migration)

- All user-facing pages are React (or explicitly ADR-exempted).
- Legacy template/page JS code paths are removed.
- Docs and ADR index reflect React as active frontend architecture.
- CI quality gates are green for backend + frontend + e2e.
- Production rollout completed without unresolved sev-1 regressions.

## Related documents

- `docs/project/spec/spec-v2.md`
- `docs/project/spec/v2/implementation.md`
- `docs/project/spec/v2/implementations/dashboard.md`
- `docs/adr/076-use-react-island-for-dashboard-widgets.md`
