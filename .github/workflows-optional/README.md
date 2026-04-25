# Optional Workflows

This directory contains **optional workflow templates** that are not active by default.

## How to Use

1. **Copy** a workflow from here into `.github/workflows/`
2. **Follow the TODO** comments at the top of the file to configure it
3. **Enable the repository guard** (replace `YOURNAME/YOURREPO` or set the
   corresponding `vars.ENABLE_*` variable)
4. The workflow will become active on the next push

## Why a Separate Directory?

GitHub Actions only executes workflows in `.github/workflows/`.
Files here are inert — they serve as a library of ready-to-use templates
you can adopt when your project needs them.

## Available Templates

<!-- TODO (template users): Remove entries from this table as you move
     workflows into .github/workflows/. Delete this directory when empty. -->

| File             | Purpose                                              |
| ---------------- | ---------------------------------------------------- |
| `changelog.yml`  | Generate CHANGELOG.md from conventional commits (git-cliff) |

## After Adopting

Once you've moved all the templates you need into `.github/workflows/`,
you can delete this directory entirely to reduce clutter.

## See Also

- [.github/workflows/](../workflows/) — Active workflows
- [docs/workflows.md](../../docs/workflows.md) — Full workflow documentation
- [ADR 011](../../docs/adr/011-repository-guard-pattern.md) — Repository guard pattern
