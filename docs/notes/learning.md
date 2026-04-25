# Learning Notes

Personal notes and learnings captured while building this project.

## Python Packaging

### The `src/` Layout Mystery (Solved)

**Problem:** Tests fail with `ModuleNotFoundError` even though code is right there.

**Why:** Python doesn't automatically look inside `src/`. The `src/` layout is _intentionally_ strict — it forces you to install the package properly.

**Solution:** Always run `pip install -e .` after cloning. The `-e` (editable) flag links your source so changes reflect immediately.

### pyproject.toml vs setup.py

- `setup.py` = Old way (executable Python, security concerns)
- `pyproject.toml` = New way (declarative TOML, standard)

Most tools now read from `[tool.X]` sections in pyproject.toml. One file to rule them all.

### Hatchling vs Hatch — The Mental Model

These two names kept confusing me. The key distinction:

- **Hatchling** = "how to build the package" (build backend, like setuptools)
- **Hatch** = "how to work on the project" (project manager, like tox/nox + venv)

| Tool          | What it does                                                     | Config section                                |
| ------------- | ---------------------------------------------------------------- | --------------------------------------------- |
| **Hatchling** | Builds sdist/wheel when you `pip install .` or `python -m build` | `[build-system]`, `[tool.hatch.build.*]`      |
| **Hatch**     | Manages envs, runs scripts, bumps versions, triggers builds      | `[tool.hatch.envs.*]`, `[tool.hatch.version]` |

**Why use both?** A single `pyproject.toml` defines everything:

- Build backend (Hatchling)
- What goes into distributions (include/exclude rules)
- Version source/bumping rules
- Dev/test/lint environments and scripts (Hatch)

**Important:** Hatchling works _without_ Hatch installed. Anyone can `pip install .` and Hatchling handles the build. Hatch is optional — it's a convenience CLI for developers.

See: [ADR 016](../adr/016-hatchling-and-hatch.md)

### Lockfiles and Transitive Dependencies — pip-tools vs uv vs Poetry

**The problem:** When you declare `requests>=2.28` in `pyproject.toml`, pip resolves it to _some_ version at install time, along with transitive deps like `urllib3`, `certifi`, etc. Different machines at different times can end up with different versions — "works on my machine" bugs.

**The solution:** A lockfile pins _every_ dependency (direct + transitive) to exact versions+hashes, ensuring reproducible environments.

#### The Three Main Approaches

| Tool          | Lockfile                       | How it works                                                                                                                     | Best for                                                  |
| ------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| **pip-tools** | `requirements.txt` (generated) | `pip-compile` reads your loose deps and outputs pinned `requirements.txt`. `pip-sync` installs exactly what's in the file.       | Existing pip-based workflows, minimal learning curve      |
| **uv**        | `uv.lock`                      | Rust-based, drop-in pip replacement. `uv lock` generates lockfile, `uv sync` installs from it. 10-100x faster than pip.          | Speed-critical workflows, modern replacement for pip+venv |
| **Poetry**    | `poetry.lock`                  | Full project manager. `poetry install` reads `pyproject.toml`, generates/uses `poetry.lock`. Also handles builds and publishing. | All-in-one solution, teams wanting integrated tooling     |

#### How They Compare

| Aspect                  | pip-tools                             | uv                            | Poetry                                              |
| ----------------------- | ------------------------------------- | ----------------------------- | --------------------------------------------------- |
| **Speed**               | Slow (pip resolver)                   | Blazing fast (Rust)           | Moderate                                            |
| **Config file**         | `pyproject.toml` or `requirements.in` | `pyproject.toml`              | `pyproject.toml` (but `[tool.poetry]`, not PEP 621) |
| **Learning curve**      | Minimal — familiar pip workflow       | Low — pip-compatible commands | Moderate — own CLI and concepts                     |
| **Hatch compatibility** | Works alongside (but awkward)         | Can replace Hatch entirely    | Replaces Hatch (different philosophy)               |
| **Maturity**            | Very mature                           | Newer but rapidly adopted     | Mature, large community                             |

#### Why This Project Uses Hatch (Without Lockfiles)

Hatch doesn't have native lockfile support — it re-resolves dependencies on each `hatch env create`. This is fine for:

- **Template projects** — users will replace deps anyway
- **Libraries** — consumers control their own dep versions
- **Development** — fast iteration matters more than reproducibility

If you need lockfiles for **deployed applications** where reproducibility is critical, consider:

1. **Switch to uv** — fastest, modern, has `uv.lock`
2. **Use Poetry** — mature, well-documented, has `poetry.lock`
3. **Bolt pip-tools onto Hatch** — possible but awkward (Hatch fights you)

The hybrid approach (Hatch for dev, pip-compile for deploy) adds complexity — usually cleaner to pick one tool that handles both.

#### pip-tools Workflow (If You Did Use It)

```bash
# 1. Create requirements.in with loose constraints
echo "requests>=2.28" > requirements.in

# 2. Compile to pinned requirements.txt
pip-compile requirements.in --output-file=requirements.txt

# 3. Install exactly those versions
pip-sync requirements.txt

# 4. Update when needed
pip-compile --upgrade requirements.in
```

The lockfile becomes the source of truth — commit it, use it in CI and production.

### Python Tool Landscape

There are a lot of overlapping tools in the Python ecosystem. This table groups them by purpose.

#### Build Backends (what `pip install .` uses)

| Tool            | Description                               | Capabilities                                                              | Pros                                             | Cons                                                     |
| --------------- | ----------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------- |
| **Hatchling**   | Modern build backend by the Hatch project | Build sdist/wheel, auto-discover packages, include/exclude rules, plugins | Fast, minimal config, auto-discovers src/ layout | Newer, smaller ecosystem than setuptools                 |
| **setuptools**  | The original build backend                | Build sdist/wheel, C extensions, entry points, data files, find_packages  | Ubiquitous, massive community, battle-tested     | Verbose config, legacy baggage (`setup.py`, `setup.cfg`) |
| **Flit-core**   | Minimalist build backend                  | Build sdist/wheel for pure-Python packages                                | Dead simple for pure-Python packages             | No compiled extensions, fewer features                   |
| **PDM-backend** | Build backend from the PDM project        | Build sdist/wheel, PEP 621 metadata, editable installs                    | PEP 621 native, supports lock files              | Tied to PDM ecosystem                                    |
| **Maturin**     | Build backend for Rust+Python (PyO3)      | Build wheels with compiled Rust extensions, cross-compile                 | First-class Rust FFI support                     | Only for Rust extensions                                 |

#### Project/Environment Managers (create envs, run tasks)

| Tool       | Description                                 | Capabilities                                                                    | Pros                                                                              | Cons                                                              |
| ---------- | ------------------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| **Hatch**  | Project manager + env manager               | Create/manage envs, run scripts, test matrices, version bumping, build, publish | Env management, test matrices, scripts, version bumping — all in `pyproject.toml` | Less established than tox in older codebases                      |
| **tox**    | Test automation / environment manager       | Multi-env test runs, dependency isolation, CI integration, plugin system        | Very mature, widely adopted in CI, plugin ecosystem                               | Separate `tox.ini` config, can be verbose                         |
| **nox**    | Like tox but config is Python code          | Session-based test runs, parametrize, reuse venvs, conda support                | Full Python flexibility, easy to debug sessions                                   | Requires writing Python (pro or con), no declarative config       |
| **PDM**    | Package + project manager                   | Dependency resolution, lock files, scripts, env management, publish             | PEP 582 support, lock files, scripts                                              | Different philosophy (centralised tool), smaller community        |
| **uv**     | Fast package installer + env manager (Rust) | Install packages, create venvs, resolve dependencies, run scripts               | Extremely fast, drop-in pip/venv replacement                                      | Newer tool, still evolving rapidly                                |
| **Poetry** | Dependency manager + build tool             | Dependency resolution, lock files, env management, build, publish               | Lock files, dependency resolution, publish built in                               | Own config format (`[tool.poetry]`), doesn't follow PEP 621 fully |
| **Pipenv** | pip + virtualenv wrapper                    | Pipfile/Pipfile.lock, auto-create venvs, `.env` loading                         | Lock files, `.env` support                                                        | Slow dependency resolution, less active development               |

#### Task Runners (run commands/scripts)

| Tool               | Description                         | Capabilities                                                      | Pros                                             | Cons                                                                  |
| ------------------ | ----------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------- |
| **Hatch scripts**  | Scripts defined in `pyproject.toml` | Run commands, chain scripts, pass args, env-aware                 | Zero extra tools, integrated with Hatch envs     | Only available through Hatch                                          |
| **Make**           | Classic build automation (Makefile) | Targets, dependencies, variables, shell commands, parallel builds | Universal, available everywhere, well understood | Not Python-native, Windows requires extra setup, tab-sensitive syntax |
| **just**           | Modern command runner (Justfile)    | Recipes, arguments, variables, dotenv loading, cross-platform     | Simple syntax, cross-platform, no tab issues     | Extra binary to install, not Python-specific                          |
| **Task (go-task)** | Task runner using `Taskfile.yml`    | Tasks, dependencies, variables, watch mode, cross-platform        | YAML-based, cross-platform, dependency graphs    | Extra binary, Go ecosystem tool                                       |
| **invoke**         | Python-based task runner            | Tasks as Python functions, namespaces, auto-parsing args          | Pure Python, good for complex logic              | Another dependency, less popular now                                  |
| **nox**            | Also works as a task runner         | Session-based commands, parametrize, venv per session             | Python-based, session isolation                  | Heavier than a simple task runner                                     |
| **tox**            | Also works as a task runner         | Env-isolated command runs, dependency pinning                     | Mature, env isolation                            | Verbose for simple tasks                                              |

#### CLI Frameworks (building user-facing CLIs)

| Tool           | Description                               | Capabilities                                                              | Pros                                           | Cons                                       |
| -------------- | ----------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------------------ |
| **argparse**   | Standard library CLI parser               | Positional/optional args, subcommands, type conversion, help generation   | No dependencies, always available              | Verbose, manual help formatting            |
| **click**      | Decorator-based CLI framework             | Commands, groups, options, prompts, file handling, colour output, plugins | Clean API, composable commands, excellent docs | Extra dependency                           |
| **typer**      | Click-based, uses type hints for CLI args | Auto CLI from type hints, auto-completion, rich help                      | Minimal boilerplate, auto-generates help       | Depends on click, newer                    |
| **rich-click** | Click + Rich for beautiful help output    | Rich-formatted help, panels, syntax highlighting, tables                  | Pretty terminal output, drop-in for click      | Extra dependency on top of click           |
| **fire**       | Auto-generates CLI from any Python object | Auto CLI from functions/classes/objects, no decorators needed             | Zero boilerplate                               | Less control over help text and validation |

#### Linting & Formatting

| Tool         | Description               | Capabilities                                                         | Pros                                                     | Cons                                           |
| ------------ | ------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------- |
| **Ruff**     | Linter + formatter (Rust) | 800+ lint rules, auto-fix, import sorting, formatting, pyupgrade     | Blazing fast, replaces flake8+isort+black+pyupgrade+more | Newer, not 100% rule parity with all tools     |
| **flake8**   | Linter                    | Style checks, error detection, plugin system (200+ plugins)          | Mature, huge plugin ecosystem                            | Slower, Python-based, being superseded by Ruff |
| **Black**    | Opinionated formatter     | Deterministic formatting, magic trailing comma, string normalisation | Zero config, consistent                                  | No flexibility, being superseded by Ruff       |
| **isort**    | Import sorter             | Sort imports, configurable sections, profiles (black-compatible)     | Focused, configurable                                    | Separate tool, Ruff handles this now           |
| **autopep8** | PEP 8 formatter           | Fix PEP 8 violations, conservative by default                        | Conservative formatting                                  | Less opinionated than Black, less popular      |

#### Type Checkers

| Tool        | Description                           | Capabilities                                                        | Pros                                         | Cons                                              |
| ----------- | ------------------------------------- | ------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------- |
| **mypy**    | The original Python type checker      | Strict mode, incremental checks, stubs, plugins, daemon mode        | Most mature, wide adoption, plugin ecosystem | Slower, can be strict to configure                |
| **Pyright** | Type checker (powers VS Code Pylance) | Full type inference, watch mode, multi-root workspaces, strict mode | Fast, excellent IDE integration              | Node.js dependency, different strictness defaults |
| **pytype**  | Google's type checker                 | Type inference without annotations, cross-function analysis         | Infers types even without annotations        | Less widely used outside Google                   |

#### Dependency & Security Tools

| Tool           | Install                  | Capabilities                                                                   | Pros                                                                   | Cons                                          |
| -------------- | ------------------------ | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------- | --------------------------------------------- |
| **pip-tools**  | `pip install pip-tools`  | `pip-compile` pins deps to a lock file, `pip-sync` installs exactly those pins | Reproducible builds, minimal lock file, works with pip                 | Extra step in workflow, no auto-update        |
| **pip-audit**  | `pip install pip-audit`  | Scan installed packages against known vulnerability databases (OSV, PyPI)      | Fast, integrates with CI, supports requirements.txt and pyproject.toml | Only checks known CVEs, not code-level issues |
| **pipdeptree** | `pip install pipdeptree` | Visualise dependency tree, detect conflicts, show reverse deps                 | Great for debugging dependency issues, simple output                   | Read-only — doesn't fix problems              |

#### Debugging & Developer Experience Tools

| Tool         | Install                | Capabilities                                                                                | Pros                                                      | Cons                                       |
| ------------ | ---------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------ |
| **rich**     | `pip install rich`     | Pretty tables, tracebacks, progress bars, syntax highlighting, logging, markdown rendering  | Beautiful console output, drop-in traceback handler       | Extra dependency, large package            |
| **icecream** | `pip install icecream` | `ic(variable)` — prints variable name + value + file/line, auto-formats                     | Much better than `print()` debugging, zero-config         | Debug-only — must remove before committing |
| **ipython**  | `pip install ipython`  | Enhanced REPL with tab completion, syntax highlighting, magic commands, `%timeit`, `%debug` | Far better than default Python shell, auto-reload modules | Heavier dependency, not for production     |
| **devtools** | `pip install devtools` | `debug(variable)` — pretty-prints with type info, file/line, colour output                  | Clean debug output, type-aware formatting                 | Less known than icecream, similar purpose  |

#### Commit Convention & Versioning Tools

| Tool                 | Install                               | Capabilities                                                                                                                          | Pros                                                                                                                    | Cons                                                                    |
| -------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **commitizen**       | `pip install commitizen`              | Interactive commit prompts enforcing Conventional Commits, auto-bump version, auto-generate changelog, pre-commit hook, CI validation | All-in-one: commit format + version bump + changelog, configurable via `pyproject.toml`, supports custom commit schemas | Python dependency, learning curve for custom rules                      |
| **commitlint**       | `npm install @commitlint/cli`         | Lint commit messages against Conventional Commits (or custom) rules, integrates with husky                                            | Huge ecosystem, very configurable rules                                                                                 | Node.js dependency, doesn't bump versions or generate changelogs        |
| **semantic-release** | `pip install python-semantic-release` | Auto-determine next version from commits, generate changelog, create Git tags, publish to PyPI                                        | Fully automated release pipeline, CI-friendly                                                                           | Opinionated workflow, less control over individual steps                |
| **towncrier**        | `pip install towncrier`               | Fragment-based changelog generation — each PR adds a news fragment file, assembled at release                                         | Avoids merge conflicts in CHANGELOG, per-PR granularity                                                                 | Extra workflow step (create fragment file per change), not commit-based |
| **standard-version** | `npm install standard-version`        | Bump version, generate changelog from Conventional Commits, create Git tag                                                            | Simple, focused on versioning + changelog                                                                               | Node.js dependency, archived/maintenance-only                           |
| **bump2version**     | `pip install bump2version`            | Find-and-replace version strings across files, create Git tag                                                                         | Simple, language-agnostic, config file driven                                                                           | No commit message parsing, no changelog generation, maintenance mode    |

#### Commit Message Prefixes (Conventional Commits)

| Prefix             | Meaning         | When to use                                            | Version bump | Example                                    |
| ------------------ | --------------- | ------------------------------------------------------ | ------------ | ------------------------------------------ |
| `feat:`            | New feature     | Adding new user-facing functionality                   | Minor        | `feat: add user login endpoint`            |
| `fix:`             | Bug fix         | Fixing a defect or incorrect behavior                  | Patch        | `fix: correct null check in parser`        |
| `docs:`            | Documentation   | Changes to documentation only                          | None         | `docs: update API usage guide`             |
| `style:`           | Code style      | Formatting, whitespace — no logic change               | None         | `style: fix indentation in models`         |
| `refactor:`        | Refactoring     | Restructuring code without changing behavior           | None         | `refactor: extract validation into helper` |
| `perf:`            | Performance     | Improving performance without changing behavior        | Patch        | `perf: cache database query results`       |
| `test:`            | Tests           | Adding or updating tests only                          | None         | `test: add unit tests for auth module`     |
| `build:`           | Build system    | Changes to build config or dependencies                | None         | `build: upgrade hatchling to 1.25`         |
| `ci:`              | CI/CD           | Changes to CI/CD configuration or scripts              | None         | `ci: add mypy check to PR workflow`        |
| `chore:`           | Maintenance     | Routine tasks, tooling, no production code change      | None         | `chore: update .gitignore`                 |
| `revert:`          | Revert          | Reverting a previous commit                            | Varies       | `revert: undo feat: add login endpoint`    |
| `feat!:` / `fix!:` | Breaking change | Append `!` after any type for incompatible API changes | Major        | `feat!: remove deprecated login endpoint`  |

> **Tip:** Use a `BREAKING CHANGE:` footer in the commit body for longer breaking change explanations.

#### Branch Prefixes

| Branch prefix | Meaning          | When to use                                   | Typical merge expectation           | Example                         |
| ------------- | ---------------- | --------------------------------------------- | ----------------------------------- | ------------------------------- |
| `wip/`        | Work in progress | Incomplete work, not ready for review         | Draft PR or no PR yet               | `wip/user-auth-flow`            |
| `spike/`      | Technical spike  | Time-boxed research or proof of concept       | May not merge — results documented  | `spike/graphql-feasibility`     |
| `explore/`    | Exploration      | Experimenting with an idea or library         | May not merge — learning exercise   | `explore/htmx-integration`      |
| `chore/`      | Maintenance      | Routine tasks, config, tooling changes        | Merge after review                  | `chore/update-gitignore`        |
| `feat/`       | Feature          | New user-facing functionality                 | Merge after review + tests pass     | `feat/user-login`               |
| `fix/`        | Bug fix          | Fixing a defect or incorrect behavior         | Merge after review + tests pass     | `fix/null-pointer-in-parser`    |
| `docs/`       | Documentation    | Changes to documentation only                 | Merge after review                  | `docs/update-readme`            |
| `refactor/`   | Refactoring      | Restructuring code without changing behavior  | Merge after review + tests pass     | `refactor/extract-auth-service` |
| `test/`       | Tests            | Adding or updating tests only                 | Merge after review                  | `test/add-auth-unit-tests`      |
| `ci/`         | CI/CD            | Changes to CI/CD configuration                | Merge after review                  | `ci/add-mypy-workflow`          |
| `build/`      | Build system     | Build config, packaging, dependencies         | Merge after review                  | `build/upgrade-hatchling`       |
| `perf/`       | Performance      | Performance improvements                      | Merge after review + benchmarks     | `perf/cache-db-queries`         |
| `style/`      | Code style       | Formatting, whitespace — no logic change      | Merge after review                  | `style/fix-indentation`         |
| `release/`    | Release          | Preparing a release (version bump, changelog) | Merge to main, tag, deploy          | `release/v1.2.0`                |
| `hotfix/`     | Hotfix           | Urgent production fix                         | Fast-track merge + deploy           | `hotfix/fix-login-crash`        |
| `deps/`       | Dependencies     | Dependency updates (manual or grouped)        | Merge after CI passes               | `deps/bump-requests-2.32`       |
| `sec/`        | Security         | Security-related fix or hardening             | Merge after review (may be private) | `sec/patch-ssrf-vulnerability`  |

#### What this project uses

| Category           | Tool          | Why                                                 |
| ------------------ | ------------- | --------------------------------------------------- |
| Build backend      | Hatchling     | Auto-discovers src/ layout, minimal config          |
| Project manager    | Hatch         | Envs, scripts, test matrices — one `pyproject.toml` |
| Task runner        | Hatch scripts | No extra tools needed                               |
| CLI framework      | argparse      | No dependencies for a simple boilerplate            |
| Linter + formatter | Ruff          | Fast, replaces multiple tools                       |
| Type checker       | mypy          | Most mature, strict mode                            |
| Testing            | pytest        | De facto standard                                   |

---

## GitHub Actions

### Why Pin to SHAs?

Tags like `@v4` are mutable — someone could push malicious code and move the tag. SHAs are immutable. Always pin to full SHA with a version comment:

```yaml
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

### Workflow Organization

Separate files > one giant file:

- Easier to disable (just rename to `_workflow.yml`)
- Each gets its own permissions
- Failures are isolated

### Secrets vs Variables

GitHub Actions has two ways to store configuration values:

| Aspect         | Secrets                        | Variables                           |
| -------------- | ------------------------------ | ----------------------------------- |
| **Visibility** | Hidden forever after creation  | Visible to anyone with repo access  |
| **In logs**    | Auto-masked if printed (`***`) | Printed in plain text               |
| **Storage**    | Encrypted at rest              | Plain text                          |
| **Access**     | `${{ secrets.NAME }}`          | `${{ vars.NAME }}`                  |
| **Use for**    | Tokens, passwords, API keys    | Feature flags, non-sensitive config |

**Rule of thumb:** If it's a token, key, or credential — use **Secrets**. If it's a
simple on/off flag or display value — use **Variables**.

**Example uses in this project:**

| Value              | Type     | Why                                                        |
| ------------------ | -------- | ---------------------------------------------------------- |
| `CODECOV_TOKEN`    | Secret   | Authenticates coverage uploads — leak = account compromise |
| `ENABLE_WORKFLOWS` | Variable | Just a feature flag — no security impact                   |
| `NPM_TOKEN`        | Secret   | Publish access to npm registry                             |

**Setting them:**

1. Repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **Secrets** tab or **Variables** tab
3. Click **New repository secret** or **New repository variable**

---

## Static Analysis Tools

| Tool        | Purpose                 | Speed               |
| ----------- | ----------------------- | ------------------- |
| **Ruff**    | Linting + formatting    | ⚡ Very fast (Rust) |
| **Mypy**    | Type checking           | 🐢 Slower           |
| **Pyright** | Type checking (VS Code) | ⚡ Fast             |
| **Bandit**  | Security scanning       | 🐢 Moderate         |

**Ruff** replaces: flake8, isort, black, pyupgrade, and more. One tool, one config.

---

## Quality Gates

A **quality gate** is a checkpoint that code must pass before moving forward (e.g., merging to main, deploying to production).

### Common Quality Gates in CI

| Gate                     | What It Checks         | Tool              |
| ------------------------ | ---------------------- | ----------------- |
| **Tests pass**           | Code works as expected | pytest            |
| **Linting passes**       | Code style, bugs       | Ruff              |
| **Type checking passes** | Type correctness       | Mypy/Pyright      |
| **Coverage threshold**   | Enough tests exist     | pytest-cov        |
| **Security scan**        | No vulnerabilities     | Bandit, pip-audit |
| **Spell check**          | No typos               | codespell         |

> **codespell: report-only by default.** codespell does _not_ auto-fix typos unless you pass `--write-changes` (or `-w`). Without that flag it reports the misspelling and a suggested fix, then exits non-zero — which blocks your commit. You have two options:
>
> 1. **Auto-fix:** Add `-w` to the hook args in `.pre-commit-config.yaml`:
>     ```yaml
>     - id: codespell
>       args: [-w, --skip, ".git,.venv,dist,build,..."]
>     ```
>     codespell will rewrite the file in-place. The commit still fails (the file changed), but re-running `git add` + `git commit` picks up the fix.
> 2. **Manual fix:** Read the output, fix the typo yourself, then re-commit. This is safer when codespell's suggestion is wrong (it happens with domain-specific terms).
>
> **Tip:** If codespell flags a word that's correct (e.g., a variable name or technical term), add it to an ignore list: `args: [-L, "word1,word2", --skip, "..."]` or set `[tool.codespell]` in `pyproject.toml` with `ignore-words-list = "word1,word2"`.

### Enforcing Quality Gates

1. **GitHub Branch Protection** — Require status checks to pass before merge
2. **CI Workflow** — Each job is a gate; if one fails, PR can't merge
3. **Pre-commit Hooks** — Catch issues before they even reach CI

### Soft vs Hard Gates

- **Hard gate** — Must pass (blocks merge/deploy)
- **Soft gate** — Informational only (warns but doesn't block)

Example: When adopting type checking, start with a soft gate (`continue-on-error: true`) while adding type hints gradually.

### Why Quality Gates Matter

- Catch bugs early (cheaper to fix)
- Maintain code consistency
- Build confidence in deployments
- Document quality expectations

---

## Containers — Production vs Development vs Orchestration

This project has three container-related files that serve completely different purposes.
Understanding the distinction is important.

### The Big Picture

```text
                    ┌─────────────────────────┐
                    │   Docker / Podman       │  ← The engine that runs everything
                    │   (container runtime)   │
                    └───────────┬─────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │ Containerfile │   │ devcontainer  │   │ docker-compose│
    │ (production)  │   │ (development) │   │ (orchestration)│
    └───────────────┘   └───────────────┘   └───────────────┘
```

### Comparison Table

| Aspect          | Containerfile               | Dev Container            | Docker Compose                 |
| --------------- | --------------------------- | ------------------------ | ------------------------------ |
| **Location**    | `Containerfile` (repo root) | `.devcontainer/`         | `docker-compose.yml`           |
| **Purpose**     | Build production image      | Development environment  | Run/orchestrate containers     |
| **Contains**    | Minimal app only (~150MB)   | Full dev tools (~1GB+)   | References other images        |
| **User**        | Run the application         | Write code interactively | Manage multi-service setups    |
| **When to use** | CI/CD, deployment           | Daily development        | Local testing, multi-container |

### 1. Containerfile (Production)

A recipe for building a minimal **production** container image. Contains only your
installed application — no dev tools, no tests, no source code.

**How to use:**

```bash
# Build the image
docker build -t simple-python-boilerplate -f Containerfile .

# Run your application
docker run --rm simple-python-boilerplate
```

**Key features:**

- Multi-stage build (builder stage + runtime stage)
- Non-root user for security
- Pinned base image digest for reproducibility
- OCI-compliant (works with Docker, Podman, etc.)

### 2. Dev Container (Development)

A VS Code feature that runs your entire development environment inside a container.
Everything is pre-configured: Python, Node.js, pre-commit hooks, extensions.

**How to use:**

1. Install Docker Desktop (or Podman)
2. Install VS Code extension: "Dev Containers"
3. Open repo in VS Code
4. Click "Reopen in Container" (or Cmd/Ctrl+Shift+P → `Dev Containers: Reopen in Container`)

Alternatively, use GitHub Codespaces — the config works there automatically.

**Key features:**

- Zero-setup onboarding for new contributors
- Consistent environment across machines
- All extensions and settings pre-configured
- Works with GitHub Codespaces

### 3. Docker Compose (Orchestration)

A declarative way to build/run containers with all options specified in a file.
Useful for local testing and multi-service setups (app + database, etc.).

**How to use:**

```bash
# Build and run
docker compose up --build

# Run in background
docker compose up -d --build

# Stop
docker compose down

# View logs
docker compose logs -f
```

**Key features:**

- Version-controlled run configuration
- Easy to add services (database, cache, etc.)
- Simpler than remembering `docker run` flags

### When to Use Which

| Scenario                                      | Use                                            |
| --------------------------------------------- | ---------------------------------------------- |
| "I want to deploy this app"                   | Containerfile → build image → push to registry |
| "I want to develop this project"              | Dev Container → VS Code "Reopen in Container"  |
| "I want to test the production build locally" | Docker Compose → `docker compose up --build`   |
| "I want to run app + database together"       | Docker Compose with multiple services          |
| "I'm a new contributor, how do I start?"      | Dev Container or Codespaces                    |

### Docker vs Podman

Both are container runtimes that can execute all three configurations above:

| Aspect            | Docker                                          | Podman                |
| ----------------- | ----------------------------------------------- | --------------------- |
| **Architecture**  | Client-server (daemon)                          | Daemonless            |
| **Root required** | Historically yes                                | Rootless by default   |
| **Compatibility** | Industry standard                               | Docker CLI-compatible |
| **License**       | Docker Desktop requires license for enterprises | Fully open source     |

For most purposes, they're interchangeable. This project uses "Containerfile" (Podman's
preferred name) instead of "Dockerfile" but both tools understand both names.

See: [ADR 025](../adr/025-container-strategy.md)

---

## Virtual Environments

### Quick Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # macOS/Linux
pip install -e ".[dev]"
```

### Check Which Python

```bash
python -c "import sys; print(sys.executable)"
```

If it doesn't show `.venv`, you're using the wrong Python!

### Viewing Installed Packages

```bash
# List all packages in the current environment (venv or global)
pip list

# Same but in requirements.txt format (useful for diffing)
pip freeze

# Show details for a specific package (version, location, dependencies)
pip show <package-name>

# Show where pip is installing to
pip -V
```

**Global vs local (venv):** The commands above always operate on whichever Python environment is active. If a venv is activated, they show/affect only that venv. If no venv is active, they target the global (user or system) Python.

To explicitly target the global Python when a venv is active:

```bash
# Windows — use the full path to the global pip
& "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python3*\Scripts\pip.exe" list

# macOS/Linux
/usr/bin/python3 -m pip list
# or
python3 -m pip list  # if no venv is active
```

### Removing Packages

```bash
# Uninstall a single package
pip uninstall <package-name>

# Uninstall without confirmation prompt
pip uninstall -y <package-name>
```

#### Bulk-Remove All pip Packages

To wipe every package in the current environment (useful for a clean slate):

```bash
# Generate the list and pipe it to uninstall (keeps pip itself)
pip freeze | xargs pip uninstall -y

# PowerShell equivalent
pip freeze | ForEach-Object { pip uninstall -y $_ }
```

> **Easier alternative for venvs:** Just delete and recreate the venv. It's faster and guarantees a clean state:
>
> ```bash
> deactivate                    # exit the venv first
> Remove-Item -Recurse .venv   # Windows PowerShell
> rm -rf .venv                 # macOS/Linux
> python -m venv .venv         # recreate
> pip install -e ".[dev]"      # reinstall project deps
> ```

#### Remove a Global Package

```bash
# Deactivate any venv first, then uninstall
deactivate
pip uninstall <package-name>
```

> **Tip:** Avoid installing packages globally. Use virtual environments for project work and `pipx` for standalone CLI tools (e.g., `pipx install ruff`). This keeps the global Python clean and avoids version conflicts.

---

## Command Workflow — How Tools Layer Together

Understanding how commands flow through the tooling stack helps when debugging
issues or customizing workflows.

### The Hierarchy

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  YOU (developer)                                                            │
│  ↓                                                                          │
│  task test         ← Task runner (Taskfile.yml) — human-friendly wrapper    │
│  ↓                                                                          │
│  hatch run test    ← Hatch — manages virtualenv + runs command inside it    │
│  ↓                                                                          │
│  pytest            ← Actual tool — runs in the Hatch-managed environment    │
│  ↓                                                                          │
│  Python            ← Interpreter — executes the test code                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Three Ways to Run the Same Thing

| Command          | What happens                                                             |
| ---------------- | ------------------------------------------------------------------------ |
| `task test`      | Taskfile finds `test:` task → runs `hatch run test`                      |
| `hatch run test` | Hatch activates `default` env → runs `pytest`                            |
| `pytest`         | Direct call — only works if you're already in a venv with deps installed |

All three ultimately run pytest. The layers add convenience:

- **Task** — Memorable names, can chain commands, no Hatch knowledge needed
- **Hatch** — Ensures correct virtualenv, handles Python version matrix
- **Direct** — Fast, but requires manual env management

### Where Each Layer Is Configured

| Layer             | Config file                                    | What it defines                                              |
| ----------------- | ---------------------------------------------- | ------------------------------------------------------------ |
| **Task**          | `Taskfile.yml`                                 | Task names, descriptions, which `hatch run` commands to call |
| **Hatch envs**    | `pyproject.toml` `[tool.hatch.envs.*]`         | Environment names, features, Python versions                 |
| **Hatch scripts** | `pyproject.toml` `[tool.hatch.envs.*.scripts]` | Script names → actual CLI commands                           |
| **Tools**         | `pyproject.toml` `[tool.*]`                    | Tool-specific config (pytest, ruff, mypy, coverage)          |

### Example: Tracing `task lint`

```text
task lint
  └→ Taskfile.yml defines: cmds: ["hatch run lint"]
      └→ pyproject.toml [tool.hatch.envs.default.scripts] defines: lint = "ruff check src/ tests/"
          └→ ruff check src/ tests/
              └→ ruff reads [tool.ruff] from pyproject.toml
```

### When CI Skips Taskfile

GitHub Actions workflows call `hatch run` directly, not `task`. Why?

1. **Fewer dependencies** — No need to install Task binary in CI
2. **Explicit** — YAML shows exactly what runs, no indirection
3. **Standard** — Other projects can copy workflow without Taskfile adoption

```yaml
# CI workflow
- run: hatch run test # Direct, not `task test`
```

### Direct Execution (Skip All Layers)

If you're in the venv already, you can call tools directly:

```bash
# After: hatch shell  OR  source .venv/bin/activate
pytest                  # No hatch/task wrapper
ruff check src/
mypy src/
```

This is faster for quick checks but bypasses Hatch's environment guarantees.

### Debugging Tips

| Problem                      | Check                                                           |
| ---------------------------- | --------------------------------------------------------------- |
| "Command not found"          | Are you in a venv? Run `hatch shell` or activate manually       |
| "Task not found"             | Is Task installed? `task --version` or use `hatch run` directly |
| "hatch run X fails"          | Does the script exist in `[tool.hatch.envs.default.scripts]`?   |
| "Works locally, fails in CI" | CI uses `hatch run`, not `task`. Check if they match.           |

### Why Not Just Use Make?

This project uses Taskfile instead of Make because:

- **Cross-platform** — Works identically on Windows, no `make` installation needed
- **YAML > Makefile syntax** — No tab-sensitivity issues
- **Built-in help** — `task` lists all tasks with descriptions

See: [ADR 017](../adr/017-task-runner.md)

---

## Pre-commit Hooks

Pre-commit hooks run checks _before_ code is committed, catching issues locally before they reach CI.

### Setup

```bash
pip install pre-commit
pre-commit install
```

### Configuration (`.pre-commit-config.yaml`)

```yaml
repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.8.6
      hooks:
          - id: ruff # Linting
            args: [--fix]
          - id: ruff-format # Formatting

    - repo: https://github.com/pre-commit/mirrors-mypy
      rev: v1.14.1
      hooks:
          - id: mypy
            additional_dependencies: []

    - repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v5.0.0
      hooks:
          - id: trailing-whitespace
          - id: end-of-file-fixer
          - id: check-yaml
          - id: check-added-large-files
```

### Key Commands

| Command                      | Purpose                            |
| ---------------------------- | ---------------------------------- |
| `pre-commit install`         | Enable hooks for this repo         |
| `pre-commit run --all-files` | Run on all files (not just staged) |
| `pre-commit autoupdate`      | Update hook versions               |
| `git commit --no-verify`     | Skip hooks (emergency only!)       |

### Why Pre-commit > Manual Checks

- **Automatic** — Can't forget to run it
- **Fast feedback** — Fix before pushing
- **Consistent** — Same checks for everyone
- **CI friendly** — Run same hooks in CI as backup

### Authoring Custom Git Hooks

Beyond using existing hooks, you can author your own and publish them for others to use. Custom hooks live in a Git repository with a `.pre-commit-hooks.yaml` file at the root that declares the available hooks.

#### How It Works

1. Create a new Git repository for your hook(s).
2. Write the script or tool that performs the check.
3. Add a `.pre-commit-hooks.yaml` file describing the hook(s).
4. Tag a release — consumers pin to this tag via `rev` in their `.pre-commit-config.yaml`.

#### `.pre-commit-hooks.yaml` Fields

The `.pre-commit-hooks.yaml` file is a list of hook definitions. Each entry supports these fields:

| Field                        | Required | Description                                                                             |
| ---------------------------- | -------- | --------------------------------------------------------------------------------------- |
| `id`                         | Yes      | Unique identifier for the hook (used in consumers' `hooks:` list)                       |
| `name`                       | Yes      | Human-readable name shown during execution                                              |
| `entry`                      | Yes      | The executable to run (script path, command, or console_script)                         |
| `language`                   | Yes      | How to install/run the hook (`python`, `node`, `system`, `script`, `docker`, etc.)      |
| `files`                      | No       | Regex pattern for filenames to pass to the hook (default: `''` — all files)             |
| `exclude`                    | No       | Regex pattern for filenames to exclude                                                  |
| `types`                      | No       | File types to filter on (e.g., `[python]`, `[yaml]`) — uses `identify` library types    |
| `types_or`                   | No       | Like `types` but matches if _any_ type matches (OR logic instead of AND)                |
| `exclude_types`              | No       | File types to exclude                                                                   |
| `always_run`                 | No       | If `true`, run even when no matching files are staged (default: `false`)                |
| `pass_filenames`             | No       | If `true`, staged filenames are passed as arguments (default: `true`)                   |
| `require_serial`             | No       | If `true`, disable parallel execution for this hook (default: `false`)                  |
| `args`                       | No       | Default arguments passed to `entry` (consumers can override via `args` in their config) |
| `description`                | No       | Short description of what the hook does                                                 |
| `minimum_pre_commit_version` | No       | Minimum pre-commit version required (e.g., `'3.0.0'`)                                   |
| `stages`                     | No       | Which git hook stages to run in (e.g., `[pre-commit]`, `[pre-push]`, `[commit-msg]`)    |
| `verbose`                    | No       | If `true`, force hook output to be printed even on success (default: `false`)           |
| `additional_dependencies`    | No       | Extra packages to install alongside the hook                                            |
| `language_version`           | No       | Version of the language runtime to use (e.g., `python3.11`)                             |

#### Minimal Example

A simple hook that checks for `TODO` comments:

```yaml
# .pre-commit-hooks.yaml
- id: no-todos
  name: Check for TODO comments
  entry: grep -rn TODO
  language: system
  types: [python]
  pass_filenames: true
```

#### Python Script Hook Example

For hooks written in Python, structure the repo as an installable package:

```text
my-hooks/
├── .pre-commit-hooks.yaml
├── pyproject.toml
└── my_hooks/
    └── check_something.py
```

```yaml
# .pre-commit-hooks.yaml
- id: check-something
  name: Check something custom
  entry: check-something # console_scripts entry point
  language: python
  types: [python]
```

The `language: python` setting tells pre-commit to create an isolated virtualenv and `pip install` the hook repository, so any `console_scripts` defined in `pyproject.toml` become available as the `entry`.

#### Hook Stages

Git supports multiple hook points. Pre-commit can target different stages:

| Stage                | Git Hook             | When It Runs                                                |
| -------------------- | -------------------- | ----------------------------------------------------------- |
| `pre-commit`         | `pre-commit`         | Before commit is created (default)                          |
| `pre-merge-commit`   | `pre-merge-commit`   | Before merge commit is created                              |
| `pre-push`           | `pre-push`           | Before push to remote                                       |
| `commit-msg`         | `commit-msg`         | After commit message is entered (can validate or modify it) |
| `post-checkout`      | `post-checkout`      | After `git checkout` or `git switch`                        |
| `post-commit`        | `post-commit`        | After commit is created                                     |
| `post-merge`         | `post-merge`         | After a merge completes                                     |
| `post-rewrite`       | `post-rewrite`       | After `git rebase` or `git commit --amend`                  |
| `prepare-commit-msg` | `prepare-commit-msg` | Before the commit message editor opens                      |
| `manual`             | —                    | Only runs via `pre-commit run --hook-stage manual`          |

To install hooks for non-default stages: `pre-commit install --hook-type commit-msg`

#### Common Hooks by Stage

> **Note:** The repos listed below are popular, widely-used choices — not an exhaustive list. Many alternative hooks exist for each stage. Browse [pre-commit.com/hooks](https://pre-commit.com/hooks.html) for a searchable directory.

**`pre-commit`** — Fast checks that run on every commit (the default stage):

| Hook                      | Repo                               | What It Does                                     |
| ------------------------- | ---------------------------------- | ------------------------------------------------ |
| `trailing-whitespace`     | pre-commit/pre-commit-hooks        | Strip trailing whitespace                        |
| `end-of-file-fixer`       | pre-commit/pre-commit-hooks        | Ensure files end with a newline                  |
| `check-yaml`              | pre-commit/pre-commit-hooks        | Validate YAML syntax                             |
| `check-toml`              | pre-commit/pre-commit-hooks        | Validate TOML syntax                             |
| `check-json`              | pre-commit/pre-commit-hooks        | Validate JSON syntax                             |
| `check-ast`               | pre-commit/pre-commit-hooks        | Validate Python syntax                           |
| `check-added-large-files` | pre-commit/pre-commit-hooks        | Block oversized files                            |
| `check-merge-conflict`    | pre-commit/pre-commit-hooks        | Detect conflict markers (`<<<<<<<`)              |
| `debug-statements`        | pre-commit/pre-commit-hooks        | Catch leftover `breakpoint()` / debugger imports |
| `detect-private-key`      | pre-commit/pre-commit-hooks        | Block private key files                          |
| `mixed-line-ending`       | pre-commit/pre-commit-hooks        | Normalize line endings                           |
| `ruff`                    | astral-sh/ruff-pre-commit          | Lint Python (replaces flake8, isort, pyupgrade)  |
| `ruff-format`             | astral-sh/ruff-pre-commit          | Format Python (replaces black)                   |
| `mypy`                    | pre-commit/mirrors-mypy            | Type check Python                                |
| `bandit`                  | PyCQA/bandit                       | Security linting for Python                      |
| `codespell`               | codespell-project/codespell        | Catch common typos in code and docs              |
| `validate-pyproject`      | abravalheri/validate-pyproject     | Validate pyproject.toml schema                   |
| `actionlint`              | rhysd/actionlint                   | Lint GitHub Actions workflows                    |
| `check-github-workflows`  | python-jsonschema/check-jsonschema | Validate workflow YAML against schema            |

**`commit-msg`** — Validate or modify the commit message after the user writes it:

| Hook                      | Repo                                     | What It Does                                     |
| ------------------------- | ---------------------------------------- | ------------------------------------------------ |
| `conventional-pre-commit` | compilerla/conventional-pre-commit       | Enforce Conventional Commits format              |
| `commitizen`              | commitizen-tools/commitizen              | Validate commit message against commitizen rules |
| `commitlint`              | alessandrojcm/commitlint-pre-commit-hook | Lint commit messages (Node-based)                |
| `gitlint`                 | jorisroovers/gitlint                     | Configurable commit message linter               |

**`pre-push`** — Slower checks that run before pushing to remote:

| Hook             | Repo                       | What It Does                               |
| ---------------- | -------------------------- | ------------------------------------------ |
| `pytest` (local) | local                      | Run full test suite                        |
| `gitleaks`       | gitleaks/gitleaks          | Secret detection across git history        |
| `trufflehog`     | trufflesecurity/trufflehog | Deep secret scanning                       |
| `mypy`           | pre-commit/mirrors-mypy    | Type check (if too slow for pre-commit)    |
| `bandit`         | PyCQA/bandit               | Security scan (if too slow for pre-commit) |

**`prepare-commit-msg`** — Modify the commit message before the editor opens:

| Hook                 | Repo                        | What It Does                            |
| -------------------- | --------------------------- | --------------------------------------- |
| `commitizen` (cz)    | commitizen-tools/commitizen | Interactive commit message prompts      |
| Custom template hook | local                       | Pre-fill commit message from a template |

**`post-checkout` / `post-merge`** — Run setup tasks after branch changes:

| Hook               | Repo  | What It Does                             |
| ------------------ | ----- | ---------------------------------------- |
| Auto `pip install` | local | Re-install deps after switching branches |
| Auto `npm install` | local | Re-install Node deps                     |
| DB migration check | local | Warn if unapplied migrations exist       |

**`manual`** — Opt-in only, run explicitly with `pre-commit run <id> --hook-stage manual`:

| Hook                | Repo                         | What It Does                                      |
| ------------------- | ---------------------------- | ------------------------------------------------- |
| `typos`             | crate-ci/typos               | Rust-based spellchecker (stricter than codespell) |
| `markdownlint-cli2` | DavidAnson/markdownlint-cli2 | Markdown linting (Node-based)                     |
| `hadolint-docker`   | hadolint/hadolint            | Dockerfile/Containerfile linter                   |
| `gitleaks`          | gitleaks/gitleaks            | Secret detection (when not on pre-push)           |

#### References

- [Creating new hooks — pre-commit docs](https://pre-commit.com/#creating-new-hooks) — Official guide to authoring hooks
- [`.pre-commit-hooks.yaml` specification](https://pre-commit.com/#pre-commit-hooks-yaml) — Full field reference for hook definitions
- [Supported languages](https://pre-commit.com/#supported-languages) — All `language` values and how each is installed/executed
- [Supported hook stages](https://pre-commit.com/#confining-hooks-to-run-at-certain-stages) — Details on `stages` field and hook stage configuration
- [Git documentation: githooks](https://git-scm.com/docs/githooks) — Underlying Git hooks that pre-commit wraps
- [identify library — file type tags](https://github.com/pre-commit/identify) — Reference for `types` / `types_or` values

---

## GitHub Actions Workflows

### Anatomy of a Workflow

```yaml
name: Tests # Display name

on: # Triggers
    push:
        branches: [main]
    pull_request:
        branches: [main]

permissions: # Least-privilege access
    contents: read

jobs:
    test:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@... # Pinned SHA
            - uses: actions/setup-python@...
              with:
                  python-version: "3.11"
            - run: pip install -e ".[dev]"
            - run: pytest
```

### Common Workflow Patterns

| Workflow       | Triggers     | Purpose           |
| -------------- | ------------ | ----------------- |
| `test.yml`     | push, PR     | Run tests         |
| `lint.yml`     | push, PR     | Ruff, mypy        |
| `release.yml`  | tag push     | Publish to PyPI   |
| `security.yml` | schedule, PR | Dependency audits |

### Matrix Testing

Test across multiple Python versions:

```yaml
strategy:
    matrix:
        python-version: ["3.11", "3.12", "3.13"]
        os: [ubuntu-latest, windows-latest]
```

### Caching Dependencies

Speed up workflows by caching pip:

```yaml
- uses: actions/setup-python@...
  with:
      python-version: "3.11"
      cache: "pip"
```

### Useful Actions

| Action                        | Purpose            |
| ----------------------------- | ------------------ |
| `actions/checkout`            | Clone repo         |
| `actions/setup-python`        | Install Python     |
| `actions/cache`               | Cache dependencies |
| `codecov/codecov-action`      | Upload coverage    |
| `pypa/gh-action-pypi-publish` | Publish to PyPI    |

### How to Configure Workflow YAML Files

#### Where to learn

The authoritative reference is [GitHub Actions documentation](https://docs.github.com/en/actions).
Key pages:

| Topic                         | URL                                                                         |
| ----------------------------- | --------------------------------------------------------------------------- |
| Workflow syntax               | `docs.github.com/en/actions/reference/workflow-syntax-for-github-actions`   |
| Events that trigger workflows | `docs.github.com/en/actions/reference/events-that-trigger-workflows`        |
| Contexts & expressions        | `docs.github.com/en/actions/learn-github-actions/contexts`                  |
| Permissions                   | `docs.github.com/en/actions/security-guides/automatic-token-authentication` |
| Encrypted secrets             | `docs.github.com/en/actions/security-guides/encrypted-secrets`              |
| Variables                     | `docs.github.com/en/actions/learn-github-actions/variables`                 |

Each action's own repo README documents its inputs/outputs (e.g., `actions/checkout`, `peter-evans/create-pull-request`).

#### YAML structure at a glance

A workflow file lives in `.github/workflows/` and has four main sections:

```yaml
name: Human-readable name # Shows in the Actions tab

on: # 1. TRIGGERS — when does this run?
    push: ...
    pull_request: ...
    schedule: ...
    workflow_dispatch: ...

permissions: # 2. PERMISSIONS — least-privilege GITHUB_TOKEN scope
    contents: read

jobs: # 3. JOBS — what to run (each gets its own runner)
    my-job:
        runs-on: ubuntu-latest
        if: <condition> # 4. GUARDS — should this job run at all?
        steps:
            - uses: owner/action@sha # Use a published action
            - run: echo "shell command" # Run a shell command
```

#### Triggers (`on:`)

| Trigger             | When it fires                              | Notes                                               |
| ------------------- | ------------------------------------------ | --------------------------------------------------- |
| `push`              | Code pushed to matching branches           | Can filter by `branches:` and `paths:`              |
| `pull_request`      | PR opened/synced against matching branches | Uses the **PR head branch's** workflow file         |
| `schedule`          | Cron expression (UTC)                      | **Only runs from default branch** (usually `main`)  |
| `workflow_dispatch` | Manual "Run workflow" button               | Uses the workflow file from the **selected branch** |
| `workflow_run`      | After another workflow completes           | Useful for chaining workflows                       |

**Key gotcha:** `schedule:` always uses the workflow file on `main`. If you
change a cron schedule on a branch, it won't take effect until merged.
`workflow_dispatch` does use the selected branch's file, so you can test
workflow changes via the manual trigger before merging.

#### Permissions (least privilege)

Always declare the minimum permissions needed. GitHub's default `GITHUB_TOKEN`
has broad access; narrowing it limits blast radius if a dependency is compromised.

```yaml
permissions:
    contents: read # Read repo contents (most workflows)
    pull-requests: write # Create/comment on PRs
    security-events: write # Upload SARIF to Security tab
    issues: write # Comment on / close issues
    id-token: write # OIDC token (OpenSSF Scorecard, cloud auth)
```

**Repo-level setting:** Some permissions also require a repo setting toggle.
Example: "Allow GitHub Actions to create and approve pull requests" must be
enabled at **Settings → Actions → General → Workflow permissions** for any
workflow that creates PRs (like `pre-commit-update.yml`).

#### Guards / Conditionals (`if:`)

Control whether a job runs using expressions:

```yaml
jobs:
    deploy:
        # Only run on the main repo, not forks
        if: github.repository == 'myorg/myrepo'

    auto-merge:
        # Only run for Dependabot PRs
        if: github.actor == 'dependabot[bot]'
```

This project uses a repository guard pattern (see [ADR 011](../adr/011-repository-guard-pattern.md))
to prevent workflows from running on forks that haven't opted in. Template users
can opt in by replacing the slug, setting `vars.ENABLE_WORKFLOWS`, or setting
per-workflow variables.

#### Repository Variables vs Secrets

| Feature               | Variables (`vars.*`)      | Secrets (`secrets.*`)      |
| --------------------- | ------------------------- | -------------------------- |
| Visible in logs       | Yes                       | Masked (never printed)     |
| Use case              | Feature flags, config     | API keys, tokens           |
| Set at                | Settings → Variables      | Settings → Secrets         |
| Access in YAML        | `${{ vars.MY_VAR }}`      | `${{ secrets.MY_SECRET }}` |
| Case-sensitive values | Yes (`'true'` ≠ `'True'`) | N/A                        |

**Gotcha:** Variable comparisons are case-sensitive. `vars.ENABLE_FOO == 'true'`
will not match if the variable is set to `'True'` or `'TRUE'`.

#### Scheduled Workflows (cron)

Cron uses five fields, all in **UTC**:

```text
┌─── minute (0–59)
│ ┌─── hour (0–23)
│ │ ┌─── day of month (1–31)
│ │ │ ┌─── month (1–12)
│ │ │ │ ┌─── day of week (0=Sun … 6=Sat)
│ │ │ │ │
* * * * *
```

Examples:

- `"0 3 * * *"` — daily at 03:00 UTC
- `"0 9 * * 1"` — every Monday at 09:00 UTC
- `"0 13 * * 1"` — every Monday at 13:00 UTC

Because cron is fixed to UTC, local time shifts with DST (Daylight Saving Time).
For US Eastern: 03:00 UTC = 22:00 EST (Nov–Mar) / 23:00 EDT (Mar–Nov).

**Important:** Scheduled workflows only run on the default branch. Changing a
cron schedule on a feature branch has no effect until merged.

#### SHA-Pinning Actions

Always pin actions to full commit SHAs, not tags:

```yaml
# BAD — tag can be moved to point at malicious code
uses: actions/checkout@v4

# GOOD — immutable commit reference
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

The version comment (`# v4.2.2`) is just for humans — GitHub resolves the SHA.
If an action maintainer force-pushes or deletes the commit, the SHA becomes
invalid and the workflow will fail at "Set up job" with an error like:
_"An action could not be found at the URI"_.

To find the correct SHA for a release:

1. Go to the action's GitHub releases page
2. Click the tag → click the commit hash
3. Copy the **full 40-character SHA** from the URL

#### Common Mistakes I've Hit

1. **`.dockerignore` excluding build-required files** — Hatchling needs
   `README.md` and `LICENSE` during `python -m build`. If your container
   ignore file excludes `*.md` or `LICENSE`, the container build fails
   silently during the wheel step. Fix: add `!README.md` after `*.md` and
   remove `LICENSE` from the exclusion list.

2. **Invalid action SHAs** — A pinned SHA that doesn't exist (typo,
   truncated, or force-pushed upstream) causes an immediate failure at
   "Set up job". Always verify the SHA exists on the action's releases page.

3. **Repo setting not enabled** — Workflows with `pull-requests: write` or
   that create PRs also need the repo-level "Allow GitHub Actions to create
   and approve pull requests" setting enabled. The workflow permissions in
   YAML are necessary but not sufficient.

4. **Schedule changes on branches** — Editing a cron schedule on a feature
   branch does nothing. Scheduled workflows always run from `main`.

5. **Variable case sensitivity** — `vars.ENABLE_FOO == 'true'` won't match
   `'True'`. Always use lowercase `'true'` as the convention.

6. **Path-filtered workflows and required checks** — If a workflow only runs
   on certain file paths (e.g., `paths: ["src/**"]`), it won't run on PRs
   that don't touch those paths. If that workflow is a required check, the
   PR will hang forever waiting. Solution: exclude path-filtered workflows
   from required checks, or use a CI gate pattern.

---

## Branch Protection

Branch protection prevents direct pushes to important branches and enforces quality gates.

### Setting Up (GitHub)

**Settings → Branches → Add rule**

### Recommended Settings for `main`

| Setting                            | Purpose                |
| ---------------------------------- | ---------------------- |
| ✅ Require PR before merging       | No direct pushes       |
| ✅ Require status checks           | CI must pass           |
| ✅ Require branches up to date     | Must merge main first  |
| ✅ Require conversation resolution | All comments addressed |
| ⬜ Require approvals               | Set to 1+ for teams    |
| ⬜ Restrict who can push           | Limit to admins        |

### Required Status Checks

Add these as required checks:

- `test` — Tests pass
- `lint` — Linting passes
- `type-check` — Types are correct

### Bypassing (Emergency)

Admins can bypass, but it's logged. Use sparingly!

---

## Security Scanning

### Tools Overview

| Tool           | What It Does                | When to Run        |
| -------------- | --------------------------- | ------------------ |
| **pip-audit**  | Checks deps for CVEs        | CI, pre-release    |
| **Bandit**     | Finds security bugs in code | CI, pre-commit     |
| **Safety**     | Dependency vulnerabilities  | CI                 |
| **Trivy**      | Container scanning          | CI (Docker builds) |
| **Dependabot** | Auto-creates upgrade PRs    | Scheduled          |

### What Is SARIF?

**SARIF** (Static Analysis Results Interchange Format) is a standardized JSON format for the output of static analysis tools. It's an [OASIS standard](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html) designed so that different tools (linters, security scanners, type checkers) can all produce results in the same shape.

**Why it matters:**

- **GitHub Security tab** — When a CI workflow uploads a `.sarif` file via `github/codeql-action/upload-sarif`, the findings appear as **Code scanning alerts** in the repository's Security tab. This gives a unified view of vulnerabilities across tools.
- **Tool-agnostic** — Whether results come from Trivy, Grype, Bandit, CodeQL, or Scorecard, SARIF normalises them into one format.
- **IDE integration** — VS Code extensions (e.g., SARIF Viewer) can display SARIF results inline, showing issues right where the code is.

**Structure:** A SARIF file contains `runs`, each with a `tool` descriptor and an array of `results`. Each result has a `ruleId`, `message`, `level` (error/warning/note), and `locations` pointing to specific files and line numbers.

**In this project:** The `scorecard.yml`, `container-scan.yml`, and `nightly-security.yml` workflows all produce SARIF output and upload it to GitHub's Security tab.

### pip-audit in CI

```yaml
- name: Security audit
  run: |
      pip install pip-audit
      pip-audit
```

### Bandit in CI

```yaml
- name: Security scan
  run: |
      pip install bandit
      bandit -r src/ -ll
```

### Dependabot Configuration (`.github/dependabot.yml`)

```yaml
version: 2
updates:
    - package-ecosystem: "pip"
      directory: "/"
      schedule:
          interval: "weekly"
      groups:
          dev-dependencies:
              patterns:
                  - "pytest*"
                  - "ruff"
                  - "mypy"

    - package-ecosystem: "github-actions"
      directory: "/"
      schedule:
          interval: "weekly"
```

---

## Automation Strategy

### The Three Lines of Defense

1. **Pre-commit hooks** — Catch issues locally, instant feedback
2. **CI workflows** — Catch anything that slips through, authoritative
3. **Branch protection** — Enforce that CI passes before merge

### What to Run Where

| Check         | Pre-commit  | CI  | Why                      |
| ------------- | ----------- | --- | ------------------------ |
| Formatting    | ✅          | ✅  | Fast, catches everything |
| Linting       | ✅          | ✅  | Fast, catches everything |
| Type checking | ⚠️ Optional | ✅  | Can be slow locally      |
| Tests         | ❌          | ✅  | Too slow for commit hook |
| Security scan | ❌          | ✅  | Needs network, slow      |
| Coverage      | ❌          | ✅  | Needs full test run      |

### Progressive Adoption

1. **Start with CI** — Get workflows running first
2. **Add branch protection** — Enforce CI passes
3. **Add pre-commit** — Speed up feedback loop
4. **Tune thresholds** — Gradually increase strictness

---

## GitHub Apps

### What Is a GitHub App?

A **GitHub App** is a first-class integration identity on GitHub — essentially a bot account with its own name, avatar, and finely scoped permissions. Unlike a personal access token (PAT) which is tied to a human user's account, a GitHub App is an independent entity that acts on its own behalf.

When you see automated commits, PR comments, or status checks from names like `dependabot[bot]`, `github-actions[bot]`, or `renovate[bot]` — those are all GitHub Apps.

### GitHub Apps vs Personal Access Tokens (PATs)

|                           | GitHub App                              | Personal Access Token (PAT)              |
| ------------------------- | --------------------------------------- | ---------------------------------------- |
| **Identity**              | Independent bot identity                | Tied to a human user account             |
| **Token lifetime**        | Short-lived (1 hour, auto-expires)      | Long-lived (up to no expiration)         |
| **Permission scope**      | Fine-grained per-repository permissions | Broad (classic) or fine-grained          |
| **Rate limits**           | Higher (5,000+/hour per installation)   | Standard user limits (5,000/hour)        |
| **Survives user leaving** | Yes — not tied to any person            | No — token dies when the user is removed |
| **Audit trail**           | Actions attributed to `app-name[bot]`   | Actions attributed to the human user     |
| **Cost**                  | Free                                    | Free                                     |

### How GitHub Apps Work

1. **You create an App** — give it a name, select which permissions it needs (e.g., read/write pull requests, read/write contents), and generate a private key (a `.pem` file)
2. **You install the App** on specific repositories — this grants it access only where you choose
3. **At runtime**, your workflow (or script) exchanges the App's credentials (App ID + private key) for a short-lived **installation token** — this token works like a `GITHUB_TOKEN` but with App-level identity
4. The token **auto-expires** after 1 hour — no long-lived secrets sitting around

### Why This Project Uses a GitHub App

GitHub has an anti-recursion rule: workflows that use the built-in `GITHUB_TOKEN` to create or update pull requests **will not trigger `pull_request` events**. This prevents infinite workflow loops (workflow creates PR → PR triggers workflow → workflow updates PR → ...).

The side effect: when release-please (running as a GitHub Actions workflow) creates the Release PR using `GITHUB_TOKEN`, none of the CI workflows (lint, test, type-check, etc.) fire for that PR. The CI gate sits waiting for checks that never appear and eventually times out.

A GitHub App token bypasses this because GitHub sees the App as a **different actor** — not the workflow itself. The PR is created by `your-app-name[bot]`, which is a separate identity from `github-actions[bot]`, so `pull_request` events fire normally.

### What Else Can GitHub Apps Do?

GitHub Apps aren't just for working around the `GITHUB_TOKEN` limitation. They're the recommended way to build any automation that interacts with GitHub:

- **CI/CD bots** — Create PRs, merge branches, manage releases
- **Code review** — Post comments, approve/request changes, add labels
- **Issue management** — Auto-triage, auto-close stale issues, add labels
- **Deployment** — Create deployments, update environments, post status checks
- **Security** — Scan code, report vulnerabilities, enforce policies
- **Notifications** — Post to Slack/Discord when events happen in repos

Well-known GitHub Apps include Dependabot, Renovate, Codecov, Netlify, Vercel, and Stale.

### Permissions Model

GitHub Apps use a granular permission system. You pick exactly what the App can access:

| Permission        | Access levels            | Example use                              |
| ----------------- | ------------------------ | ---------------------------------------- |
| **Contents**      | None / Read / Read+Write | Push commits, create tags, manage files  |
| **Pull requests** | None / Read / Read+Write | Create/update/merge PRs, post comments   |
| **Issues**        | None / Read / Read+Write | Create/close issues, add labels          |
| **Actions**       | None / Read / Read+Write | Manage workflow runs, download artifacts |
| **Checks**        | None / Read / Read+Write | Create check runs, report CI results     |
| **Metadata**      | Read (always required)   | Basic repo information (always on)       |

You grant the minimum permissions needed. If your App only creates Release PRs, it only needs Contents + Pull requests — nothing else.

### Key Terminology

| Term                   | Meaning                                                              |
| ---------------------- | -------------------------------------------------------------------- |
| **GitHub App**         | The registration (name, permissions, webhooks)                       |
| **Installation**       | A specific repo (or org) where the App is installed                  |
| **Installation token** | The short-lived credential the App uses to call the GitHub API       |
| **Private key**        | The `.pem` file used to authenticate as the App (kept secret)        |
| **App ID**             | The numeric identifier for the App (not secret, but needed for auth) |
| **`[bot]` suffix**     | How App actions appear in Git history and PR timelines               |

### Further Reading

- [GitHub Docs: About GitHub Apps](https://docs.github.com/en/apps/overview)
- [GitHub Docs: Creating a GitHub App](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps)
- [actions/create-github-app-token](https://github.com/actions/create-github-app-token) — the Action used in this project's release workflow

---

## GitHub README Priority Order

GitHub has a hidden priority order for which README displays on the repo landing page:

1. **`.github/README.md`** — Highest priority (surprising!)
2. **`README.md`** — Root (what you'd expect)
3. **`docs/README.md`** — Lowest priority

**The gotcha:** If you put a `README.md` in `.github/` to document your workflows and templates, it **silently replaces** your root `README.md` on the repository page. Visitors see your internal `.github/` docs instead of your project README — with no warning.

This is unique to `.github/`. Every other directory's `README.md` only renders when browsing _that_ directory. But `.github/README.md` is treated as a profile-level README, similar to how `<username>/<username>/README.md` shows on your GitHub profile.

**Fix:** Don't put a `README.md` in `.github/`. Document that directory's contents elsewhere (e.g., `docs/repo-layout.md`).

See: [ADR 015](../adr/015-no-github-directory-readme.md)

---

## README Badges

Badges are small status images in your README that show project health at a glance.
They're generated dynamically by external services and rendered as inline images.

### Common Badge Types

| Badge          | What it shows             | Service            |
| -------------- | ------------------------- | ------------------ |
| CI Status      | Whether tests/checks pass | GitHub Actions     |
| Coverage       | Test coverage percentage  | Codecov, Coveralls |
| License        | Project license           | Shields.io         |
| Python Version | Supported versions        | Shields.io         |
| Code Style     | Formatter/linter used     | Shields.io         |
| Downloads      | PyPI download count       | PyPI, pepy.tech    |
| Version        | Latest release            | GitHub, PyPI       |

### How Badges Work

1. You add a Markdown image link: `[![alt](image-url)](click-url)`
2. The image URL points to a service that returns a dynamically-generated SVG
3. GitHub renders the SVG inline in your README
4. The click URL takes users to the full details

### Badge Anatomy

```markdown
[![CI](https://github.com/OWNER/REPO/actions/workflows/ci-gate.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci-gate.yml)
│ │ │
│ └── Image URL (returns SVG) └── Click URL (where badge links to)
└── Alt text (shown if image fails)
```

### GitHub Actions Badge

```markdown
[![CI](https://github.com/OWNER/REPO/actions/workflows/WORKFLOW.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/WORKFLOW.yml)
```

Shows: passing/failing based on most recent workflow run on default branch.

**Gotcha:** Won't show anything until the workflow has run at least once on main.

### Codecov Badge

```markdown
[![Coverage](https://codecov.io/gh/OWNER/REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/OWNER/REPO)
```

Shows: Coverage percentage from latest upload.

**Gotcha:** Requires Codecov account and at least one coverage upload.

### Shields.io (Static/Dynamic Badges)

Shields.io generates badges for almost anything:

```markdown
<!-- Static badge (hardcoded values) -->

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)

<!-- Dynamic badge (fetches from GitHub API) -->

[![License](https://img.shields.io/github/license/OWNER/REPO)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OWNER/REPO)](https://github.com/OWNER/REPO)
[![Issues](https://img.shields.io/github/issues/OWNER/REPO)](https://github.com/OWNER/REPO/issues)
```

### Badge Best Practices

1. **Keep it minimal** — 3-6 badges max. Too many creates visual noise.
2. **Put important ones first** — CI status, coverage, then others.
3. **Use consistent styling** — Shields.io has style options (`?style=flat-square`).
4. **Test before committing** — Paste URLs in browser to verify they work.
5. **Check on both light/dark themes** — Some badges look bad on dark mode.

### Troubleshooting

| Problem                 | Cause              | Fix                                |
| ----------------------- | ------------------ | ---------------------------------- |
| Badge shows "no status" | Workflow never ran | Push to main to trigger workflow   |
| Badge shows old data    | Caching            | Add `?cache=no` or wait ~5 min     |
| Coverage badge broken   | No Codecov setup   | Sign up at codecov.io, add token   |
| Badge looks pixelated   | Using PNG          | Use SVG URL instead                |
| Badge 404               | Wrong URL          | Check owner/repo spelling and case |

### Codecov Setup

Codecov is **free for public repos** and has a free tier for private repos.

**Sign up:**

1. Go to [codecov.io](https://codecov.io)
2. Click "Sign up" → "Sign up with GitHub"
3. Authorize Codecov to access your repos
4. Add your repo from the dashboard

**For public repos:** Works automatically after first coverage upload.

**For private repos:** Copy the `CODECOV_TOKEN` from Codecov dashboard and add it
as a repository secret in GitHub (Settings → Secrets → Actions → New secret).

---

## Things I Keep Forgetting

1. **Import name ≠ package name** — `simple-python-boilerplate` (hyphen) installs, but you `import simple_python_boilerplate` (underscore)

2. **`__init__.py` is still needed** — Even in Python 3, include it for tooling compatibility

3. **Editable install is required** — With `src/` layout, you must install to import

4. **pytest needs the package installed** — Or it won't find your modules

5. **Shebang + executable bit on Windows** — When creating a new script with a
   shebang (`#!/usr/bin/env python3`), Windows doesn't have `chmod +x`. Git
   tracks the executable permission though, so you need
   `git add --chmod=+x scripts/your_script.py` to set it. Once committed, anyone
   who clones or uses the template gets the bit automatically — it's a one-time
   thing per new script file on the authoring side only.

---

## Research: Other Template Repos

Notes and conventions gathered from popular Python boilerplate/template repositories on GitHub.

---

### Hypermodern Python (cjolowicz)

**Repo:** [cjolowicz/hypermodern-python](https://github.com/cjolowicz/hypermodern-python)

A reference for cutting-edge Python tooling. Accompanied by a detailed blog series.

| Convention       | Details                            |
| ---------------- | ---------------------------------- |
| **Build tool**   | Poetry (now Hatch is also popular) |
| **Task runner**  | Nox (multi-Python testing)         |
| **Type checker** | Mypy with strict mode              |
| **Docs**         | Sphinx + Read the Docs             |
| **Pre-commit**   | Extensive hooks                    |
| **CLI**          | Click                              |

**Key Takeaways:**

- Uses Nox for consistent test environments across Python versions
- Separates "sessions" (lint, tests, docs, safety) in `noxfile.py`
- Coverage enforced with pytest-cov
- Sphinx autodoc for API docs from docstrings
- GitHub Actions with matrix for Python 3.9–3.12

---

### Cookiecutter PyPackage (audreyfeldroy)

**Repo:** [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage)

One of the most popular Python package templates. Uses Cookiecutter for project generation.

| Convention     | Details                                   |
| -------------- | ----------------------------------------- |
| **Layout**     | `src/` layout (optional, flat by default) |
| **Testing**    | pytest + tox                              |
| **Docs**       | Sphinx                                    |
| **CI**         | Travis CI (older), GitHub Actions (forks) |
| **Versioning** | bumpversion                               |

**Key Takeaways:**

- Generates CONTRIBUTING.rst, HISTORY.rst, AUTHORS.rst
- Includes Makefile with common targets (`make test`, `make docs`)
- Supports multiple open source licenses via prompts
- tox.ini for multi-version testing
- Bump2version for version management

---

### Python Project Template (rochacbruno)

**Repo:** [rochacbruno/python-project-template](https://github.com/rochacbruno/python-project-template)

Modern template with Copier (alternative to Cookiecutter).

| Convention       | Details                              |
| ---------------- | ------------------------------------ |
| **Build tool**   | Poetry or setuptools                 |
| **Linting**      | Ruff (replaced flake8, isort, black) |
| **Type checker** | Mypy                                 |
| **Task runner**  | Make                                 |
| **Docs**         | MkDocs (Material theme)              |

**Key Takeaways:**

- Uses Copier for template updates (can pull in template changes later)
- Containerfile for OCI/Docker builds
- GitHub Actions with reusable workflows
- Conventional commits enforced
- MkDocs Material for modern-looking docs

---

### FastAPI Project Structure (tiangolo)

**Repo:** [tiangolo/full-stack-fastapi-template](https://github.com/tiangolo/full-stack-fastapi-template)

While not a general template, FastAPI projects set conventions for modern Python.

| Convention   | Details                     |
| ------------ | --------------------------- |
| **Layout**   | `app/` package (not `src/`) |
| **Async**    | Native async/await          |
| **Config**   | Pydantic Settings           |
| **Database** | SQLAlchemy + Alembic        |
| **Testing**  | pytest + httpx              |

**Key Takeaways:**

- Pydantic for settings/config management with `.env` files
- Alembic for database migrations (instead of raw SQL)
- Docker Compose for local development
- Separation: `app/core/`, `app/api/`, `app/models/`, `app/crud/`
- Pre-commit with Ruff

---

### Scikit-learn Contrib Template

**Repo:** [scikit-learn-contrib/project-template](https://github.com/scikit-learn-contrib/project-template)

Template for scikit-learn compatible packages.

| Convention  | Details                   |
| ----------- | ------------------------- |
| **Layout**  | Flat (package at root)    |
| **Testing** | pytest-cov                |
| **Docs**    | Sphinx + sphinx-gallery   |
| **CI**      | GitHub Actions + CircleCI |

**Key Takeaways:**

- Strict scikit-learn API compatibility (estimator checks)
- Example gallery generated from scripts
- Extensive docstring format (NumPy style)
- Conda + pip dual support

---

### PyScaffold

**Repo:** [pyscaffold/pyscaffold](https://github.com/pyscaffold/pyscaffold)

CLI tool that generates Python projects. Very opinionated.

| Convention     | Details                               |
| -------------- | ------------------------------------- |
| **Layout**     | `src/` layout (enforced)              |
| **Config**     | `pyproject.toml` + `setup.cfg` hybrid |
| **Versioning** | setuptools-scm (git tags)             |
| **Docs**       | Sphinx                                |
| **Extensions** | Plugin system                         |

**Key Takeaways:**

- Version derived from git tags (no manual version bumping)
- setuptools-scm for automatic versioning
- Extensions for Django, pre-commit, CI templates
- Creates `CHANGELOG.rst` (reStructuredText)
- Authors file auto-generated from git log

---

### Packaging Conventions Comparison

| Aspect          | This Template       | Hypermodern      | Cookiecutter   | PyScaffold     |
| --------------- | ------------------- | ---------------- | -------------- | -------------- |
| **Layout**      | `src/`              | `src/`           | flat (default) | `src/`         |
| **Config**      | pyproject.toml only | pyproject.toml   | setup.py/cfg   | hybrid         |
| **Linting**     | Ruff                | flake8 + plugins | flake8         | flake8         |
| **Formatting**  | Ruff                | Black            | Black          | Black          |
| **Types**       | Mypy                | Mypy strict      | optional       | optional       |
| **Task runner** | Make/scripts        | Nox              | Make + tox     | tox            |
| **Docs**        | Markdown            | Sphinx           | Sphinx         | Sphinx         |
| **Versioning**  | manual              | bump2version     | bumpversion    | setuptools-scm |

---

### Common Patterns Observed

**Project Structure:**

- `src/` layout gaining popularity (isolation benefits)
- `tests/` at root level (not inside `src/`)
- `docs/` for documentation source files
- Flat configs in root (pyproject.toml, tox.ini, etc.)

**Configuration:**

- pyproject.toml as single source (PEP 518/621)
- Tool configs in `[tool.X]` sections
- `.env` + `.env.example` for secrets

**CI/CD:**

- GitHub Actions dominant (Travis CI declining)
- Matrix testing (Python 3.10, 3.11, 3.12, etc.)
- Separate workflows per concern
- Dependabot or Renovate for dependency updates

**Documentation:**

- Sphinx still dominant for libraries
- MkDocs + Material gaining traction
- README.md as landing page
- CHANGELOG.md with Keep a Changelog format

**Testing:**

- pytest universal
- pytest-cov for coverage
- tox or nox for multi-version
- conftest.py for shared fixtures

**Developer Experience:**

- Pre-commit hooks standard
- Makefile or justfile for common tasks
- Editorconfig for cross-editor consistency
- .vscode/ or .idea/ for IDE settings

---

### Ideas Worth Considering

From researching these templates, potential additions:

| Idea               | Benefit                              | Complexity |
| ------------------ | ------------------------------------ | ---------- |
| **setuptools-scm** | No manual version bumping            | Low        |
| **Nox**            | Better than tox, Python-based        | Medium     |
| **MkDocs**         | Simpler than Sphinx, Markdown-native | Low        |
| **Copier**         | Template updates after adoption      | Medium     |
| **justfile**       | Modern Makefile alternative          | Low        |
| **CITATION.cff**   | Academic citation support            | Low        |
| **.editorconfig**  | Cross-editor consistency             | Low        |

---

### Other Template Repos (To Review)

Additional template and boilerplate repositories worth studying:

---

### PyPA Sample Project

**Repo:** [pypa/sampleproject](https://github.com/pypa/sampleproject)

The official sample project from the Python Packaging Authority (PyPA). Exists as a companion to the [PyPUG Tutorial on Packaging and Distributing Projects](https://packaging.python.org/tutorials/packaging-projects/). Intentionally minimal — focuses purely on packaging, not project development practices.

| Convention     | Details                       |
| -------------- | ----------------------------- |
| **Layout**     | `src/` layout (`src/sample/`) |
| **Config**     | `pyproject.toml` only         |
| **Testing**    | Nox                           |
| **CI**         | GitHub Actions                |
| **Docs**       | None (README only)            |
| **Versioning** | Manual in `pyproject.toml`    |

**Key Takeaways:**

- The most authoritative reference for pyproject.toml packaging metadata
- Deliberately does not cover linting, formatting, type checking, or CI beyond testing
- `src/` layout used as the recommended default
- 5.3k stars — extremely well-known as the canonical packaging example
- Good reference for pyproject.toml fields (classifiers, URLs, optional-dependencies, entry-points)
- No template engine — just a plain project to clone and adapt

---

### Kotlin Android Template (cortinico)

**Repo:** [cortinico/kotlin-android-template](https://github.com/cortinico/kotlin-android-template)

A 100% Kotlin template for Android projects with static analysis and CI baked in. Useful as a cross-language comparison for how non-Python ecosystems approach project templates.

| Convention                | Details                                                       |
| ------------------------- | ------------------------------------------------------------- |
| **Language**              | Kotlin (100%)                                                 |
| **Build tool**            | Gradle (Kotlin DSL)                                           |
| **Static analysis**       | Detekt + ktlint                                               |
| **CI**                    | GitHub Actions (pre-merge, publish-snapshot, publish-release) |
| **Dependency management** | Gradle Version Catalog (`libs.versions.toml`) + Renovate      |
| **Publishing**            | Maven Central via Nexus                                       |

**Key Takeaways:**

- Multi-module structure: `app/`, `library-android/`, `library-kotlin/`, `library-compose/`
- Shared build logic lives in `buildSrc/` as precompiled script plugins
- Renovate (not Dependabot) for automated dependency updates with auto-merge
- Static analysis runs as part of CI, not just pre-commit
- Jetpack Compose module included as a ready-to-use example
- No template engine — uses GitHub "Use this template" with manual find-and-replace
- `.idea/` directory committed for consistent IDE settings (Android Studio / IntelliJ)
- 1.9k stars; maintained by a Meta/React Native engineer

---

### Electron Boilerplate (sindresorhus)

**Repo:** [sindresorhus/electron-boilerplate](https://github.com/sindresorhus/electron-boilerplate) (**Archived** May 2024)

A minimal, opinionated Electron starter from sindresorhus. Now archived but still a good reference for how a "less is more" boilerplate can work.

| Convention         | Details                                |
| ------------------ | -------------------------------------- |
| **Language**       | JavaScript (84%), CSS, HTML            |
| **Build tool**     | electron-builder                       |
| **CI**             | GitHub Actions (cross-platform builds) |
| **Config**         | electron-store                         |
| **Error handling** | electron-unhandled                     |
| **Editor**         | `.editorconfig`                        |

**Key Takeaways:**

- Extremely minimal — only the files you actually need (no over-engineering)
- electron-builder configured for cross-platform builds (macOS, Linux, Windows)
- Silent auto-updates built in
- System-native app menu out of the box
- Context menu via `electron-context-menu`
- README acts as a template itself — "remove everything above here" pattern
- Example of a successful boilerplate that is a working app, not a meta-template
- 1.6k stars; archived because the author moved on from Electron

---

### Josee9988's Project Template

**Repo:** [Josee9988/project-template](https://github.com/Josee9988/project-template)

A language-agnostic GitHub template focused on community health files, issue templates, labels, and repository automation. Not about code structure — about the GitHub repo wrapper around a project.

| Convention          | Details                                                                                |
| ------------------- | -------------------------------------------------------------------------------------- |
| **Language**        | Language-agnostic (Shell for setup script)                                             |
| **Setup**           | `SETUP_TEMPLATE.sh` script auto-detects and replaces placeholders                      |
| **Issue templates** | 8 templates (bug, failing test, docs, feature, enhancement, security, question, blank) |
| **Labels**          | 20+ labels auto-created via `settings.yml` bot                                         |
| **Community files** | CODE_OF_CONDUCT, CONTRIBUTING, SECURITY, SUPPORT, CODEOWNERS                           |
| **Bots**            | issue-label-bot, probot-settings, welcome-bot, todo-bot                                |

**Key Takeaways:**

- Strongest emphasis on community health files of any template reviewed
- Shell script for initial personalisation (replaces placeholders in all files)
- Uses GitHub Probot ecosystem heavily for automation
- CHANGELOG follows Keep a Changelog format
- Pull request template auto-closes linked issues via keywords
- No CI workflows for code — purely a "repo wrapper" template
- 934 stars; last updated 4 years ago (not actively maintained)

---

### inovintell Python Template

**Repo:** [inovintell/py-template](https://github.com/inovintell/py-template)

A Python template that uses **Cookiecutter** for project generation. Focused on CI/CD automation with semantic release and comprehensive GitHub Actions pipelines.

| Convention             | Details                                                     |
| ---------------------- | ----------------------------------------------------------- |
| **Layout**             | `src/{{cookiecutter.repository}}/` (Cookiecutter-templated) |
| **Build tool**         | Poetry                                                      |
| **Linting**            | Ruff                                                        |
| **Pre-commit**         | Yes (with commitlint for conventional commits)              |
| **CI**                 | GitHub Actions (extensive pipeline)                         |
| **Docs**               | MkDocs                                                      |
| **Dependency updates** | Renovate                                                    |
| **Versioning**         | Semantic release (automated)                                |

**Key Takeaways:**

- Uses Cookiecutter — source files have `{{cookiecutter.repository}}` placeholders throughout
- This means the template repo itself is not directly runnable or testable
- Heavy Renovate usage — bot commits dominate the commit history
- Conventional commits enforced via commitlint
- `.editorconfig` and `.yamllint.yml` included for cross-editor and YAML consistency
- Poetry for dependency management (not pip/setuptools)
- Example of the trade-off ADR-014 discusses: powerful automation but harder to read/contribute to
- 92 stars; actively maintained (Renovate keeps dependencies current)

---

### Awesome Repo Template (MarketingPipeline)

**Repo:** [MarketingPipeline/Awesome-Repo-Template](https://github.com/MarketingPipeline/Awesome-Repo-Template)

A feature-rich, language-agnostic GitHub template with heavy automation via GitHub Actions workflows that run at template setup time.

| Convention          | Details                                                                  |
| ------------------- | ------------------------------------------------------------------------ |
| **Language**        | Language-agnostic (HTML landing page)                                    |
| **Setup**           | GitHub Actions workflow auto-replaces links, emails, and metadata        |
| **Community files** | CODE_OF_CONDUCT, CONTRIBUTING, SECURITY, CODEOWNERS, CHANGE_LOG, TO_DO   |
| **Issue templates** | Bug report and feature request (YAML-based forms)                        |
| **Automation**      | Image compression, TOC generation, stargazer metrics SVG, SEO index.html |
| **Bots**            | issue-label-bot, probot-settings, welcome-bot                            |

**Key Takeaways:**

- Unique approach: uses a GitHub Actions workflow to auto-configure the repo after creation
- Generates a markdown-styled `index.html` with SEO metadata
- Auto-generates a table of contents in the README
- Stargazer metrics SVG generated automatically
- Image optimisation workflow compresses all repo images
- More "GitHub infrastructure" than "code template" — no language-specific tooling
- Similar to Josee9988's template but with more workflow-based automation
- 201 stars; last updated 4 years ago

---

## Source Code File Workflow

A clean separation of concerns for the `src/` package structure.

### The Pattern

```text
main.py   → starts the program (entry points, thin wrappers)
cli.py    → defines CLI contract (argument parsing, commands)
engine.py → defines behavior (core logic, interface-agnostic)
api.py    → defines callable interface (HTTP/REST, optional)
```

### File Responsibilities

| File        | Purpose       | Contains                               |
| ----------- | ------------- | -------------------------------------- |
| `main.py`   | Entry points  | Thin wrappers that call cli/engine     |
| `cli.py`    | CLI contract  | Argument parser, command definitions   |
| `engine.py` | Behavior      | Pure logic, no I/O, easily testable    |
| `api.py`    | API interface | HTTP routes, request/response handling |

### Data Flow

```text
User runs command
       ↓
main.py (entry point)
       ↓
cli.py (parse args, dispatch)
       ↓
engine.py (do the work)
       ↓
Return result to cli.py
       ↓
Format output (cli.py or main.py)
       ↓
User sees result
```

### Why This Pattern?

1. **Testability** — `engine.py` has no CLI/HTTP dependencies, easy to unit test
2. **Flexibility** — Same engine can power CLI, API, GUI, etc.
3. **Clarity** — Each file has one job
4. **Maintainability** — Changes to CLI don't affect core logic

### Example

```python
# engine.py — pure logic
def process_data(data: str) -> str:
    return f"Processed: {data}"

# cli.py — CLI contract
def run(args):
    from engine import process_data
    result = process_data(args.input)
    print(result)
    return 0

# main.py — entry point
def main():
    from cli import parse_args, run
    sys.exit(run(parse_args()))
```

### Anti-patterns to Avoid

- ❌ Business logic in `main.py`
- ❌ Argument parsing in `engine.py`
- ❌ HTTP-specific code in `engine.py`
- ❌ `print()` statements in `engine.py` (return data instead)

---

| File            | Primary role                 | What it contains                                                            | What it must **not** contain                                     | Who calls it                       | When to use it                                     | Common mistakes                                          |
| --------------- | ---------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------- | -------------------------------------------------- | -------------------------------------------------------- |
| **`engine.py`** | Source of truth (core logic) | Pure functions/classes that implement real behavior                         | CLI parsing, printing, shell commands, repo-specific assumptions | `api.py`, tests, other Python code | Always when behavior is non-trivial or reusable    | Mixing I/O or argument parsing into core logic           |
| **`api.py`**    | Stable internal interface    | Thin wrappers that expose intentional operations (e.g. `run_lint`, `build`) | Implementation details, argument parsing                         | `cli.py`, `main.py`, other tools   | When you want a clean boundary and refactor safety | Making it a duplicate of `engine.py` with no added value |
| **`cli.py`**    | Command-line interface       | Argument parsing, subcommands, help text                                    | Business logic, complex workflows                                | End users, developers, Just, CI    | When providing an installable CLI                  | Putting real logic directly in CLI handlers              |
| **`main.py`**   | Entry point / bootstrap      | Calls into `api.py` or `engine.py` to start execution                       | Logic, configuration rules                                       | Python runtime (`python main.py`)  | Optional; useful for quick execution or demos      | Letting it grow into the main implementation file        |

### Key Rule

> Logic flows downward; control flows upward.

- Logic lives in `engine.py`
- Interfaces adapt it (`api.py`, `cli.py`)
- Entrypoints trigger it (`main.py`)

### Decision Rules (read top → bottom)

- If someone outside this repo needs to run it → installable CLI
- If only contributors need it → task runner (Just)
- If it expresses real behavior → core logic
- If it just wires things together → orchestration

### Canonical Decision Table

| Question                                                       | Yes → Do this                                    | No → Do this |
| -------------------------------------------------------------- | ------------------------------------------------ | ------------ |
| Does this define real behavior (rules, algorithms, decisions)? | Put it in **core logic** (`engine.py` / `core/`) | Continue     |
| Should this behavior be callable by other code or tools?       | Expose via **installable CLI** (and/or API)      | Continue     |
| Is this meant to be run outside this repo?                     | **Installable CLI command**                      | Continue     |
| Is this only for contributors working on this repo?            | **Just task**                                    | Continue     |
| Is this repo-specific glue (order of steps, flags, paths)?     | **Just task or script**                          | Continue     |
| Is this a one-off or disposable automation?                    | **Script**                                       | Re-evaluate  |

### What Each Bucket Is Responsible For

| Tool / Layer       | Purpose                 | Source of truth? | Versioned? | Audience     |
| ------------------ | ----------------------- | ---------------- | ---------- | ------------ |
| Core logic         | Implements behavior     | ✅ Yes           | With code  | Everyone     |
| Installable CLI    | Defines public commands | ✅ Yes           | Yes        | Users / devs |
| Just (task runner) | Orchestrates commands   | ❌ No            | With repo  | Contributors |
| Scripts            | One-off helpers         | ❌ No            | Optional   | Maintainers  |
| CI workflows       | Automation              | ❌ No            | With repo  | CI only      |

### Concrete Examples (grounding the rules)

| Action                       | Correct place                   | Why                           |
| ---------------------------- | ------------------------------- | ----------------------------- |
| Lint Python files            | Installable CLI (`mytool lint`) | Reusable, meaningful behavior |
| Run lint + format + tests    | Just (`just check`)             | Repo workflow                 |
| Build and publish release    | CLI (`mytool release`)          | Stable, versioned behavior    |
| Clean `.pytest_cache`        | Just or script                  | Repo-specific cleanup         |
| Bootstrap venv               | Just                            | Developer convenience         |
| Parse config file            | Core logic                      | Behavior, not orchestration   |
| Call multiple tools in order | Just                            | Pure glue                     |

### Anti-patterns (what not to do)

| Smell                                | Why it's wrong                |
| ------------------------------------ | ----------------------------- |
| Logic lives in `justfile`            | Not testable or reusable      |
| CI runs `just something`             | CI now depends on dev tooling |
| CLI calls shell pipelines            | Logic trapped in strings      |
| Scripts are the only interface       | No stable API                 |
| Just command documented as "the way" | Just became the API           |

### One-sentence Rule (worth memorizing)

> Installable CLIs define behavior.
> Just coordinates behavior.
> Scripts are temporary.

### Why This Matters for Your Template

You are not just writing code—you are teaching architecture.

**If you teach:**

- "put logic in core"
- "keep runners dumb"

**Then users:**

- Can refactor safely
- Can add new interfaces later
- Avoid brittle repos

---

## Programming Conventions & Expected Patterns

When people read a Python project, they expect certain conventions. These
aren't arbitrary — they signal professionalism, ease maintenance, and
enable tooling to work correctly. This section covers the patterns that
experienced developers look for (and notice when they're missing).

### The `if __name__ == "__main__":` Guard

Every Python file that can be run directly should have this:

```python
def main() -> None:
    """Entry point for the script."""
    print("Hello, world!")

if __name__ == "__main__":
    main()
```

**Why it matters:**

- Without it, importing the module executes its top-level code as a side effect
- Tests can't safely import the module without triggering execution
- Tooling (mypy, IDEs, linters) may behave unexpectedly
- It's the first thing reviewers check in any executable file

**The pattern:** Put all logic in functions, then call the entry function
inside the guard. Never put bare logic at module level.

### Shebangs

Scripts intended to be run directly (not just imported) should start with:

```python
#!/usr/bin/env python3
```

**Why `env python3` instead of `/usr/bin/python3`?** Because `env` searches
`$PATH`, so it finds the correct Python even in virtual environments or
non-standard installs. Hardcoding the path breaks on systems where Python
is installed elsewhere.

**In this project:** After adding a shebang, mark the file executable in git:

```bash
git add --chmod=+x scripts/my_script.py
```

The pre-commit hook `check-shebang-scripts-are-executable` will fail
otherwise.

### Type Hints

Python doesn't enforce types at runtime, but type hints serve three
purposes: documentation, tooling, and catching bugs before they happen.

```python
# Without type hints — what does this accept? Return?
def process(data, threshold):
    ...

# With type hints — immediately clear
def process(data: list[dict[str, float]], threshold: float) -> bool:
    ...
```

**What's expected in this project:**

| Context                     | Expectation                                    |
| --------------------------- | ---------------------------------------------- |
| Public functions in `src/`  | Full type annotations required                 |
| Private functions (`_name`) | Type annotations recommended                   |
| Test functions              | Not required (fixtures, mocks make it noisy)   |
| Script functions            | Recommended but relaxed                        |
| Return types                | Always annotate — `-> None` for void functions |
| `TypedDict`, `dataclass`    | Prefer over raw dicts for structured data      |

**Common pitfalls:**

- `dict` instead of `dict[str, Any]` — too vague, tells the reader nothing
- Missing `-> None` — makes mypy assume `-> Any`
- `Optional[str]` vs `str | None` — use `str | None` (Python 3.10+ style)
- Forgetting `from __future__ import annotations` if targeting Python < 3.10

### Docstrings (Google Style)

This project uses **Google-style docstrings** because mkdocstrings parses
them to generate API documentation.

```python
def calculate_score(values: list[float], weight: float = 1.0) -> float:
    """Calculate weighted score from a list of values.

    Takes a list of numeric values and applies a uniform weight factor.
    Returns 0.0 for empty inputs rather than raising an error.

    Args:
        values: List of numeric values to score.
        weight: Multiplier applied to the final sum. Defaults to 1.0.

    Returns:
        The weighted sum of all values, or 0.0 if the list is empty.

    Raises:
        ValueError: If weight is negative.

    Example:
        >>> calculate_score([1.0, 2.0, 3.0], weight=0.5)
        3.0
    """
```

**What's expected:**

| Context                 | Expectation                                       |
| ----------------------- | ------------------------------------------------- |
| Public functions        | Required (one-line or full docstring)             |
| Classes                 | Required (describe purpose, not implementation)   |
| Modules (`__init__.py`) | Recommended (describe what the package does)      |
| Private functions       | Optional (add when the "why" isn't obvious)       |
| Test functions          | Optional (test name should be descriptive enough) |

**The "why not what" rule:** Don't restate the code. Instead, explain
intent, edge cases, and non-obvious behavior. `# increment counter` before
`counter += 1` teaches nothing. `# Reset to 0 after 255 to match the
protocol's unsigned-byte wraparound` is valuable.

### Import Conventions

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import requests
from rich.console import Console

# Local (absolute imports — required by this project)
from simple_python_boilerplate.engine import process_data
from simple_python_boilerplate.cli import parse_args
```

**Rules for this project:**

1. **Absolute imports only** — `from simple_python_boilerplate.module import func`, never `from .module import func`
2. **Ruff handles sorting** — Don't manually reorder; `ruff check --fix` does it for you
3. **No wildcard imports** — Never `from module import *`
4. **Lazy imports for heavy dependencies** — If a module takes 500ms to import (ML libs, etc.), import inside the function that uses it

### Constants

```python
# Module-level constants — UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT_SECONDS = 30
API_BASE_URL = "https://api.example.com/v1"

# Not constants — these are variables
retry_count = 0
current_timeout = DEFAULT_TIMEOUT_SECONDS
```

Constants go at the top of the file, after imports. They signal "this value
never changes at runtime." If you see `MAX_RETRIES = 3` being reassigned
later in the code, it's not actually a constant — rename it.

### Error Handling

```python
# Bad — catches everything, hides bugs
try:
    result = process(data)
except Exception:
    pass

# Better — specific exception, meaningful handling
try:
    result = process(data)
except ValueError as e:
    logger.warning("Invalid data format: %s", e)
    return default_result
except ConnectionError:
    logger.error("Service unavailable, retrying in %ds", backoff)
    raise
```

**Expected patterns:**

- **Catch specific exceptions** — never bare `except:` or `except Exception:`
- **Don't silence errors** — `pass` in an except block is almost always wrong
- **Re-raise when appropriate** — Use `raise` without arguments to preserve traceback
- **Use custom exceptions for API boundaries** — If your module has a public API, define domain-specific exceptions instead of leaking `KeyError` from internal dicts

### Logging vs Print

```python
# Scripts — print() is fine for user-facing output
print(f"Processed {count} files")

# Libraries/packages — use logging
import logging
logger = logging.getLogger(__name__)
logger.info("Processed %d files", count)
```

**When to use which:**

| Context                     | Use                       | Why                         |
| --------------------------- | ------------------------- | --------------------------- |
| CLI output (user sees it)   | `print()`                 | Direct, expected            |
| Diagnostic info (debugging) | `logging.debug()`         | Configurable, filterable    |
| Operational info (health)   | `logging.info()`          | Captured by log systems     |
| Warnings (degraded state)   | `logging.warning()`       | Visible but non-fatal       |
| Errors (failure path)       | `logging.error()`         | Captured, alerted on        |
| **Never** use `print()` in  | Library code, `engine.py` | Pollutes stdout, untestable |

### Exit Codes

Scripts should return meaningful exit codes:

```python
import sys

def main() -> int:
    """Return 0 on success, non-zero on failure."""
    try:
        result = run_checks()
        if result.has_errors:
            return 1
        return 0
    except KeyboardInterrupt:
        return 130  # Standard for SIGINT

if __name__ == "__main__":
    sys.exit(main())
```

| Exit code | Meaning                       |
| --------- | ----------------------------- |
| `0`       | Success                       |
| `1`       | General error                 |
| `2`       | Misuse of command (bad args)  |
| `130`     | Interrupted (Ctrl+C / SIGINT) |

**Why it matters:** CI pipelines, shell scripts, and pre-commit hooks all
check exit codes. A script that prints "Error!" but exits 0 silently
passes every quality gate.

### File-Level Structure

The expected order within a Python file:

```python
#!/usr/bin/env python3                  # 1. Shebang (scripts only)
"""Module docstring."""                 # 2. Module docstring

from __future__ import annotations     # 3. Future imports

import os                              # 4. Standard library imports
import sys

import requests                        # 5. Third-party imports

from mypackage.engine import process   # 6. Local imports

logger = logging.getLogger(__name__)   # 7. Module-level setup

MAX_RETRIES = 3                        # 8. Constants

class MyClass:                         # 9. Classes
    ...

def my_function():                     # 10. Functions
    ...

if __name__ == "__main__":             # 11. Main guard (last)
    main()
```

This order isn't a personal preference — it's what isort, Ruff, and most
style guides enforce. Deviating from it causes linter warnings and
confuses readers.

### The `__all__` Variable

Controls what `from module import *` exports and tells tooling what a
module's public API is:

```python
__all__ = ["process_data", "DataResult", "InvalidInputError"]
```

**When to use it:** When a module has a mix of public and internal names
and you want to be explicit about the API boundary. Not required for every
file, but good practice for `__init__.py` files that re-export from
submodules.

### Testing Conventions

| Pattern                         | Expected? | Example                                           |
| ------------------------------- | --------- | ------------------------------------------------- |
| Test files mirror source layout | Yes       | `src/pkg/engine.py` → `tests/unit/test_engine.py` |
| Test names describe behavior    | Yes       | `test_process_returns_empty_for_no_input`         |
| One assert per test (ideally)   | Preferred | Easier to debug failures                          |
| Fixtures for shared setup       | Yes       | `conftest.py` at test root                        |
| Mocks for external services     | Yes       | Don't hit real APIs in unit tests                 |
| Integration tests separate      | Yes       | `tests/integration/` directory                    |

See [ADR 029](../adr/029-testing-strategy.md) for the project's full
testing philosophy.

### Script Conventions

Scripts in `scripts/` follow additional rules:

| Convention                         | Example                              | Why                              |
| ---------------------------------- | ------------------------------------ | -------------------------------- |
| Shebang on line 1                  | `#!/usr/bin/env python3`             | Direct execution on Unix         |
| Module docstring                   | `"""Bootstrap a fresh clone."""`     | `--help` or file browsing        |
| `if __name__ == "__main__":` guard | Always                               | Importable for testing           |
| Meaningful exit codes              | `sys.exit(0)` or `sys.exit(1)`       | CI and shell scripts check these |
| `argparse` for CLI args            | `parser = argparse.ArgumentParser()` | Consistent, self-documenting     |
| Type hints on public functions     | `def bootstrap(path: Path) -> int:`  | mypy checks scripts too          |
| No global state                    | Pass deps as function args           | Testable, predictable            |

See [ADR 031](../adr/031-script-conventions.md) and
[scripts/README.md](../../scripts/README.md) for the full inventory and
conventions.

---

## Common Python Cache & Artifact Directories

| Path             | Created by         | Purpose                                            | Safe to delete? | Commit to git? |
| ---------------- | ------------------ | -------------------------------------------------- | --------------- | -------------- |
| `__pycache__/`   | Python interpreter | Stores compiled `.pyc` bytecode for faster imports | ✅ Yes          | ❌ Never       |
| `.pytest_cache/` | pytest             | Remembers test state (last failed, node IDs)       | ✅ Yes          | ❌ Never       |
| `.mypy_cache/`   | mypy               | Type-checking cache                                | ✅ Yes          | ❌ Never       |
| `.ruff_cache/`   | ruff               | Linting cache                                      | ✅ Yes          | ❌ Never       |
| `.coverage`      | coverage.py        | Coverage data file                                 | ✅ Yes          | ❌ Never       |
| `htmlcov/`       | coverage.py        | HTML coverage report                               | ✅ Yes          | ❌ Never       |
| `.tox/`          | tox                | Virtualenvs + test environments                    | ✅ Yes          | ❌ Never       |
| `.nox/`          | nox                | Virtualenvs + sessions                             | ✅ Yes          | ❌ Never       |
| `.venv/`         | venv / uv / poetry | Local virtual environment                          | ✅ Yes          | ❌ Never       |
| `dist/`          | build tools        | Built distributions (wheel/sdist)                  | ✅ Yes          | ❌ Never       |
| `build/`         | build tools        | Temporary build artifacts                          | ✅ Yes          | ❌ Never       |

### Why Python Creates So Many Caches

Python tooling is modular:

- Each tool optimizes independently
- Each tool owns its own cache
- No central "build system" cleans everything automatically

This is normal and healthy.

### Do Other Programming Languages Have the Same Thing?

Yes — absolutely. Every serious ecosystem does.

**Comparison across ecosystems:**

| Language   | Examples of cache / artifact dirs                          |
| ---------- | ---------------------------------------------------------- |
| Python     | `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.venv/` |
| JavaScript | `node_modules/`, `.next/`, `.turbo/`, `.parcel-cache/`     |
| Rust       | `target/`                                                  |
| Java       | `target/`, `.gradle/`                                      |
| Go         | `pkg/`, `bin/`, module cache                               |
| C/C++      | `build/`, `*.o`, `*.a`, `*.out`                            |
| .NET       | `bin/`, `obj/`                                             |

The names differ; the idea is identical.

### Why These Should Never Be Committed

Cache directories are:

- Machine-specific
- Non-deterministic
- Frequently invalidated
- Huge source of merge conflicts

A repo that commits caches is a broken repo.

### Where Cleanup Belongs (Architecture Tie-In)

Cleaning caches:

- Is not real behavior
- Is not business logic
- Is repo hygiene

**Correct places:**

- `just clean`
- `scripts/clean.py`
- CI steps

**Incorrect places:**

- Core logic
- Installable CLI
- Application code

### Example `.gitignore` Entries

```gitignore
# Python
__pycache__/
*.py[cod]

# Virtual environments
.venv/
env/

# Test / lint / type-check caches
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Build artifacts
build/
dist/
*.egg-info/
```

### One Rule to Remember

> If deleting it breaks nothing permanently, it's not source code.

---

## What is `*.egg-info`?

`*.egg-info/` is Python packaging metadata generated by setuptools (often via pip) when a project is installed, especially in editable (`pip install -e .`) mode.

It is not source code. It is installation metadata.

### What Lives Inside `*.egg-info/`

Typical contents:

```text
my_package.egg-info/
├── PKG-INFO        # Name, version, license, metadata
├── SOURCES.txt     # Files included in the package
├── requires.txt    # Dependencies
├── entry_points.txt# Console scripts / CLI entry points
├── top_level.txt   # Top-level import names
└── dependency_links.txt
```

This data answers questions like:

- "What version is installed?"
- "What console scripts should exist?"
- "What are the dependencies?"

### Why It Appears in Your Repo

Common causes:

- You ran `pip install -e .`
- A tool installed your package locally
- A test or dev workflow installed the project

Editable installs must write metadata somewhere, and `*.egg-info` is how setuptools does it.

### Should `*.egg-info` Be Committed?

**No. Never.**

Reasons:

- Machine-specific paths
- Installation-state dependent
- Regenerated at will
- Causes merge noise and confusion

Add to `.gitignore`:

```gitignore
*.egg-info/
```

### Related Packaging Artifacts (same category)

These are not caches, but build/install artifacts.

| Artifact              | Created by  | Purpose                     | Commit? |
| --------------------- | ----------- | --------------------------- | :-----: |
| `*.egg-info/`         | setuptools  | Installed package metadata  |   ❌    |
| `*.dist-info/`        | pip         | Wheel installation metadata |   ❌    |
| `dist/`               | build tools | Built wheels / sdists       |   ❌    |
| `build/`              | build tools | Temporary build output      |   ❌    |
| `pip-wheel-metadata/` | pip         | Intermediate wheel metadata |   ❌    |

**Rule:** If it only exists after install or build, it does not belong in git.

### `egg-info` vs `dist-info` (important distinction)

**`*.egg-info`**

- Legacy / setuptools-era format
- Common in editable installs

**`*.dist-info`**

- Modern standard (PEP 376)
- Created when installing wheels

Both serve the same role: describe what’s installed, not what you wrote.

### Beyond Python: Other Non-Cache Artifacts You May See

These exist in many ecosystems and are not caches, but tooling state.

| Ecosystem  | Examples                              |
| ---------- | ------------------------------------- |
| Python     | `*.egg-info/`, `*.dist-info/`         |
| JavaScript | `package-lock.json`, `pnpm-lock.yaml` |
| Rust       | `Cargo.lock`                          |
| Java       | `pom.xml`, `.classpath`               |
| .NET       | `.csproj`, `.deps.json`               |

**Key difference:**

- Lockfiles → usually committed
- Install/build metadata → never committed

### Mental Model (use this)

> Caches speed things up.
> Metadata describes installed artifacts.
> Neither is source code.

If deleting it only requires reinstalling or rebuilding → it does not belong in git.

### Where This Fits in Your Architecture Rules

`*.egg-info` is not:

- Logic
- CLI
- Just
- Scripts

It is a tool byproduct, managed by the packaging system.

### Bottom-Line Rules

- Source code → commit
- Configuration → commit
- Lockfiles → usually commit
- Caches → never commit
- Build artifacts → never commit
- Install metadata (`*.egg-info`, `*.dist-info`) → never commit

### Quick Reference: When to Use What

| Scenario              | Installable CLI | Just | Script |
| --------------------- | --------------- | ---- | ------ |
| Reusable logic        | ✅              | ❌   | ❌     |
| Distributed tool      | ✅              | ❌   | ❌     |
| Repo glue             | ❌              | ✅   | ⚠️     |
| One-off automation    | ❌              | ⚠️   | ✅     |
| User-facing command   | ✅              | ❌   | ❌     |
| Developer convenience | ⚠️              | ✅   | ⚠️     |

---

## What is `pyproject.toml`?

`pyproject.toml` is a single configuration file (written in [TOML](https://toml.io/)) that defines everything about a Python project: metadata, dependencies, build instructions, and tool settings.

Before `pyproject.toml`, Python projects needed multiple config files (`setup.py`, `setup.cfg`, `tox.ini`, `.flake8`, `mypy.ini`, etc.). Now most of that lives in one place.

### The Standards Behind It

| PEP                                          | What It Defines                                                  | Year |
| -------------------------------------------- | ---------------------------------------------------------------- | ---- |
| [PEP 518](https://peps.python.org/pep-0518/) | `[build-system]` table — how to build the project                | 2016 |
| [PEP 621](https://peps.python.org/pep-0621/) | `[project]` table — project metadata (name, version, deps, etc.) | 2020 |
| [PEP 517](https://peps.python.org/pep-0517/) | Build backend interface (how pip talks to build tools)           | 2017 |
| [PEP 660](https://peps.python.org/pep-0660/) | Editable installs via build backends                             | 2021 |

These PEPs made `pyproject.toml` the **standard** way to configure Python projects. Any PEP 621-compliant tool (pip, Hatch, setuptools, Flit, PDM, Dependabot, etc.) can read the `[project]` table.

### Structure Overview

A `pyproject.toml` has three major sections:

```text
┌─────────────────────────────────────────────────┐
│  [build-system]            ← PEP 518            │
│  How to build this project                      │
├─────────────────────────────────────────────────┤
│  [project]                 ← PEP 621            │
│  What this project IS (metadata, deps, etc.)    │
│  ├─ [project.scripts]                           │
│  ├─ [project.urls]                              │
│  └─ [project.optional-dependencies]             │
├─────────────────────────────────────────────────┤
│  [tool.*]                  ← Tool-specific      │
│  Configuration for individual tools             │
│  ├─ [tool.hatch.*]                              │
│  ├─ [tool.pytest.*]                             │
│  ├─ [tool.ruff.*]                               │
│  ├─ [tool.mypy]                                 │
│  └─ [tool.coverage.*]                           │
└─────────────────────────────────────────────────┘
```

### Section 1: `[build-system]` (PEP 518)

Tells pip and other installers **how** to build your project.

```toml
[build-system]
requires = ["hatchling"]           # What to download to build
build-backend = "hatchling.build"  # The Python object that does the build
```

| Field           | Purpose                                     | Example Values                                                    |
| --------------- | ------------------------------------------- | ----------------------------------------------------------------- |
| `requires`      | Build-time dependencies (downloaded by pip) | `["hatchling"]`, `["setuptools>=68"]`, `["flit_core>=3.9"]`       |
| `build-backend` | Python callable that builds sdist/wheel     | `"hatchling.build"`, `"setuptools.build_meta"`, `"flit_core.api"` |

**Key insight:** You don't need Hatch installed to `pip install .` your project. pip downloads `hatchling` automatically based on `requires`. Hatch (the CLI) is a separate, optional developer tool.

### Section 2: `[project]` (PEP 621)

Describes **what** your project is. This is standardized metadata — every tool reads the same fields.

```toml
[project]
name = "my-project"                  # Package name (PyPI / pip install)
version = "0.1.0"                    # Current version
description = "One-line summary"     # Short description
readme = "README.md"                 # Long description file
requires-python = ">=3.11"           # Minimum Python version
license = {text = "Apache-2.0"}      # SPDX license identifier
authors = [{name = "You"}]           # Author(s)
```

#### Subfields of `[project]`

| Field             | Type             | Purpose                                                                                |
| ----------------- | ---------------- | -------------------------------------------------------------------------------------- |
| `name`            | string           | Package name on PyPI, used with `pip install <name>`                                   |
| `version`         | string           | SemVer version (or `dynamic = ["version"]` for auto)                                   |
| `description`     | string           | One-line summary shown on PyPI                                                         |
| `readme`          | string/table     | Path to long description (usually README.md)                                           |
| `requires-python` | string           | Minimum Python version specifier                                                       |
| `license`         | table            | SPDX license identifier or file path                                                   |
| `authors`         | array of tables  | Name and/or email of author(s)                                                         |
| `keywords`        | array of strings | PyPI search keywords                                                                   |
| `classifiers`     | array of strings | [PyPI classifiers](https://pypi.org/classifiers/) (maturity, license, Python versions) |
| `dependencies`    | array of strings | **Runtime** dependencies (installed by `pip install .`)                                |

#### `[project.scripts]` — CLI Entry Points

Maps command names to Python functions. pip creates executables for these automatically.

```toml
[project.scripts]
my-tool = "my_package.main:main"     # Runs main() from my_package/main.py
my-tool-doctor = "my_package.main:doctor"
```

After `pip install .`, typing `my-tool` in a terminal calls `my_package.main:main()`.

#### `[project.urls]` — Project Links

Shown on the PyPI sidebar.

```toml
[project.urls]
Homepage = "https://github.com/user/project"
Repository = "https://github.com/user/project"
Documentation = "https://project.readthedocs.io"
Changelog = "https://github.com/user/project/blob/main/CHANGELOG.md"
"Bug Tracker" = "https://github.com/user/project/issues"
```

#### `[project.optional-dependencies]` — Extra Dependency Groups

Dependencies that are only installed when explicitly requested. This is PEP 621, so **any tool** (pip, Hatch, Dependabot, tox, nox) understands it.

```toml
[project.optional-dependencies]
test = ["pytest", "pytest-cov"]
dev = ["my-project[test]", "ruff", "mypy"]   # Can reference other groups!
docs = ["mkdocs>=1.6", "mkdocs-material>=9.4"]
```

Install with: `pip install -e ".[dev]"` or `pip install -e ".[test,docs]"`.

**Why this matters for Hatch:** Hatch environments reference these groups via `features = ["dev"]` instead of duplicating the dependency list. One source of truth, two consumers.

**Why this matters for Dependabot:** Dependabot reads `[project.optional-dependencies]` and auto-creates PRs to update version specifiers (e.g., `"ruff"` → `"ruff>=0.9.1"`).

### Section 3: `[tool.*]` — Tool-Specific Config

Each tool gets its own namespace under `[tool]`. This is not standardized — each tool defines its own schema.

```toml
[tool.hatch.envs.default]           # Hatch environment config
[tool.pytest.ini_options]           # pytest settings
[tool.ruff]                         # Ruff linter/formatter
[tool.mypy]                         # mypy type checker
[tool.coverage.run]                 # coverage.py
[tool.bandit]                       # Bandit security linter
```

**Key point:** `[tool.*]` sections are ignored by tools that don't own them. Ruff doesn't care about `[tool.mypy]`, and mypy doesn't care about `[tool.ruff]`. They coexist peacefully.

#### Hatch-Specific Tool Config

Hatch uses `[tool.hatch.*]` for environments, scripts, build config, and versioning:

```toml
# Environments — isolated virtualenvs with specific dependency groups
[tool.hatch.envs.default]
features = ["dev"]                     # Install [project.optional-dependencies].dev

[tool.hatch.envs.default.scripts]
test = "pytest {args}"                 # `hatch run test`
lint = "ruff check {args: src/}"       # `hatch run lint`

# Test matrix — test across Python versions
[tool.hatch.envs.test]
features = ["test"]

[[tool.hatch.envs.test.matrix]]        # Note: double brackets = array of tables
python = ["3.11", "3.12", "3.13"]

# Build config
[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]
```

### TOML Syntax Quick Reference

TOML has a few syntax patterns that can trip you up:

| Syntax                 | Meaning                         | Example                           |
| ---------------------- | ------------------------------- | --------------------------------- |
| `[section]`            | Table (like a dict)             | `[project]`                       |
| `[section.subsection]` | Nested table                    | `[tool.ruff.lint]`                |
| `[[section]]`          | Array of tables (list of dicts) | `[[tool.hatch.envs.test.matrix]]` |
| `key = "value"`        | String                          | `name = "my-project"`             |
| `key = ["a", "b"]`     | Array                           | `dependencies = ["click"]`        |
| `key = {a = "b"}`      | Inline table                    | `license = {text = "MIT"}`        |
| `key = [{a = "b"}]`    | Array of inline tables          | `authors = [{name = "You"}]`      |

### How Tools Discover `pyproject.toml`

Most tools (pytest, ruff, mypy, etc.) walk up the directory tree from the current working directory until they find a `pyproject.toml` with their `[tool.X]` section. No need to pass `--config` flags.

### Putting It All Together

```toml
# ── How to build ──
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# ── What this project is ──
[project]
name = "my-project"
version = "0.1.0"
dependencies = ["requests"]

[project.optional-dependencies]
dev = ["ruff", "pytest"]

[project.scripts]
my-cli = "my_project.main:main"

# ── How tools behave ──
[tool.hatch.envs.default]
features = ["dev"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 88
```

One file. Everything in one place. Every tool knows where to look.

### Dependabot and `pyproject.toml`

Dependabot understands PEP 621 fully. It scans:

- `[project].dependencies` — runtime deps
- `[project.optional-dependencies].*` — all extras (dev, test, docs, etc.)

It creates PRs to update version specifiers when new releases are published.

**What Dependabot does NOT do:**

- It does **not** update version numbers inside TOML comments (e.g., `# v0.6.9` in a comment)
- It does **not** update versions in non-standard locations (Taskfile.yml, scripts, README examples)
- It only touches the actual dependency specifier strings

If you have comments documenting current versions (like `"ruff",  # v0.9.1`), those comments will become stale as Dependabot bumps the specifier. You need a separate script or manual process to keep comments current.

---

## Unix, Terminals, and Shells

Before diving into specific shells (bash, zsh, etc.), it helps to understand
the foundational concepts: what Unix is, what a terminal is, and how shells
fit into the picture. These three thingAuto-approve + auto-merge minor/patch Dependabot PRs once CI passes.s are often confused or used
interchangeably, but they're distinct layers.

### What is Unix?

**Unix** is a family of operating systems that originated at AT&T Bell Labs
in 1969 (Ken Thompson, Dennis Ritchie). It introduced ideas that underpin
nearly every modern OS:

- **Everything is a file** — devices, sockets, pipes, and actual files are
  all accessed through the same interface (`open`, `read`, `write`, `close`)
- **Small, composable tools** — programs that do one thing well and combine
  via pipes (`grep`, `sort`, `awk`, `sed`, `cut`, `wc`)
- **Plain text as a universal interface** — configuration, data, and
  inter-process communication default to human-readable text
- **Multi-user, multi-tasking** — designed from day one for multiple users
  running multiple programs simultaneously
- **Hierarchical file system** — a single root `/` with directories branching
  below it (no drive letters)
- **Permissions model** — owner/group/others with read/write/execute bits

#### The Unix Family Tree

```text
Unix (AT&T Bell Labs, 1969)
 ├── BSD (Berkeley, 1977)
 │    ├── FreeBSD
 │    ├── OpenBSD
 │    ├── NetBSD
 │    └── macOS / Darwin (Apple, 2001) ← macOS is certified Unix
 ├── System V (AT&T, 1983)
 │    ├── Solaris (Sun/Oracle)
 │    ├── HP-UX
 │    └── AIX (IBM)
 └── Linux (Linus Torvalds, 1991) ← "Unix-like", not certified Unix
      ├── Debian → Ubuntu, Mint
      ├── Red Hat → Fedora, CentOS, RHEL
      ├── Arch → Manjaro
      ├── Alpine (used in Docker)
      └── Android (Linux kernel)
```

> **Key distinction:** Linux is _Unix-like_ (implements the same concepts and
> mostly follows POSIX standards) but is not descended from AT&T Unix code.
> macOS _is_ certified Unix (POSIX-compliant, descended from BSD).

#### POSIX — The Compatibility Standard

**POSIX** (Portable Operating System Interface) is a family of standards
published by IEEE (specifically IEEE 1003) and formalised by ISO/IEC. The
name was suggested by Richard Stallman in the late 1980s.

**The problem POSIX solves:** In the 1980s, Unix had fragmented into many
commercial variants — AT&T System V, BSD, Sun's SunOS, HP-UX, IBM's AIX.
Each had slightly different system calls, utility flags, shell syntax, and
file layouts. Code written for one often broke on another. POSIX was created
to define a _common baseline_ so that software written to the standard would
work on any conforming system.

In plain terms: POSIX is a written specification that says "if you call
yourself a Unix-like operating system, you must support _at least_ these
system calls, these shell features, these command-line utilities, and these
behaviors." It's a contract between OS vendors and software developers.

##### What POSIX Actually Defines

| Area                      | What the standard specifies                                       | Examples                                                                               |
| ------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------- |
| **Shell language**        | Syntax, builtins, control flow, variable expansion, quoting rules | `sh` grammar, `if`/`for`/`while`/`case`, `$VAR`, `$(cmd)`                              |
| **Core utilities**        | Required commands and their flags/behavior                        | `ls`, `cp`, `mv`, `rm`, `grep`, `sed`, `awk`, `find`, `sort`, `test`, `chmod`, `mkdir` |
| **C library API**         | System call wrappers and standard functions                       | `open()`, `read()`, `write()`, `close()`, `fork()`, `exec()`, `pipe()`, `malloc()`     |
| **File system**           | Path resolution, permissions, symlinks, directory structure       | `/`, `/dev`, `/tmp`, permission bits (rwx), `.` and `..`                               |
| **Environment variables** | Required variables and how they work                              | `PATH`, `HOME`, `USER`, `SHELL`, `TERM`, `LANG`                                        |
| **Process model**         | How processes are created and managed                             | PIDs, parent/child, signals (`SIGINT`, `SIGTERM`, `SIGKILL`), exit codes, job control  |
| **Regular expressions**   | Two flavors: Basic (BRE) and Extended (ERE)                       | BRE for `grep`, ERE for `grep -E` / `egrep`                                            |
| **I/O model**             | File descriptors, stdin/stdout/stderr, pipes, redirection         | fd 0/1/2, `                                                                            | `, `>`, `<`, `2>&1` |
| **Threading**             | POSIX threads (pthreads) API                                      | `pthread_create()`, `pthread_join()`, mutexes, condition variables                     |

##### Who Is and Isn't POSIX-Compliant

| System                | POSIX status                    | Notes                                                                                                |
| --------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **macOS**             | Certified POSIX-compliant       | Apple pays for the certification. macOS is _officially_ Unix.                                        |
| **Solaris / illumos** | Certified                       | Commercial Unix from Sun/Oracle                                                                      |
| **Linux**             | Mostly compliant, not certified | Follows POSIX closely but distros don't pay for certification. In practice, nearly everything works. |
| **FreeBSD / OpenBSD** | Mostly compliant, not certified | BSD heritage, very close to the standard                                                             |
| **Windows**           | Not POSIX-compliant             | Has compatibility layers: WSL (full Linux kernel), Cygwin, MSYS2/Git Bash                            |
| **Alpine Linux**      | POSIX via musl libc             | Uses `musl` instead of `glibc`, which is stricter — scripts relying on glibc quirks may break        |

##### POSIX in Practice — What It Means for You

**When writing shell scripts:**

```bash
#!/bin/sh
# POSIX-compliant — works everywhere
if [ -f "config.toml" ]; then
    echo "Config found"
fi

# NOT POSIX — uses bash-specific [[ ]] syntax
# if [[ -f "config.toml" ]]; then
```

**Common POSIX vs bash differences that bite people:**

| Feature              | POSIX `sh`           | `bash`                              |
| -------------------- | -------------------- | ----------------------------------- |
| Test syntax          | `[ -f file ]`        | `[[ -f file ]]` (extended, safer)   |
| Arrays               | Not available        | `arr=(a b c)`, `${arr[@]}`          |
| String replace       | Not available        | `${var//old/new}`                   |
| Process substitution | Not available        | `<(command)`, `>(command)`          |
| Brace expansion      | Not available        | `{1..10}`, `{a,b,c}`                |
| `source` command     | `. file` (dot-space) | `source file` (or `. file`)         |
| `function` keyword   | `myfunc() { ... }`   | `function myfunc() { ... }` (also)  |
| `echo` flags         | Behavior varies      | `-e`, `-n` (but still inconsistent) |
| `local` variables    | Not standardised     | `local var=value`                   |

**The practical rule:** Use `#!/bin/sh` and POSIX-only syntax for:

- Git hooks (contributors may use any OS)
- Docker `RUN` commands (Alpine only has `sh`)
- CI scripts that might run on minimal images
- Makefiles (Make defaults to `/bin/sh`)

Use `#!/bin/bash` when you need arrays, `[[ ]]`, string manipulation, or
other bash features — and you know bash is available (most Linux distros,
macOS pre-Catalina, CI runners with `bash` specified).

##### Why "POSIX-Compliant" Keeps Coming Up

You'll hear "POSIX" in several contexts:

| Context                         | What they mean                                                       |
| ------------------------------- | -------------------------------------------------------------------- |
| "Write POSIX-compliant scripts" | Use `#!/bin/sh` syntax only — no bashisms                            |
| "POSIX filesystem semantics"    | Forward slashes, case-sensitivity, permission bits                   |
| "POSIX signals"                 | `SIGINT` (Ctrl+C), `SIGTERM` (graceful stop), `SIGKILL` (force stop) |
| "POSIX threads" (pthreads)      | The standard threading API for C/C++                                 |
| "POSIX regular expressions"     | BRE and ERE — the regex flavors `grep` and `sed` use                 |
| "POSIX line endings"            | `LF` (`\n`), as opposed to Windows `CRLF` (`\r\n`)                   |

**Why it matters for this project:** CI runners, Docker containers, and
contributor machines may run different Unix-like systems. Writing
POSIX-compliant scripts (`#!/bin/sh`) maximises portability. Bash-specific
scripts (`#!/bin/bash`) are fine when you know bash is available.

#### Why Unix Matters for Python Development

Even if you develop on Windows, Unix concepts show up everywhere:

| Where                | Unix concept                                                                                  |
| -------------------- | --------------------------------------------------------------------------------------------- |
| **Git**              | Built on Unix tools — `diff`, `patch`, file permissions, symlinks, line endings (LF vs CRLF)  |
| **CI/CD**            | GitHub Actions runners are Ubuntu Linux by default                                            |
| **Docker**           | Container images are Linux (Alpine, Debian, Ubuntu)                                           |
| **pip / venv**       | Virtual environments use Unix-style directory layouts (`bin/`, not `Scripts/` on Linux/macOS) |
| **Shebangs**         | `#!/usr/bin/env python3` — a Unix convention for executable scripts                           |
| **File paths**       | Forward slashes `/`, case-sensitive names, no drive letters                                   |
| **Package managers** | `apt`, `brew`, `pacman` — all Unix-native tools                                               |
| **SSH**              | Key-based auth to GitHub, servers — a Unix tool (`openssh`)                                   |
| **Permissions**      | `chmod +x script.sh` — Unix file permission model                                             |
| **Signals**          | `Ctrl+C` sends `SIGINT`, `kill -9` sends `SIGKILL` — Unix process signals                     |

#### Unix vs Windows — Key Differences

| Concept           | Unix / Linux / macOS                     | Windows                                 |
| ----------------- | ---------------------------------------- | --------------------------------------- |
| Path separator    | `/` (forward slash)                      | `\` (backslash)                         |
| Root              | `/`                                      | `C:\` (drive letters)                   |
| Case sensitivity  | Case-sensitive (`File.txt` ≠ `file.txt`) | Case-insensitive (usually)              |
| Line endings      | `LF` (`\n`)                              | `CRLF` (`\r\n`)                         |
| Executable marker | File permission bit (`chmod +x`)         | File extension (`.exe`, `.bat`, `.ps1`) |
| Shell             | `sh`, `bash`, `zsh`                      | `cmd.exe`, PowerShell                   |
| Package manager   | `apt`, `brew`, `pacman`                  | `winget`, `choco`, `scoop`              |
| Hidden files      | Prefix with `.` (`.gitignore`)           | File attribute flag                     |
| Process model     | `fork()` + `exec()`                      | `CreateProcess()`                       |
| Filesystem        | ext4, APFS, ZFS                          | NTFS                                    |
| User model        | Root (`uid 0`) + normal users            | Administrator + normal users            |

### What is a Terminal?

A **terminal** (or **terminal emulator**) is a program that provides a
text-based window where you type commands and see output. That's it — it's
the _window_, not the thing interpreting your commands.

#### Historical Context

```text
1960s–70s: Physical terminals (hardware devices with a screen and keyboard)
           └── VT100, VT220, Teletype (TTY)
                └── Connected to a mainframe/minicomputer via serial cable

1980s–now: Terminal emulators (software that mimics a physical terminal)
           └── xterm, GNOME Terminal, iTerm2, Windows Terminal, VS Code terminal
                └── Connected to a shell process via a pseudo-terminal (PTY)
```

The word "TTY" (teletypewriter) persists in Unix — `tty` is a command,
`/dev/tty` is a device file, and terminal-related APIs use the term throughout.

#### Terminal vs Shell vs Command Line

These three terms are often used interchangeably, but they're different layers:

```text
┌─────────────────────────────────────────────────────┐
│  Terminal Emulator (the window)                      │
│  ┌───────────────────────────────────────────────┐  │
│  │  Shell (the interpreter)                       │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │  Commands / Programs (what you run)      │  │  │
│  │  │  e.g., git, python, ls, ruff, pytest     │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

| Layer        | What it is                                            | Examples                                                              | Analogy                     |
| ------------ | ----------------------------------------------------- | --------------------------------------------------------------------- | --------------------------- |
| **Terminal** | The window / display surface                          | Windows Terminal, iTerm2, VS Code integrated terminal, GNOME Terminal | A TV screen                 |
| **Shell**    | The command interpreter that runs inside the terminal | bash, zsh, PowerShell, fish, sh                                       | The channel you're watching |
| **Command**  | The program the shell runs                            | `git commit`, `python main.py`, `ls -la`                              | The show on the channel     |

**Key insight:** You can run _any_ shell inside _any_ terminal. The terminal
doesn't care — it just sends keystrokes to the shell and displays characters
back. You can open Windows Terminal and run bash (via WSL), or open iTerm2 on
macOS and run PowerShell.

#### Common Terminal Emulators

| Terminal                        | Platform       | Key Features                                             |
| ------------------------------- | -------------- | -------------------------------------------------------- |
| **Windows Terminal**            | Windows        | Tabs, GPU-accelerated, profiles for cmd/PowerShell/WSL   |
| **VS Code Integrated Terminal** | Cross-platform | Built into editor, multiple shells, split panes          |
| **iTerm2**                      | macOS          | Split panes, hotkey window, search, profiles             |
| **GNOME Terminal**              | Linux (GNOME)  | Default on Ubuntu/Fedora GNOME, tabs, profiles           |
| **Alacritty**                   | Cross-platform | GPU-accelerated, minimal, config-file driven (TOML)      |
| **WezTerm**                     | Cross-platform | GPU-accelerated, Lua config, multiplexer built in        |
| **kitty**                       | Linux / macOS  | GPU-accelerated, image display, extensible               |
| **Konsole**                     | Linux (KDE)    | KDE default, tabs, profiles, bookmarks                   |
| **cmd.exe**                     | Windows        | Legacy Windows shell host — not really a modern terminal |

#### The VS Code Integrated Terminal

The VS Code terminal is a full terminal emulator embedded in the editor. It
runs a real shell process (bash, zsh, PowerShell, cmd) — it's not a
simplified or sandboxed version.

| Feature             | Details                                                                  |
| ------------------- | ------------------------------------------------------------------------ |
| Default shell       | Inherits system default (PowerShell on Windows, bash/zsh on Linux/macOS) |
| Switch shells       | `Terminal: Select Default Profile` command or dropdown in terminal panel |
| Multiple terminals  | Create new ones with `+`, name them, colour-code them                    |
| Split terminals     | Run side-by-side in the same panel                                       |
| Linked to workspace | Working directory defaults to the workspace root                         |
| Environment         | Inherits VS Code's environment variables + activated venv                |
| Tasks               | Can run registered tasks (`Terminal > Run Task`)                         |

**Practical tip:** When VS Code activates a Python virtual environment, it
modifies the terminal's `PATH` so `python` and `pip` resolve to the venv's
copies. This is why you see the `(.venv)` prefix in the prompt — that's the
shell indicating the venv is active, not the terminal doing it.

### VS Code Settings Hierarchy

VS Code has multiple layers of settings. Each layer overrides the one above
it — more specific scopes win over more general ones.

#### Precedence Order (lowest → highest)

| Priority | Scope         | Where it lives                                    | Who it affects                    |
| -------- | ------------- | ------------------------------------------------- | --------------------------------- |
| 1 (low)  | **Default**   | Built into VS Code                                | Everyone (not editable)           |
| 2        | **User**      | `~/.config/Code/User/settings.json` (or equiv)    | All workspaces for this user      |
| 3        | **Remote**    | Server-side settings (SSH, WSL, containers)       | Remote sessions only              |
| 4        | **Workspace** | `.code-workspace` file or `.vscode/settings.json` | Everyone who opens this workspace |
| 5 (high) | **Folder**    | `.vscode/settings.json` in a multi-root folder    | Only that specific folder         |

**Key takeaway:** Workspace settings override User settings. If a setting
is defined in both your personal User settings and the project's
`.code-workspace` file, the workspace version wins. This is intentional —
projects should enforce their own conventions regardless of individual
developer preferences.

#### Where Settings Are Stored

| Scope         | File / Location                                                       |
| ------------- | --------------------------------------------------------------------- |
| **User**      | Windows: `%APPDATA%\Code\User\settings.json`                          |
|               | macOS: `~/Library/Application Support/Code/User/settings.json`        |
|               | Linux: `~/.config/Code/User/settings.json`                            |
| **Workspace** | Single-folder: `.vscode/settings.json` in the project root            |
|               | Multi-root: Inside the `*.code-workspace` file under `"settings": {}` |
| **Folder**    | `.vscode/settings.json` in each folder (multi-root workspaces only)   |

#### .code-workspace vs .vscode/settings.json

Both are "workspace settings" but they serve different purposes:

| Feature             | `.code-workspace` file                        | `.vscode/settings.json`            |
| ------------------- | --------------------------------------------- | ---------------------------------- |
| Format              | JSON with `folders`, `settings`, `extensions` | Pure settings JSON only            |
| Multi-root support  | Yes — can define multiple folder roots        | No — single folder only            |
| Extension recs      | Yes — `extensions.recommendations` array      | No (use `.vscode/extensions.json`) |
| Task/launch configs | Yes — can contain tasks/launch configs        | No (use `.vscode/tasks.json` etc.) |
| Open via CLI        | `code project.code-workspace`                 | `code /path/to/folder`             |
| Commit to git?      | Yes — team-shared settings                    | Yes — team-shared settings         |

This project uses a `.code-workspace` file (`simple-python-boilerplate.code-workspace`)
because it bundles settings + extension recommendations in one file.

#### Common Settings in This Project

The workspace file configures:

| Setting                              | Value              | Purpose                                     |
| ------------------------------------ | ------------------ | ------------------------------------------- |
| `python.defaultInterpreterPath`      | `.venv/.../python` | Points to the project's virtual environment |
| `editor.defaultFormatter` (Python)   | Ruff               | Format Python with Ruff, not autopep8/black |
| `editor.formatOnSave` (Python)       | `true`             | Auto-format every time you save             |
| `editor.defaultFormatter` (Markdown) | Prettier           | Format Markdown with Prettier               |
| `editor.formatOnSave` (Markdown)     | `false`            | Don't auto-format Markdown (run manually)   |
| `editor.rulers`                      | `[88, 120]`        | Vertical guide lines at columns 88 and 120  |
| `files.trimTrailingWhitespace`       | `true`             | Remove trailing spaces on save              |
| `files.insertFinalNewline`           | `true`             | Ensure files end with a newline             |
| `files.exclude`                      | (various)          | Hide `__pycache__`, `.mypy_cache`, etc.     |

> **Those vertical lines in the editor** are the rulers at columns 88 and 120. Column 88 matches Ruff's default line length limit for Python.
> Column 120 is a common secondary limit for docs/comments. They're visual
> guides only — they don't enforce anything.

#### Language-Specific Settings

VS Code allows settings scoped to a file type using `[language]` keys:

```jsonc
// Only applies to Python files
"[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
}

// Only applies to Markdown files
"[markdown]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": false
}
```

These always override the global version of that setting for matched files.
So even if you have `"editor.formatOnSave": false` globally, the
`[python]` scope above sets it to `true` for Python files.

#### Troubleshooting Settings

If a setting isn't behaving as expected:

1. **Command Palette → "Preferences: Open Settings (JSON)"** — see the
   merged result of all scopes
2. **Settings UI → search → click the gear icon** — shows where each
   setting is defined and which scope it comes from
3. **Command Palette → "Developer: Inspect Editor Tokens and Scopes"** —
   shows language scope for the current cursor position

#### Python Interpreter Discovery

The `python.defaultInterpreterPath` setting is a **hint**, not a
requirement. VS Code's Python extension automatically discovers
interpreters from:

- `.venv/` in the workspace
- Hatch environments (`hatch env find`)
- Conda environments
- pyenv versions
- System Python

If the configured path doesn't exist (e.g., `.venv/bin/python` on
Windows where it should be `.venv/Scripts/python.exe`), VS Code shows an
"Unable to handle" error. Fix it by:

1. Opening Command Palette → **"Python: Select Interpreter"**
2. Picking the correct interpreter from the list
3. VS Code saves this choice per-workspace

> **Common cause of this error:** The `.code-workspace` file ships with
> a Linux/macOS path (`.venv/bin/python`) as the default. On Windows the
> path would be `.venv/Scripts/python.exe`. But if you use **Hatch** to
> manage environments (as this project does), there is no `.venv/` at all
> — Hatch stores environments externally (run `hatch env find default` to
> see where). The fix is always the same: pick the correct interpreter via
> the Command Palette. VS Code remembers the choice per-workspace, so you
> only need to do this once.

#### Settings Sync and Profiles

**Settings Sync** (`Settings → Turn on Settings Sync`) synchronizes your
User settings, keybindings, extensions, UI state, and snippets across
machines via your GitHub or Microsoft account.

What syncs:

| What               | Synced? | Notes                                                 |
| ------------------ | ------- | ----------------------------------------------------- |
| User settings      | Yes     | `settings.json`                                       |
| Keybindings        | Yes     | `keybindings.json`                                    |
| Extensions         | Yes     | Installed extensions list                             |
| UI state           | Yes     | Open editors, sidebar, panel state                    |
| Snippets           | Yes     | User-defined code snippets                            |
| Workspace settings | **No**  | `.code-workspace` / `.vscode/settings.json` are local |
| Tasks / Launch     | **No**  | `.vscode/tasks.json`, `launch.json` are local         |

**Profiles** (File → Preferences → Profiles) let you group settings,
extensions, and keybindings into named configurations. Useful for
switching between "Python development" and "Markdown writing" setups
without conflicting extensions or settings.

#### Useful Commands for Debugging Settings

| Command Palette (`Ctrl+Shift+P`)              | What it does                               |
| --------------------------------------------- | ------------------------------------------ |
| `Preferences: Open User Settings (JSON)`      | Opens your global `settings.json`          |
| `Preferences: Open Workspace Settings (JSON)` | Opens workspace `settings.json`            |
| `Preferences: Open Default Settings (JSON)`   | Shows all defaults (read-only, searchable) |
| `Python: Select Interpreter`                  | Pick which Python executable VS Code uses  |
| `Developer: Inspect Editor Tokens and Scopes` | Shows language scope at cursor position    |
| `Developer: Toggle Developer Tools`           | Opens Chrome DevTools for VS Code itself   |
| `Preferences: Open Keyboard Shortcuts (JSON)` | Edit keybindings directly                  |

#### Extensions: Workspace Recommendations

The `extensions.recommendations` array in `.code-workspace` or
`.vscode/extensions.json` lets you recommend extensions for the project.
When someone opens the workspace, VS Code prompts them to install
missing recommendations.

```jsonc
// In .code-workspace or .vscode/extensions.json
"extensions": {
    "recommendations": [
        "ms-python.python",         // Python language support
        "charliermarsh.ruff",       // Ruff linter/formatter
        "DavidAnson.vscode-markdownlint"  // Markdown linting
    ]
}
```

**Unwanted recommendations:** If an extension is not relevant to your
workflow, use `extensions.unwantedRecommendations` to suppress prompts.

### What is a Shell? (Conceptual Overview)

A **shell** is a program that:

1. Displays a prompt
2. Reads a line of input (a command)
3. Parses the command
4. Executes the command (by forking a child process or running a builtin)
5. Displays the output
6. Goes back to step 1

That loop is called a **REPL** (Read-Eval-Print Loop) — the same concept as
Python's interactive interpreter (`>>>` prompt).

#### What the Shell Actually Does

Beyond running commands, the shell handles:

| Responsibility         | What it does                                                 | Example                                |
| ---------------------- | ------------------------------------------------------------ | -------------------------------------- |
| **Variable expansion** | Replaces `$VAR` with its value                               | `echo $HOME` → `/home/user`            |
| **Glob expansion**     | Expands wildcards into matching filenames                    | `ls *.py` → `ls main.py utils.py`      |
| **Pipes**              | Connects stdout of one command to stdin of the next          | `cat log.txt \| grep ERROR \| wc -l`   |
| **Redirection**        | Sends output to a file or reads input from a file            | `echo "hello" > out.txt`               |
| **Job control**        | Runs processes in background, foreground, suspend            | `sleep 100 &`, `fg`, `Ctrl+Z`          |
| **Environment**        | Maintains environment variables passed to child processes    | `export PATH="$PATH:/usr/local/bin"`   |
| **Scripting**          | Conditionals, loops, functions — it's a programming language | `if [ -f .env ]; then source .env; fi` |
| **History**            | Remembers previous commands (arrow keys, `Ctrl+R` search)    | `history`, `!!` (rerun last command)   |
| **Tab completion**     | Completes filenames, commands, arguments                     | Type `git com` + Tab → `git commit`    |
| **Signal handling**    | Catches `Ctrl+C` (SIGINT), `Ctrl+D` (EOF), etc.              | `trap 'cleanup' EXIT`                  |

#### Interactive vs Non-Interactive Shells

| Mode                      | When                                | Config loaded                                   | Use case             |
| ------------------------- | ----------------------------------- | ----------------------------------------------- | -------------------- |
| **Interactive login**     | SSH, first terminal after boot      | `.bash_profile` (or `.zprofile`) then `.bashrc` | User's main session  |
| **Interactive non-login** | Open a new terminal tab             | `.bashrc` (or `.zshrc`)                         | Daily use            |
| **Non-interactive**       | Running a script (`bash script.sh`) | Usually none (or `BASH_ENV` if set)             | Automation, CI, cron |

**Why this matters:** If you set an alias in `.bashrc` but your CI script runs
non-interactively, that alias won't exist. Environment setup for scripts
should go in the script itself or be passed explicitly.

#### How the Shell Runs a Command

When you type `python main.py` and press Enter, here's what happens:

```text
1. Shell reads the line: "python main.py"
2. Shell parses it: command="python", args=["main.py"]
3. Shell searches $PATH for "python" executable
   → Finds /usr/bin/python (or .venv/bin/python if venv active)
4. Shell calls fork() → creates a child process
5. Child process calls exec("python", ["main.py"])
   → Child process is replaced by the Python interpreter
6. Python runs main.py
7. Python exits with exit code (0 = success, non-zero = error)
8. Shell receives the exit code → stores in $?
9. Shell prints the next prompt
```

This `fork + exec` model is fundamental to Unix. Every command you run
(except shell builtins like `cd`, `echo`, `export`) goes through this cycle.

**Builtins are special:** Commands like `cd`, `export`, `source`, and `alias`
must run _inside_ the shell process (not in a child) because they modify the
shell's own state. `cd` changes the shell's working directory — if it ran as
a child process, only the child would change directories, and the parent shell
would be unaffected.

---

## Raw SQL vs ORMs in Python

When people say "raw SQL" they mean writing SQL statements directly as
strings in your code, as opposed to using an abstraction layer that generates
SQL for you. Both approaches talk to the same database — the difference is
_who writes the SQL_: you, or a library.

### What "Raw SQL" Actually Means

**Raw SQL** = you write the SQL yourself as a literal string, send it to the
database, and handle the results.

```python
import sqlite3

# This is raw SQL — you wrote the SELECT statement yourself
conn = sqlite3.connect("app.sqlite3")
cursor = conn.execute(
    "SELECT id, name, email FROM users WHERE active = ? ORDER BY name",
    (True,)
)
for row in cursor:
    print(row[0], row[1], row[2])  # access by index — no named attributes
conn.close()
```

**ORM (Object-Relational Mapper)** = a library translates Python
objects/method calls into SQL behind the scenes.

```python
from sqlalchemy.orm import Session
from models import User

# This is ORM — SQLAlchemy generates the SQL for you
with Session() as session:
    users = (
        session.query(User)
        .filter(User.active == True)
        .order_by(User.name)
        .all()
    )
    for user in users:
        print(user.id, user.name, user.email)  # named attributes on objects
```

Both produce the same `SELECT id, name, email FROM users WHERE active = 1
ORDER BY name` query. The ORM just writes it for you.

### The Spectrum: It's Not Binary

It's not just "raw SQL" vs "full ORM" — there's a spectrum:

| Level                              | Approach                                          | Library Examples                         | You Write SQL?                        |
| ---------------------------------- | ------------------------------------------------- | ---------------------------------------- | ------------------------------------- |
| **1. Raw SQL**                     | Strings + database driver                         | `sqlite3`, `psycopg2`, `mysql-connector` | Yes — full SQL                        |
| **2. SQL builder / query builder** | Python objects that compose SQL pieces            | `pypika`, `sqlbuilder`                   | Partially — Python API, SQL output    |
| **3. Core SQL toolkit**            | Expression language that maps closely to SQL      | SQLAlchemy Core, `databases`             | Sort of — SQL-like Python expressions |
| **4. Lightweight ORM**             | Thin models, minimal magic                        | Peewee, PonyORM, SQLModel                | No — but you see the SQL shape        |
| **5. Full ORM**                    | Models, relationships, identity map, unit of work | SQLAlchemy ORM, Django ORM, Tortoise     | No — heavily abstracted               |

Many experienced developers land at levels 2–3: they want composable queries
without the overhead and complexity of a full ORM.

### Why Many Python Projects Use ORMs Instead of Raw SQL

You're right that SQL is powerful and useful — it absolutely is. SQL has been
around since the 1970s, is standardised (like POSIX for databases), and is
the most widely used language for data. The reason many Python projects reach
for ORMs isn't that SQL is bad — it's about managing complexity at scale:

**1. Boilerplate and repetition**

CRUD operations (Create, Read, Update, Delete) are repetitive in raw SQL.
For every table you need INSERT, SELECT, UPDATE, DELETE statements, parameterized
correctly, with result-set parsing. ORMs generate all of this from a model
definition.

```python
# Raw SQL: 4 separate statements to write and maintain per table
INSERT_USER = "INSERT INTO users (name, email) VALUES (?, ?)"
SELECT_USER = "SELECT id, name, email FROM users WHERE id = ?"
UPDATE_USER = "UPDATE users SET name = ?, email = ? WHERE id = ?"
DELETE_USER = "DELETE FROM users WHERE id = ?"

# ORM: one model definition handles all CRUD
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
```

**2. SQL injection risk**

Raw SQL makes it easy to accidentally interpolate user input into queries
(especially for beginners). ORMs parameterize automatically.

```python
# DANGEROUS — SQL injection vulnerability
cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")
# If user_input = "'; DROP TABLE users; --"  ...goodbye data

# SAFE — parameterized query (raw SQL done properly)
cursor.execute("SELECT * FROM users WHERE name = ?", (user_input,))

# SAFE — ORM handles parameterization
session.query(User).filter(User.name == user_input).all()
```

**3. Schema ↔ code synchronization**

With raw SQL, your database schema and your Python code are two separate
things that can drift apart. If you add a column to the database, nothing in
your Python code knows about it until you manually update your queries. ORMs
keep the schema definition _in_ the Python code, often with migration tools
that auto-detect changes.

**4. Relationships and lazy loading**

Navigating relationships between tables ("get this user's orders, then each
order's items") requires joins or multiple queries in raw SQL. ORMs let you
traverse relationships like Python attributes:

```python
# Raw SQL: manual join
cursor.execute("""
    SELECT u.name, o.total, i.product_name
    FROM users u
    JOIN orders o ON o.user_id = u.id
    JOIN order_items i ON i.order_id = o.id
    WHERE u.id = ?
""", (user_id,))

# ORM: traverse like Python objects
user = session.get(User, user_id)
for order in user.orders:           # lazy-loads orders
    for item in order.items:        # lazy-loads items
        print(item.product_name)
```

**5. Database portability**

Raw SQL is often dialect-specific. PostgreSQL, MySQL, and SQLite have
different syntax for things like auto-increment, string functions, date
handling, and `UPSERT`. ORMs abstract these differences — switch your
connection string and (mostly) the same code works on a different database.

**6. Web framework integration**

The biggest Python web frameworks ship with ORMs built in or strongly
recommended:

- **Django** → Django ORM (built in, tightly integrated)
- **Flask** → SQLAlchemy (via Flask-SQLAlchemy)
- **FastAPI** → SQLAlchemy or SQLModel

Since most Python web tutorials start with these frameworks, new developers
learn ORMs first and may never write raw SQL in Python.

### When Raw SQL Is the Better Choice

Despite the above, there are solid reasons to use raw SQL:

| Scenario                       | Why raw SQL wins                                                                                                   |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| **Complex queries**            | Multi-table joins, window functions, CTEs, recursive queries — ORMs struggle with these or produce inefficient SQL |
| **Performance-critical paths** | You know exactly what query runs, no ORM overhead or N+1 surprises                                                 |
| **Reporting / analytics**      | Aggregations, GROUP BY, HAVING — often cleaner in SQL                                                              |
| **Database-specific features** | Full-text search, JSON operators, PostGIS, SQLite FTS5 — ORMs may not expose these                                 |
| **Simple scripts**             | A 50-line script doesn't need an ORM setup                                                                         |
| **Learning**                   | Understanding SQL directly makes you a better developer, even if you later use an ORM                              |
| **Existing schema**            | Working with a database you didn't design — raw SQL adapts easier than mapping an ORM                              |
| **Data migrations**            | Schema changes, backfills, one-off fixes — raw SQL is the right tool                                               |

### The ORM Drawbacks People Don't Mention Upfront

| Problem                             | What happens                                                                                         |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **N+1 queries**                     | ORM lazy-loads related objects one at a time — 100 users with orders = 101 queries instead of 1 join |
| **Opaque SQL**                      | Hard to see what SQL the ORM generates; performance debugging requires logging SQL output            |
| **Migration complexity**            | ORM migration tools (Alembic, Django migrations) can generate incorrect or inefficient migrations    |
| **Learning the ORM ≠ learning SQL** | ORMs have their own API, quirks, and mental model — you're learning _the ORM_, not _databases_       |
| **Abstraction leaks**               | Eventually you hit something the ORM can't do and drop to raw SQL anyway                             |
| **Heavyweight**                     | SQLAlchemy is ~45k lines of code. For a script that runs 3 queries, that's a lot of machinery        |

### What This Project Does

This template uses the `db/` directory with raw SQL files:

- `db/schema.sql` — full schema definition
- `db/migrations/` — incremental changes as numbered `.sql` files
- `db/seeds/` — test/dev data
- `db/queries/` — reusable query snippets

This is the **raw SQL** approach. The template doesn't include an ORM because:

1. It's a _template_ — template users choose their own data layer
2. Not every Python project needs a database at all
3. Raw `.sql` files are database-agnostic in structure (even if the SQL
   dialect varies)
4. It keeps the template dependency-free for database concerns

If you add a database to a project based on this template, you'd choose:

- **Raw SQL** (`sqlite3` / `psycopg2`) for simple cases or when you want full control
- **SQLAlchemy Core** for composable queries without full ORM overhead
- **SQLAlchemy ORM** / **Django ORM** for web apps with lots of CRUD
- **SQLModel** for FastAPI projects (combines SQLAlchemy + Pydantic)

### Python Database Libraries at a Glance

| Library                           | Type                   | Database                  | When to use                                    |
| --------------------------------- | ---------------------- | ------------------------- | ---------------------------------------------- |
| **sqlite3**                       | Raw SQL (stdlib)       | SQLite                    | Scripts, prototypes, single-user apps, testing |
| **psycopg2** / **psycopg3**       | Raw SQL driver         | PostgreSQL                | Direct Postgres access, performance-critical   |
| **mysql-connector** / **PyMySQL** | Raw SQL driver         | MySQL/MariaDB             | Direct MySQL access                            |
| **SQLAlchemy Core**               | SQL toolkit            | Any (via dialects)        | Composable queries, multi-DB support           |
| **SQLAlchemy ORM**                | Full ORM               | Any (via dialects)        | Web apps, complex domain models                |
| **Django ORM**                    | Full ORM (Django only) | PostgreSQL, MySQL, SQLite | Django projects                                |
| **Peewee**                        | Lightweight ORM        | SQLite, PostgreSQL, MySQL | Small projects, scripts                        |
| **SQLModel**                      | ORM + validation       | Any (SQLAlchemy backend)  | FastAPI projects                               |
| **Tortoise ORM**                  | Async ORM              | PostgreSQL, MySQL, SQLite | Async web apps                                 |
| **databases**                     | Async raw SQL          | PostgreSQL, MySQL, SQLite | Async apps with raw queries                    |

### The Pragmatic Take

SQL itself is one of the most valuable skills you can learn as a developer.
It's been around for 50 years and isn't going anywhere. The question isn't
"raw SQL vs ORM" — it's _where in the spectrum do you want to operate for
this particular project_.

Many experienced developers:

1. **Learn SQL properly first** — understand SELECT, JOIN, GROUP BY, window
   functions, indexing, query plans
2. **Use an ORM/toolkit for application code** — reduces boilerplate, handles
   the boring CRUD
3. **Drop to raw SQL when needed** — complex reports, performance-sensitive
   queries, migrations, data fixes

The worst outcome is learning only the ORM and not understanding what it
generates. If you can write the SQL yourself, you can evaluate whether the
ORM is doing something sensible. If you can't, you're flying blind.

### Setting Up SQL CI and Hooks

If you add real SQL to a project using this template, you'll want automated
checks to catch issues early. The exact setup depends on which approach you
choose (raw SQL, ORM, or somewhere in between).

#### Option 1: Raw SQL Files (what this template's `db/` directory supports)

If you keep schema, migrations, and queries as `.sql` files:

| Check                 | Tool                                      | Where to run                 | What it catches                                          |
| --------------------- | ----------------------------------------- | ---------------------------- | -------------------------------------------------------- |
| **Syntax validation** | `sqlite3 :memory: < db/schema.sql`        | CI workflow, pre-commit hook | Malformed SQL that won't parse                           |
| **Lint + format**     | [SQLFluff](https://sqlfluff.com/)         | CI workflow, pre-commit hook | Style violations, anti-patterns, inconsistent formatting |
| **Migration order**   | Custom script (`scripts/`)                | CI workflow                  | Duplicate or out-of-order migration numbers              |
| **Migration apply**   | Apply migrations sequentially to empty DB | CI workflow                  | Migrations that fail, conflict, or don't compose         |
| **Seed data**         | Apply seeds after schema                  | CI workflow                  | Seeds that violate constraints                           |

**Pre-commit hook example (SQLFluff):**

```yaml
# .pre-commit-config.yaml
repos:
    - repo: https://github.com/sqlfluff/sqlfluff
      rev: 3.3.1 # check for latest
      hooks:
          - id: sqlfluff-lint
            args: [--dialect, sqlite] # or postgres, mysql, etc.
            files: \.sql$
          - id: sqlfluff-fix
            args: [--dialect, sqlite]
            files: \.sql$
```

**CI workflow example (schema validation):**

```yaml
# .github/workflows/sql-check.yml
name: SQL Check
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@...
      - name: Validate schema
        run: sqlite3 :memory: < db/schema.sql
      - name: Apply migrations in order
        run: |
          sqlite3 :memory: < db/schema.sql
          for f in db/migrations/*.sql; do
            echo "Applying $f"
            sqlite3 :memory: < "$f" || exit 1
          done
```

#### Option 2: ORM (SQLAlchemy, Django ORM, etc.)

If you use an ORM, SQL validation happens differently:

| Check                    | Tool                                                        | What it catches                       |
| ------------------------ | ----------------------------------------------------------- | ------------------------------------- |
| **Model validation**     | pytest + ORM setup                                          | Models that don't map to valid schema |
| **Migration generation** | `alembic check` / `python manage.py makemigrations --check` | Missing migrations                    |
| **Migration apply**      | `alembic upgrade head` against a test DB                    | Migrations that fail                  |
| **Integration tests**    | pytest with a test database                                 | Queries that fail at runtime          |

ORMs handle SQL generation, so you lint Python code (Ruff, mypy) rather than
SQL files. But you should still test that migrations apply cleanly and that
your models match the actual database.

#### Option 3: Hybrid (ORM + raw SQL for complex queries)

Many projects use an ORM for CRUD and drop to raw SQL for complex queries,
reports, or performance-critical paths. In that case, combine both approaches:

- Lint `.sql` files with SQLFluff
- Test ORM models and migrations with pytest
- Integration tests that exercise both code paths

#### What to Start With

For a new project using this template:

1. **Immediately:** Add a `task db:check` shortcut that runs
   `sqlite3 :memory: < db/schema.sql` — zero dependencies, instant sanity check
2. **When you have real SQL files:** Add SQLFluff as a pre-commit hook
3. **When you have migrations:** Add a CI job that applies them sequentially
4. **When you have data access code:** Add integration tests with a test database

The key principle: validate the SQL layer the same way you validate Python
code. If it can break, it should have a check.

---

## Shells: sh, bash, zsh, and Others

Shells are command-line interpreters — programs that read your commands and execute them. They matter for git hooks, scripts, CI pipelines, and daily terminal use. Each shell is a superset or variant of the one before it.

### The Shell Family Tree

```text
sh (Bourne Shell, 1979)
 └── bash (Bourne Again Shell, 1989)
      └── zsh (Z Shell, 1990)

csh (C Shell, 1978)         ← separate lineage
 └── tcsh
      └── fish (2005)       ← inspired by csh, but independent
```

### Shell Comparison

| Shell          | Full Name                  | Default On                        | Best For                           | Key Trait                               |
| -------------- | -------------------------- | --------------------------------- | ---------------------------------- | --------------------------------------- |
| **sh**         | Bourne Shell               | POSIX systems, Docker `alpine`    | Portable scripts, git hooks, CI    | Minimal — works everywhere              |
| **bash**       | Bourne Again Shell         | Most Linux distros, older macOS   | General scripting, interactive use | Arrays, `[[ ]]`, `$()`, rich scripting  |
| **zsh**        | Z Shell                    | macOS (since Catalina), many devs | Interactive daily use              | Plugins (Oh My Zsh), autocomplete, glob |
| **dash**       | Debian Almquist Shell      | Debian/Ubuntu (`/bin/sh` → dash)  | System scripts                     | Extremely fast, strict POSIX            |
| **fish**       | Friendly Interactive Shell | — (opt-in)                        | Interactive use, beginners         | Syntax highlighting, autosuggestions    |
| **PowerShell** | PowerShell                 | Windows                           | Windows automation, .NET           | Object pipeline (not text), cmdlets     |

### sh — The Portable Baseline

`sh` (POSIX shell) is the lowest common denominator. If you write a script in `sh`, it will run on virtually any Unix-like system — Linux, macOS, BSD, Docker containers, CI runners.

```bash
#!/bin/sh
# This runs everywhere. No bashisms allowed.
echo "Hello from sh"
```

**Key limitations** (things sh does NOT have):

- No arrays (`arr=(a b c)` is bash)
- No `[[ ]]` (use `[ ]` instead)
- No `$(( ))` for arithmetic in all implementations
- No `{1..10}` brace expansion
- No `function` keyword (just `myfunc() { ... }`)

**Why this matters:** On Debian/Ubuntu, `/bin/sh` is actually `dash` (not bash), so scripts with `#!/bin/sh` that use bash features will silently break.

### bash — The Workhorse

Bash is the most widely used shell for scripting. It extends sh with arrays, better string manipulation, `[[ ]]` tests, process substitution, and more.

```bash
#!/bin/bash
# Bash-specific features
names=("alice" "bob" "charlie")      # arrays
for name in "${names[@]}"; do
    if [[ "$name" == a* ]]; then     # [[ ]] pattern matching
        echo "Found: $name"
    fi
done
```

**Bash vs sh — common "bashisms" that break in sh:**

| Feature              | bash              | sh (POSIX)    |
| -------------------- | ----------------- | ------------- |
| Test syntax          | `[[ -f file ]]`   | `[ -f file ]` |
| Arrays               | `arr=(a b c)`     | Not available |
| String substitution  | `${var//old/new}` | Not available |
| Process substitution | `<(command)`      | Not available |
| Brace expansion      | `{1..5}`          | Not available |
| `source` command     | `source file`     | `. file`      |
| Function keyword     | `function foo()`  | `foo()`       |

### zsh — The Interactive Powerhouse

zsh is bash-compatible for most scripting but shines as an interactive shell with better tab completion, theming, spelling correction, and plugin ecosystems like **Oh My Zsh**.

```zsh
#!/bin/zsh
# zsh-specific features
typeset -A config                   # associative arrays (bash 4+ also has these)
config[host]=localhost
config[port]=8080
echo "Server: $config[host]:$config[port]"

# Glob qualifiers — zsh-only
print -l *.py(om)                   # list .py files sorted by modification time
```

**Why macOS switched to zsh:** Apple shipped bash 3.2 (2007) because bash 4+ is GPLv3, which conflicts with Apple's licensing. Rather than ship ancient bash, they switched the default to zsh (MIT-licensed) in macOS Catalina (2019).

### Which Shell for What?

| Use Case                       | Recommended Shell            | Why                                                          |
| ------------------------------ | ---------------------------- | ------------------------------------------------------------ |
| **Git hooks**                  | `#!/bin/sh`                  | Portability — hooks must work on every contributor's machine |
| **CI/CD scripts**              | `#!/bin/sh` or `#!/bin/bash` | CI runners have bash, but sh is safer for Docker alpine      |
| **Complex automation scripts** | `#!/bin/bash`                | Need arrays, string ops, or conditionals                     |
| **Daily terminal use**         | zsh or fish                  | Better autocomplete, history, plugins                        |
| **Makefiles / Taskfiles**      | sh (implicit)                | Make uses `/bin/sh` by default                               |
| **Docker `RUN` commands**      | sh                           | Alpine images only have sh, not bash                         |
| **Windows scripts**            | PowerShell                   | Native, object-based pipeline                                |

### Shells and Git Hooks

Git hooks are executable scripts in `.git/hooks/`. The shebang line (`#!/bin/sh`) determines which shell interprets them.

```bash
#!/bin/sh
# .git/hooks/pre-commit — runs before every commit
# Using sh for maximum portability

echo "Running pre-commit checks..."
python -m ruff check src/ || exit 1
```

**Why pre-commit (the framework) helps:** Instead of writing raw shell hook scripts, `pre-commit` manages hooks via `.pre-commit-config.yaml`. It handles shebang lines, virtual environments, and cross-platform compatibility — you never need to think about which shell the hook uses.

**Without pre-commit** (raw hooks):

- You write shell scripts directly in `.git/hooks/`
- You choose the shell (`#!/bin/sh`, `#!/bin/bash`, etc.)
- You handle portability yourself
- Hooks aren't versioned (`.git/hooks/` is not committed)

**With pre-commit** (framework):

- Hooks are defined in `.pre-commit-config.yaml` (versioned)
- The framework generates the actual hook scripts
- Each hook tool runs in its own isolated environment
- Shell portability is handled for you

### Common Gotcha: Shebang Lines

The shebang (`#!`) must be the **first line** of the script, with no leading whitespace or BOM:

```bash
#!/bin/sh          ← correct
#!/bin/bash        ← correct, but limits portability
#!/usr/bin/env bash  ← most portable way to invoke bash (finds it in $PATH)
```

`#!/usr/bin/env bash` is preferred over `#!/bin/bash` because bash isn't always at `/bin/bash` (e.g., on NixOS or some BSD systems). `env` searches `$PATH` to find it.

### Hook Scripts in Other Programming Languages

Git hooks don't have to be shell scripts. Any executable file with a valid shebang line works. This opens the door to Python, Node.js, Ruby, Perl, Rust, Go — whatever you have installed.

#### Language Examples for Hooks

**Python:**

```python
#!/usr/bin/env python3
"""pre-commit hook: check for TODO comments with no issue reference."""
import subprocess
import sys

result = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
    capture_output=True, text=True
)
staged_files = result.stdout.strip().splitlines()

for filepath in staged_files:
    with open(filepath) as f:
        for i, line in enumerate(f, 1):
            if "TODO" in line and "#" not in line.split("TODO")[1][:10]:
                print(f"{filepath}:{i}: TODO without issue reference")
                sys.exit(1)
```

**Node.js:**

```javascript
#!/usr/bin/env node
// pre-commit hook: validate JSON files
const fs = require("fs");
const { execSync } = require("child_process");

const staged = execSync("git diff --cached --name-only --diff-filter=ACM")
    .toString()
    .trim()
    .split("\n")
    .filter((f) => f.endsWith(".json"));

let failed = false;
for (const file of staged) {
    try {
        JSON.parse(fs.readFileSync(file, "utf8"));
    } catch (e) {
        console.error(`Invalid JSON: ${file} — ${e.message}`);
        failed = true;
    }
}
process.exit(failed ? 1 : 0);
```

**Ruby:**

```ruby
#!/usr/bin/env ruby
# pre-commit hook: check for binding.pry left in code
staged = `git diff --cached --name-only --diff-filter=ACM`.split("\n")
staged.select { |f| f.end_with?('.rb') }.each do |file|
  File.readlines(file).each_with_index do |line, i|
    if line.include?('binding.pry')
      puts "#{file}:#{i + 1}: Remove binding.pry before committing"
      exit 1
    end
  end
end
```

**Perl:**

```perl
#!/usr/bin/env perl
# pre-commit hook: check for trailing whitespace
use strict;
my @files = `git diff --cached --name-only --diff-filter=ACM`;
chomp @files;
for my $file (@files) {
    open my $fh, '<', $file or next;
    while (<$fh>) {
        if (/\s+$/) {
            print "$file:$.: trailing whitespace\n";
            exit 1;
        }
    }
}
```

#### Compiled Languages as Hooks

Compiled languages (Rust, Go, C) can also be used — you compile the binary first, then point the hook at it. This is less common for one-off hooks but used by dedicated hook tools:

```bash
#!/bin/sh
# Hook that delegates to a compiled Go binary
exec .git/hooks/bin/my-hook "$@"
```

Notable tools written in compiled languages that serve as hook systems:

- **lefthook** (Go) — fast, parallel hook runner with YAML config
- **rusty-hook** (Rust) — lightweight hook runner for Node projects
- **overcommit** (Ruby) — full-featured hook manager

#### Shells vs Programming Languages for Hooks

| Factor                     | Shell (sh/bash)                | Python                     | Node.js                 | Compiled (Go/Rust)          |
| -------------------------- | ------------------------------ | -------------------------- | ----------------------- | --------------------------- |
| **Startup speed**          | Instant (~5ms)                 | Slow (~50-100ms)           | Slow (~100ms)           | Instant (~5ms)              |
| **Portability**            | sh is everywhere               | Needs Python installed     | Needs Node installed    | Binary runs anywhere        |
| **String/text processing** | Awkward (sed, awk, grep)       | Excellent                  | Good                    | Good                        |
| **Error handling**         | Fragile (`set -e`, exit codes) | try/except, robust         | try/catch, robust       | Strong type system          |
| **File system operations** | Basic (test, find, ls)         | `pathlib`, `os` — powerful | `fs` module — decent    | Full stdlib                 |
| **JSON/YAML parsing**      | Needs `jq` or similar          | Built-in `json` module     | Built-in `JSON`         | Serde (Rust), encoding/json |
| **Git integration**        | Native (`git` commands)        | Subprocess calls           | Subprocess or libraries | Subprocess or `git2`        |
| **Complexity ceiling**     | Low (~50 lines max)            | Unlimited                  | Unlimited               | Unlimited                   |
| **Dependencies**           | None                           | pip/venv                   | npm/node_modules        | Compile step                |
| **Debugging**              | Painful (`set -x`)             | Proper debugger (pdb)      | Proper debugger         | Proper debugger             |
| **Windows support**        | Needs Git Bash/WSL             | Native                     | Native                  | Native                      |

#### When to Use What

| Scenario                                       | Best Choice            | Why                                              |
| ---------------------------------------------- | ---------------------- | ------------------------------------------------ |
| Simple file checks (whitespace, merge markers) | **Shell (sh)**         | 2-5 lines, no dependencies, instant              |
| Check staged file contents or patterns         | **Python**             | Easy file I/O, regex, readable                   |
| Validate JSON/YAML/config files                | **Python or Node**     | Built-in parsers                                 |
| Complex multi-step validation                  | **Python**             | Best balance of power and readability            |
| Enforce commit message format                  | **Shell or Python**    | Shell for simple regex, Python for complex rules |
| Performance-critical (huge repos)              | **Compiled (Go/Rust)** | Sub-millisecond execution                        |
| Team with mixed OS (Windows + Mac + Linux)     | **Python or Node**     | Cross-platform without shell quirks              |
| You already use pre-commit framework           | **Doesn't matter**     | pre-commit abstracts the language away           |

#### The Reality: pre-commit Framework Handles This

In practice, choosing a language for hooks is mostly academic if you use the `pre-commit` framework (which this project does). Each hook in `.pre-commit-config.yaml` runs its own tool in an isolated environment:

```yaml
repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit # Rust binary
      hooks:
          - id: ruff # ← you don't care that Ruff is written in Rust
    - repo: https://github.com/pre-commit/mirrors-mypy # Python tool
      hooks:
          - id: mypy # ← you don't care that mypy is Python
    - repo: https://github.com/pre-commit/pre-commit-hooks # Python scripts
      hooks:
          - id: check-yaml # ← you don't care about the implementation
```

The framework:

- Downloads and installs each hook's dependencies automatically
- Creates isolated environments (virtualenvs for Python, node_modules for Node, etc.)
- Handles shebang lines and shell compatibility
- Works identically on macOS, Linux, and Windows

**Bottom line:** The pre-commit framework lets you use the _best tool for the job_ regardless of what language it's written in. You pick hooks by _what they check_, not _what language they use_.

### Quick Reference: Shell Config Files

| Shell    | Login Shell                       | Interactive (non-login) | Notes                                   |
| -------- | --------------------------------- | ----------------------- | --------------------------------------- |
| **bash** | `~/.bash_profile` or `~/.profile` | `~/.bashrc`             | `.bash_profile` often sources `.bashrc` |
| **zsh**  | `~/.zprofile` then `~/.zshrc`     | `~/.zshrc`              | Oh My Zsh configures this               |
| **sh**   | `~/.profile`                      | —                       | Minimal config                          |
| **fish** | `~/.config/fish/config.fish`      | Same file               | No login/non-login split                |

---

## Repo Versioning — Manual vs Automatic

Every repo needs a version number, but _where_ that number lives and _how_ it gets updated varies. This is the fundamental decision that shapes your release workflow.

### The Core Question: Who Decides the Version?

| Approach            | Who/what sets the version    | Where the version lives            | When it changes                |
| ------------------- | ---------------------------- | ---------------------------------- | ------------------------------ |
| **Manual**          | Developer edits a file       | Hardcoded in source                | When you remember to update it |
| **Semi-automatic**  | Developer triggers a tool    | Tool updates source file(s)        | When you run the bump command  |
| **Fully automatic** | CI derives from commits/tags | Git tags or computed at build time | Every qualifying merge to main |

### Manual Versioning

You write the version string directly in one or more files and update it by hand before each release.

#### Where the version can live

```toml
# pyproject.toml — static version
[project]
version = "1.2.3"
```

```python
# src/my_package/__init__.py
__version__ = "1.2.3"
```

```python
# src/my_package/_version.py (dedicated version file)
VERSION = "1.2.3"
```

#### Typical manual workflow

```bash
# 1. Edit pyproject.toml (and any other files with version strings)
# 2. Commit
git add pyproject.toml
git commit -m "chore: bump version to 1.3.0"
# 3. Tag
git tag v1.3.0
# 4. Push
git push origin main --tags
```

#### Problems with manual versioning

- **Drift** — easy to update pyproject.toml but forget `__init__.py` or vice versa
- **Human error** — typos, skipped versions, forgetting to tag
- **No changelog** — you have to write release notes from memory
- **Merge conflicts** — version bumps in pyproject.toml create conflicts between parallel PRs
- **Tag/version mismatch** — commit says `1.3.0` but you tagged `v1.2.9`

#### When manual versioning is fine

- Solo projects with infrequent releases
- Learning how versioning works (do it manually first, then automate)
- Projects with no consumers (internal tools, scripts)
- Very early development where releases don't matter yet

### Automatic Versioning

The version is _derived_ — either from git tags at build time, or from commit messages by a CI tool.

#### Approach A: Tag-derived (build-time versioning)

The version doesn't exist in any source file. Instead, a build plugin reads the latest git tag and computes the version.

```toml
# pyproject.toml — dynamic version via hatch-vcs
[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"         # version comes from git tags

[tool.hatch.build.hooks.vcs]
version-file = "src/my_package/_version.py"  # generated at build time
```

**How it works:**

```text
git tag v1.2.0 on commit abc123

After tagging:
  pip install .  →  version = "1.2.0"

3 commits later (no new tag):
  pip install .  →  version = "1.2.0.dev3+g7f8e9a1"
                              ↑ 3 commits since tag, at this hash
```

**Tools that do this:**

| Tool               | Build backend                     | Config                                |
| ------------------ | --------------------------------- | ------------------------------------- |
| **hatch-vcs**      | Hatchling                         | `[tool.hatch.version] source = "vcs"` |
| **setuptools-scm** | Setuptools                        | `[tool.setuptools_scm]`               |
| **versioningit**   | Any (Hatchling, setuptools, etc.) | `[tool.versioningit]`                 |
| **dunamai**        | Any (library/CLI)                 | CLI flags or API calls                |

**Pros:**

- Zero maintenance — version is always correct
- No merge conflicts — no version string in source files
- Tag is the single source of truth — impossible for code and tag to drift
- Dev versions (`1.2.0.dev3`) are automatic for unreleased commits

**Cons:**

- Requires git history at build time (`git clone --depth 1` breaks it)
- Can be confusing — "where is the version?" has no obvious answer
- Import-time overhead if the version is computed dynamically (vs generated file)
- CI must have full git history or at least tags (`fetch-depth: 0`)

#### Approach B: Commit-derived (CI determines the bump)

A CI tool reads commit messages (conventional commits), determines the bump type, updates the version, and creates the release — all automatically.

```text
feat: add export endpoint        →  CI bumps minor:  1.2.0 → 1.3.0
fix: handle null email           →  CI bumps patch:  1.3.0 → 1.3.1
feat!: redesign auth API         →  CI bumps major:  1.3.1 → 2.0.0
chore: update deps               →  no release
```

**Tools that do this:**

| Tool                        | How it manages versions                                                                                             |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **release-please**          | Opens a Release PR tracking pending changes; merging bumps version, updates CHANGELOG, creates GitHub Release + tag |
| **python-semantic-release** | Runs in CI, parses commits, bumps version in source, tags, publishes to PyPI                                        |
| **commitizen**              | `cz bump` reads commits and bumps version; can run locally or in CI                                                 |
| **semantic-release** (JS)   | The original Node.js version — full plugin pipeline                                                                 |

**Pros:**

- Fully hands-off — merge PRs with good commit messages, releases happen
- Changelog is generated automatically from commit history
- Version bumps are deterministic — same commits always produce same version
- Enforces commit discipline (teams must write meaningful commit messages)

**Cons:**

- Requires disciplined commit messages — messy commits = wrong versions
- Opinionated — you give up control over when releases happen
- Debugging release issues means reading CI logs, not local files
- Learning curve for the tooling configuration

### Combining Both Approaches (What This Project Does)

This project uses **tag-derived versioning** (hatch-vcs) for the package version and **commit-derived releases** (release-please) for deciding _when_ to create tags:

```text
Developer writes conventional commits
  → release-please opens a Release PR (accumulates changes)
  → Merging the Release PR creates a git tag (e.g. v1.3.0)
  → hatch-vcs reads that tag at build time → package version = 1.3.0
  → GitHub Actions builds and publishes artifacts
```

This gives you:

- **No version in source code** — hatch-vcs derives it from tags
- **Automatic release timing** — release-please decides when to release based on commits
- **Human review** — the Release PR lets you review the changelog before merging
- **Correct versions everywhere** — tag, package metadata, and CHANGELOG all agree

### Decision Matrix: Which Approach to Choose

| Factor                       | Manual         | Semi-auto (bump tools) | Tag-derived | Commit-derived | Both (this project)             |
| ---------------------------- | -------------- | ---------------------- | ----------- | -------------- | ------------------------------- |
| **Effort per release**       | High           | Medium                 | None        | None           | None                            |
| **Risk of version drift**    | High           | Medium                 | None        | Low            | None                            |
| **Changelog**                | Manual         | Manual                 | Manual      | Automatic      | Automatic                       |
| **Commit discipline needed** | No             | No                     | No          | Yes            | Yes                             |
| **Setup complexity**         | None           | Low                    | Low         | Medium         | Medium                          |
| **Best for**                 | Learning, solo | Small teams            | Libraries   | Apps, teams    | Template repos, mature projects |

See also: [Release Workflows](#release-workflows) below for the full tool comparison, and [ADR 021](../adr/021-automated-release-pipeline.md) for this project's specific choices.

---

## Release Workflows

How to get code from "PR merged" to "version published" — and the many tools that automate each step. There's no single right answer; the ecosystem has a lot of overlapping approaches. These notes capture what I've learned about the options.

### The Release Lifecycle

Every release workflow, regardless of tooling, follows roughly the same steps:

1. **Open a PR** — propose changes, get review
2. **Merge** — land the change on the default branch
3. **Determine the next version** — based on commit messages, labels, or manual input
4. **Update version metadata** — `pyproject.toml`, `__version__`, tags
5. **Generate changelog** — from commits, PR titles, or conventional commits
6. **Create a release** — GitHub Release, Git tag, or both
7. **Publish artifacts** — PyPI, container registry, docs site, etc.

The interesting question is: which of these steps are manual, which are automated, and which tools do the work?

### Strategy 1: Fully Manual

The simplest approach — you do everything by hand.

```text
merge PR → edit version in pyproject.toml → git tag → git push --tags → gh release create → twine upload
```

**When it makes sense:** Solo projects, early prototypes, learning how releases work.

**Downsides:** Error-prone, easy to forget a step, version and tag can drift.

### Strategy 2: Version Bump Tools (Semi-Automated)

Use a tool to bump the version, tag, and commit — but you trigger it manually.

#### Version Bumping Tools

| Tool                               | How it works                                                                                | Version source                                | Pros                                               | Cons                                                                        |
| ---------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------- |
| **hatch version**                  | `hatch version minor` bumps in pyproject.toml                                               | `[project] version` or `[tool.hatch.version]` | Integrated with Hatch, supports dynamic versioning | Requires Hatch                                                              |
| **bump2version / bump-my-version** | Reads `.bumpversion.cfg` or `pyproject.toml`, updates version strings across multiple files | Any file with version strings                 | Multi-file support, regex-based find/replace       | Extra config file (or `[tool.bumpversion]`), can be fiddly                  |
| **tbump**                          | `tbump 1.2.3` updates version, commits, tags, pushes                                        | `[tool.tbump]` in pyproject.toml              | Single command does commit+tag+push, regex-based   | Must pass the exact version (no `major`/`minor` keywords)                   |
| **setuptools-scm**                 | Derives version from Git tags at build time — no version in source                          | Git tags                                      | Zero maintenance, always matches Git               | Harder to reason about, import-time overhead, needs `[tool.setuptools_scm]` |
| **versioningit**                   | Like setuptools-scm but for other backends                                                  | Git tags + configurable format                | Backend-agnostic, flexible format strings          | More config than setuptools-scm                                             |
| **hatch-vcs**                      | Hatchling plugin that reads version from VCS (Git tags)                                     | Git tags via `[tool.hatch.version]`           | Integrates with Hatchling builds                   | Requires Hatch ecosystem                                                    |
| **incremental**                    | Twisted project's versioning tool                                                           | `_version.py` file                            | Used by Twisted/large projects                     | Less popular outside that ecosystem                                         |
| **dunamai**                        | Library + CLI for dynamic versions from VCS                                                 | Git/Mercurial tags                            | Language-agnostic, composable with other tools     | CLI-only or library — not a full release tool                               |
| **poetry version**                 | `poetry version minor`                                                                      | `[tool.poetry] version`                       | Integrated into Poetry workflow                    | Poetry-only                                                                 |
| **pdm bump**                       | `pdm bump minor`                                                                            | `[project] version`                           | Integrated into PDM                                | PDM-only                                                                    |

#### Typical semi-automated workflow

```bash
# 1. Bump version (updates pyproject.toml, commits, tags)
hatch version minor
# or: bump-my-version bump minor
# or: tbump 1.3.0

# 2. Push tag to trigger CI
git push origin main --tags

# 3. CI handles the rest (build, publish, release notes)
```

### Strategy 3: Conventional Commits + Automated Release

This is the "commit message is the API" approach. The version bump and changelog are **derived from commit messages** — no manual version decisions.

#### How conventional commits drive releases

```text
feat: add user export endpoint    →  minor bump (0.2.0 → 0.3.0)
fix: handle null email in signup  →  patch bump (0.3.0 → 0.3.1)
feat!: redesign auth API          →  major bump (0.3.1 → 1.0.0)
  (or: BREAKING CHANGE: in body)
chore: update CI config           →  no release
docs: fix typo in README          →  no release
```

#### Tools that consume conventional commits

| Tool                        | Language      | What it does                                                                                | Outputs                                                  | Pros                                                                  | Cons                                                      |
| --------------------------- | ------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------- |
| **python-semantic-release** | Python        | Parses commits, bumps version, updates changelog, creates GitHub Release, publishes to PyPI | Version bump, CHANGELOG.md, GitHub Release, PyPI publish | Full pipeline for Python, GitHub Actions friendly                     | Config can be complex, opinionated defaults               |
| **semantic-release** (JS)   | Node.js       | The original — parses commits, bumps, publishes, releases                                   | Version bump, changelog, npm publish, GitHub Release     | Massive plugin ecosystem, very mature                                 | Node dependency in a Python project                       |
| **release-please** (Google) | GitHub Action | Creates a "Release PR" that tracks pending changes; merging the PR triggers the release     | Release PR, version bump, CHANGELOG.md, GitHub Release   | No local tooling needed, PR-based review of release, monorepo support | Google-maintained (bus factor), opinionated PR flow       |
| **commitizen**              | Python        | Commit message prompting (`cz commit`), version bump, changelog generation                  | Guided commits, version bump, CHANGELOG.md               | Interactive commit helper + release tool in one, Python native        | Two jobs in one tool — some prefer separation             |
| **standard-version**        | Node.js       | Bump version, generate changelog from conventional commits, tag                             | Version bump, CHANGELOG.md, Git tag                      | Simple, focused                                                       | Deprecated in favour of release-please                    |
| **cocogitto**               | Rust          | Validate conventional commits, bump version, generate changelog                             | Version bump, CHANGELOG.md, Git tag                      | Fast, strict validation, good CI integration                          | Rust binary, smaller community                            |
| **git-cliff**               | Rust          | Highly configurable changelog generator (not a full release tool)                           | CHANGELOG.md                                             | Extremely customisable templates, fast, any commit convention         | Changelog only — doesn't bump versions or create releases |
| **auto** (Intuit)           | Node.js       | Label-based releases — uses PR labels instead of commit messages                            | Version bump, changelog, GitHub Release, npm publish     | PR-label approach is more accessible than commit conventions          | Node dependency, label-driven (different paradigm)        |
| **changelogithub**          | Node.js       | Generate changelog from GitHub PR titles/commits                                            | Changelog, GitHub Release body                           | Uses GitHub API, pretty output                                        | Changelog only, Node dependency                           |

### Strategy 4: Release PR Pattern (release-please Style)

This is a higher-level pattern where the tool **opens a PR** that represents the next release, and **merging that PR** triggers the actual release.

#### How it works

```text
1. Contributors merge feature PRs into main
2. Bot watches main, accumulates changes, opens/updates a "Release PR"
3. Release PR contains:
   - Version bump in pyproject.toml (or package.json, etc.)
   - Updated CHANGELOG.md with all changes since last release
4. Maintainer reviews the Release PR
5. Merging the Release PR triggers:
   - Git tag creation
   - GitHub Release creation
   - CI publish workflow (PyPI, npm, etc.)
```

#### Tools supporting the Release PR pattern

| Tool               | How the Release PR works                                                                       | Monorepo                | Multi-language                           |
| ------------------ | ---------------------------------------------------------------------------------------------- | ----------------------- | ---------------------------------------- |
| **release-please** | GitHub Action watches pushes to main, opens/updates a Release PR automatically                 | Yes (workspace plugins) | Yes (Python, Node, Java, Go, Rust, etc.) |
| **changesets**     | CLI generates "changeset" files in PRs; a bot opens a "Version Packages" PR that combines them | Yes (native)            | Mainly JS/TS but adaptable               |
| **knope**          | Rust-based, uses changeset files or conventional commits to generate a Release PR              | Yes                     | Yes (any language)                       |

### Strategy 5: Tag-Driven Releases (CI Does Everything)

Push a Git tag → CI builds, publishes, releases. The simplest CI-driven approach.

```yaml
# .github/workflows/publish.yml
on:
    push:
        tags: ["v*"]

jobs:
    publish:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@...
            - run: python -m build
            - uses: pypa/gh-action-pypi-publish@...
```

You manually (or via a bump tool) create the tag. CI handles the rest.

### Changelog Generation — Deeper Dive

Changelogs can be generated from multiple sources. The tools differ in what they consume and how customisable the output is.

#### Changelog Source Material

| Source                           | Tools that use it                                                | Pros                                                | Cons                                                   |
| -------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------ |
| **Conventional commit messages** | python-semantic-release, commitizen, cocogitto, standard-version | Automated, structured, links to commits             | Requires discipline from all contributors              |
| **PR titles / PR bodies**        | release-please, auto, changelogithub                             | Easier for contributors (just write good PR titles) | Less granular than per-commit                          |
| **PR labels**                    | auto (Intuit), release-drafter                                   | Visual, easy to apply retroactively                 | Extra manual step (labelling), labels can be forgotten |
| **Changeset files**              | changesets, knope, towncrier                                     | Each PR includes a human-written changelog fragment | Extra file per PR, merge conflicts possible            |
| **Git log (any format)**         | git-cliff, gitmoji-changelog                                     | Works with any commit format                        | Noisy unless commits are clean                         |
| **Manual**                       | Keep a Changelog format                                          | Full control, human-quality writing                 | Easy to forget, drifts from actual changes             |

#### Changelog Fragment / Towncrier Pattern

Some projects use **changelog fragments** — small files added per-PR that are combined at release time.

| Tool           | Fragment format              | How it works                                                                 | Pros                                | Cons                                                    |
| -------------- | ---------------------------- | ---------------------------------------------------------------------------- | ----------------------------------- | ------------------------------------------------------- |
| **towncrier**  | `changes/123.feature.md`     | Each PR adds a fragment file; `towncrier build` combines them into CHANGELOG | Human-written entries, categorised  | Extra file per change, merge conflicts on the directory |
| **changesets** | `.changeset/cool-feature.md` | CLI generates a changeset file; bot combines on release                      | Interactive CLI, monorepo support   | JS-ecosystem origin                                     |
| **knope**      | `.changeset/*.md`            | Similar to changesets but Rust-based                                         | Cross-language, fast                | Newer tool                                              |
| **scriv**      | `changelog.d/*.md`           | Fragment-based, configurable, Python-native                                  | Flexible templates, Python-friendly | Smaller community                                       |

### PR Automation Tools

Tools that help manage the PR lifecycle itself — auto-labelling, auto-merge, auto-assign, etc.

| Tool                          | What it does                                                                    | How it works                                       |
| ----------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------- |
| **release-drafter**           | Drafts GitHub Release notes from PR labels; auto-labels PRs based on file paths | GitHub Action, reads `.github/release-drafter.yml` |
| **auto-approve**              | Auto-approves PRs from trusted bots (Dependabot, Renovate)                      | GitHub Action with conditions                      |
| **mergify**                   | Auto-merge, priority queues, auto-label, CI retries                             | SaaS with `.mergify.yml` config                    |
| **kodiak**                    | Auto-merge when checks pass and PR is approved                                  | GitHub App with `.kodiak.toml`                     |
| **bulldozer**                 | Auto-merge + auto-delete branch after merge                                     | GitHub App by Palantir                             |
| **probot-auto-merge**         | Auto-merge based on labels and check status                                     | GitHub App (Probot framework)                      |
| **actions/labeler**           | Auto-label PRs based on changed file paths                                      | GitHub Action with `.github/labeler.yml`           |
| **action-automatic-releases** | Create GitHub Releases automatically on tag push                                | GitHub Action                                      |
| **pr-agent** (CodiumAI)       | AI-powered PR review, auto-describe, auto-label                                 | GitHub App or Action                               |
| **danger-js / danger-python** | Programmable PR review rules (check PR size, missing tests, etc.)               | CI step, reads `Dangerfile`                        |

### Dependency Update Bots

These open PRs to keep dependencies current — relevant because they feed into the release pipeline.

| Tool           | What it updates                                 | How it works                                | Pros                                                           | Cons                                            |
| -------------- | ----------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------- |
| **Dependabot** | pip, npm, GitHub Actions, Docker, Bundler, etc. | GitHub-native, `.github/dependabot.yml`     | Zero setup, built into GitHub                                  | Limited grouping, no lock file merging strategy |
| **Renovate**   | 50+ package managers                            | Self-hosted or Mend.io App, `renovate.json` | Extremely configurable, auto-merge rules, grouping, scheduling | Complex config, can be noisy                    |
| **pyup**       | Python (pip, pipenv, poetry)                    | GitHub App or CLI                           | Python-focused, safety DB integration                          | Smaller scope than Renovate                     |
| **depfu**      | npm, Yarn, Bundler                              | GitHub App                                  | Clean PRs, grouped updates                                     | Limited language support                        |

### Putting It All Together — Example Workflows

#### Minimal (solo project, tag-driven)

```text
1. Work on main
2. hatch version patch → commits + tags
3. git push --tags
4. CI publishes to PyPI on tag push
```

**Tools:** Hatch, GitHub Actions, pypa/gh-action-pypi-publish

#### Mid-size (team, conventional commits)

```text
1. Feature PR → conventional commit messages enforced by commitizen/pre-commit
2. Merge PR to main
3. python-semantic-release in CI:
   - Parses new commits since last tag
   - Bumps version in pyproject.toml
   - Updates CHANGELOG.md
   - Creates Git tag + GitHub Release
   - Publishes to PyPI
```

**Tools:** commitizen (commit helper), python-semantic-release (CI), GitHub Actions

#### Large / monorepo (Release PR pattern)

```text
1. Feature PRs merged to main
2. release-please Action opens/updates a Release PR:
   - Bumps version
   - Updates CHANGELOG.md
   - Lists all changes since last release
3. Maintainer reviews and merges the Release PR
4. Merge triggers: tag → GitHub Release → CI publish
```

**Tools:** release-please, GitHub Actions, pypa/gh-action-pypi-publish

#### Fragment-based (human-written changelogs)

```text
1. Each feature PR includes a changelog fragment (changes/123.feature.md)
2. At release time: towncrier build → combines fragments into CHANGELOG.md
3. bump-my-version bump minor → updates version, commits, tags
4. git push --tags → CI publishes
```

**Tools:** towncrier, bump-my-version, GitHub Actions

### Version Numbering Schemes

Not all projects use SemVer. Here are the common schemes and which tools support them.

| Scheme      | Format                                       | When to use                                                         | Tools that support it                                              |
| ----------- | -------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------ |
| **SemVer**  | `MAJOR.MINOR.PATCH`                          | Libraries, APIs, anything with a public contract                    | All of the above                                                   |
| **CalVer**  | `YYYY.MM.DD` or `YY.MM.MICRO`                | Applications, data pipelines, things without API stability promises | bump-my-version, hatch-calver, commitizen (custom), setuptools-scm |
| **PEP 440** | `1.2.3`, `1.2.3.dev4`, `1.2.3a1`, `1.2.3rc1` | Python packages (required for PyPI)                                 | All Python tools enforce this                                      |
| **ZeroVer** | `0.x.y` forever                              | Projects that never commit to stability (half-joking)               | Any tool — just never bump major                                   |

### What This Project Uses

This project uses a fully automated release pipeline:

- **Conventional commits** validated by commitizen (pre-commit hook + CI)
- **release-please** for automated Release PRs, CHANGELOG, tags, and GitHub Releases
- **hatch-vcs** for deriving package version from git tags at build time
- **Rebase+merge** strategy for linear history with fine-grained CHANGELOG entries
- **GitHub Actions** for build, publish, SBOM generation on tag push

See [ADR 021](../adr/021-automated-release-pipeline.md) and [releasing.md](../releasing.md) for the full workflow.

---

## Pre-1.0 Release Readiness

### Why 1.0 Is Different

Everything before `1.0.0` is understood to be unstable — APIs can change,
features can disappear, and users expect rough edges. Once you tag `1.0.0`,
you're making a social contract:

- **Backward compatibility matters.** Breaking changes require a major version bump.
- **Security responsiveness is expected.** Users assume you'll patch CVEs.
- **The project is usable.** It's not a demo, sketch, or experiment anymore.

A 1.0 that can't pass its own CI, has placeholder code, or ships with broken
docs erodes trust fast. The checklist below is a systematic way to verify
you're actually ready.

### The Readiness Checklist

The canonical checklist lives in [releasing.md — Pre-1.0 Release Readiness
Checklist](../releasing.md#pre-10-release-readiness-checklist). Use it as
a worksheet: copy it into a GitHub issue or PR description and check items
off as you verify them.

The checklist covers these areas:

| Area                         | What to verify                                                                     |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| **Code quality**             | Placeholder code removed, type hints, docstrings, clean `task check`               |
| **Test coverage**            | Core logic covered, edge cases tested, coverage threshold set, version consistency  |
| **Security**                 | SECURITY.md finalized, pip-audit clean, no hardcoded secrets, Dependabot enabled    |
| **Documentation**            | README accurate, API reference renders, CHANGELOG meaningful, docs build clean      |
| **CI/CD & Infrastructure**   | All workflows pass, branch protection configured, repo guards set, release tested   |
| **Packaging & Distribution** | Metadata complete, classifier updated, entry points work, clean install succeeds    |
| **Release configuration**    | release-please config reviewed, manifest version correct, tag format verified       |

### Common Pre-1.0 Mistakes

Things that trip people up when going from 0.x to 1.0:

1. **Forgetting `bump-minor-pre-major`** — release-please treats minor and
   major differently pre-1.0. If you have `"bump-minor-pre-major": true` in
   your config, a `feat!:` commit bumps minor (0.x → 0.y) instead of major.
   After 1.0, you should remove this flag so breaking changes bump major.

2. **Stale `Development Status` classifier** — `pyproject.toml` still says
   `Development Status :: 3 - Alpha` when you ship 1.0. Update it to
   `Development Status :: 5 - Production/Stable` (or `4 - Beta` if you're
   not fully there yet).

3. **Placeholder SECURITY.md** — The template ships with generic contact
   info. Before 1.0, replace it with a real email or enable GitHub's
   private vulnerability reporting.

4. **No release dry-run** — Ship a 0.9.0 first. Verify the full pipeline
   (tag → build → publish → docs deploy) works end-to-end before the
   irreversible 1.0.0 tag.

5. **Template TODOs still present** — Run `python scripts/check_todos.py`
   to catch any `TODO (template users):` markers that should have been
   resolved.

6. **Python version drift** — The minimum Python version in `pyproject.toml`,
   CI matrix, classifiers, and `bootstrap.py` can drift apart silently.
   Run `python scripts/check_python_support.py` to catch mismatches.

### After 1.0

Once 1.0 is out:

- SemVer is fully enforced: breaking changes bump **major** version
- Remove `"bump-minor-pre-major": true` from `release-please-config.json`
- Update `SECURITY.md` support window (e.g., "latest major version")
- Consider setting up automated PyPI publishing if not already done
- Enable GitHub's "Require status checks to pass before merging" on `main`

See [releasing.md](../releasing.md) for the mechanical steps of cutting the
1.0.0 release (Release-As trailer, manifest edit, etc.).

---

## Breaking Changes & Version Bumping

### What Is a Breaking Change?

A **breaking change** is any modification that forces existing users to
change their code, configuration, commands, or workflows to keep things
working. If someone was relying on old behaviour and the update makes
that behaviour stop working, it's a breaking change.

#### Examples of Breaking Changes

| Domain              | Breaking change example                                          | Why it breaks                                            |
| ------------------- | ---------------------------------------------------------------- | -------------------------------------------------------- |
| **Python library**  | Renaming a public function from `get_users()` to `fetch_users()` | All callers must update their import / call site         |
| **REST API**        | Removing the `/api/v1/users` endpoint                            | Clients sending requests to that URL get 404             |
| **CLI tool/script** | Removing `--fix` flag from `git_doctor.py`                       | Scripts or aliases using `--fix` fail with "unknown arg" |
| **Config format**   | Changing YAML key from `database_url` to `db.url`                | Existing config files are silently ignored               |
| **Database**        | Dropping a column that other code reads                          | Queries crash with "column not found"                    |
| **File format**     | Changing a CSV export from comma-separated to tab-separated      | Downstream parsers split on the wrong character          |
| **Game**            | Removing a character ability after players invested in it        | Players' builds/strategies break                         |
| **OS**              | Dropping support for a system call (Linux kernel) or API (Win32) | Programs compiled against the old API crash or fail      |
| **Browser**         | Removing `document.all` or changing CSS default behaviour        | Old websites visually break or lose functionality        |

#### What Is NOT a Breaking Change

- Adding a new function, endpoint, or config key (existing code ignores it)
- Adding a new optional flag to a CLI tool
- Fixing a bug (unless people depended on the buggy behaviour)
- Internal refactors that don't change public interfaces
- Performance improvements with no API change
- Adding new default values for previously-unset fields

#### The Grey Area

Some changes are debatable:

- **Fixing a security bug** that changes behaviour — technically breaking,
  usually accepted as necessary.
- **Widening return types** (e.g. function returns `int | None` instead of
  `int`) — not a breaking change in dynamic languages, breaking in statically
  typed ones.
- **Tightening validation** (rejecting inputs that were previously accepted) —
  breaking for anyone sending those inputs, even if the old acceptance was a bug.

### What Is Version Bumping?

**Version bumping** is incrementing a project's version number to indicate
that something changed. It tells users (humans, package managers, CI
systems) "this release is different from the last one."

A version number is not just a label — it carries information about what
the update contains, how risky it is to upgrade, and whether old code
will keep working.

### How Version Bumping Works (SemVer)

The most widely used scheme is **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`.

| Component | When to bump                    | What it signals to users                            | Example           |
| --------- | ------------------------------- | --------------------------------------------------- | ----------------- |
| **PATCH** | Bug fix, docs, internal cleanup | "Safe to upgrade — nothing new, just fixes."        | `1.2.3` → `1.2.4` |
| **MINOR** | New feature, non-breaking       | "New stuff available, old stuff still works."       | `1.2.4` → `1.3.0` |
| **MAJOR** | Breaking change                 | "Read the changelog — something you use may break." | `1.3.0` → `2.0.0` |

When you bump a higher component, lower ones reset to zero:

- `1.2.4` → minor bump → `1.3.0` (patch resets)
- `1.3.0` → major bump → `2.0.0` (minor and patch reset)

### When to Bump Major (and When Not To)

Strictly by SemVer, a major bump signals a breaking change. In practice,
projects interpret this differently:

| Approach                   | Who does it                         | Philosophy                                                    |
| -------------------------- | ----------------------------------- | ------------------------------------------------------------- |
| **Strict SemVer**          | Libraries with public API contracts | Major = breaking. Period. Even if the change is small.        |
| **Marketing / milestone**  | Games, apps, commercial software    | Major bump for big feature milestones, even if nothing breaks |
| **Time-based**             | Ubuntu, some enterprise software    | Major bump on a schedule (Ubuntu 22.04 → 24.04)               |
| **Internal scripts/tools** | Teams, personal projects            | Major bump when it "feels like a new version" — less rigorous |
| **ZeroVer (0.x.y)**        | Pre-1.0 projects                    | Everything is unstable, bump minor freely, never commit       |

**Bottom line:** For libraries consumed by others, follow SemVer strictly.
For internal tools, scripts, and apps, a major bump for a significant
overhaul (even without a breaking change) is common and accepted.

### How Version Numbers Work Across Domains

Not everything follows SemVer. Different categories of software have
different versioning traditions:

#### Libraries & Packages (SemVer)

Format: `MAJOR.MINOR.PATCH` (e.g. `requests 2.31.0`, `numpy 1.26.4`)

- Consumed by other code, so compatibility matters.
- Package managers (pip, npm) use version ranges (`>=1.2,<2` means
  "any minor/patch in 1.x").
- Breaking change = major bump. This is a contract, not a suggestion.

#### Applications & Desktop Software

Format: Varies. `MAJOR.MINOR` (Chrome 122), `MAJOR.MINOR.PATCH`
(VS Code 1.87.2), or marketing names (Windows 11).

- Users don't pin to version ranges — they just "update to latest."
- Major bumps often mark feature milestones or UI overhauls, not
  necessarily API breaks.
- Some apps use CalVer: `JetBrains 2024.1`, `Ubuntu 24.04`.

#### Games

Format: Varies widely.

| Pattern                  | Example                     | Notes                                                      |
| ------------------------ | --------------------------- | ---------------------------------------------------------- |
| **Major.Minor**          | Minecraft 1.21              | Minor = content updates. Major rarely changes.             |
| **Sequential**           | Final Fantasy XVI           | Each game is a new product, not a version bump.            |
| **Season / patch**       | Fortnite Chapter 5 Season 2 | Marketing-driven; "patch 29.10" for internal builds.       |
| **Year**                 | FIFA 24, F1 2024            | Annual franchise, version = year.                          |
| **Build number**         | Dwarf Fortress 50.12        | Incrementing build; major changes are just bigger numbers. |
| **Early access / alpha** | Valheim 0.217.46            | Pre-1.0, ZeroVer, rapid iteration.                         |

Games care about player perception and marketing more than API
compatibility, so version numbers serve branding purposes.

#### Scripts & Internal Tools

Format: Whatever the maintainer wants. Often `MAJOR.MINOR.PATCH` by
convention, but rules are looser.

- No external consumers to break, so the version is informational.
- Common to bump major for significant rewrites or feature overhauls.
- Example: `git_doctor.py` went from 2.1.0 → 3.0.0 when the `--fix`
  flag was removed (breaking change for anyone scripting against it)
  and the output display was completely redesigned.

#### Operating Systems

| OS          | Scheme                          | Example                  | Notes                                                         |
| ----------- | ------------------------------- | ------------------------ | ------------------------------------------------------------- |
| **Linux**   | `MAJOR.MINOR` (kernel)          | 6.8                      | Even/odd minor was once stable/dev. Now just linear.          |
| **Ubuntu**  | CalVer `YY.MM`                  | 24.04 (April 2024)       | LTS every 2 years. Version = release date.                    |
| **macOS**   | Marketing + `MAJOR.MINOR.PATCH` | Sonoma 14.4              | Marketing name changes yearly, version increments.            |
| **Windows** | Marketing number                | Windows 11 (build 22621) | Version number is mostly marketing. Build number is internal. |
| **Android** | API level + marketing           | Android 14 (API 34)      | API level is the real version for developers.                 |
| **iOS**     | `MAJOR.MINOR.PATCH`             | 17.4.1                   | Major = yearly, minor = features, patch = fixes.              |

Operating systems face the hardest compatibility challenge: they must
support millions of programs built over decades. Breaking changes in OS
APIs are extremely rare and flagged years in advance (deprecation warnings,
compatibility shims, migration guides).

### How Version Bumps Are Triggered

| Method                   | How it works                                                           | Best for                     |
| ------------------------ | ---------------------------------------------------------------------- | ---------------------------- |
| **Manual edit**          | Change the version string in a file and commit                         | Solo projects, learning      |
| **Bump tool**            | `hatch version minor` / `bump-my-version bump patch`                   | Semi-automated workflows     |
| **Conventional commits** | `feat:` = minor, `fix:` = patch, `feat!:` / `BREAKING CHANGE:` = major | Fully automated CI pipelines |
| **Git tag**              | `git tag v1.2.3` — version derived from tag at build time              | Tag-driven releases          |
| **Release PR**           | Bot (release-please) opens a PR with the version bump                  | Team projects, code review   |

### Pre-release & Build Metadata

SemVer also defines pre-release and build metadata suffixes:

| Suffix                   | Meaning                                | Example           | Use case                         |
| ------------------------ | -------------------------------------- | ----------------- | -------------------------------- |
| `-alpha.1`               | Early unstable release                 | `2.0.0-alpha.1`   | Internal testing, incomplete API |
| `-beta.2`                | Feature-complete but untested          | `2.0.0-beta.2`    | External beta testers            |
| `-rc.1`                  | Release candidate                      | `2.0.0-rc.1`      | Final validation before release  |
| `+build.123`             | Build metadata (ignored in precedence) | `2.0.0+build.123` | CI tracking, debug info          |
| `.dev4` (Python/PEP 440) | Development pre-release                | `2.0.0.dev4`      | Nightly builds, dev installs     |

Pre-release versions have **lower** precedence than the release:
`1.0.0-alpha.1 < 1.0.0-beta.1 < 1.0.0-rc.1 < 1.0.0`.

---

## Merge Strategies for Integrating into Main

When changes from a feature branch need to get into `main`, there are several strategies. Each produces a different commit history shape, affects traceability, and has implications for tools like `git bisect`, changelog generation, and `git log` readability.

### Direct Push to Main (No Branch, No PR)

The simplest approach: commit directly on `main` and push.

```text
main:  A ─ B ─ C ─ D
                     ↑ your commits land here
```

- **History:** Linear
- **When to use:** Solo projects, trivial changes, CI-only repos
- **Pros:** No overhead, no branches to manage
- **Cons:** No review, no CI checks before landing, no PR record, dangerous for teams
- **Who uses this:** Very small projects, personal repos, config-only repos

### Merge Commit (GitHub Default)

Creates a special commit with **two parents** — one from main, one from the branch tip. Preserves the branch topology.

```text
main:    A ─ B ─ ─ ─ ─ ─ M
              \         /
feature:       C ─ D ─ E
```

Where `M` is the merge commit with parents `B` and `E`.

- **History:** Non-linear (graph shape, "railroad tracks" in `git log --graph`)
- **Original SHAs:** Preserved — the branch commits keep their hashes
- **Merge event:** Visible — the merge commit marks exactly where the branch was integrated
- **Pros:**
    - Full history preserved with branch context
    - Easy to revert an entire feature: `git revert -m 1 <merge-commit>`
    - Original SHAs intact — links to branch commits never break
    - `git log --merges` shows all integration points
- **Cons:**
    - Cluttered history with merge commits between every PR
    - Hard to `git bisect` when merge commits are involved
    - `git log` without `--graph` is confusing (interleaved commits from multiple branches)
    - Non-linear history is harder for tools to parse

### Squash and Merge

Takes all commits from the feature branch and **squashes** them into a **single commit** on main. The PR title typically becomes the commit message.

```text
feature:  C ─ D ─ E    (3 commits)
                ↓ squash
main:     A ─ B ─ S    (1 commit, S = squashed C+D+E)
```

- **History:** Linear (one commit per PR)
- **Original SHAs:** Lost — all branch commits are discarded, replaced by one new commit
- **Merge event:** No — just a single commit, no visual merge point
- **Pros:**
    - Clean, linear history — one commit per logical change
    - PR title becomes the commit message — only enforce PR title format
    - Easy to `git bisect` (each commit is one PR's worth of change)
    - Good for messy branches with WIP/fixup commits
- **Cons:**
    - **Loses individual commit detail** — can't go back to specific changes within a PR
    - Author attribution may be lost (shows merger, not individual committers via co-authored-by)
    - Can't cherry-pick individual changes from a squashed PR
    - Large PRs become one giant commit — hard to review in `git log`

### Rebase and Merge (What This Project Uses)

Takes each commit from the feature branch and **replays** them one at a time on top of main's tip. Produces a linear history where every commit is preserved.

```text
feature:  C ─ D ─ E           (on top of B)
                  ↓ rebase onto main's tip
main:     A ─ B ─ C' ─ D' ─ E'  (C', D', E' are replayed copies)
```

The `'` marks indicate new SHAs — the commits are re-hashed because their parent changed.

- **History:** Linear (every commit preserved)
- **Original SHAs:** Changed — rebased commits get new hashes
- **Merge event:** No — no visual merge point in the graph
- **Pros:**
    - **Linear AND detailed** — best of both worlds
    - Individual commits preserved — can navigate to specific changes
    - Easy to `git bisect` — each commit is atomic and testable
    - Clean `git log` — no merge commit noise
    - Commit authors preserved — individual attribution maintained
    - Fine-grained CHANGELOG — tools can generate one entry per commit
- **Cons:**
    - **Original SHAs change** — links to branch commits break after rebase
    - **No merge graph** — can't see where a PR started/ended in `git log --graph`
    - Requires commit message discipline — every commit message matters
    - Force-push needed to update branch after rebase: `git push --force-with-lease`
    - Contributors must understand rebase workflow

### Comparison Summary

|                            | Merge Commit         | Squash+Merge      | Rebase+Merge              | Direct Push |
| -------------------------- | -------------------- | ----------------- | ------------------------- | ----------- |
| History shape              | Graph                | Linear            | Linear                    | Linear      |
| Commits on main per PR     | All + merge          | 1                 | All                       | All         |
| Original SHAs              | Kept                 | Lost              | Changed                   | Kept        |
| Revert entire PR           | Easy (`revert -m 1`) | Easy (one commit) | Hard (revert each commit) | N/A         |
| `git bisect`               | Awkward with merges  | Good (coarse)     | Good (fine)               | Good        |
| CHANGELOG granularity      | Per commit           | Per PR            | Per commit                | Per commit  |
| Commit message enforcement | Per commit           | PR title only     | Per commit                | Per commit  |
| Merge event visible        | Yes                  | No                | No                        | N/A         |

### Mental Model for Rebase+Merge

Think of rebase as **transplanting** your branch. Your commits are "picked up" from their original base and "replanted" on top of main's latest. The content is the same but the commit IDs change because the parent changed.

The **PR is the integration record** (review comments, approvals, design discussion). The **commit history is the technical audit trail** (what changed, in what order). Together they provide full traceability even without merge commits.

### Branching off Someone Else's Branch (The "Stacked Branch" Problem)

A common scenario: Alice creates `feature-a` off `main`. Bob needs Alice's work, so he branches `feature-b` off `feature-a`. Alice's branch eventually gets merged into `main`. Now Bob's branch has problems.

```text
main:       A ─ B ─ ─ ─ ─ ─ ─ ─ ─ (Alice's work arrives here somehow)
                 \
feature-a:        C ─ D ─ E         (Alice's branch)
                          \
feature-b:                 F ─ G    (Bob's branch, based on Alice's)
```

The **severity of the problem depends on the merge strategy** used to integrate Alice's branch into main.

#### With Merge Commits

When `feature-a` is merged into main with a merge commit:

```text
main:       A ─ B ─ ─ ─ ─ ─ M      (M = merge commit, parents: B and E)
                 \         /
feature-a:        C ─ D ─ E
                          \
feature-b:                 F ─ G
```

**Problem:** Mild. Commits C, D, E still exist with their **original SHAs**. Bob's branch is based on E, which is still reachable from main (through the merge). When Bob opens a PR for `feature-b`, git sees that C, D, E are already in main (via M), so the PR diff only shows F and G. **This usually works fine.**

**Potential issue:** If Bob rebases `feature-b` onto `main`, git may get confused about which commits are already applied. The merge commit's two-parent structure can cause unexpected conflicts during rebase.

**Solution:**

```bash
# Bob rebases onto main, skipping Alice's already-merged commits
git checkout feature-b
git rebase --onto main feature-a    # "move F,G from feature-a base to main base"
```

The `--onto` flag says: "take the commits that are on `feature-b` but NOT on `feature-a`, and replay them on top of `main`."

#### With Squash+Merge

When `feature-a` is squash-merged into main:

```text
main:       A ─ B ─ S              (S = squashed C+D+E into one commit, NEW SHA)
                 \
feature-a:        C ─ D ─ E        (these commits are now abandoned)
                          \
feature-b:                 F ─ G   (still based on E, which is NOT on main)
```

**Problem:** Serious. The squash created a **brand-new commit S** with a different SHA than C, D, or E. Git does NOT know that S contains the same changes as C+D+E. From git's perspective, commits C, D, E are **not on main** — only S is. So when Bob tries to rebase or merge `feature-b` onto main:

1. Git tries to replay C, D, E, F, G on top of S
2. C, D, E conflict with S (same changes, different commits)
3. Bob has to manually resolve conflicts for work that's already merged

This is the **most dangerous** strategy for stacked branches.

**Solutions:**

```bash
# Option 1: rebase --onto (skip Alice's commits entirely)
git checkout feature-b
git rebase --onto main feature-a
# This says: "replay only F,G (not C,D,E) onto main"

# Option 2: Interactive rebase — drop Alice's commits manually
git checkout feature-b
git rebase -i main
# In the editor, DELETE the lines for commits C, D, E
# Keep only F and G
```

**Prevention:** When you know squash+merge is the strategy, avoid branching off other people's branches. Instead, wait for their PR to be merged, then branch off `main`.

#### With Rebase+Merge

When `feature-a` is rebase-merged into main:

```text
main:       A ─ B ─ C' ─ D' ─ E'    (C', D', E' = rebased copies, NEW SHAs)
                 \
feature-a:        C ─ D ─ E          (original SHAs, now orphaned)
                          \
feature-b:                 F ─ G     (based on E, not E')
```

**Problem:** Moderate. Similar to squash but less severe. The commits C', D', E' on main have **different SHAs** than the originals C, D, E. Git doesn't know they're the same changes. When Bob rebases `feature-b` onto main, git will try to replay C, D, E, F, G and conflict on the duplicated commits.

However, git is often **smarter about this than with squash** because the individual commit patches are identical (same diff, same message). Git's `rebase` command has a built-in mechanism (`--reapply-cherry-picks=false`, which is the default) that can detect "this patch is already applied" and skip it automatically. So sometimes it **just works** — but not always, especially if there were conflict resolutions during the original rebase.

**Solutions:**

```bash
# Option 1: rebase --onto (most reliable)
git checkout feature-b
git rebase --onto main feature-a
# Replays only F,G onto main, skipping C,D,E entirely

# Option 2: Plain rebase (often works due to patch-id detection)
git checkout feature-b
git rebase main
# Git may auto-skip C,D,E if it detects matching patches
# But if there were conflicts in the original rebase, this may fail

# Option 3: If plain rebase gives conflicts, abort and use --onto
git rebase --abort
git rebase --onto main feature-a
```

#### Summary: Stacked Branch Risk by Strategy

| Strategy         | Risk level | Why                                                                         | Best fix                                             |
| ---------------- | ---------- | --------------------------------------------------------------------------- | ---------------------------------------------------- |
| **Merge commit** | Low        | Original SHAs preserved, git knows they're on main                          | `git rebase --onto main feature-a` if needed         |
| **Squash+merge** | High       | All original commits replaced with one new SHA, git can't detect duplicates | `git rebase --onto main feature-a` (mandatory)       |
| **Rebase+merge** | Medium     | New SHAs but identical patches — git can often auto-detect                  | `git rebase main` (try first), fall back to `--onto` |

#### The Universal Fix: `git rebase --onto`

No matter the merge strategy, `git rebase --onto` is the universal fix for stacked branches:

```bash
git rebase --onto <new-base> <old-base> [<branch>]
```

Read it as: "Take commits that are on `<branch>` but NOT on `<old-base>`, and replay them onto `<new-base>`."

```bash
# The pattern is always:
git checkout feature-b
git rebase --onto main feature-a

# Which means:
# "Take commits on feature-b that aren't on feature-a (= F, G)
#  and replay them onto main"
```

**Tip:** If you've already deleted the `feature-a` branch and can't reference it, you can use the SHA of the commit where `feature-b` diverged:

```bash
# Find where feature-b branched off feature-a
git log --oneline feature-b
# Identify commit E (last of Alice's commits)
git rebase --onto main <SHA-of-E> feature-b
```

#### Prevention Strategies

1. **Don't stack** unless necessary — wait for the base PR to merge, then branch off `main`
2. **Communicate** — if you must stack, tell the base branch author so they don't force-push or rebase without warning
3. **Use `--onto` proactively** — as soon as the base branch is merged, immediately rebase your branch with `--onto main`
4. **Keep stacked branches small** — the fewer commits, the easier to resolve conflicts
5. **Consider draft PRs** — open your stacked PR as draft, noting it depends on the base PR

---

## Git Configuration

Git configuration controls how git behaves — from your identity (name/email) to merging strategies, line endings, and diff tools. Understanding the config system is essential because many git defaults are suboptimal and can cause subtle issues (e.g., merge commits when you wanted a linear history, or CRLF corruption on cross-platform projects).

### What Git Configs Are

Git configs are key-value pairs stored in plain-text INI-style files. They control virtually every aspect of git's behavior. You interact with them via `git config`:

```bash
# Read a value
git config user.name

# Set a value (global scope)
git config --global user.name "Your Name"

# List all configs and their sources
git config --list --show-origin
```

### The Three Scopes

Git reads configuration from three levels, each overriding the previous:

| Scope      | File Location                                                                  | Applies To            | Use For                                                          |
| ---------- | ------------------------------------------------------------------------------ | --------------------- | ---------------------------------------------------------------- |
| **system** | `/etc/gitconfig` (Linux/macOS), `C:\Program Files\Git\etc\gitconfig` (Windows) | Every user on machine | Machine-wide defaults (usually set by installers, rarely by you) |
| **global** | `~/.gitconfig` or `~/.config/git/config`                                       | All your repositories | Personal preferences: identity, editor, aliases, merge tools     |
| **local**  | `.git/config` inside a repository                                              | This repository only  | Project-specific overrides: email for work repos, hooks path     |

**Precedence:** local > global > system. A local setting always wins.

```bash
# Set at each scope
git config --system core.autocrlf true   # All users on this machine
git config --global user.email "me@example.com"   # All your repos
git config --local  commit.template .gitmessage.txt  # This repo only
```

### How to View Your Configuration

```bash
# See everything with file sources
git config --list --show-origin

# See only global settings
git config --list --global

# See only local (repo-specific) settings
git config --list --local

# Check where a specific value comes from
git config --show-origin user.email
```

### Common Configuration Categories

#### Identity (Required)

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Every commit records the author name and email. Without these, git will guess from your OS username and hostname — usually wrong. Use `--local` to override per-repo (e.g., work email for work projects).

#### Editor and Pager

```bash
git config --global core.editor "code --wait"   # VS Code
git config --global core.pager "delta"           # Syntax-highlighted diffs
```

`core.editor` is used for commit messages, interactive rebase, etc. `core.pager` controls how git output is displayed (diff, log). `delta` is a popular upgrade over the default `less`.

#### Line Endings (Cross-Platform)

```bash
# Windows: convert CRLF to LF on commit, LF to CRLF on checkout
git config --global core.autocrlf true

# macOS/Linux: convert CRLF to LF on commit, leave LF on checkout
git config --global core.autocrlf input
```

Line ending mismatches are a common source of phantom diffs on cross-platform teams. The `core.autocrlf` setting normalizes them. For finer control, use a `.gitattributes` file in the repo root.

#### Pull Behavior

```bash
git config --global pull.rebase true    # Rebase instead of merge on pull
git config --global pull.ff only        # Only fast-forward, refuse merge commits
```

By default, `git pull` creates merge commits when your local branch has diverged from the remote. `pull.rebase true` gives you a clean linear history by replaying your local commits on top of the upstream changes.

#### Push Behavior

```bash
git config --global push.default current           # Push current branch to same-named remote
git config --global push.autoSetupRemote true       # Auto-set upstream on first push (Git 2.37+)
git config --global push.followTags true            # Push annotated tags automatically
```

`push.autoSetupRemote` eliminates the need for `git push --set-upstream origin <branch>` on first push.

#### Fetch and Cleanup

```bash
git config --global fetch.prune true        # Remove stale remote-tracking refs on fetch
git config --global fetch.prunetags true    # Remove stale remote tags on fetch
```

Without `fetch.prune`, deleted remote branches linger as stale tracking refs forever.

#### Merge and Rebase

```bash
git config --global merge.conflictstyle zdiff3   # 3-way diff with common ancestor (Git 2.35+)
git config --global rebase.autostash true         # Auto-stash dirty worktree before rebase
git config --global rebase.autoSquash true        # Honor fixup!/squash! prefixes in interactive rebase
git config --global rerere.enabled true           # Remember merge conflict resolutions
```

`zdiff3` shows the common ancestor in conflict markers, making it much easier to understand what changed where. `rerere` (REuse REcorded Resolution) replays previous conflict resolutions automatically — a huge time saver when repeatedly rebasing.

#### Commit Signing

```bash
git config --global commit.gpgsign true    # Sign every commit
git config --global tag.gpgsign true       # Sign every tag
git config --global gpg.format ssh         # Use SSH keys instead of GPG
git config --global user.signingkey ~/.ssh/id_ed25519.pub
```

Signed commits show a "Verified" badge on GitHub. SSH signing (Git 2.34+) is simpler than GPG — you can reuse your existing SSH key.

### Why Configure Git?

| Problem                                          | Config fix                   |
| ------------------------------------------------ | ---------------------------- |
| Accidental merge commits on pull                 | `pull.rebase true`           |
| CRLF/LF diffs everywhere on Windows              | `core.autocrlf true`         |
| "Please tell me who you are" error               | `user.name` + `user.email`   |
| Stale remote branches cluttering `git branch -r` | `fetch.prune true`           |
| `--set-upstream` on every first push             | `push.autoSetupRemote true`  |
| Merge conflicts hard to understand               | `merge.conflictstyle zdiff3` |
| Dirty worktree blocks rebase                     | `rebase.autostash true`      |
| Repeating the same conflict resolution           | `rerere.enabled true`        |

### Global vs Local — When to Use Which

**Use global** for personal preferences that apply everywhere:

- `user.name`, `user.email` (personal identity)
- `core.editor`, `core.pager`
- `pull.rebase`, `push.autoSetupRemote`
- `merge.conflictstyle`, `rebase.autostash`

**Use local** for project-specific overrides:

- `user.email` (different email for work repos)
- `commit.template` (project-specific commit message template)
- `core.hooksPath` (project-specific hooks)
- `core.filemode false` (Windows repos with Unix permission issues)
- `merge.ff` (project-specific merge strategy)

**Use system** rarely — it's for machine-wide defaults set by admins. Most developers never touch system config.

### Characteristics and Gotchas

1. **Configs are hierarchical** — local overrides global overrides system. A repo can always override your global preferences.
2. **Configs persist** — once set, they stay until you explicitly unset them (`git config --unset <key>`).
3. **Some configs require minimum git versions** — `push.autoSetupRemote` needs Git 2.37+, `merge.conflictstyle zdiff3` needs Git 2.35+, `rebase.updateRefs` needs Git 2.38+.
4. **Configs don't travel with repos** — global/system configs are machine-specific. Use a dotfiles repo or setup script to sync across machines.
5. **`.gitattributes` > `core.autocrlf`** — for line endings, `.gitattributes` in the repo is more reliable than per-machine config because it travels with the repo.
6. **Conditional includes** — Git supports `[includeIf]` to load different configs based on directory, remote URL, or branch. Useful for different identities per org:

    ```ini
    # In ~/.gitconfig
    [includeIf "gitdir:~/work/"]
        path = ~/.gitconfig-work

    # In ~/.gitconfig-work
    [user]
        email = you@company.com
    ```

7. **Inspect with `--show-origin`** — when a config value is unexpected, `git config --show-origin <key>` tells you exactly which file is setting it.

### Recommended Starter Configuration

A solid global config for most developers:

```bash
# Identity
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Editor
git config --global core.editor "code --wait"

# Pull/push behavior
git config --global pull.rebase true
git config --global push.default current
git config --global push.autoSetupRemote true

# Cleanup
git config --global fetch.prune true
git config --global fetch.prunetags true

# Merge/rebase improvements
git config --global merge.conflictstyle zdiff3
git config --global rebase.autostash true
git config --global rebase.autoSquash true
git config --global rerere.enabled true

# Branch sorting
git config --global branch.sort -committerdate
```

### This Project's Configuration

This project uses `git_doctor.py --export-config` to generate a full reference of all git configs with their current values, scopes, and recommendations. Run it to see what's configured and what's missing.

### VS Code settings.json vs .gitconfig

VS Code has its own git settings in `settings.json` that control **VS Code's git behavior** (autofetch interval, confirm sync, default clone directory, etc.). These are **not** the same as git config and they do **not** write to `.gitconfig`.

**They are separate systems:**

| Setting                 | Where it lives              | What reads it                                                  |
| ----------------------- | --------------------------- | -------------------------------------------------------------- |
| `git.autofetch`         | VS Code `settings.json`     | VS Code only                                                   |
| `fetch.prune`           | `.gitconfig` (global/local) | All git clients (terminal, CI, editors)                        |
| `git.pullRebase`        | VS Code `settings.json`     | VS Code only (overrides `pull.rebase` for VS Code pull button) |
| `pull.rebase`           | `.gitconfig` (global/local) | All git clients                                                |
| `git.enableSmartCommit` | VS Code `settings.json`     | VS Code only (no git equivalent)                               |

**Key facts:**

- A change in `settings.json` does **NOT** reflect in `.gitconfig` or vice versa
- Some VS Code settings overlap with git config and can **override** it for VS Code operations only
- `terminal.integrated.env.*` in `settings.json` can affect git behavior in the integrated terminal (e.g. setting `GIT_AUTHOR_EMAIL`)
- VS Code reads your `.gitconfig` for identity, signing, and other git-level settings

**Recommendation:** Set behavior in `.gitconfig` (via `git config --global`), and use `settings.json` only for VS Code-specific UI preferences. That way your git behavior is consistent regardless of which tool you use (terminal, CI, other editors).

Common VS Code git settings (these go in `settings.json`, NOT `.gitconfig`):

```json
{
    "git.autofetch": true,
    "git.fetchOnPull": true,
    "git.pruneOnFetch": true,
    "git.confirmSync": false,
    "git.enableSmartCommit": true,
    "git.suggestSmartCommit": false,
    "git.openRepositoryInParentFolders": "always"
}
```

---

## Git Tags

### What Are Tags?

Tags are **named pointers to specific commits** in git. They're like bookmarks — a human-readable label permanently attached to a point in history.

```text
main:  A ─ B ─ C ─ D ─ E ─ F
                   ↑           ↑
                v0.1.0      v1.0.0
```

Tags don't move. Unlike branches (which advance with each new commit), a tag stays put.

### Types of Tags

| Type            | Command                                | What it stores                                                             | Use case                             |
| --------------- | -------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------ |
| **Lightweight** | `git tag v1.0.0`                       | Just a pointer to a commit (like a branch that never moves)                | Quick labels, local markers          |
| **Annotated**   | `git tag -a v1.0.0 -m "Release 1.0.0"` | Full git object: tagger name, email, date, message, optional GPG signature | Releases (preferred for public tags) |

### Where Do Tags Live?

| Location   | Path                                                     | How to see                       |
| ---------- | -------------------------------------------------------- | -------------------------------- |
| **Local**  | `.git/refs/tags/` (one file per tag, containing the SHA) | `git tag` or `git tag -l "v1.*"` |
| **Remote** | `refs/tags/` on the remote server                        | `git ls-remote --tags origin`    |

**Important:** Tags are **NOT pushed by default.** You must explicitly push them:

```bash
git push origin v1.0.0          # Push a specific tag
git push origin --tags          # Push ALL local tags
```

### Common Tag Operations

```bash
# List all tags
git tag

# List tags matching a pattern
git tag -l "v1.*"

# Create a lightweight tag
git tag v1.0.0

# Create an annotated tag (preferred for releases)
git tag -a v1.0.0 -m "Release 1.0.0"

# Tag a specific commit (not HEAD)
git tag -a v1.0.0 abc1234 -m "Release 1.0.0"

# Show tag details
git show v1.0.0

# Delete a local tag
git tag -d v1.0.0

# Delete a remote tag
git push origin :refs/tags/v1.0.0
# or
git push origin --delete v1.0.0

# See what commit a tag points to
git rev-parse v1.0.0
```

### How Tags Are Used in This Project

- **release-please** creates annotated tags (e.g., `v1.2.0`) when the Release PR is merged
- **hatch-vcs** reads the latest tag to derive the Python package version at build time
- **release.yml** triggers on `push: tags: v*.*.*` — building and publishing on tag creation
- **Convention:** Tags use the `v` prefix (e.g., `v1.0.0`) per SemVer convention

### Tags vs Branches

|              | Tags                                      | Branches                            |
| ------------ | ----------------------------------------- | ----------------------------------- |
| Moves?       | No — fixed to one commit                  | Yes — advances with each new commit |
| Purpose      | Mark a point in time (release, milestone) | Track ongoing work                  |
| Storage      | `.git/refs/tags/`                         | `.git/refs/heads/`                  |
| Auto-pushed? | No — must explicitly push                 | Yes — with `git push`               |

---

## Commit Traceability and PR Linkage

With rebase+merge, individual commits lose their branch context — there's no merge commit to mark where a PR started and ended. This raises the question: **how do you trace a commit back to the PR and discussion that produced it?**

### Option A: Let GitHub Handle It Automatically (Recommended)

GitHub's rebase+merge automatically appends `(#PR)` to each commit's subject line when you merge via the web UI. No configuration needed.

**The flow:**

1. You write locally: `feat: add user authentication`
2. You push your branch and open PR #42
3. When you click "Rebase and merge" on GitHub, each commit becomes: `feat: add user authentication (#42)`
4. release-please reads commits on `main` and generates CHANGELOG entries with the `(#42)` link
5. In the rendered CHANGELOG on GitHub, `#42` is automatically a clickable link to the PR

**What the CHANGELOG looks like:**

```markdown
### Features

- add user authentication (#42)
- add login CLI command (#42)
- add password hashing utility (#43)
```

Each `(#42)` links to the full PR with review comments, approvals, and design discussion.

**Why this works well:**

- Zero friction — you don't think about it locally, the linkage just appears on `main`
- Commitizen already accepts the `(#PR)` suffix — the commit-msg hook won't reject these
- The PR number is always correct (GitHub appends it, not a human)
- Works with every PR, no exceptions

**Important:** This only happens when you merge **via the GitHub UI** (or API). If you push directly to `main` or use `git rebase` locally and push, there's no PR to reference.

### Option B: Require Issue References in Commit Messages

If you want commits to reference an **issue** (not just the PR), you can enforce a pattern in the commit body. This is useful when you want traceability to requirements/tickets, not just PRs.

**Example commit with issue reference:**

```text
feat: add user authentication

Refs: #15
```

Or using GitHub's closing keywords:

```text
fix: correct token expiration calculation

Fixes #28
```

**How to enforce this with commitizen:**

You can customize the commitizen schema in `pyproject.toml` to require a footer. However, commitizen's built-in `cz_conventional_commits` schema prompts for an optional footer during `cz commit` — it just doesn't **require** it.

To strictly enforce issue references, you'd need a custom commitizen plugin or a CI check:

```yaml
# In commit-lint.yml — add a step after the cz check:
- name: Check for issue references
  run: |
      # Check that every feat/fix commit has a "Refs:" or "Fixes" footer
      git log --format="%H %s%n%b---" origin/${{ github.base_ref }}..HEAD | \
      awk '
        /^[a-f0-9]+ (feat|fix)/ { needs_ref=1; sha=$1; subject=$0 }
        /Refs:|Fixes|Closes|Resolves/ { needs_ref=0 }
        /^---$/ { if (needs_ref) print "Missing issue ref: " subject; needs_ref=0 }
      '
```

**Trade-offs:**

- More friction — developers must know the issue number before committing
- Not all commits map neatly to one issue
- PR linkage (Option A) is already automatic and often sufficient
- Useful for projects with strict requirements traceability (e.g., regulated industries)

### Combining Both Options

You can use both: GitHub auto-appends `(#PR)` and you optionally include `Refs: #issue` in the body. The commit on `main` would look like:

```text
feat: add user authentication (#42)

Refs: #15
```

This gives three layers of traceability:

1. **Commit message** — what changed and why
2. **`(#42)`** — links to the PR (review, discussion, approval)
3. **`Refs: #15`** — links to the issue (requirements, user story, bug report)

### Configuring GitHub's Auto-Append Behavior

GitHub's `(#PR)` append behavior is controlled at the repository level:

**Settings → General → Pull Requests → "Pull Request default commit message"**

For each merge strategy, you can choose what GitHub puts in the default commit message:

- **Default message** — uses the commit message as-is, appends `(#PR)`
- **Pull request title** — uses the PR title as the commit subject
- **Pull request title and description** — uses the PR title and body

For rebase+merge specifically, GitHub preserves each individual commit message and appends `(#PR)` to the subject line. This behavior is built-in for rebase+merge and cannot be disabled — the `(#PR)` is always appended.

---

## Programming Jargon

Common programming and development terminology, including informal terms you'll encounter in open-source projects, code reviews, and technical discussions.

### General Development Jargon

| Term                               | Meaning                                                                                                                                                                    | Example usage                                                                     |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Landing** / **Landing a branch** | Getting your changes merged into the main branch. "Landed" = "merged and now on main."                                                                                     | "I landed my feature branch" = "my PR was merged"                                 |
| **Landing on main**                | Same as above — emphasizes that the changes arrived at their destination.                                                                                                  | "Once this lands on main, we can release"                                         |
| **Ship it**                        | Approve and merge/deploy. Implies confidence that it's ready.                                                                                                              | "LGTM, ship it" (in a PR review)                                                  |
| **LGTM**                           | "Looks Good To Me" — approval shorthand in code reviews.                                                                                                                   | Comment on a PR: "LGTM"                                                           |
| **Nit**                            | A nitpick — minor style or preference feedback, not a blocker.                                                                                                             | "nit: prefer `snake_case` here"                                                   |
| **Bikeshedding**                   | Spending disproportionate time on trivial decisions (color of the bikeshed).                                                                                               | "Let's not bikeshed the variable name — either is fine"                           |
| **Yak shaving**                    | A series of nested tasks you must complete before doing the original task.                                                                                                 | "I needed to fix the linter to fix the import to fix the test to add the feature" |
| **Rubber ducking**                 | Explaining a problem out loud (even to an inanimate object) to understand it better.                                                                                       | "I rubber-ducked it and realized the bug was in the loop"                         |
| **Dogfooding**                     | Using your own product internally before releasing to users.                                                                                                               | "We're dogfooding the new API before v2 launch"                                   |
| **Greenfield**                     | A brand-new project with no existing code or constraints.                                                                                                                  | "This is a greenfield project — no legacy to worry about"                         |
| **Brownfield**                     | Working within an existing codebase with established patterns and constraints.                                                                                             | "It's a brownfield project — we have to work around the existing schema"          |
| **Tech debt**                      | Shortcuts or suboptimal code that works now but will cost more to maintain later.                                                                                          | "We're accruing tech debt by skipping tests"                                      |
| **Foot gun**                       | A feature or API that makes it easy to accidentally cause problems.                                                                                                        | "`eval()` is a foot gun — too easy to introduce security vulnerabilities"         |
| **Escape hatch**                   | A way to bypass normal rules or abstractions when you need to.                                                                                                             | "`--no-verify` is the escape hatch for pre-commit hooks"                          |
| **Happy path**                     | The expected, error-free flow through code.                                                                                                                                | "The happy path works, but we need to handle edge cases"                          |
| **Sad path**                       | Error or failure scenarios.                                                                                                                                                | "What happens on the sad path — when the API is down?"                            |
| **Blast radius**                   | How much is affected if something goes wrong.                                                                                                                              | "The blast radius of this change is small — only affects the CLI"                 |
| **Upstream** / **Downstream**      | Upstream = the original source you forked from or depend on. Downstream = consumers of your code.                                                                          | "We need to submit the fix upstream"                                              |
| **Vendoring**                      | Copying a dependency's source code directly into your project instead of installing it.                                                                                    | "We vendored the library to avoid the pip dependency"                             |
| **Shim**                           | A thin adapter layer that translates between two interfaces.                                                                                                               | "We added a shim to support both the old and new API"                             |
| **Tombstone**                      | Code or data that's been logically deleted but physically retained (marked as dead).                                                                                       | "The method is a tombstone — it exists but is never called"                       |
| **DX**                             | Developer Experience — how easy, pleasant, and efficient it is for developers to work with a tool, project, or codebase. The developer-facing equivalent of UX.            | "Good error messages and fast CI improve DX"                                      |
| **UX**                             | User Experience — how easy, pleasant, and efficient a product is to use from the end user's perspective. Covers usability, accessibility, and overall satisfaction.        | "The UX of this CLI is confusing — too many flags"                                |
| **GHCR**                           | GitHub Container Registry — GitHub's built-in container image registry at `ghcr.io`. Stores OCI/Docker container images alongside your source code. Free for public repos. | "The container-build workflow pushes images to GHCR"                              |

### Git-Specific Jargon

| Term                          | Meaning                                                                                              | Example usage                                                  |
| ----------------------------- | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **Trunk**                     | The main development branch (`main` or `master`). From "trunk-based development."                    | "We develop on trunk — no long-lived feature branches"         |
| **HEAD**                      | The current commit your working directory is on. Usually the tip of a branch.                        | "HEAD is at abc1234"                                           |
| **Detached HEAD**             | When HEAD points to a specific commit, not a branch. Commits here aren't on any branch.              | "git checkout v1.0.0 puts you in detached HEAD state"          |
| **Fast-forward**              | When a branch can be moved forward without creating a merge commit (no divergence).                  | "Pull with `--ff-only` to ensure a clean fast-forward"         |
| **Force-push**                | Overwriting remote history. Dangerous on shared branches, normal after rebase.                       | "After rebasing, force-push with `--force-with-lease`"         |
| **Cherry-pick**               | Applying a single commit from one branch onto another.                                               | "Cherry-pick the hotfix onto the release branch"               |
| **Stash**                     | Temporarily shelving uncommitted changes.                                                            | "Stash your changes, switch branches, then pop them back"      |
| **Reflog**                    | Git's safety net — a log of every HEAD position change, even after resets or rebases.                | "I lost my commit but found it in `git reflog`"                |
| **Porcelain** vs **Plumbing** | Porcelain = user-friendly git commands (`git log`). Plumbing = low-level internals (`git cat-file`). | "For scripts, use plumbing commands — they have stable output" |

---

## GitHub Copilot Instructions File

### What is `.github/copilot-instructions.md`?

A Markdown file that GitHub Copilot reads **on every interaction** when
working in a repository. It acts as a persistent briefing — project
conventions, tool choices, file layout, review priorities, and things to
ignore. Copilot treats its contents as soft rules: it follows them by
default but the user can override with explicit instructions.

The file lives at `.github/copilot-instructions.md` (this is the
convention that VS Code / GitHub Copilot looks for automatically).

### Why It Matters

Without this file, Copilot starts every conversation from scratch — it has
to rediscover your project structure, conventions, and tooling by reading
source files. With it, Copilot arrives pre-briefed and:

- Generates code that matches your conventions (imports, naming, type hints)
- Knows which tools to run and how (Hatch, pytest, Ruff, mypy)
- Avoids suggesting patterns you've already decided against
- Keeps documentation, workflows, and config in sync
- Understands your project layout without exploring every directory

Think of it like onboarding documentation, but for your AI pair programmer.

### How Big Should It Be?

This is the most important practical question. Copilot loads the entire
file into its context window on every interaction. That context window is
shared with: your current file, open files, conversation history, and any
files Copilot reads during the session. A bloated instructions file crowds
out the actual code Copilot needs to reason about.

| Range             | Verdict                         | Notes                                                                                                                          |
| ----------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **< 100 lines**   | Too thin                        | Likely missing key conventions. Copilot will guess at things you'd rather it know.                                             |
| **100–300 lines** | Good starting point             | Covers project overview, conventions, review priorities, and key files. Good for small-to-medium projects.                     |
| **300–500 lines** | Sweet spot for complex projects | Room for workflow tables, commit format, tool inventories, and architecture pointers. This boilerplate sits here (~350 lines). |
| **500–800 lines** | Caution zone                    | Still workable if every section pulls its weight. Audit quarterly — remove anything that duplicates what's in dedicated docs.  |
| **800+ lines**    | Diminishing returns             | Context window pressure becomes real. Copilot may miss instructions buried in the noise. Split detail into referenced docs.    |

**Rule of thumb:** If you can't skim the whole file in 2 minutes, it's
too long. Prefer linking out to detailed docs (ADRs, architecture.md,
tool-decisions.md) rather than inlining everything.

### Recommended Layout

A well-structured instructions file follows this general pattern:

```markdown
# Copilot Instructions

Guidelines for GitHub Copilot when working in this repository.

<!-- TODO (template users): Customise this file for your project. -->

---

## How This Project Works ← What the project IS

### Overview (1-2 paragraphs)

### Build & Environment (how to build/run)

### Key Configuration Files (table of important files)

### CI/CD (workflow summary if relevant)

## Working Style ← How Copilot should BEHAVE

### Keep Related Files in Sync (cross-reference rules)

### Leave TODOs for Template Users (if template repo)

### Provide Feedback and Pushback (don't be a yes-machine)

### Session Recap (end-of-session summary format)

## Review Priorities ← What to WATCH FOR

### High Priority (type hints, tests, security)

### Medium Priority (docstrings, error handling)

### Low Priority (comments, style)

### General Guidance (minimal diffs, don't churn)

## Conventions ← Project RULES

### Language (imports, naming, style)

### Project Structure (where things go)

### Git & PRs (commit format, branch rules)

## Ignore / Don't Flag ← What to SKIP

                                    (disabled rules, generated files)

## Architecture & Design Refs ← Where to find DEPTH

                                    (links to ADRs, architecture.md, etc.)

## Common Issues to Catch ← Known PITFALLS

                                    (src/ layout, mutable defaults, etc.)
```

**Key principles:**

1. **Lead with context** — "How This Project Works" goes first because
   Copilot needs to understand the project before it can follow rules.

2. **Behaviour before rules** — "Working Style" (how to act) before
   "Conventions" (what to enforce). Copilot's collaboration style
   matters more than import order.

3. **Reference, don't duplicate** — Link to `architecture.md`,
   `tool-decisions.md`, and ADRs for detailed reasoning. Keep this file
   as a summary layer.

4. **End with escape hatches** — "Ignore / Don't Flag" and "Common Issues"
   are quick-reference sections that prevent false positives.

### What to Include vs. Link Out

The goal is **fast orientation**, not exhaustive documentation.

| Include in instructions file              | Link out to separate docs                     |
| ----------------------------------------- | --------------------------------------------- |
| Project overview (2-3 sentences)          | Full architecture (architecture.md)           |
| Tool names and how to run them            | Tool comparison reasoning (tool-decisions.md) |
| Convention summary (1-2 lines each)       | Detailed ADRs (docs/adr/)                     |
| Workflow table (name + trigger + purpose) | Individual workflow files                     |
| Commit message format                     | Full contributing guide                       |
| What to ignore (disabled rules)           | Ruff/mypy full config (pyproject.toml)        |

### Maintenance

The instructions file is only useful if it's accurate. Stale instructions
are worse than no instructions — they actively mislead Copilot.

**Keep it current by treating it like code:**

- Update it in the same PR that changes what it describes
- Include it in review checklists ("does this change affect copilot-instructions?")
- Consider adding a Copilot meta-instruction: "If a change affects how
  Copilot should work, update this file as part of the same change"
  (this boilerplate does exactly this)

**Signs it needs a trim:**

- Sections that repeat what's in other docs verbatim
- Tool details for tools you removed months ago
- Rules that Ruff/mypy already enforce automatically
- Overly detailed workflow descriptions (the YAML is the source of truth)

### This Project's Instructions File

This boilerplate's `.github/copilot-instructions.md` is ~350 lines and
covers:

| Section                    | Purpose                                | ~Lines |
| -------------------------- | -------------------------------------- | ------ |
| How This Project Works     | Build, hooks, workflows, config        | ~130   |
| Working Style              | TODOs, sync, pushback, recaps          | ~70    |
| Review Priorities          | What to check at high/med/low priority | ~30    |
| Conventions                | Python, project structure, git, CI     | ~50    |
| Ignore / Don't Flag        | Disabled rules, generated files        | ~10    |
| Architecture & Design Refs | Links to deep docs + ADR table         | ~40    |
| Common Issues              | Known pitfalls                         | ~10    |

It sits comfortably in the 300–500 sweet spot for a project of this
complexity. The heaviest section is "How This Project Works" — which is
justifiable because this project has 24 workflows, 30+ pre-commit hooks,
and multiple environments. For simpler projects, that section could be
much shorter.

---

## Standard Streams — stdout, stderr, and stdin

Every process on Unix/Windows has three standard I/O streams, opened
automatically by the OS before `main()` runs:

| Stream     | File Descriptor | Python Object | Default Destination | Purpose                                      |
| ---------- | --------------- | ------------- | ------------------- | -------------------------------------------- |
| **stdin**  | 0               | `sys.stdin`   | Keyboard / pipe     | Input data (interactive prompts, piped data) |
| **stdout** | 1               | `sys.stdout`  | Terminal / pipe     | Normal program output (results, reports)     |
| **stderr** | 2               | `sys.stderr`  | Terminal / pipe     | Errors, warnings, diagnostics                |

### Why Two Output Streams?

The separation exists so that **data** (stdout) can be piped to another
program while **diagnostics** (stderr) still reach the human watching
the terminal. Example:

```bash
# stdout → file, stderr → terminal
python scripts/check_todos.py --json > results.json
# The JSON report goes to the file; errors/warnings still print on screen.

# Both streams explicitly
python scripts/clean.py 2>errors.log 1>output.log
```

If everything went to one stream, you couldn't reliably separate a
program's useful output from its error messages.

### How Python Maps to the Streams

#### `print()` → stdout (fd 1)

```python
print("Hello")                    # writes to sys.stdout
print("Error!", file=sys.stderr)  # explicitly writes to stderr
```

`print()` defaults to `sys.stdout`. This is what downstream consumers
(pipes, Task runner, CI log parsers) treat as "the program's output."

#### `logging` module → stderr (fd 2)

```python
import logging
logging.basicConfig(format="%(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

log.info("Processing...")   # → stderr
log.warning("Slow query")  # → stderr
log.error("Failed!")        # → stderr
```

Python's `logging` module sends **all levels** to stderr by default
(via `StreamHandler(sys.stderr)`). This is correct for library code
and daemons, but it causes problems for CLI scripts that also need
to produce human-readable status output.

#### `input()` → stdin (fd 0) + stdout

```python
answer = input("Continue? [y/N] ")  # reads from stdin, prompt on stdout
```

When stdin is a pipe (not a terminal), `input()` reads from the pipe
without showing a prompt. Scripts should check `sys.stdin.isatty()`
before using interactive prompts.

### The Problem: stderr + PowerShell + Task Runner

This project discovered the issue firsthand. Here's what happens:

1. A Python script uses `log.info("✓ All checks passed")` — this goes to **stderr**
2. The script exits with code 1 (e.g. "TODOs found")
3. **PowerShell** sees data on stderr from a process with non-zero exit → wraps every
   stderr line in a red `NativeCommandError` block
4. **Task runner** pipes both streams through its own buffering, sometimes interleaving them

Result: garbled, duplicated, red-wrapped output that looks broken even though the
script is working correctly.

#### The Fix

Split output by intent:

| What                    | Stream | Python API                      | Why                                               |
| ----------------------- | ------ | ------------------------------- | ------------------------------------------------- |
| Human status reports    | stdout | `print()`                       | Passes cleanly through pipes, Task, PowerShell    |
| Errors and warnings     | stderr | `log.error()` / `log.warning()` | Goes to stderr where it belongs                   |
| Machine-readable output | stdout | `print(json.dumps())`           | Consumers expect data on stdout                   |
| Debug/diagnostic info   | stderr | `log.debug()`                   | Hidden unless `--verbose`, doesn't pollute stdout |

```python
# Before (broken on PowerShell):
log.info("  ✓ No TODOs found")              # stderr → NativeCommandError

# After (clean):
if not args.quiet:
    print("  ✓ No TODOs found")             # stdout → passes through cleanly

log.error("  ✗ File not found: %s", path)   # stderr → correct: this IS an error
```

The `--quiet` flag still works: instead of relying on `logging.WARNING` level
to suppress `log.info()`, the script checks `if not args.quiet` before calling
`print()`.

### stdin: Interactive vs Piped

Scripts should behave differently when stdin is a terminal vs a pipe:

```python
import sys

if sys.stdin.isatty():
    # Interactive: ask for confirmation
    answer = input("Delete 47 files? [y/N] ")
    if answer.lower() != "y":
        sys.exit(0)
else:
    # Piped: assume non-interactive, require --yes flag
    if not args.yes:
        print("Error: --yes required in non-interactive mode", file=sys.stderr)
        sys.exit(1)
```

This pattern appears in `scripts/clean.py` for the `--include-venv` confirmation.

### Stream Encoding and Unicode

Each stream has an encoding (`sys.stdout.encoding`). On modern Linux/macOS,
it's almost always UTF-8. On Windows, it depends:

| Terminal         | Default Encoding | Unicode Safe?    |
| ---------------- | ---------------- | ---------------- |
| Windows Terminal | UTF-8            | Yes              |
| PowerShell 7     | UTF-8            | Yes              |
| PowerShell 5.1   | Often CP1252     | No — ✓ → garbled |
| cmd.exe          | CP437/CP1252     | No               |
| VS Code terminal | UTF-8            | Yes              |
| GitHub Actions   | UTF-8            | Yes              |

This is why the project has `_colors.supports_unicode()` — it checks
`sys.stdout.encoding` (with a `locale.getpreferredencoding()` fallback)
and returns True only for UTF-8/16/32. Scripts use it to choose between
Unicode decorations (`✓`, `─`, `═`) and ASCII fallbacks (`OK`, `-`, `=`).

### Redirection Cheat Sheet

```bash
# Redirect stdout to file
command > output.txt

# Redirect stderr to file
command 2> errors.txt

# Redirect both to same file
command > all.txt 2>&1

# Pipe stdout only (stderr still goes to terminal)
command | grep "pattern"

# Pipe both streams
command 2>&1 | grep "pattern"

# Discard stderr
command 2>/dev/null

# Discard stdout, keep stderr
command > /dev/null
```

In PowerShell, the syntax differs:

```powershell
# Redirect stdout
command > output.txt

# Redirect stderr (PowerShell 7+)
command 2> errors.txt

# Redirect all streams
command *> all.txt

# Pipe (PowerShell pipes objects, not byte streams)
command | Select-String "pattern"
```

### Key Takeaways

1. **stdout = data**, **stderr = diagnostics**. Don't mix them.
2. Python's `logging` module sends everything to stderr. For CLI scripts
   that produce human-readable reports, use `print()` for the report and
   `logging` for errors/warnings.
3. Always check encoding before using Unicode symbols on Windows.
   Use `supports_unicode()` from `_colors.py`, not hardcoded `✓`.
4. When your script might be piped, check `sys.stdin.isatty()` and
   `sys.stdout.isatty()` to adjust behavior (skip prompts, skip color,
   skip progress bars).
5. PowerShell wraps stderr in error records when exit code is non-zero.
   This is a PowerShell behavior, not a Python bug — but you need to
   design around it for scripts that run through task runners.

---

## Resources

### Python Packaging

- [Python Packaging User Guide](https://packaging.python.org/)
- [Hynek's Testing & Packaging](https://hynek.me/articles/testing-packaging/)
- [Real Python: Python Packaging](https://realpython.com/pypi-publish-python-package/)
- [PyPA Sample Project](https://github.com/pypa/sampleproject)
- [PEP 621 – Project metadata in pyproject.toml](https://peps.python.org/pep-0621/)

### Testing & Quality

- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Hypothesis (property-based testing)](https://hypothesis.readthedocs.io/)

### Linting & Formatting

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [pre-commit](https://pre-commit.com/)

### CI/CD & GitHub Actions

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)

### Project Templates & Best Practices

- [Hypermodern Python](https://cjolowicz.github.io/posts/hypermodern-python-01-setup/)
- [Scientific Python Library Development Guide](https://learn.scientific-python.org/development/)
- [The Hitchhiker's Guide to Python](https://docs.python-guide.org/)

### Security

- [pip-audit](https://github.com/pypa/pip-audit)
- [Bandit](https://bandit.readthedocs.io/)
- [OpenSSF Scorecard](https://securityscorecards.dev/)

---

## VS Code Settings — Hierarchy, Files, and Best Practices

VS Code has a layered settings system. Understanding which file controls what — and
which one wins when they conflict — is essential for keeping a project consistent
without fighting contributors' personal preferences.

### The Settings Hierarchy

Settings are evaluated bottom-to-top. **Lower layers override higher layers:**

```text
┌────────────────────────────────────────────────────┐
│  1. Default Settings (built into VS Code)          │  ← Lowest priority
├────────────────────────────────────────────────────┤
│  2. User Settings (settings.json)                  │
├────────────────────────────────────────────────────┤
│  3. Remote Settings (SSH, WSL, container)          │
├────────────────────────────────────────────────────┤
│  4. Workspace Settings (.code-workspace)           │
├────────────────────────────────────────────────────┤
│  5. Folder Settings (.vscode/settings.json)        │  ← Highest priority
└────────────────────────────────────────────────────┘
```

If the same setting is defined at multiple levels, the most specific one wins. For
example, if User Settings sets `editor.tabSize` to 4 and Folder Settings sets it to 2,
VS Code uses 2 when editing files in that folder.

### The Settings Files

#### 1. Default Settings (read-only)

Every VS Code setting has a built-in default. You can view them all with:
`Ctrl+Shift+P` → `Preferences: Open Default Settings (JSON)`

You never edit these — they're the baseline that everything else overrides.

#### 2. User Settings — `settings.json`

| Aspect       | Detail                                                                                                                                                     |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Location** | Windows: `%APPDATA%\Code\User\settings.json` · macOS: `~/Library/Application Support/Code/User/settings.json` · Linux: `~/.config/Code/User/settings.json` |
| **Scope**    | Applies to **every** VS Code window, every project, every workspace                                                                                        |
| **Commit?**  | **No** — this is personal to your machine                                                                                                                  |
| **Open it**  | `Ctrl+Shift+P` → `Preferences: Open User Settings (JSON)`                                                                                                  |

**What belongs here:**

- Personal editor preferences: font, theme, colour scheme, keybindings
- Global extension config that you want everywhere (e.g., spell checker language,
  GitLens AI model, Error Lens settings, Copilot toggle)
- Default formatters and editor behaviour you prefer across all projects
- Extension-specific API keys or tokens (though secrets should ideally go in
  environment variables, not settings files)

**What does NOT belong here:**

- Project-specific tool configs (ruff, mypy, pytest settings)
- Formatter choices that should be shared with the team
- File exclusions specific to one project

**Example — personal preferences only:**

```jsonc
{
    "workbench.colorTheme": "Monokai Dimmed",
    "editor.fontSize": 14,
    "editor.cursorSurroundingLines": 2,
    "editor.renderWhitespace": "all",
    "gitlens.ai.model": "vscode",
    "gitlens.ai.vscode.model": "copilot:gpt-4.1",
    "errorLens.enabled": true,
    "cSpell.language": "en",
}
```

#### 3. Workspace Settings — `*.code-workspace`

| Aspect       | Detail                                                                       |
| ------------ | ---------------------------------------------------------------------------- |
| **Location** | Repo root (e.g., `my-project.code-workspace`)                                |
| **Scope**    | Applies when you open the workspace file (`File → Open Workspace from File`) |
| **Commit?**  | **Yes** — this is the team's shared baseline                                 |
| **Open it**  | `Ctrl+Shift+P` → `Preferences: Open Workspace Settings (JSON)`               |

A `.code-workspace` file is a JSON file with three top-level keys:

```jsonc
{
    "folders": [{ "path": "." }],       // Which folders are in the workspace
    "settings": { ... },                // Shared editor settings
    "extensions": {                     // Recommended extensions
        "recommendations": [ ... ]
    }
}
```

**What belongs here:**

- Shared formatter and language settings the team should agree on
  (`[python].editor.defaultFormatter`, `[markdown].editor.formatOnSave`, etc.)
- File exclusions for project-specific generated/cache directories
- Editor rulers matching project line-length conventions
- Extension recommendations so new contributors get prompted to install them
- Extension-specific settings that affect code quality consistency (indent rainbow
  colours, markdownlint config path, etc.)

**What does NOT belong here:**

- Personal preferences (theme, font size, keybindings)
- Machine-specific paths (absolute interpreter paths don't work across machines)
- Secrets or tokens

**Key gotcha:** `${workspaceFolder}` doesn't reliably resolve in `.code-workspace`
files. Use relative paths instead, or let extensions auto-discover (e.g., the Python
extension finds `.venv` automatically).

#### 4. Folder Settings — `.vscode/settings.json`

| Aspect       | Detail                                                      |
| ------------ | ----------------------------------------------------------- |
| **Location** | `.vscode/settings.json` inside the project folder           |
| **Scope**    | Applies to files in that specific folder only               |
| **Commit?**  | **It depends** — see below                                  |
| **Open it**  | `Ctrl+Shift+P` → `Preferences: Open Folder Settings (JSON)` |

This is the **highest priority** settings file. It overrides everything above it.

**When to commit `.vscode/settings.json`:**

- When your project doesn't use a `.code-workspace` file and you need shared settings
- When you need machine-specific overrides that the workspace file can't handle
  (e.g., `python.defaultInterpreterPath` with an absolute path)

**When NOT to commit it:**

- When you already have a `.code-workspace` file with shared settings (avoid
  duplication and conflicts)
- When it contains only personal preferences

**Common pattern:** `.gitignore` the entire `.vscode/` directory, then use the
`.code-workspace` file for shared settings. Or commit only specific files like
`.vscode/launch.json` (debug configs) and `.vscode/tasks.json` (build tasks)
while ignoring `.vscode/settings.json`.

### Workspace File vs Folder Settings — When to Use Which

| Scenario                                      | Use                     |
| --------------------------------------------- | ----------------------- |
| Team-shared settings for a single-root repo   | `.code-workspace` file  |
| Multi-root workspace (multiple project dirs)  | `.code-workspace` file  |
| Machine-specific overrides (interpreter path) | `.vscode/settings.json` |
| Project doesn't use a workspace file          | `.vscode/settings.json` |
| Personal preferences (not project-specific)   | User `settings.json`    |

### What Happens When Settings Conflict

When the same setting appears at multiple levels, VS Code uses the most specific one:

```text
User:      editor.tabSize = 4
Workspace: editor.tabSize = 2      ← Workspace wins when workspace is open
Folder:    editor.tabSize = 3      ← Folder wins over everything
```

This means:

- A contributor can set their personal theme in User Settings without affecting anyone
- The workspace file enforces project conventions (formatter, rulers, exclusions)
- Folder settings can override workspace settings for edge cases

### Structuring Settings Files Well

**User Settings — organize by category:**

```jsonc
{
    // ── Editor ──────────────────────────────────────
    "editor.fontSize": 14,
    "editor.renderWhitespace": "all",
    "workbench.colorTheme": "Monokai Dimmed",

    // ── Language Overrides ──────────────────────────
    "[python]": { "editor.formatOnSave": true },
    "[markdown]": { "editor.wordWrap": "on" },

    // ── Extensions ──────────────────────────────────
    "gitlens.ai.model": "vscode",
    "errorLens.enabled": true,
}
```

**Workspace file — project conventions only:**

```jsonc
{
    "folders": [{ "path": "." }],
    "settings": {
        // Language-specific formatters the team agreed on
        "[python]": {
            "editor.defaultFormatter": "charliermarsh.ruff",
            "editor.formatOnSave": true,
        },
        // Project-specific file exclusions
        "files.exclude": {
            "**/__pycache__": true,
            "**/*.egg-info": true,
        },
        // Line-length rulers matching project config
        "editor.rulers": [88, 120],
    },
    "extensions": {
        "recommendations": ["ms-python.python", "charliermarsh.ruff"],
    },
}
```

### Common Mistakes

1. **Duplicating settings across User and Workspace** — If the workspace file sets
   `[python].editor.defaultFormatter`, don't also set it in User Settings. The
   workspace wins anyway, and duplication makes it confusing to debug.

2. **Putting personal preferences in the workspace file** — Theme, font size, and
   keybindings are personal. Don't force them on the team.

3. **Absolute paths in committed files** — `python.defaultInterpreterPath` with
   `C:\Users\yourname\...` breaks on every other machine. Let the Python extension
   auto-discover, or use `.vscode/settings.json` (gitignored) for machine-local paths.

4. **Ignoring the workspace file** — If a project has a `.code-workspace` file, open
   it with `File → Open Workspace from File` (not `Open Folder`). Opening the folder
   directly skips all workspace settings and extension recommendations.

5. **Settings in the wrong scope** — A setting that only makes sense for one project
   (like `editor.rulers: [88, 120]` matching ruff's line length) belongs in the
   workspace file, not User Settings. Conversely, `editor.fontSize` is personal and
   belongs in User Settings.

### Where This Project Defines Settings

| File                                       | What it defines                                                                                   |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| `simple-python-boilerplate.code-workspace` | Shared formatter choices, file exclusions, rulers, indent rainbow colours, recommended extensions |
| User `settings.json` (your machine)        | Personal theme, font, GitLens AI model, Error Lens, Copilot, spell checker, terminal profile      |
| `.vscode/settings.json`                    | Not committed — used for machine-local overrides if needed                                        |

### Release & Versioning

- [python-semantic-release](https://python-semantic-release.readthedocs.io/)
- [release-please](https://github.com/googleapis/release-please)
- [commitizen (Python)](https://commitizen-tools.github.io/commitizen/)
- [conventional commits spec](https://www.conventionalcommits.org/)
- [git-cliff](https://git-cliff.org/)
- [towncrier](https://towncrier.readthedocs.io/)
- [bump-my-version](https://github.com/callowayproject/bump-my-version)
- [setuptools-scm](https://setuptools-scm.readthedocs.io/)
- [hatch-vcs](https://github.com/ofek/hatch-vcs)
- [changesets](https://github.com/changesets/changesets)
- [auto (Intuit)](https://intuit.github.io/auto/)
- [release-drafter](https://github.com/release-drafter/release-drafter)
- [Keep a Changelog](https://keepachangelog.com/)
- [SemVer spec](https://semver.org/)
- [CalVer](https://calver.org/)
- [PEP 440 – Version Identification](https://peps.python.org/pep-0440/)
