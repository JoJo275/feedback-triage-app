# Trivy + Grype

!!! note "Active Tool"
    This tool is currently active in this repository and documented from the canonical inventory.

---

## Metadata

- **Tool name:** Trivy + Grype
- **Status:** Active
- **Layer:** Operations
- **Scope:** Container security
- **Owner:** Engineering
- **Adoption gate:** Already adopted
- **Last reviewed:** 2026-05-23

## Trivy + Grype

### Role

Container vulnerability scanning with complementary DBs.

### What it is

Container vulnerability scanners with complementary advisory data.

### Why this project uses it

Container vulnerability scanning with complementary DBs.

### Repo locations

| Purpose | Path |
| --- | --- |
| Config | docs/tooling.md |
| Source files | Containerfile and docker-compose.yml |
| Generated output | Not applicable |
| Tests | container workflows and local docker runs |

### Common commands

```bash
task check
```

### Verify tool exists

Run:

```bash
task check
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

- Image security checks in CI/release gates.

**Do not use this tool for:**

- Runtime intrusion detection or application-level authorization checks.

### Testing expectations

Run the relevant commands in this page and validate with task check before merge when changes can affect quality gates.

### Observability and failure modes

| Failure | How detected | Response |
| --- | --- | --- |
| Tool command fails or returns non-zero | Local command output and CI job status | Review config and command arguments, then rerun targeted checks. |

### Example

```bash
task check
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

This tool owns no durable product truth by itself.

### Rollback or replacement plan

Remove this tool's config and workflow hooks in the same change, update docs/tooling.md, and verify with task check plus affected CI jobs.
