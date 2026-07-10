"""Perf batch P1.2: lazy path-backed frame/mask streams.

The load-bearing test is the eager-vs-lazy EQUIVALENCE: the full correspondence
pipeline must produce byte-identical results whether frames arrive as in-memory
arrays (ArrayFrameProvider) or stream from disk (LazyFrameProvider) — laziness
is a memory optimization, never a numerical one.
"""

from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d.sequence import (  # noqa: E402
    ArrayFrameProvider,
    LazyFrameProvider,
    LazyMaskList,
    StereoSequence,
    load_gray,
)
from tests import synth_stereo  # noqa: E402


def _write_frames(tmp_path, arrays):
    paths = []
    for i, a in enumerate(arrays):
        p = tmp_path / f"f_{i:03d}.png"
        cv2.imwrite(str(p), a.astype(np.uint16))
        paths.append(p)
    return paths


def test_lazy_provider_serves_raw_frames_and_shape(tmp_path):
    arrays = [np.full((6, 8), 100 * (i + 1), dtype=np.float64) for i in range(3)]
    paths = _write_frames(tmp_path, arrays)

    prov = LazyFrameProvider(paths)
    assert len(prov) == 3
    assert prov.shape == (6, 8)  # decoded lazily from frame 0
    for i, a in enumerate(arrays):
        got = prov.get_normalized(i)
        assert got.dtype == np.float64
        np.testing.assert_array_equal(got, a)  # RAW intensities, no normalization


def test_lazy_provider_lru_bounds_decodes(tmp_path, monkeypatch):
    arrays = [np.full((4, 4), i + 1, dtype=np.float64) for i in range(6)]
    paths = _write_frames(tmp_path, arrays)

    import al_dic_3d.sequence.lazy as lazy_mod

    calls: list[str] = []
    real = load_gray

    def counting(path):
        calls.append(str(path))
        return real(path)

    monkeypatch.setattr(lazy_mod, "load_gray", counting)
    prov = LazyFrameProvider(paths, capacity=2)

    prov.get_normalized(0)
    prov.get_normalized(0)  # hit
    assert len(calls) == 1
    prov.get_normalized(1)
    prov.get_normalized(0)  # still resident (capacity 2)
    assert len(calls) == 2
    prov.get_normalized(2)  # evicts 1
    prov.get_normalized(1)  # miss -> re-decode
    assert len(calls) == 4


def test_lazy_mask_list_serves_float64_contiguous(tmp_path):
    m = np.zeros((5, 7), dtype=np.uint8)
    m[1:4, 2:5] = 255
    paths = _write_frames(tmp_path, [m, m])

    masks = LazyMaskList(paths)
    assert len(masks) == 2
    got = masks[0]
    assert got.dtype == np.float64 and got.flags["C_CONTIGUOUS"]
    assert got[2, 3] == 255.0 and got[0, 0] == 0.0
    # Sequence protocol (StereoSequence.validate iterates the stream).
    assert len(list(masks)) == 2


def _correspondence(seq, rig, mesh_L, cfg_kwargs):
    from al_dic_3d.matching import CorrespondenceConfig, get_strategy

    strategy = get_strategy("track_both")(winsize=32, winstepsize=16)
    cfg = CorrespondenceConfig(strategy="track_both", **cfg_kwargs)
    return strategy.compute(seq, rig, mesh_L, cfg)


def test_eager_vs_lazy_full_pipeline_equivalence(tmp_path):
    """THE equivalence gate: eager arrays vs lazy provider, byte-identical."""
    from al_dic_3d.calibration import load_calibration
    from al_dic_3d.runner import build_reference_mesh

    synth_stereo.build_scene(tmp_path, n_frames=3)
    rig = load_calibration(tmp_path / "calib.yml", "opencv_yaml")

    left_paths = sorted(tmp_path.glob("L_*.png"))
    right_paths = sorted(tmp_path.glob("R_*.png"))
    assert len(left_paths) == 3 and len(right_paths) == 3

    lazy_seq = StereoSequence(
        providers={
            "L": LazyFrameProvider(left_paths),
            "R": LazyFrameProvider(right_paths),
        }
    )
    eager_seq = StereoSequence(
        providers={
            "L": ArrayFrameProvider([load_gray(p) for p in left_paths]),
            "R": ArrayFrameProvider([load_gray(p) for p in right_paths]),
        }
    )

    img_h, img_w = eager_seq.providers["L"].shape
    mesh_L = build_reference_mesh(img_h, img_w, (45, 175, 45, 215))
    cfg_kwargs = dict(disparity_offset=None, init_guess="fft")

    cs_eager = _correspondence(eager_seq, rig, mesh_L, cfg_kwargs)
    cs_lazy = _correspondence(lazy_seq, rig, mesh_L, cfg_kwargs)

    assert np.array_equal(cs_eager.xL, cs_lazy.xL, equal_nan=True)
    assert np.array_equal(cs_eager.xR, cs_lazy.xR, equal_nan=True)
    assert np.array_equal(cs_eager.quality, cs_lazy.quality, equal_nan=True)
    assert np.array_equal(cs_eager.source, cs_lazy.source)
    # And the tracks actually exist (an all-NaN == all-NaN pass would be hollow).
    assert np.isfinite(cs_lazy.xL).all(axis=2).any()

    # Reconstruction consumes only the (identical) correspondence, so the 3D
    # points are byte-identical too — assert the endpoint the user ships.
    from al_dic_3d.reconstruct import reconstruct_correspondence

    rec_eager = reconstruct_correspondence(cs_eager, rig)
    rec_lazy = reconstruct_correspondence(cs_lazy, rig)
    assert np.array_equal(rec_eager.points, rec_lazy.points, equal_nan=True)


def test_run_pipeline_streams_lazily(tmp_path, monkeypatch):
    """The runner path never materializes the full stack: decode count stays
    far below what eager double-loading (raw + engine-normalized) would need,
    while results still track (the honesty gate re-reads raw frames via the
    same LRU)."""
    import al_dic_3d.sequence.lazy as lazy_mod
    from al_dic_3d.runner import load_config, run_pipeline

    scene = synth_stereo.build_scene(tmp_path, n_frames=3)
    cfg = load_config(synth_stereo.write_config(tmp_path, scene))

    calls: list[str] = []
    real = load_gray

    def counting(path):
        calls.append(str(path))
        return real(path)

    monkeypatch.setattr(lazy_mod, "load_gray", counting)
    result = run_pipeline(cfg)
    assert result.meta["n_tracked_positions"] > 0
    # 3 frames x 2 cameras: a handful of re-decodes (stereo/seed/gate revisits)
    # is fine; an eager full materialization per consumer is not.
    assert len(calls) <= 6 * 4
