# PostgreSQL 16

!!! note "Active Tool"
    This tool is currently active in this repository and documented from the canonical inventory.

---

## Metadata

- **Tool name:** PostgreSQL 16
- **Status:** Active
- **Layer:** Database
- **Scope:** Data store
- **Owner:** Engineering
- **Adoption gate:** Already adopted
- **Last reviewed:** 2026-05-23

## PostgreSQL 16

### Role

Production and test DB dialect baseline with durable relational guarantees.

### What it is

Primary relational database and source-of-truth store.

### Why this project uses it

Production and test DB dialect baseline with durable relational guarantees.

### Repo locations

| Purpose | Path |
| --- | --- |
| Config | docs/tooling.md |
| Source files | src/feedback_triage/ and alembic/ |
| Generated output | Not applicable |
| Tests | tests/ |

### Common commands

```bash
task up
```

### Verify tool exists

Run:

```bash
task up
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

- Local dev DB, integration tests, migration validation, and permanent product data storage.

**Do not use this tool for:**

- Short-lived counters, cache, ephemeral locks, or temporary rate-limit state.

### Testing expectations

Run the relevant commands in this page and validate with task check before merge when changes can affect quality gates.

### Observability and failure modes

| Failure | How detected | Response |
| --- | --- | --- |
| Tool command fails or returns non-zero | Local command output and CI job status | Review config and command arguments, then rerun targeted checks. |

### Example

```bash
task up
```

### Related docs

- ../tooling.md
- ../design/tool-decisions.md
- ../workflows.md

### Runtime and cost footprint

| Category | Notes |
| --- | --- |
| Runtime service? | Yes |
| Runs in CI only? | No |
| Requires external service? | Yes |
| Cost risk | Medium |
| Scaling concern | Reassess as adoption, data volume, or workflow frequency increases. |

### Source-of-truth responsibility

PostgreSQL owns durable product data for the application.

### Rollback or replacement plan

Remove this tool's config and workflow hooks in the same change, update docs/tooling.md, and verify with task check plus affected CI jobs.
