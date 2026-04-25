"""Script CLI entry points (backward-compatibility re-exports).

All entry-point functions now live in ``entry_points.py``.  This module
re-exports the 18 script wrapper functions so that any external code
importing from ``scripts_cli`` continues to work.

TODO (template users): You can safely delete this file once you have
     removed any imports that reference ``scripts_cli``.

See Also:
    - entry_points.py: All 22 CLI entry points in one place
    - docs/guide/entry-points.md: Full user documentation
"""

from __future__ import annotations

from simple_python_boilerplate.entry_points import (
    apply_labels,
    archive_todos,
    bootstrap,
    changelog_check,
    check_known_issues,
    check_python_support,
    check_todos,
    clean,
    customize,
    dashboard,
    dep_versions,
    doctor_bundle,
    env_doctor,
    env_inspect,
    git_doctor,
    repo_doctor,
    repo_sauron,
    workflow_versions,
)

__all__ = [
    "apply_labels",
    "archive_todos",
    "bootstrap",
    "changelog_check",
    "check_known_issues",
    "check_python_support",
    "check_todos",
    "clean",
    "customize",
    "dashboard",
    "dep_versions",
    "doctor_bundle",
    "env_doctor",
    "env_inspect",
    "git_doctor",
    "repo_doctor",
    "repo_sauron",
    "workflow_versions",
]
