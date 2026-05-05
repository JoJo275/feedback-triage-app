#!/usr/bin/env python3
"""Build the v2.0 Tailwind CSS bundle (cross-platform wrapper).

Wraps the Tailwind Standalone CLI binary (no Node, no npm). On first
run, downloads the platform-appropriate binary into ``.tools/`` and
verifies its SHA256 against the pinned digest. Subsequent runs reuse
the cached binary.

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
"""

from __future__ import annotations

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
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _imports import find_repo_root

logger = logging.getLogger(__name__)

# --- Constants ---
SCRIPT_VERSION = "1.1.0"

# Pinned Tailwind Standalone CLI release. Refresh quarterly or when a
# fix is required; bump SCRIPT_VERSION in lockstep.
TAILWIND_VERSION = "v3.4.13"
TAILWIND_RELEASE_BASE = (
    f"https://github.com/tailwindlabs/tailwindcss/releases/download/{TAILWIND_VERSION}"
)

# Pinned SHA256 digests for the Tailwind v3.4.13 platform assets.
# The Windows-x64 hash was captured locally on 2026-05-05 from the
# binary downloaded by this script (TOFU). Other-platform digests are
# blank until verified on the corresponding host; an empty string
# disables verification for that asset only and emits a warning.
# Refresh every entry in the same commit that bumps TAILWIND_VERSION.
_PLATFORM_SHA256: dict[str, str] = {
    "tailwindcss-windows-x64.exe": (
        "76d7a37764c172bd25f9eb2b76d46099cca642f84c8dda10891a536018ab1511"
    ),
    "tailwindcss-windows-arm64.exe": "",
    "tailwindcss-linux-x64": "",
    "tailwindcss-linux-arm64": "",
    "tailwindcss-macos-x64": "",
    "tailwindcss-macos-arm64": "",
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


def _binary_name() -> str:
    """Return the Tailwind binary filename for this platform."""
    key = (platform.system(), platform.machine())
    asset = _PLATFORM_ASSETS.get(key)
    if asset is None:
        raise RuntimeError(
            f"No Tailwind Standalone CLI asset known for platform "
            f"{platform.system()} / {platform.machine()}. Add it to "
            f"_PLATFORM_ASSETS in scripts/build_css.py."
        )
    # Cache it under a stable local name so the rest of the script
    # doesn't care which asset was downloaded.
    return "tailwindcss.exe" if platform.system() == "Windows" else "tailwindcss"


def _binary_path(repo_root: Path) -> Path:
    return repo_root / TOOLS_DIR_NAME / _binary_name()


def _download_binary(repo_root: Path) -> Path:
    """Download the Tailwind binary for this platform into ``.tools/``."""
    asset = _PLATFORM_ASSETS[(platform.system(), platform.machine())]
    url = f"{TAILWIND_RELEASE_BASE}/{asset}"
    target = _binary_path(repo_root)
    target.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading Tailwind %s for %s ...", TAILWIND_VERSION, asset)
    tmp = target.with_suffix(target.suffix + ".part")
    # URL is a hard-coded HTTPS GitHub release asset; B310's file:/ /
    # custom-scheme concern does not apply.
    with urllib.request.urlopen(url, timeout=60) as response:  # nosec B310
        if response.status != 200:
            raise RuntimeError(f"Download failed: HTTP {response.status} from {url}")
        payload = response.read()

    expected = _PLATFORM_SHA256.get(asset, "")
    actual = hashlib.sha256(payload).hexdigest()
    if expected:
        if actual != expected:
            raise RuntimeError(
                f"Tailwind binary SHA256 mismatch for {asset}.\n"
                f"  expected: {expected}\n"
                f"  actual:   {actual}\n"
                f"If this is a legitimate version bump, update _PLATFORM_SHA256 "
                f"in scripts/build_css.py in the same commit as TAILWIND_VERSION."
            )
        logger.info("SHA256 verified: %s", actual)
    else:
        logger.warning(
            "No pinned SHA256 for %s; downloaded digest is %s. "
            "Add it to _PLATFORM_SHA256 in scripts/build_css.py.",
            asset,
            actual,
        )

    tmp.write_bytes(payload)
    tmp.replace(target)
    if platform.system() != "Windows":
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    logger.info("Tailwind installed at %s", target)
    return target


def _ensure_binary(repo_root: Path) -> Path:
    """Return path to the Tailwind binary, downloading if missing."""
    target = _binary_path(repo_root)
    if target.exists():
        return target
    return _download_binary(repo_root)


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
        raise RuntimeError(
            f"Tailwind did not produce {src}. Check the build output above for errors."
        )
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
    return argparse.ArgumentParser(
        prog="build_css",
        description="Build the v2.0 Tailwind CSS bundle (Standalone CLI).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the exit code."""
    parser = _build_parser()
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
    args = parser.parse_args(argv)

    logging.basicConfig(format="%(message)s", level=logging.INFO)

    if args.smoke:
        # Validate that platform mapping resolves and paths compute.
        _ = _binary_name()  # raises if unsupported platform
        repo_root = find_repo_root()
        assert (repo_root / "tailwind.config.cjs").is_file(), (
            "tailwind.config.cjs missing at repo root"
        )
        assert (repo_root / CSS_DIR_RELATIVE / INPUT_CSS).is_file(), "input.css missing"
        print(f"build_css {SCRIPT_VERSION}: smoke ok")
        return 0

    repo_root = find_repo_root()
    css_dir = repo_root / CSS_DIR_RELATIVE
    if not css_dir.is_dir():
        logger.error("CSS source dir not found: %s", css_dir)
        return 2

    # Allow CI to inject a pre-staged binary path; otherwise download.
    env_override = os.environ.get("TAILWINDCSS_BIN")
    if env_override:
        binary = Path(env_override)
        if not binary.is_file():
            logger.error("TAILWINDCSS_BIN points at a missing file: %s", binary)
            return 2
    else:
        binary = _ensure_binary(repo_root)

    if args.setup:
        return 0

    rc = _build_once(binary, css_dir, watch=args.watch)
    if rc != 0:
        return rc
    if args.watch:
        # Watch mode never reaches here under normal exit.
        return 0
    _hash_and_manifest(css_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
