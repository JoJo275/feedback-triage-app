"""Unit tests for scripts/generate_command_reference.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from generate_command_reference import (
    OUTPUT,
    ROOT,
    SCRIPT_VERSION,
    _collect_scripts,
    _escape_md_brackets,
    _extract_module_description,
    _parse_taskfile_tasks,
    _run,
    _run_combined,
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

    def test_root_is_directory(self) -> None:
        assert ROOT.is_dir()

    def test_output_path_is_under_root(self) -> None:
        assert str(OUTPUT).startswith(str(ROOT))


# ---------------------------------------------------------------------------
# _escape_md_brackets
# ---------------------------------------------------------------------------


class TestEscapeMdBrackets:
    """Tests for _escape_md_brackets()."""

    def test_no_brackets(self) -> None:
        assert _escape_md_brackets("hello world") == "hello world"

    def test_square_brackets_escaped(self) -> None:
        assert _escape_md_brackets("[foo]") == "\\[foo\\]"

    def test_nested_brackets(self) -> None:
        assert _escape_md_brackets("[[bar]]") == "\\[\\[bar\\]\\]"

    def test_mixed_content(self) -> None:
        result = _escape_md_brackets("Run [task] for help")
        assert result == "Run \\[task\\] for help"

    def test_empty_string(self) -> None:
        assert _escape_md_brackets("") == ""

    def test_no_parens_escaped(self) -> None:
        """Parentheses should NOT be escaped (only square brackets)."""
        assert _escape_md_brackets("(foo)") == "(foo)"


# ---------------------------------------------------------------------------
# _extract_module_description
# ---------------------------------------------------------------------------


class TestExtractModuleDescription:
    """Tests for _extract_module_description() — AST-based docstring extraction."""

    def test_extracts_first_line(self, tmp_path: Path) -> None:
        script = tmp_path / "sample.py"
        script.write_text('"""This is the first line.\n\nMore details here.\n"""')
        result = _extract_module_description(script)
        assert result == "This is the first line"

    def test_single_line_docstring(self, tmp_path: Path) -> None:
        script = tmp_path / "sample.py"
        script.write_text('"""Simple description."""')
        result = _extract_module_description(script)
        assert result == "Simple description"

    def test_no_docstring(self, tmp_path: Path) -> None:
        script = tmp_path / "sample.py"
        script.write_text("import sys\nprint('hello')\n")
        result = _extract_module_description(script)
        assert result == "*(no description)*"

    def test_empty_file(self, tmp_path: Path) -> None:
        script = tmp_path / "sample.py"
        script.write_text("")
        result = _extract_module_description(script)
        assert result == "*(no description)*"

    def test_syntax_error_file(self, tmp_path: Path) -> None:
        script = tmp_path / "bad.py"
        script.write_text("def broken(:\n    pass")
        result = _extract_module_description(script)
        assert result == "*(no description)*"

    def test_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.py"
        result = _extract_module_description(missing)
        assert result == "*(no description)*"

    def test_strips_trailing_period(self, tmp_path: Path) -> None:
        script = tmp_path / "sample.py"
        script.write_text('"""Description with period."""')
        result = _extract_module_description(script)
        assert not result.endswith(".")


# ---------------------------------------------------------------------------
# _collect_scripts
# ---------------------------------------------------------------------------


class TestCollectScripts:
    """Tests for _collect_scripts()."""

    def test_returns_list_of_paths(self) -> None:
        scripts = _collect_scripts()
        assert isinstance(scripts, list)
        assert all(isinstance(p, Path) for p in scripts)

    def test_excludes_underscore_prefixed(self) -> None:
        scripts = _collect_scripts()
        for p in scripts:
            assert not p.name.startswith("_"), f"Should exclude {p.name}"

    def test_all_are_python_files(self) -> None:
        scripts = _collect_scripts()
        assert all(p.suffix == ".py" for p in scripts)

    def test_sorted_within_groups(self) -> None:
        """Scripts should be sorted within each directory group."""
        scripts = _collect_scripts()
        from generate_command_reference import PRECOMMIT_DIR, SCRIPTS_DIR

        main_names = [p.name for p in scripts if p.parent == SCRIPTS_DIR]
        assert main_names == sorted(main_names)
        precommit_names = [p.name for p in scripts if p.parent == PRECOMMIT_DIR]
        assert precommit_names == sorted(precommit_names)

    def test_known_script_present(self) -> None:
        """At least clean.py should be in the list."""
        scripts = _collect_scripts()
        names = {p.name for p in scripts}
        assert "clean.py" in names

    def test_init_excluded(self) -> None:
        scripts = _collect_scripts()
        names = {p.name for p in scripts}
        assert "__init__.py" not in names


# ---------------------------------------------------------------------------
# _run / _run_combined
# ---------------------------------------------------------------------------


class TestRun:
    """Tests for _run() subprocess helper."""

    def test_successful_command(self) -> None:
        result = _run([sys.executable, "-c", "print('hello')"])
        assert result == "hello"

    def test_failing_command_returns_none(self) -> None:
        result = _run([sys.executable, "-c", "import sys; sys.exit(1)"])
        assert result is None

    def test_missing_command_returns_none(self) -> None:
        result = _run(["nonexistent_command_xyz"])
        assert result is None

    def test_timeout_returns_none(self) -> None:
        result = _run(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            timeout=1,
        )
        assert result is None


class TestRunCombined:
    """Tests for _run_combined() subprocess helper."""

    def test_successful_stdout(self) -> None:
        result = _run_combined([sys.executable, "-c", "print('out')"])
        assert result is not None
        assert "out" in result

    def test_stderr_included(self) -> None:
        result = _run_combined(
            [sys.executable, "-c", "import sys; sys.stderr.write('err\\n')"]
        )
        assert result is not None
        assert "err" in result


# ---------------------------------------------------------------------------
# _parse_taskfile_tasks
# ---------------------------------------------------------------------------


class TestParseTaskfileTasks:
    """Tests for _parse_taskfile_tasks()."""

    def test_returns_list_of_tuples(self) -> None:
        # This may return empty if `task` is not installed, which is fine
        result = _parse_taskfile_tasks()
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], tuple)
            assert len(result[0]) == 2

    @patch("generate_command_reference._run", return_value=None)
    def test_returns_empty_when_task_not_installed(self, _mock: object) -> None:
        result = _parse_taskfile_tasks()
        assert result == []

    @patch("generate_command_reference._run")
    def test_parses_task_list_output(self, mock_run: MagicMock) -> None:
        mock_run.return_value = (
            "task: Available tasks for this project:\n"
            "* test:       Run tests\n"
            "* lint:       Run linter\n"
            "* clean:all:  Clean everything\n"
        )
        result = _parse_taskfile_tasks()
        assert len(result) == 3
        # Should be sorted
        names = [t[0] for t in result]
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for main() entry point."""

    def test_dry_run_exits_zero(self) -> None:
        with patch("sys.argv", ["generate_command_reference", "--dry-run"]):
            result = main()
        assert result == 0

    def test_check_when_file_missing(self, tmp_path: Path) -> None:
        fake_out = tmp_path / "missing.md"
        with (
            patch("sys.argv", ["generate_command_reference", "--check"]),
            patch("generate_command_reference.OUTPUT", fake_out),
            patch("generate_command_reference.ROOT", tmp_path),
            patch("generate_command_reference._generate", return_value="# Fake\n"),
        ):
            result = main()
        assert result == 1

    def test_check_when_file_matches(self, tmp_path: Path) -> None:
        """--check should exit 0 when file matches generated content."""
        fake_content = "# Command Reference\nGenerated.\n"
        out = tmp_path / "commands.md"
        out.write_text(fake_content, encoding="utf-8")
        with (
            patch("sys.argv", ["generate_command_reference", "--check"]),
            patch("generate_command_reference.OUTPUT", out),
            patch("generate_command_reference.ROOT", tmp_path),
            patch("generate_command_reference._generate", return_value=fake_content),
        ):
            result = main()
        assert result == 0

    def test_generates_file(self, tmp_path: Path) -> None:
        fake_content = "# Command Reference\nGenerated.\n"
        out = tmp_path / "reference" / "commands.md"
        with (
            patch("sys.argv", ["generate_command_reference"]),
            patch("generate_command_reference.OUTPUT", out),
            patch("generate_command_reference.ROOT", tmp_path),
            patch("generate_command_reference._generate", return_value=fake_content),
        ):
            result = main()
        assert result == 0
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "# Command Reference" in content
