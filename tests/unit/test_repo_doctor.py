"""Unit tests for scripts/repo_doctor.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from repo_doctor import (
    SCRIPT_VERSION,
    DoctorConfig,
    OnlyIf,
    Rule,
    Warning,
    _build_parser,
    _colorize,
    _evaluate_rules,
    _exists_kind,
    _file_contains_regex,
    _format_warning,
    _load_doctor_config,
    _load_profile_rules,
    _load_rules,
    _matches_deletion,
    _parse_rule_entries,
    _run_git,
    _supports_color,
    _toml_has_path,
)

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
# _supports_color
# ---------------------------------------------------------------------------


class TestSupportsColor:
    """Tests for ANSI color detection."""

    def test_no_color_env_disables(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = True
        with patch.dict("os.environ", {"NO_COLOR": "1"}, clear=False):
            assert _supports_color(stream) is False

    def test_force_color_env_enables(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = False
        env = {"FORCE_COLOR": "1"}
        with patch.dict("os.environ", env, clear=True):
            assert _supports_color(stream) is True

    def test_tty_stream_returns_true(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = True
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("_colors._enable_windows_ansi", return_value=True),
        ):
            assert _supports_color(stream) is True

    def test_non_tty_stream_returns_false(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = False
        with patch.dict("os.environ", {}, clear=True):
            assert _supports_color(stream) is False


# ---------------------------------------------------------------------------
# _colorize
# ---------------------------------------------------------------------------


class TestColorize:
    """Tests for ANSI color wrapping."""

    def test_color_enabled(self) -> None:
        result = _colorize("hello", "33", use_color=True)
        assert result == "\033[33mhello\033[0m"

    def test_color_disabled(self) -> None:
        result = _colorize("hello", "33", use_color=False)
        assert result == "hello"


# ---------------------------------------------------------------------------
# _run_git
# ---------------------------------------------------------------------------


class TestRunGit:
    """Tests for the git command wrapper."""

    def test_returns_error_when_git_not_found(self) -> None:
        with patch("repo_doctor._GIT_CMD", None):
            code, _out, err = _run_git(Path(), ["status"])
        assert code == 1
        assert "not found" in err

    def test_returns_subprocess_result(self, tmp_path: Path) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123\n"
        mock_result.stderr = ""
        with (
            patch("repo_doctor._GIT_CMD", "/usr/bin/git"),
            patch("repo_doctor.subprocess.run", return_value=mock_result),
        ):
            code, out, _err = _run_git(tmp_path, ["rev-parse", "HEAD"])
        assert code == 0
        assert out == "abc123\n"

    def test_passes_timeout(self, tmp_path: Path) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        with (
            patch("repo_doctor._GIT_CMD", "/usr/bin/git"),
            patch(
                "repo_doctor.subprocess.run",
                return_value=mock_result,
            ) as mock_run,
        ):
            _run_git(tmp_path, ["status"])
        _, kwargs = mock_run.call_args
        assert kwargs.get("timeout") == 30


# ---------------------------------------------------------------------------
# _exists_kind
# ---------------------------------------------------------------------------


class TestExistsKind:
    """Tests for file/dir/any existence checks."""

    def test_file_exists(self, tmp_path: Path) -> None:
        (tmp_path / "hello.txt").write_text("hi")
        assert _exists_kind(tmp_path, "hello.txt", "file") is True

    def test_file_not_exists(self, tmp_path: Path) -> None:
        assert _exists_kind(tmp_path, "nope.txt", "file") is False

    def test_dir_exists(self, tmp_path: Path) -> None:
        (tmp_path / "subdir").mkdir()
        assert _exists_kind(tmp_path, "subdir", "dir") is True

    def test_dir_not_exists(self, tmp_path: Path) -> None:
        assert _exists_kind(tmp_path, "subdir", "dir") is False

    def test_any_matches_file(self, tmp_path: Path) -> None:
        (tmp_path / "thing").write_text("data")
        assert _exists_kind(tmp_path, "thing", "any") is True

    def test_any_matches_dir(self, tmp_path: Path) -> None:
        (tmp_path / "thing").mkdir()
        assert _exists_kind(tmp_path, "thing", "any") is True

    def test_any_not_exists(self, tmp_path: Path) -> None:
        assert _exists_kind(tmp_path, "thing", "any") is False


# ---------------------------------------------------------------------------
# _file_contains_regex
# ---------------------------------------------------------------------------


class TestFileContainsRegex:
    """Tests for regex matching in files."""

    def test_match_found(self, tmp_path: Path) -> None:
        (tmp_path / "f.txt").write_text("version = 1.2.3")
        assert _file_contains_regex(tmp_path, "f.txt", r"version\s*=") is True

    def test_no_match(self, tmp_path: Path) -> None:
        (tmp_path / "f.txt").write_text("nothing here")
        assert _file_contains_regex(tmp_path, "f.txt", r"version") is False

    def test_missing_file(self, tmp_path: Path) -> None:
        assert _file_contains_regex(tmp_path, "missing.txt", r"x") is False

    def test_match_in_subdirectory(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "a.txt").write_text("target_pattern")
        assert _file_contains_regex(tmp_path, "sub", r"target_pattern") is True


# ---------------------------------------------------------------------------
# _toml_has_path
# ---------------------------------------------------------------------------


class TestTomlHasPath:
    """Tests for TOML dotted-key lookup."""

    def test_key_exists(self, tmp_path: Path) -> None:
        (tmp_path / "cfg.toml").write_text('[project]\nname = "test"\n')
        ok, note = _toml_has_path(tmp_path, "cfg.toml", "project.name")
        assert ok is True
        assert note == ""

    def test_key_missing(self, tmp_path: Path) -> None:
        (tmp_path / "cfg.toml").write_text("[project]\n")
        ok, _note = _toml_has_path(tmp_path, "cfg.toml", "project.name")
        assert ok is False

    def test_file_missing(self, tmp_path: Path) -> None:
        ok, _note = _toml_has_path(tmp_path, "no.toml", "x.y")
        assert ok is False

    def test_invalid_toml(self, tmp_path: Path) -> None:
        (tmp_path / "bad.toml").write_text("not valid [[[toml")
        ok, note = _toml_has_path(tmp_path, "bad.toml", "x")
        assert ok is False
        assert "Could not parse TOML" in note


# ---------------------------------------------------------------------------
# _matches_deletion
# ---------------------------------------------------------------------------


class TestMatchesDeletion:
    """Tests for path-based deletion matching."""

    def test_file_exact_match(self) -> None:
        assert _matches_deletion("README.md", "file", "README.md") is True

    def test_file_no_match(self) -> None:
        assert _matches_deletion("README.md", "file", "LICENSE") is False

    def test_dir_prefix_match(self) -> None:
        assert _matches_deletion("docs/", "dir", "docs/index.md") is True

    def test_dir_no_match(self) -> None:
        assert _matches_deletion("docs/", "dir", "src/main.py") is False


# ---------------------------------------------------------------------------
# _parse_rule_entries
# ---------------------------------------------------------------------------


class TestParseRuleEntries:
    """Tests for TOML dict → Rule conversion."""

    def test_basic_rule(self) -> None:
        raw = [{"type": "exists", "path": "README.md"}]
        rules = _parse_rule_entries(raw)
        assert len(rules) == 1
        assert rules[0].type == "exists"
        assert rules[0].path == "README.md"

    def test_skips_empty_type(self) -> None:
        raw = [{"type": "", "path": "README.md"}]
        assert _parse_rule_entries(raw) == []

    def test_skips_empty_path(self) -> None:
        raw = [{"type": "exists", "path": ""}]
        assert _parse_rule_entries(raw) == []

    def test_only_if_parsed(self) -> None:
        raw = [
            {
                "type": "exists",
                "path": "src/app.py",
                "only_if": {"path": "pyproject.toml", "regex": "app"},
            }
        ]
        rules = _parse_rule_entries(raw)
        assert rules[0].only_if is not None
        assert rules[0].only_if.path == "pyproject.toml"

    def test_all_fields_populated(self) -> None:
        raw = [
            {
                "type": "regex_present",
                "path": "pyproject.toml",
                "level": "info",
                "category": "ci",
                "impact": "High",
                "hint": "Add it",
                "link": "docs/adr/001.md",
                "fix": "echo fix",
                "regex": r"name\s*=",
            }
        ]
        rules = _parse_rule_entries(raw)
        r = rules[0]
        assert r.level == "info"
        assert r.category == "ci"
        assert r.impact == "High"
        assert r.hint == "Add it"
        assert r.link == "docs/adr/001.md"
        assert r.fix == "echo fix"
        assert r.regex == r"name\s*="


# ---------------------------------------------------------------------------
# _load_doctor_config
# ---------------------------------------------------------------------------


class TestLoadDoctorConfig:
    """Tests for parsing the [doctor] section."""

    def test_empty_data(self) -> None:
        cfg = _load_doctor_config({})
        assert cfg.ignore_missing == frozenset()
        assert cfg.profiles == ()

    def test_with_ignore_and_profiles(self) -> None:
        data = {
            "doctor": {
                "ignore_missing": ["a.txt", "b.txt"],
                "profiles": ["python", "ci"],
            }
        }
        cfg = _load_doctor_config(data)
        assert cfg.ignore_missing == frozenset({"a.txt", "b.txt"})
        assert cfg.profiles == ("python", "ci")

    def test_invalid_doctor_section(self) -> None:
        cfg = _load_doctor_config({"doctor": "not a dict"})
        assert cfg == DoctorConfig()


# ---------------------------------------------------------------------------
# _load_rules
# ---------------------------------------------------------------------------


class TestLoadRules:
    """Tests for loading rules from .repo-doctor.toml."""

    def test_no_config_file(self, tmp_path: Path) -> None:
        rules, _cfg = _load_rules(tmp_path)
        assert rules == []

    def test_loads_rules_from_toml(self, tmp_path: Path) -> None:
        toml_content = '[[rule]]\ntype = "exists"\npath = "README.md"\n'
        (tmp_path / ".repo-doctor.toml").write_text(toml_content)
        rules, _cfg = _load_rules(tmp_path)
        assert len(rules) == 1
        assert rules[0].path == "README.md"


# ---------------------------------------------------------------------------
# _load_profile_rules
# ---------------------------------------------------------------------------


class TestLoadProfileRules:
    """Tests for loading profile rules from repo_doctor.d/."""

    def test_no_profile_dir(self, tmp_path: Path) -> None:
        assert _load_profile_rules(tmp_path, ["python"]) == []

    def test_loads_named_profile(self, tmp_path: Path) -> None:
        profile_dir = tmp_path / "repo_doctor.d"
        profile_dir.mkdir()
        (profile_dir / "python.toml").write_text(
            '[[rule]]\ntype = "exists"\npath = "setup.py"\n'
        )
        rules = _load_profile_rules(tmp_path, ["python"])
        assert len(rules) == 1
        assert rules[0].path == "setup.py"

    def test_all_keyword(self, tmp_path: Path) -> None:
        profile_dir = tmp_path / "repo_doctor.d"
        profile_dir.mkdir()
        (profile_dir / "a.toml").write_text(
            '[[rule]]\ntype = "exists"\npath = "a.txt"\n'
        )
        (profile_dir / "b.toml").write_text(
            '[[rule]]\ntype = "exists"\npath = "b.txt"\n'
        )
        rules = _load_profile_rules(tmp_path, ["all"])
        assert len(rules) == 2

    def test_invalid_profile_logs_to_stderr(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        profile_dir = tmp_path / "repo_doctor.d"
        profile_dir.mkdir()
        (profile_dir / "bad.toml").write_text("invalid [[[toml")
        with caplog.at_level("WARNING"):
            rules = _load_profile_rules(tmp_path, ["bad"])
        assert rules == []
        assert "bad.toml" in caplog.text

    def test_missing_profile_ignored(self, tmp_path: Path) -> None:
        profile_dir = tmp_path / "repo_doctor.d"
        profile_dir.mkdir()
        rules = _load_profile_rules(tmp_path, ["nonexistent"])
        assert rules == []


# ---------------------------------------------------------------------------
# _evaluate_rules
# ---------------------------------------------------------------------------


class TestEvaluateRules:
    """Tests for rule evaluation logic."""

    def test_missing_file_produces_warning(self, tmp_path: Path) -> None:
        rules = [Rule(type="exists", path="missing.txt")]
        warnings, _passed = _evaluate_rules(
            tmp_path, rules, check_missing=True, deleted=set()
        )
        assert len(warnings) == 1
        assert "Missing" in warnings[0].message

    def test_existing_file_no_warning(self, tmp_path: Path) -> None:
        (tmp_path / "present.txt").write_text("ok")
        rules = [Rule(type="exists", path="present.txt")]
        warnings, passed = _evaluate_rules(
            tmp_path, rules, check_missing=True, deleted=set()
        )
        assert warnings == []
        assert len(passed) == 1
        assert "OK" in passed[0].message

    def test_deleted_file_produces_warning(self, tmp_path: Path) -> None:
        rules = [Rule(type="exists", path="gone.txt")]
        warnings, _passed = _evaluate_rules(
            tmp_path,
            rules,
            check_missing=True,
            deleted={"gone.txt"},
        )
        # Should only produce ONE warning (deleted), not both
        # (deleted + missing)
        deleted_warnings = [w for w in warnings if "Deleted" in w.message]
        missing_warnings = [w for w in warnings if "Missing" in w.message]
        assert len(deleted_warnings) == 1
        assert len(missing_warnings) == 0

    def test_no_duplicate_for_deleted_and_missing(self, tmp_path: Path) -> None:
        """Deleted path should NOT also appear as missing."""
        rules = [Rule(type="exists", path="file.txt")]
        warnings, _passed = _evaluate_rules(
            tmp_path,
            rules,
            check_missing=True,
            deleted={"file.txt"},
        )
        assert len(warnings) == 1
        assert "Deleted" in warnings[0].message

    def test_regex_present_success(self, tmp_path: Path) -> None:
        (tmp_path / "cfg.toml").write_text("name = 'test'")
        rules = [
            Rule(
                type="regex_present",
                path="cfg.toml",
                regex=r"name\s*=",
            )
        ]
        warnings, passed = _evaluate_rules(
            tmp_path, rules, check_missing=True, deleted=set()
        )
        assert warnings == []
        assert len(passed) == 1

    def test_regex_present_failure(self, tmp_path: Path) -> None:
        (tmp_path / "cfg.toml").write_text("empty file")
        rules = [
            Rule(
                type="regex_present",
                path="cfg.toml",
                regex=r"name\s*=",
            )
        ]
        warnings, _passed = _evaluate_rules(
            tmp_path, rules, check_missing=True, deleted=set()
        )
        assert len(warnings) == 1
        assert "Check failed" in warnings[0].message

    def test_toml_has_path_success(self, tmp_path: Path) -> None:
        (tmp_path / "p.toml").write_text('[project]\nname = "x"\n')
        rules = [
            Rule(
                type="toml_has_path",
                path="p.toml",
                toml_path="project.name",
            )
        ]
        warnings, passed = _evaluate_rules(
            tmp_path, rules, check_missing=True, deleted=set()
        )
        assert warnings == []
        assert len(passed) == 1

    def test_toml_has_path_missing_key(self, tmp_path: Path) -> None:
        (tmp_path / "p.toml").write_text("[project]\n")
        rules = [
            Rule(
                type="toml_has_path",
                path="p.toml",
                toml_path="project.name",
            )
        ]
        warnings, _passed = _evaluate_rules(
            tmp_path, rules, check_missing=True, deleted=set()
        )
        assert len(warnings) == 1
        assert "missing" in warnings[0].message.lower()

    def test_unknown_rule_type(self, tmp_path: Path) -> None:
        rules = [Rule(type="bogus", path="x.txt")]
        warnings, _passed = _evaluate_rules(
            tmp_path, rules, check_missing=True, deleted=set()
        )
        assert len(warnings) == 1
        assert "Unknown rule type" in warnings[0].message

    def test_only_if_skips_when_condition_false(self, tmp_path: Path) -> None:
        (tmp_path / "gate.toml").write_text("nothing")
        rules = [
            Rule(
                type="exists",
                path="target.txt",
                only_if=OnlyIf(path="gate.toml", regex="required"),
            )
        ]
        warnings, passed = _evaluate_rules(
            tmp_path, rules, check_missing=True, deleted=set()
        )
        assert warnings == []
        assert passed == []  # skipped, not passed

    def test_only_if_evaluates_when_condition_true(self, tmp_path: Path) -> None:
        (tmp_path / "gate.toml").write_text("required pattern here")
        rules = [
            Rule(
                type="exists",
                path="target.txt",
                only_if=OnlyIf(path="gate.toml", regex="required"),
            )
        ]
        warnings, _passed = _evaluate_rules(
            tmp_path, rules, check_missing=True, deleted=set()
        )
        assert len(warnings) == 1
        assert "Missing" in warnings[0].message

    def test_check_missing_false_skips_exists_check(self, tmp_path: Path) -> None:
        rules = [Rule(type="exists", path="missing.txt")]
        warnings, _passed = _evaluate_rules(
            tmp_path, rules, check_missing=False, deleted=set()
        )
        assert warnings == []


# ---------------------------------------------------------------------------
# _format_warning
# ---------------------------------------------------------------------------


class TestFormatWarning:
    """Tests for warning output formatting."""

    def test_basic_format(self) -> None:
        rule = Rule(type="exists", path="f.txt", level="warn")
        w = Warning(rule=rule, message="Missing: f.txt")
        output = _format_warning(
            w,
            show_hints=True,
            show_links=True,
            show_fix=False,
        )
        assert "[warn]" in output
        assert "Missing: f.txt" in output

    def test_includes_category(self) -> None:
        rule = Rule(type="exists", path="f.txt", category="ci")
        w = Warning(rule=rule, message="Missing: f.txt")
        output = _format_warning(
            w,
            show_hints=True,
            show_links=True,
            show_fix=False,
        )
        assert "(ci)" in output

    def test_shows_hint(self) -> None:
        rule = Rule(type="exists", path="f.txt", hint="Add the file")
        w = Warning(rule=rule, message="Missing: f.txt")
        output = _format_warning(
            w,
            show_hints=True,
            show_links=True,
            show_fix=False,
        )
        assert "Hint:" in output
        assert "Add the file" in output

    def test_hides_hint_when_disabled(self) -> None:
        rule = Rule(type="exists", path="f.txt", hint="Add the file")
        w = Warning(rule=rule, message="Missing: f.txt")
        output = _format_warning(
            w,
            show_hints=False,
            show_links=True,
            show_fix=False,
        )
        assert "Hint:" not in output

    def test_shows_link(self) -> None:
        rule = Rule(type="exists", path="f.txt", link="docs/adr/001.md")
        w = Warning(rule=rule, message="Missing: f.txt")
        output = _format_warning(
            w,
            show_hints=True,
            show_links=True,
            show_fix=False,
        )
        assert "See:" in output

    def test_shows_fix_command(self) -> None:
        rule = Rule(type="exists", path="f.txt", fix="touch f.txt")
        w = Warning(rule=rule, message="Missing: f.txt")
        output = _format_warning(
            w,
            show_hints=True,
            show_links=True,
            show_fix=True,
        )
        assert "Fix:" in output
        assert "touch f.txt" in output

    def test_hides_fix_when_disabled(self) -> None:
        rule = Rule(type="exists", path="f.txt", fix="touch f.txt")
        w = Warning(rule=rule, message="Missing: f.txt")
        output = _format_warning(
            w,
            show_hints=True,
            show_links=True,
            show_fix=False,
        )
        assert "Fix:" not in output

    def test_color_output(self) -> None:
        rule = Rule(type="exists", path="f.txt", level="warn")
        w = Warning(rule=rule, message="Missing: f.txt")
        output = _format_warning(
            w,
            show_hints=True,
            show_links=True,
            show_fix=False,
            use_color=True,
        )
        assert "\033[33m" in output  # yellow for warn
        assert "\033[0m" in output

    def test_no_color_output(self) -> None:
        rule = Rule(type="exists", path="f.txt", level="warn")
        w = Warning(rule=rule, message="Missing: f.txt")
        output = _format_warning(
            w,
            show_hints=True,
            show_links=True,
            show_fix=False,
            use_color=False,
        )
        assert "\033[" not in output

    def test_impact_shown(self) -> None:
        rule = Rule(type="exists", path="f.txt", impact="CI will fail")
        w = Warning(rule=rule, message="Missing: f.txt")
        output = _format_warning(
            w,
            show_hints=True,
            show_links=True,
            show_fix=False,
        )
        assert "Impact:" in output
        assert "CI will fail" in output


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

    def test_no_color_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--no-color"])
        assert args.no_color is True

    def test_defaults(self) -> None:
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.missing is False
        assert args.staged is False
        assert args.no_color is False
        assert args.no_hints is False
        assert args.fix is False
        assert args.min_level == "warn"

    def test_profile_repeatable(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--profile", "python", "--profile", "ci"])
        assert args.profile == ["python", "ci"]

    def test_include_info(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--include-info"])
        assert args.include_info is True

    def test_category_filter(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--category", "security"])
        assert args.category == "security"

    def test_diff_range(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--diff", "origin/main...HEAD"])
        assert args.diff == "origin/main...HEAD"


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


class TestMain:
    """Integration-style tests for the main entry point."""

    def test_no_rules_prints_message(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        from repo_doctor import main

        with (
            patch("repo_doctor._repo_root", return_value=tmp_path),
            patch(
                "repo_doctor._build_parser",
                return_value=self._parser([]),
            ),
            caplog.at_level("INFO"),
        ):
            ret = main()
        assert ret == 0
        assert "no rules found" in caplog.text.lower()

    def test_all_checks_pass(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from repo_doctor import main

        (tmp_path / "README.md").write_text("# Hello")
        toml = '[[rule]]\ntype = "exists"\npath = "README.md"\n'
        (tmp_path / ".repo-doctor.toml").write_text(toml)

        with (
            patch("repo_doctor._repo_root", return_value=tmp_path),
            patch(
                "repo_doctor._build_parser",
                return_value=self._parser(["--missing"]),
            ),
            patch("repo_doctor._check_shared_modules", return_value=[]),
        ):
            ret = main()
        assert ret == 0
        assert "checks passed" in capsys.readouterr().out

    def test_missing_file_shows_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from repo_doctor import main

        toml = '[[rule]]\ntype = "exists"\npath = "MISSING.md"\n'
        (tmp_path / ".repo-doctor.toml").write_text(toml)

        with (
            patch("repo_doctor._repo_root", return_value=tmp_path),
            patch(
                "repo_doctor._build_parser",
                return_value=self._parser(["--missing", "--no-color"]),
            ),
        ):
            ret = main()
        assert ret == 0
        out = capsys.readouterr().out
        assert "Missing: MISSING.md" in out

    @staticmethod
    def _parser(argv: list[str]) -> argparse.ArgumentParser:
        """Build a parser pre-loaded with given args."""
        parser = _build_parser()
        # Override parse_args to return fixed namespace
        original_parse = parser.parse_args
        parser.parse_args = lambda *_a, **_kw: original_parse(argv)
        return parser
