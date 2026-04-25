"""Unit tests for scripts/apply_labels.py helper functions."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from apply_labels import (
    SCRIPT_VERSION,
    _get_existing_label,
    default_repo,
    gh_api,
    gh_exists,
    run,
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


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


class TestRun:
    """Tests for the run() subprocess wrapper."""

    @patch("apply_labels.subprocess.run")
    def test_run_returns_completed_process(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            ["echo"], 0, stdout="ok", stderr=""
        )
        result = run(["echo", "hello"])
        assert result.returncode == 0
        assert result.stdout == "ok"
        mock_run.assert_called_once_with(
            ["echo", "hello"], text=True, capture_output=True
        )

    @patch("apply_labels.subprocess.run")
    def test_run_passes_through_nonzero_exit(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            ["false"], 1, stdout="", stderr="error"
        )
        result = run(["false"])
        assert result.returncode == 1
        assert result.stderr == "error"


# ---------------------------------------------------------------------------
# gh_exists
# ---------------------------------------------------------------------------


class TestGhExists:
    """Tests for gh_exists()."""

    @patch("apply_labels.subprocess.run")
    def test_returns_true_when_gh_installed(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(["gh"], 0)
        assert gh_exists() is True

    @patch("apply_labels.subprocess.run", side_effect=FileNotFoundError)
    def test_returns_false_when_gh_missing(self, mock_run) -> None:
        assert gh_exists() is False

    @patch(
        "apply_labels.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "gh"),
    )
    def test_returns_false_on_called_process_error(self, mock_run) -> None:
        assert gh_exists() is False


# ---------------------------------------------------------------------------
# default_repo
# ---------------------------------------------------------------------------


class TestDefaultRepo:
    """Tests for default_repo()."""

    @patch("apply_labels.run")
    def test_returns_repo_slug_on_success(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            [], 0, stdout="owner/repo\n", stderr=""
        )
        assert default_repo() == "owner/repo"

    @patch("apply_labels.run")
    def test_returns_none_on_failure(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            [], 1, stdout="", stderr="error"
        )
        assert default_repo() is None

    @patch("apply_labels.run")
    def test_returns_none_on_empty_stdout(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        assert default_repo() is None


# ---------------------------------------------------------------------------
# gh_api
# ---------------------------------------------------------------------------


class TestGhApi:
    """Tests for gh_api()."""

    @patch("apply_labels.run")
    def test_builds_correct_command(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            [], 0, stdout="{}", stderr=""
        )
        gh_api("POST", "repos/owner/repo/labels", {"name": "bug", "color": "ff0000"})
        args = mock_run.call_args[0][0]
        assert args[:4] == ["gh", "api", "-X", "POST"]
        assert "repos/owner/repo/labels" in args
        assert "-f" in args


# ---------------------------------------------------------------------------
# _get_existing_label
# ---------------------------------------------------------------------------


class TestGetExistingLabel:
    """Tests for _get_existing_label()."""

    @patch("apply_labels.run")
    def test_returns_label_dict_on_success(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            [],
            0,
            stdout='{"name": "bug", "color": "ff0000", "description": ""}',
            stderr="",
        )
        result = _get_existing_label("owner/repo", "bug")
        assert result is not None
        assert result["name"] == "bug"

    @patch("apply_labels.run")
    def test_returns_none_on_failure(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            [], 1, stdout="", stderr="not found"
        )
        assert _get_existing_label("owner/repo", "bug") is None

    @patch("apply_labels.run")
    def test_returns_none_on_invalid_json(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            [], 0, stdout="not json", stderr=""
        )
        assert _get_existing_label("owner/repo", "bug") is None
