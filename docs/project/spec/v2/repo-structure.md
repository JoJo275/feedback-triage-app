# v2.0 — Repository structure

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Authoritative for src/ layout under v2.0. When this conflicts with
> [`../spec-v1.md`](../spec-v1.md) for the v2.0 codebase, this file
> wins.

---

## Top-level layout

```text
feedback-triage-app/
├── src/
│   └── feedback_triage/            # Python package (import root)
│       ├── __init__.py
│       ├── main.py                 # FastAPI app factory
│       ├── config.py               # pydantic-settings, env-driven
│       ├── database.py             # engine, get_db, session lifecycle
│       ├── enums.py                # native PG enum bindings
│       ├── errors.py               # exception → response mapping
│       ├── middleware.py           # request id, security headers
│       ├── auth/                   # NEW v2.0 — sessions, hashing, deps
│       │   ├── __init__.py
│       │   ├── deps.py             # CurrentUser, RequireSession
│       │   ├── hashing.py          # Argon2id wrapper
│       │   ├── sessions.py         # cookie-session CRUD + rolling renewal
│       │   └── tokens.py           # email-verify / reset / invite tokens
│       ├── tenancy/                # NEW v2.0 — workspace context
│       │   ├── __init__.py
│       │   ├── context.py          # WorkspaceContext dependency
│       │   └── policies.py         # role checks (owner, member)
│       ├── email/                  # NEW v2.0 — Resend client + templates
│       │   ├── __init__.py
│       │   ├── client.py           # fail-soft send wrapper
│       │   └── templates/          # plain-text + minimal HTML
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── api/
│       │   │   ├── __init__.py
│       │   │   ├── auth.py
│       │   │   ├── workspaces.py
│       │   │   ├── memberships.py
│       │   │   ├── feedback.py
│       │   │   ├── submitters.py
│       │   │   ├── tags.py
│       │   │   ├── notes.py
│       │   │   ├── insights.py
│       │   │   └── public.py        # /api/v1/public/...
│       │   ├── pages/
│       │   │   ├── __init__.py
│       │   │   ├── landing.py
│       │   │   ├── auth_pages.py
│       │   │   ├── workspace_pages.py
│       │   │   ├── public_pages.py  # /w/<slug>/submit, /roadmap/public
│       │   │   └── styleguide.py
│       │   └── probes.py            # /health, /ready
│       ├── crud/                    # SQLModel-level data access
│       │   ├── __init__.py
│       │   ├── feedback.py
│       │   ├── workspace.py
│       │   ├── user.py
│       │   ├── membership.py
│       │   ├── tag.py
│       │   ├── note.py
│       │   └── submitter.py
│       ├── models.py                # SQLModel ORM models
│       ├── schemas.py               # Pydantic v2 request/response
│       ├── static/                  # served by StaticFiles
│       │   ├── css/
│       │   │   ├── input.css        # entry: @tailwind + @import
│       │   │   ├── tokens.css       # design tokens (CSS custom properties)
│       │   │   ├── base.css         # element resets, a11y floors
│       │   │   ├── layout.css       # layout primitives (page shell, grid)
│       │   │   ├── components.css   # .sn-* component vocabulary (@apply)
│       │   │   ├── effects.css      # transitions, animations, polish
│       │   │   └── app.css          # generated; NOT committed
│       │   ├── js/
│       │   │   ├── api.js           # fetch wrapper, X-Workspace-Slug
│       │   │   ├── toast.js
│       │   │   ├── inbox.js
│       │   │   ├── feedback-detail.js
│       │   │   ├── settings.js
│       │   │   └── landing-demo.js  # FU1 mini demo, self-contained
│       │   ├── img/
│       │   │   └── icons/           # Lucide static SVGs
│       │   └── pages/               # static HTML page shells
│       └── version.py               # __version__, sourced via hatch-vcs
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                    # one migration per ADR or schema PR
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── api/
│   │   ├── test_auth.py
│   │   ├── test_workspaces.py
│   │   ├── test_feedback.py
│   │   ├── test_isolation.py        # cross-tenant leak canaries
│   │   └── test_public_submit.py
│   ├── unit/
│   │   ├── test_hashing.py
│   │   ├── test_sessions.py
│   │   └── test_email_client.py
│   └── e2e/                         # Playwright; @pytest.mark.e2e
│       ├── test_signup_flow.py
│       ├── test_inbox_smoke.py
│       └── test_public_submit.py
├── scripts/                         # dev tooling (retained from template)
│   ├── seed.py                      # demo workspace + sample feedback
│   ├── build_css.py                 # invokes Tailwind Standalone CLI
│   └── ...
├── docs/
│   ├── project/
│   │   └── spec/
│   │       ├── spec-v1.md
│   │       ├── spec-v2.md           # entry point
│   │       ├── core-idea.md         # canonical brand brief
│   │       ├── v2/                  # this directory
│   │       └── _archive/            # historical pushback / feedback
│   ├── adr/
│   ├── notes/
│   └── ...
├── tools/
│   └── dev_tools/                   # env dashboard, etc. (template)
├── pyproject.toml                   # hatchling + hatch-vcs
├── uv.lock                          # committed
├── tailwind.config.cjs              # NEW v2.0 — content globs + tokens
├── Taskfile.yml
├── Containerfile
├── docker-compose.yml
├── alembic.ini
└── .pre-commit-config.yaml
```

---

## What's new in v2.0 vs. v1.0

Listed so a reviewer can scan the diff:

| Path                                  | Status         | Notes                                                |
| ------------------------------------- | -------------- | ---------------------------------------------------- |
| `src/feedback_triage/auth/`           | new            | sessions, hashing, deps                              |
| `src/feedback_triage/tenancy/`        | new            | workspace context + policies                         |
| `src/feedback_triage/email/`          | new            | Resend client + plain-text templates                 |
| `src/feedback_triage/routes/api/`     | new layout     | one module per resource                              |
| `src/feedback_triage/routes/pages/`   | new layout     | HTML page routes split out                           |
| `src/feedback_triage/static/css/`     | new layout     | five-file source split (`input.css` orchestrator + `tokens` / `base` / `layout` / `components` / `effects`); generated `app.css` |
| `src/feedback_triage/static/js/`      | expanded       | per-page JS files (no bundler)                       |
| `tailwind.config.cjs`                 | new            | added by [ADR 058](../../../adr/058-tailwind-via-standalone-cli.md) |
| `tests/api/test_isolation.py`         | new            | cross-tenant leak canaries — required Must test      |
| `scripts/build_css.py`                | new            | `task build:css` entry point                         |

`src/feedback_triage/static/css/app.css` is **generated** by the
Tailwind Standalone CLI and **not committed.** It is produced by
`task build:css` and bundled into the container image at build
time. Its absence in git is enforced by `.gitignore`.

---

## Module boundaries (rules)

The boundaries below are enforced by code review, not by Python
import machinery. Violations are bugs.

1. **`routes/` never touches `models`** directly. Routes call
   `crud/` or `auth/` or `tenancy/`.
2. **`crud/` never imports from `routes/`.** No HTTP types in
   `crud/`.
3. **`auth/` and `tenancy/` are leaves.** They depend on `models`,
   `database`, `errors`, but never on `routes/` or `crud/`.
4. **`email/` is a leaf.** It depends only on `config` and the
   stdlib + `httpx`. Never imports models.
5. **`schemas.py` is the only place Pydantic v2 models live.**
   Routes import from `schemas`, not from each other's modules.
6. **`static/` contents are not Python.** No Python file imports
   from `static/`; the path is resolved at runtime by FastAPI's
   `StaticFiles`.

---

## Naming conventions

- Python modules: `snake_case`. No abbreviations except `crud`,
  `api`, `db`.
- Pydantic schemas: `<Resource><Verb>` — `FeedbackCreate`,
  `FeedbackRead`, `FeedbackUpdate`, `FeedbackList`.
- SQLModel ORM classes: singular noun — `Feedback`, `Workspace`,
  `User`, `Membership`. Table name is `__tablename__` plural.
- Test files: `test_<surface>.py`; one file per resource.
- Static JS files: lowercase-hyphenated, e.g. `feedback-detail.js`.
- CSS classes: pure Tailwind utilities; bespoke classes (rare) live
  in `static/css/components.css` (or `layout.css` for layout
  primitives) with a `sn-` prefix (see [`css.md`](css.md)).

---

## Files that must exist for v2.0 ratification

A v2.0 PR is incomplete until each of these is present and
non-empty:

- [ ] `src/feedback_triage/auth/sessions.py`
- [ ] `src/feedback_triage/auth/hashing.py`
- [ ] `src/feedback_triage/auth/tokens.py`
- [ ] `src/feedback_triage/tenancy/context.py`
- [ ] `src/feedback_triage/email/client.py`
- [ ] `tailwind.config.cjs`
- [ ] `src/feedback_triage/static/css/input.css`
- [ ] `src/feedback_triage/static/css/tokens.css`
- [ ] `src/feedback_triage/static/css/base.css`
- [ ] `src/feedback_triage/static/css/layout.css`
- [ ] `src/feedback_triage/static/css/components.css`
- [ ] `src/feedback_triage/static/css/effects.css`
- [ ] `tests/api/test_isolation.py`
- [ ] `scripts/build_css.py`
- [ ] Alembic migration that adds every table in
      [`schema.md`](schema.md).

---

## Cross-references

- [`schema.md`](schema.md) — DDL behind the modules above.
- [`tooling.md`](tooling.md) — build / lint / test stack.
- [`implementation.md`](implementation.md) — phase plan that
  creates the files in this layout.
- [ADR 001 — `src/` layout](../../../adr/001-src-layout.md)
- [ADR 058 — Tailwind via Standalone CLI](../../../adr/058-tailwind-via-standalone-cli.md)
