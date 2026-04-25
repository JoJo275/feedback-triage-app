# ADR 002: Use pyproject.toml for all configuration

## Status

Accepted

## Context

Historically, Python projects used multiple configuration files:

- `setup.py` — Build script (executable Python)
- `setup.cfg` — Declarative build config
- `requirements.txt` — Dependencies
- Tool-specific files: `.flake8`, `mypy.ini`, `pytest.ini`, `.isort.cfg`, etc.

PEP 517/518/621 introduced `pyproject.toml` as a unified configuration file for Python projects, and most modern tools now support it.

## Decision

Use `pyproject.toml` as the single source of truth for:

- Package metadata (name, version, description, dependencies)
- Build system configuration
- Tool configurations (pytest, ruff, mypy, coverage, etc.)

Avoid legacy files like `setup.py`, `setup.cfg`, and tool-specific config files.

## Consequences

### Positive

- **Single file** — All configuration in one place
- **Declarative** — No executable code in build config
- **Standard format** — TOML is well-defined and readable
- **Modern tooling** — All major tools support `[tool.X]` sections
- **Easier onboarding** — New contributors find everything in one file

### Negative

- **Some tools lag behind** — Older tools may not support pyproject.toml
- **Large file** — Can become lengthy with many tool configs
- **Learning curve** — Developers familiar with setup.py need to adapt

### Neutral

- `requirements.txt` still useful for pinned deployments or CI caching

## Alternatives Considered

### setup.py + setup.cfg

Traditional approach with executable `setup.py` and declarative `setup.cfg`.

**Rejected because:** `setup.py` is executable code (security concern), requires two files, and is being phased out by the Python community.

### Poetry (pyproject.toml with [tool.poetry])

Poetry uses pyproject.toml but with its own `[tool.poetry]` format instead of PEP 621's `[project]`.

**Rejected because:** Non-standard metadata format, vendor lock-in, adds complexity for simple projects.

### Multiple Config Files

Separate files for each tool: `.flake8`, `mypy.ini`, `pytest.ini`, etc.

**Rejected because:** Scattered configuration, harder to onboard new contributors, most tools now support pyproject.toml.

## Implementation

- [pyproject.toml](../../pyproject.toml) — Single configuration file containing:
    - `[build-system]` — Build backend configuration
    - `[project]` — Package metadata (PEP 621)
    - `[tool.pytest.ini_options]` — pytest configuration
    - `[tool.coverage]` — Coverage configuration
    - `[tool.ruff]` — Ruff linter/formatter configuration
    - `[tool.mypy]` — mypy type checker configuration

## References

- [PEP 517 – Build system interface](https://peps.python.org/pep-0517/)
- [PEP 518 – Build system requirements](https://peps.python.org/pep-0518/)
- [PEP 621 – Project metadata](https://peps.python.org/pep-0621/)
