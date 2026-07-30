"""Offscreen GUI stress measurements for pyALDIC-3D (batch G4, report-only).

Loads a with-results ``.aldic3d`` session into the REAL ``MainWindow3D`` under
the offscreen Qt platform (the test-suite pattern) and measures what a user
would feel at scale:

    - session load (Qt-free parse) + GUI adopt/resync (first result render)
    - frame-scrub latency across the whole sequence, cold then hot:
        * blocking time of ``signals.set_current_frame`` (the UI-thread stall)
        * settle time until the background decode prefetcher goes idle
    - strain-window open time on the full result
    - RSS at each milestone

Prints one JSON report to stdout. Run in a fresh process:
    python tools/stress_gui.py --session <path>.aldic3d --json out.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np  # noqa: E402

GIB = 1024**3


def _rss() -> float:
    import psutil

    return psutil.Process().memory_info().rss / GIB


def _pump(app, ms: int = 50) -> None:
    from PySide6.QtCore import QCoreApplication

    end = time.perf_counter() + ms / 1000.0
    while time.perf_counter() < end:
        QCoreApplication.processEvents()


def _scrub_pass(win, app, n_frames: int, order) -> dict:
    """One scrub sweep; returns per-frame blocking + settle latency stats."""
    prefetcher = win._canvas_area._prefetcher
    block, settle = [], []
    for k in order:
        t0 = time.perf_counter()
        win.signals.set_current_frame(int(k), n_frames)
        t1 = time.perf_counter()
        prefetcher.wait_idle(timeout_ms=15_000)
        _pump(app, 1)
        t2 = time.perf_counter()
        block.append(t1 - t0)
        settle.append(t2 - t0)
    ms = lambda a: {  # noqa: E731
        "median_ms": round(float(np.median(a)) * 1e3, 1),
        "p95_ms": round(float(np.percentile(a, 95)) * 1e3, 1),
        "max_ms": round(float(np.max(a)) * 1e3, 1),
    }
    return {"blocking": ms(block), "settle": ms(settle), "n": len(order)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--json", default="")
    ap.add_argument("--scrub-max", type=int, default=0, help="cap scrubbed frames (0 = all)")
    args = ap.parse_args(argv)

    report: dict = {"session": str(args.session), "rss_start_gb": round(_rss(), 2)}

    from al_dic_3d.project.session import load_session

    t0 = time.perf_counter()
    state = load_session(args.session)
    report["load_session_s"] = round(time.perf_counter() - t0, 2)
    report["rss_after_load_gb"] = round(_rss(), 2)
    n_frames = int(state.result.correspondence.n_frames) if state.result else 0
    report["n_frames"] = n_frames
    report["n_pts"] = int(state.result.correspondence.n_pts) if state.result else 0

    from al_dic_3d.gui.app import create_app
    from al_dic_3d.gui.main_window import MainWindow3D

    app = create_app([])
    t0 = time.perf_counter()
    win = MainWindow3D()
    win.show()
    win.controller.adopt_state(state)
    win._resync_all()  # emits results_changed -> first result render
    _pump(app, 200)
    report["gui_adopt_first_render_s"] = round(time.perf_counter() - t0, 2)
    report["rss_after_gui_gb"] = round(_rss(), 2)

    # jump to the Results step like a reopened project would
    win.controller.goto(6)
    _pump(app, 50)

    order = list(range(n_frames))
    if args.scrub_max and n_frames > args.scrub_max:
        order = list(np.linspace(0, n_frames - 1, args.scrub_max).astype(int))
    t0 = time.perf_counter()
    report["scrub_cold"] = _scrub_pass(win, app, n_frames, order)
    report["scrub_cold_total_s"] = round(time.perf_counter() - t0, 1)
    t0 = time.perf_counter()
    report["scrub_hot"] = _scrub_pass(win, app, n_frames, list(reversed(order)))
    report["scrub_hot_total_s"] = round(time.perf_counter() - t0, 1)
    report["rss_after_scrub_gb"] = round(_rss(), 2)

    # strain window on the full result
    t0 = time.perf_counter()
    win._open_strain_window()
    _pump(app, 300)
    report["strain_window_open_s"] = round(time.perf_counter() - t0, 2)
    sw = win._strain_window
    report["strain_window_visible"] = bool(sw is not None and sw.isVisible())
    report["rss_after_strain_gb"] = round(_rss(), 2)

    # scrub inside the strain window (its own navigator)
    if sw is not None and n_frames > 1:
        lat = []
        for k in order[: min(len(order), 30)]:
            t0 = time.perf_counter()
            sw._on_frame_nav(int(k))  # the navigator's frame_changed handler
            _pump(app, 1)
            lat.append(time.perf_counter() - t0)
        if lat:
            report["strain_scrub"] = {
                "median_ms": round(float(np.median(lat)) * 1e3, 1),
                "p95_ms": round(float(np.percentile(lat, 95)) * 1e3, 1),
                "n": len(lat),
            }

    win.close()
    _pump(app, 100)

    out = json.dumps(report, indent=2)
    print(out)
    if args.json:
        Path(args.json).write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
