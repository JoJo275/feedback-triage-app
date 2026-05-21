# Tool Inventory

!!! danger "Read This Before Editing Tool Choices"
    This document labels the tools used in this repository and records their boundaries.
    For end-to-end guidance on how these tools are applied in day-to-day delivery, see [development/development-framework.md](development/development-framework.md).

Project tool inventory with practical guidance for each tool:

- **Why** this tool exists in this repo.
- **When** to use it in day-to-day development.
- **How** to use it here (entrypoint commands and config location).
- **What** each tool is responsible for.
- **Avoid** boundaries to prevent tool overlap.

## Operating Layers

| Tool | What it is | Why | When | How | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| [uv](https://docs.astral.sh/uv/) | Python environment, dependency, and lockfile manager. | Single source of truth for Python environment and lockfile management. | Any dependency or environment change. | `uv sync`, `uv add <pkg>`, `uv run <cmd>`. Config in `pyproject.toml`; lockfile is `uv.lock`. | Ad-hoc package installs or unmanaged virtualenv workflows that bypass `uv.lock`. |
| [hatchling](https://hatch.pypa.io/latest/config/build/) + [hatch-vcs](https://github.com/ofek/hatch-vcs) | Python build backend plus git-tag-based versioning plugin. | Build backend and versioning from git tags. | Building distributions or packaging in CI/image builds. | `uv build` (invokes hatchling). Build config in `pyproject.toml` under `[build-system]` and `[tool.hatch.version]`. | Runtime dependency management or manual version stamping outside the tag-driven release flow. |
| [Task](https://taskfile.dev/) | Task runner for project command aliases and repeatable workflows. | Human-friendly wrappers for frequent command sequences. | Daily workflows when you want short, discoverable commands. | `task --list`, `task test`, `task check`, `task dev`. Config in `Taskfile.yml`. | Hiding complex business logic that should live in versioned scripts, app code, or CI workflows. |

## Application Runtime

| Tool | What it is | Why | When | How | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| [FastAPI](https://fastapi.tiangolo.com/) | Python API framework based on Python type hints; built for APIs. | Keeps the API boundary explicit while hosting backend business logic and the web shell. | Defining routes, request/response models, middleware, and API contracts. | App code in `src/feedback_triage/`; run via `task dev` or `uv run uvicorn feedback_triage.main:app --reload`. For web app shells, frontend routes call `/api/v1/` endpoints exposed by FastAPI. | Frontend rendering/layout, chart hover state, dashboard drag UI, or client-only interactivity. |
| [SQLModel](https://sqlmodel.tiangolo.com/) / SQLAlchemy 2.x | Python SQL toolkit/ORM layer for typed relational modeling and queries. | Typed ORM models and DB access patterns for reliable CRUD and transactional behavior. | Model/schema and CRUD changes. | Models in `src/feedback_triage/models.py`; session-per-request via `get_db` dependency; service functions query PostgreSQL through ORM/session patterns. | Temporary cache/rate-limit counters or durable workflow orchestration concerns. |
| [Pydantic](https://docs.pydantic.dev/) | Python data validation and serialization layer used by FastAPI. | Validates request/response models and keeps API contracts clear and typed. | Defining API schemas and internal typed data models. | Request/response schemas are defined in the app schema modules (for example, response DTOs and create/update payload models). | Long-term DB schema migrations or relational schema evolution (use Alembic for those). |
| OpenAPI Generator | API client and type generation tooling based on OpenAPI schemas. | Keeps FastAPI and frontend types aligned from a shared contract. | Use when API surface changes need synchronized frontend models/clients. | Generate typed clients/models from the FastAPI OpenAPI document as part of frontend build or CI checks. | Hand-maintaining duplicate backend/frontend API types that drift over time. |
| [Alembic](https://alembic.sqlalchemy.org/) | Database migration tool for SQLAlchemy-backed projects. | Versioned schema migrations with reviewable history. | Any DB schema change. | `task migration m="desc"`, `task migrate`; migration files in `alembic/versions/`; add and review migration files for every schema change. | Runtime data processing pipelines or request-time app business logic. |
| PostgreSQL 16 | Primary relational database and source-of-truth store. | Production and test DB dialect baseline with durable relational guarantees. | Local dev DB, integration tests, migration validation, and permanent product data storage. | Local stack via `task up` / `docker-compose.yml`; `DATABASE_URL` from env; stores users/workspaces/signals/layouts and related records. | Short-lived counters, cache, ephemeral locks, or temporary rate-limit state. |

## Background Processing and Messaging

| Tool | What it is | Why | When | How | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| [Temporal](https://temporal.io/) | Durable workflow platform; workflows can resume after crashes/outages. | Durable workflow execution for long-running or multi-step business processes with retries and resumability. | Imports, AI classification, onboarding flows, weekly reports, webhook workflows with failure recovery. | Use for workflows only. Keep permanent product state in PostgreSQL. See `docs/design/background-processing-architecture.md`. | High-volume throwaway events, simple cache operations, and rate limits. |
| [Celery](https://docs.celeryq.dev/) | Python distributed task queue with broker-backed workers. | Handles short independent Python jobs, especially when many small tasks are expected. | Single-purpose jobs like password reset email, email verification, invite email, and lightweight cleanup tasks. | Use workers for discrete tasks, not durable multi-step orchestration. Pair with RabbitMQ as broker. | Durable multi-step workflows that need history/progress/recovery semantics (use Temporal). |
| [RabbitMQ](https://www.rabbitmq.com/) | Message broker for queueing and task routing. | Message transport and routing for Celery tasks. | Celery task message delivery and queue routing. | Use as Celery broker only; do not use it as cache, rate-limit store, or permanent state store. | Cache, rate limits, and source-of-truth product data persistence. |
| [Redis](https://redis.io/) | Fast in-memory store for temporary shared state. | Fast temporary state store for latency-sensitive controls. | Distributed rate limits, caching, short-lived counters, and transient locks. | Keep data ephemeral. Do not use as source-of-truth or durable workflow state. | Permanent business records and durable workflow history/state. |

## Frontend and Dashboard

| Tool | What it is | Why | When | How | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| [Vite](https://vitejs.dev/) + React (v2 runtime) | Frontend build/runtime pipeline currently used for migrated v2 React pages. | Frontend build/runtime for migrated v2 pages. | Editing code under `web/src/`. | `npm --prefix web run build` for production assets; source in `web/`, emitted assets consumed by backend shell routes. | Server-side API/business logic, background orchestration, or permanent data rules. |
| Next.js | React framework for building full-stack web applications; it adds routing, rendering, optimization, and build tooling around React. | Gives a SaaS frontend a stronger app-shell framework with routes, layouts, loading states, and error boundaries. | Use when adopting a Next.js app shell for frontend route/layout orchestration. | User opens `/dashboard`; Next.js renders the page, runs React components, and calls FastAPI through an API client/TanStack Query layer. | Core Python business logic, background jobs, and source-of-truth data rules. |
| React | UI component library. | Lets teams build reusable dashboard widgets, forms, modals, tables, cards, and charts. | Use for all interactive frontend UI. | Components like cards/tables/charts are composed into pages and bound to API-driven data/state. | Backend logic and direct database access. |
| TypeScript | Strongly typed language that builds on JavaScript and improves editor/type-checking support. | Stronger frontend contracts plus better editor and AI assistance across the codebase. | Use across the whole frontend. | Define types for widgets, signals, API responses, Redux state, and route parameters. | Runtime validation by itself when inputs are untrusted (pair with runtime validators/backend validation). |
| Zod | TypeScript-first runtime schema validation library. | Adds runtime validation for forms, env inputs, URL params, and localStorage payloads. | Use wherever user/browser/runtime input must be validated at execution time. | Define schemas near input boundaries, parse/validate incoming values, and surface typed validated data to components/services. | Replacing API contract source-of-truth or long-term relational schema migrations. |
| useState | React hook for small local component state. | Keeps tiny local UI state simple and explicit. | Use for isolated UI state such as toggles, selected tabs, and simple form interactions. | Store minimal per-component state values and update directly with setter functions. | Complex multi-action state transitions or cross-component shared state. |
| useReducer | React hook for reducer-driven local state transitions. | Better for complex local state with multiple actions and deterministic transitions. | Use when component-local state logic grows beyond straightforward `useState` updates. | Model state updates as actions with a reducer function for traceable, testable transitions. | Global app state synchronization or server-state caching concerns. |
| Zustand | Lightweight shared state library for React apps. | Small shared UI state without full Redux ceremony. | Use for compact cross-component UI state where reducers/middleware are unnecessary. | Create small stores for shared client state and consume via hook selectors in components. | Undo/redo-heavy editor flows or very complex dashboard state graphs needing stricter structure. |
| Tailwind CSS | Utility-first CSS framework. | Fast, consistent styling for dashboard UI. | Use for layout, spacing, color, and typography utilities. | Components use utility classes plus project design tokens. | Replacing design-system thinking; utility classes alone are not a design system. |
| CSS variables / design tokens | Named CSS values for color, spacing, radius, and shadow decisions. | Keeps theme decisions consistent and easier to evolve. | Use for brand color systems, density, and semantic styling primitives. | Define reusable tokens (for example color, radius, and spacing scales) and consume them in component styles. | One-off, untracked styling values scattered across unrelated components. |
| shadcn/ui | Copy-in React component patterns commonly built with Radix + Tailwind; source stays in your repo. | Speeds up accessible UI primitives without locking the project into a monolithic UI library. | Use for buttons, dialogs, dropdowns, tooltips, forms, sheets, and command menus. | Add component source to the repo, then customize to project styling and UX requirements. | App-specific widgets that should be purpose-built (for example, custom signal visualizations). |
| Radix UI | Low-level accessible UI primitives. | Good accessibility-focused foundation for menus, popovers, dialogs, tooltips, and tabs. | Use through shadcn/ui or directly when accessibility primitives are needed. | Radix provides behavior/accessibility primitives and project styles provide the visual language. | Data charts, dashboard layout logic, and backend concerns. |
| TanStack Query | Server-state library for fetching, caching, synchronizing, and updating backend data. | Prevents ad-hoc fetch/loading/error/cache logic spread through components. | Use for FastAPI-backed data flows: signals, users, workspaces, summaries, and tags. | Components issue typed queries/mutations and invalidate/refetch related caches after writes. | Pure local UI state like hover/tooltips/drag state that does not represent server state. |
| Redux Toolkit | Structured global/client state management layer (`createSlice` reducers/actions). | Best fit for undo/redo plus complex dashboard layout state and multi-slice coordination. | Use for complex dashboard editor state. | Store draft layout, saved layout, undo/redo stacks, selection, edit mode, and breakpoint-specific editor state. | Server-state synchronization concerns that belong in TanStack Query. |
| [FastAPI](https://fastapi.tiangolo.com/) + [Jinja2](https://jinja.palletsprojects.com/) (dashboard app) | Server-rendered dashboard stack for internal environment tooling. | Internal environment dashboard server-rendered UI. | Working in `tools/dev_tools/env_dashboard/`. | Run dashboard task/command; templates in `tools/dev_tools/env_dashboard/templates/`. | Replacing the main frontend runtime where SPA-style component composition is required. |
| [htmx](https://htmx.org/) | HTML-driven partial update library for dynamic server-rendered pages. | Partial-page updates without SPA overhead in dashboard views. | Adding dynamic section refresh/filter behavior in dashboard templates. | Add `hx-*` attributes in dashboard templates; backend serves partial endpoints. | Complex client-side application state orchestration across many independent views. |
| [Alpine.js](https://alpinejs.dev/) | Lightweight declarative client-state layer for server-rendered pages. | Lightweight client state in dashboard pages. | Local state toggles/search UI behavior in templates. | Use `x-data`, `x-show`, `x-on` patterns in dashboard templates. | Full application-wide state management with complex data synchronization needs. |

## Quality and Testing

| Tool | What it is | Why | When | How | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| ESLint | JavaScript/TypeScript linting framework with ecosystem plugin support. | Catches JS/TS/React problems early before runtime and review. | Use on frontend changes and CI quality gates for `web/` code. | Run with the frontend toolchain/lint scripts and enforce rule sets for TS, React, hooks, and imports. | Replacing type-checking, runtime validation, or end-to-end behavioral tests. |
| [Ruff](https://docs.astral.sh/ruff/) | Python linter and formatter. | Fast lint + format baseline for Python code quality. | Before committing any Python/doc tooling edits touching linted files. | `task lint`, `task fmt`, or `uv run ruff check src tests scripts`. Config in `pyproject.toml` (`[tool.ruff]`). | Replacing static typing, security analysis, or runtime behavior tests. |
| [mypy](https://mypy.readthedocs.io/) | Static type checker for Python. | Static type safety for `src/feedback_triage/`. | Public API changes, schema/model changes, refactors. | `task typecheck` or `uv run mypy src/`. Config in `pyproject.toml` (`[tool.mypy]`). | Runtime input validation or behavioral/regression test coverage. |
| [pytest](https://docs.pytest.org/) | Python test framework focused on scalable test suites. | Primary automated test runner for backend confidence. | API/model/business logic verification. | `task test`, `task test:k -- <expr>`. Config in `pyproject.toml` (`[tool.pytest.ini_options]`); CI runs backend suites before deploy. | Browser UI testing. |
| [pytest-cov](https://pytest-cov.readthedocs.io/) | Coverage measurement plugin for pytest. | Coverage reporting for test completeness. | Coverage checks and regression analysis. | `task test:cov` or pytest with `--cov`. Coverage config in `pyproject.toml`. | Judging correctness by coverage percentage alone without quality assertions. |
| Vitest | JS/TS unit and component test runner. | Fast frontend tests for component and utility layers. | Use for pure functions, React components, and reducer logic in frontend code. | Run frontend unit/component tests for slices, components, and utility modules. | Full browser flow validation (use Playwright for end-to-end behavior). |
| React Testing Library | Component testing approach focused on user-visible behavior. | Encourages resilient React tests aligned to user interactions. | Use for widgets/forms/components. | Render components and assert text/state/interaction outcomes from a user perspective. | Backend logic and database-access testing. |
| MSW | Mock Service Worker for API mocking in browser and test environments. | Mocks API states for tests, local dev, and Storybook scenarios. | Use when frontend behavior must be exercised against deterministic success/error/edge API responses. | Define request handlers that intercept network calls and return controlled fixtures for tests/dev/stories. | Replacing integration/e2e coverage against real backend behavior. |
| [Playwright](https://playwright.dev/python/) | End-to-end browser automation framework for modern web apps. | Browser-level smoke/e2e checks to prevent critical flow regressions. | Frontend shell/page flow changes and UI parity checks. | `task test:e2e` (gated/opt-in). Tests under `tests/e2e/`; use for critical smoke paths. | Unit testing small functions. |
| [deptry](https://deptry.com/) | Python dependency analysis tool for missing/unused/transitive drift. | Detects missing/unused/transitive dependency drift. | Dependency cleanups or unexplained import failures. | `task deptry` or `uv run deptry .`. Config in `pyproject.toml`. | Replacing lockfile management or package vulnerability scanning. |
| [typos](https://github.com/crate-ci/typos) + [codespell](https://github.com/codespell-project/codespell) | Spelling and typo detection tools for code/docs/config text. | Catch spelling mistakes in code/docs/config. | Content edits across docs, code, and workflow files. | Runs in pre-commit/CI; manual via `uv run typos` and `uv run codespell`. Config in `_typos.toml` and workflow hooks. | Semantic documentation review or technical correctness verification. |

## Security and Supply Chain

| Tool | What it is | Why | When | How | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| [Bandit](https://bandit.readthedocs.io/) | Python security static analysis tool. | Python security linting for common risky patterns. | Any Python changes before merge. | `task security` or `uv run bandit -c pyproject.toml -r src/`. | Dependency vulnerability inventory or infrastructure/container scanning. |
| [pip-audit](https://github.com/pypa/pip-audit) | Python dependency vulnerability scanner. | Dependency vulnerability detection. | Dependency updates, release readiness checks. | Run via pre-commit/CI or `uv run pip-audit`. | Static code-pattern security analysis of application logic. |
| [gitleaks](https://github.com/gitleaks/gitleaks) | Secret scanning tool for git history and staged content. | Secret scanning for commits/history. | Before pushing when handling env/config/secrets-adjacent changes. | Runs in pre-push/CI; config in `.gitleaks.toml` if present. | Runtime secret management, key rotation, or credential storage policy enforcement. |
| [CodeQL](https://codeql.github.com/) | Semantic code analysis engine integrated with GitHub code scanning. | Semantic code scanning in GitHub CI. | PR validation for security regressions. | Workflow: `.github/workflows/security-codeql.yml`. | Dependency update automation or infrastructure-level hardening checks. |
| [OpenSSF Scorecard](https://scorecard.dev/) | Repository security posture benchmarking tool. | Repository security posture checks. | Periodic posture review and release governance. | Workflow: `.github/workflows/scorecard.yml`. | Deep, repo-specific static analysis of project code paths. |

## Documentation Stack

| Tool | What it is | Why | When | How | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| [MkDocs](https://www.mkdocs.org/) | Static site generator for project documentation. | Static documentation site generator. | Any docs changes that should be validated as a site. | `uv run mkdocs serve` or `uv run mkdocs build --strict`. Main config: `mkdocs.yml`. | Replacing runtime user-facing UI or application API documentation generated at request time. |
| [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) | Theme and UX extension package for MkDocs. | Site theme and docs UX features. | Navigation/theme/layout changes in docs site. | Configure via `theme:` in `mkdocs.yml`. | Serving as a frontend framework for product application pages. |
| [mkdocstrings](https://mkdocstrings.github.io/) | API documentation extraction/generation plugin. | API reference generation from Python docstrings. | Updating docs/reference API pages. | Plugin configured in `mkdocs.yml`; resolves modules from `src/`. | Replacing test coverage or code review of API behavior. |
| MkDocs hooks (`mkdocs-hooks/*.py`) | Repository-specific build-time documentation transformation hooks. | Repo-specific docs transformations and generation. | Repo link rewriting, command reference generation, template inclusion behavior. | Hook registration in `mkdocs.yml` `hooks:` section. | General application runtime logic outside documentation build workflows. |

## Git and Release Automation

| Tool | What it is | Why | When | How | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| [pre-commit](https://pre-commit.com/) | Framework for running versioned checks before commits/pushes. | Local quality/security gate before commits. | Always before commit/push in active branches. | `pre-commit install`, `pre-commit run --all-files`; config in `.pre-commit-config.yaml`. | Replacing CI enforcement or repository branch protection controls. |
| [commitizen](https://commitizen-tools.github.io/commitizen/) | Conventional Commit tooling for message validation/authoring. | Conventional Commit validation and guided commit authoring. | Writing structured commit messages and enforcing release semantics. | `task commit` or `uv run cz commit`; config in `pyproject.toml` (`[tool.commitizen]`). | Automated semantic release execution by itself without the configured release workflow. |
| [GitHub Actions](https://docs.github.com/en/actions) | CI/CD automation platform for repository workflows. | Prevents broken code from merging/deploying with gated validation and automation. | All PR and merge validation, release automation, scans. | Workflow files in `.github/workflows/`; lint with `actionlint`; CI runs frontend/backend checks and release/security jobs. | Runtime monitoring and production observability responsibilities. |
| [release-please](https://github.com/googleapis/release-please) | Automated release-PR and changelog workflow based on commit history. | Automated changelog/release PR from commit history. | Preparing tagged releases with consistent changelog flow. | Config in `release-please-config.json`; runs in release workflow. | Replacing required manual review and release governance approvals. |
| [Dependabot](https://docs.github.com/en/code-security/dependabot) | Automated dependency update PR generator. | Automated dependency update PR creation. | Ongoing dependency hygiene and CVE response. | Config in `.github/dependabot.yml`. | Confirming runtime compatibility without tests or review. |

## Containers and Local Infra

| Tool | What it is | Why | When | How | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| [Docker](https://www.docker.com/) / [Podman](https://podman.io/) | OCI container engines for building/running application images. | Consistent deploy/runtime environment and local parity. | Building/running service containers locally or in CI. | Build from `Containerfile`; local stack in `docker-compose.yml`. | Replacing tests, observability, or business workflow orchestration. |
| Docker Compose | Multi-service local orchestration for containerized dependencies. | Multi-service local orchestration (app + Postgres). | Local integration testing and DB-backed dev workflows. | `task up`, `task down` (or `docker compose up/down`). | Production orchestration and autoscaling concerns that need dedicated platforms. |
| [Trivy](https://trivy.dev/) + [Grype](https://github.com/anchore/grype) | Container vulnerability scanners with complementary advisory data. | Container vulnerability scanning with complementary DBs. | Image security checks in CI/release gates. | Run in `.github/workflows/container-scan.yml`. | Runtime intrusion detection or application-level authorization checks. |

## Validation and Hygiene Utilities

| Tool | What it is | Why | When | How | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| [actionlint](https://github.com/rhysd/actionlint) | Static linter for GitHub Actions workflows. | Static lint for GitHub Actions syntax and expressions. | Any workflow edit before pushing. | `uv run actionlint` from repo root. | Runtime CI debugging, test execution, or workflow policy governance. |
| [check-jsonschema](https://github.com/python-jsonschema/check-jsonschema) | Schema validation CLI for JSON/YAML configuration files. | Schema validation for YAML/JSON configs. | Editing workflow/dependabot/structured config files. | Runs in CI/pre-commit according to hook configuration. | Semantic behavior checks that require executing the application. |
| [validate-pyproject](https://validate-pyproject.readthedocs.io/) | Validator for Python packaging metadata in `pyproject.toml`. | Validates packaging metadata structure. | Editing `pyproject.toml`. | Run via pre-commit/CI or `uv run validate-pyproject pyproject.toml`. | Dependency vulnerability analysis or environment lockfile reconciliation. |
| [lychee](https://github.com/lycheeverse/lychee) | Link checker for markdown/docs/site outputs. | Broken-link detection in docs and site output. | Documentation changes, especially link-heavy updates. | CI workflow `.github/workflows/link-checker.yml`; local run with lychee CLI. | Content quality review beyond URL reachability. |

## Observability and Communication

| Tool | What it is | Why | When | How | Avoid using it for |
| --- | --- | --- | --- | --- | --- |
| Sentry / error monitoring | Application error capture and aggregation platform. | Paid product operations need visibility into production failures. | Use after core app/runtime paths are deployed and traffic is active. | Frontend/backend exceptions are reported with stack traces and linked metadata for triage. | Job queue status tracking by itself; still pair with worker/workflow health monitoring. |
| Email provider | Transactional email delivery service. | Handles password reset, verification, invite, and report delivery reliably. | Use instead of sending raw SMTP directly from app processes. | FastAPI/Celery/Temporal integrations call provider APIs using rendered templates and event logging semantics. | Permanent user identity/auth source or long-term account state storage. |
| Jinja2 email templates | Python templating layer for HTML/text transactional email bodies (email plates/templates). | Keeps backend-generated transactional email content consistent and maintainable. | Use for transactional email rendering flows. | FastAPI/Celery render HTML/TXT templates (for example password reset and verification) before sending through email provider integrations. | Main frontend application pages or interactive SPA route rendering. |
| MJML | Component-oriented markup language compiled to responsive HTML emails. | Improves maintainability and responsiveness of email layouts across clients. | Use when email layouts become complex and plain HTML templates are hard to maintain. | Author MJML templates, compile to provider-friendly HTML, and deliver through backend/provider email pipelines. | Interactive web-page rendering or frontend application route/layout concerns. |
| Provider email templates (deferred) | Email content/templates managed directly in the delivery provider platform. | Allows late-binding copy/layout edits without app deploys when governance permits. | Maybe later: adopt if product operations need provider-side template management. | Store template versions in the provider, pass dynamic variables from app/workers, and keep identifiers versioned in code/docs. | Replacing source-controlled critical templates where auditability and code review are required. |

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
