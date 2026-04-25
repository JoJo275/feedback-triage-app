"""System info collector — OS, arch, hostname, shell, cwd, privilege, locale."""

from __future__ import annotations

import os
import platform
import re
import sys
from pathlib import Path
from typing import Any

from _env_collectors._base import BaseCollector

# Avoid circular import at module level
_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


def _linux_distro_info() -> dict[str, str]:
    """Read Linux distribution info from /etc/os-release."""
    info: dict[str, str] = {}
    os_release = Path("/etc/os-release")
    if not os_release.is_file():
        return info
    try:
        content = os_release.read_text(encoding="utf-8", errors="replace")
        for key in ("NAME", "VERSION_ID", "PRETTY_NAME", "ID", "ID_LIKE"):
            match = re.search(rf'^{key}="?([^"\n]+)"?$', content, re.MULTILINE)
            if match:
                info[key.lower()] = match.group(1).strip()
    except OSError:
        pass
    return info


def _linux_uptime() -> str | None:
    """Read system uptime on Linux from /proc/uptime."""
    uptime_file = Path("/proc/uptime")
    if not uptime_file.is_file():
        return None
    try:
        raw = uptime_file.read_text(encoding="utf-8").split()[0]
        seconds = int(float(raw))
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        return " ".join(parts)
    except (OSError, ValueError, IndexError):
        return None


class SystemCollector(BaseCollector):
    """Collect OS, architecture, hostname, shell, cwd, privilege, locale."""

    name = "system"
    timeout = 5.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().MINIMAL

    def collect(self) -> dict[str, Any]:
        env = os.environ
        shell = env.get("SHELL") or env.get("COMSPEC") or "unknown"

        is_root = False
        if sys.platform != "win32":
            is_root = os.getuid() == 0  # type: ignore[attr-defined]
        else:
            import ctypes

            is_root = bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]

        import locale

        try:
            current_locale = locale.getlocale()
            locale_str = (
                f"{current_locale[0]}.{current_locale[1]}"
                if current_locale[0]
                else "unknown"
            )
        except Exception:
            locale_str = "unknown"

        result: dict[str, Any] = {
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "kernel": platform.platform(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "username": env.get("USER") or env.get("USERNAME") or "unknown",
            "shell": shell,
            "cwd": str(Path.cwd()),
            "privilege": "root" if is_root else "user",
            "locale": locale_str,
            "cpu_count": os.cpu_count(),
            "encoding": sys.getdefaultencoding(),
            "filesystem_encoding": sys.getfilesystemencoding(),
        }

        # Linux-specific fields
        if sys.platform == "linux":
            distro = _linux_distro_info()
            if distro.get("pretty_name"):
                result["distro"] = distro["pretty_name"]
            elif distro.get("name"):
                ver = distro.get("version_id", "")
                result["distro"] = f"{distro['name']} {ver}".strip()
            if distro.get("id_like"):
                result["distro_family"] = distro["id_like"]

            uptime = _linux_uptime()
            if uptime:
                result["uptime"] = uptime

            # Kernel release (more specific than platform.release() in some cases)
            uname = platform.uname()
            result["kernel_release"] = uname.release
            result["kernel_version"] = uname.version

        return result
