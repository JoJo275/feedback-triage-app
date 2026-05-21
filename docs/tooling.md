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

## Recommended Tool Matrix

| Tool | What it is | Why use it | When to use it | How it operates in your app | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| Next.js | React framework for building full-stack web applications; it adds routing, rendering, optimization, and build tooling around React. | Gives your SaaS frontend a serious framework structure: routes, layouts, loading states, error boundaries, marketing pages, app pages. | Use for the frontend/app shell. | User opens /dashboard; Next.js renders the page, runs React components, calls FastAPI through API client/TanStack Query. | Core Python business logic, background jobs, source-of-truth data rules. |
| React | UI component library. | Lets you build reusable dashboard widgets, forms, modals, tables, cards, charts. | Use for all interactive frontend UI. | TotalSignalsCard, Sparkline, DashboardGrid, FeedbackTable, etc. become components. | Backend logic, database access. |
| TypeScript | Strongly typed language that builds on JavaScript and improves editor/type-checking support. | Reduces breakage from wrong prop names, wrong API response shapes, invalid layout objects, bad state transitions. | Use across the whole frontend. | Define types for widgets, signals, API responses, Redux state, route params. | Runtime validation by itself; use Zod or backend validation where runtime input is untrusted. |
| Tailwind CSS | Utility-first CSS framework. | Fast, consistent styling for dashboard UI. | Use for layout, spacing, color, typography utilities. | Components use utility classes plus your own design tokens. | Replacing design thinking; Tailwind alone does not create a good design system. |
| CSS variables / design tokens | Named CSS values for colors, spacing, radius, shadows. | Keeps your UI theme consistent and easier to change. | Use for SignalNest brand colors, dashboard density, semantic colors. | --color-signal-blue, --card-radius, --density-compact-gap. | Random one-off styling everywhere. |
| shadcn/ui | Copy-in React component patterns, commonly built with Radix + Tailwind. It gives you component source code you own/customize. | Speeds up accessible UI primitives without locking you into a generic component library. | Use for buttons, dialogs, dropdowns, tooltips, forms, sheets, command menu. | Add components into your repo, customize them to SignalNest styling. | App-specific widgets that should look custom, like your signal cards/sparklines. |
| Radix UI | Low-level accessible UI primitives. | Good foundation for menus, popovers, dialogs, tooltips, tabs. | Use through shadcn or directly when accessibility matters. | Radix handles behavior/accessibility; you provide styling. | Data charts, dashboard layout logic, backend logic. |
| TanStack Query | Server-state library for fetching, caching, synchronizing, and updating backend data. | Prevents messy manual fetch/loading/error/cache state. | Use for FastAPI data: signals, users, workspaces, dashboard summaries, tags. | React component calls useQuery(["signal-summary", range], fetchSummary); mutations invalidate/refetch related queries. | Pure UI state like tooltip hover or drag state. |
| Redux Toolkit | Structured global/client state system; createSlice is the standard Redux Toolkit way to define reducers/actions. | Your dashboard editor has undo/redo, complex layout editing, selected widgets, unsaved changes. That justifies real state management. | Use for complex dashboard editor state. | Store draft layout, saved layout, undo stack, redo stack, selected widget, edit mode, active breakpoint. | Server data from FastAPI; use TanStack Query for that. |
| FastAPI | Python API framework based on Python type hints; built for APIs. | Keeps Python backend, business rules, auth, permissions, OpenAPI-style API boundary. | Use as the real backend/API service. | Next.js calls FastAPI endpoints. FastAPI validates request, checks permissions, queries DB, starts workflows/tasks. | Frontend rendering/layout, chart hover state, dashboard drag UI. |
| Pydantic | Python data validation/serialization layer used heavily with FastAPI. | Validates request/response models and keeps API contracts clearer. | Use for API schemas and internal typed data models. | SignalSummaryResponse, CreateSignalRequest, DashboardLayoutResponse. | Long-term DB migrations; use Alembic. |
| SQLAlchemy / SQLModel | Python SQL toolkit/ORM; SQLAlchemy describes itself as the Python SQL toolkit and ORM. | Lets backend model/query relational data. | Use for users, workspaces, signals, tags, comments, layout records, audit logs. | FastAPI service function queries PostgreSQL through ORM/session. | Temporary cache/rate-limit counters. |
| Alembic | Database migration tool for SQLAlchemy projects. | Safely evolves schema over time. | Use whenever DB schema changes. | Add migration for new table/column, run during deploy. | Runtime data processing or app logic. |
| PostgreSQL | Primary relational database. | Source of truth for paid SaaS data. | Use for permanent data. | Store users, workspaces, signals, tags, comments, permissions, dashboard layouts, job records, audit history. | Short-lived counters, cache, locks. |
| Temporal | Durable workflow platform; workflows can resume after crashes/outages. | Handles important multi-step processes with retries, timers, state/history, failure recovery. | Use for business workflows, not trivial counters. | FastAPI starts workflow -> Temporal stores workflow history -> Temporal worker runs workflow/activities -> status written to PostgreSQL. | High-volume throwaway events, simple cache, rate limits. |
| Celery | Python distributed task queue; clients add task messages to a broker and workers process them. | Handles short independent Python jobs, especially if you expect many tiny tasks. | Use for simple one-step background tasks. | FastAPI enqueues Celery task -> RabbitMQ broker -> Celery worker executes task. | Durable multi-step workflows; use Temporal. |
| RabbitMQ | Message broker; queues are ordered collections of messages delivered to consumers. | Broker for Celery tasks. | Use only as Celery's transport/broker. | Celery publishes task message -> RabbitMQ queue holds/routes it -> Celery worker consumes it. | Cache, rate limits, source-of-truth data. |
| Redis | Fast in-memory store. Redis is specifically suitable for distributed rate limiting with shared counters/quotas. | Cache, rate limits, short-lived locks, temporary counters. | Use on synchronous request path where speed matters. | FastAPI checks Redis before accepting password reset/public feedback; caches dashboard summary for 30-120 seconds. | Permanent business records, durable workflow history. |
| pytest | Python test framework; pytest describes itself as a framework for simple and scalable tests. | Backend confidence. | Use for FastAPI services, DB logic, permission logic, workflow-starting logic. | CI runs backend test suite before deploy. | Browser UI testing. |
| Vitest | JS/TS unit/component test runner. | Fast frontend tests. | Use for pure functions, React components, Redux reducers. | Test dashboardEditorSlice, Sparkline, utility functions. | Full browser flows; use Playwright. |
| React Testing Library | Component testing approach. | Tests React UI from user-visible behavior. | Use for widgets/forms/components. | Render component, assert title/count/button/tooltip behavior. | Backend logic. |
| Playwright | End-to-end test framework for modern web apps; supports Chromium, WebKit, and Firefox. | Prevents real app flows from silently breaking. | Use for smoke/critical flows. | Login -> dashboard loads -> click Total Signals card -> filtered inbox opens. | Unit testing small functions. |
| Docker | Containerization. | Consistent deploy/runtime environment. | Use for FastAPI, worker, Temporal worker, maybe Next.js. | Build images, run services consistently locally/deployed. | Replacing tests or monitoring. |
| GitHub Actions | CI/CD automation. | Prevent broken code from merging/deploying. | Use for lint, typecheck, tests, builds, migrations check. | PR opens -> CI runs frontend/backend tests -> build passes -> deploy allowed. | Runtime monitoring. |
| Sentry / error monitoring | Production error capture. | Paid product needs visibility into failures. | Use after core app is deployable. | Frontend/backend exceptions get reported with stack traces. | Job queue status by itself; still need worker/workflow monitoring. |
| Email provider | Transactional email service. | Password reset, verification, invites, reports. | Use instead of sending raw SMTP yourself. | FastAPI/Celery/Temporal calls provider API with rendered template. | Permanent user identity/auth source. |
| Jinja2 email templates | Python template system. | Clean backend-generated HTML/text emails. | Use only for transactional emails. | FastAPI/Celery renders password_reset.html and .txt, sends via provider. | Main frontend pages; use Next.js/React. |
