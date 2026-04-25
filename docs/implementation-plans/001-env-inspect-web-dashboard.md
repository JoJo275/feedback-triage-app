# Implementation Plan 001: Environment Inspection Web Dashboard

## Status

Draft — Revised (v2)

## Revision History

| Version | Date | Summary |
| :------ | :--- | :------ |
| v1 | — | Initial plan: 6 phases, 42 tasks, basic dashboard |
| v2 | 2026-04-01 | Restructured: 8 phases, expanded scope — shared collector module, redaction layer, REST API, tiered output, derived insights, static HTML export, diff-against-previous-scan |

## Summary

Build the local environment inspection web dashboard and REST API
described in [Blueprint 001](../blueprints/001-env-inspect-web-dashboard.md)
and approved in [ADR 041](../adr/041-env-inspect-web-dashboard.md).

The v2 plan reflects the expanded scope: extract data collection into a
shared plugin-based module (`scripts/_env_collectors/`), implement a
redaction layer for secret stripping, build both HTML and JSON endpoints,
support tiered output, compute derived insights, and provide static HTML
export with strict security controls.

## Origin

- [Blueprint 001: Environment inspection web dashboard](../blueprints/001-env-inspect-web-dashboard.md)
- [ADR 041: Environment inspection web dashboard](../adr/041-env-inspect-web-dashboard.md)

## Prerequisites

- [x] Exploration concluded — Proceed
- [x] Blueprint accepted (v2)
- [x] ADR accepted
- [ ] `fastapi[standard]` available on PyPI (it is — just needs adding)

## Task Order

### Phase 1: Shared Collector Module and Redaction Layer

Extract `gather_env_info()` into a shared, plugin-based module. This is
the foundation — both the CLI and dashboard depend on it. The redaction
layer must be in place before any data reaches a UI or export.

| # | Task | Files changed | Notes |
|---|------|---------------|-------|
| 1 | Create `scripts/_env_collectors/` package | `scripts/_env_collectors/__init__.py` | `gather_env_info(tier, redact_level)`, collector registry, schema version |
| 2 | Create `_base.py` — BaseCollector ABC | `scripts/_env_collectors/_base.py` | `name`, `tier`, `timeout`, `collect()` method, timeout wrapper, error isolation |
| 3 | Create `_redact.py` — redaction layer | `scripts/_env_collectors/_redact.py` | `RedactLevel` enum, pattern-based redaction rules, env var allowlist, URL credential stripping, high-entropy detection |
| 4 | Create `system.py` collector | `scripts/_env_collectors/system.py` | OS, arch, hostname, shell, cwd, privilege, locale (Minimal tier) |
| 5 | Create `runtimes.py` collector | `scripts/_env_collectors/runtimes.py` | Python versions/installations, compilers, version managers (Minimal tier) |
| 6 | Create `path_analysis.py` collector | `scripts/_env_collectors/path_analysis.py` | PATH dirs, duplicates, dead entries, ordering, exec counts (Minimal tier) |
| 7 | Create `project.py` collector | `scripts/_env_collectors/project.py` | Repo root, lockfiles, build/test/lint tools, config files (Minimal tier) |
| 8 | Create `git_info.py` collector | `scripts/_env_collectors/git_info.py` | Git version, branch, dirty state, remote URLs (Minimal tier) |
| 9 | Create `venv.py` collector | `scripts/_env_collectors/venv.py` | Virtualenv detection, Hatch envs, mismatch (Standard tier) |
| 10 | Create `packages.py` collector | `scripts/_env_collectors/packages.py` | Installed packages, outdated, duplicates, entry points (Full tier) |
| 11 | Create `network.py` collector | `scripts/_env_collectors/network.py` | DNS, proxy, outbound summary (Standard tier) |
| 12 | Create `filesystem.py` collector | `scripts/_env_collectors/filesystem.py` | Writable dirs, disk space, mounts (Standard tier) |
| 13 | Create `security.py` collector | `scripts/_env_collectors/security.py` | Secret scan, permissions, insecure PATH (Standard tier) |
| 14 | Create `container.py` collector | `scripts/_env_collectors/container.py` | Docker/CI/WSL/cloud detection, resource limits (Standard tier) |
| 15 | Create `insights.py` collector | `scripts/_env_collectors/insights.py` | Derived warnings from cross-section analysis (Standard tier) |
| 16 | Update `env_inspect.py` to import from `_env_collectors` | `scripts/env_inspect.py` | Replace monolithic `gather_env_info()` with import from shared module. CLI output and flags unchanged. |
| 17 | Verify: `python scripts/env_inspect.py` works identically | — | Regression test: output should match pre-refactor |
| 18 | Verify: `python scripts/env_inspect.py --json` output passes redaction | — | JSON output should redact secrets at `SECRETS` level by default |

### Phase 2: Dashboard Scaffolding and Backend

Set up the directory, dependencies, and a minimal working server.

| # | Task | Files changed | Notes |
|---|------|---------------|-------|
| 19 | Create `tools/dev-tools/env-dashboard/` directory structure | `tools/dev-tools/env-dashboard/__init__.py` | Empty `__init__.py` |
| 20 | Add `dashboard` optional-dependency group | `pyproject.toml` | `fastapi[standard]` under `[project.optional-dependencies]` |
| 21 | Add Hatch `dashboard` environment | `pyproject.toml` | `[tool.hatch.envs.dashboard]` with `features = ["dashboard"]` and `serve` script |
| 22 | Add Taskfile shortcut | `Taskfile.yml` | `dashboard:serve` task |
| 23 | Create `app.py` — FastAPI app factory | `tools/dev-tools/env-dashboard/app.py` | Mount static files, configure Jinja2 (autoescape=True), `if __name__` starts Uvicorn on `127.0.0.1:8000` |
| 24 | Create `collector.py` — caching adapter | `tools/dev-tools/env-dashboard/collector.py` | Import from `_env_collectors`, cache results with TTL, expose `get_report(tier, redact)` |
| 25 | Create `redact.py` — dashboard redaction wiring | `tools/dev-tools/env-dashboard/redact.py` | Thin wrapper connecting `_redact.py` to route-level `?redact=` parameter |
| 26 | Create `routes.py` — HTML route handlers | `tools/dev-tools/env-dashboard/routes.py` | `GET /` (index), `GET /section/{name}` (htmx partial) |
| 27 | Create `api.py` — JSON API route handlers | `tools/dev-tools/env-dashboard/api.py` | `GET /api/summary`, `GET /api/report`, `GET /api/warnings`, `GET /api/sections/:name`, `POST /api/scan`, `GET /api/export.json` |
| 28 | Verify: `hatch run dashboard:serve` starts and returns HTTP 200 | — | Manual smoke test |

### Phase 3: Templates and Static Assets

Build the HTML shell, vendor JS/CSS, and create the index page.

| # | Task | Files changed | Notes |
|---|------|---------------|-------|
| 29 | Vendor Pico CSS into `static/css/pico.min.css` | `tools/.../static/css/pico.min.css` | Download from picocss.com (MIT licence) |
| 30 | Create `style.css` — custom properties and layout | `tools/.../static/css/style.css` | `--color-pass/warn/fail` tokens, dashboard grid, section card styles, badge styles |
| 31 | Vendor htmx into `static/js/htmx.min.js` | `tools/.../static/js/htmx.min.js` | Download from htmx.org (BSD licence) |
| 32 | Vendor Alpine.js into `static/js/alpine.min.js` | `tools/.../static/js/alpine.min.js` | Download from alpinejs.dev (MIT licence) |
| 33 | Create `base.html` — layout shell | `tools/.../templates/base.html` | Nav sidebar, top summary bar, controls bar (search, redact toggle, hide empty, export, refresh), footer, `<script>` tags, `{% block content %}` |
| 34 | Create `index.html` — dashboard home | `tools/.../templates/index.html` | Summary bar + warnings panel + grid of section cards with `hx-get` triggers and pass/warn/fail badges |
| 35 | Create `favicon.svg` | `tools/.../static/img/favicon.svg` | Simple Python-themed SVG |
| 36 | Verify: dashboard loads in browser with styled layout | — | Nav, cards, Pico styles, controls render correctly |

### Phase 4: Section Partials (Core Sections)

Build templates for the highest-value sections first.

| # | Task | Files changed | Notes |
|---|------|---------------|-------|
| 37 | `partials/summary.html` — top summary bar | `tools/.../templates/partials/summary.html` | OS, hostname, user, shell, Python, git, container/CI, warnings count, timestamp |
| 38 | `partials/warnings.html` — warnings panel | `tools/.../templates/partials/warnings.html` | List of derived insights with pass/warn/fail badges |
| 39 | `partials/system.html` — system info | `tools/.../templates/partials/system.html` | OS, kernel, arch, shell, locale, privilege |
| 40 | `partials/runtimes.html` — runtimes | `tools/.../templates/partials/runtimes.html` | Python versions, installations, compilers |
| 41 | `partials/path.html` — PATH analysis | `tools/.../templates/partials/path.html` | Entries, duplicates, dead entries, ordering |
| 42 | `partials/git.html` — Git info | `tools/.../templates/partials/git.html` | Version, branch, dirty state, remotes (redacted) |
| 43 | `partials/venv.html` — virtualenvs | `tools/.../templates/partials/venv.html` | Active venv, Hatch envs, mismatch |
| 44 | Verify: seven core sections load via htmx and display data | — | Manual smoke test |

### Phase 5: Remaining Sections

| # | Task | Files changed | Notes |
|---|------|---------------|-------|
| 45 | `partials/project.html` — project info | `tools/.../templates/partials/project.html` | Repo root, lockfiles, build tools, configs |
| 46 | `partials/packages.html` — packages | `tools/.../templates/partials/packages.html` | Grouped by location, Alpine.js search/filter, expandable groups |
| 47 | `partials/network.html` — network | `tools/.../templates/partials/network.html` | DNS, proxy, outbound, interfaces |
| 48 | `partials/filesystem.html` — filesystem | `tools/.../templates/partials/filesystem.html` | Writable dirs, disk space, mounts |
| 49 | `partials/security.html` — security | `tools/.../templates/partials/security.html` | Secret scan results, permission warnings |
| 50 | `partials/container.html` — container/CI | `tools/.../templates/partials/container.html` | Docker/CI/WSL/cloud, resource limits |
| 51 | `partials/raw_json.html` — raw JSON viewer | `tools/.../templates/partials/raw_json.html` | Formatted, syntax-highlighted full scan JSON |
| 52 | Verify: all sections render correctly | — | Full manual walkthrough |

### Phase 6: Interactive Features and Controls

| # | Task | Files changed | Notes |
|---|------|---------------|-------|
| 53 | Implement search box | `base.html`, `index.html` | Alpine.js `x-model` filtering across all visible sections |
| 54 | Implement hide/show empty fields toggle | `base.html`, `style.css` | Alpine.js toggle, CSS classes to hide empty rows |
| 55 | Implement redact secrets toggle | `base.html`, `routes.py` | Toggle switches between `NONE` and `SECRETS` via htmx re-render |
| 56 | Implement copy field value | `partials/*.html` | Clipboard API button on each field value |
| 57 | Implement refresh scan | `base.html`, `routes.py`, `api.py` | Button triggers `POST /api/scan` then refreshes all sections via htmx |
| 58 | Implement timestamps | `partials/summary.html`, `collector.py` | Scan timestamp in summary, per-section timestamps |
| 59 | Lazy-load slow sections | `routes.py`, `partials/packages.html` | `hx-trigger="load"` for outdated check, spinner while loading |
| 60 | Per-section refresh buttons | `partials/*.html` | `hx-get` + `hx-target` on a refresh icon per section |
| 61 | Dark/light mode toggle | `style.css`, `base.html` | CSS `prefers-color-scheme` + Alpine.js toggle switch |
| 62 | Verify: all interactive features work | — | Manual smoke test |

### Phase 7: Export and Diff

| # | Task | Files changed | Notes |
|---|------|---------------|-------|
| 63 | Create `export.py` — static HTML export logic | `tools/.../export.py` | Renders `export.html` template, inlines CSS, strips JS, adds CSP meta tag |
| 64 | Create `export.html` — self-contained export template | `tools/.../templates/export.html` | No JS, inline CSS, redaction level + timestamp header, warning banner if low redaction |
| 65 | Add `GET /api/export.html` endpoint | `api.py` | Returns static HTML with `Content-Disposition: attachment` |
| 66 | Add export dropdown to UI | `base.html` | Export JSON / Export HTML buttons |
| 67 | Implement diff against previous scan | `collector.py`, `routes.py`, `partials/` | Cache previous scan result, compute delta, highlight changes in UI |
| 68 | Verify: export generates valid HTML with correct redaction | — | Download export, verify no secrets, verify CSP, verify no JS |
| 69 | Verify: diff highlights changes correctly | — | Run scan, change something, re-scan, check diff |

### Phase 8: Documentation and Cleanup

| # | Task | Files changed | Notes |
|---|------|---------------|-------|
| 70 | Create `tools/dev-tools/env-dashboard/README.md` | `tools/.../README.md` | Usage, development, architecture, security constraints |
| 71 | Create `scripts/_env_collectors/README.md` | `scripts/_env_collectors/README.md` | Module purpose, how to add collectors, tier reference |
| 72 | Extend Prettier to cover `*.css` files | `.pre-commit-config.yaml` | Add CSS to Prettier file patterns |
| 73 | Update `docs/design/tool-decisions.md` | `docs/design/tool-decisions.md` | Note FastAPI, htmx, Alpine.js choices |
| 74 | Update `docs/repo-layout.md` | `docs/repo-layout.md` | Add `tools/dev-tools/` and `scripts/_env_collectors/` |
| 75 | Update `.github/copilot-instructions.md` | `.github/copilot-instructions.md` | Add ADR 041 to key ADRs if warranted |
| 76 | Update `scripts/README.md` | `scripts/README.md` | Document `_env_collectors` shared module |
| 77 | Final verification: full walkthrough | — | All sections, API, search, refresh, export, diff, dark mode |

## Migrations / Refactors

### `gather_env_info()` extraction

The primary refactor is extracting data-collection logic from
`env_inspect.py` into `scripts/_env_collectors/`. This is the only
change that touches existing code.

**Migration strategy:**

1. Create the `_env_collectors` package with all collector files.
2. Move logic from `env_inspect.py` private functions into collectors.
3. Update `gather_env_info()` in `env_inspect.py` to delegate to
   `_env_collectors.gather_env_info()`.
4. Verify CLI output is identical (regression test).
5. Deprecate the old private functions in `env_inspect.py`.

**Risk:** If existing code imports `env_inspect.gather_env_info()`, it
continues to work — the function still exists, it just delegates. No
external breakage.

## Testing Checklist

### Shared collector module

- [ ] `gather_env_info()` returns valid data at each tier
- [ ] Each collector handles timeout gracefully
- [ ] Each collector handles errors without crashing the scan
- [ ] Redaction strips known secret patterns
- [ ] Redaction preserves allowlisted env var values
- [ ] URL credential stripping works (scheme://user:pass@host)
- [ ] High-entropy detection at PARANOID level works
- [ ] Schema version is present in output
- [ ] `env_inspect.py` CLI output unchanged after refactor

### Dashboard

- [ ] `hatch run dashboard:serve` starts without errors
- [ ] `http://127.0.0.1:8000` returns HTTP 200
- [ ] Index page renders with summary bar, warnings panel, section cards
- [ ] Each section loads correctly via htmx
- [ ] Pass/warn/fail badges display correctly
- [ ] Search box filters across sections (Alpine.js)
- [ ] Hide/show empty fields works
- [ ] Redact toggle switches between NONE and SECRETS
- [ ] Copy field value copies to clipboard
- [ ] Raw JSON viewer shows formatted output
- [ ] Lazy-load spinner shows for slow sections
- [ ] Per-section refresh updates data
- [ ] Refresh scan re-runs all collectors
- [ ] Timestamps display on summary and per-section
- [ ] Dark/light mode toggle works
- [ ] Diff against previous scan highlights changes

### API

- [ ] `GET /api/summary` returns summary JSON
- [ ] `GET /api/report` returns full scan JSON
- [ ] `GET /api/warnings` returns warnings list
- [ ] `GET /api/sections/:name` returns single section
- [ ] `POST /api/scan` triggers fresh scan
- [ ] `GET /api/export.json` returns downloadable JSON with PII redaction
- [ ] `?redact=` parameter works on all endpoints

### Export

- [ ] Static HTML export contains no JavaScript
- [ ] Export has CSP meta tag blocking scripts
- [ ] Export uses PII-level redaction by default
- [ ] Export includes timestamp and redaction level header
- [ ] Warning banner appears when redaction < PII
- [ ] `Content-Disposition: attachment` header is set
- [ ] HTML is valid and renders correctly when opened in browser
- [ ] No external URLs in export

### Security

- [ ] Jinja2 autoescape active (test with env var containing `<script>`)
- [ ] Server binds to `127.0.0.1` only (verify with `netstat`/`ss`)
- [ ] Redaction active by default (SECRETS level)
- [ ] Export redaction defaults to PII level
- [ ] No raw secret values in HTML source at SECRETS level
- [ ] `task dashboard:serve` works as Taskfile shortcut
- [ ] No console errors in browser DevTools

## Rollout Notes

- **Feature flags:** None — the dashboard is opt-in via
  `hatch run dashboard:serve`. It doesn't affect any existing workflow.
- **Breaking changes:** `env_inspect.py` internal functions are moved
  to `_env_collectors` but the public `gather_env_info()` interface is
  preserved. The CLI works identically.
- **Rollback plan:** Revert `env_inspect.py` changes (restore inline
  functions), delete `scripts/_env_collectors/` and
  `tools/dev-tools/env-dashboard/`, remove the `dashboard` dependency
  group and Hatch env from `pyproject.toml`, remove the Taskfile task.
- **Documentation updates:** READMEs in `_env_collectors/` and
  `env-dashboard/`, plus updates to `repo-layout.md`,
  `tool-decisions.md`, and `scripts/README.md`.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep — dashboard grows beyond documented features | Med | Freeze feature list at v2 design. Defer unlisted features to future blueprints. |
| Secret leakage in exports | High | Redaction layer is Phase 1. Exports default to PII level. No JavaScript in exports. CSP meta tag. |
| `gather_env_info()` refactor breaks CLI | Med | Regression test: compare CLI output before/after refactor. Keep public interface unchanged. |
| New collectors are slow | Med | Per-collector timeout + htmx lazy-loading. Deep scan is opt-in. |
| Vendored JS becomes outdated | Low | Pin versions in README. Update periodically. No security risk for local-only tool. |
| Template users don't want the dashboard | Low | Self-contained in `tools/dev-tools/env-dashboard/`. Delete the directory — no impact. |
| Insights rules produce false positives | Med | Each insight has a severity level. Keep rules conservative — warn only when confident. |

## References

- [Exploration 001: Environment inspection web dashboard](../explorations/001-env-inspect-web-dashboard.md)
- [Blueprint 001: Environment inspection web dashboard](../blueprints/001-env-inspect-web-dashboard.md)
- [ADR 041: Environment inspection web dashboard](../adr/041-env-inspect-web-dashboard.md)
- [scripts/env_inspect.py](../../scripts/env_inspect.py)
