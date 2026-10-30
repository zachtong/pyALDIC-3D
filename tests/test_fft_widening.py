"""The engine's FFT search widenings are counted per frame and explained in the log.

al-dic widens its FFT initial-guess search (20 -> 42 -> ... px) whenever a
correlation peak lands on the search boundary, and says so only through
``logging`` — never reaching the GUI log. An incremental run whose frame-1
region no longer covers the moved specimen (no per-frame masks) widened on
every frame up to 702 px: about five times slower, with no reason given.
"""

from __future__ import annotations

import logging
import threading

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from al_dic_3d.matching.diagnostics import (
    RunSummary,
    frame_row,
    summarize_run,
    summary_lines,
    temporal_rows,
    widening_advice,
)
from al_dic_3d.matching.engine_log import ENGINE_LOGGER, record_fft_widening

cv2 = pytest.importorskip("cv2")

_RETRY = (
    "FFT peaks clipped at search boundary (%d nodes, max_disp=%.1f). "
    "Retry %d: search_region %d -> %d."
)
_CAP = (
    "FFT peaks still clipped (%d nodes, max_disp=%.1f); search_region hit hard cap "
    "%d (image half-size). Accepting result."
)


def _log(msg: str, *args) -> None:
    logging.getLogger(ENGINE_LOGGER).warning(msg, *args)


def test_the_recorder_keeps_the_widest_search_per_frame_of_its_own_thread():
    frame = [3]
    with record_fft_widening(lambda: frame[0]) as rec:
        _log(_RETRY, 9, 20.0, 1, 20, 42)
        _log(_RETRY, 4, 42.0, 2, 42, 86)
        frame[0] = 5
        _log(_CAP, 2, 350.0, 702)
        _log("Running FFT integer search for initial guess...")  # not a widening
        _log("FFT peaks clipped at search boundary (reworded)")  # no radius: ignored
        other = threading.Thread(target=_log, args=(_RETRY, 9, 20.0, 1, 20, 999))
        other.start()
        other.join()  # the other camera's track (parallel tracking)
    assert rec.widened == {3: 86, 5: 702}
    _log(_RETRY, 9, 20.0, 1, 20, 42)  # after the run: no longer recorded
    assert rec.widened == {3: 86, 5: 702}
    assert rec not in logging.getLogger(ENGINE_LOGGER).handlers


def _speckle(h: int, w: int) -> np.ndarray:
    f = gaussian_filter(np.random.default_rng(11).standard_normal((h, w)), 2.3, mode="nearest")
    return 20.0 + 215.0 * (f - f.min()) / (f.max() - f.min())


def _shift(img: np.ndarray, dx: float, dy: float) -> np.ndarray:
    h, w = img.shape
    m = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def test_a_large_increment_is_recorded_on_its_frame():
    from al_dic_3d.matching.primitives import make_local_dicpara
    from al_dic_3d.matching.temporal import build_grid_mesh, temporal_track

    h = w = 260
    f0 = _speckle(h, w)
    frames = [f0, _shift(f0, 1.5, 0.5), _shift(f0, 31.5, 0.5)]  # frame 2 jumps 30 px
    para = make_local_dicpara(
        img_size=(h, w), roi=(60, w - 60, 60, h - 60), winsize=32, reference_mode="incremental"
    )
    tf = temporal_track(frames, build_grid_mesh(para, h, w), para)
    assert tf.fft_widened == {2: 42}  # the reference switch at frame 2 widened 20 -> 42
    assert np.nanmedian(tf.u_accum[2][:, 0]) == pytest.approx(31.5, abs=0.05)  # and tracked

    rows = temporal_rows("L", tf)
    assert rows[2]["search_px"] == 42 and "search_px" not in rows[1]


def _summary(widened: dict[str, int], search: int = 702) -> RunSummary:
    return RunSummary(
        n_frames=10,
        n_pts=100,
        valid_frac=(1.0,) * 10,
        median_valid_frac=1.0,
        low_frames=(),
        all_empty=False,
        stereo_n_pts=None,
        stereo_n_valid=None,
        gated_by_cam={},
        fft_widened_by_cam=widened,
        fft_max_search_px=search,
    )


def test_the_summary_counts_widened_frames_per_camera():
    from types import SimpleNamespace

    rows = [frame_row(0, "stereo", 4, 4, note="frame-1 stereo match")]
    for k in (2, 3, 4):
        rows.append({**frame_row(k, "L", 4, 4), "search_px": 86 * (k - 1)})
    rows.append({**frame_row(2, "R", 4, 4), "search_px": 42})
    cs = SimpleNamespace(xL=np.zeros((5, 4, 2)), xR=np.zeros((5, 4, 2)), diagnostics=tuple(rows))
    s = summarize_run(cs)
    assert s.fft_widened_by_cam == {"L": 3, "R": 1}
    assert s.fft_max_search_px == 258
    meta = s.to_meta()
    assert meta["fft_widened_by_cam"] == {"L": 3, "R": 1} and meta["fft_max_search_px"] == 258


def test_repeated_widening_comes_with_advice():
    assert widening_advice(_summary({"L": 1})) == {}  # one widening (frame 1): normal
    assert widening_advice(_summary({"L": 5, "R": 2})) == {"L": 5}
    assert widening_advice(_summary({})) == {}

    no_masks = {"run_params": {"reference_mode": "incremental", "per_frame_masks": False}}
    text = " ".join(t for _, t in summary_lines(_summary({"L": 5}), stopped=no_masks))
    assert "5 frames" in text and "702 px" in text
    assert "per-frame masks" in text and "accumulative" in text

    masks = {"run_params": {"reference_mode": "incremental", "per_frame_masks": True}}
    text = " ".join(t for _, t in summary_lines(_summary({"L": 5}), stopped=masks))
    assert "fft_search" in text and "per-frame masks" not in text  # already given
