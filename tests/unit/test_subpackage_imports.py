"""Tests for subpackage __init__ imports (dev_tools, sql)."""

from __future__ import annotations


def test_dev_tools_importable():
    import simple_python_boilerplate.dev_tools  # noqa: F401


def test_sql_importable():
    import simple_python_boilerplate.sql  # noqa: F401
