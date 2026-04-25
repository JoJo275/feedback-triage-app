"""Runtimes collector — Python versions, installations, compilers."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any

from _env_collectors._base import BaseCollector

_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


class RuntimesCollector(BaseCollector):
    """Collect Python runtime info and discover installations."""

    name = "runtimes"
    timeout = 15.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().MINIMAL

    def collect(self) -> dict[str, Any]:
        return {
            "python": self._python_info(),
            "installations": self._find_installations(),
            "compiler": platform.python_compiler(),
        }

    @staticmethod
    def _python_info() -> dict[str, Any]:
        return {
            "version": platform.python_version(),
            "version_tuple": list(sys.version_info[:3]),
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler(),
            "executable": sys.executable,
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
            "in_venv": sys.prefix != sys.base_prefix,
            "platform": platform.platform(),
            "architecture": platform.machine(),
        }

    @staticmethod
    def _find_installations() -> list[dict[str, str]]:
        pythons: list[dict[str, str]] = []
        seen_paths: set[str] = set()

        candidates = [
            "python3",
            "python",
            "python3.11",
            "python3.12",
            "python3.13",
            "python3.14",
        ]
        if sys.platform == "win32":
            candidates.extend(["py", "python.exe"])

        for name in candidates:
            path = shutil.which(name)
            if not path:
                continue
            resolved = str(Path(path).resolve())
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)

            version = ""
            implementation = ""
            try:
                result = subprocess.run(  # nosec B603
                    [
                        path,
                        "-c",
                        "import sys, platform; "
                        "print(platform.python_version()); "
                        "print(platform.python_implementation())",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().splitlines()
                    version = lines[0] if lines else ""
                    implementation = lines[1] if len(lines) > 1 else ""
            except (subprocess.TimeoutExpired, OSError):
                pass

            pythons.append(
                {
                    "name": name,
                    "path": resolved,
                    "version": version,
                    "implementation": implementation,
                }
            )

        # Windows py launcher
        if sys.platform == "win32":
            pythons.extend(RuntimesCollector._py_launcher_installs(seen_paths))

        return pythons

    @staticmethod
    def _py_launcher_installs(seen_paths: set[str]) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        py_cmd = shutil.which("py")
        if not py_cmd:
            return results
        try:
            result = subprocess.run(  # nosec B603
                [py_cmd, "--list-paths"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return results
            for line in result.stdout.strip().splitlines():
                m = re.match(r"\s*-V?:?(\S+)\s+(.+)", line)
                if not m:
                    m = re.match(r"\s*-(\S+)\s+(.+?)(?:\s+\*)?$", line)
                if not m:
                    continue
                py_path = m.group(2).strip().rstrip(" *")
                resolved = str(Path(py_path).resolve())
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)
                ver = ""
                impl = ""
                try:
                    r2 = subprocess.run(  # nosec B603
                        [
                            py_path,
                            "-c",
                            "import platform; "
                            "print(platform.python_version()); "
                            "print(platform.python_implementation())",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if r2.returncode == 0:
                        ls = r2.stdout.strip().splitlines()
                        ver = ls[0] if ls else ""
                        impl = ls[1] if len(ls) > 1 else ""
                except (subprocess.TimeoutExpired, OSError):
                    pass
                results.append(
                    {
                        "name": f"py {m.group(1)}",
                        "path": resolved,
                        "version": ver,
                        "implementation": impl,
                    }
                )
        except (subprocess.TimeoutExpired, OSError):
            pass
        return results
