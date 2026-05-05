#!/usr/bin/env python3
"""Build the v2.0 Tailwind CSS bundle (cross-platform wrapper).

Wraps the Tailwind Standalone CLI binary (no Node, no npm). On first
run, downloads the platform-appropriate binary into ``.tools/``,
**verifies its SHA256** against the in-script pin, and caches it under
a version-stamped filename so a ``TAILWIND_VERSION`` bump invalidates
the cache automatically.

Outputs:
    src/feedback_triage/static/css/app.<hash>.css   (hashed for cache-busting)
    src/feedback_triage/static/css/manifest.json    ({"app.css": "app.<hash>.css"})

Usage::

    python scripts/build_css.py             # one-shot build
    python scripts/build_css.py --setup     # download binary, exit
    python scripts/build_css.py --watch     # rebuild on change
    python scripts/build_css.py --smoke     # self-check (no download, no build)

See:
    docs/project/spec/v2/css.md
    docs/adr/058-tailwind-via-standalone-cli.md
    scripts/.instructions.md   # required CLI conventions
"""

from __future__ import annotations

# 1. stdlib
import argparse
import hashlib
import json
import logging
import os
import platform
import shutil
import stat
import subprocess  # nosec B404 — argv-only invocations below
import sys
import urllib.request
from contextlib import suppress
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _imports import find_repo_root, import_sibling

_ui = import_sibling("_ui")
ExitCode = _ui.ExitCode

logger = logging.getLogger(__name__)

# --- Constants ---
SCRIPT_VERSION = "1.2.1"
THEME = "cyan"

# Pinned Tailwind Standalone CLI release. Refresh quarterly or when a
# fix is required; bump SCRIPT_VERSION and refresh _PLATFORM_SHA256
# in the same commit.
TAILWIND_VERSION = "v3.4.13"
TAILWIND_RELEASE_BASE = (
    f"https://github.com/tailwindlabs/tailwindcss/releases/download/{TAILWIND_VERSION}"
)

# Pinned SHA256 digests for the Tailwind v3.4.13 platform assets.
# All six entries were captured from
# https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.13/...
# on 2026-05-05. Refresh every entry in the same commit that bumps
# TAILWIND_VERSION. An empty string disables verification for that
# asset only and the script will refuse to use the binary unless
# ``--allow-unverified-download`` is passed (never used in CI).
_PLATFORM_SHA256: dict[str, str] = {
    "tailwindcss-windows-x64.exe": (
        "76d7a37764c172bd25f9eb2b76d46099cca642f84c8dda10891a536018ab1511"
    ),
    "tailwindcss-windows-arm64.exe": (
        "a6fbf64a92ca03b6a60488c8fb887e54b7b8199bcdd4890064d82498028470ab"
    ),
    "tailwindcss-linux-x64": (
        "c91ccc8642f79d7db5538e8d686a4dc18e00a93180f5377208a9a93c7efb9b6a"
    ),
    "tailwindcss-linux-arm64": (
        "d878afd75b6a792945c7f234543f0c389b7e026001e72505aa7cb76d3e1e47ec"
    ),
    "tailwindcss-macos-x64": (
        "3c4423494d8204b37455cb77b1b85ef5c6c42413f58e1516a4bf7528531c067d"
    ),
    "tailwindcss-macos-arm64": (
        "327703a4646081906e11d116ff4e8e43076466c3d269282bbe612555b9fe0c58"
    ),
}

# Platform → asset-name suffix (matches Tailwind's release naming).
_PLATFORM_ASSETS: dict[tuple[str, str], str] = {
    ("Windows", "AMD64"): "tailwindcss-windows-x64.exe",
    ("Windows", "ARM64"): "tailwindcss-windows-arm64.exe",
    ("Linux", "x86_64"): "tailwindcss-linux-x64",
    ("Linux", "aarch64"): "tailwindcss-linux-arm64",
    ("Darwin", "x86_64"): "tailwindcss-macos-x64",
    ("Darwin", "arm64"): "tailwindcss-macos-arm64",
}

CSS_DIR_RELATIVE = Path("src/feedback_triage/static/css")
INPUT_CSS = "input.css"
OUTPUT_CSS = "app.css"
MANIFEST = "manifest.json"
TOOLS_DIR_NAME = ".tools"


# --- Helpers ---
def _load_env() -> str | None:
    """Read env vars consumed by this script in one place."""
    return os.environ.get("TAILWINDCSS_BIN") or None


def _platform_asset() -> str:
    """Return the Tailwind asset name for the current platform.

    Raises:
        RuntimeError: when the (system, machine) pair is unknown.
    """
    key = (platform.system(), platform.machine())
    asset = _PLATFORM_ASSETS.get(key)
    if asset is None:
        msg = (
            f"No Tailwind Standalone CLI asset known for platform "
            f"{platform.system()} / {platform.machine()}. Add it to "
            f"_PLATFORM_ASSETS in scripts/build_css.py."
        )
        raise RuntimeError(msg)
    return asset


def _binary_filename() -> str:
    """Local cache filename, stamped with ``TAILWIND_VERSION``.

    Embedding the version means a ``TAILWIND_VERSION`` bump invalidates
    the cache automatically — the next run downloads the new binary
    instead of silently reusing the previous version.
    """
    suffix = ".exe" if platform.system() == "Windows" else ""
    return f"tailwindcss-{TAILWIND_VERSION}{suffix}"


def _binary_path(repo_root: Path) -> Path:
    return repo_root / TOOLS_DIR_NAME / _binary_filename()


def _verify_sha256(payload: bytes, asset: str, *, allow_unverified: bool) -> None:
    """Check ``payload`` against the pinned digest. Fail closed by default."""
    expected = _PLATFORM_SHA256.get(asset, "")
    actual = hashlib.sha256(payload).hexdigest()
    if expected:
        if actual != expected:
            msg = (
                f"Tailwind binary SHA256 mismatch for {asset}.\n"
                f"  expected: {expected}\n"
                f"  actual:   {actual}\n"
                f"If this is a legitimate version bump, update "
                f"_PLATFORM_SHA256 in scripts/build_css.py in the same "
                f"commit as TAILWIND_VERSION."
            )
            raise RuntimeError(msg)
        logger.info("SHA256 verified: %s", actual)
        return

    # No pin recorded for this platform.
    if not allow_unverified:
        msg = (
            f"No pinned SHA256 for {asset} (downloaded digest is {actual}).\n"
            f"Refusing to use an unverified Tailwind binary.\n"
            f"  - Add the digest to _PLATFORM_SHA256 in "
            f"scripts/build_css.py and retry, or\n"
            f"  - re-run with --allow-unverified-download (NEVER in CI), or\n"
            f"  - pre-stage a trusted binary and point TAILWINDCSS_BIN at it."
        )
        raise RuntimeError(msg)
    logger.warning(
        "Using unverified Tailwind binary for %s (digest %s). "
        "--allow-unverified-download is set; do NOT use this in CI.",
        asset,
        actual,
    )


def _download_binary(repo_root: Path, *, allow_unverified: bool) -> Path:
    """Download the Tailwind binary for this platform into ``.tools/``."""
    asset = _platform_asset()
    url = f"{TAILWIND_RELEASE_BASE}/{asset}"
    target = _binary_path(repo_root)
    target.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading Tailwind %s for %s ...", TAILWIND_VERSION, asset)
    # URL is a hard-coded HTTPS GitHub release asset; B310's file:/ /
    # custom-scheme concern does not apply.
    with urllib.request.urlopen(url, timeout=60) as response:  # nosec B310
        if response.status != 200:
            msg = f"Download failed: HTTP {response.status} from {url}"
            raise RuntimeError(msg)
        payload = response.read()

    _verify_sha256(payload, asset, allow_unverified=allow_unverified)

    tmp = target.with_suffix(target.suffix + ".part")
    tmp.write_bytes(payload)
    tmp.replace(target)
    if platform.system() != "Windows":
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Best-effort cleanup of stale cached binaries from older versions.
    for stale in target.parent.glob("tailwindcss-v*"):
        if stale.name != target.name:
            with suppress(OSError):
                stale.unlink()

    logger.info("Tailwind installed at %s", target)
    return target


def _ensure_binary(repo_root: Path, *, allow_unverified: bool) -> Path:
    """Return path to the Tailwind binary, downloading if missing."""
    target = _binary_path(repo_root)
    if target.exists():
        logger.debug("Reusing cached Tailwind binary: %s", target)
        return target
    return _download_binary(repo_root, allow_unverified=allow_unverified)


def _build_once(binary: Path, css_dir: Path, *, watch: bool) -> int:
    """Invoke Tailwind: input.css → app.css. Returns the process rc."""
    input_path = css_dir / INPUT_CSS
    output_path = css_dir / OUTPUT_CSS

    cmd = [
        str(binary),
        "-c",
        "tailwind.config.cjs",
        "-i",
        str(input_path),
        "-o",
        str(output_path),
        "--minify",
    ]
    if watch:
        cmd.append("--watch")
    logger.info("Running: %s", " ".join(cmd))
    proc = subprocess.run(cmd, check=False)  # nosec B603 — argv list, no shell
    return proc.returncode


def _hash_and_manifest(css_dir: Path) -> Path:
    """Hash app.css → app.<hash>.css; write manifest.json. Return hashed path."""
    src = css_dir / OUTPUT_CSS
    if not src.exists():
        msg = (
            f"Tailwind did not produce {src}. Check the build output above for errors."
        )
        raise RuntimeError(msg)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()[:10]
    hashed_name = f"app.{digest}.css"
    hashed_path = css_dir / hashed_name

    # Remove stale hashed builds before writing the new one.
    for stale in css_dir.glob("app.*.css"):
        if stale.name != hashed_name:
            stale.unlink()

    shutil.copy2(src, hashed_path)

    manifest = {OUTPUT_CSS: hashed_name}
    (css_dir / MANIFEST).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    logger.info("Wrote %s and %s", hashed_path.name, MANIFEST)
    return hashed_path


# --- CLI ---
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="build_css",
        description="Build the v2.0 Tailwind CSS bundle (Standalone CLI).",
        epilog=(
            "Examples:\n"
            "  python scripts/build_css.py --setup\n"
            "  python scripts/build_css.py\n"
            "  python scripts/build_css.py --watch -v\n"
            "  TAILWINDCSS_BIN=/usr/local/bin/tailwindcss "
            "python scripts/build_css.py\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {SCRIPT_VERSION}"
    )
    parser.add_argument(
        "--setup", action="store_true", help="Download the binary and exit"
    )
    parser.add_argument("--watch", action="store_true", help="Re-build on file change")
    parser.add_argument(
        "--smoke", action="store_true", help="Self-check; no download or build"
    )
    parser.add_argument(
        "--allow-unverified-download",
        action="store_true",
        help=(
            "Permit downloading a Tailwind binary even when no pinned "
            "SHA256 is recorded for this platform. NEVER set in CI."
        ),
    )
    parser.add_argument(
        "-q", "--quiet", action="count", default=0, help="Decrease verbosity"
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity"
    )
    return parser


def _do_smoke() -> int:
    try:
        _platform_asset()
        repo_root = find_repo_root()
    except (RuntimeError, FileNotFoundError) as exc:
        logger.error("smoke failed: %s", exc)
        return ExitCode.FAIL
    if not (repo_root / "tailwind.config.cjs").is_file():
        logger.error("tailwind.config.cjs missing at repo root")
        return ExitCode.FAIL
    if not (repo_root / CSS_DIR_RELATIVE / INPUT_CSS).is_file():
        logger.error("input.css missing")
        return ExitCode.FAIL
    for name, digest in _PLATFORM_SHA256.items():
        if digest and len(digest) != 64:
            logger.error("malformed SHA256 entry for %s", name)
            return ExitCode.FAIL
    print(f"build_css {SCRIPT_VERSION}: smoke ok")
    return ExitCode.OK


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns one of the ``ExitCode`` values."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    level = logging.INFO - 10 * args.verbose + 10 * args.quiet
    logging.basicConfig(format="%(message)s", level=max(level, logging.DEBUG))

    if args.smoke:
        return _do_smoke()

    try:
        repo_root = find_repo_root()
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return ExitCode.FAIL

    css_dir = repo_root / CSS_DIR_RELATIVE
    if not css_dir.is_dir():
        logger.error("CSS source dir not found: %s", css_dir)
        return ExitCode.FAIL

    env_bin = _load_env()
    if env_bin:
        binary = Path(env_bin)
        if not binary.is_file():
            logger.error("TAILWINDCSS_BIN points at a missing file: %s", binary)
            return ExitCode.FAIL
    else:
        try:
            binary = _ensure_binary(
                repo_root, allow_unverified=args.allow_unverified_download
            )
        except RuntimeError as exc:
            logger.error("%s", exc)
            return ExitCode.FAIL

    if args.setup:
        return ExitCode.OK

    rc = _build_once(binary, css_dir, watch=args.watch)
    if rc != 0:
        return ExitCode.FAIL
    if args.watch:
        return ExitCode.OK
    try:
        _hash_and_manifest(css_dir)
    except RuntimeError as exc:
        logger.error("%s", exc)
        return ExitCode.FAIL
    return ExitCode.OK


if __name__ == "__main__":
    sys.exit(main())
