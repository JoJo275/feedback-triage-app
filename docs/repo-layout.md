# Repository Layout

<!-- TODO (template users): After forking, update this directory tree and
     component tables to reflect your actual project structure. Remove
     entries for components you deleted (db/, experiments/, etc.) and add
     entries for new directories you created. -->

Full annotated structure of this repository with details on what each component does and what breaks if removed.

For a quick overview, see the [Repository Layout](#repository-layout) section in the main [README](../README.md).

---

## Directory Tree

```text
simple-python-boilerplate/
├── .github/                    # GitHub-specific configuration
│   ├── CODEOWNERS              # Code ownership rules
│   ├── copilot-instructions.md # GitHub Copilot project context
│   ├── dependabot.yml          # Automated dependency updates
│   ├── FUNDING.yml             # Sponsorship links
│   ├── ISSUE_TEMPLATE/         # Issue templates (bug, feature, etc.)
│   │   ├── bug_report.yml      # Bug report form
│   │   ├── config.yml          # External links and Discussions redirect
│   │   ├── documentation.yml   # Docs improvement form
│   │   └── feature_request.yml # Feature request form
│   ├── instructions/           # Copilot instruction files (6 files)
│   │   ├── collectors.instructions.md   # Env collector conventions
│   │   ├── dashboard.instructions.md    # Dashboard app conventions
│   │   ├── dashboard-css.instructions.md # Dashboard CSS conventions
│   │   ├── dashboard-templates.instructions.md # Jinja2 template conventions
│   │   ├── python.instructions.md       # Python style, imports, security
│   │   └── tests.instructions.md        # pytest conventions, fixtures
│   ├── labeler.yml             # Auto-label rules for PRs
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── SKILL.md                # Multi-step operation procedures
│   ├── skills/                 # Copilot skill definitions
│   │   └── dashboard-dev/SKILL.md # Dashboard development skill
│   ├── workflows/              # GitHub Actions CI/CD (37 YAML files)
│   │   ├── ci-gate.yml         # Single required check for branch protection
│   │   ├── lint-format.yml     # Ruff linting and formatting
│   │   ├── release.yml         # Build artifacts on tag push
│   │   ├── release-please.yml  # Automated Release PR creation
│   │   ├── test.yml            # Pytest across Python versions
│   │   └── ...                 # Security, docs, maintenance workflows
│   └── workflows-optional/     # Opt-in workflows (copy to workflows/)
│       ├── changelog.yml       # Changelog validation workflow
│       └── README.md           # Opt-in workflow documentation
│
├── .devcontainer/              # Dev container configuration
│   ├── devcontainer.json       # VS Code dev container settings
│   └── README.md               # Dev container documentation
│
├── db/                         # Database assets (optional)
│   ├── migrations/             # Schema migration scripts
│   │   ├── 001_example_migration.sql # Example migration
│   │   └── README.md           # Migration conventions
│   ├── queries/                # Reusable SQL queries
│   │   ├── example_queries.sql # Example query patterns
│   │   └── README.md           # Query conventions
│   ├── seeds/                  # Sample/test data
│   │   ├── 001_example_seed.sql # Example seed data
│   │   └── README.md           # Seed conventions
│   ├── README.md               # Database strategy overview
│   └── schema.sql              # Database schema definition
│
├── docs/                       # Project documentation
│   ├── adr/                    # Architecture Decision Records (44 ADRs)
│   │   ├── template.md         # ADR template
│   │   ├── archive/            # Superseded ADRs
│   │   └── README.md           # ADR index table
│   ├── blueprints/             # Proposed design shapes
│   │   ├── 001-env-inspect-web-dashboard.md # Dashboard design
│   │   ├── template.md         # Blueprint template
│   │   └── README.md           # Blueprint index
│   ├── design/                 # Architecture and design docs
│   │   ├── architecture.md     # System overview and data flows
│   │   ├── ci-cd-design.md     # CI/CD pipeline design
│   │   ├── database.md         # Database design
│   │   ├── tool-decisions.md   # Tool comparison notes
│   │   └── README.md           # Design docs index
│   ├── development/            # Developer guides
│   │   ├── branch-workflows.md # Git branching workflows
│   │   ├── command-workflows.md # Command execution flow (task→hatch→tool)
│   │   ├── dev-setup.md        # Development environment setup
│   │   ├── developer-commands.md # Available developer commands
│   │   ├── development.md      # Development process overview
│   │   ├── pull-requests.md    # PR conventions and review process
│   │   └── README.md           # Development docs index
│   ├── explorations/           # Early-stage idea evaluation
│   │   ├── 001-env-inspect-web-dashboard.md # Dashboard exploration
│   │   ├── template.md         # Exploration template
│   │   └── README.md           # Exploration index
│   ├── guide/                  # User-facing guides
│   │   ├── dashboard-guide.md  # Environment dashboard guide
│   │   ├── entry-points.md     # Global CLI entry points guide
│   │   ├── getting-started.md  # Documentation quickstart
│   │   ├── troubleshooting.md  # FAQ and common errors
│   │   └── README.md           # Guide index
│   ├── implementation-plans/   # Step-by-step execution details
│   │   ├── 001-env-inspect-web-dashboard.md # Dashboard implementation
│   │   ├── template.md         # Plan template
│   │   └── README.md           # Plan index
│   ├── notes/                  # Personal learning notes
│   │   ├── archive.md          # Archived notes
│   │   ├── how-to-edit-web-ui.md # Web UI editing guide
│   │   ├── learning-web-apps.md # Web development concepts
│   │   ├── learning.md         # General learning captures
│   │   ├── pico-css.md         # PicoCSS framework notes
│   │   ├── resources_links.md  # External resource links
│   │   ├── resources_written.md # Written resource summaries
│   │   ├── todo.md             # TODO tracking
│   │   ├── tool-comparison.md  # Tool comparison notes
│   │   ├── web-dev-questions.md # Web dev Q&A
│   │   └── README.md           # Notes index
│   ├── reference/              # Reference documentation
│   │   ├── api.md              # API reference (mkdocstrings)
│   │   ├── commands.md         # Auto-generated command reference
│   │   ├── scripts.md          # Script reference
│   │   ├── template-inventory.md # File template inventory
│   │   ├── index.md            # Reference index
│   │   └── README.md           # Reference docs index
│   ├── templates/              # Reusable file templates
│   │   ├── BUG_BOUNTY.md       # Bug bounty policy template
│   │   ├── SECURITY_no_bounty.md # Security policy (no bounty)
│   │   ├── SECURITY_with_bounty.md # Security policy (with bounty)
│   │   ├── pull-request-draft.md # PR draft template
│   │   ├── issue_templates/    # Additional issue template options
│   │   │   ├── issue_forms/    # GitHub issue form YAML templates (7)
│   │   │   └── legacy_markdown/ # Legacy Markdown issue templates (10)
│   │   └── README.md           # Template inventory
│   │   # Design lifecycle (optional):
│   │   #   idea/problem → explorations/
│   │   #   proposed design → blueprints/
│   │   #   decision locked in → adr/
│   │   #   build steps → implementation-plans/
│   ├── index.md                # MkDocs homepage
│   ├── known-issues.md         # Known issues and limitations
│   ├── labels.md               # GitHub label catalog
│   ├── release-policy.md       # Versioning and release policy
│   ├── releasing.md            # How to create releases
│   ├── repo-layout.md          # This file
│   ├── sbom.md                 # Software Bill of Materials guide
│   ├── tooling.md              # Tooling overview (50+ tools)
│   ├── USING_THIS_TEMPLATE.md  # Template customization guide
│   ├── workflows.md            # GitHub Actions reference
│   └── README.md               # Docs index
│
├── experiments/                # Scratch space for exploration
│   ├── example_api_test.py     # Example API test script
│   ├── example_data_exploration.py # Example data exploration
│   └── README.md               # Experiments conventions
│
├── labels/                     # GitHub label definitions
│   ├── baseline.json           # Core labels (18)
│   └── extended.json           # Full label set (62)
│
├── mkdocs-hooks/               # MkDocs build hooks
│   ├── generate_commands.py    # Auto-regenerate command reference
│   ├── include_templates.py    # Include file templates in docs
│   ├── repo_links.py           # Rewrite repo-relative links
│   └── README.md               # Hook documentation
│
├── repo_doctor.d/              # Diagnostic check definitions
│   ├── ci.toml                 # CI/CD health checks
│   ├── container.toml          # Container health checks
│   ├── db.toml                 # Database health checks
│   ├── docs.toml               # Documentation health checks
│   ├── python.toml             # Python project health checks
│   ├── security.toml           # Security health checks
│   └── README.md               # Check definition conventions
│
├── scripts/                    # Developer/maintenance scripts (20 CLIs + 6 helpers)
│   ├── _colors.py              # Shared ANSI color utilities
│   ├── _container_common.py    # Shared container-test utilities
│   ├── _doctor_common.py       # Shared doctor-family utilities
│   ├── _imports.py             # Shared import helper (repo root discovery)
│   ├── _progress.py            # Shared progress indicators (ProgressBar, Spinner)
│   ├── _ui.py                  # Shared dashboard UI (headers, sections, tables)
│   ├── apply_labels.py         # Apply GitHub labels from JSON definitions
│   ├── apply-labels.sh         # Shell wrapper for label application
│   ├── archive_todos.py        # Archive completed TODO items from todo.md
│   ├── bootstrap.py            # One-command setup for fresh clones
│   ├── changelog_check.py      # Validate CHANGELOG.md has entry for PR
│   ├── check_known_issues.py   # Flag stale resolved entries in known-issues.md
│   ├── check_python_support.py # Validate Python version support consistency
│   ├── check_todos.py          # Scan for TODO (template users) comments
│   ├── clean.py                # Remove build artifacts and caches
│   ├── customize.py            # Interactive project customization
│   ├── dep_versions.py         # Show/update dependency versions
│   ├── doctor.py               # Print diagnostics bundle for bug reports
│   ├── env_doctor.py           # Environment health check + consistency checks
│   ├── env_inspect.py          # Environment and dependency inspector
│   ├── generate_command_reference.py # Generate docs/reference/commands.md
│   ├── git_doctor.py           # Git health dashboard and config manager
│   ├── repo_doctor.py          # Repository structure health checks
│   ├── repo_sauron.py          # Repository statistics dashboard
│   ├── test_containerfile.py   # Test Containerfile (build, validate, cleanup)
│   ├── test_containerfile.sh   # Bash equivalent of test_containerfile.py
│   ├── test_docker_compose.py  # Test docker-compose stack
│   ├── test_docker_compose.sh  # Bash equivalent of test_docker_compose.py
│   ├── workflow_versions.py    # Show/update SHA-pinned GitHub Actions versions
│   ├── _env_collectors/        # Environment data collector plugins (20 collectors)
│   │   ├── __init__.py         # Orchestrator (gather_env_info, Tier enum)
│   │   ├── _base.py            # BaseCollector ABC (timeout, error isolation)
│   │   ├── _redact.py          # RedactLevel enum + recursive redaction
│   │   ├── ci_cd_status.py     # CI/CD pipeline detection
│   │   ├── container.py        # Docker/Podman/WSL/CI detection
│   │   ├── dependency_health.py # Outdated packages, version conflicts
│   │   ├── disk_workspace.py   # Workspace disk usage, largest files
│   │   ├── docs_status.py      # MkDocs config, build status
│   │   ├── filesystem.py       # Directory permissions, temp dir
│   │   ├── git_info.py         # Git branch, remotes, dirty state
│   │   ├── hardware.py         # CPU, RAM, disk hardware info
│   │   ├── insights.py         # Cross-section derived warnings
│   │   ├── network.py          # Proxy vars, DNS, connectivity
│   │   ├── packages.py         # Installed packages with versions
│   │   ├── path_analysis.py    # PATH entries, dead dirs, duplicates
│   │   ├── pip_environments.py # pip config, index URLs
│   │   ├── precommit_hooks.py  # Installed hooks and health
│   │   ├── project.py          # pyproject.toml metadata, config files
│   │   ├── project_commands.py # Hatch scripts, Task commands
│   │   ├── runtimes.py         # Python interpreters on system
│   │   ├── security.py         # Secret env vars, insecure PATH
│   │   ├── system.py           # OS, architecture, hostname
│   │   └── venv.py             # Virtualenv and Hatch env detection
│   ├── precommit/              # Custom pre-commit hook scripts
│   │   ├── auto_chmod_scripts.py # Auto-fix executable bit on shebang scripts
│   │   ├── check_local_imports.py # Enforce local-module section comment
│   │   ├── check_nul_bytes.py  # Detect NUL bytes in staged files
│   │   └── README.md           # Pre-commit hook documentation
│   ├── sql/                    # SQL utility scripts
│   │   ├── reset.sql           # Reset database (drop/recreate)
│   │   ├── scratch.example.sql # Template for ad-hoc queries
│   │   └── README.md           # SQL script conventions
│   └── README.md               # Script inventory and usage
│
├── src/                        # Source code (package root)
│   └── simple_python_boilerplate/
│       ├── __init__.py         # Package initialization, version
│       ├── _version.py         # Generated by hatch-vcs (git tag version)
│       ├── py.typed            # PEP 561 type stub marker
│       ├── api.py              # Programmatic interface
│       ├── cli.py              # Command-line interface
│       ├── engine.py           # Core business logic
│       ├── main.py             # Entry points (spb, spb-doctor, etc.)
│       ├── scripts_cli.py      # Script entry points (spb-git-doctor, etc.)
│       ├── dev_tools/          # Development utilities
│       │   └── __init__.py     # Package marker
│       └── sql/                # SQL query assets
│           ├── __init__.py     # Package marker
│           ├── example_query.sql # Example SQL query
│           └── README.md       # SQL asset conventions
│
├── tests/                      # Test suite (1066 tests)
│   ├── conftest.py             # Shared fixtures (project_root, sample_input)
│   ├── unit/                   # Unit tests (45 test files)
│   │   ├── conftest.py         # Unit-test-specific fixtures
│   │   ├── test_*.py           # One per module/script (45 files)
│   │   └── __init__.py         # Package marker
│   └── integration/            # Integration tests
│       ├── conftest.py         # Integration fixtures
│       ├── sql/                # SQL integration test assets
│       ├── test_cli_smoke.py   # CLI smoke tests
│       ├── test_db_example.py  # Database integration test
│       └── __init__.py         # Package marker
│
├── tools/                      # Development tool packages
│   ├── __init__.py             # Package marker
│   └── dev_tools/              # Development tool directory
│       ├── __init__.py         # Package marker
│       └── env_dashboard/      # Environment inspection web dashboard
│           ├── __init__.py     # Package marker
│           ├── __main__.py     # python -m entry point
│           ├── app.py          # FastAPI app factory, Uvicorn startup
│           ├── api.py          # REST API endpoints (JSON + SSE)
│           ├── routes.py       # HTML route handlers (Jinja2 templates)
│           ├── collector.py    # Cache layer (30s TTL over collectors)
│           ├── export.py       # Static HTML export renderer
│           ├── redact.py       # Redaction level parsing
│           ├── static/         # Static assets (CSS, JS, images)
│           │   ├── css/pico.min.css   # PicoCSS framework (vendored)
│           │   ├── css/style.css      # Custom dashboard styles
│           │   ├── js/htmx.min.js     # HTMX library (vendored)
│           │   ├── js/alpine.min.js   # Alpine.js library (vendored)
│           │   ├── img/favicon.svg    # Dashboard favicon
│           │   ├── offline.html       # Offline fallback page
│           │   └── sw.js              # Service worker
│           └── templates/      # Jinja2 templates
│               ├── base.html   # Base layout (nav, sidebar, scripts)
│               ├── index.html  # Dashboard main page
│               ├── export.html # Static export page
│               └── partials/   # Section templates (20 files)
│                   ├── _macros.html     # Reusable Jinja2 macros
│                   └── *.html           # One per collector section
│
├── var/                        # Runtime/generated files
│   ├── app.example.sqlite3     # Example database file
│   └── README.md               # Runtime files documentation
│
├── .containerignore            # Container build context exclusions
├── .devcontainer/              # VS Code dev container config
├── .dockerignore               # Docker build context exclusions
├── .editorconfig               # Cross-editor formatting rules (indent, EOL, whitespace)
├── .gitattributes              # Git file handling (line endings, diff drivers, binary detection)
├── .gitconfig.recommended      # Recommended git configuration
├── .gitignore                  # Files excluded from git
├── .gitmessage.txt             # Commit message template (Conventional Commits)
├── .lycheeignore               # Lychee link checker exclusions
├── .markdownlint-cli2.jsonc    # markdownlint rule overrides
├── .pre-commit-config.yaml     # Pre-commit hook configuration
├── .prettierignore             # Prettier formatter exclusions
├── .readthedocs.yaml           # Read the Docs configuration
├── .release-please-manifest.json # Version tracker for release-please
├── .repo-doctor.toml           # Repo doctor configuration
├── _typos.toml                 # Typos spellchecker exceptions
├── CHANGELOG.md                # Version history
├── CODE_OF_CONDUCT.md          # Community guidelines
├── Containerfile               # Multi-stage container build
├── container-structure-test.yml # Container structure tests
├── CONTRIBUTING.md             # Contribution guidelines
├── codecov.yml                 # Code coverage config
├── docker-compose.yml          # Container orchestration
├── git-config-reference.md     # Generated git config reference (git_doctor.py --export-config)
├── LICENSE                     # Project license (Apache-2.0)
├── mkdocs.yml                  # Documentation site config
├── pgp-key.asc                 # PGP public key for security reports
├── pyproject.toml              # Project metadata and tool config
├── README.md                   # Project overview
├── release-please-config.json  # Release automation config
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── SECURITY.md                 # Security policy
├── simple-python-boilerplate.code-workspace  # VS Code workspace
└── Taskfile.yml                # Task runner shortcuts
```

---

## Component Details

### Core (Required)

These are essential for the package to function.

| Path                                        | Purpose                               | What Breaks If Removed                   |
| ------------------------------------------- | ------------------------------------- | ---------------------------------------- |
| `src/simple_python_boilerplate/`            | Package source code                   | Everything — no package to import        |
| `src/simple_python_boilerplate/__init__.py` | Package marker, exports version       | Package won't be recognized              |
| `pyproject.toml`                            | Build config, metadata, tool settings | Can't install, build, or configure tools |
| `LICENSE`                                   | Legal terms                           | License compliance issues                |

### Testing

| Path                 | Purpose           | What Breaks If Removed              |
| -------------------- | ----------------- | ----------------------------------- |
| `tests/`             | Test suite        | No tests to run, CI fails           |
| `tests/conftest.py`  | Shared fixtures   | Fixtures unavailable across tests   |
| `tests/unit/`        | Unit tests        | Reduced test coverage               |
| `tests/integration/` | Integration tests | Can't verify component interactions |

### CI/CD

| Path                                | Purpose               | What Breaks If Removed         |
| ----------------------------------- | --------------------- | ------------------------------ |
| `.github/workflows/test.yml`        | Run tests on push/PR  | No automated testing           |
| `.github/workflows/lint-format.yml` | Code quality checks   | Formatting issues slip through |
| `.github/workflows/release.yml`     | Build on version tags | Manual build required          |
| `.github/dependabot.yml`            | Dependency updates    | Manual dependency management   |

See [workflows.md](workflows.md) for full workflow documentation.

### Documentation

| Path              | Purpose                | What Breaks If Removed         |
| ----------------- | ---------------------- | ------------------------------ |
| `README.md`       | Project overview       | No landing page                |
| `CONTRIBUTING.md` | Contribution guide     | Contributors lack guidance     |
| `docs/`           | Detailed documentation | Missing context for developers |
| `docs/adr/`       | Decision records       | Lost architectural context     |
| `docs/explorations/` | Early-stage idea evaluation | Lost exploration context |
| `docs/blueprints/` | Proposed design shapes | Lost design context |
| `docs/implementation-plans/` | Execution details | Lost implementation context |
| `CHANGELOG.md`    | Version history        | No release notes               |

### Development Experience

| Path                      | Purpose                                                                        | What Breaks If Removed                    |
| ------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------- |
| `.pre-commit-config.yaml` | Pre-commit hooks                                                               | Local checks disabled                     |
| `requirements-dev.txt`    | Dev dependencies list                                                          | Unclear what to install                   |
| `.gitignore`              | Exclude generated files                                                        | Caches committed to git                   |
| `.gitattributes`          | Line ending normalization, diff drivers, binary file detection, linguist stats | Cross-platform line ending mismatches     |
| `.editorconfig`           | Cross-editor indent, charset, EOL, trailing whitespace rules                   | Inconsistent formatting across editors    |
| `.gitmessage.txt`         | Commit message template (Conventional Commits)                                 | No guided commit format                   |
| `git-config-reference.md` | Generated git config reference (via `git_doctor.py --export-config`)           | Regenerated on demand; informational only |

### Environment Dashboard

| Path | Purpose | What Breaks If Removed |
| --- | --- | --- |
| `tools/dev_tools/env_dashboard/` | Web-based environment inspector | No dashboard (no effect on core package) |
| `tools/dev_tools/env_dashboard/app.py` | FastAPI app factory and Uvicorn startup | Dashboard won't start |
| `tools/dev_tools/env_dashboard/api.py` | REST API endpoints (JSON, SSE streaming) | No JSON API or pip install endpoint |
| `tools/dev_tools/env_dashboard/routes.py` | HTML route handlers (Jinja2 templates) | No dashboard pages |
| `tools/dev_tools/env_dashboard/collector.py` | Cache layer (30s TTL) over env collectors | Every request re-collects (slow) |
| `tools/dev_tools/env_dashboard/templates/` | Jinja2 template files | No HTML output |
| `tools/dev_tools/env_dashboard/static/` | CSS, JS, images | Unstyled, non-interactive dashboard |
| `scripts/_env_collectors/` | Plugin-based data collection (20 collectors) | No environment data to display |

See [Dashboard Guide](guide/dashboard-guide.md) for architecture and usage.

### Global Entry Points

| Path | Purpose | What Breaks If Removed |
| --- | --- | --- |
| `src/simple_python_boilerplate/scripts_cli.py` | Entry point wrappers for all scripts | `spb-*` script commands unavailable |
| `src/simple_python_boilerplate/main.py` | Core entry points (spb, spb-doctor) | `spb` and core commands unavailable |

Scripts are bundled into the wheel via `[tool.hatch.build.targets.wheel.force-include]` so they're available when installed globally with `pipx install .`

See [Entry Points Guide](guide/entry-points.md) for usage.

### Optional Components

These can be removed without breaking core functionality.

| Path              | Purpose         | Safe to Remove?                      |
| ----------------- | --------------- | ------------------------------------ |
| `db/`             | Database assets | ✅ If not using a database           |
| `experiments/`    | Scratch space   | ✅ Personal exploration              |
| `mkdocs-hooks/`   | MkDocs hooks    | ✅ If no repo-relative links in docs |
| `labels/`         | GitHub labels   | ✅ Manual label management           |
| `scripts/`        | Utility scripts | ✅ Convenience only                  |
| `repo_doctor.d/`  | Diagnostics     | ✅ Custom health checks only         |
| `var/`            | Runtime files   | ✅ Example data                      |
| `docs/notes/`     | Personal notes  | ✅ Learning reference                |
| `docs/templates/` | File templates  | ✅ Copy as needed                    |

---

## Source Code Architecture

```text
src/simple_python_boilerplate/
├── __init__.py     # Package exports, version
├── _version.py     # Generated by hatch-vcs (do not edit)
├── py.typed        # PEP 561 marker for type checkers
├── main.py         # Core entry points (spb, spb-doctor, spb-start)
├── scripts_cli.py  # Script entry points (spb-git-doctor, spb-dashboard, etc.)
├── cli.py          # CLI argument parsing
├── engine.py       # Core business logic
├── api.py          # Programmatic interface
├── dev_tools/      # Development utilities
│   └── __init__.py
└── sql/            # SQL query assets
    ├── __init__.py
    ├── example_query.sql
    └── README.md
```

### Data Flow

```text
User → main.py → cli.py → engine.py → result
              ↘ api.py ↗
```

### Key Principle

> Logic lives in `engine.py`. Interfaces (`cli.py`, `api.py`) adapt it.

See [docs/notes/learning.md](notes/learning.md#source-code-file-workflow) for detailed architecture notes.

---

## Configuration Files

### pyproject.toml Sections

| Section                           | Purpose                                  |
| --------------------------------- | ---------------------------------------- |
| `[build-system]`                  | How to build the package                 |
| `[project]`                       | Name, version, dependencies              |
| `[project.optional-dependencies]` | Dev/test/docs extras                     |
| `[project.scripts]`              | CLI entry points (21 commands)           |
| `[tool.hatch.*]`                  | Environments, version (hatch-vcs), build |
| `[tool.hatch.build.targets.wheel.force-include]` | Bundle scripts/ and tools/ into wheel |
| `[tool.ruff]`                     | Linter and formatter configuration       |
| `[tool.mypy]`                     | Type checker configuration               |
| `[tool.pytest]`                   | Test runner configuration                |
| `[tool.coverage.*]`               | Coverage measurement and reporting       |
| `[tool.bandit]`                   | Security scanner configuration           |
| `[tool.deptry]`                   | Unused/missing dependency checker        |
| `[tool.commitizen]`               | Conventional commit validation           |

### Other Config Files

| File                         | Tool           | Purpose                  |
| ---------------------------- | -------------- | ------------------------ |
| `.pre-commit-config.yaml`    | pre-commit     | Git hook definitions     |
| `.github/dependabot.yml`     | Dependabot     | Dependency update rules  |
| `_typos.toml`                | typos          | Spellcheck exceptions    |
| `.markdownlint-cli2.jsonc`   | markdownlint   | Markdown lint overrides  |
| `Taskfile.yml`               | Task           | Task runner shortcuts    |
| `mkdocs.yml`                 | MkDocs         | Documentation site       |
| `codecov.yml`                | Codecov        | Coverage reporting       |
| `release-please-config.json` | release-please | Release automation       |
| `Containerfile`              | Podman/Docker  | Container build          |
| `docker-compose.yml`         | Docker Compose | Container orchestration  |
| `requirements.txt`           | pip            | Production dependencies  |
| `requirements-dev.txt`       | pip            | Development dependencies |

---

## Naming Conventions

| Pattern        | Meaning                 | Example                            |
| -------------- | ----------------------- | ---------------------------------- |
| `test_*.py`    | Test file               | `test_example.py`                  |
| `conftest.py`  | Shared pytest fixtures  | `tests/conftest.py`                |
| `_*.py`        | Internal/private module | `_version.py`                      |
| `py.typed`     | PEP 561 type marker     | Enables type-checking for package  |
| `*.example.*`  | Example/template file   | `app.example.sqlite3`              |
| `__init__.py`  | Package marker          | Required in all packages           |
| `__pycache__/` | Python bytecode cache   | Never commit                       |
| `_version.py`  | Generated version       | Created by hatch-vcs (do not edit) |
| `README.md`    | Directory documentation | One per directory (convention)     |

---

## What to Remove When Adopting

If you're using this template, consider removing:

| Path                      | When to Remove                         |
| ------------------------- | -------------------------------------- |
| `docs/notes/`             | Optional — keep as reference or remove |
| `experiments/`            | After exploration                      |
| `var/app.example.sqlite3` | Replace with your data                 |
| `docs/templates/`         | After copying what you need            |
| `db/`                     | If not using a database                |

---

## See Also

- [README.md](../README.md) — Quick overview
- [CONTRIBUTING.md](../CONTRIBUTING.md) — How to contribute
- [workflows.md](workflows.md) — CI/CD workflows
- [releasing.md](releasing.md) — Release process
- [ADR index](adr/README.md) — Architecture decisions
