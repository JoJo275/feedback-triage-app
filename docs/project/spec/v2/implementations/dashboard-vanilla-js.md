# Dashboard widget system implementation (vanilla JS path)

> This is the implementation plan for the current SignalNest v2 frontend architecture:
> static HTML + vanilla JS + Tailwind output CSS.

## Goal

Provide and harden a widget system where users can:

- drag widgets
- resize widgets
- snap widgets to a 12-column grid
- save layout as `{ id, x, y, w, h }`
- restore layout on page load
- toggle edit mode
- support responsive breakpoints
- prevent overlap

## Current status

Most of this behavior already exists in
`src/feedback_triage/static/js/dashboard.js`.

That file currently handles:

- local persistence (`localStorage`)
- edit-mode toggling
- drag and resize interactions
- collision checks
- custom density and widget visibility

This plan focuses on stabilization and maintainability rather than a rewrite.

## Architecture

### Server-rendered shell

- Template: `src/feedback_triage/templates/pages/dashboard/index.html`
- Script entry: `src/feedback_triage/static/js/dashboard.js`

### State model

Persisted data shape (canonical):

```json
{
  "version": 1,
  "widgets": [
    { "id": "signals-over-time", "x": 0, "y": 4, "w": 6, "h": 9 }
  ]
}
```

Notes:

- Keep geometry shape minimal and explicit.
- Keep display-only metadata (title, tone, filters) outside the persisted layout.

## Implementation plan

## Phase 1: Geometry contract hardening

- Isolate geometry normalization into one utility section.
- Clamp all widget geometry through one canonical function.
- Add versioned persisted payloads and migration shim for old payloads.

Done when:

1. Every persisted read passes through one parser.
2. Invalid payloads fail closed to defaults.
3. Existing user layouts continue to load.

## Phase 2: Interaction reliability

- Keep drag/resize disabled unless edit mode is on.
- Keep a stable drag threshold to prevent accidental drags on click.
- Add keyboard move/resize controls while in edit mode.

Done when:

1. Pointer interactions no longer trigger accidental layout moves.
2. Keyboard-only users can reorder and resize widgets.
3. Edit mode has clear visual affordances.

## Phase 3: Responsive persistence

- Persist one layout per breakpoint (`lg`, `md`, `sm`, `xs`, `xxs`).
- Normalize breakpoint changes so mobile edits do not corrupt desktop layouts.
- Keep 12 columns for desktop breakpoints.

Done when:

1. Reload preserves layout at every breakpoint.
2. Breakpoint switching does not create overlaps.
3. Layout shape remains `{ id, x, y, w, h }`.

## Phase 4: UX polish and supportability

- Add "reset layout" and "save now" actions.
- Add a JSON debug panel in dev mode only.
- Add lightweight telemetry hooks for layout-save failures.

Done when:

1. Reset action restores defaults deterministically.
2. Save failures are observable.
3. On-call debugging does not require manual localStorage digging.

## Verification checklist

1. Drag works only in edit mode.
2. Resize works only in edit mode.
3. Overlap is rejected.
4. Saved layout restores after refresh.
5. Breakpoint-specific layouts restore independently.
6. Reset returns to defaults.
7. Keyboard controls work in edit mode.

## Test plan

- API/page smoke: `tests/api/auth/test_dashboard_page.py`
- E2E regression surface: `tests/e2e/test_dashboard_smoke.py`
- Add targeted JS behavior checks through Playwright for:
  - drag/resize gating
  - persistence round-trip
  - overlap prevention

## Related docs

- `docs/project/spec/v2/ui.md`
- `docs/project/spec/v2/layouts/dashboard.md`
- `docs/project/spec/v2/css.md`
- `docs/project/spec/v2/implementations/dashboard.md`
