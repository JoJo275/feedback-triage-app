# ADR 031: Script Conventions

## Status

Accepted

## Context

The `scripts/` directory has grown to 14+ Python scripts plus shell wrappers
and subdirectories. Without conventions, scripts become inconsistent in naming,
argument handling, output formatting, and error behavior — making them harder
to maintain, discover, and compose.

### Current inventory

```
scripts/
├── apply_labels.py      # Apply GitHub labels from JSON definitions
├── apply-labels.sh      # Shell wrapper for apply_labels.py
├── archive_todos.py     # Archive completed TODOs
├── bootstrap.py         # One-command project setup
├── changelog_check.py   # Validate CHANGELOG entries
├── check_todos.py       # Scan for TODO comments
├── clean.py             # Remove build artifacts and caches
├── customize.py         # Interactive project customization
├── dep_versions.py      # Show dependency versions
├── doctor.py            # Diagnostics bundle for bug reports
├── env_doctor.py        # Environment health checks
├── repo_doctor.py       # Repository health checks (configurable)
├── workflow_versions.py # Show SHA-pinned action versions
├── precommit/           # Pre-commit hook scripts
├── sql/                 # SQL utility scripts
└── README.md            # Script inventory and usage guide
```

### Forces

- Scripts are standalone tools, not part of the installed package — they
  must work without `pip install -e .`
- Some scripts are called from CI, some from Taskfile, some directly by
  developers
- Consistency in argument parsing, exit codes, and output formatting
  reduces cognitive load
- New contributors should be able to add a script that "fits in" by
  following clear patterns

## Decision

Establish the following conventions for all scripts in `scripts/`:

### Naming

- **Python scripts:** `snake_case.py` (e.g., `dep_versions.py`,
  `check_todos.py`)
- **Shell scripts:** `kebab-case.sh` (e.g., `apply-labels.sh`)
- **Subdirectories:** Group related scripts by domain (`precommit/`,
  `sql/`)
- Names should be verb-first or noun-descriptive: `clean.py`,
  `doctor.py`, `bootstrap.py`

### Shebang and permissions

All scripts with a shebang (`#!/usr/bin/env python3`) must be marked
executable in git:

```bash
git add --chmod=+x scripts/my_script.py
```

The pre-commit hook `check-shebang-scripts-are-executable` enforces this.

### Argument parsing

- Use `argparse` for all scripts that accept arguments — including
  pre-commit hooks in `scripts/precommit/`
- Always include `--version` (print version and exit)
- Always include `--dry-run` where the script modifies files or state
- Include `-q` / `--quiet` for scripts with verbose output
- Use `description=` and `epilog=` in `ArgumentParser` for self-documenting
  help text

### Exit codes

| Code | Meaning                                          |
| :--- | :----------------------------------------------- |
| `0`  | Success                                          |
| `1`  | General error or check failure                   |
| `2`  | Usage error (argparse default for bad arguments) |

### Output conventions

- **Normal output** goes to `stdout`
- **Errors and warnings** go to `stderr`
- **Quiet mode** (`--quiet`) suppresses informational output; errors still
  go to `stderr`
- **Dry-run mode** prefixes output with `[DRY RUN]` or equivalent to make
  it clear no changes were made

### Logging

- Use `print()` for simple scripts with minimal output
- Use the `logging` module for scripts with configurable verbosity
- Never use `print()` for error messages — use `sys.stderr` or `logging`

### Independence

Scripts are **standalone** — they do not import from
`simple_python_boilerplate` (the installed package) and do not require
the package to be installed. They may import from the standard library
and from each other (within `scripts/`).

### Taskfile integration

Scripts that are commonly used have Taskfile shortcuts:

| Script                 | Taskfile command        |
| :--------------------- | :---------------------- |
| `bootstrap.py`         | `task setup`            |
| `customize.py`         | `task customize`        |
| `clean.py`             | `task clean`            |
| `dep_versions.py`      | `task deps:versions`    |
| `workflow_versions.py` | `task actions:versions` |

Not every script needs a Taskfile entry. The boundary: if a script is
used frequently during development, give it a task. If it's used
occasionally or only from CI, calling it directly is fine.

### Documentation

- Each script should have a module-level docstring explaining what it does
- `scripts/README.md` maintains a full inventory with one-line descriptions
- Scripts with CLI arguments should have helpful `--help` output
  (via `argparse`)

## Alternatives Considered

### Scripts as package entry points

Define scripts as `[project.scripts]` entry points in `pyproject.toml` so
they install as CLI commands.

**Rejected because:** These are development/maintenance scripts, not
user-facing CLI tools. Entry points require the package to be installed,
adding friction. Standalone scripts work immediately after cloning.

### invoke / fabric

Use a Python task automation library for scripts.

**Rejected because:** Adds a dependency, overlaps with Taskfile's role,
and doesn't solve the core problem of inconsistent script conventions.

### All scripts in a single file

Consolidate utility functions into one large script with subcommands.

**Rejected because:** Separate scripts are easier to maintain, test, and
compose. Each script has a focused responsibility.

## Consequences

### Positive

- Consistency — new scripts follow established patterns
- Discoverability — `scripts/README.md` and `--help` make scripts findable
- Safety — `--dry-run` prevents accidental damage
- CI-friendly — predictable exit codes and output streams
- Pre-commit enforces executable permissions on shebangs

### Negative

- Some boilerplate per script (argparse setup, shebang, docstring)
- Convention enforcement is social, not automated (no linter for script
  conventions)
- Taskfile integration requires manual sync when scripts are added/renamed

### Mitigations

- The boilerplate is small (~15 lines) and consistent
- PR review catches convention violations
- `copilot-instructions.md` documents the shebang → executable requirement

## Implementation

- [scripts/](../../scripts/) — Script directory
- [scripts/README.md](../../scripts/README.md) — Script inventory
- [Taskfile.yml](../../Taskfile.yml) — Task runner shortcuts
- [.pre-commit-config.yaml](../../.pre-commit-config.yaml) —
  `check-shebang-scripts-are-executable` hook

## References

- [ADR 017](017-task-runner.md) — Taskfile as task runner
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html)
- [scripts/README.md](../../scripts/README.md) — Full script inventory
