# Dashboard Feature Structure

Dashboard feature files are colocated under this folder.

Convention:
- Keep dashboard feature UI components in this directory.
- Keep dashboard feature tests beside components as `*.test.tsx`.
- Prefer importing DTOs from generated OpenAPI-based contracts in `web/src/types/contracts.ts`.

## Recommended Updates

- Keep dashboard page composition in `DashboardOverview.tsx` and split reusable widgets into focused components in this folder.
- Keep KPI and queue behavior aligned with the v2 layout contracts documented in `docs/project/spec/v2/layouts/dashboard.md`.
- Keep the Total signals widget contract stable (`label`, marker wording, click target, sparkline accessibility) per `docs/project/spec/v2/implementations/total-signals-widget.md`.
- Treat this folder as feature-owned UI only: shared primitives should live in `web/src/components/primitives/`.
- If a new dashboard block has independent state or interaction rules, promote it to its own component file rather than growing `DashboardOverview.tsx`.

## Testing Expectations

- Add or update colocated unit tests whenever dashboard rendering or interaction logic changes.
- Keep `web/src/App.test.tsx` assertions aligned with dashboard headings and key navigation affordances.
- Keep e2e parity checks green, especially `tests/e2e/test_react_authenticated_pages_phase2.py` for dashboard route behavior.
