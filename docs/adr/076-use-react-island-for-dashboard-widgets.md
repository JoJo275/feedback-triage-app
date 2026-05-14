# ADR 076: Use a React island for dashboard widget editing pilot

## Status

Accepted

## Context

The v2.0 frontend architecture is static HTML plus vanilla JS
([ADR 051](051-static-html-vanilla-js.md)). The v2.0 spec also defers a
full React/Vite SPA rewrite as future work due cost and scope.

At the same time, widget-grid interactions (drag, resize, responsive
breakpoints, collision prevention, and persistence) are easier to compose
with React-first grid libraries.

We need a way to adopt React for this surface without forcing an immediate
full-frontend rewrite.

## Decision

Introduce React as an isolated page-level island for dashboard widget editing.

- Add a dedicated route: `/w/{slug}/dashboard/react`.
- Keep the production dashboard route (`/w/{slug}/dashboard`) unchanged.
- Implement the pilot surface in `static/js/dashboard_react_widgets.js`.
- Use `react-grid-layout` for drag/resize/snap/collision behavior.
- Persist layout per workspace in localStorage with shape `{ id, x, y, w, h }`.

This is an incremental adoption decision, not a framework migration decision.

## Alternatives Considered

### Full React/Vite SPA rewrite now

Move all page surfaces to a bundled React frontend.

**Rejected because:** This conflicts with current v2.0 scope control and would
expand the migration blast radius far beyond the widget surface.

### Continue with vanilla JS only

Keep all widget behavior in the existing `dashboard.js` implementation.

**Rejected because:** We need a practical React path in this repository and a
safe proving ground for future React-heavy UI requirements.

### Replace the main dashboard route with React immediately

Swap `/w/{slug}/dashboard` to React rendering directly.

**Rejected because:** Replacing the primary route would mix framework migration
risk with product behavior changes and make rollback harder.

## Consequences

### Positive

- React is now available in this repo as working implementation code.
- The widget surface can use React ecosystem layout tooling directly.
- The pilot route provides a low-risk experimentation path.

### Negative

- Frontend architecture now has two paradigms (vanilla + React island).
- React dependencies are loaded at runtime from ESM URLs.
- Feature parity between classic dashboard and pilot route must be managed.

### Neutral

- Existing dashboard, auth pages, and API contracts remain unchanged.
- ADR 051 remains authoritative for the default/frontend baseline.

### Mitigations

- Keep React scoped to one route and one script entrypoint.
- Keep a clear link back to the classic dashboard route.
- Keep the persisted layout shape minimal and framework-agnostic.

## Implementation

- [src/feedback_triage/pages/dashboard.py](../../src/feedback_triage/pages/dashboard.py) - adds the React pilot route.
- [src/feedback_triage/templates/pages/dashboard/react_widgets.html](../../src/feedback_triage/templates/pages/dashboard/react_widgets.html) - isolated React mount page.
- [src/feedback_triage/static/js/dashboard_react_widgets.js](../../src/feedback_triage/static/js/dashboard_react_widgets.js) - React island and widget-grid behavior.
- [src/feedback_triage/templates/pages/dashboard/index.html](../../src/feedback_triage/templates/pages/dashboard/index.html) - entry link to pilot page.
- [tests/api/auth/test_dashboard_page.py](../../tests/api/auth/test_dashboard_page.py) - route coverage for the React pilot surface.

## References

- [ADR 051 - Static HTML + vanilla JS](051-static-html-vanilla-js.md)
- [Spec v2.0 - deferred React SPA item](../project/spec/spec-v2.md)
- [React Grid Layout](https://github.com/react-grid-layout/react-grid-layout)
