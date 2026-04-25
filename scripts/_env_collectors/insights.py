"""Insights collector — derived warnings from cross-section analysis."""

from __future__ import annotations

import re
from typing import Any, ClassVar

from _env_collectors._base import BaseCollector

_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


class InsightsCollector(BaseCollector):
    """Derive warnings and recommendations from already-collected sections."""

    name = "insights"
    timeout = 5.0
    _sections: ClassVar[dict[str, Any]] = {}

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().STANDARD

    def collect(self) -> dict[str, Any]:
        warnings: list[dict[str, str]] = []
        s = self._sections

        # Virtualenv not active
        runtimes = s.get("runtimes", {})
        python_info = runtimes.get("python", {})
        if not python_info.get("in_venv", False):
            warnings.append(
                {
                    "severity": "warn",
                    "message": "Not running inside a virtual environment",
                    "section": "venv",
                    "hint": "Running outside a venv means pip install affects the system Python.",
                    "action": "Run 'hatch shell' to enter the project virtual environment.",
                }
            )

        # Git dirty
        git = s.get("git", {})
        if git.get("dirty"):
            warnings.append(
                {
                    "severity": "warn",
                    "message": "Git working tree is dirty — builds may be non-reproducible",
                    "section": "git",
                    "hint": "Uncommitted changes mean version tags and builds won't be reproducible.",
                    "action": "Review changes with 'git status' then commit or stash.",
                }
            )

        # PATH has dead entries
        path_data = s.get("path", {})
        dead = path_data.get("dead_entries", 0)
        if dead > 0:
            warnings.append(
                {
                    "severity": "warn",
                    "message": f"PATH has {dead} non-existent director{'ies' if dead != 1 else 'y'}",
                    "section": "path",
                    "hint": "Dead PATH entries slow down command lookup and can cause confusing errors.",
                    "action": "Remove stale entries from your PATH environment variable.",
                }
            )

        # PATH duplicates
        dups = path_data.get("duplicates", 0)
        if dups > 0:
            warnings.append(
                {
                    "severity": "info",
                    "message": f"PATH has {dups} duplicate entr{'ies' if dups != 1 else 'y'}",
                    "section": "path",
                    "hint": "Duplicate PATH entries are harmless but indicate messy shell config.",
                    "action": "Clean up duplicate entries in your shell profile (.bashrc, $PROFILE, etc.).",
                }
            )

        # Secret env vars found
        security = s.get("security", {})
        secret_vars = security.get("secret_env_vars", [])
        if secret_vars:
            warnings.append(
                {
                    "severity": "warn",
                    "message": f"{len(secret_vars)} secret-like environment variable(s) detected",
                    "section": "security",
                    "hint": "Environment variables matching secret patterns (API_KEY, TOKEN, etc.) are visible to all processes.",
                    "action": "Use a .env file or secrets manager instead of exporting secrets in shell config.",
                }
            )

        # Insecure PATH
        insecure = security.get("insecure_path_entries", [])
        if insecure:
            warnings.append(
                {
                    "severity": "fail",
                    "message": f"{len(insecure)} insecure PATH entr{'ies' if len(insecure) != 1 else 'y'} found",
                    "section": "security",
                    "hint": "World-writable directories in PATH allow any user to inject malicious executables.",
                    "action": "Remove world-writable directories from PATH or fix their permissions (chmod 755).",
                }
            )

        # SSH keys exposed
        ssh = security.get("ssh_keys_exposed", [])
        if ssh:
            warnings.append(
                {
                    "severity": "fail",
                    "message": f"{len(ssh)} SSH/private key(s) exposed in environment",
                    "section": "security",
                    "hint": "Private key paths in environment variables risk accidental exposure in logs or error reports.",
                    "action": "Use an SSH agent instead of storing key paths in environment variables.",
                }
            )

        # Filesystem: disk nearly full
        fs = s.get("filesystem", {})
        disk = fs.get("disk", {})
        pct = disk.get("percent_used", 0)
        if pct > 90:
            warnings.append(
                {
                    "severity": "fail",
                    "message": f"Disk {pct}% full — installs/builds may fail",
                    "section": "filesystem",
                    "hint": "Very low disk space will cause pip installs, builds, and test runs to fail.",
                    "action": "Free disk space: remove old venvs, Docker images, or build artifacts.",
                }
            )
        elif pct > 80:
            warnings.append(
                {
                    "severity": "warn",
                    "message": f"Disk {pct}% full — consider freeing space",
                    "section": "filesystem",
                    "hint": "Getting close to full disk. Builds and installs may start failing soon.",
                    "action": "Run 'task clean' to remove build caches, or clear Docker/temp files.",
                }
            )

        # Temp dir not writable
        writable = fs.get("writable", {})
        tmp = writable.get("temp_dir", {})
        if tmp and not tmp.get("writable", True):
            warnings.append(
                {
                    "severity": "fail",
                    "message": "Temp directory is not writable",
                    "section": "filesystem",
                    "hint": "Many tools (pip, pytest, compilers) need a writable temp directory.",
                    "action": "Check permissions on the TMPDIR/TEMP directory, or set TMPDIR to a writable path.",
                }
            )

        # Network: DNS or outbound issues
        network = s.get("network", {})
        if not network.get("dns_resolves", True):
            warnings.append(
                {
                    "severity": "warn",
                    "message": "DNS resolution failed (pypi.org) — package installs may fail",
                    "section": "network",
                    "hint": "Cannot resolve pypi.org — you may be offline or behind a restrictive firewall.",
                    "action": "Check your network connection and DNS settings. Try 'nslookup pypi.org'.",
                }
            )
        elif not network.get("outbound_https", True):
            warnings.append(
                {
                    "severity": "warn",
                    "message": "DNS works but outbound HTTPS is blocked — package installs may fail",
                    "section": "network",
                    "hint": "DNS resolves but HTTPS connections are blocked — proxy or firewall issue.",
                    "action": "Configure pip to use your proxy: pip config set global.proxy http://proxy:port",
                }
            )

        # Container/CI detection
        container = s.get("container", {})
        if container.get("ci"):
            warnings.append(
                {
                    "severity": "info",
                    "message": f"CI environment detected: {container['ci']}",
                    "section": "container",
                    "hint": "Running in a CI environment — some local dev features may behave differently.",
                    "action": "No action needed. CI-specific behavior is expected.",
                }
            )
        if container.get("wsl"):
            warnings.append(
                {
                    "severity": "info",
                    "message": "Running under WSL — path behavior differs from native Windows",
                    "section": "container",
                    "hint": "WSL translates paths between Linux and Windows formats, which can cause issues with some tools.",
                    "action": "Use Linux-native paths when possible. Access Windows files via /mnt/c/.",
                }
            )

        # Python version vs requires-python
        project_cmds = s.get("project_commands", {})
        project_meta = project_cmds.get("project", {})
        requires_python = project_meta.get("requires_python", "")
        py_version = python_info.get("version", "")
        if (
            requires_python
            and py_version
            and not _version_satisfies(py_version, requires_python)
        ):
            warnings.append(
                {
                    "severity": "fail",
                    "message": f"Python {py_version} does not satisfy requires-python '{requires_python}'",
                    "section": "runtimes",
                    "hint": "The active Python version doesn't meet the project's minimum version constraint. Builds and tests will fail.",
                    "action": f"Install a Python version matching '{requires_python}' and activate it (pyenv, hatch, or system package manager).",
                }
            )

        # Outdated pip
        pip_envs = s.get("pip_environments", {})
        for env in pip_envs.get("environments", []):
            for pkg in env.get("packages", []):
                if pkg.get("name", "").lower() == "pip" and pkg.get("update_available"):
                    current_v = pkg.get("version", "?")
                    latest_v = pkg.get("latest_version", "?")
                    warnings.append(
                        {
                            "severity": "warn",
                            "message": f"pip is outdated ({current_v} → {latest_v})",
                            "section": "packages",
                            "hint": "An outdated pip may miss dependency resolution improvements and security fixes.",
                            "action": "Run 'python -m pip install --upgrade pip' inside your venv.",
                        }
                    )
                    break
            else:
                continue
            break

        # Missing critical tools (git, hatch, pre-commit)
        _check_critical_tools(s, warnings)

        return {"warnings": warnings, "count": len(warnings)}


def _version_satisfies(version: str, constraint: str) -> bool:
    """Check if a version string satisfies a requires-python constraint."""
    match = re.match(r"(\d+)\.(\d+)", version)
    if not match:
        return True  # can't parse, assume OK
    major, minor = int(match.group(1)), int(match.group(2))

    # Parse constraints like ">=3.11", ">=3.11,<4", "<4"
    for part in constraint.split(","):
        part = part.strip()
        m = re.match(r"([><=!]+)\s*(\d+)(?:\.(\d+))?", part)
        if not m:
            continue
        op = m.group(1)
        req_maj = int(m.group(2))
        req_min = int(m.group(3)) if m.group(3) is not None else 0
        ver = (major, minor)
        req = (req_maj, req_min)
        if op == ">=" and not (ver >= req):
            return False
        if op == ">" and not (ver > req):
            return False
        if op == "<=" and not (ver <= req):
            return False
        if op == "<" and not (ver < req):
            return False
        if op == "==" and ver != req:
            return False
        if op == "!=" and ver == req:
            return False
    return True


def _check_critical_tools(
    sections: dict[str, Any], warnings: list[dict[str, str]]
) -> None:
    """Check whether git, hatch, and pre-commit are available."""
    git_data = sections.get("git", {})
    if not git_data.get("available", True):
        warnings.append(
            {
                "severity": "fail",
                "message": "git is not installed or not on PATH",
                "section": "git",
                "hint": "git is required for version control, hatch-vcs versioning, and pre-commit hooks.",
                "action": "Install git: https://git-scm.com/downloads",
            }
        )

    project = sections.get("project", {})
    build_tools = project.get("build_tools", [])
    tool_map = {t["name"].lower(): t for t in build_tools if isinstance(t, dict)}

    hatch = tool_map.get("hatch", {})
    if hatch and not hatch.get("available", True):
        warnings.append(
            {
                "severity": "warn",
                "message": "Hatch is not installed — cannot manage environments or build",
                "section": "project",
                "hint": "This project uses Hatch for environment management, builds, and script running.",
                "action": "Install Hatch: 'pipx install hatch' or 'pip install hatch'.",
            }
        )

    # Check pre-commit: if config exists but tool isn't in PATH
    config_files = project.get("config_files", [])
    has_precommit_config = any(
        ".pre-commit-config.yaml" in str(f) for f in config_files
    )
    if has_precommit_config:
        import shutil

        if not shutil.which("pre-commit"):
            warnings.append(
                {
                    "severity": "warn",
                    "message": "pre-commit config found but pre-commit is not installed",
                    "section": "project",
                    "hint": "This project uses pre-commit for code quality hooks but the tool isn't available.",
                    "action": "Install pre-commit: 'pipx install pre-commit' or activate the Hatch dev env with 'hatch shell'.",
                }
            )
