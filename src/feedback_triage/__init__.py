"""Feedback Triage App — FastAPI backend for triaging customer feedback.

Public API surface stabilises in Phase 3 (see
docs/project/implementation.md). The version is supplied at build time by
hatch-vcs from the latest git tag.
"""

from __future__ import annotations

try:
    from feedback_triage._version import __version__
except ImportError:  # pragma: no cover - sdist/dev tree before first build
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
