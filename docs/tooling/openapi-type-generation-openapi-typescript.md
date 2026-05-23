# OpenAPI Type Generation (openapi-typescript)

!!! note "Active Tool"
    This tool is currently active in this repository and documented from the canonical inventory.

---

## Metadata

- **Tool name:** OpenAPI Type Generation (openapi-typescript)
- **Status:** Active
- **Layer:** Backend
- **Scope:** API contract
- **Owner:** Engineering
- **Adoption gate:** Already adopted
- **Last reviewed:** 2026-05-23

## OpenAPI Type Generation (openapi-typescript)

### Role

Keeps FastAPI and frontend types aligned from a shared contract.

### What it is

API type generation from OpenAPI schemas for frontend contract sync.

### Why this project uses it

Keeps FastAPI and frontend types aligned from a shared contract.

### Repo locations

| Purpose | Path |
| --- | --- |
| Config | docs/tooling.md |
| Source files | src/feedback_triage/ |
| Generated output | web/src/types/openapi.generated.ts |
| Tests | tests/ |

### Common commands

```bash
npm --prefix web run contracts:generate
npm --prefix web run contracts:check
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

- Use when API surface changes need synchronized frontend models/types.

**Do not use this tool for:**

- Hand-maintaining duplicate backend/frontend API types that drift over time.

### Testing expectations

Run the relevant commands in this page and validate with task check before merge when changes can affect quality gates.

### Observability and failure modes

| Failure | How detected | Response |
| --- | --- | --- |
| Tool command fails or returns non-zero | Local command output and CI job status | Review config and command arguments, then rerun targeted checks. |

### Example

```bash
npm --prefix web run contracts:generate
```

### Related docs

- ../tooling.md
- ../design/tool-decisions.md
- ../workflows.md

### Runtime and cost footprint

| Category | Notes |
| --- | --- |
| Runtime service? | No |
| Runs in CI only? | No |
| Requires external service? | No |
| Cost risk | Low |
| Scaling concern | Reassess as adoption, data volume, or workflow frequency increases. |

### Source-of-truth responsibility

Generated types are derived artifacts. Backend API remains the source of truth.

### Rollback or replacement plan

Remove this tool's config and workflow hooks in the same change, update docs/tooling.md, and verify with task check plus affected CI jobs.
