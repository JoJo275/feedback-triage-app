# Development Framework

The project-specific operating system for engineering work in this repo:
rules, workflows, and conventions.

## Purpose

Use this page as the default execution model for day-to-day work.

- Decide what source of truth applies when guidance conflicts.
- Run changes through a consistent workflow from idea to verified delivery.
- Keep implementation, tests, docs, and operations artifacts synchronized.

## Rule Hierarchy

When two documents conflict, apply this precedence order:

1. **Project spec**: v2.0 is the active spec for current work (`docs/project/spec/spec-v2.md`).
2. **ADRs**: architecture/process decisions in `docs/adr/`.
3. **Instruction files**: scoped rules in `.github/instructions/*.instructions.md`.
4. **Area docs**: development/design/reference docs (including this page).
5. **PR-local notes**: temporary implementation notes in the active branch.

If a requested change conflicts with a higher-order rule, update that higher-order rule first, then implement.

## Core Operating Rules

- Keep changes minimal and reversible; avoid unrelated churn.
- Implement **Must** scope before **Should** scope from the spec.
- Keep related surfaces in sync (code, tests, docs, workflows, migrations).
- Remove dead code when proven unused.
- Prefer secure defaults and fail-closed behavior in security-sensitive flows.
- Use `uv` for Python env/dependency management; do not bypass with ad-hoc `pip install`.
- Hand-review every Alembic migration after autogenerate.
- Keep PRs logically scoped and commit messages in Conventional Commit format.

## Standard Workflow

1. **Sync environment**
   - `uv sync`
2. **Implement smallest viable change**
   - Touch only required files.
3. **Run targeted checks first**
   - File/module tests, then broader checks.
4. **Run repository gates relevant to the change**
   - `task check` minimum for code changes.
5. **Update docs/contracts in same change**
   - API shape, conventions, and runbooks.
6. **Prepare review-ready branch**
   - Clear commit messages, no hidden work-in-progress artifacts.

## Workflow by Change Type

| Change Type | Required Companion Updates | Minimum Verification |
| --- | --- | --- |
| API route/schema | `src/feedback_triage/` handlers + schemas + API tests + docs/spec if contract changed | `task test`, `task typecheck` |
| DB schema/model | SQLModel models + Alembic migration + migration review + tests | `task migrate`, `task test` |
| Frontend runtime (`web/src/`) | Build output usage paths + UI tests/e2e coverage | `npm --prefix web run build`, `task test:e2e` |
| Script/tooling (`scripts/`) | Script conventions alignment + help/smoke/version behavior | Targeted script run + relevant lint/test hooks |
| Docs only | Linked docs and indexes (`README.md`, nav entries) | `uv run mkdocs build --strict` |
| Workflow/CI files | Workflow docs and guard consistency | `uv run actionlint` |

## Conventions Matrix

| Area | Conventions | Canonical Sources |
| --- | --- | --- |
| Python | Typed public interfaces, absolute imports, secure subprocess usage | `.github/instructions/python.instructions.md` |
| API | `/api/v1/` JSON contract discipline, explicit response models, pagination envelope | `docs/project/spec/spec-v2.md`, ADRs 045-054 |
| Database | Postgres-first semantics, enums + checks, session-per-request | ADRs 045-054, `alembic/`, `src/feedback_triage/database.py` |
| Frontend | Semantic HTML, accessibility-first, React runtime conventions for v2 | `.github/instructions/react.instructions.md`, `docs/design/conventions/*.md` |
| Scripts | Shared CLI surface (`--smoke`, verbosity flags, exit codes), `_ui` patterns | `scripts/.instructions.md`, `docs/design/conventions/scripts.md` |
| Docs | Relative linking, concise technical writing, lifecycle docs for non-trivial changes | `docs/.instructions.md` |
| CI/CD | SHA-pinned actions, repository-guard policy, gate-first pipelines | `docs/workflows.md`, `.github/workflows/` |

## Definition of Done

Treat work as done only when all applicable items are true:

- Requested behavior is implemented.
- Relevant tests and checks pass.
- Docs and conventions are updated where behavior or policy changed.
- No unresolved TODOs were introduced without an owner/context.
- Diff is scoped, readable, and review-ready.

## Related Docs

- [development.md](development.md) - Daily development guide.
- [developer-commands.md](developer-commands.md) - Command catalog.
- [command-workflows.md](command-workflows.md) - Command layering and invocation flows.
- [../tooling.md](../tooling.md) - Tool inventory with why/when/how guidance.
- [../design/conventions/README.md](../design/conventions/README.md) - Cross-area conventions index.
