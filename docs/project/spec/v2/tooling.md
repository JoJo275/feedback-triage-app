# v2.0 — Tooling Stack

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).

---

## Backend

| Item                          | Status vs. v1.0  | Notes                                                  |
| ----------------------------- | ---------------- | ------------------------------------------------------ |
| FastAPI                       | ✅ same           | sync routes ([ADR 050](../../../adr/050-sync-db-driver-v1.md)) |
| Uvicorn                       | ✅ same           | —                                                      |
| SQLAlchemy 2.0 / SQLModel     | ✅ same           | —                                                      |
| Alembic                       | ✅ same           | hand-reviewed migrations                                |
| Pydantic v2                   | ✅ same           | —                                                      |
| `pydantic-settings`           | ✅ same           | —                                                      |
| `argon2-cffi`                 | 🆕               | password hashing ([ADR 059](../../../adr/059-auth-model.md)) |
| `resend`                      | 🆕               | transactional email ([ADR 061](../../../adr/061-resend-email-fail-soft.md)) |
| `psycopg[binary]`             | ✅ same           | sync driver                                             |
| `httpx`                       | ✅ test-only      | —                                                      |

`asyncpg`, `python-jose`/`pyjwt`, `passlib`, `fastapi-users` —
**not** introduced. See
[ADR 050](../../../adr/050-sync-db-driver-v1.md) and
[ADR 059](../../../adr/059-auth-model.md).

---

## Frontend / build

| Item                                  | Notes                                                       |
| ------------------------------------- | ----------------------------------------------------------- |
| Tailwind CSS (Standalone CLI binary)  | [ADR 058](../../../adr/058-tailwind-via-standalone-cli.md). `task build:css`. No Node, no `package.json`. |
| Lucide static SVGs                    | hand-exported into `static/img/icons/`                       |
| Playwright (Python)                   | gated `@pytest.mark.e2e` smoke suite                         |
| `axe-core` (via Playwright)           | per-page accessibility check in the e2e suite ([`ui.md`](ui.md)) |

No bundler, no React, no Vite, no TypeScript on the frontend.

---

## Test stack

| Item                          | Notes                                                              |
| ----------------------------- | ------------------------------------------------------------------ |
| pytest                        | unchanged                                                          |
| `pytest-postgresql`           | ephemeral Postgres per session (ADR for ephemeral test DB — TBD) |
| Playwright (Python)           | gated `@pytest.mark.e2e`                                           |
| `axe-core` integration        | accessibility regression                                           |
| Cross-tenant canary fixture   | `client_w1` / `client_w2` for tenant-isolation tests               |

---

## Build / dev tooling

| Item                          | Notes                                                              |
| ----------------------------- | ------------------------------------------------------------------ |
| uv                            | env + lockfile + Python install                                    |
| hatchling + hatch-vcs         | build backend, version from git tags                               |
| Task (Taskfile.yml)           | `task dev`, `task build:css`, `task test`, `task test:e2e`, `task check` |
| pre-commit                    | ruff, mypy, bandit, typos, pip-audit, gitleaks, commitizen, custom hooks |
| Dependabot                    | weekly dep PRs                                                     |
| Containerfile                 | multi-stage; non-root; `HEALTHCHECK /health`                        |
| docker-compose                | local Postgres + app                                               |

---

## Email-provider snapshot (re-verify before launch)

> **Pricing claims dated May 2026.** Re-verify against the
> provider's current page before committing.

| Provider         | Free tier (May 2026)                          | Verdict                              |
| ---------------- | --------------------------------------------- | ------------------------------------ |
| **Resend**       | 3,000 emails/month                            | Best DX. Recommended.                |
| Mailgun          | 100/day                                       | Mature; sales-heavy UX.              |
| Amazon SES       | $0.10/1k                                      | Cheapest long-term; AWS overhead.    |
| SendGrid         | 60-day trial then 100/day                     | Skip for cost-sensitive demo.        |

Expected v2.0 volume well under 1k / month → free tier
indefinitely.

---

## Cross-references

- [`auth.md`](auth.md) — what `argon2-cffi` is doing.
- [`email.md`](email.md) — what `resend` is doing.
- [`ui.md`](ui.md) — what Tailwind + Lucide are doing.
- [`rollout.md`](rollout.md) — what runs in CI per tag.
