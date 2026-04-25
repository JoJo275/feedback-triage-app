---
name: dashboard-dev
description: >-
  Develop, debug, or extend the environment dashboard web app.
  Use when adding sections, fixing styles, modifying API endpoints,
  updating templates, or troubleshooting dashboard performance.
  Covers FastAPI backend, Jinja2 templates, htmx partials, Alpine.js
  state, CSS theming, and collector data integration.
---

# Dashboard Development Skill

## Quick Start

```bash
hatch run dashboard:serve        # Start dev server with hot reload
# Open http://127.0.0.1:8000
```

## Architecture Overview

| Layer | Technology | Location |
|-------|-----------|----------|
| Server | FastAPI + Uvicorn | `tools/dev_tools/env_dashboard/app.py` |
| API | REST + SSE streaming | `api.py` (JSON), `routes.py` (HTML) |
| Templates | Jinja2 + htmx | `templates/` |
| State | Alpine.js | `base.html <script>` block |
| Styling | Pico CSS + custom | `static/css/style.css` |
| Data | Plugin collectors | `scripts/_env_collectors/` |
| Cache | In-memory TTL (30s) | `collector.py` |

## Adding a New Dashboard Section

1. Create collector in `scripts/_env_collectors/<name>.py` extending `BaseCollector`
2. Register in `scripts/_env_collectors/__init__.py` → `_discover_collectors()`
3. Create template partial `tools/dev_tools/env_dashboard/templates/partials/<name>.html`
4. The section auto-appears: `index.html` loops over all sections
5. Sidebar link auto-generated from `sections.items()`
6. Add tests in `tests/unit/test_dashboard_*.py`

## Adding a New API Endpoint

1. Add route to `api.py` (JSON) or `routes.py` (HTML)
2. Security: validate all user inputs (package names, paths)
3. For streaming output: use `StreamingResponse` with SSE format
4. Add tests in `tests/unit/test_dashboard_api.py`

## Modifying Styles

1. Edit `static/css/style.css` — find the labeled section (`/* ========== Name ========== */`)
2. Use CSS variables (`--color-accent`, `--color-bg-card`, etc.)
3. Test both light and dark modes
4. Test all 7 accent themes if changing accent-dependent styles
5. Check responsive behavior at 768px breakpoint

## Performance Checklist

- [ ] Collector has a timeout set
- [ ] New data cached by collector.py TTL
- [ ] htmx partials load lazily (`hx-trigger="load"`)
- [ ] No blocking calls in async route handlers
- [ ] Templates don't duplicate large data in DOM

## Testing

```bash
hatch run test -k dashboard      # All dashboard tests
hatch run test -k test_dashboard_api  # API tests only
```

## Related Files

- [ADR 041](../../../docs/adr/041-env-inspect-web-dashboard.md) — Architecture decision
- [Blueprint 001](../../../docs/blueprints/001-env-inspect-web-dashboard.md) — Design document
- [Dashboard instructions](../../instructions/dashboard.instructions.md) — Coding conventions
