"""Integration tests for CLI entry points and end-to-end flows.

These tests exercise the application through its public interfaces
(entry points, CLI commands) rather than testing individual functions.
They verify that the wiring between main.py, cli.py, and engine.py
works correctly.
"""

import subprocess
import sys

import pytest

# Mark all tests in this module as integration tests.
# Skip with: pytest -m "not integration"
pytestmark = pytest.mark.integration

# ── Entry point smoke tests ──────────────────────────────────


class TestMainEntryPoint:
    """Smoke tests for the ``spb`` entry point (main.main)."""

    def test_main_no_args_exits_zero(self) -> None:
        """Running with no args should print help and exit 0."""
        from simple_python_boilerplate.cli import parse_args, run

        args = parse_args([])
        exit_code = run(args)
        assert exit_code == 0

    def test_main_version_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """``--version`` should print version string and exit 0."""
        from simple_python_boilerplate.cli import parse_args, run

        args = parse_args(["--version"])
        exit_code = run(args)
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "simple-python-boilerplate" in captured.out

    def test_main_help_flag(self) -> None:
        """``--help`` should exit 0 (argparse handles this)."""
        from simple_python_boilerplate.cli import parse_args

        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--help"])
        assert exc_info.value.code == 0


class TestVersionEntryPoint:
    """Smoke tests for the ``spb-version`` entry point."""

    def test_print_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Should print package and Python version info."""
        from simple_python_boilerplate.main import print_version

        print_version()

        captured = capsys.readouterr()
        assert "simple-python-boilerplate" in captured.out
        assert "Python" in captured.out


class TestDoctorEntryPoint:
    """Smoke tests for the ``spb-doctor`` entry point."""

    def test_doctor_runs(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Doctor command should complete without errors."""
        from simple_python_boilerplate.main import doctor

        monkeypatch.setattr("sys.argv", ["spb-doctor"])
        doctor()

        captured = capsys.readouterr()
        assert "doctor" in captured.out.lower()
        assert "Version" in captured.out or "version" in captured.out

    def test_doctor_via_cli_run(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``cli.run(parse_args(["doctor"]))`` should invoke doctor and exit 0."""
        from simple_python_boilerplate.cli import parse_args, run

        # doctor() internally calls argparse.parse_args() which reads sys.argv
        monkeypatch.setattr("sys.argv", ["spb-doctor"])
        args = parse_args(["doctor"])
        exit_code = run(args)
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "doctor" in captured.out.lower()


# ── CLI command integration tests ────────────────────────────


class TestProcessCommand:
    """Integration tests for the ``process`` subcommand."""

    def test_process_with_input(self, capsys: pytest.CaptureFixture[str]) -> None:
        """``process <input>`` should output processed result."""
        from simple_python_boilerplate.cli import parse_args, run

        args = parse_args(["process", "hello world"])
        exit_code = run(args)
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "Processed: hello world" in captured.out

    def test_process_with_output_file(
        self, tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """``process <input> -o <file>`` should write to file."""
        from simple_python_boilerplate.cli import parse_args, run

        output_file = tmp_path / "output.txt"
        args = parse_args(["process", "test data", "-o", str(output_file)])
        exit_code = run(args)
        assert exit_code == 0
        assert output_file.read_text() == "Processed: test data"

    def test_process_with_verbose(
        self, tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """``process <input> -o <file> --verbose`` should print confirmation."""
        from simple_python_boilerplate.cli import parse_args, run

        output_file = tmp_path / "output.txt"
        args = parse_args(["--verbose", "process", "test data", "-o", str(output_file)])
        exit_code = run(args)
        assert exit_code == 0

        captured = capsys.readouterr()
        assert str(output_file) in captured.out

    def test_process_empty_input_rejected(self) -> None:
        """``process ""`` should return non-zero exit code."""
        from simple_python_boilerplate.cli import parse_args, run

        args = parse_args(["process", ""])
        exit_code = run(args)
        assert exit_code == 1


# ── Subprocess tests (true end-to-end) ──────────────────────


class TestSubprocessEntryPoints:
    """Test entry points as subprocesses (closest to real usage).

    These tests run the actual installed console scripts via ``python -m``
    or the module's entry points, verifying the full stack works.
    """

    def test_module_runnable(self) -> None:
        """``python -c 'from simple_python_boilerplate import __version__'`` should work."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from simple_python_boilerplate import __version__; print(__version__)",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert result.stdout.strip()  # version string is non-empty

    def test_version_entry_point(self) -> None:
        """The print_version entry point should be callable via Python."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from simple_python_boilerplate.main import print_version; print_version()",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "simple-python-boilerplate" in result.stdout

    def test_cli_help(self) -> None:
        """``python -c '...parse_args(["--help"])'`` should print usage."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from simple_python_boilerplate.cli import create_parser; "
                    "create_parser().print_help()"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert (
            "usage:" in result.stdout.lower()
            or "simple-python-boilerplate" in result.stdout
        )
