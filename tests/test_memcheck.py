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
