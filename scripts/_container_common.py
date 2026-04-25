"""Shared helpers for container test scripts.

Used by ``test_containerfile.py`` and ``test_docker_compose.py``.
"""

from __future__ import annotations

import logging
import re
import subprocess  # nosec B404

logger = logging.getLogger(__name__)


def run(
    args: list[str],
    *,
    check: bool = True,
    timeout: int = 300,
    verbose: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the CompletedProcess."""
    logger.info("Running: %s", " ".join(args))
    result = subprocess.run(  # nosec B603
        args,
        check=check,
        timeout=timeout,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        log_stdout = logger.info if verbose else logger.debug
        for line in result.stdout.splitlines():
            log_stdout("  %s", line)
    if verbose and result.stderr:
        for line in result.stderr.splitlines():
            logger.debug("  stderr: %s", line)
    if result.returncode != 0 and result.stderr:
        for line in result.stderr.splitlines():
            logger.error("  %s", line)
    return result


def check_docker_available() -> bool:
    """Verify docker CLI is available and the daemon is running."""
    try:
        result = subprocess.run(  # nosec B603 B607
            ["docker", "info"],
            check=False,
            timeout=15,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(
                "Docker daemon not running or not accessible. "
                "Start Docker Desktop or the docker service first."
            )
            return False
        return True
    except FileNotFoundError:
        logger.error("docker CLI not found on PATH")
        return False
    except subprocess.TimeoutExpired:
        logger.error("docker info timed out — daemon may be unresponsive")
        return False


def check_non_root(output: str) -> bool:
    """Verify the container is not running as root (uid=0)."""
    # `id` output looks like: uid=1000(app) gid=1000(app) groups=1000(app)
    uid_match = re.search(r"uid=(\d+)", output)
    if not uid_match:
        logger.error("Could not parse uid from `id` output: %s", output.strip())
        return False
    if uid_match.group(1) == "0":
        logger.error("Container is running as root (uid=0)")
        return False
    logger.info("  Non-root verified: %s", output.strip().split()[0])
    return True
