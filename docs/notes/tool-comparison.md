# Tool Comparison Notes

Quick reference for choosing between similar tools. See
[tool-decisions.md](../design/tool-decisions.md) for the detailed rationale
behind each choice made in this project.

<!-- TODO (template users): Update the "Chosen" column and winner notes
     to reflect your own tool choices if they differ from this template. -->

## Formatters

| Tool         | Language | Notes                                     | Chosen? |
| ------------ | -------- | ----------------------------------------- | :-----: |
| **Ruff**     | Rust     | Black-compatible, much faster, also lints |   ✅    |
| **Black**    | Python   | Opinionated, zero-config, widely adopted  |   ❌    |
| **autopep8** | Python   | PEP 8 focused, less opinionated           |   ❌    |
| **YAPF**     | Python   | Google's formatter, highly configurable   |   ❌    |
| **Prettier** | Node.js  | Markdown/YAML/JSON formatting             |   ✅    |

**Winner:** Ruff for Python, Prettier for Markdown.
See [ADR 005](../adr/005-ruff-for-linting-formatting.md) and
[ADR 033](../adr/033-prettier-for-markdown-formatting.md).

---

## Linters

| Tool       | Language | Notes                                   | Chosen? |
| ---------- | -------- | --------------------------------------- | :-----: |
| **Ruff**   | Rust     | Replaces flake8, isort, pyupgrade, etc. |   ✅    |
| **Flake8** | Python   | Classic, plugin ecosystem               |   ❌    |
| **Pylint** | Python   | Very thorough, can be noisy             |   ❌    |

**Winner:** Ruff — 10-100x faster, replaces multiple tools.

---

## Type Checkers

| Tool        | Notes                                | Chosen? |
| ----------- | ------------------------------------ | :-----: |
| **Mypy**    | Original, most widely used in CI     |   ✅    |
| **Pyright** | Microsoft, powers Pylance in VS Code |  ✅\*   |
| **Pyre**    | Facebook, incremental checking       |   ❌    |

\*Pyright runs in-editor via Pylance. Mypy runs in CI and pre-commit.

**Recommendation:** Pyright in editor (via Pylance), Mypy in CI.
See [ADR 007](../adr/007-mypy-for-type-checking.md).

---

## Test Frameworks

| Tool         | Notes                            | Chosen? |
| ------------ | -------------------------------- | :-----: |
| **pytest**   | De facto standard, great plugins |   ✅    |
| **unittest** | Built-in, Java-style (verbose)   |   ❌    |
| **nose2**    | unittest successor, less active  |   ❌    |

**Winner:** pytest. See [ADR 006](../adr/006-pytest-for-testing.md) and
[ADR 029](../adr/029-testing-strategy.md).

---

## Build Backends

| Tool           | Notes                                | Chosen? |
| -------------- | ------------------------------------ | :-----: |
| **Hatchling**  | Modern, good CLI, version management |   ✅    |
| **setuptools** | Standard, most compatible            |   ❌    |
| **flit**       | Simple, minimal config               |   ❌    |
| **poetry**     | All-in-one (deps + build + publish)  |   ❌    |
| **PDM**        | PEP 582 support, modern              |   ❌    |

**Winner:** Hatchling + Hatch. See [ADR 016](../adr/016-hatchling-and-hatch.md).

---

## Package Installers

| Tool     | Language | Notes                                          | Chosen? |
| -------- | -------- | ---------------------------------------------- | :-----: |
| **pip**  | Python   | Standard, universal, slower                    |   ✅    |
| **uv**   | Rust     | 10-100x faster, pip-compatible, Astral project |  ✅\*   |
| **pipx** | Python   | Isolated CLI tool installs                     |   ✅    |

\*uv is recommended as a drop-in replacement for faster installs but pip is
the default in CI. See [troubleshooting](../guide/troubleshooting.md#pip-install-is-slow).

---

## Task Runners

| Tool         | Language | Notes                                     | Chosen? |
| ------------ | -------- | ----------------------------------------- | :-----: |
| **Taskfile** | Go       | YAML-based, simple, cross-platform        |   ✅    |
| **Make**     | C        | Classic, ubiquitous, tab-sensitive syntax |   ❌    |
| **Just**     | Rust     | Make alternative, cleaner syntax          |   ❌    |
| **Invoke**   | Python   | Python-based, good for Python projects    |   ❌    |
| **Nox**      | Python   | Test/session automation, pytest-like      |   ❌    |

**Winner:** Taskfile. See [ADR 017](../adr/017-task-runner.md).

---

## Pre-commit Hook Frameworks

| Tool           | Notes                                    | Chosen? |
| -------------- | ---------------------------------------- | :-----: |
| **pre-commit** | Language-agnostic, huge hook ecosystem   |   ✅    |
| **Husky**      | Node.js-focused, common in JS projects   |   ❌    |
| **lefthook**   | Go-based, parallel execution, fast       |   ❌    |
| **Git hooks**  | Manual scripts in `.git/hooks/`, no mgmt |   ❌    |

**Winner:** pre-commit. See [ADR 008](../adr/008-pre-commit-hooks.md).

---

## Security Linters

| Tool        | Notes                                        | Chosen? |
| ----------- | -------------------------------------------- | :-----: |
| **Bandit**  | Python-specific, AST-based security analysis |   ✅    |
| **Semgrep** | Multi-language, pattern-based, rule registry |   ❌    |
| **Safety**  | Dependency vulnerability checking only       |   ❌    |

**Winner:** Bandit for code, pip-audit for dependencies.
See [ADR 018](../adr/018-bandit-for-security-linting.md).

---

## Documentation Generators

| Tool           | Notes                                      | Chosen? |
| -------------- | ------------------------------------------ | :-----: |
| **MkDocs**     | Markdown-native, Material theme, fast      |   ✅    |
| **Sphinx**     | reStructuredText, Python ecosystem default |   ❌    |
| **Docusaurus** | React-based, good for JS projects          |   ❌    |
| **mdBook**     | Rust-based, minimal, fast                  |   ❌    |

**Winner:** MkDocs + Material. See [ADR 020](../adr/020-mkdocs-documentation-stack.md).

---

## CI Platforms

| Platform           | Notes                                          | Chosen? |
| ------------------ | ---------------------------------------------- | :-----: |
| **GitHub Actions** | Best GitHub integration, free for public repos |   ✅    |
| **GitLab CI**      | Built into GitLab, powerful                    |   ❌    |
| **CircleCI**       | Fast, good caching                             |   ❌    |
| **Travis CI**      | Pioneer, less popular now                      |   ❌    |

**For GitHub repos:** GitHub Actions. See
[ADR 003](../adr/003-separate-workflow-files.md).

---

## Container Runtimes

| Tool        | Notes                                       | Chosen? |
| ----------- | ------------------------------------------- | :-----: |
| **Docker**  | Industry standard, largest ecosystem        |   ✅    |
| **Podman**  | Daemonless, rootless, Docker-compatible CLI |   ✅    |
| **nerdctl** | containerd CLI, Docker-compatible commands  |   ❌    |

Both Docker and Podman work — the Containerfile is OCI-compatible.
See [ADR 019](../adr/019-containerfile.md) and
[ADR 025](../adr/025-container-strategy.md).

---

## Release Automation

| Tool                 | Notes                                       | Chosen? |
| -------------------- | ------------------------------------------- | :-----: |
| **release-please**   | Google's tool, conventional commit driven   |   ✅    |
| **semantic-release** | Node.js, wider ecosystem, more configurable |   ❌    |
| **commitizen bump**  | Python, simpler, fewer features             |   ❌    |

**Winner:** release-please. See
[ADR 021](../adr/021-automated-release-pipeline.md).

---

## How to Update This Page

When evaluating a new tool category:

1. Add a comparison table with columns: Tool, Notes, Chosen?
2. Note the winner and link to the relevant ADR
3. Update [tool-decisions.md](../design/tool-decisions.md) with the detailed
   rationale if the choice is significant
