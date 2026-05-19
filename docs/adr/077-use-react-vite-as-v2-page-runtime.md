# ADR 077: Use React + Vite as the v2 page runtime

## Status

Accepted

## Context

v1.0 intentionally chose static HTML + vanilla JS ([ADR 051](051-static-html-vanilla-js.md)).
Later, v2.0 introduced a scoped React dashboard-widget pilot
([ADR 076](076-use-react-island-for-dashboard-widgets.md)).

The current codebase has moved beyond the pilot model:

- Workspace routes (`/w/{slug}/dashboard`, `/inbox`, `/roadmap`, etc.) now render through a shared React shell.
- Public routes (`/`, `/w/{slug}/submit`, `/roadmap/public`, `/changelog/public`) also render through a React shell.
- Vite assets and manifest resolution are runtime requirements for these routes.

That implementation drift left architecture docs split between:

- "vanilla-first + React island" language, and
- production behavior that is already React-first for the page surfaces users rely on.

This mismatch causes planning confusion and parity regressions (including dashboard widget behavior not surviving route/runtime swaps).

## Decision

Adopt React + Vite as the authoritative page runtime for v2 surfaces.

1. Frontend source of truth for migrated pages is `web/`.
2. FastAPI remains the server/runtime boundary for auth, tenancy, API contracts, and static hosting.
3. React pages are mounted through shared shell templates that bootstrap route metadata and resolve hashed assets from Vite's `manifest.json`.
4. Auth pages and selected legacy pages may remain server-rendered while intentionally unmigrated.
5. ADR 076 is superseded by this decision.
6. ADR 051 remains historical context for the shipped v1.0 implementation.

## Alternatives Considered

### Revert to v2 vanilla-plus-island model

Return workspace/public routes to static HTML + vanilla JS and keep React only for a small island.

**Rejected because:** The repository has already moved to React-backed route rendering across major surfaces. Reverting now would add large churn, re-open parity risk, and delay feature work.

### Keep current code and leave docs unchanged

Treat the migration as an implementation detail and avoid architecture updates.

**Rejected because:** This keeps decision debt unresolved and guarantees repeated confusion about allowed dependencies, project structure, and release criteria.

## Consequences

### Positive

- Architecture docs match runtime behavior.
- One primary frontend runtime for migrated page surfaces.
- Better leverage of typed UI components and frontend test tooling.

### Negative

- Permanent Node/npm toolchain ownership.
- Bundle/manifest/CSP concerns become first-class operational risks.
- Two rendering modes still coexist during remaining migration tails.

### Neutral

- FastAPI, SQLModel, auth/session model, tenancy rules, and `/api/v1` contracts are unchanged.
- Session-per-request and DB invariants remain exactly as before.

### Mitigations

- Keep manifest validation fail-closed at startup.
- Keep route-parity tests as release gates per the migration plan.
- Keep React scope explicit in route helpers and shell templates.

## Implementation

- [web/package.json](../../web/package.json) - React/Vite toolchain and scripts.
- [web/vite.config.ts](../../web/vite.config.ts) - manifest output into `static/app`.
- [src/feedback_triage/pages/react_shell.py](../../src/feedback_triage/pages/react_shell.py) - shared React shell rendering helpers.
- [src/feedback_triage/templates/pages/react/workspace_shell.html](../../src/feedback_triage/templates/pages/react/workspace_shell.html) - authenticated shell bootstrap.
- [src/feedback_triage/templates/pages/react/public_shell.html](../../src/feedback_triage/templates/pages/react/public_shell.html) - public shell bootstrap.
- [src/feedback_triage/frontend_assets.py](../../src/feedback_triage/frontend_assets.py) - Vite manifest resolution.

## References

- [ADR 051](051-static-html-vanilla-js.md)
- [ADR 076](076-use-react-island-for-dashboard-widgets.md)
- [Full React migration plan](../project/spec/v2/implementations/react-full-migration.md)
- [v2 tooling](../project/spec/v2/tooling.md)
- [v2 UI](../project/spec/v2/ui.md)
