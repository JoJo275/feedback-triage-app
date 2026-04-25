# Command Workflows

<!-- TODO (template users): Update the command examples and tables below to
     match your project.  Remove entries for features you've deleted
     (e.g. security scanning, docs, container tasks). -->

How commands flow through the tooling layers in this project.

---

## The Three Layers

This project has three ways to run developer commands, each building on the
one below:

```text
┌─────────────────────────────────────────────┐
│  Layer 3: Task Runner (Taskfile.yml)        │  ← task test
│  Convenience shortcuts, no Hatch knowledge  │
├─────────────────────────────────────────────┤
│  Layer 2: Hatch (pyproject.toml envs)       │  ← hatch run test
│  Manages virtualenvs, installs deps         │
├─────────────────────────────────────────────┤
│  Layer 1: Python tools (pytest, ruff, mypy) │  ← pytest
│  The actual tools that do the work          │
└─────────────────────────────────────────────┘
```

Each layer is optional — you can work at whichever level you prefer.

---

## How a Command Flows

When you run `task test`, here's what happens:

```text
task test
  → Taskfile.yml runs: hatch run test
    → Hatch activates the default env (creates it if needed)
    → Hatch runs the "test" script defined in pyproject.toml
      → Which executes: pytest {args}
```

The same pattern applies to every command:

| You type             | Taskfile runs              | Hatch script | Actual tool                                    |
| -------------------- | -------------------------- | ------------ | ---------------------------------------------- |
| `task test`          | `hatch run test`           | `test`       | `pytest`                                       |
| `task test:cov`      | `hatch run test-cov`       | `test-cov`   | `pytest --cov`                                 |
| `task lint`          | `hatch run lint`           | `lint`       | `ruff check src/ tests/`                       |
| `task lint:fix`      | `hatch run lint-fix`       | `lint-fix`   | `ruff check --fix src/ tests/`                 |
| `task fmt`           | `hatch run fmt`            | `fmt`        | `ruff format src/ tests/`                      |
| `task fmt:check`     | `hatch run fmt-check`      | `fmt-check`  | `ruff format --check src/ tests/`              |
| `task typecheck`     | `hatch run typecheck`      | `typecheck`  | `mypy src/`                                    |
| `task security`      | `hatch run bandit -r src/` | _(direct)_   | `bandit -r src/`                               |
| `task deptry`        | `hatch run deptry .`       | _(direct)_   | `deptry .`                                     |
| `task check`         | `hatch run check`          | `check`      | lint + fmt-check + typecheck + test            |
| `task test:matrix`   | `hatch run test:run`       | `test:run`   | pytest across Python 3.11–3.13                 |
| `task docs:serve`    | `hatch run docs:serve`     | `docs:serve` | `mkdocs serve`                                 |
| `task docs:build`    | `hatch run docs:build`     | `docs:build` | `mkdocs build --strict`                        |
| `task docs:commands` | _(runs script directly)_   | —            | `python scripts/generate_command_reference.py` |
| `task dashboard:serve` | `hatch run dashboard:serve` | `dashboard:serve` | FastAPI uvicorn server                  |

<!-- TODO (template users): Update the table above after renaming Hatch scripts
     or adding new ones in pyproject.toml. Add rows for any domain-specific
     commands (e.g. `task migrate`, `task seed`). Remove rows for features
     you've deleted. -->

!!! note "Direct commands vs Hatch scripts"

    Most Task commands map to a named Hatch script (e.g. `lint` →
    `ruff check src/ tests/`).  A few — like `security` — run the tool
    directly via `hatch run <command>` without a named script.  The
    result is the same; the only difference is whether a shorthand
    alias exists in `[tool.hatch.envs.default.scripts]`.

---

## Pick Your Layer

### Layer 1: Direct tools (no Hatch, no Task)

<!-- TODO (template users): Update tool paths and flags below to match your
     project's source layout and tool configuration. -->

Use this if you manage your own virtualenv with `pip install -e ".[dev]"`.

```bash
pytest                          # run tests
ruff check src/ tests/          # lint
ruff format src/ tests/         # format
mypy src/                       # type check
bandit -r src/                  # security lint
mkdocs serve                    # serve docs
```

**Pros:** No extra tooling. Works in any venv.
**Cons:** You manage the venv, dependency installs, and Python versions yourself.

!!! warning "Default paths"

    The Hatch scripts default to `src/ tests/` for Ruff and `src/` for
    mypy.  If you run direct tools, remember to pass the same paths or
    you may lint/format files that Hatch normally skips.

### Layer 2: Hatch

Use this if you want managed environments but don't want Task installed.

```bash
hatch shell                     # enter the dev environment
hatch run test                  # run tests (auto-creates env if needed)
hatch run lint                  # lint
hatch run fmt                   # format
hatch run typecheck             # type check
hatch run test:run              # test across Python 3.11–3.13
hatch run docs:serve            # serve docs (uses docs env)
hatch env show                  # show all environments
```

**Pros:** Automatic venv creation, dep syncing, multi-version matrix.
**Cons:** Requires Hatch installed (`pipx install hatch`).

### Layer 3: Task runner

Use this for the shortest commands. Requires both Hatch and [Task](https://taskfile.dev/).

```bash
task test                       # run tests
task lint                       # lint
task fmt                        # format
task typecheck                  # type check
task check                      # all quality gates
task test:matrix                # test across Python 3.11–3.13
task docs:serve                 # serve docs
task                            # list all available tasks
```

**Pros:** Shortest commands, discoverable via `task --list`.
**Cons:** Requires both Hatch and Task installed.

---

## Which Layer Should I Use?

| Situation                          | Recommended layer                             |
| ---------------------------------- | --------------------------------------------- |
| Quick contribution, minimal setup  | Layer 1 (pip + direct tools)                  |
| Regular development                | Layer 2 (Hatch) or Layer 3 (Task)             |
| CI/CD workflows                    | Layer 2 (Hatch) — Task is not installed in CI |
| Multi-version testing              | Layer 2 or 3 — Hatch manages the matrix       |
| First time, just want to run tests | Layer 3 if Task is installed, else Layer 2    |

---

## Passing CLI Arguments

All three layers support forwarding extra arguments to the underlying tool.

=== "Taskfile"

    Append `--` then your arguments:

    ```bash
    task test -- tests/unit/test_example.py -v
    task lint -- --fix src/
    task test:k -- my_function
    ```

=== "Hatch"

    Arguments after the script name are forwarded automatically:

    ```bash
    hatch run test tests/unit/test_example.py -v
    hatch run lint --fix src/
    ```

    Hatch scripts use `{args}` or `{args: default}` placeholders in
    `pyproject.toml`.  When you pass arguments, they replace the
    placeholder; when you don't, the default is used.

=== "Direct"

    Just pass arguments normally:

    ```bash
    pytest tests/unit/test_example.py -v
    ruff check --fix src/
    ```

---

## More Task Shortcuts

Beyond the core table above, the Taskfile provides shortcuts for common
workflows. Run `task --list-all` to see everything.

### Testing

| Task                    | What it does                    |
| ----------------------- | ------------------------------- |
| `task test:v`           | Tests with verbose output       |
| `task test:cov`         | Tests with coverage report      |
| `task test:unit`        | Unit tests only (`tests/unit/`) |
| `task test:integration` | Integration tests only          |
| `task test:lf`          | Rerun last-failed tests         |
| `task test:x`           | Stop on first failure           |
| `task test:k`           | Run tests matching a keyword    |
| `task test:matrix`      | All Python versions (3.11–3.13) |
| `task test:matrix:cov`  | Matrix with coverage            |

### Environment

| Task             | What it does                        |
| ---------------- | ----------------------------------- |
| `task shell`     | Enter the Hatch dev shell           |
| `task env:show`  | Show all Hatch envs and scripts     |
| `task env:reset` | Remove and recreate the default env |
| `task env:prune` | Remove ALL Hatch environments       |

### Pre-commit

| Task                      | What it does                       |
| ------------------------- | ---------------------------------- |
| `task pre-commit:install` | Install all hook stages            |
| `task pre-commit:run`     | Run all hooks on all files         |
| `task pre-commit:update`  | Update hooks to latest versions    |
| `task pre-commit:hook`    | Run a single hook (e.g. `-- ruff`) |

### Dependencies & Actions

| Task                    | What it does                             |
| ----------------------- | ---------------------------------------- |
| `task deps:versions`    | Show installed vs latest dep versions    |
| `task deps:upgrade`     | Upgrade dependencies in `pyproject.toml` |
| `task deps:outdated`    | Check for outdated packages              |
| `task deps:update-comments` | Update version comments in pyproject.toml |
| `task actions:versions` | Show SHA-pinned action versions          |
| `task actions:upgrade`  | Upgrade SHA-pinned actions               |
| `task actions:check`    | CI gate: exit non-zero if stale actions  |

### Utility

| Task               | What it does                             |
| ------------------ | ---------------------------------------- |
| `task build`       | Build source + wheel distributions       |
| `task clean:all`   | Remove all build artifacts and caches    |
| `task clean:build` | Clean build artifacts (Hatch only)       |
| `task clean:todo`  | Archive completed TODO items             |
| `task doctor`      | Print diagnostics bundle for bug reports |
| `task doctor:repo` | Run repository health checks             |
| `task commit`      | Interactive conventional commit          |
| `task version`     | Show project version                     |
| `task info`        | Show project metadata                    |
| `task security`    | Run bandit security linter               |
| `task deptry`      | Check for unused/missing dependencies    |
| `task stats`       | Repository statistics dashboard          |
| `task run`         | Run the application                      |
| `task customize`   | Interactive project customization        |
| `task todo:check`  | Find and report TODO items               |

### Container

| Task                             | What it does                                 |
| -------------------------------- | -------------------------------------------- |
| `task container:test`            | Run all container tests                      |
| `task container:test:containerfile` | Test the Containerfile build              |
| `task container:test:compose`    | Test the docker compose stack                |
| `task container:test:dry-run`    | Preview container tests without running      |

### Dashboard

| Task                  | What it does                                          |
| --------------------- | ----------------------------------------------------- |
| `task dashboard:serve` | Start environment dashboard (http://127.0.0.1:8000) |

### Labels

| Task                  | What it does                            |
| --------------------- | --------------------------------------- |
| `task labels:apply`   | Apply GitHub labels (with flags)        |
| `task labels:baseline`| Apply baseline labels to current repo   |
| `task labels:full`    | Apply extended labels to current repo   |
| `task labels:dry-run` | Preview baseline labels without applying|

### Doctor & Health Checks

| Task                             | What it does                         |
| -------------------------------- | ------------------------------------ |
| `task doctor:all`                | All health checks in one report      |
| `task doctor:env`                | Environment health check             |
| `task doctor:repo`               | Repository structure checks          |
| `task doctor:git`                | Git health dashboard                 |
| `task doctor:git:refresh`        | Fetch, prune stale refs, sync tags   |
| `task doctor:git:cleanup`        | Delete stale branches, run gc        |
| `task doctor:git:commits`        | Detailed commit report               |
| `task doctor:git:watch`          | Re-run git dashboard every N seconds |
| `task doctor:git:config:export`  | Export git config reference          |
| `task doctor:git:config:apply`   | Apply recommended git config         |
| `task doctor:git:config:minimal` | Apply core subset (12 keys)          |

---

## Adding Your Own Commands

<!-- TODO (template users): After adding your own Hatch scripts and Task
     shortcuts, update the tables in this file and in developer-commands.md
     to keep them in sync. -->

### Hatch scripts

Add a new entry to `[tool.hatch.envs.default.scripts]` in `pyproject.toml`:

```toml
[tool.hatch.envs.default.scripts]
my-command = "python -m my_tool {args}"
```

Then run with `hatch run my-command`.

### Task shortcuts

Add a new task to `Taskfile.yml`:

```yaml
tasks:
    my-command:
        desc: Run my custom tool
        cmds:
            - hatch run my-command {{.CLI_ARGS}}
```

Then run with `task my-command`.

### Compound scripts

Hatch scripts can reference other scripts by name to create pipelines:

```toml
[tool.hatch.envs.default.scripts]
check = ["lint", "fmt-check", "typecheck", "test"]
```

This is how `task check` / `hatch run check` runs all quality gates in
sequence — it's a compound script that calls four other scripts.

---

## Where Commands Are Defined

| Layer             | Config file      | Section                             |
| ----------------- | ---------------- | ----------------------------------- |
| Hatch scripts     | `pyproject.toml` | `[tool.hatch.envs.default.scripts]` |
| Hatch test matrix | `pyproject.toml` | `[tool.hatch.envs.test]`            |
| Hatch docs env    | `pyproject.toml` | `[tool.hatch.envs.docs]`            |
| Task shortcuts    | `Taskfile.yml`   | `tasks:`                            |

<!-- TODO (template users): If you rename Hatch environments or add new ones
     (e.g. a `staging` env), add them to the table above and update
     pyproject.toml accordingly. -->

To see all available commands:

```bash
task                            # list Task shortcuts
task --list-all                 # include internal tasks
hatch env show                  # show Hatch envs and their scripts
```

---

## See Also

- [developer-commands.md](developer-commands.md) — Complete command reference
- [dev-setup.md](dev-setup.md) — Environment setup instructions
- [Getting Started](../guide/getting-started.md) — Quick start guide
- [Command Reference](../reference/commands.md) — Auto-generated task & script reference
- [ADR 016](../adr/016-hatchling-and-hatch.md) — Why Hatch
- [ADR 017](../adr/017-task-runner.md) — Why Taskfile
