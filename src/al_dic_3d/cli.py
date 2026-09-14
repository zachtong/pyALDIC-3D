"""Command-line interface for pyALDIC-3D.

Exposes ``--version``, the Phase-1 ``run`` sub-command (a headless
``config.toml`` -> ``.npz`` + ``.mat`` pipeline), ``gui``, and the D12
``calibrate`` sub-command (board image pairs -> QC'd stereo calibration ->
OpenCV YAML), ``demo`` (a synthetic dataset to try the pipeline on, see
:mod:`al_dic_3d.synthetic`) and ``self-test`` (the installation / frozen-bundle
check, see :mod:`al_dic_3d.self_test`). Further sub-commands land as their backing
modules arrive; the ``subparsers`` handle is the reserved seam. The heavy
lifting lives in :mod:`al_dic_3d.runner` / :mod:`al_dic_3d.calibration` so it
stays unit-testable without a subprocess.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from al_dic_3d import __version__

# ``demo`` defaults: small enough to write in about a second and to run in a few
# seconds once the kernels are compiled.
_DEMO_FRAMES = 4
_DEMO_SIZE = 320
_DEMO_FRAMES_RANGE = (2, 100)
_DEMO_SIZE_RANGE = (160, 2048)


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

    gui_p = subparsers.add_parser(
        "gui",
        help="launch the graphical workflow (requires PySide6)",
        description="Open the pyALDIC-3D desktop application.",
    )
    gui_p.add_argument(
        "session",
        nargs="?",
        metavar="SESSION",
        help="optional .aldic3d project to open at startup",
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

    demo_p = subparsers.add_parser(
        "demo",
        help="write a small synthetic stereo dataset (images, calibration, config.toml)",
        description=(
            "Write a synthetic stereo-DIC dataset with analytic ground truth into OUT: "
            "a distorted 18 deg convergent camera pair viewing a tilted speckle plane "
            "under a known deformation, its OpenCV calibration YAML and a ready "
            "config.toml. Then run 'al-dic-3d run OUT/config.toml', or pass --run."
        ),
    )
    demo_p.add_argument("out", metavar="OUT", help="folder to write into (created if missing)")
    demo_p.add_argument(
        "--frames",
        type=int,
        default=_DEMO_FRAMES,
        metavar="N",
        help=f"frames per camera, {_DEMO_FRAMES_RANGE[0]}-{_DEMO_FRAMES_RANGE[1]} "
        f"(default {_DEMO_FRAMES})",
    )
    demo_p.add_argument(
        "--size",
        type=int,
        default=_DEMO_SIZE,
        metavar="PX",
        help=f"square image size in pixels, {_DEMO_SIZE_RANGE[0]}-{_DEMO_SIZE_RANGE[1]} "
        f"(default {_DEMO_SIZE})",
    )
    demo_p.add_argument(
        "--run",
        action="store_true",
        help="also run the pipeline and report the accuracy against the ground truth",
    )

    st_p = subparsers.add_parser(
        "self-test",
        help="check that this installation works end to end",
        description=(
            "Check the packaged data, Qt, the translations, numba, file I/O in a "
            "non-ASCII folder, the video/GIF writers, the colorbar, session save/load, "
            "an offscreen 3D render and a mini stereo run. One line per check; exit "
            "code 0 when nothing failed. ALDIC3D_SELFTEST_SKIP_GL=1 skips the render."
        ),
    )
    st_p.add_argument("--json", metavar="PATH", help="also write a UTF-8 JSON report to PATH")

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
            _say(f"  [{frac * 100:5.1f}%] {msg}")

    # Fix batch V: the first Ctrl+C asks the pipeline to stop at its next
    # cooperative checkpoint and KEEPS the finished frames (the partial-results
    # contract the GUI already used); a second Ctrl+C aborts outright.
    import signal
    import threading

    stop_event = threading.Event()

    def _on_sigint(signum, frame):  # noqa: ARG001
        if stop_event.is_set():
            raise KeyboardInterrupt
        stop_event.set()
        print(
            "\ninterrupt: finishing the current frame and keeping the finished ones; "
            "if the first camera was still tracking, the second camera is tracked over the "
            "kept frames first (press Ctrl+C again to abort)",
            file=sys.stderr,
        )

    previous = signal.signal(signal.SIGINT, _on_sigint)
    try:
        try:
            result = run_pipeline(
                cfg, progress=progress, stop=stop_event.is_set, complete_partial=True
            )
        except RuntimeError as exc:
            if stop_event.is_set() and str(exc) == "cancelled":
                print("interrupted before any frame finished: nothing to write", file=sys.stderr)
                return 130
            raise
    finally:
        signal.signal(signal.SIGINT, previous)

    write_errors: list[str] = []
    paths = write_results(result, cfg, formats=formats, errors=write_errors)

    m = result.meta
    total = int(m["n_frames"]) * int(m["n_pts"])
    print(
        f"strategy={m['strategy']} frames={m['n_frames']} points={m['n_pts']} "
        f"tracked={m['n_tracked_positions']}/{total}"
    )

    # F3.1: post-run failure accounting — every silent kill becomes a line.
    from al_dic_3d.matching.diagnostics import summarize_run, summary_lines

    summary = summarize_run(
        result.correspondence, result.reconstruction.points, n_eligible=m.get("n_pts_in_roi")
    )
    for level, msg in summary_lines(summary, m.get("gates"), stopped=m):
        if level in ("warning", "error"):
            _say(f"{level}: {msg}", err=True)
        else:
            _say(msg)

    for key in ("params", *formats):
        if key in paths:
            _say(f"wrote {paths[key]}")
    for err in write_errors:
        _say(f"error: could not write {err}", err=True)
    if write_errors:
        return 1
    if m.get("stopped_early"):
        print(
            f"interrupted: kept frames [0, {m.get('stopped_at_frame')}); later frames are empty",
            file=sys.stderr,
        )
        return 130
    # An all-empty result is a failure even though the pipeline ran to the end.
    return 1 if summary.all_empty else 0


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

    from al_dic_3d.calibration import calibrate_stereo, detect_board, summarize, to_opencv_yaml
    from al_dic_3d.pathsafe import imread_unicode

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
            img = imread_unicode(f)
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

    first = imread_unicode(left_files[0])
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

        det_vl = detect_board(imread_unicode(args.verify_left), spec)
        det_vr = detect_board(imread_unicode(args.verify_right), spec)
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


# Typographic characters the compute layer's English messages use, spelled in
# ASCII for the terminal (fix batch V: an em dash came out as mojibake when the
# output was redirected to a file, and crashed a console on code page 437).
_PLAIN = str.maketrans(
    {"\u2014": "-", "\u2013": "-", "\u2192": "->", "\u00d7": "x", "\u00b5": "u",
     "\u2026": "...", "\u2264": "<=", "\u2265": ">=", "\u2212": "-"}
)  # fmt: skip


def _say(text: str, *, err: bool = False) -> None:
    """Print pipeline text in plain ASCII punctuation (paths still escaped safely)."""
    _echo(str(text).translate(_PLAIN), err=err)


def _echo(text: str, *, err: bool = False) -> None:
    """Print a line; a console that cannot encode it (a path) gets it escaped, never a crash."""
    stream = sys.stderr if err else sys.stdout
    if stream is None:
        return
    try:
        print(text, file=stream, flush=True)
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "ascii"
        print(text.encode(encoding, "backslashreplace").decode(encoding), file=stream, flush=True)


def _quote(path: Path) -> str:
    """``path`` quoted (only when needed) for pasting into this platform's shell."""
    if sys.platform == "win32":
        import subprocess

        return subprocess.list2cmdline([str(path)])
    import shlex

    return shlex.quote(str(path))


def _demo_command(args: argparse.Namespace) -> int:
    """Handle ``al-dic-3d demo OUT`` (synthetic dataset; ``--run`` also runs it)."""
    from al_dic_3d import synthetic

    for flag, value, (lo, hi) in (
        ("--frames", args.frames, _DEMO_FRAMES_RANGE),
        ("--size", args.size, _DEMO_SIZE_RANGE),
    ):
        if not lo <= value <= hi:
            _echo(f"error: {flag} must be between {lo} and {hi}, got {value}", err=True)
            return 2
    out = Path(args.out).expanduser()
    if out.exists() and not out.is_dir():
        _echo(f"error: {out} exists and is not a folder", err=True)
        return 2
    if out.is_dir() and any(out.iterdir()) and not synthetic.is_synthetic_dataset(out):
        # Never write calib.yml / config.toml over somebody's project.
        _echo(
            f"error: {out} is not empty; choose a new folder (only an earlier demo "
            "folder is rewritten)",
            err=True,
        )
        return 2
    try:
        # Rewriting an earlier demo: drop its frames beyond the new count, so the
        # folder holds exactly the dataset the new config.toml describes.
        for stale in synthetic.frame_files(out, first=args.frames):
            stale.unlink()
        scene = synthetic.build_scene(out, img=args.size, n_frames=args.frames)
        synthetic.write_config(
            out, scene, prefix="demo", explicit_files=True, output_dir="results", strain=True
        )
    except (OSError, ValueError) as exc:
        _echo(f"error: could not write the demo dataset: {exc}", err=True)
        return 1
    config = out / synthetic.CONFIG_NAME  # spelled the way the user gave OUT
    _echo(f"wrote a synthetic stereo dataset to {out}")
    _echo(
        f"  {args.frames} frames per camera, {args.size}x{args.size} px, "
        f"{synthetic.RIG_ANGLE_DEG:g} deg convergent rig with lens distortion; "
        "a tilted speckle plane under a known deformation"
    )
    _echo(
        f"  {synthetic.CALIB_NAME} (OpenCV YAML), {scene['left'][0]} ... "
        f"{scene['right'][-1]}, {synthetic.CONFIG_NAME}"
    )
    if not args.run:
        _echo("next, run the pipeline on it:")
        _echo(f"  al-dic-3d run {_quote(config)}")
        return 0
    return _run_demo(config, scene)


def _run_demo(config: Path, scene: dict) -> int:
    """``demo --run``: run the pipeline on the dataset and report its accuracy."""
    from al_dic_3d import synthetic
    from al_dic_3d.runner import load_config, run_pipeline, write_results

    _echo(f"running: al-dic-3d run {_quote(config)}")
    _echo("  (the first run on a new installation also compiles its kernels)")

    def progress(frac: float, msg: str) -> None:
        _echo(f"  [{frac * 100:5.1f}%] {msg}")

    errors: list[str] = []
    try:
        cfg = load_config(config)
        result = run_pipeline(cfg, progress=progress)
        paths = write_results(result, cfg, formats=("npz", "mat"), errors=errors)
        acc = synthetic.accuracy_summary(result, scene)
    except Exception as exc:  # noqa: BLE001 - a first-run check reports, it does not crash
        _echo(f"error: the demo run failed: {type(exc).__name__}: {exc}", err=True)
        _echo("  run 'al-dic-3d self-test' to check this installation", err=True)
        return 1
    _echo(
        "accuracy vs analytic ground truth: 3D displacement error median "
        f"{acc['disp_median_mm'] * 1000:.1f} um, p90 {acc['disp_p90_mm'] * 1000:.1f} um; "
        f"coverage {acc['coverage_min']:.0%} ({int(acc['n_points'])} points x "
        f"{int(acc['n_frames'])} frames)"
    )
    for key in ("params", "npz", "mat"):
        if key in paths:
            _echo(f"wrote {paths[key]}")
    for err in errors:
        _echo(f"error: could not write {err}", err=True)
    return 1 if errors or not acc["coverage_min"] > 0 else 0


def normalize_argv(argv: list[str]) -> list[str]:
    """Rewrite a bare ``SESSION.aldic3d`` first argument to ``gui SESSION`` (Q6).

    The Windows file association launches ``python -m al_dic_3d "<file>"``
    (the 2D pattern); a session path is not a sub-command, so it is folded
    into the ``gui`` sub-command here.
    """
    if argv and argv[0].lower().endswith(".aldic3d"):
        return ["gui", *argv]
    return argv


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(normalize_argv(sys.argv[1:] if argv is None else list(argv)))
    command = getattr(args, "command", None)
    if command is None:
        parser.print_help()
        return 0
    if command == "run":
        return _run_command(args)
    if command == "calibrate":
        return _calibrate_command(args)
    if command == "demo":
        return _demo_command(args)
    if command == "self-test":
        from al_dic_3d.self_test import run_self_test

        return run_self_test(json_path=args.json)
    if command == "gui":
        try:
            from al_dic_3d.gui.app import main as gui_main
        except ImportError as exc:  # PySide6 missing
            print(f"the GUI requires PySide6: {exc}", file=sys.stderr)
            return 2
        return gui_main([args.session] if getattr(args, "session", None) else [])
    parser.error(f"unknown command: {command}")
    return 2
