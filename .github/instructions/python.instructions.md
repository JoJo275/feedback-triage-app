---
description: >-
  Use when writing or modifying Python source code in src/, scripts/,
  mkdocs-hooks/, or tools/. Covers style, imports, type hints, security,
  and tooling conventions.
applyTo: "**/*.py"
---

# Python — Copilot Instructions

## Language & Runtime

- **Minimum Python:** 3.11 (see `requires-python` in `pyproject.toml`).
- **Use modern syntax:** `X | Y` unions, `match`/`case`, `tomllib`, `ExceptionGroup` — no backports.
- **`from __future__ import annotations`** at the top of every file.

## Style

- **Formatter/linter:** Ruff (config in `pyproject.toml [tool.ruff]`).
  Write code that passes on the first try.
- **Quotes:** Double quotes (`"`) everywhere.
- **Trailing commas:** Always on the last element of multi-line collections.
- **Import order:** stdlib → third-party → local (isort via Ruff).
- **Absolute imports:** `from simple_python_boilerplate.module import func`.
  Never use relative imports or import from `src`.
- **Constants:** `UPPER_SNAKE_CASE`.
- **No `print()` in `src/`:** Use `logging`. The T20 Ruff rule enforces this.
  `print()` is allowed in `scripts/` for primary output.

## Type Hints

- **Required** on all public functions in `src/`.
- **mypy strict mode** (`pyproject.toml [tool.mypy]`).
- Use `pathlib.Path` over `os.path` (PTH Ruff rules).
- Prefer `list`, `dict`, `tuple`, `set` lowercase generics (PEP 585).
- Use `from __future__ import annotations` to enable `X | Y` union syntax.

## Docstrings

- **Google style** on all public functions and classes.
- Module-level docstring on every file explaining purpose.

## Security (Bandit enforced)

- No `eval()`, `exec()`, `pickle` on untrusted data.
- No `shell=True` in `subprocess` calls — use arg lists.
- No hardcoded `/tmp` — use `tempfile`.
- `yaml.safe_load()` only, never `yaml.load()`.
- Parameterised queries for any SQL — no string interpolation.

## Pathlib & Subprocess

- `pathlib.Path` over `os.path` for all file operations.
- `subprocess.run()` with explicit arg lists, never `shell=True`.

## TOML & Metadata

- `tomllib` (stdlib) for reading TOML. No `toml` or `tomli` third-party.
- `importlib.metadata` for package introspection at runtime.

## Error Handling

- **Validate at system boundaries** (CLI args, file I/O, network).
- Don't add error handling for impossible scenarios.
- Actionable error messages: what went wrong + how to fix it.

## Ruff Rules to Know

| Rule  | Meaning                                                  |
|-------|----------------------------------------------------------|
| T20   | No `print()` in `src/` — use `logging`                  |
| PTH   | Use `pathlib` instead of `os.path`                       |
| UP    | Modern 3.11+ syntax (unions, `match`, etc.)              |
| C4    | Comprehensions over `list()`/`dict()` calls              |
| PERF  | `list.extend()` over append-in-loop                      |
| E501  | **Disabled** — don't manually wrap lines for length      |

## Common Gotchas

1. **Mutable default arguments:** `def func(items=[])` is a bug → use `None`.
2. **Wrong imports:** Use `simple_python_boilerplate`, not `src`.
3. **Missing editable install:** `pip install -e .` for src/ layout.
4. **Bare `pip install`:** Always use `hatch run` or `hatch shell`.
5. **Stale Hatch env:** `hatch env remove default` then re-create after dep removal.
