"""Tests for customize.py interactive flows and CLI execution paths."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from customize import (
    Config,
    Replacement,
    _prompt,
    _prompt_choice,
    _prompt_multi,
    _prompt_yn,
    config_from_args,
    gather_config_interactive,
    parse_args,
    plan_replacements,
    print_plan,
)

# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------


class TestPrompt:
    """Tests for _prompt() interactive input."""

    def test_returns_user_input(self) -> None:
        with patch("builtins.input", return_value="my-value"):
            result = _prompt("Enter value")
        assert result == "my-value"

    def test_strips_whitespace(self) -> None:
        with patch("builtins.input", return_value="  trimmed  "):
            result = _prompt("Enter value")
        assert result == "trimmed"

    def test_returns_default_on_empty(self) -> None:
        with patch("builtins.input", return_value=""):
            result = _prompt("Enter value", default="fallback")
        assert result == "fallback"

    def test_requires_value_when_no_default(self) -> None:
        # First call returns empty, second returns a value
        with patch("builtins.input", side_effect=["", "valid"]):
            result = _prompt("Enter value")
        assert result == "valid"

    def test_eof_exits(self) -> None:
        with patch("builtins.input", side_effect=EOFError), pytest.raises(SystemExit):
            _prompt("Enter value")

    def test_keyboard_interrupt_exits(self) -> None:
        with (
            patch("builtins.input", side_effect=KeyboardInterrupt),
            pytest.raises(SystemExit),
        ):
            _prompt("Enter value")


class TestPromptYn:
    """Tests for _prompt_yn() yes/no prompt."""

    def test_yes_input(self) -> None:
        with patch("builtins.input", return_value="y"):
            assert _prompt_yn("Continue?") is True

    def test_no_input(self) -> None:
        with patch("builtins.input", return_value="n"):
            assert _prompt_yn("Continue?") is False

    def test_empty_returns_default_true(self) -> None:
        with patch("builtins.input", return_value=""):
            assert _prompt_yn("Continue?", default=True) is True

    def test_empty_returns_default_false(self) -> None:
        with patch("builtins.input", return_value=""):
            assert _prompt_yn("Continue?", default=False) is False

    def test_yes_variations(self) -> None:
        for val in ("yes", "YES", "Y"):
            with patch("builtins.input", return_value=val):
                assert _prompt_yn("Continue?") is True

    def test_no_variations(self) -> None:
        for val in ("no", "NO", "N", "x", "anything"):
            with patch("builtins.input", return_value=val):
                assert _prompt_yn("Continue?") is False

    def test_eof_exits(self) -> None:
        with patch("builtins.input", side_effect=EOFError), pytest.raises(SystemExit):
            _prompt_yn("Continue?")


class TestPromptChoice:
    """Tests for _prompt_choice() single-selection prompt."""

    def test_select_by_number(self) -> None:
        choices = {"a": "Option A", "b": "Option B", "c": "Option C"}
        with patch("builtins.input", return_value="2"):
            result = _prompt_choice("Pick one:", choices, "a")
        assert result == "b"

    def test_empty_returns_default(self) -> None:
        choices = {"a": "Option A", "b": "Option B"}
        with patch("builtins.input", return_value=""):
            result = _prompt_choice("Pick one:", choices, "b")
        assert result == "b"

    def test_select_by_key(self) -> None:
        choices = {"mit": "MIT License", "apache": "Apache 2.0"}
        with patch("builtins.input", return_value="mit"):
            result = _prompt_choice("Pick one:", choices, "apache")
        assert result == "mit"

    def test_invalid_then_valid(self) -> None:
        choices = {"a": "Option A", "b": "Option B"}
        with patch("builtins.input", side_effect=["99", "1"]):
            result = _prompt_choice("Pick one:", choices, "a")
        assert result == "a"

    def test_eof_exits(self) -> None:
        choices = {"a": "Option A"}
        with patch("builtins.input", side_effect=EOFError), pytest.raises(SystemExit):
            _prompt_choice("Pick:", choices, "a")


class TestPromptMulti:
    """Tests for _prompt_multi() multi-selection prompt."""

    def test_select_multiple(self) -> None:
        choices = {"a": "Option A", "b": "Option B", "c": "Option C"}
        with patch("builtins.input", return_value="1,3"):
            result = _prompt_multi("Select:", choices)
        assert result == ["a", "c"]

    def test_select_none(self) -> None:
        choices = {"a": "Option A", "b": "Option B"}
        with patch("builtins.input", return_value="0"):
            result = _prompt_multi("Select:", choices)
        assert result == []

    def test_empty_returns_empty(self) -> None:
        choices = {"a": "Option A"}
        with patch("builtins.input", return_value=""):
            result = _prompt_multi("Select:", choices)
        assert result == []

    def test_deduplicates(self) -> None:
        choices = {"a": "Option A", "b": "Option B"}
        with patch("builtins.input", return_value="1,1,2"):
            result = _prompt_multi("Select:", choices)
        assert result == ["a", "b"]

    def test_ignores_invalid_entries(self) -> None:
        choices = {"a": "Option A", "b": "Option B"}
        with patch("builtins.input", return_value="1,99,abc"):
            result = _prompt_multi("Select:", choices)
        assert result == ["a"]

    def test_eof_exits(self) -> None:
        choices = {"a": "Option A"}
        with patch("builtins.input", side_effect=EOFError), pytest.raises(SystemExit):
            _prompt_multi("Select:", choices)

    def test_all_of_the_above_standalone(self) -> None:
        """Entering the 'all of the above' index selects every choice."""
        choices = {"a": "Option A", "b": "Option B", "c": "Option C"}
        # all_idx = len(choices) + 1 = 4
        with patch("builtins.input", return_value="4"):
            result = _prompt_multi("Select:", choices)
        assert result == ["a", "b", "c"]

    def test_all_of_the_above_in_comma_list(self) -> None:
        """Including the 'all' index in a comma list selects everything."""
        choices = {"x": "X", "y": "Y"}
        # all_idx = 3; entering "1,3" should trigger the all-of-the-above
        # short-circuit and return all keys
        with patch("builtins.input", return_value="1,3"):
            result = _prompt_multi("Select:", choices)
        assert result == ["x", "y"]

    def test_select_by_key_name(self) -> None:
        """Entering a key name directly (not a number) should select it."""
        choices = {"db": "Database", "var": "Variable dir"}
        with patch("builtins.input", return_value="var"):
            result = _prompt_multi("Select:", choices)
        assert result == ["var"]

    def test_keyboard_interrupt_exits(self) -> None:
        choices = {"a": "Option A"}
        with (
            patch("builtins.input", side_effect=KeyboardInterrupt),
            pytest.raises(SystemExit),
        ):
            _prompt_multi("Select:", choices)


# ---------------------------------------------------------------------------
# gather_config_interactive
# ---------------------------------------------------------------------------


class TestGatherConfigInteractive:
    """Tests for the full interactive wizard flow."""

    def test_minimal_interactive_session(self) -> None:
        """Simulate a user going through the wizard with minimal choices."""
        inputs = iter(
            [
                "my-project",  # project name
                "",  # package name (accept default my_project)
                "Jane Doe",  # author
                "janedoe",  # github user
                "",  # description (accept default)
                "",  # CLI prefix (accept default mp)
                "n",  # private repo (no)
                "",  # license (accept default apache-2.0)
                "0",  # strip dirs (none)
                "0",  # template cleanup (none)
            ]
        )
        with patch("builtins.input", side_effect=inputs):
            cfg = gather_config_interactive()

        assert cfg.project_name == "my-project"
        assert cfg.package_name == "my_project"
        assert cfg.author == "Jane Doe"
        assert cfg.github_user == "janedoe"
        assert cfg.private_repo is False
        assert cfg.license_id == "apache-2.0"
        assert cfg.strip_dirs == []
        assert cfg.template_cleanup == []

    def test_interactive_with_strip_dirs(self) -> None:
        """Simulate selecting directories to strip."""
        inputs = iter(
            [
                "test-proj",  # project name
                "",  # package name (default)
                "Author",  # author
                "testuser",  # github user
                "",  # description (default)
                "",  # CLI prefix (default)
                "n",  # private repo (no)
                "",  # license (default)
                "1,2",  # strip dirs (first two)
                "0",  # template cleanup (none)
            ]
        )
        with patch("builtins.input", side_effect=inputs):
            cfg = gather_config_interactive()

        assert cfg.project_name == "test-proj"
        assert len(cfg.strip_dirs) == 2

    def test_interactive_strip_dirs_all_of_the_above(self) -> None:
        """Selecting 'all of the above' for strip dirs selects every entry."""
        from customize import STRIPPABLE

        all_idx = str(len(STRIPPABLE) + 1)
        inputs = iter(
            [
                "my-app",  # project name
                "",  # package name (default)
                "Author",  # author
                "user",  # github user
                "",  # description (default)
                "",  # CLI prefix (default)
                "n",  # private repo (no)
                "",  # license (default)
                all_idx,  # strip dirs — all of the above
                "0",  # template cleanup (none)
            ]
        )
        with patch("builtins.input", side_effect=inputs):
            cfg = gather_config_interactive()

        assert cfg.strip_dirs == list(STRIPPABLE.keys())

    def test_interactive_template_cleanup_all_of_the_above(self) -> None:
        """Selecting 'all of the above' for template cleanup selects all."""
        from customize import TEMPLATE_CLEANUP

        all_idx = str(len(TEMPLATE_CLEANUP) + 1)
        inputs = iter(
            [
                "my-app",  # project name
                "",  # package name (default)
                "Author",  # author
                "user",  # github user
                "",  # description (default)
                "",  # CLI prefix (default)
                "n",  # private repo (no)
                "",  # license (default)
                "0",  # strip dirs (none)
                all_idx,  # template cleanup — all of the above
                "y",  # confirm disclaimers
            ]
        )
        with patch("builtins.input", side_effect=inputs):
            cfg = gather_config_interactive()

        assert cfg.template_cleanup == list(TEMPLATE_CLEANUP.keys())

    def test_interactive_with_template_cleanup_confirmed(self) -> None:
        """Simulate selecting template cleanup items and confirming."""
        inputs = iter(
            [
                "my-app",  # project name
                "",  # package name (default)
                "Dev",  # author
                "devuser",  # github user
                "",  # description (default)
                "",  # CLI prefix (default)
                "n",  # private repo (no)
                "",  # license (default)
                "0",  # strip dirs (none)
                "1",  # template cleanup (first item)
                "y",  # confirm disclaimer
            ]
        )
        with patch("builtins.input", side_effect=inputs):
            cfg = gather_config_interactive()

        assert len(cfg.template_cleanup) == 1

    def test_interactive_with_template_cleanup_declined(self) -> None:
        """Simulate selecting cleanup items but declining after disclaimer."""
        inputs = iter(
            [
                "my-app",  # project name
                "",  # package name (default)
                "Dev",  # author
                "devuser",  # github user
                "",  # description (default)
                "",  # CLI prefix (default)
                "n",  # private repo (no)
                "",  # license (default)
                "0",  # strip dirs (none)
                "1",  # template cleanup (first item)
                "n",  # decline after disclaimer
            ]
        )
        with patch("builtins.input", side_effect=inputs):
            cfg = gather_config_interactive()

        assert cfg.template_cleanup == []

    def test_interactive_invalid_project_name_then_valid(self) -> None:
        """Simulate entering an invalid name first, then a valid one."""
        inputs = iter(
            [
                "INVALID",  # invalid (uppercase)
                "valid-name",  # valid
                "",  # package name (default)
                "Author",  # author
                "user",  # github user
                "",  # description
                "",  # CLI prefix
                "n",  # private repo (no)
                "",  # license
                "0",  # strip dirs
                "0",  # template cleanup
            ]
        )
        with patch("builtins.input", side_effect=inputs):
            cfg = gather_config_interactive()

        assert cfg.project_name == "valid-name"

    def test_interactive_mit_license(self) -> None:
        """Simulate choosing MIT license."""
        inputs = iter(
            [
                "my-lib",  # project name
                "",  # package name (default)
                "Author",  # author
                "user",  # github user
                "",  # description
                "",  # CLI prefix
                "n",  # private repo (no)
                "2",  # license = MIT (second choice)
                "0",  # strip dirs
                "0",  # template cleanup
            ]
        )
        with patch("builtins.input", side_effect=inputs):
            cfg = gather_config_interactive()

        assert cfg.license_id == "mit"


# ---------------------------------------------------------------------------
# plan_replacements
# ---------------------------------------------------------------------------


class TestPlanReplacements:
    """Tests for plan_replacements()."""

    def test_produces_replacements(self) -> None:
        cfg = Config(
            project_name="new-project",
            package_name="new_project",
            author="TestAuthor",
            github_user="testorg",
            description="A test project",
            cli_prefix="np",
        )
        reps = plan_replacements(cfg)
        assert len(reps) > 0
        assert all(isinstance(r, Replacement) for r in reps)

    def test_github_slug_replacement_is_first(self) -> None:
        cfg = Config(
            project_name="my-proj",
            package_name="my_proj",
            author="Me",
            github_user="myorg",
            description="desc",
            cli_prefix="mp",
        )
        reps = plan_replacements(cfg)
        assert reps[0].old == "YOURNAME/YOURREPO"
        assert reps[0].new == "myorg/my-proj"

    def test_no_project_rename_when_same(self) -> None:
        cfg = Config(
            project_name="simple-python-boilerplate",
            package_name="simple_python_boilerplate",
            author="Joseph",
            github_user="other",
            description="Simple Python boilerplate using src/ layout",
            cli_prefix="spb",
        )
        reps = plan_replacements(cfg)
        # Should not have a replacement for project name since it's the same
        old_values = [r.old for r in reps]
        assert "simple-python-boilerplate" not in old_values

    def test_cli_prefix_compound_entries(self) -> None:
        cfg = Config(
            project_name="my-tool",
            package_name="my_tool",
            author="Dev",
            github_user="dev",
            description="desc",
            cli_prefix="mt",
        )
        reps = plan_replacements(cfg)
        old_values = [r.old for r in reps]
        assert "spb-version" in old_values
        assert "spb-doctor" in old_values


# ---------------------------------------------------------------------------
# print_plan (smoke test — just ensure it doesn't crash)
# ---------------------------------------------------------------------------


class TestPrintPlan:
    """Tests for print_plan() output rendering."""

    def test_print_plan_default_config(self, capsys) -> None:
        cfg = Config(
            project_name="test-proj",
            package_name="test_proj",
            author="Author",
            github_user="user",
            description="A test",
            cli_prefix="tp",
        )
        reps = plan_replacements(cfg)
        print_plan(cfg, reps)
        captured = capsys.readouterr()
        assert "Customization Plan" in captured.out

    def test_print_plan_with_strip_dirs(self, capsys) -> None:
        cfg = Config(
            project_name="test-proj",
            package_name="test_proj",
            author="Author",
            github_user="user",
            description="A test",
            cli_prefix="tp",
            strip_dirs=["db", "experiments"],
        )
        reps = plan_replacements(cfg)
        print_plan(cfg, reps)
        captured = capsys.readouterr()
        assert "Directories to remove" in captured.out

    def test_print_plan_with_cleanup(self, capsys) -> None:
        cfg = Config(
            project_name="test-proj",
            package_name="test_proj",
            author="Author",
            github_user="user",
            description="A test",
            cli_prefix="tp",
            template_cleanup=["placeholder-code"],
        )
        reps = plan_replacements(cfg)
        print_plan(cfg, reps)
        captured = capsys.readouterr()
        assert "Template cleanup" in captured.out


# ---------------------------------------------------------------------------
# CLI: parse_args and config_from_args
# ---------------------------------------------------------------------------


class TestParseArgs:
    """Tests for CLI argument parsing."""

    def test_dry_run_flag(self) -> None:
        args = parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_non_interactive_flags(self) -> None:
        args = parse_args(
            [
                "--non-interactive",
                "--project-name",
                "test-proj",
                "--author",
                "Author",
                "--github-user",
                "user",
            ]
        )
        assert args.non_interactive is True
        assert args.project_name == "test-proj"

    def test_strip_choices(self) -> None:
        args = parse_args(["--strip", "db", "experiments"])
        assert args.strip == ["db", "experiments"]

    def test_enable_workflows(self) -> None:
        args = parse_args(["--enable-workflows", "myorg/myrepo"])
        assert args.enable_workflows == "myorg/myrepo"

    def test_version_flag(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--version"])
        assert exc_info.value.code == 0


class TestConfigFromArgs:
    """Tests for config_from_args() non-interactive config build."""

    def test_builds_config_from_args(self) -> None:
        args = parse_args(
            [
                "--non-interactive",
                "--project-name",
                "my-proj",
                "--author",
                "Author",
                "--github-user",
                "org",
            ]
        )
        cfg = config_from_args(args)
        assert cfg.project_name == "my-proj"
        assert cfg.package_name == "my_proj"  # auto-derived
        assert cfg.author == "Author"
        assert cfg.github_user == "org"

    def test_custom_package_name(self) -> None:
        args = parse_args(
            [
                "--non-interactive",
                "--project-name",
                "my-proj",
                "--package-name",
                "custom_pkg",
                "--author",
                "Author",
                "--github-user",
                "org",
            ]
        )
        cfg = config_from_args(args)
        assert cfg.package_name == "custom_pkg"

    def test_missing_required_exits(self) -> None:
        args = parse_args(["--non-interactive"])
        with pytest.raises(SystemExit) as exc_info:
            config_from_args(args)
        assert exc_info.value.code == 2

    def test_invalid_project_name_exits(self) -> None:
        args = parse_args(
            [
                "--non-interactive",
                "--project-name",
                "INVALID",
                "--author",
                "Author",
                "--github-user",
                "org",
            ]
        )
        with pytest.raises(SystemExit) as exc_info:
            config_from_args(args)
        assert exc_info.value.code == 2

    def test_invalid_package_name_exits(self) -> None:
        args = parse_args(
            [
                "--non-interactive",
                "--project-name",
                "my-proj",
                "--package-name",
                "123bad",
                "--author",
                "Author",
                "--github-user",
                "org",
            ]
        )
        with pytest.raises(SystemExit) as exc_info:
            config_from_args(args)
        assert exc_info.value.code == 2

    def test_cli_prefix_auto_derived(self) -> None:
        args = parse_args(
            [
                "--non-interactive",
                "--project-name",
                "my-cool-app",
                "--author",
                "Author",
                "--github-user",
                "org",
            ]
        )
        cfg = config_from_args(args)
        assert cfg.cli_prefix == "mca"  # initials of my-cool-app

    def test_cli_prefix_explicit(self) -> None:
        args = parse_args(
            [
                "--non-interactive",
                "--project-name",
                "my-proj",
                "--author",
                "Author",
                "--github-user",
                "org",
                "--cli-prefix",
                "xyz",
            ]
        )
        cfg = config_from_args(args)
        assert cfg.cli_prefix == "xyz"

    def test_description_auto_derived(self) -> None:
        args = parse_args(
            [
                "--non-interactive",
                "--project-name",
                "my-proj",
                "--author",
                "Author",
                "--github-user",
                "org",
            ]
        )
        cfg = config_from_args(args)
        assert "my-proj" in cfg.description

    def test_license_default(self) -> None:
        args = parse_args(
            [
                "--non-interactive",
                "--project-name",
                "my-proj",
                "--author",
                "Author",
                "--github-user",
                "org",
            ]
        )
        cfg = config_from_args(args)
        assert cfg.license_id == "apache-2.0"

    def test_license_explicit(self) -> None:
        args = parse_args(
            [
                "--non-interactive",
                "--project-name",
                "my-proj",
                "--author",
                "Author",
                "--github-user",
                "org",
                "--license",
                "mit",
            ]
        )
        cfg = config_from_args(args)
        assert cfg.license_id == "mit"


# ---------------------------------------------------------------------------
# main() entry point — integration-style tests with mocked filesystem
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for main() CLI entry point."""

    def test_main_dry_run_non_interactive(self) -> None:
        """Non-interactive dry-run should succeed without modifying files."""
        from customize import main

        test_args = [
            "customize.py",
            "--non-interactive",
            "--dry-run",
            "--force",
            "--project-name",
            "test-proj",
            "--author",
            "Test Author",
            "--github-user",
            "testuser",
        ]
        with patch("sys.argv", test_args):
            result = main()
        assert result == 0

    def test_main_enable_workflows_dry_run(self) -> None:
        """--enable-workflows with --dry-run should succeed."""
        from customize import main

        test_args = [
            "customize.py",
            "--dry-run",
            "--enable-workflows",
            "testuser/test-proj",
        ]
        with patch("sys.argv", test_args):
            result = main()
        assert result == 0

    def test_main_enable_workflows_invalid_slug(self) -> None:
        """--enable-workflows with invalid slug should return error."""
        from customize import main

        test_args = [
            "customize.py",
            "--enable-workflows",
            "invalid-no-slash",
        ]
        with patch("sys.argv", test_args):
            result = main()
        assert result == 1
