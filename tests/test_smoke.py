"""Pre-Phase smoke test — package imports and exposes a version string.

Replaced in Phase 1 by real config/health/version tests.
"""

from __future__ import annotations

import feedback_triage


def test_package_has_version() -> None:
    assert isinstance(feedback_triage.__version__, str)
    assert feedback_triage.__version__
