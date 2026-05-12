#!/usr/bin/env python3
"""Run FastAPI dev server + CSS watcher with reliable Ctrl+C teardown.

This script is used by ``task dev:all``. It starts two long-running
processes and supervises them as a unit:

1. ``python -m fastapi dev src/feedback_triage/main.py``
2. ``python scripts/build_css.py --watch``

On Windows, each child is started in its own process group so Ctrl+C
can be forwarded as ``CTRL_BREAK_EVENT`` and the entire tree is
terminated (reloader + worker), avoiding orphaned ``watchfiles`` logs.
An intentional Ctrl+C exits with status 0 so ``task dev:all`` closes
without a failed-task banner.
"""

from __future__ import annotations

import argparse
import contextlib
import logging
import os
import signal
import subprocess  # nosec B404 - argv lists only, no shell.
import sys
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

SCRIPT_VERSION = "1.1.0"

_IS_WINDOWS = os.name == "nt"
_INTERRUPT_WAIT_SECONDS = 3.0
_TERMINATE_WAIT_SECONDS = 2.0
_FAST_INTERRUPT_WAIT_SECONDS = 0.8
_FAST_TERMINATE_WAIT_SECONDS = 0.6
_WIN_CTRL_C_EXIT_CODE = 3221225786


@dataclass(slots=True)
class ManagedProcess:
    """A child process tracked by the supervisor."""

    name: str
    popen: subprocess.Popen[bytes]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dev_all_supervisor",
        description="Run API server + CSS watcher with coordinated shutdown.",
        epilog=(
            "Examples:\n"
            "  uv run python tools/dev_tools/dev_all_supervisor.py\n"
            "  uv run python tools/dev_tools/dev_all_supervisor.py --smoke\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run local self-checks and exit.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="Decrease log verbosity.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity.",
    )
    return parser


def _smoke() -> int:
    required = [
        Path("src/feedback_triage/main.py"),
        Path("scripts/build_css.py"),
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        logger.error("Missing required files: %s", ", ".join(missing))
        return 2
    print(f"dev_all_supervisor {SCRIPT_VERSION}: smoke ok")  # noqa: T201
    return 0


def _spawn(name: str, cmd: list[str]) -> ManagedProcess:
    logger.info("Starting %s: %s", name, " ".join(cmd))
    kwargs: dict[str, int | bool] = {}
    if _IS_WINDOWS:
        kwargs["creationflags"] = int(subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        kwargs["start_new_session"] = True
    popen = subprocess.Popen(cmd, **kwargs)  # nosec B603 - argv list only.
    return ManagedProcess(name=name, popen=popen)


def _send_interrupt(proc: ManagedProcess) -> None:
    if proc.popen.poll() is not None:
        return
    if _IS_WINDOWS:
        # Requires CREATE_NEW_PROCESS_GROUP on spawn.
        with contextlib.suppress(OSError, ValueError):
            proc.popen.send_signal(signal.CTRL_BREAK_EVENT)
        return
    with contextlib.suppress(ProcessLookupError, OSError, ValueError):
        os.killpg(proc.popen.pid, signal.SIGINT)


def _send_terminate(proc: ManagedProcess) -> None:
    if proc.popen.poll() is not None:
        return
    if _IS_WINDOWS:
        with contextlib.suppress(OSError):
            proc.popen.terminate()
        return
    with contextlib.suppress(ProcessLookupError, OSError, ValueError):
        os.killpg(proc.popen.pid, signal.SIGTERM)


def _send_kill(proc: ManagedProcess) -> None:
    if proc.popen.poll() is not None:
        return
    if _IS_WINDOWS:
        with contextlib.suppress(OSError):
            proc.popen.kill()
        return
    with contextlib.suppress(ProcessLookupError, OSError, ValueError):
        os.killpg(proc.popen.pid, signal.SIGKILL)


def _wait_for_exit(processes: list[ManagedProcess], timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(proc.popen.poll() is not None for proc in processes):
            return True
        time.sleep(0.1)
    return all(proc.popen.poll() is not None for proc in processes)


def _shutdown(processes: list[ManagedProcess], *, fast: bool = False) -> None:
    interrupt_wait = (
        _FAST_INTERRUPT_WAIT_SECONDS if fast else _INTERRUPT_WAIT_SECONDS
    )
    terminate_wait = (
        _FAST_TERMINATE_WAIT_SECONDS if fast else _TERMINATE_WAIT_SECONDS
    )

    for proc in processes:
        _send_interrupt(proc)
    if _wait_for_exit(processes, interrupt_wait):
        return

    for proc in processes:
        _send_terminate(proc)
    if _wait_for_exit(processes, terminate_wait):
        return

    for proc in processes:
        _send_kill(proc)
    _wait_for_exit(processes, 1.0)


def _is_interrupt_exit(rc: int) -> bool:
    return rc in {130, -int(signal.SIGINT), _WIN_CTRL_C_EXIT_CODE}


def main(argv: list[str] | None = None) -> int:
    """Run the supervisor entrypoint and return a shell-friendly exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    level = logging.INFO - (10 * args.verbose) + (10 * args.quiet)
    logging.basicConfig(level=max(level, logging.DEBUG), format="%(message)s")

    if args.smoke:
        return _smoke()

    signal_seen: int | None = None
    def _signal_handler(signum: int, _frame: object) -> None:
        nonlocal signal_seen
        signal_seen = signum

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(OSError, ValueError):
            signal.signal(sig, _signal_handler)

    commands = [
        [sys.executable, "-m", "fastapi", "dev", "src/feedback_triage/main.py"],
        [sys.executable, "scripts/build_css.py", "--watch"],
    ]
    processes = [
        _spawn("api", commands[0]),
        _spawn("css", commands[1]),
    ]

    exit_code = 0
    try:
        while signal_seen is None:
            for proc in processes:
                rc = proc.popen.poll()
                if rc is None:
                    continue
                other_name = next(
                    p.name for p in processes if p is not proc
                )
                logger.warning(
                    "%s exited with code %s; stopping %s.",
                    proc.name,
                    rc,
                    other_name,
                )
                if _is_interrupt_exit(rc):
                    exit_code = 0
                    signal_seen = signal.SIGINT
                else:
                    exit_code = rc if rc != 0 else 1
                    signal_seen = signal.SIGTERM
                break
            time.sleep(0.2)
    finally:
        # User-triggered Ctrl+C should return control to the shell quickly.
        _shutdown(processes, fast=signal_seen == signal.SIGINT)

    if signal_seen == signal.SIGINT:
        # ``task dev:all`` should stop cleanly on an intentional Ctrl+C
        # instead of printing a failed-task banner.
        return 0
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
