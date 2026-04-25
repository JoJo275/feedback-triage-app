#!/usr/bin/env python3
"""Validate that Python version support is consistent across all config files.

Checks that the declared Python version support is aligned between:
  - pyproject.toml requires-python
  - pyproject.toml classifiers
  - Hatch test matrix (pyproject.toml)
  - CI test workflow matrix (.github/workflows/test.yml)
  - bootstrap.py MIN_PYTHON constant

Also performs code-level compatibility analysis:
  - Scans ``src/`` and ``scripts/`` for Python syntax features that
    require specific minimum versions (e.g. ``match/case`` → 3.10+,
    ``except*`` → 3.11+, ``type`` statement → 3.12+).
  - Flags versions listed in project files that are incompatible with
    syntax features used in source code.
  - Flags versions supported by the code but not declared in project
    classifiers (potential missing classifier).

Reports mismatches so you never accidentally test or ship a version
you don't officially support (or forget to add support you do).

Flags::

    --json          Output as JSON (for CI integration)
    -q, --quiet     Suppress output; exit code only
    --no-color      Disable colored output
    --version       Print version and exit

Usage::

    python scripts/check_python_support.py
    python scripts/check_python_support.py --json
    python scripts/check_python_support.py --quiet   # Exit code only (for CI)

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in other repos that have a ``pyproject.toml`` with
    classifiers and ``requires-python``.  Requires shared modules:
    ``_colors.py``, ``_imports.py``, ``_ui.py``.
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import re
import sys
import tomllib
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors
from _imports import find_repo_root
from _ui import UI

log = logging.getLogger(__name__)

ROOT = find_repo_root()
SCRIPT_VERSION = "1.2.0"

# Known Python versions and the features that first appeared in each.
# Used to determine the minimum Python version required by source code.
# Only features detectable via AST or regex are listed.
_VERSION_FEATURES: dict[tuple[int, int], list[str]] = {
    (3, 8): ["walrus operator (:=)", "positional-only params (/)"],
    (3, 9): ["dict union operator (|)", "builtin generic types (list[int])"],
    (3, 10): ["match/case statement", "union type hints (X | Y)"],
    (3, 11): ["except* (exception groups)", "tomllib in stdlib"],
    (3, 12): ["type statement (type aliases)", "f-string nesting"],
    (3, 13): ["improved error messages"],
}

# Stable Python versions available for CI support consideration.
_KNOWN_STABLE_VERSIONS: list[tuple[int, int]] = [
    (3, 9),
    (3, 10),
    (3, 11),
    (3, 12),
    (3, 13),
]

# Theme color for this script's dashboard output.
THEME = "green"

# TODO (template users): Update these paths if your project structure
#   differs (e.g., monorepo with multiple pyproject.toml files).


def _read_pyproject() -> dict:
    """Read and parse pyproject.toml."""
    path = ROOT / "pyproject.toml"
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _parse_requires_python(spec: str) -> tuple[int, int] | None:
    """Extract minimum Python version from requires-python spec (e.g., '>=3.11')."""
    match = re.match(r">=\s*(\d+)\.(\d+)", spec)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return None


def _extract_classifier_versions(classifiers: list[str]) -> list[tuple[int, int]]:
    """Extract Python X.Y versions from PyPI classifiers."""
    versions = []
    for c in classifiers:
        match = re.match(r"Programming Language :: Python :: (\d+)\.(\d+)$", c)
        if match:
            versions.append((int(match.group(1)), int(match.group(2))))
    return sorted(versions)


def _extract_hatch_matrix(data: dict) -> list[tuple[int, int]]:
    """Extract Python versions from Hatch test matrix."""
    versions = []
    matrices = (
        data.get("tool", {})
        .get("hatch", {})
        .get("envs", {})
        .get("test", {})
        .get("matrix", [])
    )
    for matrix in matrices:
        for v in matrix.get("python", []):
            parts = str(v).split(".")
            if len(parts) >= 2:
                versions.append((int(parts[0]), int(parts[1])))
    return sorted(versions)


def _extract_ci_matrix() -> list[tuple[int, int]]:
    """Extract Python versions from CI test workflow matrix."""
    test_yml = ROOT / ".github" / "workflows" / "test.yml"
    if not test_yml.is_file():
        return []
    content = test_yml.read_text(encoding="utf-8")
    # Match python-version: ["3.11", "3.12", "3.13"]
    match = re.search(r"python-version:\s*\[([^\]]+)\]", content)
    if not match:
        return []
    versions = []
    for v in re.findall(r'"(\d+\.\d+)"', match.group(1)):
        parts = v.split(".")
        versions.append((int(parts[0]), int(parts[1])))
    return sorted(versions)


def _extract_bootstrap_min() -> tuple[int, int] | None:
    """Extract MIN_PYTHON from bootstrap.py."""
    bootstrap = ROOT / "scripts" / "bootstrap.py"
    if not bootstrap.is_file():
        return None
    content = bootstrap.read_text(encoding="utf-8")
    match = re.search(r"MIN_PYTHON\s*=\s*\((\d+),\s*(\d+)\)", content)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return None


def _fmt_version(v: tuple[int, int]) -> str:
    return f"{v[0]}.{v[1]}"


def _fmt_versions(versions: list[tuple[int, int]]) -> str:
    return ", ".join(_fmt_version(v) for v in versions)


# ---------------------------------------------------------------------------
# Code compatibility scanning
# ---------------------------------------------------------------------------


def _collect_python_files() -> list[Path]:
    """Collect Python files from src/ and scripts/ directories."""
    dirs = [ROOT / "src", ROOT / "scripts"]
    files: list[Path] = []
    for d in dirs:
        if d.is_dir():
            files.extend(d.rglob("*.py"))
    return sorted(files)


def _detect_min_version_from_ast(source: str, filepath: str) -> tuple[int, int]:
    """Detect the minimum Python version required by AST features in *source*.

    Returns the highest minimum version required by any detected feature.
    """
    min_ver = (3, 0)

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return min_ver

    for node in ast.walk(tree):
        # 3.8: walrus operator (:=)
        if isinstance(node, ast.NamedExpr):
            min_ver = max(min_ver, (3, 8))

        # 3.10: match/case statement
        if isinstance(node, ast.Match):
            min_ver = max(min_ver, (3, 10))

        # 3.10: union type hints in annotations (X | Y) via BinOp
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.BitOr)
            and (isinstance(node.left, ast.Name) or isinstance(node.right, ast.Name))
        ):
            # Could be a type union — conservative: only flag in annotations
            pass

        # 3.11: except* (ExceptionGroup)
        if isinstance(node, ast.TryStar):
            min_ver = max(min_ver, (3, 11))

        # 3.12: type alias statement
        if isinstance(node, ast.TypeAlias):
            min_ver = max(min_ver, (3, 12))

    return min_ver


def _detect_min_version_from_imports(source: str) -> tuple[tuple[int, int], str]:
    """Detect minimum version from stdlib imports that appeared in specific versions.

    Returns (min_version, feature_description).
    """
    min_ver = (3, 0)
    desc = ""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return min_ver, desc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "tomllib":
                    min_ver = max(min_ver, (3, 11))
                    desc = "tomllib import (stdlib 3.11+)"
        elif isinstance(node, ast.ImportFrom) and node.module == "tomllib":
            min_ver = max(min_ver, (3, 11))
            desc = "tomllib import (stdlib 3.11+)"

    return min_ver, desc


def _scan_code_compatibility(
    files: list[Path],
) -> dict:
    """Scan Python files and determine code-level version requirements.

    Returns a dict with:
        - ``code_min_version``: the highest minimum version required
        - ``features_found``: list of (file, feature, min_version) tuples
        - ``file_count``: number of files scanned
    """
    code_min = (3, 0)
    features: list[dict[str, str]] = []

    for filepath in files:
        try:
            source = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel = filepath.relative_to(ROOT)

        # AST-based detection
        file_min = _detect_min_version_from_ast(source, str(rel))
        if file_min > code_min:
            code_min = file_min

        import_min, import_desc = _detect_min_version_from_imports(source)
        if import_min > code_min:
            code_min = import_min

        # Record specific features found — prefer AST feature name, fall
        # back to import description
        effective_min = max(file_min, import_min)
        if effective_min > (3, 0):
            if file_min >= import_min:
                feature_names = _VERSION_FEATURES.get(file_min, [])
                feature_desc = (
                    feature_names[0]
                    if feature_names
                    else f"{_fmt_version(file_min)}+ syntax"
                )
            else:
                feature_desc = import_desc or f"{_fmt_version(import_min)}+ import"
            features.append(
                {
                    "file": str(rel),
                    "feature": feature_desc,
                    "min_version": _fmt_version(effective_min),
                }
            )

    return {
        "code_min_version": code_min,
        "features_found": features,
        "file_count": len(files),
    }


def _find_unlisted_supported_versions(
    code_min: tuple[int, int],
    declared_versions: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Find stable Python versions the code supports but aren't declared."""
    return sorted(
        v
        for v in _KNOWN_STABLE_VERSIONS
        if v >= code_min and v not in declared_versions
    )


def _find_unsupported_declared_versions(
    code_min: tuple[int, int],
    declared_versions: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Find versions declared in project files that code doesn't support."""
    return sorted(v for v in declared_versions if v < code_min)


def check_python_support(*, quiet: bool = False, no_color: bool = False) -> dict:
    """Check all sources of Python version info and report mismatches.

    Returns:
        Dictionary with results: sources, mismatches, and overall status.
    """
    data = _read_pyproject()

    # Gather all sources
    requires_python = data.get("project", {}).get("requires-python", "")
    min_version = _parse_requires_python(requires_python)
    classifiers = data.get("project", {}).get("classifiers", [])
    classifier_versions = _extract_classifier_versions(classifiers)
    hatch_versions = _extract_hatch_matrix(data)
    ci_versions = _extract_ci_matrix()
    bootstrap_min = _extract_bootstrap_min()

    sources = {
        "requires-python": requires_python,
        "min_version": _fmt_version(min_version) if min_version else None,
        "classifiers": _fmt_versions(classifier_versions),
        "hatch_matrix": _fmt_versions(hatch_versions),
        "ci_matrix": _fmt_versions(ci_versions),
        "bootstrap_min": _fmt_version(bootstrap_min) if bootstrap_min else None,
    }

    mismatches: list[str] = []

    # Check: classifier versions should match hatch and CI matrices
    if classifier_versions and hatch_versions and classifier_versions != hatch_versions:
        mismatches.append(
            f"Classifier versions ({_fmt_versions(classifier_versions)}) "
            f"!= Hatch matrix ({_fmt_versions(hatch_versions)})"
        )

    if classifier_versions and ci_versions and classifier_versions != ci_versions:
        mismatches.append(
            f"Classifier versions ({_fmt_versions(classifier_versions)}) "
            f"!= CI matrix ({_fmt_versions(ci_versions)})"
        )

    if hatch_versions and ci_versions and hatch_versions != ci_versions:
        mismatches.append(
            f"Hatch matrix ({_fmt_versions(hatch_versions)}) "
            f"!= CI matrix ({_fmt_versions(ci_versions)})"
        )

    # Check: min version should match the lowest classifier/matrix version
    if min_version and classifier_versions:
        lowest_classifier = classifier_versions[0]
        if min_version != lowest_classifier:
            mismatches.append(
                f"requires-python minimum ({_fmt_version(min_version)}) "
                f"!= lowest classifier ({_fmt_version(lowest_classifier)})"
            )

    if min_version and hatch_versions:
        lowest_hatch = hatch_versions[0]
        if min_version != lowest_hatch:
            mismatches.append(
                f"requires-python minimum ({_fmt_version(min_version)}) "
                f"!= lowest Hatch matrix ({_fmt_version(lowest_hatch)})"
            )

    # Check: bootstrap MIN_PYTHON should match requires-python
    if bootstrap_min and min_version and bootstrap_min != min_version:
        mismatches.append(
            f"bootstrap.py MIN_PYTHON ({_fmt_version(bootstrap_min)}) "
            f"!= requires-python ({_fmt_version(min_version)})"
        )

    # Check: current Python meets minimum
    current = sys.version_info[:2]
    current_ok = min_version is None or current >= min_version

    # -- Code compatibility analysis --
    python_files = _collect_python_files()
    code_scan = _scan_code_compatibility(python_files)
    code_min = code_scan["code_min_version"]

    # Use classifiers as the canonical declared version list
    declared = classifier_versions or hatch_versions or ci_versions

    # Versions declared but code doesn't support (code needs higher min)
    unsupported_declared = _find_unsupported_declared_versions(code_min, declared)
    if unsupported_declared:
        mismatches.append(
            f"Code requires >={_fmt_version(code_min)} but project declares "
            f"support for: {_fmt_versions(unsupported_declared)}"
        )

    # Stable versions code supports but aren't declared
    unlisted = _find_unlisted_supported_versions(code_min, declared)

    result = {
        "sources": sources,
        "mismatches": mismatches,
        "current_python": _fmt_version(current),
        "current_meets_minimum": current_ok,
        "code_analysis": {
            "files_scanned": code_scan["file_count"],
            "code_min_version": _fmt_version(code_min) if code_min > (3, 0) else None,
            "features_found": code_scan["features_found"],
            "unsupported_declared": _fmt_versions(unsupported_declared),
            "unlisted_supported": _fmt_versions(unlisted),
        },
        "ok": len(mismatches) == 0,
    }

    if not quiet:
        c = Colors(enabled=not no_color)
        ui = UI(
            title="Python Version Support",
            version=SCRIPT_VERSION,
            theme=THEME,
            no_color=no_color,
        )
        ui.header()

        ui.section("Version Sources")
        ui.kv("requires-python", requires_python or c.dim("(not set)"))
        ui.kv(
            "Classifiers",
            _fmt_versions(classifier_versions) or c.dim("(none)"),
        )
        ui.kv(
            "Hatch matrix",
            _fmt_versions(hatch_versions) or c.dim("(none)"),
        )
        ui.kv(
            "CI test matrix",
            _fmt_versions(ci_versions) or c.dim("(not found)"),
        )
        ui.kv(
            "bootstrap.py",
            _fmt_version(bootstrap_min) if bootstrap_min else c.dim("(not found)"),
        )
        ui.kv("Current Python", _fmt_version(current))

        ui.blank()
        if mismatches:
            ui.section("Mismatches")
            for m in mismatches:
                ui.status_line("cross", m, "red")
            ui.blank()
            ui.status_line(
                "cross",
                "Python version support is inconsistent across config files.",
                "red",
            )
        else:
            ui.status_line("check", "All version sources are consistent.", "green")

        if not current_ok:
            ui.status_line(
                "warn",
                f"Current Python {_fmt_version(current)} does not meet "
                f"minimum {_fmt_version(min_version) if min_version else '?'}",
                "yellow",
            )

        # Code compatibility analysis output
        ui.section("Code Compatibility Analysis")
        ui.kv("Files scanned", str(code_scan["file_count"]))
        if code_min > (3, 0):
            ui.kv("Code minimum version", _fmt_version(code_min))
        else:
            ui.kv(
                "Code minimum version", c.dim("(no version-specific features detected)")
            )

        if code_scan["features_found"]:
            ui.blank()
            ui.info_line("Version-specific features found:")
            for feat in code_scan["features_found"]:
                ui.info_line(
                    f"  {feat['file']}: {feat['feature']} "
                    f"(requires {feat['min_version']}+)"
                )

        if unsupported_declared:
            ui.blank()
            ui.status_line(
                "cross",
                f"Declared versions not supported by code: "
                f"{_fmt_versions(unsupported_declared)}",
                "red",
            )

        if unlisted:
            ui.blank()
            ui.status_line(
                "info",
                f"Versions code supports but not declared: {_fmt_versions(unlisted)}",
                "yellow",
            )
            ui.info_line(
                "Consider adding classifiers/matrix entries for these versions."
            )

        passed = (0 if mismatches else 1) + (1 if current_ok else 0)
        failed = (1 if mismatches else 0) + (0 if current_ok else 1)
        ui.footer(passed=passed, failed=failed)

    return result


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="check-python-support",
        description="Validate Python version support is consistent across config files.",
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
        print(f"check_python_support {SCRIPT_VERSION}: smoke ok")
        return 0

    level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(format="%(message)s", level=level)

    result = check_python_support(
        quiet=args.json_output or args.quiet,
        no_color=args.no_color,
    )

    if args.json_output:
        print(json.dumps(result, indent=2))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
