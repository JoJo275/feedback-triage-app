# simple-python-boilerplate

A modern Python project template with `src/` layout, automated CI/CD, and batteries-included tooling.

<!-- TODO (template users): Replace 'JoJo275/simple-python-boilerplate' with your repo slug -->

[![CI](https://github.com/JoJo275/simple-python-boilerplate/actions/workflows/ci-gate.yml/badge.svg?branch=main)](https://github.com/JoJo275/simple-python-boilerplate/actions/workflows/ci-gate.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Coverage](https://codecov.io/gh/JoJo275/simple-python-boilerplate/branch/main/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/JoJo275/simple-python-boilerplate)

<!-- TODO (template users): Replace YOUR_TOKEN in the coverage badge above
     with your actual Codecov repository token, or remove the badge entirely
     if you don't use Codecov. The token is found in your Codecov repo settings. -->

---

## What's Included

<!-- TODO (template users): Update the hook/workflow counts below after
     adding or removing hooks and workflows in your fork. -->

| Category                    | Tools                                                       |
| :-------------------------- | :---------------------------------------------------------- |
| [**Build**][adr-016]        | Hatchling + hatch-vcs (version from git tags)               |
| [**Environments**][adr-016] | Hatch (virtualenv management, test matrix)                  |
| [**Linting**][adr-005]      | Ruff (lint + format), mypy (strict), bandit (security)      |
| [**Testing**][adr-006]      | pytest, pytest-cov, Python 3.11–3.13 matrix                 |
| [**Pre-commit**][adr-008]   | 47 hooks across 4 stages (commit, commit-msg, push, manual) |
| [**CI/CD**][workflows]      | 37 GitHub Actions workflows, SHA-pinned                     |
| [**Docs**][adr-020]         | MkDocs Material + mkdocstrings, auto-deploy to Pages        |
| [**Release**][adr-021]      | release-please → automated changelog + versioning           |
| [**Security**][adr-012]     | CodeQL, pip-audit, Trivy, dependency-review, gitleaks       |
| [**Container**][adr-025]    | Multi-stage Containerfile with scan                         |

## Quick Start

### Prerequisites

- Python **3.11+** (required)
- [Git](https://git-scm.com/) (recommended — hooks, branching, CI)
- [Hatch](https://hatch.pypa.io/) (recommended — `pipx install hatch`)
- [Task](https://taskfile.dev/) (optional — short aliases for Hatch commands)

### Setup

```bash
# Clone and enter the project
git clone https://github.com/YOURNAME/YOURREPO.git
cd YOURREPO

# Enter the dev environment (installs everything automatically)
hatch shell

# Install all git hooks
task pre-commit:install
```

### Daily Workflow

```bash
task test                 # Run tests
task test:cov             # Run tests with coverage
task test:matrix          # Run across Python 3.11-3.13
task lint                 # Check linting issues
task lint:fix             # Auto-fix linting issues
task fmt                  # Apply formatting
task typecheck            # Run mypy
task check                # All quality gates at once
task doctor:all           # All health checks in one report
task doctor:git           # Git health dashboard
task doctor:git:refresh   # Fetch, prune stale refs, sync tags
task doctor:git:commits   # Detailed commit report
task branch:create        # Interactive branch creation
task docs:serve           # Live-reload docs at localhost:8000
task docs:build           # Build docs (strict mode)
task docs:commands        # Regenerate command reference
task security             # Run bandit security linter
task dashboard:serve      # Environment dashboard at localhost:8000
```

> Run `task --list` for all commands, or see [Taskfile.yml](Taskfile.yml) directly.
> No Task installed? Use `hatch run <command>` instead (e.g., `hatch run test`).

### Alternative: pip

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -e ".[dev]"
pytest
```

## Project Structure

```
src/simple_python_boilerplate/   # Package source (src/ layout)
tests/unit/                      # Unit tests
tests/integration/               # Integration tests
docs/                            # MkDocs documentation
scripts/                         # Developer utility scripts
.github/workflows/               # 37 CI/CD workflows
db/                              # Database schema, migrations, seeds
```

See [docs/repo-layout.md](docs/repo-layout.md) for the full annotated tree.

## CLI Entry Points

<!-- TODO (template users): Replace these with your own CLI commands after
     updating [project.scripts] in pyproject.toml. -->

**21 `spb-*` commands** are available after installing the package.
Install globally with `pipx install .` to use them from any repo on your machine.

| Command | Purpose |
| :------ | :------ |
| `spb` | Main CLI command |
| `spb-version` | Print version info |
| `spb-start` | Start the application |
| `spb-doctor` | Diagnose environment issues |
| `spb-diag` | Full diagnostics bundle for bug reports |
| `spb-git-doctor` | Git health dashboard and branch operations |
| `spb-env-doctor` | Environment health check |
| `spb-repo-doctor` | Repository structure health checks |
| `spb-env-inspect` | Environment, packages, PATH inspection |
| `spb-repo-stats` | Repository statistics dashboard |
| `spb-clean` | Remove build artifacts and caches |
| `spb-bootstrap` | One-command setup for fresh clones |
| `spb-dep-versions` | Show/update dependency versions |
| `spb-workflow-versions` | Show/update SHA-pinned action versions |
| `spb-check-todos` | Scan for template TODO comments |
| `spb-check-python` | Verify Python version consistency |
| `spb-changelog-check` | Verify CHANGELOG matches git tags |
| `spb-apply-labels` | Apply GitHub labels from JSON definitions |
| `spb-archive-todos` | Archive completed TODOs |
| `spb-customize` | Interactive project customization |
| `spb-check-issues` | Flag stale entries in known-issues.md |
| `spb-dashboard` | Start the environment inspection dashboard |

All arguments are forwarded: `spb-git-doctor --json` works the same as
`python scripts/git_doctor.py --json`.

See [docs/guide/entry-points.md](docs/guide/entry-points.md) for installation
options, how it works, and the full command reference.

## CI/CD Pipeline

Every push and PR triggers automated checks:

- **Quality:** Ruff lint/format, mypy strict, codespell, test matrix (3.11-3.13), coverage
- **Security:** bandit, pip-audit, CodeQL, dependency-review, Trivy, gitleaks
- **PR:** title validation, auto-labeler, spellcheck autofix
- **Release:** release-please changelog, SBOM generation
- **Gate:** Single `ci-gate` check for branch protection ([ADR 024](docs/adr/024-ci-gate-pattern.md))

All actions are SHA-pinned ([ADR 004](docs/adr/004-pin-action-shas.md)) with repository guards ([ADR 011](docs/adr/011-repository-guard-pattern.md)).

See [docs/workflows.md](docs/workflows.md) for the full workflow inventory.

## Utility Scripts

| Script                                  | Purpose                                                                  |
| :-------------------------------------- | :----------------------------------------------------------------------- |
| `scripts/bootstrap.py`                  | One-command setup for fresh clones                                       |
| `scripts/customize.py`                  | Interactive project customization (placeholders, license, optional dirs) |
| `scripts/repo_doctor.py`                | Health checker with `--fix` support                                      |
| `scripts/env_doctor.py`                 | Quick environment health check                                           |
| `scripts/git_doctor.py`                 | Git health check and branch activity dashboard                           |
| `scripts/doctor.py`                     | Diagnostics bundle for bug reports                                       |
| `scripts/dep_versions.py`               | Show/update dependency versions                                          |
| `scripts/workflow_versions.py`          | Show/update SHA-pinned action versions                                   |
| `scripts/generate_command_reference.py` | Generate docs/reference/commands.md from project commands                |
| `scripts/apply_labels.py`               | Apply GitHub labels (`--set baseline\|extended`)                         |
| `scripts/check_todos.py`                | Scan for `TODO (template users)` comments                                |
| `scripts/archive_todos.py`              | Archive resolved TODOs                                                   |
| `scripts/changelog_check.py`            | Verify CHANGELOG.md matches git tags                                     |
| `scripts/clean.py`                      | Remove build artifacts and caches                                        |
| `scripts/test_containerfile.py`         | Test the Containerfile image: build, validate, clean up                  |
| `scripts/test_docker_compose.py`        | Test docker compose stack: build, run, validate, clean up                |

## Environment Dashboard

A web-based environment inspection dashboard built with FastAPI + Jinja2 +
htmx + Alpine.js. Collects data from 20 plugin-based collectors covering
system info, Python runtimes, packages, git status, security, CI/CD, docs,
disk usage, and more.

```bash
task dashboard:serve          # http://127.0.0.1:8000
# or directly:
hatch run dashboard:serve
```

Features: dark/light mode, 7 accent themes, real-time data freshness,
redaction levels, copy-to-clipboard, pip package management, section
guides, keyboard shortcuts, static HTML export, and JSON API.

See [docs/guide/dashboard-guide.md](docs/guide/dashboard-guide.md) for
the full guide.

## Using This Template

See [docs/USING_THIS_TEMPLATE.md](docs/USING_THIS_TEMPLATE.md) for a step-by-step setup guide.

**Quick checklist:**

1. Click "Use this template" on GitHub
2. Run `python scripts/customize.py` for interactive setup, **or** manually:
    1. Replace `simple-python-boilerplate` / `simple_python_boilerplate` with your project name
    2. Update `pyproject.toml` (name, description, URLs, author)
    3. Update `mkdocs.yml` (`site_url`, `repo_url`, `site_name`)
3. Run `python scripts/bootstrap.py` to set up the local environment
4. Delete placeholder code in `src/` and `tests/`
5. Enable repository guards via repository variables (see [ADR 011][adr-011])
6. Install labels: `python scripts/apply_labels.py --set baseline --repo OWNER/REPO`

**Customization workflow (export → edit → preview → apply):**

```bash
python scripts/customize.py                                         # generate customize-config.md
# edit customize-config.md — fill in values, toggle checkboxes
python scripts/customize.py --apply-from customize-config.md --dry-run  # preview changes
python scripts/customize.py --apply-from customize-config.md            # apply for real
```

**Bootstrap (one-command setup):**

```bash
python scripts/bootstrap.py              # full setup: Hatch envs, hooks, verification
python scripts/bootstrap.py --dry-run    # preview what would happen
python scripts/bootstrap.py --ci-like    # run all checks like CI (quality + docs build)
python scripts/bootstrap.py --strict     # include ruff + mypy quality pass
```

See [USING_THIS_TEMPLATE.md](docs/USING_THIS_TEMPLATE.md) for the full walkthrough, [resources_links.md](docs/notes/resources_links.md) for curated learning links, and [resources_written.md](docs/notes/resources_written.md) for self-written references.

## Documentation

- **Live docs:** `task docs:serve` (serves at `http://localhost:8000`)
- **Getting started:** [docs/guide/getting-started.md](docs/guide/getting-started.md)
- **Architecture decisions:** [docs/adr/](docs/adr/)
- **Developer guides:** [docs/development/](docs/development/)
- **Troubleshooting:** [docs/guide/troubleshooting.md](docs/guide/troubleshooting.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

## License

<!-- TODO (template users): Update the license if you chose something other
     than Apache 2.0 during customization. -->

Apache License 2.0 — see [LICENSE](LICENSE).

<!-- reference-style links (keep sorted) -->

[adr-005]: docs/adr/005-ruff-for-linting-formatting.md
[adr-006]: docs/adr/006-pytest-for-testing.md
[adr-008]: docs/adr/008-pre-commit-hooks.md
[adr-011]: docs/adr/011-repository-guard-pattern.md
[adr-012]: docs/adr/012-multi-layer-security-scanning.md
[adr-016]: docs/adr/016-hatchling-and-hatch.md
[adr-020]: docs/adr/020-mkdocs-documentation-stack.md
[adr-021]: docs/adr/021-automated-release-pipeline.md
[adr-025]: docs/adr/025-container-strategy.md
[workflows]: docs/workflows.md
