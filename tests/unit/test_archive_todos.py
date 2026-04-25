"""Unit tests for scripts/archive_todos.py helper functions."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from archive_todos import (
    _build_archive_content,
    _collect_completed_blocks,
    _remove_blocks,
)

# ---------------------------------------------------------------------------
# _collect_completed_blocks
# ---------------------------------------------------------------------------


class TestCollectCompletedBlocks:
    """Tests for _collect_completed_blocks."""

    def test_no_completed_items(self) -> None:
        text = "- [ ] Not done\n- [ ] Also not done\n"
        assert _collect_completed_blocks(text) == []

    def test_single_completed_item(self) -> None:
        text = "- [x] Done task\n- [ ] Not done\n"
        result = _collect_completed_blocks(text)
        assert result == ["- [x] Done task"]

    def test_uppercase_x(self) -> None:
        text = "- [X] Done with uppercase\n"
        result = _collect_completed_blocks(text)
        assert result == ["- [X] Done with uppercase"]

    def test_multiple_completed_items(self) -> None:
        text = "- [x] First\n- [x] Second\n- [ ] Third\n"
        result = _collect_completed_blocks(text)
        assert result == ["- [x] First", "- [x] Second"]

    def test_completed_item_with_sub_items(self) -> None:
        text = "- [x] Parent task\n  - Sub-item 1\n  - Sub-item 2\n- [ ] Other\n"
        result = _collect_completed_blocks(text)
        assert len(result) == 1
        assert "Parent task" in result[0]
        assert "Sub-item 1" in result[0]
        assert "Sub-item 2" in result[0]

    def test_completed_item_with_blank_line_before_sub_item(self) -> None:
        """Blank line between parent and indented child should still group."""
        text = "- [x] Parent task\n\n  - Sub-item after blank\n- [ ] Other\n"
        result = _collect_completed_blocks(text)
        assert len(result) == 1
        assert "Sub-item after blank" in result[0]

    def test_sub_items_with_four_space_indent(self) -> None:
        text = "- [x] Parent\n    - Deep sub-item\n- [ ] Next\n"
        result = _collect_completed_blocks(text)
        assert len(result) == 1
        assert "Deep sub-item" in result[0]

    def test_empty_text(self) -> None:
        assert _collect_completed_blocks("") == []

    def test_unchecked_items_not_captured(self) -> None:
        text = "- [ ] Unchecked\n  - Sub-item\n"
        assert _collect_completed_blocks(text) == []


# ---------------------------------------------------------------------------
# _remove_blocks
# ---------------------------------------------------------------------------


class TestRemoveBlocks:
    """Tests for _remove_blocks."""

    def test_remove_single_block(self) -> None:
        text = "- [x] Done\n- [ ] Keep\n"
        result = _remove_blocks(text, ["- [x] Done"])
        assert result == "- [ ] Keep\n"

    def test_remove_preserves_surrounding_content(self) -> None:
        text = "# Header\n\n- [x] Remove me\n\n## Footer\n"
        result = _remove_blocks(text, ["- [x] Remove me"])
        assert "# Header" in result
        assert "## Footer" in result
        assert "Remove me" not in result

    def test_remove_collapses_triple_blank_lines(self) -> None:
        text = "Before\n\n- [x] Gone\n\n\nAfter\n"
        result = _remove_blocks(text, ["- [x] Gone"])
        # Should not have 3+ consecutive newlines
        assert "\n\n\n" not in result

    def test_remove_multi_line_block(self) -> None:
        block = "- [x] Parent\n  - Child"
        text = f"Before\n{block}\nAfter\n"
        result = _remove_blocks(text, [block])
        assert "Parent" not in result
        assert "Child" not in result
        assert "Before" in result
        assert "After" in result

    def test_remove_only_first_occurrence(self) -> None:
        """If the same block appears twice, only the first is removed."""
        text = "- [x] Dup\n- [x] Dup\n"
        result = _remove_blocks(text, ["- [x] Dup"])
        assert result.count("- [x] Dup") == 1

    def test_special_characters_in_block(self) -> None:
        """Regex metacharacters in blocks should not cause mismatches."""
        block = "- [x] Fix bug (issue #42)"
        text = f"{block}\n- [ ] Other\n"
        result = _remove_blocks(text, [block])
        assert "Fix bug" not in result
        assert "Other" in result


# ---------------------------------------------------------------------------
# _build_archive_content
# ---------------------------------------------------------------------------


class TestBuildArchiveContent:
    """Tests for _build_archive_content."""

    def test_creates_month_section_when_missing(self) -> None:
        archive = "# Archive\n"
        result = _build_archive_content(archive, ["- [x] Done"], "## February 2026")
        assert "## February 2026" in result
        assert "### Completed" in result
        assert "- [x] Done" in result

    def test_appends_to_existing_month_section(self) -> None:
        archive = "# Archive\n\n## February 2026\n\n### Completed\n\n- [x] Old item\n"
        result = _build_archive_content(archive, ["- [x] New item"], "## February 2026")
        assert "- [x] Old item" in result
        assert "- [x] New item" in result

    def test_new_items_appear_after_completed_header(self) -> None:
        archive = "# Archive\n\n## February 2026\n\n### Completed\n\n"
        result = _build_archive_content(
            archive, ["- [x] Item A", "- [x] Item B"], "## February 2026"
        )
        completed_pos = result.index("### Completed")
        item_a_pos = result.index("- [x] Item A")
        item_b_pos = result.index("- [x] Item B")
        assert item_a_pos > completed_pos
        assert item_b_pos > item_a_pos

    def test_ensures_trailing_newline(self) -> None:
        archive = "# Archive"  # No trailing newline
        result = _build_archive_content(archive, ["- [x] Done"], "## March 2026")
        assert result.endswith("\n")

    def test_multiple_blocks_joined(self) -> None:
        archive = "# Archive\n"
        blocks = ["- [x] First", "- [x] Second"]
        result = _build_archive_content(archive, blocks, "## April 2026")
        assert "- [x] First\n- [x] Second" in result


# ---------------------------------------------------------------------------
# Integration-style: collect + remove round-trip
# ---------------------------------------------------------------------------


class TestCollectAndRemoveRoundTrip:
    """Verify that collected blocks can be cleanly removed."""

    @pytest.mark.parametrize(
        "todo_text",
        [
            "- [x] Simple\n- [ ] Keep\n",
            "- [x] Parent\n  - Child\n- [ ] Keep\n",
            "- [x] With special (chars) #1\n- [ ] Keep\n",
            "- [x] A\n- [x] B\n- [ ] C\n",
        ],
        ids=["simple", "sub-items", "special-chars", "multiple"],
    )
    def test_round_trip(self, todo_text: str) -> None:
        blocks = _collect_completed_blocks(todo_text)
        assert len(blocks) >= 1
        cleaned = _remove_blocks(todo_text, blocks)
        # All completed blocks should be gone
        for block in blocks:
            assert block not in cleaned
        # Unchecked items should remain
        assert "- [ ] Keep" in cleaned or "- [ ] C" in cleaned
