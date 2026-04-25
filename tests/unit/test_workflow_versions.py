"""Unit tests for scripts/workflow_versions.py."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import workflow_versions as _wv_mod
from _colors import Colors
from workflow_versions import (
    _USES_RE,
    SCRIPT_VERSION,
    _build_parser,
    _cached_gh_api,
    _normalize_version,
    _repo_slug,
    _shorten_description,
    _unique_by_slug,
    _versions_equal,
    scan_workflows,
    update_comments,
    upgrade_action,
    upgrade_all_actions,
)


@pytest.fixture(autouse=True)
def _reset_rate_limit_state() -> None:
    """Reset the module-level rate-limit flag between tests."""
    _wv_mod._rate_limited = False
    _wv_mod._rate_limit["remaining"] = None


# ---------------------------------------------------------------------------
# SCRIPT_VERSION
# ---------------------------------------------------------------------------


class TestScriptVersion:
    """Validate version constant is well-formed."""

    def test_version_is_string(self) -> None:
        assert isinstance(SCRIPT_VERSION, str)

    def test_version_format(self) -> None:
        parts = SCRIPT_VERSION.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


# ---------------------------------------------------------------------------
# _USES_RE
# ---------------------------------------------------------------------------


class TestUsesRegex:
    """Tests for the ``uses:`` line regex."""

    def test_simple_action(self) -> None:
        sha = "a" * 40
        line = f"      - uses: actions/checkout@{sha} # v4.2.0"
        m = _USES_RE.match(line)
        assert m is not None
        assert m.group("action") == "actions/checkout"
        assert m.group("ref") == sha
        assert "v4.2.0" in m.group("trail")

    def test_sub_path_action(self) -> None:
        sha = "a" * 40
        line = f"      uses: github/codeql-action/init@{sha}"
        m = _USES_RE.match(line)
        assert m is not None
        assert m.group("action") == "github/codeql-action/init"

    def test_no_comment(self) -> None:
        sha = "a" * 40
        line = f"      uses: actions/upload-artifact@{sha}"
        m = _USES_RE.match(line)
        assert m is not None
        assert m.group("trail").strip() == ""

    def test_description_with_version_in_parens(self) -> None:
        sha = "a" * 40
        line = f"      - uses: actions/checkout@{sha} # Checkout code (v4.2.0)"
        m = _USES_RE.match(line)
        assert m is not None
        assert "v4.2.0" in m.group("trail")

    def test_non_sha_ref_does_not_match(self) -> None:
        line = "      uses: actions/checkout@v4"
        m = _USES_RE.match(line)
        assert m is None

    def test_short_sha_does_not_match(self) -> None:
        line = "      uses: actions/checkout@abc123"
        m = _USES_RE.match(line)
        assert m is None


# ---------------------------------------------------------------------------
# _repo_slug
# ---------------------------------------------------------------------------


class TestRepoSlug:
    """Tests for stripping sub-path from action references."""

    def test_simple_action(self) -> None:
        assert _repo_slug("actions/checkout") == "actions/checkout"

    def test_sub_path_action(self) -> None:
        assert _repo_slug("github/codeql-action/init") == "github/codeql-action"

    def test_deep_sub_path(self) -> None:
        assert _repo_slug("owner/repo/a/b/c") == "owner/repo"


# ---------------------------------------------------------------------------
# _shorten_description
# ---------------------------------------------------------------------------


class TestShortenDescription:
    """Tests for action description shortening."""

    def test_strips_this_action_prefix(self) -> None:
        result = _shorten_description("This action checks out your repository")
        assert not result.startswith("This action")
        assert "checks out" in result.lower()

    def test_strips_github_action_prefix(self) -> None:
        result = _shorten_description("A GitHub Action for running tests")
        assert not result.startswith("A GitHub Action")
        assert "running tests" in result.lower()

    def test_takes_first_sentence(self) -> None:
        result = _shorten_description("Uploads artifacts. This is extra info.")
        assert "extra" not in result

    def test_capitalises_first_letter(self) -> None:
        result = _shorten_description("checks out code")
        assert result[0].isupper()

    def test_truncates_long_descriptions(self) -> None:
        long_desc = "A" * 60
        result = _shorten_description(long_desc)
        assert len(result) <= 51  # 47 + "…" = 48, or word break

    def test_strips_trailing_punctuation(self) -> None:
        result = _shorten_description("Upload artifacts.")
        assert not result.endswith(".")

    def test_empty_string(self) -> None:
        assert _shorten_description("") == ""

    def test_short_description_unchanged(self) -> None:
        result = _shorten_description("Run tests")
        assert result == "Run tests"


# ---------------------------------------------------------------------------
# _unique_by_slug
# ---------------------------------------------------------------------------


class TestUniqueBySlug:
    """Tests for the slug-based deduplication helper."""

    def test_deduplicates(self) -> None:
        rows = [
            {"action": "actions/checkout", "file": "a.yml"},
            {"action": "actions/checkout", "file": "b.yml"},
            {"action": "actions/upload-artifact", "file": "a.yml"},
        ]
        result = _unique_by_slug(rows)
        assert len(result) == 2
        actions = [r["action"] for r in result]
        assert "actions/checkout" in actions
        assert "actions/upload-artifact" in actions

    def test_keeps_first_occurrence(self) -> None:
        rows = [
            {"action": "actions/checkout", "file": "first.yml"},
            {"action": "actions/checkout", "file": "second.yml"},
        ]
        result = _unique_by_slug(rows)
        assert result[0]["file"] == "first.yml"

    def test_sub_path_deduplicates_by_repo(self) -> None:
        rows = [
            {"action": "github/codeql-action/init", "file": "a.yml"},
            {
                "action": "github/codeql-action/analyze",
                "file": "a.yml",
            },
        ]
        result = _unique_by_slug(rows)
        assert len(result) == 1

    def test_empty_list(self) -> None:
        assert _unique_by_slug([]) == []


# ---------------------------------------------------------------------------
# _normalize_version / _versions_equal
# ---------------------------------------------------------------------------


class TestNormalizeVersion:
    """Tests for semver normalization."""

    def test_full_semver(self) -> None:
        assert _normalize_version("v4.2.1") == (4, 2, 1)

    def test_two_segments(self) -> None:
        assert _normalize_version("v4.2") == (4, 2, 0)

    def test_one_segment(self) -> None:
        assert _normalize_version("v4") == (4, 0, 0)

    def test_no_v_prefix(self) -> None:
        assert _normalize_version("4.2.1") == (4, 2, 1)

    def test_four_segments(self) -> None:
        assert _normalize_version("v1.2.3.4") == (1, 2, 3, 4)

    def test_pre_release_suffix_stripped(self) -> None:
        # "v1.2.3-beta" — partition("-") strips the suffix so int("3") succeeds
        assert _normalize_version("v1.2.3-beta") == (1, 2, 3)

    def test_empty_string(self) -> None:
        assert _normalize_version("") == (0, 0, 0)


class TestVersionsEqual:
    """Tests for version equality with normalization."""

    def test_same_versions(self) -> None:
        assert _versions_equal("v4.2.1", "v4.2.1") is True

    def test_v_prefix_mismatch(self) -> None:
        assert _versions_equal("v4.2.1", "4.2.1") is True

    def test_padded_segments(self) -> None:
        assert _versions_equal("v4", "v4.0.0") is True

    def test_two_vs_three_segments(self) -> None:
        assert _versions_equal("v4.2", "v4.2.0") is True

    def test_different_versions(self) -> None:
        assert _versions_equal("v4.1.0", "v4.2.0") is False

    def test_major_vs_padded(self) -> None:
        assert _versions_equal("v4", "v5.0.0") is False


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------


class TestColors:
    """Tests for the color support class."""

    def test_enabled_wraps_text(self) -> None:
        c = Colors(enabled=True)
        result = c.red("error")
        assert "\033[31m" in result
        assert "\033[0m" in result
        assert "error" in result

    def test_disabled_returns_plain_text(self) -> None:
        c = Colors(enabled=False)
        assert c.red("error") == "error"
        assert c.green("ok") == "ok"
        assert c.bold("title") == "title"

    def test_all_color_methods(self) -> None:
        c = Colors(enabled=True)
        for method in ("bold", "dim", "red", "green", "yellow", "blue", "cyan"):
            result = getattr(c, method)("test")
            assert "test" in result
            assert "\033[" in result

    def test_auto_detect_respects_no_color_env(self) -> None:
        with patch.dict("os.environ", {"NO_COLOR": "1"}, clear=False):
            c = Colors()
            assert c.enabled is False

    def test_auto_detect_respects_force_color_env(self) -> None:
        with patch.dict(
            "os.environ",
            {"FORCE_COLOR": "1"},
            clear=False,
        ):
            # Remove NO_COLOR if present
            env = dict(os.environ)
            env.pop("NO_COLOR", None)
            env["FORCE_COLOR"] = "1"
            with patch.dict("os.environ", env, clear=True):
                c = Colors()
                assert c.enabled is True


# ---------------------------------------------------------------------------
# _build_parser
# ---------------------------------------------------------------------------


class TestBuildParser:
    """Tests for CLI argument parser."""

    def test_version_flag(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_show_defaults(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["show"])
        assert args.command == "show"
        assert args.offline is False
        assert args.json_output is False

    def test_show_offline(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["show", "--offline"])
        assert args.offline is True

    def test_show_json(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["show", "--json"])
        assert args.json_output is True

    def test_update_comments_command(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["update-comments"])
        assert args.command == "update-comments"

    def test_upgrade_with_action_and_version(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["upgrade", "actions/checkout", "v6.1.0"])
        assert args.command == "upgrade"
        assert args.action == "actions/checkout"
        assert args.version == "v6.1.0"

    def test_upgrade_without_args(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["upgrade"])
        assert args.action is None
        assert args.version is None

    def test_no_command_defaults_to_none(self) -> None:
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.command is None

    def test_color_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--color", "show"])
        assert args.color is True

    def test_no_color_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--no-color", "show"])
        assert args.color is False

    def test_color_default_is_none(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["show"])
        assert args.color is None

    def test_upgrade_dry_run_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["upgrade", "--dry-run"])
        assert args.dry_run is True

    def test_upgrade_dry_run_default(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["upgrade"])
        assert args.dry_run is False

    def test_quiet_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--quiet", "show"])
        assert args.quiet is True

    def test_quiet_short_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["-q", "show"])
        assert args.quiet is True

    def test_quiet_default_is_false(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["show"])
        assert args.quiet is False

    def test_filter_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["show", "--filter", "stale"])
        assert args.filter_mode == "stale"

    def test_filter_default_is_all(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["show"])
        assert args.filter_mode == "all"

    def test_filter_choices(self) -> None:
        parser = _build_parser()
        for choice in ("all", "stale", "upgradable", "no-desc"):
            args = parser.parse_args(["show", "--filter", choice])
            assert args.filter_mode == choice

    def test_filter_invalid_choice_errors(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["show", "--filter", "invalid"])


# ---------------------------------------------------------------------------
# scan_workflows (offline / mocked)
# ---------------------------------------------------------------------------


class TestScanWorkflows:
    """Tests for workflow scanning with mocked filesystem."""

    def test_no_workflows_dir(self, tmp_path: Path) -> None:
        with patch("workflow_versions.WORKFLOWS_DIR", tmp_path / "nope"):
            assert scan_workflows(resolve_tags=False) == []

    def test_scans_uses_lines(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        sha = "a" * 40
        content = (
            "jobs:\n"
            "  build:\n"
            "    steps:\n"
            f"      - uses: actions/checkout@{sha} # v4.2.0\n"
        )
        (wf_dir / "test.yml").write_text(content)

        with patch("workflow_versions.WORKFLOWS_DIR", wf_dir):
            rows = scan_workflows(resolve_tags=False, check_latest=False)

        assert len(rows) == 1
        assert rows[0]["action"] == "actions/checkout"
        assert rows[0]["sha"] == sha
        assert rows[0]["comment_tag"] == "v4.2.0"

    def test_detects_description_with_parens(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        sha = "b" * 40
        content = (
            "jobs:\n"
            "  build:\n"
            "    steps:\n"
            f"      - uses: actions/checkout@{sha}"
            " # Checkout code (v4.2.0)\n"
        )
        (wf_dir / "ci.yml").write_text(content)

        with patch("workflow_versions.WORKFLOWS_DIR", wf_dir):
            rows = scan_workflows(resolve_tags=False, check_latest=False)

        assert rows[0]["comment_tag"] == "v4.2.0"
        assert rows[0]["has_description"] == "yes"

    def test_detects_missing_comment(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        sha = "c" * 40
        content = f"      uses: actions/checkout@{sha}\n"
        (wf_dir / "ci.yml").write_text(content)

        with patch("workflow_versions.WORKFLOWS_DIR", wf_dir):
            rows = scan_workflows(resolve_tags=False, check_latest=False)

        assert rows[0]["comment_tag"] is None

    def test_multiple_actions_across_files(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        sha1 = "a" * 40
        sha2 = "b" * 40
        (wf_dir / "a.yml").write_text(f"      uses: actions/checkout@{sha1} # v4\n")
        (wf_dir / "b.yml").write_text(
            f"      uses: actions/upload-artifact@{sha2} # v3\n"
        )

        with patch("workflow_versions.WORKFLOWS_DIR", wf_dir):
            rows = scan_workflows(resolve_tags=False, check_latest=False)

        assert len(rows) == 2
        actions = {r["action"] for r in rows}
        assert "actions/checkout" in actions
        assert "actions/upload-artifact" in actions


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


class TestMain:
    """Integration-style tests for the main entry point."""

    def test_returns_1_when_no_workflows_dir(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        from workflow_versions import main

        with (
            patch(
                "workflow_versions.WORKFLOWS_DIR",
                tmp_path / "missing",
            ),
            patch("sys.argv", ["workflow_versions", "show"]),
            caplog.at_level("ERROR"),
        ):
            ret = main()
        assert ret == 1
        assert "No workflows directory" in caplog.text

    def test_show_json_empty(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from workflow_versions import main

        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch(
                "sys.argv",
                ["workflow_versions", "show", "--json"],
            ),
        ):
            ret = main()
        assert ret == 0
        out = capsys.readouterr().out
        output = json.loads(out)
        assert output == []

    def test_show_json_with_actions(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from workflow_versions import main

        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        sha = "d" * 40
        (wf_dir / "ci.yml").write_text(f"      uses: actions/checkout@{sha} # v4.2.0\n")

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch(
                "sys.argv",
                [
                    "workflow_versions",
                    "show",
                    "--json",
                    "--offline",
                ],
            ),
        ):
            ret = main()
        assert ret == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["action"] == "actions/checkout"
        assert data[0]["comment_tag"] == "v4.2.0"

    def test_show_returns_0(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from workflow_versions import main

        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        sha = "e" * 40
        (wf_dir / "ci.yml").write_text(f"      uses: actions/checkout@{sha} # v4.2.0\n")

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch(
                "sys.argv",
                ["workflow_versions", "show", "--offline"],
            ),
        ):
            ret = main()
        assert ret == 0

    def test_quiet_returns_0_when_no_issues(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from workflow_versions import main

        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        sha = "f" * 40
        (wf_dir / "ci.yml").write_text(f"      uses: actions/checkout@{sha} # v4.2.0\n")

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch(
                "sys.argv",
                ["workflow_versions", "--quiet", "show", "--offline"],
            ),
        ):
            ret = main()
        assert ret == 0
        # Quiet mode suppresses table output on stdout
        out = capsys.readouterr().out
        assert out == ""

    def test_quiet_suppresses_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from workflow_versions import main

        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        sha = "f" * 40
        (wf_dir / "ci.yml").write_text(f"      uses: actions/checkout@{sha} # v4.2.0\n")

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch(
                "sys.argv",
                ["workflow_versions", "-q", "show", "--json", "--offline"],
            ),
        ):
            ret = main()
        assert ret == 0
        out = capsys.readouterr().out
        assert out == ""

    def test_filter_stale_returns_only_stale_rows(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from workflow_versions import main

        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()

        # Mock scan_workflows to return rows with known stale values
        mock_rows = [
            {
                "file": "ci.yml",
                "line": "1",
                "action": "actions/checkout",
                "sha": "a" * 40,
                "comment_tag": "v3.0.0",
                "resolved_tag": "v4.2.0",
                "latest_tag": None,
                "stale": "yes",
                "upgradable": "",
                "has_description": "",
            },
            {
                "file": "ci.yml",
                "line": "2",
                "action": "actions/upload-artifact",
                "sha": "b" * 40,
                "comment_tag": "v4.0.0",
                "resolved_tag": "v4.0.0",
                "latest_tag": None,
                "stale": "",
                "upgradable": "",
                "has_description": "yes",
            },
        ]

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch("workflow_versions.scan_workflows", return_value=mock_rows),
            patch(
                "sys.argv",
                [
                    "workflow_versions",
                    "show",
                    "--json",
                    "--filter",
                    "stale",
                ],
            ),
        ):
            ret = main()

        assert ret == 0
        data = json.loads(capsys.readouterr().out)
        assert len(data) == 1
        assert data[0]["action"] == "actions/checkout"
        assert data[0]["stale"] == "yes"

    def test_header_goes_to_stdout(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from workflow_versions import main

        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch(
                "sys.argv",
                ["workflow_versions", "show", "--offline"],
            ),
        ):
            main()
        assert "Workflow Action Versions" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# update_comments (write path)
# ---------------------------------------------------------------------------


class TestUpdateComments:
    """Tests for the comment-update write path."""

    def _make_workflow(
        self, wf_dir: Path, content: str, *, name: str = "ci.yml"
    ) -> Path:
        wf_dir.mkdir(exist_ok=True)
        f = wf_dir / name
        f.write_text(content, encoding="utf-8")
        return f

    def test_updates_stale_comment(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        sha = "a" * 40
        content = f"      - uses: actions/checkout@{sha} # v3.0.0\n"
        wf = self._make_workflow(wf_dir, content)

        rows = [
            {
                "file": "ci.yml",
                "line": "1",
                "action": "actions/checkout",
                "sha": sha,
                "comment_tag": "v3.0.0",
                "resolved_tag": "v4.2.0",
                "latest_tag": None,
                "stale": "yes",
                "upgradable": "",
                "has_description": "",
            }
        ]

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch("workflow_versions._action_description", return_value=None),
        ):
            count = update_comments(rows)

        assert count == 1
        updated = wf.read_text(encoding="utf-8")
        assert "v4.2.0" in updated
        assert "v3.0.0" not in updated

    def test_adds_missing_comment(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        sha = "b" * 40
        content = f"      - uses: actions/checkout@{sha}\n"
        wf = self._make_workflow(wf_dir, content)

        rows = [
            {
                "file": "ci.yml",
                "line": "1",
                "action": "actions/checkout",
                "sha": sha,
                "comment_tag": None,
                "resolved_tag": "v4.2.0",
                "latest_tag": None,
                "stale": "missing",
                "upgradable": "",
                "has_description": "",
            }
        ]

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch("workflow_versions._action_description", return_value=None),
        ):
            count = update_comments(rows)

        assert count == 1
        updated = wf.read_text(encoding="utf-8")
        assert "# v4.2.0" in updated

    def test_adds_description_to_no_desc(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        sha = "c" * 40
        content = f"      - uses: actions/checkout@{sha} # v4.2.0\n"
        wf = self._make_workflow(wf_dir, content)

        rows = [
            {
                "file": "ci.yml",
                "line": "1",
                "action": "actions/checkout",
                "sha": sha,
                "comment_tag": "v4.2.0",
                "resolved_tag": "v4.2.0",
                "latest_tag": None,
                "stale": "no-desc",
                "upgradable": "",
                "has_description": "",
            }
        ]

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch(
                "workflow_versions._action_description",
                return_value="Checkout code",
            ),
        ):
            count = update_comments(rows)

        assert count == 1
        updated = wf.read_text(encoding="utf-8")
        assert "Checkout code" in updated
        assert "(v4.2.0)" in updated

    def test_returns_zero_when_nothing_to_update(self, tmp_path: Path) -> None:
        rows = [
            {
                "file": "ci.yml",
                "line": "1",
                "action": "actions/checkout",
                "sha": "a" * 40,
                "comment_tag": "v4.2.0",
                "resolved_tag": "v4.2.0",
                "latest_tag": None,
                "stale": "",
                "upgradable": "",
                "has_description": "yes",
            }
        ]
        with patch("workflow_versions.WORKFLOWS_DIR", tmp_path):
            count = update_comments(rows)
        assert count == 0

    def test_skips_deleted_file(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        # Don't create the file — simulates deletion after scan

        rows = [
            {
                "file": "gone.yml",
                "line": "1",
                "action": "actions/checkout",
                "sha": "a" * 40,
                "comment_tag": "v3.0.0",
                "resolved_tag": "v4.0.0",
                "latest_tag": None,
                "stale": "yes",
                "upgradable": "",
                "has_description": "",
            }
        ]

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch("workflow_versions._action_description", return_value=None),
            caplog.at_level("WARNING"),
        ):
            count = update_comments(rows)

        assert count == 0
        assert "Cannot read" in caplog.text


# ---------------------------------------------------------------------------
# upgrade_action (write path)
# ---------------------------------------------------------------------------


class TestUpgradeAction:
    """Tests for the single-action upgrade write path."""

    def test_upgrades_sha_and_comment(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        old_sha = "a" * 40
        new_sha = "b" * 40
        content = f"      - uses: actions/checkout@{old_sha} # v3.0.0\n"
        wf = wf_dir / "ci.yml"
        wf.write_text(content, encoding="utf-8")

        rows = [
            {
                "file": "ci.yml",
                "line": "1",
                "action": "actions/checkout",
                "sha": old_sha,
                "comment_tag": "v3.0.0",
                "resolved_tag": "v3.0.0",
                "latest_tag": "v4.2.0",
                "stale": "",
                "upgradable": "yes",
                "has_description": "",
            }
        ]

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch(
                "workflow_versions._resolve_sha_for_tag",
                return_value=new_sha,
            ),
        ):
            count = upgrade_action("actions/checkout", "v4.2.0", rows)

        assert count == 1
        updated = wf.read_text(encoding="utf-8")
        assert new_sha in updated
        assert old_sha not in updated
        assert "v4.2.0" in updated

    def test_returns_zero_when_tag_unresolvable(self, tmp_path: Path) -> None:
        rows = [
            {
                "file": "ci.yml",
                "line": "1",
                "action": "actions/checkout",
                "sha": "a" * 40,
                "comment_tag": "v3.0.0",
                "resolved_tag": "v3.0.0",
                "latest_tag": "v4.2.0",
                "stale": "",
                "upgradable": "yes",
                "has_description": "",
            }
        ]

        with (
            patch("workflow_versions.WORKFLOWS_DIR", tmp_path),
            patch("workflow_versions._resolve_sha_for_tag", return_value=None),
        ):
            count = upgrade_action("actions/checkout", "v99.0.0", rows)

        assert count == 0

    def test_skips_deleted_file(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        # Don't create the file

        rows = [
            {
                "file": "gone.yml",
                "line": "1",
                "action": "actions/checkout",
                "sha": "a" * 40,
                "comment_tag": "v3.0.0",
                "resolved_tag": "v3.0.0",
                "latest_tag": "v4.2.0",
                "stale": "",
                "upgradable": "yes",
                "has_description": "",
            }
        ]

        new_sha = "b" * 40
        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch(
                "workflow_versions._resolve_sha_for_tag",
                return_value=new_sha,
            ),
            caplog.at_level("WARNING"),
        ):
            count = upgrade_action("actions/checkout", "v4.2.0", rows)

        assert count == 0
        assert "Cannot read" in caplog.text


# ---------------------------------------------------------------------------
# upgrade_all_actions
# ---------------------------------------------------------------------------


class TestUpgradeAllActions:
    """Tests for the upgrade-all write path."""

    def test_upgrades_only_upgradable_rows(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        old_sha = "a" * 40
        new_sha = "b" * 40
        content = f"      - uses: actions/checkout@{old_sha} # v3.0.0\n"
        wf = wf_dir / "ci.yml"
        wf.write_text(content, encoding="utf-8")

        rows = [
            {
                "file": "ci.yml",
                "line": "1",
                "action": "actions/checkout",
                "sha": old_sha,
                "comment_tag": "v3.0.0",
                "resolved_tag": "v3.0.0",
                "latest_tag": "v4.2.0",
                "stale": "",
                "upgradable": "yes",
                "has_description": "",
            }
        ]

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch(
                "workflow_versions._resolve_sha_for_tag",
                return_value=new_sha,
            ),
        ):
            count = upgrade_all_actions(rows)

        assert count == 1
        updated = wf.read_text(encoding="utf-8")
        assert new_sha in updated

    def test_returns_zero_when_nothing_upgradable(self) -> None:
        rows = [
            {
                "file": "ci.yml",
                "line": "1",
                "action": "actions/checkout",
                "sha": "a" * 40,
                "comment_tag": "v4.2.0",
                "resolved_tag": "v4.2.0",
                "latest_tag": "v4.2.0",
                "stale": "",
                "upgradable": "",
                "has_description": "yes",
            }
        ]
        count = upgrade_all_actions(rows)
        assert count == 0


# ---------------------------------------------------------------------------
# _cached_gh_api
# ---------------------------------------------------------------------------


class TestCachedGhApi:
    """Tests for the disk-caching wrapper."""

    def test_caches_successful_response(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / "cache"
        with (
            patch("workflow_versions._CACHE_DIR", cache_dir),
            patch("workflow_versions._CACHE_TTL", 3600),
            patch(
                "workflow_versions._gh_api",
                return_value={"tag_name": "v1.0.0"},
            ) as mock_api,
        ):
            # First call — should hit the API
            result1 = _cached_gh_api("https://api.github.com/test")
            assert result1 == {"tag_name": "v1.0.0"}
            assert mock_api.call_count == 1

            # Second call — should come from cache
            result2 = _cached_gh_api("https://api.github.com/test")
            assert result2 == {"tag_name": "v1.0.0"}
            assert mock_api.call_count == 1  # no additional API call

    def test_does_not_cache_none(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / "cache"
        with (
            patch("workflow_versions._CACHE_DIR", cache_dir),
            patch("workflow_versions._CACHE_TTL", 3600),
            patch(
                "workflow_versions._gh_api",
                return_value=None,
            ) as mock_api,
        ):
            result = _cached_gh_api("https://api.github.com/test")
            assert result is None
            assert mock_api.call_count == 1

            # Second call should still hit API (no cache for None)
            _cached_gh_api("https://api.github.com/test")
            assert mock_api.call_count == 2

    def test_bypasses_cache_when_ttl_zero(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / "cache"
        with (
            patch("workflow_versions._CACHE_DIR", cache_dir),
            patch("workflow_versions._CACHE_TTL", 0),
            patch(
                "workflow_versions._gh_api",
                return_value={"data": 1},
            ) as mock_api,
        ):
            _cached_gh_api("https://api.github.com/test")
            _cached_gh_api("https://api.github.com/test")
            assert mock_api.call_count == 2


# ---------------------------------------------------------------------------
# scan_workflows error handling (B6/B7)
# ---------------------------------------------------------------------------


class TestScanWorkflowsErrorHandling:
    """Tests for graceful handling of file errors during scanning."""

    def test_skips_non_utf8_file(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        # Write invalid UTF-8 bytes
        (wf_dir / "bad.yml").write_bytes(b"\xff\xfe invalid utf-8")

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            caplog.at_level("WARNING"),
        ):
            rows = scan_workflows(resolve_tags=False)

        assert rows == []
        assert "Non-UTF-8" in caplog.text

    def test_skips_deleted_file_during_scan(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        sha = "a" * 40
        f = wf_dir / "ci.yml"
        f.write_text(f"      uses: actions/checkout@{sha} # v4\n")

        original_glob = Path.glob

        def patched_glob(self_path: Path, pattern: str) -> list[Path]:
            results = list(original_glob(self_path, pattern))
            # Return a path that will be deleted before read
            ghost = wf_dir / "ghost.yml"
            results.append(ghost)
            return results

        with (
            patch("workflow_versions.WORKFLOWS_DIR", wf_dir),
            patch.object(Path, "glob", patched_glob),
            caplog.at_level("WARNING"),
        ):
            rows = scan_workflows(resolve_tags=False)

        # Should have scanned ci.yml successfully and skipped ghost.yml
        assert len(rows) == 1
        assert rows[0]["action"] == "actions/checkout"
        assert "disappeared" in caplog.text


# ---------------------------------------------------------------------------
# Comment regex (B1 fix)
# ---------------------------------------------------------------------------


class TestCommentRegexB1Fix:
    """Verify the B1 fix: comment regex doesn't capture description words."""

    def test_descriptive_comment_not_captured_as_tag(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        sha = "a" * 40
        # "Checkout" starts with a capital letter, not a digit — should not
        # be captured as a version tag
        content = f"      - uses: actions/checkout@{sha} # Checkout code\n"
        (wf_dir / "ci.yml").write_text(content)

        with patch("workflow_versions.WORKFLOWS_DIR", wf_dir):
            rows = scan_workflows(resolve_tags=False)

        assert rows[0]["comment_tag"] is None

    def test_version_tag_still_captured(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        sha = "a" * 40
        content = f"      - uses: actions/checkout@{sha} # v4.2.0\n"
        (wf_dir / "ci.yml").write_text(content)

        with patch("workflow_versions.WORKFLOWS_DIR", wf_dir):
            rows = scan_workflows(resolve_tags=False)

        assert rows[0]["comment_tag"] == "v4.2.0"


# ---------------------------------------------------------------------------
# Rate-limit early bail-out
# ---------------------------------------------------------------------------


class TestRateLimitBailOut:
    """Tests for the _rate_limited flag and early bail-out behavior."""

    def test_gh_api_returns_none_when_rate_limited(self) -> None:
        """Once _rate_limited is set, _gh_api should return None immediately."""
        _wv_mod._rate_limited = True
        result = _wv_mod._gh_api("https://api.github.com/repos/test/tags")
        assert result is None

    def test_gh_api_sets_flag_on_403(self) -> None:
        """A 403 HTTP error with X-RateLimit-Remaining: 0 should set _rate_limited."""
        import email.message
        import urllib.error

        hdrs = email.message.Message()
        hdrs["X-RateLimit-Remaining"] = "0"
        exc = urllib.error.HTTPError(
            "https://api.github.com/test",
            403,
            "rate limit exceeded",
            hdrs,
            None,
        )
        with patch("urllib.request.urlopen", side_effect=exc):
            result = _wv_mod._gh_api("https://api.github.com/test")
        assert result is None
        assert _wv_mod._rate_limited is True

    def test_rate_limit_warning_logged_only_once(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The rate-limit warning should appear exactly once, not per call."""
        import email.message
        import urllib.error

        hdrs = email.message.Message()
        hdrs["X-RateLimit-Remaining"] = "0"
        exc = urllib.error.HTTPError(
            "https://api.github.com/test",
            403,
            "rate limit exceeded",
            hdrs,
            None,
        )
        with patch("urllib.request.urlopen", side_effect=exc):
            _wv_mod._gh_api("https://api.github.com/test1")
            _wv_mod._gh_api("https://api.github.com/test2")
            _wv_mod._gh_api("https://api.github.com/test3")

        captured = capsys.readouterr()
        assert captured.err.count("rate limit") == 1

    def test_cached_api_still_returns_cache_when_rate_limited(
        self, tmp_path: Path
    ) -> None:
        """Cached responses should still be returned even after rate limiting."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Pre-populate the cache
        import hashlib

        url = "https://api.github.com/repos/test/cached"
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        cache_file = cache_dir / f"{url_hash}.json"
        cache_file.write_text('{"cached": true}', encoding="utf-8")

        _wv_mod._rate_limited = True
        with (
            patch("workflow_versions._CACHE_DIR", cache_dir),
            patch("workflow_versions._CACHE_TTL", 3600),
        ):
            result = _cached_gh_api(url)

        assert result == {"cached": True}
