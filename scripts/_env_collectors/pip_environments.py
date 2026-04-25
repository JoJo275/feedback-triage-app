"""Pip environments collector — all pip installs across all environments.

Discovers packages in:
- Global (system) Python installs
- Virtual environments (.venv, venv)
- Hatch, tox, nox, poetry, conda environments
- pipx-installed tools
- User (--user) installs

Also detects:
- Non-Python language ecosystems (Node.js/npm, Ruby/gem, Rust/cargo, Go, etc.)
- Python version at each install location
- Available updates for each package
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any

from _env_collectors._base import BaseCollector

_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


def _run_cmd(
    cmd: list[str], *, timeout: float = 30.0
) -> subprocess.CompletedProcess[str]:
    """Run a command safely, returning CompletedProcess."""
    return subprocess.run(  # nosec B603
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _get_python_version_at(python_exe: str) -> str | None:
    """Get the Python version string for a specific Python executable."""
    try:
        result = _run_cmd([python_exe, "--version"], timeout=5.0)
        if result.returncode == 0:
            # "Python 3.11.5" -> "3.11.5"
            return result.stdout.strip().replace("Python ", "")
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _get_pip_list_for(
    python_exe: str, *, outdated: bool = False
) -> list[dict[str, str]]:
    """Run pip list (JSON format) via a specific Python executable."""
    cmd = [python_exe, "-m", "pip", "list", "--format=json"]
    if outdated:
        cmd.append("--outdated")
    try:
        result = _run_cmd(cmd, timeout=60.0)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return []


def _find_python_executables() -> list[dict[str, Any]]:
    """Find all Python executables on the system."""
    found: dict[str, dict[str, Any]] = {}

    # Current interpreter
    current = sys.executable
    if current:
        current_path = Path(current).resolve()
        found[str(current_path)] = {
            "path": str(current_path),
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "is_current": True,
            "source": "current interpreter",
        }

    # Search PATH for python executables
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    python_names = ["python", "python3"]
    if sys.platform == "win32":
        python_names.extend(["python3.11", "python3.12", "python3.13", "python3.14"])
    else:
        python_names.extend(
            [f"python3.{v}" for v in range(8, 15)]  # python3.8 through python3.14
        )

    for d in path_dirs:
        for name in python_names:
            if sys.platform == "win32":
                exe_path = Path(d) / f"{name}.exe"
            else:
                exe_path = Path(d) / name
            if exe_path.is_file():
                try:
                    resolved = str(exe_path.resolve())
                    if resolved not in found:
                        version = _get_python_version_at(str(exe_path))
                        found[resolved] = {
                            "path": resolved,
                            "version": version,
                            "is_current": False,
                            "source": "PATH",
                        }
                except OSError:
                    pass

    return list(found.values())


def _discover_venvs(repo_root: Path) -> list[dict[str, Any]]:
    """Discover virtual environments near the repo root."""
    venvs: list[dict[str, Any]] = []

    # Common venv directories
    for venv_name in [".venv", "venv", ".env", "env"]:
        venv_path = repo_root / venv_name
        if sys.platform == "win32":
            python = venv_path / "Scripts" / "python.exe"
        else:
            python = venv_path / "bin" / "python"
        if python.is_file():
            version = _get_python_version_at(str(python))
            venvs.append(
                {
                    "name": venv_name,
                    "path": str(venv_path),
                    "python_exe": str(python),
                    "python_version": version,
                    "type": "venv",
                }
            )

    return venvs


def _discover_hatch_envs() -> list[dict[str, Any]]:
    """Discover Hatch environments."""
    envs: list[dict[str, Any]] = []
    hatch_exe = shutil.which("hatch")
    if not hatch_exe:
        return envs

    try:
        result = _run_cmd([hatch_exe, "env", "show", "--json"], timeout=15.0)
        if result.returncode == 0 and result.stdout.strip():
            env_data = json.loads(result.stdout)
            if isinstance(env_data, dict):
                for env_name, info in env_data.items():
                    env_entry: dict[str, Any] = {
                        "name": f"hatch-{env_name}",
                        "type": "hatch",
                        "env_name": env_name,
                    }
                    if isinstance(info, dict):
                        env_entry["python_version"] = info.get("python", "")
                    envs.append(env_entry)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    # Also try to find hatch env paths
    try:
        result = _run_cmd([hatch_exe, "env", "find"], timeout=10.0)
        if result.returncode == 0 and result.stdout.strip():
            env_path = Path(result.stdout.strip())
            if env_path.is_dir():
                if sys.platform == "win32":
                    python = env_path / "Scripts" / "python.exe"
                else:
                    python = env_path / "bin" / "python"
                if python.is_file():
                    for e in envs:
                        if e.get("name") == "hatch-default":
                            e["path"] = str(env_path)
                            e["python_exe"] = str(python)
                            e["python_version"] = _get_python_version_at(str(python))
    except (OSError, subprocess.TimeoutExpired):
        pass

    return envs


def _get_pipx_packages() -> list[dict[str, Any]]:
    """Get packages installed via pipx."""
    pipx_exe = shutil.which("pipx")
    if not pipx_exe:
        return []

    try:
        result = _run_cmd([pipx_exe, "list", "--json"], timeout=15.0)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            packages = []
            venvs = data.get("venvs", {})
            for name, info in venvs.items():
                metadata = info.get("metadata", {})
                main_pkg = metadata.get("main_package", {})
                python_ver = metadata.get("python_version", "")
                packages.append(
                    {
                        "name": name,
                        "version": main_pkg.get("package_version", ""),
                        "python_version": python_ver,
                        "source": "pipx",
                        "apps": main_pkg.get("apps", []),
                    }
                )
            return packages
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return []


def _detect_language_ecosystems() -> list[dict[str, Any]]:
    """Detect non-Python language ecosystems and their package managers."""
    ecosystems: list[dict[str, Any]] = []

    checks = [
        {
            "language": "Node.js",
            "exe": "node",
            "version_cmd": ["node", "--version"],
            "installer": "npm",
            "installer_cmd": ["npm", "--version"],
            "alt_installers": [
                ("yarn", ["yarn", "--version"]),
                ("pnpm", ["pnpm", "--version"]),
                ("bun", ["bun", "--version"]),
            ],
        },
        {
            "language": "Ruby",
            "exe": "ruby",
            "version_cmd": ["ruby", "--version"],
            "installer": "gem",
            "installer_cmd": ["gem", "--version"],
            "alt_installers": [("bundler", ["bundle", "--version"])],
        },
        {
            "language": "Rust",
            "exe": "rustc",
            "version_cmd": ["rustc", "--version"],
            "installer": "cargo",
            "installer_cmd": ["cargo", "--version"],
            "alt_installers": [],
        },
        {
            "language": "Go",
            "exe": "go",
            "version_cmd": ["go", "version"],
            "installer": "go",
            "installer_cmd": ["go", "version"],
            "alt_installers": [],
        },
        {
            "language": "Java",
            "exe": "java",
            "version_cmd": ["java", "-version"],
            "installer": "mvn",
            "installer_cmd": ["mvn", "--version"],
            "alt_installers": [("gradle", ["gradle", "--version"])],
        },
        {
            "language": ".NET",
            "exe": "dotnet",
            "version_cmd": ["dotnet", "--version"],
            "installer": "nuget",
            "installer_cmd": ["dotnet", "nuget", "--version"],
            "alt_installers": [],
        },
        {
            "language": "PHP",
            "exe": "php",
            "version_cmd": ["php", "--version"],
            "installer": "composer",
            "installer_cmd": ["composer", "--version"],
            "alt_installers": [],
        },
    ]

    for check in checks:
        exe_path = shutil.which(check["exe"])
        if not exe_path:
            continue

        ecosystem: dict[str, Any] = {
            "language": check["language"],
            "executable": exe_path,
            "version": None,
            "installers": [],
        }

        # Get language version
        try:
            result = _run_cmd(check["version_cmd"], timeout=5.0)
            output = (result.stdout or result.stderr or "").strip()
            # Extract version number
            m = re.search(r"(\d+\.\d+[\.\d]*)", output)
            if m:
                ecosystem["version"] = m.group(1)
        except (OSError, subprocess.TimeoutExpired):
            pass

        # Check primary installer
        installer_path = shutil.which(check["installer"])
        if installer_path:
            inst_info: dict[str, Any] = {
                "name": check["installer"],
                "path": installer_path,
                "version": None,
            }
            try:
                result = _run_cmd(check["installer_cmd"], timeout=5.0)
                output = (result.stdout or result.stderr or "").strip()
                m = re.search(r"(\d+\.\d+[\.\d]*)", output)
                if m:
                    inst_info["version"] = m.group(1)
            except (OSError, subprocess.TimeoutExpired):
                pass
            ecosystem["installers"].append(inst_info)

        # Check alternative installers
        for alt_name, alt_cmd in check.get("alt_installers", []):
            alt_path = shutil.which(alt_name)
            if alt_path:
                alt_info: dict[str, Any] = {
                    "name": alt_name,
                    "path": alt_path,
                    "version": None,
                }
                try:
                    result = _run_cmd(alt_cmd, timeout=5.0)
                    output = (result.stdout or result.stderr or "").strip()
                    m = re.search(r"(\d+\.\d+[\.\d]*)", output)
                    if m:
                        alt_info["version"] = m.group(1)
                except (OSError, subprocess.TimeoutExpired):
                    pass
                ecosystem["installers"].append(alt_info)

        ecosystems.append(ecosystem)

    return ecosystems


def _categorize_environment(path: str) -> str:
    """Classify an install path into a human-readable category."""
    if not path:
        return "Unknown"
    loc = path.lower().replace("\\", "/")

    if "/.local/share/hatch/" in loc or "/hatch/env/" in loc:
        m = re.search(r"hatch/env[s]?/([^/]+)", loc)
        return f"Hatch ({m.group(1)})" if m else "Hatch Environment"
    if "appdata" in loc and "hatch" in loc:
        m = re.search(r"hatch/env[s]?/([^/]+)", loc)
        return f"Hatch ({m.group(1)})" if m else "Hatch Environment"
    if "/.tox/" in loc or "\\.tox\\" in path.lower():
        return "Tox Environment"
    if "/.nox/" in loc or "\\.nox\\" in path.lower():
        return "Nox Environment"
    if "/pypoetry/" in loc:
        return "Poetry Environment"
    if "/conda/" in loc or "/envs/" in loc:
        m = re.search(r"envs/([^/\\]+)", loc)
        return f"Conda ({m.group(1)})" if m else "Conda Environment"
    if any(kw in loc for kw in ("/.venv/", "/venv/", "\\.venv\\", "\\venv\\")):
        return "Virtual Environment (.venv)"
    if "/pipx/" in loc:
        return "pipx"
    if "/site-packages" in loc and ("/.local/" in loc or "/appdata/" in loc):
        return "User (--user)"
    return "Global (system)"


def _python_version_for_path(path: str) -> str | None:
    """Extract Python version from an install path."""
    m = re.search(r"python(\d+\.\d+)", path.lower().replace("\\", "/"))
    if m:
        return m.group(1)
    return None


class PipEnvironmentsCollector(BaseCollector):
    """Collect comprehensive pip install data across all environments."""

    name = "pip_environments"
    timeout = 120.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().STANDARD

    def collect(self) -> dict[str, Any]:
        from _imports import find_repo_root

        repo_root = find_repo_root()

        # 1. All Python executables found
        python_installs = _find_python_executables()

        # 2. Virtual environments
        venvs = _discover_venvs(repo_root)

        # 3. Hatch environments
        hatch_envs = _discover_hatch_envs()

        # 4. pipx packages
        pipx_packages = _get_pipx_packages()

        # 5. Current environment packages with outdated info
        current_packages = _get_pip_list_for(sys.executable)
        outdated_packages = _get_pip_list_for(sys.executable, outdated=True)

        # Build outdated lookup: name -> {latest_version}
        outdated_lookup: dict[str, str] = {}
        for pkg in outdated_packages:
            outdated_lookup[pkg["name"].lower()] = pkg.get(
                "latest_version", pkg.get("version", "")
            )

        # Enrich current packages with outdated info
        environments: list[dict[str, Any]] = []
        enriched: list[dict[str, Any]] = []
        for pkg in current_packages:
            name_lower = pkg["name"].lower()
            entry: dict[str, Any] = {
                "name": pkg["name"],
                "version": pkg.get("version", ""),
                "latest_version": outdated_lookup.get(name_lower),
                "update_available": name_lower in outdated_lookup,
            }
            enriched.append(entry)

        # Build environment entries for each Python install location
        current_env: dict[str, Any] = {
            "name": "Current Environment",
            "type": _categorize_environment(sys.prefix),
            "python_exe": sys.executable,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "path": sys.prefix,
            "packages": enriched,
            "package_count": len(enriched),
            "outdated_count": len(outdated_lookup),
        }
        environments.append(current_env)

        # Add discovered venvs
        for venv in venvs:
            venv_pkgs = _get_pip_list_for(venv["python_exe"])
            venv_outdated = _get_pip_list_for(venv["python_exe"], outdated=True)
            venv_outdated_lookup = {
                p["name"].lower(): p.get("latest_version", "") for p in venv_outdated
            }
            venv_enriched = [
                {
                    "name": p["name"],
                    "version": p.get("version", ""),
                    "latest_version": venv_outdated_lookup.get(p["name"].lower()),
                    "update_available": p["name"].lower() in venv_outdated_lookup,
                }
                for p in venv_pkgs
            ]
            environments.append(
                {
                    "name": venv["name"],
                    "type": "Virtual Environment",
                    "python_exe": venv["python_exe"],
                    "python_version": venv.get("python_version"),
                    "path": venv["path"],
                    "packages": venv_enriched,
                    "package_count": len(venv_enriched),
                    "outdated_count": len(venv_outdated_lookup),
                }
            )

        # Add hatch envs (if we can find their pythons)
        for henv in hatch_envs:
            if henv.get("python_exe"):
                henv_pkgs = _get_pip_list_for(henv["python_exe"])
                henv_outdated = _get_pip_list_for(henv["python_exe"], outdated=True)
                henv_outdated_lookup = {
                    p["name"].lower(): p.get("latest_version", "")
                    for p in henv_outdated
                }
                henv_enriched = [
                    {
                        "name": p["name"],
                        "version": p.get("version", ""),
                        "latest_version": henv_outdated_lookup.get(p["name"].lower()),
                        "update_available": p["name"].lower() in henv_outdated_lookup,
                    }
                    for p in henv_pkgs
                ]
                environments.append(
                    {
                        "name": henv["name"],
                        "type": "Hatch Environment",
                        "python_exe": henv["python_exe"],
                        "python_version": henv.get("python_version"),
                        "path": henv.get("path", ""),
                        "packages": henv_enriched,
                        "package_count": len(henv_enriched),
                        "outdated_count": len(henv_outdated_lookup),
                    }
                )

        # 6. Detect other language ecosystems
        language_ecosystems = _detect_language_ecosystems()

        # Build summary stats
        total_envs = len(environments)
        total_packages = sum(e["package_count"] for e in environments)
        total_outdated = sum(e.get("outdated_count", 0) for e in environments)

        return {
            "python_installs": python_installs,
            "environments": environments,
            "pipx_packages": pipx_packages,
            "language_ecosystems": language_ecosystems,
            "summary": {
                "total_environments": total_envs,
                "total_packages": total_packages,
                "total_outdated": total_outdated,
                "languages_detected": [e["language"] for e in language_ecosystems],
            },
        }
