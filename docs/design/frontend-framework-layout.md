# Frontend Framework Layout (v2 React Runtime)

This document records the current frontend framework baseline for migrated
v2 routes. It complements:

- [ADR 077](../adr/077-use-react-vite-as-v2-page-runtime.md)
- [ADR 078](../adr/078-make-web-build-and-widget-parity-required-gates.md)
- [ADR 079](../adr/079-use-umbrella-react-baseline-for-v2-frontend.md)
- [`docs/project/spec/v2/ui.md`](../project/spec/v2/ui.md)
- [`docs/project/spec/v2/tooling.md`](../project/spec/v2/tooling.md)

## Dependency Baseline (May 2026)

Source of truth: [`web/package.json`](../../web/package.json).

| Category | Dependency | Version in repo | Role |
| --- | --- | --- | --- |
| Runtime | `react` | `^18.3.1` | Component runtime |
| Runtime | `react-dom` | `^18.3.1` | DOM renderer |
| Build | `vite` | `^8.0.13` | Dev server + production build |
| Build | `@vitejs/plugin-react` | `^6.0.2` | React transform for Vite |
| Language | `typescript` | `^5.6.3` | Static typing |
| Contracts | `openapi-typescript` | `^7.10.1` | Generates API contract types |
| Lint | `eslint` | `^9.14.0` | JavaScript/TypeScript linting |
| Lint | `typescript-eslint` | `^8.13.0` | TypeScript lint integration |
| Lint | `eslint-plugin-react-hooks` | `^5.0.0` | Hook safety rules |
| Lint | `eslint-plugin-react-refresh` | `^0.4.14` | Fast-refresh lint rules |
| Unit test | `vitest` | `^4.1.6` | Test runner |
| Unit test | `@testing-library/react` | `^16.0.1` | React component testing |
| Unit test | `@testing-library/dom` | `^10.4.1` | DOM-testing utilities |
| Unit test | `@testing-library/jest-dom` | `^6.6.3` | Matchers (`toBeInTheDocument`, etc.) |
| Unit test env | `jsdom` | `^25.0.1` | Browser-like DOM environment |

## Routing Conventions

FastAPI owns canonical URLs and auth/tenant enforcement. React is mounted
inside server-rendered shell templates.

- Authenticated pages live under `/w/<slug>/...` and are rendered by
  `maybe_render_workspace_react_shell(...)` in
  [`src/feedback_triage/pages/react_shell.py`](../../src/feedback_triage/pages/react_shell.py).
- Public pages (`/`, `/w/<slug>/submit`, `/roadmap/public`,
  `/changelog/public`) use `maybe_render_public_react_shell(...)`.
- The shell injects route metadata through mount-node data attributes:
  `data-page-key`, `data-active-section`, `data-workspace-slug`,
  `data-workspace-name`, `data-client-release`.
- Public routes can also inject JSON payload bootstrap data via
  `#sn-react-route-payload` (`type="application/json"`).
- The single frontend entrypoint
  ([`web/src/main.tsx`](../../web/src/main.tsx)) dispatches rendering based on
  `pageKey`:
  - Authenticated keys: `dashboard`, `inbox`, `feedback`, `roadmap`,
    `changelog`, `submitters`, `insights`, `settings`
  - Public keys: `landing`, `public_submit`, `public_roadmap`,
    `public_changelog`

Recommended rule for new pages:

1. Add or update a FastAPI page route first.
2. Emit a stable `data-page-key` from the shell.
3. Add the key to `main.tsx` parsing logic.
4. Add parity checks in API/e2e tests before rollout.

## File Structure Conventions

Frontend source of truth is [`web/`](../../web/).

- Entrypoint: [`web/src/main.tsx`](../../web/src/main.tsx)
- Top-level surfaces:
  - Authenticated app: [`web/src/App.tsx`](../../web/src/App.tsx)
  - Public app: [`web/src/PublicApp.tsx`](../../web/src/PublicApp.tsx)
- Shared concerns:
  - Hooks: [`web/src/hooks/`](../../web/src/hooks)
  - API/telemetry/error utilities: [`web/src/lib/`](../../web/src/lib)
  - UI components: [`web/src/components/`](../../web/src/components)
  - Typed contracts: [`web/src/types/`](../../web/src/types)
  - Test setup: [`web/src/test/setup.ts`](../../web/src/test/setup.ts)
- Generated build output (not hand-edited):
  [`src/feedback_triage/static/app/`](../../src/feedback_triage/static/app)

Colocation convention:

- Keep tests near implementation (`*.test.ts` / `*.test.tsx`) where practical.
- Keep generated OpenAPI client types in
  [`web/src/types/openapi.generated.ts`](../../web/src/types/openapi.generated.ts)
  and regenerate via `npm run contracts:generate`.

## Build Tooling

Build and test pipeline is Vite-centric.

- Dev server: `npm --prefix web run dev`
- Production build: `npm --prefix web run build`
- Lint: `npm --prefix web run lint`
- Typecheck: `npm --prefix web run typecheck`
- Unit tests: `npm --prefix web run test`
- Contracts generation/check:
  - `npm --prefix web run contracts:generate`
  - `npm --prefix web run contracts:check`

Build output contract:

- Vite writes hashed assets plus `manifest.json` to
  `src/feedback_triage/static/app/`.
- FastAPI resolves entry assets via
  [`src/feedback_triage/frontend_assets.py`](../../src/feedback_triage/frontend_assets.py).
- Missing or malformed manifest entries fail closed for React shell responses.

## Rendering Model

Rendering is server-routed + client-rendered (CSR), not SPA routing.

- FastAPI resolves URL, auth/session, tenant scope, and initial route metadata.
- Jinja shell template renders the mount node and script tags.
- React mounts on `#sn-react-app-root` and renders either `App` or `PublicApp`.
- There is no React Router dependency in the current baseline.
- Navigation between major pages is URL-driven and handled by FastAPI routes.

This keeps deep links and access control server-authoritative while allowing a
typed component runtime inside each page shell.

## Data Loading Patterns

Primary patterns in current code:

- Route-context bootstrapping via
  [`useRouteContextLoader`](../../web/src/hooks/useRouteContextLoader.ts)
  with `AbortController` cleanup and `Promise.all` fan-out.
- API access centralized in
  [`web/src/lib/apiClient.ts`](../../web/src/lib/apiClient.ts):
  - `fetch` with `credentials: "same-origin"`
  - `x-client-release` on all requests
  - `X-Workspace-Slug` on scoped routes
  - normalized error envelopes (`ApiClientError`)
- Frontend telemetry hooks for API/mutation failures and runtime events.

Hook guidance (current baseline):

- Use `useMemo` for expensive derived values that are reused in render paths
  (for example chart coordinate transforms, filtered table rows, column defs).
- Do not add `useMemo` around trivial expressions.
- Use `useCallback` only when function identity stability is required:
  - callback props passed into memoized children,
  - function references used in effect dependencies,
  - event subscription/unsubscription boundaries.
- Prefer plain inline handlers when identity stability is not required.

## Deployment Assumptions

- Node 22 + npm 10 toolchain is available in CI/build environments.
- `npm --prefix web run build` runs before app startup/deploy image finalization.
- Backend serves frontend assets from same-origin `/static/app/*`.
- Manifest lookup is startup/runtime critical for React routes.
- CSP for React shell responses is controlled by backend settings
  (`react_csp_enabled`, `react_csp_policy`).
- Release gates require web lint/typecheck/tests/build and route parity checks
  (ADR 078).

## Plugin Ecosystem

Current plugin posture is intentionally small:

- Vite plugin: `@vitejs/plugin-react`
- ESLint plugins:
  - `eslint-plugin-react-hooks`
  - `eslint-plugin-react-refresh`
- Testing stack:
  - `vitest` + `jsdom`
  - React Testing Library (`@testing-library/react`,
    `@testing-library/dom`, `@testing-library/jest-dom`)

Not currently part of baseline:

- `react-router`
- state-manager libraries (`redux`, `zustand`, etc.)
- data-cache libraries (`@tanstack/react-query`, SWR)

If any of the above are introduced as defaults, update this document and the
related ADR/spec references in the same change.
