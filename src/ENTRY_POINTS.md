# CLI Entry Points (22 commands)

<!--
TODO (template users): After renaming the package with scripts/customize.py,
     update the `spb-` prefixes in pyproject.toml to match your project name
     (e.g., `myapp-doctor`, `myapp-clean`). Remove any commands you don't need.
-->

This file lists every CLI command defined in `pyproject.toml` under
`[project.scripts]`. Install the package (`pipx install .` or
`pip install -e .`) and all `spb-*` commands become available on your PATH.

For the full guide (how it works, argument forwarding, requirements for
target repos), see [docs/guide/entry-points.md](../docs/guide/entry-points.md).

---

## Where They Live

| Source module | Responsibility |
|---------------|---------------|
| `simple_python_boilerplate/entry_points.py` | **All 22 entry points** — core + script wrappers in one file |
| `simple_python_boilerplate/main.py` | Re-exports 4 core entry points (backward compat only) |
| `simple_python_boilerplate/scripts_cli.py` | Re-exports 18 script entry points (backward compat only) |

---

## Core Commands (main.py)

| # | Command | Function | What it does |
|---|---------|----------|-------------|
| 1 | `spb` | `main:main` | Primary CLI entry point (argparse → cli.py → engine.py) |
| 2 | `spb-version` | `main:print_version` | Print package and Python version |
| 3 | `spb-doctor` | `main:doctor` | Diagnose package environment and dev tools |
| 4 | `spb-start` | `main:start` | Bootstrap project setup (runs `scripts/bootstrap.py`) |

---

## Diagnostics & Health Checks (scripts_cli.py)

| # | Command | Function | Equivalent script |
|---|---------|----------|-------------------|
| 5 | `spb-git-doctor` | `scripts_cli:git_doctor` | `python scripts/git_doctor.py` |
| 6 | `spb-env-doctor` | `scripts_cli:env_doctor` | `python scripts/env_doctor.py` |
| 7 | `spb-repo-doctor` | `scripts_cli:repo_doctor` | `python scripts/repo_doctor.py` |
| 8 | `spb-diag` | `scripts_cli:doctor_bundle` | `python scripts/doctor.py` |
| 9 | `spb-env-inspect` | `scripts_cli:env_inspect` | `python scripts/env_inspect.py` |
| 10 | `spb-repo-stats` | `scripts_cli:repo_sauron` | `python scripts/repo_sauron.py` |

## Maintenance (scripts_cli.py)

| # | Command | Function | Equivalent script |
|---|---------|----------|-------------------|
| 11 | `spb-clean` | `scripts_cli:clean` | `python scripts/clean.py` |
| 12 | `spb-bootstrap` | `scripts_cli:bootstrap` | `python scripts/bootstrap.py` |
| 13 | `spb-dep-versions` | `scripts_cli:dep_versions` | `python scripts/dep_versions.py` |
| 14 | `spb-workflow-versions` | `scripts_cli:workflow_versions` | `python scripts/workflow_versions.py` |

## Validation (scripts_cli.py)

| # | Command | Function | Equivalent script |
|---|---------|----------|-------------------|
| 15 | `spb-check-todos` | `scripts_cli:check_todos` | `python scripts/check_todos.py` |
| 16 | `spb-check-python` | `scripts_cli:check_python_support` | `python scripts/check_python_support.py` |
| 17 | `spb-changelog-check` | `scripts_cli:changelog_check` | `python scripts/changelog_check.py` |
| 18 | `spb-check-issues` | `scripts_cli:check_known_issues` | `python scripts/check_known_issues.py` |

## Project Setup (scripts_cli.py)

| # | Command | Function | Equivalent script |
|---|---------|----------|-------------------|
| 19 | `spb-apply-labels` | `scripts_cli:apply_labels` | `python scripts/apply_labels.py` |
| 20 | `spb-archive-todos` | `scripts_cli:archive_todos` | `python scripts/archive_todos.py` |
| 21 | `spb-customize` | `scripts_cli:customize` | `python scripts/customize.py` |

## Web Dashboard (scripts_cli.py)

| # | Command | Function | Equivalent |
|---|---------|----------|------------|
| 22 | `spb-dashboard` | `scripts_cli:dashboard` | `hatch run dashboard:serve` |

---

## Adding a New Entry Point

1. Create (or reuse) a function in `main.py` or `scripts_cli.py`.
2. Register it in `pyproject.toml` under `[project.scripts]`:
   ```toml
   spb-my-command = "simple_python_boilerplate.scripts_cli:my_command"
   ```
3. Reinstall the package: `pip install -e .` or restart `hatch shell`.
4. Update this file, [docs/guide/entry-points.md](../docs/guide/entry-points.md),
   and `.github/copilot-instructions.md` with the new count.

## Removing an Entry Point

1. Delete the line from `[project.scripts]` in `pyproject.toml`.
2. Remove the wrapper function from `scripts_cli.py` (or `main.py`).
3. Reinstall the package.
4. Update this file and the docs.

---

## See Also

- [pyproject.toml](../pyproject.toml) — Canonical entry point definitions
- [entry_points.py](simple_python_boilerplate/entry_points.py) — All 22 entry points
- [main.py](simple_python_boilerplate/main.py) — Backward-compat re-exports (core)
- [scripts_cli.py](simple_python_boilerplate/scripts_cli.py) — Backward-compat re-exports (scripts)
- [docs/guide/entry-points.md](../docs/guide/entry-points.md) — Full user guide
- [scripts/README.md](../scripts/README.md) — Script inventory
