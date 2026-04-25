"""Tests for all individual _env_collectors — one class per collector.

Each collector is tested via ``safe_collect()`` to ensure:
1. It returns a dict
2. It does not raise
3. It contains expected top-level keys
4. Edge cases with mocked dependencies behave correctly

The tests mock external commands (subprocess, shutil.which, socket) so they
run fast and don't depend on the host environment.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _env_collectors._base import BaseCollector

# ── Helpers ──────────────────────────────────────────────────


def _safe(cls: type[BaseCollector], **kwargs: Any) -> dict[str, Any]:
    """Instantiate a collector and run safe_collect()."""
    instance = cls(**kwargs) if kwargs else cls()
    return instance.safe_collect()


# ── SystemCollector ──────────────────────────────────────────


class TestSystemCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.system import SystemCollector

        result = _safe(SystemCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_contains_expected_keys(self):
        from _env_collectors.system import SystemCollector

        result = _safe(SystemCollector)
        for key in ("os", "hostname", "architecture", "shell", "cwd"):
            assert key in result, f"Missing key: {key}"

    def test_os_is_string(self):
        from _env_collectors.system import SystemCollector

        result = _safe(SystemCollector)
        assert isinstance(result["os"], str)
        assert len(result["os"]) > 0


# ── HardwareCollector ────────────────────────────────────────


class TestHardwareCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.hardware import HardwareCollector

        result = _safe(HardwareCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_contains_cpu(self):
        from _env_collectors.hardware import HardwareCollector

        result = _safe(HardwareCollector)
        assert "cpu" in result

    def test_cpu_has_logical_cores(self):
        from _env_collectors.hardware import HardwareCollector

        result = _safe(HardwareCollector)
        cpu = result["cpu"]
        assert "logical_cores" in cpu
        assert cpu["logical_cores"] is None or isinstance(cpu["logical_cores"], int)


# ── RuntimesCollector ────────────────────────────────────────


class TestRuntimesCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.runtimes import RuntimesCollector

        result = _safe(RuntimesCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_python_info_present(self):
        from _env_collectors.runtimes import RuntimesCollector

        result = _safe(RuntimesCollector)
        assert "python" in result
        py = result["python"]
        assert "version" in py
        assert "executable" in py

    def test_installations_is_list(self):
        from _env_collectors.runtimes import RuntimesCollector

        result = _safe(RuntimesCollector)
        assert isinstance(result["installations"], list)


# ── PathAnalysisCollector ────────────────────────────────────


class TestPathAnalysisCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.path_analysis import PathAnalysisCollector

        result = _safe(PathAnalysisCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_contains_entries_and_counts(self):
        from _env_collectors.path_analysis import PathAnalysisCollector

        result = _safe(PathAnalysisCollector)
        assert "entries" in result
        assert "total" in result
        assert "duplicates" in result
        assert "dead_entries" in result

    def test_dead_entries_detected(self, monkeypatch):
        from _env_collectors.path_analysis import PathAnalysisCollector

        monkeypatch.setenv("PATH", "/nonexistent/dir/that/should/not/exist")
        result = _safe(PathAnalysisCollector)
        assert result["dead_entries"] >= 1


# ── ProjectCollector ─────────────────────────────────────────


class TestProjectCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.project import ProjectCollector

        result = _safe(ProjectCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_contains_repo_root(self):
        from _env_collectors.project import ProjectCollector

        result = _safe(ProjectCollector)
        assert "repo_root" in result


# ── ProjectCommandsCollector ─────────────────────────────────


class TestProjectCommandsCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.project_commands import ProjectCommandsCollector

        result = _safe(ProjectCommandsCollector)
        assert isinstance(result, dict)
        assert result["error"] is None


# ── GitInfoCollector ─────────────────────────────────────────


class TestGitInfoCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.git_info import GitInfoCollector

        result = _safe(GitInfoCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_available_key_present(self):
        from _env_collectors.git_info import GitInfoCollector

        result = _safe(GitInfoCollector)
        assert "available" in result

    @patch("shutil.which", return_value=None)
    def test_no_git_returns_unavailable(self, _mock_which):
        from _env_collectors.git_info import GitInfoCollector

        result = _safe(GitInfoCollector)
        assert result["available"] is False
        assert result["repo_detected"] is False


# ── VenvCollector ────────────────────────────────────────────


class TestVenvCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.venv import VenvCollector

        result = _safe(VenvCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_active_is_bool(self):
        from _env_collectors.venv import VenvCollector

        result = _safe(VenvCollector)
        assert isinstance(result["active"], bool)

    def test_prefix_is_string(self):
        from _env_collectors.venv import VenvCollector

        result = _safe(VenvCollector)
        assert isinstance(result["prefix"], str)


# ── PipEnvironmentsCollector ─────────────────────────────────


class TestPipEnvironmentsCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.pip_environments import PipEnvironmentsCollector

        result = _safe(PipEnvironmentsCollector)
        assert isinstance(result, dict)
        assert result["error"] is None


# ── PackagesCollector ────────────────────────────────────────


class TestPackagesCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.packages import PackagesCollector

        result = _safe(PackagesCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_packages_is_list(self):
        from _env_collectors.packages import PackagesCollector

        result = _safe(PackagesCollector)
        assert isinstance(result["packages"], list)
        assert result["total"] >= 0

    def test_has_duplicate_detection(self):
        from _env_collectors.packages import PackagesCollector

        result = _safe(PackagesCollector)
        assert "duplicate_packages" in result


# ── NetworkCollector ─────────────────────────────────────────


class TestNetworkCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.network import NetworkCollector

        result = _safe(NetworkCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_contains_proxy_info(self):
        from _env_collectors.network import NetworkCollector

        result = _safe(NetworkCollector)
        assert "proxy" in result
        assert "hostname" in result

    @patch("socket.getaddrinfo", side_effect=OSError("no dns"))
    @patch("socket.create_connection", side_effect=OSError("no conn"))
    def test_handles_network_failure(self, _mock_conn, _mock_dns):
        from _env_collectors.network import NetworkCollector

        result = _safe(NetworkCollector)
        assert result["dns_resolves"] is False
        assert result["outbound_https"] is False


# ── FilesystemCollector ──────────────────────────────────────


class TestFilesystemCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.filesystem import FilesystemCollector

        result = _safe(FilesystemCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_contains_disk_and_writable(self):
        from _env_collectors.filesystem import FilesystemCollector

        result = _safe(FilesystemCollector)
        assert "disk" in result
        assert "writable" in result
        assert "temp_dir" in result


# ── SecurityCollector ────────────────────────────────────────


class TestSecurityCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.security import SecurityCollector

        result = _safe(SecurityCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_contains_expected_keys(self):
        from _env_collectors.security import SecurityCollector

        result = _safe(SecurityCollector)
        assert "secret_env_vars" in result
        assert "insecure_path_entries" in result
        assert "ssh_keys_exposed" in result

    def test_detects_secret_env_var(self, monkeypatch):
        from _env_collectors.security import SecurityCollector

        monkeypatch.setenv("MY_API_TOKEN", "fake-secret-value")
        result = _safe(SecurityCollector)
        names = [s["name"] for s in result["secret_env_vars"]]
        assert "MY_API_TOKEN" in names

    def test_no_false_positive_on_safe_var(self, monkeypatch):
        from _env_collectors.security import SecurityCollector

        monkeypatch.setenv("MY_SAFE_VAR_XYZ", "hello")
        result = _safe(SecurityCollector)
        names = [s["name"] for s in result["secret_env_vars"]]
        assert "MY_SAFE_VAR_XYZ" not in names


# ── ContainerCollector ───────────────────────────────────────


class TestContainerCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.container import ContainerCollector

        result = _safe(ContainerCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    def test_contains_detection_keys(self):
        from _env_collectors.container import ContainerCollector

        result = _safe(ContainerCollector)
        assert "docker" in result
        assert "ci" in result
        assert "wsl" in result

    def test_detects_github_actions(self, monkeypatch):
        from _env_collectors.container import ContainerCollector

        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        result = _safe(ContainerCollector)
        assert result["ci"] == "GitHub Actions"

    def test_detects_gitlab_ci(self, monkeypatch):
        from _env_collectors.container import ContainerCollector

        monkeypatch.setenv("GITLAB_CI", "true")
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
        result = _safe(ContainerCollector)
        assert result["ci"] == "GitLab CI"


# ── PrecommitHooksCollector ──────────────────────────────────


class TestPrecommitHooksCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.precommit_hooks import PrecommitHooksCollector

        result = _safe(PrecommitHooksCollector)
        assert isinstance(result, dict)
        assert result["error"] is None


# ── CiCdStatusCollector ──────────────────────────────────────


class TestCiCdStatusCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.ci_cd_status import CiCdStatusCollector

        result = _safe(CiCdStatusCollector)
        assert isinstance(result, dict)
        assert result["error"] is None


# ── DependencyHealthCollector ────────────────────────────────


class TestDependencyHealthCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.dependency_health import DependencyHealthCollector

        result = _safe(DependencyHealthCollector)
        assert isinstance(result, dict)
        assert result["error"] is None

    @patch("shutil.which", return_value=None)
    def test_no_pip_no_crash(self, _mock):
        from _env_collectors.dependency_health import DependencyHealthCollector

        result = _safe(DependencyHealthCollector)
        assert result["error"] is None


# ── DiskWorkspaceSizeCollector ───────────────────────────────


class TestDiskWorkspaceSizeCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.disk_workspace import DiskWorkspaceSizeCollector

        result = _safe(DiskWorkspaceSizeCollector)
        assert isinstance(result, dict)
        assert result["error"] is None


# ── DocsStatusCollector ──────────────────────────────────────


class TestDocsStatusCollector:
    def test_collect_returns_dict(self):
        from _env_collectors.docs_status import DocsStatusCollector

        result = _safe(DocsStatusCollector)
        assert isinstance(result, dict)
        assert result["error"] is None


# ── InsightsCollector (as a BaseCollector) ────────────────────


class TestInsightsCollectorAsCollector:
    """Test InsightsCollector safe_collect with minimal section data."""

    def test_safe_collect_returns_dict(self):
        from _env_collectors.insights import InsightsCollector

        c = InsightsCollector()
        c._sections = {}
        result = c.safe_collect()
        assert isinstance(result, dict)
        assert result["error"] is None
        assert "warnings" in result
