---
description: >-
  Use when working on the environment dashboard web app: FastAPI routes,
  Jinja2 templates, htmx partials, Alpine.js state, CSS styling, or
  collector data integration. Covers architecture, conventions, and
  common patterns for the dashboard at tools/dev_tools/env_dashboard/.
applyTo: "tools/dev_tools/env_dashboard/**"
---

# Environment Dashboard — Copilot Instructions

## Architecture

- **Server**: FastAPI + Uvicorn on `127.0.0.1:8000` (local-only)
- **Templates**: Jinja2 with `autoescape=True` (XSS prevention, non-negotiable)
- **Frontend**: htmx (partial swaps) + Alpine.js (reactive state) + Pico CSS + custom CSS
- **Data source**: `scripts/_env_collectors/` — shared plugin collectors
- **Caching**: 30-second in-memory TTL in `collector.py`

## File Layout

| File | Purpose |
|------|---------|
| `app.py` | FastAPI app factory, Uvicorn entry point |
| `routes.py` | HTML routes: index page, htmx section partials, HTML export |
| `api.py` | JSON API: summary, report, warnings, scan, export, pip ops, shutdown |
| `collector.py` | Caching wrapper around `gather_env_info()` |
| `redact.py` | Redaction level parsing (NONE/SECRETS/PII/PARANOID) |
| `export.py` | Self-contained HTML export renderer |
| `templates/base.html` | Master layout: topbar, sidebar, main content, terminal panel |
| `templates/index.html` | Home: summary bar, warnings, section cards, raw JSON |
| `templates/partials/*.html` | Individual section renderers (htmx partials) |
| `static/css/style.css` | All custom styles (~1600+ lines) |
| `static/js/` | Vendored htmx + Alpine.js (no npm, no CDN, no build step) |

## Conventions

### Templates
- Use `{% from "partials/_macros.html" import kv_row, status_badge %}` macros
- Section partials receive `data` (section dict) and `section_name`
- All user-facing text goes through Jinja2 autoescape — never use `|safe` on user data
- htmx attributes go on HTML elements, Alpine.js state on `x-data`/`x-model`

### CSS
- CSS variables defined in `:root` — always use variables, not hardcoded colors
- Accent-aware: all accent colors use `--color-accent-*` variables
- Dark mode via `[data-theme="dark"]` selector
- Class naming: BEM-ish — `.section-card`, `.section-card-body`, `.warning-item`
- Keep mobile responsive: sidebar collapses at `768px`

### Browser Target
- Primary development browser: **Opera GX** (Chromium-based)
- Avoid `::details-content` pseudo-element — Opera GX may not support it
- Prefer proven CSS animation patterns (keyframes) over cutting-edge CSS transitions for `<details>`
- Always test animations replay correctly on repeated open/close cycles

### JavaScript
- Alpine.js `dashboard()` function in base.html holds all app state
- No external JS dependencies — everything vendored
- SSE streaming for pip operations via `fetch()` + `ReadableStream`
- Use `x-cloak` to prevent flash of unstyled Alpine content

### Python (Backend)
- All routes are `async` (FastAPI convention)
- Security: validate package names with regex, validate python exe paths
- Collectors run with per-collector timeouts — don't bypass this
- Cache invalidation: `invalidate_cache()` before force-refresh

## Security Rules (Non-Negotiable)

1. Jinja2 autoescape stays ON — never disable
2. Server binds to 127.0.0.1 ONLY — never 0.0.0.0
3. Package name validation via `_PACKAGE_NAME_RE` before any pip operation
4. Python exe validation: must exist, name starts with "python", no `..`
5. No `shell=True` in subprocess calls — use arg lists
6. CSP headers on export HTML

## Data Flow

1. Browser → `routes.py` handler (or htmx partial request)
2. Handler calls `collector.get_report(tier=..., redact_level=...)`
3. Collector calls `gather_env_info()` (or returns cached result)
4. Redaction applied server-side
5. Jinja2 renders template with data context

## Testing

Tests in `tests/unit/test_dashboard_*.py`. Run: `hatch run test -k dashboard`

## Common Pitfalls

- Editing CSS without checking both light and dark modes
- Forgetting `scroll-margin-top` on new scrollable sections
- Not handling empty data in templates (use `|default()` filter)
- Adding new sections without updating sidebar nav in base.html
