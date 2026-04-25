"""Unit tests for scripts/test_docker_compose.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from test_docker_compose import (
    ROOT,
    SCRIPT_VERSION,
    _check_docker_available,
    _check_non_root,
    _run,
    main,
)

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class TestMetadata:
    """Verify module-level metadata."""

    def test_version_is_string(self) -> None:
        assert isinstance(SCRIPT_VERSION, str)

    def test_version_format(self) -> None:
        parts = SCRIPT_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_root_is_repo_root(self) -> None:
        assert (ROOT / "pyproject.toml").is_file()


# ---------------------------------------------------------------------------
# _run
# ---------------------------------------------------------------------------


class TestRun:
    """Tests for _run() helper."""

    @patch("_container_common.subprocess.run")
    def test_returns_completed_process(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            ["echo"], 0, stdout="hello\n", stderr=""
        )
        result = _run(["echo", "hello"])
        assert result.returncode == 0
        assert result.stdout == "hello\n"

    @patch("_container_common.subprocess.run")
    def test_passes_timeout(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            ["cmd"], 0, stdout="", stderr=""
        )
        _run(["cmd"], timeout=60)
        _, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 60

    @patch("_container_common.subprocess.run")
    def test_raises_on_check_failure(self, mock_run) -> None:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        with pytest.raises(subprocess.CalledProcessError):
            _run(["cmd"], check=True)


# ---------------------------------------------------------------------------
# _check_docker_available
# ---------------------------------------------------------------------------


class TestCheckDockerAvailable:
    """Tests for _check_docker_available()."""

    @patch("_container_common.subprocess.run")
    def test_returns_true_when_docker_running(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            ["docker", "info"], 0, stdout="", stderr=""
        )
        assert _check_docker_available() is True

    @patch("_container_common.subprocess.run")
    def test_returns_false_when_daemon_not_running(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            ["docker", "info"], 1, stdout="", stderr="error"
        )
        assert _check_docker_available() is False

    @patch("_container_common.subprocess.run", side_effect=FileNotFoundError)
    def test_returns_false_when_docker_not_installed(self, mock_run) -> None:
        assert _check_docker_available() is False

    @patch(
        "_container_common.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=15),
    )
    def test_returns_false_on_timeout(self, mock_run) -> None:
        assert _check_docker_available() is False


# ---------------------------------------------------------------------------
# _check_non_root
# ---------------------------------------------------------------------------


class TestCheckNonRoot:
    """Tests for _check_non_root()."""

    def test_passes_for_non_root_user(self) -> None:
        assert _check_non_root("uid=1000(app) gid=1000(app) groups=1000(app)") is True

    def test_fails_for_root_user(self) -> None:
        assert _check_non_root("uid=0(root) gid=0(root) groups=0(root)") is False

    def test_fails_for_unparsable_output(self) -> None:
        assert _check_non_root("no uid info here") is False

    def test_fails_for_empty_output(self) -> None:
        assert _check_non_root("") is False


# ---------------------------------------------------------------------------
# main (CLI)
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for main() entry point."""

    @patch("test_docker_compose._check_docker_available", return_value=True)
    @patch("test_docker_compose._run")
    def test_dry_run_returns_zero(self, mock_run, mock_docker) -> None:
        with patch("sys.argv", ["test_docker_compose.py", "--dry-run"]):
            assert main() == 0
        mock_run.assert_not_called()

    @patch("test_docker_compose._check_docker_available", return_value=False)
    def test_returns_one_when_docker_unavailable(self, mock_docker) -> None:
        with patch("sys.argv", ["test_docker_compose.py"]):
            assert main() == 1

    @patch("test_docker_compose.os.chdir")
    @patch("test_docker_compose.subprocess.run")  # cleanup call
    @patch("test_docker_compose._check_docker_available", return_value=True)
    @patch("test_docker_compose._run")
    def test_passes_all_steps(
        self, mock_run, mock_docker, mock_cleanup, mock_chdir
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            ["docker"], 0, stdout="uid=1000(app) gid=1000(app)", stderr=""
        )
        with patch("sys.argv", ["test_docker_compose.py"]):
            assert main() == 0

    @patch("test_docker_compose.os.chdir")
    @patch("test_docker_compose.subprocess.run")  # cleanup call
    @patch("test_docker_compose._check_docker_available", return_value=True)
    @patch("test_docker_compose._run")
    def test_fails_on_step_error(
        self, mock_run, mock_docker, mock_cleanup, mock_chdir
    ) -> None:
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker")
        with patch("sys.argv", ["test_docker_compose.py"]):
            assert main() == 1

    @patch("test_docker_compose.os.chdir")
    @patch("test_docker_compose.subprocess.run")  # cleanup call
    @patch("test_docker_compose._check_docker_available", return_value=True)
    @patch("test_docker_compose._run")
    def test_fails_on_timeout(
        self, mock_run, mock_docker, mock_cleanup, mock_chdir
    ) -> None:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=300)
        with patch("sys.argv", ["test_docker_compose.py"]):
            assert main() == 1

    @patch("test_docker_compose.os.chdir")
    @patch("test_docker_compose._check_docker_available", return_value=True)
    @patch("test_docker_compose._run")
    def test_keep_flag_skips_cleanup(self, mock_run, mock_docker, mock_chdir) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            ["docker"], 0, stdout="uid=1000(app) gid=1000(app)", stderr=""
        )
        with (
            patch("sys.argv", ["test_docker_compose.py", "--keep"]),
            patch("test_docker_compose.subprocess.run") as mock_subprocess,
        ):
            assert main() == 0
        mock_subprocess.assert_not_called()
