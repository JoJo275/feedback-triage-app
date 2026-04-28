# ADR 031: Script Conventions

## Status

Accepted

## Context

`scripts/` is retained from the template as a project-wide tooling
library: `bootstrap.py`, the doctor family (`doctor.py`,
`env_doctor.py`, `repo_doctor.py`, `git_doctor.py`), env collectors
(`_env_collectors/*`), dependency helpers (`dep_versions.py`,
`workflow_versions.py`, `check_python_support.py`), container test
runners (`test_containerfile.py`, `test_docker_compose.py`),
spec-related helpers (`archive_todos.py`, `check_todos.py`,
`changelog_check.py`, `check_known_issues.py`), and pre-commit hooks
under `scripts/precommit/`.

Two things changed at the fork that affect this ADR:

1. The package being introspected is now `feedback_triage`, not
   `simple_python_boilerplate`.
2. Scripts must work without the project's runtime dependencies on
   `PATH`. Where they need them, they declare so with a
   `# /// script` PEP 723 header or are invoked through `uv run`.

Without conventions, scripts drift in shape (argparse vs. plain
`sys.argv`, exit codes, where output goes), and adding the next one
becomes an exercise in deciding everything from scratch.

## Decision

The conventions below apply to every Python script in `scripts/`.
Project-specific scripts (only `scripts/seed.py` in v1.0) follow them
too.

### Naming

- Python scripts: `snake_case.py`.
- Shell wrappers: `kebab-case.sh`.
- Subdirectories group related scripts: `_env_collectors/`, `precommit/`,
  `sql/`.
- The leading underscore on `_env_collectors`, `_imports.py`,
  `_doctor_common.py`, `_ui.py`, etc. signals "private — imported only
  by other scripts in this folder". They are not stable interfaces.

### Argument parsing

- Use `argparse` for any script that takes arguments.
- Always include `--version`.
- Include `--dry-run` whenever the script writes files, mutates Git
  state, or hits the network.
- Include `-q` / `--quiet` for scripts with verbose output.
- Use `description=` and `epilog=` to make `--help` self-documenting.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | General failure / check failed |
| `2` | Usage error (argparse default) |

### Output

- Normal output → `stdout`.
- Errors and warnings → `stderr`.
- `--quiet` suppresses informational output but never errors.
- `--dry-run` prefixes any "would do X" line with `[DRY RUN]`.

### Independence and runtime

- Scripts do **not** import from `feedback_triage`. The doctor / env /
  dep helpers must work on a fresh clone before `uv sync`.
- Scripts that depend on third-party libraries declare them via PEP 723
  `# /// script` headers, so `uv run scripts/<name>.py` resolves the
  right env automatically.
- Scripts may import each other within `scripts/`. Common helpers live
  under leading-underscore modules.

### Taskfile integration

Frequently used scripts get a Taskfile shortcut. Currently:

| Script | Task |
|---|---|
| `bootstrap.py` | `task setup` |
| `clean.py` | `task clean` |
| `dep_versions.py` | `task deps:versions` |
| `workflow_versions.py` | `task actions:versions` |
| `seed.py` | `task seed` |
| `doctor.py` | `task doctor` |

Single-shot or CI-only scripts (`changelog_check.py`,
`archive_todos.py`, etc.) are called directly; no task entry needed.

### Pre-commit hooks

Hooks under `scripts/precommit/` follow the same conventions.
`check-shebang-scripts-are-executable` enforces the executable bit on
shebang-bearing files.

### Tests

Tests for the doctor / env / dep helpers live under
`tests/scripts/test_*.py` (added in Phase 1+ as the suite grows). They
run with the same pytest invocation as everything else.

## Alternatives Considered

### Promote scripts to `[project.scripts]` console entries

**Rejected for v1.0.** These are dev tooling, not user-facing CLIs.
Console entries require an installed package, which forces the
chicken-and-egg "doctor before install" tools to grow extra paths.
Reconsider per-script if a workflow proves the abstraction useful.

### Replace scripts with a `nox` or `invoke` setup

**Rejected because:** Taskfile already does the runner role; `uv run`
already does the env-execution role. Adding `nox` would duplicate both.

### Rewrite scripts as entries in `Taskfile.yml`

**Rejected because:** Taskfile is good for short pipelines, not for
multi-hundred-line Python with rich output and argument parsing.

## Consequences

### Positive

- A new contributor can read one ADR and produce a script that fits.
- `--help`, `--dry-run`, and predictable exit codes make scripts safe
  to call from CI and from `Taskfile.yml`.
- Pre-commit enforces the executable-bit invariant; nothing else needs
  policing.

### Negative

- Boilerplate per script (argparse setup, docstring, shebang). It's
  ~15 lines and consistent.
- Convention enforcement is social, not automated, beyond the executable
  bit. PR review is the backstop.

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
