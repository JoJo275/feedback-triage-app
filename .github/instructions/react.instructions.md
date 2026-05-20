---
description: >-
  Use when editing React/TypeScript frontend code in web/src/. Covers
  route bootstrap contracts, hook usage, API layering/data loading,
  testing, and security conventions for the v2 runtime.
applyTo: "web/src/**"
---

# React Frontend — Copilot Instructions

## Runtime Boundary

- v2 migrated page routes use React + Vite from `web/`, mounted by FastAPI
  shell templates.
- Keep FastAPI as authority for URL routing, auth/session checks, and tenant
  scope decisions.
- Do not introduce client-side routing libraries as baseline behavior unless
  there is an ADR/spec update.

## Route Bootstrap Contract

- `web/src/main.tsx` is the single entrypoint for route dispatch.
- Route identity comes from mount-node data attributes:
  `data-page-key`, `data-active-section`, and route context fields.
- Public routes may pass JSON payload through
  `#sn-react-route-payload[type="application/json"]`.
- If adding a route, update both backend shell data emission and frontend
  page-key parsing in the same change.

## Hook Guidance (Use Hooks Intentionally)

- Prefer the smallest hook set that keeps code correct and readable. Do not add
  hooks "just in case."
- Use `useState` for local UI state; keep state minimal and derive values in
  render when possible instead of duplicating state.
- Use `useEffect` only for side effects and external synchronization
  (networking, subscriptions, timers, document APIs). Do not use effects to
  compute pure derived values.
- Always clean up long-lived effects (subscriptions, timers, listeners) and
  cancel in-flight async work (`AbortController`) when dependencies change.
- Use `useRef` for mutable instance values and DOM handles that should not
  trigger re-renders.
- Use `useId` for stable, accessible input/label wiring.
- Use `useReducer` when state transitions are complex or tightly coupled across
  multiple fields.
- Use `useMemo` for expensive, deterministic derived values used in render
  paths (for example chart transforms, heavy filters, and column definitions).
- Avoid `useMemo` around trivial expressions; measure readability and
  re-render impact first.
- Use `useCallback` only when function identity stability is required
  (memoized children, effect dependencies, or subscribe/unsubscribe contracts).
- Do not wrap every event handler in `useCallback`; plain inline handlers are
  preferred when identity stability is irrelevant.
- Extract custom hooks when logic is reused across components or when it
  meaningfully isolates side-effect orchestration.
- Keep dependency arrays complete and explicit.

## Data Loading and API Layer

- Prefer shared hooks for route-context loading (for example,
  `useRouteContextLoader`) with `AbortController` cancellation on cleanup.
- Keep raw `fetch()` calls out of page/components. Call an API layer instead.
- Use `web/src/lib/apiClient.ts` as the default transport boundary so headers,
  error normalization, telemetry, and auth/session semantics stay consistent.
- Put endpoint-specific request functions in API modules and return typed DTOs
  (not raw `Response`) to UI code.
- Feature hooks/components should orchestrate state and UX; API modules should
  own request construction and response normalization.
- Keep `credentials: "same-origin"` semantics and include `x-client-release`
  and workspace scope headers where required.

## Testing Baseline

- Unit/component tests use Vitest + React Testing Library + jsdom.
- Keep tests behavior-focused (what the user sees/can do), not
  implementation-detail-focused.
- Shared test setup lives in `web/src/test/setup.ts`.
- If UI behavior changes, update nearest `*.test.tsx` and relevant Playwright
  parity checks.

## Security and Rendering Safety

- Do not render user-controlled strings with `dangerouslySetInnerHTML`.
- Keep user content in JSX text nodes (React escapes by default).
- For URL/attribute composition, use explicit attribute assignment rather than
  string-templated HTML snippets.
