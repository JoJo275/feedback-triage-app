"""Unit tests for tools/dev_tools/env_dashboard/app.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts/ to sys.path so _env_collectors can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

fastapi = pytest.importorskip(
    "fastapi", reason="fastapi not installed (dashboard env only)"
)

from tools.dev_tools.env_dashboard.app import create_app  # noqa: E402

# ---------------------------------------------------------------------------
# create_app
# ---------------------------------------------------------------------------


class TestCreateApp:
    """Tests for the FastAPI app factory."""

    def test_returns_fastapi_instance(self) -> None:
        app = create_app()
        assert app is not None
        assert app.title == "Environment Dashboard"

    def test_docs_disabled(self) -> None:
        app = create_app()
        assert app.docs_url is None
        assert app.redoc_url is None

    def test_static_mount_exists(self) -> None:
        app = create_app()
        # Check that /static is mounted
        route_paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert any("/static" in p for p in route_paths)

    def test_templates_on_app_state(self) -> None:
        app = create_app()
        assert hasattr(app.state, "templates")

    def test_templates_autoescape_enabled(self) -> None:
        app = create_app()
        assert app.state.templates.env.autoescape is True

    def test_routes_registered(self) -> None:
        app = create_app()
        route_paths = [r.path for r in app.routes if hasattr(r, "path")]
        # HTML routes
        assert "/" in route_paths
        # API routes (prefixed with /api)
        assert any("/api" in p for p in route_paths)
