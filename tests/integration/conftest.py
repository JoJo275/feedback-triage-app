"""Integration test configuration — fixtures specific to integration tests.

Fixtures here are available to all tests under tests/integration/.
For shared fixtures (available to all tests), see tests/conftest.py.

Note:
    All tests in this directory are automatically marked with the
    ``integration`` marker via the pytestmark in individual test files.
    To skip integration tests: ``pytest -m "not integration"``
"""

from __future__ import annotations
