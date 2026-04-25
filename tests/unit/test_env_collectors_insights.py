"""Tests for _env_collectors.insights — InsightsCollector and helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _env_collectors.insights import InsightsCollector, _version_satisfies

# ── _version_satisfies ───────────────────────────────────────


class TestVersionSatisfies:
    @pytest.mark.parametrize(
        "version,constraint,expected",
        [
            ("3.12", ">=3.11", True),
            ("3.11", ">=3.11", True),
            ("3.10", ">=3.11", False),
            ("3.12", ">=3.11,<4", True),
            ("4.0", ">=3.11,<4", False),
            ("3.11", ">=3.11,<4", True),
            ("3.11", "==3.11", True),
            ("3.12", "==3.11", False),
            ("3.11", "!=3.11", False),
            ("3.12", "!=3.11", True),
            ("3.12", ">3.11", True),
            ("3.11", ">3.11", False),
            ("3.11", "<=3.11", True),
            ("3.12", "<=3.11", False),
            # Single-component constraints (e.g. "<4" → treated as "<4.0")
            ("3.99", "<4", True),
            ("4.0", "<4", False),
            ("4.1", ">=4", True),
            ("3.11", ">=4", False),
        ],
    )
    def test_constraint_evaluation(self, version, constraint, expected):
        assert _version_satisfies(version, constraint) is expected

    def test_unparsable_version_returns_true(self):
        assert _version_satisfies("nope", ">=3.11") is True

    def test_empty_constraint_returns_true(self):
        assert _version_satisfies("3.12", "") is True


# ── InsightsCollector ────────────────────────────────────────


class TestInsightsCollector:
    """Test insights derived from section data."""

    def _make_collector(self, sections):
        c = InsightsCollector()
        c._sections = sections
        return c

    def test_no_warnings_on_healthy_data(self):
        sections = {
            "runtimes": {"python": {"in_venv": True, "version": "3.12.0"}},
            "git": {"available": True, "dirty": False, "repo_detected": True},
            "path": {"dead_entries": 0, "duplicates": 0},
            "security": {
                "secret_env_vars": [],
                "insecure_path_entries": [],
                "ssh_keys_exposed": [],
            },
            "filesystem": {
                "disk": {"percent_used": 50},
                "writable": {"temp_dir": {"writable": True}},
            },
            "network": {"dns_resolves": True, "outbound_https": True},
            "container": {"ci": "", "wsl": False},
            "project_commands": {"project": {}},
            "pip_environments": {"environments": []},
            "project": {"build_tools": [], "config_files": []},
        }
        c = self._make_collector(sections)
        result = c.collect()
        assert result["count"] == 0
        assert result["warnings"] == []

    def test_warns_on_no_venv(self):
        sections = {
            "runtimes": {"python": {"in_venv": False}},
            "git": {},
            "path": {},
            "security": {},
            "filesystem": {},
            "network": {},
            "container": {},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        msgs = [w["message"] for w in result["warnings"]]
        assert any("virtual environment" in m for m in msgs)

    def test_warns_on_dirty_git(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {"dirty": True},
            "path": {},
            "security": {},
            "filesystem": {},
            "network": {},
            "container": {},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        msgs = [w["message"] for w in result["warnings"]]
        assert any("dirty" in m.lower() for m in msgs)

    def test_warns_on_dead_path_entries(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {},
            "path": {"dead_entries": 3, "duplicates": 0},
            "security": {},
            "filesystem": {},
            "network": {},
            "container": {},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        msgs = [w["message"] for w in result["warnings"]]
        assert any("non-existent" in m for m in msgs)

    def test_warns_on_path_duplicates(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {},
            "path": {"dead_entries": 0, "duplicates": 2},
            "security": {},
            "filesystem": {},
            "network": {},
            "container": {},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        msgs = [w["message"] for w in result["warnings"]]
        assert any("duplicate" in m.lower() for m in msgs)

    def test_warns_on_secret_env_vars(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {},
            "path": {},
            "security": {
                "secret_env_vars": [{"name": "API_TOKEN"}],
                "insecure_path_entries": [],
                "ssh_keys_exposed": [],
            },
            "filesystem": {},
            "network": {},
            "container": {},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        msgs = [w["message"] for w in result["warnings"]]
        assert any("secret" in m.lower() for m in msgs)

    def test_fails_on_insecure_path(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {},
            "path": {},
            "security": {
                "secret_env_vars": [],
                "insecure_path_entries": [{"path": "."}],
                "ssh_keys_exposed": [],
            },
            "filesystem": {},
            "network": {},
            "container": {},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        severities = [w["severity"] for w in result["warnings"]]
        assert "fail" in severities

    def test_warns_on_disk_over_80(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {},
            "path": {},
            "security": {},
            "filesystem": {"disk": {"percent_used": 85}, "writable": {}},
            "network": {},
            "container": {},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        msgs = [w["message"] for w in result["warnings"]]
        assert any("85%" in m for m in msgs)

    def test_fails_on_disk_over_90(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {},
            "path": {},
            "security": {},
            "filesystem": {"disk": {"percent_used": 95}, "writable": {}},
            "network": {},
            "container": {},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        severities = [w["severity"] for w in result["warnings"]]
        assert "fail" in severities

    def test_warns_on_dns_failure(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {},
            "path": {},
            "security": {},
            "filesystem": {},
            "network": {"dns_resolves": False, "outbound_https": False},
            "container": {},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        msgs = [w["message"] for w in result["warnings"]]
        assert any("DNS" in m for m in msgs)

    def test_warns_on_outbound_blocked(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {},
            "path": {},
            "security": {},
            "filesystem": {},
            "network": {"dns_resolves": True, "outbound_https": False},
            "container": {},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        msgs = [w["message"] for w in result["warnings"]]
        assert any("HTTPS" in m for m in msgs)

    def test_info_on_ci_detected(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {},
            "path": {},
            "security": {},
            "filesystem": {},
            "network": {},
            "container": {"ci": "GitHub Actions", "wsl": False},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        msgs = [w["message"] for w in result["warnings"]]
        assert any("CI" in m for m in msgs)

    def test_info_on_wsl_detected(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {},
            "path": {},
            "security": {},
            "filesystem": {},
            "network": {},
            "container": {"ci": "", "wsl": True},
            "project_commands": {},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        msgs = [w["message"] for w in result["warnings"]]
        assert any("WSL" in m for m in msgs)

    def test_fails_on_python_version_mismatch(self):
        sections = {
            "runtimes": {"python": {"in_venv": True, "version": "3.9.0"}},
            "git": {},
            "path": {},
            "security": {},
            "filesystem": {},
            "network": {},
            "container": {},
            "project_commands": {"project": {"requires_python": ">=3.11"}},
            "pip_environments": {},
            "project": {},
        }
        c = self._make_collector(sections)
        result = c.collect()
        severities = [w["severity"] for w in result["warnings"]]
        assert "fail" in severities

    def test_warns_on_git_not_available(self):
        sections = {
            "runtimes": {"python": {"in_venv": True}},
            "git": {"available": False},
            "path": {},
            "security": {},
            "filesystem": {},
            "network": {},
            "container": {},
            "project_commands": {},
            "pip_environments": {},
            "project": {"build_tools": [], "config_files": []},
        }
        c = self._make_collector(sections)
        result = c.collect()
        msgs = [w["message"] for w in result["warnings"]]
        assert any("git" in m.lower() and "not installed" in m.lower() for m in msgs)

    def test_all_warnings_have_required_fields(self):
        """Every warning must have severity, message, section."""
        sections = {
            "runtimes": {"python": {"in_venv": False, "version": "3.9"}},
            "git": {"available": False, "dirty": True},
            "path": {"dead_entries": 2, "duplicates": 1},
            "security": {
                "secret_env_vars": [{"name": "X"}],
                "insecure_path_entries": [{"path": "."}],
                "ssh_keys_exposed": [{"name": "SSH_KEY"}],
            },
            "filesystem": {
                "disk": {"percent_used": 95},
                "writable": {"temp_dir": {"writable": False}},
            },
            "network": {"dns_resolves": False},
            "container": {"ci": "GitHub Actions", "wsl": True},
            "project_commands": {"project": {"requires_python": ">=3.11"}},
            "pip_environments": {"environments": []},
            "project": {"build_tools": [], "config_files": []},
        }
        c = self._make_collector(sections)
        result = c.collect()
        for w in result["warnings"]:
            assert "severity" in w, f"Missing severity: {w}"
            assert "message" in w, f"Missing message: {w}"
            assert "section" in w, f"Missing section: {w}"
