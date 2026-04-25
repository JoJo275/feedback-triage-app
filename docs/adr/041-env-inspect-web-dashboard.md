# ADR 041: Environment Inspection Web Dashboard

## Status

Accepted — Revised (v2)

## Context

`scripts/env_inspect.py` provides a comprehensive CLI dashboard covering
Python info, git status, venv detection, installed packages, entry points,
build tools, PATH inspection, Python installations, and system environment.
The output is rich but confined to the terminal — long tables scroll off
screen, cross-referencing sections requires scrolling, and data can't be
filtered, searched, or bookmarked interactively.

[Exploration 001](../explorations/001-env-inspect-web-dashboard.md)
evaluated five alternatives (web dashboard, full SPA, Textual TUI, static
HTML export, do nothing) and concluded that a local web dashboard adds
genuine value for onboarding and debugging while staying lightweight.

[Blueprint 001](../blueprints/001-env-inspect-web-dashboard.md) defined
the structural design: FastAPI + Uvicorn backend, Jinja2 + htmx + Alpine.js
frontend, Pico CSS styling, REST API, plugin-based collectors, redaction
layer, tiered output, static HTML export, and derived insights engine.

The v2 revision expands scope based on three requirements:

1. **Security:** Environment data contains tokens, SSH keys, cloud
   credentials, cookies, auth headers, and `.env` secrets. Any display
   or export must strip these by default.
2. **Shared data module:** Both CLI and dashboard need the same data.
   Extracting `gather_env_info()` to a shared module eliminates
   duplication and enables independent collector development.
3. **Richer diagnostics:** Beyond raw facts, developers need computed
   insights ("Python version doesn't satisfy constraint", "PATH has dead
   entries"), tiered output levels, an API for programmatic access, and
   a static HTML export for sharing.

This ADR locks in seven decisions.

## Decision

### 1. Build a local-only web dashboard and REST API

Serve a read-only web dashboard at `http://127.0.0.1:8000` with a JSON
API (`/api/summary`, `/api/report`, `/api/warnings`,
`/api/sections/:name`, `POST /api/scan`, `/api/export.json`). The
dashboard presents environment data with pass/warn/fail badges,
collapsible sections, search, timestamps, and diff-against-previous-scan.

### 2. Introduce `tools/dev-tools/` for multi-file developer tools

`scripts/` is for single-file CLI utilities. The dashboard is a multi-file
application with templates, static assets, and internal structure. A new
`tools/dev-tools/env-dashboard/` directory clearly separates it. The path
is explicit — important for a template repo where clarity beats brevity.

This also establishes a convention: future multi-file developer tools
go under `tools/dev-tools/` in their own subdirectory.

### 3. Extract `gather_env_info()` to `scripts/_env_collectors/`

The current monolithic `gather_env_info()` in `env_inspect.py` is
extracted into a plugin-based collector system:

- `scripts/_env_collectors/__init__.py` — registry, `gather_env_info(tier, redact_level)`, schema
- `scripts/_env_collectors/_base.py` — `BaseCollector` ABC with timeout/error isolation
- `scripts/_env_collectors/_redact.py` — `RedactLevel` enum, pattern-based redaction
- One collector per section: `system.py`, `runtimes.py`, `path_analysis.py`, etc.

The CLI (`env_inspect.py`) imports from `_env_collectors`. The dashboard
imports from `_env_collectors`. One source of truth.

### 4. Implement a redaction layer

`_env_collectors/_redact.py` provides four redaction levels:

| Level | Strips |
| :---- | :----- |
| `NONE` | Nothing (local viewing only) |
| `SECRETS` | Tokens, keys, passwords, DB URLs, auth headers (default) |
| `PII` | Secrets + usernames, hostnames, IPs (default for exports) |
| `PARANOID` | PII + high-entropy strings + all env var values |

Redaction is applied **server-side** before data reaches templates or
JSON serialisation. Exports default to `PII`. The UI redact toggle
switches between `NONE` and `SECRETS` for local viewing only.

### 5. Support tiered output

Collectors declare their tier (Minimal, Standard, Full).
`gather_env_info(tier=...)` runs only collectors at or below the
requested tier. This balances speed vs. detail.

### 6. Technology stack

| Layer | Tool | Rationale |
| :---- | :--- | :-------- |
| Backend — framework | FastAPI | Async routing, Jinja2 integration, auto OpenAPI docs |
| Backend — server | Uvicorn | Standard FastAPI server; `--reload` for dev; lightweight |
| Backend — templating | Jinja2 | Already a transitive dep; partials map to htmx endpoints |
| Frontend — interactivity | htmx (vendored) | SPA-like UX, zero JS framework, ~14 KB |
| Frontend — client state | Alpine.js (vendored) | Search/filter, toggles, tabs; ~15 KB; declarative HTML |
| Frontend — styling | Pico CSS + custom CSS | Classless base + project-specific overrides |

All JS vendored as single files in `static/js/`. No npm, no build step,
no CDN dependency.

**Chart.js deferred.** 65 KB for a few pie charts isn't justified yet.
Add later if specific visualisations prove more useful than tables.

### 7. Static HTML export with strict security

The dashboard provides a secondary export feature: download a
self-contained `.html` file for sharing or attaching to issues.

Security constraints:
- No JavaScript in export (pure HTML + inline CSS)
- CSP meta tag: `default-src 'none'; style-src 'unsafe-inline'`
- PII-level redaction by default
- No external URLs (no CDN, no fonts, no tracking)
- HTML-escaped values (Jinja2 autoescape)
- Timestamp and redaction level stamped in header
- Warning banner if redaction < PII
- `Content-Disposition: attachment` header

### 8. Dependencies

Add a `dashboard` optional-dependency group in `pyproject.toml`:

```toml
[project.optional-dependencies]
dashboard = [
    "fastapi[standard]",
]
```

Create a dedicated Hatch environment:

```toml
[tool.hatch.envs.dashboard]
features = ["dashboard"]
```

### 9. Security constraints

- Bind to `127.0.0.1` only — never `0.0.0.0`.
- `Jinja2 autoescape=True` — non-negotiable.
- Read-only — `POST /api/scan` triggers collection but doesn't mutate
  system state.
- Redaction active by default (`SECRETS` level for viewing, `PII` for
  exports).
- No secrets reach the browser at `SECRETS` level or above.
- Static HTML exports contain no JavaScript.

## Alternatives Considered

### Full SPA (React/Vue/Svelte + FastAPI)

Maximum flexibility and rich interactivity.

**Rejected because:** Disproportionate complexity — adds Node.js, npm,
bundler, and a JS build step to a Python-focused project. Template users
who don't want the dashboard still inherit the JS toolchain.

### Textual TUI

Terminal-based interactive dashboard using the Textual framework.

**Rejected because:** Terminal-only — can't bookmark, can't share a URL,
limited layout flexibility vs. HTML+CSS. Textual is a ~5 MB dependency.
Worth considering as a complementary option but doesn't replace the web
dashboard.

### Static HTML export only

Generate a standalone `.html` file with all data inlined.

**Adopted as secondary feature.** Useful for sharing but not as the
primary interface (no interactivity). Security constraints for export
are documented in Decision 7.

### Do nothing

Keep the CLI as-is.

**Rejected because:** The CLI works but misses UX improvements for
onboarding and debugging. It can't safely export data (no redaction),
compute cross-section insights, or provide a navigable UI.

### Keep it in `scripts/`

Put the dashboard files in `scripts/env_dashboard/`.

**Rejected because:** `scripts/` convention is single-file CLIs. A
multi-file application with templates and static assets doesn't fit.

### Keep `gather_env_info()` in `env_inspect.py`

Have the dashboard import directly from `scripts/env_inspect.py`.

**Rejected because:** The monolithic function has ~15 private `_*`
helpers. Extracting to a shared module enables plugin-based development,
tiered collection, per-collector timeouts, and independent testing.

## Consequences

### Positive

- Developers get a navigable, filterable view of their environment —
  faster debugging and easier onboarding.
- **Redaction layer prevents secret leakage** in exports and shared
  reports.
- **Shared collector module** eliminates code duplication between CLI
  and dashboard, and enables plugin-based extension.
- **REST API** enables programmatic consumption by CI/editors/scripts.
- **Derived insights** provide actionable diagnostics, not just raw data.
- Template users can delete `tools/dev-tools/env-dashboard/` cleanly
  without affecting the core package or scripts.
- Establishes a reusable `tools/dev-tools/` convention.
- No npm/Node.js dependency — all JS vendored, no build step.

### Negative

- Larger scope than v1 — more files, more tests, more documentation.
- New optional dependency group (`fastapi[standard]`).
- Refactoring `env_inspect.py` to use `_env_collectors` touches existing
  code (mitigation: keep public interface identical).
- Another subsystem to maintain. The insights engine adds cross-section
  logic which is inherently more complex.

### Neutral

- The CLI (`env_inspect.py`) continues to work identically.
- CI is unaffected — no new workflows, no new gate checks.

### Mitigations

- **Maintenance:** Plugin architecture means each collector is
  independent. Changes to one section don't affect others.
- **Scope creep:** Feature list is frozen at v2 design. Unlisted
  features require a new blueprint.
- **Secret leakage:** Redaction is Phase 1 of implementation —
  built before any UI or export ships.
- **Refactor risk:** `env_inspect.py` keeps its public interface.
  The delegation to `_env_collectors` is internal.

## Implementation

Planned file locations (not yet created):

- `scripts/_env_collectors/` — Shared data-collection module
- `tools/dev-tools/env-dashboard/app.py` — FastAPI app factory
- `tools/dev-tools/env-dashboard/collector.py` — Caching adapter
- `tools/dev-tools/env-dashboard/api.py` — JSON API endpoints
- `tools/dev-tools/env-dashboard/routes.py` — HTML route handlers
- `tools/dev-tools/env-dashboard/export.py` — Static HTML export
- `tools/dev-tools/env-dashboard/templates/` — Jinja2 templates
- `tools/dev-tools/env-dashboard/static/` — CSS, JS, images
- [pyproject.toml](../../pyproject.toml) — `dashboard` dependency group and Hatch env
- [Taskfile.yml](../../Taskfile.yml) — `dashboard:serve` task

## References

- [Exploration 001: Environment inspection web dashboard](../explorations/001-env-inspect-web-dashboard.md)
- [Blueprint 001: Environment inspection web dashboard](../blueprints/001-env-inspect-web-dashboard.md)
- [Implementation Plan 001: Environment inspection web dashboard](../implementation-plans/001-env-inspect-web-dashboard.md)
- [ADR 036: Diagnostic tooling strategy](../adr/036-diagnostic-tooling-strategy.md)
- [ADR 031: Script conventions](../adr/031-script-conventions.md)
- [scripts/env_inspect.py](../../scripts/env_inspect.py)
