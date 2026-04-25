# ADR 003: Separate GitHub Actions workflow files

## Status

Accepted

## Context

GitHub Actions workflows can be organized in two ways:

1. **Single file** — All jobs in one `ci.yml` file
2. **Multiple files** — Separate files per concern (`test.yml`, `lint.yml`, `release.yml`)

## Decision

Use separate workflow files for distinct concerns:

```
.github/workflows/
├── test.yml          # Run tests on push/PR
├── lint.yml          # Code quality checks
├── release.yml       # Build and publish
└── _spellcheck.yml   # Disabled (underscore prefix)
```

## Consequences

### Positive

- **Easy to enable/disable** — Rename with underscore prefix to disable
- **Granular permissions** — Each workflow gets only required permissions
- **Independent triggers** — Different events for different workflows
- **Clearer debugging** — Failures are isolated to relevant workflow
- **Smaller diffs** — Changes scoped to relevant file

### Negative

- **More files** — More files to manage in `.github/workflows/`
- **Potential duplication** — Common steps may be repeated
- **Harder to share state** — Jobs in different workflows can't share artifacts directly

### Mitigations

- Use reusable workflows for shared logic (if needed)
- Keep workflows focused and simple
- Document workflow purposes in this ADR

## Alternatives Considered

### Single ci.yml File

All jobs (test, lint, release) in one workflow file.

**Rejected because:**

- Can't disable individual concerns without editing the file
- All jobs share the same trigger events
- Harder to grant minimal permissions per job
- Larger diffs for small changes

### Monorepo-style with Path Filters

Single workflow with path-based job triggers.

**Rejected because:** Adds complexity, path filters can be error-prone, still can't easily disable jobs.

### Reusable Workflows Only

Define all logic in reusable workflows, call from thin wrapper files.

**Rejected because:** Over-engineering for a simple project; adds indirection without significant benefit.

## Implementation

- [.github/workflows/test.yml](../../.github/workflows/test.yml) — Run tests on push/PR
- [.github/workflows/lint-format.yml](../../.github/workflows/lint-format.yml) — Code quality checks
- [.github/workflows/release.yml](../../.github/workflows/release.yml) — Build and publish
- [.github/workflows/spellcheck.yml](../../.github/workflows/spellcheck.yml) — Spell checking
- [.github/workflows/spellcheck-autofix.yml](../../.github/workflows/spellcheck-autofix.yml) — Auto-fix typos weekly

## References

- [GitHub Actions: Reusing workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
