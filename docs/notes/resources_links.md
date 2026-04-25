# Learning Resources

Curated links to documentation, tutorials, and references for the tools and
patterns used in this project. Organized by topic for quick lookup.

---

## Python Packaging & Project Structure

| Resource                                                                                                   | Description                                                                   |
| ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| [Python Packaging User Guide](https://packaging.python.org/)                                               | Official guide — covers pyproject.toml, src/ layout, builds, and publishing   |
| [PEP 621 — Project metadata](https://peps.python.org/pep-0621/)                                            | The standard for declaring metadata in pyproject.toml                         |
| [PEP 517 — Build system interface](https://peps.python.org/pep-0517/)                                      | How build backends (Hatchling, setuptools) work under the hood                |
| [src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) | Official comparison — why we chose src/ ([ADR 001](../adr/001-src-layout.md)) |
| [Hatch documentation](https://hatch.pypa.io/)                                                              | Project manager used for environments, builds, and scripts                    |
| [Hatchling documentation](https://hatch.pypa.io/latest/build/)                                             | Build backend configuration                                                   |

## Testing

| Resource                                                                                            | Description                                                  |
| --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| [pytest documentation](https://docs.pytest.org/)                                                    | Test framework — fixtures, parametrize, markers, plugins     |
| [pytest-cov](https://pytest-cov.readthedocs.io/)                                                    | Coverage plugin for pytest                                   |
| [Effective Python Testing with pytest (Real Python)](https://realpython.com/pytest-python-testing/) | Practical tutorial covering fixtures, marks, and parametrize |
| [Testing Best Practices (The Hitchhiker's Guide)](https://docs.python-guide.org/writing/tests/)     | General Python testing guidance                              |

## Linting, Formatting & Type Checking

| Resource                                                                       | Description                                             |
| ------------------------------------------------------------------------------ | ------------------------------------------------------- |
| [Ruff documentation](https://docs.astral.sh/ruff/)                             | Linter + formatter — rules reference, configuration     |
| [Ruff rule index](https://docs.astral.sh/ruff/rules/)                          | Searchable index of all lint rules by code              |
| [mypy documentation](https://mypy.readthedocs.io/)                             | Static type checker — configuration, error codes, stubs |
| [mypy cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html) | Quick reference for type annotations                    |
| [typing module docs](https://docs.python.org/3/library/typing.html)            | Standard library typing reference                       |

## Pre-commit Hooks

| Resource                                                          | Description                                                  |
| ----------------------------------------------------------------- | ------------------------------------------------------------ |
| [pre-commit documentation](https://pre-commit.com/)               | Hook framework — installation, configuration, creating hooks |
| [pre-commit hook directory](https://pre-commit.com/hooks.html)    | Searchable directory of available hooks                      |
| [Supported hooks in this project](../adr/008-pre-commit-hooks.md) | Full inventory of hooks used here (ADR 008)                  |

## GitHub Actions & CI/CD

| Resource                                                                                                                   | Description                                             |
| -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| [GitHub Actions documentation](https://docs.github.com/en/actions)                                                         | Official docs — workflows, syntax, runners, expressions |
| [Workflow syntax reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)         | Complete YAML syntax for workflow files                 |
| [GitHub Actions expressions](https://docs.github.com/en/actions/learn-github-actions/expressions)                          | `${{ }}` expression syntax, contexts, functions         |
| [Security hardening for Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions) | Best practices — permissions, SHA pinning, secrets      |
| [actionlint](https://github.com/rhysd/actionlint)                                                                          | Workflow linter — catches errors before pushing         |
| [act](https://github.com/nektos/act)                                                                                       | Run GitHub Actions locally for faster iteration         |

## Security Tools

| Resource                                                        | Description                                         |
| --------------------------------------------------------------- | --------------------------------------------------- |
| [Bandit documentation](https://bandit.readthedocs.io/)          | Python security linter — issue types, configuration |
| [pip-audit](https://github.com/pypa/pip-audit)                  | Vulnerability scanning for Python dependencies      |
| [gitleaks](https://github.com/gitleaks/gitleaks)                | Secret detection in git repositories                |
| [Trivy](https://aquasecurity.github.io/trivy/)                  | Container and dependency vulnerability scanner      |
| [OpenSSF Scorecard](https://securityscorecards.dev/)            | Supply-chain security scoring                       |
| [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) | Application security cheat sheets (OWASP)           |

## Documentation (MkDocs)

| Resource                                                                                                              | Description                                          |
| --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| [MkDocs documentation](https://www.mkdocs.org/)                                                                       | Static site generator for project docs               |
| [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)                                                   | Theme used in this project — features, customization |
| [mkdocstrings](https://mkdocstrings.github.io/)                                                                       | Auto-generate API docs from Python docstrings        |
| [Google Python Style Guide — Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) | Docstring convention used in this project            |

## Containers

| Resource                                                                  | Description                                                |
| ------------------------------------------------------------------------- | ---------------------------------------------------------- |
| [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)     | Syntax reference for Containerfile / Dockerfile            |
| [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/) | Pattern used in our Containerfile for minimal images       |
| [Podman documentation](https://docs.podman.io/)                           | Daemonless container engine (alternative to Docker)        |
| [Dev Containers specification](https://containers.dev/)                   | Standard for development containers (VS Code / Codespaces) |

## Git & Conventional Commits

| Resource                                                                             | Description                                                           |
| ------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| [Pro Git book (free)](https://git-scm.com/book/en/v2)                                | The definitive Git book — covers fundamentals through advanced topics |
| [Git documentation](https://git-scm.com/doc)                                         | Official reference — man pages, videos, cheat sheet                   |
| [Learn Git Branching](https://learngitbranching.js.org/)                             | Interactive visual tutorial for learning Git branching                |
| [Oh Shit, Git!?!](https://ohshitgit.com/)                                            | Plain-English fixes for common Git mistakes                           |
| [Git flight rules](https://github.com/k88hudson/git-flight-rules)                    | FAQ-style guide — "I did X, how do I fix it?"                         |
| [GitHub Git cheat sheet](https://education.github.com/git-cheat-sheet-education.pdf) | One-page PDF reference for common commands                            |
| [Atlassian Git tutorials](https://www.atlassian.com/git/tutorials)                   | Well-illustrated guides on branching, merging, rebasing               |
| [Conventional Commits](https://www.conventionalcommits.org/)                         | Commit message convention used in this project                        |
| [commitizen](https://commitizen-tools.github.io/commitizen/)                         | CLI tool for authoring conventional commits                           |
| [release-please](https://github.com/googleapis/release-please)                       | Automated release management from conventional commits                |

## Architecture Decision Records

| Resource                                                                                                 | Description                              |
| -------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| [ADR overview (adr.github.io)](https://adr.github.io/)                                                   | What ADRs are and why they matter        |
| [Michael Nygard's ADR article](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) | Original blog post that popularized ADRs |
| [MADR template](https://adr.github.io/madr/)                                                             | Markdown ADR template (similar to ours)  |

## General Python

| Resource                                                                                      | Description                                                      |
| --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| [Python documentation](https://docs.python.org/3/)                                            | Official language and stdlib reference                           |
| [Real Python](https://realpython.com/)                                                        | High-quality tutorials and guides                                |
| [The Hitchhiker's Guide to Python](https://docs.python-guide.org/)                            | Best practices for Python development                            |
| [PEP 8 — Style Guide](https://peps.python.org/pep-0008/)                                      | The foundational Python style guide (Ruff enforces most of this) |
| [Python Type Hints cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)   | Quick reference for common type patterns                         |
| [Python 3 Module of the Week](https://pymotw.com/3/)                                          | In-depth stdlib module walkthroughs                              |
| [Fluent Python (book)](https://www.oreilly.com/library/view/fluent-python-2nd/9781492056348/) | Advanced Python — data models, concurrency, metaprogramming      |

## Project Dependencies (Dev & Test)

Every tool declared in `pyproject.toml` `[project.optional-dependencies]`:

| Tool                    | Docs                                                                                            | Description                                          |
| ----------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| **pytest**              | [docs.pytest.org](https://docs.pytest.org/)                                                     | Testing framework                                    |
| **pytest-cov**          | [pytest-cov.readthedocs.io](https://pytest-cov.readthedocs.io/)                                 | Coverage plugin for pytest                           |
| **Ruff**                | [docs.astral.sh/ruff](https://docs.astral.sh/ruff/)                                             | Linter + formatter                                   |
| **mypy**                | [mypy.readthedocs.io](https://mypy.readthedocs.io/)                                             | Static type checker                                  |
| **pre-commit**          | [pre-commit.com](https://pre-commit.com/)                                                       | Git hooks framework                                  |
| **Bandit**              | [bandit.readthedocs.io](https://bandit.readthedocs.io/)                                         | Security linter for Python                           |
| **commitizen**          | [commitizen-tools.github.io](https://commitizen-tools.github.io/commitizen/)                    | Conventional commit helper                           |
| **deptry**              | [deptry.com](https://deptry.com/)                                                               | Dependency hygiene checker                           |
| **pipdeptree**          | [github.com/tox-dev/pipdeptree](https://github.com/tox-dev/pipdeptree)                          | Dependency tree visualizer                           |
| **MkDocs**              | [mkdocs.org](https://www.mkdocs.org/)                                                           | Documentation site generator                         |
| **Material for MkDocs** | [squidfunk.github.io/mkdocs-material](https://squidfunk.github.io/mkdocs-material/)             | MkDocs theme                                         |
| **pymdown-extensions**  | [facelessuser.github.io/pymdown-extensions](https://facelessuser.github.io/pymdown-extensions/) | Markdown extensions (tabbed, highlight, superfences) |
| **mkdocstrings**        | [mkdocstrings.github.io](https://mkdocstrings.github.io/)                                       | Auto-generate API docs from docstrings               |

## Configuration File Formats

| Resource                                               | Description                                                |
| ------------------------------------------------------ | ---------------------------------------------------------- |
| [TOML specification](https://toml.io/)                 | Config file format used by pyproject.toml                  |
| [YAML specification](https://yaml.org/spec/)           | Config format used by workflows, mkdocs.yml, pre-commit    |
| [YAML multiline strings](https://yaml-multiline.info/) | Interactive guide to YAML's confusing string styles        |
| [JSON Schema](https://json-schema.org/)                | Used for labels/\*.json, GitHub issue templates            |
| [Cron expression guide](https://crontab.guru/)         | Interactive helper for GitHub Actions schedule cron syntax |

## GitHub Platform

| Resource                                                                                                                                                                            | Description                                                   |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| [GitHub Docs](https://docs.github.com/)                                                                                                                                             | Official platform documentation                               |
| [Branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule) | How to configure required checks                              |
| [Repository variables](https://docs.github.com/en/actions/learn-github-actions/variables)                                                                                           | Variables and secrets for Actions (used by repository guards) |
| [Dependabot documentation](https://docs.github.com/en/code-security/dependabot)                                                                                                     | Automated dependency updates                                  |
| [GitHub Pages](https://docs.github.com/en/pages)                                                                                                                                    | Hosting docs from the repo (used by docs-deploy workflow)     |
| [GitHub Codespaces](https://docs.github.com/en/codespaces)                                                                                                                          | Cloud dev environments (pairs with .devcontainer/)            |
| [GitHub CLI (gh)](https://cli.github.com/)                                                                                                                                          | Command-line tool for GitHub — PRs, issues, releases          |

## Task Runner

| Resource                                                            | Description                                         |
| ------------------------------------------------------------------- | --------------------------------------------------- |
| [Taskfile documentation](https://taskfile.dev/)                     | Task runner used for `task test`, `task lint`, etc. |
| [Taskfile schema reference](https://taskfile.dev/reference/schema/) | YAML schema for Taskfile.yml                        |

## Software Supply Chain & SBOMs

| Resource                                            | Description                                              |
| --------------------------------------------------- | -------------------------------------------------------- |
| [SPDX specification](https://spdx.dev/)             | Software Package Data Exchange — SBOM format             |
| [CycloneDX specification](https://cyclonedx.org/)   | Alternative SBOM format (also generated by this project) |
| [OpenSSF best practices](https://best.openssf.org/) | Open Source Security Foundation guidelines               |
| [SLSA framework](https://slsa.dev/)                 | Supply-chain Levels for Software Artifacts               |

## Markdown & Formatting

| Resource                                                                                | Description                                            |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| [Prettier documentation](https://prettier.io/docs/en/)                                  | Code formatter used for Markdown files in this project |
| [markdownlint rules](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md) | Rule reference for markdownlint-cli2                   |
| [GitHub Flavored Markdown](https://github.github.com/gfm/)                              | GitHub's Markdown spec — tables, task lists, autolinks |
| [CommonMark specification](https://commonmark.org/)                                     | The foundational Markdown standard                     |

## AI Coding Assistants

<!-- TODO (template users): If you don't use AI assistants in your workflow,
     you can remove this section. If you do, update the links to match
     the tools your team uses. -->

| Resource                                                                                                                                              | Description                                 |
| ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| [GitHub Copilot custom instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot) | How `.github/copilot-instructions.md` works |
| [Copilot chat documentation](https://docs.github.com/en/copilot/using-github-copilot/asking-github-copilot-questions-in-your-ide)                     | Using Copilot in VS Code                    |
| [Cursor Rules](https://cursor.sh/docs/context/rules)                                                                                                  | Similar context files for the Cursor editor |

## Modern Python Tooling

| Resource                                                                                | Description                                                   |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| [uv documentation](https://docs.astral.sh/uv/)                                          | Ultra-fast Python package installer and resolver (Astral)     |
| [Rye documentation](https://rye.astral.sh/)                                             | Experimental Python project manager (Astral, merging into uv) |
| [Scientific Python Development Guide](https://learn.scientific-python.org/development/) | Modern packaging guide for scientific Python                  |
| [Hypermodern Python](https://cjolowicz.github.io/posts/hypermodern-python-01-setup/)    | Blog series on modern Python project setup                    |

---

## How to Use This Page

- **New to the project?** Start with the Python Packaging, Git, and Testing sections
- **Setting up CI?** GitHub Actions, GitHub Platform, and Security Tools sections
- **Writing docs?** MkDocs section and the Google docstring guide
- **Configuring tools?** Configuration File Formats section for TOML/YAML reference
- **Looking for a tool's docs?** Project Dependencies table links every dev tool
- **Making an architectural decision?** ADR section for the template and process
- **Using AI assistants?** AI Coding Assistants section + `copilot-instructions.md`

This is a living document — add links as you discover useful resources and
remove ones that go stale.

For self-written references and cheat sheets (e.g., Git commands), see
[resources_written.md](resources_written.md).
