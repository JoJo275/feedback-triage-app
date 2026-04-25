# Copilot Instructions

Guidelines for GitHub Copilot when working in this repository.

<!-- TODO (template users): After forking, update to match YOUR project:
     - Replace project-specific names, entry points, and paths
     - Add your own conventions and review priorities
     - Remove sections that don't apply
     Copilot reads this file on every interaction, so keep it accurate. -->

---

## How This Project Works

### Overview

A Python boilerplate/template project using src/ layout, Hatch for
environment/build management, and extensive CI/CD. The single source of truth
for tool configuration is `pyproject.toml`.

### Domain / Business Context

This is a **template repository** — no application logic. The "product" is the
project structure, CI/CD pipelines, tooling conventions, and documentation.
Everything under `src/` is placeholder code for template users to replace.

<!-- TODO (template users): Replace with 2-3 sentences describing what YOUR
     application does, then delete this comment block. -->

### Build & Environment — Hatch

- **Build backend:** Hatchling with `hatch-vcs` for git-tag versioning.
- **Envs:** `hatch run <cmd>` or `hatch shell`. Key envs: `default` (dev), `docs` (mkdocs), `test` (pytest matrix 3.11–3.13).
- **Dependencies:** `[project.optional-dependencies]` groups are the source of truth. Hatch envs consume via `features = [...]`.
- **Removing a dep** requires `hatch env remove default` then re-create; Hatch doesn't auto-uninstall.
- **Version** from git tags via `hatch-vcs`. Fallback: `0.0.0+unknown`.

### Pre-commit Hooks

| Stage          | Key hooks                                                | Count |
| :------------- | :------------------------------------------------------- | ----: |
| **pre-commit** | ruff, mypy, bandit, typos, actionlint, deptry, + suite   |    38 |
| **commit-msg** | commitizen (Conventional Commits)                        |     1 |
| **pre-push**   | pytest, pip-audit, gitleaks, repo-doctor                 |     4 |
| **manual**     | markdownlint-cli2, hadolint-docker, prettier, forbid-sub |     4 |
| **Total**      |                                                          | **47**|

Config: `.pre-commit-config.yaml` · Full inventory: [ADR 008](../docs/adr/008-pre-commit-hooks.md)

### GitHub Actions Workflows

~37 workflow files in `.github/workflows/`, all SHA-pinned ([ADR 004](../docs/adr/004-pin-action-shas.md)).
**Canonical inventory:** `docs/workflows.md`. See `.github/workflows/.instructions.md` for conventions.

### Task Runner — Taskfile

Key tasks: `task test`, `task lint`, `task fmt`, `task typecheck`, `task check` (all gates),
`task commit`, `task deps:versions`. Run `task` for full list.

### Scripts

Utility scripts in `scripts/`. See `scripts/README.md` for inventory,
`scripts/.instructions.md` for conventions.

### Global Entry Points

22 CLI commands (21 `spb-*` commands plus `spb`) defined in `[project.scripts]` in `pyproject.toml`.
Thin wrappers in `src/simple_python_boilerplate/scripts_cli.py` run bundled
scripts via subprocess with `SPB_REPO_ROOT` set to CWD, enabling cross-repo
use via `pipx install .`. See `docs/guide/entry-points.md` for the full list.

### Environment Dashboard

FastAPI + Jinja2 + HTMX + Alpine.js web app in `tools/dev_tools/env_dashboard/`.
20 plugin-based collectors gather environment data. Start with `spb-dashboard`
or `hatch run dashboard:serve`. See `docs/guide/dashboard-guide.md`.

### Documentation

MkDocs Material. See `docs/.instructions.md` and `docs/adr/.instructions.md`.
Serve: `hatch run docs:serve`.

### Key Configuration Files

| File | Controls |
| --- | --- |
| `pyproject.toml` | Project metadata, deps, Hatch envs, tool configs (ruff, mypy, pytest, bandit, etc.) |
| `.pre-commit-config.yaml` | Hook definitions and stages |
| `Taskfile.yml` | Task runner shortcuts |
| `mkdocs.yml` | Documentation site config |
| `Containerfile` | Multi-stage container build |
| `release-please-config.json` | Release automation |
| `mkdocs-hooks/*.py` | MkDocs build hooks (repo_links, generate_commands, include_templates) |
| `src/.../scripts_cli.py` | Entry point wrappers for `spb-*` CLI commands |
| `*.code-workspace` | VS Code settings. **Note:** use relative paths, not `${workspaceFolder}`. |

### Targeted Instruction Files

| File | Scope |
| --- | --- |
| `.github/workflows/.instructions.md` | Workflow YAML conventions |
| `scripts/.instructions.md` | Script conventions |
| `docs/.instructions.md` | Documentation conventions |
| `docs/adr/.instructions.md` | ADR creation procedure |
| `tests/.instructions.md` | Test conventions |
| `.github/instructions/dashboard.instructions.md` | Dashboard app conventions (FastAPI, htmx, Alpine.js) |
| `.github/instructions/dashboard-css.instructions.md` | Dashboard CSS/theme conventions |
| `.github/instructions/dashboard-templates.instructions.md` | Dashboard Jinja2 template conventions |
| `.github/instructions/collectors.instructions.md` | Environment data collector conventions |
| `.github/instructions/python.instructions.md` | Python style, imports, type hints, security |
| `.github/instructions/tests.instructions.md` | pytest conventions, fixtures, coverage |

This file covers **project-wide** rules. Prefer the targeted instruction file for file-type-specific details.

---

## Working Style

### Leave TODOs for Template Users

Include `TODO (template users):` comments in new files explaining what to
customise. Be specific: "Replace `YOURNAME/YOURREPO` with your repo slug."

### Check Templates Before Creating Files

Check [template inventory](../docs/reference/template-inventory.md) for
existing templates and conventions before creating files from scratch.

### Use SKILL.md for Multi-step Operations

`.github/SKILL.md` has step-by-step procedures for adding components
(workflows, scripts, ADRs, hooks, deps, instruction files). **Always read
it before multi-step operations** — it lists sync steps easy to forget.

### Keep Related Files in Sync

When updating a file, update dependent files too. Use `.github/SKILL.md`
as a checklist. Don't let documentation drift from reality.

### Provide Feedback and Pushback

Push back when a request introduces unnecessary complexity, conflicts with
conventions/ADRs, or has a simpler alternative. Be direct: state the problem,
explain why, suggest an alternative.

### Clean Up Dead Code

Remove dead code when encountered. Grep first to confirm it's unused.
Preserve public API and documented extension points.

### Session Recap

After significant sessions, provide a brief recap: what changed, why,
impact (pros and cons), what to watch for, decisions made, and recommendations.
Skip for trivial single-file edits.

### Surface Issues

Proactively flag issues, risks, or anomalies noticed during any session —
even if unrelated to the current task. Keep flags brief: what's wrong,
why it matters, suggested next step.

### Verify Before Finishing

- **Code** — run tests (`task test`) or check for syntax/type errors
- **Workflows** — run `actionlint`
- **Hooks** — `pre-commit run <hook-id> --all-files`
- **SHA-pinned actions** — verify the commit SHA exists upstream

### Don't Churn

Avoid unnecessary rewrites, renames, or restructurings that don't fix a
bug or deliver a requested feature. Churn creates merge conflicts, pollutes
blame history, and wastes CI minutes. If existing code works and isn't
blocking a change, leave it alone.

### Tone

Direct and factual. No filler praise or diplomatic hedging. If something
is broken, say so.

## Review Priorities

1. **Type hints** — Public functions in `src/` should have annotations
2. **Tests** — Changes should include or update tests
3. **Security** — Flag hardcoded secrets, `shell=True`, unsafe `yaml.load()`, SQL injection
4. **Import errors** — Must work with src/ layout
5. **Docstrings** — Google style on public functions
6. **Error handling** — Appropriate exception handling

### General Guidance

- Prefer minimal diffs — Ruff handles formatting
- Use `hatch shell` for envs, never bare `pip install`
- Don't create `.venv` manually; use Hatch

## Conventions

### Python

- Absolute imports: `from simple_python_boilerplate.module import func`
- Type hints on all public functions; mypy strict mode
- Google style docstrings; constants in UPPER_SNAKE_CASE
- `pathlib.Path` over `os.path`; `subprocess.run()` with arg lists (never `shell=True`)
- `from __future__ import annotations` at top of every file
- `tomllib` for TOML; `importlib.metadata` for package introspection

Script-specific conventions are in `scripts/.instructions.md`.

### Ruff — Linting & Formatting

Ruff handles both linting and formatting as pre-commit hooks. **Write code
that passes on the first try.** Full config in `pyproject.toml` under `[tool.ruff]`.

Validate before committing:

    hatch run ruff check src/ scripts/ tests/    # lint
    hatch run ruff format --check src/ scripts/  # format check

Key conventions: double quotes, trailing commas, isort import order
(stdlib → third-party → local), no `print()` in `src/` (T20), pathlib
over os.path (PTH), modern 3.11+ syntax (UP), comprehensions over
`list()`/`dict()` calls (C4), `list.extend()` over append-in-loop (PERF401).
For any specific rule: `ruff rule <CODE>`.

### Bandit — Security Linting

Pre-commit hook. Config in `pyproject.toml` under `[tool.bandit]`.
Validate: `hatch run bandit -c pyproject.toml -r src/`

Key rules: no `eval()`/`exec()`, no `pickle` on untrusted data, no
`shell=True`, no hardcoded `/tmp` (use `tempfile`), `yaml.safe_load()`
not `yaml.load()`, parameterized SQL queries.

### Project Structure

- Source: `src/simple_python_boilerplate/`
- Tests: `tests/` · Scripts: `scripts/` · Docs: `docs/`

### Git & PRs

- Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `ci:`, `test:`, `refactor:`
- One logical change per commit; PR titles follow conventional format
- Commit message template in `.gitmessage.txt`: `<type>(<scope>): <description>`
  with body sections `Why:`, `What changed:`, `How tested:`

## Ignore / Don't Flag

- **E501** — Disabled; don't request rewrapping
- **Generated files** — `*.egg-info/`, `__pycache__/`, `.venv/`
- **Types in tests** — See `tests/.instructions.md`

## Architecture References

- `docs/design/architecture.md` — System overview, data flows
- `docs/design/tool-decisions.md` — Tool comparison notes
- `docs/adr/` — 44 Architecture Decision Records

Key ADRs: 001 (src/ layout), 008 (pre-commit hooks), 024 (CI gate),
031 (script conventions), 040 (v1.0 readiness), 041 (env dashboard),
042 (smoke testing), 043 (collector plugins), 044 (Copilot instructions).

**When numbers here conflict with those docs, the docs win.**

## Common Issues

1. Missing `pip install -e .` — use editable install for src/ layout
2. Wrong imports — use `simple_python_boilerplate`, not `src`
3. Mutable default arguments — `def func(items=[])` is a bug
4. Hatch env stale after dep removal — `hatch env remove default` then re-create
5. Bare `pip install` outside venv — always use Hatch env or `pipx`

## Known Limitations

See [`docs/known-issues.md`](../docs/known-issues.md) for the canonical list.
