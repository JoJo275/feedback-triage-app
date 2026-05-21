# Script Conventions

This page tracks active script conventions used in this project.

## Canonical Sources

- [Script instructions](../../../scripts/.instructions.md)
- [Script conventions notes](../../notes/script-conventions.md)
- [ADR 031 - Script Conventions](../../adr/031-script-conventions.md)

## Working Rules

- Use the standard script skeleton and import ordering defined in `scripts/.instructions.md`.
- Keep script CLI surfaces predictable (`--version`, `--smoke`, `--quiet`, `--verbose`, and `--dry-run` when side effects exist).
- Return standardized exit codes through `ExitCode` from `scripts/_ui.py`.
- Prefer shared script utilities (`_ui.py`, `_progress.py`, `_colors.py`, `_imports.py`) over ad-hoc local implementations.
- Keep script output readable in both color and plain-text/no-color environments.

## When Changing Script Conventions

1. Update canonical guidance in `scripts/.instructions.md` first.
2. Update affected scripts and related task/workflow references in the same PR.
3. Sync this page (and notes/ADR references if needed) to avoid competing guidance.
