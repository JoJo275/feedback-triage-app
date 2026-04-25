---
description: >-
  Use when writing, modifying, or reviewing test files. Covers pytest
  conventions, fixture patterns, coverage, naming, and the test matrix.
applyTo: "tests/**"
---

# Tests — Copilot Instructions

## Framework & Config

- **pytest** with `pytest-cov` for coverage.
- All config in `pyproject.toml` under `[tool.pytest.ini_options]`.
- Run: `hatch run test` (default env), `hatch run test:run` (3.11–3.13 matrix).
- Coverage: `hatch run test-cov`.

## Directory Layout

```
tests/
├── conftest.py        # Shared fixtures (repo_root, tmp_path helpers)
├── unit/              # Fast, isolated unit tests
│   ├── test_*.py
│   └── ...
└── integration/       # Slower tests that touch filesystem, network, subprocesses
    ├── test_*.py
    └── ...
```

## Naming

- Files: `test_<module_or_feature>.py`.
- Functions: `test_<function_or_behavior>`.
- Classes: `Test<Class>` (rare — prefer standalone functions).
- Fixtures: descriptive nouns (`repo_root`, `sample_config`, `mock_git`).

## Type Hints in Tests

- **Relaxed:** Don't require full annotations on mocks, fixtures, or test helpers.
- Annotate fixtures only when the return type clarifies intent.
- Never annotate `self` on test class methods.

## Fixtures

- Shared fixtures go in `tests/conftest.py`.
- Use `tmp_path` (built-in) for temporary files — never hard-code paths.
- Prefer `pytest.fixture` scope `"function"` (default) unless setup is expensive.
- For expensive setup, use `"session"` scope and document why.

## Assertions

- Use plain `assert` — pytest's introspection gives detailed diffs.
- For expected exceptions: `with pytest.raises(TypeError, match="expected .+")`.
- For warnings: `with pytest.warns(DeprecationWarning)`.
- Avoid `assertEqual`, `assertTrue` — those are `unittest` style.

## Mocking

- `unittest.mock.patch` / `unittest.mock.MagicMock` — standard library.
- Patch at the import site: `patch("module_under_test.dependency")`.
- Prefer dependency injection over patching where feasible.

## Markers

- `@pytest.mark.slow` — tests that take > 1 second.
- `@pytest.mark.integration` — tests requiring external resources.
- Register custom markers in `pyproject.toml` under `[tool.pytest.ini_options] markers`.

## Coverage

- Coverage config in `pyproject.toml` under `[tool.coverage.*]`.
- Source: `src/simple_python_boilerplate/`.
- Don't test private implementation details — test behaviour through public API.

## Pre-push Gate

- `hatch run test` runs as a **pre-push** hook. All tests must pass before pushing.
- The matrix (`hatch run test:run`) covers Python 3.11, 3.12, 3.13.

## What NOT to Test

- Generated files, third-party library internals.
- Private methods directly (test through public API).
- Type annotations (mypy handles that).

## Common Patterns

```python
# Fixture with cleanup
@pytest.fixture
def temp_config(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text('[project]\nname = "test"\n')
    return config

# Parametrize for multiple inputs
@pytest.mark.parametrize("input_val,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
])
def test_upper(input_val, expected):
    assert input_val.upper() == expected

# Subprocess mock
def test_git_version(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/git")
    # ...
```
