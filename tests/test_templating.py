"""Unit tests for ``feedback_triage.templating``.

Covers ``static_url`` and the cached ``_load_manifest`` helper across
the present / missing / unreadable / malformed manifest paths and
asserts that the missing-manifest warning is logged at most once.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from feedback_triage import templating

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def isolated_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Path]:
    """Point the module's ``CSS_MANIFEST`` at a temp file and reset the cache."""
    manifest = tmp_path / "manifest.json"
    monkeypatch.setattr(templating, "CSS_MANIFEST", manifest)
    monkeypatch.setattr(templating, "_manifest_cache", {})
    monkeypatch.setattr(templating, "_manifest_mtime", None)
    yield manifest


def test_static_url_uses_hashed_name_from_manifest(isolated_manifest: Path) -> None:
    isolated_manifest.write_text(
        json.dumps({"app.css": "app.deadbeef.css"}), encoding="utf-8"
    )
    assert templating.static_url("app.css") == "/static/css/app.deadbeef.css"


def test_static_url_non_css_uses_static_root(isolated_manifest: Path) -> None:
    isolated_manifest.write_text(json.dumps({}), encoding="utf-8")
    assert templating.static_url("logo.svg") == "/static/logo.svg"


def test_static_url_falls_back_when_manifest_missing(
    isolated_manifest: Path, caplog: pytest.LogCaptureFixture
) -> None:
    assert not isolated_manifest.exists()
    with caplog.at_level(logging.WARNING, logger=templating.logger.name):
        url = templating.static_url("app.css")
    assert url == "/static/css/app.css"
    assert any("missing" in r.message for r in caplog.records)


def test_missing_manifest_warning_emitted_only_once(
    isolated_manifest: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger=templating.logger.name):
        templating.static_url("app.css")
        templating.static_url("app.css")
        templating.static_url("app.css")
    warnings = [r for r in caplog.records if "missing" in r.message]
    assert len(warnings) == 1


def test_manifest_malformed_json_falls_back(
    isolated_manifest: Path, caplog: pytest.LogCaptureFixture
) -> None:
    isolated_manifest.write_text("{not json", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger=templating.logger.name):
        assert templating.static_url("app.css") == "/static/css/app.css"
    assert any("Could not parse" in r.message for r in caplog.records)


def test_manifest_non_dict_falls_back(isolated_manifest: Path) -> None:
    isolated_manifest.write_text(json.dumps(["nope"]), encoding="utf-8")
    assert templating.static_url("app.css") == "/static/css/app.css"


def test_manifest_cache_invalidates_on_mtime_change(isolated_manifest: Path) -> None:
    isolated_manifest.write_text(
        json.dumps({"app.css": "app.aaaaaaaa.css"}), encoding="utf-8"
    )
    assert templating.static_url("app.css") == "/static/css/app.aaaaaaaa.css"

    # Bump mtime forward and rewrite — cache must pick up the new value.
    isolated_manifest.write_text(
        json.dumps({"app.css": "app.bbbbbbbb.css"}), encoding="utf-8"
    )
    new_mtime = isolated_manifest.stat().st_mtime + 5
    import os

    os.utime(isolated_manifest, (new_mtime, new_mtime))
    assert templating.static_url("app.css") == "/static/css/app.bbbbbbbb.css"
