#!/usr/bin/env python3
"""One-command setup for fresh clones.

Typical actions:
1. Verify Python version meets requirements
2. Check Git repository
3. Check Hatch is installed
4. Create all Hatch environments (default, docs, test matrix)
5. Install pre-commit hooks (all stages)
6. Check Task runner availability
7. Verify editable install
8. Build smoke test (hatch build)
9. Wheel install test (pip install --dry-run)
10. Template placeholder validation
11. Publishability checks (pyproject.toml fields)
12. CLI entry point check
Plus optional: quality pass (ruff + mypy), docs build, Hatch env verification

Flags::

    --dry-run            Show what would happen without making changes
    --skip-hooks         Skip pre-commit hook installation
    --skip-test-matrix   Skip creating test.py3.x environments (faster setup)
    --strict             Run optional quality pass (ruff + mypy) after setup
    --fix                With --strict, auto-fix ruff issues where possible
    --ci-like            Run all checks including quality pass and docs build
    --version            Print version and exit

Usage::

    python scripts/bootstrap.py                            # full setup
    python scripts/bootstrap.py --skip-hooks               # skip hook install
    python scripts/bootstrap.py --skip-hooks --skip-test-matrix  # fastest setup
    python scripts/bootstrap.py --dry-run                  # preview
    python scripts/bootstrap.py --strict                   # setup + quality pass
    python scripts/bootstrap.py --strict --fix             # setup + auto-fix lint
    python scripts/bootstrap.py --ci-like                  # setup + quality + docs

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Repo-specific — expects Hatch, pre-commit, and this project's
    layout.  Requires shared modules: ``_colors.py``, ``_imports.py``,
    ``_ui.py``, ``_progress.py``.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import re
import shutil
import subprocess  # nosec B404
import sys
import time
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors, unicode_symbols
from _imports import find_repo_root
from _progress import Spinner
from _ui import UI

log = logging.getLogger(__name__)

ROOT = find_repo_root()
MIN_PYTHON = (3, 11)
TOTAL_STEPS = 12
SCRIPT_VERSION = "2.0.0"

# Theme color for this script's dashboard output.
THEME = "green"

# TODO (template users): Update MIN_PYTHON if your project supports
#   a different minimum Python version. Update TOTAL_STEPS if you
#   add or remove setup phases.

# Default timeout for subprocess calls (5 minutes). Prevents hanging forever
# if a command (e.g., hatch env create) gets stuck.
_TIMEOUT = 300


def run_cmd(
    cmd: list[str],
    *,
    check: bool = True,
    capture: bool = False,
    dry_run: bool = False,
    timeout: int = _TIMEOUT,
) -> subprocess.CompletedProcess[str]:
    """Run a command with standard settings.

    Args:
        cmd: Command and arguments to run.
        check: Raise on non-zero exit code.
        capture: Capture stdout/stderr instead of printing.
        dry_run: If True, log the command but don't execute it.
        timeout: Maximum seconds to wait for the command.

    Returns:
        Completed process result (or a dummy result in dry-run mode).
    """
    log.debug("  $ %s", " ".join(cmd))
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    return subprocess.run(  # nosec B603
        cmd,
        cwd=ROOT,
        check=check,
        capture_output=capture,
        text=True,
        timeout=timeout,
    )


def _step_label(step: int, title: str) -> str:
    """Format a colored step label like ``[1/12] Title``."""
    c = Colors()
    return f"{c.cyan(f'[{step}/{TOTAL_STEPS}]')} {c.bold(c.green(title))}"


def check_python() -> bool:
    """Verify Python version."""
    c = Colors()
    log.info("\n%s", _step_label(1, "Checking Python version..."))
    log.info("")
    current = sys.version_info[:2]
    min_str = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    cur_str = f"{current[0]}.{current[1]}"

    sym = unicode_symbols()
    if current >= MIN_PYTHON:
        log.info(
            "  %s Python %s (>= %s)", c.green(sym["check"]), c.green(cur_str), min_str
        )
        log.info("")
        log.info("    %s Executable: %s", c.dim(sym["arrow"]), c.cyan(sys.executable))
        return True
    else:
        log.error(
            "  %s Python %s %s requires >= %s",
            c.red(sym["cross"]),
            cur_str,
            sym["dash"],
            min_str,
        )
        log.error("")
        log.error("    %s Executable: %s", c.dim(sym["arrow"]), c.dim(sys.executable))
        log.error(
            "  Install Python %s+: %s",
            min_str,
            c.cyan("https://www.python.org/downloads/"),
        )
        return False


def check_git() -> bool:
    """Verify Git is installed and we're inside a Git repository."""
    c = Colors()
    log.info("\n%s", _step_label(2, "Checking Git..."))
    log.info("")
    sym = unicode_symbols()
    git = shutil.which("git")
    if not git:
        log.error("  %s Git not found", c.red(sym["cross"]))
        log.error("  Install from: %s", c.cyan("https://git-scm.com/downloads"))
        return False

    git_dir = ROOT / ".git"
    if not git_dir.is_dir():
        log.error("  %s Not a Git repository (no .git/ directory)", c.red(sym["cross"]))
        log.error("  Run: %s", c.cyan("git init"))
        return False

    log.info("  %s Git repository detected", c.green(sym["check"]))
    log.info("")
    log.info("    %s Project root: %s", c.dim(sym["arrow"]), c.cyan(str(ROOT)))
    return True


def check_hatch() -> bool:
    """Verify Hatch is installed."""
    c = Colors()
    log.info("\n%s", _step_label(3, "Checking Hatch..."))
    log.info("")
    sym = unicode_symbols()
    hatch = shutil.which("hatch")
    if not hatch:
        log.error("  %s Hatch not found", c.red(sym["cross"]))
        if shutil.which("pipx"):
            log.error("  Install with: %s", c.cyan("pipx install hatch"))
        else:
            log.error("  Install with: %s", c.cyan("pip install --user hatch"))
            log.error(
                "  (Recommended: install pipx first, then: %s)",
                c.cyan("pipx install hatch"),
            )
            log.error(
                "  Why pipx? It installs Hatch in an isolated environment, avoiding"
            )
            log.error(
                "  dependency conflicts with your project's packages. pip install"
            )
            log.error(
                "  --user puts Hatch and its dependencies into your global Python,"
            )
            log.error("  which can cause version conflicts that are hard to diagnose.")
        return False

    result = run_cmd(["hatch", "--version"], capture=True, check=False)
    if result.returncode == 0:
        log.info("  %s %s", c.green(sym["check"]), result.stdout.strip())
        log.info("    %s Hatch path: %s", c.dim(sym["arrow"]), c.cyan(hatch))
        # Show Hatch cache/data directory
        cache_result = run_cmd(["hatch", "config", "find"], capture=True, check=False)
        if cache_result.returncode == 0:
            config_path = Path(cache_result.stdout.strip())
            log.info(
                "    %s Config dir: %s",
                c.dim(sym["arrow"]),
                c.cyan(str(config_path.parent)),
            )
        return True
    log.error("  %s Hatch found but failed to run", c.red(sym["cross"]))
    return False


def create_hatch_env(*, skip_test_matrix: bool = False, dry_run: bool = False) -> bool:
    """Create all Hatch environments (default, docs, test matrix).

    Args:
        skip_test_matrix: If True, skip creating test.py3.x environments.
        dry_run: If True, show what would happen without executing.

    Returns:
        True if all environments were created successfully.
    """
    c = Colors()
    log.info("\n%s", _step_label(4, "Creating Hatch environments..."))
    log.info("")

    # Environments to create
    envs = ["default", "docs"]
    if not skip_test_matrix:
        envs.extend(["test.py3.11", "test.py3.12", "test.py3.13"])

    sym = unicode_symbols()
    # Query existing environments once (not per-env)
    existing_env_names: set[str] = set()
    if not dry_run:
        result = run_cmd(["hatch", "env", "show", "--json"], capture=True, check=False)
        if result.returncode == 0:
            with contextlib.suppress(json.JSONDecodeError, AttributeError):
                existing_env_names = set(json.loads(result.stdout).keys())

    all_ok = True
    for env in envs:
        try:
            if not dry_run and env in existing_env_names:
                log.info(
                    "  %s %s environment already exists",
                    c.green(sym["check"]),
                    c.cyan(env),
                )
            else:
                with Spinner(f"Creating {env} environment") as spin:
                    spin.update(env)
                    run_cmd(["hatch", "env", "create", env], dry_run=dry_run)
                label = "Would create" if dry_run else "Created"
                log.info(
                    "  %s %s %s environment", c.green(sym["check"]), label, c.cyan(env)
                )
        except subprocess.CalledProcessError as e:
            log.error("  %s Failed to create %s: %s", c.red(sym["cross"]), env, e)
            all_ok = False

    # Show environment paths
    if not dry_run:
        _show_env_paths(c, sym)

    return all_ok


def _show_env_paths(c: Colors, sym: dict[str, str]) -> None:
    """Display discovered Hatch environment paths."""
    result = run_cmd(["hatch", "env", "show", "--json"], capture=True, check=False)
    if result.returncode != 0:
        return
    try:
        env_data = json.loads(result.stdout)
    except (json.JSONDecodeError, AttributeError):
        return
    if not env_data:
        return
    log.info("")
    log.info("  %s Environment paths:", c.bold(sym["info"]))
    for env_name in sorted(env_data):
        path_result = run_cmd(
            ["hatch", "env", "find", env_name], capture=True, check=False
        )
        if path_result.returncode == 0 and path_result.stdout.strip():
            env_path = path_result.stdout.strip()
            exists = Path(env_path).exists()
            status = c.green(sym["check"]) if exists else c.dim("(not created)")
            log.info(
                "    %s %s %s %s",
                status,
                c.cyan(env_name),
                c.dim(sym["arrow"]),
                c.dim(env_path),
            )


def install_hooks(*, skip: bool = False, dry_run: bool = False) -> bool:
    """Install pre-commit hooks.

    Args:
        skip: If True, skip hook installation entirely.
        dry_run: If True, show what would happen without executing.

    Returns:
        True if hooks were installed (or skipped) successfully.
    """
    c = Colors()
    log.info("\n%s", _step_label(5, "Installing pre-commit hooks..."))
    log.info("")
    sym = unicode_symbols()
    if skip:
        log.info("  %s Skipped (--skip-hooks)", c.dim(sym["arrow"]))
        return True

    # Build base command: direct pre-commit or via hatch
    pre_commit = shutil.which("pre-commit")
    if pre_commit:
        base = [pre_commit]
    else:
        log.info("  Using pre-commit via Hatch...")
        base = ["hatch", "run", "pre-commit"]

    stages = ["pre-commit", "commit-msg", "pre-push"]
    try:
        with Spinner("Installing hook stages") as spin:
            for stage in stages:
                spin.update(stage)
                cmd = [*base, "install"]
                if stage != "pre-commit":
                    cmd.extend(["--hook-type", stage])
                run_cmd(cmd, dry_run=dry_run)
        label = "Would install" if dry_run else "Installed"
        log.info("  %s %s all hook stages", c.green(sym["check"]), label)
        config = ROOT / ".pre-commit-config.yaml"
        if config.is_file():
            log.info(
                "    %s Config: %s",
                c.dim(sym["arrow"]),
                c.dim(str(config.relative_to(ROOT))),
            )
        return True
    except subprocess.CalledProcessError as e:
        log.error("  %s Failed: %s", c.red(sym["cross"]), e)
        return False


def check_task_runner() -> bool:
    """Check if Task runner is available (advisory only).

    Returns:
        True always — Task is optional so this never blocks setup.
    """
    c = Colors()
    log.info("\n%s", _step_label(6, "Checking Task runner..."))
    log.info("")
    sym = unicode_symbols()
    task = shutil.which("task")
    if task:
        log.info("  %s Task runner available", c.green(sym["check"]))
    else:
        log.warning(
            "  %s Task not found (optional but recommended)", c.yellow(sym["warn"])
        )
        log.warning("  Install from: %s", c.cyan("https://taskfile.dev/installation/"))
    return True


def verify_setup(*, dry_run: bool = False) -> bool:
    """Run a quick sanity check.

    Args:
        dry_run: If True, skip actual verification.

    Returns:
        True if the setup is verified (or dry-run mode).
    """
    c = Colors()
    log.info("\n%s", _step_label(7, "Verifying setup..."))
    log.info("")
    sym = unicode_symbols()
    if dry_run:
        log.info("  %s Would verify package version", c.dim(sym["arrow"]))
        return True
    try:
        with Spinner("Verifying package install") as spin:
            spin.update("importing package")
            # Quick test run
            # TODO (template users): Replace 'simple_python_boilerplate' with
            #   your package name after running customize.py.
            result = run_cmd(
                [
                    "hatch",
                    "run",
                    "python",
                    "-c",
                    "from simple_python_boilerplate import __version__; print(__version__)",
                ],
                capture=True,
            )
            spin.update("checking version")
        version = result.stdout.strip()
        log.info("  %s Package version: %s", c.green(sym["check"]), c.cyan(version))
        return True
    except subprocess.CalledProcessError as e:
        log.error("  %s Verification failed: %s", c.red(sym["cross"]), e)
        return False


# -- Template placeholder patterns that should be replaced after customize --
_PLACEHOLDER_PATTERNS: list[tuple[str, str]] = [
    (r"simple_python_boilerplate", "package name"),
    (r"simple-python-boilerplate", "project slug"),
    (r"JoJo275/simple-python-boilerplate", "repo slug"),
    (r"JoJo275", "GitHub owner"),
]


def build_smoke_test(*, dry_run: bool = False) -> bool:
    """Run ``hatch build`` and verify it produces artifacts.

    Args:
        dry_run: If True, skip actual build.

    Returns:
        True if the build succeeds.
    """
    c = Colors()
    log.info("\n%s", _step_label(8, "Build smoke test..."))
    log.info("")
    sym = unicode_symbols()
    if dry_run:
        log.info("  %s Would run hatch build", c.dim(sym["arrow"]))
        return True
    try:
        with Spinner("Building package") as spin:
            spin.update("sdist + wheel")
            run_cmd(["hatch", "build"], capture=True)
        # Check that dist/ contains files
        dist_dir = ROOT / "dist"
        artifacts = list(dist_dir.glob("*")) if dist_dir.is_dir() else []
        if artifacts:
            names = [a.name for a in artifacts[-2:]]  # show last sdist + wheel
            log.info(
                "  %s Build succeeded (%d artifact%s)",
                c.green(sym["check"]),
                len(artifacts),
                "s" if len(artifacts) != 1 else "",
            )
            for name in names:
                log.info("    %s %s", c.dim(sym["arrow"]), c.dim(name))
            return True
        log.warning("  %s Build ran but produced no artifacts", c.yellow(sym["warn"]))
        return False
    except subprocess.CalledProcessError as e:
        log.error("  %s Build failed: %s", c.red(sym["cross"]), e)
        return False


def wheel_install_test(*, dry_run: bool = False) -> bool:
    """Install the built wheel with ``pip install --dry-run`` to verify.

    Args:
        dry_run: If True, skip actual install test.

    Returns:
        True if wheel validates successfully.
    """
    c = Colors()
    log.info("\n%s", _step_label(9, "Wheel install test..."))
    log.info("")
    sym = unicode_symbols()
    if dry_run:
        log.info("  %s Would test wheel installation", c.dim(sym["arrow"]))
        return True

    dist_dir = ROOT / "dist"
    wheels = sorted(dist_dir.glob("*.whl")) if dist_dir.is_dir() else []
    if not wheels:
        log.warning("  %s No wheel found in dist/ — skipping", c.yellow(sym["warn"]))
        return True  # advisory only

    wheel = wheels[-1]  # latest
    try:
        with Spinner("Testing wheel install") as spin:
            spin.update("pip install --dry-run")
            # TODO (template users): Replace 'simple_python_boilerplate' with
            #   your package name after running customize.py.
            run_cmd(
                [
                    "hatch",
                    "run",
                    "pip",
                    "install",
                    "--dry-run",
                    str(wheel),
                ],
                capture=True,
            )
        log.info("  %s Wheel installable: %s", c.green(sym["check"]), c.dim(wheel.name))
        return True
    except subprocess.CalledProcessError as e:
        log.error("  %s Wheel install test failed: %s", c.red(sym["cross"]), e)
        return False


def check_template_placeholders() -> bool:
    """Check if template placeholders have been customized.

    Returns:
        True always (advisory check — never blocks setup).
    """
    c = Colors()
    log.info("\n%s", _step_label(10, "Checking template placeholders..."))
    log.info("")
    sym = unicode_symbols()

    pyproject = ROOT / "pyproject.toml"
    if not pyproject.is_file():
        log.warning("  %s pyproject.toml not found — skipping", c.yellow(sym["warn"]))
        return True

    content = pyproject.read_text(encoding="utf-8")
    found: list[str] = []
    for pattern, label in _PLACEHOLDER_PATTERNS:
        if re.search(pattern, content):
            found.append(label)

    if found:
        log.info(
            "  %s Template defaults detected %s:",
            c.yellow(sym["warn"]),
            c.dim(f"(in {pyproject.relative_to(ROOT)})"),
        )
        for label in found:
            log.info("    %s %s", c.dim(sym["arrow"]), label)
        log.info(
            "    %s Run %s to customize",
            c.dim(sym["arrow"]),
            c.cyan("python scripts/customize.py"),
        )
    else:
        log.info("  %s Template placeholders customized", c.green(sym["check"]))

    return True  # advisory — never blocks


def check_publishability() -> bool:
    """Check pyproject.toml has required fields for publishing.

    Returns:
        True always (advisory check — never blocks setup).
    """
    c = Colors()
    log.info("\n%s", _step_label(11, "Checking publishability..."))
    log.info("")
    sym = unicode_symbols()

    pyproject = ROOT / "pyproject.toml"
    if not pyproject.is_file():
        log.warning("  %s pyproject.toml not found — skipping", c.yellow(sym["warn"]))
        return True

    content = pyproject.read_text(encoding="utf-8")

    required_fields = {
        "name": r"^\s*name\s*=",
        "version / dynamic": r'(^\s*version\s*=|dynamic\s*=\s*\[.*"version")',
        "description": r"^\s*description\s*=",
        "license": r"^\s*license\s*=",
        "authors": r"^\s*\[\[project\.authors\]\]|^\s*authors\s*=",
    }

    missing: list[str] = []
    for field, pattern in required_fields.items():
        if not re.search(pattern, content, re.MULTILINE):
            missing.append(field)

    if missing:
        log.warning(
            "  %s Missing fields for PyPI publishing %s:",
            c.yellow(sym["warn"]),
            c.dim(f"(in {pyproject.relative_to(ROOT)})"),
        )
        for field in missing:
            log.warning("    %s %s", c.dim(sym["arrow"]), field)
    else:
        log.info("  %s All required publishing fields present", c.green(sym["check"]))
        log.info(
            "    %s Checked: %s",
            c.dim(sym["arrow"]),
            c.dim(str(pyproject.relative_to(ROOT))),
        )

    return True  # advisory


def check_cli_entry_point(*, dry_run: bool = False) -> bool:
    """Check if CLI entry points are defined and functional.

    Args:
        dry_run: If True, skip execution test.

    Returns:
        True if entry points are found (or none defined — not an error).
    """
    c = Colors()
    log.info("\n%s", _step_label(12, "Checking CLI entry points..."))
    log.info("")
    sym = unicode_symbols()

    pyproject = ROOT / "pyproject.toml"
    if not pyproject.is_file():
        log.info("  %s No pyproject.toml — skipping", c.dim(sym["arrow"]))
        return True

    content = pyproject.read_text(encoding="utf-8")

    # Check for [project.scripts] section
    if "[project.scripts]" not in content:
        log.info(
            "  %s No CLI entry points defined %s",
            c.dim(sym["arrow"]),
            c.dim("(add [project.scripts] to pyproject.toml to define one)"),
        )
        return True

    # Extract entry point names
    in_scripts = False
    entry_points: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "[project.scripts]":
            in_scripts = True
            continue
        if in_scripts:
            if stripped.startswith("["):
                break
            match = re.match(r"^(\w[\w-]*)\s*=", stripped)
            if match:
                entry_points.append(match.group(1))

    if not entry_points:
        log.info("  %s No entry points parsed", c.dim(sym["arrow"]))
        return True

    if dry_run:
        for ep in entry_points:
            log.info("  %s Would test: %s", c.dim(sym["arrow"]), c.cyan(ep))
        return True

    ok = True
    for ep in entry_points:
        try:
            run_cmd(
                ["hatch", "run", ep, "--help"],
                capture=True,
                check=True,
                timeout=30,
            )
            log.info("  %s %s --help works", c.green(sym["check"]), c.cyan(ep))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            log.warning("  %s %s --help failed", c.yellow(sym["warn"]), c.cyan(ep))
            ok = False

    return ok


def run_quality_pass(*, dry_run: bool = False, fix: bool = False) -> bool:
    """Run linting and type checking (optional quality pass).

    Args:
        dry_run: If True, skip execution.
        fix: If True, run ruff with --fix.

    Returns:
        True if all quality checks pass.
    """
    c = Colors()
    log.info("\n%s", c.bold("Quality pass (optional)..."))
    sym = unicode_symbols()

    if dry_run:
        log.info("  %s Would run ruff check + mypy", c.dim(sym["arrow"]))
        return True

    all_ok = True

    # Ruff check
    try:
        ruff_cmd = ["hatch", "run", "ruff", "check", "src/", "scripts/", "tests/"]
        if fix:
            ruff_cmd.append("--fix")
        with Spinner("Running ruff") as spin:
            spin.update("linting")
            run_cmd(ruff_cmd, capture=True)
        log.info("  %s ruff check passed", c.green(sym["check"]))
    except subprocess.CalledProcessError:
        log.warning("  %s ruff check found issues", c.yellow(sym["warn"]))
        if not fix:
            log.info(
                "    %s Run with %s to auto-fix",
                c.dim(sym["arrow"]),
                c.cyan("--fix"),
            )
        all_ok = False

    # Mypy
    try:
        with Spinner("Running mypy") as spin:
            spin.update("type checking")
            run_cmd(["hatch", "run", "mypy", "src/"], capture=True)
        log.info("  %s mypy passed", c.green(sym["check"]))
    except subprocess.CalledProcessError:
        log.warning("  %s mypy found issues", c.yellow(sym["warn"]))
        all_ok = False

    return all_ok


def check_docs_build(*, dry_run: bool = False) -> bool:
    """Try building docs with mkdocs.

    Args:
        dry_run: If True, skip actual build.

    Returns:
        True if docs build succeeds (or skipped).
    """
    c = Colors()
    log.info("\n%s", c.bold("Docs build check (optional)..."))
    sym = unicode_symbols()

    mkdocs_yml = ROOT / "mkdocs.yml"
    if not mkdocs_yml.is_file():
        log.info("  %s No mkdocs.yml — skipping", c.dim(sym["arrow"]))
        return True

    if dry_run:
        log.info("  %s Would run hatch run docs:build", c.dim(sym["arrow"]))
        return True

    try:
        with Spinner("Building docs") as spin:
            spin.update("mkdocs build")
            run_cmd(["hatch", "run", "docs:build", "--strict"], capture=True)
        log.info("  %s Docs build succeeded", c.green(sym["check"]))
        return True
    except subprocess.CalledProcessError:
        log.warning(
            "  %s Docs build failed %s",
            c.yellow(sym["warn"]),
            c.dim("(check mkdocs config)"),
        )
        return False


def check_hatch_envs(*, dry_run: bool = False) -> bool:
    """Verify that Hatch environments are healthy.

    Args:
        dry_run: If True, skip actual checks.

    Returns:
        True if all environments are healthy.
    """
    c = Colors()
    log.info("\n%s", c.bold("Hatch environment verification..."))
    sym = unicode_symbols()

    if dry_run:
        log.info("  %s Would verify Hatch environments", c.dim(sym["arrow"]))
        return True

    try:
        result = run_cmd(["hatch", "env", "show", "--json"], capture=True, check=False)
        if result.returncode != 0:
            log.warning(
                "  %s Could not query Hatch environments", c.yellow(sym["warn"])
            )
            return False

        envs = json.loads(result.stdout)
        expected = {"default", "docs"}
        found = set(envs.keys())
        missing = expected - found

        if missing:
            log.warning(
                "  %s Missing environments: %s",
                c.yellow(sym["warn"]),
                ", ".join(c.cyan(e) for e in sorted(missing)),
            )
            return False

        log.info(
            "  %s %d environment%s available: %s",
            c.green(sym["check"]),
            len(found),
            "s" if len(found) != 1 else "",
            ", ".join(c.dim(e) for e in sorted(found)),
        )
        return True
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        log.warning("  %s Env check failed: %s", c.yellow(sym["warn"]), e)
        return False


def print_next_steps(ui: UI, *, results: dict[str, bool] | None = None) -> None:
    """Print helpful next steps and recommended scripts.

    Args:
        ui: UI instance for rendering.
        results: Dict of step name → pass/fail, used to tailor advice.
    """
    # TODO (template users): Update the package name and URLs below
    #   after running customize.py, or remove this function if your
    #   bootstrap has different post-setup instructions.
    c = Colors()
    results = results or {}
    ui.section("Setup Complete — Next Steps")
    log.info("")

    step = 1

    log.info("  %d. Enter the dev environment:", step)
    log.info("     $ %s", c.cyan("hatch shell"))
    log.info("")
    step += 1

    log.info("  %d. Verify the package is importable:", step)
    log.info(
        "     $ %s", c.cyan('hatch run python -c "import simple_python_boilerplate"')
    )
    log.info("")
    step += 1

    log.info("  %d. Verify tools work:", step)
    log.info(
        "     $ %s        %s", c.cyan("task check"), c.dim("# Run all quality gates")
    )
    log.info("     $ %s         %s", c.cyan("task test"), c.dim("# Run tests"))
    log.info(
        "     $ %s       %s", c.cyan("task --list"), c.dim("# See all available tasks")
    )
    log.info("")
    step += 1

    # Dynamic: show customize step only if placeholders were detected
    if results.get("placeholders", True):
        log.info("  %d. Customize the template:", step)
        log.info("     $ %s", c.cyan("python scripts/customize.py"))
        log.info("")
        step += 1

    log.info("  %d. (Optional) Enable GitHub workflows:", step)
    log.info(
        "     $ %s", c.cyan("python scripts/customize.py --enable-workflows OWNER/REPO")
    )
    log.info(
        "     %s", c.dim("Or set repository variable: vars.ENABLE_WORKFLOWS = 'true'")
    )
    log.info("")
    step += 1

    # Dynamic: suggest quality pass if it wasn't run
    if not results.get("quality_ran"):
        log.info("  %d. (Optional) Run quality checks:", step)
        log.info(
            "     $ %s",
            c.cyan("python scripts/bootstrap.py --strict"),
        )
        log.info(
            "     %s",
            c.dim("Runs ruff + mypy to catch issues early"),
        )
        log.info("")
        step += 1

    # Dynamic: suggest docs build if it wasn't run
    if not results.get("docs_ran") and (ROOT / "mkdocs.yml").is_file():
        log.info("  %d. (Optional) Build docs:", step)
        log.info("     $ %s", c.cyan("hatch run docs:serve"))
        log.info("")
        step += 1

    log.info(
        "  %s %s",
        c.dim("Documentation:"),
        c.cyan("https://JoJo275.github.io/simple-python-boilerplate/"),
    )
    log.info("")

    ui.recommended_scripts(
        ["customize", "doctor", "repo_sauron", "dep_versions", "clean"],
        preamble="Scripts that help after initial setup.",
    )


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="bootstrap",
        description="One-command setup for fresh clones.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--skip-hooks",
        action="store_true",
        help="Skip pre-commit hook installation",
    )
    parser.add_argument(
        "--skip-test-matrix",
        action="store_true",
        help="Skip creating test.py3.x environments (faster setup)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick import and arg-parse health check; exit 0 immediately",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Run optional quality pass (ruff + mypy) after setup",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="With --strict, auto-fix ruff issues where possible",
    )
    parser.add_argument(
        "--ci-like",
        action="store_true",
        help="Run all checks including quality pass and docs build "
        "(mirrors CI pipeline)",
    )
    args = parser.parse_args()

    if args.smoke:
        print(f"bootstrap {SCRIPT_VERSION}: smoke ok")
        return 0

    level = logging.INFO
    logging.basicConfig(format="%(message)s", level=level)

    ui = UI(title="Bootstrap", version=SCRIPT_VERSION, theme=THEME)

    start_time = time.monotonic()

    ui.header()
    mode_parts: list[str] = []
    if args.dry_run:
        mode_parts.append("dry run")
    if args.skip_hooks:
        mode_parts.append("skip hooks")
    if args.skip_test_matrix:
        mode_parts.append("skip test matrix")
    if args.strict:
        mode_parts.append("strict")
    if args.fix:
        mode_parts.append("fix")
    if args.ci_like:
        mode_parts.append("CI-like")
    if mode_parts:
        ui.blank()
        ui.info_line(f"Mode: {ui.c.bold(', '.join(mode_parts))}")

    # ── Environment overview section ─────────────────────────
    ui.section("Environment Overview")
    c_info = Colors()
    ui.kv(
        "Python",
        c_info.green(
            f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
        ),
    )
    print()
    ui.kv("Executable", c_info.cyan(sys.executable))
    print()
    ui.kv("Project root", c_info.cyan(str(ROOT)))
    print()
    ui.kv("Platform", c_info.cyan(sys.platform))
    print()
    # Show cache dir
    cache_dir = os.environ.get("XDG_CACHE_HOME") or (
        Path.home() / ".cache"
        if sys.platform != "win32"
        else Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    )
    ui.kv("Cache directory", c_info.cyan(str(cache_dir)))

    # ── Section: Prerequisite Checks ────────────────────────────
    ui.section("Prerequisite Checks", compact=True)
    all_ok = True
    all_ok &= check_python()
    all_ok &= check_git()
    all_ok &= check_hatch()

    sym = unicode_symbols()
    c = Colors()
    if not all_ok:
        log.error(
            "\n%s %s",
            c.red(sym["cross"]),
            c.red("Prerequisites not met. Fix the issues above and re-run."),
        )
        return 1

    # Track results for dynamic next steps
    step_results: dict[str, bool] = {}

    # ── Section: Core Setup ──────────────────────────────────
    ui.section("Core Setup", compact=True)
    all_ok &= create_hatch_env(
        skip_test_matrix=args.skip_test_matrix, dry_run=args.dry_run
    )
    all_ok &= install_hooks(skip=args.skip_hooks, dry_run=args.dry_run)
    check_task_runner()
    all_ok &= verify_setup(dry_run=args.dry_run)

    # ── Section: Extended Checks ─────────────────────────────
    ui.section("Extended Checks", compact=True)
    all_ok &= build_smoke_test(dry_run=args.dry_run)
    all_ok &= wheel_install_test(dry_run=args.dry_run)
    check_template_placeholders()
    step_results["placeholders"] = True  # always true (advisory)
    check_publishability()
    all_ok &= check_cli_entry_point(dry_run=args.dry_run)

    # Hatch env verification
    check_hatch_envs(dry_run=args.dry_run)

    # Optional: quality pass (--strict or --ci-like)
    step_results["quality_ran"] = False
    if args.strict or args.ci_like:
        ui.section("Quality & Docs", compact=True)
        quality_ok = run_quality_pass(dry_run=args.dry_run, fix=args.fix)
        step_results["quality_ran"] = True
        if args.strict:
            all_ok &= quality_ok  # strict mode: quality failures block

    # Optional: docs build (--ci-like only)
    step_results["docs_ran"] = False
    if args.ci_like:
        docs_ok = check_docs_build(dry_run=args.dry_run)
        step_results["docs_ran"] = True
        all_ok &= docs_ok

    elapsed = time.monotonic() - start_time

    if all_ok:
        print_next_steps(ui, results=step_results)
        log.info("")
        log.info("%s", c.dim(f"Completed in {elapsed:.1f}s"))
        log.info("")
        return 0
    else:
        log.warning(
            "\n%s %s",
            c.yellow(sym["warn"]),
            c.yellow("Setup completed with warnings. Review the output above."),
        )
        log.info("")
        log.info("%s", c.dim(f"Completed in {elapsed:.1f}s"))
        log.info("")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
