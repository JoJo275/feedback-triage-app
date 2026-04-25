"""Static HTML export logic — self-contained, no JavaScript."""

from __future__ import annotations

import time
from typing import Any

from fastapi.templating import Jinja2Templates


def render_export(
    templates: Jinja2Templates,
    report: dict[str, Any],
    redact_level: str,
) -> str:
    """Render a self-contained HTML export from the scan report.

    The export:
    - Contains no JavaScript
    - Uses inline CSS only
    - Has a CSP meta tag blocking scripts
    - Shows a warning banner if redaction < PII

    Args:
        templates: Jinja2Templates instance.
        report: Full scan report dict.
        redact_level: String name of the redaction level applied.

    Returns:
        Complete HTML string ready for download.
    """
    timestamp = report.get("meta", {}).get(
        "timestamp", time.strftime("%Y-%m-%dT%H:%M:%S%z")
    )

    context = {
        "report": report,
        "summary": report.get("summary", {}),
        "warnings": report.get("warnings", []),
        "sections": report.get("sections", {}),
        "meta": report.get("meta", {}),
        "redact_level": redact_level,
        "timestamp": timestamp,
        "show_warning_banner": redact_level in ("none", "secrets"),
    }

    template = templates.get_template("export.html")
    return template.render(context)
