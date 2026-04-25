# ADR 006: Use pytest for testing

## Status

Accepted

## Context

Python has several testing frameworks:

- **unittest** — Built-in, class-based, xUnit-style
- **pytest** — Third-party, function-based, fixture-oriented
- **nose/nose2** — Extended unittest (largely deprecated)

The choice of testing framework affects:

- How tests are written and organized
- Available assertion styles and fixtures
- Plugin ecosystem and extensibility
- CI integration and reporting

## Decision

Use pytest as the testing framework:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-ra", "-q"]
```

Tests are written as simple functions with `assert`:

```python
def test_example():
    result = add(2, 3)
    assert result == 5
```

## Consequences

### Positive

- **Simple syntax** — Plain `assert` statements with detailed failure messages
- **Fixtures** — Powerful dependency injection for test setup/teardown
- **Parametrize** — Easy data-driven testing with `@pytest.mark.parametrize`
- **Plugin ecosystem** — pytest-cov, pytest-mock, pytest-asyncio, and hundreds more
- **Auto-discovery** — Finds tests automatically by naming convention
- **Better output** — Clear, colorized failure messages

### Negative

- **External dependency** — Not built into Python (must install)
- **Magic behavior** — Fixture injection can be surprising to newcomers
- **Learning curve** — Advanced features (conftest, plugins) take time to master

### Neutral

- Can run unittest-style tests too (backward compatible)
- pytest-cov integrates coverage reporting seamlessly

## Alternatives Considered

### unittest (standard library)

Python's built-in testing framework.

**Rejected because:** Verbose class-based syntax, weaker assertion introspection, limited fixture support, smaller plugin ecosystem.

### doctest

Embed tests in docstrings.

**Rejected because:** Good for documentation examples but awkward for comprehensive testing; pytest can run doctests anyway.

## Implementation

- [pyproject.toml](../../pyproject.toml) — `[tool.pytest.ini_options]` section
- [tests/](../../tests/) — Test directory
- [tests/unit/test_example.py](../../tests/unit/test_example.py) — Example test file
- [.github/workflows/test.yml](../../.github/workflows/test.yml) — CI test execution

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
