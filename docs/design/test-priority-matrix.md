# Test Priority Matrix

## Critical

- tests/e2e/test_react_authenticated_pages_phase2.py - Dashboard loads for an authenticated user.
- tests/e2e/test_react_authenticated_pages_phase2.py - Total Signals widget renders with the expected KPI contract.
- tests/e2e/test_react_authenticated_pages_phase2.py - Sparkline tooltip/trend-detail affordance appears on dashboard interaction.
- tests/e2e/test_react_authenticated_pages_phase2.py - Clicking the full Total Signals card opens the feedback list (filtered-signals surface).
- tests/e2e/test_react_authenticated_pages_phase2.py - Feedback inbox route loads.
- tests/e2e/test_react_authenticated_pages_phase2.py - Feedback item detail opens from feedback list navigation.
- tests/e2e/test_react_authenticated_pages_phase2.py - Feedback status can be changed from the detail page and persists.
- tests/e2e/test_react_authenticated_pages_phase2.py - Empty-state copy renders when no feedback rows match.
- tests/e2e/test_react_authenticated_pages_phase2.py - API error state renders when route-context requests fail.

## Important

- tests/e2e/test_react_authenticated_pages_phase2.py - Authenticated route matrix parity (dashboard, inbox, feedback, roadmap, changelog, submitters, insights, settings).
- tests/e2e/test_react_public_pages_phase3.py - Public routes render with React shell and preserve anonymous flows.
- tests/e2e/test_a11y.py - Accessibility smoke checks for key authenticated and public pages.
- tests/api/test_dashboard_summary.py - Dashboard summary API contract and widget payload shape stay stable.
- tests/api/auth/test_workspaces.py - Workspace membership and tenancy guardrails remain correct.

## Recommended

- web/src/components/dashboard/TotalSignalsWidget.test.tsx - Component-level rendering contract for the Total Signals card.
- web/src/App.test.tsx - React shell primitive rendering and route-context wiring smoke.
- web/src/lib/apiClient.test.ts - API error normalization and transport behavior checks.
- tests/e2e/test_signup_flow.py - End-to-end signup path and verification email log behavior.
- tests/e2e/test_react_public_pages_phase3.py - Legacy query-parameter compatibility on public routes.
