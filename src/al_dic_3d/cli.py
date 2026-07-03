"""Command-line interface for pyALDIC-3D.

Exposes ``--version`` and the Phase-1 ``run`` sub-command (a headless
``config.toml`` -> ``.npz`` + ``.mat`` pipeline). Further sub-commands
(``calibrate``, ``export``, ...) land as their backing modules arrive; the
``subparsers`` handle is the reserved seam. The heavy lifting lives in
:mod:`al_dic_3d.runner` so it stays unit-testable without a subprocess.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from al_dic_3d import __version__


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser.

    Kept as a standalone factory so tests can introspect the CLI surface without
    spawning a subprocess.
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
        epilog="Run 'al-dic-3d run config.toml' for a headless stereo-DIC pipeline.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"al-dic-3d {__version__}",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="<command>",
    )

    run_p = subparsers.add_parser(
        "run",
        help="run a headless correspondence + 3D-reconstruction pipeline from a TOML config",
        description=(
            "Load calibration + image sequences per the config, run the "
            "correspondence strategy and DLT reconstruction, and write "
            "<output.dir>/<output.prefix>.{npz,mat}."
        ),
    )
    run_p.add_argument("config", help="path to the run configuration (TOML)")
    run_p.add_argument(
        "-o", "--output", metavar="DIR", help="override [output].dir from the config"
    )
    run_p.add_argument(
        "-q", "--quiet", action="store_true", help="suppress per-frame progress output"
    )

    return parser


def _run_command(args: argparse.Namespace) -> int:
    """Handle ``al-dic-3d run <config.toml>``."""
    from dataclasses import replace

    from al_dic_3d.runner import load_config, run_pipeline, write_results

    cfg = load_config(args.config)
    if args.output:
        cfg = replace(cfg, output_dir=Path(args.output))

    def progress(frac: float, msg: str) -> None:
        if not args.quiet:
            print(f"  [{frac * 100:5.1f}%] {msg}")

    result = run_pipeline(cfg, progress=progress)
    paths = write_results(result, cfg)

    m = result.meta
    total = int(m["n_frames"]) * int(m["n_pts"])
    print(
        f"strategy={m['strategy']} frames={m['n_frames']} points={m['n_pts']} "
        f"tracked={m['n_tracked_positions']}/{total}"
    )
    print(f"wrote {paths['npz']}")
    print(f"wrote {paths['mat']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    command = getattr(args, "command", None)
    if command is None:
        parser.print_help()
        return 0
    if command == "run":
        return _run_command(args)
    parser.error(f"unknown command: {command}")
    return 2
