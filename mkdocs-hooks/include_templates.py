"""MkDocs hook: force-include docs/templates/ on all MkDocs versions.

MkDocs 1.6 introduced built-in default exclusions for certain directory
names, including ``templates/``.  The ``!templates/`` negation in
``exclude_docs`` overrides this, but that negation syntax is
MkDocs 1.6-specific and may not work on earlier versions.

This hook provides a version-agnostic workaround: it uses the
``on_files`` event to re-add any ``templates/`` files that MkDocs
excluded from the collection.  This works on MkDocs 1.5 (where
templates/ is never excluded, so the hook is a no-op) and MkDocs 1.6+
(where the hook catches and reverses the default exclusion).

Configuration (optional ``extra`` key in ``mkdocs.yml``)::

    extra:
      include_templates: false   # Set to false to disable this hook

Reference:
    https://www.mkdocs.org/user-guide/configuration/#hooks
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

HOOK_VERSION = "1.1.0"

__all__ = ["on_files"]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

log = logging.getLogger("mkdocs.hooks.include_templates")

# Subdirectory under docs_dir that MkDocs 1.6+ silently excludes.
# TODO (template users): If you rename docs/templates/ to something else,
#   update this constant to match your chosen directory name.
_TEMPLATES_DIR = "templates"


# ---------------------------------------------------------------------------
# Hook
# ---------------------------------------------------------------------------


def on_files(files: Files, *, config: MkDocsConfig, **kwargs: object) -> Files:
    """Re-add docs/templates/ files if MkDocs excluded them.

    Scans the ``templates/`` subdirectory under ``docs_dir`` and adds any
    files that are missing from the MkDocs file collection.  On versions
    that don't exclude ``templates/``, this is a fast no-op.

    Args:
        files: The MkDocs file collection.
        config: The loaded MkDocs configuration.
        **kwargs: Additional keyword arguments (unused, for forward compat).

    Returns:
        The (possibly augmented) file collection.
    """
    # Allow disabling via mkdocs.yml extra config
    extra = config.get("extra", {})  # type: ignore[arg-type]
    if not extra.get("include_templates", True):  # type: ignore[union-attr]
        log.debug("include_templates hook disabled via extra.include_templates")
        return files

    docs_dir = Path(str(config["docs_dir"]))
    templates_dir = docs_dir / _TEMPLATES_DIR

    if not templates_dir.is_dir():
        log.debug(
            "templates directory not found at %s — nothing to re-add",
            templates_dir,
        )
        return files

    # Build a set of already-included source paths for fast lookup
    existing_src_paths: set[str] = {f.src_path for f in files}

    # Import File here to avoid import-time dependency on mkdocs
    from mkdocs.structure.files import File

    added = 0
    site_dir = str(config["site_dir"])
    use_directory_urls: bool = bool(config["use_directory_urls"])

    for path in sorted(templates_dir.rglob("*")):
        if not path.is_file():
            continue

        src_path = path.relative_to(docs_dir).as_posix()
        if src_path in existing_src_paths:
            continue

        new_file = File(
            src_path,
            str(docs_dir),
            site_dir,
            use_directory_urls,
        )
        files.append(new_file)
        added += 1
        log.debug("Re-added excluded file: %s", src_path)

    if added:
        log.info(
            "include_templates hook: re-added %d excluded file(s) from %s/",
            added,
            _TEMPLATES_DIR,
        )

    return files
