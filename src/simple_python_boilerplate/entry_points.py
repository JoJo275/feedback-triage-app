"""All CLI entry points for the simple-python-boilerplate package.

Every function registered in ``pyproject.toml`` under ``[project.scripts]``
lives here — **22 commands in total**.  Template users: this is the single
file to read (and customise) when you want to understand what each ``spb-*``
command does.

The entry points fall into two categories:

Core (4):
    Direct application commands that delegate to ``cli.py`` / ``engine.py``.

    ==============================  =======================================
    Command                         Function
    ==============================  =======================================
    ``spb``                         :func:`main`
    ``spb-version``                 :func:`print_version`
    ``spb-doctor``                  :func:`doctor`
    ``spb-start``                   :func:`start`
    ==============================  =======================================

Script wrappers (18):
    Run bundled ``scripts/`` via subprocess from the user's **current
    working directory**, so ``spb-git-doctor`` run from ``~/my-app/``
    inspects *that* repo — not the one where the package was installed.

    ==============================  =======================================
    Command                         Function
    ==============================  =======================================
    ``spb-git-doctor``              :func:`git_doctor`
    ``spb-env-doctor``              :func:`env_doctor`
    ``spb-repo-doctor``             :func:`repo_doctor`
    ``spb-diag``                    :func:`doctor_bundle`
    ``spb-env-inspect``             :func:`env_inspect`
    ``spb-repo-stats``              :func:`repo_sauron`
    ``spb-clean``                   :func:`clean`
    ``spb-bootstrap``               :func:`bootstrap`
    ``spb-dep-versions``            :func:`dep_versions`
    ``spb-workflow-versions``       :func:`workflow_versions`
    ``spb-check-todos``             :func:`check_todos`
    ``spb-check-python``            :func:`check_python_support`
    ``spb-changelog-check``         :func:`changelog_check`
    ``spb-apply-labels``            :func:`apply_labels`
    ``spb-archive-todos``           :func:`archive_todos`
    ``spb-customize``               :func:`customize`
    ``spb-check-issues``            :func:`check_known_issues`
    ``spb-dashboard``               :func:`dashboard`
    ==============================  =======================================

TODO (template users):
    After renaming the package with ``scripts/customize.py``, update the
    ``spb-`` prefixes in ``pyproject.toml`` to match your project name
    (e.g., ``myapp-doctor``).  Remove any commands you don't need, and
    delete the corresponding wrapper functions from this file.

See Also:
    - ``pyproject.toml`` — Entry point registration under ``[project.scripts]``
    - ``docs/guide/entry-points.md`` — Full user documentation
    - ``scripts/README.md`` — Script inventory and usage
"""

from __future__ import annotations

import os
import subprocess  # nosec B404
import sys
from pathlib import Path

# ── Script runner infrastructure ─────────────────────────────
#
# The scripts/ and tools/ directories are force-included in the wheel
# at build time (see [tool.hatch.build.targets.wheel.force-include]
# in pyproject.toml).

_BUNDLED_SCRIPTS = Path(__file__).resolve().parent / "_bundled_scripts" / "scripts"
_BUNDLED_TOOLS = Path(__file__).resolve().parent / "_bundled_tools" / "tools"


def _run_script(script_name: str) -> None:
    """Locate and run a bundled script from the user's CWD.

    Args:
        script_name: Filename of the script (e.g. ``"git_doctor.py"``).
    """
    script_path = _BUNDLED_SCRIPTS / script_name
    if not script_path.is_file():
        sys.stderr.write(f"Error: bundled script not found at {script_path}\n")
        sys.exit(1)

    cwd = str(Path.cwd())
    env = os.environ.copy()
    env["SPB_REPO_ROOT"] = cwd

    # Add the bundled scripts dir to PYTHONPATH so _imports.py and
    # sibling modules (_colors.py, _progress.py, etc.) can be found.
    scripts_dir = str(_BUNDLED_SCRIPTS)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{scripts_dir}{os.pathsep}{existing}" if existing else scripts_dir
    )

    raise SystemExit(
        subprocess.call(  # nosec B603
            [sys.executable, str(script_path), *sys.argv[1:]],
            cwd=cwd,
            env=env,
        )
    )


def _run_dashboard() -> None:
    """Locate and run the bundled dashboard web app from the user's CWD."""
    app_module = _BUNDLED_TOOLS / "dev_tools" / "env_dashboard" / "app.py"
    if not app_module.is_file():
        sys.stderr.write(f"Error: bundled dashboard not found at {app_module}\n")
        sys.exit(1)

    cwd = str(Path.cwd())
    env = os.environ.copy()
    env["SPB_REPO_ROOT"] = cwd

    # Add bundled directories to PYTHONPATH so imports resolve
    scripts_dir = str(_BUNDLED_SCRIPTS)
    tools_parent = str(
        _BUNDLED_TOOLS.parent
    )  # Parent of tools/ so "tools.dev_tools..." works
    existing = env.get("PYTHONPATH", "")
    parts = [tools_parent, scripts_dir]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)

    raise SystemExit(
        subprocess.call(  # nosec B603
            [sys.executable, str(app_module), *sys.argv[1:]],
            cwd=cwd,
            env=env,
        )
    )


# ── Core entry points (main.py → pyproject.toml) ────────────


def main() -> None:
    """Main CLI entry point.

    Delegates to cli.run() for argument parsing and dispatch.
    """
    from simple_python_boilerplate import cli

    sys.exit(cli.run(cli.parse_args()))


def print_version() -> None:
    """Print version information and exit."""
    from simple_python_boilerplate.engine import get_version_info

    info = get_version_info()
    print(f"simple-python-boilerplate {info['package_version']}")  # noqa: T201
    print(f"Python {info['python_full']}")  # noqa: T201


def start() -> None:
    """Bootstrap the project for first-time setup.

    Runs ``scripts/bootstrap.py`` from the repository root so new
    contributors can type ``spb-start`` instead of remembering the
    full ``python scripts/bootstrap.py`` path.

    All arguments are forwarded to the bootstrap script, so
    ``spb-start --dry-run`` works exactly like
    ``python scripts/bootstrap.py --dry-run``.
    """
    root = Path(__file__).resolve().parent.parent.parent
    bootstrap_script = root / "scripts" / "bootstrap.py"
    if not bootstrap_script.exists():
        print(f"Error: bootstrap script not found at {bootstrap_script}")  # noqa: T201
        sys.exit(1)
    raise SystemExit(
        subprocess.call(  # nosec B603
            [sys.executable, str(bootstrap_script), *sys.argv[1:]],
            cwd=str(root),
        )
    )


def doctor() -> None:
    """Diagnose environment and configuration issues.

    Delegates to engine.diagnose_environment() for the actual checks,
    then formats the output for the terminal.
    """
    import argparse

    from simple_python_boilerplate.engine import (
        DiagnosticInfo,
        diagnose_environment,
    )

    parser = argparse.ArgumentParser(
        description="Diagnose environment and configuration issues.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (simple-python-boilerplate doctor)",
    )
    parser.parse_args()

    diag: DiagnosticInfo = diagnose_environment()

    print("\U0001fa7a simple-python-boilerplate doctor\n")  # noqa: T201

    # Version info
    print("== Version ==")  # noqa: T201
    print(f"  Package version: {diag['version']['package_version']}")  # noqa: T201
    print(f"  Python version:  {diag['version']['python_version']}")  # noqa: T201
    print(f"  Platform:        {diag['version']['platform']}")  # noqa: T201
    print()  # noqa: T201

    # Python environment
    print("== Environment ==")  # noqa: T201
    print(f"  Executable: {diag['executable']}")  # noqa: T201
    print(f"  Prefix:     {diag['prefix']}")  # noqa: T201
    venv_status = (
        "\u2705 Yes"
        if diag["in_virtual_env"]
        else "\u26a0\ufe0f  No (consider using a venv)"
    )
    print(f"  Virtual env: {venv_status}")  # noqa: T201
    print()  # noqa: T201

    # Check for common dev tools
    print("== Dev Tools ==")  # noqa: T201
    for tool, path in diag["tools"].items():
        if path:
            print(f"  {tool}: \u2705 {path}")  # noqa: T201
        else:
            print(f"  {tool}: \u274c not found")  # noqa: T201
    print()  # noqa: T201

    # Check for config files
    print("== Config Files ==")  # noqa: T201
    for cfg, exists in diag["config_files"].items():
        status = "\u2705 found" if exists else "\u26a0\ufe0f  missing"
        print(f"  {cfg}: {status}")  # noqa: T201
    print()  # noqa: T201

    print("\u2728 Doctor complete!")  # noqa: T201


# ── Script entry points (scripts_cli.py → pyproject.toml) ───
# Each function is a thin wrapper that delegates to _run_script()
# or _run_dashboard().


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
