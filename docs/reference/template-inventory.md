# Template & Example File Inventory

This project includes templates, examples, and starter files across many
directories. Before creating a new file, check whether a relevant template
already exists — following the established pattern saves time and keeps
the project consistent.

<!-- TODO (template users): After forking, update this inventory to reflect
     your project's actual templates and examples. Remove entries for
     directories you deleted (e.g., db/, experiments/, docs/templates/). -->

---

## Quick Reference

| Category            | Template / Example                    | Location                                                                                   | Notes                                                             |
| :------------------ | :------------------------------------ | :----------------------------------------------------------------------------------------- | :---------------------------------------------------------------- |
| **ADR**             | ADR template                          | [`docs/adr/template.md`](../adr/template.md)                                               | Copy to `NNN-short-title.md`, fill in sections                    |
| **Exploration**     | Exploration template                  | [`docs/explorations/template.md`](../explorations/template.md)                             | Copy to `NNN-short-description.md`, fill in sections              |
| **Blueprint**       | Blueprint template                    | [`docs/blueprints/template.md`](../blueprints/template.md)                                 | Copy to `NNN-short-description.md`, fill in sections              |
| **Impl Plan**       | Implementation plan template          | [`docs/implementation-plans/template.md`](../implementation-plans/template.md)             | Copy to `NNN-short-description.md`, fill in sections              |
| **Workflow**        | Any existing workflow                 | [`.github/workflows/*.yml`](../../.github/workflows/)                                      | Follow repo guard pattern, SHA-pinned actions, naming conventions |
| **Script (CLI)**    | Any script in `scripts/`              | [`scripts/`](../../scripts/)                                                               | Use argparse, shebang, logging; mark executable in git            |
| **Script (lib)**    | Shared progress module                | [`scripts/_progress.py`](../../scripts/_progress.py)                                       | Underscore prefix = internal module, not a CLI                    |
| **MkDocs hook**     | repo_links hook                       | [`mkdocs-hooks/repo_links.py`](../../mkdocs-hooks/repo_links.py)                           | Register in `mkdocs.yml` under `hooks:`                           |
| **Migration**       | Example SQL migration                 | [`db/migrations/001_example_migration.sql`](../../db/migrations/001_example_migration.sql) | Numbered, idempotent, with rollback                               |
| **Seed**            | Example seed data                     | [`db/seeds/001_example_seed.sql`](../../db/seeds/001_example_seed.sql)                     | Numbered, idempotent                                              |
| **SQL query**       | Example queries                       | [`db/queries/example_queries.sql`](../../db/queries/example_queries.sql)                   | Documented queries for common operations                          |
| **Security policy** | Standard (no bounty)                  | [`docs/templates/SECURITY_no_bounty.md`](../templates/SECURITY_no_bounty.md)               | Copy to repo root as `SECURITY.md`                                |
| **Security policy** | With bug bounty                       | [`docs/templates/SECURITY_with_bounty.md`](../templates/SECURITY_with_bounty.md)           | Copy to repo root as `SECURITY.md`                                |
| **Bug bounty**      | Standalone bounty policy              | [`docs/templates/BUG_BOUNTY.md`](../templates/BUG_BOUNTY.md)                               | Link from `SECURITY.md`                                           |
| **PR template**     | Pull request description              | [`docs/templates/pull-request-draft.md`](../templates/pull-request-draft.md)               | Copy to `.github/PULL_REQUEST_TEMPLATE.md`                        |
| **Issue template**  | Bug report, feature request, docs     | [`.github/ISSUE_TEMPLATE/*.yml`](../../.github/ISSUE_TEMPLATE/)                            | YAML-based issue forms                                            |
| **Issue template**  | Additional templates (question, perf) | [`docs/templates/issue_templates/`](../templates/issue_templates/README.md)                | Copy what you need to `.github/ISSUE_TEMPLATE/`                   |
| **VS Code**         | Workspace settings                    | [`*.code-workspace`](../../simple-python-boilerplate.code-workspace)                       | Extensions, settings, file exclusions                             |
| **Experiment**      | API test, data exploration            | [`experiments/`](../../experiments/)                                                       | Throwaway scripts, not part of the package                        |
| **Commit message**  | Conventional commit template          | [`.gitmessage.txt`](../../.gitmessage.txt)                                                 | `git config commit.template .gitmessage.txt`                      |
| **Collector**       | Environment data collector plugin     | [`scripts/_env_collectors/`](../../scripts/_env_collectors/)                                 | Subclass `BaseCollector`, auto-discovered by dashboard            |
| **Dashboard**       | Dashboard template / route            | [`tools/dev_tools/env_dashboard/`](../../tools/dev_tools/env_dashboard/)                   | FastAPI + Jinja2 + htmx + Alpine.js                               |
| **Repo doctor**     | Health check rules                    | [`repo_doctor.d/*.toml`](../../repo_doctor.d/)                                             | Add new `.toml` rule files per category                           |

---

## Conventions When Creating New Files

### Scripts

- Add `#!/usr/bin/env python3` shebang, then mark executable:
  `git add --chmod=+x scripts/my_script.py`
- Use `argparse` for CLI flags (`--help`, `--version`, `--dry-run`)
- Use `logging` for status messages, `print()` only for primary output
- Internal/shared modules use `_` prefix (e.g., `_progress.py`)
- After creating: update [`scripts/README.md`](../../scripts/README.md) and
  re-run `python scripts/generate_command_reference.py`

### MkDocs Hooks

- Place in `mkdocs-hooks/` directory
- Register in `mkdocs.yml` under `hooks:`
- Update [`mkdocs-hooks/README.md`](../../mkdocs-hooks/README.md) inventory
- Follow the pattern in existing hooks (module docstring, logging, version constant)

### Workflows

- SHA-pin all GitHub Actions ([ADR 004](../adr/004-pin-action-shas.md))
- Include repository guard pattern ([ADR 011](../adr/011-repository-guard-pattern.md))
- Add `TODO (template users)` comment for enabling the guard
- Update [`docs/workflows.md`](../workflows.md) inventory
- Update `REQUIRED_CHECKS` in `ci-gate.yml` if the workflow is a required check

### ADRs

- Copy `docs/adr/template.md` to `docs/adr/NNN-short-title.md`
- Update [`docs/adr/README.md`](../adr/README.md) index table
- Update `mkdocs.yml` nav under ADRs section
- Update `.github/copilot-instructions.md` ADR table if the ADR affects day-to-day work

### Database Files

- Migrations: numbered (`NNN_description.sql`), idempotent, include rollback
- Seeds: numbered, idempotent
- Queries: documented with comments explaining purpose

### Environment Collectors

- Place in `scripts/_env_collectors/` as a new module
- Subclass `BaseCollector`, implement `collect()` method
- Auto-discovered by the dashboard ([ADR 043](../adr/043-collector-plugin-architecture.md))
- See [collector conventions](../../.github/instructions/collectors.instructions.md) for the full pattern

---

## Related Docs

- [Repo layout](../repo-layout.md) — what each top-level directory contains
- [Script conventions](../adr/031-script-conventions.md) — full ADR on script patterns
- [Documentation organization](../adr/034-documentation-organization-strategy.md) — where docs go
- [scripts/README.md](../../scripts/README.md) — script inventory with descriptions
- [mkdocs-hooks/README.md](../../mkdocs-hooks/README.md) — hook inventory
