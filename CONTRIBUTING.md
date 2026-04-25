# Contributing

Thank you for your interest in contributing to this project! This document explains how to set up your environment, how changes flow through the quality pipeline, and what to expect at each stage.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Command Reference](#command-reference)
- [Quality Pipeline Overview](#quality-pipeline-overview)
- [Stage 1: Writing Code (Editor)](#stage-1-writing-code-editor)
- [Stage 2: Pre-commit Hooks (Local)](#stage-2-pre-commit-hooks-local)
- [Stage 3: Push & CI Workflows](#stage-3-push--ci-workflows)
- [Stage 4: Pull Request Checks](#stage-4-pull-request-checks)
- [Stage 5: Merge to Main](#stage-5-merge-to-main)
- [Commit Messages](#commit-messages)
- [Further Reading](#further-reading)
- [Reporting Issues](#reporting-issues)
- [Code of Conduct](#code-of-conduct)

---

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment (see below)
4. Create a branch for your changes

---

## Development Setup

### Prerequisites

- Python **3.11+**
- [Hatch](https://hatch.pypa.io/) (recommended) or `pip`
- [Task](https://taskfile.dev/) (optional, for convenience commands)

### Option A: Using Hatch (recommended)

```bash
# Enter the dev environment (installs all dependencies automatically)
hatch shell

# Install all pre-commit git hooks (one-time, required)
# Or use the Taskfile shortcut: task pre-commit:install
pre-commit install                              # pre-commit stage
pre-commit install --hook-type commit-msg        # commit-msg stage (conventional commits)
pre-commit install --hook-type pre-push          # pre-push stage (pytest, pip-audit, gitleaks)
```

### Option B: Using pip

```bash
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

# Install with dev dependencies
python -m pip install -e ".[dev]"

# Install all pre-commit git hooks (one-time, required)
# Or use the Taskfile shortcut: task pre-commit:install
pre-commit install                              # pre-commit stage
pre-commit install --hook-type commit-msg        # commit-msg stage (conventional commits)
pre-commit install --hook-type pre-push          # pre-push stage (pytest, pip-audit, gitleaks)
```

> **Note:** All three `pre-commit install` commands must be run once per clone. They register git hooks that run automatically at each stage (commit, commit-msg, push).

### Option C: Using Dev Container (zero local setup)

If you have Docker (or Podman) and the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) VS Code extension:

1. Open this repo in VS Code
2. Click "Reopen in Container" when prompted (or run `Dev Containers: Reopen in Container` from the command palette)

Everything — Python, dependencies, pre-commit hooks, extensions — is configured automatically. This also works with [GitHub Codespaces](https://github.com/features/codespaces) for a browser-based environment with no local setup at all.

See [`.devcontainer/README.md`](.devcontainer/README.md) for details.

---

## Running with Containers

To build and run the **production** container image locally:

```bash
# Build and run (foreground)
docker compose up --build

# Or with Podman directly
podman build -t simple-python-boilerplate -f Containerfile .
podman run --rm simple-python-boilerplate
```

> **Note:** The production Containerfile and the Dev Container (`.devcontainer/`) serve different purposes. The Containerfile builds a minimal runtime image; the Dev Container provides a full development environment. See [`.devcontainer/README.md`](.devcontainer/README.md) for the comparison.

---

## Command Reference

This project uses a layered command system: **Task** (convenience) → **Hatch** (environment) → **Tool** (execution).

### Quick Reference

| Task             | Command               | What it does                    |
| ---------------- | --------------------- | ------------------------------- |
| Run tests        | `task test`           | pytest (unit tests only)        |
| Tests + coverage | `task test:cov`       | pytest with coverage report     |
| Test matrix      | `task test:matrix`    | pytest across Python 3.11-3.13  |
| Lint             | `task lint`           | ruff check (report issues)      |
| Lint + fix       | `task lint:fix`       | ruff check with auto-fix        |
| Format           | `task fmt`            | ruff format                     |
| Type check       | `task typecheck`      | mypy strict mode                |
| All checks       | `task check`          | lint + typecheck + test         |
| Security         | `task security`       | bandit security scan            |
| Docs serve       | `task docs:serve`     | Local docs at localhost:8000    |
| Docs build       | `task docs:build`     | Build docs (strict mode)        |
| Pre-commit       | `task pre-commit:run` | Run all hooks manually          |
| Commit           | `task commit`         | Interactive conventional commit |

### Without Task Installed

If you don't have Task, use Hatch directly:

```bash
hatch run test              # Instead of: task test
hatch run lint              # Instead of: task lint
hatch run fmt               # Instead of: task fmt
hatch run typecheck         # Instead of: task typecheck
hatch run docs:serve        # Instead of: task docs:serve
```

### Direct Tool Execution

If you're already in an activated environment (`hatch shell` or `.venv`):

```bash
pytest                      # Run tests directly
ruff check src/ tests/      # Lint directly
ruff format src/ tests/     # Format directly
mypy src/                   # Type check directly
```

### How Commands Layer Together

```text
task test
  └→ hatch run test
       └→ pytest
            └→ Python
```

- **Task** (`Taskfile.yml`) — Human-friendly names, command chaining
- **Hatch** (`pyproject.toml`) — Manages virtualenv, runs commands inside it
- **Tool** — The actual linter/tester/formatter

For a deeper explanation, see [docs/notes/learning.md](docs/notes/learning.md) ("Command Workflow" section).

---

## Quality Pipeline Overview

Every change passes through multiple layers of automated checks before reaching `main`. This catches issues progressively — fast feedback first, comprehensive checks later.

```text
 You write code
      │
      ▼
┌─────────────────────────────────────────┐
│  Stage 1: Editor (real-time)            │
│  Pylance/Pyright, Ruff extension        │
└─────────────┬───────────────────────────┘
              │  git commit
              ▼
┌─────────────────────────────────────────┐
│  Stage 2: Pre-commit hooks (local)      │
│  Ruff, mypy, bandit, file checks        │
└─────────────┬───────────────────────────┘
              │  git push
              ▼
┌─────────────────────────────────────────┐
│  Stage 3: CI workflows (GitHub)         │
│  Lint, test, typecheck, security, spell │
└─────────────┬───────────────────────────┘
              │  open PR
              ▼
┌─────────────────────────────────────────┐
│  Stage 4: PR-specific checks            │
│  PR title, dependency review, labeler   │
└─────────────┬───────────────────────────┘
              │  approved & merged
              ▼
┌─────────────────────────────────────────┐
│  Stage 5: Post-merge (main)             │
│  Changelog, release (on tag)            │
└─────────────────────────────────────────┘
```

---

## Stage 1: Writing Code (Editor)

These tools provide **real-time feedback** as you type — no commands needed.

| Tool                  | What it does                                   | How it helps                                      |
| --------------------- | ---------------------------------------------- | ------------------------------------------------- |
| **Pylance / Pyright** | Type checking, IntelliSense, import resolution | Catches type errors and missing imports instantly |
| **Ruff extension**    | Inline lint warnings and auto-format on save   | Shows style issues and potential bugs as you type |

**Setup:** Install the [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) and [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) VS Code extensions. These are optional but strongly recommended — most issues they catch would otherwise fail at a later stage.

---

## Stage 2: Pre-commit Hooks (Local)

When you run `git commit`, pre-commit hooks run **automatically** and block the commit if anything fails. This is your last line of defense before code leaves your machine.

| Hook                                     | What it checks                                             |
| ---------------------------------------- | ---------------------------------------------------------- |
| **trailing-whitespace**                  | Removes trailing whitespace                                |
| **end-of-file-fixer**                    | Ensures files end with a newline                           |
| **check-yaml / check-toml / check-json** | Validates config file syntax                               |
| **check-added-large-files**              | Blocks files over 1 MB                                     |
| **check-merge-conflict**                 | Catches leftover conflict markers                          |
| **detect-private-key**                   | Prevents accidental secret commits                         |
| **debug-statements**                     | Catches leftover `breakpoint()` / `pdb` imports            |
| **Ruff (lint + format)**                 | Linting with auto-fix and formatting                       |
| **mypy**                                 | Static type checking on `src/`                             |
| **Bandit**                               | Security analysis (SQL injection, hardcoded secrets, etc.) |

**If a hook fails:** Some hooks (Ruff, trailing-whitespace) auto-fix the file. Stage the fixes with `git add` and commit again. Others (mypy, bandit) require you to fix the code manually.

**Bypassing hooks** (use sparingly): `git commit --no-verify`

**Run hooks manually** without committing:

```bash
task pre-commit:run          # or: hatch run pre-commit run --all-files
```

---

## Stage 3: Push & CI Workflows

After pushing your branch, GitHub Actions workflows run automatically on every push and PR to `main`.

| Workflow           | What it does                                          |
| ------------------ | ----------------------------------------------------- |
| **lint-format**    | Runs Ruff linter and formatter checks                 |
| **test**           | Runs pytest across Python 3.11, 3.12, and 3.13        |
| **type-check**     | Runs mypy in strict mode against `src/`               |
| **coverage**       | Measures test coverage and uploads to Codecov         |
| **security-audit** | Runs pip-audit against vulnerability databases        |
| **codeql**         | GitHub's static analysis for security vulnerabilities |
| **spellcheck**     | Catches typos with codespell                          |
| **docs**           | Builds documentation (when docs files change)         |

These workflows **must all pass** before a PR can be merged. If CI fails, check the workflow logs in the PR's "Checks" tab.

> **Why do CI checks duplicate pre-commit?** Pre-commit can be bypassed (`--no-verify`) or skipped if not installed. CI is the authoritative gate — it runs regardless.

---

## Stage 4: Pull Request Checks

These checks run **only on pull requests**, not on plain pushes.

| Workflow              | What it does                                                                        |
| --------------------- | ----------------------------------------------------------------------------------- |
| **pr-title**          | Validates the PR title follows conventional commit format (e.g., `feat: add login`) |
| **dependency-review** | Flags newly added dependencies with known vulnerabilities or restrictive licenses   |
| **labeler**           | Auto-labels the PR based on which files changed                                     |

### PR guidelines

1. Keep PRs focused — one logical change per PR
2. Write a clear description: what changed, why, and any relevant issue numbers
3. Ensure your branch is up to date with `main`
4. Request a review once all checks pass

See [docs/development/pull-requests.md](docs/development/pull-requests.md) for detailed PR conventions.

---

## Stage 5: Merge to Main

After approval and merge, additional automation runs:

| Workflow           | What it does                                                                    |
| ------------------ | ------------------------------------------------------------------------------- |
| **release-please** | Scans new commits on `main`, creates a Release PR with CHANGELOG + version bump |
| **release**        | Builds and publishes the package when a version tag (`v*.*.*`) is pushed        |

This is why commit message format matters — the changelog is generated directly from your commit messages.

For the full release workflow (including how the two PRs work), see [Releasing](docs/releasing.md).

---

## Commit Messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/).

### Format

```text
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type       | Description                                             |
| ---------- | ------------------------------------------------------- |
| `feat`     | A new feature                                           |
| `fix`      | A bug fix                                               |
| `docs`     | Documentation only changes                              |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test`     | Adding or updating tests                                |
| `chore`    | Maintenance (deps, CI config, tooling)                  |
| `ci`       | CI/CD workflow changes                                  |
| `style`    | Formatting changes (no logic change)                    |

### Examples

```bash
git commit -m "feat: add user authentication"
git commit -m "fix(cli): handle missing config file gracefully"
git commit -m "docs: update contributing guide"
git commit -m "ci: add bandit to pre-commit hooks"
```

### Commit Template (optional)

This repo includes a `.gitmessage.txt` commit template that pre-fills your editor with the suggested format and prompts for Why / What changed / How tested.

```bash
# Activate (for this repo only)
git config commit.template .gitmessage.txt

# Deactivate
git config --unset commit.template
```

Once activated, running `git commit` (without `-m`) opens your editor with the template. All `#` lines are comments and are stripped from the final message.

> **Note:** `git commit -m "..."` bypasses the template entirely — it only appears when Git opens an editor.

### Commitizen (optional)

[Commitizen](https://commitizen-tools.github.io/commitizen/) provides an interactive prompt that walks you through writing a properly formatted commit message:

```bash
pipx install commitizen
cz commit
```

This is entirely optional — write commits manually if you prefer. The PR title check and changelog generation only require the format, not the tool.

---

## Further Reading

This contributing guide covers the essentials. For deeper dives:

| Topic                             | Document                                                                         |
| --------------------------------- | -------------------------------------------------------------------------------- |
| **Getting started**               | [docs/guide/getting-started.md](docs/guide/getting-started.md)                   |
| **Developer setup (detailed)**    | [docs/development/dev-setup.md](docs/development/dev-setup.md)                   |
| **Developer commands**            | [docs/development/developer-commands.md](docs/development/developer-commands.md) |
| **Command workflows**             | [docs/development/command-workflows.md](docs/development/command-workflows.md)   |
| **PR conventions**                | [docs/development/pull-requests.md](docs/development/pull-requests.md)           |
| **Release process**               | [docs/releasing.md](docs/releasing.md)                                           |
| **CI/CD workflows**               | [docs/workflows.md](docs/workflows.md)                                           |
| **Tooling overview**              | [docs/tooling.md](docs/tooling.md)                                               |
| **Architecture & design**         | [docs/design/architecture.md](docs/design/architecture.md)                       |
| **Tool decisions**                | [docs/design/tool-decisions.md](docs/design/tool-decisions.md)                   |
| **Architecture Decision Records** | [docs/adr/README.md](docs/adr/README.md)                                         |
| **Repository layout**             | [docs/repo-layout.md](docs/repo-layout.md)                                       |
| **Troubleshooting**               | [docs/guide/troubleshooting.md](docs/guide/troubleshooting.md)                   |
| **Using this template**           | [docs/USING_THIS_TEMPLATE.md](docs/USING_THIS_TEMPLATE.md)                       |
| **Container setup**               | [.devcontainer/README.md](.devcontainer/README.md)                               |

---

## Reporting Issues

When reporting issues, please include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Python version and operating system
- Any relevant error messages or logs

---

## Code of Conduct

Please be respectful and constructive in all interactions. See our [Code of Conduct](CODE_OF_CONDUCT.md) for details.

---

## License

By contributing to this project, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
