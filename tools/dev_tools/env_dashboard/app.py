"""FastAPI app factory and Uvicorn entry point.

Security:
    - Binds to 127.0.0.1 only (local access).
    - Jinja2 autoescape=True (XSS prevention).
    - Read-only — no system mutations.

Performance:
    - Background cache warmup at startup so first page load is instant.
    - Collector runs in thread pool (non-blocking async event loop).

Port management:
    - On startup, kills any existing process holding the configured port.
    - Writes a PID file so stale processes can be cleaned up reliably.
    - Registers atexit + signal handlers to kill the full process tree
      (reloader + worker) when the server exits, preventing zombie sockets.

Usage::

    python -m tools.dev_tools.env_dashboard.app
    # or
    hatch run dashboard:serve
"""

from __future__ import annotations

import atexit
import contextlib
import logging
import os
import signal
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

_logger = logging.getLogger(__name__)

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[2]
_DEFAULT_PORT = 8000
_PID_FILE = _HERE / ".dashboard.pid"

# Add scripts/ to sys.path so _env_collectors can be imported
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Add repo root to sys.path so tools.dev_tools.env_dashboard can be imported
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ---------------------------------------------------------------------------
# Port & PID management — prevent zombie sockets on Windows
# ---------------------------------------------------------------------------


def _kill_pid(pid: int, *, tree: bool = False) -> bool:
    """Kill a single process by PID. Returns True if killed or already gone."""
    import contextlib

    if sys.platform == "win32":
        import subprocess  # nosec B404

        cmd = ["taskkill", "/F", "/PID", str(pid)]
        if tree:
            cmd.append("/T")
        with contextlib.suppress(subprocess.SubprocessError, OSError):
            subprocess.run(cmd, capture_output=True, timeout=5)  # nosec B603
            return True
    else:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.kill(pid, signal.SIGTERM)
            return True
    return False


def _is_python_process(pid: int) -> bool:
    """Check if a PID belongs to a Python process (Windows only)."""
    if sys.platform != "win32":
        return True  # Assume yes on non-Windows
    import subprocess  # nosec B404

    try:
        result = subprocess.run(  # nosec B603 B607
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return "python" in result.stdout.lower()
    except (subprocess.SubprocessError, OSError):
        return False


def _kill_port_holders(port: int) -> None:
    """Find and kill any process listening on *port* (Windows only).

    Uses ``netstat`` to find the owning PID, then ``taskkill /T`` to
    terminate the entire process tree.  Silently does nothing on
    non-Windows or if the port is free.
    """
    if sys.platform != "win32":
        return

    import subprocess  # nosec B404

    try:
        result = subprocess.run(  # nosec B603 B607
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.SubprocessError, OSError):
        return

    pids_to_kill: set[int] = set()
    for line in result.stdout.splitlines():
        # Look for LISTENING sockets on our port
        if f":{port} " not in line or "LISTENING" not in line:
            continue
        parts = line.split()
        if parts:
            try:
                pids_to_kill.add(int(parts[-1]))
            except (ValueError, IndexError):
                continue

    for pid in pids_to_kill:
        if pid == os.getpid() or pid == os.getppid():
            continue
        if not _is_python_process(pid):
            continue
        _kill_pid(pid, tree=True)
        print(f"  Killed stale process {pid} on port {port}")  # noqa: T201


def _read_pid_file() -> list[int]:
    """Read PIDs from the PID file. Returns empty list if missing/invalid."""
    if not _PID_FILE.is_file():
        return []
    try:
        text = _PID_FILE.read_text(encoding="utf-8").strip()
        return [int(p) for p in text.splitlines() if p.strip().isdigit()]
    except (OSError, ValueError):
        return []


def _write_pid_file() -> None:
    """Write current PID (and parent, if different) to the PID file."""
    pids = {os.getpid()}
    ppid = os.getppid()
    if ppid and ppid != os.getpid():
        pids.add(ppid)
    with contextlib.suppress(OSError):
        _PID_FILE.write_text(
            "\n".join(str(p) for p in sorted(pids)) + "\n",
            encoding="utf-8",
        )


def _remove_pid_file() -> None:
    """Delete the PID file on clean shutdown."""
    with contextlib.suppress(OSError):
        _PID_FILE.unlink(missing_ok=True)


def _cleanup_stale_processes(port: int) -> None:
    """Kill stale dashboard processes from a previous run.

    1. Kill PIDs recorded in the PID file (reliable — catches the exact
       processes from the last session).
    2. Kill any Python process still listening on *port* (fallback — catches
       zombie sockets where the PID file was lost).
    3. Retry up to 3 times — on Windows, taskkill /T can take a moment to
       propagate through the process tree, and sockets linger in TIME_WAIT.
    """
    import time

    my_pid = os.getpid()
    my_ppid = os.getppid()

    # Phase 1: PID file cleanup
    stale_pids = _read_pid_file()
    for pid in stale_pids:
        if pid in (my_pid, my_ppid):
            continue
        if not _is_python_process(pid):
            continue
        if _kill_pid(pid, tree=True):
            print(f"  Killed stale PID {pid} from previous session")  # noqa: T201
    _remove_pid_file()

    # Phase 2: Port-based cleanup with retry — catches zombies the PID file
    # missed and ensures they're actually dead before we try to bind.
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        _kill_port_holders(port)
        time.sleep(0.8)

        # Check if any Python process is still LISTENING on the port
        if not _port_has_listeners(port):
            break
        if attempt < max_attempts:
            _logger.warning(
                "Port %d still occupied, retrying (%d/%d)...",
                port,
                attempt,
                max_attempts,
            )
            time.sleep(1.0)
    else:
        _logger.warning(
            "Port %d may still be occupied after %d attempts",
            port,
            max_attempts,
        )


def _port_has_listeners(port: int) -> bool:
    """Return True if any process is LISTENING on *port* (Windows only)."""
    if sys.platform != "win32":
        return False
    import subprocess  # nosec B404

    try:
        result = subprocess.run(  # nosec B603 B607
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.SubprocessError, OSError):
        return False

    my_pid = os.getpid()
    my_ppid = os.getppid()
    for line in result.stdout.splitlines():
        if f":{port} " not in line or "LISTENING" not in line:
            continue
        parts = line.split()
        if parts:
            with contextlib.suppress(ValueError, IndexError):
                pid = int(parts[-1])
                if pid not in (my_pid, my_ppid, 0):
                    return True
    return False


def _register_exit_handlers() -> None:
    """Register atexit + signal handlers to kill the entire process tree.

    On Windows, Uvicorn's reload mode creates a parent (reloader) and
    child (worker) process.  When VS Code kills the terminal, only the
    shell dies — the reloader and worker become orphans whose TCP
    sockets linger as zombies.

    This function ensures both processes are killed on any exit path:
    SIGTERM, SIGINT, or normal Python exit.
    """
    _write_pid_file()
    atexit.register(_remove_pid_file)

    def _exit_handler(signum: int, _frame: Any) -> None:
        """Kill the sibling process (parent or child) then exit."""
        ppid = os.getppid()
        pid = os.getpid()
        _remove_pid_file()

        # Kill the other half of the reloader/worker pair
        if ppid and ppid != pid and ppid != 1:
            _kill_pid(ppid)

        # Re-raise as SystemExit so atexit handlers still run
        raise SystemExit(128 + signum)

    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(OSError, ValueError):
            signal.signal(sig, _exit_handler)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[Any]:
    """Warm the collector cache on startup so the first page load is fast."""
    import asyncio

    from tools.dev_tools.env_dashboard.collector import warmup_cache

    # Background warmup — don't delay server readiness
    task = asyncio.create_task(warmup_cache())
    yield
    task.cancel()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Environment Dashboard",
        description="Local-only environment inspection dashboard",
        docs_url=None,  # Disable Swagger UI for local tool
        redoc_url=None,
        lifespan=_lifespan,
    )

    # Mount static files (no-cache in dev so CSS changes appear immediately)
    static_dir = _HERE / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.middleware("http")
    async def no_cache_static(request: Any, call_next: Any) -> Any:
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response

    # Set up Jinja2 templates with autoescape (non-negotiable)
    templates = Jinja2Templates(directory=str(_HERE / "templates"))
    templates.env.autoescape = True

    # Cache-bust ID — unique per server restart so browsers fetch fresh CSS/JS
    import time

    templates.env.globals["cache_bust"] = str(int(time.time()))

    # Store templates on app state for route handlers
    app.state.templates = templates

    # Register routes
    from tools.dev_tools.env_dashboard.api import router as api_router
    from tools.dev_tools.env_dashboard.routes import router as html_router

    app.include_router(html_router)
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()


def main() -> None:
    """Start the dashboard server."""
    import uvicorn

    port = _DEFAULT_PORT

    # Kill any stale processes from a previous session before binding
    _cleanup_stale_processes(port)
    _register_exit_handlers()

    url = f"http://127.0.0.1:{port}"
    _print_startup_banner(url, port)

    uvicorn.run(
        "tools.dev_tools.env_dashboard.app:app",
        host="127.0.0.1",
        port=port,
        reload=True,
        reload_dirs=[str(_HERE)],
    )


def _print_startup_banner(url: str, port: int) -> None:
    """Print a helpful startup banner with server info and quick links."""
    import platform
    import time

    now = time.strftime("%H:%M:%S")
    py = platform.python_version()
    os_name = platform.system()
    w = 52  # interior width
    separator = "─" * w

    # Count available collector sections
    section_count = "?"
    try:
        from _env_collectors import gather_env_info

        data = gather_env_info()
        sections = data.get("sections", {})
        section_count = str(len(sections))
    except Exception:  # nosec B110 — best-effort count; default "?" is fine
        section_count = "?"

    def row(text: str = "") -> str:
        """Pad *text* to exactly *w* visible columns inside │…│ borders."""
        # Emoji 🖥 occupies 2 terminal columns but len() counts 1 char.
        extra = text.count("🖥")
        return f"  │{text:<{w - extra}}│"

    def center(text: str) -> str:
        extra = text.count("🖥")
        return f"  │{text:^{w - extra}}│"

    pid = os.getpid()
    dash_url = f"{url}/"
    api_url = f"{url}/api/report"
    summary_url = f"{url}/api/summary"
    export_url = f"{url}/export.html"

    lines = [
        f"  ╭{separator}╮",
        center(""),
        center("🖥  Environment Dashboard"),
        center(""),
        f"  ├{separator}┤",
        row(f"  Server:     {url}"),
        row(f"  Port:       {port}"),
        row("  Host:       127.0.0.1 (local only)"),
        row("  Reload:     enabled"),
        row(f"  Started:    {now}"),
        row(f"  PID:        {pid}"),
        row(f"  Python:     {py}"),
        row(f"  Platform:   {os_name}"),
        row(f"  Sections:   {section_count}"),
        f"  ├{separator}┤",
        row(),
        row("  Quick links:"),
        row(f"    Dashboard:    {dash_url}"),
        row(f"    API JSON:     {api_url}"),
        row(f"    Summary:      {summary_url}"),
        row(f"    HTML export:  {export_url}"),
        row(),
        f"  ├{separator}┤",
        row(),
        row("  Routes:"),
        row("    GET /              Dashboard page"),
        row("    GET /api/report    Full JSON report"),
        row("    GET /api/summary   Report summary"),
        row("    GET /export.html   Static HTML export"),
        row("    GET /section/...   htmx partials"),
        row(),
        row("  Keyboard shortcuts:"),
        row("    Ctrl+C     Stop the server"),
        row(),
        f"  ╰{separator}╯",
    ]
    print("\n" + "\n".join(lines) + "\n")  # noqa: T201


if __name__ == "__main__":
    main()
