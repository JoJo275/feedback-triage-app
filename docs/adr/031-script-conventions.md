# ADR 031: Script Conventions

## Status

Accepted

## Context

The `scripts/` directory is retained from the template as project-wide
tooling. It has grown to 25+ Python scripts plus shell wrappers and
subdirectories. Without conventions, scripts drift in naming, argument
handling, output formatting, and error behaviour — making them harder
to maintain, discover, and compose.

### Current inventory (high level)

```text
scripts/
├── apply_labels.py         # Apply GitHub labels from JSON definitions
├── apply-labels.sh         # Shell wrapper for apply_labels.py
├── archive_todos.py        # Archive completed TODOs
├── bootstrap.py            # One-command project setup
├── changelog_check.py      # Validate CHANGELOG entries
├── check_known_issues.py   # Flag stale entries in known-issues.md
├── check_python_support.py # Verify Python support config consistency
├── check_todos.py          # Scan for TODO comments
├── clean.py                # Remove build artifacts and caches
├── customize.py            # Interactive project customisation (legacy)
├── dep_versions.py         # Show dependency versions
├── doctor.py               # Diagnostics bundle for bug reports
├── env_doctor.py           # Environment health checks
├── env_inspect.py          # Environment / package inspector
├── generate_command_reference.py  # Regenerate docs/reference/commands.md
├── git_doctor.py           # Git health dashboard
├── repo_doctor.py          # Repository health checks (configurable)
├── repo_sauron.py          # Repo audit / report generator
├── seed.py                 # (project-specific) seed demo feedback rows
├── test_containerfile.py   # Containerfile validation
├── test_docker_compose.py  # Compose stack validation
├── workflow_versions.py    # Show SHA-pinned action versions
├── _env_collectors/        # Plugin collectors used by env_inspect / dashboard
├── precommit/              # Pre-commit hook scripts
└── sql/                    # SQL utility scripts
```

Two things changed at the fork that affect this ADR:

1. The package being introspected is now `feedback_triage`, not
   `simple_python_boilerplate`.
2. Scripts must work without the project's runtime dependencies on
   `PATH`. Where they need them, they declare so with a PEP 723
   `# /// script` header or are invoked through `uv run`.

### Forces

- Scripts are standalone tools, not part of the installed package —
  they must work without `uv sync` / editable install.
- Some are called from CI, some from `Taskfile.yml`, some directly by
  developers.
- Consistency in argument parsing, exit codes, and output formatting
  reduces cognitive load.
- New contributors should be able to add a script that "fits in" by
  following clear patterns.

## Decision

The conventions below apply to every Python script in `scripts/`. The
project-specific `scripts/seed.py` follows them too.

### Naming

- **Python scripts:** `snake_case.py` (e.g. `dep_versions.py`,
  `check_todos.py`).
- **Shell wrappers:** `kebab-case.sh` (e.g. `apply-labels.sh`).
- **Subdirectories** group related scripts by domain (`_env_collectors/`,
  `precommit/`, `sql/`).
- The leading underscore on `_env_collectors`, `_imports.py`,
  `_doctor_common.py`, `_ui.py`, etc. signals **private — imported
  only by other scripts in this folder**. They are not stable
  interfaces.
- Names should be verb-first or noun-descriptive: `clean.py`,
  `doctor.py`, `bootstrap.py`.

### Shebang and permissions

All scripts with a shebang (`#!/usr/bin/env python3`) must be marked
executable in git:

```bash
git add --chmod=+x scripts/my_script.py
```

The pre-commit hook `check-shebang-scripts-are-executable` enforces
this.

### Argument parsing

- Use `argparse` for every script that takes arguments — including
  pre-commit hooks in `scripts/precommit/`.
- Always include `--version`.
- Always include `--dry-run` whenever the script writes files, mutates
  Git state, or hits the network.
- Include `-q` / `--quiet` for scripts with verbose output.
- Use `description=` and `epilog=` in `ArgumentParser` for
  self-documenting `--help` text.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | General failure / check failed |
| `2` | Usage error (argparse default) |

### Output

- **Normal output** → `stdout`.
- **Errors and warnings** → `stderr`.
- **Quiet mode** (`--quiet`) suppresses informational output; errors
  still go to `stderr`.
- **Dry-run mode** prefixes any "would do X" line with `[DRY RUN]` to
  make it clear no changes were made.

### Logging

- Use `print()` for simple scripts with minimal output.
- Use the `logging` module for scripts with configurable verbosity.
- Never use `print()` for error messages — use `sys.stderr` or
  `logging`.

### Independence and runtime

- Scripts do **not** import from `feedback_triage`. The doctor / env
  / dep helpers must work on a fresh clone before `uv sync`.
- Scripts that depend on third-party libraries declare them via PEP 723
  `# /// script` headers, so `uv run scripts/<name>.py` resolves the
  right env automatically.
- Scripts may import each other within `scripts/`. Common helpers live
  under leading-underscore modules.

### Taskfile integration

Frequently used scripts get a Taskfile shortcut. Currently:

| Script | Task |
| --- | --- |
| `bootstrap.py` | `task setup` |
| `clean.py` | `task clean` |
| `dep_versions.py` | `task deps:versions` |
| `workflow_versions.py` | `task actions:versions` |
| `seed.py` | `task seed` |
| `doctor.py` | `task doctor` |
| `env_doctor.py` | `task doctor:env` |
| `repo_doctor.py` | `task doctor:repo` |
| `git_doctor.py` | `task doctor:git` |

Boundary: if a script is used frequently during development, give it a
task. If it's used occasionally or only from CI, calling it directly
is fine. Single-shot or CI-only scripts (`changelog_check.py`,
`archive_todos.py`, etc.) are called directly; no task entry needed.

### Pre-commit hooks

Hooks under `scripts/precommit/` follow the same conventions.
`check-shebang-scripts-are-executable` enforces the executable bit on
shebang-bearing files.

### Documentation

- Each script should have a module-level docstring explaining what it
  does.
- [`scripts/README.md`](../../scripts/README.md) maintains a full
  inventory with one-line descriptions.
- Scripts with CLI arguments should have helpful `--help` output via
  `argparse`.

### Tests

Tests for the doctor / env / dep helpers live under
`tests/scripts/test_*.py` (added in Phase 1+ as the suite grows). They
run with the same pytest invocation as everything else.

## Alternatives Considered

### Promote scripts to `[project.scripts]` console entries

Define scripts as `[project.scripts]` entry points in `pyproject.toml`
so they install as CLI commands.

**Rejected for v1.0** because these are dev tooling, not user-facing
CLIs. Console entries require an installed package, which forces the
chicken-and-egg "doctor before install" tools to grow extra paths. The
template's `spb-*` console-script entries were dropped at the fork
(commented out in `[project.scripts]`); reconsider per-script if a
workflow proves the abstraction useful.

### `invoke` / `fabric`

Use a Python task automation library for scripts.

**Rejected because:** adds a dependency, overlaps with Taskfile's
role, and doesn't solve the core problem of inconsistent script
conventions.

### Replace scripts with a `nox` setup

**Rejected because:** Taskfile already does the runner role; `uv run`
already does the env-execution role. Adding `nox` would duplicate
both.

### Rewrite scripts as entries in `Taskfile.yml`

**Rejected because:** Taskfile is good for short pipelines, not for
multi-hundred-line Python with rich output and argument parsing.

### All scripts in a single file with subcommands

**Rejected because:** separate scripts are easier to maintain, test,
and compose. Each script has a focused responsibility.

## Consequences

### Positive

- Consistency — new scripts follow established patterns.
- Discoverability — `scripts/README.md` and `--help` make scripts
  findable.
- Safety — `--dry-run` prevents accidental damage.
- CI-friendly — predictable exit codes and output streams.
- A new contributor can read this ADR and produce a script that fits.
- Pre-commit enforces the executable-bit invariant.

### Negative

- Some boilerplate per script (argparse setup, docstring, shebang).
  It's about 15 lines and consistent.
- Convention enforcement is social, not automated, beyond the
  executable bit. PR review is the backstop.
- Taskfile integration requires manual sync when scripts are
  added/renamed.

### Mitigations

- The boilerplate is small and consistent across the directory.
- PR review catches convention violations.
- [`copilot-instructions.md`](../../.github/copilot-instructions.md)
  documents the shebang → executable requirement.

## Implementation

- [`scripts/`](../../scripts/) — script directory
- [`scripts/README.md`](../../scripts/README.md) — running inventory
- [`Taskfile.yml`](../../Taskfile.yml) — task shortcuts
- [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) —
  `check-shebang-scripts-are-executable`

## See also

- [ADR 008](008-pre-commit-hooks.md) — pre-commit framework
- [ADR 017](017-task-as-runner.md) — Task as the developer runner
- [ADR 055](055-uv-as-project-manager.md) — `uv run` for env-aware
  script execution
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html)
- [PEP 723](https://peps.python.org/pep-0723/) — inline script metadata
