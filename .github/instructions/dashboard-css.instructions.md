---
description: >-
  Use when editing dashboard CSS styling: themes, dark mode, layout,
  responsive design, animations, or accent color palettes.
applyTo: "tools/dev_tools/env_dashboard/static/css/style.css"
---

# Dashboard CSS Conventions

## Variable System

All colors use CSS custom properties in `:root`. Never hardcode colors.

| Variable | Purpose |
|----------|---------|
| `--color-accent` | Primary theme color |
| `--color-accent-dim` | 12% opacity accent for backgrounds |
| `--color-accent-glow` | 35% opacity accent for glows/shadows |
| `--color-accent-bright` | Lighter accent for text on dark backgrounds |
| `--color-border-accent` | 18% opacity accent for borders |
| `--color-pass/warn/fail/info` | Status colors (green/amber/red/blue) |
| `--color-bg`, `--color-bg-card` | Background colors |

## Theme Support

- 7 accent themes set via `[data-accent="<name>"]` selectors
- Light/dark mode via `[data-theme="dark"]` selector
- **Always test both modes** when changing styles

## Section Organization

CSS is organized in labeled sections with `/* ========== Name ========== */` headers.
Add new styles in the appropriate section or create a new labeled section.

## Key Layout Values

- `--sidebar-width: 200px` (collapses to 0 on mobile)
- `--topbar-height: 44px` (fixed positioning)
- `--gap-sm/md/lg`: spacing scale (0.35rem / 0.75rem / 1.25rem)

## Responsive

- Breakpoint: `768px` — sidebar hides, layout goes single-column
- Terminal panel goes full-width bottom sheet on mobile

## Browser Target

- Primary development browser: **Opera GX** (Chromium-based)
- Avoid `::details-content` pseudo-element — not reliably supported in Opera GX
- Don't replace working `@keyframes` animations with custom ones for specific sections — the browser may not replay them on subsequent toggles
- Use `!important` on padding/margin to lock values that base keyframes try to animate
