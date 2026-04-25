# Learning Notes — Web Apps

Notes on web application concepts, captured while building the environment
inspection dashboard (`tools/dev_tools/env_dashboard/`).

---

## What Is a Web App?

A **web application** is software that runs on a server and is accessed through
a web browser. Instead of installing a desktop program, users visit a URL and
the server sends back HTML, CSS, and JavaScript for the browser to render.

Key difference from a static website: a web app **generates responses
dynamically** — it runs code on the server to produce each page, often pulling
data from databases, APIs, or (in our case) live system inspection.

### How a Web App Works (Request → Response Cycle)

```text
Browser                          Server
  │                                │
  │── GET http://127.0.0.1:8000 ──▶│
  │                                │  1. Server receives HTTP request
  │                                │  2. Routing: matches URL to handler function
  │                                │  3. Handler runs logic (collect data, query DB, etc.)
  │                                │  4. Template engine renders HTML with data
  │◀── HTTP 200 + HTML response ───│  5. Server sends response back
  │                                │
  │  Browser renders HTML/CSS/JS   │
```

Every interaction — clicking a link, submitting a form, HTMX loading a
partial — follows this same cycle.

---

## Components of a Web App

### 1. Web Framework (FastAPI)

The **framework** is the backbone. It provides:

- **Routing** — maps URLs to Python functions (e.g., `GET /` → `index()`)
- **Request/response handling** — parses headers, query params, body
- **Middleware** — cross-cutting concerns (logging, CORS, auth)
- **Dependency injection** — shared resources like DB connections, templates

**FastAPI** (used in our dashboard) is a modern Python framework built on:

- **Starlette** — the underlying ASGI framework (handles HTTP, WebSockets)
- **Pydantic** — data validation and serialization
- **Type hints** — FastAPI uses Python type annotations to auto-generate
  docs and validate inputs

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")              # Route: GET request to /
async def index():         # Handler function
    return {"status": "ok"}  # Response (auto-serialized to JSON)
```

Other popular Python web frameworks:

| Framework   | Type       | Best for                            |
| ----------- | ---------- | ----------------------------------- |
| **FastAPI** | ASGI/async | APIs, modern apps, type-safe        |
| **Flask**   | WSGI/sync  | Simple apps, learning, prototyping  |
| **Django**  | WSGI/sync  | Full-featured apps (ORM, admin, auth) |
| **Starlette** | ASGI/async | Lightweight, FastAPI builds on it |
| **Litestar** | ASGI/async | Performance-focused, similar to FastAPI |

#### WSGI vs ASGI

- **WSGI** (Web Server Gateway Interface) — synchronous. One request at a time
  per worker. Flask and Django use this.
- **ASGI** (Asynchronous Server Gateway Interface) — async. Can handle many
  concurrent connections efficiently. FastAPI and Starlette use this.

### 2. Application Server (Uvicorn)

The **application server** is what actually runs your Python code and speaks
HTTP. The framework defines _what_ to do; the server handles _how_ to listen
for and serve requests.

**Uvicorn** is an ASGI server (serves async Python apps). It:

- Listens on a host:port (e.g., `127.0.0.1:8000`)
- Accepts incoming HTTP connections
- Passes requests to your FastAPI app
- Sends responses back to the browser
- Supports hot-reload during development (`--reload`)

```python
# This is what `hatch run dashboard:serve` ultimately runs:
uvicorn.run(
    "tools.dev_tools.env_dashboard.app:app",  # Module path to app object
    host="127.0.0.1",   # Only accept local connections (security)
    port=8000,           # Listen on port 8000
    reload=True,         # Auto-restart on code changes (dev only)
    reload_dirs=[...],   # Watch these directories for changes
)
```

Other Python application servers:

| Server       | Protocol | Notes                                    |
| ------------ | -------- | ---------------------------------------- |
| **Uvicorn**  | ASGI     | Fast, default for FastAPI                |
| **Gunicorn** | WSGI     | Battle-tested, production standard       |
| **Hypercorn**| ASGI     | Alternative to Uvicorn                   |
| **Daphne**   | ASGI     | Django Channels server                   |
| **Waitress** | WSGI     | Pure Python, Windows-friendly            |

**Important:** Uvicorn with `--reload` is for **development only**. In
production you'd use Uvicorn behind a process manager (like Gunicorn with
Uvicorn workers) or a reverse proxy (like Nginx).

#### What Are Ports?

A **port** is a number (0–65535) that identifies a specific service on a
machine. Think of it like apartment numbers in a building: the IP address is
the building's street address, and the port is the apartment number.

```text
http://127.0.0.1:8000
      ─────────  ────
      IP address  port
```

**Why ports exist:** A computer can run many network services simultaneously
(web server, database, email). The OS uses ports to route incoming traffic to
the correct program. When you open `http://127.0.0.1:8000`, your browser
connects to the program listening on port 8000 of your local machine.

**Port ranges:**

| Range         | Name          | Description                                      |
| ------------- | ------------- | ------------------------------------------------ |
| 0–1023        | Well-known    | Reserved for standard services (80=HTTP, 443=HTTPS, 22=SSH). Need admin/root to use. |
| 1024–49151    | Registered    | Assigned to specific apps (3306=MySQL, 5432=PostgreSQL, 8080=alt HTTP). |
| 49152–65535   | Dynamic       | Used by OS for temporary outgoing connections.    |

**Only one program can listen on a given port at a time.** If you try to start
two servers on port 8000, the second one fails with "Address already in use."

#### Why We Use Port 8000

Port 8000 is a convention for local development web servers:

- **Not port 80** (standard HTTP) — that requires admin/root privileges on
  most OSes, and your machine may already have something on port 80.
- **Not port 443** (HTTPS) — requires SSL certificates and admin privileges.
- **8000 and 8080** are the de facto "development server" ports. Most
  frameworks default to one of these: Django uses 8000, many Java servers
  use 8080, Vite uses 5173, Next.js uses 3000.
- **It's arbitrary** — you could use any unused port above 1023. We use 8000
  because it's conventional, easy to remember, and unlikely to conflict.

To use a different port, change the `port=` argument in `uvicorn.run()`:

```python
uvicorn.run("app:app", host="127.0.0.1", port=9000)  # Now at http://127.0.0.1:9000
```

#### How to Choose a Port

1. **Start with the framework default** (8000 for FastAPI/Django, 3000 for
   Node.js, etc.) — other developers expect these conventions.
2. **Check if it's in use:** run `netstat -ano | findstr :8000` (Windows) or
   `lsof -i :8000` (macOS/Linux).
3. **Avoid well-known ports** (0–1023) unless you're running a "real" service.
4. **Avoid ports used by other tools** on your machine (e.g., 5432 if you run
   PostgreSQL, 3306 for MySQL).
5. **Pick something memorable** if you run multiple dev servers: dashboard on
   8000, API on 8001, docs on 8002, etc.

### 3. Template Engine (Jinja2)

The **template engine** generates HTML dynamically by combining HTML templates
with data from Python.

**Jinja2** is the standard Python template engine. It lets you:

- Insert variables: `{{ report.hostname }}`
- Use control flow: `{% for item in items %}...{% endfor %}`
- Inherit layouts: `{% extends "base.html" %}` + `{% block content %}`
- Include partials: `{% include "partials/system.html" %}`
- Define macros (reusable components): `{% macro kv_row(k, v) %}`

```html
<!-- templates/index.html -->
{% extends "base.html" %}
{% block content %}
  <h1>Dashboard for {{ summary.hostname }}</h1>
  {% for warning in warnings %}
    <div class="warning">{{ warning.message }}</div>
  {% endfor %}
{% endblock %}
```

**Autoescape** (`autoescape=True`) is critical — it prevents XSS attacks by
escaping `<`, `>`, `&` in user data so they render as text, not HTML/scripts.

### 4. Static Files (CSS, JavaScript, Images)

Static files are served directly without processing. They don't change
per-request — the server just sends the file as-is.

In our dashboard:

```text
static/
├── css/
│   ├── pico.min.css    ← CSS framework (classless, third-party)
│   └── style.css       ← Custom dashboard styles
└── js/
    ├── htmx.min.js     ← HTMX library (partial page updates)
    └── alpine.min.js   ← Alpine.js (client-side reactivity)
```

FastAPI mounts the static directory so the browser can request these:

```python
app.mount("/static", StaticFiles(directory="static"), name="static")
# Browser requests: GET /static/css/style.css → serves the file
```

#### Why `style.css` Not `style.min.css`?

The third-party libraries (`pico.min.css`, `htmx.min.js`, `alpine.min.js`)
are served **minified** (`.min.`) because:

- They're vendored copies of released libraries — you don't edit them
- Minification removes whitespace, comments, shortens variable names
- Smaller file size = faster browser loads

Our custom `style.css` is **not minified** because:

- It's our own code — we need to read and edit it
- This is a local dev tool, not a production website
- Minification adds a build step (need a CSS minifier like cssnano,
  Lightning CSS, or esbuild) which is unnecessary complexity for a
  local-only dashboard
- The file is ~350 lines — minification would save maybe 2KB, negligible
  for localhost

**When would you minify?** For production public-facing web apps, you'd add a
build step (e.g., Vite, Webpack, esbuild) that minifies CSS/JS, adds
fingerprinted filenames for cache-busting, and tree-shakes unused code.

### 5. Frontend Libraries

#### HTMX — HTML-Driven Dynamic Updates

HTMX lets you make parts of a page update dynamically **without writing
JavaScript**. Instead of full page reloads, HTMX sends HTTP requests and
swaps HTML fragments.

```html
<!-- When clicked, fetch /section/system and replace this div's content -->
<div hx-get="/section/system" hx-trigger="click" hx-swap="innerHTML">
  Click to load system info
</div>
```

How it works:
1. Browser sees `hx-get="/section/system"` on an element
2. When triggered (click, load, etc.), HTMX sends an AJAX request
3. Server returns an HTML fragment (not a full page)
4. HTMX swaps the fragment into the DOM

This is the "hypermedia" approach — the server returns HTML, not JSON. Much
simpler than React/Vue/Angular for server-rendered apps.

#### Alpine.js — Lightweight Reactivity

Alpine.js adds client-side interactivity (show/hide, toggle, state) using
HTML attributes. Think of it as "jQuery for the declarative era" or
"Tailwind for JavaScript."

```html
<div x-data="{ open: false }">
  <button @click="open = !open">Toggle</button>
  <div x-show="open">Now you see me</div>
</div>
```

In our dashboard, Alpine.js manages:

- Dark/light theme toggle state
- Section expand/collapse
- Auto-refresh timer
- JSON viewer visibility

#### PicoCSS — Classless CSS Framework

PicoCSS styles semantic HTML elements directly — no utility classes needed.
Write `<table>`, `<nav>`, `<article>` and they look good out of the box.

```html
<!-- No classes needed — Pico styles the semantic elements -->
<article>
  <header>System Info</header>
  <table>
    <tr><td>OS</td><td>Windows 11</td></tr>
  </table>
</article>
```

### 6. Data Collection Layer (`scripts/_env_collectors/`)

The dashboard's "backend logic" — the actual data — comes from the
`_env_collectors` package in `scripts/`. This is a plugin-based system:

```text
_env_collectors/
├── __init__.py          ← gather_env_info() orchestrator + Tier enum
├── _base.py             ← BaseCollector ABC (timeout, error isolation)
├── _redact.py           ← RedactLevel enum + recursive redaction
├── system.py            ← OS, architecture, hostname, CPU
├── runtimes.py          ← Python versions, discovered interpreters
├── path_analysis.py     ← PATH entries, dead dirs, duplicates
├── project.py           ← Lockfiles, config files, build tools
├── git_info.py          ← Git version, branch, dirty state, remotes
├── venv.py              ← Virtualenv detection, Hatch environments
├── packages.py          ← Installed packages, grouping, entry points
├── network.py           ← Proxy vars, DNS, outbound connectivity
├── filesystem.py        ← Disk usage, writable checks
├── security.py          ← Secret env vars, insecure PATH, SSH exposure
├── container.py         ← Docker/CI/WSL/cloud detection
└── insights.py          ← Cross-section warnings (derives from all above)
```

**Architecture:** Each collector inherits `BaseCollector` and implements
`collect()`. The orchestrator calls `safe_collect()` which wraps each in a
timeout and error handler — one slow/broken collector can't crash the others.

**Tiers** control how much data to collect:

| Tier       | Collectors             | Use case                    |
| ---------- | ---------------------- | --------------------------- |
| `MINIMAL`  | system, runtimes, path, project, git | Quick check (~1s) |
| `STANDARD` | + venv, network, filesystem, security, container, insights | Default dashboard |
| `FULL`     | + packages (slow, scans all installed packages) | Deep inspection |

**Redaction** is applied before data leaves the collector layer:

| Level      | What it hides                                     |
| ---------- | ------------------------------------------------- |
| `NONE`     | Nothing — raw data                                |
| `SECRETS`  | Tokens, passwords, API keys (default for viewing) |
| `PII`      | + usernames, hostnames, IPs (default for export)  |
| `PARANOID` | + paths, environment variables                    |

### 7. Caching Layer (`collector.py`)

The dashboard wraps `_env_collectors` with a 30-second TTL cache:

- First request: runs full collection, caches result
- Subsequent requests within 30s: returns cached data instantly
- After 30s or manual refresh: re-runs collection
- Stores previous scan for diff comparison

This prevents hammering the system with expensive subprocess calls (git, py
launcher, pip list) on every page load or HTMX partial request.

---

## The Dashboard Architecture (Putting It All Together)

```text
┌─────────────┐     HTTP      ┌──────────────────────────────────┐
│   Browser   │◀────────────▶│  Uvicorn (127.0.0.1:8000)        │
│             │               │  ┌──────────────────────────────┐ │
│  PicoCSS    │               │  │  FastAPI App                 │ │
│  HTMX       │               │  │  ├── HTML Routes (Jinja2)    │ │
│  Alpine.js  │               │  │  ├── JSON API Routes         │ │
│             │               │  │  └── Static File Server      │ │
└─────────────┘               │  └──────────┬───────────────────┘ │
                              │             │                     │
                              │  ┌──────────▼───────────────────┐ │
                              │  │  Caching Layer (30s TTL)     │ │
                              │  └──────────┬───────────────────┘ │
                              │             │                     │
                              │  ┌──────────▼───────────────────┐ │
                              │  │  _env_collectors             │ │
                              │  │  12 collectors + redaction    │ │
                              │  │  (subprocess calls, os info)  │ │
                              │  └──────────────────────────────┘ │
                              └──────────────────────────────────┘
```

1. **Browser** sends GET request to `http://127.0.0.1:8000`
2. **Uvicorn** receives it, hands to **FastAPI**
3. **FastAPI** routes to the correct handler (HTML page or JSON API)
4. Handler calls **collector.get_report()** which checks the **cache**
5. If stale, cache calls **gather_env_info()** which runs all **collectors**
6. Data flows back: collectors → cache → handler → Jinja2 template → HTML
7. **Uvicorn** sends the HTML response to the **browser**
8. **Browser** renders HTML; HTMX loads section partials lazily

---

## Where Does the Server Run?

When you run `hatch run dashboard:serve`:

- **Host:** `127.0.0.1` (localhost only — not accessible from other machines)
- **Port:** `8000`
- **URL:** `http://127.0.0.1:8000`
- **Server:** Uvicorn (ASGI server) running inside a Hatch-managed virtualenv
- **Framework:** FastAPI (Python web framework)

The server runs **in the foreground** — it takes over your terminal and keeps
running until you press **Ctrl+C**. This is called a "blocking" or
"foreground" process.

- **While running:** the dashboard is available in your browser
- **After Ctrl+C:** the server stops, the port is freed, the browser shows
  a connection error if you try to reload
- **No persistence:** there's no database, no saved state. Each server start
  collects fresh environment data

### Server Logs

Uvicorn prints access logs to the terminal where you started it:

```text
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     127.0.0.1:54321 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:54321 - "GET /static/css/style.css HTTP/1.1" 200 OK
INFO:     127.0.0.1:54321 - "GET /section/system HTTP/1.1" 200 OK
```

Each line shows: client IP, HTTP method, path, and response status code.
These logs appear in the same terminal where `hatch run dashboard:serve` is
running. There is no separate log file — it's all stdout/stderr.

To see more verbose logs, you could modify `uvicorn.run()` to set
`log_level="debug"`.

---

## Why No `vendor/` Directory?

Some web projects use a `vendor/` directory to store third-party library files
(JavaScript, CSS) as committed copies in the repository. This was common before
package managers like npm existed.

Our dashboard doesn't use `vendor/` because:

1. **The files are already committed** — `pico.min.css`, `htmx.min.js`, and
   `alpine.min.js` live in `static/css/` and `static/js/` directly. Having a
   separate `vendor/` directory is just an organizational choice, not a
   technical requirement.

2. **This is a local dev tool** — we only have 3 small vendored files. A
   `vendor/` directory makes sense when you have dozens of third-party assets
   and want to separate them from your own code.

3. **No build pipeline** — there's no npm, no bundler, no `node_modules`.
   The vendored files are downloaded once and committed. A `vendor/` directory
   usually implies a dependency management process (npm install → vendor/).

4. **Convention varies:**
   - `vendor/` — common in Go, PHP, Ruby
   - `static/vendor/` — common in Django/Flask projects
   - `node_modules/` — JavaScript ecosystem (gitignored, not vendored)
   - Flat `static/` — simpler, fine for small projects

If the dashboard grew to include many third-party libraries, reorganizing to
`static/vendor/css/` and `static/vendor/js/` vs `static/css/` and `static/js/`
would be reasonable.

---

## Key Takeaways

1. **Web apps = server + framework + templates + static files + data layer**
2. **FastAPI** is the framework (routing, request handling)
3. **Uvicorn** is the server (listens on a port, speaks HTTP)
4. **Jinja2** is the template engine (generates HTML from data + templates)
5. **HTMX** enables partial page updates without writing JavaScript
6. **Alpine.js** adds client-side interactivity declaratively
7. **PicoCSS** makes semantic HTML look good without CSS classes
8. The _env_collectors do the heavy lifting; the dashboard is just a web UI
   on top of an existing data collection system
9. Everything runs locally on `127.0.0.1` — never exposed to the network
10. Ctrl+C stops the server completely. No persistence, no background process.
