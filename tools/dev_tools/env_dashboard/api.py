"""JSON API route handlers."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
import shutil
import signal
import subprocess  # nosec B404
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response, StreamingResponse

from tools.dev_tools.env_dashboard.collector import (
    get_report_async,
    invalidate_cache,
)
from tools.dev_tools.env_dashboard.redact import parse_redact_param

router = APIRouter()
_background_tasks: set[asyncio.Task[Any]] = set()


@router.get("/summary")
async def api_summary(redact: str | None = Query(default=None)) -> JSONResponse:
    """Top summary bar data only."""
    redact_level = parse_redact_param(redact)
    report = await get_report_async(redact_level=redact_level)
    return JSONResponse(report.get("summary", {}))


@router.get("/report")
async def api_report(
    redact: str | None = Query(default=None),
    tier: str = Query(default="standard"),
) -> JSONResponse:
    """Full scan report (all sections, current tier)."""
    redact_level = parse_redact_param(redact)
    tier_enum = _parse_tier(tier)
    report = await get_report_async(tier=tier_enum, redact_level=redact_level)
    return JSONResponse(report)


@router.get("/warnings")
async def api_warnings(redact: str | None = Query(default=None)) -> JSONResponse:
    """Warnings panel data only."""
    redact_level = parse_redact_param(redact)
    report = await get_report_async(redact_level=redact_level)
    return JSONResponse(report.get("warnings", []))


@router.get("/sections/{name}")
async def api_section(
    name: str,
    redact: str | None = Query(default=None),
) -> JSONResponse:
    """Single section by name."""
    redact_level = parse_redact_param(redact)
    report = await get_report_async(redact_level=redact_level)
    sections = report.get("sections", {})
    if name not in sections:
        return JSONResponse({"error": f"Section '{name}' not found"}, status_code=404)
    return JSONResponse(sections[name])


@router.post("/scan")
async def api_scan(
    redact: str | None = Query(default=None),
    tier: str = Query(default="standard"),
) -> JSONResponse:
    """Trigger a fresh scan in the background and return immediately."""
    invalidate_cache()
    redact_level = parse_redact_param(redact)
    tier_enum = _parse_tier(tier)
    # Run scan in background — caller doesn't have to wait
    task = asyncio.create_task(
        get_report_async(tier=tier_enum, redact_level=redact_level, force=True)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return JSONResponse({"status": "started"})


@router.get("/export.json")
async def api_export_json(
    redact: str | None = Query(default=None),
    tier: str = Query(default="standard"),
) -> Response:
    """Full scan as downloadable JSON (PII-redacted by default)."""
    redact_level = parse_redact_param(redact, export=True)
    tier_enum = _parse_tier(tier)
    report = await get_report_async(tier=tier_enum, redact_level=redact_level)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"env-report-{timestamp}.json"

    return Response(
        content=json.dumps(report, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _parse_tier(value: str) -> object:
    """Parse tier string to Tier enum."""
    from _env_collectors import Tier

    value_lower = value.lower().strip()
    for t in Tier:
        if t.value == value_lower:
            return t
    return Tier.STANDARD


# --------------------------------------------------------------------------
# Allowlist for pip operations (security: prevent command injection)
# --------------------------------------------------------------------------
_PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")


def _validate_package_name(name: str) -> bool:
    """Check that a package name is safe (PEP 508 subset)."""
    return bool(_PACKAGE_NAME_RE.match(name)) and len(name) <= 200


# --------------------------------------------------------------------------
# Python executable allowlist — breaks CodeQL taint chain by returning only
# values from a server-side registry, never user-derived strings.
# --------------------------------------------------------------------------


def _normcase(s: str) -> str:
    """Pure-string equivalent of ``os.path.normcase``.

    On Windows: lowercases and normalises separators.
    On POSIX: identity.
    Uses only ``str`` methods so CodeQL does not treat the result as a
    path expression derived from user input.
    """
    if sys.platform == "win32":
        return s.replace("/", "\\").lower()
    return s


_allowed_python_exes: dict[str, str] = {}


def register_python_executable(exe_path: str) -> None:
    """Register a verified Python executable in the server-side allowlist.

    Called at startup and whenever collectors discover new environments.
    The *exe_path* is resolved and validated once here; API endpoints only
    return paths from this map, so user input never flows into
    ``subprocess`` or ``Path`` operations.
    """
    try:
        p = Path(exe_path).resolve(strict=True)
        if p.is_file() and p.name.lower().startswith("python"):
            canonical = str(p)
            # Index under the resolved canonical form.
            _allowed_python_exes[_normcase(canonical)] = canonical
            # Also index under the raw input (normcase'd) so that lookups
            # using the exact same string the collector returned will match
            # without any Path construction on the user-supplied value.
            _allowed_python_exes[_normcase(exe_path)] = canonical
    except (OSError, ValueError):
        pass


def _init_python_allowlist() -> None:
    """Seed the allowlist with the current interpreter and PATH entries."""
    register_python_executable(sys.executable)
    for name in ("python3", "python", "python3.11", "python3.12", "python3.13"):
        found = shutil.which(name)
        if found:
            register_python_executable(found)


_init_python_allowlist()


def _validate_python_exe(python_exe: str) -> str | None:
    """Validate that *python_exe* matches a known-good Python executable.

    Only ``_normcase`` (pure ``str`` methods — no ``os.path``, no ``Path``,
    no filesystem access) is performed on the user value, so CodeQL does
    not flag a path-injection.  The returned value comes from the
    pre-verified allowlist, breaking the taint chain.
    """
    normalised = _normcase(python_exe)
    return _allowed_python_exes.get(normalised)


def _sync_allowlist_from_report(report: dict[str, Any]) -> None:
    """Register Python executables discovered by the collectors.

    Extracts ``python_exe`` / ``executable`` fields from the
    ``pip_environments`` section so that user-selected environments
    pass ``_validate_python_exe`` without the API ever touching
    user-controlled paths directly.
    """
    pip_section = report.get("sections", {}).get("pip_environments", {})
    for env in pip_section.get("environments", []):
        exe = env.get("python_exe") or env.get("executable")
        if exe:
            register_python_executable(exe)
    for inst in pip_section.get("python_installs", []):
        exe = inst.get("python_exe") or inst.get("executable")
        if exe:
            register_python_executable(exe)


async def _ensure_allowlist_synced() -> None:
    """Ensure the Python executable allowlist includes collector discoveries."""
    from tools.dev_tools.env_dashboard.collector import get_report_async

    report = await get_report_async()
    _sync_allowlist_from_report(report)


async def _stream_pip_command(
    cmd: list[str],
) -> Any:
    """Run a pip command and stream output line by line."""

    async def _generate() -> Any:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        if proc.stdout:
            async for line in proc.stdout:
                text = line.decode("utf-8", errors="replace")
                yield f"data: {json.dumps({'line': text})}\n\n"
        returncode = await proc.wait()
        yield f"data: {json.dumps({'done': True, 'returncode': returncode})}\n\n"

    return _generate()


@router.post("/pip/update")
async def api_pip_update(
    package: str = Query(...),
    python_exe: str = Query(default=""),
) -> StreamingResponse:
    """Update a pip package via streaming SSE output.

    Security: validates package name + python exe path. Only local access.
    """
    if not _validate_package_name(package):
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'Invalid package name'})}\n\n"]),
            media_type="text/event-stream",
        )

    await _ensure_allowlist_synced()
    resolved_exe = _validate_python_exe(python_exe or sys.executable)
    if resolved_exe is None:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'Invalid Python executable'})}\n\n"]),
            media_type="text/event-stream",
        )

    cmd = [resolved_exe, "-m", "pip", "install", "--upgrade", package]
    return StreamingResponse(
        await _stream_pip_command(cmd),
        media_type="text/event-stream",
    )


@router.post("/pip/uninstall")
async def api_pip_uninstall(
    package: str = Query(...),
    python_exe: str = Query(default=""),
) -> StreamingResponse:
    """Uninstall a pip package via streaming SSE output.

    Security: validates package name + python exe path. Only local access.
    """
    if not _validate_package_name(package):
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'Invalid package name'})}\n\n"]),
            media_type="text/event-stream",
        )

    await _ensure_allowlist_synced()
    resolved_exe = _validate_python_exe(python_exe or sys.executable)
    if resolved_exe is None:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'Invalid Python executable'})}\n\n"]),
            media_type="text/event-stream",
        )

    cmd = [resolved_exe, "-m", "pip", "uninstall", "-y", package]
    return StreamingResponse(
        await _stream_pip_command(cmd),
        media_type="text/event-stream",
    )


@router.post("/pip/install")
async def api_pip_install(
    package: str = Query(...),
    python_exe: str = Query(default=""),
) -> StreamingResponse:
    """Install a pip package via streaming SSE output.

    Used by the "Move to" feature to install a package into a target
    environment before uninstalling from the source.

    Security: validates package name + python exe path. Only local access.
    """
    if not _validate_package_name(package):
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'Invalid package name'})}\n\n"]),
            media_type="text/event-stream",
        )

    await _ensure_allowlist_synced()
    resolved_exe = _validate_python_exe(python_exe or sys.executable)
    if resolved_exe is None:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'Invalid Python executable'})}\n\n"]),
            media_type="text/event-stream",
        )

    cmd = [resolved_exe, "-m", "pip", "install", package]
    return StreamingResponse(
        await _stream_pip_command(cmd),
        media_type="text/event-stream",
    )


@router.post("/pip/check-updates")
async def api_pip_check_updates(
    python_exe: str = Query(default=""),
) -> JSONResponse:
    """Check all outdated packages for a given Python environment."""
    await _ensure_allowlist_synced()
    resolved_exe = _validate_python_exe(python_exe or sys.executable)
    if resolved_exe is None:
        return JSONResponse({"error": "Invalid Python executable"}, status_code=400)

    try:
        result = subprocess.run(  # nosec B603
            [resolved_exe, "-m", "pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            timeout=60.0,
        )
        if result.returncode == 0 and result.stdout.strip():
            packages = json.loads(result.stdout)
            return JSONResponse({"outdated": packages})
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return JSONResponse(
            {"error": "Failed to check for package updates"}, status_code=500
        )

    return JSONResponse({"outdated": []})


# --------------------------------------------------------------------------
# PATH management (Windows only — modifies User PATH in registry)
# --------------------------------------------------------------------------


def _validate_path_entry(entry: str) -> bool:
    """Check that a PATH entry looks like a directory path, not an injection."""
    if not entry or len(entry) > 1024:
        return False
    # Block obvious shell metacharacters
    forbidden = set('";<>|&`$')
    return not any(c in forbidden for c in entry)


@router.post("/path/remove")
async def api_path_remove(
    path_entry: str = Query(...),
) -> JSONResponse:
    """Remove a directory from the User PATH (Windows registry).

    Security: validates the path string, only modifies HKCU (user-level),
    and only listens on 127.0.0.1.
    """
    import platform

    if platform.system() != "Windows":
        return JSONResponse(
            {"error": "PATH removal only supported on Windows"},
            status_code=501,
        )

    if not _validate_path_entry(path_entry):
        return JSONResponse(
            {"error": "Invalid path entry"},
            status_code=400,
        )

    try:
        import winreg  # nosec B404 — Windows registry access

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Environment",
            0,
            winreg.KEY_READ | winreg.KEY_WRITE,
        )
        try:
            current_path, reg_type = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError:
            winreg.CloseKey(key)
            return JSONResponse(
                {"error": "No User PATH variable found"},
                status_code=404,
            )

        entries = [e for e in current_path.split(";") if e.strip()]
        target = path_entry.strip().lower().rstrip("\\")
        new_entries = [e for e in entries if e.strip().lower().rstrip("\\") != target]

        if len(new_entries) == len(entries):
            winreg.CloseKey(key)
            return JSONResponse(
                {"error": "Entry not found in User PATH"},
                status_code=404,
            )

        new_path = ";".join(new_entries)
        winreg.SetValueEx(key, "PATH", 0, reg_type, new_path)
        winreg.CloseKey(key)

        # Update current process PATH so the next scan reflects the change
        process_path = os.environ.get("PATH", "")
        process_entries = process_path.split(";")
        os.environ["PATH"] = ";".join(
            e for e in process_entries if e.strip().lower().rstrip("\\") != target
        )

        # Invalidate cache so next scan picks up the change
        invalidate_cache()

        return JSONResponse(
            {
                "status": "ok",
                "removed": path_entry,
                "remaining": len(new_entries),
            }
        )
    except OSError:
        return JSONResponse({"error": "Failed to modify PATH"}, status_code=500)


@router.post("/shutdown")
async def api_shutdown() -> JSONResponse:
    """Gracefully shut down the dashboard server.

    Security: only listens on 127.0.0.1 so only local users can trigger this.

    On Windows with Uvicorn's ``--reload``, SIGINT only kills the worker
    process; the reloader respawns it.  ``CTRL_C_EVENT`` signals the
    entire console process group (reloader + worker), matching Ctrl+C.
    """
    import asyncio
    import sys

    async def _delayed_shutdown() -> None:
        """Small delay so the JSON response reaches the client first."""
        await asyncio.sleep(0.3)
        if sys.platform == "win32":
            # Forcefully terminate the reloader parent process, then self.
            # CTRL_C_EVENT alone is caught by Uvicorn's reloader which
            # just restarts the worker instead of exiting.
            parent_pid = os.getppid()
            with contextlib.suppress(OSError):
                os.kill(parent_pid, signal.SIGTERM)
            os.kill(os.getpid(), signal.SIGTERM)
        else:
            # Kill parent (reloader) then self.
            os.kill(os.getppid(), signal.SIGINT)
            os.kill(os.getpid(), signal.SIGINT)

    asyncio.get_running_loop().create_task(_delayed_shutdown())
    return JSONResponse({"status": "shutting_down"})
