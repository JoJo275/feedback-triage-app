#!/usr/bin/env python3
"""Quick environment health check for daily development.

Verifies that the development environment is correctly set up:
Python version, virtual environment, editable install, Hatch,
Task, pre-commit hooks, and key tool availability.

Also runs extended checks for project consistency: dependency
freshness, Python version alignment, stale Hatch environments,
license format, encoding/BOM, orphaned test files, import cycles,
pre-commit config staleness, and workflow YAML syntax.

Note:
    The ``cz`` tool check requires the ``commitizen`` package to be
    installed (it provides the ``cz`` CLI).  If you see ``cz not found
    in PATH``, install it via ``hatch shell`` (which pulls in the dev
    extras) or ``pipx install commitizen``.

Flags::

    --strict     Treat optional tool warnings as failures
    --no-color   Disable colored output
    --json       Output results as JSON (for CI integration)
    --version    Print version and exit

Usage::

    python scripts/env_doctor.py
    python scripts/env_doctor.py --strict
    python scripts/env_doctor.py --json

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Repo-specific — checks are tailored to this project's tooling
    (Hatch, pre-commit, Taskfile). Requires shared modules:
    ``_colors.py``, ``_imports.py``, ``_ui.py``, ``_progress.py``,
    ``_doctor_common.py``.
"""

from __future__ import annotations

import argparse
import ast
import importlib.metadata
import json
import logging
import os
import platform
import re
import shutil
import struct
import subprocess  # nosec B404
import sys
import time
from collections.abc import Callable
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors
from _colors import status_icon as _icon
from _colors import supports_color as _supports_color
from _doctor_common import (
    check_hook_installed,
    get_package_version,
    get_version,
    parse_version_specifier,
    read_pyproject,
)
from _imports import find_repo_root, import_sibling
from _ui import UI

if not __import__("typing").TYPE_CHECKING:
    ProgressBar = import_sibling("_progress").ProgressBar
else:
    from _progress import ProgressBar

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_VERSION = "1.6.0"

# Theme color for this script's dashboard output.
THEME = "blue"

logger = logging.getLogger(__name__)

ROOT = find_repo_root()
# TODO (template users): Update MIN_PYTHON to match your project's
#   minimum supported Python version (see pyproject.toml requires-python).
MIN_PYTHON = (3, 11)

# TODO (template users): Update EXPECTED_TOOLS and OPTIONAL_TOOLS to
#   match the dev tools your project actually uses. Remove tools you
#   don't need and add any project-specific ones.
# Tools expected in the dev environment
EXPECTED_TOOLS = ["ruff", "mypy", "pytest", "bandit", "pre-commit", "cz", "deptry"]

# Optional tools — reported but don't fail unless --strict
OPTIONAL_TOOLS = ["actionlint"]

# TODO (template users): If you add or remove pre-commit hook stages,
#   update HOOK_FILES to match.
# Pre-commit hook files to check
HOOK_FILES = {
    "pre-commit": ROOT / ".git" / "hooks" / "pre-commit",
    "commit-msg": ROOT / ".git" / "hooks" / "commit-msg",
    "pre-push": ROOT / ".git" / "hooks" / "pre-push",
}


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def check_python_version() -> tuple[bool, str]:
    """Verify Python version meets minimum requirement.

    Returns:
        Tuple of (passed, message).
    """
    current = sys.version_info[:2]
    ok = current >= MIN_PYTHON
    version_str = f"{current[0]}.{current[1]}"
    min_str = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    if ok:
        return True, f"Python {version_str} (>= {min_str})"
    return False, f"Python {version_str} — requires >= {min_str}"


def check_architecture() -> tuple[bool, str]:
    """Report Python architecture (32-bit vs 64-bit).

    Returns:
        Tuple of (passed, message).
    """
    bits = struct.calcsize("P") * 8
    return True, f"{bits}-bit Python"


def check_os_platform() -> tuple[bool, str]:
    """Report the operating system and platform.

    Returns:
        Tuple of (passed, message). Always passes (informational).
    """
    os_name = platform.system()
    os_version = platform.version()
    machine = platform.machine()
    return True, f"{os_name} {os_version} ({machine})"


def check_pip_version() -> tuple[bool, str]:
    """Check if pip is available and report its version.

    Returns:
        Tuple of (passed, message).
    """
    version = get_version([sys.executable, "-m", "pip", "--version"])
    if version == "not found":
        return False, "pip not found"
    if version == "error":
        return False, "pip found but failed to run"
    # pip --version outputs: "pip X.Y.Z from /path ..." — extract version
    parts = version.split()
    if len(parts) >= 2:
        return True, f"pip {parts[1]}"
    return True, version


def check_venv_active() -> tuple[bool, str]:
    """Check if a virtual environment is active.

    Returns:
        Tuple of (passed, message).
    """
    venv = os.environ.get("VIRTUAL_ENV", "")
    if venv:
        return True, f"Virtual env active: {Path(venv).name}"
    return False, "No virtual environment active"


def check_editable_install() -> tuple[bool, str]:
    """Check if the project is installed (ideally in editable mode).

    Uses PEP 610 ``direct_url.json`` (via ``importlib.metadata``) to
    detect editable installs.  Falls back to checking whether the
    package's ``__file__`` points into the repo's ``src/`` tree.

    Returns:
        Tuple of (passed, message).
    """
    pkg = "simple-python-boilerplate"
    version = get_package_version(pkg)
    if version == "not installed":
        return (
            False,
            "Package not installed — run: hatch shell (or pip install -e '.[dev]')",
        )

    # --- PEP 610: check direct_url.json for editable marker -----------
    try:
        import json as _json

        dist = importlib.metadata.distribution(pkg)
        du_text = dist.read_text("direct_url.json")
        if du_text:
            du = _json.loads(du_text)
            if du.get("dir_info", {}).get("editable", False):
                return True, f"Editable install OK (v{version})"
            return True, f"Installed v{version} (non-editable direct install)"
    except (importlib.metadata.PackageNotFoundError, KeyError, ValueError):
        pass

    # --- Fallback: check if imported module lives in src/ tree ---------
    try:
        import simple_python_boilerplate as _spb

        mod_path = Path(_spb.__file__).resolve()
        src_dir = ROOT / "src"
        if src_dir.exists() and src_dir.resolve() in mod_path.parents:
            return True, f"Editable install OK (v{version})"
    except (ImportError, AttributeError, TypeError):
        pass

    return True, f"Installed v{version} (may not be editable)"


def check_tool_available(tool: str) -> tuple[bool, str]:
    """Check if a development tool is available.

    Args:
        tool: Name of the tool/command to check.

    Returns:
        Tuple of (passed, message).
    """
    if shutil.which(tool):
        return True, f"{tool} available"
    return False, f"{tool} not found in PATH"


def check_hatch() -> tuple[bool, str]:
    """Check if Hatch is installed and accessible.

    Returns:
        Tuple of (passed, message).
    """
    version = get_version(["hatch", "--version"])
    if version == "not found":
        return False, "Hatch not found — install: pipx install hatch"
    if version == "error":
        return False, "Hatch found but failed to run"
    # hatch --version outputs "Hatch, version X.Y.Z" — avoid
    # prefixing with "Hatch" again
    if version.lower().startswith("hatch"):
        return True, version
    return True, f"Hatch {version}"


def check_task() -> tuple[bool, str]:
    """Check if Task runner is installed.

    Returns:
        Tuple of (passed, message).
    """
    task = shutil.which("task")
    if not task:
        return False, "Task not found (optional) — install: https://taskfile.dev"
    return True, "Task available"


def check_pre_commit_hooks() -> tuple[bool, str]:
    """Check if all pre-commit hook stages are installed.

    Uses :func:`_doctor_common.check_hook_installed` for detailed
    hook status detection (distinguishes installed, sample, custom,
    and missing hooks).

    Returns:
        Tuple of (passed, message).
    """
    installed: list[str] = []
    missing: list[str] = []

    for name, path in HOOK_FILES.items():
        status = check_hook_installed(path)
        if status == "installed":
            installed.append(name)
        else:
            missing.append(name)

    if not missing:
        return True, f"All hooks installed ({', '.join(installed)})"
    if not installed:
        return False, "No hooks installed — run: task pre-commit:install"
    return False, f"Missing hooks: {', '.join(missing)} — run: task pre-commit:install"


def check_git_repo() -> tuple[bool, str]:
    """Check if we're inside a git repository.

    Returns:
        Tuple of (passed, message).
    """
    git_dir = ROOT / ".git"
    if git_dir.is_dir():
        return True, "Git repository detected"
    return False, "Not a git repository"


def check_git_user_config() -> tuple[bool, str]:
    """Check if git user.name and user.email are configured.

    Returns:
        Tuple of (passed, message).
    """
    git = shutil.which("git")
    if not git:
        return False, "git not found in PATH"

    missing: list[str] = []
    for key in ("user.name", "user.email"):
        try:
            result = subprocess.run(  # nosec B603
                [git, "config", key],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if not result.stdout.strip():
                missing.append(key)
        except (subprocess.TimeoutExpired, OSError):
            missing.append(key)

    if not missing:
        return True, "Git user.name and user.email configured"
    return (
        False,
        f"Git config missing: {', '.join(missing)} — run: git config --global {missing[0]} <value>",
    )


def check_pyproject_toml() -> tuple[bool, str]:
    """Check if pyproject.toml exists in the project root.

    Returns:
        Tuple of (passed, message).
    """
    pyproject = ROOT / "pyproject.toml"
    if pyproject.is_file():
        return True, "pyproject.toml found"
    return False, "pyproject.toml missing — project configuration is incomplete"


def check_node_available() -> tuple[bool, str]:
    """Check if Node.js is available (needed by prettier, markdownlint-cli2 hooks).

    Returns:
        Tuple of (passed, message).
    """
    node = shutil.which("node")
    if not node:
        return (
            False,
            "Node.js not found — needed by prettier/markdownlint pre-commit hooks",
        )
    version = get_version(["node", "--version"])
    if version in ("not found", "error"):
        return False, "Node.js found but failed to get version"
    return True, f"Node.js {version}"


def check_container_runtime() -> tuple[bool, str]:
    """Check if Docker or Podman is available for container workflows.

    Returns:
        Tuple of (passed, message).
    """
    for runtime in ("docker", "podman"):
        if shutil.which(runtime):
            version = get_version([runtime, "--version"])
            if version not in ("not found", "error"):
                return True, f"{runtime}: {version}"
            return True, f"{runtime} available"
    return False, "No container runtime (docker/podman) found"


def check_git_remote() -> tuple[bool, str]:
    """Check if a git remote origin is configured.

    Returns:
        Tuple of (passed, message).
    """
    git = shutil.which("git")
    if not git:
        return False, "git not found in PATH"
    try:
        result = subprocess.run(  # nosec B603
            [git, "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(ROOT),
        )
        url = result.stdout.strip()
        if url:
            return True, f"Git remote origin: {url}"
        return False, "No remote 'origin' configured"
    except (subprocess.TimeoutExpired, OSError):
        return False, "Could not check git remote"


def check_hatch_env_exists() -> tuple[bool, str]:
    """Check if the Hatch default environment is created.

    Returns:
        Tuple of (passed, message).
    """
    hatch = shutil.which("hatch")
    if not hatch:
        return False, "Hatch not found — cannot check env"
    try:
        result = subprocess.run(  # nosec B603
            [hatch, "env", "find", "default"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(ROOT),
        )
        env_path = result.stdout.strip()
        if result.returncode == 0 and env_path and Path(env_path).is_dir():
            return True, f"Hatch default env exists: {Path(env_path).name}"
        return False, "Hatch default env not created — run: hatch env create default"
    except (subprocess.TimeoutExpired, OSError):
        return False, "Could not check Hatch env"


def check_disk_space() -> tuple[bool, str]:
    """Warn if disk space on the project drive is below 1 GB.

    Returns:
        Tuple of (passed, message).
    """
    try:
        usage = shutil.disk_usage(ROOT)
        free_gb = usage.free / (1024**3)
        if free_gb < 1.0:
            return False, f"Low disk space: {free_gb:.1f} GB free"
        return True, f"Disk space: {free_gb:.1f} GB free"
    except OSError:
        return True, "Could not check disk space"


# ---------------------------------------------------------------------------
# Extended checks (absorbed from health_checks.py)
# ---------------------------------------------------------------------------


def check_dependency_freshness() -> tuple[bool, str]:
    """Check if requirements.txt/requirements-dev.txt match pyproject.toml.

    Compares package names listed in requirements files against those
    in pyproject.toml optional-dependencies to detect drift.

    Returns:
        Tuple of (passed, message).
    """
    pyproject = read_pyproject(ROOT)
    if pyproject is None:
        return False, "Cannot parse pyproject.toml"

    project = pyproject.get("project", {})
    if not isinstance(project, dict):
        return False, "Invalid [project] section in pyproject.toml"

    # Collect runtime deps from pyproject.toml
    runtime_deps: set[str] = set()
    for dep in project.get("dependencies", []):
        if isinstance(dep, str) and not dep.strip().startswith("#"):
            runtime_deps.add(parse_version_specifier(dep))

    # Collect dev deps from optional-dependencies
    opt_deps = project.get("optional-dependencies", {})
    if not isinstance(opt_deps, dict):
        opt_deps = {}
    dev_deps_pyproject: set[str] = set()
    pkg_name = parse_version_specifier(str(project.get("name", "")))
    for group_deps in opt_deps.values():
        if isinstance(group_deps, list):
            for dep in group_deps:
                if isinstance(dep, str) and not dep.strip().startswith("#"):
                    name = parse_version_specifier(dep)
                    if "[" not in dep or name != pkg_name:
                        dev_deps_pyproject.add(name)

    issues: list[str] = []

    req_file = ROOT / "requirements.txt"
    if req_file.is_file():
        req_deps: set[str] = set()
        for line in req_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                req_deps.add(parse_version_specifier(line))
        missing_in_req = runtime_deps - req_deps
        extra_in_req = req_deps - runtime_deps
        if missing_in_req:
            issues.append(
                f"requirements.txt missing: {', '.join(sorted(missing_in_req))}"
            )
        if extra_in_req:
            issues.append(f"requirements.txt extras: {', '.join(sorted(extra_in_req))}")

    req_dev_file = ROOT / "requirements-dev.txt"
    if req_dev_file.is_file():
        req_dev_deps: set[str] = set()
        for line in req_dev_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                req_dev_deps.add(parse_version_specifier(line))
        missing_in_dev = dev_deps_pyproject - req_dev_deps - runtime_deps
        missing_in_dev.discard(pkg_name)
        if missing_in_dev:
            issues.append(
                f"requirements-dev.txt missing: {', '.join(sorted(missing_in_dev))}"
            )

    if not issues:
        return True, "Requirements files in sync with pyproject.toml"
    return False, "; ".join(issues)


def check_python_version_consistency() -> tuple[bool, str]:
    """Compare Python version requirements across project files.

    Checks MIN_PYTHON in bootstrap.py, requires-python in pyproject.toml,
    and the test matrix versions.

    Returns:
        Tuple of (passed, message).
    """
    issues: list[str] = []
    found_versions: dict[str, str] = {}
    pyproject_min: str | None = None

    pyproject = read_pyproject(ROOT)
    if pyproject is not None:
        project = pyproject.get("project", {})
        if isinstance(project, dict):
            requires_python = project.get("requires-python", "")
            if isinstance(requires_python, str):
                found_versions["pyproject.toml requires-python"] = requires_python
                match = re.search(r">=(\d+\.\d+)", requires_python)
                pyproject_min = match.group(1) if match else None

        # Test matrix versions
        hatch_cfg = pyproject.get("tool", {})
        if isinstance(hatch_cfg, dict):
            hatch_envs = hatch_cfg.get("hatch", {})
            if isinstance(hatch_envs, dict):
                envs = hatch_envs.get("envs", {})
                if isinstance(envs, dict):
                    test_env = envs.get("test", {})
                    if isinstance(test_env, dict):
                        matrix = test_env.get("matrix", [])
                        if isinstance(matrix, list):
                            for entry in matrix:
                                if isinstance(entry, dict) and "python" in entry:
                                    versions = entry["python"]
                                    if isinstance(versions, list):
                                        found_versions["test matrix"] = str(versions)
                                        if pyproject_min and versions:
                                            min_matrix = min(
                                                versions,
                                                key=lambda v: tuple(
                                                    map(int, str(v).split("."))
                                                ),
                                            )
                                            if str(min_matrix) != pyproject_min:
                                                issues.append(
                                                    f"Test matrix min ({min_matrix}) != "
                                                    f"requires-python ({pyproject_min})"
                                                )

    # bootstrap.py MIN_PYTHON
    bootstrap_path = ROOT / "scripts" / "bootstrap.py"
    if bootstrap_path.is_file():
        content = bootstrap_path.read_text(encoding="utf-8")
        match = re.search(r"MIN_PYTHON\s*=\s*\((\d+),\s*(\d+)\)", content)
        if match:
            bootstrap_min = f"{match.group(1)}.{match.group(2)}"
            found_versions["bootstrap.py MIN_PYTHON"] = bootstrap_min
            if pyproject_min and bootstrap_min != pyproject_min:
                issues.append(
                    f"bootstrap.py MIN_PYTHON ({bootstrap_min}) != "
                    f"requires-python ({pyproject_min})"
                )

    # env_doctor.py MIN_PYTHON (self-check)
    min_str = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    found_versions["env_doctor.py MIN_PYTHON"] = min_str
    if pyproject_min and min_str != pyproject_min:
        issues.append(
            f"env_doctor.py MIN_PYTHON ({min_str}) != requires-python ({pyproject_min})"
        )

    if not issues:
        versions_str = ", ".join(f"{k}={v}" for k, v in found_versions.items())
        return True, f"Python versions consistent: {versions_str}"
    return False, "; ".join(issues)


def check_stale_hatch_envs() -> tuple[bool, str]:
    """Detect Hatch envs for Python versions no longer in the test matrix.

    Returns:
        Tuple of (passed, message).
    """
    hatch = shutil.which("hatch")
    if not hatch:
        return True, "Hatch not installed \u2014 skipping stale env check"

    pyproject = read_pyproject(ROOT)
    if pyproject is None:
        return True, "Cannot read pyproject.toml \u2014 skipping"

    matrix_versions: set[str] = set()
    hatch_cfg = pyproject.get("tool", {})
    if isinstance(hatch_cfg, dict):
        hatch_envs = hatch_cfg.get("hatch", {})
        if isinstance(hatch_envs, dict):
            envs = hatch_envs.get("envs", {})
            if isinstance(envs, dict):
                test_env = envs.get("test", {})
                if isinstance(test_env, dict):
                    matrix = test_env.get("matrix", [])
                    if isinstance(matrix, list):
                        for entry in matrix:
                            if isinstance(entry, dict) and "python" in entry:
                                for v in entry["python"]:
                                    matrix_versions.add(str(v))

    if not matrix_versions:
        return True, "No test matrix found \u2014 skipping"

    stale: list[str] = []
    try:
        for version in ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]:
            if version not in matrix_versions:
                env_check = subprocess.run(  # nosec B603
                    [hatch, "env", "find", f"test.py{version}"],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if env_check.returncode == 0:
                    env_path = env_check.stdout.strip()
                    if env_path and Path(env_path).is_dir():
                        stale.append(f"test.py{version}")
    except (subprocess.TimeoutExpired, OSError):
        return True, "Could not check Hatch env paths \u2014 skipping"

    if stale:
        return (
            False,
            f"Stale Hatch envs: {', '.join(stale)} "
            f"\u2014 run: hatch env remove {' '.join(stale)}",
        )
    return True, "No stale Hatch test environments"


def check_license_format() -> tuple[bool, str]:
    """Verify LICENSE file SPDX identifier matches pyproject.toml.

    Returns:
        Tuple of (passed, message).
    """
    license_path = ROOT / "LICENSE"
    if not license_path.is_file():
        return False, "LICENSE file missing"

    content = license_path.read_text(encoding="utf-8", errors="ignore")

    detected_spdx: str | None = None
    license_lower = content.lower()
    if "apache license" in license_lower and "version 2.0" in license_lower:
        detected_spdx = "Apache-2.0"
    elif (
        "mit license" in license_lower
        or "permission is hereby granted" in license_lower
    ):
        detected_spdx = "MIT"
    elif "gnu general public license" in license_lower:
        if "version 3" in license_lower:
            detected_spdx = "GPL-3.0"
        elif "version 2" in license_lower:
            detected_spdx = "GPL-2.0"
    elif "bsd" in license_lower:
        detected_spdx = "BSD"

    pyproject = read_pyproject(ROOT)
    if pyproject is None:
        return True, f"LICENSE detected as {detected_spdx or 'unknown'}"

    project = pyproject.get("project", {})
    if not isinstance(project, dict):
        return True, f"LICENSE detected as {detected_spdx or 'unknown'}"

    classifiers = project.get("classifiers", [])
    declared_license: str | None = None
    if isinstance(classifiers, list):
        for clf in classifiers:
            if isinstance(clf, str) and "License" in clf and "OSI Approved" in clf:
                declared_license = clf.split("::")[-1].strip()
                break

    if detected_spdx and declared_license:
        if detected_spdx.lower().split("-")[0] in declared_license.lower():
            return (
                True,
                f"LICENSE ({detected_spdx}) matches pyproject.toml ({declared_license})",
            )
        return (
            False,
            f"LICENSE looks like {detected_spdx} but pyproject.toml "
            f"declares '{declared_license}'",
        )

    return True, f"LICENSE detected as {detected_spdx or 'unrecognized'}"


def check_encoding_bom() -> tuple[bool, str]:
    """Scan key files for unexpected BOMs or non-UTF-8 encoding.

    Returns:
        Tuple of (passed, message).
    """
    key_files = [
        "pyproject.toml",
        "Taskfile.yml",
        ".pre-commit-config.yaml",
        "Containerfile",
        "mkdocs.yml",
        "README.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
    ]

    bom_files: list[str] = []
    encoding_issues: list[str] = []
    utf8_bom = b"\xef\xbb\xbf"

    for rel_path in key_files:
        fpath = ROOT / rel_path
        if not fpath.is_file():
            continue
        try:
            raw = fpath.read_bytes()
        except OSError:
            continue
        if raw.startswith(utf8_bom):
            bom_files.append(rel_path)
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            encoding_issues.append(rel_path)

    for search_dir in [ROOT / "src", ROOT / "scripts"]:
        if not search_dir.is_dir():
            continue
        for py_file in search_dir.rglob("*.py"):
            rel = str(py_file.relative_to(ROOT))
            try:
                raw = py_file.read_bytes()
            except OSError:
                continue
            if raw.startswith(utf8_bom):
                bom_files.append(rel)
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                encoding_issues.append(rel)

    issues: list[str] = []
    if bom_files:
        issues.append(f"UTF-8 BOM detected in: {', '.join(bom_files[:5])}")
    if encoding_issues:
        issues.append(f"Non-UTF-8 encoding in: {', '.join(encoding_issues[:5])}")

    if not issues:
        return True, "All key files are clean UTF-8 (no BOM)"
    return False, "; ".join(issues)


def check_orphaned_test_files() -> tuple[bool, str]:
    """Find test files that don't map to any source module.

    Returns:
        Tuple of (passed, message).
    """
    src_dir = ROOT / "src"
    test_dirs = [ROOT / "tests" / "unit", ROOT / "tests" / "integration"]

    if not src_dir.is_dir():
        return True, "No src/ directory \u2014 skipping"

    source_modules: set[str] = set()
    for py_file in src_dir.rglob("*.py"):
        name = py_file.stem
        if name != "__init__":
            source_modules.add(name)

    scripts_dir = ROOT / "scripts"
    if scripts_dir.is_dir():
        for py_file in scripts_dir.rglob("*.py"):
            source_modules.add(py_file.stem)

    hooks_dir = ROOT / "mkdocs-hooks"
    if hooks_dir.is_dir():
        for py_file in hooks_dir.glob("*.py"):
            source_modules.add(py_file.stem)

    orphaned: list[str] = []
    known_non_module_tests = {
        "conftest",
        "__init__",
        "test_example",
        "test_init_fallback",
        "test_main_entry",
        "test_customize_interactive",
        "test_cli_smoke",
        "test_db_example",
    }

    for test_dir in test_dirs:
        if not test_dir.is_dir():
            continue
        for test_file in test_dir.glob("test_*.py"):
            test_name = test_file.stem
            if test_name in known_non_module_tests:
                continue
            module_name = test_name.removeprefix("test_")
            if (
                module_name not in source_modules
                and f"_{module_name}" not in source_modules
            ):
                orphaned.append(test_name)

    if orphaned:
        return (
            False,
            f"Orphaned test files: {', '.join(sorted(orphaned)[:10])}",
        )
    return True, "All test files have matching source modules"


def check_import_cycles() -> tuple[bool, str]:
    """Quick check for circular imports in src/.

    Uses AST parsing to build an import graph and detect cycles.

    Returns:
        Tuple of (passed, message).
    """
    pkg_dir = ROOT / "src" / "simple_python_boilerplate"
    if not pkg_dir.is_dir():
        return True, "No package directory found \u2014 skipping"

    pkg_name = "simple_python_boilerplate"
    imports: dict[str, set[str]] = {}

    for py_file in pkg_dir.rglob("*.py"):
        module = py_file.stem
        if module == "__init__":
            rel = py_file.parent.relative_to(pkg_dir)
            module = str(rel).replace(os.sep, ".") if str(rel) != "." else pkg_name
        else:
            rel = py_file.relative_to(pkg_dir)
            module = str(rel.with_suffix("")).replace(os.sep, ".")

        imports[module] = set()
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(pkg_name + "."):
                        target = alias.name.removeprefix(pkg_name + ".")
                        imports[module].add(target)
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith(pkg_name)
            ):
                target = node.module.removeprefix(pkg_name + ".")
                if target:
                    imports[module].add(target)

    cycles: list[list[str]] = []
    visited: set[str] = set()
    path: list[str] = []
    on_stack: set[str] = set()

    def dfs(node: str) -> None:
        if node in on_stack:
            cycle_start = path.index(node)
            cycles.append([*path[cycle_start:], node])
            return
        if node in visited:
            return
        visited.add(node)
        on_stack.add(node)
        path.append(node)
        for dep in imports.get(node, set()):
            dfs(dep)
        path.pop()
        on_stack.discard(node)

    for module in imports:
        dfs(module)

    if cycles:
        cycle_strs = [" -> ".join(c) for c in cycles[:3]]
        return False, f"Import cycles: {'; '.join(cycle_strs)}"
    return True, "No circular imports detected"


def check_precommit_config_staleness() -> tuple[bool, str]:
    """Check if pre-commit hook revs look outdated.

    Returns:
        Tuple of (passed, message).
    """
    config_path = ROOT / ".pre-commit-config.yaml"
    if not config_path.is_file():
        return True, "No .pre-commit-config.yaml found"

    try:
        content = config_path.read_text(encoding="utf-8")
    except OSError:
        return False, "Cannot read .pre-commit-config.yaml"

    repo_count = content.count("- repo:")
    rev_pattern = re.compile(r"rev:\s*['\"]?v?(\d+\.\d+\.\d+)")
    revs = rev_pattern.findall(content)

    if not revs:
        return True, f"{repo_count} repos configured (no version revs to check)"

    pre_commit = shutil.which("pre-commit")
    if pre_commit:
        try:
            result = subprocess.run(  # nosec B603
                [pre_commit, "autoupdate", "--dry-run"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and "updating" in result.stdout.lower():
                update_count = result.stdout.lower().count("updating")
                return (
                    False,
                    f"{update_count} hook(s) have updates \u2014 "
                    f"run: pre-commit autoupdate",
                )
        except (subprocess.TimeoutExpired, OSError):
            pass

    return True, f"{repo_count} repos with {len(revs)} version pins"


def check_workflow_yaml_syntax() -> tuple[bool, str]:
    """Run actionlint via pre-commit if available, report error count.

    Returns:
        Tuple of (passed, message).
    """
    workflows_dir = ROOT / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return True, "No .github/workflows/ directory"

    # Prefer running via pre-commit (manages the binary automatically)
    pre_commit = shutil.which("pre-commit")
    if pre_commit:
        try:
            result = subprocess.run(  # nosec B603
                [pre_commit, "run", "actionlint", "--all-files"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return True, "actionlint (via pre-commit): all workflow files pass"
            error_lines = [
                line
                for line in result.stdout.splitlines()
                if line.strip() and not line.startswith("- hook id:")
            ]
            error_count = len(error_lines)
            return (
                False,
                f"actionlint: {error_count} error(s) in workflow files",
            )
        except (subprocess.TimeoutExpired, OSError):
            pass

    # Fall back to direct actionlint binary
    actionlint = shutil.which("actionlint")
    if actionlint:
        try:
            result = subprocess.run(  # nosec B603
                [actionlint],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, "actionlint: all workflow files pass"
            error_lines = [line for line in result.stdout.splitlines() if line.strip()]
            return (
                False,
                f"actionlint: {len(error_lines)} error(s) in workflow files",
            )
        except (subprocess.TimeoutExpired, OSError):
            pass

    return True, "actionlint not available \u2014 skipping workflow lint"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

CHECKS = [
    ("OS / Platform", check_os_platform),
    ("Python version", check_python_version),
    ("Architecture", check_architecture),
    ("pip", check_pip_version),
    ("Disk space", check_disk_space),
    ("Git repository", check_git_repo),
    ("Git user config", check_git_user_config),
    ("Git remote", check_git_remote),
    ("pyproject.toml", check_pyproject_toml),
    ("Virtual environment", check_venv_active),
    ("Editable install", check_editable_install),
    ("Hatch", check_hatch),
    ("Hatch default env", check_hatch_env_exists),
    ("Task runner", check_task),
    ("Pre-commit hooks", check_pre_commit_hooks),
]

# Additional optional checks with richer output than simple tool availability.
# Placed here (after function definitions) to avoid forward references.
OPTIONAL_CHECKS = [
    ("Node.js", check_node_available),
    ("Container runtime", check_container_runtime),
]

# Extended checks — deeper project consistency validation.
# Warnings unless --strict is set.
EXTENDED_CHECKS: list[tuple[str, Callable[[], tuple[bool, str]]]] = [
    ("Dependency freshness", check_dependency_freshness),
    ("Python version consistency", check_python_version_consistency),
    ("Stale Hatch environments", check_stale_hatch_envs),
    ("License format", check_license_format),
    ("Encoding / BOM", check_encoding_bom),
    ("Orphaned test files", check_orphaned_test_files),
    ("Import cycles", check_import_cycles),
    ("Pre-commit config staleness", check_precommit_config_staleness),
    ("Workflow YAML syntax", check_workflow_yaml_syntax),
]


def _total_check_count() -> int:
    """Return the total number of checks that will run."""
    return (
        len(CHECKS)
        + len(EXPECTED_TOOLS)
        + len(OPTIONAL_TOOLS)
        + len(OPTIONAL_CHECKS)
        + len(EXTENDED_CHECKS)
    )


def _collect_results(
    strict: bool = False,
    on_progress: Callable[[str], None] | None = None,
) -> tuple[list[dict[str, str]], int]:
    """Run all checks and collect structured results.

    Args:
        strict: If True, treat optional items as required.
        on_progress: Optional callback invoked with the check name
            after each check completes (drives the progress bar).

    Returns:
        Tuple of (list of result dicts, failure count).
    """
    optional_checks = {
        "Task runner",
        "Architecture",
        "OS / Platform",
        "pip",
        "Disk space",
        "Git remote",
        "Hatch default env",
    }
    results: list[dict[str, str]] = []
    failures = 0

    def _tick(name: str) -> None:
        if on_progress:
            on_progress(name)

    # Core checks
    for name, check_fn in CHECKS:
        passed, msg = check_fn()
        status = "PASS" if passed else "FAIL"
        if not passed and name in optional_checks and not strict:
            status = "WARN"
        else:
            if not passed:
                failures += 1
        results.append(
            {"name": name, "status": status, "message": msg, "group": "core"}
        )
        _tick(name)

    # Required dev tools
    for tool in EXPECTED_TOOLS:
        passed, msg = check_tool_available(tool)
        status = "PASS" if passed else "FAIL"
        if not passed:
            failures += 1
        results.append(
            {"name": tool, "status": status, "message": msg, "group": "tools"}
        )
        _tick(tool)

    # Optional tools
    for tool in OPTIONAL_TOOLS:
        passed, msg = check_tool_available(tool)
        status = "PASS" if passed else "WARN"
        if not passed and strict:
            status = "FAIL"
            failures += 1
        results.append(
            {
                "name": tool,
                "status": status,
                "message": msg,
                "group": "optional",
            }
        )
        _tick(tool)

    # Optional checks (richer than simple tool lookup)
    for name, check_fn in OPTIONAL_CHECKS:
        passed, msg = check_fn()
        status = "PASS" if passed else "WARN"
        if not passed and strict:
            status = "FAIL"
            failures += 1
        results.append(
            {"name": name, "status": status, "message": msg, "group": "optional"}
        )
        _tick(name)

    # Extended checks (project consistency)
    for name, check_fn in EXTENDED_CHECKS:
        passed, msg = check_fn()
        status = "PASS" if passed else "WARN"
        if not passed and strict:
            status = "FAIL"
            failures += 1
        results.append(
            {"name": name, "status": status, "message": msg, "group": "extended"}
        )
        _tick(name)

    return results, failures


def run_checks(
    strict: bool = False,
    *,
    color: bool | None = None,
    output_json: bool = False,
) -> int:
    """Run all environment checks and print results.

    Args:
        strict: If True, treat warnings (Task not found) as failures.
        color: Force color on/off. None = auto-detect.
        output_json: If True, output results as JSON instead of text.

    Returns:
        Exit code: 0 if all passed, 1 if any failed.
    """
    elapsed_start = time.monotonic()

    # Show a progress bar while checks run (interactive terminals only).
    # JSON mode skips the bar since only machine-readable output matters.
    total = _total_check_count()
    bar: ProgressBar | None = None
    if not output_json:
        bar = ProgressBar(total=total, label="Checking", color="green", pulse=True)
        bar.start_pulse()  # start smooth animation immediately

    def _on_progress(name: str) -> None:
        if bar is not None:
            bar.update(name)

    results, failures = _collect_results(strict, on_progress=_on_progress)

    if bar is not None:
        bar.finish()

    if output_json:
        total = len(results)
        passed_count = total - failures
        payload = {
            "version": SCRIPT_VERSION,
            "total": total,
            "passed": passed_count,
            "failed": failures,
            "checks": results,
        }
        print(json.dumps(payload, indent=2))
        return 1 if failures else 0

    use_color = color if color is not None else _supports_color(sys.stdout)
    c = Colors(enabled=use_color)
    ui = UI(
        title="Environment Health Check",
        version=SCRIPT_VERSION,
        theme=THEME,
        no_color=not use_color,
    )

    ui.header()

    # Core checks
    ui.section("Core")
    for r in results:
        if r["group"] == "core":
            print(
                f"  [{_icon(r['status'], use_color=use_color)}]"
                f" {c.cyan(r['name'] + ':')} {r['message']}"
            )

    # Dev tool checks
    ui.section("Development Tools")
    for r in results:
        if r["group"] in ("tools", "optional"):
            print(f"  [{_icon(r['status'], use_color=use_color)}] {r['message']}")

    # Extended checks
    extended = [r for r in results if r["group"] == "extended"]
    if extended:
        ui.section("Extended Checks")
        for r in extended:
            print(
                f"  [{_icon(r['status'], use_color=use_color)}]"
                f" {c.cyan(r['name'] + ':')} {r['message']}"
            )

    # Summary
    elapsed = time.monotonic() - elapsed_start
    total = len(results)
    passed_count = total - failures
    warned = 0

    # ── Recommended Scripts ──
    ui.recommended_scripts(
        [
            "repo_sauron",
            "env_inspect",
            "repo_doctor",
            "dep_versions",
            "doctor",
        ],
        preamble="Scripts that expand on environment and health diagnostics.",
    )

    ui.footer(passed=passed_count, failed=failures, warned=warned, elapsed=elapsed)

    return 1 if failures else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point for env_doctor.

    Returns:
        Exit code from run_checks().
    """
    parser = argparse.ArgumentParser(
        description="Quick environment health check for development.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat optional tool warnings as failures",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (for CI integration)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick import and arg-parse health check; exit 0 immediately",
    )
    args = parser.parse_args()

    if args.smoke:
        print(f"env_doctor {SCRIPT_VERSION}: smoke ok")
        return 0

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    color = False if args.no_color else None
    return run_checks(strict=args.strict, color=color, output_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
