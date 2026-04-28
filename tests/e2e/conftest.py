"""Fixtures for the Playwright smoke suite.

The smoke suite drives a *live* stack: a real uvicorn process serving the
FastAPI app, talking to the same Postgres database the API tests use. We
truncate ``feedback_item`` before each spec so the three flows stay
order-independent.

Run with::

    task test:e2e

The suite is gated behind the ``e2e`` marker so the default ``task test``
run does not pull in Playwright or the browser.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from sqlalchemy import text

from feedback_triage.database import engine


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_for_health(url: str, timeout_s: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return
        except (URLError, OSError) as exc:
            last_err = exc
        time.sleep(0.25)
    raise RuntimeError(f"App did not become healthy at {url}: {last_err!r}")


@pytest.fixture(scope="session")
def live_app_url() -> Iterator[str]:
    """Spin up uvicorn for the duration of the session."""
    port = _free_port()
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "feedback_triage.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    proc = subprocess.Popen(cmd)
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_health(f"{base_url}/health")
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


@pytest.fixture
def truncate_feedback() -> Iterator[None]:
    """Wipe ``feedback_item`` and reset its identity sequence per test."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE feedback_item RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, object]) -> dict[str, object]:
    """Lock the smoke suite to a single, predictable viewport."""
    return {**browser_context_args, "viewport": {"width": 1280, "height": 800}}
