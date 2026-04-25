# Environment Dashboard Guide

A guide to the environment inspection web dashboard — what it does, how it
works, and how to extend it.

The dashboard is a local-only web application that collects and displays
detailed information about your development environment: Python versions,
git state, installed packages, disk usage, network connectivity, security
checks, and more.

---

## Quick Start

```bash
hatch run dashboard:serve        # Start at http://127.0.0.1:8000
# or, if installed globally:
spb-dashboard                    # Works from any repo
```

Open <http://127.0.0.1:8000> in your browser. Press **Ctrl+C** in the
terminal to stop.

---

## What the Dashboard Shows

The dashboard collects data from **20 sections** organized into categories:

### System & Hardware

| Section | What it shows |
|---------|--------------|
| **System** | OS, architecture, hostname, CPU count, locale |
| **Hardware** | CPU model, core count, RAM, disk space |
| **Disk & Workspace** | Workspace directory size, largest files, disk free space |

### Python Environment

| Section | What it shows |
|---------|--------------|
| **Runtimes** | All Python interpreters found on the system (py launcher, PATH) |
| **Virtual Environment** | Active venv, Hatch environments, conda presence |
| **Packages** | All installed packages with versions, grouped by source |
| **Pip Environments** | pip configuration, index URLs, trusted hosts |

### Project State

| Section | What it shows |
|---------|--------------|
| **Project** | pyproject.toml metadata, build backend, entry points, config files |
| **Project Commands** | Available Hatch scripts, Task commands, Makefile targets |
| **Git** | Branch, remotes, recent commits, dirty state, tag info |
| **CI/CD Status** | GitHub Actions workflow files, branch protection, required checks |

### Development Tools

| Section | What it shows |
|---------|--------------|
| **Pre-commit Hooks** | Installed hooks, stages, versions, health checks |
| **Dependency Health** | Outdated packages, version conflicts, unused deps |
| **Docs Status** | MkDocs config, doc file count, build status |

### Infrastructure

| Section | What it shows |
|---------|--------------|
| **Network** | Proxy settings, DNS resolution, outbound connectivity |
| **Filesystem** | Directory permissions, writable checks, temp dir |
| **PATH Analysis** | PATH entries, dead directories, duplicates, shadowing |
| **Security** | Secret-like env vars, insecure PATH entries, SSH exposure |
| **Container** | Docker/Podman availability, WSL detection, CI environment |

### Cross-Section Analysis

| Section | What it shows |
|---------|--------------|
| **Insights & Warnings** | Derived warnings from all collectors (e.g., "Git is dirty", "PATH has dead entries") |

---

## Architecture Overview

```text
┌─────────────┐     HTTP      ┌──────────────────────────────────┐
│   Browser   │◀────────────▶│  Uvicorn (127.0.0.1:8000)        │
│             │               │                                  │
│  PicoCSS    │               │  FastAPI App (app.py)            │
│  HTMX       │               │  ├── HTML Routes (routes.py)     │
│  Alpine.js  │               │  ├── JSON API (api.py)           │
│             │               │  └── Static Files                │
└─────────────┘               │          │                       │
                              │  ┌───────▼──────────────────┐    │
                              │  │  Cache (collector.py)     │    │
                              │  │  30-second TTL            │    │
                              │  └───────┬──────────────────┘    │
                              │          │                       │
                              │  ┌───────▼──────────────────┐    │
                              │  │  _env_collectors/         │    │
                              │  │  20 plugin collectors     │    │
                              │  │  + redaction + insights   │    │
                              │  └──────────────────────────┘    │
                              └──────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Server** | Uvicorn | ASGI server — listens on port, speaks HTTP |
| **Framework** | FastAPI | Routing, request handling, middleware |
| **Templates** | Jinja2 | Server-side HTML rendering |
| **Styling** | PicoCSS + custom CSS | Classless CSS framework + dashboard theme |
| **Interactivity** | HTMX | Partial page updates without JavaScript |
| **Client State** | Alpine.js | Theme toggle, expand/collapse, auto-refresh |
| **Data** | _env_collectors | Plugin-based system data collection |
| **Cache** | In-memory TTL | 30-second cache to prevent redundant collection |

### Request Flow

1. Browser sends `GET /` to `http://127.0.0.1:8000`
2. Uvicorn receives the request, passes to FastAPI
3. FastAPI routes to `routes.index()` handler
4. Handler calls `collector.get_report_async()`
5. Collector checks cache — if fresh, returns cached data; otherwise runs
   all `_env_collectors` in a thread pool
6. Handler passes data to Jinja2 template (`index.html`)
7. Jinja2 renders HTML using `base.html` layout + section partials
8. FastAPI sends HTML response through Uvicorn to browser
9. Browser renders HTML; HTMX lazy-loads section partials via
   `GET /section/{name}` requests

---

## File Structure

```text
tools/dev_tools/env_dashboard/
├── __init__.py          # Package marker
├── __main__.py          # python -m entry point
├── app.py               # FastAPI app factory, Uvicorn startup, port management
├── api.py               # REST API endpoints (JSON responses)
├── routes.py            # HTML route handlers (Jinja2 templates)
├── collector.py         # Cache layer wrapping _env_collectors
├── export.py            # Static HTML export renderer
├── redact.py            # Redaction level parsing for query params
├── static/
│   ├── css/
│   │   ├── pico.min.css     # PicoCSS framework (vendored)
│   │   └── style.css        # Custom dashboard styles (900+ lines)
│   ├── js/
│   │   ├── htmx.min.js      # HTMX library (vendored)
│   │   └── alpine.min.js    # Alpine.js library (vendored)
│   ├── img/
│   │   └── favicon.svg      # Dashboard favicon
│   ├── offline.html          # Offline fallback page
│   └── sw.js                 # Service worker for offline support
└── templates/
    ├── base.html             # Base layout (nav, sidebar, scripts)
    ├── index.html            # Main dashboard page
    ├── export.html           # Static export page
    └── partials/             # Section templates (one per collector)
        ├── _macros.html      # Reusable Jinja2 macros
        ├── system.html       # System info section
        ├── runtimes.html     # Python runtimes section
        ├── git.html          # Git info section
        └── ...               # 17 more section templates
```

### Key Modules Explained

#### `app.py` — Application Factory

Creates and configures the FastAPI application:

- Mounts static file server
- Configures Jinja2 templates with autoescape (XSS prevention)
- Registers HTML routes and API routes
- Manages port cleanup (kills stale processes on startup)
- Writes PID file for reliable process management
- Prints startup banner with server info and routes

#### `routes.py` — HTML Pages

Three main routes:

| Route | Handler | Returns |
|-------|---------|---------|
| `GET /` | `index()` | Full dashboard page |
| `GET /section/{name}` | `section_partial()` | Single section HTML (htmx partial) |
| `GET /export.html` | `export_html()` | Static HTML export of all data |

#### `api.py` — JSON API

REST endpoints for programmatic access:

| Route | Returns |
|-------|---------|
| `GET /api/report` | Full environment report as JSON |
| `GET /api/summary` | Summary with hostname, Python version, warnings |
| `GET /api/section/{name}` | Single section data as JSON |
| `GET /api/health` | Server health check |
| `GET /api/pip/install` | Stream pip install output (SSE) |

#### `collector.py` — Cache Layer

Wraps `_env_collectors.gather_env_info()` with TTL caching:

- **`get_report_async()`** — Main function called by route handlers
- Runs collection in a thread pool (non-blocking for async routes)
- 30-second TTL: first request collects, subsequent requests serve cache
- Stores previous scan for diff comparison
- Warms cache on startup so first page load is instant

#### `export.py` — HTML Export

Renders a standalone HTML file with all dashboard data embedded. Useful
for sharing environment info without requiring the server to be running.

#### `redact.py` — Redaction Parsing

Parses the `?redact=` query parameter into a `RedactLevel` enum. The
dashboard supports four redaction levels that control what sensitive data
is hidden:

| Level | Hides | Use case |
|-------|-------|----------|
| `none` | Nothing | Local debugging |
| `secrets` | Tokens, passwords, API keys | Default for viewing |
| `pii` | + usernames, hostnames, IPs | Default for export |
| `paranoid` | + paths, environment variables | Maximum privacy |

---

## Data Collection System

### Collector Architecture

Each collector inherits from `BaseCollector` and implements `collect()`:

```python
class SystemCollector(BaseCollector):
    """Collect OS, architecture, and hostname info."""

    name = "system"
    tier = Tier.MINIMAL

    def collect(self) -> dict:
        return {
            "os": platform.system(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            # ...
        }
```

The orchestrator (`__init__.py`) discovers all collectors, filters by tier,
and calls `safe_collect()` on each — which wraps collection in a timeout
and error handler so one broken collector can't crash the dashboard.

### Tier System

Tiers control how many collectors run:

| Tier | Collectors | Speed | Use case |
|------|-----------|-------|----------|
| `MINIMAL` | 5 | ~1 second | Quick health check |
| `STANDARD` | 16 | ~3 seconds | Default dashboard view |
| `FULL` | 20 | ~8 seconds | Deep inspection (includes slow package scan) |

Change tier via query parameter: `http://127.0.0.1:8000/?tier=full`

### Adding a New Collector

1. Create `scripts/_env_collectors/my_section.py`:

    ```python
    from __future__ import annotations
    from _env_collectors._base import BaseCollector, Tier

    class MyCollector(BaseCollector):
        name = "my_section"
        tier = Tier.STANDARD

        def collect(self) -> dict:
            return {"key": "value"}
    ```

2. Register in `scripts/_env_collectors/__init__.py` → `_discover_collectors()`

3. Create template `tools/dev_tools/env_dashboard/templates/partials/my_section.html`:

    ```html
    {% from "partials/_macros.html" import kv_row %}
    <article>
      <header>My Section</header>
      <table>
        {{ kv_row("Key", data.key) }}
      </table>
    </article>
    ```

4. The section auto-appears in the sidebar and main page — no registration
   needed in the templates.

---

## Template System

### Layout Hierarchy

```text
base.html                    ← Global layout (nav, sidebar, footer, scripts)
├── index.html               ← Dashboard page (loops over sections)
│   └── partials/*.html      ← Section templates (loaded by htmx)
└── export.html              ← Static export page
```

### Jinja2 Features Used

| Feature | Example | Purpose |
|---------|---------|---------|
| Template inheritance | `{% extends "base.html" %}` | Shared layout |
| Block override | `{% block content %}...{% endblock %}` | Page-specific content |
| Include | `{% include "partials/system.html" %}` | Embed section templates |
| Macros | `{% macro kv_row(k, v) %}` | Reusable table rows |
| Autoescape | `autoescape=True` | XSS prevention |
| Filters | `{{ value \| default("N/A") }}` | Safe defaults |
| Loop | `{% for item in items %}` | Iterate collections |

### HTMX Partials

Sections load lazily via HTMX. The `index.html` template renders
placeholder divs with `hx-get` attributes:

```html
<div hx-get="/section/system"
     hx-trigger="load"
     hx-swap="innerHTML">
  Loading...
</div>
```

When the page loads, HTMX sends `GET /section/system` and swaps the
response HTML into the div. This means:

- The main page loads fast (just the layout)
- Sections load in parallel
- Individual sections can be refreshed independently

---

## Styling

### Theme System

The dashboard supports **light and dark modes** with **7 accent color themes**:

| Theme | Color | CSS Variable |
|-------|-------|-------------|
| Default | Blue | `--color-accent: #4a9eff` |
| Forest | Green | `--color-accent: #22c55e` |
| Sunset | Orange | `--color-accent: #f97316` |
| Berry | Purple | `--color-accent: #a855f7` |
| Ocean | Teal | `--color-accent: #14b8a6` |
| Rose | Pink | `--color-accent: #f43f5e` |
| Amber | Yellow | `--color-accent: #f59e0b` |

Theme switching is handled by Alpine.js state in `base.html` and
persisted to `localStorage`.

### CSS Architecture

The custom `style.css` is organized into labeled sections:

```css
/* ========== Variables ========== */
/* ========== Layout ========== */
/* ========== Navigation ========== */
/* ========== Sidebar ========== */
/* ========== Cards ========== */
/* ========== Tables ========== */
/* ========== Responsive ========== */
/* ========== Dark Mode ========== */
/* ========== Themes ========== */
/* ========== Animations ========== */
```

PicoCSS provides base styles for semantic HTML elements. The custom CSS
overrides and extends these for dashboard-specific needs.

---

## API Reference

### HTML Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard home page |
| GET | `/section/{name}` | HTMX partial for a single section |
| GET | `/export.html` | Static HTML export |
| GET | `/sw.js` | Service worker |

### JSON API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/report` | Full environment report |
| GET | `/api/summary` | Summary (hostname, Python, warnings) |
| GET | `/api/section/{name}` | Single section data |
| GET | `/api/health` | Health check (`{"status": "ok"}`) |
| GET | `/api/pip/install?package=NAME` | Stream pip install (SSE) |

### Query Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `tier` | `minimal`, `standard`, `full` | `standard` | Collection depth |
| `redact` | `none`, `secrets`, `pii`, `paranoid` | `secrets` | Data redaction level |

---

## Security

The dashboard is designed as a **local-only** development tool:

- **Binds to 127.0.0.1** — not accessible from other machines
- **Jinja2 autoescape** — prevents XSS in rendered templates
- **Read-only** — no system mutations (except `pip install` via API, which
  requires explicit package name)
- **Input validation** — package names validated against allowlist patterns
- **No authentication** — unnecessary for localhost-only tool
- **PID file management** — prevents orphan processes from hogging ports

---

## Offline Support

The dashboard includes a service worker (`sw.js`) that caches the last
successful page load. If the server is stopped while the browser tab is
open, it shows an offline fallback page instead of a browser error.

---

## Performance

- **Cache warmup** — collector runs at startup so first page load is instant
- **Lazy loading** — sections load asynchronously via HTMX
- **Thread pool** — collectors run in a thread pool (non-blocking async loop)
- **30-second TTL** — prevents redundant subprocess calls
- **No-cache headers** on static files during development (CSS changes
  appear immediately)

---

## Troubleshooting

### Port already in use

The dashboard auto-detects and kills stale processes on startup. If that
fails:

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux/macOS
lsof -i :8000
kill <pid>
```

### Sections show errors

Individual collectors are isolated. If one fails, it shows an error message
in its section without affecting others. Check the terminal logs for the
stack trace.

### Dashboard won't start

```bash
# Check Python version (needs 3.11+)
python --version

# Check FastAPI is installed
pip show fastapi

# Run with verbose logging
python -m tools.dev_tools.env_dashboard.app
```

---

## See Also

- [Learning Notes — Web Apps](../notes/learning-web-apps.md) — Web development
  concepts explained (HTTP, frameworks, templates, HTMX, CSS)
- [ADR 041](../adr/041-env-inspect-web-dashboard.md) — Architecture decision
- [Blueprint 001](../blueprints/001-env-inspect-web-dashboard.md) — Design document
- [Entry Points](entry-points.md) — Global CLI commands including `spb-dashboard`
- [Tooling Reference](../tooling.md) — All tools used in this project
