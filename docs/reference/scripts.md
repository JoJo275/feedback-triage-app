# Scripts Reference

<!-- TODO (template users): Update this file after renaming, removing, or
     adding scripts. Keep it in sync with scripts/README.md. -->

!!! note "Consider using commands.md instead"
[commands.md](commands.md) is **auto-generated** and covers everything
in this file plus Taskfile tasks, Hatch environments, CLI entry points,
and common flag patterns. This hand-curated page provides a quick-scan
flag table but requires manual updates. If you only maintain one
reference, prefer commands.md.

Comprehensive reference of every script in `scripts/` and the flags each
supports. Internal modules (prefixed with `_`) are listed at the bottom
for completeness but are not intended to be run directly.

> **See also:** [commands.md](commands.md) for the auto-generated
> comprehensive command reference (Taskfile + scripts + Hatch + entry points).

---

## User-Facing Scripts

### apply_labels.py

Apply GitHub issue/PR labels to a repository from a JSON baseline.

| Flag                        | Description                               |
| :-------------------------- | :---------------------------------------- |
| `--set {baseline,extended}` | **(required)** Label set to apply         |
| `--repo OWNER/REPO`         | Target repository (default: current repo) |
| `--dry-run`                 | Preview without applying                  |
| `--version`                 | Print version and exit                    |

### apply-labels.sh

Shell wrapper around `apply_labels.py`.

| Argument               | Description                          |
| :--------------------- | :----------------------------------- |
| `{baseline\|extended}` | **(required, positional)** Label set |
| `[OWNER/REPO]`         | Optional target repository           |
| `[--dry-run]`          | Preview without applying             |

### archive_todos.py

Archive completed TODO items from `docs/notes/todo.md`.

| Flag                  | Description                 |
| :-------------------- | :-------------------------- |
| `--dry-run`           | Preview without writing     |
| `--no-backup`         | Skip creating a `.bak` file |
| `--todo-file PATH`    | Custom path to todo file    |
| `--archive-file PATH` | Custom path to archive file |
| `-q, --quiet`         | Suppress output             |
| `--version`           | Print version and exit      |

### bootstrap.py

One-command setup for fresh clones (install hooks, create envs, run tests).

| Flag                 | Description                       |
| :------------------- | :-------------------------------- |
| `--dry-run`          | Preview without executing         |
| `--skip-hooks`       | Skip pre-commit hook installation |
| `--skip-test-matrix` | Skip running the full test matrix |
| `-q, --quiet`        | Suppress output                   |
| `--version`          | Print version and exit            |

### changelog_check.py

Verify CHANGELOG.md entries match git tags.

| Flag                    | Description              |
| :---------------------- | :----------------------- |
| `-v, --verbose`         | Show detailed comparison |
| `-q, --quiet`           | Suppress output          |
| `--changelog-path PATH` | Custom changelog path    |
| `--version`             | Print version and exit   |

### check_known_issues.py

Check for stale "Resolved" entries in `docs/known-issues.md`.

| Flag                 | Description                                      |
| :------------------- | :----------------------------------------------- |
| `--days N`           | Days before a resolved entry is considered stale |
| `--issues-path PATH` | Custom path to known-issues file                 |
| `--json`             | Output as JSON                                   |
| `-q, --quiet`        | Suppress output                                  |
| `--version`          | Print version and exit                           |

### check_todos.py

Scan for `TODO (template users)` comments in the codebase.

| Flag               | Description                        |
| :----------------- | :--------------------------------- |
| `--pattern TEXT`   | Custom pattern to search for       |
| `--count`          | Only print the count               |
| `--json`           | Output as JSON                     |
| `--exclude PREFIX` | Exclude paths starting with PREFIX |
| `-q, --quiet`      | Suppress output                    |
| `--version`        | Print version and exit             |

### clean.py

Remove build artifacts, caches, and temporary files.

| Flag             | Description                     |
| :--------------- | :------------------------------ |
| `--dry-run`      | Preview without deleting        |
| `--include-venv` | Also remove `.venv` directories |
| `-y, --yes`      | Skip confirmation prompt        |
| `-q, --quiet`    | Suppress output                 |
| `--version`      | Print version and exit          |

### customize.py

Interactive project customization (rename package, set author, etc.).

| Flag                                | Description                    |
| :---------------------------------- | :----------------------------- |
| `--dry-run`                         | Preview without writing        |
| `--non-interactive`                 | Skip prompts, use flag values  |
| `--project-name NAME`               | Set project name               |
| `--package-name NAME`               | Set Python package name        |
| `--author NAME`                     | Set author name                |
| `--github-user NAME`                | Set GitHub username            |
| `--description TEXT`                | Set project description        |
| `--cli-prefix PREFIX`               | Set CLI command prefix         |
| `--license ID`                      | Set license identifier         |
| `--strip DIR [DIR...]`              | Remove directories             |
| `--template-cleanup ITEM [ITEM...]` | Remove template-specific items |
| `--force`                           | Overwrite without confirmation |
| `--enable-workflows SLUG`           | Enable guarded workflows       |
| `-q, --quiet`                       | Suppress output                |
| `--version`                         | Print version and exit         |

### dep_versions.py

Dependency version manager — show, comment, and upgrade pinned deps.

| Subcommand                    | Description                         |
| :---------------------------- | :---------------------------------- |
| `show`                        | Display current dependency versions |
| `update-comments`             | Update inline version comments      |
| `upgrade [package] [version]` | Upgrade a dependency                |

| Flag        | Description             |
| :---------- | :---------------------- |
| `--offline` | Skip PyPI lookups       |
| `--dry-run` | Preview without writing |
| `--version` | Print version and exit  |

### doctor.py

Print a diagnostics bundle for bug reports.

| Flag                | Description            |
| :------------------ | :--------------------- |
| `-o, --output PATH` | Write output to a file |
| `--markdown`        | Format as Markdown     |
| `--json`            | Output as JSON         |
| `-q, --quiet`       | Suppress output        |
| `--no-color`        | Disable colored output |
| `--version`         | Print version and exit |

### env_doctor.py

Environment health check for development prerequisites.

| Flag         | Description              |
| :----------- | :----------------------- |
| `--strict`   | Treat warnings as errors |
| `--no-color` | Disable colored output   |
| `--json`     | Output as JSON           |
| `--version`  | Print version and exit   |

### generate_command_reference.py

Auto-generate `docs/reference/commands.md` from Taskfile, scripts, and Hatch.

| Flag        | Description                                      |
| :---------- | :----------------------------------------------- |
| `--check`   | Exit non-zero if the file would change (CI mode) |
| `--dry-run` | Preview without writing                          |
| `--version` | Print version and exit                           |

### git_doctor.py

Git-focused health check, information dashboard, and configuration manager.

| Flag                          | Description                                                           |
| :---------------------------- | :-------------------------------------------------------------------- |
| `--no-color`                  | Disable colored output                                                |
| `--json`                      | Output as JSON (for CI integration)                                   |
| `--export-config`             | Export full git config reference to Markdown                          |
| `--apply-from PATH`           | Apply desired values from an edited reference file                    |
| `--apply-recommended`         | Apply ALL catalog recommended values and scopes                       |
| `--apply-recommended-minimal` | Apply core subset of recommended configs                              |
| `--dry-run`                   | Preview without applying (with `--apply-*`, `--refresh`, `--cleanup`) |
| `--new-branch`                | Interactive branch creation off `origin/main`                         |
| `--watch [N]`                 | Re-run dashboard every N seconds (default: 10, min: 2)                |
| `--refresh`                   | Interactive refresh: fetch, prune, sync tags, update remote HEAD      |
| `--cleanup`                   | Interactive cleanup: delete stale branches, run `git gc`              |
| `--view-commits`              | Detailed commit report for current branch                             |
| `--markdown`                  | With `--view-commits`, write Markdown report to `commit-report.md`    |
| `--version`                   | Print version and exit                                                |

### repo_doctor.py

Repository health checks (file presence, conventions, best practices).

| Flag                | Description                             |
| :------------------ | :-------------------------------------- |
| `--missing`         | Only show missing/failing checks        |
| `--staged`          | Only check staged files                 |
| `--diff RANGE`      | Only check files changed in a git range |
| `--category NAME`   | Filter by check category                |
| `--min-level LEVEL` | Minimum severity level to show          |
| `--include-info`    | Include info-level checks               |
| `--profile NAME`    | Use a named check profile               |
| `--fix`             | Auto-fix issues where possible          |
| `--no-hints`        | Hide hint text                          |
| `--no-links`        | Hide documentation links                |
| `--no-color`        | Disable colored output                  |
| `--strict`          | Treat warnings as errors                |
| `--show-passed`     | Show passing checks too                 |
| `--version`         | Print version and exit                  |

### test_containerfile.py

Build and test the Containerfile (smoke tests, image size, cleanup).

| Flag          | Description                      |
| :------------ | :------------------------------- |
| `--dry-run`   | Preview without building         |
| `--keep`      | Keep the built image after tests |
| `--verbose`   | Show detailed output             |
| `--timeout N` | Build timeout in seconds         |
| `--version`   | Print version and exit           |

### test_containerfile.sh

Shell wrapper for Containerfile testing.

| Variable       | Description          |
| :------------- | :------------------- |
| `KEEP_IMAGE=1` | Skip image cleanup   |
| `VERBOSE=1`    | Show detailed output |

### test_docker_compose.py

Test the Docker Compose stack (up, health check, down).

| Flag          | Description                         |
| :------------ | :---------------------------------- |
| `--dry-run`   | Preview without running             |
| `--keep`      | Keep containers running after tests |
| `--verbose`   | Show detailed output                |
| `--timeout N` | Startup timeout in seconds          |
| `--version`   | Print version and exit              |

### test_docker_compose.sh

Shell wrapper for Docker Compose testing.

| Variable    | Description            |
| :---------- | :--------------------- |
| `KEEP=1`    | Skip container cleanup |
| `VERBOSE=1` | Show detailed output   |

### workflow_versions.py

GitHub Actions workflow version manager — show, comment, and upgrade SHA-pinned actions.

| Subcommand                   | Description                     |
| :--------------------------- | :------------------------------ |
| `show`                       | Display current action versions |
| `update-comments`            | Update inline version comments  |
| `upgrade [action] [version]` | Upgrade a pinned action         |

| Flag              | Description             |
| :---------------- | :---------------------- |
| `--offline`       | Skip GitHub API lookups |
| `--json`          | Output as JSON          |
| `--filter FILTER` | Filter actions by name  |
| `--dry-run`       | Preview without writing |
| `--color`         | Force colored output    |
| `--no-color`      | Disable colored output  |
| `-q, --quiet`     | Suppress output         |
| `--version`       | Print version and exit  |

---

## Internal Modules

These are shared utilities imported by the scripts above. They are **not**
intended to be run directly.

| Module              | Purpose                                                                         |
| :------------------ | :------------------------------------------------------------------------------ |
| `_colors.py`        | ANSI color detection, colorization helpers, `Colors` class                      |
| `_doctor_common.py` | Shared helpers for doctor scripts (repo slug extraction, pyproject reading)     |
| `_imports.py`       | Repo root discovery and path setup                                              |
| `_progress.py`      | `ProgressBar` (determinate) and `Spinner` (indeterminate) for terminal feedback |

---

## Common Flag Patterns

Most scripts follow these conventions:

- **`--dry-run`** — Preview changes without executing or writing
- **`-q, --quiet`** — Suppress non-essential output
- **`--version`** — Print the script version and exit
- **`--json`** — Machine-readable JSON output (for CI integration)
- **`--no-color`** — Disable ANSI color escapes (also respects `NO_COLOR` env var)
