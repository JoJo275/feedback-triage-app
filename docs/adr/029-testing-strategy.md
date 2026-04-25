# ADR 029: Testing Strategy

## Status

Accepted

## Context

[ADR 006](006-pytest-for-testing.md) established pytest as the testing
framework. This ADR addresses higher-level questions that ADR 006 did not
cover: how tests are organized, what coverage expectations exist, how the
test matrix works, and where the boundaries are between test categories.

### Forces

- Tests must run fast in local development (seconds, not minutes)
- CI must validate across Python 3.11–3.13 to match the support matrix
- Coverage must be measured and enforced to prevent silent regressions
- Integration tests may need external resources (database, network) that
  unit tests must not depend on
- This is a template — the testing structure should be a clear example for
  template users to follow

## Decision

### Directory structure

```
tests/
├── conftest.py              # Root fixtures and marker registration
├── unit/                    # Fast, isolated tests (no I/O, no network)
│   ├── conftest.py          # Unit-test-specific fixtures
│   ├── __init__.py
│   ├── test_example.py      # Example test (template placeholder)
│   ├── test_version.py      # Package version test
│   ├── test_archive_todos.py
│   ├── test_dep_versions.py
│   ├── test_doctor.py
│   ├── test_env_doctor.py
│   ├── test_repo_doctor.py
│   ├── test_workflow_versions.py
│   └── test_api.py
└── integration/             # Tests that touch real resources
    ├── conftest.py          # Integration-specific fixtures
    ├── __init__.py
    ├── test_cli_smoke.py    # CLI end-to-end smoke tests
    ├── test_db_example.py   # Database integration tests
    └── sql/                 # SQL file validation tests
```

### Test categories

| Category    | Directory            | Marker                     | Characteristics                                             |
| :---------- | :------------------- | :------------------------- | :---------------------------------------------------------- |
| Unit        | `tests/unit/`        | (none — default)           | No I/O, no network, no database. Fast. Mocked dependencies. |
| Integration | `tests/integration/` | `@pytest.mark.integration` | May use real files, databases, or subprocesses. Slower.     |
| Slow        | Any                  | `@pytest.mark.slow`        | Long-running tests. Deselect with `-m "not slow"`.          |

### Custom markers

Registered in `pyproject.toml` under `[tool.pytest.ini_options]` with
`strict_markers = true` to catch typos:

```toml
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]
```

### Coverage

Coverage is configured in `pyproject.toml` under `[tool.coverage.*]`:

- **Source:** `src/` (the installed package)
- **Branch coverage:** enabled
- **Minimum threshold:** 80% (`fail_under = 80`)
- **Path mapping:** ensures CI (site-packages) and local (src/) coverage
  data merge correctly
- **Excluded lines:** `pragma: no cover`, `TYPE_CHECKING` blocks,
  `__main__` guards, `NotImplementedError`

Template users should raise the threshold as their test suite matures.

### Test matrix

Hatch manages a test matrix across Python 3.11, 3.12, and 3.13:

```toml
[[tool.hatch.envs.test.matrix]]
python = ["3.11", "3.12", "3.13"]
```

This mirrors the CI matrix in `.github/workflows/test.yml`. Running locally:

```bash
hatch run test:run           # All Python versions
hatch run +py=3.12 test:run  # Specific version
task test:matrix             # Via Taskfile
```

### Pytest configuration

Key settings in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
strict_markers = true
strict_config = true
filterwarnings = ["error::DeprecationWarning"]
```

- `strict_markers` catches marker typos at collection time
- `strict_config` catches invalid pytest config keys
- `filterwarnings` turns deprecation warnings into errors so they surface
  before upstream libraries remove deprecated APIs

## Alternatives Considered

### Flat test directory (no unit/integration split)

All tests in a single `tests/` directory without subdirectories.

**Rejected because:** As the test suite grows, the distinction between fast
unit tests and slower integration tests becomes important for developer
workflow (running just unit tests locally, running the full suite in CI).

### tox for test matrix

Use tox to manage multi-version testing.

**Rejected because:** Hatch already provides matrix support via
`[[tool.hatch.envs.test.matrix]]`. Adding tox would duplicate environment
management and conflict with the Hatch-based workflow
([ADR 016](016-hatchling-and-hatch.md)).

### No coverage threshold

Skip `fail_under` and rely on PR review to catch coverage regressions.

**Rejected because:** Automated enforcement prevents gradual erosion. 80% is
a reasonable starting floor that catches obvious gaps without being punitive
during early development.

### 100% coverage requirement

Require full coverage from the start.

**Rejected because:** 100% creates perverse incentives (testing trivial code,
`# pragma: no cover` spam). 80% is a pragmatic starting point; the template
includes a TODO prompting users to raise it.

## Consequences

### Positive

- Clear separation between fast unit tests and slower integration tests
- Coverage threshold prevents silent regression
- Multi-version matrix catches compatibility issues early
- `strict_markers` and `strict_config` catch configuration errors
- Deprecation warnings surfaced as errors before they become breaking changes
- conftest.py hierarchy provides fixture scoping (root → category-specific)

### Negative

- Developers must decide which directory a new test belongs in
- 80% floor may be too low for mature projects or too high for early prototypes
- Multi-version matrix increases CI run time (~3× for 3 versions)

### Mitigations

- The split is simple (I/O? → integration; no I/O? → unit) with clear
  documentation in `tests/README.md`
- Coverage threshold is configurable via `fail_under` in `pyproject.toml`
- CI matrix runs in parallel, keeping wall-clock time reasonable

## Implementation

- [pyproject.toml](../../pyproject.toml) — `[tool.pytest.ini_options]`,
  `[tool.coverage.*]` sections
- [tests/conftest.py](../../tests/conftest.py) — Root fixtures and markers
- [tests/unit/](../../tests/unit/) — Unit test directory
- [tests/integration/](../../tests/integration/) — Integration test directory
- [.github/workflows/test.yml](../../.github/workflows/test.yml) — CI test
  matrix (3.11–3.13)
- [.github/workflows/coverage.yml](../../.github/workflows/coverage.yml) — CI
  coverage reporting

## References

- [ADR 006](006-pytest-for-testing.md) — pytest as testing framework
- [pytest documentation](https://docs.pytest.org/)
- [coverage.py configuration](https://coverage.readthedocs.io/en/latest/config.html)
- [Hatch test matrix](https://hatch.pypa.io/latest/config/environment/advanced/#matrix)
