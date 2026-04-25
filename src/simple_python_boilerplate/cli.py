"""Command-line interface definitions and argument parsing.

This module handles CLI argument parsing and command definitions. It provides
the user-facing command structure while delegating actual work to the engine
module. Entry points in main.py call into this module.

Typical contents:
    - Argument parser setup
    - Command definitions
    - Input validation for CLI
    - Output formatting for terminal

Usage:
    # As entry point (configured in pyproject.toml)
    $ my-command --help

    # Programmatic
    from simple_python_boilerplate.cli import parse_args, run
    args = parse_args()
    run(args)

Note:
    For simple CLIs, argparse is sufficient. For complex CLIs,
    consider click, typer, or rich-click.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="simple-python-boilerplate",
        description="A minimal Python boilerplate project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show version information and exit",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process input data")
    process_parser.add_argument("input", help="Input data to process")
    process_parser.add_argument(
        "-o",
        "--output",
        help="Output file (default: stdout)",
    )

    # Doctor command
    subparsers.add_parser("doctor", help="Diagnose environment issues")

    return parser


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Arguments to parse. If None, uses sys.argv.

    Returns:
        Parsed arguments namespace.
    """
    parser = create_parser()
    return parser.parse_args(args)


def run(args: argparse.Namespace) -> int:
    """Execute the CLI based on parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    if args.version:
        from simple_python_boilerplate.engine import get_version_info

        info = get_version_info()
        print(f"simple-python-boilerplate {info['package_version']}")
        print(f"Python {info['python_full']}")
        return 0

    if args.command == "doctor":
        from simple_python_boilerplate.entry_points import doctor

        doctor()  # doctor() in entry_points.py handles formatting
        return 0

    if args.command == "process":
        from simple_python_boilerplate.engine import (
            process_data,
            validate_input,
        )

        if not validate_input(args.input):
            print("Error: Invalid input")
            return 1

        result = process_data(args.input)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            if args.verbose:
                print(f"Output written to {args.output}")
        else:
            print(result)

        return 0

    # No command specified - show help
    create_parser().print_help()
    return 0
