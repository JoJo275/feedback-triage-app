# Global Entry Points

<!-- TODO (template users): After renaming the package with
     scripts/customize.py, update the `fta-` prefixes in pyproject.toml
     to match your project name (e.g., `myapp-git-doctor`). -->

Install this package once and get access to **21 CLI commands** you can run
from any repository on your machine. Each command inspects whichever repo
your terminal is currently in — not the repo the package was installed from.

---

## Quick Setup

Install globally with [pipx](https://pipx.pypa.io/) (recommended):

```bash
# From a local clone of the template repo
pipx install /path/to/simple-python-boilerplate

# Or install directly from GitHub
pipx install git+https://github.com/JoJo275/simple-python-boilerplate.git
```

Or install with pip into a specific environment:

```bash
pip install /path/to/simple-python-boilerplate
```

After installation, all `fta-*` commands are available globally.

---

## How It Works

Entry points are defined in `pyproject.toml` under `[project.scripts]`.
When you install the package, pip/pipx creates executable wrappers for
each entry point on your `PATH`.

Each script command:

1. Locates the **bundled copy** of the script inside the installed package
2. Sets the `FEEDBACK_TRIAGE_REPO_ROOT` environment variable to your **current working
   directory**
3. Runs the script as a subprocess with `cwd` set to your current directory

This means `fta-git-doctor` run from `~/projects/my-app/` will show git
info for `my-app`, not for the template repo where the package was built.

```text
┌──────────────────────────────────┐
│  Your terminal (CWD: ~/my-app)   │
│  $ fta-git-doctor                │
│            │                     │
│            ▼                     │
│  Entry point wrapper             │
│  (scripts_cli.py)                │
│            │                     │
│   sets FEEDBACK_TRIAGE_REPO_ROOT=~/my-app    │
│   sets PYTHONPATH to bundled     │
│   scripts directory              │
│            │                     │
│            ▼                     │
│  Runs: python git_doctor.py      │
│  (from installed package)        │
│  (CWD = ~/my-app)               │
│            │                     │
│            ▼                     │
│  _imports.find_repo_root()       │
│  checks FEEDBACK_TRIAGE_REPO_ROOT env var    │
│  → finds ~/my-app/pyproject.toml │
│  → inspects ~/my-app repo        │
└──────────────────────────────────┘
```

### Requirements for Target Repos

The scripts look for `pyproject.toml` to identify the repo root. Most
commands work on any Python project. Some features depend on specific files:

| Command | Requires in target repo |
|---------|------------------------|
| `fta-git-doctor` | Git repository (`.git/`) |
| `fta-repo-doctor` | `repo_doctor.d/*.toml` rule files (optional — warns if missing) |
| `fta-env-doctor` | `pyproject.toml` |
| `fta-dep-versions` | `pyproject.toml` with `[project.optional-dependencies]` |
| `fta-workflow-versions` | `.github/workflows/*.yml` |
| `fta-dashboard` | `pyproject.toml` + `scripts/_env_collectors/` |
| `fta-apply-labels` | `labels/*.json` |
| `fta-changelog-check` | `CHANGELOG.md` |
| Most others | `pyproject.toml` (any Python project) |

---

## Available Commands

### Core

| Command | Description |
|---------|------------|
| `fta` | Primary CLI entry point |
| `fta-version` | Print version information |
| `fta-doctor` | Diagnose package environment (built-in checks) |
| `fta-start` | Bootstrap project setup (runs `scripts/bootstrap.py`) |

### Diagnostics & Health Checks

| Command | Description | Equivalent script |
|---------|------------|-------------------|
| `fta-git-doctor` | Git health check and information dashboard | `python scripts/git_doctor.py` |
| `fta-env-doctor` | Development environment health check | `python scripts/env_doctor.py` |
| `fta-repo-doctor` | Repository structure health checks | `python scripts/repo_doctor.py` |
| `fta-diag` | Print diagnostics bundle for bug reports | `python scripts/doctor.py` |
| `fta-env-inspect` | Environment and dependency inspector | `python scripts/env_inspect.py` |
| `fta-repo-stats` | Repository statistics dashboard | `python scripts/repo_sauron.py` |

### Maintenance

| Command | Description | Equivalent script |
|---------|------------|-------------------|
| `fta-clean` | Remove build artifacts and caches | `python scripts/clean.py` |
| `fta-bootstrap` | One-command setup for fresh clones | `python scripts/bootstrap.py` |
| `fta-dep-versions` | Show/update dependency versions | `python scripts/dep_versions.py` |
| `fta-workflow-versions` | Show/update SHA-pinned GitHub Actions | `python scripts/workflow_versions.py` |

### Validation

| Command | Description | Equivalent script |
|---------|------------|-------------------|
| `fta-check-todos` | Scan for TODO (template users) comments | `python scripts/check_todos.py` |
| `fta-check-python` | Validate Python version support consistency | `python scripts/check_python_support.py` |
| `fta-changelog-check` | Validate CHANGELOG.md has entry for PR | `python scripts/changelog_check.py` |
| `fta-check-issues` | Flag stale resolved entries in known-issues.md | `python scripts/check_known_issues.py` |

### Project Setup

| Command | Description | Equivalent script |
|---------|------------|-------------------|
| `fta-apply-labels` | Apply GitHub labels from JSON definitions | `python scripts/apply_labels.py` |
| `fta-archive-todos` | Archive completed TODO items | `python scripts/archive_todos.py` |
| `fta-customize` | Interactive project customization | `python scripts/customize.py` |

### Web Dashboard

| Command | Description | Equivalent |
|---------|------------|------------|
| `fta-dashboard` | Start environment inspection web dashboard | `hatch run dashboard:serve` |

---

## Arguments Are Forwarded

All commands forward arguments to the underlying script:

```bash
# These are equivalent:
fta-git-doctor --json
python scripts/git_doctor.py --json

fta-clean --dry-run
python scripts/clean.py --dry-run

fta-dep-versions show --json
python scripts/dep_versions.py show --json

fta-git-doctor --help
python scripts/git_doctor.py --help
```

---

## Uninstalling

```bash
pipx uninstall simple-python-boilerplate
# or
pip uninstall simple-python-boilerplate
```

---

## Technical Details

### Package Structure

The `scripts/` and `tools/` directories are bundled into the wheel at
build time via `[tool.hatch.build.targets.wheel.force-include]` in
`pyproject.toml`:

```text
feedback_triage/
├── _bundled_scripts/
│   ├── scripts/        ← All utility scripts
│   └── repo_doctor.d/  ← Diagnostic rule definitions
├── _bundled_tools/
│   └── tools/          ← Dashboard web app
├── scripts_cli.py      ← Entry point wrappers
├── main.py             ← Core entry points (fta, fta-doctor, etc.)
└── ...                 ← Package source code
```

### Environment Variable: `FEEDBACK_TRIAGE_REPO_ROOT`

When set, `scripts/_imports.py` `find_repo_root()` uses this path as the
repo root instead of walking up from the script file location. Entry points
set this automatically. You can also set it manually:

```bash
FEEDBACK_TRIAGE_REPO_ROOT=/path/to/repo fta-git-doctor
```

---

## See Also

- [pyproject.toml](../../pyproject.toml) — Entry point definitions
- [scripts_cli.py](../../src/feedback_triage/scripts_cli.py) — Entry point wrappers
- [scripts/README.md](../../scripts/README.md) — Script inventory and usage
- [Development Setup](../development/dev-setup.md) — Local development guide
