"""Unit tests for the API module."""

import pytest

from simple_python_boilerplate.api import create_app, health_check


class TestHealthCheck:
    """Tests for the health_check function."""

    def test_health_check_returns_dict(self) -> None:
        """Health check should return a dictionary."""
        result = health_check()
        assert isinstance(result, dict)

    def test_health_check_has_status_key(self) -> None:
        """Health check should contain a 'status' key."""
        result = health_check()
        assert "status" in result

    def test_health_check_status_is_ok(self) -> None:
        """Health check status should be 'ok'."""
        result = health_check()
        assert result["status"] == "ok"


class TestCreateApp:
    """Tests for the create_app factory function."""

    def test_create_app_raises_not_implemented(self) -> None:
        """create_app should raise NotImplementedError (placeholder)."""
        with pytest.raises(NotImplementedError):
            create_app()

    def test_create_app_error_message(self) -> None:
        """create_app error message should mention framework selection."""
        with pytest.raises(NotImplementedError, match="framework"):
            create_app()
