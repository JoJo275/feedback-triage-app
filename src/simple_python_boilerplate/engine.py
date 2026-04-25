"""Core business logic and processing engine.

This module contains the core functionality of the application, independent of
any interface (CLI, API, etc.). It should be interface-agnostic and focused
purely on domain logic.

Typical contents:
    - Data processing functions
    - Business rule implementations
    - Core algorithms
    - State management
    - Environment diagnostics

Usage:
    from simple_python_boilerplate.engine import process_data

Example:
    >>> from simple_python_boilerplate.engine import process_data
    >>> result = process_data(input_data)
"""

from __future__ import annotations

import platform
import shutil
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import TypedDict


class VersionInfo(TypedDict):
    """Version information structure."""

    package_version: str
    python_version: str
    python_full: str
    platform: str


class DiagnosticInfo(TypedDict):
    """Environment diagnostic information structure."""

    version: VersionInfo
    executable: str
    prefix: str
    in_virtual_env: bool
    tools: dict[str, str | None]
    config_files: dict[str, bool]


def get_version_info() -> VersionInfo:
    """Get version information for the package and environment.

    Returns:
        Dictionary with version details.
    """
    try:
        pkg_version = version("simple-python-boilerplate")
    except PackageNotFoundError:
        from simple_python_boilerplate import __version__

        pkg_version = __version__

    py_ver = sys.version_info
    return {
        "package_version": pkg_version,
        "python_version": f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}",
        "python_full": sys.version,
        "platform": f"{platform.system()} {platform.release()}",
    }


def diagnose_environment() -> DiagnosticInfo:
    """Diagnose the development environment.

    Returns:
        Dictionary with diagnostic information.
    """
    version_info = get_version_info()

    # Check virtual environment
    in_venv = sys.prefix != sys.base_prefix

    # Check for dev tools
    tools = ["pytest", "ruff", "mypy", "pre-commit"]
    tool_status = {}
    for tool in tools:
        path = shutil.which(tool)
        tool_status[tool] = path if path else None

    # Check for config files
    config_files = [
        "pyproject.toml",
        ".pre-commit-config.yaml",
        ".gitignore",
        "requirements.txt",
        "requirements-dev.txt",
    ]
    cwd = Path.cwd()
    config_status = {cfg: (cwd / cfg).exists() for cfg in config_files}

    return {
        "version": version_info,
        "executable": sys.executable,
        "prefix": sys.prefix,
        "in_virtual_env": in_venv,
        "tools": tool_status,
        "config_files": config_status,
    }


def process_data(data: str) -> str:
    """Process input data and return result.

    Args:
        data: Input data to process.

    Returns:
        Processed data string.
    """
    # TODO (template users): Replace this placeholder with your actual
    # business logic. This is the core processing function that your
    # CLI and API layers delegate to.
    return f"Processed: {data}"


def validate_input(data: str) -> bool:
    """Validate input data before processing.

    Args:
        data: Input data to validate.

    Returns:
        True if valid, False otherwise.
    """
    return bool(data)
