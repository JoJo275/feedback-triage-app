"""Unit tests for :mod:`feedback_triage.auth.cookies`.

The cookie writer is the single chokepoint for ``Set-Cookie`` on the
auth surface; if the attribute set drifts, every login gets the wrong
cookie. These tests pin the spec contract (auth.md — Session cookie):
HttpOnly always, SameSite=Lax, Path=/, Max-Age=604800, and Secure
mirrored from settings.
"""

from __future__ import annotations

from fastapi import Response

from feedback_triage.auth.cookies import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    clear_session_cookie,
    set_session_cookie,
)


def _set_cookie_header(response: Response) -> str:
    raw = response.raw_headers
    headers = [(k.decode(), v.decode()) for k, v in raw]
    set_cookies = [v for k, v in headers if k.lower() == "set-cookie"]
    assert len(set_cookies) == 1, set_cookies
    return set_cookies[0]


def test_session_cookie_attributes_secure() -> None:
    response = Response()
    set_session_cookie(response, raw_token="abc123", secure=True)
    header = _set_cookie_header(response)
    assert header.startswith(f"{SESSION_COOKIE_NAME}=abc123")
    assert "HttpOnly" in header
    assert "Secure" in header
    assert "samesite=lax" in header.lower()
    assert "Path=/" in header
    assert f"Max-Age={SESSION_MAX_AGE_SECONDS}" in header


def test_session_cookie_omits_secure_in_dev() -> None:
    response = Response()
    set_session_cookie(response, raw_token="abc123", secure=False)
    header = _set_cookie_header(response)
    assert "Secure" not in header
    assert "HttpOnly" in header


def test_clear_session_cookie_writes_expiry() -> None:
    response = Response()
    clear_session_cookie(response, secure=True)
    header = _set_cookie_header(response)
    assert SESSION_COOKIE_NAME in header
    # Starlette emits ``Max-Age=0`` and an ``Expires`` header in the
    # past; we only assert the canonical "expired" marker.
    assert "Max-Age=0" in header
