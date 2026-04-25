"""Root test configuration — shared fixtures and marker registration.

This conftest.py is automatically loaded by pytest for all tests in this
directory and below. It registers custom markers and provides shared fixtures
that any test file can use without importing.

Pytest conftest.py files:
    - Are auto-discovered (no imports needed)
    - Provide fixtures available to all tests in their directory tree
    - Register markers so ``strict_markers`` can catch typos
    - Run hooks like ``pytest_configure`` for custom setup

See Also:
    - tests/unit/conftest.py — unit-test-specific fixtures
    - tests/integration/conftest.py — integration-test-specific fixtures
    - https://docs.pytest.org/en/stable/reference/fixtures.html
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ── Shared fixtures ──────────────────────────────────────────


@pytest.fixture()
def project_root() -> Path:
    """Return the project root directory (where pyproject.toml lives).

    Useful for tests that need to read config files or resolve paths
    relative to the repository root.
    """
    return Path(__file__).resolve().parent.parent


@pytest.fixture()
def sample_input() -> str:
    """Provide sample input data for processing tests.

    TODO (template users): Replace this with a fixture relevant to your
    project, or delete it if you don't need shared test data.

    Returns:
        A non-empty string suitable for placeholder tests.
    """
    return "hello world"
