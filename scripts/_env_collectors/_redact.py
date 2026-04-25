"""Redaction layer — strip secrets from collected data."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

# --------------------------------------------------------------------------
# Redaction levels
# --------------------------------------------------------------------------


class RedactLevel(Enum):
    """How aggressively to strip sensitive data."""

    NONE = "none"  # No redaction (local viewing only)
    SECRETS = "secrets"  # Tokens, keys, passwords (default)
    PII = "pii"  # Secrets + usernames/hostnames/IPs
    PARANOID = "paranoid"  # PII + high-entropy + all env var values


REDACTED = "[REDACTED]"

# --------------------------------------------------------------------------
# Pattern-based rules
# --------------------------------------------------------------------------

# Env-var names that are always safe to show (value unredacted at SECRETS level)
_SAFE_ENV_VARS = frozenset(
    {
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "LANG",
        "LANGUAGE",
        "LC_ALL",
        "LC_CTYPE",
        "LOGNAME",
        "PATH",
        "PATHEXT",
        "PS1",
        "PWD",
        "SHELL",
        "SHLVL",
        "TERM",
        "TERM_PROGRAM",
        "TMPDIR",
        "USER",
        "USERNAME",
        "VIRTUAL_ENV",
        "HATCH_ENV_ACTIVE",
        "CONDA_DEFAULT_ENV",
        "EDITOR",
        "VISUAL",
        "PAGER",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_CACHE_HOME",
        "SYSTEMROOT",
        "COMSPEC",
        "PROCESSOR_ARCHITECTURE",
        "NUMBER_OF_PROCESSORS",
        "OS",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "WINDIR",
        "APPDATA",
        "LOCALAPPDATA",
        "USERPROFILE",
        "COMPUTERNAME",
    }
)

# Env-var name patterns whose *values* should be redacted at SECRETS level
_SECRET_NAME_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"TOKEN",
        r"SECRET",
        r"_KEY$",
        r"PASSWORD",
        r"PASSWD",
        r"CREDENTIAL",
        r"AUTH",
        r"API_KEY",
        r"PRIVATE",
        r"^AWS_",
        r"^GITHUB_TOKEN$",
        r"^GH_TOKEN$",
        r"^NPM_TOKEN$",
        r"^PYPI_TOKEN$",
        r"^AZURE_",
        r"^GCP_",
        r"^GOOGLE_APPLICATION_CREDENTIALS$",
        r"^DATABASE_URL$",
        r"^DB_",
        r"^REDIS_URL$",
        r"^MONGO",
        r"^SMTP_",
        r"^MAIL_",
        r"^SENDGRID",
        r"^TWILIO",
        r"^STRIPE",
        r"^SLACK_",
        r"^DISCORD_",
    ]
]

# URL credential pattern: scheme://user:pass@host
_URL_CRED_RE = re.compile(r"(https?://)[^@/:]+:[^@/:]+@", re.IGNORECASE)

# High-entropy detector (base64-like strings > 20 chars)
_HIGH_ENTROPY_RE = re.compile(r"[A-Za-z0-9+/=_\-]{20,}")

# PII patterns
_USERNAME_KEYS = frozenset({"username", "user", "hostname"})
_IP_RE = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b"  # IPv4
    r"|(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}",  # IPv6 (simplified)
)

# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------


def _is_secret_name(name: str) -> bool:
    """Check if an env-var name looks like it holds a secret."""
    return any(p.search(name) for p in _SECRET_NAME_PATTERNS)


def _strip_url_creds(value: str) -> str:
    """Replace user:pass in URLs with [REDACTED]."""
    return _URL_CRED_RE.sub(rf"\1{REDACTED}@", value)


def _is_high_entropy(value: str) -> bool:
    """Heuristic: does the value look like a base64 token?"""
    if len(value) < 20:
        return False
    m = _HIGH_ENTROPY_RE.fullmatch(value)
    return m is not None


def _redact_string(value: str, level: RedactLevel) -> str:
    """Redact a string value based on the level."""
    # Always strip URL credentials at SECRETS+
    value = _strip_url_creds(value)

    if level.value in ("pii", "paranoid"):
        # Mask IP addresses
        value = _IP_RE.sub(REDACTED, value)

    if level == RedactLevel.PARANOID and _is_high_entropy(value):
        return REDACTED

    return value


# --------------------------------------------------------------------------
# Recursive redaction
# --------------------------------------------------------------------------


def redact(data: Any, level: RedactLevel) -> Any:
    """Recursively redact sensitive values from a data structure.

    Args:
        data: Dict, list, or scalar to redact.
        level: Redaction level.

    Returns:
        A new data structure with secrets removed.
    """
    if level == RedactLevel.NONE:
        return data

    if isinstance(data, dict):
        return _redact_dict(data, level)

    if isinstance(data, list):
        return [redact(item, level) for item in data]

    if isinstance(data, str):
        return _redact_string(data, level)

    return data


def _redact_dict(d: dict[str, Any], level: RedactLevel) -> dict[str, Any]:
    """Redact values in a dict, key-aware."""
    result: dict[str, Any] = {}
    for key, value in d.items():
        key_lower = key.lower()

        # PII-level: mask username/hostname fields
        if level.value in ("pii", "paranoid") and key_lower in _USERNAME_KEYS:
            result[key] = REDACTED
            continue

        # SECRETS-level: check if key name is a known secret pattern
        if isinstance(value, str) and _is_secret_name(key):
            result[key] = REDACTED
            continue

        # PARANOID: redact all env var values except safe ones
        if (
            level == RedactLevel.PARANOID
            and key.isupper()
            and key not in _SAFE_ENV_VARS
        ):
            result[key] = REDACTED if isinstance(value, str) else redact(value, level)
            continue

        # Recurse into nested structures
        result[key] = redact(value, level)

    return result
