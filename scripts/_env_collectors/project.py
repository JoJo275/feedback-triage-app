"""Project collector — repo root, lockfiles, build/test/lint tools, configs."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from typing import Any

from _imports import find_repo_root

from _env_collectors._base import BaseCollector

_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


_LOCKFILES = [
    "requirements.txt",
    "requirements-dev.txt",
    "requirements.lock",
    "poetry.lock",
    "Pipfile.lock",
    "pdm.lock",
    "uv.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
]

_CONFIG_FILES = [
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "tox.ini",
    "noxfile.py",
    ".flake8",
    ".pylintrc",
    "mypy.ini",
    ".mypy.ini",
    ".pre-commit-config.yaml",
    "Taskfile.yml",
    "Makefile",
    "Containerfile",
    "Dockerfile",
    "docker-compose.yml",
    ".tool-versions",
    ".python-version",
    ".node-version",
    ".nvmrc",
    "mkdocs.yml",
]

_BUILD_TOOLS = [
    ("Hatch", "hatch", "--version", "pyproject.toml"),
    ("tox", "tox", "--version", "tox.ini"),
    ("nox", "nox", "--version", "noxfile.py"),
    ("Poetry", "poetry", "--version", "pyproject.toml"),
    ("PDM", "pdm", "--version", "pyproject.toml"),
    ("Flit", "flit", "--version", "pyproject.toml"),
    ("pip", "pip", "--version", "requirements.txt"),
    ("pipx", "pipx", "--version", None),
    ("uv", "uv", "version", "pyproject.toml"),
    ("conda", "conda", "--version", None),
    ("mamba", "mamba", "--version", None),
]


def _get_tool_version(exe: str, version_flag: str) -> str:
    """Try to get a tool's version string. Returns empty string on failure."""
    try:
        result = subprocess.run(  # nosec B603
            [exe, version_flag],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        if result.returncode == 0:
            output = result.stdout.strip() or result.stderr.strip()
            # Extract version-like pattern from output
            for part in output.replace(",", " ").split():
                if part and part[0].isdigit():
                    return part.rstrip(")")
            return output[:60] if output else ""
    except (OSError, subprocess.TimeoutExpired):
        pass
    return ""


class ProjectCollector(BaseCollector):
    """Detect project structure, lockfiles, build tools, and config files."""

    name = "project"
    timeout = 15.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().MINIMAL

    def collect(self) -> dict[str, Any]:
        root = find_repo_root()
        lockfiles = [f for f in _LOCKFILES if (root / f).is_file()]
        configs = [f for f in _CONFIG_FILES if (root / f).is_file()]
        tools = []
        for name, exe, version_flag, config_file in _BUILD_TOOLS:
            exe_path = shutil.which(exe)
            available = exe_path is not None
            version = _get_tool_version(exe, version_flag) if available else ""
            tools.append(
                {
                    "name": name,
                    "available": available,
                    "version": version,
                    "exe": exe_path or "",
                    "config_file": config_file
                    if config_file and (root / config_file).is_file()
                    else "",
                }
            )

        return {
            "repo_root": str(root),
            "lockfiles": lockfiles,
            "config_files": configs,
            "build_tools": tools,
            "critical_files": self._detect_critical_files(root),
        }

    @staticmethod
    def _detect_critical_files(root: object) -> list[dict[str, object]]:
        """Detect critical repo files that should exist in a well-maintained project."""
        from pathlib import Path

        root_path = Path(str(root))
        critical_names = [
            "README.md",
            "LICENSE",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            "SECURITY.md",
            "pyproject.toml",
            ".gitignore",
            ".pre-commit-config.yaml",
            ".github/workflows",
        ]
        result: list[dict[str, object]] = []
        for name in critical_names:
            path = root_path / name
            result.append(
                {
                    "name": name,
                    "exists": path.exists(),
                }
            )
        return result
