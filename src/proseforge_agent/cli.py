"""Command line entry point for ProseForge Agent.

This is the minimal CLI shell. Subcommands (init, status, phase-plan,
daily-workbook, chapter, export) are added by later tasks. For now the
parser exists, ``--help`` works before any project is initialized, and
running with no arguments prints help and exits cleanly.
"""

from __future__ import annotations

import argparse

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level ``pf-agent`` argument parser."""
    parser = argparse.ArgumentParser(
        prog="pf-agent",
        description=(
            "ProseForge Agent: agentic orchestration for long-form novel "
            "production on top of the ProseForge engine."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    With no subcommands available yet, print help when invoked without
    arguments and return ``0``. ``--help`` and ``--version`` are handled
    by argparse, which raises ``SystemExit(0)``.
    """
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
