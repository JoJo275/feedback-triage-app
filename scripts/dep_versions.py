#!/usr/bin/env python3
"""Dependency version manager for pyproject.toml and requirements files.

Show installed/latest versions, update inline comments, and upgrade
individual or all dependencies.

Dependabot updates the actual version *specifiers* (e.g., ``>=1.6`` to
``>=1.7``) but does NOT touch comments. This script fills that gap and
adds the ability to upgrade dependencies via pip.

The ``update-comments`` command annotates **every** dependency line with
a succinct description (from PyPI metadata) and the installed version.
Lines that already have a comment get their version refreshed; lines
without a comment receive a new ``# <summary> (vX.Y.Z)`` annotation.
This works across pyproject.toml **and** any requirements*.txt files
found in the project root.

Requirements:
    - Python 3.11+
    - pip
    - The project installed in the current environment

Subcommands and flags::

    show                     Show installed and latest versions (default)
      --offline              Skip querying PyPI for latest versions
      --dry-run              Write preview report to dep-versions-report.md
    update-comments          Update inline version comments in pyproject.toml
                             and requirements*.txt files
      --dry-run              Preview without modifying files; writes report
    upgrade                  Upgrade dependencies via pip
      [package]              Package to upgrade (omit to upgrade all)
      [version]              Target version (omit to upgrade to latest)
      --dry-run              Show what would be upgraded without installing
    --version                Print version and exit
    --smoke                  Quick health check; exit 0 immediately

Usage::

    python scripts/dep_versions.py                       # Show all dep versions
    python scripts/dep_versions.py show --offline        # Skip PyPI check
    python scripts/dep_versions.py show --dry-run        # Show + write report
    python scripts/dep_versions.py update-comments       # Sync comments with installed
    python scripts/dep_versions.py update-comments --dry-run  # Preview comment changes
    python scripts/dep_versions.py upgrade               # Upgrade ALL deps to latest
    python scripts/dep_versions.py upgrade --dry-run     # Preview upgrades + report
    python scripts/dep_versions.py upgrade ruff           # Upgrade ruff to latest
    python scripts/dep_versions.py upgrade ruff 0.9.0    # Upgrade ruff to specific version

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in any Python repo with a ``pyproject.toml`` that
    declares dependencies.  Requires shared modules: ``_colors.py``,
    ``_imports.py``, ``_ui.py``, ``_progress.py``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404
import sys
import tomllib
from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as pkg_metadata
from importlib.metadata import version as pkg_version
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors
from _imports import find_repo_root, import_sibling
from _ui import UI

_progress = import_sibling("_progress")
ProgressBar = _progress.ProgressBar
Spinner = _progress.Spinner

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_VERSION = "1.5.0"


def _clickable_path(path: Path) -> str:
    """Return a terminal-clickable file path using OSC 8 hyperlinks."""
    c = Colors()
    name = str(path.name)
    if sys.stdout.isatty():
        uri = path.resolve().as_uri()
        return f"\033]8;;{uri}\033\\{c.cyan(name)}\033]8;;\033\\"
    return c.cyan(name)


# Theme color for this script's dashboard output.
THEME = "blue"

ROOT = find_repo_root()
PYPROJECT = ROOT / "pyproject.toml"

# TODO (template users): If you use a monorepo with multiple
#   pyproject.toml files, update PYPROJECT to point to the correct one
#   or extend the script to accept a --pyproject flag.


def _get_req_files() -> list[Path]:
    """Return requirements files, discovered fresh each call.

    Avoids stale results if files are created/deleted after import.
    """
    return sorted(ROOT.glob("requirements*.txt"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _warn_if_no_venv() -> None:
    """Print a prominent warning banner if running outside a virtual environment.

    Installing or upgrading packages outside a venv risks polluting
    the global Python installation.  This project convention is to
    always use a Hatch-managed environment.
    """
    if sys.prefix == sys.base_prefix:
        c = Colors()
        sym = (
            "\u26a0"
            if sys.stdout.encoding and "utf" in sys.stdout.encoding.lower()
            else "!"
        )
        border = c.yellow("\u2500" * 60)
        print()
        print(f"  {border}")
        print(
            f"  {c.yellow(c.bold(f'  {sym}  WARNING: No virtual environment detected'))}"
        )
        print(f"  {border}")
        print(
            f"  {c.yellow('  Upgrading packages here will modify the global Python')}"
        )
        print(f"  {c.yellow('  installation. Consider running:')}")
        print(f"  {c.bold(c.cyan('    hatch shell'))}")
        print(f"  {border}")
        print()


def _installed_version(pkg: str) -> str | None:
    """Return the installed version of *pkg*, or ``None``."""
    try:
        return pkg_version(pkg)
    except PackageNotFoundError:
        return None


def _package_summary(pkg: str) -> str | None:
    """Return the one-line PyPI summary for *pkg*, or ``None``.

    Uses locally installed metadata — no network call required.
    If the summary starts with the package name (e.g. ``"pytest:
    simple powerful testing…"``), the redundant prefix is stripped.
    """
    try:
        meta = pkg_metadata(pkg)
        summary: str | None = meta["Summary"]
        if not summary:
            return None
        # Strip trailing periods for consistency
        summary = summary.rstrip(".")
        # Remove leading "pkgname: " or "pkgname - " prefix (redundant)
        prefix_re = re.compile(
            r"^" + re.escape(pkg) + r"\s*[:—–-]\s*",  # noqa: RUF001
            re.IGNORECASE,
        )
        summary = prefix_re.sub("", summary)
        return summary
    except PackageNotFoundError:
        return None


def _latest_version(pkg: str) -> str | None:
    """Query PyPI for the latest version of *pkg*.

    Tries ``pip index versions --format=json`` first (stable, machine-
    readable output added in pip 24.2).  Falls back to parsing the
    human-readable output for older pip versions.

    Returns ``None`` on any failure (network, pip too old, etc.).
    """
    try:
        # Attempt JSON format first (pip >= 24.2)
        result = subprocess.run(  # nosec B603
            [
                sys.executable,
                "-m",
                "pip",
                "index",
                "versions",
                pkg,
                "--format=json",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                # JSON output: {"name": ..., "version": "1.2.3", ...}
                ver = data.get("version")
                if ver:
                    return str(ver)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        # Fallback: parse human-readable output (older pip)
        result = subprocess.run(  # nosec B603
            [sys.executable, "-m", "pip", "index", "versions", pkg],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return None
        # Output like: "my-package (1.2.3)"
        match = re.search(r"\(([^)]+)\)", result.stdout)
        return match.group(1) if match else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _normalise_name(raw: str) -> str:
    """Normalise a PEP 503 package name for comparison.

    ``mkdocs-material`` and ``mkdocs_material`` both become ``mkdocs-material``.
    Extras are stripped: ``mkdocstrings[python]`` -> ``mkdocstrings``.
    """
    name = re.split(r"[><=!~;\[]", raw)[0].strip()
    return re.sub(r"[-_.]+", "-", name).lower()


def _capitalise(text: str) -> str:
    """Upper-case the first letter, leave the rest unchanged.

    Unlike ``str.capitalize()``, this does **not** lower-case the tail,
    so ``"PyPI metadata"`` stays ``"PyPI metadata"`` instead of becoming
    ``"Pypi metadata"``.
    """
    if not text:
        return text
    return text[0].upper() + text[1:]


# ---------------------------------------------------------------------------
# TOML parser (dependency lines only)
# ---------------------------------------------------------------------------

_DEP_RE = re.compile(
    r"""
    ^                     # start of line
    (?P<indent>\s*)       # leading whitespace
    "                     # opening quote
    (?P<spec>[^"]+)       # dependency specifier
    "                     # closing quote
    (?P<sep>\s*,)         # comma (possibly with space before)
    (?P<trail>.*)         # trailing content (comment or nothing)
    $
    """,
    re.VERBOSE,
)


def _parse_deps_from_toml(text: str) -> dict[str, list[str]]:
    """Return ``{group_name: [specifier_string, ...]}`` from pyproject.toml.

    Uses ``tomllib`` (stdlib) for reliable TOML parsing.  Reads
    ``[project].dependencies`` and every key under
    ``[project.optional-dependencies]``.
    """
    data = tomllib.loads(text)
    project = data.get("project", {})
    groups: dict[str, list[str]] = {}

    deps = project.get("dependencies")
    if deps:
        groups["dependencies"] = list(deps)

    opt = project.get("optional-dependencies", {})
    for group_name, specs in opt.items():
        groups[group_name] = list(specs)

    return groups


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def collect_report(*, check_latest: bool = True) -> list[dict[str, str | None]]:
    """Build a report of all dependencies with installed and latest versions."""
    text = PYPROJECT.read_text(encoding="utf-8")
    groups = _parse_deps_from_toml(text)

    rows: list[dict[str, str | None]] = []
    seen: set[str] = set()

    # Count total unique deps for progress
    all_deps: list[tuple[str, str]] = []
    for group, deps in groups.items():
        for raw in deps:
            name = _normalise_name(raw)
            if name not in seen and "simple-python-boilerplate" not in name:
                seen.add(name)
                all_deps.append((group, raw))
    seen.clear()

    if check_latest:
        bar = ProgressBar(
            total=len(all_deps), label="Querying PyPI", color="cyan", pulse=True
        )
        bar.start_pulse()  # start pulse immediately
        spinner = None
    else:
        bar = None
        spinner = Spinner("Collecting packages", color="cyan")
        spinner.start()

    for group, raw in all_deps:
        name = _normalise_name(raw)
        if name in seen:
            continue
        seen.add(name)

        installed = _installed_version(name)
        latest = _latest_version(name) if check_latest else None
        upgradable = installed != latest if installed and latest else None

        if bar is not None:
            bar.update(name)
        elif spinner is not None:
            spinner.update(name)

        rows.append(
            {
                "group": group,
                "name": name,
                "specifier": raw,
                "installed": installed,
                "latest": latest,
                "upgradable": "yes" if upgradable else "",
            }
        )

    if bar is not None:
        bar.finish(vanish=True)
    elif spinner is not None:
        spinner.finish()

    return rows


def print_report(rows: list[dict[str, str | None]]) -> None:
    """Pretty-print the dependency report."""
    c = Colors()
    ui = UI(title="Dependency Versions", version=SCRIPT_VERSION, theme=THEME)
    ui.section("Packages")

    w_name = max((len(r["name"] or "") for r in rows), default=10)
    w_group = max((len(r["group"] or "") for r in rows), default=10)
    w_spec = min(max((len(r["specifier"] or "") for r in rows), default=10), 30)
    w_inst = max((len(r["installed"] or "-") for r in rows), default=9)
    w_lat = max((len(r["latest"] or "-") for r in rows), default=6)

    ui.table_header(
        [
            ("Package", w_name),
            ("Group", w_group),
            ("Specifier", w_spec),
            ("Installed", w_inst),
            ("Latest", w_lat),
            ("Upgrade?", 8),
        ]
    )

    for r in rows:
        upgradable = r["upgradable"] == "yes"
        flag = c.yellow("^") if upgradable else ""
        inst = r["installed"] or "-"
        lat = r["latest"] or "-"
        name = r["name"] or ""
        spec = r["specifier"] or ""
        if len(spec) > w_spec:
            spec = spec[: w_spec - 1] + "\u2026"
        # Colorize upgradable rows
        if upgradable:
            name = c.yellow(name)
            inst = c.yellow(inst)
            lat = c.yellow(lat)
        ui.table_row(
            [
                (name, w_name),
                (r["group"] or "", w_group),
                (spec, w_spec),
                (inst, w_inst),
                (lat, w_lat),
                (flag, 8),
            ]
        )

    # Summary counts
    groups = {r["group"] for r in rows if r.get("group")}
    upgradable_count = sum(1 for r in rows if r["upgradable"] == "yes")
    ui.blank()
    ui.info_line(
        f"{len(rows)} package(s) across {len(groups)} group(s)"
        + (f", {upgradable_count} upgradable" if upgradable_count else "")
    )


# ---------------------------------------------------------------------------
# Comment updater
# ---------------------------------------------------------------------------


def update_comments(rows: list[dict[str, str | None]]) -> int:
    """Rewrite inline comments on dependency lines in pyproject.toml.

    Behaviour per line:

    * **Has a comment with a version** — version is replaced with the
      installed version, description text is preserved.
    * **Has a comment without a version** — installed version is appended
      in parentheses.
    * **No comment at all** — a new comment is generated from the
      package's PyPI summary and the installed version, e.g.
      ``# Simple powerful testing with Python (v8.4.2)``.

    Returns the number of lines modified.
    """
    text = PYPROJECT.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    versions: dict[str, str] = {}
    for r in rows:
        name = r.get("name", "")
        inst = r.get("installed")
        if name and inst:
            versions[name] = inst

    modified = 0

    for i, line in enumerate(lines):
        m = _DEP_RE.match(line.rstrip("\n"))
        if not m:
            continue

        spec = m.group("spec")
        name = _normalise_name(spec)
        trail = m.group("trail")

        if name not in versions:
            continue

        installed = versions[name]

        if "#" in trail:
            # ---- existing comment: update version in place ----
            comment_match = re.search(r"#\s*(.*)", trail)
            if not comment_match:
                continue

            comment_text = comment_match.group(1).strip()

            ver_in_comment = re.search(r"v?\d+\.\d+[\.\d]*", comment_text)
            if ver_in_comment:
                new_comment = (
                    comment_text[: ver_in_comment.start()]
                    + f"v{installed}"
                    + comment_text[ver_in_comment.end() :]
                )
            else:
                new_comment = f"{comment_text} (v{installed})"
        else:
            # ---- no comment: generate description + version ----
            summary = _package_summary(name)
            desc = _capitalise(summary) if summary else name
            new_comment = f"{desc} (v{installed})"

        new_trail = f"  # {new_comment}"
        new_line = f'{m.group("indent")}"{spec}"{m.group("sep")}{new_trail}\n'

        if new_line != lines[i]:
            lines[i] = new_line
            modified += 1

    if modified:
        PYPROJECT.write_text("".join(lines), encoding="utf-8")

    return modified


# ---------------------------------------------------------------------------
# Requirements-file comment updater
# ---------------------------------------------------------------------------

# Matches an uncommented dependency line in a requirements file.
# Examples:  pytest, pytest>=8.0, pytest==8.4.2, ruff  # some comment
_REQ_DEP_RE = re.compile(
    r"""
    ^                        # start of line
    (?P<spec>[A-Za-z0-9]     # package name starts with alphanumeric
        [A-Za-z0-9._-]*      # rest of package name
        (?:\[[^\]]+\])?      # optional extras  e.g. [python]
        (?:[><=!~]\S*)?)     # optional version constraint
    (?P<trail>\s*(?:[#].*)?) # optional trailing comment
    $
    """,
    re.VERBOSE,
)


def update_requirements_comments() -> dict[str, int]:
    """Update inline comments in every ``requirements*.txt`` file.

    The same logic as ``update_comments`` for pyproject.toml is applied:

    * Lines with a comment get their version refreshed.
    * Lines without a comment receive a generated
      ``# <summary> (vX.Y.Z)`` annotation.

    Returns a mapping ``{filename: lines_modified}``.
    """
    results: dict[str, int] = {}

    for req_path in _get_req_files():
        text = req_path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        modified = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            # Skip blanks, pure comments, options, and -r includes
            if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                continue

            m = _REQ_DEP_RE.match(stripped)
            if not m:
                continue

            raw_spec = m.group("spec")
            name = _normalise_name(raw_spec)
            trail = m.group("trail").strip()
            installed = _installed_version(name)

            if not installed:
                continue

            if trail and "#" in trail:
                # Update existing comment
                comment_match = re.search(r"#\s*(.*)", trail)
                if not comment_match:
                    continue
                comment_text = comment_match.group(1).strip()
                ver_in = re.search(r"v?\d+\.\d+[\.\d]*", comment_text)
                if ver_in:
                    new_comment = (
                        comment_text[: ver_in.start()]
                        + f"v{installed}"
                        + comment_text[ver_in.end() :]
                    )
                else:
                    new_comment = f"{comment_text} (v{installed})"
            else:
                # Generate new comment
                summary = _package_summary(name)
                desc = _capitalise(summary) if summary else name
                new_comment = f"{desc} (v{installed})"

            new_line = f"{raw_spec}  # {new_comment}\n"
            if new_line != lines[i]:
                lines[i] = new_line
                modified += 1

        if modified:
            req_path.write_text("".join(lines), encoding="utf-8")
        results[req_path.name] = modified

    return results


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade_package(name: str, target_version: str | None = None) -> bool:
    """Upgrade a single package via pip.

    Args:
        name: Package name (e.g., ``ruff``).
        target_version: Specific version to install. If ``None``, installs
            the latest version.

    Returns:
        ``True`` if pip returned success.
    """
    c = Colors()
    spec = f"{name}=={target_version}" if target_version else name
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", spec]
    print(f"  pip install --upgrade {c.cyan(spec)}")
    result = subprocess.run(  # nosec B603
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"  {c.red('FAILED')}: {result.stderr.strip()}")
        return False
    # Show what was installed
    new_ver = _installed_version(name)
    print(f"  {c.green('->')} {name} {c.green(new_ver or '?')}")
    return True


# ---------------------------------------------------------------------------
# Specifier updater
# ---------------------------------------------------------------------------

# Matches a version specifier like >=1.6, >=0.27, ==8.0.0
_SPEC_VER_RE = re.compile(r"(>=|~=|==)([\d]+(?:\.[\d]+)*)")


def _update_minimum_specifier(old_spec: str, new_version: str) -> str:
    """Update the minimum version in a specifier to *new_version*.

    Only touches ``>=`` and ``~=`` constraints — exact pins (``==``) and
    upper bounds (``<``, ``<=``) are left alone.

    Examples::

        _update_minimum_specifier("ruff>=0.9.0", "0.15.0")  -> "ruff>=0.15.0"
        _update_minimum_specifier("mkdocs>=1.6", "1.6.1")   -> "mkdocs>=1.6.1"
        _update_minimum_specifier("pytest", "9.0.2")         -> "pytest"  # no constraint
    """

    def _replace(m: re.Match[str]) -> str:
        op = m.group(1)
        if op in (">=", "~="):
            return f"{op}{new_version}"
        return m.group(0)  # leave == pins alone

    return _SPEC_VER_RE.sub(_replace, old_spec)


def update_specifiers_in_toml(upgraded: list[dict[str, str | None]]) -> int:
    """Update version specifiers in pyproject.toml for upgraded packages.

    For each upgraded package, rewrites ``>=old`` to ``>=new`` in the
    dependency line.  Only touches ``>=`` and ``~=`` constraints.

    Returns the number of lines modified.
    """
    text = PYPROJECT.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # Build lookup: normalised name -> new installed version
    new_versions: dict[str, str] = {}
    for r in upgraded:
        name = r.get("name", "")
        inst = _installed_version(name) if name else None
        if name and inst:
            new_versions[name] = inst

    modified = 0

    for i, line in enumerate(lines):
        m = _DEP_RE.match(line.rstrip("\n"))
        if not m:
            continue

        spec = m.group("spec")
        name = _normalise_name(spec)

        if name not in new_versions:
            continue

        new_spec = _update_minimum_specifier(spec, new_versions[name])
        if new_spec == spec:
            continue

        new_line = (
            f'{m.group("indent")}"{new_spec}"{m.group("sep")}{m.group("trail")}\n'
        )

        if new_line != lines[i]:
            lines[i] = new_line
            modified += 1

    if modified:
        PYPROJECT.write_text("".join(lines), encoding="utf-8")

    return modified


def upgrade_all(rows: list[dict[str, str | None]]) -> int:
    """Upgrade all packages that have a newer version available.

    Returns the number of packages upgraded.
    """
    upgraded = 0
    for r in rows:
        if (
            r["upgradable"] == "yes"
            and r["name"]
            and r["installed"]
            and upgrade_package(r["name"])
        ):
            upgraded += 1
    return upgraded


# ---------------------------------------------------------------------------
# Dry-run report generation
# ---------------------------------------------------------------------------

_REPORT_OUTPUT = ROOT / "dep-versions-report.md"


def _generate_dry_run_report(
    rows: list[dict[str, str | None]],
    command: str,
) -> Path:
    """Write a Markdown dry-run report to ``dep-versions-report.md``.

    Includes a summary table, a dependency tree showing what would
    change, and details per group.  Returns the output path.
    """
    import datetime

    now = datetime.datetime.now(tz=datetime.UTC)
    upgradable = [r for r in rows if r["upgradable"] == "yes"]
    groups = sorted({r["group"] for r in rows if r.get("group")})

    lines: list[str] = []
    w = lines.append  # shorthand

    w("# Dependency Versions \u2014 Dry-Run Preview")
    w("")
    w("<!-- Auto-generated by dep_versions.py \u2014 do not edit manually. -->")
    w("")
    w("| **Report type** | Dry-Run Preview |")
    w("| --- | --- |")
    w(f"| **Generated by** | `dep_versions.py` v{SCRIPT_VERSION} |")
    w(f"| **Timestamp** | {now.strftime('%Y-%m-%d %H:%M:%S UTC')} |")
    w(f"| **Command** | `{command}` |")
    w(f"| **Total packages** | {len(rows)} |")
    w(f"| **Upgradable** | {len(upgradable)} |")
    w(f"| **Groups** | {', '.join(groups)} |")
    w("")
    w(
        "> **Preview only** \u2014 no files were modified. "
        "Re-run without `--dry-run` to apply."
    )
    w("")
    w("---")
    w("")
    w("## All Dependencies")
    w("")
    w("| Package | Group | Specifier | Installed | Latest | Upgrade? |")
    w("| :--- | :--- | :--- | :--- | :--- | :---: |")
    for r in rows:
        up = "\u2b06\ufe0f" if r["upgradable"] == "yes" else ""
        w(
            f"| {r['name']} | {r['group']} | `{r['specifier']}` "
            f"| {r['installed'] or '-'} | {r['latest'] or '-'} | {up} |"
        )
    w("")

    if upgradable:
        w("---")
        w("")
        w("## Upgradable Packages")
        w("")
        w("| Package | Installed | Latest | Delta |")
        w("| :--- | :--- | :--- | :--- |")
        for r in upgradable:
            w(
                f"| **{r['name']}** | {r['installed']} "
                f"| {r['latest']} | `{r['installed']}` \u2192 `{r['latest']}` |"
            )
        w("")

    w("---")
    w("")
    w("## Virtual Dependency Tree")
    w("")
    w("```")
    w("pyproject.toml")
    for g_idx, group in enumerate(groups):
        g_rows = [r for r in rows if r["group"] == group]
        is_last_group = g_idx == len(groups) - 1
        branch = "\u2514" if is_last_group else "\u251c"
        w(f"{branch}\u2500\u2500 [{group}]")
        for r_idx, r in enumerate(g_rows):
            is_last = r_idx == len(g_rows) - 1
            prefix = "    " if is_last_group else "\u2502   "
            connector = "\u2514" if is_last else "\u251c"
            marker = " \u2b06" if r["upgradable"] == "yes" else ""
            ver = r["installed"] or "?"
            w(f"{prefix}{connector}\u2500\u2500 {r['name']} ({ver}){marker}")
    w("```")
    w("")
    w("---")
    w("")
    w(
        f"*Generated by `dep_versions.py` v{SCRIPT_VERSION} on "
        f"{now.strftime('%Y-%m-%d')}*"
    )
    w("")

    _REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    return _REPORT_OUTPUT


def _print_recommended_scripts() -> None:
    """Print the recommended scripts section (called at end of every command)."""
    ui = UI(title="Dependency Versions", version=SCRIPT_VERSION, theme=THEME)
    ui.recommended_scripts(
        [
            "repo_sauron",
            "env_inspect",
            "repo_doctor",
            "env_doctor",
            "doctor",
        ],
        preamble="Scripts that expand on dependency and project information.",
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="dep_versions",
        description="Dependency version manager for pyproject.toml and requirements files.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick import and arg-parse health check; exit 0 immediately "
        "(aliases --offline for consistency with other scripts)",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # -- show (default) --
    show_p = sub.add_parser(
        "show",
        help="Show installed and latest versions of all dependencies (default).",
    )
    show_p.add_argument(
        "--offline",
        action="store_true",
        help="Skip querying PyPI for latest versions (faster).",
    )
    show_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Write a preview report to dep-versions-report.md.",
    )

    # -- update-comments --
    uc_p = sub.add_parser(
        "update-comments",
        help=(
            "Update inline version comments in pyproject.toml and "
            "requirements*.txt files.  Adds descriptions and versions "
            "to lines that have no comment."
        ),
    )
    uc_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would change without modifying files; writes dep-versions-report.md.",
    )

    # -- upgrade --
    upgrade_p = sub.add_parser(
        "upgrade",
        help="Upgrade dependencies via pip.",
    )
    upgrade_p.add_argument(
        "package",
        nargs="?",
        default=None,
        help="Package to upgrade (omit to upgrade all upgradable).",
    )
    upgrade_p.add_argument(
        "version",
        nargs="?",
        default=None,
        help="Target version (omit to upgrade to latest).",
    )
    upgrade_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be upgraded without installing anything.",
    )

    return parser


def main() -> int:
    """Entry point.

    Returns:
        Exit code: 0 = success, 1 = errors encountered.
    """
    parser = build_parser()
    args = parser.parse_args()

    if args.smoke:
        print(f"dep_versions {SCRIPT_VERSION}: smoke ok")
        return 0

    c = Colors()

    # Default to "show" when no subcommand given
    command = args.command or "show"
    dry_run = getattr(args, "dry_run", False)

    ui = UI(
        title="Dependency Versions",
        version=SCRIPT_VERSION,
        theme=THEME,
    )
    ui.header()

    if command == "show":
        offline = getattr(args, "offline", False)
        rows = collect_report(check_latest=not offline)
        if not rows:
            print("  No dependencies found in pyproject.toml.")
            _print_recommended_scripts()
            print()
            return 0
        print_report(rows)

        if dry_run:
            report_path = _generate_dry_run_report(
                rows, f"dep_versions show{'  --offline' if offline else ''} --dry-run"
            )
            _check = c.green("\u2713")
            _link = _clickable_path(report_path)
            print(f"\n  {_check} Report written to {_link}")

    elif command == "update-comments":
        rows = collect_report(check_latest=False)
        if not rows:
            print("  No dependencies found in pyproject.toml.")
            _print_recommended_scripts()
            print()
            return 0
        print_report(rows)

        if dry_run:
            report_path = _generate_dry_run_report(
                rows, "dep_versions update-comments --dry-run"
            )
            _check = c.green("\u2713")
            _link = _clickable_path(report_path)
            print(f"\n  {_check} Report written to {_link}")
            print(f"  {c.dim('No files were modified (dry-run).')}")
        else:
            # ---- pyproject.toml ----
            count = update_comments(rows)
            if count:
                _check = "\u2713"
                print(
                    f"\n  {c.green(_check)} Updated"
                    f" {c.green(str(count))} comment(s)"
                    f" in pyproject.toml"
                )
            else:
                print(f"\n  {c.dim('pyproject.toml: no changes needed.')}")

            # ---- requirements*.txt ----
            req_results = update_requirements_comments()
            for fname, n in req_results.items():
                if n:
                    _check = "\u2713"
                    print(
                        f"  {c.green(_check)} Updated"
                        f" {c.green(str(n))} comment(s)"
                        f" in {fname}"
                    )
                else:
                    print(f"  {c.dim(f'{fname}: no changes needed.')}")

    elif command == "upgrade":
        pkg = getattr(args, "package", None)
        ver = getattr(args, "version", None)

        # Warn if running outside a virtual environment
        _warn_if_no_venv()

        if pkg:
            # Upgrade a single package
            normalised = _normalise_name(pkg)
            # Verify it's one of our declared deps
            text = PYPROJECT.read_text(encoding="utf-8")
            groups = _parse_deps_from_toml(text)
            all_deps = {_normalise_name(s) for specs in groups.values() for s in specs}
            if normalised not in all_deps:
                print(
                    f"  '{pkg}' is not declared in pyproject.toml."
                    " Only deps listed in [project.optional-dependencies]"
                    " or [project].dependencies can be upgraded."
                )
                return 1
            if dry_run:
                latest = _latest_version(normalised)
                installed = _installed_version(normalised)
                print(f"  [dry-run] {normalised}: {installed} -> {latest or '?'}")
                # Generate single-package report
                single_row = [
                    {
                        "group": "upgrade",
                        "name": normalised,
                        "specifier": normalised,
                        "installed": installed,
                        "latest": latest,
                        "upgradable": "yes" if installed != latest else "",
                    }
                ]
                report_path = _generate_dry_run_report(
                    single_row, f"dep_versions upgrade {pkg} --dry-run"
                )
                _check = c.green("\u2713")
                _link = _clickable_path(report_path)
                print(f"\n  {_check} Report written to {_link}")
            else:
                success = upgrade_package(normalised, ver)
                if not success:
                    return 1
        else:
            # Upgrade all
            rows = collect_report(check_latest=True)
            if not rows:
                print("  No dependencies found.")
                _print_recommended_scripts()
                print()
                return 0
            print_report(rows)

            upgradable = [r for r in rows if r["upgradable"] == "yes"]
            if not upgradable:
                _msg = "\u2713 All dependencies are up to date."
                print(f"\n  {c.green(_msg)}")
                _print_recommended_scripts()
                print()
                return 0

            if dry_run:
                print(
                    f"\n  {c.yellow('[dry-run]')} {c.yellow(str(len(upgradable)))}"
                    " package(s) would be upgraded:\n"
                )
                max_name = max(len(r["name"] or "") for r in upgradable)
                max_inst = max(len(r["installed"] or "") for r in upgradable)
                for r in upgradable:
                    padded_name = (r["name"] or "").ljust(max_name + 2)
                    inst = (r["installed"] or "").rjust(max_inst)
                    print(
                        f"    {c.cyan(padded_name)}"
                        f" {inst} -> {c.green(r['latest'] or '?')}"
                    )
                report_path = _generate_dry_run_report(
                    rows, "dep_versions upgrade --dry-run"
                )
                _check = c.green("\u2713")
                _link = _clickable_path(report_path)
                print(f"\n  {_check} Report written to {_link}")
                print(f"  {c.dim('Run without --dry-run to install.')}")

            else:
                print(f"\n{c.bold(f'Upgrading {len(upgradable)} package(s)...')}\n")
                count = upgrade_all(rows)
                print(f"\n{c.green(f'Upgraded {count} package(s).')}")

        # After successful upgrade, refresh specifiers and comments
        if not dry_run:
            # Update >=X.Y specifiers in pyproject.toml
            fresh_rows = collect_report(check_latest=False)
            upgradable_rows = [
                r
                for r in fresh_rows
                if r["name"]
                in {
                    _normalise_name(pkg)
                    for pkg in (
                        [pkg] if pkg else [r2["name"] or "" for r2 in fresh_rows]
                    )
                }
            ]
            spec_count = update_specifiers_in_toml(upgradable_rows)
            if spec_count:
                print(f"  Updated {spec_count} specifier(s) in pyproject.toml")

            # Refresh version comments
            print("  Refreshing version comments...")
            fresh_rows = collect_report(check_latest=False)
            toml_count = update_comments(fresh_rows)
            req_results = update_requirements_comments()
            if toml_count:
                print(f"  Updated {toml_count} comment(s) in pyproject.toml")
            for fname, n in req_results.items():
                if n:
                    print(f"  Updated {n} comment(s) in {fname}")

    _print_recommended_scripts()
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
