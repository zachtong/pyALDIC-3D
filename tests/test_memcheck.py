"""Perf batch P1.4: fail-fast RAM pre-check (estimator + runner integration)."""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d import memcheck


def test_lazy_estimate_is_flat_in_frames_eager_is_not():
    lazy_20 = memcheck.estimate_peak_bytes(20, 2048, 2448, 2, lazy=True, n_pts=20000)
    lazy_200 = memcheck.estimate_peak_bytes(200, 2048, 2448, 2, lazy=True, n_pts=20000)
    eager_200 = memcheck.estimate_peak_bytes(200, 2048, 2448, 2, lazy=False, n_pts=20000)

    # Lazy grows only through the per-(frame, point) results, never the stacks.
    assert lazy_200 < 4 * lazy_20
    # The eager 200-frame 5 Mpx stereo case is the ~32 GB OOM scenario; lazy
    # must project a small fraction of it (the point of batch P1).
    assert eager_200 > 30 * 1024**3
    assert lazy_200 < eager_200 / 5


def test_check_raises_actionable_error(monkeypatch):
    monkeypatch.setattr(memcheck, "available_ram_bytes", lambda: 1024**2)  # 1 MB
    with pytest.raises(ValueError) as exc:
        memcheck.check_run_memory(200, 2048, 2448, 2, lazy=True, n_pts=20000)
    msg = str(exc.value)
    assert "Projected peak memory" in msg and "GB" in msg
    assert "ignore_memory_check" in msg  # the override is spelled out


def test_check_skips_when_ram_unknown(monkeypatch):
    monkeypatch.setattr(memcheck, "available_ram_bytes", lambda: None)
    memcheck.check_run_memory(10**6, 10**4, 10**4, 2)  # absurd run, no probe -> no raise


def test_available_ram_probe_returns_plausible_value():
    avail = memcheck.available_ram_bytes()
    if avail is None:  # non-Windows without psutil: probe is allowed to opt out
        pytest.skip("RAM probe unsupported on this platform")
    assert 256 * 1024**2 < avail < 16 * 1024**4  # between 256 MB and 16 TB


def test_load_config_parses_ignore_memory_check(tmp_path):
    from al_dic_3d.runner import load_config

    (tmp_path / "calib.yml").write_text("", encoding="utf-8")
    (tmp_path / "config.toml").write_text(
        """
[calibration]
file = "calib.yml"
format = "opencv_yaml"
[sequence]
left = "L_*.png"
right = "R_*.png"
[roi]
xmin = 0
xmax = 10
ymin = 0
ymax = 10
[advanced]
ignore_memory_check = true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    assert load_config(tmp_path / "config.toml").ignore_memory_check is True


def test_run_pipeline_fails_fast_and_override_runs(tmp_path, monkeypatch):
    cv2 = pytest.importorskip("cv2")  # noqa: F841 - synthetic scene needs cv2
    from dataclasses import replace

    from al_dic_3d.runner import load_config, run_pipeline
    from tests import synth_stereo

    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    cfg = load_config(synth_stereo.write_config(tmp_path, scene))

    # Starve the probe: the pre-check must reject the run BEFORE any tracking.
    monkeypatch.setattr(memcheck, "available_ram_bytes", lambda: 1024**2)
    with pytest.raises(ValueError, match="Projected peak memory"):
        run_pipeline(cfg)

    # The documented override lets the same run proceed to a real result.
    result = run_pipeline(replace(cfg, ignore_memory_check=True))
    assert result.meta["n_tracked_positions"] > 0
    assert np.isfinite(result.reconstruction.points[0]).any()


# Peaks measured by the 2026-11-26 audit (peak working set, GiB) and the run
# geometry: (img_h, img_w, nodes, frames, incremental, peak). Synthetic 5 / 12
# Mpx scenes and a real 5 Mpx notched specimen, track_both, default engine.
MEASURED_PEAKS = {
    "5mp ws32 acc": (1944, 2592, 11532, 20, False, 2.46),
    "5mp ws24 step8 acc": (1944, 2592, 45695, 20, False, 4.12),
    "12mp ws32 acc": (3000, 4000, 27170, 20, False, 5.32),
    "12mp ws24 step8 acc": (3000, 4000, 108300, 20, False, 9.40),
    "12mp ws32 acc 50 frames": (3000, 4000, 27170, 50, False, 5.42),
    "real 5mp ws24 step8 acc": (2448, 2048, 37230, 12, False, 3.65),
    "5mp ws32 inc 5 frames": (1944, 2592, 11532, 5, True, 4.14),
    "5mp ws32 inc": (1944, 2592, 11532, 20, True, 4.19),
    "12mp ws24 step8 inc": (3000, 4000, 108300, 10, True, 18.88),
    "real 5mp ws24 step8 inc": (2448, 2048, 39260, 12, True, 6.94),
}


@pytest.mark.parametrize("name", sorted(MEASURED_PEAKS))
def test_the_projection_covers_every_measured_peak(name):
    h, w, nodes, frames, inc, peak = MEASURED_PEAKS[name]
    projected = (
        memcheck.estimate_peak_bytes(frames, h, w, 2, lazy=True, n_pts=nodes, incremental=inc)
        / 1024**3
    )
    # Above the measured peak, and not so far above that it refuses runs that fit.
    assert peak <= projected <= 1.2 * peak, (name, round(projected, 2))


def test_a_16_gb_pc_is_stopped_before_a_dense_incremental_run(monkeypatch):
    # 12 Mpx, winsize 24 / step 8, incremental: 18.9 GB measured; the old
    # projection (5.0 GB) let it start on a PC with 16 GB free, which then swaps.
    monkeypatch.setattr(memcheck, "available_ram_bytes", lambda: 16 * 1024**3)
    with pytest.raises(memcheck.MemoryBudgetError, match="Projected peak memory"):
        memcheck.check_run_memory(10, 3000, 4000, 2, n_pts=108300, incremental=True)
    # The same run tracked accumulatively (9.4 GB) is let through on 16 GB free.
    memcheck.check_run_memory(10, 3000, 4000, 2, n_pts=108300, incremental=False)
