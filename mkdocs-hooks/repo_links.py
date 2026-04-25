"""MkDocs hook: rewrite repo-relative links to absolute GitHub URLs.

Links in ``docs/`` that point outside the docs directory (e.g.
``../../pyproject.toml``) work correctly when browsing on GitHub, but MkDocs
can only resolve links to files within ``docs_dir``.  On the deployed site
these relative links would 404.

This hook intercepts the ``on_page_markdown`` event and rewrites them at
build time to absolute GitHub URLs, so they work in both contexts without
changing any source Markdown files.

How it works:
    1. Protects code blocks, inline code, and HTML comments by replacing
       them with temporary placeholders (so example links in docs are
       never accidentally rewritten)
    2. For each page, finds Markdown links whose target starts with ``../``
       — including standard ``[text](../path)``, HTML ``<a href="..">``,
       and reference-style ``[ref]: ../path`` definitions
    3. Resolves the path relative to the page's location within ``docs/``
    4. If the resolved path escapes ``docs/`` (normalised path starts with
       ``..``), rewrites it to ``{repo_url}/blob/main/{path}`` (files) or
       ``tree/main/`` (directories)
    5. Restores all protected regions

Template users only need to set ``repo_url`` in ``mkdocs.yml`` — all
repo-relative links will point to the correct GitHub repository
automatically.

Configuration (optional ``extra`` keys in ``mkdocs.yml``)::

    extra:
      repo_links_default_branch: develop   # default: main
      repo_links_log: true                 # emit INFO per rewrite

Reference:
    https://www.mkdocs.org/user-guide/configuration/#hooks
"""

# TODO (template users): If your default branch is not ``main``, either
#   set ``extra.repo_links_default_branch`` in ``mkdocs.yml`` or change
#   ``_DEFAULT_BRANCH`` below.

from __future__ import annotations

import logging
import posixpath
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

# Semantic version of this hook — bump when behaviour changes.
HOOK_VERSION = "1.4.0"

__all__ = ["on_page_markdown"]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_BRANCH = "main"

log = logging.getLogger("mkdocs.hooks.repo_links")

# Files without extensions that should use blob/ (not tree/).
# TODO (template users): If your repo contains extensionless files beyond
#   these common ones, add them here so the hook generates ``blob/`` URLs
#   instead of ``tree/``.
_EXTENSIONLESS_FILES: frozenset[str] = frozenset(
    {
        "Brewfile",
        "Containerfile",
        "Dockerfile",
        "Gemfile",
        "Justfile",
        "LICENSE",
        "Makefile",
        "Procfile",
        "Rakefile",
        "Taskfile",
        "Vagrantfile",
    }
)

# ---------------------------------------------------------------------------
# Protected-region patterns — matched BEFORE link rewriting
# ---------------------------------------------------------------------------

# These patterns identify regions of the Markdown source that should never
# be processed by the link rewriter: fenced code blocks, inline code spans,
# and HTML comments.  They are temporarily replaced with null-byte-delimited
# placeholders and restored after all link rewrites are complete.

# Fenced code blocks: opening ``` or ~~~ (3+ chars) through matching close.
_FENCED_RE = re.compile(
    r"^(`{3,}|~{3,})[^\n]*\n[\s\S]*?\n\1[ \t]*$",
    re.MULTILINE,
)

# Inline code spans: `content` (no newlines allowed inside).
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")

# HTML comments: <!-- ... --> (may span multiple lines).
_HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")

# ---------------------------------------------------------------------------
# Link patterns — matched AFTER protected regions are removed
# ---------------------------------------------------------------------------

# Matches standard Markdown links whose target starts with ../
# Captures: [link text](../some/path) and [link text](../some/path#anchor)
# The negative lookbehind (?<!!) skips image links: ![alt](../path).
_LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\((\.\./[^)]*)\)")

# HTML <a href=".."> links whose href starts with ../
# Captures the href value.  Works with single or double quotes.
_HTML_HREF_RE = re.compile(
    r"""(<a\s[^>]*?href\s*=\s*)(["'])(\.\.\/[^"']*)\2([^>]*>)""",
    re.IGNORECASE,
)

# Reference-style link definitions: [ref]: ../path
# Captures: label prefix, path, and optional title.
_REF_LINK_RE = re.compile(
    r"""^(\[([^\]]+)\]:\s*)(\.\.\/\S+)([ \t]+"[^"]*")?[ \t]*$""",
    re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Placeholder constants for protected-region replacement
# ---------------------------------------------------------------------------

_PLACEHOLDER_PREFIX = "\x00PROT"
_PLACEHOLDER_SUFFIX = "\x00"


def _is_likely_file(path: str) -> bool:
    """Heuristic: determine if *path* targets a file rather than a directory.

    A path is considered a file if its basename contains a dot (extension)
    or matches a known extensionless filename like ``LICENSE``.
    """
    basename = posixpath.basename(path.rstrip("/"))
    return "." in basename or basename in _EXTENSIONLESS_FILES


def _build_github_url(
    repo_url: str,
    repo_path: str,
    suffix: str,
    branch: str,
) -> str:
    """Build a GitHub URL for a repo-root-relative *repo_path*.

    Args:
        repo_url: Repository base URL (no trailing slash).
        repo_path: Path relative to the repository root.
        suffix: Optional query string and/or fragment to append (e.g.
            ``?plain=1#L10`` or ``#my-heading``).
        branch: Git branch name (e.g. ``main``).

    Returns:
        Absolute GitHub URL using ``blob/`` (file) or ``tree/`` (directory).
    """
    clean = repo_path.rstrip("/")
    kind = "blob" if _is_likely_file(clean) else "tree"
    return f"{repo_url}/{kind}/{branch}/{clean}{suffix}"


def _split_target(target: str) -> tuple[str, str]:
    """Split a link target into ``(path, suffix)``.

    *suffix* contains the query string and/or fragment (e.g.
    ``?plain=1#L10``).
    """
    path = target
    query = ""
    fragment = ""
    if "?" in path:
        path, query_and_rest = path.split("?", 1)
        if "#" in query_and_rest:
            q, frag = query_and_rest.split("#", 1)
            query = f"?{q}"
            fragment = f"#{frag}"
        else:
            query = f"?{query_and_rest}"
    elif "#" in path:
        path, frag = path.split("#", 1)
        fragment = f"#{frag}"
    return path, query + fragment


def _resolve_and_rewrite(
    target: str,
    page_dir: str,
    repo_url: str,
    branch: str,
) -> str | None:
    """Resolve a relative *target* and return a GitHub URL if it escapes docs/.

    Returns ``None`` if the resolved path stays within ``docs/`` (i.e. should
    not be rewritten).
    """
    path, suffix = _split_target(target)
    resolved = posixpath.normpath(posixpath.join(page_dir, path))
    if not resolved.startswith(".."):
        return None

    repo_path = re.sub(r"^(\.\./)+", "", resolved)
    if path.endswith("/"):
        repo_path += "/"

    return _build_github_url(repo_url, repo_path, suffix, branch)


# ---------------------------------------------------------------------------
# Protected-region helpers
# ---------------------------------------------------------------------------


def _protect(markdown: str) -> tuple[str, dict[str, str]]:
    """Replace code blocks, inline code, and HTML comments with placeholders.

    Returns the modified text and a mapping of placeholder → original content.
    Processing order matters: fenced code blocks first (they may contain
    inline backticks), then inline code, then HTML comments.
    """
    placeholders: dict[str, str] = {}
    counter = 0

    def _sub(match: re.Match[str]) -> str:
        nonlocal counter
        key = f"{_PLACEHOLDER_PREFIX}{counter}{_PLACEHOLDER_SUFFIX}"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    markdown = _FENCED_RE.sub(_sub, markdown)
    markdown = _INLINE_CODE_RE.sub(_sub, markdown)
    markdown = _HTML_COMMENT_RE.sub(_sub, markdown)
    return markdown, placeholders


def _restore(text: str, placeholders: dict[str, str]) -> str:
    """Restore all placeholders with their original content."""
    for key, original in placeholders.items():
        text = text.replace(key, original)
    return text


def on_page_markdown(
    markdown: str,
    *,
    page: Page,
    config: MkDocsConfig,
    files: Files,  # required by MkDocs hook API but unused here
    **kwargs: object,
) -> str:
    """Rewrite repo-relative links to absolute GitHub URLs.

    Called by MkDocs for every page *before* the Markdown-to-HTML conversion.
    Only links whose resolved path escapes ``docs/`` are rewritten; internal
    cross-references are left untouched.

    Protected regions (fenced code blocks, inline code spans, HTML comments)
    are excluded from processing so that example links in documentation are
    never accidentally rewritten.
    """
    repo_url: str = config.get("repo_url", "").rstrip("/")
    if not repo_url:
        log.debug(
            "[repo_links] %s: no repo_url configured — skipping",
            page.file.src_path,
        )
        return markdown

    extra: dict[str, object] = config.get("extra", {}) or {}
    branch: str = str(extra.get("repo_links_default_branch", _DEFAULT_BRANCH))
    verbose: bool = bool(extra.get("repo_links_log", False))

    page_dir = posixpath.dirname(page.file.src_path)
    rewrite_count = 0

    # ── Protect code blocks and comments ─────────────────────
    markdown, placeholders = _protect(markdown)

    # ── Standard Markdown links ──────────────────────────────
    def _rewrite_md(match: re.Match[str]) -> str:
        nonlocal rewrite_count
        text = match.group(1)
        target = match.group(2)

        url = _resolve_and_rewrite(target, page_dir, repo_url, branch)
        if url is None:
            return match.group(0)

        rewrite_count += 1
        if verbose:
            log.info(
                "[repo_links] %s: %s -> %s",
                page.file.src_path,
                target,
                url,
            )
        return f"[{text}]({url})"

    markdown = _LINK_RE.sub(_rewrite_md, markdown)

    # ── HTML <a href> links ──────────────────────────────────
    def _rewrite_html(match: re.Match[str]) -> str:
        nonlocal rewrite_count
        prefix = match.group(1)  # <a ... href=
        quote = match.group(2)  # " or '
        target = match.group(3)  # ../some/path
        tail = match.group(4)  # ... >

        url = _resolve_and_rewrite(target, page_dir, repo_url, branch)
        if url is None:
            return match.group(0)

        rewrite_count += 1
        if verbose:
            log.info(
                "[repo_links] %s: href %s -> %s",
                page.file.src_path,
                target,
                url,
            )
        return f"{prefix}{quote}{url}{quote}{tail}"

    markdown = _HTML_HREF_RE.sub(_rewrite_html, markdown)

    # ── Reference-style link definitions ─────────────────────
    def _rewrite_ref(match: re.Match[str]) -> str:
        nonlocal rewrite_count
        prefix = match.group(1)  # [label]:
        target = match.group(3)  # ../some/path
        title = match.group(4) or ""  # optional "title"

        url = _resolve_and_rewrite(target, page_dir, repo_url, branch)
        if url is None:
            return match.group(0)

        rewrite_count += 1
        if verbose:
            log.info(
                "[repo_links] %s: ref %s -> %s",
                page.file.src_path,
                target,
                url,
            )
        return f"{prefix}{url}{title}"

    markdown = _REF_LINK_RE.sub(_rewrite_ref, markdown)

    # ── Restore protected regions ────────────────────────────
    markdown = _restore(markdown, placeholders)

    if rewrite_count and verbose:
        log.info(
            "[repo_links] %s: rewrote %d link(s)",
            page.file.src_path,
            rewrite_count,
        )

    return markdown
