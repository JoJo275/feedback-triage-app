#!/usr/bin/env python3
"""Print a diagnostics bundle for bug reports and environment debugging.

Collects: Python version, OS, Hatch version, active environment, key tool
versions, important paths, git status, configuration status, and health
checks (pre-commit hooks, editable install, pyproject validity, etc.).

Flags::

    -o, --output PATH   Write output to file (e.g. var/doctor.txt)
    --markdown           Output as markdown (for GitHub issues)
    --json               Output as JSON (machine-readable)
    -q, --quiet          Print a one-line summary only
    --no-color           Disable colored output
    --version            Print version and exit

Usage::

    python scripts/doctor.py
    python scripts/doctor.py --output var/doctor.txt
    python scripts/doctor.py --markdown   # For GitHub issues
    python scripts/doctor.py --json       # Machine-readable output
    python scripts/doctor.py --quiet      # One-line summary

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Repo-specific — aggregates project-specific health checks.
    Requires shared modules: ``_colors.py``, ``_imports.py``,
    ``_ui.py``, ``_progress.py``.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import logging
import os
import platform
import re
import shutil
import subprocess  # nosec B404
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

# TODO (template users): remove try/except once requires-python >= 3.11 is guaranteed
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors, supports_color, unicode_symbols
from _doctor_common import (
    check_hook_installed,
    check_path_exists,
    get_package_version,
    get_version,
)
from _imports import find_repo_root, import_sibling
from _ui import UI, Spacing

_progress = import_sibling("_progress")
Spinner = _progress.Spinner

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_VERSION = "2.6.0"

# Theme color for this script's dashboard output.
THEME = "magenta"

ROOT = find_repo_root()

log = logging.getLogger(__name__)

# Tools that are optional — reported but don't trigger a "problem" if missing.
# These are typically external binaries not installed via pip.
# TODO (template users): Update OPTIONAL_TOOLS if your project has different
#   optional external binaries (e.g. hadolint, shellcheck, trivy).
OPTIONAL_TOOLS = frozenset({"actionlint"})


# get_version, get_package_version, check_path_exists, check_hook_installed
# are imported from _doctor_common above.


def _git_info() -> dict[str, str]:
    """Collect git repository information (branch, commit, dirty state)."""
    result: dict[str, str] = {}
    git_exe = shutil.which("git")
    if not git_exe:
        return {"status": "git not found"}

    def _run_git(*args: str) -> str:
        try:
            proc = subprocess.run(  # nosec B603
                [git_exe, *args],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=ROOT,
            )
            return proc.stdout.strip() if proc.returncode == 0 else ""
        except (subprocess.TimeoutExpired, OSError):
            return ""

    result["branch"] = _run_git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    result["commit"] = _run_git("rev-parse", "--short", "HEAD") or "unknown"
    result["commit_date"] = _run_git("log", "-1", "--format=%ci") or "unknown"

    # Dirty = uncommitted changes exist
    dirty_check = _run_git("status", "--porcelain")
    if dirty_check:
        result["dirty"] = "yes (uncommitted changes in working tree)"
    else:
        result["dirty"] = "no (working tree clean)"

    return result


# ---------------------------------------------------------------------------
# Health check helpers
# ---------------------------------------------------------------------------


def _check_precommit_hooks(root: Path) -> dict[str, str]:
    """Check whether the three expected pre-commit hook stages are installed."""
    hooks_dir = root / ".git" / "hooks"
    return {
        "pre-commit": check_hook_installed(hooks_dir / "pre-commit"),
        "commit-msg": check_hook_installed(hooks_dir / "commit-msg"),
        "pre-push": check_hook_installed(hooks_dir / "pre-push"),
    }


def _check_editable_install() -> dict[str, str]:
    """Check if the package is importable and where it's installed from."""
    # TODO (template users): Replace "simple-python-boilerplate" with your
    # actual package name (the [project].name from pyproject.toml).
    result: dict[str, str] = {}
    try:
        dist = importlib.metadata.distribution("simple-python-boilerplate")
        # Use public files() API to find install location; fall back to
        # package metadata directory. Avoids reliance on the private
        # dist._path attribute that may change across Python versions.
        location = "unknown"
        dist_files = dist.files
        if dist_files:
            first_file = dist_files[0]
            located = first_file.locate()
            location = str(Path(located).parent) if located else "unknown"
        result["installed"] = "yes"
        result["version"] = dist.metadata["Version"] or "unknown"
        # Detect editable install: check for .egg-link or direct_url.json
        # with dir_info.editable=true, which is more reliable than path inspection.
        editable = False
        try:
            direct_url = dist.read_text("direct_url.json")
            if direct_url:
                import json as _json

                url_info = _json.loads(direct_url)
                editable = url_info.get("dir_info", {}).get("editable", False)
        except (ValueError, KeyError, OSError):
            # direct_url.json missing, malformed, or unreadable — fall
            # through to the path-based heuristic below.
            pass
        if not editable:
            # Fallback heuristic: src/ in path or not in site-packages
            editable = "src" in location or "site-packages" not in location
        result["editable"] = "yes" if editable else "no"
        result["location"] = location
    except importlib.metadata.PackageNotFoundError:
        result["installed"] = "no"
        result["editable"] = "N/A"
        result["version"] = "N/A"
        result["location"] = "N/A"
    return result


def _check_pyproject(root: Path) -> dict[str, str]:
    """Validate pyproject.toml can be parsed and has expected sections."""
    pyproject = root / "pyproject.toml"
    result: dict[str, str] = {}

    if not pyproject.is_file():
        result["status"] = "missing"
        return result

    if tomllib is None:
        result["status"] = "cannot parse (tomllib unavailable)"
        return result

    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        result["parseable"] = "yes"
    except (OSError, ValueError) as exc:
        result["parseable"] = f"no ({exc!s})"
        return result

    # Check key sections exist
    project = data.get("project", {})
    result["project.name"] = project.get("name", "MISSING")
    result["requires-python"] = project.get("requires-python", "not set")

    # Check optional-dependencies groups
    opt_deps = project.get("optional-dependencies", {})
    groups = sorted(opt_deps.keys()) if opt_deps else []
    result["optional-dep-groups"] = ", ".join(groups) if groups else "none"

    # Check build system
    build = data.get("build-system", {})
    result["build-backend"] = build.get("build-backend", "not set")

    return result


def _check_python_compat(root: Path) -> dict[str, str]:
    """Check if current Python version meets requires-python constraint."""
    result: dict[str, str] = {}
    pyproject = root / "pyproject.toml"

    if not pyproject.is_file() or tomllib is None:
        result["status"] = "cannot check"
        return result

    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        result["status"] = "cannot parse pyproject.toml"
        return result

    requires = data.get("project", {}).get("requires-python", "")
    if not requires:
        result["status"] = "no requires-python set"
        return result

    current = sys.version.split()[0]
    result["current"] = current
    result["requires"] = requires

    # Simple >=X.Y check (covers the common case)
    match = re.match(r">=(\d+)\.(\d+)", requires)
    if match:
        req_major, req_minor = int(match.group(1)), int(match.group(2))
        cur_parts = [int(x) for x in current.split(".")[:2]]
        if (cur_parts[0], cur_parts[1]) >= (req_major, req_minor):
            result["compatible"] = "yes"
        else:
            result["compatible"] = f"NO (need >={req_major}.{req_minor})"
    else:
        result["compatible"] = f"unknown (complex specifier: {requires})"

    return result


def _check_key_config_files(root: Path) -> dict[str, str]:
    """Check presence of key configuration files."""
    # TODO (template users): Update this list to match your project's
    # key configuration files. Remove entries for tools you don't use
    # and add any project-specific config files.
    files = {
        ".pre-commit-config.yaml": root / ".pre-commit-config.yaml",
        "Taskfile.yml": root / "Taskfile.yml",
        "mkdocs.yml": root / "mkdocs.yml",
        ".repo-doctor.toml": root / ".repo-doctor.toml",
        "release-please-config.json": root / "release-please-config.json",
        ".release-please-manifest.json": root / ".release-please-manifest.json",
        "codecov.yml": root / "codecov.yml",
        ".github/dependabot.yml": root / ".github" / "dependabot.yml",
        "_typos.toml": root / "_typos.toml",
        ".markdownlint-cli2.jsonc": root / ".markdownlint-cli2.jsonc",
        "Containerfile": root / "Containerfile",
        "container-structure-test.yml": root / "container-structure-test.yml",
    }
    return {name: "present" if p.is_file() else "MISSING" for name, p in files.items()}


def _check_hatch_env() -> dict[str, str]:
    """Check Hatch environments.

    Lists all environments reported by ``hatch env show --json``,
    explicitly labelled as *user-defined* or *internal* (``hatch-*``).
    """
    result: dict[str, str] = {}
    hatch_exe = shutil.which("hatch")
    if not hatch_exe:
        result["status"] = "hatch not found"
        return result

    try:
        proc = subprocess.run(  # nosec B603
            [hatch_exe, "env", "show", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            try:
                envs = json.loads(proc.stdout)
                if isinstance(envs, dict):
                    names = sorted(envs.keys())
                elif isinstance(envs, list):
                    names = [
                        e["name"] for e in envs if isinstance(e, dict) and "name" in e
                    ]
                else:
                    result["environments"] = "unknown format"
                    return result

                user_envs = [n for n in names if not n.startswith("hatch-")]
                internal_envs = [n for n in names if n.startswith("hatch-")]
                result["user_defined"] = ", ".join(user_envs) if user_envs else "none"
                result["internal"] = (
                    ", ".join(internal_envs) if internal_envs else "none"
                )
            except (json.JSONDecodeError, TypeError):
                # Fallback: just report raw output
                result["environments"] = proc.stdout.strip()[:100] or "none"
        else:
            result["status"] = "hatch env show failed"
    except (subprocess.TimeoutExpired, OSError):
        result["status"] = "error running hatch"

    return result


def _check_venv_activation() -> dict[str, str]:
    """Enhanced environment detection with guidance."""
    result: dict[str, str] = {}
    venv = os.environ.get("VIRTUAL_ENV", "")
    hatch_env = os.environ.get("HATCH_ENV", "")

    if venv:
        result["virtual_env"] = Path(venv).name
        result["virtual_env_path"] = venv
        result["activated"] = "yes"
    else:
        result["virtual_env"] = "none"
        result["virtual_env_path"] = "N/A"
        result["activated"] = "no"

    result["hatch_env"] = hatch_env if hatch_env else "none"

    # Check if a .venv directory exists even if not activated
    venv_dir = ROOT / ".venv"
    if venv_dir.is_dir() and not venv:
        result["note"] = ".venv/ exists but is NOT activated"
    elif not venv_dir.is_dir() and not venv and not hatch_env:
        result["note"] = "no venv found — run 'hatch shell' or create a .venv"

    # Check if running inside hatch
    if hatch_env:
        result["running_via"] = "hatch"
    elif venv:
        result["running_via"] = "virtualenv"
    else:
        result["running_via"] = "system Python (not recommended)"

    return result


def collect_diagnostics() -> dict[str, str | dict[str, str]]:
    """Collect all diagnostic information.

    Shows a spinner on interactive terminals while gathering tool
    versions and running health checks.
    """
    info: dict[str, str | dict[str, str]] = {}

    spinner = Spinner("Collecting diagnostics", color="magenta")
    spinner.start()

    # Timestamp (UTC for unambiguous reports)
    info["timestamp"] = datetime.now(tz=UTC).isoformat()
    spinner.update("timestamp")

    # System
    info["system"] = {
        "os": f"{platform.system()} {platform.release()}",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python_version": sys.version.split()[0],
        "python_path": sys.executable,
        "python_bits": "64-bit" if sys.maxsize > 2**32 else "32-bit",
    }
    spinner.update("system info")

    # Virtual Environment (enhanced)
    info["environment"] = _check_venv_activation()
    spinner.update("environment")

    # Tool versions — collected in parallel to reduce wall-clock time
    # TODO (template users): Update this tool list to match your project's
    # toolchain. Remove tools you don't use and add any project-specific ones.
    tool_cmds: dict[str, list[str]] = {
        "hatch": ["hatch", "--version"],
        "pip": [sys.executable, "-m", "pip", "--version"],
        "task": ["task", "--version"],
        "ruff": ["ruff", "--version"],
        "mypy": ["mypy", "--version"],
        "pytest": ["pytest", "--version"],
        "pre-commit": ["pre-commit", "--version"],
        "bandit": ["bandit", "--version"],
        "deptry": ["deptry", "--version"],
        "git": ["git", "--version"],
        "actionlint": ["actionlint", "--version"],
        "cz": ["cz", "version"],
    }

    tools: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=len(tool_cmds)) as pool:
        futures = {
            pool.submit(get_version, cmd): name for name, cmd in tool_cmds.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            tools[name] = future.result()
            spinner.update(name)

    # Preserve a stable key order (same as tool_cmds definition)
    info["tools"] = {name: tools[name] for name in tool_cmds}

    # Git repository — also collected in parallel with tools above
    info["git"] = _git_info()
    spinner.update("git info")

    # Package status
    info["package"] = {
        "simple-python-boilerplate": get_package_version("simple-python-boilerplate"),
    }
    spinner.update("package status")

    # Key paths
    info["paths"] = {
        "root": str(ROOT),
        "pyproject.toml": check_path_exists(ROOT / "pyproject.toml"),
        "src/": check_path_exists(ROOT / "src"),
        ".git/": check_path_exists(ROOT / ".git"),
        ".git/hooks/pre-commit": check_path_exists(
            ROOT / ".git" / "hooks" / "pre-commit"
        ),
        ".git/hooks/commit-msg": check_path_exists(
            ROOT / ".git" / "hooks" / "commit-msg"
        ),
        ".git/hooks/pre-push": check_path_exists(ROOT / ".git" / "hooks" / "pre-push"),
    }
    spinner.update("paths")

    # -----------------------------------------------------------------------
    # Health checks
    # -----------------------------------------------------------------------

    # Pre-commit hook installation
    info["hooks"] = _check_precommit_hooks(ROOT)
    spinner.update("hooks")

    # Editable install check — whether the package is pip-installed
    # (so that `import simple_python_boilerplate` works)
    info["pip_install"] = _check_editable_install()
    spinner.update("install check")

    # Python version compatibility
    info["python_compat"] = _check_python_compat(ROOT)
    spinner.update("python compat")

    # pyproject.toml validation
    info["pyproject"] = _check_pyproject(ROOT)
    spinner.update("pyproject")

    # Key config files
    info["config_files"] = _check_key_config_files(ROOT)
    spinner.update("config files")

    # Hatch environment status
    info["hatch_envs"] = _check_hatch_env()
    spinner.update("hatch envs")

    # Summary — surface problems so callers don't have to scan every section
    info["problems"] = _collect_problems(info)

    spinner.finish()

    return info


def _collect_problems(info: dict[str, str | dict[str, str]]) -> dict[str, str]:
    """Scan collected diagnostics and flag potential issues."""
    problems: dict[str, str] = {}

    # Environment: no venv active
    env = info.get("environment", {})
    if isinstance(env, dict) and env.get("activated") == "no":
        problems["no_venv"] = "No virtual environment active"

    # Install: package not installed
    install = info.get("pip_install", {})
    if isinstance(install, dict) and install.get("installed") == "no":
        problems["not_installed"] = "Package not installed (editable install missing)"

    # Python compatibility
    compat = info.get("python_compat", {})
    if isinstance(compat, dict) and compat.get("compatible", "").startswith("NO"):
        problems["python_compat"] = compat["compatible"]

    # Pre-commit hooks not installed
    hooks = info.get("hooks", {})
    if isinstance(hooks, dict):
        missing_hooks = [k for k, v in hooks.items() if v != "installed"]
        if missing_hooks:
            problems["hooks_missing"] = (
                f"Pre-commit hooks not installed: {', '.join(missing_hooks)}"
            )

    # Missing config files
    cfg = info.get("config_files", {})
    if isinstance(cfg, dict):
        missing_files = [k for k, v in cfg.items() if v == "MISSING"]
        if missing_files:
            problems["config_missing"] = (
                f"Config files missing: {', '.join(missing_files)}"
            )

    # Tools not found (skip optional tools like actionlint)
    tools = info.get("tools", {})
    if isinstance(tools, dict):
        missing_tools = [
            k for k, v in tools.items() if v == "not found" and k not in OPTIONAL_TOOLS
        ]
        if missing_tools:
            problems["tools_missing"] = f"Tools not found: {', '.join(missing_tools)}"
        # Report optional tools separately as info, not a problem
        optional_missing = [
            k for k, v in tools.items() if v == "not found" and k in OPTIONAL_TOOLS
        ]
        if optional_missing:
            problems["tools_optional"] = (
                f"Optional tools not found: {', '.join(optional_missing)}"
            )

    if not problems:
        problems["status"] = "no problems detected"

    return problems


def format_plain(
    info: dict[str, str | dict[str, str]],
    *,
    use_color: bool = False,
) -> str:
    """Format diagnostics as plain text with optional color."""
    c = Colors(enabled=use_color)
    sym = unicode_symbols()
    ui = UI(
        title="Diagnostics Report",
        version=SCRIPT_VERSION,
        theme=THEME,
        no_color=not use_color,
    )

    lines: list[str] = []

    def _colorize_value(key: str, val: str) -> str:
        """Apply color to a value based on its content."""
        if val in ("missing", "MISSING", "no", "N/A", "not found", "error"):
            return c.red(val)
        if val.startswith(("yes", "installed", "present")) or val in (
            "file",
            "directory",
        ):
            return c.green(val)
        if val.startswith("NO ") or val.startswith("no "):
            return c.red(val)
        if key == "tools_optional":
            return c.yellow(val)
        return val

    def _section(title: str, *, color: str | None = None) -> None:
        """Append a section header to lines."""
        border = ui.h_line * 60
        color_fn = getattr(c, color, ui._themed) if color else ui._themed
        lines.append("")
        lines.append(color_fn(f"  {ui.tl}{border}{ui.tr}"))
        lines.append(f"  {color_fn(ui.vl)} {c.bold(color_fn(title))}")
        lines.append(color_fn(f"  {ui.bl}{border}{ui.br}"))
        lines.append("")

    def _kv(label: str, value: str, *, key: str = "", width: int = 22) -> None:
        """Append a key-value line to lines with proper alignment."""
        colored_val = _colorize_value(key or label, value)
        # Pad the raw label text first, then apply dim styling so ANSI
        # codes don't interfere with column alignment.
        padded_label = (label + ":").ljust(width)
        # Wrap long values so they don't exceed terminal width.
        wrapped = Spacing.wrap_value(
            colored_val,
            indent=4,
            label_width=width,
        )
        lines.append(f"    {c.dim(padded_label)} {wrapped}")

    # -- Human-friendly section labels --
    _section_labels: dict[str, str] = {
        "timestamp": "Timestamp",
        "system": "System Information",
        "environment": "Environment",
        "tools": "Tool Versions",
        "git": "Git Repository",
        "package": "Package Status",
        "paths": "Key Paths",
        "hooks": "Pre-commit Hooks",
        "pip_install": "Editable Install",
        "python_compat": "Python Compatibility",
        "pyproject": "pyproject.toml Validation",
        "config_files": "Configuration Files",
        "hatch_envs": "Hatch Environments",
        "problems": "Problems",
    }

    # -- Sections --
    for section, data in info.items():
        display_name = _section_labels.get(section, section.upper())

        # Compute per-section label width from actual keys.
        if isinstance(data, dict):
            sec_width = Spacing.auto_label_width(list(data.keys()))
        else:
            sec_width = 22

        # Problems section gets special color treatment
        if section == "problems":
            has_issues = isinstance(data, dict) and "status" not in data
            color = "red" if has_issues else "green"
            icon = sym["cross"] if has_issues else sym["check"]
            _section(f"{icon} {display_name}", color=color)
        else:
            _section(display_name)

        if isinstance(data, dict):
            for key, value in data.items():
                _kv(key, str(value), key=key, width=sec_width)
        else:
            lines.append(f"    {data}")

        lines.append("")

    # -- Summary bar --
    problems = info.get("problems", {})
    total_checks = sum(
        len(v) if isinstance(v, dict) else 1 for k, v in info.items() if k != "problems"
    )

    if isinstance(problems, dict) and "status" in problems:
        lines.append(
            f"  {c.green(sym['check'])} "
            f"{c.bold(c.green('All checks passed'))} "
            f"{c.dim(f'({total_checks} items collected)')}"
        )
    else:
        real_problems = (
            sum(1 for k in problems if k not in ("status", "tools_optional"))
            if isinstance(problems, dict)
            else 0
        )
        lines.append(
            f"  {c.yellow(sym['warn'])} "
            f"{c.bold(c.yellow(f'{real_problems} problem(s) found'))} "
            f"{c.dim(f'({total_checks} items collected)')}"
        )

    lines.append("")

    return "\n".join(lines)


def format_markdown(info: dict[str, str | dict[str, str]]) -> str:
    """Format diagnostics as markdown for GitHub issues."""
    lines = [
        "<details>",
        "<summary>Environment diagnostics</summary>",
        "",
        "```",
    ]

    for section, data in info.items():
        lines.append(f"[{section}]")
        if isinstance(data, dict):
            for key, value in data.items():
                lines.append(f"  {key}: {value}")
        else:
            lines.append(f"  {data}")

    lines.extend(["```", "</details>"])
    return "\n".join(lines)


def format_json(info: dict[str, str | dict[str, str]]) -> str:
    """Format diagnostics as JSON for scripting and automation."""
    return json.dumps(info, indent=2)


# ---------------------------------------------------------------------------
# Color output helpers (delegated to shared _colors module)
# ---------------------------------------------------------------------------

# Re-export for backward compatibility and tests
_supports_color = supports_color


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="doctor",
        description="Print a diagnostics bundle for bug reports.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Write output to file (e.g., var/doctor.txt)",
    )

    fmt_group = parser.add_mutually_exclusive_group()
    fmt_group.add_argument(
        "--markdown",
        action="store_true",
        help="Output as markdown (for GitHub issues)",
    )
    fmt_group.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (machine-readable)",
    )
    fmt_group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Print a one-line summary only",
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
        print(f"doctor {SCRIPT_VERSION}: smoke ok")
        return 0

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    info = collect_diagnostics()

    use_color = False if args.no_color else supports_color()

    # Quiet mode: summarise problems instead of blindly claiming "all OK"
    if args.quiet:
        problems = info.get("problems", {})
        c = Colors(enabled=use_color)
        sym = unicode_symbols()
        if isinstance(problems, dict) and "status" in problems:
            output = c.green(
                f"doctor {SCRIPT_VERSION} {sym['dash']} no problems detected"
            )
        else:
            count = len(problems) if isinstance(problems, dict) else 0
            output = c.yellow(
                f"doctor {SCRIPT_VERSION} {sym['dash']} {count} problem(s) found"
            )
    elif args.json:
        output = format_json(info)
    elif args.markdown:
        output = format_markdown(info)
    else:
        ui = UI(
            title="Diagnostics Report",
            version=SCRIPT_VERSION,
            theme=THEME,
            no_color=not use_color,
        )
        ui.header()
        output = format_plain(info, use_color=use_color)
        print(output)
        ui.recommended_scripts(
            ["bootstrap", "env_doctor", "repo_doctor", "clean", "dep_versions"]
        )
        # Summary footer
        problems = info.get("problems", {})
        _info_keys = frozenset({"status", "tools_optional"})
        if isinstance(problems, dict) and "status" in problems:
            ui.footer(passed=1, failed=0, warned=0)
        else:
            real = (
                sum(1 for k in problems if k not in _info_keys)
                if isinstance(problems, dict)
                else 0
            )
            warned = (
                1 if isinstance(problems, dict) and "tools_optional" in problems else 0
            )
            ui.footer(passed=0, failed=real, warned=warned)
        output = ""  # already printed

    if output:
        print(output)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        log.info("Saved to: %s", args.output)

    # Return non-zero exit code when real problems are detected so CI
    # can gate on `python scripts/doctor.py --quiet`.
    # Informational entries (tools_optional) don't count as real problems.
    _INFO_KEYS = frozenset({"status", "tools_optional"})
    problems = info.get("problems", {})
    has_problems = isinstance(problems, dict) and any(
        k not in _INFO_KEYS for k in problems
    )
    return 1 if has_problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
