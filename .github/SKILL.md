---
description: >-
  Add new components to this project: ADRs, workflows, scripts, MkDocs hooks,
  pre-commit hooks, dependencies, instruction files. Each procedure includes
  the file creation step AND all required sync steps (index updates,
  regeneration, instruction file updates). Use this skill when asked to
  "add a new ADR", "add a new workflow", "add a new script", etc.
---

# Project Component Procedures

<!-- TODO (template users): After forking, update these procedures to match
     YOUR project's file locations, conventions, and sync requirements.
     Remove procedures for component types you don't use. -->

Multi-step recipes for adding new components to this repository. Each
procedure lists creation steps AND the sync/registration steps that keep
documentation and tooling up-to-date.

## How to Invoke

Copilot loads this skill automatically when a request matches the description
(e.g., "add a new ADR"). To invoke explicitly in VS Code chat, reference the
file directly: `#file:.github/SKILL.md` then describe what you need.

---

## Add a New ADR

1. Find the next sequential number by listing `docs/adr/`.
2. Copy `docs/adr/template.md` to `docs/adr/NNN-short-title.md`.
3. Fill in all sections: Status, Context, Decision, Alternatives, Consequences, Implementation, References.
4. Update `docs/adr/README.md` — add the new ADR to the index table.
5. If the ADR affects day-to-day work, add it to the "Key ADRs" table in `.github/copilot-instructions.md`.
6. If the decision touches architecture or tooling, update `docs/design/architecture.md` and/or `docs/design/tool-decisions.md`.
7. If the ADR introduces a convention for a specific file type, update the matching `.instructions.md` file.

## Add a New Workflow

1. Create `.github/workflows/<name>.yml`.
2. Pin all third-party actions to full 40-character commit SHAs with a version comment: `uses: actions/checkout@<sha> # v4.2.0`.
3. Add repository guard pattern (`if: github.repository == ...`) unless the workflow is essential.
4. Update `docs/workflows.md` — add the workflow to the appropriate category table.
5. If the workflow is required for PRs, add its job display name to `REQUIRED_CHECKS` in `ci-gate.yml`.
6. If this introduces a new workflow convention, update `.github/workflows/.instructions.md`.

## Add a New Script

1. Create `scripts/<name>.py` with shebang (`#!/usr/bin/env python3`), argparse CLI (`--help`, `--version`, optionally `--dry-run`), and `logging` for status messages.
2. Mark executable: `git add --chmod=+x scripts/<name>.py`.
3. Update `scripts/README.md` — add to the inventory table.
4. Re-run: `python scripts/generate_command_reference.py` to refresh `docs/reference/commands.md`.
5. If the script is useful as a Taskfile shortcut, add a task to `Taskfile.yml`.
6. For shared utilities (not CLIs), name as `scripts/_<name>.py` (underscore prefix).
7. If this introduces a new script pattern, update `scripts/.instructions.md`.
8. Add an entry to `RECOMMENDED_SCRIPTS` in `scripts/_ui.py` so other scripts can recommend it.
9. If the script is relevant to customization, add its paths to the appropriate dict in `scripts/customize.py` (`STRIPPABLE`, `TEMPLATE_CLEANUP`, or `PRIVATE_REPO_STRIP`).

## Add a New MkDocs Hook

1. Create `mkdocs-hooks/<name>.py` with the hook function (e.g., `on_files`, `on_page_markdown`).
2. Register in `mkdocs.yml` under `hooks:`.
3. Update `mkdocs-hooks/README.md` — add to the inventory.
4. Add tests in `tests/unit/test_<name>.py` if the hook has non-trivial logic.
5. If the hook needs mkdocs-specific imports, ensure `mkdocs>=1.6` stays in the `test` dependency group so tests pass in the matrix.

## Add a New Pre-commit Hook

1. Add the hook definition to `.pre-commit-config.yaml` under the appropriate stage.
2. Update `docs/adr/008-pre-commit-hooks.md` — add to the hook inventory table and update the count.
3. Update the hook count in `.github/copilot-instructions.md` (Pre-commit Hooks table).

## Add a New Dependency

1. Add to the appropriate group in `pyproject.toml` `[project.optional-dependencies]`: `test`, `dev`, `docs`, or `extras`.
2. If the tool is a significant choice, update `docs/design/tool-decisions.md`.
3. Run `hatch env remove default` then re-enter with `hatch shell` to pick up changes.
4. If the dependency affects conventions for a specific file type, update the matching `.instructions.md`.

## Add or Update a `.instructions.md` File

1. Create the file with an `applyTo` frontmatter glob matching the target directory (e.g., `applyTo: "src/**"`).
2. Add a `<!-- TODO (template users): ... -->` comment if template users should customize it.
3. Update the "Targeted Instruction Files" table in `.github/copilot-instructions.md`.
4. Update the "Files Included" table in `docs/USING_THIS_TEMPLATE.md`.
