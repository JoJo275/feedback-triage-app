# ADR 001: Use src/ layout for package structure

## Status

Accepted

## Context

Python projects can be structured in multiple ways:

1. **Flat layout** — Package at repository root (`mypackage/`)
2. **src/ layout** — Package inside `src/` directory (`src/mypackage/`)

The flat layout is simpler but has a subtle problem: when running tests or scripts from the repository root, Python may import the local source directory instead of the installed package. This can hide packaging bugs that only appear when users install the package.

## Decision

Use the `src/` layout for all Python packages in this project.

```
project/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       └── main.py
├── tests/
└── pyproject.toml
```

## Consequences

### Positive

- **Prevents accidental imports** — Forces you to install the package to import it
- **Surfaces packaging bugs early** — If `pyproject.toml` is misconfigured, imports fail immediately
- **Matches user experience** — Development imports work the same as installed imports
- **Recommended by PyPA** — The Python Packaging Authority recommends this layout

### Negative

- **Requires editable install** — Must run `pip install -e .` for development
- **Slightly more nesting** — One extra directory level
- **Less familiar** — Some developers expect flat layout

### Neutral

- Works with all major build backends (setuptools, hatch, flit, poetry)
- No runtime performance difference

## Alternatives Considered

### Flat Layout

```
project/
├── mypackage/
│   ├── __init__.py
│   └── main.py
├── tests/
└── pyproject.toml
```

**Rejected because:** Running `pytest` or scripts from the repo root can accidentally import the local directory instead of the installed package. This hides packaging bugs until users install it.

### No Package Structure (Single File)

Just a `main.py` at the root.

**Rejected because:** Doesn't scale, can't be installed as a package, no clear separation of concerns.

## Implementation

- [src/simple_python_boilerplate/](../../src/simple_python_boilerplate/) — Package source code
- [pyproject.toml](../../pyproject.toml) — `[tool.setuptools]` section configures `package-dir = {"" = "src"}`
- [tests/](../../tests/) — Tests directory (separate from src/)

## References

- [PyPA Packaging Guide](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Hynek Schlawack: Testing & Packaging](https://hynek.me/articles/testing-packaging/)
