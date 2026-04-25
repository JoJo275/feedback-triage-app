"""Project commands collector — task runners, entry points, scripts, and commands.

Discovers:
- Taskfile.yml tasks
- Makefile targets
- Hatch scripts/commands
- pyproject.toml scripts and entry points
- npm scripts (if package.json exists)
- Custom commands from .vscode/tasks.json
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess  # nosec B404
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


def _run_cmd(
    cmd: list[str], *, timeout: float = 15.0
) -> subprocess.CompletedProcess[str]:
    """Run a command safely."""
    return subprocess.run(  # nosec B603
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _parse_taskfile(repo_root: Path) -> list[dict[str, str]]:
    """Parse Taskfile.yml to extract task names and descriptions."""
    taskfile = repo_root / "Taskfile.yml"
    if not taskfile.is_file():
        return []

    tasks: list[dict[str, str]] = []

    # Try running `task --list` for accurate task list
    task_exe = shutil.which("task")
    if task_exe:
        try:
            result = _run_cmd([task_exe, "--list"], timeout=10.0)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    # task --list outputs: "* taskname: description"
                    m = re.match(r"\*\s+(\S+):\s*(.*)", line.strip())
                    if m:
                        tasks.append(
                            {
                                "name": m.group(1),
                                "description": m.group(2).strip(),
                                "runner": "Taskfile",
                                "command": f"task {m.group(1)}",
                            }
                        )
                return tasks
        except (OSError, subprocess.TimeoutExpired):
            pass

    # Fallback: parse YAML manually (simple regex-based, no yaml dependency)
    try:
        content = taskfile.read_text(encoding="utf-8")
        # Match top-level task definitions
        in_tasks = False
        for line in content.splitlines():
            if re.match(r"^tasks:", line):
                in_tasks = True
                continue
            if in_tasks:
                m = re.match(r"^  (\w[\w-]*):", line)
                if m:
                    task_name = m.group(1)
                    tasks.append(
                        {
                            "name": task_name,
                            "description": "",
                            "runner": "Taskfile",
                            "command": f"task {task_name}",
                        }
                    )
    except OSError:
        pass

    return tasks


def _parse_makefile(repo_root: Path) -> list[dict[str, str]]:
    """Parse Makefile to extract targets."""
    makefile = repo_root / "Makefile"
    if not makefile.is_file():
        return []

    targets: list[dict[str, str]] = []
    try:
        content = makefile.read_text(encoding="utf-8")
        for line in content.splitlines():
            m = re.match(r"^([a-zA-Z_][\w-]*):", line)
            if m:
                target = m.group(1)
                targets.append(
                    {
                        "name": target,
                        "description": "",
                        "runner": "Makefile",
                        "command": f"make {target}",
                    }
                )
    except OSError:
        pass
    return targets


def _parse_hatch_scripts(repo_root: Path) -> list[dict[str, str]]:
    """Parse Hatch scripts from pyproject.toml."""
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return []

    scripts: list[dict[str, str]] = []
    try:
        import tomllib

        content = pyproject.read_bytes()
        data = tomllib.loads(content.decode("utf-8"))

        # Hatch env scripts: [tool.hatch.envs.{env}.scripts]
        hatch_envs = data.get("tool", {}).get("hatch", {}).get("envs", {})
        for env_name, env_conf in hatch_envs.items():
            if not isinstance(env_conf, dict):
                continue
            env_scripts = env_conf.get("scripts", {})
            for script_name, cmd in env_scripts.items():
                if isinstance(cmd, str):
                    cmd_str = cmd
                elif isinstance(cmd, list):
                    cmd_str = " && ".join(cmd) if cmd else ""
                else:
                    cmd_str = str(cmd)
                scripts.append(
                    {
                        "name": script_name,
                        "description": cmd_str,
                        "runner": f"Hatch ({env_name})",
                        "command": f"hatch run {env_name}:{script_name}"
                        if env_name != "default"
                        else f"hatch run {script_name}",
                    }
                )
    except (OSError, ImportError, ValueError, KeyError):
        pass

    return scripts


def _parse_pyproject_scripts(repo_root: Path) -> list[dict[str, str]]:
    """Parse [project.scripts] and [project.gui-scripts] entry points."""
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return []

    entries: list[dict[str, str]] = []
    try:
        import tomllib

        content = pyproject.read_bytes()
        data = tomllib.loads(content.decode("utf-8"))

        project = data.get("project", {})

        # Console scripts
        for name, value in project.get("scripts", {}).items():
            entries.append(
                {
                    "name": name,
                    "description": value,
                    "runner": "Entry Point (console)",
                    "command": name,
                }
            )

        # GUI scripts
        for name, value in project.get("gui-scripts", {}).items():
            entries.append(
                {
                    "name": name,
                    "description": value,
                    "runner": "Entry Point (GUI)",
                    "command": name,
                }
            )
    except (OSError, ImportError, ValueError, KeyError):
        pass

    return entries


def _parse_npm_scripts(repo_root: Path) -> list[dict[str, str]]:
    """Parse npm scripts from package.json."""
    package_json = repo_root / "package.json"
    if not package_json.is_file():
        return []

    scripts: list[dict[str, str]] = []
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
        for name, cmd in data.get("scripts", {}).items():
            scripts.append(
                {
                    "name": name,
                    "description": cmd,
                    "runner": "npm",
                    "command": f"npm run {name}",
                }
            )
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    return scripts


def _parse_vscode_tasks(repo_root: Path) -> list[dict[str, str]]:
    """Parse VS Code tasks from .vscode/tasks.json."""
    tasks_file = repo_root / ".vscode" / "tasks.json"
    if not tasks_file.is_file():
        return []

    tasks: list[dict[str, str]] = []
    try:
        # Strip comments from JSON (VS Code tasks.json often has them)
        content = tasks_file.read_text(encoding="utf-8")
        # Remove single-line comments
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        data = json.loads(content)
        for t in data.get("tasks", []):
            label = t.get("label", "")
            cmd = t.get("command", "")
            detail = t.get("detail", "")
            tasks.append(
                {
                    "name": label,
                    "description": detail or cmd,
                    "runner": "VS Code Task",
                    "command": cmd,
                }
            )
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    return tasks


def _find_project_info(repo_root: Path) -> dict[str, Any]:
    """Extract project metadata from pyproject.toml."""
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return {}

    try:
        import tomllib

        content = pyproject.read_bytes()
        data = tomllib.loads(content.decode("utf-8"))
        project = data.get("project", {})

        return {
            "name": project.get("name", ""),
            "version": project.get("version", ""),
            "description": project.get("description", ""),
            "requires_python": project.get("requires-python", ""),
            "dependencies": project.get("dependencies", []),
            "optional_dep_groups": list(
                project.get("optional-dependencies", {}).keys()
            ),
        }
    except (OSError, ImportError, ValueError, KeyError):
        return {}


class ProjectCommandsCollector(BaseCollector):
    """Collect project commands, task runners, entry points, and scripts."""

    name = "project_commands"
    timeout = 30.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().STANDARD

    def collect(self) -> dict[str, Any]:
        from _imports import find_repo_root

        repo_root = find_repo_root()

        # Project metadata
        project_info = _find_project_info(repo_root)

        # Collect all command sources
        taskfile_tasks = _parse_taskfile(repo_root)
        makefile_targets = _parse_makefile(repo_root)
        hatch_scripts = _parse_hatch_scripts(repo_root)
        pyproject_scripts = _parse_pyproject_scripts(repo_root)
        npm_scripts = _parse_npm_scripts(repo_root)
        vscode_tasks = _parse_vscode_tasks(repo_root)

        # Group by runner
        all_commands = (
            taskfile_tasks
            + makefile_targets
            + hatch_scripts
            + pyproject_scripts
            + npm_scripts
            + vscode_tasks
        )

        runners: dict[str, list[dict[str, str]]] = {}
        for cmd in all_commands:
            runner = cmd.get("runner", "Unknown")
            runners.setdefault(runner, []).append(cmd)

        return {
            "project": project_info,
            "commands": all_commands,
            "by_runner": runners,
            "runner_names": list(runners.keys()),
            "total_commands": len(all_commands),
        }
