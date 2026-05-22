# Tool Template (Replace With Tool Name)

<!-- Optional admonitions. Delete any block that does not apply. -->

!!! danger "Required Change"
    TODO: Add must-change or hard boundary warnings for this specific tool page.

!!! note "Context"
    TODO: Add important implementation or adoption context for this tool.

!!! tip "Practical Guidance"
    TODO: Add practical authoring or usage tips for this tool page.

---

## Metadata

- **Tool name:** TODO
- **Status:** TODO (Active, Planned, Deferred)
- **Layer:** TODO (Frontend / Backend / Database / Workers / CI / Docs / Operations)
- **Scope:** TODO
- **Owner:** TODO
- **Adoption gate:** TODO (Required for Planned/Deferred tools. Use `Already adopted` for Active tools.)
- **Last reviewed:** YYYY-MM-DD

## [Tool Name]

### Role

TODO: One sentence describing what this tool owns in this project.

### What it is

TODO: Plain-English explanation of the tool.

### Why this project uses it

TODO: Specific reason this project needs this tool.

### Repo locations

| Purpose | Path |
| --- | --- |
| Config | `path/to/config` |
| Source files | `path/to/source` |
| Generated output | `path/to/output` |
| Tests | `path/to/tests` |

### Common commands

```bash
# TODO: Add one or more real commands
<command>
```

### Inputs and outputs

| Type | Examples |
| --- | --- |
| Inputs | `schemas, files, requests, config, events` |
| Outputs | `generated types, rendered UI, DB records, cache entries` |

### Standard workflow

1. Step one.
2. Step two.
3. Step three.

### Integration points

| Integrates with | How |
| --- | --- |
| Tool name | Relationship |

### Boundaries

**Use this tool for:**

- TODO

**Do not use this tool for:**

- TODO

### Testing expectations

TODO: Add required tests, checks, and validation commands.

### Observability and failure modes

| Failure | How detected | Response |
| --- | --- | --- |
| Failure scenario | Signal or alert | Required action |

### Example

TODO: Add a small practical example.

### Related docs

- TODO: `docs/path/to/doc.md`
- TODO: `docs/adr/NNN-title.md`

### Runtime and cost footprint

| Category | Notes |
| --- | --- |
| Runtime service? | Yes/No |
| Runs in CI only? | Yes/No |
| Requires external service? | Yes/No |
| Cost risk | Low / Medium / High |
| Scaling concern | TODO |

### Source-of-truth responsibility

TODO: State what this tool owns, if anything. If it owns no product truth, say so explicitly.

Examples:

- PostgreSQL owns durable product data.
- Redis owns no durable product truth.
- Redux Toolkit owns draft dashboard editor state, not saved layouts.
- TanStack Query owns frontend server-state cache, not backend truth.

### Rollback or replacement plan

TODO: Explain how this tool can be removed, replaced, or backed out if it causes problems.
