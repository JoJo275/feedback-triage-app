# Tests

<!-- TODO (template users): Replace the placeholder tests with your own.
     Update this README with project-specific testing conventions, fixture
     descriptions, and any required test infrastructure (databases, APIs). -->

Test suite for the project.

## Structure

```text
tests/
├── conftest.py        # Shared fixtures and pytest configuration
├── unit/              # Unit tests (fast, isolated)
│   └── test_*.py
└── integration/       # Integration tests (database, external services)
    ├── test_*.py
    └── sql/           # SQL fixtures for integration tests
```

## Running Tests

```bash
# Via Task runner (preferred)
task test              # Run all tests
task test:cov          # Run with coverage report
task test:matrix       # Run across Python 3.11-3.13

# Via pytest directly
pytest                 # Run all tests
pytest -v              # Verbose output
pytest tests/unit/     # Only unit tests
pytest tests/integration/  # Only integration tests
pytest --cov=simple_python_boilerplate  # With coverage

# Specific tests
pytest tests/unit/test_example.py
pytest tests/unit/test_example.py::test_placeholder
pytest -k "test_name_pattern"  # By name pattern
```

## Writing Tests

- Place unit tests in [tests/unit/](unit/)
- Place integration tests in [tests/integration/](integration/)
- Name test files `test_*.py`
- Name test functions `test_*`
- Use `conftest.py` for shared fixtures (project-wide in root, or scoped
  in subdirectories)
- Mark slow tests with `@pytest.mark.slow` for selective exclusion

### Unit vs Integration

| Aspect           | Unit (`tests/unit/`) | Integration (`tests/integration/`) |
| ---------------- | -------------------- | ---------------------------------- |
| **Speed**        | Fast (milliseconds)  | Slower (may involve I/O)           |
| **Dependencies** | Mocked / none        | Real database, filesystem, APIs    |
| **Isolation**    | Fully isolated       | May share state                    |
| **Run when**     | Every commit         | Every commit + dedicated CI job    |

## Coverage

Coverage is configured in `pyproject.toml` under `[tool.coverage.*]`.
CI uploads coverage reports to Codecov. View the threshold and exclude
patterns there.

## See Also

- [pyproject.toml](../pyproject.toml) — pytest and coverage configuration
- [conftest.py](conftest.py) — Shared test fixtures
- [ADR 006: pytest](../docs/adr/006-pytest-for-testing.md) — Why we use pytest
- [ADR 029: Testing strategy](../docs/adr/029-testing-strategy.md) — Unit/integration split, coverage, matrix
