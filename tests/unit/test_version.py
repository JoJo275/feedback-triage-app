"""Unit tests for package version metadata."""

from simple_python_boilerplate import __version__


def test_version_exists() -> None:
    """Package exposes a version string."""
    assert isinstance(__version__, str)
