"""Dashboard redaction wiring.

Thin wrapper connecting ``_env_collectors._redact`` to route-level
``?redact=`` parameter handling.
"""

from __future__ import annotations

from _env_collectors._redact import RedactLevel

# Default levels
DEFAULT_VIEW_LEVEL = RedactLevel.SECRETS
DEFAULT_EXPORT_LEVEL = RedactLevel.PII


def parse_redact_param(value: str | None, *, export: bool = False) -> RedactLevel:
    """Parse a ``?redact=`` query parameter into a RedactLevel.

    Args:
        value: The raw query string value (e.g. "secrets", "pii", "none").
        export: If True, default to PII level instead of SECRETS.

    Returns:
        The resolved RedactLevel.
    """
    default = DEFAULT_EXPORT_LEVEL if export else DEFAULT_VIEW_LEVEL

    if not value:
        return default

    value_lower = value.lower().strip()
    for level in RedactLevel:
        if level.value == value_lower:
            return level

    return default
