# ADR 005: Use Ruff for linting and formatting

## Status

Accepted

## Context

Python projects traditionally use multiple tools for code quality:

- **Linting:** flake8, pylint, pyflakes, pycodestyle
- **Formatting:** black, autopep8, yapf
- **Import sorting:** isort
- **Security:** bandit

Managing multiple tools means:

- Multiple configuration sections
- Multiple CI steps
- Potential conflicts between tools
- Slower execution (each tool parses code separately)

Ruff is a modern, Rust-based linter and formatter that replaces many of these tools with a single, fast binary.

## Decision

Use Ruff as the sole linter and formatter for this project:

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM"]

[tool.ruff.format]
quote-style = "double"
```

## Consequences

### Positive

- **Single tool** — One dependency, one config section, one CI step
- **Extremely fast** — 10–100x faster than Python-based tools
- **Drop-in replacement** — Compatible with flake8, isort, and black rules
- **Active development** — Rapidly adding new rules and features
- **Built-in formatter** — No need for separate black installation

### Negative

- **Newer tool** — Less battle-tested than flake8/black (though widely adopted)
- **Rust dependency** — Binary distribution, not pure Python
- **Not 100% black-compatible** — Minor formatting differences exist

### Neutral

- Requires occasional config updates as Ruff evolves
- Some rules are preview-only and may change

## Alternatives Considered

### flake8 + black + isort

The traditional stack used by many Python projects.

**Rejected because:** Three tools to configure, slower execution, more complex CI setup.

### pylint

Comprehensive linter with many checks.

**Rejected because:** Very slow, opinionated defaults require extensive configuration, not a formatter.

### Ruff (linting only) + black (formatting)

Use Ruff for linting but keep black for formatting.

**Rejected because:** Ruff's formatter is fast and good enough; reduces dependencies.

## Implementation

- [pyproject.toml](../../pyproject.toml) — `[tool.ruff]` and `[tool.ruff.lint]` sections
- [.pre-commit-config.yaml](../../.pre-commit-config.yaml) — Ruff hooks (`ruff` and `ruff-format`)
- [.github/workflows/lint-format.yml](../../.github/workflows/lint-format.yml) — CI linting and formatting checks

## References

- [Ruff documentation](https://docs.astral.sh/ruff/)
- [Ruff rules reference](https://docs.astral.sh/ruff/rules/)
