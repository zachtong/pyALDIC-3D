"""Command-line interface for pyALDIC-3D.

Exposes ``--version``, the Phase-1 ``run`` sub-command (a headless
``config.toml`` -> ``.npz`` + ``.mat`` pipeline), ``gui``, and the D12
``calibrate`` sub-command (board image pairs -> QC'd stereo calibration ->
OpenCV YAML). Further sub-commands (``export``, ...) land as their backing
modules arrive; the ``subparsers`` handle is the reserved seam. The heavy
lifting lives in :mod:`al_dic_3d.runner` / :mod:`al_dic_3d.calibration` so it
stays unit-testable without a subprocess.
"""

from __future__ import annotations

import argparse
import sys
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
            "correspondence strategy and DLT reconstruction, and write the "
            "selected --formats (plus a parameters JSON) under <output.dir>."
        ),
    )
    run_p.add_argument("config", help="path to the run configuration (TOML)")
    run_p.add_argument(
        "-o", "--output", metavar="DIR", help="override [output].dir from the config"
    )
    run_p.add_argument(
        "-q", "--quiet", action="store_true", help="suppress per-frame progress output"
    )
    run_p.add_argument(
        "--formats",
        default="npz,mat",
        metavar="LIST",
        help=(
            "comma-separated output formats: npz,mat,csv,ply,vtu "
            "(default: npz,mat; a parameters JSON is always written)"
        ),
    )

    subparsers.add_parser(
        "gui",
        help="launch the graphical workflow (requires PySide6)",
        description="Open the pyALDIC-3D desktop application.",
    )

    cal_p = subparsers.add_parser(
        "calibrate",
        help="built-in stereo calibration from board image pairs (D12)",
        description=(
            "Detect a calibration board in synchronized L/R image sets, solve "
            "per-camera intrinsics + stereo extrinsics with QC (worst-pair "
            "rejection, epipolar validation), and write an OpenCV YAML that "
            "'run' consumes as [calibration] file/format=opencv_yaml."
        ),
    )
    cal_p.add_argument("--left", required=True, metavar="GLOB", help="left image glob")
    cal_p.add_argument("--right", required=True, metavar="GLOB", help="right image glob")
    cal_p.add_argument(
        "-o", "--output", default="calibration.yml", metavar="FILE", help="output YAML path"
    )
    cal_p.add_argument(
        "--board",
        required=True,
        choices=("chessboard", "charuco", "circles", "coded"),
        help="board family",
    )
    cal_p.add_argument("--cols", type=int, required=True, help="inner corners / dots per row")
    cal_p.add_argument("--rows", type=int, required=True, help="inner corners / dots per column")
    cal_p.add_argument("--square", type=float, help="square size in mm (chessboard / charuco)")
    cal_p.add_argument("--marker", type=float, help="ArUco marker size in mm (charuco)")
    cal_p.add_argument(
        "--dict", default="DICT_5X5_1000", metavar="NAME", help="ArUco dictionary (charuco)"
    )
    cal_p.add_argument(
        "--legacy", action="store_true", help="board printed with OpenCV < 4.7 (charuco)"
    )
    cal_p.add_argument("--spacing", type=float, help="dot pitch in mm (circles / coded)")
    cal_p.add_argument("--dot", type=float, help="dot diameter in mm (circles / coded)")
    cal_p.add_argument("--asymmetric", action="store_true", help="asymmetric circle grid (circles)")
    cal_p.add_argument(
        "--joint", action="store_true", help="jointly refine intrinsics in the stereo solve"
    )
    cal_p.add_argument(
        "--tangential", action="store_true", help="estimate tangential distortion p1/p2"
    )
    cal_p.add_argument("--fix-k3", action="store_true", help="fix k3 = 0 (low-distortion lens)")
    cal_p.add_argument(
        "--release-object",
        action="store_true",
        help="release-object method for imprecise printed boards (full views only)",
    )
    cal_p.add_argument(
        "--no-ecc-correction",
        action="store_true",
        help="disable the dot eccentricity correction (circles / coded)",
    )
    cal_p.add_argument(
        "--min-pairs", type=int, default=6, help="minimum usable stereo pairs (default 6)"
    )
    cal_p.add_argument(
        "--bundle",
        action="store_true",
        help="joint scipy bundle adjustment after the solve (robust loss, uses mono views)",
    )
    cal_p.add_argument(
        "--verify-left", metavar="FILE", help="LEFT image of a verification board pair"
    )
    cal_p.add_argument(
        "--verify-right", metavar="FILE", help="RIGHT image of a verification board pair"
    )

    return parser


def _run_command(args: argparse.Namespace) -> int:
    """Handle ``al-dic-3d run <config.toml>``."""
    from dataclasses import replace

    from al_dic_3d.runner import RESULT_FORMATS, load_config, run_pipeline, write_results

    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    unknown = sorted(set(formats) - set(RESULT_FORMATS))
    if unknown or not formats:
        print(
            f"error: --formats must be a comma list of {','.join(RESULT_FORMATS)}; "
            f"got {args.formats!r}",
            file=sys.stderr,
        )
        return 2

    cfg = load_config(args.config)
    if args.output:
        cfg = replace(cfg, output_dir=Path(args.output))

    def progress(frac: float, msg: str) -> None:
        if not args.quiet:
            print(f"  [{frac * 100:5.1f}%] {msg}")

    result = run_pipeline(cfg, progress=progress)
    paths = write_results(result, cfg, formats=formats)

    m = result.meta
    total = int(m["n_frames"]) * int(m["n_pts"])
    print(
        f"strategy={m['strategy']} frames={m['n_frames']} points={m['n_pts']} "
        f"tracked={m['n_tracked_positions']}/{total}"
    )
    for key in ("params", *formats):
        print(f"wrote {paths[key]}")
    return 0


def _board_spec_from_args(args: argparse.Namespace, parser_error) -> object:
    """Build the BoardSpec for the ``calibrate`` sub-command's argument set."""
    from al_dic_3d.calibration import (
        CharucoSpec,
        ChessboardSpec,
        CircleGridSpec,
        CodedCircleGridSpec,
    )

    if args.board == "chessboard":
        if args.square is None:
            parser_error("--square is required for --board chessboard")
        return ChessboardSpec(cols=args.cols, rows=args.rows, square_size=args.square)
    if args.board == "charuco":
        if args.square is None or args.marker is None:
            parser_error("--square and --marker are required for --board charuco")
        return CharucoSpec(
            squares_x=args.cols,
            squares_y=args.rows,
            square_size=args.square,
            marker_size=args.marker,
            dictionary=args.dict,
            legacy_pattern=args.legacy,
        )
    if args.spacing is None:
        parser_error(f"--spacing is required for --board {args.board}")
    if args.board == "circles":
        return CircleGridSpec(
            cols=args.cols,
            rows=args.rows,
            spacing=args.spacing,
            asymmetric=args.asymmetric,
            dot_diameter=args.dot,
        )
    return CodedCircleGridSpec(
        cols=args.cols, rows=args.rows, spacing=args.spacing, dot_diameter=args.dot
    )


def _calibrate_command(args: argparse.Namespace) -> int:
    """Handle ``al-dic-3d calibrate`` (detect -> solve -> QC -> YAML)."""
    import glob as globlib

    import cv2

    from al_dic_3d.calibration import calibrate_stereo, detect_board, summarize, to_opencv_yaml

    def fail(msg: str) -> None:
        print(f"error: {msg}", file=sys.stderr)
        raise SystemExit(2)

    try:
        spec = _board_spec_from_args(args, fail)
    except ValueError as exc:  # invalid board geometry (spec validation)
        fail(str(exc))
    left_files = sorted(globlib.glob(args.left))
    right_files = sorted(globlib.glob(args.right))
    if not left_files or len(left_files) != len(right_files):
        fail(
            f"left/right image sets must be non-empty and equal length "
            f"(got {len(left_files)}/{len(right_files)})"
        )

    def detect_all(files: list[str], tag: str):
        dets = []
        for f in files:
            img = cv2.imread(f, cv2.IMREAD_UNCHANGED)
            if img is None:
                fail(f"cannot read image: {f}")
            det = detect_board(img, spec)
            status = f"{det.n_points} pts" if det.ok else f"FAIL ({det.reason})"
            print(f"  [{tag}] {Path(f).name}: {status}")
            dets.append(det)
        return dets

    print(f"detecting {args.board} board in {len(left_files)} pairs...")
    dl = detect_all(left_files, "L")
    dr = detect_all(right_files, "R")

    first = cv2.imread(left_files[0], cv2.IMREAD_UNCHANGED)
    image_size = (first.shape[1], first.shape[0])
    dot_mm = getattr(spec, "dot_mm", None)
    ecc = None if args.no_ecc_correction or dot_mm is None else dot_mm / 2.0

    try:
        res = calibrate_stereo(
            dl,
            dr,
            image_size,
            joint_refine=args.joint,
            zero_tangent=not args.tangential,
            fix_k3=args.fix_k3,
            release_object=args.release_object,
            min_pairs=args.min_pairs,
            dot_radius_mm=ecc,
        )
    except ValueError as exc:
        fail(str(exc))

    if args.bundle:
        from dataclasses import replace as _replace

        from al_dic_3d.calibration import bundle_refine

        new_rig, info = bundle_refine(
            dl, dr, res, zero_tangent=not args.tangential, fix_k3=args.fix_k3
        )
        res = _replace(res, rig=new_rig)
        print(
            f"bundle adjustment: rms {info['rms_before']:.4f} -> {info['rms_after']:.4f} px "
            f"({info['n_views']:.0f} views, {info['n_mono_views']:.0f} mono-only)"
        )

    print("\npair QC (rms px, left/right):")
    for p in res.pairs:
        mark = "used" if p.used else f"DROPPED: {p.note}"
        rms = f"{p.rms_left:5.3f}/{p.rms_right:5.3f}" if p.n_common else "  -  /  -  "
        print(f"  #{p.index:02d} n={p.n_common:3d} {rms}  {mark}")
    for w in res.warnings:
        print(f"warning: {w}")

    stats = summarize(res, dl, dr, image_size)
    print(
        f"\nstereo rms {res.rms:.4f} px | epipolar {res.epipolar_rms:.4f} px | "
        f"baseline {res.baseline:.3f} | pairs {res.n_pairs_used}/{len(res.pairs)} | "
        f"coverage L {stats['coverage_left']:.0%} R {stats['coverage_right']:.0%}"
    )
    meta = {
        "source": "al-dic-3d calibrate",
        "board": args.board,
        "rms_px": res.rms,
        "epipolar_rms_px": res.epipolar_rms,
        "n_pairs_used": res.n_pairs_used,
    }
    path = to_opencv_yaml(res.rig, args.output, meta=meta)
    print(f"wrote {path}")

    if bool(args.verify_left) != bool(args.verify_right):
        fail("--verify-left and --verify-right must be given together")
    if args.verify_left:
        from al_dic_3d.calibration import verify_known_distance

        det_vl = detect_board(cv2.imread(args.verify_left, cv2.IMREAD_UNCHANGED), spec)
        det_vr = detect_board(cv2.imread(args.verify_right, cv2.IMREAD_UNCHANGED), spec)
        try:
            v = verify_known_distance(res.rig, det_vl, det_vr, spec)
        except ValueError as exc:
            fail(f"verification failed: {exc}")
        print(
            f"verify: pitch {v.pitch_measured:.4f} mm vs {v.pitch_true:g} mm | "
            f"scale error {v.scale_error:+.4%} | distance rmse {v.distance_rmse:.4f} mm | "
            f"plane rms {v.plane_rms:.4f} mm"
        )
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
    if command == "calibrate":
        return _calibrate_command(args)
    if command == "gui":
        try:
            from al_dic_3d.gui.app import main as gui_main
        except ImportError as exc:  # PySide6 missing
            print(f"the GUI requires PySide6: {exc}", file=sys.stderr)
            return 2
        return gui_main([])
    parser.error(f"unknown command: {command}")
    return 2
