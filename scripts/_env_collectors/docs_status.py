"""Documentation status collector — MkDocs config, broken links, ADRs.

Discovers:
- MkDocs configuration and build readiness
- Documentation file inventory
- ADR count and status
- Broken internal links (basic check)
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from _env_collectors._base import BaseCollector

_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


def _parse_mkdocs_config(repo_root: Path) -> dict[str, Any]:
    """Parse mkdocs.yml for config info."""
    mkdocs_file = repo_root / "mkdocs.yml"
    if not mkdocs_file.is_file():
        return {"found": False}

    try:
        content = mkdocs_file.read_text(encoding="utf-8")
        site_name = ""
        theme = ""

        name_match = re.search(
            r"^site_name:\s*['\"]?(.+?)['\"]?\s*$", content, re.MULTILINE
        )
        if name_match:
            site_name = name_match.group(1).strip()

        theme_match = re.search(
            r"name:\s*['\"]?(material|readthedocs|mkdocs)['\"]?", content
        )
        if theme_match:
            theme = theme_match.group(1)

        # Count nav entries
        nav_count = len(re.findall(r"^\s+-\s+", content, re.MULTILINE))

        # Check for plugins
        plugins = re.findall(r"^\s+-\s+(\w+)", content, re.MULTILINE)

        return {
            "found": True,
            "site_name": site_name,
            "theme": theme,
            "nav_entries": nav_count,
            "plugins": plugins[:10],
        }
    except OSError:
        return {"found": False}


def _scan_docs_directory(repo_root: Path) -> dict[str, Any]:
    """Scan docs/ directory for inventory."""
    docs_dir = repo_root / "docs"
    if not docs_dir.is_dir():
        return {"found": False, "files": [], "total_files": 0}

    md_files: list[str] = []
    other_files: list[str] = []
    total_size = 0

    try:
        for f in docs_dir.rglob("*"):
            if f.is_file():
                rel = str(f.relative_to(repo_root))
                total_size += f.stat().st_size
                if f.suffix == ".md":
                    md_files.append(rel)
                else:
                    other_files.append(rel)
    except OSError:
        pass

    return {
        "found": True,
        "markdown_files": len(md_files),
        "other_files": len(other_files),
        "total_files": len(md_files) + len(other_files),
        "total_size_kb": round(total_size / 1024, 1),
    }


def _scan_adrs(repo_root: Path) -> dict[str, Any]:
    """Scan ADR directory for architecture decision records."""
    adr_dir = repo_root / "docs" / "adr"
    if not adr_dir.is_dir():
        return {"found": False, "count": 0, "adrs": []}

    adrs: list[dict[str, str]] = []
    try:
        for f in sorted(adr_dir.glob("*.md")):
            if f.name.startswith("_") or f.name == "README.md":
                continue
            # Extract title from first heading
            title = f.stem
            try:
                content = f.read_text(encoding="utf-8")
                heading = re.search(r"^#\s+(.+)", content, re.MULTILINE)
                if heading:
                    title = heading.group(1).strip()
            except OSError:
                pass
            adrs.append({"file": f.name, "title": title})
    except OSError:
        pass

    return {
        "found": True,
        "count": len(adrs),
        "adrs": adrs[:20],  # Show first 20
        "total": len(adrs),
    }


def _check_broken_links(repo_root: Path) -> list[dict[str, str]]:
    """Improved check for broken internal markdown links.

    Reduces false positives by handling:
    - MkDocs directory indexes (``dir/`` → ``dir/index.md`` or ``dir/README.md``)
    - Auto ``.md`` extension appending (MkDocs convention)
    - Jinja2 template variables (``{{ var }}``)
    - Code blocks and inline code (protected from scanning)
    - Markdown reference-style links
    - Image links and badges
    - Anchor-only links and root-relative paths
    - Links to files outside docs/ resolved relative to repo root
    """
    docs_dir = repo_root / "docs"
    if not docs_dir.is_dir():
        return []

    broken: list[dict[str, str]] = []

    # Pre-compile patterns
    # Strip fenced code blocks (``` or ~~~) to avoid false positives
    code_block_re = re.compile(r"^(`{3,}|~{3,}).*?^\1", re.MULTILINE | re.DOTALL)
    # Strip inline code
    inline_code_re = re.compile(r"`[^`\n]+`")
    # Strip HTML comments
    html_comment_re = re.compile(r"<!--.*?-->", re.DOTALL)
    # Standard markdown links: [text](target)
    link_re = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
    # Reference-style link definitions: [label]: url
    ref_link_re = re.compile(r"^\[([^\]]+)\]:\s*(.+)$", re.MULTILINE)

    # Patterns for targets to skip
    skip_prefixes = (
        "http://",
        "https://",
        "#",
        "mailto:",
        "tel:",
        "{{",
        "{%",
        "javascript:",
    )

    try:
        for md_file in docs_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8", errors="replace")

            # Protect code regions from scanning
            cleaned = code_block_re.sub("", content)
            cleaned = inline_code_re.sub("", cleaned)
            cleaned = html_comment_re.sub("", cleaned)

            # Collect all link targets from both inline and reference links
            link_targets: list[tuple[str, str]] = [
                (m.group(1), m.group(2)) for m in link_re.finditer(cleaned)
            ]
            link_targets.extend(
                (m.group(1), m.group(2).strip()) for m in ref_link_re.finditer(cleaned)
            )

            for text, raw_target in link_targets:
                target = raw_target.strip()

                # Skip external URLs, anchors, templates, etc.
                if any(target.lower().startswith(p) for p in skip_prefixes):
                    continue
                # Skip bare anchor references (e.g., [text](#anchor))
                if target.startswith("#"):
                    continue
                # Skip targets with Jinja2 / template syntax inside
                if "{{" in target or "{%" in target:
                    continue
                # Skip absolute paths (MkDocs resolves these differently)
                if target.startswith("/"):
                    continue

                # Strip query string and anchor from target
                target_path = target.split("?")[0].split("#")[0].strip()
                if not target_path:
                    continue

                # Resolve relative to the markdown file's directory
                resolved = (md_file.parent / target_path).resolve()

                if _link_target_exists(resolved, repo_root):
                    continue

                # For links going above docs/ (e.g., ../pyproject.toml),
                # also try resolving from repo root
                if target_path.startswith(".."):
                    # Walk up from the file to see if it exists relative to repo
                    from_repo = (
                        repo_root
                        / "docs"
                        / md_file.relative_to(docs_dir).parent
                        / target_path
                    ).resolve()
                    if _link_target_exists(from_repo, repo_root):
                        continue

                broken.append(
                    {
                        "file": str(md_file.relative_to(repo_root)),
                        "link": raw_target,
                        "text": text[:50],
                    }
                )
    except OSError:
        pass

    return broken[:30]  # Limit results


def _link_target_exists(resolved: Path, repo_root: Path) -> bool:
    """Check if a resolved link target exists with MkDocs-aware fallbacks.

    Handles:
    - Direct file existence
    - Directory with index.md or README.md (MkDocs directory indexes)
    - Missing .md extension (``page`` → ``page.md``)
    - Path outside the repo (reject — shouldn't resolve there)
    """
    # Safety: don't resolve outside repo
    try:
        resolved.relative_to(repo_root)
    except ValueError:
        return False

    # Direct existence
    if resolved.exists():
        return True

    # Try appending .md (MkDocs convention: ``page`` → ``page.md``)
    if not resolved.suffix and resolved.with_suffix(".md").is_file():
        return True

    # Directory index fallback: ``dir/`` → ``dir/index.md`` or ``dir/README.md``
    if resolved.is_dir():
        if (resolved / "index.md").is_file():
            return True
        if (resolved / "README.md").is_file():
            return True

    # If the resolved path is a directory name without trailing slash,
    # check if dir/index.md exists
    dir_path = resolved
    if not dir_path.suffix and dir_path.is_dir():
        if (dir_path / "index.md").is_file():
            return True
        if (dir_path / "README.md").is_file():
            return True

    return False


class DocsStatusCollector(BaseCollector):
    """Collect documentation status and health information."""

    name = "docs_status"
    timeout = 15.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().STANDARD

    def collect(self) -> dict[str, Any]:
        from _imports import find_repo_root

        repo_root = find_repo_root()

        mkdocs = _parse_mkdocs_config(repo_root)
        docs_scan = _scan_docs_directory(repo_root)
        adrs = _scan_adrs(repo_root)
        broken_links = _check_broken_links(repo_root)
        mkdocs_available = shutil.which("mkdocs") is not None

        return {
            "mkdocs": mkdocs,
            "mkdocs_available": mkdocs_available,
            "docs": docs_scan,
            "adrs": adrs,
            "broken_links": broken_links,
            "broken_link_count": len(broken_links),
        }
