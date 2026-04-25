<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Suggested branch rename: feat/env-dashboard -->
<!--
  Suggested PR titles (must use conventional commit format — type: description):

  Full titles:
    feat: Add environment dashboard web app with collector plugin architecture
    feat: Add environment inspection dashboard, global entry points, and Copilot instructions

  Available prefixes:
    feat:     — new feature or capability
    fix:      — bug fix
    docs:     — documentation only
    chore:    — maintenance, no production code change
    refactor: — code restructuring, no behavior change
    test:     — adding or updating tests
    ci:       — CI/CD workflow changes
    style:    — formatting, no logic change
    perf:     — performance improvement
    build:    — build system or dependency changes
    revert:   — reverts a previous commit
-->

<!--
  ╔══════════════════════════════════════════════════════════════╗
  ║  This PR description is for HUMAN REVIEWERS.                 ║
  ║                                                              ║
  ║  Release automation (release-please) reads individual        ║
  ║  commit messages on main — not this description.             ║
  ║  Write commits with conventional format (feat:, fix:, etc.)  ║
  ║  and include (#PR) or (#issue) references in each commit.    ║
  ║                                                              ║
  ║  This template captures: WHY you made changes, HOW to test   ║
  ║  them, and WHAT reviewers should focus on.                   ║
  ╚══════════════════════════════════════════════════════════════╝
-->

## Description

Adds a full-featured environment inspection dashboard — a local-only FastAPI
web app that collects and displays development environment data across 20
plugin-based collectors. Also introduces global `spb-*` CLI entry points,
VS Code task definitions, Copilot instruction/skill files, and extensive
documentation (ADRs, guides, notes).

**What changes you made:**

- **Environment Dashboard** (`tools/dev_tools/env_dashboard/`): FastAPI +
  Jinja2 + htmx + Alpine.js web app with 20 data collector plugins, export
  functionality, background scanning, offline support (service worker),
  graceful shutdown, dark/light theming, and a responsive UI.
- **20 Collector Plugins** (`scripts/_env_collectors/`): Plugin-based
  architecture gathering data on hardware, system, git, packages, runtimes,
  PATH analysis, disk/workspace, container files, CI/CD status, docs status,
  dependency health, pre-commit hooks, security, network, filesystem,
  pip environments, virtualenvs, and project commands.
- **Global Entry Points** (`src/.../scripts_cli.py`, `pyproject.toml`):
  21 `spb-*` CLI commands defined in `[project.scripts]`, thin subprocess
  wrappers enabling cross-repo use via `pipx install .`.
- **VS Code Tasks** (`.vscode/tasks.json`): Task definitions for test, lint,
  format, typecheck, docs, dashboard, build, and more.
- **Copilot Customization** (`.github/instructions/`, `.github/skills/`):
  6 targeted instruction files and 1 skill file covering Python style,
  tests, dashboard development, CSS, templates, and collectors.
- **ADRs**: 042 (script smoke testing), 043 (collector plugin architecture),
  044 (Copilot instructions).
- **Documentation**: Dashboard guide, entry points guide, web dev notes,
  command reference updates, architecture updates, repo layout updates.
- **Unit Tests** (`tests/unit/`): 12 new test files covering dashboard app,
  API, routes, collectors, export, redact, and several scripts.
- **Misc**: Hatch env additions (`dashboard`, updated deps), Taskfile
  additions, `_typos.toml` updates, `.gitignore` additions, improved
  `git_doctor.py` with interactive branch creation.

**Why you made them:**

The boilerplate lacked a way to quickly inspect and debug the development
environment. The dashboard provides a single-pane view of everything a
developer needs to diagnose setup issues — replacing scattered CLI commands
with a browsable, searchable, exportable web UI. The entry points make
scripts usable outside the repo (via `pipx`), and the Copilot instructions
codify project conventions for AI-assisted development.

## Related Issue

N/A — Feature development from blueprint
[001-env-inspect-web-dashboard](../blueprints/001-env-inspect-web-dashboard.md).

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [x] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [ ] 🔧 Refactor (no functional changes)
- [x] 🧪 Test update

## How to Test

**Steps:**

1. Install the project in editable mode: `hatch shell`
2. Start the dashboard: `spb-dashboard` (or `hatch run dashboard:serve`)
3. Open <http://127.0.0.1:8000> — verify all 20 sections load with data
4. Test export via the Export button (JSON download)
5. Test theme toggle (dark/light)
6. Test graceful shutdown via the shutdown button in the sidebar
7. Run unit tests to verify backend logic

**Test command(s):**

```bash
# Dashboard unit tests
hatch run pytest tests/unit/test_dashboard_app.py tests/unit/test_dashboard_api.py tests/unit/test_dashboard_routes.py tests/unit/test_dashboard_collector.py tests/unit/test_dashboard_export.py tests/unit/test_dashboard_redact.py -v

# All unit tests
hatch run pytest tests/ -v

# Entry point smoke test
spb-dashboard --help
```

**Screenshots / Demo (if applicable):**

<!-- TODO: Add screenshots of the dashboard sections before merging -->

## Risk / Impact

**Risk level:** Low

**What could break:**

- New dependencies (`fastapi`, `uvicorn`, `jinja2`, `python-multipart`) are
  isolated to the `dashboard` Hatch env and `[project.optional-dependencies]`
  — they do not affect the default dev environment.
- The 21 new `spb-*` entry points are additive; no existing scripts or
  commands are modified.
- Collector plugins use `subprocess.run()` with argument lists (no
  `shell=True`) and redact sensitive data (tokens, keys, passwords).

**Rollback plan:** Revert this PR

## Dependencies (if applicable)

**New runtime dependencies (optional group `dashboard`):**

- `fastapi` — web framework
- `uvicorn[standard]` — ASGI server
- `jinja2` — templating
- `python-multipart` — form data support

No external PRs or upstream changes required.

## Checklist

- [x] My code follows the project's style guidelines
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [ ] No new warnings (or explained in Additional Notes)
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] Relevant tests pass locally (or explained in Additional Notes)
- [x] No security concerns introduced (or flagged for review)
- [x] No performance regressions expected (or flagged for review)

## Reviewer Focus

- **Collector plugins** (`scripts/_env_collectors/`): Verify the plugin
  discovery pattern in `__init__.py` and that each collector handles missing
  tools gracefully (returns empty/default data, never crashes).
- **Redaction** (`scripts/_env_collectors/_redact.py`,
  `tools/dev_tools/env_dashboard/redact.py`): Confirm sensitive values
  (tokens, API keys, passwords, paths with usernames) are properly masked
  in all output paths (HTML, JSON export, API responses).
- **Entry points** (`src/.../scripts_cli.py`): Verify subprocess wrappers
  don't introduce `shell=True` or path injection risks.
- **Dashboard shutdown** (`tools/dev_tools/env_dashboard/api.py`): The
  graceful shutdown endpoint calls `os._exit()` — confirm this is acceptable
  for a local-only dev tool.

## Additional Notes

- This is a large PR (~19,000 lines across 140 files). Consider reviewing
  by area: collectors → dashboard backend → templates/CSS → entry points →
  docs → tests.
- The dashboard is a **local-only dev tool** — it binds to `127.0.0.1` and
  is not intended for production or network-exposed use.
- The `wip/2026-04-02-scratch` branch should be renamed to something like
  `feat/env-dashboard` before merging.
- Some commits could be squashed for a cleaner history on `main`.
