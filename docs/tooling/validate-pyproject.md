# validate-pyproject

!!! note "Active Tool"
    This tool is currently active in this repository and documented from the canonical inventory.

---

## Metadata

- **Tool name:** validate-pyproject
- **Status:** Active
- **Layer:** Database
- **Scope:** Packaging metadata
- **Owner:** Engineering
- **Adoption gate:** Already adopted
- **Last reviewed:** 2026-05-23

## validate-pyproject

### Role

Validates packaging metadata structure.

### What it is

Validator for Python packaging metadata in pyproject.toml.

### Why this project uses it

Validates packaging metadata structure.

### Repo locations

| Purpose | Path |
| --- | --- |
| Config | docs/tooling.md |
| Source files | src/feedback_triage/ and alembic/ |
| Generated output | Not applicable |
| Tests | tests/ |

### Common commands

```bash
uv run validate-pyproject pyproject.toml
```

### Verify tool exists

Run:

```bash
uv run validate-pyproject pyproject.toml
```

Expected result:

- Command exits with status code 0.
- Command does not fail with "command not found" or "is not recognized".

If this tool supports a version command, also add or use a `--version` check here.

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

- Editing pyproject.toml.

**Do not use this tool for:**

- Dependency vulnerability analysis or environment lockfile reconciliation.

### Testing expectations

Run the relevant commands in this page and validate with task check before merge when changes can affect quality gates.

### Observability and failure modes

| Failure | How detected | Response |
| --- | --- | --- |
| Tool command fails or returns non-zero | Local command output and CI job status | Review config and command arguments, then rerun targeted checks. |

### Example

```bash
uv run validate-pyproject pyproject.toml
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
