---
description: >-
  Use when editing dashboard Jinja2 HTML templates: base layout, index page,
  section partials, macros, or htmx partial endpoints.
applyTo: "tools/dev_tools/env_dashboard/templates/**"
---

# Dashboard Template Conventions

## Template Hierarchy

- `base.html` — Master layout (topbar, sidebar, terminal panel, scripts)
- `index.html` — Extends base, provides main content blocks
- `partials/*.html` — htmx-swappable section renderers
- `partials/_macros.html` — Shared Jinja2 macros (`kv_row`, `status_badge`)

## htmx Patterns

- Section bodies use `hx-get="/section/{name}"` with `hx-trigger="load"`
- Scan refresh triggers `scan-complete` event on body
- Use `hx-indicator` to show spinners during loading

## Alpine.js State

The `dashboard()` function in `base.html <script>` manages:
- `searchQuery`, `redactLevel`, `hideEmpty`, `scanning` — UI filters
- `terminalOpen`, `terminalTitle`, `terminalStatus` — terminal panel
- `mode`, `activeTheme` — appearance
- Methods: `refreshScan()`, `pipAction()`, `shutdownServer()`, etc.

## Macros

Import from `_macros.html`:
```jinja2
{% from "partials/_macros.html" import kv_row, status_badge %}
{{ kv_row("Label", value, copyable=true) }}
```

## Data Context

- `base.html` receives: `redact_level`, `warnings`, `sections`, `meta`
- `index.html` receives: `report`, `summary`, `warnings`, `sections`, `meta`
- Partials receive: `data` (section dict), `section_name`, `redact_level`

## Security

- NEVER use `|safe` on user/collector data
- All template variables auto-escaped by Jinja2
