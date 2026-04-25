# Blueprint 001: Environment Inspection Web Dashboard

## Status

Accepted — Revised (v2)

## Revision History

| Version | Date | Summary |
| :------ | :--- | :------ |
| v1 | — | Initial blueprint: basic read-only dashboard mirroring env_inspect.py |
| v2 | 2026-04-01 | Major expansion: security/redaction layer, shared data module, REST API, plugin-based collectors, tiered output, static HTML export, derived insights, diff-against-previous-scan |

## Summary

A local-only web dashboard and REST API that inspects the developer
environment — Python runtimes, PATH health, virtualenvs, git state,
system resources, network/proxy, container/CI detection, and security
posture. Presents the data in a navigable, filterable, searchable
interface with pass/warn/fail status badges, collapsible sections,
timestamps, and diff-against-previous-scan capability.

Built with FastAPI + Uvicorn (backend), Jinja2 templates + htmx +
Alpine.js (frontend), and Pico CSS (styling). Data collection uses a
**plugin-based collector system** in a **shared module**
(`scripts/_env_collectors/`) so both the CLI (`env_inspect.py`) and the
web dashboard consume identical data. A **redaction layer** strips
tokens, SSH keys, cloud credentials, cookies, auth headers, `.env`
secrets, and optionally usernames/hostnames before any data reaches
the UI or an export.

Lives in `tools/dev-tools/env_dashboard/` outside the distributed
package.

## Origin

- [Exploration 001: Environment inspection web dashboard](../explorations/001-env-inspect-web-dashboard.md)

## Proposed Architecture

```
┌──────────────┐      ┌──────────────┐     ┌──────────────────────┐
│  Browser     │─────▶│  Uvicorn     │────▶│  FastAPI app          │
│  (htmx +     │◀─────│  127.0.0.1   │◀────│  routes.py (HTML)     │
│   Alpine)    │ HTML │  :8000       │     │  api.py    (JSON)     │
└──────────────┘      └──────────────┘     └────────┬─────────────┘
                                                    │
                                           ┌────────▼─────────────┐
                                           │  collector.py         │
                                           │  (cache, orchestrate) │
                                           └────────┬─────────────┘
                                                    │
                                           ┌────────▼─────────────┐
                                           │  redact.py            │
                                           │  (strip secrets)      │
                                           └────────┬─────────────┘
                                                    │
                                           ┌────────▼─────────────┐
                                           │  scripts/_env_collectors/  │
                                           │  (plugin-based data)  │
                                           │  ├─ system.py         │
                                           │  ├─ runtimes.py       │
                                           │  ├─ path_analysis.py  │
                                           │  ├─ git_info.py       │
                                           │  ├─ network.py        │
                                           │  ├─ security.py       │
                                           │  └─ ...               │
                                           └──────────────────────┘
```

**Request flow:**

1. Browser requests a page (htmx partial) or API endpoint (JSON).
2. Uvicorn routes to FastAPI: `routes.py` serves HTML, `api.py` serves
   JSON.
3. `collector.py` orchestrates plugin collectors, applies timeouts and
   error isolation per section, caches results.
4. `redact.py` strips sensitive data before it reaches the response.
5. Response is either a rendered Jinja2 template (HTML) or JSON.

**Data flow:**

- All data originates from plugin collectors in
  `scripts/_env_collectors/`.
- `gather_env_info()` (in `scripts/_env_collectors/__init__.py`) is the
  single entry point — used by both the CLI and the web dashboard.
- `collector.py` is a thin adapter: calls `gather_env_info()`, caches
  results, and reshapes data for template or API consumption.
- `redact.py` applies secret-stripping rules before data is rendered
  or serialised.
- No database. Scan results are cached in memory with timestamps. The
  dashboard stores one previous scan for diff comparison.

## Shared Data Module: `scripts/_env_collectors/`

### Why extract

The current `gather_env_info()` in `scripts/env_inspect.py` is a
monolithic function calling ~15 private `_*` functions. Both the CLI
and web dashboard need the same data. Duplicating the collection logic
is a maintenance hazard. Extracting to a shared module lets both
consumers import the same code.

### Design

```
scripts/
├── _env_collectors/           ← NEW: shared data-collection module
│   ├── __init__.py            ← gather_env_info(), registry, tier logic
│   ├── _base.py               ← BaseCollector ABC, timeout/error helpers
│   ├── system.py              ← OS, arch, hostname, shell, cwd, privilege
│   ├── runtimes.py            ← Python version, installations, compilers
│   ├── path_analysis.py       ← PATH dirs, duplicates, dead entries, ordering
│   ├── project.py             ← Repo detection, lockfiles, build/test tools
│   ├── git_info.py            ← Git version, dirty state, remote URLs
│   ├── venv.py                ← Virtualenv detection, mismatch, Hatch envs
│   ├── packages.py            ← Installed packages, outdated, duplicates
│   ├── network.py             ← DNS, proxy, outbound summary
│   ├── filesystem.py          ← Writable dirs, disk space, mount info
│   ├── security.py            ← Secret scan, permission warnings, insecure PATH
│   ├── container.py           ← Docker/Podman/CI/WSL/cloud detection
│   └── insights.py            ← Derived warnings and recommendations
├── env_inspect.py             ← CLI (imports from _env_collectors)
└── ...
```

Each collector is a class inheriting from `BaseCollector`:

```python
class BaseCollector(ABC):
    name: str           # Section key ("system", "runtimes", etc.)
    tier: Tier          # MINIMAL, STANDARD, FULL
    timeout: float      # Per-collector timeout in seconds

    @abstractmethod
    def collect(self) -> dict: ...
```

`gather_env_info(tier=Tier.STANDARD)` discovers and runs all registered
collectors, applies timeouts, isolates errors per section, and returns
a stable dict schema.

### Migration path

1. Create `scripts/_env_collectors/` with the new plugin structure.
2. Move data-collection logic from `env_inspect.py` private functions
   into the appropriate collector modules.
3. Update `env_inspect.py` to import from `_env_collectors` — its CLI
   interface and output formatting stay unchanged.
4. The web dashboard's `collector.py` imports from `_env_collectors`
   directly.

## Redaction Layer

### Threat model

The dashboard displays environment state. Environment variables, git
remote URLs, PATH entries, and system info can contain:

- **API tokens** (GitHub, AWS, GCP, Azure, npm, PyPI, etc.)
- **SSH private key paths** (and occasionally key contents in env vars)
- **Cloud credentials** (AWS_SECRET_ACCESS_KEY, GOOGLE_APPLICATION_CREDENTIALS, etc.)
- **Cookies and session tokens**
- **Auth headers** (Authorization, Bearer tokens)
- **`.env` file secrets** loaded into the environment
- **Usernames and hostnames** (PII concern if exporting/sharing)
- **Database connection strings** with embedded passwords
- **Remote URLs with credentials** (`https://user:token@github.com/...`)

### Redaction rules

`redact.py` applies these rules:

| Category | Pattern examples | Redacted to |
| :------- | :--------------- | :---------- |
| Known secret env vars | `*_TOKEN`, `*_SECRET`, `*_KEY`, `*_PASSWORD`, `*_CREDENTIAL`, `AWS_*`, `GITHUB_TOKEN`, `NPM_TOKEN`, `PYPI_TOKEN` | `[REDACTED]` |
| High-entropy strings | Base64-like values > 20 chars in env vars | `[REDACTED]` |
| URLs with credentials | `https://user:pass@host/...` | `https://[REDACTED]@host/...` |
| SSH key paths | `~/.ssh/id_*` contents if exposed | `[REDACTED]` |
| Cookie values | `Set-Cookie`, `Cookie` header patterns | `[REDACTED]` |
| Auth headers | `Authorization: Bearer ...` | `Authorization: [REDACTED]` |
| Usernames (optional) | `$USER`, `$USERNAME`, `$LOGNAME` | `[REDACTED]` (opt-in) |
| Hostnames (optional) | `$HOSTNAME`, hostname in URLs | `[REDACTED]` (opt-in) |
| IP addresses (optional) | IPv4/IPv6 in network info | `[REDACTED]` (opt-in) |

### Redaction modes

```python
class RedactLevel(Enum):
    NONE = "none"           # No redaction (local-only viewing)
    SECRETS = "secrets"     # Strip tokens, keys, passwords (DEFAULT)
    PII = "pii"            # Secrets + usernames/hostnames/IPs
    PARANOID = "paranoid"   # PII + high-entropy strings + all env values
```

The UI provides a "Redact secrets" toggle that switches between `NONE`
and `SECRETS`. Exports default to `PII` level. The API accepts a
`?redact=` query parameter.

### Design principles

- **Redaction is applied server-side** — the browser never receives
  unredacted data for `SECRETS`/`PII`/`PARANOID` modes.
- **Toggle only disables redaction when viewing locally** — the `NONE`
  mode is available in the UI but exports always apply at least
  `SECRETS` level.
- **Allowlist approach for env vars** — only known-safe env vars
  (`PATH`, `HOME`, `SHELL`, `LANG`, `TERM`, etc.) pass through
  unredacted. Unknown env vars show name only, value redacted.
- **Deny-by-default for exports** — static HTML and JSON exports use
  `PII` redaction by default. Users must explicitly opt in to lower
  redaction levels.

## Output Tiers

Data collection and display are organised into four tiers:

### Minimal

Quick snapshot — safe to share, fast to collect.

- OS, arch, hostname, username, shell, cwd
- PATH summary (entry count, duplicates, dead entries)
- Runtimes (Python version, Node version, etc.)
- Package managers detected (pip, hatch, uv, conda, etc.)
- Git/project summary (repo detected, branch, clean/dirty)

### Standard (default)

Adds diagnostics and warnings.

- All of Minimal
- Env vars summary (names only, values redacted by default)
- Disk/memory/network summary
- Container/CI/cloud detection
- Tool versions (all detected build tools)
- Warnings panel (all derived insights)
- Virtualenv status and mismatch detection

### Full

Complete inventory — verbose, may be slow.

- All of Standard
- Package inventories (full list with versions/locations)
- Full env var dump (values visible, secrets redacted)
- Loaded config files (pyproject.toml, .tool-versions, etc.)
- Network interface details
- Mount/filesystem details
- Service/process details

### Redacted Full (Full tier + PII redaction)

Not a separate tier — this is the Full tier with `PII` redaction level
applied. The tier (Minimal/Standard/Full) and redaction level
(NONE/SECRETS/PII/PARANOID) are independent axes. "Redacted Full" is
shorthand for the combination used by default for exports:

- All of Full
- Usernames masked (PII level)
- Hostnames masked (PII level)
- IP addresses masked (PII level)
- Env var secrets stripped (SECRETS level, included in PII)
- Tokens/keys stripped
- Remote URLs with credentials stripped
- Database connection strings stripped

This is the **default combination for exports**.

## Dashboard Structure

### Top Summary Bar

| Field | Source |
| :---- | :----- |
| OS | `system.os` |
| Hostname | `system.hostname` (redactable) |
| User | `system.username` (redactable) |
| Shell | `system.shell` |
| Python version | `runtimes.python.version` |
| Git repo detected | `git.repo_detected` |
| Container/CI detected | `container.detected` |
| Warnings count | `insights.warnings_count` |
| Scan timestamp | `meta.timestamp` |

### Warnings Panel

High-value derived insights computed from collected data:

- Virtualenv not active
- Wrong Python version (doesn't satisfy `requires-python`)
- PATH has dead entries
- PATH ordering means wrong python/node/gcc is being used
- Git working tree dirty; builds may be non-reproducible
- Secrets found in environment variables
- Lockfile mismatch (requirements.txt vs installed)
- Missing compiler/native build tools
- `/tmp` not writable
- Running under WSL; path behavior differs from Windows native
- CI environment detected; avoid interactive prompts
- Container detected with memory cap
- DNS works but outbound HTTPS blocked
- Clock skew may break certificates or builds
- Disk nearly full; installs/builds may fail
- Project expects one package manager but another is active
- Node/Python version mismatch with version file
- X11/Wayland unavailable; GUI tests will fail
- System locale may affect sorting/parsing
- Cloud credentials found but region not set
- Unsupported Python/Node/tool versions

### Sections

| Section | Key data | Tier |
| :------ | :------- | :--- |
| **System** | OS, kernel, arch, shell, terminal, privilege level, locale | Minimal |
| **Runtimes** | Python versions/installations, Node, compilers, version managers | Minimal |
| **PATH Analysis** | All entries, duplicates, dead entries, ordering issues, executable counts | Minimal |
| **Project** | Repo root, lockfiles, build/test/lint tool detection, config files | Minimal |
| **Git** | Version, branch, dirty state, remote URLs (redacted), stash count | Minimal |
| **Virtual Environments** | Active venv, Hatch envs, mismatch detection, interpreter path | Standard |
| **Packages** | Installed packages by location, outdated, duplicates, entry points | Full |
| **Network** | DNS, proxy, outbound summary, interface details | Standard |
| **Filesystem** | Writable temp/cache dirs, disk space, mount info | Standard |
| **Security** | Secret exposure scan, insecure PATH, permission warnings | Standard |
| **Container/CI** | Docker/Podman/CI/WSL/cloud detection, resource limits | Standard |
| **Raw JSON** | Full scan output as formatted JSON | Full |

### Controls

| Control | Behaviour |
| :------ | :-------- |
| Search box | Client-side filter across all visible sections (Alpine.js) |
| Filter by section | Show/hide individual sections |
| Hide/show empty fields | Toggle display of fields with no value |
| Redact secrets toggle | Switch between `NONE` and `SECRETS` redaction (local viewing only) |
| Copy field value | Clipboard copy for any field value |
| Export JSON | Download full scan as JSON (redacted by default) |
| Export HTML | Download static HTML report (redacted by default) |
| Refresh scan | Re-run all collectors, update dashboard |
| Diff against previous | Compare current scan to previous (highlights changes) |

## API Endpoints

All endpoints return JSON. Redaction level is controlled via the
`?redact=` query parameter (default: `secrets`).

| Method | Path | Description |
| :----- | :--- | :---------- |
| `GET` | `/api/summary` | Top summary bar data only |
| `GET` | `/api/report` | Full scan report (all sections, current tier) |
| `GET` | `/api/warnings` | Warnings panel data only |
| `GET` | `/api/sections/:name` | Single section by name |
| `POST` | `/api/scan` | Trigger a fresh scan (accepts `?tier=` and `?deep=true`) |
| `GET` | `/api/export.json` | Full scan as downloadable JSON (PII-redacted by default) |

`POST /api/scan` does not mutate state — it triggers a read-only
environment scan and caches the result. The "POST" method is used
because it has a side effect (cache invalidation and re-collection)
and may be slow.

## Backend Features

### Plugin-based collectors

Each section is collected by an independent plugin class. New sections
are added by creating a new collector in `scripts/_env_collectors/` —
the registry auto-discovers them. No changes to the dashboard needed.

### Timeouts for slow checks

Each collector has a configurable `timeout` (default: 10s). If a
collector exceeds its timeout, the section returns a partial result
with an error flag. The dashboard shows a timeout warning badge.

### Error isolation per section

A failing collector does not crash the scan. Each collector runs in a
try/except wrapper. Errors are captured in the section result as
`{"error": "...", "partial": true}`. The UI renders an error badge
with the message.

### Redaction layer

See [Redaction Layer](#redaction-layer) above. Applied server-side
before data reaches templates or JSON serialisation.

### Stable schema

The collector output follows a versioned schema:

```json
{
  "schema_version": "1.0",
  "meta": { "timestamp": "...", "tier": "standard", "redact_level": "secrets" },
  "summary": { ... },
  "warnings": [ ... ],
  "sections": {
    "system": { ... },
    "runtimes": { ... },
    ...
  }
}
```

Schema changes increment the version. The dashboard and CLI both
validate against the schema version they expect.

### Cached results

Scan results are cached in memory with a timestamp. Subsequent
requests within a configurable TTL (default: 30s) return cached data.
`POST /api/scan` forces cache invalidation.

### Optional deep scan mode

`?deep=true` on `POST /api/scan` enables expensive checks: outdated
package detection, full network probe, security audit. Default scans
skip these for speed.

## Static HTML Export

### Purpose

Generate a standalone `.html` file containing the full scan report
for sharing, attaching to issues, or archiving. This is a **secondary
export feature**, not the primary interface.

### Security constraints for export

- **Redacted by default.** Exports use `PII` redaction level unless
  the user explicitly opts for a lower level via the API
  (`?redact=secrets` or `?redact=none`).
- **No JavaScript in export.** The exported HTML is a static snapshot —
  no scripts, no htmx, no Alpine.js. This prevents XSS if the file is
  opened in an untrusted context.
- **Inline CSS only.** All styles are inlined into a `<style>` block.
  No external resource references.
- **CSP meta tag.** The export includes
  `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">`
  to block any script execution even if one were injected.
- **No external URLs.** No CDN links, no font imports, no tracking pixels.
- **Sanitised values.** All values are HTML-escaped (Jinja2 autoescape).
- **Timestamp and redaction level stamped.** The export header clearly
  shows when the scan was taken and what redaction level was applied.
- **Warning banner.** If redaction is below `PII`, the export includes
  a visible warning: "This report may contain sensitive information."

### Implementation

The export endpoint (`GET /api/export.html` or the UI "Export HTML"
button) renders the same Jinja2 templates used for the dashboard but
into a single self-contained HTML string (base template + all section
partials inlined). The response sets `Content-Disposition: attachment;
filename="env-report-{timestamp}.html"`.

## Repo Layout

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
        ├── app.py                ← FastAPI app factory + Uvicorn entrypoint
        ├── collector.py          ← Wraps _env_collectors, caching, tier selection
        ├── redact.py             ← Dashboard-specific redaction wiring
        ├── routes.py             ← HTML route handlers: full pages + htmx partials
        ├── api.py                ← JSON API route handlers
        ├── export.py             ← Static HTML export logic
        ├── static/
        │   ├── css/
        │   │   ├── pico.min.css  ← Vendored Pico CSS minified (~10 KB, production)
        │   │   └── style.min.css ← Custom properties minified (production)
        │   ├── js/
        │   │   ├── htmx.min.js   ← Vendored minified (~14 KB, production)
        │   │   └── alpine.min.js ← Vendored minified (~15 KB, production)
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
        │   ├── base.html         ← Layout shell: nav, footer, <script> tags
        │   ├── index.html        ← Dashboard home: summary + section cards
        │   ├── export.html       ← Self-contained export template (no JS)
        │   └── partials/         ← One per section, htmx-swappable
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
        └── README.md
```

**New top-level directory:** `tools/` — for multi-file developer tools
that don't belong in `scripts/` (single-file CLIs) or `src/` (distributed
package). See [ADR 041](../adr/041-env-inspect-web-dashboard.md).

**New shared module:** `scripts/_env_collectors/` — underscore prefix
follows the existing convention for shared script modules (`_colors.py`,
`_ui.py`, etc.). This is a package (directory with `__init__.py`) rather
than a single file because the collector count warrants separation.

## Components / Modules

| Component | Responsibility | Key interfaces |
| :-------- | :------------- | :------------- |
| `_env_collectors/__init__.py` | Registry, `gather_env_info(tier, redact_level)`, schema | `gather_env_info() → dict` |
| `_env_collectors/_base.py` | Base class, timeout wrapper, error isolation | `BaseCollector` ABC |
| `_env_collectors/_redact.py` | Secret-stripping rules, pattern matching | `redact(data, level) → dict` |
| `_env_collectors/*.py` | One collector per section | `collect() → dict` |
| `_env_collectors/insights.py` | Derived warnings from cross-section analysis | `derive_insights(data) → list[Warning]` |
| `app.py` | Create FastAPI app, mount static files, configure Jinja2, start Uvicorn | `create_app() → FastAPI`, `main()` |
| `collector.py` | Orchestrate `gather_env_info()`, caching, tier selection | `get_report(tier, redact) → dict` |
| `api.py` | JSON API endpoints | `GET /api/*`, `POST /api/scan` |
| `routes.py` | HTML route handlers for pages and htmx partials | `GET /`, `GET /section/{name}` |
| `export.py` | Static HTML export rendering | `render_export(data, redact) → str` |
| `base.html` | Layout shell with nav sidebar, controls, script loading | Jinja2 `{% block content %}` |
| `index.html` | Dashboard home — summary bar + section cards with `hx-get` | Extends `base.html` |
| `export.html` | Self-contained export template — no JS, inline CSS, CSP | Standalone Jinja2 template |
| `partials/*.html` | One template per section — htmx-friendly HTML fragments | Standalone renderable fragments |
| `style.css` | Dashboard-specific styles, CSS custom properties for theming | `--color-pass`, `--color-warn`, `--color-fail` tokens |

## Tooling Impact

### New dependencies

Add to `pyproject.toml` under `[project.optional-dependencies]`:

```toml
dashboard = [
    "fastapi[standard]",  # Includes uvicorn, jinja2, python-multipart
]
```

Jinja2 is already a transitive dep of MkDocs but should be declared
explicitly via `fastapi[standard]`.

### Config changes

| File | Change |
| :--- | :----- |
| `pyproject.toml` | Add `dashboard` optional-dependency group |
| `Taskfile.yml` | Add `dashboard:serve` task |
| `.gitignore` | No change needed (no build artifacts) |
| `.pre-commit-config.yaml` | Extend Prettier to cover `*.css` files (low-cost) |

### Hatch environment

```toml
[tool.hatch.envs.dashboard]
features = ["dashboard"]

[tool.hatch.envs.dashboard.scripts]
serve = "python -m tools.dev_tools.env_dashboard.app"
```

### Taskfile shortcut

```yaml
dashboard:serve:
  desc: Start the env_dashboard web UI
  cmds:
    - hatch run dashboard:serve
```

### CI/CD impact

None. This is a local-only tool. No CI workflow needed. No deployment.

## Workflow / UX

### Starting the dashboard

```bash
task dashboard:serve
# or
hatch run dashboard:serve
# or directly
python -m tools.dev_tools.env_dashboard.app
```

Opens `http://127.0.0.1:8000` in the default browser (or prints the URL).

### Using the dashboard

1. **Landing page** shows a top summary bar (OS, Python, git, warnings
   count, scan timestamp) and a grid of section cards with pass/warn/fail
   badges.
2. **Warnings panel** is always visible at the top — lists all derived
   insights with severity badges and actionable descriptions.
3. Each section card has a **collapsible** body loaded via htmx
   (`hx-get="/section/packages"` → swaps in `partials/packages.html`).
4. **Slow sections** (outdated packages, network probes) show a loading
   spinner and load asynchronously via `hx-trigger="load"`.
5. **Search box** (Alpine.js `x-model`) provides instant client-side
   filtering across all visible sections.
6. **Hide/show empty fields** toggle removes fields with no value from
   the display.
7. **Redact secrets toggle** switches between showing and hiding
   sensitive values (local viewing only — exports always redact).
8. **Copy field value** button on each field copies the value to clipboard.
9. **Raw JSON viewer** shows the full scan output as formatted,
   syntax-highlighted JSON.
10. **Refresh scan** button re-runs all collectors and updates the
    dashboard without full page reload.
11. **Timestamps** shown on the summary bar and per-section (when that
    section was last collected).
12. **Diff against previous scan** highlights what changed since the
    last scan (new warnings, changed values, resolved issues).
13. **Export** dropdown offers JSON and static HTML download, both
    redacted by default.

### Stopping

`Ctrl+C` in the terminal. No cleanup needed — no state, no database.

## Open Design Questions

- [x] `tools/` vs `devtools/` directory name — **Decided: `tools/dev-tools/`**
- [x] FastAPI vs Starlette vs stdlib — **Decided: FastAPI + Uvicorn**
- [x] Should `gather_env_info()` be extracted to a shared module? —
  **Decided: Yes.** Extract to `scripts/_env_collectors/` as a
  plugin-based collector system.
- [x] Static HTML export mode — **Decided: Yes.** Secondary export
  feature with PII-level redaction by default. No JavaScript in export.
- [ ] Chart.js usage — **Deferred.** Start without Chart.js. Add later
  only if specific visualisations prove more useful than tables. The
  65 KB cost needs to be justified by real UX value.
- [ ] Exact allowlist for "safe" env vars — needs review of common
  platforms (Linux, macOS, Windows) to build a comprehensive list.
- [ ] Deep scan timeout budget — total time limit for `?deep=true`
  scans to prevent runaway collection.

## Constraints

- **Local-only.** Bind to `127.0.0.1` only. No authentication, no TLS,
  no CORS. See security section in exploration.
- **Read-only.** `POST /api/scan` triggers collection (a read operation)
  but does not mutate system state. No write endpoints. No forms that
  submit.
- **No npm / Node.js.** All JS vendored as single files. No build step.
- **Python 3.11+** — matches project minimum.
- **Exports are redacted by default.** Users must explicitly opt in to
  lower redaction levels.
- **No secrets in the browser.** When redaction is `SECRETS` or higher,
  the server never sends unredacted values to the client.
- **Jinja2 autoescape=True** — non-negotiable for safe rendering of
  arbitrary env-var values.

## References

- [Exploration 001: Environment inspection web dashboard](../explorations/001-env-inspect-web-dashboard.md)
- [ADR 041: Environment inspection web dashboard](../adr/041-env-inspect-web-dashboard.md)
- [Implementation Plan 001: Environment inspection web dashboard](../implementation-plans/001-env-inspect-web-dashboard.md)
- [scripts/env_inspect.py](../../scripts/env_inspect.py)
- [ADR 036: Diagnostic tooling strategy](../adr/036-diagnostic-tooling-strategy.md)
