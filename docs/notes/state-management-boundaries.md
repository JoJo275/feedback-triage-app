# State Management Boundaries

A practical guide for choosing where state should live.

## Why This Exists

Many bugs and unnecessary complexity come from storing state in the
wrong place. This note clarifies the boundary between:

- server/API data
- local UI state
- shared UI state
- complex global state

## Quick Definitions

| State type | What it is | Typical examples | Primary owner |
| --- | --- | --- | --- |
| Server/API data | Canonical data from backend/domain systems | user profile, workspaces, feedback items, permissions, email_log status | Backend + API contract |
| Local UI state | View-only state needed by one component or page | modal open/close, input text, selected tab, transient loading spinner | Component/page |
| Shared UI state | UI state used by multiple sibling/nearby components | table sort/filter controls, current pagination in a feature area, panel collapse state | Feature-level UI container |
| Complex global state | Cross-route, cross-feature state with non-trivial transitions | authenticated session context, active workspace context, background-job dashboard coordination | App-level state layer |

## Rule of Thumb

1. If the state must survive reloads, reconcile across clients, or be
   trusted for business logic, it is server/API data.
2. If only one component needs it and it is purely presentational,
   keep it local.
3. If multiple components in the same feature need it, share it at the
   feature boundary.
4. If it spans many routes/features and has complex transitions,
   promote it to complex global state.

## What Not To Do

- Do not copy server data into many UI stores "just in case."
- Do not move simple local toggles into a global store.
- Do not make API data ownership ambiguous between server and UI.
- Do not treat cache as source of truth.

## Practical Examples

| Scenario | Correct home | Why |
| --- | --- | --- |
| Password reset token validation result | Server/API data | Security and correctness require backend ownership. |
| Whether an invite modal is open | Local UI state | Single component concern; no cross-feature value. |
| Filter chips + table sorting in one workspace page | Shared UI state | Multiple components in one page need consistent controls. |
| Current authenticated user + active workspace across routes | Complex global state | Cross-route coordination and lifecycle complexity. |

## Escalation Path

When uncertain, start small and move up only when needed:

- local UI state -> shared UI state -> complex global state

Do not move in the opposite direction unless simplifying after proven
over-engineering.
