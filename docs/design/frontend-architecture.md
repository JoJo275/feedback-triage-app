# Frontend Architecture

!!! danger "Frontend Boundary"
    The frontend owns user interface, routing, component composition, visual state, and browser interactions.
    It must not become the source of truth for product data, permissions, background work, or backend business rules.

## Purpose

This document defines the frontend architecture for the product app. It explains:

- How the frontend is structured.
- Which frontend tools own which responsibilities.
- How React state is divided between local, shared, editor, and server state.
- How the frontend talks to FastAPI.
- How Vite and Next.js decisions are handled.
- How UI components, styling, tests, and accessibility should be implemented.

## Related Documents

- [`../tooling.md`](../tooling.md) — complete tool inventory.
- [`tool-decisions.md`](tool-decisions.md) — rationale for tool choices.
- [`background-processing-architecture.md`](background-processing-architecture.md) — backend workflow/task boundaries.
- [`production-readiness.md`](production-readiness.md) — production hardening and release gates.
- [`../development/development-framework.md`](../development/development-framework.md) — day-to-day development workflow.

## Architecture Summary

The target frontend architecture is:

```text
React + TypeScript UI
→ API client generated from FastAPI OpenAPI schema
→ TanStack Query for server-state fetching/caching/mutations
→ Redux Toolkit for complex dashboard editor state
→ local React state for small UI interactions
→ CSS variables/design tokens plus optional Tailwind/shadcn/Radix for styling and primitives
```

The current frontend runtime is **Vite + React**. **Next.js** is a planned app-shell migration option, not an active runtime replacement until an ADR approves the migration.

## Frontend Responsibilities

The frontend owns:

- Page routing and layout shell.
- Dashboard widget composition.
- Interactive UI behavior.
- Forms and client-side validation.
- Loading, empty, and error states.
- Accessibility behavior and labels.
- Responsive behavior.
- Client-side draft state.
- API request orchestration.
- User-facing visual polish.

The frontend does **not** own:

- Permanent data truth.
- Authorization decisions.
- Tenant/workspace permission enforcement.
- Background jobs or durable workflows.
- Database access.
- Email delivery.
- Rate-limit enforcement.
- Analytics source-of-truth calculations.

## Runtime Decision: Vite vs Next.js

### Current Runtime: Vite + React

Vite + React is active and should remain the working baseline until a migration is deliberately executed.

Use Vite when:

- The product is mostly an authenticated dashboard app.
- FastAPI remains the backend and serves API routes.
- The frontend can be delivered as static assets or a separately hosted SPA.
- Simplicity and debuggability are more important than framework conventions.

### Planned Runtime: Next.js

Next.js is a planned option for a stronger app-shell structure.

Use Next.js when:

- The project needs route/layout/loading/error conventions.
- Public marketing pages and authenticated app pages should share a frontend framework.
- The portfolio value of a modern React framework is important.
- Route-level organization becomes difficult in Vite.
- Server-rendered or SEO-sensitive public pages become important.

### Next.js Boundary

If Next.js is adopted:

- Next.js owns frontend routing, layouts, and React app shell.
- FastAPI remains the backend source of truth.
- Next.js should not duplicate Python business logic.
- Next.js should not directly replace background processing.
- Generated OpenAPI types should remain the API contract between frontend and FastAPI.

### Migration Gate

Before migrating to Next.js, write an ADR covering:

1. Which routes migrate first.
2. Whether Vite is retired or remains for any surface.
3. How auth/session state crosses Next.js and FastAPI.
4. How generated API types are consumed.
5. How deployment changes.
6. Which Playwright tests prove the migration works.

## Suggested Route Map

If using Next.js, use a route structure like:

```text
app/
  page.tsx                         # public marketing homepage
  login/page.tsx                   # auth
  signup/page.tsx
  reset-password/page.tsx
  w/[workspaceSlug]/
    layout.tsx                     # authenticated workspace shell
    dashboard/page.tsx
    inbox/page.tsx
    feedback/page.tsx
    feedback/[feedbackId]/page.tsx
    tags/page.tsx
    settings/page.tsx
```

If using Vite + React Router, mirror the same route model in router configuration.

## Component Architecture

Use layered components.

| Layer | Purpose | Examples | Rules |
| --- | --- | --- | --- |
| App routes/pages | Page-level composition | `DashboardPage`, `InboxPage` | Fetch route-level params and compose feature components. |
| Feature modules | Product-specific UI areas | `dashboard/`, `inbox/`, `feedback/` | Own feature logic and feature-specific components. |
| App components | Reusable product UI | `SignalCard`, `DashboardGrid`, `Sparkline` | May use project-specific styling and semantics. |
| UI primitives | Generic reusable UI | `Button`, `Dialog`, `Dropdown`, `Tooltip` | Prefer shadcn/Radix where useful. |
| Generated API types | API contract | `openapi.generated.ts` | Do not hand-edit generated files. |

Suggested structure for Vite:

```text
web/src/
  api/
    client.ts
    queries/
    mutations/
  components/
    ui/
    dashboard/
    feedback/
  features/
    dashboard/
    inbox/
    feedback/
  state/
    dashboardEditorSlice.ts
    stores/
  styles/
    tokens.css
    globals.css
  types/
    openapi.generated.ts
```

Suggested structure for Next.js:

```text
apps/web/
  app/
  src/
    api/
    components/
      ui/
      dashboard/
      feedback/
    features/
    state/
    styles/
    types/
```

## API Contract Architecture

FastAPI remains the source of API truth.

Workflow:

```text
Pydantic models / FastAPI routes
→ OpenAPI schema
→ openapi-typescript output
→ frontend typed API layer
→ TanStack Query hooks
→ React components
```

Rules:

- Do not hand-maintain duplicate frontend types for API responses.
- Do not scatter raw `fetch()` calls across components.
- Keep API wrappers in `api/` or `features/*/api.ts`.
- Use TanStack Query for request lifecycle, caching, errors, refetching, and mutations.
- Use MSW for deterministic frontend test states once query hooks exist.

Example query ownership:

| Data | Owner |
| --- | --- |
| Total Signals summary | TanStack Query |
| Feedback list | TanStack Query |
| Workspace metadata | TanStack Query |
| Saved dashboard layout | TanStack Query |
| Draft dashboard layout while editing | Redux Toolkit |
| Sparkline active hover point | local React state |

## State Architecture

### State Ownership Table

| State Type | Tool | Examples |
| --- | --- | --- |
| Tiny local UI state | `useState` | Tooltip open, active chart point, dropdown open. |
| Structured local state | `useReducer` | Feature-local wizard, complex form state, local widget settings panel. |
| Server/API state | TanStack Query | Signals, users, tags, summaries, saved layouts. |
| Complex editor state | Redux Toolkit | Dashboard draft layout, undo/redo, selected widget, breakpoints, unsaved changes. |
| Small shared UI state | Zustand, if needed | Sidebar collapsed, command palette open, dashboard density. |
| Runtime boundary validation | Zod | Forms, URL params, env values, localStorage payloads. |

### useState

Use `useState` for state that is:

- Local to one component.
- Easy to understand.
- Updated directly.
- Not shared across unrelated components.

Examples:

```text
sparkline tooltip open
active tooltip point
local dropdown open
input field value
```

### useReducer

Use `useReducer` when local state has:

- Multiple actions.
- Deterministic transitions.
- State updates that are easier to read as events.

Examples:

```text
local form wizard
widget settings modal
temporary filter builder
```

### TanStack Query

Use TanStack Query for server state:

- Loading/error/success state.
- Refetching.
- Cache invalidation.
- Mutations.
- API data synchronization.

Examples:

```text
useSignalSummary(workspaceId, range)
useFeedbackList(filters)
useWorkspace(workspaceSlug)
useSaveDashboardLayout()
```

### Redux Toolkit

Use Redux Toolkit for dashboard editor state because the editor has:

- Undo/redo.
- Draft vs saved layouts.
- Drag/resize actions.
- Selection.
- Breakpoint-specific layouts.
- Unsaved changes.
- Save/cancel/reset flows.

Redux state should own the draft editing model, not the saved server data.

Example slice state:

```ts
type DashboardEditorState = {
  mode: "view" | "edit";
  selectedWidgetId: string | null;
  activeBreakpoint: "desktop" | "tablet" | "mobile";
  savedLayout: WidgetLayout[];
  draftLayout: WidgetLayout[];
  past: WidgetLayout[][];
  future: WidgetLayout[][];
  hasUnsavedChanges: boolean;
};
```

### Zustand

Use Zustand only if a small shared UI state need exists outside Redux.

Good Zustand examples:

```text
sidebar collapsed
command palette open
dashboard density preference
active app shell panel
```

Avoid Zustand for:

```text
server state
saved API data
undo/redo dashboard editor state already owned by Redux
```

## Dashboard Widget Architecture

Widgets should be product-specific components, not generic copied cards.

A dashboard widget should define:

- Metric identity.
- Data contract.
- Loading state.
- Empty state.
- Error state.
- Click target destination.
- Tooltip behavior.
- Accessibility label.
- Responsive behavior.
- Edit-mode behavior.

Example widget contract:

```ts
type DashboardWidgetDefinition = {
  id: string;
  type: "total-signals" | "open-signals" | "resolution-rate";
  title: string;
  minW: number;
  minH: number;
  defaultW: number;
  defaultH: number;
};
```

### Total Signals Widget Rules

The Total Signals card should represent valid received signals during the selected period.

Rules:

- Resolved signals do not reduce Total Signals.
- Deleted spam/test data may be excluded if the backend defines it as invalid.
- The card click should navigate to the filtered signals/inbox list.
- Sparkline hover should inspect chart data only.
- The whole card can be clickable, but nested controls must stop propagation.
- Cursor should use pointer wherever click navigates.

## Styling and Design System

### Foundation

Use CSS variables/design tokens as the stable foundation.

Tokens should cover:

- Brand colors.
- Semantic colors.
- Text colors.
- Backgrounds.
- Borders.
- Radius.
- Spacing.
- Shadows.
- Density modes.

Example:

```css
:root {
  --color-signal-blue: #2563eb;
  --card-radius: 1.5rem;
  --card-border: #e2e8f0;
  --density-card-padding: 1rem;
}
```

### Tailwind

Tailwind is planned, not automatically adopted everywhere.

If adopted:

- Use Tailwind for layout, spacing, typography, and utility composition.
- Keep semantic values mapped to tokens where possible.
- Avoid random one-off colors that bypass the design system.
- Do not let utility classes replace design documentation.

### shadcn/ui and Radix

Use shadcn/ui and Radix for accessible primitives:

- Dialogs.
- Dropdowns.
- Menus.
- Popovers.
- Tooltips.
- Tabs.
- Sheets.
- Command menu.

Customize them heavily so the product does not look like a default template.

Do not use shadcn/Radix for:

- App-specific signal widgets.
- Dashboard visualizations.
- Business-specific layout editors.

## Accessibility Requirements

Every frontend feature should define accessibility behavior.

Baseline rules:

- Interactive cards need accessible labels.
- Buttons must be real buttons.
- Links must be real links.
- Do not nest interactive controls inside links without deliberate event handling.
- Tooltips must not be the only place critical information exists.
- Forms need labels and errors associated with inputs.
- Keyboard navigation must work for dashboard settings, menus, dialogs, and forms.
- Radix primitives should be preferred for complex overlays.

Recommended planned addition:

```text
@axe-core/playwright
```

Use it for automated accessibility smoke checks in Playwright.

## Testing Strategy

| Test Layer | Tool | What to Test |
| --- | --- | --- |
| Typecheck | TypeScript | Props, API shapes, state objects. |
| Lint | ESLint | React hooks, unused vars, unsafe patterns. |
| Unit | Vitest | Utility functions, reducers, data transforms. |
| Component | React Testing Library | Widget rendering, forms, empty/error states. |
| API mocks | MSW | Deterministic frontend success/error/loading states. |
| Browser | Playwright | Login, dashboard load, card navigation, inbox filters. |
| Accessibility | axe + Playwright, planned | Critical app pages and dialogs. |

Critical frontend flows:

- Dashboard loads.
- Total Signals widget renders.
- Sparkline tooltip appears.
- Whole card click opens filtered inbox/signals page.
- Dashboard editor can move widget.
- Undo/redo works.
- Save/cancel/reset layout works.
- Empty state renders.
- API error state renders.

## Migration Plan

### Phase 1: Stabilize Current Frontend

- Keep Vite + React running.
- Ensure TypeScript typecheck passes.
- Ensure ESLint passes.
- Ensure OpenAPI type generation works.
- Add TanStack Query for API data flows.
- Add Redux Toolkit for editor state only.

### Phase 2: Add Production-Grade State Boundaries

- Move server data to TanStack Query.
- Move dashboard editor draft state to Redux Toolkit.
- Keep tooltips/dropdowns local.
- Add Zod for forms, URL params, env values, and localStorage.
- Add MSW for frontend test states.

### Phase 3: Decide Next.js

Write ADR for:

- Whether to migrate.
- Which route moves first.
- How auth works.
- How FastAPI is called.
- How Vite is retired or retained.
- What tests prove success.

### Phase 4: Migrate by Vertical Slice

First slice:

```text
Dashboard route
→ Total Signals widget
→ FastAPI summary endpoint
→ click card
→ filtered inbox/signals page
→ Playwright smoke test
```

Do not migrate the whole frontend in one untested pass.

## Guardrails

- Do not use Redux for server state.
- Do not use TanStack Query for hover/drag state.
- Do not use Zustand for state already owned by Redux.
- Do not hand-edit generated OpenAPI files.
- Do not put permission rules in the frontend only.
- Do not use frontend validation as a substitute for backend validation.
- Do not keep Vite and Next.js indefinitely without a documented reason.
- Do not allow dashboard widgets to bypass shared metric/data contracts.

## Open Questions

- Will Next.js replace Vite for the main product app?
- Will Tailwind become the default styling approach?
- Will shadcn/ui be adopted before or after the Next.js decision?
- Which route owns the filtered signal list: `/inbox`, `/feedback`, or `/signals`?
- How are dashboard layouts stored: per user, per workspace, or both?
- Which frontend state should survive reload through URL/localStorage/backend persistence?
