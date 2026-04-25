# Troubleshooting & FAQ

Common problems, error messages, and their solutions. If you're stuck,
check here before opening an issue.

<!-- TODO (template users): Add project-specific troubleshooting entries
     as you discover them. Remove template-specific entries that don't
     apply to your project. -->

---

## Installation & Setup

### `ModuleNotFoundError: No module named 'simple_python_boilerplate'`

**Cause:** The package isn't installed. The `src/` layout intentionally
prevents direct imports without installation.

**Fix:**

```bash
# Using Hatch (recommended)
hatch shell

# Or manual install
pip install -e .
```

The `-e` flag means "editable" — your source changes reflect immediately
without reinstalling. See [ADR 001](../adr/001-src-layout.md) for why the
`src/` layout requires this.

---

### `pip install -e .` fails with build errors

**Cause:** Usually a missing build dependency or wrong Python version.

**Fix:**

1. Check Python version: `python --version` (need 3.11+)
2. Upgrade pip: `pip install --upgrade pip`
3. Try Hatch instead: `hatch shell` (handles everything automatically)

---

### Hatch environment is stale after removing a dependency

**Cause:** Hatch doesn't auto-uninstall removed packages. If you remove a
dependency from `pyproject.toml`, the old package silently remains in the env.

**Fix:**

```bash
hatch env remove default
hatch shell  # recreates the environment from scratch
```

---

### `command not found: hatch`

**Cause:** Hatch isn't installed globally or isn't on your PATH.

**Fix:**

```bash
# Install globally (recommended)
pip install hatch

# Or use pipx for isolation
pipx install hatch

# Verify
hatch --version
```

---

### `command not found: task`

**Cause:** Task runner (go-task) isn't installed.

**Fix:**

See [Task installation docs](https://taskfile.dev/installation/). On macOS:
`brew install go-task`. On Windows: `choco install go-task` or
`scoop install task`.

Task is optional — every `task <name>` command has a `hatch run` equivalent
documented in the [Taskfile.yml](../../Taskfile.yml).

---

## Pre-commit Hooks

### Pre-commit hooks aren't running

**Cause:** Hooks aren't installed in your local git repo.

**Fix:**

```bash
pre-commit install                              # pre-commit stage
pre-commit install --hook-type commit-msg        # commit-msg stage
pre-commit install --hook-type pre-push          # pre-push stage
```

All three stages need to be installed separately. See
[ADR 008](../adr/008-pre-commit-hooks.md) for the full hook inventory.

---

### `deptry` hook fails with import errors

**Cause:** `deptry` needs access to your installed packages (unlike most hooks
that run in pre-commit's isolated environment). It runs as a `local`/`system`
hook via `hatch run deptry .`.

**Fix:**

1. Make sure you're in the Hatch environment: `hatch shell`
2. Run manually to see the full error: `hatch run deptry .`
3. If packages are missing, recreate the env: `hatch env remove default && hatch shell`

---

### Hook fails on first run / downloads slowly

**Cause:** Pre-commit downloads and caches hook environments on first use.
This is normal.

**Fix:** Wait for the download. Subsequent runs are fast (cached). To
pre-download all hooks: `pre-commit install-hooks`.

---

### `check-shebang-scripts-are-executable` fails

**Cause:** A script has a shebang (`#!/usr/bin/env python3`) but isn't
marked as executable in git.

**Fix:**

```bash
git add --chmod=+x scripts/my_script.py
```

---

### Prettier hook "Failed" but says "files were modified by this hook"

**Cause:** This is **expected behavior**, not a real error. Prettier is a
_formatter_, not a _linter_. When pre-commit runs it:

1. Prettier reads each Markdown file and reformats it in place
2. If any file changed, pre-commit reports the hook as **Failed**
3. The modified files now contain the correct formatting

**Fix:**

```bash
# Stage the reformatted files and commit again
git add -A
git commit -m "style: format markdown with prettier"

# Or review changes first
git diff                  # See what Prettier changed
git add -p                # Stage selectively
```

This "fail-and-fix" pattern is how all formatter hooks work in pre-commit
(Ruff format, Black, Prettier). The "failure" means "I fixed something —
re-stage and retry." See [ADR 033](../adr/033-prettier-for-markdown-formatting.md).

---

### Prettier reformats a file I don't want changed

**Cause:** Prettier applies to all Markdown files by default. Some files
(generated content, copied templates) may have intentional formatting.

**Fix:** Add a `.prettierignore` file at the repo root, or use
`<!-- prettier-ignore -->` comments for specific blocks:

```markdown
<!-- prettier-ignore-start -->
This    content    won't   be   reformatted.
<!-- prettier-ignore-end -->
```

---

### Hook runs but reports "no files to check" / skipped

**Cause:** The hook's file filter doesn't match any staged files. For
example, the `mypy` hook only runs on `.py` files — if you only changed
Markdown, mypy is skipped.

**Fix:** No fix needed — this is correct behavior. Hooks use file type
filters to avoid running on irrelevant changes. Check `.pre-commit-config.yaml`
for each hook's `types:` or `files:` filter.

---

## Git & Commits

### Commit rejected: "commit message does not match pattern"

**Cause:** The `commit-msg` hook (commitizen) validates that your message
follows Conventional Commits format.

**Fix:** Use the correct format:

```text
<type>(<scope>): <description>

# Examples:
feat(cli): add verbose flag
fix: handle empty input gracefully
docs: update installation guide
chore: bump ruff to 0.15.1
```

Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
`build`, `ci`, `chore`, `revert`.

Or use the interactive helper: `task commit` (runs `cz commit`).

---

### Push rejected: tests fail in pre-push hook

**Cause:** The pre-push hook runs `pytest` and `pip-audit`. If tests fail
or vulnerabilities are found, the push is blocked.

**Fix:**

1. Run tests locally: `hatch run test:run` or `task test`
2. Fix failures
3. Push again

To bypass in emergencies (not recommended): `git push --no-verify`.

---

## CI/CD & GitHub Actions

### Workflows don't run on my fork

**Cause:** Repository guards disable all workflows by default on forks and
clones. This is intentional — see
[ADR 011](../adr/011-repository-guard-pattern.md).

**Fix (pick one):**

| Method           | How                                                                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------------ |
| **Script**       | `python scripts/customize.py --enable-workflows myorg/myrepo`                                          |
| **Global**       | Set repo variable `ENABLE_WORKFLOWS = 'true'` (Settings → Secrets and variables → Actions → Variables) |
| **Per-workflow** | Set `ENABLE_<NAME> = 'true'` (e.g. `ENABLE_TEST`)                                                      |
| **Edit YAML**    | Replace `YOURNAME/YOURREPO` with your repo slug in each file                                           |

---

### CI gate times out / stays pending

**Cause:** A required check name was changed (workflow job renamed) but
`REQUIRED_CHECKS` in `ci-gate.yml` still references the old name.

**Fix:**

1. Check which checks are missing: look at the PR's Checks tab
2. Update `REQUIRED_CHECKS` in `.github/workflows/ci-gate.yml`
3. Verify: `grep -r 'ci-gate: required' .github/workflows/`

---

### "Resource not accessible by integration" error

**Cause:** The workflow's `permissions:` block doesn't include the needed
permission.

**Fix:** Add the required permission to the workflow. Common ones:

```yaml
permissions:
  contents: read          # Read repo contents (default)
  contents: write         # Push commits, create releases
  pull-requests: write    # Comment on PRs, approve
  issues: write           # Label, comment on issues
  packages: write         # Push container images
```

---

### Path-filtered workflow doesn't run on my PR

**Cause:** The PR doesn't change files matching the workflow's path filter.
This is expected behavior — e.g., `bandit.yml` only runs when Python source
files change.

**Fix:** No fix needed. These workflows also run on `push` to `main` and on
schedules, so nothing slips through permanently.

---

### Dependabot PRs fail CI

**Cause:** Dependabot can't access repository secrets, which may be needed
by some workflows.

**Fix:** The `auto-merge-dependabot.yml` workflow handles this — it auto-
approves and merges minor/patch updates after CI passes. For major version
bumps, review manually.

---

## Testing

### Tests pass locally but fail in CI

**Cause:** Common reasons:

- Different Python version (CI runs 3.11, 3.12, 3.13)
- Missing editable install (CI does `pip install -e ".[test]"`)
- Platform-specific behavior (CI runs Ubuntu)
- Stale cached dependencies

**Fix:**

1. Run the full matrix locally: `hatch run test:run` (tests all Python versions)
2. Check the CI log for the specific Python version that failed
3. Ensure your Hatch env is fresh: `hatch env remove default && hatch shell`

---

### `pytest` can't find tests

**Cause:** Tests need to be in `tests/` and follow pytest naming conventions.

**Fix:**

- Test files: `test_*.py` or `*_test.py`
- Test functions: `def test_*()`
- Test classes: `class Test*`
- Verify pytest config in `pyproject.toml` under `[tool.pytest.ini_options]`

---

### Coverage report shows 0% / missing lines

**Cause:** Coverage is measuring the installed package, not your source files.

**Fix:** Make sure `[tool.coverage.run]` in `pyproject.toml` has
`source = ["simple_python_boilerplate"]` (not `src/simple_python_boilerplate`).
The `--cov` flag should point to the package name, not the file path.

---

## Linting & Type Checking

### Ruff reports errors that don't matter

**Cause:** Some rules may not apply to your project.

**Fix:** Disable specific rules in `pyproject.toml`:

```toml
[tool.ruff.lint]
ignore = ["E501"]  # Already disabled — line length

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]  # Allow assert in tests
```

See the [Ruff rule index](https://docs.astral.sh/ruff/rules/) to understand
each code.

---

### mypy errors on third-party libraries

**Cause:** The library doesn't ship type stubs.

**Fix:**

```toml
# In pyproject.toml
[[tool.mypy.overrides]]
module = ["some_library.*"]
ignore_missing_imports = true
```

Or install stubs: `pip install types-requests` (for requests, etc.).

---

### "The legacy server (ruff-lsp) has been deprecated"

**Cause:** Your VS Code **User Settings** contain `ruff.lint.run` (or other
settings from the old `ruff-lsp` language server). The Ruff extension now uses
a native server and those settings are no longer recognized.

**Fix:**

1. Open VS Code User Settings: `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"
2. Search for `ruff.lint.run` and remove it
3. Also remove any other `ruff.lint.*` VS Code settings (not to be confused with
   `[tool.ruff.lint]` in `pyproject.toml` — those are fine)
4. Reload VS Code

The Ruff extension reads linting/formatting config from `pyproject.toml`
automatically. VS Code-side `ruff.lint.*` settings are legacy and should
be removed.

See the [Ruff extension migration guide](https://github.com/astral-sh/ruff-vscode/blob/main/README.md#migrating-from-ruff-lsp)
for full details.

---

## Documentation

### `mkdocs build` fails with link warnings

**Cause:** MkDocs in `--strict` mode flags broken internal links. Links to
files outside `docs/` (like `pyproject.toml`) are expected to produce INFO
messages — these are downgraded via the `validation:` config in `mkdocs.yml`.

**Fix:**

- For broken doc-to-doc links: fix the relative path
- For repo-file links (pyproject.toml, workflows): these work on GitHub but
  MkDocs can't resolve them — this is expected
- Check the full output for actual `ERROR` lines vs. `INFO` messages

---

### API docs show "Module not found"

**Cause:** `mkdocstrings` can't find your package. Usually means it's not
installed in the docs environment.

**Fix:**

```bash
# Use the docs environment (includes mkdocstrings + your package)
hatch run docs:build

# Don't use raw mkdocs commands — they won't have your package
```

---

## Containers

### Container build fails

**Cause:** Common reasons:

- `Containerfile` references files not in the build context
- Build arg or Python version mismatch
- Network issues downloading packages

**Fix:**

1. Build locally to see errors: `docker build -f Containerfile .`
2. Check the stage that fails in the multi-stage build
3. Ensure all `COPY` paths exist relative to the repo root

---

### Container image is too large

**Cause:** The multi-stage build should produce a ~150 MB image. If it's
larger, dev dependencies may be leaking into the runtime stage.

**Fix:** Check that the final `FROM` stage in `Containerfile` only copies
the built package, not the full build environment. The runtime stage should
not have `pip install -e ".[dev]"`.

---

## Miscellaneous

### `_typos.toml` — typos flags a valid word

**Cause:** The typos spellchecker doesn't know the word.

**Fix:** Add it to `_typos.toml`:

```toml
[default.extend-words]
# Word = "Word" keeps the original casing
MySacronym = "MySacronym"
```

---

### Scripts fail on Windows with "permission denied"

**Cause:** Windows doesn't use Unix file permissions the same way.

**Fix:**

- Use `python scripts/my_script.py` instead of `./scripts/my_script.py`
- Or ensure Git is configured to handle line endings:
  `git config core.autocrlf true`

---

## Python Environment & Virtual Environments

### `python` command not found / opens the wrong version

**Cause:** Multiple Python installations, or Python isn't on your PATH.

**Fix:**

```bash
# Check what's available
python --version
python3 --version
py --version          # Windows Python launcher

# If wrong version, be explicit
python3.12 -m venv .venv

# On Windows, use the py launcher to pick a version
py -3.12 -m venv .venv
```

On macOS/Linux, `python` may point to Python 2. Always use `python3` or
set up a shell alias.

---

### `pip install` puts packages in the wrong place / globally

**Cause:** You're not in a virtual environment. Bare `pip install` installs
globally, which pollutes your system Python.

**Fix:**

```bash
# Always use Hatch (recommended)
hatch shell

# Or manually activate your venv first
source .venv/bin/activate     # macOS/Linux
.venv\Scripts\activate        # Windows

# Verify you're in a venv
which python                  # should show the venv path
pip --version                 # should show the venv site-packages
```

Rule of thumb: if `which python` shows `/usr/bin/python` or a system path,
you're NOT in a venv. Activate one first.

---

### `pip install` fails with "externally managed environment" (PEP 668)

**Cause:** Recent Linux distros (Ubuntu 23.04+, Fedora 38+) and macOS with
Homebrew Python block `pip install` outside a virtual environment to prevent
breaking system packages.

**Fix:**

```bash
# Use Hatch (handles venvs for you)
hatch shell

# Or create a venv manually
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Or use pipx for standalone CLI tools
pipx install hatch
```

Never use `--break-system-packages` unless you know exactly what you're doing.

---

### Virtual environment won't activate / "running scripts is disabled" (Windows)

**Cause:** PowerShell's default execution policy blocks `.ps1` activation
scripts.

**Fix:**

```powershell
# Allow scripts for the current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
.venv\Scripts\activate
```

Or use `hatch shell` which doesn't require activating scripts manually.

---

### Multiple Python versions — which one is Hatch using?

**Cause:** Hatch picks a Python version based on `requires-python` in
`pyproject.toml` and what's available on your system.

**Fix:**

```bash
# Check which Python Hatch is using
hatch env show

# Force a specific version
hatch env create --python 3.12

# See all available Pythons
hatch python show
```

---

### `venv` vs `virtualenv` vs Hatch — which should I use?

| Tool                 | When to use                                                     |
| -------------------- | --------------------------------------------------------------- |
| **Hatch**            | Default for this project — manages envs, scripts, and builds    |
| **`python -m venv`** | Quick one-off venv when Hatch isn't available                   |
| **`virtualenv`**     | Slightly faster venv creation, more options — but rarely needed |
| **conda**            | If you need non-Python dependencies (C libraries, etc.)         |

For this project: use `hatch shell`. It reads `pyproject.toml` and sets
everything up — correct Python version, all dependencies, editable install.

---

## pip & Package Management

### `pip install` is slow

**Cause:** pip resolves dependencies sequentially and downloads from PyPI.

**Fix:**

```bash
# Use Hatch (caches aggressively)
hatch shell

# Or use uv as a drop-in pip replacement (10-100x faster)
pip install uv
uv pip install -e .

# Or use pip's cache explicitly
pip install --cache-dir ~/.pip-cache -e .
```

---

### `pip install` shows "Could not find a version that satisfies the requirement"

**Cause:** Common reasons:

- Typo in package name
- Package doesn't exist on PyPI (private package, wrong name)
- Python version incompatible (package doesn't support your Python)
- Network/firewall blocking PyPI

**Fix:**

```bash
# Check the correct package name on pypi.org
pip index versions some-package

# Check your Python version
python --version

# Try with verbose output to see what's happening
pip install -v some-package
```

---

### `pip install` fails with "No matching distribution found"

**Cause:** The package doesn't have a wheel (pre-built binary) for your
platform/Python version. Needs to compile from source but build tools
are missing.

**Fix:**

```bash
# On Ubuntu/Debian
sudo apt install python3-dev build-essential

# On macOS
xcode-select --install

# On Windows — install Visual Studio Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

---

### Dependency conflicts: "X requires Y, but you have Z"

**Cause:** Two packages need incompatible versions of the same dependency.

**Fix:**

```bash
# See the conflict details
pip check

# Visualize the dependency tree
pip install pipdeptree
pipdeptree

# Or with Hatch
hatch run pip check
hatch run pipdeptree    # if [extras] includes pipdeptree
```

Often the fix is to relax version constraints or update the conflicting
package. Check both packages' release notes for compatible version combos.

---

### ImportError after `pip install` — "cannot import name X from Y"

**Cause:** Common reasons:

- Package installed but the import name differs from the pip name
  (e.g., `pip install Pillow` but `import PIL`)
- Wrong environment — installed in one venv, running in another
- Stale `.pyc` cache files
- Circular imports in your own code

**Fix:**

```bash
# Check where the package actually is
python -c "import some_module; print(some_module.__file__)"

# Clear bytecode cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Or use the clean script
python scripts/clean.py
```

---

## Git Workflows

### "fatal: not a git repository"

**Cause:** You're not inside a git repo, or `.git/` is missing.

**Fix:**

```bash
# Initialize if starting fresh
git init

# Or check you're in the right directory
pwd
ls -la .git
```

---

### Merge conflicts — how to resolve

**Fix:**

```bash
# 1. See which files conflict
git status

# 2. Open conflicting files — look for conflict markers:
#    <<<<<<< HEAD
#    your changes
#    =======
#    their changes
#    >>>>>>> branch-name

# 3. Edit the file to keep what you want (remove all marker lines)

# 4. Mark resolved and commit
git add <resolved-file>
git commit
```

Tips:

- Use VS Code's built-in merge editor (it highlights and offers buttons)
- For complex merges: `git mergetool` opens a visual diff
- To abort a merge entirely: `git merge --abort`

---

### Accidentally committed to `main` instead of a branch

**Fix:**

```bash
# Create a new branch with your commits
git branch my-feature

# Reset main to where it should be (before your commits)
git reset --hard origin/main

# Switch to your feature branch
git checkout my-feature
```

---

### How to undo the last commit (keep changes)

**Fix:**

```bash
# Undo last commit, keep files staged
git reset --soft HEAD~1

# Undo last commit, unstage files but keep changes
git reset HEAD~1

# Undo last commit AND discard all changes (DANGEROUS)
git reset --hard HEAD~1
```

---

### "Your branch is behind origin/main by N commits"

**Fix:**

```bash
# Rebase your branch onto latest main (preferred for this project)
git fetch origin
git rebase origin/main

# Or merge main into your branch
git merge origin/main
```

This project uses rebase merge strategy for PRs
([ADR 022](../adr/022-rebase-merge-strategy.md)), so rebase is preferred
for keeping history linear.

---

### `.gitignore` isn't ignoring a file

**Cause:** The file was already tracked before adding the `.gitignore` rule.
`.gitignore` only prevents tracking _new_ files — it doesn't untrack
existing ones.

**Fix:**

```bash
# Stop tracking the file (keeps local copy)
git rm --cached path/to/file

# For a directory
git rm -r --cached path/to/directory/

# Then commit the removal
git commit -m "chore: stop tracking ignored file"
```

---

### Large file accidentally committed / repo bloated

**Fix:**

```bash
# Remove from current commit (if not pushed yet)
git reset HEAD~1
# Remove the file, add to .gitignore, recommit

# If already pushed — rewrite history (coordinate with team)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/large-file" \
  --prune-empty -- --all
```

For persistent large-file problems, consider
[git-filter-repo](https://github.com/newren/git-filter-repo) (faster than
`filter-branch`) or [Git LFS](https://git-lfs.com/) for legitimate large
files.

---

## VS Code Integration

### Python interpreter not detected / wrong interpreter

**Cause:** VS Code doesn't know about your Hatch-managed environment.

**Fix:**

1. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Type "Python: Select Interpreter"
3. Choose the Hatch environment, or enter the path manually:

```bash
# Find Hatch's Python path
hatch env find default
```

---

### Pylance/IntelliSense not working for project imports

**Cause:** Pylance can't find the package because it's not installed
in the selected interpreter's environment.

**Fix:**

1. Select the correct Python interpreter (see above)
2. Make sure the package is installed: `hatch shell` then check `pip list`
3. If using `src/` layout, ensure Pylance has `"python.analysis.extraPaths": ["src"]` in `.vscode/settings.json` (but editable install is better)

---

### VS Code terminal doesn't activate the venv automatically

**Fix:** Add to `.vscode/settings.json`:

```json
{
    "python.terminal.activateEnvironment": true,
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
}
```

Or just use `hatch shell` in the terminal — it sets up the environment
regardless of VS Code settings.

---

### Tests not showing in the Test Explorer

**Cause:** VS Code's test discovery is misconfigured.

**Fix:** In `.vscode/settings.json`:

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "python.testing.unittestEnabled": false
}
```

Then click the refresh button in the Testing sidebar.

---

### Extensions fighting each other (Ruff vs Pylint vs Black)

**Cause:** Multiple linting/formatting extensions enabled at once.

**Fix:** This project uses Ruff for both linting and formatting. Disable
these if installed:

- Pylint extension (Ruff covers this)
- Black formatter (Ruff's formatter replaces it)
- autopep8 (Ruff replaces it)
- isort (Ruff handles import sorting)

Keep: Ruff extension, Pylance (for IntelliSense/type checking).

---

## Dependencies & Security

### `pip-audit` reports a vulnerability — what do I do?

**Fix:**

1. Check the advisory: `pip-audit` shows the CVE link
2. If a fix exists: update the package in `pyproject.toml`
3. If no fix exists yet: check if you're actually affected
   (not all vulnerabilities are exploitable in every context)
4. Document exceptions in your security process

```bash
# Run audit with details
pip-audit --desc

# Update the vulnerable package
pip install --upgrade vulnerable-package
# Then update pyproject.toml to match
```

---

### Dependabot opened too many PRs at once

**Cause:** Dependabot's default schedule may create many PRs if deps are
outdated.

**Fix:** Limit concurrent PRs in `.github/dependabot.yml`:

```yaml
updates:
    - package-ecosystem: pip
      open-pull-requests-limit: 5 # Max concurrent PRs
```

The `auto-merge-dependabot.yml` workflow helps by auto-merging minor/patch
updates so the queue clears faster.

---

### How to update all dependencies at once

**Fix:**

```bash
# See current versions vs latest
task deps:versions
# or
python scripts/dep_versions.py

# Update a specific package
pip install --upgrade ruff

# Regenerate pinned requirements files
task deps:regenerate
# or trigger the regenerate-files.yml workflow manually
```

Don't forget to test after updating: `task test` or `hatch run test:run`.

---

### deptry says a dependency is unused but I'm using it

**Cause:** deptry analyzes static imports. If you use a package only at
runtime (entry points, plugins, test fixtures) or through dynamic imports,
deptry may not detect it.

**Fix:** Mark it as a known false positive in `pyproject.toml`:

```toml
[tool.deptry.per_rule_ignores]
DEP002 = ["package-name"]  # Used as a runtime plugin / entry point
```

---

## Performance & Build

### `hatch run` is slow on first invocation

**Cause:** Hatch creates the virtual environment and installs dependencies
on first run. Subsequent runs reuse the cached environment.

**Fix:** No fix needed — this is a one-time cost. To force a rebuild:
`hatch env remove default && hatch shell`.

---

### `pre-commit` is slow

**Cause:** Running 38 hooks takes time, especially on first run (downloads
environments) or on large changesets.

**Fix:**

```bash
# Only run on staged files (default behavior)
git add <files>
git commit

# Skip slow hooks during rapid iteration (not recommended for final commit)
SKIP=pytest,pip-audit git commit -m "wip: quick save"

# Pre-download all hook environments
pre-commit install-hooks

# Run only specific hooks
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

---

### Build produces `.tar.gz` but I expected a `.whl`

**Cause:** You ran `python -m build` which creates both sdist (`.tar.gz`)
and wheel (`.whl`).

**Fix:** Both are correct. Use the wheel for installation:

```bash
# Build both
python -m build

# Build only wheel
python -m build --wheel

# Or use Hatch
hatch build
```

---

## GitHub-Specific Issues

### Branch protection blocks my push to `main`

**Cause:** Branch protection is working as intended — direct pushes to
`main` are blocked. Use PRs instead.

**Fix:**

1. Create a feature branch: `git checkout -b feat/my-change`
2. Push the branch: `git push origin feat/my-change`
3. Open a PR on GitHub
4. Wait for CI checks to pass
5. Merge via the GitHub UI

---

### PR checks are pending forever

**Cause:** Common reasons:

- CI gate waiting for a check that never runs (name mismatch)
- GitHub Actions queue is backed up
- Workflow file has a syntax error
- Repository guard is blocking the workflow

**Fix:**

1. Click "Details" on the pending check to see its status
2. If "Queued" — wait, or check [GitHub Status](https://www.githubstatus.com/)
3. If "Skipped" — the repository guard is blocking it (see [enabling workflows](../USING_THIS_TEMPLATE.md#enabling-workflows))
4. If never appears — check that the workflow file exists and triggers on PRs

---

### Actions minutes are running out

**Cause:** Public repos get unlimited Actions minutes. Private repos have
a monthly quota depending on your GitHub plan.

**Fix:**

- Consider making the repo public if appropriate
- Reduce workflow runs: use path filters, reduce matrix dimensions
- Use concurrency groups (already configured) to cancel duplicate runs
- Disable non-essential scheduled workflows (e.g., `stale.yml`,
  `link-checker.yml`)

---

### GitHub Pages shows 404 after deploy

**Cause:** Pages isn't configured to use GitHub Actions as the source.

**Fix:**

1. Go to Settings → Pages
2. Under "Build and deployment", set Source to **GitHub Actions**
3. Trigger the `docs-deploy.yml` workflow (push to main, or manual dispatch)
4. Wait 1-2 minutes for the deployment to propagate

---

### Codecov shows "no coverage data"

**Cause:** The Codecov token isn't configured, or coverage files aren't
being uploaded.

**Fix:**

1. Sign up at [codecov.io](https://codecov.io/) and add your repo
2. Copy your upload token
3. Add it as a repository secret: `CODECOV_TOKEN`
4. The `coverage.yml` workflow uploads automatically on each run

For public repos, Codecov may work without a token, but a token is
recommended for reliability.

---

## Debugging Tips

### How to debug a failing test

**Fix:**

```bash
# Run a single test with verbose output
pytest tests/unit/test_engine.py::test_my_function -v

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run with full traceback
pytest --tb=long

# Run only failing tests from last run
pytest --lf
```

---

### How to debug a type error from mypy

**Fix:**

```bash
# Run mypy on a single file
mypy src/simple_python_boilerplate/engine.py

# Show error codes (useful for ignoring specific errors)
mypy --show-error-codes src/

# Reveal the inferred type of an expression
# Add this to your code temporarily:
reveal_type(my_variable)  # mypy will print the inferred type
```

Common mypy fixes:

- `# type: ignore[error-code]` — suppress a specific error on one line
- `assert x is not None` — narrow a type from `Optional[X]` to `X`
- `cast(MyType, value)` — tell mypy the type when it can't infer it

---

### How to see what Ruff would fix without changing files

**Fix:**

```bash
# Check without fixing
ruff check .

# Show what would be fixed
ruff check --diff .

# Fix automatically
ruff check --fix .

# Format without changing files (just check)
ruff format --check .

# Show format diff
ruff format --diff .
```

---

### How to run a single pre-commit hook

**Fix:**

```bash
# Run one hook on all files
pre-commit run ruff --all-files
pre-commit run mypy --all-files

# Run one hook on staged files only
pre-commit run ruff

# Run all hooks on a specific file
pre-commit run --files src/simple_python_boilerplate/engine.py

# List all installed hooks
pre-commit run --all-files --list-hooks
```

---

### How to check what Python packages are installed

**Fix:**

```bash
# In your environment (Hatch or venv)
pip list

# See outdated packages
pip list --outdated

# See dependency tree
pipdeptree            # if installed via [extras]

# Check for conflicts
pip check

# See where packages are installed
pip show some-package
```

---

## Common Error Messages — Quick Reference

| Error                                        | Likely cause                   | Quick fix                                       |
| -------------------------------------------- | ------------------------------ | ----------------------------------------------- |
| `ModuleNotFoundError`                        | Package not installed          | `pip install -e .` or `hatch shell`             |
| `externally-managed-environment`             | PEP 668 — no global pip        | Use a venv or Hatch                             |
| `No module named 'pip'`                      | venv created without pip       | `python -m ensurepip --upgrade`                 |
| `SyntaxError: invalid syntax`                | Wrong Python version           | Check `python --version` (need 3.11+)           |
| `PermissionError`                            | File locked or no write access | Close editors using the file, check permissions |
| `FileNotFoundError: pyproject.toml`          | Wrong directory                | `cd` to the project root                        |
| `subprocess-exited-with-error`               | Build dependency missing       | Install build tools (see pip section)           |
| `FAILED tests/... AssertionError`            | Test failure                   | Read the assertion diff, fix the code           |
| `error: Skipping analyzing ...`              | mypy can't find type stubs     | Add `ignore_missing_imports` for that module    |
| `Connection refused: 127.0.0.1:8000`         | Docs server not running        | `hatch run docs:serve` first                    |
| `fatal: not a git repository`                | Not in a git repo              | `git init` or `cd` to the right directory       |
| `git push rejected (non-fast-forward)`       | Remote has commits you don't   | `git pull --rebase` first                       |
| `Your branch is up to date` but files differ | Unstaged changes               | `git add -A` then check status                  |
| `files were modified by this hook`           | Formatter hook (Prettier/Ruff) | Re-stage files and commit again                 |

---

## Taskfile & Hatch Shortcuts

### `task` commands not working / "task: not found"

**Cause:** Task runner (go-task) isn't installed, or you're not in the
project root.

**Fix:** See the [Installation & Setup](#command-not-found-task) section
above. All `task` commands wrap `hatch run` equivalents, so you can always
use `hatch run` directly if Task isn't available.

---

### `task check` fails — how to read the output

**Cause:** `task check` runs all quality gates in sequence (lint, format
check, typecheck, tests). It stops at the first failure.

**Fix:**

```bash
# Run gates individually to isolate the failure
task lint         # Ruff linting
task fmt          # Check formatting
task typecheck    # mypy
task test         # pytest

# Or auto-fix what's fixable
task lint:fix     # Auto-fix lint issues
```

---

## Still Stuck?

<!-- TODO (template users): Update the issue URLs below with your actual
     repository path after forking. -->

1. Search existing [issues](https://github.com/JoJo275/simple-python-boilerplate/issues) — someone may have hit the same problem
2. Run the diagnostic tool: `spb-doctor` or `python scripts/doctor.py`
3. Open a [new issue](https://github.com/JoJo275/simple-python-boilerplate/issues/new) with:
    - What you tried
    - Expected vs. actual behavior
    - Output of `spb-doctor`
    - Python version and OS

---

## Related Documentation

- [Dev Setup](../development/dev-setup.md) — environment setup guide
- [CI/CD Design](../design/ci-cd-design.md) — pipeline architecture and debugging
- [Using This Template](../USING_THIS_TEMPLATE.md) — first-time setup checklist
- [Tooling](../tooling.md) — what each tool does
- [ADR 008](../adr/008-pre-commit-hooks.md) — Pre-commit hook inventory
- [ADR 033](../adr/033-prettier-for-markdown-formatting.md) — Prettier for Markdown
