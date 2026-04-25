#!/usr/bin/env python3
"""Test the docker compose stack: build, run, validate, and clean up.

Builds the image via docker compose, runs the container to verify the
entrypoint works and the configuration is valid, then tears everything
down.

Flags::

    --help       Show help message and exit
    --dry-run    Show what would be executed without running
    --keep       Keep containers and images after running (skip cleanup)
    --verbose    Show full command output including stderr
    --timeout N  Per-step timeout in seconds (default: 300)
    --version    Print version and exit

Usage::

    python scripts/test_docker_compose.py
    python scripts/test_docker_compose.py --dry-run
    python scripts/test_docker_compose.py --keep --verbose
    python scripts/test_docker_compose.py --timeout 600

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in any repo with a ``docker-compose.yml`` and
    ``Containerfile``.  Requires shared modules: ``_imports.py``,
    ``_progress.py``, ``_container_common.py``.
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

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Test the docker compose stack: build, run, validate, clean up.",
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
        help="Keep containers and images after running (skip cleanup)",
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

    # Ensure we're in the repo root so docker compose finds docker-compose.yml
    os.chdir(ROOT)

    # TODO (template users): Add or remove compose test steps to match your
    #   docker-compose.yml services (e.g. database readiness checks, port
    #   mapping validation, multi-service integration tests).
    # Build first, then run individual checks via `docker compose run`.
    # This avoids `up -d` which would start the CLI and immediately exit.
    build_cmd = ["docker", "compose", "build"]
    if not args.verbose:
        build_cmd.append("--quiet")
    steps: list[tuple[str, list[str]]] = [
        ("Build image via docker compose", build_cmd),
        ("Validate compose config", ["docker", "compose", "config", "--quiet"]),
        (
            "Verify entrypoint (--help)",
            ["docker", "compose", "run", "--rm", "app", "--help"],
        ),
        (
            "Check non-root user",
            [
                "docker",
                "compose",
                "run",
                "--rm",
                "--entrypoint",
                "id",
                "app",
            ],
        ),
    ]

    if args.dry_run:
        print("Dry run — would execute:")
        for desc, cmd in steps:
            print(f"  [{desc}] {' '.join(cmd)}")
        if not args.keep:
            print("  [Clean up] docker compose down --rmi local --volumes")
        return 0

    step_timeout = args.timeout
    failed = False
    with Spinner("Running docker compose tests", log_interval=5) as spin:
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

    # Always clean up unless --keep
    if not args.keep:
        logger.info("Cleaning up containers and images")
        try:
            subprocess.run(  # nosec B603 B607
                ["docker", "compose", "down", "--rmi", "local", "--volumes"],
                check=False,
                timeout=60,
                capture_output=True,
            )
        except subprocess.TimeoutExpired:
            logger.warning("Cleanup timed out")

    if failed:
        logger.error("Docker compose test FAILED")
        return 1

    logger.info("Docker compose test PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
