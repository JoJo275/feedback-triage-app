# SignalNest (Feedback Triage App)

Portfolio-grade FastAPI + PostgreSQL app for triaging customer feedback.

The single source of truth for **what** to build is the
[Project Spec v2.0](project/spec/spec-v2.md) (Ratified 2026-05-04).
The companion [v2.0 Implementation Plan](project/spec/v2/implementation.md)
sequences the work into phases with explicit definitions of done.
[Spec v1.0](project/spec/spec-v1.md) and its
[Implementation Plan](project/implementation.md) remain available as
historical reference for the shipped v1.0 codebase.

## Quick links

| Resource                                              | Description                                |
| ----------------------------------------------------- | ------------------------------------------ |
| [Project Spec v2.0](project/spec/spec-v2.md)         | **Authoritative** product, schema, and API spec |
| [v2.0 Implementation Plan](project/spec/v2/implementation.md) | Phase-by-phase build plan for v2.0 |
| [Project Spec v1.0](project/spec/spec-v1.md)         | Historical v1.0 spec (shipped)             |
| [Open Questions](project/questions.md)                | Tracked open questions & decisions         |
| [Deployment Notes](project/deployment-notes.md)       | Railway operational notes                  |
| [ADRs](adr/README.md)                                 | Architecture Decision Records              |
| [Workflows](workflows.md)                             | GitHub Actions inventory                   |
| [Known Issues](known-issues.md)                       | Current limitations and gotchas            |

## Tech stack

- **API:** FastAPI
- **ORM:** SQLModel on SQLAlchemy 2.x
- **Database:** PostgreSQL 16 + Alembic migrations
- **Frontend:** Server-rendered Jinja2 + Tailwind + htmx + Alpine.js (v2.0)
- **Tests:** pytest + httpx TestClient + Playwright (smoke)
- **Build/env:** uv + hatchling + hatch-vcs
- **Container:** Multi-stage `Containerfile`, non-root, healthcheck on `/health`
- **Deploy:** Railway with `alembic upgrade head` as pre-deploy command

When this site and the spec disagree, the spec wins.
