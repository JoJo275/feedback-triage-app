"""Unit tests for scripts/_container_common.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _container_common import check_non_root

# ---------------------------------------------------------------------------
# check_non_root
# ---------------------------------------------------------------------------


class TestCheckNonRoot:
    """Tests for check_non_root()."""

    def test_non_root_returns_true(self) -> None:
        output = "uid=1000(app) gid=1000(app) groups=1000(app)"
        assert check_non_root(output) is True

    def test_root_returns_false(self) -> None:
        output = "uid=0(root) gid=0(root) groups=0(root)"
        assert check_non_root(output) is False

    def test_unparsable_output_returns_false(self) -> None:
        output = "something unexpected"
        assert check_non_root(output) is False

    def test_empty_output_returns_false(self) -> None:
        assert check_non_root("") is False
