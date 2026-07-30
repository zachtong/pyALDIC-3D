"""Scale stress-test driver for pyALDIC-3D (batch G4, REPORT-ONLY).

Measures whether the software SURVIVES and how it SCALES on
hundreds-of-frames x 12-25 Mpx stereo sequences, and audits the memory
pre-check's honesty (projection vs measured peak RSS). Never modifies src/;
instrumentation that needs a hook uses log-only monkeypatching in THIS process.

Sub-commands
    gen           render a synthetic stress dataset (tools/stress_synth.py)
    run           instrumented IN-PROCESS pipeline run (RSS 1 Hz, per-frame
                  stage timing, optional cooperative cancel, GT sanity check,
                  optional .aldic3d save, optional animation export)
    spawn         plain `python -m al_dic_3d run <config>` SUBPROCESS run:
                  the honest CLI UX record (progress gaps, warnings, peak RSS)
    session-load  time + memory of loading a with-results .aldic3d bundle

All results land as JSON under --logs (plus an RSS timeline CSV per run).

Usage examples (conda env `pyaldic3d`):
    python tools/stress_test.py gen  --dir <scratch>/tierA --frames 150 --width 4000 --height 3000
    python tools/stress_test.py run  --config <scratch>/tierA/config.toml --tag tierA --gt
    python tools/stress_test.py spawn --config <scratch>/tierA/config.toml --tag tierA_cli
    python tools/stress_test.py run  --config <scratch>/tierB/config.toml --tag tierB_cancel --cancel-frac 0.6
    python tools/stress_test.py session-load --path <scratch>/tierA/session.aldic3d
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # tools/ (stress_synth)

GIB = 1024**3


# --- shared instrumentation -------------------------------------------------


class RssSampler:
    """1 Hz RSS/available-RAM sampler for a process (+children) via psutil.

    ``live_csv`` streams samples to disk as they are taken (heartbeat
    visibility for multi-hour endurance runs); ``write_csv`` still writes the
    complete timeline at the end.
    """

    def __init__(
        self, pid: int | None = None, interval: float = 1.0, live_csv: Path | None = None
    ) -> None:
        import psutil

        self._proc = psutil.Process(pid)
        self._psutil = psutil
        self.interval = interval
        self.samples: list[tuple[float, int, int]] = []  # (t, rss, sys_available)
        self.peak = 0
        self._t0 = time.perf_counter()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._live = live_csv.open("w", encoding="utf-8", buffering=1) if live_csv else None

    def _rss(self) -> int:
        try:
            total = self._proc.memory_info().rss
            for ch in self._proc.children(recursive=True):
                try:
                    total += ch.memory_info().rss
                except self._psutil.Error:
                    pass
            return total
        except self._psutil.Error:
            return 0

    def _loop(self) -> None:
        while not self._stop.is_set():
            rss = self._rss()
            avail = self._psutil.virtual_memory().available
            t = time.perf_counter() - self._t0
            self.samples.append((t, rss, avail))
            self.peak = max(self.peak, rss)
            if self._live is not None:
                self._live.write(f"{t:.1f},{rss},{avail}\n")
            self._stop.wait(self.interval)

    def __enter__(self) -> "RssSampler":
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._stop.set()
        self._thread.join(timeout=5)
        if self._live is not None:
            self._live.close()

    def write_csv(self, path: Path) -> None:
        with path.open("w", encoding="utf-8") as fh:
            fh.write("t_s,rss_bytes,sys_available_bytes\n")
            for t, rss, avail in self.samples:
                fh.write(f"{t:.1f},{rss},{avail}\n")


class EventLog:
    """Timestamped progress events, split by channel (main / L / R)."""

    def __init__(self, live_jsonl: Path | None = None) -> None:
        self._t0 = time.perf_counter()
        self.events: list[dict] = []
        self.frac = {"L": 0.0, "R": 0.0}
        self._lock = threading.Lock()
        self._live = live_jsonl.open("w", encoding="utf-8", buffering=1) if live_jsonl else None

    def now(self) -> float:
        return time.perf_counter() - self._t0

    def log(self, ch: str, frac: float, msg: str) -> None:
        with self._lock:
            e = {"t": round(self.now(), 3), "ch": ch, "frac": frac, "msg": msg}
            self.events.append(e)
            if self._live is not None:
                self._live.write(json.dumps(e) + "\n")
            if ch in self.frac:
                self.frac[ch] = max(self.frac[ch], frac)

    def overall_track_frac(self) -> float:
        return 0.5 * self.frac["L"] + 0.5 * self.frac["R"]

    def channel_times(self, ch: str, contains: str | None = None) -> list[float]:
        return [
            e["t"]
            for e in self.events
            if e["ch"] == ch and (contains is None or contains in e["msg"])
        ]

    def dump_jsonl(self, path: Path) -> None:
        with path.open("w", encoding="utf-8") as fh:
            for e in self.events:
                fh.write(json.dumps(e) + "\n")


def _stats(diffs: list[float]) -> dict:
    if not diffs:
        return {"n": 0}
    a = np.asarray(diffs)
    return {
        "n": int(a.size),
        "median_s": round(float(np.median(a)), 3),
        "mean_s": round(float(a.mean()), 3),
        "p95_s": round(float(np.percentile(a, 95)), 3),
        "max_s": round(float(a.max()), 3),
        "total_s": round(float(a.sum()), 1),
    }


def _per_frame_stats(times: list[float]) -> dict:
    return _stats([b - a for a, b in zip(times, times[1:])])


def _frame_start_times(events: list[dict], ch: str) -> list[float]:
    """First event timestamp per engine frame index on a channel.

    The engine emits several sub-stage ticks per frame ("Frame k/n: S4 done"
    ...); per-frame wall time is the diff between successive frames' FIRST
    ticks.
    """
    import re

    first: dict[int, float] = {}
    for e in events:
        if e["ch"] != ch:
            continue
        m = re.match(r"Frame (\d+)/", e["msg"])
        if m:
            first.setdefault(int(m.group(1)), e["t"])
    return [first[k] for k in sorted(first)]


# --- gen ----------------------------------------------------------------------


def cmd_gen(args) -> int:
    import stress_synth as ss

    spec = ss.SceneSpec(
        width=args.width, height=args.height, n_frames=args.frames, seed=args.seed
    )
    stats = ss.build_scene(args.dir, spec, workers=args.workers)
    cfg = ss.write_config(Path(args.dir), spec, winstepsize=args.step)
    stats["config"] = str(cfg)
    print(json.dumps(stats, indent=2))
    return 0


# --- run (in-process, instrumented) --------------------------------------------


def _patch_track_progress(elog: EventLog):
    """Log-only monkeypatch: forward engine per-frame progress from BOTH
    sequential temporal tracks into the event log (the sequential track_both
    path passes no progress callback of its own — see report). Behavior of the
    pipeline is unchanged; the injected callback only records timestamps."""
    import al_dic_3d.matching.strategies.track_both as tb

    orig = tb.temporal_track
    order = {"i": 0}

    def wrapped(frames, mesh, para, **kw):
        tag = "L" if order["i"] % 2 == 0 else "R"
        order["i"] += 1
        if kw.get("progress") is None:
            kw["progress"] = lambda f, m, _tag=tag: elog.log(_tag, float(f), str(m))
        return orig(frames, mesh, para, **kw)

    tb.temporal_track = wrapped
    return lambda: setattr(tb, "temporal_track", orig)


def _memcheck_projection(cfg, n_frames: int, img_h: int, img_w: int) -> dict:
    from al_dic_3d import memcheck

    xmin, xmax, ymin, ymax = cfg.roi
    step = max(1, cfg.winstepsize)
    n_pts_est = max(1, (max(0, xmax - xmin) // step + 1) * (max(0, ymax - ymin) // step + 1))
    projected = memcheck.estimate_peak_bytes(
        n_frames, img_h, img_w, 2, lazy=True, n_pts=n_pts_est, parallel=cfg.parallel_cameras
    )
    available = memcheck.available_ram_bytes() or 0
    return {
        "n_pts_est": n_pts_est,
        "projected_gb": round(projected / GIB, 2),
        "available_gb": round(available / GIB, 2),
        "budget_gb": round(0.7 * available / GIB, 2),
        "passes": projected <= 0.7 * available,
    }


def _draft_from_config(cfg, left_files: list[str], right_files: list[str]):
    from al_dic_3d.project.draft import ProjectDraft

    return ProjectDraft(
        calibration_file=cfg.calibration_file,
        calibration_format=cfg.calibration_format,
        left=list(left_files),
        right=list(right_files),
        roi=cfg.roi,
        strategy=cfg.strategy,
        reference_mode=cfg.reference_mode,
        winsize=cfg.winsize,
        winstepsize=cfg.winstepsize,
        stereo_search=cfg.stereo_search,
        init_guess=cfg.init_guess,
        seed_point=cfg.seed_point,
        seed_points=list(cfg.seed_points),
        use_global_step=cfg.use_global_step,
        admm_max_iter=cfg.admm_max_iter,
        fft_search=cfg.fft_search,
        output_dir=cfg.output_dir,
        output_prefix=cfg.output_prefix,
    )


def _gt_check(dataset_dir: Path, result) -> dict:
    """Median/95p tracking error vs the analytic scene GT on sampled frames."""
    import stress_synth as ss

    spec = ss.load_spec(dataset_dir)
    cs = result.correspondence
    n = cs.n_frames
    frames = sorted({1, n // 2, n - 1})
    gt = ss.gt_tracks(spec, result.ref_coords, frames)
    out = {}
    for i, k in enumerate(frames):
        valid = np.isfinite(cs.xL[k]).all(axis=1) & np.isfinite(cs.xR[k]).all(axis=1)
        row = {"coverage": round(float(valid.mean()), 4)}
        if valid.any():
            exl = np.linalg.norm(cs.xL[k][valid] - gt["xL"][i][valid], axis=1)
            exr = np.linalg.norm(cs.xR[k][valid] - gt["xR"][i][valid], axis=1)
            pts = result.reconstruction.points[k][valid]
            e3d = np.linalg.norm(pts - gt["world"][i][valid], axis=1)
            row.update(
                xL_med_px=round(float(np.median(exl)), 4),
                xL_p95_px=round(float(np.percentile(exl, 95)), 4),
                xR_med_px=round(float(np.median(exr)), 4),
                point_med_mm=round(float(np.median(e3d)), 4),
                point_p95_mm=round(float(np.percentile(e3d, 95)), 4),
            )
        out[f"frame_{k}"] = row
    return out


def _coverage_curve(cs) -> list[float]:
    valid = np.isfinite(cs.xL).all(axis=2) & np.isfinite(cs.xR).all(axis=2)
    return [round(float(v.mean()), 4) for v in valid]


def cmd_run(args) -> int:
    import faulthandler
    from dataclasses import replace

    from al_dic_3d.runner import load_config, run_pipeline, write_results

    logs = Path(args.logs)
    logs.mkdir(parents=True, exist_ok=True)
    # A native crash (access violation / abort) would otherwise kill the
    # process with NO trace — dump the stacks of all threads to a file.
    fault_file = (logs / f"{args.tag}_fault.log").open("w", encoding="utf-8")
    faulthandler.enable(file=fault_file, all_threads=True)
    cfg = load_config(args.config)

    if args.limit_frames:
        from al_dic_3d.runner import _resolve_paths

        left = [str(p) for p in _resolve_paths(cfg.left, cfg.base_dir)][: args.limit_frames]
        right = [str(p) for p in _resolve_paths(cfg.right, cfg.base_dir)][: args.limit_frames]
        cfg = replace(cfg, left=left, right=right, output_dir=cfg.output_dir / "pilot")

    elog = EventLog(live_jsonl=logs / f"{args.tag}_events_live.jsonl")
    unpatch = _patch_track_progress(elog)

    def progress(frac: float, msg: str) -> None:
        elog.log("main", float(frac), str(msg))

    stop = None
    cancel_state = {"tripped_at": None}
    if args.cancel_frac:

        def stop() -> bool:
            trip = elog.overall_track_frac() >= args.cancel_frac
            if trip and cancel_state["tripped_at"] is None:
                cancel_state["tripped_at"] = elog.now()
            return trip

    report: dict = {"tag": args.tag, "config": str(args.config), "cancel_frac": args.cancel_frac}
    t0 = time.perf_counter()
    with RssSampler(live_csv=logs / f"{args.tag}_rss_live.csv") as rss:
        baseline_rss = rss._rss()
        try:
            result = run_pipeline(cfg, progress=progress, stop=stop)
            error = None
        except Exception as exc:  # noqa: BLE001 - a crash IS a finding, capture it
            import traceback

            error = f"{type(exc).__name__}: {exc}"
            report["traceback"] = traceback.format_exc()
            result = None
        t_pipeline = time.perf_counter() - t0

        t_write = None
        out_sizes = {}
        if result is not None and not args.no_write:
            tw = time.perf_counter()
            paths = write_results(result, cfg, formats=("npz", "mat"))
            t_write = time.perf_counter() - tw
            out_sizes = {
                k: round(p.stat().st_size / 1024**2, 1)
                for k, p in paths.items()
                if p.is_file()
            }

        session_stats = None
        if result is not None and args.save_session:
            session_stats = _save_session(cfg, result, Path(args.save_session))

        anim_stats = None
        if result is not None and args.export_anim:
            anim_stats = _export_anim(cfg, result)

    unpatch()
    total = time.perf_counter() - t0

    n_frames = img_h = img_w = None
    if result is not None:
        n_frames = int(result.meta["n_frames"])
        img_h, img_w = result.meta["image_size"]
        report["meta"] = {
            k: result.meta[k]
            for k in (
                "n_frames", "n_pts", "n_tracked_positions", "stopped_early",
                "stopped_at_frame", "stop_reason", "crack_aware",
            )
        }
        report["diagnostics"] = result.meta.get("diagnostics")
        report["coverage_per_frame_sample"] = {
            "frame_1": _coverage_curve(result.correspondence)[1] if n_frames > 1 else None,
            "mid": _coverage_curve(result.correspondence)[n_frames // 2],
            "last": _coverage_curve(result.correspondence)[-1],
        }
        report["coverage_curve"] = _coverage_curve(result.correspondence)
        if args.gt:
            report["gt_errors"] = _gt_check(Path(args.config).parent, result)
    else:
        # memcheck numbers still useful on a crash
        try:
            from al_dic_3d.runner import _resolve_paths

            paths_l = _resolve_paths(cfg.left, cfg.base_dir)
            import cv2

            im = cv2.imread(str(paths_l[0]), cv2.IMREAD_GRAYSCALE)
            n_frames, (img_h, img_w) = len(paths_l), im.shape
        except Exception:  # noqa: BLE001
            pass

    if n_frames and img_h:
        report["memcheck"] = _memcheck_projection(cfg, n_frames, img_h, img_w)
        report["memcheck"]["measured_peak_rss_gb"] = round(rss.peak / GIB, 2)
        report["memcheck"]["baseline_rss_gb"] = round(baseline_rss / GIB, 2)
        if report["memcheck"]["projected_gb"] > 0:
            report["memcheck"]["peak_over_projection"] = round(
                (rss.peak - baseline_rss) / (report["memcheck"]["projected_gb"] * GIB), 2
            )

    report["error"] = error
    report["wall"] = {
        "pipeline_s": round(t_pipeline, 1),
        "write_results_s": None if t_write is None else round(t_write, 1),
        "total_s": round(total, 1),
    }
    report["output_sizes_mb"] = out_sizes
    if session_stats:
        report["session"] = session_stats
    if anim_stats:
        report["animation"] = anim_stats
    if cancel_state["tripped_at"] is not None:
        report["cancel_tripped_at_s"] = round(cancel_state["tripped_at"], 1)

    # stage timing from the event log
    tL, tR = elog.channel_times("L"), elog.channel_times("R")
    t_asm = elog.channel_times("main", contains="track_both frame")
    t_strain = elog.channel_times("main", contains="strain")
    stages = {}
    if tL:
        stages["setup_stereo_s"] = round(tL[0], 1)
        stages["track_L"] = _per_frame_stats(_frame_start_times(elog.events, "L"))
        stages["track_L_span_s"] = round(tL[-1] - tL[0], 1)
    if tR:
        stages["track_R"] = _per_frame_stats(_frame_start_times(elog.events, "R"))
        stages["track_R_span_s"] = round(tR[-1] - tR[0], 1)
        if tL:
            stages["gap_L_to_R_s"] = round(tR[0] - tL[-1], 1)
    if t_asm:
        stages["assembly_span_s"] = round(t_asm[-1] - t_asm[0], 1)
        if tR:
            stages["gap_R_to_assembly_s"] = round(t_asm[0] - tR[-1], 1)
    if t_strain:
        stages["strain"] = _per_frame_stats(t_strain)
        stages["strain_span_s"] = round(t_strain[-1] - t_strain[0], 1)
        if t_asm:
            stages["gap_assembly_to_strain_s"] = round(t_strain[0] - t_asm[-1], 1)
    report["stages"] = stages

    rss.write_csv(logs / f"{args.tag}_rss.csv")
    elog.dump_jsonl(logs / f"{args.tag}_events.jsonl")
    (logs / f"{args.tag}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("coverage_curve", "traceback", "diagnostics")}, indent=2))
    return 0 if error is None else 1


def _save_session(cfg, result, path: Path) -> dict:
    """Build an AppState3D around the finished run and save/size the bundle."""
    from al_dic_3d.project.session import estimated_result_nbytes, save_session
    from al_dic_3d.project.state import STEP_RESULTS, AppState3D
    from al_dic_3d.runner import _resolve_paths

    left = [str(p) for p in _resolve_paths(cfg.left, cfg.base_dir)]
    right = [str(p) for p in _resolve_paths(cfg.right, cfg.base_dir)]
    state = AppState3D(
        draft=_draft_from_config(cfg, left, right),
        config=cfg,
        result=result,
        workflow_step=STEP_RESULTS,
    )
    est = estimated_result_nbytes(result)
    t0 = time.perf_counter()
    save_session(state, path)
    dt = time.perf_counter() - t0
    return {
        "path": str(path),
        "estimated_uncompressed_gb": round(est / GIB, 2),
        "file_gb": round(path.stat().st_size / GIB, 3),
        "save_s": round(dt, 1),
    }


def _export_anim(cfg, result) -> dict:
    """Time a streaming MP4 animation export of U over the full sequence."""
    from al_dic_3d.export import make_timestamp
    from al_dic_3d.export.animation import export_animation
    from al_dic_3d.export.render import FieldImageConfig
    from al_dic_3d.runner import _resolve_paths

    left = [str(p) for p in _resolve_paths(cfg.left, cfg.base_dir)]
    ticks: list[float] = []
    t0 = time.perf_counter()
    paths = export_animation(
        cfg.output_dir,
        cfg.output_prefix,
        make_timestamp(),
        result,
        {"L": left},
        [FieldImageConfig(field_id="U")],
        cameras=("L",),
        fmt="mp4",
        fps=30,
        progress_cb=lambda done, tot, label: ticks.append(time.perf_counter() - t0),
    )
    dt = time.perf_counter() - t0
    return {
        "files": [str(p) for p in paths],
        "sizes_mb": [round(p.stat().st_size / 1024**2, 1) for p in paths if p.exists()],
        "wall_s": round(dt, 1),
        "frames": len(ticks),
        "s_per_frame": _stats([b - a for a, b in zip(ticks, ticks[1:])]),
    }


# --- spawn (plain CLI subprocess) ----------------------------------------------


def cmd_spawn(args) -> int:
    logs = Path(args.logs)
    logs.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "al_dic_3d", "run", str(args.config), "--formats", "npz,mat"]
    t0 = time.perf_counter()
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        encoding="utf-8", errors="replace", bufsize=1,
    )
    lines: list[tuple[float, str]] = []

    def reader() -> None:
        for line in proc.stdout:  # type: ignore[union-attr]
            lines.append((time.perf_counter() - t0, line.rstrip("\n")))

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    with RssSampler(proc.pid) as rss:
        code = proc.wait()
    th.join(timeout=10)
    total = time.perf_counter() - t0

    gaps = [(round(b - a, 1), round(a, 1)) for (a, _), (b, _) in zip(lines, lines[1:])]
    gaps.sort(reverse=True)
    report = {
        "tag": args.tag,
        "cmd": " ".join(cmd),
        "exit_code": code,
        "total_s": round(total, 1),
        "peak_rss_gb": round(rss.peak / GIB, 2),
        "n_stdout_lines": len(lines),
        "first_output_at_s": round(lines[0][0], 1) if lines else None,
        "top_silent_gaps_s": gaps[:5],
        "tail": [ln for _, ln in lines[-25:]],
    }
    rss.write_csv(logs / f"{args.tag}_rss.csv")
    with (logs / f"{args.tag}_stdout.log").open("w", encoding="utf-8") as fh:
        for t, ln in lines:
            fh.write(f"[{t:8.1f}s] {ln}\n")
    (logs / f"{args.tag}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


# --- session-load ----------------------------------------------------------------


def cmd_session_load(args) -> int:
    import psutil

    from al_dic_3d.project.session import load_session

    proc = psutil.Process()
    rss0 = proc.memory_info().rss
    t0 = time.perf_counter()
    state = load_session(args.path)
    dt = time.perf_counter() - t0
    rss1 = proc.memory_info().rss
    r = state.result
    report = {
        "path": str(args.path),
        "load_s": round(dt, 2),
        "rss_before_gb": round(rss0 / GIB, 2),
        "rss_after_gb": round(rss1 / GIB, 2),
        "rss_delta_gb": round((rss1 - rss0) / GIB, 2),
        "has_results": state.has_results,
        "n_frames": int(r.correspondence.n_frames) if r is not None else None,
        "n_pts": int(r.correspondence.n_pts) if r is not None else None,
        "has_strain": bool(r is not None and r.strain is not None),
        "stopped_early": bool(r.meta.get("stopped_early")) if r is not None else None,
    }
    print(json.dumps(report, indent=2))
    return 0


# --- CLI -----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="stress_test", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen", help="render a synthetic stress dataset")
    g.add_argument("--dir", required=True)
    g.add_argument("--frames", type=int, default=150)
    g.add_argument("--width", type=int, default=4000)
    g.add_argument("--height", type=int, default=3000)
    g.add_argument("--step", type=int, default=16, help="mesh winstepsize for config.toml")
    g.add_argument("--seed", type=int, default=11)
    g.add_argument("--workers", type=int, default=6)
    g.set_defaults(fn=cmd_gen)

    r = sub.add_parser("run", help="instrumented in-process pipeline run")
    r.add_argument("--config", required=True)
    r.add_argument("--tag", required=True)
    r.add_argument("--logs", default=str(Path.cwd() / "stress_logs"))
    r.add_argument("--limit-frames", type=int, default=0, help="pilot: first N frames only")
    r.add_argument("--cancel-frac", type=float, default=0.0, help="cooperative cancel at frac")
    r.add_argument("--gt", action="store_true", help="compare against analytic scene GT")
    r.add_argument("--no-write", action="store_true", help="skip write_results")
    r.add_argument("--save-session", default="", help="save a with-results .aldic3d here")
    r.add_argument("--export-anim", action="store_true", help="time an MP4 export of U")
    r.set_defaults(fn=cmd_run)

    s = sub.add_parser("spawn", help="plain CLI subprocess run (UX honesty record)")
    s.add_argument("--config", required=True)
    s.add_argument("--tag", required=True)
    s.add_argument("--logs", default=str(Path.cwd() / "stress_logs"))
    s.set_defaults(fn=cmd_spawn)

    sl = sub.add_parser("session-load", help="time/memory of loading a .aldic3d")
    sl.add_argument("--path", required=True)
    sl.set_defaults(fn=cmd_session_load)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
