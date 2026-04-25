# ADR 043: Environment Data Collector Plugin Architecture

<!-- TODO (template users): If you remove the dashboard or replace the
     collector system, supersede this ADR with your new approach. -->

## Status

Accepted

## Context

The environment dashboard ([ADR 041](041-env-inspect-web-dashboard.md))
needs to gather system, project, and tooling data from many independent
sources (git, Python runtimes, packages, hardware, network, security
tools, CI status, containers, etc.). Mixing all collection logic into a
single module would be hard to maintain, test, and extend.

## Decision

Adopt a **plugin-based collector architecture** in
`scripts/_env_collectors/`. Each collector is a self-contained Python
module that:

1. Inherits from `_base.BaseCollector`.
2. Implements a `collect()` method returning structured data.
3. Is auto-discovered by the `__init__.py` registry — no manual
   registration required.

A tiered system (Tier 1 / 2 / 3) categorises collectors by importance
and execution cost. An `insights.py` module post-processes collected
data to generate warnings and recommendations.

## Alternatives Considered

### Single monolithic collector

Put all collection logic in one file.

**Rejected because:** A single 2,000+ line module is unmaintainable.
Individual collectors can be tested, toggled, and extended independently.

### Third-party plugin framework (pluggy, stevedore)

Use an established plugin system.

**Rejected because:** The discovery needs are simple (glob a directory,
import modules, call `collect()`). A framework adds a dependency for
functionality achievable in ~30 lines of Python.

## Consequences

### Positive

- Adding a new data source requires only creating a new file in
  `scripts/_env_collectors/` — no registry edits.
- Each collector is independently testable.
- Collectors can be toggled or tiered by cost (fast vs. slow).
- The insights engine can cross-reference data from multiple collectors.

### Negative

- Contributors must learn the `BaseCollector` contract.
- Auto-discovery means import errors in one collector can affect the
  whole dashboard.

### Mitigations

- Each collector wraps its collection in try/except — a failing
  collector degrades gracefully without crashing the dashboard.
- The `.github/instructions/collectors.instructions.md` file documents
  the contract and conventions.

## Implementation

- [`scripts/_env_collectors/`](../../scripts/_env_collectors/) — Collector plugin directory (20 collectors)
- [`scripts/_env_collectors/_base.py`](../../scripts/_env_collectors/_base.py) — Base class
- [`scripts/_env_collectors/insights.py`](../../scripts/_env_collectors/insights.py) — Cross-collector insights engine
- [`tools/dev_tools/env_dashboard/collector.py`](../../tools/dev_tools/env_dashboard/collector.py) — Dashboard integration
- [`.github/instructions/collectors.instructions.md`](../../.github/instructions/collectors.instructions.md) — Conventions

## References

- [ADR 041](041-env-inspect-web-dashboard.md) — Environment inspection dashboard
- [ADR 036](036-diagnostic-tooling-strategy.md) — Diagnostic tooling strategy
