# Tool Pages

This directory contains tool-specific pages generated from the active inventory in docs/tooling.md, plus additional active workflow and platform tools in current use.

## Index

| Tool | Page | Scope |
| --- | --- | --- |
| actionlint | [actionlint.md](actionlint.md) | CI workflow quality |
| Alembic | [alembic.md](alembic.md) | Data migrations |
| Alpine.js | [alpine-js.md](alpine-js.md) | Operations UI |
| axe-core / @axe-core/playwright | [axe-core-at-axe-core-playwright.md](axe-core-at-axe-core-playwright.md) | Frontend accessibility testing |
| Bandit | [bandit.md](bandit.md) | Application security |
| check-jsonschema | [check-jsonschema.md](check-jsonschema.md) | Config validation |
| Codecov | [codecov.md](codecov.md) | Test coverage reporting |
| CodeQL | [codeql.md](codeql.md) | Application security |
| commitizen | [commitizen.md](commitizen.md) | Release workflow |
| CSS variables / design tokens | [css-variables-design-tokens.md](css-variables-design-tokens.md) | Frontend styling |
| Dependabot | [dependabot.md](dependabot.md) | Dependency updates |
| deptry | [deptry.md](deptry.md) | Dependency hygiene |
| Dev Containers | [dev-containers.md](dev-containers.md) | Developer environment |
| Docker / Podman | [docker-podman.md](docker-podman.md) | Container runtime |
| Docker Compose | [docker-compose.md](docker-compose.md) | Local orchestration |
| Email provider | [email-provider.md](email-provider.md) | Email delivery |
| ESLint | [eslint.md](eslint.md) | Frontend quality |
| FastAPI | [fastapi.md](fastapi.md) | Backend API |
| FastAPI + Jinja2 (dashboard app) | [fastapi-and-jinja2-dashboard-app.md](fastapi-and-jinja2-dashboard-app.md) | Operations UI |
| GitHub Actions | [github-actions.md](github-actions.md) | CI/CD |
| GitHub Dependency Review | [github-dependency-review.md](github-dependency-review.md) | CI security |
| GitHub Pages | [github-pages.md](github-pages.md) | Documentation hosting |
| gitleaks | [gitleaks.md](gitleaks.md) | Secret security |
| hadolint | [hadolint.md](hadolint.md) | Container linting |
| hatchling + hatch-vcs | [hatchling-and-hatch-vcs.md](hatchling-and-hatch-vcs.md) | Cross-repo |
| htmx | [htmx.md](htmx.md) | Operations UI |
| Jinja2 email templates | [jinja2-email-templates.md](jinja2-email-templates.md) | Email templating |
| lychee | [lychee.md](lychee.md) | Documentation validation |
| markdownlint-cli2 | [markdownlint-cli2.md](markdownlint-cli2.md) | Documentation linting |
| Material for MkDocs | [material-for-mkdocs.md](material-for-mkdocs.md) | Documentation |
| MkDocs | [mkdocs.md](mkdocs.md) | Documentation |
| MkDocs hooks (mkdocs-hooks/*.py) | [mkdocs-hooks-mkdocs-hooks-py.md](mkdocs-hooks-mkdocs-hooks-py.md) | Documentation build |
| mkdocstrings | [mkdocstrings.md](mkdocstrings.md) | Documentation API refs |
| mypy | [mypy.md](mypy.md) | Python quality |
| Node.js + npm | [node-js-and-npm.md](node-js-and-npm.md) | Frontend toolchain |
| OpenAPI Type Generation (openapi-typescript) | [openapi-type-generation-openapi-typescript.md](openapi-type-generation-openapi-typescript.md) | API contract |
| OpenSSF Scorecard | [openssf-scorecard.md](openssf-scorecard.md) | Repository security |
| pip-audit | [pip-audit.md](pip-audit.md) | Supply chain security |
| pip-licenses | [pip-licenses.md](pip-licenses.md) | Supply chain governance |
| Playwright | [playwright.md](playwright.md) | E2E testing |
| PostgreSQL 16 | [postgresql-16.md](postgresql-16.md) | Data store |
| pre-commit | [pre-commit.md](pre-commit.md) | Developer workflow |
| Prettier | [prettier.md](prettier.md) | Content formatting |
| Pydantic | [pydantic.md](pydantic.md) | Backend API |
| PyPI Publish Action | [pypi-publish-action.md](pypi-publish-action.md) | Release publishing |
| pytest | [pytest.md](pytest.md) | Backend testing |
| pytest-cov | [pytest-cov.md](pytest-cov.md) | Test coverage |
| Railway | [railway.md](railway.md) | Deployment platform |
| React | [react.md](react.md) | Frontend UI |
| React Testing Library | [react-testing-library.md](react-testing-library.md) | Frontend testing |
| release-please | [release-please.md](release-please.md) | Release automation |
| Ruff | [ruff.md](ruff.md) | Python quality |
| SQLModel / SQLAlchemy 2.x | [sqlmodel-sqlalchemy-2-x.md](sqlmodel-sqlalchemy-2-x.md) | Backend data |
| Syft | [syft.md](syft.md) | Supply chain security |
| Tailwind CSS (Standalone CLI) | [tailwind-css-standalone-cli.md](tailwind-css-standalone-cli.md) | Frontend styling |
| Task | [task.md](task.md) | Cross-repo |
| Trivy + Grype | [trivy-and-grype.md](trivy-and-grype.md) | Container security |
| TypeScript | [typescript.md](typescript.md) | Frontend typing |
| typos + codespell | [typos-and-codespell.md](typos-and-codespell.md) | Content quality |
| useState | [usestate.md](usestate.md) | Frontend local state |
| uv | [uv.md](uv.md) | Cross-repo |
| validate-pyproject | [validate-pyproject.md](validate-pyproject.md) | Packaging metadata |
| Vite + React (v2 runtime) | [vite-and-react-v2-runtime.md](vite-and-react-v2-runtime.md) | Frontend runtime |
| Vitest | [vitest.md](vitest.md) | Frontend testing |

## Template

- [TOOL_PAGE_TEMPLATE.md](TOOL_PAGE_TEMPLATE.md)

## Maintenance

1. Update docs/tooling.md when tool status or boundaries change.
2. Regenerate or edit matching pages in this directory.
3. Keep CI, workflow, and deployment tool pages aligned with .github/workflows/ and runtime config files.
