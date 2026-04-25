"""Unit tests for tools/dev_tools/env_dashboard/export.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add scripts/ to sys.path so _env_collectors can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

pytest.importorskip("fastapi", reason="fastapi not installed (dashboard env only)")

from tools.dev_tools.env_dashboard.export import render_export

# ---------------------------------------------------------------------------
# render_export
# ---------------------------------------------------------------------------

_FAKE_REPORT = {
    "meta": {"timestamp": "2025-01-01T00:00:00+0000"},
    "summary": {"hostname": "test-host"},
    "warnings": [],
    "sections": {"system": {"os": "Linux"}},
}


class TestRenderExport:
    """Tests for the render_export() function."""

    def _make_templates(self, rendered: str = "<html>ok</html>"):
        """Create a mock Jinja2Templates that returns *rendered*."""
        template = MagicMock()
        template.render.return_value = rendered
        templates = MagicMock()
        templates.get_template.return_value = template
        return templates, template

    def test_returns_string(self) -> None:
        templates, _ = self._make_templates()
        result = render_export(templates, _FAKE_REPORT, "secrets")
        assert isinstance(result, str)

    def test_uses_export_template(self) -> None:
        templates, _ = self._make_templates()
        render_export(templates, _FAKE_REPORT, "secrets")
        templates.get_template.assert_called_once_with("export.html")

    def test_passes_report_data_to_context(self) -> None:
        templates, template = self._make_templates()
        render_export(templates, _FAKE_REPORT, "pii")
        ctx = (
            template.render.call_args[1]
            if template.render.call_args[1]
            else template.render.call_args[0][0]
        )
        assert ctx["report"] == _FAKE_REPORT
        assert ctx["summary"] == _FAKE_REPORT["summary"]
        assert ctx["sections"] == _FAKE_REPORT["sections"]
        assert ctx["redact_level"] == "pii"

    def test_show_warning_banner_true_for_none_level(self) -> None:
        templates, template = self._make_templates()
        render_export(templates, _FAKE_REPORT, "none")
        ctx = (
            template.render.call_args[1]
            if template.render.call_args[1]
            else template.render.call_args[0][0]
        )
        assert ctx["show_warning_banner"] is True

    def test_show_warning_banner_true_for_secrets_level(self) -> None:
        templates, template = self._make_templates()
        render_export(templates, _FAKE_REPORT, "secrets")
        ctx = (
            template.render.call_args[1]
            if template.render.call_args[1]
            else template.render.call_args[0][0]
        )
        assert ctx["show_warning_banner"] is True

    def test_show_warning_banner_false_for_pii_level(self) -> None:
        templates, template = self._make_templates()
        render_export(templates, _FAKE_REPORT, "pii")
        ctx = (
            template.render.call_args[1]
            if template.render.call_args[1]
            else template.render.call_args[0][0]
        )
        assert ctx["show_warning_banner"] is False

    def test_timestamp_from_report_meta(self) -> None:
        templates, template = self._make_templates()
        render_export(templates, _FAKE_REPORT, "secrets")
        ctx = (
            template.render.call_args[1]
            if template.render.call_args[1]
            else template.render.call_args[0][0]
        )
        assert ctx["timestamp"] == "2025-01-01T00:00:00+0000"

    def test_fallback_timestamp_when_meta_missing(self) -> None:
        templates, template = self._make_templates()
        report_no_meta = {"meta": {}, "summary": {}, "warnings": [], "sections": {}}
        render_export(templates, report_no_meta, "secrets")
        ctx = (
            template.render.call_args[1]
            if template.render.call_args[1]
            else template.render.call_args[0][0]
        )
        # Should be a timestamp string, not empty
        assert isinstance(ctx["timestamp"], str)
        assert len(ctx["timestamp"]) > 0
