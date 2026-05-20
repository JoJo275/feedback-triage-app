---
description: >-
  Use when editing React/TypeScript frontend code in web/src/. Covers
  route bootstrap contracts, hook usage (useMemo/useCallback), data loading,
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

## Hook Guidance (`useMemo` / `useCallback`)

- Use `useMemo` for expensive, deterministic derived values used in render:
  filtered/sorted collections, chart coordinate transforms, table column
  definitions.
- Avoid `useMemo` around trivial expressions; measure readability and actual
  re-render impact first.
- Use `useCallback` only when function identity stability matters:
  - callback props consumed by memoized children,
  - function references used in effect dependencies,
  - subscribe/unsubscribe APIs that require the same function reference.
- Do not wrap every event handler in `useCallback`; plain inline functions are
  preferred when identity stability is not required.
- Keep dependency arrays complete and explicit.

## Data Loading and API Access

- Prefer shared hooks for route-context loading (for example,
  `useRouteContextLoader`) with `AbortController` cancellation on cleanup.
- Use `web/src/lib/apiClient.ts` for HTTP requests so headers, error
  normalization, and telemetry remain consistent.
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
