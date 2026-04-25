from __future__ import annotations

# Version is set by hatch-vcs from git tags at build/install time.
# The _version.py file is auto-generated and gitignored.
# The fallback below is updated by release-please in its Release PR.
#
# TODO (template users): Before tagging 1.0.0, ensure:
#   1. release-please-config.json: set "bump-minor-pre-major" to false
#   2. pyproject.toml: change classifier to "Development Status :: 5 - Production/Stable"
#   3. docs/release-policy.md: review the pre-1.0 versioning notes
try:
    from simple_python_boilerplate._version import __version__, __version_tuple__
except ImportError:
    __version__ = "1.2.0"  # x-release-please-version
    # Derive tuple from the string so release-please only needs to
    # update one line.  The marker above is the single source of truth.
    # Only parse leading numeric segments; pre-release/local suffixes
    # (e.g. 1.2.3rc1, 1.2.3+abc) get a default 0 to avoid ValueError.

    def _parse_version_tuple(v: str) -> tuple[int, ...]:
        parts: list[int] = []
        for segment in v.split("."):
            digits = ""
            for ch in segment:
                if ch.isdigit():
                    digits += ch
                else:
                    break
            parts.append(int(digits) if digits else 0)
        return tuple(parts)

    __version_tuple__ = _parse_version_tuple(__version__)
    del _parse_version_tuple

__all__ = ["__version__", "__version_tuple__"]
