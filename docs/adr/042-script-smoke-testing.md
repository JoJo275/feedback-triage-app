# ADR 042: Script Smoke Testing in CI

<!-- TODO (template users): Update the script list if you add or remove
     scripts. If you remove the smoke-test workflow, supersede this ADR. -->

## Status

Accepted

## Context

The project has 20+ standalone scripts in `scripts/` that are invoked by
CI workflows, Taskfile shortcuts, and developers. A broken import, missing
shared module, or argparse regression in any script is invisible until
someone tries to use it — often mid-PR review or during a release.

Existing CI checks (lint, typecheck, test) catch many issues, but none
exercise the scripts' argument parsers or validate that all transitive
imports resolve in the CI environment.

## Decision

Add a `smoke-test.yml` workflow that runs `python scripts/<name>.py --smoke`
for every smoke-capable script. The `--smoke` flag:

1. Imports the script module (verifying all dependencies resolve).
2. Initialises `argparse` (verifying the parser builds without error).
3. Exits `0` immediately — no real logic is executed.

Scripts are enumerated in a GitHub Actions matrix so failures are isolated
per-script and easy to diagnose.

## Alternatives Considered

### Import-only test via pytest

Write a parametrised pytest test that imports each script module.

**Rejected because:** This catches import errors but not argparse
regressions. The `--smoke` convention is already established in multiple
scripts via the shared `_imports.py` module.

### No smoke testing

Rely on type checking and unit tests to catch regressions.

**Rejected because:** Type checking doesn't run the code. Unit tests
may mock away the exact import chain that breaks in CI. Fast, cheap
smoke tests fill the gap.

## Consequences

### Positive

- Broken script imports are caught before merge.
- Argparse regressions are caught before merge.
- Each script failure is isolated in the matrix — no cascading failures.
- Runs only when `scripts/**` changes (path-filtered).

### Negative

- Adds one more workflow file to maintain.
- New scripts must add the `--smoke` flag to participate (convention, not enforcement).

### Mitigations

- Path filtering limits CI minutes — the workflow only runs on `scripts/**` changes.
- The `--smoke` convention is trivial to implement (3 lines in any script using `_imports.py`).

## Implementation

- [`.github/workflows/smoke-test.yml`](../../.github/workflows/smoke-test.yml) — Workflow definition
- [`scripts/_imports.py`](../../scripts/_imports.py) — Shared `--smoke` handling

## References

- [ADR 024](024-ci-gate-pattern.md) — CI gate pattern
- [ADR 031](031-script-conventions.md) — Script conventions
- [ADR 036](036-diagnostic-tooling-strategy.md) — Diagnostic tooling strategy
