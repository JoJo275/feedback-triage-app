"""Tests for _env_collectors._redact — redaction engine."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _env_collectors._redact import (
    REDACTED,
    RedactLevel,
    _is_high_entropy,
    _is_secret_name,
    _strip_url_creds,
    redact,
)

# ── RedactLevel enum ────────────────────────────────────────


class TestRedactLevel:
    def test_none_value(self):
        assert RedactLevel.NONE.value == "none"

    def test_secrets_value(self):
        assert RedactLevel.SECRETS.value == "secrets"

    def test_pii_value(self):
        assert RedactLevel.PII.value == "pii"

    def test_paranoid_value(self):
        assert RedactLevel.PARANOID.value == "paranoid"


# ── _is_secret_name ─────────────────────────────────────────


class TestIsSecretName:
    @pytest.mark.parametrize(
        "name",
        [
            "API_TOKEN",
            "GITHUB_TOKEN",
            "GH_TOKEN",
            "NPM_TOKEN",
            "SECRET_KEY",
            "AWS_ACCESS_KEY_ID",
            "DATABASE_URL",
            "SMTP_PASSWORD",
            "SLACK_WEBHOOK",
        ],
    )
    def test_secret_names_detected(self, name):
        assert _is_secret_name(name) is True

    @pytest.mark.parametrize(
        "name",
        [
            "HOME",
            "PATH",
            "SHELL",
            "LANG",
            "TERM",
        ],
    )
    def test_safe_names_not_flagged(self, name):
        assert _is_secret_name(name) is False


# ── _strip_url_creds ────────────────────────────────────────


class TestStripUrlCreds:
    def test_strips_user_pass(self):
        url = "https://user:s3cret@github.com/repo"
        result = _strip_url_creds(url)
        assert "s3cret" not in result
        assert REDACTED in result
        assert result.endswith("github.com/repo")

    def test_no_creds_unchanged(self):
        url = "https://github.com/repo"
        assert _strip_url_creds(url) == url

    def test_http_scheme(self):
        url = "http://admin:pass@localhost:8080"
        result = _strip_url_creds(url)
        assert "admin" not in result
        assert "pass" not in result


# ── _is_high_entropy ────────────────────────────────────────


class TestIsHighEntropy:
    def test_short_string_is_not_high_entropy(self):
        assert _is_high_entropy("abc") is False

    def test_base64_token_detected(self):
        token = "dGhpcyBpcyBhIGJhc2U2NCB0b2tlbiB3aXRoIGVub3VnaCBsZW5ndGg="
        assert _is_high_entropy(token) is True

    def test_normal_sentence_is_not_high_entropy(self):
        assert _is_high_entropy("hello world, this is a test") is False


# ── redact() recursive ──────────────────────────────────────


class TestRedact:
    def test_none_level_returns_data_unchanged(self):
        data = {"secret_key": "hunter2"}
        assert redact(data, RedactLevel.NONE) == data

    def test_secrets_level_redacts_secret_env_var_values(self):
        data = {"GITHUB_TOKEN": "ghp_abc123def456"}
        result = redact(data, RedactLevel.SECRETS)
        assert result["GITHUB_TOKEN"] == REDACTED

    def test_secrets_level_preserves_safe_keys(self):
        data = {"hostname": "my-machine", "version": "3.11"}
        result = redact(data, RedactLevel.SECRETS)
        assert result["version"] == "3.11"

    def test_pii_level_redacts_username(self):
        data = {"username": "jdoe", "version": "1.0"}
        result = redact(data, RedactLevel.PII)
        assert result["username"] == REDACTED
        assert result["version"] == "1.0"

    def test_pii_level_redacts_ip_in_string(self):
        data = {"log": "connected from 192.168.1.100 at noon"}
        result = redact(data, RedactLevel.PII)
        assert "192.168.1.100" not in result["log"]

    def test_paranoid_level_redacts_high_entropy_strings(self):
        token = "dGhpcyBpcyBhIGJhc2U2NCB0b2tlbiB3aXRoIGVub3VnaCBsZW5ndGg="
        data = {"some_field": token}
        result = redact(data, RedactLevel.PARANOID)
        assert result["some_field"] == REDACTED

    def test_redacts_nested_dicts(self):
        data = {"outer": {"API_TOKEN": "secret123"}}
        result = redact(data, RedactLevel.SECRETS)
        assert result["outer"]["API_TOKEN"] == REDACTED

    def test_redacts_lists(self):
        data = [{"API_TOKEN": "abc"}, {"name": "test"}]
        result = redact(data, RedactLevel.SECRETS)
        assert result[0]["API_TOKEN"] == REDACTED
        assert result[1]["name"] == "test"

    def test_scalar_passthrough(self):
        assert redact(42, RedactLevel.SECRETS) == 42
        assert redact(True, RedactLevel.SECRETS) is True
        assert redact(None, RedactLevel.SECRETS) is None

    def test_url_creds_stripped_in_nested_value(self):
        data = {"remote": "https://user:pass@github.com/repo.git"}
        result = redact(data, RedactLevel.SECRETS)
        assert "pass" not in result["remote"]
