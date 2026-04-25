#!/usr/bin/env python3
"""Environment and dependency inspector — full inventory of your setup.

Shows a comprehensive view of your development environment:
  - Python version, location, implementation, and supported versions
  - Duplicate Python installations on the system
  - Git version and location
  - Virtual environment status (global vs local)
  - Installed packages grouped by installation location (global, venv, Hatch, etc.)
  - Duplicate package detection across environments
  - Entry points registered by installed packages (with removal instructions)
  - Build and environment tools found on PATH (hatch, tox, nox, etc.)
  - Python version support validation (cross-checks pyproject.toml sources)
  - Key PATH directories with duplicate detection
  - System environment summary
  - Related scripts for further investigation

This complements ``dep_versions.py`` (which focuses on project deps
declared in pyproject.toml) by showing the full picture including
globally installed packages, entry points, and PATH.

Flags::

    --json              Output as JSON (for CI integration)
    --section SECTION   Only show a specific section
                        (python, git, venv, packages, entrypoints,
                         build-tools, python-support, path,
                         python-installs, system)
    -q, --quiet         Suppress output; exit code only
    --no-color          Disable colored output
    --version           Print version and exit

Usage::

    python scripts/env_inspect.py
    python scripts/env_inspect.py --json
    python scripts/env_inspect.py --section packages
    python scripts/env_inspect.py --section build-tools
    python scripts/env_inspect.py --section python-support
    python scripts/env_inspect.py --section path
    python scripts/env_inspect.py --section python-installs
    python scripts/env_inspect.py --section system

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in other repos. Requires shared modules from this repo's
    scripts/ directory: ``_colors.py``, ``_imports.py``, ``_progress.py``,
    ``_ui.py``.  Also optionally imports ``check_python_support.py`` for
    the python-support section.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.metadata
import json
import logging
import os
import platform
import re
import shutil
import subprocess  # nosec B404
import sys
import textwrap
import time
import tomllib
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors
from _imports import find_repo_root
from _progress import Spinner
from _ui import UI, Spacing

log = logging.getLogger(__name__)

SCRIPT_VERSION = "2.0.0"
THEME = "cyan"

ROOT = find_repo_root()


# ---------------------------------------------------------------------------
# Python info
# ---------------------------------------------------------------------------


def _python_info() -> dict:
    """Gather Python interpreter details."""
    info: dict = {
        "version": platform.python_version(),
        "version_tuple": list(sys.version_info[:3]),
        "implementation": platform.python_implementation(),
        "compiler": platform.python_compiler(),
        "executable": sys.executable,
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
        "in_venv": sys.prefix != sys.base_prefix,
        "platform": platform.platform(),
        "architecture": platform.machine(),
    }

    # Project-supported versions from pyproject.toml
    pyproject = ROOT / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            info["requires_python"] = data.get("project", {}).get("requires-python", "")
            classifiers = data.get("project", {}).get("classifiers", [])
            supported = []
            for c in classifiers:
                m = re.match(r"Programming Language :: Python :: (\d+\.\d+)$", c)
                if m:
                    supported.append(m.group(1))
            info["supported_versions"] = supported
        except (OSError, ValueError):
            pass

    return info


# ---------------------------------------------------------------------------
# Git info
# ---------------------------------------------------------------------------


def _git_info() -> dict:
    """Gather git version and location."""
    git_cmd = shutil.which("git")
    info: dict = {"available": git_cmd is not None, "path": git_cmd}

    if git_cmd:
        try:
            result = subprocess.run(  # nosec B603
                [git_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                m = re.search(r"(\d+\.\d+[\.\d]*)", result.stdout)
                info["version"] = m.group(1) if m else result.stdout.strip()
        except (subprocess.TimeoutExpired, OSError):
            pass

    return info


# ---------------------------------------------------------------------------
# Package inventory
# ---------------------------------------------------------------------------


def _all_installed_packages() -> list[dict]:
    """List all packages installed in the current environment.

    Returns all discovered distributions including duplicates (same name
    at different locations). The caller is responsible for deduplication
    if a unique list is needed.
    """
    packages = []
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"]
        version = dist.metadata["Version"]
        summary = dist.metadata.get("Summary", "")
        location = str(dist._path.parent) if hasattr(dist, "_path") else ""

        packages.append(
            {
                "name": name,
                "version": version,
                "summary": summary or "",
                "location": location,
            }
        )

    return sorted(packages, key=lambda p: (p["name"] or "").lower())


def _deduplicate_packages(packages: list[dict]) -> list[dict]:
    """Deduplicate packages by name, keeping the first occurrence."""
    seen: set[str] = set()
    unique: list[dict] = []
    for pkg in packages:
        key = (pkg["name"] or "").lower()
        if key not in seen:
            seen.add(key)
            unique.append(pkg)
    return unique


def _check_outdated_packages() -> dict[str, str]:
    """Use pip to find outdated packages. Returns {name: latest_version}."""
    try:
        result = subprocess.run(  # nosec B603
            [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {pkg["name"].lower(): pkg["latest_version"] for pkg in data}
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        pass
    return {}


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def _collect_entry_points() -> list[dict]:
    """Collect console_scripts entry points from installed packages."""
    entries = [
        {"name": ep.name, "value": ep.value, "group": "console_scripts"}
        for ep in importlib.metadata.entry_points(group="console_scripts")
    ]
    entries.extend(
        {"name": ep.name, "value": ep.value, "group": "gui_scripts"}
        for ep in importlib.metadata.entry_points(group="gui_scripts")
    )

    return sorted(entries, key=lambda e: e["name"])


# ---------------------------------------------------------------------------
# PATH inspection
# ---------------------------------------------------------------------------


def _inspect_path() -> list[dict]:
    """Inspect PATH directories and count executables in each."""
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    results = []
    seen: set[str] = set()

    for dir_path in path_dirs:
        # Normalize for duplicate detection (case-insensitive on Windows)
        normalized = str(Path(dir_path).resolve()).casefold()
        is_duplicate = normalized in seen
        seen.add(normalized)

        p = Path(dir_path)
        if not p.is_dir():
            results.append(
                {
                    "path": dir_path,
                    "exists": False,
                    "executable_count": 0,
                    "duplicate": is_duplicate,
                }
            )
            continue

        try:
            executables = sum(
                1 for f in p.iterdir() if f.is_file() and os.access(f, os.X_OK)
            )
        except (PermissionError, OSError):
            executables = 0

        results.append(
            {
                "path": dir_path,
                "exists": True,
                "executable_count": executables,
                "duplicate": is_duplicate,
            }
        )

    return results


# ---------------------------------------------------------------------------
# Hatch env status
# ---------------------------------------------------------------------------


def _hatch_info() -> dict | None:
    """Get Hatch environment info if hatch is available."""
    hatch = shutil.which("hatch")
    if not hatch:
        return None

    info: dict = {"available": True, "path": hatch}

    try:
        result = subprocess.run(  # nosec B603
            [hatch, "version"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=ROOT,
        )
        if result.returncode == 0:
            info["version"] = result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass

    try:
        result = subprocess.run(  # nosec B603
            [hatch, "env", "show", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=ROOT,
        )
        if result.returncode == 0:
            with contextlib.suppress(json.JSONDecodeError):
                info["environments"] = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, OSError):
        pass

    return info


# ---------------------------------------------------------------------------
# Discover Python installations on the system
# ---------------------------------------------------------------------------


def _find_python_installations() -> list[dict]:
    """Find all Python installations on the system.

    Searches PATH and common install locations for python executables,
    returning version and path info for each unique installation found.
    """
    pythons: list[dict] = []
    seen_paths: set[str] = set()

    # Candidate executable names
    candidates = [
        "python3",
        "python",
        "python3.11",
        "python3.12",
        "python3.13",
        "python3.14",
    ]
    if sys.platform == "win32":
        candidates.extend(["py", "python.exe"])

    for name in candidates:
        path = shutil.which(name)
        if not path:
            continue
        resolved = str(Path(path).resolve())
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)

        version = ""
        implementation = ""
        try:
            result = subprocess.run(  # nosec B603
                [
                    path,
                    "-c",
                    "import sys, platform; "
                    "print(platform.python_version()); "
                    "print(platform.python_implementation())",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().splitlines()
                version = lines[0] if lines else ""
                implementation = lines[1] if len(lines) > 1 else ""
        except (subprocess.TimeoutExpired, OSError):
            pass

        pythons.append(
            {
                "name": name,
                "path": resolved,
                "version": version,
                "implementation": implementation,
            }
        )

    # Also try the Windows `py` launcher to discover all installed versions
    if sys.platform == "win32":
        py_cmd = shutil.which("py")
        if py_cmd:
            try:
                result = subprocess.run(  # nosec B603
                    [py_cmd, "--list-paths"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().splitlines():
                        # Format: " -V-32    C:\...\python.exe" or similar
                        m = re.match(r"\s*-V?:?(\S+)\s+(.+)", line)
                        if not m:
                            # Alternate format: " -3.12-64  C:\...\python.exe *"
                            m = re.match(r"\s*-(\S+)\s+(.+?)(?:\s+\*)?$", line)
                        if m:
                            py_path = m.group(2).strip().rstrip(" *")
                            resolved = str(Path(py_path).resolve())
                            if resolved not in seen_paths:
                                seen_paths.add(resolved)
                                # Get version from the executable itself
                                ver = ""
                                impl = ""
                                try:
                                    r2 = subprocess.run(  # nosec B603
                                        [
                                            py_path,
                                            "-c",
                                            "import platform; "
                                            "print(platform.python_version()); "
                                            "print(platform.python_implementation())",
                                        ],
                                        capture_output=True,
                                        text=True,
                                        timeout=10,
                                    )
                                    if r2.returncode == 0:
                                        ls = r2.stdout.strip().splitlines()
                                        ver = ls[0] if ls else ""
                                        impl = ls[1] if len(ls) > 1 else ""
                                except (subprocess.TimeoutExpired, OSError):
                                    pass
                                pythons.append(
                                    {
                                        "name": f"py {m.group(1)}",
                                        "path": resolved,
                                        "version": ver,
                                        "implementation": impl,
                                    }
                                )
            except (subprocess.TimeoutExpired, OSError):
                pass

    return pythons


# ---------------------------------------------------------------------------
# Package location categorization
# ---------------------------------------------------------------------------


def _categorize_location(location: str) -> str:
    """Classify a package installation path into a human-readable category.

    Returns a category string like 'Global (system)', 'Virtual Environment',
    'Hatch Environment', etc.
    """
    if not location:
        return "Unknown"

    loc_lower = location.lower().replace("\\", "/")

    # Hatch environments
    if "/.local/share/hatch/" in loc_lower or "/hatch/env/" in loc_lower:
        # Try to extract the env name
        for pattern in [r"hatch/env[s]?/([^/]+)", r"hatch/([^/]+)/lib"]:
            m = re.search(pattern, loc_lower)
            if m:
                return f"Hatch ({m.group(1)})"
        return "Hatch Environment"

    # Windows AppData hatch
    if "appdata" in loc_lower and "hatch" in loc_lower:
        m = re.search(r"hatch/env[s]?/([^/]+)", loc_lower)
        if m:
            return f"Hatch ({m.group(1)})"
        return "Hatch Environment"

    # Tox environments
    if "/.tox/" in loc_lower or "\\.tox\\" in location.lower():
        m = re.search(r"\.tox/([^/\\]+)", loc_lower)
        if m:
            return f"Tox ({m.group(1)})"
        return "Tox Environment"

    # Nox environments
    if "/.nox/" in loc_lower or "\\.nox\\" in location.lower():
        m = re.search(r"\.nox/([^/\\]+)", loc_lower)
        if m:
            return f"Nox ({m.group(1)})"
        return "Nox Environment"

    # Poetry environments
    if "/pypoetry/" in loc_lower:
        return "Poetry Environment"

    # Conda environments
    if "/conda/" in loc_lower or "/envs/" in loc_lower:
        m = re.search(r"envs/([^/\\]+)", loc_lower)
        if m:
            return f"Conda ({m.group(1)})"
        return "Conda Environment"

    # Generic virtual environment
    if (
        "/.venv/" in loc_lower
        or "/venv/" in loc_lower
        or "\\.venv\\" in location.lower()
        or "\\venv\\" in location.lower()
    ):
        return "Virtual Environment (.venv)"

    # pipx
    if "/pipx/" in loc_lower:
        return "pipx"

    # User site-packages (--user installs)
    if "/site-packages" in loc_lower and (
        "/.local/" in loc_lower or "/appdata/" in loc_lower
    ):
        # Check if it's inside a venv by comparing with sys.prefix
        if sys.prefix != sys.base_prefix:
            return "Virtual Environment"
        return "User (--user)"

    # If it's inside sys.prefix and we're in a venv, it's the active venv
    if sys.prefix != sys.base_prefix:
        prefix_norm = sys.prefix.lower().replace("\\", "/")
        if loc_lower.startswith(prefix_norm):
            return "Virtual Environment (active)"

    # System/global Python
    base_norm = sys.base_prefix.lower().replace("\\", "/")
    if loc_lower.startswith(base_norm):
        return "Global (system)"

    return "Global (system)"


def _group_packages_by_location(packages: list[dict]) -> dict[str, list[dict]]:
    """Group packages by their installation location category."""
    groups: dict[str, list[dict]] = {}
    for pkg in packages:
        category = _categorize_location(pkg.get("location", ""))
        groups.setdefault(category, []).append(pkg)
    return groups


def _find_duplicate_packages(packages: list[dict]) -> dict[str, list[dict]]:
    """Find packages installed in multiple locations.

    Returns {package_name: [list of package entries from different locations]}.
    Only includes packages found in more than one distinct location.
    """
    by_name: dict[str, list[dict]] = {}
    for pkg in packages:
        key = (pkg.get("name") or "").lower()
        if key:
            by_name.setdefault(key, []).append(pkg)

    # Keep only those with multiple distinct locations
    duplicates: dict[str, list[dict]] = {}
    for name, entries in by_name.items():
        locations = {e.get("location", "") for e in entries}
        if len(locations) > 1:
            duplicates[name] = entries
    return duplicates


# ---------------------------------------------------------------------------
# System environment summary
# ---------------------------------------------------------------------------


def _system_env_summary() -> dict:
    """Gather system environment info relevant to Python development."""
    env = os.environ
    info: dict = {
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "hostname": platform.node(),
        "cpu_count": os.cpu_count(),
        "encoding": sys.getdefaultencoding(),
        "filesystem_encoding": sys.getfilesystemencoding(),
    }

    # Virtual env indicators
    if env.get("VIRTUAL_ENV"):
        info["VIRTUAL_ENV"] = env["VIRTUAL_ENV"]
    if env.get("CONDA_DEFAULT_ENV"):
        info["CONDA_DEFAULT_ENV"] = env["CONDA_DEFAULT_ENV"]
    if env.get("HATCH_ENV_ACTIVE"):
        info["HATCH_ENV_ACTIVE"] = env["HATCH_ENV_ACTIVE"]

    return info


# ---------------------------------------------------------------------------
# Main collector
# ---------------------------------------------------------------------------


def gather_env_info(*, check_updates: bool = True) -> dict:
    """Gather all environment information."""
    all_packages = _all_installed_packages()
    packages = _deduplicate_packages(all_packages)
    info: dict = {
        "python": _python_info(),
        "git": _git_info(),
        "packages": packages,
        "packages_by_location": _group_packages_by_location(all_packages),
        "duplicate_packages": _find_duplicate_packages(all_packages),
        "python_installations": _find_python_installations(),
        "entry_points": _collect_entry_points(),
        "path": _inspect_path(),
        "system": _system_env_summary(),
    }

    if check_updates:
        info["outdated"] = _check_outdated_packages()

    # Build system info from pyproject.toml
    pyproject = ROOT / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            build_sys = data.get("build-system", {})
            info["build_backend"] = build_sys.get("build-backend", "")
            info["build_requires"] = build_sys.get("requires", [])
        except (OSError, ValueError):
            pass

    hatch = _hatch_info()
    if hatch:
        info["hatch"] = hatch

    return info


# ---------------------------------------------------------------------------
# Build tools detection
# ---------------------------------------------------------------------------

_BUILD_TOOLS: list[tuple[str, str, list[str]]] = [
    # (display_name, executable, version_args)
    ("Hatch", "hatch", ["--version"]),
    ("tox", "tox", ["--version"]),
    ("nox", "nox", ["--version"]),
    ("Poetry", "poetry", ["--version"]),
    ("PDM", "pdm", ["--version"]),
    ("Flit", "flit", ["--version"]),
    ("pip", "pip", ["--version"]),
    ("pipx", "pipx", ["--version"]),
    ("uv", "uv", ["--version"]),
    ("conda", "conda", ["--version"]),
    ("mamba", "mamba", ["--version"]),
    ("virtualenv", "virtualenv", ["--version"]),
]


def _detect_build_tools() -> list[dict]:
    """Detect installed build/environment tools."""
    tools = []
    for name, exe, ver_args in _BUILD_TOOLS:
        path = shutil.which(exe)
        if not path:
            continue
        version = "unknown"
        try:
            result = subprocess.run(  # nosec B603
                [path, *ver_args],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if result.returncode == 0:
                # Extract version from output (first line, strip tool name)
                out = (result.stdout + result.stderr).strip().splitlines()[0]
                # Try to find a version-like pattern
                m = re.search(r"(\d+\.\d+[\w.+-]*)", out)
                version = m.group(1) if m else out.strip()
        except (subprocess.TimeoutExpired, OSError):
            pass
        tools.append(
            {"name": name, "executable": exe, "path": path, "version": version}
        )
    return tools


# ---------------------------------------------------------------------------
# Python support validation
# ---------------------------------------------------------------------------


def _check_python_support_summary() -> dict | None:
    """Run a lightweight python-support check and return a summary.

    Imports from check_python_support.py to get version consistency data.
    Returns None if the check is unavailable.
    """
    try:
        # Import inline to avoid hard dependency
        from check_python_support import check_python_support

        result = check_python_support(quiet=True, no_color=True)
        return {
            "ok": result["ok"],
            "sources": result.get("sources", {}),
            "mismatches": result.get("mismatches", []),
            "current_meets_minimum": result.get("current_meets_minimum", True),
            "code_min_version": result.get("code_analysis", {}).get("code_min_version"),
        }
    except Exception:
        return None


def print_env_info(
    info: dict,
    *,
    no_color: bool = False,
    section: str | None = None,
) -> None:
    """Print environment info as a dashboard."""
    c = Colors(enabled=not no_color)
    ui = UI(
        title="Environment Inspector",
        version=SCRIPT_VERSION,
        theme=THEME,
        no_color=no_color,
        spacing=Spacing(kv_gap=1, progress_pulse=True, command_wrap=True),
    )
    ui.header()
    ui.blank()
    ui.info_line(c.magenta("Comprehensive snapshot of your development environment."))
    ui.info_line(
        c.magenta("Use --section <name> to focus on a single area, or --json for CI.")
    )

    show_all = section is None

    # ── Python ──
    if show_all or section == "python":
        py = info["python"]
        ui.section("Python")
        ui.info_line(
            c.magenta(
                "Core Python runtime info. Verify the version matches your project's"
            )
        )
        ui.info_line(
            c.magenta(
                "requires-python constraint and that you're using the right executable."
            )
        )
        ui.blank()
        ui.kv("Version", py["version"])
        ui.kv("Implementation", c.magenta(py["implementation"]))
        ui.kv("Compiler", py.get("compiler", "unknown"))
        ui.kv("Executable", py["executable"])
        ui.kv("Platform", py["platform"])
        ui.kv("Architecture", py["architecture"])
        ui.kv("In virtualenv", c.green("Yes") if py["in_venv"] else c.yellow("No"))
        if py.get("requires_python"):
            ui.kv("requires-python", py["requires_python"])
        if py.get("supported_versions"):
            ui.kv("Supported versions", ", ".join(py["supported_versions"]))

            # Check if current version is in the supported list
            current = f"{sys.version_info.major}.{sys.version_info.minor}"
            if current in py["supported_versions"]:
                ui.status_line(
                    "check", f"Current Python {current} is supported", "green"
                )
            else:
                ui.status_line(
                    "warn", f"Current Python {current} not in supported list", "yellow"
                )

    # ── Python Installations ──
    if show_all or section == "python-installs":
        py_installs = info.get("python_installations", [])
        ui.section(f"Python Installations ({len(py_installs)})")
        ui.info_line(
            c.magenta("All Python installations found on your system. Duplicate")
        )
        ui.info_line(
            c.magenta("installations can cause confusion about which Python is used.")
        )
        ui.blank()
        if py_installs:
            ui.table_header(
                [
                    ("Name", 16),
                    ("Version", 12),
                    ("Impl", 10),
                    ("Path", 36),
                ],
                themed=True,
            )
            # Detect duplicate versions
            version_counts: dict[str, int] = {}
            for inst in py_installs:
                v = inst.get("version", "")
                if v:
                    version_counts[v] = version_counts.get(v, 0) + 1

            for inst in py_installs:
                name = inst.get("name", "")
                ver = inst.get("version", "unknown")
                impl = inst.get("implementation", "")
                path = inst.get("path", "")

                # Flag current interpreter
                is_current = Path(path).resolve() == Path(sys.executable).resolve()
                name_display = c.green(name) if is_current else name
                if is_current:
                    name_display = name_display + c.dim(" *")

                # Flag duplicates (same version, different path)
                is_dup = version_counts.get(ver, 0) > 1
                ver_display = c.yellow(ver) if is_dup else ver

                # Truncate path
                path_display = path
                if len(path_display) > 36:
                    path_display = "..." + path_display[-33:]

                ui.table_row(
                    [
                        (name_display, 16),
                        (ver_display, 12),
                        (c.magenta(impl) if impl else c.dim("-"), 10),
                        (c.dim(path_display), 36),
                    ]
                )

            # Check for actual duplicates (same version, different paths)
            dup_versions = [v for v, count in version_counts.items() if count > 1]
            if dup_versions:
                ui.blank()
                ui.status_line(
                    "warn",
                    f"Duplicate Python version(s) found: {', '.join(dup_versions)} "
                    "— ensure you're using the intended installation",
                    "yellow",
                )
            if any(
                Path(inst.get("path", "")).resolve() == Path(sys.executable).resolve()
                for inst in py_installs
            ):
                ui.blank()
                ui.info_line(c.dim("* = currently active Python interpreter"))
        else:
            ui.info_line("No Python installations detected on PATH.")

    # ── Git ──
    if show_all or section == "git":
        git = info["git"]
        ui.section("Git")
        ui.info_line(
            c.magenta("Git is required for version control and hatch-vcs versioning.")
        )
        ui.blank()
        if git["available"]:
            ui.kv("Version", git.get("version", "unknown"), width=14)
            ui.kv("Path", git["path"] or "unknown", width=14)
        else:
            ui.status_line("cross", "Git not found on PATH", "red")

    # ── Virtual Environment ──
    if show_all or section == "venv":
        py = info["python"]
        ui.section("Virtual Environment")
        ui.info_line(c.magenta("Shows whether you're inside a virtual environment."))
        ui.info_line(
            c.magenta("Working inside a venv prevents polluting the global Python.")
        )
        ui.blank()
        # Detect workflow tool dynamically
        hatch_info = info.get("hatch")
        env_cmd = "hatch shell" if hatch_info else "your env manager's shell command"
        if py["in_venv"]:
            ui.kv("Status", c.green("Active"), width=14)
            ui.kv("Prefix", py["prefix"], width=14)
            ui.kv("Base prefix", py["base_prefix"], width=14)
        else:
            ui.kv("Status", c.yellow("Not in a virtualenv"), width=14)
            ui.info_line(f"Run '{env_cmd}' to enter the dev environment.")

    # ── Hatch / Build System ──
    if show_all and info.get("hatch"):
        hatch = info["hatch"]
        ui.section("Hatch")
        ui.info_line(c.magenta("Hatch manages environments and builds."))
        print(
            f"    {c.dim('Use')}"
            f" {ui._command_styled('hatch shell')}"
            f" {c.dim('to enter the dev environment.')}"
        )
        ui.blank()
        ui.kv("Version", hatch.get("version", "unknown"), width=18)
        ui.kv("Path", hatch.get("path", "unknown"), width=18)
        # Show build backend dynamically
        build_backend = info.get("build_backend", "")
        if build_backend:
            ui.kv("Build backend", build_backend, width=18)
        build_requires = info.get("build_requires", [])
        if build_requires:
            ui.kv("Build requires", ", ".join(build_requires), width=18)

    # ── Packages ──
    if show_all or section == "packages":
        packages = info["packages"]
        outdated = info.get("outdated", {})
        packages_by_loc = info.get("packages_by_location", {})
        duplicate_pkgs = info.get("duplicate_packages", {})

        ui.section(f"Installed Packages ({len(packages)})")
        ui.info_line(
            c.magenta("All packages in the current environment, grouped by install")
        )
        ui.info_line(
            "location. Run "
            + ui._command_styled("python scripts/dep_versions.py")
            + c.dim(" for project dep details.")
        )

        # Show packages grouped by location
        for location_name in sorted(packages_by_loc.keys()):
            loc_packages = packages_by_loc[location_name]
            ui.blank()
            print(
                f"    {c.bold(c.magenta(location_name))}"
                f"  {c.dim(f'({len(loc_packages)} package(s)')}"
            )
            ui.blank()

            ui.table_header(
                [
                    ("Package", 30),
                    ("Version", 16),
                    ("Latest", 14),
                    ("Status", 10),
                ],
                themed=True,
            )

            for pkg in sorted(loc_packages, key=lambda p: (p["name"] or "").lower()):
                name = pkg["name"] or ""
                ver = pkg["version"] or ""
                name_lower = name.lower()
                latest = outdated.get(name_lower, "")

                is_dup = name_lower in duplicate_pkgs
                if latest and latest != ver:
                    status = c.yellow("outdated")
                    name_col = c.yellow(name)
                elif is_dup:
                    status = c.magenta("dup")
                    name_col = c.magenta(name)
                else:
                    status = c.green("ok") if ver else c.dim("-")
                    name_col = name

                ver_display = ver if len(ver) <= 15 else ver[:12] + "..."
                latest_display = latest if len(latest) <= 13 else latest[:10] + "..."

                ui.table_row(
                    [
                        (name_col, 30),
                        (ver_display, 16),
                        (latest_display or c.dim("-"), 14),
                        (status, 10),
                    ]
                )

        # Duplicate packages summary
        if duplicate_pkgs:
            ui.blank()
            ui.status_line(
                "warn",
                f"{len(duplicate_pkgs)} package(s) installed in multiple locations",
                "yellow",
            )
            for dup_name, dup_entries in sorted(duplicate_pkgs.items()):
                locations = [
                    _categorize_location(e.get("location", "")) for e in dup_entries
                ]
                versions = [e.get("version", "?") for e in dup_entries]
                loc_ver = ", ".join(
                    f"{loc} (v{ver})"
                    for loc, ver in zip(locations, versions, strict=True)
                )
                ui.info_line(f"  {c.magenta(dup_name)}: {loc_ver}")

        outdated_count = len(outdated)
        ui.blank()
        ui.info_line(
            f"{len(packages)} package(s) installed across "
            f"{len(packages_by_loc)} location(s)"
            + (f", {outdated_count} outdated" if outdated_count else "")
        )

    # ── Entry Points ──
    if show_all or section == "entrypoints":
        eps = info["entry_points"]
        ui.section(f"Entry Points ({len(eps)})")
        ui.info_line(
            c.magenta("Console commands registered by installed packages. These are")
        )
        ui.info_line(
            c.magenta("the CLI tools available in your environment. If your package")
        )
        ui.info_line(
            c.magenta("defines [project.scripts] in pyproject.toml, its commands")
        )
        ui.info_line(c.magenta("appear here after installation."))
        ui.blank()
        # Note about terminal availability
        py = info["python"]
        if py["in_venv"]:
            ui.info_line(
                c.dim("Note: these entry points are available in any terminal where")
            )
            ui.info_line(
                c.dim("this virtual environment is activated. They are NOT available")
            )
            ui.info_line(c.dim("in terminals using a different Python environment."))
        else:
            ui.info_line(
                c.dim("Note: these entry points are available in any terminal on your")
            )
            ui.info_line(c.dim("system where this Python installation is on PATH."))
        ui.blank()
        if eps:
            cmd_col = 30
            target_col = 40
            ui.table_header(
                [("Command", cmd_col), ("Target", target_col)],
                themed=True,
            )
            for ep in eps:
                cmd_raw = ep["name"]
                target_raw = ep["value"]

                # Wrap both columns independently for long text
                cmd_lines = textwrap.wrap(
                    cmd_raw,
                    width=cmd_col,
                    break_on_hyphens=True,
                ) or [cmd_raw]
                target_lines = textwrap.wrap(
                    target_raw,
                    width=target_col,
                    break_on_hyphens=False,
                ) or [target_raw]

                row_lines = max(len(cmd_lines), len(target_lines))
                for i in range(row_lines):
                    cmd_part = cmd_lines[i] if i < len(cmd_lines) else ""
                    tgt_part = target_lines[i] if i < len(target_lines) else ""
                    ui.table_row(
                        [
                            (c.green(cmd_part), cmd_col),
                            (c.magenta(tgt_part), target_col),
                        ]
                    )
                # Separation line between each entry point for clarity
                sep_w = cmd_col + target_col + 1
                sep_line = ("· " * ((sep_w + 1) // 2))[:sep_w]
                print(f"    {c.dim(sep_line)}")
            # How to remove entry points
            ui.blank()
            ui.info_line(c.bold("Removing an entry point:"))
            ui.info_line(
                "  To remove an unwanted entry point, uninstall the package that"
            )
            ui.info_line("  provides it:")
            ui.blank()
            print(
                f"    {ui._command_styled('pip uninstall <package-name>')}"
                f"  {c.dim('(removes the package and its entry points)')}"
            )
            ui.blank()
            ui.info_line(
                "  If you want to keep the package but remove only the command,"
            )
            ui.info_line("  remove the [project.scripts] entry from its pyproject.toml")
            ui.info_line("  and reinstall:")
            ui.blank()
            print(
                f"    {ui._command_styled('pip install -e .')}"
                f"  {c.dim('(reinstalls without the removed entry point)')}"
            )
        else:
            ui.info_line("No console_scripts or gui_scripts entry points found.")

    # ── Build Tools ──
    if show_all or section == "build-tools":
        build_tools = info.get("build_tools", [])
        ui.section(f"Build & Environment Tools ({len(build_tools)})")
        ui.info_line(
            c.magenta("Build tools, environment managers, and package installers found")
        )
        ui.info_line(
            c.magenta("on PATH. Verify the expected tool is available and up to date.")
        )
        ui.blank()
        if build_tools:
            ui.table_header(
                [("Tool", 14), ("Version", 14), ("Path", 42)],
                themed=True,
            )
            for t in build_tools:
                path_display = t["path"]
                if len(path_display) > 42:
                    path_display = "..." + path_display[-39:]
                ui.table_row(
                    [
                        (c.bold(t["name"]), 14),
                        (t["version"], 14),
                        (c.dim(path_display), 42),
                    ]
                )
        else:
            ui.info_line("No build/environment tools found on PATH.")

    # ── Python Support Validation ──
    if show_all or section == "python-support":
        py_support = info.get("python_support")
        if py_support is not None:
            ui.section("Python Version Support")
            ui.info_line(
                c.magenta(
                    "Cross-checks pyproject.toml, classifiers, env manager matrix,"
                )
            )
            ui.info_line(c.magenta("and CI matrix for version consistency."))
            ui.blank()
            ui.info_line(
                c.magenta("Mismatches here can cause CI failures or user-facing")
            )
            ui.info_line(c.magenta("compatibility issues."))
            ui.blank()
            sources = py_support.get("sources", {})
            if sources.get("requires-python"):
                ui.kv("requires-python", sources["requires-python"])
            if sources.get("classifiers"):
                ui.kv("Classifiers", sources["classifiers"])
            # Show env manager matrix dynamically
            if sources.get("hatch_matrix"):
                ui.kv("Hatch matrix", sources["hatch_matrix"])
            if sources.get("tox_matrix"):
                ui.kv("Tox matrix", sources["tox_matrix"])
            if sources.get("nox_matrix"):
                ui.kv("Nox matrix", sources["nox_matrix"])
            if sources.get("ci_matrix"):
                ui.kv("CI matrix", sources["ci_matrix"])
            if py_support.get("code_min_version"):
                ui.kv("Code min version", py_support["code_min_version"])
            if py_support["ok"]:
                ui.status_line("check", "All version sources consistent", "green")
            else:
                for m in py_support.get("mismatches", []):
                    ui.status_line("cross", m, "red")
            ui.blank()
            if not py_support.get("current_meets_minimum", True):
                ui.status_line("warn", "Current Python does not meet minimum", "yellow")
                ui.blank()
            print(
                f"    {c.dim('Run')}"
                f" {ui._command_styled('python scripts/check_python_support.py')}"
                f" {c.dim('for full analysis')}"
            )

    # ── PATH ──
    if show_all or section == "path":
        path_dirs = info["path"]
        dup_count = sum(1 for d in path_dirs if d.get("duplicate"))
        label = f"PATH Directories ({len(path_dirs)}"
        if dup_count:
            label += f", {dup_count} duplicate{'s' if dup_count != 1 else ''}"
        label += ")"
        ui.section(label)
        ui.info_line(
            c.magenta("Directories on your system PATH. Duplicates waste lookup time.")
        )
        ui.blank()
        print(f"    {ui._themed(c.bold('Directory:'))}")
        ui.info_line("  the path entry")
        ui.blank()
        print(f"    {ui._themed(c.bold('Exists:'))}")
        ui.info_line("  whether it's on disk")
        ui.blank()
        print(f"    {ui._themed(c.bold('Execs:'))}")
        ui.info_line("  number of executable files found")
        ui.blank()
        print(f"    {ui._themed(c.bold('Note:'))}")
        ui.info_line("  flags duplicates")
        ui.blank()
        ui.table_header(
            [
                ("Directory", 42),
                ("Exists", 8),
                ("Execs", 7),
                ("Note", 12),
            ],
            themed=True,
        )
        for d in path_dirs:
            exists_str = c.green("Yes") if d["exists"] else c.red("No")
            exe_count = str(d["executable_count"]) if d["exists"] else c.dim("-")
            note = c.yellow("(duplicate)") if d.get("duplicate") else ""
            # Truncate long paths
            path_display = d["path"]
            if len(path_display) > 42:
                path_display = "..." + path_display[-39:]
            ui.table_row(
                [
                    (path_display, 42),
                    (exists_str, 8),
                    (exe_count, 7),
                    (note, 12),
                ]
            )
        if dup_count:
            ui.blank()
            ui.status_line(
                "warn",
                f"{dup_count} duplicate PATH entr{'ies' if dup_count != 1 else 'y'} "
                "found -- consider cleaning up your PATH",
                "yellow",
            )

    # ── System Environment ──
    if show_all or section == "system":
        sys_info = info.get("system", {})
        ui.section("System Environment")
        ui.info_line(
            c.magenta("System and environment details relevant to Python development.")
        )
        ui.blank()
        ui.kv(
            "OS",
            f"{sys_info.get('os', '?')} {sys_info.get('os_release', '')}",
            width=20,
        )
        ui.kv("OS version", sys_info.get("os_version", "unknown"), width=20)
        ui.kv("Hostname", sys_info.get("hostname", "unknown"), width=20)
        ui.kv("CPU count", str(sys_info.get("cpu_count", "?")), width=20)
        ui.kv("Default encoding", sys_info.get("encoding", "unknown"), width=20)
        ui.kv("FS encoding", sys_info.get("filesystem_encoding", "unknown"), width=20)
        if sys_info.get("VIRTUAL_ENV"):
            ui.kv("VIRTUAL_ENV", sys_info["VIRTUAL_ENV"])
        if sys_info.get("CONDA_DEFAULT_ENV"):
            ui.kv("CONDA_DEFAULT_ENV", sys_info["CONDA_DEFAULT_ENV"])
        if sys_info.get("HATCH_ENV_ACTIVE"):
            ui.kv("HATCH_ENV_ACTIVE", sys_info["HATCH_ENV_ACTIVE"])

    # ── Recommended Scripts ──
    if show_all:
        ui.recommended_scripts(
            [
                "check_python_support",
                "dep_versions",
                "env_doctor",
                "doctor",
                "repo_sauron",
            ],
            preamble="Scripts that expand on environment information and health checks.",
        )

    ui.blank()
    ui.separator(double=True, themed=True)
    print()


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="env-inspect",
        description="Environment and dependency inspector.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )
    parser.add_argument(
        "--section",
        choices=[
            "python",
            "python-installs",
            "git",
            "venv",
            "packages",
            "entrypoints",
            "build-tools",
            "python-support",
            "path",
            "system",
        ],
        help="Only show a specific section",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output; exit code only",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick import and arg-parse health check; exit 0 immediately",
    )
    args = parser.parse_args()

    if args.smoke:
        print(f"env_inspect {SCRIPT_VERSION}: smoke ok")
        return 0

    level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(format="%(message)s", level=level)

    start = time.monotonic()
    # Only check for package updates when showing the packages section
    check_updates = not args.quiet and (
        args.section is None or args.section == "packages"
    )

    with Spinner("Gathering environment info", color="cyan") as spin:
        spin.update("Python info")
        info = gather_env_info(check_updates=check_updates)
        spin.update("Build tools")
        info["build_tools"] = _detect_build_tools()
        spin.update("Python support")
        info["python_support"] = _check_python_support_summary()

    elapsed = time.monotonic() - start

    if args.json_output:
        # Serialize PATH info strings properly
        print(json.dumps(info, indent=2, default=str))
    elif not args.quiet:
        print_env_info(info, no_color=args.no_color, section=args.section)
        c = Colors(enabled=not args.no_color)
        print(f"  {c.dim(f'Completed in {elapsed:.1f}s')}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
