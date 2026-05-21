# Tool Inventory

Project tool inventory with practical guidance for each tool:

- **Why** this tool exists in this repo.
- **When** to use it in day-to-day development.
- **How** to use it here (entrypoint commands and config location).

## Operating Layers

| Tool | Why | When | How |
| --- | --- | --- | --- |
| [uv](https://docs.astral.sh/uv/) | Single source of truth for Python environment and lockfile management. | Any dependency or environment change. | `uv sync`, `uv add <pkg>`, `uv run <cmd>`. Config in `pyproject.toml`; lockfile is `uv.lock`. |
| [hatchling](https://hatch.pypa.io/latest/config/build/) + [hatch-vcs](https://github.com/ofek/hatch-vcs) | Build backend and versioning from git tags. | Building distributions or packaging in CI/image builds. | `uv build` (invokes hatchling). Build config in `pyproject.toml` under `[build-system]` and `[tool.hatch.version]`. |
| [Task](https://taskfile.dev/) | Human-friendly wrappers for frequent command sequences. | Daily workflows when you want short, discoverable commands. | `task --list`, `task test`, `task check`, `task dev`. Config in `Taskfile.yml`. |

## Application Runtime

| Tool | Why | When | How |
| --- | --- | --- | --- |
| [FastAPI](https://fastapi.tiangolo.com/) | API framework and web shell host. | Defining routes, request/response models, middleware. | App code in `src/feedback_triage/`; run via `task dev` or `uv run uvicorn feedback_triage.main:app --reload`. |
| [SQLModel](https://sqlmodel.tiangolo.com/) / SQLAlchemy 2.x | Typed ORM models and DB access patterns. | Model/schema and CRUD changes. | Models in `src/feedback_triage/models.py`; session-per-request via `get_db` dependency. |
| [Alembic](https://alembic.sqlalchemy.org/) | Versioned schema migrations. | Any DB schema change. | `task migration m="desc"`, `task migrate`; migration files in `alembic/versions/`. |
| PostgreSQL 16 | Production and test DB dialect baseline. | Local dev DB, integration tests, migration validation. | Local stack via `task up` / `docker-compose.yml`; `DATABASE_URL` from env. |

## Background Processing and Messaging

| Tool | Why | When | How |
| --- | --- | --- | --- |
| [Temporal](https://temporal.io/) | Durable workflow execution for long-running or multi-step business processes with retries and resumability. | Imports, AI classification, onboarding flows, weekly reports, webhook workflows with failure recovery. | Use for workflows only. Keep permanent product state in PostgreSQL. See `docs/design/background-processing-architecture.md`. |
| [Celery](https://docs.celeryq.dev/) | Python task queue for short, independent background jobs. | Single-purpose jobs like password reset email, email verification, invite email, and lightweight cleanup tasks. | Use workers for discrete tasks, not durable multi-step orchestration. Pair with RabbitMQ as broker. |
| [RabbitMQ](https://www.rabbitmq.com/) | Message transport and routing for Celery tasks. | Celery task message delivery and queue routing. | Use as Celery broker only; do not use it as cache, rate-limit store, or permanent state store. |
| [Redis](https://redis.io/) | Fast temporary state store for latency-sensitive controls. | Distributed rate limits, caching, short-lived counters, and transient locks. | Keep data ephemeral. Do not use as source-of-truth or durable workflow state. |

## Frontend and Dashboard

| Tool | Why | When | How |
| --- | --- | --- | --- |
| [Vite](https://vitejs.dev/) + React (v2 runtime) | Frontend build/runtime for migrated v2 pages. | Editing code under `web/src/`. | `npm --prefix web run build` for production assets; source in `web/`, emitted assets consumed by backend shell routes. |
| [FastAPI](https://fastapi.tiangolo.com/) + [Jinja2](https://jinja.palletsprojects.com/) (dashboard app) | Internal environment dashboard server-rendered UI. | Working in `tools/dev_tools/env_dashboard/`. | Run dashboard task/command; templates in `tools/dev_tools/env_dashboard/templates/`. |
| [htmx](https://htmx.org/) | Partial-page updates without SPA overhead in dashboard views. | Adding dynamic section refresh/filter behavior in dashboard templates. | Add `hx-*` attributes in dashboard templates; backend serves partial endpoints. |
| [Alpine.js](https://alpinejs.dev/) | Lightweight client state in dashboard pages. | Local state toggles/search UI behavior in templates. | Use `x-data`, `x-show`, `x-on` patterns in dashboard templates. |

## Quality and Testing

| Tool | Why | When | How |
| --- | --- | --- | --- |
| [Ruff](https://docs.astral.sh/ruff/) | Fast lint + format baseline for Python code quality. | Before committing any Python/doc tooling edits touching linted files. | `task lint`, `task fmt`, or `uv run ruff check src tests scripts`. Config in `pyproject.toml` (`[tool.ruff]`). |
| [mypy](https://mypy.readthedocs.io/) | Static type safety for `src/feedback_triage/`. | Public API changes, schema/model changes, refactors. | `task typecheck` or `uv run mypy src/`. Config in `pyproject.toml` (`[tool.mypy]`). |
| [pytest](https://docs.pytest.org/) | Primary automated test runner. | API/model/business logic verification. | `task test`, `task test:k -- <expr>`. Config in `pyproject.toml` (`[tool.pytest.ini_options]`). |
| [pytest-cov](https://pytest-cov.readthedocs.io/) | Coverage reporting for test completeness. | Coverage checks and regression analysis. | `task test:cov` or pytest with `--cov`. Coverage config in `pyproject.toml`. |
| [Playwright](https://playwright.dev/python/) | Browser-level smoke/e2e checks. | Frontend shell/page flow changes and UI parity checks. | `task test:e2e` (gated/opt-in). Tests under `tests/e2e/`. |
| [deptry](https://deptry.com/) | Detects missing/unused/transitive dependency drift. | Dependency cleanups or unexplained import failures. | `task deptry` or `uv run deptry .`. Config in `pyproject.toml`. |
| [typos](https://github.com/crate-ci/typos) + [codespell](https://github.com/codespell-project/codespell) | Catch spelling mistakes in code/docs/config. | Content edits across docs, code, and workflow files. | Runs in pre-commit/CI; manual via `uv run typos` and `uv run codespell`. Config in `_typos.toml` and workflow hooks. |

## Security and Supply Chain

| Tool | Why | When | How |
| --- | --- | --- | --- |
| [Bandit](https://bandit.readthedocs.io/) | Python security linting for common risky patterns. | Any Python changes before merge. | `task security` or `uv run bandit -c pyproject.toml -r src/`. |
| [pip-audit](https://github.com/pypa/pip-audit) | Dependency vulnerability detection. | Dependency updates, release readiness checks. | Run via pre-commit/CI or `uv run pip-audit`. |
| [gitleaks](https://github.com/gitleaks/gitleaks) | Secret scanning for commits/history. | Before pushing when handling env/config/secrets-adjacent changes. | Runs in pre-push/CI; config in `.gitleaks.toml` if present. |
| [CodeQL](https://codeql.github.com/) | Semantic code scanning in GitHub CI. | PR validation for security regressions. | Workflow: `.github/workflows/security-codeql.yml`. |
| [OpenSSF Scorecard](https://scorecard.dev/) | Repository security posture checks. | Periodic posture review and release governance. | Workflow: `.github/workflows/scorecard.yml`. |

## Documentation Stack

| Tool | Why | When | How |
| --- | --- | --- | --- |
| [MkDocs](https://www.mkdocs.org/) | Static documentation site generator. | Any docs changes that should be validated as a site. | `uv run mkdocs serve` or `uv run mkdocs build --strict`. Main config: `mkdocs.yml`. |
| [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) | Site theme and docs UX features. | Navigation/theme/layout changes in docs site. | Configure via `theme:` in `mkdocs.yml`. |
| [mkdocstrings](https://mkdocstrings.github.io/) | API reference generation from Python docstrings. | Updating docs/reference API pages. | Plugin configured in `mkdocs.yml`; resolves modules from `src/`. |
| MkDocs hooks (`mkdocs-hooks/*.py`) | Repo-specific docs transformations and generation. | Repo link rewriting, command reference generation, template inclusion behavior. | Hook registration in `mkdocs.yml` `hooks:` section. |

## Git and Release Automation

| Tool | Why | When | How |
| --- | --- | --- | --- |
| [pre-commit](https://pre-commit.com/) | Local quality/security gate before commits. | Always before commit/push in active branches. | `pre-commit install`, `pre-commit run --all-files`; config in `.pre-commit-config.yaml`. |
| [commitizen](https://commitizen-tools.github.io/commitizen/) | Conventional Commit validation and guided commit authoring. | Writing structured commit messages and enforcing release semantics. | `task commit` or `uv run cz commit`; config in `pyproject.toml` (`[tool.commitizen]`). |
| [GitHub Actions](https://docs.github.com/en/actions) | CI/CD execution platform. | All PR and merge validation, release automation, scans. | Workflow files in `.github/workflows/`; lint with `actionlint`. |
| [release-please](https://github.com/googleapis/release-please) | Automated changelog/release PR from commit history. | Preparing tagged releases with consistent changelog flow. | Config in `release-please-config.json`; runs in release workflow. |
| [Dependabot](https://docs.github.com/en/code-security/dependabot) | Automated dependency update PR creation. | Ongoing dependency hygiene and CVE response. | Config in `.github/dependabot.yml`. |

## Containers and Local Infra

| Tool | Why | When | How |
| --- | --- | --- | --- |
| [Docker](https://www.docker.com/) / [Podman](https://podman.io/) | OCI image build/run for local parity and deployment packaging. | Building/running service containers locally or in CI. | Build from `Containerfile`; local stack in `docker-compose.yml`. |
| Docker Compose | Multi-service local orchestration (app + Postgres). | Local integration testing and DB-backed dev workflows. | `task up`, `task down` (or `docker compose up/down`). |
| [Trivy](https://trivy.dev/) + [Grype](https://github.com/anchore/grype) | Container vulnerability scanning with complementary DBs. | Image security checks in CI/release gates. | Run in `.github/workflows/container-scan.yml`. |

## Validation and Hygiene Utilities

| Tool | Why | When | How |
| --- | --- | --- | --- |
| [actionlint](https://github.com/rhysd/actionlint) | Static lint for GitHub Actions syntax and expressions. | Any workflow edit before pushing. | `uv run actionlint` from repo root. |
| [check-jsonschema](https://github.com/python-jsonschema/check-jsonschema) | Schema validation for YAML/JSON configs. | Editing workflow/dependabot/structured config files. | Runs in CI/pre-commit according to hook configuration. |
| [validate-pyproject](https://validate-pyproject.readthedocs.io/) | Validates packaging metadata structure. | Editing `pyproject.toml`. | Run via pre-commit/CI or `uv run validate-pyproject pyproject.toml`. |
| [lychee](https://github.com/lycheeverse/lychee) | Broken-link detection in docs and site output. | Documentation changes, especially link-heavy updates. | CI workflow `.github/workflows/link-checker.yml`; local run with lychee CLI. |

## Quick Command Set

| Goal | Primary command |
| --- | --- |
| Sync environment | `uv sync` |
| Start local API dev server | `task dev` |
| Run full quality gate | `task check` |
| Run e2e smoke tests | `task test:e2e` |
| Build docs strictly | `uv run mkdocs build --strict` |
| Lint workflows | `uv run actionlint` |
| Start local DB stack | `task up` |

## See Also

- [development/development-framework.md](development/development-framework.md) - Project operating rules, workflows, and conventions.
- [development/developer-commands.md](development/developer-commands.md) - Command catalog.
- [workflows.md](workflows.md) - CI workflow inventory.
- [design/tool-decisions.md](design/tool-decisions.md) - Tool selection rationale.
- [design/background-processing-architecture.md](design/background-processing-architecture.md) - Background processing ownership boundaries.
- [adr/README.md](adr/README.md) - Architecture Decision Record index.
