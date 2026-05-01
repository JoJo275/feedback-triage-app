# Feedback Triage App

Portfolio-grade FastAPI + PostgreSQL app for triaging customer feedback.

The single source of truth for **what** to build is the
[Project Spec v1.0](project/spec/spec-v1.md). The companion
[Implementation Plan](project/implementation.md) sequences the work into
phases with explicit definitions of done.

## Quick links

| Resource                                              | Description                                |
| ----------------------------------------------------- | ------------------------------------------ |
| [Project Spec v1.0](project/spec/spec-v1.md)         | Canonical product, schema, and API spec    |
| [Implementation Plan](project/implementation.md)      | Phase-by-phase build plan                  |
| [Open Questions](project/questions.md)                | Tracked open questions & decisions         |
| [Deployment Notes](project/deployment-notes.md)       | Railway operational notes                  |
| [ADRs](adr/README.md)                                 | Architecture Decision Records              |
| [Workflows](workflows.md)                             | GitHub Actions inventory                   |
| [Known Issues](known-issues.md)                       | Current limitations and gotchas            |

## Tech stack

- **API:** FastAPI (sync routes in v1.0)
- **ORM:** SQLModel on SQLAlchemy 2.x
- **Database:** PostgreSQL 16 + Alembic migrations
- **Frontend:** Static HTML + vanilla JS (no Jinja, no SPA)
- **Tests:** pytest + httpx TestClient + Playwright (smoke)
- **Build/env:** uv + hatchling + hatch-vcs
- **Container:** Multi-stage `Containerfile`, non-root, healthcheck on `/health`
- **Deploy:** Railway with `alembic upgrade head` as pre-deploy command

When this site and the spec disagree, the spec wins.
