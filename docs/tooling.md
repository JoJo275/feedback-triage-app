# Repo Tools at a Glance

A quick reference to every tool used in this project — what it does, where
it's configured, and where to learn more.

> **Why this file exists:** Template users may not be familiar with all the
> tools bundled in this repo. This page gives a one-line explanation of each
> tool and a link to its docs so you can learn at your own pace.

---

## Build & Environments

| Tool                                               | What it does                                                                                                                                                                  | Config                                    | Docs                                                         |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------ |
| **[Hatchling](https://hatch.pypa.io/latest/)**     | Builds Python packages (sdist + wheel) from source. This is the _build backend_ — it runs when you `pip install .` or `hatch build`.                                          | `pyproject.toml` → `[build-system]`       | [Hatchling docs](https://hatch.pypa.io/latest/config/build/) |
| **[Hatch](https://hatch.pypa.io/latest/)**         | Manages virtual environments, runs scripts, and orchestrates builds. This is the _project manager_ — it creates envs, installs deps, and runs commands like `hatch run test`. | `pyproject.toml` → `[tool.hatch.*]`       | [Hatch docs](https://hatch.pypa.io/latest/)                  |
| **[hatch-vcs](https://github.com/ofek/hatch-vcs)** | Derives the package version from git tags at build time. No manual version bumping needed.                                                                                    | `pyproject.toml` → `[tool.hatch.version]` | [hatch-vcs docs](https://github.com/ofek/hatch-vcs)          |
| **[Task](https://taskfile.dev/)**                  | A task runner that wraps `hatch run` commands into shorter aliases like `task test`. Optional convenience layer.                                                              | `Taskfile.yml`                            | [Taskfile docs](https://taskfile.dev/)                       |

> **How these layers relate:** See [command-workflows.md](development/command-workflows.md)
> for a visual breakdown of `task test` → `hatch run test` → `pytest`.

---

## Code Quality

| Tool                                                            | What it does                                                                                                  | Config                             | Docs                                                             |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------- |
| **[Ruff](https://docs.astral.sh/ruff/)**                        | Lints and formats Python code. A single Rust binary that replaces flake8, isort, black, pyupgrade, and more.  | `pyproject.toml` → `[tool.ruff]`   | [Ruff docs](https://docs.astral.sh/ruff/)                        |
| **[mypy](https://mypy.readthedocs.io/)**                        | Static type checker. Catches type errors without running your code. Runs in strict mode in this project.      | `pyproject.toml` → `[tool.mypy]`   | [mypy docs](https://mypy.readthedocs.io/)                        |
| **[typos](https://github.com/crate-ci/typos)**                  | Finds spelling mistakes in source code, docs, and filenames. Rust-based, very fast.                           | `_typos.toml`                      | [typos docs](https://github.com/crate-ci/typos)                  |
| **[codespell](https://github.com/codespell-project/codespell)** | Another spellchecker that runs in CI as a safety net alongside typos.                                         | CLI args in `spellcheck.yml`       | [codespell docs](https://github.com/codespell-project/codespell) |
| **[deptry](https://deptry.com/)**                               | Checks for unused, missing, and transitive dependencies by comparing `pyproject.toml` against actual imports. | `pyproject.toml` → `[tool.deptry]` | [deptry docs](https://deptry.com/)                               |

---

## Testing

| Tool                                                 | What it does                                                                                                                | Config                                         | Docs                                                  |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------- |
| **[pytest](https://docs.pytest.org/)**               | Test framework. Discovers and runs tests in `tests/`. Supports fixtures, parametrize, markers, and a huge plugin ecosystem. | `pyproject.toml` → `[tool.pytest.ini_options]` | [pytest docs](https://docs.pytest.org/)               |
| **[pytest-cov](https://pytest-cov.readthedocs.io/)** | Coverage plugin for pytest. Measures which lines are executed during tests and generates reports.                           | `pyproject.toml` → `[tool.coverage]`           | [pytest-cov docs](https://pytest-cov.readthedocs.io/) |

---

## Security

| Tool                                                 | What it does                                                                                                                 | Config                             | Docs                                                  |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | ----------------------------------------------------- |
| **[Bandit](https://bandit.readthedocs.io/)**         | Static security linter for Python. Finds common security issues like hardcoded passwords, `shell=True`, unsafe YAML loading. | `pyproject.toml` → `[tool.bandit]` | [Bandit docs](https://bandit.readthedocs.io/)         |
| **[pip-audit](https://github.com/pypa/pip-audit)**   | Checks installed packages against vulnerability databases (OSV, PyPI). The PyPA-maintained successor to `safety`.            | — (scans the environment)          | [pip-audit docs](https://github.com/pypa/pip-audit)   |
| **[gitleaks](https://github.com/gitleaks/gitleaks)** | Scans git history and staged changes for secrets (API keys, tokens, passwords). Runs as a pre-push hook.                     | `.gitleaks.toml` (if present)      | [gitleaks docs](https://github.com/gitleaks/gitleaks) |
| **[CodeQL](https://codeql.github.com/)**             | GitHub's semantic code analysis engine. Finds security vulnerabilities via deep static analysis. Runs in CI.                 | `security-codeql.yml`              | [CodeQL docs](https://codeql.github.com/)             |
| **[OpenSSF Scorecard](https://scorecard.dev/)**      | Evaluates repository security practices (branch protection, dependency pinning, etc.). Runs in CI.                           | `scorecard.yml`                    | [Scorecard docs](https://scorecard.dev/)              |

---

## Git Hooks

| Tool                                                             | What it does                                                                                                                                                           | Config                                                  | Docs                                                              |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------- |
| **[pre-commit](https://pre-commit.com/)**                        | Framework that manages and runs git hooks. Hooks run automatically before commits, on commit messages, and before pushes.                                              | [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) | [pre-commit docs](https://pre-commit.com/)                        |
| **[commitizen](https://commitizen-tools.github.io/commitizen/)** | Validates that commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) format. Also provides `cz commit` for interactive commit authoring. | `pyproject.toml` → `[tool.commitizen]`                  | [commitizen docs](https://commitizen-tools.github.io/commitizen/) |

---

## Documentation

| Tool                                                                    | What it does                                                                                            | Config                    | Docs                                                          |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------- |
| **[MkDocs](https://www.mkdocs.org/)**                                   | Static site generator for project documentation. Writes docs in Markdown, builds an HTML site.          | `mkdocs.yml`              | [MkDocs docs](https://www.mkdocs.org/)                        |
| **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)** | Theme for MkDocs with search, dark mode, admonitions, tabs, and more.                                   | `mkdocs.yml` → `theme:`   | [Material docs](https://squidfunk.github.io/mkdocs-material/) |
| **[mkdocstrings](https://mkdocstrings.github.io/)**                     | Generates API reference docs from Python docstrings. Auto-renders function signatures and descriptions. | `mkdocs.yml` → `plugins:` | [mkdocstrings docs](https://mkdocstrings.github.io/)          |

---

## CI/CD & Release

| Tool                                                                  | What it does                                                                                                             | Config                       | Docs                                                                   |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------- | ---------------------------------------------------------------------- |
| **[GitHub Actions](https://docs.github.com/en/actions)**              | CI/CD platform. Runs workflows on push, PR, schedule, or manual trigger. This project has 37 workflows.                  | `.github/workflows/*.yml`    | [Actions docs](https://docs.github.com/en/actions)                     |
| **[release-please](https://github.com/googleapis/release-please)**    | Automates versioning and changelog generation from Conventional Commits. Creates a Release PR that you review and merge. | `release-please-config.json` | [release-please docs](https://github.com/googleapis/release-please)    |
| **[Dependabot](https://docs.github.com/en/code-security/dependabot)** | Automatically opens PRs to update outdated or vulnerable dependencies.                                                   | `.github/dependabot.yml`     | [Dependabot docs](https://docs.github.com/en/code-security/dependabot) |

---

## Container

| Tool                                                                 | What it does                                                                                                 | Config                                 | Docs                                           |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------- | ---------------------------------------------- |
| **[Podman](https://podman.io/) / [Docker](https://www.docker.com/)** | Builds and runs OCI container images. The project uses a `Containerfile` (same syntax as `Dockerfile`).      | `Containerfile`, `docker-compose.yml`  | [Podman docs](https://podman.io/)              |
| **[Trivy](https://trivy.dev/)**                                      | Scans container images for vulnerabilities. Runs in CI.                                                      | `.github/workflows/container-scan.yml` | [Trivy docs](https://trivy.dev/)               |
| **[Grype](https://github.com/anchore/grype)**                        | Scans container images for vulnerabilities using a different DB than Trivy. Provides complementary coverage. | `.github/workflows/container-scan.yml` | [Grype docs](https://github.com/anchore/grype) |

---

## Link Checking

| Tool                                                | What it does                                                                                     | Config                               | Docs                                                 |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------ | ---------------------------------------------------- |
| **[lychee](https://github.com/lycheeverse/lychee)** | Checks Markdown and HTML for broken links. Rust-based, async. Runs in CI via `link-checker.yml`. | `.github/workflows/link-checker.yml` | [lychee docs](https://github.com/lycheeverse/lychee) |

---

## Config Validation

| Tool                                                                          | What it does                                                                                       | Config                         | Docs                                                                           |
| ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------ |
| **[validate-pyproject](https://validate-pyproject.readthedocs.io/)**          | Validates `pyproject.toml` against PEP 621 and packaging schemas. Catches config errors before CI. | — (validates `pyproject.toml`) | [validate-pyproject docs](https://validate-pyproject.readthedocs.io/)          |
| **[actionlint](https://github.com/rhysd/actionlint)**                         | Lints GitHub Actions workflow files. Catches expression errors, unknown inputs, and runner issues. | — (lints `.github/workflows/`) | [actionlint docs](https://github.com/rhysd/actionlint)                         |
| **[check-jsonschema](https://github.com/python-jsonschema/check-jsonschema)** | Validates YAML/JSON files against schemas from SchemaStore (workflows, Dependabot config, etc.).   | — (schema auto-detected)       | [check-jsonschema docs](https://github.com/python-jsonschema/check-jsonschema) |

---

## Developer Dashboard

| Tool                                                                | What it does                                                                                                                   | Config                                       | Docs                                                          |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------- | ------------------------------------------------------------- |
| **[FastAPI](https://fastapi.tiangolo.com/)**                        | Powers the environment dashboard web app at `http://127.0.0.1:8000`. Gathers system, project, and tooling data via 20 plugins. | `tools/dev_tools/env_dashboard/`             | [FastAPI docs](https://fastapi.tiangolo.com/)                 |
| **[htmx](https://htmx.org/)**                                      | Provides dynamic UI updates without a full SPA framework. Used for dashboard section toggling and live refresh.                | Dashboard templates                          | [htmx docs](https://htmx.org/)                               |
| **[Alpine.js](https://alpinejs.dev/)**                              | Lightweight client-side state for search, filters, and toggles in the dashboard.                                               | Dashboard templates                          | [Alpine.js docs](https://alpinejs.dev/)                       |

---

## Formatting (non-Python)

| Tool                                                                     | What it does                                                                                            | Config                     | Docs                                                                      |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------- |
| **[Prettier](https://prettier.io/)**                                     | Formats Markdown, YAML, and JSON files. Runs as a manual pre-commit hook and VS Code default formatter. | `.pre-commit-config.yaml`  | [Prettier docs](https://prettier.io/)                                     |
| **[markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2)** | Lints Markdown files for style and structure issues. Runs as a manual pre-commit hook.                  | `.markdownlint-cli2.jsonc` | [markdownlint-cli2 docs](https://github.com/DavidAnson/markdownlint-cli2) |
| **[hadolint](https://github.com/hadolint/hadolint)**                     | Lints Dockerfiles/Containerfiles for best practices. Runs as a manual pre-commit hook.                  | `.pre-commit-config.yaml`  | [hadolint docs](https://github.com/hadolint/hadolint)                     |

---

## See Also

- [command-workflows.md](development/command-workflows.md) — How the tool layers (Python → Hatch → Task) work together
- [tool-decisions.md](design/tool-decisions.md) — Detailed notes on why each tool was chosen over alternatives
- [ADR index](adr/README.md) — Architecture Decision Records for major tool choices
- [developer-commands.md](development/developer-commands.md) — Complete command reference
- [workflows.md](workflows.md) — Canonical workflow inventory (many tools run via CI)
- [USING_THIS_TEMPLATE.md](USING_THIS_TEMPLATE.md) — Tool customization for template users
- [repo-layout.md](repo-layout.md) — Where tools are configured in the project structure
