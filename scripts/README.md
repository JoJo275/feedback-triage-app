# Scripts

<!-- TODO (template users): Remove scripts you don't need and add your own.
     Update this README table when adding or removing scripts. -->

Utility scripts for development and maintenance.

## Contents

| Script                                                         | Description                                                              |
| -------------------------------------------------------------- | ------------------------------------------------------------------------ |
| [\_imports.py](_imports.py)                                    | Shared import helper for loading sibling modules safely                  |
| [\_progress.py](_progress.py)                                  | Shared progress-indicator utilities (ProgressBar, Spinner)               |
| [\_colors.py](_colors.py)                                      | Shared ANSI color utilities (color detection, Colors class)              |
| [\_container_common.py](_container_common.py)                  | Shared container-test utilities (Docker/Podman detection, cleanup)        |
| [\_doctor_common.py](_doctor_common.py)                        | Shared doctor-family utilities (version lookup, path/hook checks)        |
| [\_ui.py](_ui.py)                                              | Shared dashboard UI module (themed headers, sections, tables, footers)   |
| [apply_labels.py](apply_labels.py)                             | Apply GitHub labels from JSON                                            |
| [apply-labels.sh](apply-labels.sh)                             | Shell wrapper for label application                                      |
| [archive_todos.py](archive_todos.py)                           | Archive completed TODO items from todo.md                                |
| [auto_chmod_scripts.py](precommit/auto_chmod_scripts.py)      | Auto-fix executable bit on staged shebang scripts                        |
| [bootstrap.py](bootstrap.py)                                   | One-command setup for fresh clones                                       |
| [changelog_check.py](changelog_check.py)                       | Validate CHANGELOG.md has an entry for the current PR                    |
| [check_known_issues.py](check_known_issues.py)                 | Flag stale Resolved entries in docs/known-issues.md                      |
| [check_local_imports.py](precommit/check_local_imports.py)     | Enforce local-module section comment in scripts                          |
| [check_nul_bytes.py](precommit/check_nul_bytes.py)             | Detect NUL (0x00) bytes in staged files                                  |
| [check_python_support.py](check_python_support.py)             | Validate Python version support is consistent across config files        |
| [check_todos.py](check_todos.py)                               | Scan for `TODO (template users)` comments                                |
| [clean.py](clean.py)                                           | Remove build artifacts and caches                                        |
| [customize.py](customize.py)                                   | Interactive project customization — replaces boilerplate placeholders    |
| [dep_versions.py](dep_versions.py)                             | Show/update dependency versions in pyproject.toml and requirements files |
| [generate_command_reference.py](generate_command_reference.py) | Generate docs/reference/commands.md from project commands                |
| [doctor.py](doctor.py)                                         | Print diagnostics bundle for bug reports                                 |
| [env_doctor.py](env_doctor.py)                                 | Environment health check + extended project consistency checks           |
| [git_doctor.py](git_doctor.py)                                 | Git-focused health check and information dashboard                       |
| [repo_doctor.py](repo_doctor.py)                               | Warn-only repo health checker driven by `.repo-doctor.toml` rules        |
| [repo_sauron.py](repo_sauron.py)                               | Repository statistics dashboard — file counts, git history, sizes        |
| [env_inspect.py](env_inspect.py)                               | Environment and dependency inspector — packages, versions, PATH          |
| [test_containerfile.py](test_containerfile.py)                 | Test the Containerfile: build image, validate, clean up                  |
| [test_containerfile.sh](test_containerfile.sh)                 | Bash equivalent of test_containerfile.py                                 |
| [test_docker_compose.py](test_docker_compose.py)               | Test docker compose stack: build, run, validate, clean up                |
| [test_docker_compose.sh](test_docker_compose.sh)               | Bash equivalent of test_docker_compose.py                                |
| [workflow_versions.py](workflow_versions.py)                   | Show/update version comments on SHA-pinned GitHub Actions                |
| [\_env_collectors/](_env_collectors/)                           | Environment data collector plugins (20 modules) for the dashboard        |
| [precommit/](precommit/)                                       | Custom pre-commit hook scripts                                           |
| [sql/](sql/)                                                   | SQL scripts for database operations                                      |

## SQL Scripts

| Script                                             | Description                    |
| -------------------------------------------------- | ------------------------------ |
| [sql/reset.sql](sql/reset.sql)                     | Reset database (drop/recreate) |
| [sql/scratch.example.sql](sql/scratch.example.sql) | Template for ad-hoc queries    |

## Usage

### Global Entry Points (spb-\* commands)

All scripts are also available as **global CLI commands** when the package is
installed with `pipx install .` (or `pip install .`). This lets you run them
from **any repository**, not just this one.

```bash
# Install globally (one-time)
pipx install .

# Now run scripts from any directory:
spb-doctor          # instead of python scripts/doctor.py
spb-git-doctor      # instead of python scripts/git_doctor.py
spb-env-doctor      # instead of python scripts/env_doctor.py
spb-repo-doctor     # instead of python scripts/repo_doctor.py
spb-clean           # instead of python scripts/clean.py
spb-dashboard       # instead of hatch run dashboard:serve
```

The entry point automatically sets `SPB_REPO_ROOT` to your current working
directory, so scripts discover the target repo from wherever you run them.
All arguments are forwarded: `spb-git-doctor --json` works the same as
`python scripts/git_doctor.py --json`.

For the full list of 21 commands, see the
[Global Entry Points guide](../docs/guide/entry-points.md).

### Running scripts directly

```bash
# One-command setup for fresh clones
python scripts/bootstrap.py

# Run a Python script
python scripts/apply_labels.py

# Customize the template for your project
python scripts/customize.py
python scripts/customize.py --dry-run

# Run repo health checks
python scripts/repo_doctor.py

# Git health check and info dashboard
python scripts/git_doctor.py
python scripts/git_doctor.py --json

python scripts/repo_doctor.py --category ci --level warn
python scripts/repo_doctor.py --fix

# Clean build artifacts and caches
python scripts/clean.py
python scripts/clean.py --dry-run

# Print diagnostics bundle for bug reports
python scripts/doctor.py
python scripts/doctor.py --markdown   # For GitHub issues

# Archive completed TODO items
python scripts/archive_todos.py

# Manage SHA-pinned GitHub Actions versions
python scripts/workflow_versions.py                    # Show all actions
python scripts/workflow_versions.py show --offline     # Skip GitHub API
python scripts/workflow_versions.py show --json        # JSON output
python scripts/workflow_versions.py show --filter stale      # Only stale actions
python scripts/workflow_versions.py show --filter upgradable # Only upgradable
python scripts/workflow_versions.py show --quiet       # CI mode: exit 1 if issues
python scripts/workflow_versions.py update-comments    # Sync comments + add descriptions
python scripts/workflow_versions.py upgrade            # Upgrade all to latest
python scripts/workflow_versions.py upgrade --dry-run  # Preview upgrades
python scripts/workflow_versions.py upgrade actions/checkout v6.1.0  # Specific version

# Test containers
python scripts/test_containerfile.py           # Build + validate Containerfile image
python scripts/test_containerfile.py --dry-run  # Preview steps
python scripts/test_containerfile.py --keep     # Keep image after test
python scripts/test_docker_compose.py           # Build + validate compose stack
python scripts/test_docker_compose.py --dry-run # Preview steps
bash scripts/test_containerfile.sh              # Bash equivalent
bash scripts/test_docker_compose.sh             # Bash equivalent

# Run SQL against database
sqlite3 var/app.sqlite3 < scripts/sql/reset.sql

# Repository statistics dashboard
python scripts/repo_sauron.py
python scripts/repo_sauron.py --json

# Environment and dependency inspector
python scripts/env_inspect.py
python scripts/env_inspect.py --section packages
python scripts/env_inspect.py --section entrypoints
python scripts/env_inspect.py --section path
python scripts/env_inspect.py --json
```

## Conventions

- **Shebang:** Include `#!/usr/bin/env python3` and mark executable:
  `git add --chmod=+x scripts/my_script.py`
- **Naming:** `snake_case.py` for Python scripts, `kebab-case.sh` for shell
- **Standalone:** Scripts must not import from `src/simple_python_boilerplate/`
  — they should work without installing the package
- **`--dry-run`:** Destructive scripts should support `--dry-run` to preview changes
- **Exit codes:** 0 = success, non-zero = failure (for CI compatibility)
- **Version constant:** Include `SCRIPT_VERSION = "x.y.z"` near the top of
  each script. Bump when behavior changes. Useful for debugging and
  `--version` flags.
- **Argparse for all arguments:** Use `argparse` for all CLI parsing —
  including positional arguments — avoid ad-hoc `sys.argv` parsing. This
  gives `--help` and `--version` for free and keeps interfaces consistent.
  This applies to pre-commit hooks in `precommit/` too.
- **`__main__` guard:** Wrap execution in `if __name__ == "__main__":` so
  the script can be imported for testing without side effects.
- **Docstring:** Every script should have a module-level docstring explaining
  what it does, when to use it, and any prerequisites.
- **Logging over print:** Prefer `logging` over bare `print()` for status
  messages. Use `print()` only for primary output (e.g., JSON, tables).
- **Idempotency:** Scripts should be safe to run multiple times. Don't
  create duplicates, corrupt state, or fail on re-runs.
- **Error messages:** Write actionable error messages that tell the user
  what went wrong _and_ how to fix it. Avoid bare tracebacks when a
  human-readable message is possible.

See [ADR 031: Script conventions](../docs/adr/031-script-conventions.md) for the full rationale.

## See Also

- [Taskfile.yml](../Taskfile.yml) — Task runner shortcuts for common scripts
- [precommit/](precommit/) — Custom pre-commit hook scripts
- [sql/](sql/) — Ad-hoc SQL experimentation scripts
