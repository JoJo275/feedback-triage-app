"""Unit tests for mkdocs-hooks/repo_links.py.

Tests the MkDocs build hook that rewrites repo-relative links to absolute
GitHub URLs.  Covers all public/private functions, all three link pattern
types (standard Markdown, HTML href, reference-style), and the
protected-region system (fenced code, inline code, HTML comments).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

# mkdocs-hooks/ is not an installed package — add it to sys.path so we can
# import the module directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "mkdocs-hooks"))

from repo_links import (
    _EXTENSIONLESS_FILES,
    _FENCED_RE,
    _HTML_COMMENT_RE,
    _HTML_HREF_RE,
    _INLINE_CODE_RE,
    _LINK_RE,
    _PLACEHOLDER_PREFIX,
    _PLACEHOLDER_SUFFIX,
    _REF_LINK_RE,
    HOOK_VERSION,
    _build_github_url,
    _is_likely_file,
    _protect,
    _resolve_and_rewrite,
    _restore,
    _split_target,
    on_page_markdown,
)

# ---------------------------------------------------------------------------
# Helpers — lightweight fakes for MkDocs types
# ---------------------------------------------------------------------------


def _make_page(src_path: str = "guide/getting-started.md") -> Any:
    """Create a minimal fake Page object with ``page.file.src_path``."""
    page = MagicMock()
    page.file.src_path = src_path
    return page


def _make_config(
    repo_url: str = "https://example.com/owner/repo",
    branch: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Create a minimal dict that behaves like ``MkDocsConfig``."""
    extra: dict[str, object] = {}
    if branch is not None:
        extra["repo_links_default_branch"] = branch
    if verbose:
        extra["repo_links_log"] = True

    return {
        "repo_url": repo_url,
        "extra": extra,
    }


def _make_files() -> Any:
    """Create a minimal fake Files object (unused by the hook)."""
    return MagicMock()


# ---------------------------------------------------------------------------
# HOOK_VERSION
# ---------------------------------------------------------------------------


class TestHookVersion:
    """Validate the version constant is well-formed."""

    def test_version_is_string(self) -> None:
        assert isinstance(HOOK_VERSION, str)

    def test_version_format(self) -> None:
        parts = HOOK_VERSION.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


# ---------------------------------------------------------------------------
# _is_likely_file
# ---------------------------------------------------------------------------


class TestIsLikelyFile:
    """Tests for the file-vs-directory heuristic."""

    def test_file_with_extension(self) -> None:
        assert _is_likely_file("pyproject.toml") is True

    def test_nested_file_with_extension(self) -> None:
        assert _is_likely_file("src/simple_python_boilerplate/__init__.py") is True

    def test_directory_no_extension(self) -> None:
        assert _is_likely_file("src/") is False
        assert _is_likely_file("docs") is False

    @pytest.mark.parametrize("name", sorted(_EXTENSIONLESS_FILES))
    def test_extensionless_known_files(self, name: str) -> None:
        assert _is_likely_file(name) is True

    def test_extensionless_unknown(self) -> None:
        assert _is_likely_file("somedir") is False

    def test_trailing_slash_stripped(self) -> None:
        # "LICENSE/" should be recognised as the file LICENSE
        assert _is_likely_file("LICENSE/") is True

    def test_dotfile(self) -> None:
        assert _is_likely_file(".gitignore") is True

    def test_nested_extensionless(self) -> None:
        assert _is_likely_file("path/to/Makefile") is True


# ---------------------------------------------------------------------------
# _build_github_url
# ---------------------------------------------------------------------------


class TestBuildGithubUrl:
    """Tests for GitHub URL construction."""

    def test_file_uses_blob(self) -> None:
        url = _build_github_url(
            "https://example.com/owner/repo", "pyproject.toml", "", "main"
        )
        assert url == "https://example.com/owner/repo/blob/main/pyproject.toml"

    def test_directory_uses_tree(self) -> None:
        url = _build_github_url("https://example.com/owner/repo", "src/", "", "main")
        assert url == "https://example.com/owner/repo/tree/main/src"

    def test_suffix_appended(self) -> None:
        url = _build_github_url(
            "https://example.com/owner/repo",
            "pyproject.toml",
            "?plain=1#L10",
            "main",
        )
        assert url == (
            "https://example.com/owner/repo/blob/main/pyproject.toml?plain=1#L10"
        )

    def test_custom_branch(self) -> None:
        url = _build_github_url(
            "https://example.com/owner/repo", "README.md", "", "develop"
        )
        assert url == "https://example.com/owner/repo/blob/develop/README.md"

    def test_extensionless_file_uses_blob(self) -> None:
        url = _build_github_url("https://example.com/owner/repo", "LICENSE", "", "main")
        assert url == "https://example.com/owner/repo/blob/main/LICENSE"

    def test_trailing_slash_stripped_for_tree(self) -> None:
        url = _build_github_url("https://example.com/owner/repo", "docs/", "", "main")
        assert url == "https://example.com/owner/repo/tree/main/docs"


# ---------------------------------------------------------------------------
# _split_target
# ---------------------------------------------------------------------------


class TestSplitTarget:
    """Tests for splitting link targets into (path, suffix)."""

    def test_plain_path(self) -> None:
        assert _split_target("../pyproject.toml") == ("../pyproject.toml", "")

    def test_fragment_only(self) -> None:
        assert _split_target("../README.md#usage") == ("../README.md", "#usage")

    def test_query_only(self) -> None:
        assert _split_target("../file.py?plain=1") == ("../file.py", "?plain=1")

    def test_query_and_fragment(self) -> None:
        assert _split_target("../file.py?plain=1#L10") == (
            "../file.py",
            "?plain=1#L10",
        )

    def test_empty_fragment(self) -> None:
        # Trailing # with no fragment name — still preserved.
        path, suffix = _split_target("../file.md#")
        assert path == "../file.md"
        assert suffix == "#"

    def test_multiple_hashes_in_fragment(self) -> None:
        # Only the first # splits.
        path, suffix = _split_target("../file.md#a#b")
        assert path == "../file.md"
        assert suffix == "#a#b"


# ---------------------------------------------------------------------------
# _resolve_and_rewrite
# ---------------------------------------------------------------------------


class TestResolveAndRewrite:
    """Tests for path resolution and rewrite logic."""

    REPO_URL = "https://example.com/owner/repo"

    def test_escapes_docs_rewrites(self) -> None:
        """A link from guide/ to ../../pyproject.toml escapes docs/."""
        result = _resolve_and_rewrite(
            "../../pyproject.toml", "guide", self.REPO_URL, "main"
        )
        assert result == ("https://example.com/owner/repo/blob/main/pyproject.toml")

    def test_stays_in_docs_returns_none(self) -> None:
        """A link from guide/ to ../index.md stays within docs/."""
        result = _resolve_and_rewrite("../index.md", "guide", self.REPO_URL, "main")
        assert result is None

    def test_preserves_fragment(self) -> None:
        result = _resolve_and_rewrite(
            "../../pyproject.toml#L5", "guide", self.REPO_URL, "main"
        )
        assert result is not None
        assert result.endswith("#L5")

    def test_preserves_query_and_fragment(self) -> None:
        result = _resolve_and_rewrite(
            "../../file.py?plain=1#L10", "guide", self.REPO_URL, "main"
        )
        assert result is not None
        assert "?plain=1#L10" in result

    def test_directory_trailing_slash(self) -> None:
        """Directories keep trailing slash → tree/ URL."""
        result = _resolve_and_rewrite("../../scripts/", "guide", self.REPO_URL, "main")
        assert result is not None
        assert "/tree/main/scripts" in result

    def test_deep_page_dir(self) -> None:
        """Page in a nested docs subdir."""
        result = _resolve_and_rewrite(
            "../../../pyproject.toml", "adr", self.REPO_URL, "main"
        )
        assert result == ("https://example.com/owner/repo/blob/main/pyproject.toml")

    def test_root_level_page(self) -> None:
        """Page at docs root — one ../ escapes docs/."""
        result = _resolve_and_rewrite("../Taskfile.yml", "", self.REPO_URL, "main")
        assert result == ("https://example.com/owner/repo/blob/main/Taskfile.yml")

    def test_same_dir_link_returns_none(self) -> None:
        """A link to a file in the same directory doesn't escape docs/."""
        result = _resolve_and_rewrite("./sibling.md", "guide", self.REPO_URL, "main")
        assert result is None


# ---------------------------------------------------------------------------
# Protected-region patterns (compiled regexes)
# ---------------------------------------------------------------------------


class TestProtectedPatterns:
    """Verify the regex patterns match expected content."""

    def test_fenced_code_block_backticks(self) -> None:
        block = "```python\nimport os\n```"
        assert _FENCED_RE.search(block) is not None

    def test_fenced_code_block_tildes(self) -> None:
        block = "~~~\nsome code\n~~~"
        assert _FENCED_RE.search(block) is not None

    def test_inline_code(self) -> None:
        assert _INLINE_CODE_RE.search("`some_code`") is not None

    def test_inline_code_no_match_empty(self) -> None:
        assert _INLINE_CODE_RE.search("``") is None

    def test_html_comment_single_line(self) -> None:
        assert _HTML_COMMENT_RE.search("<!-- comment -->") is not None

    def test_html_comment_multiline(self) -> None:
        comment = "<!--\n  multi\n  line\n-->"
        assert _HTML_COMMENT_RE.search(comment) is not None


# ---------------------------------------------------------------------------
# Link patterns (compiled regexes)
# ---------------------------------------------------------------------------


class TestLinkPatterns:
    """Verify the link-matching regexes."""

    # ---- Standard Markdown links ----

    def test_link_re_basic(self) -> None:
        m = _LINK_RE.search("[text](../path)")
        assert m is not None
        assert m.group(1) == "text"
        assert m.group(2) == "../path"

    def test_link_re_with_fragment(self) -> None:
        m = _LINK_RE.search("[text](../file.md#anchor)")
        assert m is not None
        assert m.group(2) == "../file.md#anchor"

    def test_link_re_skips_images(self) -> None:
        """Image links (![alt](..)) should NOT match."""
        assert _LINK_RE.search("![alt](../image.png)") is None

    def test_link_re_no_match_non_relative(self) -> None:
        assert _LINK_RE.search("[text](https://example.com)") is None

    # ---- HTML href links ----

    def test_html_href_double_quotes(self) -> None:
        m = _HTML_HREF_RE.search('<a href="../file.md">')
        assert m is not None
        assert m.group(3) == "../file.md"

    def test_html_href_single_quotes(self) -> None:
        m = _HTML_HREF_RE.search("<a href='../file.md'>")
        assert m is not None
        assert m.group(3) == "../file.md"

    def test_html_href_no_match_absolute(self) -> None:
        assert _HTML_HREF_RE.search('<a href="https://example.com">') is None

    # ---- Reference-style links ----

    def test_ref_link_basic(self) -> None:
        m = _REF_LINK_RE.search("[myref]: ../path/to/file.md")
        assert m is not None
        assert m.group(3) == "../path/to/file.md"

    def test_ref_link_with_title(self) -> None:
        m = _REF_LINK_RE.search('[myref]: ../file.md "My Title"')
        assert m is not None
        assert m.group(3) == "../file.md"
        assert m.group(4) is not None
        assert "My Title" in m.group(4)

    def test_ref_link_no_match_non_relative(self) -> None:
        assert _REF_LINK_RE.search("[ref]: https://example.com") is None


# ---------------------------------------------------------------------------
# _protect / _restore
# ---------------------------------------------------------------------------


class TestProtectRestore:
    """Tests for the placeholder protection system."""

    def test_round_trip_preserves_content(self) -> None:
        md = "text `code` more\n```\nblock\n```\nend"
        protected, placeholders = _protect(md)
        restored = _restore(protected, placeholders)
        assert restored == md

    def test_fenced_block_replaced(self) -> None:
        md = "before\n```\ncode\n```\nafter"
        protected, placeholders = _protect(md)
        assert "```" not in protected
        assert len(placeholders) == 1

    def test_inline_code_replaced(self) -> None:
        md = "say `hello` world"
        protected, placeholders = _protect(md)
        assert "`hello`" not in protected
        assert len(placeholders) == 1

    def test_html_comment_replaced(self) -> None:
        md = "text <!-- hidden --> more"
        protected, placeholders = _protect(md)
        assert "<!--" not in protected
        assert len(placeholders) == 1

    def test_multiple_regions(self) -> None:
        md = "`a` and `b` and <!-- c -->"
        _protected, placeholders = _protect(md)
        assert len(placeholders) == 3

    def test_placeholder_format(self) -> None:
        md = "`code`"
        _protected, placeholders = _protect(md)
        key = next(iter(placeholders))
        assert key.startswith(_PLACEHOLDER_PREFIX)
        assert key.endswith(_PLACEHOLDER_SUFFIX)

    def test_empty_input(self) -> None:
        protected, placeholders = _protect("")
        assert protected == ""
        assert placeholders == {}

    def test_no_protected_regions(self) -> None:
        md = "just plain text with [a link](../something)"
        protected, placeholders = _protect(md)
        assert protected == md
        assert placeholders == {}

    def test_restore_with_empty_placeholders(self) -> None:
        assert _restore("unchanged", {}) == "unchanged"


# ---------------------------------------------------------------------------
# on_page_markdown — integration-level tests of the full hook
# ---------------------------------------------------------------------------


class TestOnPageMarkdown:
    """Tests for the main entry point."""

    REPO_URL = "https://example.com/owner/repo"

    def _run(
        self,
        markdown: str,
        *,
        src_path: str = "guide/getting-started.md",
        repo_url: str | None = None,
        branch: str | None = None,
    ) -> str:
        return on_page_markdown(
            markdown,
            page=_make_page(src_path),
            config=_make_config(repo_url or self.REPO_URL, branch=branch),
            files=_make_files(),
        )

    # ---- No repo_url → pass-through ----

    def test_no_repo_url_returns_unchanged(self) -> None:
        md = "[text](../../pyproject.toml)"
        result = on_page_markdown(
            md,
            page=_make_page(),
            config=_make_config(repo_url=""),
            files=_make_files(),
        )
        assert result == md

    # ---- Standard Markdown links ----

    def test_rewrites_standard_link(self) -> None:
        result = self._run("[cfg](../../pyproject.toml)")
        assert result == (
            "[cfg](https://example.com/owner/repo/blob/main/pyproject.toml)"
        )

    def test_standard_link_with_fragment(self) -> None:
        result = self._run("[cfg](../../pyproject.toml#L5)")
        assert "#L5" in result
        assert "blob/main/pyproject.toml" in result

    def test_standard_link_stays_in_docs(self) -> None:
        result = self._run("[index](../index.md)")
        assert result == "[index](../index.md)"

    def test_standard_link_skips_image(self) -> None:
        md = "![logo](../../assets/logo.png)"
        assert self._run(md) == md

    def test_standard_link_directory(self) -> None:
        result = self._run("[scripts](../../scripts/)")
        assert "/tree/main/scripts" in result

    # ---- HTML href links ----

    def test_rewrites_html_href(self) -> None:
        md = '<a href="../../pyproject.toml">config</a>'
        result = self._run(md)
        assert "blob/main/pyproject.toml" in result
        assert "<a" in result

    def test_html_href_stays_in_docs(self) -> None:
        md = '<a href="../index.md">home</a>'
        assert self._run(md) == md

    # ---- Reference-style links ----

    def test_rewrites_ref_link(self) -> None:
        md = "[cfg]: ../../pyproject.toml"
        result = self._run(md)
        assert "blob/main/pyproject.toml" in result
        assert "[cfg]:" in result

    def test_ref_link_with_title(self) -> None:
        md = '[cfg]: ../../pyproject.toml "Project Config"'
        result = self._run(md)
        assert "blob/main/pyproject.toml" in result
        assert '"Project Config"' in result

    def test_ref_link_stays_in_docs(self) -> None:
        md = "[idx]: ../index.md"
        assert self._run(md) == md

    # ---- Protected regions ----

    def test_link_in_fenced_code_not_rewritten(self) -> None:
        md = "```\n[text](../../file.md)\n```"
        assert self._run(md) == md

    def test_link_in_inline_code_not_rewritten(self) -> None:
        md = "`[text](../../file.md)`"
        assert self._run(md) == md

    def test_link_in_html_comment_not_rewritten(self) -> None:
        md = "<!-- [text](../../file.md) -->"
        assert self._run(md) == md

    def test_mixed_protected_and_real_links(self) -> None:
        md = "`[skip](../../a.md)` and [rewrite](../../pyproject.toml)"
        result = self._run(md)
        # The inline-code link is untouched.
        assert "`[skip](../../a.md)`" in result
        # The real link is rewritten.
        assert "blob/main/pyproject.toml" in result

    # ---- Custom branch ----

    def test_custom_branch(self) -> None:
        result = self._run("[f](../../pyproject.toml)", branch="develop")
        assert "/blob/develop/pyproject.toml" in result

    # ---- Multiple links in one document ----

    def test_multiple_links_rewritten(self) -> None:
        md = "[a](../../pyproject.toml)\n[b](../../Taskfile.yml)\n[c](../index.md)\n"
        result = self._run(md)
        assert "blob/main/pyproject.toml" in result
        assert "blob/main/Taskfile.yml" in result
        # Internal link kept.
        assert "[c](../index.md)" in result

    # ---- Page at different depths ----

    def test_page_at_docs_root(self) -> None:
        result = self._run("[cfg](../pyproject.toml)", src_path="index.md")
        assert "blob/main/pyproject.toml" in result

    def test_page_in_nested_subdir(self) -> None:
        result = self._run(
            "[cfg](../../../pyproject.toml)", src_path="adr/deep/page.md"
        )
        assert "blob/main/pyproject.toml" in result

    # ---- Trailing-slash repo_url ----

    def test_trailing_slash_repo_url_stripped(self) -> None:
        result = self._run(
            "[cfg](../../pyproject.toml)",
            repo_url="https://example.com/owner/repo/",
        )
        # Should not produce double slash before blob/.
        assert "repo//blob" not in result
        assert "blob/main/pyproject.toml" in result

    # ---- Edge cases ----

    def test_empty_markdown(self) -> None:
        assert self._run("") == ""

    def test_no_links(self) -> None:
        md = "Just some text with no links at all."
        assert self._run(md) == md

    def test_query_string_preserved(self) -> None:
        result = self._run("[f](../../file.py?plain=1#L10)")
        assert "?plain=1#L10" in result
