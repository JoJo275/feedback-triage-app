"""Tests for entry point functions — covering start() and main()."""

import sys
from unittest.mock import patch

import pytest


class TestMainFunction:
    """Cover main() which calls cli.run(cli.parse_args()) then sys.exit."""

    def test_main_exits_zero_no_args(self):
        """main() with no args should sys.exit(0)."""
        from simple_python_boilerplate.entry_points import main

        with patch("sys.argv", ["spb"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


class TestStartFunction:
    """Cover start() — bootstrap script entry point."""

    def test_start_bootstrap_not_found(self, tmp_path):
        """start() should exit 1 when bootstrap.py doesn't exist."""
        from simple_python_boilerplate.entry_points import start

        # Point the module to a fake root with no bootstrap.py
        fake_file = tmp_path / "src" / "simple_python_boilerplate" / "entry_points.py"
        fake_file.parent.mkdir(parents=True)
        fake_file.touch()

        with (
            patch("simple_python_boilerplate.entry_points.__file__", str(fake_file)),
            patch("sys.argv", ["spb-start"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            start()
        assert exc_info.value.code == 1

    def test_start_runs_bootstrap(self, tmp_path):
        """start() should call subprocess when bootstrap.py exists."""
        from simple_python_boilerplate.entry_points import start

        # Create the expected directory structure
        fake_root = tmp_path / "repo"
        scripts_dir = fake_root / "scripts"
        scripts_dir.mkdir(parents=True)
        bootstrap = scripts_dir / "bootstrap.py"
        bootstrap.write_text("print('bootstrapping')")

        fake_file = fake_root / "src" / "simple_python_boilerplate" / "entry_points.py"
        fake_file.parent.mkdir(parents=True)
        fake_file.touch()

        with (
            patch("simple_python_boilerplate.entry_points.__file__", str(fake_file)),
            patch("sys.argv", ["spb-start"]),
            patch("subprocess.call", return_value=0) as mock_call,
            pytest.raises(SystemExit) as exc_info,
        ):
            start()

        assert exc_info.value.code == 0
        mock_call.assert_called_once_with(
            [sys.executable, str(bootstrap)],
            cwd=str(fake_root),
        )
