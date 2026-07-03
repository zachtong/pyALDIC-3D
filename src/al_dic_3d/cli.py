"""Command-line interface for pyALDIC-3D.

Phase 0 provides only ``--help`` and ``--version`` so the console-script entry
point (``al-dic-3d``) is wired and verifiable in CI. Sub-commands (``calibrate``,
``run``, ``export``, ...) land as their backing modules are implemented in later
phases; the ``subparsers`` handle below is the reserved seam for them.
"""

from __future__ import annotations

import argparse

from al_dic_3d import __version__


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser.

    Kept as a standalone factory so tests can introspect the CLI surface
    without spawning a subprocess.
    """
    parser = argparse.ArgumentParser(
        prog="al-dic-3d",
        description=(
            "pyALDIC-3D: stereo / multi-camera Digital Image Correlation "
            "(built on the pyALDIC-2D engine)."
        ),
        # ASCII-only: argparse prints this to stdout, whose encoding on a Windows
        # console can be a legacy code page that would raise UnicodeEncodeError on
        # em-dashes / section signs and crash `--help`.
        epilog="Phase 0 scaffold - no sub-commands are implemented yet.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"al-dic-3d {__version__}",
    )
    # Reserved seam for future sub-commands (calibrate / run / export / ...).
    # Declared but empty so `--help` documents the shape without requiring any
    # not-yet-implemented backend.
    parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="<command>",
        help="(none available yet - see docs/architecture/01 sec. G for the roadmap)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code.

    With no sub-command (all that Phase 0 offers), print help and exit 0 so the
    binary is a well-behaved no-op rather than an error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", None) is None:
        parser.print_help()
        return 0
    # Unreachable in Phase 0 (no sub-commands registered), but keeps the
    # contract explicit for when the first sub-command lands.
    parser.error(f"unknown command: {args.command}")
    return 2
