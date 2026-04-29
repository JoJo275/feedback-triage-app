"""CLI entry points for the ``feedback-triage-app`` package.

Each function here is registered in ``pyproject.toml`` under
``[project.scripts]`` as an ``fta-*`` console script. The wrappers
delegate to the dev-tooling scripts in ``scripts/`` (kept as
general-purpose helpers per the project's fork policy — see
``.github/copilot-instructions.md``).

Unlike the upstream template, ``scripts/`` is **not** force-included
in the wheel: the production container ships only the FastAPI app.
These ``fta-*`` commands are therefore intended for the **editable
install used during development** (``uv sync``), where the repo root
sits two levels above this file. Invoking them from a wheel installed
outside a checkout will exit with a clear error.

Inventory (mirrors the originals in
``attic/simple_python_boilerplate/entry_points.py``):

============================  ===================================
Command                       Function
============================  ===================================
``fta-start``                 :func:`start`
``fta-git-doctor``            :func:`git_doctor`
``fta-env-doctor``            :func:`env_doctor`
``fta-repo-doctor``           :func:`repo_doctor`
``fta-diag``                  :func:`doctor_bundle`
``fta-env-inspect``           :func:`env_inspect`
``fta-repo-stats``            :func:`repo_sauron`
``fta-clean``                 :func:`clean`
``fta-bootstrap``             :func:`bootstrap`
``fta-dep-versions``          :func:`dep_versions`
``fta-workflow-versions``     :func:`workflow_versions`
``fta-check-todos``           :func:`check_todos`
``fta-check-python``          :func:`check_python_support`
``fta-changelog-check``       :func:`changelog_check`
``fta-apply-labels``          :func:`apply_labels`
``fta-archive-todos``         :func:`archive_todos`
``fta-customize``             :func:`customize`
``fta-check-issues``          :func:`check_known_issues`
``fta-dashboard``             :func:`dashboard`
============================  ===================================

The template's core entry points (``spb`` / ``spb-version`` /
``spb-doctor``) were dropped on fork: they delegated to ``cli.py`` and
``engine.py`` modules that don't exist in ``feedback_triage``. The
FastAPI app itself is launched via ``uvicorn feedback_triage.main:app``
or ``task dev``.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404
import sys
from pathlib import Path

# Repo root = two parents above this file (src/feedback_triage/entry_points.py).
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_TOOLS_DIR = _REPO_ROOT / "tools"


def _run_script(script_name: str) -> None:
    """Locate and run a dev-tooling script from the user's CWD.

    Args:
        script_name: Filename of the script (e.g. ``"git_doctor.py"``).
    """
    script_path = _SCRIPTS_DIR / script_name
    if not script_path.is_file():
        sys.stderr.write(
            f"Error: script not found at {script_path}\n"
            "fta-* helpers require an editable install of the repo "
            "(uv sync); they are not bundled in the wheel.\n",
        )
        sys.exit(1)

    cwd = str(Path.cwd())
    env = os.environ.copy()
    # Surface the repo root so scripts that need to find sibling
    # config files (repo_doctor.d/, labels/, etc.) can do so without
    # walking up from CWD.
    env["FTA_REPO_ROOT"] = str(_REPO_ROOT)

    # Add scripts/ to PYTHONPATH so _imports.py and friends resolve.
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{_SCRIPTS_DIR}{os.pathsep}{existing}" if existing else str(_SCRIPTS_DIR)
    )

    raise SystemExit(
        subprocess.call(  # nosec B603
            [sys.executable, str(script_path), *sys.argv[1:]],
            cwd=cwd,
            env=env,
        ),
    )


def _run_dashboard() -> None:
    """Locate and run the bundled environment dashboard web app."""
    app_module = _TOOLS_DIR / "dev_tools" / "env_dashboard" / "app.py"
    if not app_module.is_file():
        sys.stderr.write(
            f"Error: dashboard not found at {app_module}\n"
            "fta-dashboard requires an editable install of the repo "
            "(uv sync); the dashboard is dev-only tooling.\n",
        )
        sys.exit(1)

    cwd = str(Path.cwd())
    env = os.environ.copy()
    env["FTA_REPO_ROOT"] = str(_REPO_ROOT)

    existing = env.get("PYTHONPATH", "")
    parts = [str(_REPO_ROOT), str(_SCRIPTS_DIR)]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)

    raise SystemExit(
        subprocess.call(  # nosec B603
            [sys.executable, str(app_module), *sys.argv[1:]],
            cwd=cwd,
            env=env,
        ),
    )


# ── Bootstrap ────────────────────────────────────────────────


def start() -> None:
    """Bootstrap the project for first-time setup.

    Forwards arguments to ``scripts/bootstrap.py`` so that
    ``fta-start --dry-run`` is equivalent to
    ``python scripts/bootstrap.py --dry-run``.
    """
    bootstrap_script = _SCRIPTS_DIR / "bootstrap.py"
    if not bootstrap_script.exists():
        sys.stderr.write(f"Error: bootstrap script not found at {bootstrap_script}\n")
        sys.exit(1)
    raise SystemExit(
        subprocess.call(  # nosec B603
            [sys.executable, str(bootstrap_script), *sys.argv[1:]],
            cwd=str(_REPO_ROOT),
        ),
    )


# ── Script wrappers ──────────────────────────────────────────


def git_doctor() -> None:
    """Git health check and information dashboard."""
    _run_script("git_doctor.py")


def env_doctor() -> None:
    """Development environment health check."""
    _run_script("env_doctor.py")


def repo_doctor() -> None:
    """Repository structure health checks."""
    _run_script("repo_doctor.py")


def doctor_bundle() -> None:
    """Print diagnostics bundle for bug reports."""
    _run_script("doctor.py")


def env_inspect() -> None:
    """Environment and dependency inspector."""
    _run_script("env_inspect.py")


def repo_sauron() -> None:
    """Repository statistics dashboard."""
    _run_script("repo_sauron.py")


def clean() -> None:
    """Remove build artifacts and caches."""
    _run_script("clean.py")


def bootstrap() -> None:
    """One-command setup for fresh clones."""
    _run_script("bootstrap.py")


def dep_versions() -> None:
    """Show/update dependency versions."""
    _run_script("dep_versions.py")


def workflow_versions() -> None:
    """Show/update SHA-pinned GitHub Actions versions."""
    _run_script("workflow_versions.py")


def check_todos() -> None:
    """Scan for TODO (template users) comments."""
    _run_script("check_todos.py")


def check_python_support() -> None:
    """Validate Python version support consistency."""
    _run_script("check_python_support.py")


def changelog_check() -> None:
    """Validate CHANGELOG.md has entry for current PR."""
    _run_script("changelog_check.py")


def apply_labels() -> None:
    """Apply GitHub labels from JSON definitions."""
    _run_script("apply_labels.py")


def archive_todos() -> None:
    """Archive completed TODO items."""
    _run_script("archive_todos.py")


def customize() -> None:
    """Interactive project customization."""
    _run_script("customize.py")


def check_known_issues() -> None:
    """Flag stale resolved entries in known-issues.md."""
    _run_script("check_known_issues.py")


def dashboard() -> None:
    """Start the environment inspection web dashboard."""
    _run_dashboard()
