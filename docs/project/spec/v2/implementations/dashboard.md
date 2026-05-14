# Dashboard widget system implementation (React option)

> Goal: build equivalent functionality without copying source code from another product.

> Status in this repository: reference-only implementation path.
> Current SignalNest v2 frontend remains static HTML + vanilla JS
> (no React/Vite/TypeScript) per `ui.md`, `tooling.md`, and `spec-v2.md`.

## Scope and status

- Use this file directly if your app is React-based.
- If you are implementing inside this repository today, treat this as a
	design reference and either:
	- implement a vanilla JS equivalent, or
	- ratify an ADR before introducing a React frontend slice.

## Recommendation

Use a library-first approach with
[react-grid-layout](https://github.com/react-grid-layout/react-grid-layout).

This requirement set matches what the library already solves well:

- drag and resize behavior
- 12-column snapping
- responsive breakpoint layouts
- collision handling / no overlap
- layout serialization

### Why not fully custom?

Custom drag + resize + collision + responsive packing logic is possible,
but it is usually high-risk and time-heavy for little product advantage.

Choose custom only if you need engine behavior that libraries cannot support,
such as non-rectangular widgets or advanced algorithmic packing rules.

### Current-stack equivalent (no React)

For the existing SignalNest v2 stack, choose a vanilla-capable grid engine
(for example GridStack.js) and keep the same persisted layout shape
`{ id, x, y, w, h }`. That gives equivalent behavior without changing the
project-wide frontend architecture.

## Requirement mapping

| Requirement | Implementation choice |
| --- | --- |
| Drag widgets | `isDraggable` in edit mode |
| Resize widgets | `isResizable` in edit mode |
| 12-column snap | `cols={{ lg: 12, md: 12, sm: 6, xs: 4, xxs: 2 }}` |
| Save layout as `{ id, x, y, w, h }` | Persist normalized layout items |
| Restore on load | Load from storage before first render |
| Toggle edit mode | Local UI state + toolbar button |
| Responsive breakpoints | `ResponsiveGridLayout` with per-breakpoint layouts |
| Prevent overlap | `allowOverlap={false}` and `preventCollision={true}` |

## Data model

Store one layout array per breakpoint. Each item keeps the exact shape you
requested, with optional constraints for future-proofing.

```ts
type WidgetLayoutItem = {
	id: string;
	x: number;
	y: number;
	w: number;
	h: number;
	minW?: number;
	maxW?: number;
	minH?: number;
	maxH?: number;
};

type LayoutByBreakpoint = {
	lg: WidgetLayoutItem[];
	md: WidgetLayoutItem[];
	sm: WidgetLayoutItem[];
	xs: WidgetLayoutItem[];
	xxs: WidgetLayoutItem[];
};
```

Normalized payload example:

```json
{
	"version": 1,
	"layouts": {
		"lg": [{ "id": "kpi", "x": 0, "y": 0, "w": 6, "h": 4 }],
		"md": [{ "id": "kpi", "x": 0, "y": 0, "w": 12, "h": 4 }]
	}
}
```

## Component architecture

- `DashboardPage`: fetches widget data and layout state.
- `DashboardToolbar`: edit toggle, reset layout, save status.
- `WidgetGrid`: wraps `ResponsiveGridLayout`.
- `WidgetCard`: visual container per widget.
- `useDashboardLayout`: load/save, defaults, breakpoint sync.

## Implementation steps

### 1) Install dependencies

```bash
npm install react-grid-layout react-resizable lodash.debounce
```

### 2) Build the responsive grid shell

Use a config-first pattern for readability, then wire those options into your
`ResponsiveGridLayout` component.

```ts
import { Responsive, WidthProvider, type Layouts } from "react-grid-layout";

const ResponsiveGridLayout = WidthProvider(Responsive);

export const GRID_BREAKPOINTS = {
	lg: 1280,
	md: 1024,
	sm: 768,
	xs: 480,
	xxs: 0
} as const;

export const GRID_COLS = {
	lg: 12,
	md: 12,
	sm: 6,
	xs: 4,
	xxs: 2
} as const;

export const GRID_PROPS = {
	breakpoints: GRID_BREAKPOINTS,
	cols: GRID_COLS,
	rowHeight: 24,
	margin: [12, 12] as [number, number],
	allowOverlap: false,
	preventCollision: true,
	compactType: "vertical" as const,
	draggableHandle: "[data-drag-handle]"
};

export function applyLayoutChange(
	allLayouts: Layouts,
	setLayouts: (next: Layouts) => void,
	onLayoutsChange: (next: Layouts) => void
): void {
	setLayouts(allLayouts);
	onLayoutsChange(allLayouts);
}
```

In render:

- bind `isDraggable` and `isResizable` to edit mode
- pass `layouts`, `breakpoints`, and `cols`
- call `applyLayoutChange` from `onLayoutChange`

### 3) Save and restore layout

- Restore: read persisted value before first grid render.
- Save: debounce writes on layout change (for example, 300-500 ms).
- Persist normalized shape as `{ id, x, y, w, h }`.

Persistence tiers:

- Local only: `localStorage` key like `dashboard-layout:v1:<userId>`.
- Server-backed: save to `PATCH /api/user-preferences/layout` and hydrate at boot.
- Hybrid: render from server state, apply local optimistic edits, then reconcile.

### 4) Breakpoint strategy

- Keep 12 columns on `lg` and `md`.
- Reduce columns on smaller breakpoints for touch ergonomics.
- Save each breakpoint independently so mobile edits do not break desktop layout.

### 5) Non-overlap and compaction

- Keep `allowOverlap={false}`.
- Use `preventCollision={true}` to reject invalid drops.
- Use `compactType="vertical"` for stable packing and predictable movement.

## Tailwind styling notes

- Give each widget a clear drag handle in edit mode:
	`data-drag-handle` on a header row.
- Provide edit mode affordances (border highlight, move cursor, resize grip).
- Avoid hard-coded heights in content; let the grid control card bounds.

## Accessibility and UX guardrails

- Keep all actions available by button, not drag-only.
- Announce mode switches (for example, "Edit layout enabled").
- Provide Reset to default layout.
- Keep hit areas large on touch devices.
- Respect reduced-motion preferences where animation is added.

## Testing checklist

1. Widgets drag only in edit mode.
2. Widgets resize only in edit mode.
3. Dropping on occupied cells is rejected.
4. Layout persists across refresh.
5. Layout restores correctly for each breakpoint.
6. Reset returns to defaults.
7. Keyboard-accessible controls work without drag.

## Decision summary

- Recommended now: `react-grid-layout`.
- Reason: fastest safe path to complete feature parity with low maintenance risk.
- Revisit custom engine only if product requirements exceed rectangular
	responsive grid capabilities.
