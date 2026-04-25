# Development Guide

<!-- TODO (template users): Update project-specific references (package name,
     CLI commands, example test paths) throughout this guide after renaming
     the project. Remove tool sections you don't use. -->

This guide covers developer tools and workflows for contributing to this project.

> **First time?** See [dev-setup.md](dev-setup.md) for environment setup instructions.
>
> **Ready to contribute?** See [pull-requests.md](pull-requests.md) for PR guidelines.

---

## Idea Development Lifecycle

Non-trivial changes follow this lifecycle from idea to implementation.
Skip stages that don't apply — small changes can go straight to an ADR
or implementation plan.

```
idea/problem        →  explorations/           Early-stage evaluation
proposed design     →  blueprints/             Structural design shape
decision locked in  →  adr/                    Permanent decision record
build steps         →  implementation-plans/   Step-by-step execution
```

| Stage | Directory | Purpose | When to Use |
| :---- | :-------- | :------ | :---------- |
| **Explore** | [`docs/explorations/`](../explorations/) | Evaluate whether an idea is worth pursuing. Weigh alternatives, risks, and tradeoffs. | New idea surfaces; scope/cost is unclear; multiple options need comparison |
| **Design** | [`docs/blueprints/`](../blueprints/) | Define the structural shape of an approved idea. Components, repo layout, tooling impact. | Exploration concluded with "proceed"; design spans multiple files/modules |
| **Decide** | [`docs/adr/`](../adr/) | Lock in the decision with context and consequences. Permanent project record. | Decision is hard to reverse, affects multiple areas, or needs future context |
| **Build** | [`docs/implementation-plans/`](../implementation-plans/) | Step-by-step execution plan with file-level detail, sequencing, and verification. | Work spans multiple phases/sessions; sequencing matters; checklist needed |

Each directory has a README with detailed guidance and a template to copy.

---

## Common Workflows

### Running Tests

```bash
# Run all tests
hatch run test

# Run with verbose output
hatch run test -v

# Run specific test file
hatch run test tests/unit/test_example.py

# Run with coverage report
hatch run test-cov
```

### Code Quality

```bash
# Lint code (check for issues)
hatch run lint

# Auto-fix linting issues
hatch run lint-fix

# Format code
hatch run fmt

# Type checking
hatch run typecheck

# Run ALL checks (lint + format + typecheck + test)
hatch run check
```

### Building the Package

```bash
# Build source and wheel distributions
hatch build

# Clean build artifacts
hatch clean

# Output goes to dist/
```

---

## Developer Tools

This project uses the following developer tools:

### GitHub CLI

GitHub CLI (`gh`) is required to run the label management scripts in `scripts/`.

Install GitHub CLI:

- **Windows (winget):**

    ```bash
    winget install --id GitHub.cli
    ```

- **Windows (Chocolatey):**

    ```bash
    choco install gh
    ```

- **macOS (Homebrew):**

    ```bash
    brew install gh
    ```

- **Linux (Debian/Ubuntu):**
    ```bash
    sudo apt install gh
    ```

After installation, authenticate with GitHub:

```bash
gh auth login
```

See the [GitHub CLI installation docs](https://cli.github.com/manual/installation) for other platforms.

### Commit Messages (Conventional Commits)

Commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. You can write them manually — no tooling required.

#### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

- **type** — what kind of change (see table below)
- **scope** — what area is affected (optional, e.g. `cli`, `docs`, `ci`)
- **description** — short imperative summary, lowercase, no period

#### Types

| Type       | When to Use                               |
| ---------- | ----------------------------------------- |
| `feat`     | New feature or capability                 |
| `fix`      | Bug fix                                   |
| `docs`     | Documentation only                        |
| `style`    | Whitespace, formatting (no logic changes) |
| `refactor` | Code restructuring (no feature/fix)       |
| `perf`     | Performance improvement                   |
| `test`     | Adding or fixing tests                    |
| `build`    | Build system, dependencies                |
| `ci`       | CI/CD configuration                       |
| `chore`    | Maintenance, tooling, config              |
| `revert`   | Reverting a previous commit               |

#### Breaking Changes

Add `!` after the type/scope, and explain in the footer:

```
feat(api)!: change authentication to OAuth2

BREAKING CHANGE: removed basic auth support
```

#### Examples

```bash
git commit -m "feat: add user authentication"
git commit -m "fix(cli): handle missing config file gracefully"
git commit -m "docs: update installation guide"
git commit -m "refactor(engine): extract validation into separate module"
git commit -m "ci: add Python 3.13 to test matrix"
git commit -m "chore: bump ruff to 0.9.x"
```

#### Optional: Commitizen

Commitizen is already installed in the dev environment. Use it via Hatch
or the Taskfile shortcut:

```bash
hatch run cz commit
# or
task commit
```

Alternatively, install it standalone with [pipx](https://pipx.pypa.io/):

```bash
pipx install commitizen
cz commit
```

#### Optional: Commit Template

This repo includes a `.gitmessage.txt` that pre-fills your editor with the suggested format and prompts (Why / What changed / How tested):

```bash
# Activate (for this repo only)
git config commit.template .gitmessage.txt

# Deactivate
git config --unset commit.template
```

Once activated, `git commit` (without `-m`) opens your editor with the template. All `#` lines are stripped from the final message.

---

## Helpful Tools (Optional)

These tools aren't required but can make development easier. Install them individually or all at once:

```bash
# Install all extras
pip install -e ".[extras]"

# Or install individually
pip install pipdeptree
```

### pipdeptree

Visualize your project's dependency tree - helpful for understanding what packages depend on what:

```bash
# Show full dependency tree
python -m pipdeptree

# Show dependencies for a specific package
python -m pipdeptree -p simple-python-boilerplate

# Reverse: show what depends on a package
python -m pipdeptree -r -p requests

# Output as JSON (for tooling)
python -m pipdeptree --json
```

### Other Helpful Tools

Tools I found helpful during development:

| Tool        | Install                 | Description                           |
| ----------- | ----------------------- | ------------------------------------- |
| `pip-tools` | `pip install pip-tools` | Pin dependencies with `pip-compile`   |
| `pip-audit` | `pip install pip-audit` | Check for security vulnerabilities    |
| `rich`      | `pip install rich`      | Pretty console output and tables      |
| `typer`     | `pip install typer`     | Build CLI apps with type hints        |
| `click`     | `pip install click`     | Composable command-line toolkit       |
| `icecream`  | `pip install icecream`  | Better debug printing: `ic(variable)` |
| `ipython`   | `pip install ipython`   | Enhanced interactive Python shell     |
| `devtools`  | `pip install devtools`  | Debug utilities: `debug(variable)`    |

---

## Pre-commit Hooks (Optional)

<!-- TODO (template users): If you add or remove hooks from
     .pre-commit-config.yaml, update the hook table below and ADR 008. -->

This project ships with a comprehensive `.pre-commit-config.yaml` (47 hooks
across 4 stages — see [ADR 008](../adr/008-pre-commit-hooks.md) for the full
inventory). To activate them:

```bash
# Install pre-commit (if not already installed)
pipx install pre-commit

# Install all hook stages
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push

# Run against all files (first time)
pre-commit run --all-files
```

Or use the Taskfile shortcut:

```bash
task pre-commit:install   # Install all hook stages
task pre-commit:run        # Run all hooks on all files
```

### Seeing Which Hooks Are Enabled

The project already has a `.pre-commit-config.yaml` with all hooks configured.
To see what's active:

```bash
# Inspect the config to see all configured hooks
cat .pre-commit-config.yaml

# Or run all hooks verbosely to see each hook's status
pre-commit run --all-files --verbose
```

Key hooks by stage:

| Hook                      | Source           | Purpose                                  |
| ------------------------- | ---------------- | ---------------------------------------- |
| `trailing-whitespace`     | pre-commit-hooks | Remove trailing whitespace               |
| `end-of-file-fixer`       | pre-commit-hooks | Ensure files end with newline            |
| `check-yaml`              | pre-commit-hooks | Validate YAML syntax                     |
| `check-toml`              | pre-commit-hooks | Validate TOML syntax                     |
| `check-json`              | pre-commit-hooks | Validate JSON syntax                     |
| `check-added-large-files` | pre-commit-hooks | Prevent large files (>500 KB)            |
| `check-merge-conflict`    | pre-commit-hooks | Detect merge conflict markers            |
| `check-case-conflict`     | pre-commit-hooks | Detect case-insensitive filename clashes |
| `debug-statements`        | pre-commit-hooks | Find leftover debugger imports           |
| `detect-private-key`      | pre-commit-hooks | Detect committed private keys            |
| `ruff`                    | ruff-pre-commit  | Lint Python code (with auto-fix)         |
| `ruff-format`             | ruff-pre-commit  | Format Python code                       |
| `mypy`                    | mirrors-mypy     | Type checking (`src/` only)              |
| `bandit`                  | bandit           | Security linting (excludes `tests/`)     |

See [ADR 008](../adr/008-pre-commit-hooks.md) for the complete hook inventory
(38 pre-commit, 1 commit-msg, 4 pre-push, 4 manual — 47 total).

#### Without pre-commit (raw Git hooks)

```bash
# List installed Git hook scripts
ls .git/hooks/

# Show what a specific hook does
cat .git/hooks/pre-commit
```

Hook files without a `.sample` extension are active. When pre-commit is installed, `.git/hooks/pre-commit` is a shim that delegates to the pre-commit framework.

### Disabling Hooks

#### With pre-commit

```bash
# Uninstall pre-commit hooks from this repo (removes the .git/hooks/pre-commit shim)
pre-commit uninstall

# Skip hooks for a single commit
SKIP=all git commit -m "feat: commit without hooks"
# On Windows (PowerShell)
$env:SKIP="all"; git commit -m "feat: commit without hooks"; Remove-Item Env:SKIP

# Skip specific hooks only (comma-separated hook IDs)
SKIP=mypy,bandit git commit -m "fix: skip slow hooks this time"
# On Windows (PowerShell)
$env:SKIP="mypy,bandit"; git commit -m "fix: skip slow hooks this time"; Remove-Item Env:SKIP

# Re-enable hooks later
pre-commit install
```

#### Without pre-commit (raw Git)

```bash
# Skip all Git hooks for a single commit
git commit --no-verify -m "feat: bypass all hooks"
# Short form
git commit -n -m "feat: bypass all hooks"

# Disable hooks globally by pointing core.hooksPath to an empty directory
mkdir -p /tmp/no-hooks
git config core.hooksPath /tmp/no-hooks

# Restore default hooks path
git config --unset core.hooksPath

# Or delete the hook script directly (permanent until re-installed)
rm .git/hooks/pre-commit
```

> **Tip:** Use `--no-verify` / `-n` for quick one-off bypasses. Use `pre-commit uninstall` if you want hooks off until you explicitly re-enable them.

---

## Dependency Management

<!-- TODO (template users): Update dependency group names if you change the
     groups in pyproject.toml [project.optional-dependencies]. -->

### Adding Dependencies

Edit `pyproject.toml` and Hatch picks them up automatically on the next command:

```toml
# Runtime dependencies (required to run the package)
[project]
dependencies = [
    "requests>=2.28",
]

# Dev dependencies (add to the 'dev' optional-dependencies group)
[project.optional-dependencies]
dev = [
    "pytest",
    "new-dev-tool",  # Add here
]
```

> **Note:** This project uses `[project.optional-dependencies]` groups
> consumed by Hatch via `features = ["dev"]`. Don't add dev dependencies
> directly to `[tool.hatch.envs.default] dependencies` — add them to the
> appropriate group in `[project.optional-dependencies]` instead.

Then run any `hatch run` command — Hatch syncs and installs the new dependency automatically.

### Removing Dependencies

Remove the line from `pyproject.toml`. However, some setups/versions of Hatch may leave the old package installed in the environment. The reliable cleanup is to recreate the environment:

```bash
# Remove a specific environment
hatch env remove default

# Or remove ALL environments
hatch env prune
```

The next `hatch run` or `hatch shell` command will rebuild a clean environment.

### Checking Installed Packages

```bash
# List all installed packages in the Hatch default env
hatch run pip list

# Show package details
hatch run pip show simple-python-boilerplate

# Show Hatch environments
hatch env show
```

---

## Useful Resources

- [Hatch Documentation](https://hatch.pypa.io/latest/)
- [pyproject.toml Reference](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## Environment Dashboard

The project includes a web-based environment dashboard
([ADR 041](../adr/041-env-inspect-web-dashboard.md)) powered by FastAPI,
htmx, and Alpine.js. It runs 20 plugin-based data collectors to display
system info, git status, dependency health, security posture, and more.

```bash
task dashboard:serve
# or
hatch run dashboard:serve
# Opens at http://127.0.0.1:8000
```

See [Dashboard Guide](../guide/dashboard-guide.md) for full documentation.
