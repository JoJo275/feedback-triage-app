# actionlint

!!! note "Active Tool"
    This tool is currently active in this repository and documented from the canonical inventory.

---

## Metadata

- **Tool name:** actionlint
- **Status:** Active
- **Layer:** CI
- **Scope:** CI workflow quality
- **Owner:** Engineering
- **Adoption gate:** Already adopted
- **Last reviewed:** 2026-05-23

## actionlint

### Role

Static lint for GitHub Actions syntax and expressions.

### What it is

Static linter for GitHub Actions workflows.

### Why this project uses it

Static lint for GitHub Actions syntax and expressions.

### Repo locations

| Purpose | Path |
| --- | --- |
| Config | docs/tooling.md |
| Source files | .github/workflows/ |
| Generated output | Not applicable |
| Tests | workflow runs and branch protections |

### Common commands

```bash
uv run actionlint
```

Lint one workflow file:

```bash
uv run actionlint .github/workflows/test.yml
```

### Verify tool exists

Run:

```bash
uv run actionlint --version
```

Expected result:

- Command exits with status code 0.
- Output includes an `actionlint` version (for example, `1.7.12`).

If the command fails with `program not found`, install or sync dev dependencies:

```bash
uv sync
```

### Inputs and outputs

| Type | Examples |
| --- | --- |
| Inputs | Source files, project config, repository metadata, and command arguments. |
| Outputs | Tool-specific artifacts, diagnostics, build products, or CI check results. |

### Standard workflow

1. Confirm configuration and prerequisites for this tool.
2. Run the primary command for the current change.
3. Validate output and keep related docs and config in sync.

### Integration points

| Integrates with | How |
| --- | --- |
| GitHub Actions | Executes this tool in CI where applicable. |
| Tool inventory | This page is derived from docs/tooling.md status and boundaries. |

### Boundaries

**Use this tool for:**

- Any workflow edit before pushing.

**Do not use this tool for:**

- Runtime CI debugging, test execution, or workflow policy governance.

### Testing expectations

Run the relevant commands in this page and validate with task check before merge when changes can affect quality gates.

### Observability and failure modes

| Failure | How detected | Response |
| --- | --- | --- |
| Tool command fails or returns non-zero | Local command output and CI job status | Review config and command arguments, then rerun targeted checks. |

### Example

```bash
uv run actionlint
```

### Related docs

- ../tooling.md
- ../design/tool-decisions.md
- ../workflows.md

### Runtime and cost footprint

| Category | Notes |
| --- | --- |
| Runtime service? | No |
| Runs in CI only? | Yes |
| Requires external service? | No |
| Cost risk | Low |
| Scaling concern | Reassess as adoption, data volume, or workflow frequency increases. |

### Source-of-truth responsibility

This tool owns no durable product truth by itself.

### Rollback or replacement plan

Remove this tool's config and workflow hooks in the same change, update docs/tooling.md, and verify with task check plus affected CI jobs.
