#!/usr/bin/env python3
"""Test the Containerfile: build the image, run basic checks, and clean up.

Builds the production image directly from the Containerfile (without
docker compose), verifies the entrypoint works, checks the non-root user,
validates the image size is reasonable, and removes the test image.

Flags::

    --help       Show help message and exit
    --dry-run    Show what would be executed without running
    --keep       Keep the test image after running (skip cleanup)
    --verbose    Show full command output including stderr
    --timeout N  Per-step timeout in seconds (default: 300)
    --version    Print version and exit

Usage::

    python scripts/test_containerfile.py
    python scripts/test_containerfile.py --dry-run
    python scripts/test_containerfile.py --keep --verbose
    python scripts/test_containerfile.py --timeout 600

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in any repo with a ``Containerfile``.  Requires shared
    modules: ``_imports.py``, ``_progress.py``, ``_container_common.py``.
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess  # nosec B404
import sys

# -- Local script modules (not third-party; live in scripts/) ----------------
from _container_common import (
    check_docker_available as _check_docker_available,
)
from _container_common import (
    check_non_root as _check_non_root,
)
from _container_common import (
    run as _run,
)
from _imports import find_repo_root, import_sibling

Spinner = import_sibling("_progress").Spinner

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_VERSION = "1.4.0"

# Theme color for this script's dashboard output.
THEME = "cyan"
ROOT = find_repo_root()
# TODO (template users): Update IMAGE_NAME to match your project.
IMAGE_NAME = "simple-python-boilerplate:test"
# Maximum expected image size in MB (flag a warning if exceeded)
# TODO (template users): Adjust MAX_IMAGE_SIZE_MB for your application's
#   expected image size.  200 MB is generous for a Python CLI; a web app
#   with ML dependencies may need 500+ MB.
MAX_IMAGE_SIZE_MB = 200

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_image_size(image: str, *, verbose: bool = False) -> bool:
    """Report image size and warn if it exceeds the threshold."""
    try:
        result = _run(
            ["docker", "image", "inspect", image, "--format", "{{.Size}}"],
            verbose=verbose,
        )
        size_bytes = int(result.stdout.strip())
        size_mb = size_bytes / (1024 * 1024)
        logger.info("  Image size: %.1f MB", size_mb)
        if size_mb > MAX_IMAGE_SIZE_MB:
            logger.warning(
                "  Image exceeds %d MB threshold (%.1f MB)",
                MAX_IMAGE_SIZE_MB,
                size_mb,
            )
        return True
    except (subprocess.CalledProcessError, ValueError) as exc:
        logger.warning("  Could not determine image size: %s", exc)
        return True  # Non-fatal


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Test the Containerfile: build, validate, clean up.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the test image after running (skip cleanup)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full command output including stderr",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        metavar="N",
        help="Per-step timeout in seconds (default: 300)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not args.dry_run and not _check_docker_available():
        return 1

    # Ensure we're in the repo root so the docker build context is correct
    os.chdir(ROOT)

    # TODO (template users): Add or remove build steps to match your
    #   Containerfile (e.g. HEALTHCHECK validation, extra entrypoints,
    #   environment variable checks).
    build_cmd = ["docker", "build", "-t", IMAGE_NAME, "-f", "Containerfile", "."]
    if not args.verbose:
        build_cmd.insert(2, "--quiet")
    steps: list[tuple[str, list[str]]] = [
        ("Build image from Containerfile", build_cmd),
        (
            "Verify entrypoint (--help)",
            ["docker", "run", "--rm", IMAGE_NAME, "--help"],
        ),
        (
            "Check non-root user",
            ["docker", "run", "--rm", "--entrypoint", "id", IMAGE_NAME],
        ),
        (
            "Check Python is available",
            [
                "docker",
                "run",
                "--rm",
                "--entrypoint",
                "python",
                IMAGE_NAME,
                "--version",
            ],
        ),
    ]

    if args.dry_run:
        print("Dry run — would execute:")
        for desc, cmd in steps:
            print(f"  [{desc}] {' '.join(cmd)}")
        print(f"  [Check image size] docker image inspect {IMAGE_NAME} --format ...")
        if not args.keep:
            print(f"  [Remove test image] docker rmi {IMAGE_NAME}")
        return 0

    step_timeout = args.timeout
    failed = False
    with Spinner("Running containerfile tests", log_interval=5) as spin:
        for desc, cmd in steps:
            spin.update(desc)
            logger.info("Step: %s", desc)
            try:
                result = _run(cmd, verbose=args.verbose, timeout=step_timeout)
                # Extra validation for the non-root check
                if desc == "Check non-root user" and not _check_non_root(result.stdout):
                    failed = True
                    break
            except subprocess.TimeoutExpired:
                logger.error(
                    "Step timed out after %ds: %s (increase with --timeout)",
                    step_timeout,
                    desc,
                )
                failed = True
                break
            except subprocess.CalledProcessError as exc:
                logger.error("Step failed: %s (exit %d)", desc, exc.returncode)
                failed = True
                break

    # Report image size (non-fatal)
    if not failed:
        logger.info("Step: Check image size")
        _check_image_size(IMAGE_NAME, verbose=args.verbose)

    # Clean up image unless --keep
    if not args.keep:
        logger.info("Removing test image: %s", IMAGE_NAME)
        try:
            subprocess.run(  # nosec B603 B607
                ["docker", "rmi", IMAGE_NAME],
                check=False,
                timeout=30,
                capture_output=True,
            )
        except subprocess.TimeoutExpired:
            logger.warning("Image removal timed out")

    if failed:
        logger.error("Containerfile test FAILED")
        return 1

    logger.info("Containerfile test PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
