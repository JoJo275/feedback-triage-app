"""Export the FastAPI OpenAPI schema to a JSON file.

The frontend type-generation pipeline reads this file as input for
``openapi-typescript`` so API contracts and UI DTOs stay synchronized.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from sys import stdout

from feedback_triage.main import create_app


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export /api/v1 OpenAPI schema to disk.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("web/openapi.v1.json"),
        help="Output file path for the exported OpenAPI JSON.",
    )
    return parser.parse_args()


def export_openapi(*, out_path: Path) -> Path:
    """Write the app's OpenAPI schema to ``out_path``.

    Args:
        out_path: Destination JSON file.

    Returns:
        The resolved output path.
    """
    app = create_app()
    openapi = app.openapi()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(openapi, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_path.resolve()


def main() -> int:
    """Parse CLI args, export OpenAPI, and return an exit code."""
    args = _parse_args()
    output = export_openapi(out_path=args.out)
    stdout.write(f"Exported OpenAPI schema to {output}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
