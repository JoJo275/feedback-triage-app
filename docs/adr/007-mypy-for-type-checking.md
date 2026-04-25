# ADR 007: Use mypy for static type checking

## Status

Accepted

## Context

Python is dynamically typed, but type hints (PEP 484) allow optional static type checking. Several type checkers exist:

- **mypy** — The original, most widely used
- **pyright** — Microsoft's checker, powers Pylance in VS Code
- **pytype** — Google's checker with type inference
- **pyre** — Facebook's checker

Type checking catches bugs before runtime:

- Incorrect argument types
- Missing return statements
- Attribute access on wrong types
- None/null safety issues

## Decision

Use mypy with strict mode for static type checking:

```toml
[tool.mypy]
strict = true
warn_return_any = true
warn_unused_ignores = true
```

All public functions must have type annotations.

## Consequences

### Positive

- **Early bug detection** — Catches type errors before runtime
- **Documentation** — Type hints serve as inline documentation
- **IDE support** — Better autocomplete and refactoring
- **Ecosystem standard** — Most Python projects use mypy
- **Gradual adoption** — Can start loose and tighten over time

### Negative

- **Annotation overhead** — Must write type hints for public APIs
- **False positives** — Sometimes mypy is wrong or overly strict
- **Third-party stubs** — Some libraries lack type information
- **Learning curve** — Generics, protocols, and overloads can be complex

### Neutral

- Strict mode can be relaxed per-file with `# mypy: disable-error-code`
- VS Code's Pylance uses pyright, which is compatible but may differ slightly

## Alternatives Considered

### pyright

Microsoft's type checker, faster than mypy.

**Not rejected, but mypy preferred because:** mypy is the ecosystem standard, has more documentation, and is what most CI systems expect. Pyright is still used via Pylance in VS Code.

### No type checking

Skip static type checking entirely.

**Rejected because:** Type hints catch real bugs, improve maintainability, and are expected in modern Python projects.

## Implementation

- [pyproject.toml](../../pyproject.toml) — `[tool.mypy]` section with `strict = true`
- [.pre-commit-config.yaml](../../.pre-commit-config.yaml) — mypy hook for pre-commit checks
- [src/simple_python_boilerplate/](../../src/simple_python_boilerplate/) — Type-annotated source code

## References

- [mypy documentation](https://mypy.readthedocs.io/)
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)
- [typing module](https://docs.python.org/3/library/typing.html)
