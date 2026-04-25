# ADR 039: Developer Onboarding Automation (Bootstrap and Customize)

## Status

Accepted

## Context

This is a template repository. New users go through two distinct phases:

1. **Clone and set up** — Get the development environment working
2. **Customize** — Replace placeholder names, strip optional components,
   and make it their own project

These phases have different goals, different frequencies (setup runs on
every fresh clone; customize runs once after forking), and different risk
profiles (setup is safe and idempotent; customize modifies files
irreversibly).

Mixing both into a single script would create confusion about when to run
it and what it does each time.

## Decision

Provide two separate scripts for the two onboarding phases:

### `bootstrap.py` — Run on every fresh clone

An idempotent setup script that gets the development environment into a
working state:

1. Verifies Python version meets the minimum requirement
2. Checks git configuration (runs env_doctor checks)
3. Creates Hatch environments
4. Installs pre-commit hooks (all three stages)
5. Verifies the package is importable

**Key properties:**

- **Idempotent** — Safe to run multiple times; skips steps already done
- **Non-destructive** — Never modifies source files
- **Supports `--dry-run`** — Preview what would happen

### `customize.py` — Run once after forking

An interactive script that transforms the template into a real project:

1. Replaces the package name (`simple_python_boilerplate` → user's name)
2. Updates metadata in `pyproject.toml`
3. Optionally strips components the user doesn't need (`--strip db`,
   `--strip experiments`, `--strip var`, etc.)
4. Swaps the license if needed
5. Updates import paths across the codebase

**Key properties:**

- **One-time** — Designed to run once; re-running on an already-customized
  project is a no-op or error
- **Destructive** — Modifies files across the repo
- **Supports `--dry-run`** — Preview changes before applying
- **Interactive** — Prompts for project name, author, etc. when not
  supplied via flags

### Why they're separate

| Concern         | `bootstrap.py`   | `customize.py`     |
| :-------------- | :--------------- | :----------------- |
| When to run     | Every clone      | Once after forking |
| Idempotent      | Yes              | No                 |
| Modifies source | No               | Yes                |
| Risk level      | Safe             | Irreversible       |
| CI usage        | Yes (verify env) | No                 |

Combining these would mean either: (a) customize runs on every clone
(dangerous), or (b) bootstrap is gated behind "have you customized yet?"
checks (complex). Separate scripts keep the mental model simple.

## Alternatives Considered

### Single setup script with modes

One script: `setup.py --bootstrap` vs `setup.py --customize`.

**Rejected because:** Modes add complexity and risk. A typo
(`--customize` instead of `--bootstrap`) on a fresh clone of a
production fork could re-run customization destructively.

### GitHub template repository wizard

Use GitHub's template repository feature with manual find-and-replace.

**Rejected because:** GitHub's template feature only copies files — it
doesn't rename packages, update imports, or strip optional components.
Manual find-and-replace is error-prone and misses files.

### Template engine (Cookiecutter, Copier)

Use a proper template engine that prompts for variables and generates
a customized project.

**Rejected because:** See [ADR 014](014-no-template-engine.md). Template
engines add tooling complexity, make the template harder to develop
(you work with Jinja syntax instead of real Python), and create a
one-way door — the generated project can't easily pull template updates.

## Consequences

### Positive

- Clear two-phase onboarding: clone → bootstrap → customize
- Bootstrap is safe to run anytime (CI, new machines, troubleshooting)
- Customize handles the tedious find-and-replace across 50+ files
- Both support `--dry-run` for confidence before committing
- Stripping optional components (db, experiments) is built in

### Negative

- Two scripts instead of one — users must learn which to run when
- Customize may not catch every placeholder in custom files added
  after the template was created
- The "run once" nature of customize means mistakes require git revert

### Mitigations

- `USING_THIS_TEMPLATE.md` documents the exact sequence
- Bootstrap detects if customize hasn't been run and suggests it
- `--dry-run` lets users preview customize changes safely
- Git history provides a safety net for mistakes

## Implementation

- [scripts/bootstrap.py](../../scripts/bootstrap.py) — Environment setup script
- [scripts/customize.py](../../scripts/customize.py) — Template customization script
- [docs/USING_THIS_TEMPLATE.md](../../docs/USING_THIS_TEMPLATE.md) — Onboarding guide

## References

- [ADR 014: No template engine](014-no-template-engine.md) — Why customize.py instead of Cookiecutter
- [ADR 031: Script conventions](031-script-conventions.md) — Script patterns both follow
- [ADR 036: Diagnostic tooling strategy](036-diagnostic-tooling-strategy.md) — Bootstrap runs env_doctor
