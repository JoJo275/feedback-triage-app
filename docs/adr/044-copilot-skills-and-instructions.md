# ADR 044: Copilot Skills and Instruction File Architecture

<!-- TODO (template users): After forking, update .github/copilot-instructions.md
     and instruction files to match YOUR project. Remove skills that don't
     apply. See this ADR for the architecture rationale. -->

## Status

Accepted

## Context

As the repository's tooling grew (47 pre-commit hooks, 37 workflows, 20+
scripts, a dashboard web app), GitHub Copilot needed progressively more
context to generate code that follows project conventions. A single
`copilot-instructions.md` file grew unwieldy and could not provide
file-type-specific guidance.

## Decision

Adopt a **layered instruction architecture**:

1. **`copilot-instructions.md`** — Project-wide rules loaded on every
   interaction (working style, conventions, review priorities).
2. **`applyTo`-scoped `.instructions.md` files** — Targeted rules that
   activate only when editing matching files (e.g., `tests/**`,
   `scripts/_env_collectors/**`, dashboard templates).
3. **`SKILL.md` files** — Multi-step procedures (adding ADRs, workflows,
   scripts) that Copilot loads on demand when a request matches the skill
   description.

Instruction files live in `.github/instructions/` and are referenced from
`copilot-instructions.md`'s "Targeted Instruction Files" table.

## Alternatives Considered

### Single instructions file

Keep everything in `copilot-instructions.md`.

**Rejected because:** The file exceeded 400 lines. Copilot loads the
full file on every interaction — most of it irrelevant to the current
task. `applyTo` scoping solves this.

### No instruction files

Rely on Copilot's general knowledge.

**Rejected because:** Copilot consistently generated code that violated
project-specific conventions (wrong import style, missing `from __future__`
imports, `os.path` instead of `pathlib`, wrong test patterns).

## Consequences

### Positive

- Copilot receives the right context for the right file type.
- Skills encode multi-step procedures that prevent forgotten sync steps.
- New conventions are documented once and enforced automatically.

### Negative

- Instruction files must be kept in sync with actual conventions.
- Contributors unfamiliar with the system may not know these files exist.

### Mitigations

- `copilot-instructions.md` lists all instruction files in a table.
- The SKILL.md references instruction file updates as explicit steps.

## Implementation

- [`.github/copilot-instructions.md`](../../.github/copilot-instructions.md) — Project-wide rules
- [`.github/instructions/`](../../.github/instructions/) — Targeted instruction files
- [`.github/SKILL.md`](../../.github/SKILL.md) — Multi-step procedures
- [`.github/instructions/python.instructions.md`](../../.github/instructions/python.instructions.md) — Python conventions
- [`.github/instructions/tests.instructions.md`](../../.github/instructions/tests.instructions.md) — Test conventions
- [`.github/instructions/collectors.instructions.md`](../../.github/instructions/collectors.instructions.md) — Collector conventions
- [`.github/instructions/dashboard.instructions.md`](../../.github/instructions/dashboard.instructions.md) — Dashboard conventions

## References

- [ADR 035](035-copilot-instructions-as-context.md) — Copilot instructions as developer context
- [VS Code Copilot Customization docs](https://code.visualstudio.com/docs/copilot/copilot-customization)
