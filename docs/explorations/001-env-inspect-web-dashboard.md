# Exploration 001: Environment Inspection Web Dashboard

## Status

Concluded — Proceed (revised scope v2)

## Revision History

| Version | Date | Summary |
| :------ | :--- | :------ |
| v1 | — | Initial exploration: basic web view of env_inspect.py output |
| v2 | 2026-04-01 | Expanded scope: security/redaction layer, shared collector module, REST API, plugin-based architecture, tiered output, static HTML export, derived insights engine, diff-against-previous-scan |

## Problem Statement

`scripts/env_inspect.py` provides a comprehensive CLI dashboard covering
Python info, git status, venv detection, installed packages, entry points,
build tools, PATH inspection, Python installations, and system environment.
The output is rich but confined to the terminal — long tables scroll off
screen, cross-referencing sections requires scrolling, and the data can't
be filtered, searched, or bookmarked interactively.

Beyond just displaying data, developers need **actionable diagnostics**:
not just "Python 3.11.5" but "Python version does not satisfy project
constraint." Not just a list of PATH entries but "PATH has dead entries"
and "PATH ordering means the wrong python is being used." The current
CLI dumps raw facts — a web dashboard can compute and surface derived
insights with pass/warn/fail severity.

Additionally, **sharing environment state** (for issue reports, team
debugging) requires careful secret redaction. Environment variables
routinely contain API tokens, SSH key references, cloud credentials,
database connection strings, and auth headers. Any export or sharing
mechanism must strip these by default.

A local web dashboard with a REST API, tiered output, and a redaction
layer would address all of these needs in a navigable, filterable,
visually structured interface.

## Why This Might Matter

- **Onboarding:** New contributors get a single URL that shows everything
  about their local setup, with pass/warn/fail badges and guidance on
  what's wrong and how to fix it.
- **Debugging:** When something breaks, a filterable, colour-coded dashboard
  is faster than scrolling terminal output. Tables can be sorted by status,
  outdated packages highlighted, duplicate entries grouped. Diff against
  previous scan shows exactly what changed.
- **Diagnostics:** Complements the existing `doctor.py` / `env_doctor.py`
  family — those check rules, this _shows state and computes insights_.
  Together they answer "what do I have?", "is it correct?", and "what
  should I fix first?".
- **Safe sharing:** With a redaction layer, environment snapshots can
  be exported and attached to bug reports without leaking tokens, SSH
  keys, or cloud credentials. The current CLI offers `--json` but with
  no secret filtering.
- **Programmatic access:** A REST API (`/api/summary`, `/api/warnings`,
  etc.) enables CI scripts, editor extensions, and other tools to
  consume environment data without parsing CLI output.
- **Cost of inaction:** Low — the CLI works fine for single-user terminal
  use. But it can't safely export data, compute cross-section insights,
  or provide a navigable UI for complex environments.

## Alternatives

### Option 1: Jinja + htmx + CSS + minimal JS (recommended)

Serve a Python HTTP server locally, render templates with Jinja2, use htmx
for interactive behaviour (lazy-load slow sections, refresh data, expand/
collapse), and plain CSS for layout.

**Pros:**

- Pure Python backend — no Node.js toolchain, no npm, no bundler
- htmx gives SPA-like interactivity with zero JS framework overhead
- Jinja2 is already a transitive dependency of MkDocs (already in the env)
- Lightweight: the entire frontend is HTML templates + one CSS file + a
  few htmx attributes
- Aligns with the project's "minimal tooling" philosophy
- Easy to extend: add a new section = add a Jinja partial + a route

**Cons:**

- htmx is a CDN/vendored JS dependency (≈14 KB min+gzip) — though it can
  be vendored as a single file in the repo
- CSS-only styling limits chart/graph visualisations (but we don't need
  charts for this use case — tables and key-value grids suffice)
- Less familiar to developers who expect React/Vue patterns

### Option 2: Flask / FastAPI + full frontend framework (React, Vue, Svelte)

Use a proper ASGI/WSGI framework with a JS SPA for the frontend.

**Pros:**

- Maximum flexibility for rich interactivity
- Large ecosystem and community support

**Cons:**

- Massive tooling overhead: Node.js, npm, bundler, framework boilerplate
- Adds a JS build step to a Python-focused project
- overkill for a local diagnostic tool
- Template users who don't want the app still inherit the JS toolchain

**Rejected as primary approach.** Disproportionate complexity for a local
inspection tool.

### Option 3: Rich Live / Textual TUI

Use Rich's Live display or the Textual framework for a terminal-based
interactive dashboard.

**Pros:**

- Stays entirely in the terminal — no browser needed
- Pure Python, no web stack at all
- Textual supports tables, tabs, scrolling, search

**Cons:**

- Terminal-only; can't bookmark, can't share a link
- Textual is a heavyweight dependency (~5 MB) with its own API surface
- Limited layout flexibility vs. HTML+CSS
- Doesn't solve the "show someone your environment state" use case

**Worth considering as a complementary option**, but doesn't replace the
web dashboard.

### Option 4: Static HTML export (no server)

Generate a standalone `.html` file with all data inlined. Open in browser.

**Pros:**

- No server process needed
- File can be shared, attached to issues

**Cons:**

- No interactivity (filtering, lazy-loading, refresh)
- Every inspection generates a new file — workspace clutter
- Stale the moment it's generated
- Security risk: must redact secrets before export or the file becomes
  a credential leak vector

**Adopted as a secondary feature** of the web dashboard. The dashboard
renders the same Jinja2 templates into a self-contained HTML file with
inline CSS, no JavaScript, a Content-Security-Policy meta tag, and
PII-level redaction by default. See the blueprint's "Static HTML Export"
section for security constraints.

### Option 5: Do nothing

Keep `env_inspect.py --json` and `env_inspect.py --section <name>` as-is.

**Pros:**

- Zero effort
- CLI already works well

**Cons:**

- Misses UX improvements for onboarding and debugging
- Long terminal output remains hard to navigate

## Proposed Repo Layout

The app should live **outside `src/`** since it's a developer tool, not
part of the distributed package. Template users who don't want it can
delete the directory without affecting the core package.

Data collection logic should be **extracted to a shared module** so that
both the CLI and the web dashboard use identical code.

```
scripts/
├── _env_collectors/              ← NEW: shared data-collection module
│   ├── __init__.py               ← gather_env_info(), registry, tier logic
│   ├── _base.py                  ← BaseCollector ABC, timeout/error helpers
│   ├── _redact.py                ← Redaction rules and RedactLevel enum
│   ├── system.py                 ← OS, arch, hostname, shell, privilege
│   ├── runtimes.py               ← Python installations, compilers, version mgrs
│   ├── path_analysis.py          ← PATH dirs, duplicates, dead entries, ordering
│   ├── project.py                ← Repo detection, lockfiles, build tools
│   ├── git_info.py               ← Git version, dirty state, remotes
│   ├── venv.py                   ← Virtualenv, Hatch envs, mismatch
│   ├── packages.py               ← Installed packages, outdated, entry points
│   ├── network.py                ← DNS, proxy, outbound summary
│   ├── filesystem.py             ← Writable dirs, disk space, mounts
│   ├── security.py               ← Secret scan, permissions, insecure PATH
│   ├── container.py              ← Docker/CI/WSL/cloud detection
│   └── insights.py               ← Derived warnings and recommendations
├── env_inspect.py                ← CLI (imports from _env_collectors)
└── ...

tools/
└── dev-tools/
    └── env_dashboard/
        ├── __init__.py
        ├── app.py              ← Entry point: starts Uvicorn server
        ├── collector.py        ← Wraps _env_collectors, caching, tier selection
        ├── redact.py           ← Dashboard-specific redaction wiring
        ├── routes.py           ← HTML route handlers, returns rendered templates
        ├── api.py              ← JSON API route handlers
        ├── export.py           ← Static HTML export logic
        ├── static/
        │   ├── css/
        │   │   ├── pico.min.css  ← Vendored Pico CSS minified (production)
        │   │   └── style.min.css ← Custom properties minified (production)
        │   ├── js/
        │   │   ├── htmx.min.js   ← Vendored htmx minified (~14 KB, production)
        │   │   └── alpine.min.js ← Vendored Alpine.js minified (~15 KB, production)
        │   ├── vendor/           ← Readable (unminified) versions for debugging
        │   │   ├── css/
        │   │   │   ├── pico.css   ← Readable Pico CSS source
        │   │   │   └── style.css ← Readable custom styles source
        │   │   └── js/
        │   │       ├── htmx.js    ← Readable htmx source
        │   │       └── alpine.js  ← Readable Alpine.js source
        │   └── img/
        │       └── favicon.svg   ← Simple Python-themed SVG
        ├── templates/
        │   ├── base.html       ← Layout shell (nav, footer, script tags)
        │   ├── index.html      ← Main dashboard page
        │   ├── export.html     ← Self-contained export template (no JS)
        │   └── partials/       ← htmx-swappable fragments
        │       ├── summary.html
        │       ├── warnings.html
        │       ├── system.html
        │       ├── runtimes.html
        │       ├── path.html
        │       ├── project.html
        │       ├── git.html
        │       ├── venv.html
        │       ├── packages.html
        │       ├── network.html
        │       ├── filesystem.html
        │       ├── security.html
        │       ├── container.html
        │       └── raw_json.html
        └── README.md           ← Usage, development instructions
```

**Why `tools/dev-tools/` and not `scripts/`?** `scripts/` is for
single-file CLI utilities. The env_dashboard is a multi-file application
with its own templates, static assets, and internal structure. The
`tools/dev-tools/` path makes the purpose explicit — this is a template
repo, so clarity matters more than brevity. Template users scanning the
repo tree immediately understand what lives here. The extra nesting also
leaves room for sibling directories under `tools/` (e.g., `tools/ci/`,
`tools/release/`) without overloading one flat folder.

**Why extract `gather_env_info()` to `scripts/_env_collectors/`?** The
current monolithic function in `env_inspect.py` calls ~15 private `_*`
functions. Both consumers (CLI and web dashboard) need the same data.
Extracting to a shared plugin-based module:

- **Eliminates duplication** — one source of truth for data collection.
- **Enables independent collector development** — new sections are just
  new files in the package.
- **Supports tiered output** — collectors declare their tier (minimal,
  standard, full) and are filtered at query time.
- **Supports timeouts and error isolation** — the base class wraps each
  collector in try/except with per-collector timeouts.
- **Follows naming convention** — underscore-prefix `_env_collectors`
  signals it's a shared module, not a standalone CLI.

## Technology Details

### Backend

- **FastAPI** or **Starlette** as the backend framework. FastAPI is the
  natural choice: it's already in the Python ecosystem, gives you async
  route handlers, automatic OpenAPI docs, and clean dependency injection.
  Yes, FastAPI _is_ the backend — it handles HTTP routing, serves the
  Jinja2 templates, and exposes the data-collection endpoints. No
  separate "backend" is needed beyond it.
- **Uvicorn** as the ASGI server. Uvicorn is the standard way to run
  FastAPI/Starlette apps — lightweight, fast, pure-Python, and supports
  `--reload` for development. It's the default recommendation in the
  FastAPI docs and adds no conceptual overhead. Install it alongside
  FastAPI (often via `fastapi[standard]` which bundles Uvicorn). For a
  local dev tool the built-in Uvicorn invocation (`uvicorn app:app
  --reload --host 127.0.0.1 --port 8000`) is all you need — no process
  manager, no Gunicorn, no reverse proxy.
- Alternatively, Python stdlib `http.server` works for a zero-dependency
  start, but if routing gets beyond ~5 routes or you want async data
  collection (fetching slow package info without blocking), FastAPI +
  Uvicorn earns its keep quickly.
- **Jinja2** for templating — already available via MkDocs dependency.
  Add as an explicit optional dependency in `pyproject.toml` under a
  `[project.optional-dependencies] dashboard` group.
- Data collection reuses `gather_env_info()` from `env_inspect.py`.

### Frontend

- **htmx** (vendored, ~14 KB): handles lazy-loading of slow sections
  (e.g., outdated package checks), refresh-in-place, and expand/collapse
  without writing JS handlers.
- **Alpine.js** (vendored, ~15 KB min+gzip): tiny reactive JS framework
  for client-side state that htmx doesn't cover — search/filter input
  binding, toggle/accordion state, tab switching, dropdown menus. Uses
  declarative HTML attributes (`x-data`, `x-show`, `x-on`) so it reads
  like htmx and requires no build step. Alpine and htmx complement each
  other cleanly: htmx owns server communication, Alpine owns local UI
  state. Only reach for Alpine when the interaction is purely client-side
  and doesn't need a server round-trip.
- **Chart.js** (vendored or CDN, ~65 KB min+gzip): canvas-based charting
  library for data visualisations where tables aren't enough — e.g.,
  package distribution by location (pie/doughnut), dependency freshness
  over time (bar), Python version coverage matrix (horizontal bar), or
  PATH entry counts. Simple API, sensible defaults, responsive out of the
  box. Only include Chart.js on pages/sections that actually render a
  chart — don't load it globally if most sections are pure tables.
- **CSS**: Custom stylesheet. Start with a clean, minimal design. CSS
  custom properties for theming.  Consider classless CSS frameworks
  (Pico CSS, Simple.css, MVP.css) as a starting base — they style
  semantic HTML with zero class annotations and weigh <10 KB.
- **Minimal additional JS**: Only for behaviour that htmx + Alpine can't
  handle (e.g., clipboard API for copy-to-clipboard). No framework, no
  build step, no npm. **Use minimal JavaScript unless it adds a feature
  or idea worth having** — one of the reasons a web app makes sense here
  is the amount of information to display is too heavy for a terminal
  view, but the interactivity budget should stay small. If a feature can
  be done with htmx attributes, Alpine directives, or CSS, do it that
  way.

### Sections (expanded beyond env_inspect.py)

The v1 sections mirrored `env_inspect.py` 1:1. The v2 design reorganises
into domain-oriented sections with broader coverage:

| Section | Data collected | Tier | Notes |
| :------ | :------------- | :--- | :---- |
| **System** | OS, kernel, arch, shell, terminal, cwd, privilege, locale, clock | Minimal | Core identity |
| **Runtimes** | Python versions/installations, Node, compilers, version managers | Minimal | What's available to run code |
| **PATH Analysis** | All entries, duplicates, dead entries, ordering issues, exec counts | Minimal | High-value diagnostics |
| **Project** | Repo root, lockfiles, build/test/lint tools, config files | Minimal | Project-specific context |
| **Git** | Version, branch, dirty state, remote URLs (redacted), stash | Minimal | Source control state |
| **Virtual Environments** | Active venv, Hatch envs, mismatch, interpreter path | Standard | Environment isolation state |
| **Packages** | Installed packages by location, outdated, duplicates, entry points | Full | Slow — full inventory |
| **Network** | DNS, proxy, outbound summary, interface details | Standard | Connectivity diagnostics |
| **Filesystem** | Writable temp/cache dirs, disk space, mount info | Standard | Build/install feasibility |
| **Security** | Secret exposure scan, insecure PATH, permission warnings | Standard | Safety checks |
| **Container/CI** | Docker/Podman/CI/WSL/cloud detection, resource limits | Standard | Runtime context |
| **Raw JSON** | Full scan output as formatted JSON | Full | For power users and debugging |

### Tiered output

Data collection is organised into four tiers to balance speed, detail,
and safety:

**Minimal** — Quick snapshot, safe to share, fast to collect.

- OS, arch, hostname, username, shell, cwd
- PATH summary (count, duplicates, dead entries)
- Runtimes (Python, Node, compilers detected)
- Package managers (pip, hatch, uv, conda, etc.)
- Git/project summary (repo, branch, clean/dirty)

**Standard** (default) — Adds diagnostics and warnings.

- All of Minimal
- Env vars summary (names only, values redacted by default)
- Disk/memory/network summary
- Container/CI/cloud detection
- All detected tool versions
- Warnings panel (all derived insights)
- Virtualenv status and mismatch

**Full** — Complete inventory, may be slow.

- All of Standard
- Full package lists with versions/locations
- Full env var dump (values visible, secrets still redacted)
- Loaded config files (pyproject.toml, .tool-versions, etc.)
- Network interface details, mount details

**Redacted Full** (Full + PII redaction) — Not a separate tier.
This is the Full tier with `PII` redaction level applied. The tier
(Minimal/Standard/Full) and redaction level (NONE/SECRETS/PII/PARANOID)
are independent axes. "Redacted Full" is shorthand for the combination
used by default for exports: Full data with usernames, hostnames, IPs,
tokens, keys, and credentials masked.

### Derived insights

The most useful output is often not raw facts but computed
**warnings and recommendations**. The `insights.py` collector
cross-references data from other sections to produce actionable
diagnostics:

| Insight | Severity | Source sections |
| :------ | :------- | :-------------- |
| Python version doesn't satisfy `requires-python` | fail | runtimes, project |
| Virtualenv not active | warn | venv |
| PATH has dead entries | warn | path_analysis |
| PATH ordering: wrong python/node/gcc is used | fail | path_analysis, runtimes |
| PATH has duplicate entries | warn | path_analysis |
| Git working tree dirty; builds may be non-reproducible | warn | git |
| Secrets found in environment variables | fail | security |
| Lockfile mismatch (requirements.txt vs installed) | warn | project, packages |
| Missing compiler/native build tools | warn | runtimes |
| `/tmp` not writable | fail | filesystem |
| Running under WSL; path behavior differs | info | container |
| CI environment detected; avoid interactive prompts | info | container |
| Container detected with memory cap | warn | container |
| DNS works but outbound HTTPS blocked | warn | network |
| Clock skew may break certs or builds | warn | system |
| Disk nearly full; installs/builds may fail | warn | filesystem |
| Project expects one pkg manager but another is active | warn | project, runtimes |
| Node/Python version mismatch with version file | fail | runtimes, project |
| X11/Wayland unavailable; GUI tests will fail | info | system |
| System locale may affect sorting/parsing | info | system |
| Cloud credentials found but region not set | warn | security |
| Unsupported Python/tool versions | warn | runtimes |

Not all of these will be implemented in Phase 1. Insights that require
data from collectors not yet built (network, filesystem) are deferred to
later phases.

### REST API design

The dashboard exposes a JSON API alongside the HTML interface. This
enables CI scripts, editor extensions, and other tools to consume
environment data programmatically.

| Method | Path | Description |
| :----- | :--- | :---------- |
| `GET` | `/api/summary` | Top summary bar data |
| `GET` | `/api/report` | Full scan (all sections at current tier) |
| `GET` | `/api/warnings` | Warnings panel data |
| `GET` | `/api/sections/:name` | Single section by name |
| `POST` | `/api/scan` | Trigger a fresh scan (`?tier=`, `?deep=true`) |
| `GET` | `/api/export.json` | Downloadable JSON (PII-redacted by default) |

**Why `POST /api/scan`?** It doesn't mutate system state — it triggers
a read-only environment scan. POST is used because it has side effects
(cache invalidation, may be slow) and isn't idempotent in timing.

All endpoints accept `?redact=none|secrets|pii|paranoid` (default:
`secrets`). Export endpoints default to `pii`.

### Interactive features via htmx + Alpine.js

- **Lazy-load slow sections:** Package outdated check (runs `pip list
  --outdated`) is slow. Load the page immediately, then htmx-trigger the
  outdated check in the background and swap in results.
- **Refresh button per section:** `hx-get="/section/packages"
  hx-target="#packages"` — re-collect and re-render just that section.
- **Expand/collapse details:** Collapsible section cards. Package list
  grouped by location, each group collapsible. Alpine.js `x-show` /
  `x-data` handles the toggle state client-side — no server round-trip.
- **Search/filter:** Alpine.js `x-model` on an input bound to a filtered
  list — instant client-side filtering across all visible sections.
- **Pass/warn/fail badges:** Each section and the top summary bar shows
  coloured status badges computed from the insights engine.
- **Hide/show empty fields:** Toggle to remove clutter from sections
  where many fields are empty (e.g., network on offline machines).
- **Redact secrets toggle:** Switches between showing and hiding
  sensitive values. Local viewing only — exports always redact.
- **Raw JSON viewer:** Full scan output as syntax-highlighted, copyable
  JSON. Useful for sharing with support or filing bug reports.
- **Copy field value:** Clipboard button on each field for quick copying.
- **Timestamps:** Shown on the summary bar and per-section.
- **Diff against previous scan:** Highlights what changed since the last
  scan — new warnings, changed values, resolved issues.

### Technology Stack Summary

All tools for the web dashboard in one table. "Vendored" means checked
into the repo as a single file — no CDN dependency, no npm, no build
step.

| Tool | Category | What It Does | Why Use It Here |
| :--- | :------- | :----------- | :-------------- |
| **FastAPI** | Backend — framework | ASGI web framework: routing, dependency injection, async endpoints | Clean route declarations, native async (critical for slow subprocess calls), auto OpenAPI docs for the REST API, Jinja2 integration built-in |
| **Uvicorn** | Backend — server | ASGI server that runs the FastAPI app | The standard FastAPI server; lightweight, fast, pure-Python; `--reload` for dev; hardcode `--host 127.0.0.1` for local-only binding |
| **Jinja2** | Backend — templating | Server-side HTML template rendering with inheritance and partials | Already a transitive dep (MkDocs); proven and well-documented; partials map 1:1 to htmx fragment endpoints; `autoescape=True` for safe rendering of arbitrary env-var values |
| **htmx** | Frontend — interactivity | HTML-over-the-wire: AJAX, lazy-loading, partial page updates via HTML attributes | SPA-like UX with zero JS framework overhead; lazy-load slow sections, refresh-in-place, swap HTML fragments; ~14 KB vendored; no build step |
| **Alpine.js** | Frontend — client-side state | Minimal reactive JS framework for local UI interactions | Client-side search/filter binding, toggle/accordion state, redact toggle, hide/show empty fields; ~15 KB vendored; declarative HTML attributes (`x-data`, `x-show`, `x-model`) — reads like htmx; no build step |
| **Pico CSS** | Frontend — styling | Classless CSS framework for semantic HTML | Clean typography, tables, cards, dark/light mode with zero class annotations; <10 KB; styles `<table>`, `<article>`, `<nav>` directly; rapid prototyping without writing CSS from scratch |
| **Custom CSS** | Frontend — styling | Project-specific dashboard styles and theming | CSS custom properties for colour theming, dashboard grid layouts, status-colour tokens (pass/warn/fail), overrides on top of Pico CSS base |
| **djLint** | Tooling — linting | Jinja/HTML template linter and formatter | Catches unclosed tags, malformed Jinja blocks, attribute ordering issues; single Python package (`pip install djlint`), no Node.js; add as pre-commit hook when templates exceed ~20 files |
| **Prettier** | Tooling — formatting | Code formatter for CSS (already in project) | Already available via pre-commit; extend existing file patterns to cover `.css` files — trivial config change |
| **Biome** | Tooling — linting | Fast JS linter and formatter (Rust binary) | Single binary, zero npm dep; add when JS exceeds ~200 lines or spans multiple files; handles JS + JSON + CSS in one tool |

**Chart.js deferred:** The original v1 design included Chart.js (~65 KB)
for package distribution pie charts and PATH bar charts. On reflection,
these visualisations don't add enough value over well-formatted tables
to justify the weight. Chart.js is deferred — add it later only if
specific visualisations prove genuinely more useful than tables.

### Additional Recommendations

Tools not in the core stack but worth considering as the dashboard
evolves:

| Tool | Category | What It Does | When to Add |
| :--- | :------- | :----------- | :---------- |
| **htmx SSE extension** | Frontend — real-time | Server-Sent Events via htmx attributes | If you want live-updating sections (e.g., auto-refresh on file changes); FastAPI/Starlette support SSE natively; htmx has a built-in SSE extension |
| **orjson** | Backend — performance | Fast JSON serialisation (Rust-backed) | Only if the `/api/` JSON endpoints become a bottleneck; the stdlib `json` module is fine for a local tool |
| **python-multipart** | Backend — forms | Multipart form data parsing for FastAPI | Only if you ever add a form (e.g., a search box that POSTs); currently not needed since the dashboard is read-only |
| **Heroicons / Lucide** | Frontend — icons | SVG icon sets | Small inline SVGs for status indicators (check, warning, error), nav icons, section headers; copy individual SVGs into templates — no icon font, no sprite sheet |
| **favicon** | Frontend — branding | `.ico` or `.svg` favicon | Minor polish; a simple Python-themed SVG favicon avoids the browser's default blank tab icon |

## Linting and Formatting for Additional Languages

The web app introduces HTML (Jinja templates), CSS, and a small amount of
JS. The question: do these need dedicated linters/formatters?

**Recommendation: not yet, but plan for it.**

### HTML (Jinja) — djLint vs manual review

- **djLint** is the leading linter/formatter for Jinja/Nunjucks/Django
  templates. It checks tag balance, attribute ordering, indentation, and
  Jinja syntax errors. It runs as a single Python package (`pip install
  djlint`) with no Node.js dependency — fits this project perfectly.
- **curlylint** is an alternative but is unmaintained.
- With only ~12 template files initially, manual review is sufficient.
  If templates grow past ~20 files, add djLint as a pre-commit hook —
  it's cheap and catches real bugs (unclosed tags, malformed blocks).

### CSS — Prettier (already available)

- **Stylelint** is the standard CSS linter, but for a single stylesheet
  it's overkill and adds a Node.js dependency.
- **Prettier** (already in the project for Markdown) can format CSS.
  Add `css` to the Prettier file patterns in `.pre-commit-config.yaml`
  as a low-cost first step.

### JS — ESLint vs Biome vs nothing

- **ESLint** is the standard JS linter but requires Node.js, npm, and a
  config file. For ~50 lines of vanilla JS in a Python project, the
  dependency weight is disproportionate.
- **Biome** (https://biomejs.dev/) is a single Rust binary that handles
  linting + formatting for JS/TS/JSON/CSS with zero npm dependency. It
  can be installed via `curl`, Homebrew, or as a pre-commit hook. If JS
  grows beyond a single file, Biome is the right choice — fast, zero
  config by default, and doesn't drag in the Node.js ecosystem.
- **For now:** Skip dedicated JS linting. The JS surface is tiny (vanilla
  snippets, no modules, no build step). Revisit when JS exceeds ~200
  lines or spans multiple files.

**TL;DR:** Extend Prettier to cover CSS (trivial). Skip dedicated
HTML/JS linters until the codebase warrants it. When it does, use djLint
for Jinja templates and Biome for JS — both avoid Node.js/npm overhead.
Revisit if the template count exceeds ~20 files or JS exceeds ~200 lines.

## Risks

- **Scope creep:** The v2 design is significantly larger than v1. The
  expanded feature set (API, tiers, insights, export, diff) is justified
  by real use cases, but must be delivered in phases. Each phase should
  be independently useful. Resist adding features beyond what's documented.
- **Secret leakage:** Environment data routinely contains tokens, SSH
  key references, cloud credentials, cookies, auth headers, and `.env`
  secrets. The redaction layer is a hard requirement — it must be in
  place before any export feature ships. See the dedicated security
  section below.
- **Dependency on env_inspect.py internals:** Extracting to
  `_env_collectors` makes the dependency explicit and clean. The CLI
  and dashboard both import from the same module. Breaking changes are
  localised to the shared module.
- **Maintenance burden:** More sections, more collectors, more templates.
  Mitigate with the plugin architecture (each collector is independent)
  and by keeping the frontend simple (no build step, no npm). The
  insights engine adds cross-section logic which is inherently more
  complex — keep insight rules simple and well-documented.
- **Performance:** Some collectors are slow (outdated package checks,
  network probes). Per-collector timeouts and htmx lazy-loading ensure
  the dashboard stays responsive. The deep-scan mode is opt-in.

## Security — Redaction Layer and Local-Only Scope

This is a **local developer tool**, not a public web app. The security
requirements are fundamentally different from a production service —
but the **redaction layer** is critical because the tool handles data
that contains secrets, and exports may be shared.

### Threat model: what leaks

Environment data routinely contains:

| Category | Examples | Risk |
| :------- | :------- | :--- |
| API tokens | `GITHUB_TOKEN`, `NPM_TOKEN`, `AWS_SECRET_ACCESS_KEY`, `PYPI_TOKEN` | Full account compromise |
| SSH keys | `~/.ssh/id_*` paths, key contents in env vars | Server access |
| Cloud credentials | `GOOGLE_APPLICATION_CREDENTIALS`, `AZURE_*`, `AWS_*` | Cloud resource access |
| Cookies / sessions | `Set-Cookie`, session tokens in env vars | Session hijack |
| Auth headers | `Authorization: Bearer ...`, basic auth in URLs | API access |
| `.env` secrets | Any value loaded from `.env` files | Varies — often DB passwords, API keys |
| Database URLs | `DATABASE_URL=postgres://user:pass@host/db` | Database access |
| Usernames / hostnames | `$USER`, `$HOSTNAME`, hostnames in URLs | PII, attack surface |
| IP addresses | Interface IPs, proxy IPs | Network reconnaissance |
| Remote URLs with creds | `https://user:token@github.com/repo.git` | Repository access |

### Redaction design

`_env_collectors/_redact.py` provides the redaction layer:

```python
class RedactLevel(Enum):
    NONE = "none"           # No redaction (local-only viewing)
    SECRETS = "secrets"     # Tokens, keys, passwords, DB URLs (DEFAULT)
    PII = "pii"            # Secrets + usernames, hostnames, IPs
    PARANOID = "paranoid"   # PII + high-entropy strings + all env values
```

**Key principles:**

- **Server-side redaction.** The browser never receives unredacted data
  at `SECRETS`/`PII`/`PARANOID` levels. The toggle in the UI only works
  for downgrading from `SECRETS` to `NONE` during local viewing.
- **Exports default to PII.** Static HTML and JSON exports apply `PII`
  redaction by default. Users must explicitly request lower levels.
- **Allowlist for env vars at SECRETS level.** Only known-safe env var
  names (`PATH`, `HOME`, `SHELL`, `LANG`, `TERM`, `EDITOR`, etc.) pass
  through with values. Unknown env vars show name only, value redacted.
- **Pattern matching.** Known secret patterns (`*_TOKEN`, `*_SECRET`,
  `*_KEY`, `*_PASSWORD`, `*_CREDENTIAL`, `AWS_*`, `GITHUB_TOKEN`, etc.)
  are always redacted regardless of the allowlist.
- **High-entropy detection.** At `PARANOID` level, Base64-like strings
  > 20 characters in env var values are redacted.
- **URL credential stripping.** URLs matching `scheme://user:pass@host`
  have the credential portion replaced with `[REDACTED]`.

### Static HTML export security

Exports are a special concern because the file leaves the developer's
machine:

- **No JavaScript.** The export is pure HTML + inline CSS. No scripts,
  no htmx, no Alpine. This prevents XSS if the file is opened in an
  untrusted context or served over a local HTTP server.
- **CSP meta tag.** `<meta http-equiv="Content-Security-Policy"
  content="default-src 'none'; style-src 'unsafe-inline';">` blocks
  script execution.
- **No external URLs.** No CDN links, no font imports, no tracking.
- **HTML-escaped values.** Jinja2 `autoescape=True` — non-negotiable.
- **Redaction level stamped.** The export header shows the redaction
  level and timestamp. If redaction is below `PII`, a visible warning
  banner reads: "This report may contain sensitive information."
- **Content-Disposition: attachment.** The browser downloads the file
  rather than navigating to it, reducing accidental exposure.

### What you need for local-only use

- **Bind to localhost only.** Hardcode `--bind 127.0.0.1` — never
  `0.0.0.0`. This means only processes on your machine can reach it.
- **Jinja2 autoescaping.** Non-negotiable even for local use.
- **Redaction layer active by default.** Even local viewing uses
  `SECRETS` level — the user must explicitly toggle to `NONE`.
- **Read-only.** `POST /api/scan` triggers collection but doesn't
  mutate system state.

### What you do NOT need for local-only use

- **Authentication / authorization** — only you can reach 127.0.0.1.
- **HTTPS / TLS** — traffic never leaves your machine.
- **CSRF tokens** — no state-changing operations.
- **Rate limiting** — only one user (you).
- **Session management** — no login, no cookies, no state.
- **Database hardening** — there is no database.
- **CORS headers** — no cross-origin requests to handle.

### When security gets serious

If this were ever exposed to the network or multiple users, you'd need
all of the above plus: authentication (OAuth/API keys), TLS, CORS policy,
CSRF protection, rate limiting, input sanitization, and audit logging.
The local-only constraint is itself a security strategy.

## Complexity Scaling — What If You Want a Lot of Features?

A natural question: what if the dashboard grows to show a _lot_ of
information — not just env state but also doctor results, CI status,
dependency graphs, security audit results, and more?

### It stays manageable if you follow these rules

1. **Each section is a Jinja partial + a route.** Adding a new section
   means one template file and one route handler. The architecture is
   additive, not exponential — 20 sections isn't 20× harder than 5.
2. **htmx lazy-loading keeps the page fast.** Slow sections (package
   outdated checks, security audits) load asynchronously. The initial
   page render stays snappy regardless of how many sections exist.
3. **Data collection is the bottleneck, not the frontend.** The hard
   part is gathering data (subprocess calls, file parsing, network
   requests). The dashboard just renders what `gather_env_info()` and
   similar functions return. If a new data source is slow, give it an
   htmx lazy-load endpoint.
4. **No client-side state management.** With htmx, the server owns all
   state. Each section is an independent HTML fragment. No Redux, no
   Vuex, no component lifecycle — just templates.

### Where it gets harder

- **Cross-section relationships.** If sections need to reference each
  other ("this package is outdated AND breaks this entry point"), you
  need a data layer that correlates information before rendering. This
  is still backend Python logic, not frontend complexity.
- **Real-time updates.** If you want live-updating data (watch for file
  changes, auto-refresh on git operations), you'd need SSE (Server-Sent
  Events) or WebSocket support. FastAPI/Starlette handle both natively,
  and htmx has SSE support built in — but it adds moving parts.
- **User preferences.** If you want saved filters, layout customization,
  or bookmarkable views, you need persistence (even just a JSON file).
  This is where local tools start creeping toward app territory.
- **Multiple data sources with different refresh rates.** Some data is
  instant (Python version), some is slow (outdated packages), some is
  very slow (security audit). Managing per-section refresh intervals
  adds coordination overhead.

### Honest assessment

For a local diagnostic dashboard with 10–20 read-only sections, the
Jinja + htmx + FastAPI stack handles it comfortably. The complexity
growth is linear, not exponential. It gets genuinely harder only if you
add write operations, real-time features, or cross-section data
correlations — and even then, it's backend complexity (Python code you
control), not frontend framework wrestling.

The danger isn't technical complexity — it's scope creep. Define what the
dashboard shows, resist the urge to add config editing or package
management, and it stays a simple read-only tool.

## Worth Doing?

**Yes — the expanded scope is justified.**

The v2 design is larger than the original "simple dashboard" but every
addition addresses a real need:

- **Redaction layer:** Hard requirement. Without it, exports leak secrets.
- **Shared collector module:** Eliminates duplication between CLI and web.
- **Plugin-based collectors:** Makes the system extensible without touching
  core code. New sections = new files.
- **Tiered output:** Users choose their speed/detail trade-off.
- **Derived insights:** The most valuable part — computed diagnostics
  ("your PATH is misconfigured") are more useful than raw facts.
- **REST API:** Enables programmatic consumption by CI/editors/scripts.
- **Static HTML export:** Secondary feature, not a complex undertaking
  given the Jinja2 templates already exist. Security constraints are
  well-defined.
- **Diff against previous scan:** Small incremental effort (cache one
  previous result, compute delta) with high debugging value.

The risk is scope creep _beyond_ this list. The design is now
comprehensive enough — resist adding more features.

**Recommendation:** Proceed in phases. Phase 1 delivers the shared
collector module, redaction layer, and minimal dashboard. Phase 2 adds
the API and remaining sections. Phase 3 adds export, diff, and polish.

## Open Questions

- ~~**`tools/` vs `devtools/` vs another directory name?**~~ —
  **Decided: `tools/dev-tools/`.**
- ~~**FastAPI vs Starlette vs stdlib?**~~ — **Decided: FastAPI + Uvicorn.**
- ~~**Should `gather_env_info()` be extracted into a shared module?**~~ —
  **Decided: Yes.** Extract to `scripts/_env_collectors/` as a
  plugin-based collector system with a `BaseCollector` ABC.
- ~~**Static HTML export?**~~ — **Decided: Yes.** Secondary export
  feature. PII-redacted by default, no JavaScript, CSP meta tag.
- ~~**Vendor vs CDN for Alpine.js?**~~ — **Decided: Vendor.** Consistent
  with htmx approach, avoids CDN dependency.
- ~~**Chart.js scope?**~~ — **Decided: Deferred.** Start without it.
  Add later only if specific visualisations prove more useful than tables.
- **Exact allowlist for "safe" env vars** — needs review of common
  platforms (Linux, macOS, Windows) to build a comprehensive list.
- **Deep scan timeout budget** — total time limit for `?deep=true`
  scans to prevent runaway collection.
- **Insights that require new collectors** — network probes, clock
  skew detection, X11/Wayland checks. Phase these based on value.

## Next Steps

- [x] Create a blueprint in `docs/blueprints/` with detailed component
      design and template wireframes →
      [Blueprint 001](../blueprints/001-env-inspect-web-dashboard.md)
- [x] Draft an ADR for the `tools/dev-tools/` directory convention →
      [ADR 041](../adr/041-env-inspect-web-dashboard.md)
- [ ] Build `scripts/_env_collectors/` shared module — extract from
      `env_inspect.py`, add `BaseCollector` ABC, tier logic, redaction
- [ ] Prototype: minimal dashboard with summary + 3 sections →
      [Implementation Plan 001](../implementation-plans/001-env-inspect-web-dashboard.md)

## References

- [scripts/env_inspect.py](../../scripts/env_inspect.py) — Existing CLI
  tool with all data-gathering logic
- [scripts/env_doctor.py](../../scripts/env_doctor.py) — Complementary
  diagnostic tool (checks rules, not state)
- [htmx documentation](https://htmx.org/docs/)
- [Alpine.js documentation](https://alpinejs.dev/)
- [Chart.js documentation](https://www.chartjs.org/docs/)
- [Uvicorn documentation](https://www.uvicorn.org/)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Jinja2 documentation](https://jinja.palletsprojects.com/)
- [Pico CSS documentation](https://picocss.com/docs)
- [ADR 036: Diagnostic tooling strategy](../adr/036-diagnostic-tooling-strategy.md)
- [ADR 031: Script conventions](../adr/031-script-conventions.md)
