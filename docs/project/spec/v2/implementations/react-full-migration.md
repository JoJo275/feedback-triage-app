# Full React Migration Plan (Project-Wide)

> Status: execution-ready plan, pending ADR approval gate.
> Owner: v2 frontend track.
> Scope: migrate all user-facing pages from server-rendered HTML + vanilla JS to a React frontend, while keeping FastAPI + Postgres as the backend.

## Why this exists

The current v2 contract ships static HTML + vanilla JS for page rendering.
This document defines a concrete migration plan for a full React frontend,
including sequencing, risk controls, and rollback gates.

This is intentionally staged so we avoid a big-bang rewrite.

## Where this fits in current architecture

- This file is the project-wide React migration plan.
- ADR 076 is still authoritative for the current React-island pilot only
   (`/w/{slug}/dashboard/react`).
- The default dashboard route (`/w/{slug}/dashboard`) remains the shipped
   production surface until a new ADR explicitly approves full-route replacement.

## Decision gate first

Before coding starts, file and accept a new ADR to supersede the v2 deferment
of a full React rewrite (F2 in spec-v2).

Required ADR outcomes:

- confirm React adoption scope (full SPA vs hybrid)
- confirm build toolchain and deployment model
- confirm whether any pages remain server-rendered for SEO/caching reasons
- confirm data-fetching and state-management approach

Without this decision gate, this plan is reference-only.

## Should this project switch fully to React?

This section answers the switch question directly and sets an actionable
recommendation.

### Pros of switching to React

- Better long-term maintainability for complex UI state and composition.
- Stronger component reuse across dashboard, inbox, roadmap, changelog, and settings.
- More predictable testing at the component/unit boundary.
- Cleaner client-side routing and data orchestration for multi-page workflows.
- Easier onboarding for frontend contributors used to TypeScript + component patterns.

### Cons of switching to React

- Introduces a permanent Node toolchain and lockfile governance burden.
- Higher operational complexity (bundle pipeline, manifest serving, CSP hardening).
- Short-term migration risk from parity regressions while two stacks coexist.
- Potential performance regressions if bundle budgets and code splitting are not enforced.
- Longer release cadence during migration because each route needs parity sign-off.

### Recommendation

Recommend switching this project to React if all three conditions are true:

1. The team accepts long-term ownership of Node dependency governance.
2. Route-level parity testing capacity is available for every migrated page.
3. The roadmap expects continued UI complexity growth beyond vanilla JS comfort.

If any condition is false, keep the current architecture and continue with scoped
React islands only.

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

## Recommended additions incorporated (execution baselines)

The plan now includes the previously recommended additions as locked execution
decisions.

| Area | Locked decision for implementation | Verification gate |
| --- | --- | --- |
| Frontend package governance | Use npm in `web/` with committed `package-lock.json`, Node LTS 22, Dependabot weekly updates, and CI gate on `npm audit --audit-level=high`. | CI fails on lock drift or high/critical advisories. |
| CSP and asset-hosting policy | Serve React assets only from same-origin `/static/app/`; no runtime CDN scripts/styles in production. CSP baseline: `script-src 'self'`, `style-src 'self'`, `img-src 'self' data:`, `connect-src 'self'`. | Security tests confirm headers on migrated routes. |
| Manifest + cache-bust integration | Vite emits `manifest.json`; FastAPI loads and validates required entries at startup. Missing/invalid manifest triggers legacy-route fallback and startup error log. | Startup validation test plus rollback canary. |
| Frontend observability contract | Every React request includes `x-client-release`; client error boundary and `window` error handlers emit structured telemetry with backend `x-request-id` correlation when present. | End-to-end telemetry smoke test in canary workspace. |
| Page-level parity checklists | Every route gets a checklist in this file before migration starts; each checklist is a release gate for that route's flag. | Route cannot flip default-on without signed checklist. |
| Keyboard/a11y parity details | Route-level requirements include skip-link continuity, heading order, label coverage, focus visibility, keyboard-only workflow completion, and axe clean run. | Playwright + axe + manual keyboard pass required. |
| Feature-flag ownership model | Every `react_*` flag must define owner role, creation date, expiry date, and removal criteria; expired flags block release. | Release checklist fails if any expired flag remains. |

## Route parity checklists (release gates)

Use this table as a required sign-off sheet before enabling each React route by
default.

| Route group | Behavior parity | Data/API parity | A11y parity | Performance parity |
| --- | --- | --- | --- | --- |
| Dashboard | widget ordering, inline actions, card links, visual states | same summary values and filters | keyboard card navigation and focus ring | no worse than +15 percent LCP vs legacy |
| Inbox | filters, sorting, pagination, stale-row treatment | same query params and envelope handling | full keyboard triage flow | no worse than +15 percent LCP vs legacy |
| Roadmap | status columns and publish toggles | same publish semantics and enum handling | keyboard movement across columns | no worse than +15 percent LCP vs legacy |
| Changelog | shipped list behavior and empty states | same published item selection rules | keyboard navigation for list actions | no worse than +15 percent LCP vs legacy |
| Submitters | row actions, detail drill-down, search | same submitter matching semantics | table navigation and visible labels | no worse than +15 percent LCP vs legacy |
| Insights | chart interactions and labels | same aggregation windows and filters | non-pointer path for all actions | no worse than +15 percent LCP vs legacy |
| Settings | member/tag/public-submit controls | same mutation outcomes and error codes | form labels, errors, and focus return | no worse than +15 percent LCP vs legacy |

## Feature flag register (initial)

| Flag | Owner role | Expiry | Removal criteria |
| --- | --- | --- | --- |
| `react_dashboard` | Frontend lead | 2026-09-15 | 14-day stable default-on with no sev-1 parity incidents |
| `react_inbox` | Frontend lead | 2026-10-01 | parity checklist complete and 14-day stable default-on |
| `react_roadmap` | Frontend lead | 2026-10-15 | parity checklist complete and 14-day stable default-on |
| `react_changelog` | Frontend lead | 2026-10-15 | parity checklist complete and 14-day stable default-on |
| `react_submitters` | Frontend lead | 2026-11-01 | parity checklist complete and 14-day stable default-on |
| `react_insights` | Frontend lead | 2026-11-01 | parity checklist complete and 14-day stable default-on |
| `react_settings` | Frontend lead | 2026-11-15 | parity checklist complete and 14-day stable default-on |

## Implementation start checklist

This checklist must be complete before any Phase 1 route migration begins.

1. ADR for full migration is accepted and linked from this file.
2. Node 22 and npm are pinned in CI and local setup docs.
3. `web/package-lock.json` is committed and `npm audit --audit-level=high` is wired into CI.
4. FastAPI manifest startup validation and legacy-fallback behavior are merged.
5. CSP policy for `/static/app/` bundles is deployed in non-production and verified.
6. Client telemetry with release id + `x-request-id` correlation is validated in canary.
7. Feature flags from the register are created with owners and expiry metadata.
8. Baseline legacy metrics are recorded for LCP, JS payload size, and route error rate.

## Impact summary (if full migration proceeds)

| Area | Expected impact | Risk level | Notes |
| --- | --- | --- | --- |
| FastAPI API routes | Low | Low | Keep `/api/v1/` contract stable; frontend consumer changes only |
| Page rendering layer | High | High | Route handlers/templates transition to React-mounted pages |
| Static asset/build pipeline | High | Medium | Adds Vite/React build outputs and CI checks |
| Frontend test matrix | Medium | Medium | Adds React unit/type/lint + broader e2e parity checks |
| Auth/session behavior | Low | Medium | Cookie/session model stays; client auth flow must preserve semantics |
| Multi-tenant scoping | Medium | High | Client-side fetching must preserve workspace-scoped URL/params |
| Existing widgets (including Total signals) | High | High | Breakage risk is mostly parity loss, not backend schema risk |

## Project areas React should not be used for

Even with a full UI migration, these surfaces should remain non-React.

| Area | Example paths/routes | Why React is not the right tool here |
| --- | --- | --- |
| API contract and request handling | `/api/v1/**`, `src/feedback_triage/api/**` | Server responsibilities (authz, tenancy, validation, persistence) stay in FastAPI. |
| Health/readiness probes | `/health`, `/ready` | Operational endpoints must stay lightweight, backend-native, and JS-independent. |
| Database schema and migrations | `alembic/**`, `src/feedback_triage/models/**` | React has no role in schema lifecycle or transactional integrity. |
| Auth/session enforcement | `src/feedback_triage/auth/**`, backend deps | Session/cookie trust boundary must remain server-side. |
| Email delivery logic | `src/feedback_triage/email/**` | Transactional email generation/sending remains backend infrastructure. |
| Repository docs site | `docs/**`, `mkdocs.yml` | Documentation publishing uses MkDocs and should remain decoupled from app runtime. |
| Dev/CI automation | `scripts/**`, `tools/**`, `.github/workflows/**` | Build/test/release automation remains scripting + CI concern, not frontend runtime code. |

## Pros and cons of keeping those areas non-React

### Pros

- Smaller migration blast radius; backend and operational surfaces remain stable.
- Lower risk of regressions in auth, tenancy, and database invariants.
- Faster rollback: UI route flags can revert without touching API/migration code.
- Clear separation of concerns between rendering layer and system-of-record logic.
- Better resilience for probes/ops endpoints because they do not depend on frontend build artifacts.

### Cons

- Mixed-stack complexity (React frontend + Python backend + docs/tooling systems).
- More integration seams (manifest lookup, error correlation, shared contracts).
- Team context switching cost across different stacks and toolchains.
- Higher chance of duplicated presentation logic if boundaries are not documented.
- Requires stronger architecture discipline to prevent UI concerns leaking into backend domains (and vice versa).

## Total signals no-break contract during migration

Do not switch the default dashboard route to React until all items below are
true on the React implementation:

1. Visual parity with
   `docs/project/spec/v2/implementations/total-signals-widget.md`.
2. Top-left icon remains `/static/img/inbox-badge.svg`.
3. Card remains a single clickable target routing to `/w/{slug}/feedback`.
4. Hover cursor over sparkline remains `pointer` (not crosshair).
5. Marker wording remains `Largest increase` and
   `Second-largest increase`.
6. Delta formatting and direction semantics remain unchanged.
7. The sparkline `aria-label` remains present and meaningful.

Required validation gates before flipping any React dashboard flag:

1. `tests/api/auth/test_dashboard_page.py` stays green.
2. `tests/api/test_dashboard_summary.py` stays green.
3. Playwright parity check for the Total signals card passes
   (visual + click target + keyboard focus).
4. Manual canary on a seeded workspace confirms icon, delta row,
   comparison label, and sparkline behaviors match the shipped card.

## What breaks first when switching dependencies

Changing dependencies alone usually does not break production behavior.
The common breakpoints are route swaps and asset/runtime assumptions:

1. Replacing `/w/{slug}/dashboard` before parity is complete.
2. Removing legacy dashboard script/template paths before React route is default-safe.
3. Changing CSS/token pipeline without preserving summary-card classes.
4. Moving/removing static icon assets referenced by the shipped template.
5. Losing localStorage key compatibility for dashboard layout state.

## Target architecture

- Backend: FastAPI remains system of record for APIs, auth/session cookies, and DB access.
- Frontend: React + TypeScript + Vite app source in `web/`; hashed build artifacts emitted to `src/feedback_triage/static/app/` and served by FastAPI static mounts.
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
- React app scaffold under `web/` with TypeScript + Vite.
- Build integration: Vite output served from `src/feedback_triage/static/app/` with manifest lookup.
- CI jobs for React lint, typecheck, unit tests, build, and audit.
- CSP/header updates merged for bundled assets.
- Feature-flag metadata register created and tracked.

Verification:

- `task check` remains green.
- `task web:install`, `task web:build`, and `task web:typecheck` pass in CI and local dev.
- startup validation fails closed when manifest keys are missing.
- CSP checks pass on at least one migrated canary route.

Exit criteria:

- foundation merged without replacing any existing production page.
- implementation start checklist is fully complete.

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

### Phase 2 implementation status (2026-05-19)

- [x] Flag-gated React shells now render on the authenticated routes
   (`/dashboard`, `/inbox`, `/feedback`, `/roadmap`, `/changelog`,
   `/submitters`, `/insights`, `/settings`) with `?view=legacy`
   parity fallback.
- [x] Shared React route metadata is emitted via a common template and
   consumed by the Vite entrypoint (`data-page-key`,
   `data-active-section`, `data-legacy-url`).
- [x] Frontend failure telemetry hooks are wired for API errors,
   mutation errors, and runtime error events, with authenticated
   ingestion at `/api/v1/frontend-events`.
- [x] Full Playwright parity matrix per route is implemented in
   `tests/e2e/test_react_authenticated_pages_phase2.py` and remains
   the final rollout gate before default-on in production.

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

### Phase 3 implementation status (2026-05-19)

- [x] Flag-gated React shells now render on public routes (`/`,
   `/w/{slug}/submit`, `/w/{slug}/roadmap/public`,
   `/w/{slug}/changelog/public`) with `?view=legacy` fallback.
- [x] Public route payload bootstrap is emitted through the shared
   React public-shell template and consumed by the Vite entrypoint.
- [x] Public submit continues to post to
   `/api/v1/public/feedback/{slug}` with unchanged honeypot and
   rate-limit behavior.
- [x] API parity checks are implemented in
   `tests/api/test_react_public_pages_phase3.py`.
- [x] Playwright parity checks are implemented in
   `tests/e2e/test_react_public_pages_phase3.py`.

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
task web:install
task web:test
task web:lint
task web:typecheck
task web:build
task web:audit
```

Targeted no-regression commands for the shipped Total signals card:

```bash
uv run pytest tests/api/auth/test_dashboard_page.py
uv run pytest tests/api/test_dashboard_summary.py
```

## Rollout and rollback

Rollout:

- feature flag by page group (`react_dashboard`, `react_inbox`, etc.)
- canary workspace allowlist first
- observe error rate and page load metrics before widening
- keep previous stable asset bundle available until each page-group stability window closes

Rollback:

- flip feature flags to restore legacy page handlers
- retain legacy scripts/templates until full-production stability window passes
- on manifest/asset integrity failure, force legacy handler path and block React route rendering

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
- `docs/project/spec/v2/implementations/total-signals-widget.md`
- `docs/adr/076-use-react-island-for-dashboard-widgets.md`
