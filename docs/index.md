<!-- TODO (template users): Replace the title, description, features list,
     quick links, and project layout below with your own project details.
     This page becomes your documentation site's landing page. -->

# simple-python-boilerplate

A minimal Python boilerplate using the **src/ layout**, configured with
[Hatch](https://hatch.pypa.io/) as the build system. Fork it, run
`python scripts/customize.py`, and start building.

## Features

- **src/ layout** — clean separation between source code and project root
  ([ADR 001](adr/001-src-layout.md)).
- **Hatch** — modern build backend and environment manager
  ([ADR 016](adr/016-hatchling-and-hatch.md)).
- **pytest** — testing framework with coverage support, multi-version
  matrix ([ADR 006](adr/006-pytest-for-testing.md)).
- **Ruff** — fast linting and formatting
  ([ADR 005](adr/005-ruff-for-linting-formatting.md)).
- **mypy** — strict static type checking
  ([ADR 007](adr/007-mypy-for-type-checking.md)).
- **MkDocs + Material** — documentation with auto-generated API reference.
- **47 pre-commit hooks** — across 4 stages: pre-commit, commit-msg,
  pre-push, manual ([ADR 008](adr/008-pre-commit-hooks.md)).
- **37 GitHub Actions workflows** — all SHA-pinned, with repository
  guard pattern ([ADR 004](adr/004-pin-action-shas.md),
  [ADR 011](adr/011-repository-guard-pattern.md)).
- **Security scanning** — Bandit, pip-audit, CodeQL, Trivy, Gitleaks,
  Dependency Review, OpenSSF Scorecard
  ([ADR 012](adr/012-multi-layer-security-scanning.md)).

## Quick links

| Resource                                          | Description                                     |
| ------------------------------------------------- | ----------------------------------------------- |
| [Getting Started](guide/getting-started.md)       | Installation and local development              |
| [Using This Template](USING_THIS_TEMPLATE.md)     | Customizing the boilerplate for your project    |
| [Development Guide](development/development.md)   | Developer tools and workflows                   |
| [Command Reference](reference/commands.md)        | All task / hatch / script commands in one place |
| [API Reference](reference/api.md)                 | Auto-generated from source docstrings           |
| [Architecture](design/architecture.md)            | System overview and module responsibilities     |
| [ADRs](adr/README.md)                             | Architecture Decision Records                   |
| [Workflows](workflows.md)                         | GitHub Actions inventory                        |
| [Tooling](tooling.md)                             | All repo tools at a glance                      |
| [Troubleshooting](guide/troubleshooting.md)       | Common issues and fixes                         |
| [Security Policy](../SECURITY.md)                 | Vulnerability reporting and tooling             |
| [Learning Notes](notes/learning.md)               | Concepts and tool comparisons from building     |
| [Resources (Links)](notes/resources_links.md)     | Curated external links and further reading      |
| [Resources (Written)](notes/resources_written.md) | Self-written references and cheat sheets        |

## Project layout

```text
src/
  simple_python_boilerplate/
    __init__.py       # Package root, version export
    api.py            # HTTP/REST interface (placeholder)
    cli.py            # CLI argument parsing (argparse)
    engine.py         # Core business logic (TypedDicts)
    main.py           # Entry points (console scripts)
    dev_tools/        # Development utilities (clean, etc.)
tests/                # Test suite (unit + integration)
docs/                 # Documentation source (this site)
scripts/              # Utility scripts (bootstrap, clean, doctor, git_doctor, etc.)
db/                   # Database schema, migrations, seeds, queries
experiments/          # Scratch files for exploration (not packaged)
.github/
  workflows/          # 37 GitHub Actions workflows (SHA-pinned)
  ISSUE_TEMPLATE/     # Issue form templates
pyproject.toml        # Project configuration (single source of truth)
Taskfile.yml          # Task runner shortcuts
Containerfile         # Multi-stage container build
mkdocs.yml            # Documentation site config
```

See [Repo Layout](repo-layout.md) for the full annotated directory tree.
