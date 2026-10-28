"""A frame-1 ROI mask must not stop the tracking of material that leaves it (issue #1).

The 2D engine reads the mask of a frame that is never a reference only in its
crack-aware composition, where every node whose tracked position lands on a
masked pixel of that frame's mask dies. A mask drawn on frame 1 says nothing
about where the material is once the specimen has moved, yet the runner used
to repeat it on every frame: a dogbone translating ~70 px lost every gauge
node (GitHub issue #1, accumulative mode). The mask now goes to the reference
frames only, the 2D app's rule (``pipeline_controller._build_masks``), and so
does the crack barrier the right camera derives from the left ROI.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from al_dic_3d.matching.primitives import make_dicpara
from al_dic_3d.matching.temporal import (
    build_frame_schedule,
    build_grid_mesh,
    reference_frame_masks,
    temporal_track,
)


def _outline(shape=(8, 8)) -> np.ndarray:
    m = np.zeros(shape, dtype=np.float64)
    m[2:6, 2:6] = 1.0
    return m


def test_accumulative_masks_only_the_reference_frame():
    m = _outline()
    masks = reference_frame_masks(m, 4, "accumulative")
    assert len(masks) == 4
    assert masks[0] is m
    assert all(np.array_equal(masks[k], np.ones_like(m)) for k in (1, 2, 3))
    assert masks[1] is masks[2] is masks[3]  # one shared all-ones array, not n copies


def test_incremental_masks_every_reference_frame():
    m = _outline()
    masks = reference_frame_masks(m, 4, "incremental")
    assert masks[0] is masks[1] is masks[2] is m  # frames 0..2 are references
    assert np.array_equal(masks[3], np.ones_like(m))  # the last frame never is


def test_explicit_schedules_mask_their_reference_frames():
    m = _outline()
    custom = build_frame_schedule("incremental", 6, ref_update_mode="custom", ref_update_frames=[3])
    masks = reference_frame_masks(m, 6, "incremental", custom)
    assert [k for k in range(6) if masks[k] is m] == [0, 3]
    every_2 = build_frame_schedule("incremental", 6, ref_update_mode="every_n", ref_update_n=2)
    masks = reference_frame_masks(m, 6, "incremental", every_2)
    assert [k for k in range(6) if masks[k] is m] == [0, 2, 4]


# --- the engine mechanism: material moving out of a fixed outline -----------------

H, W = 180, 200
SHIFT_PX = 10  # rigid translation of the speckle, +x
PAD = SHIFT_PX + 10
# The frame-1 outline (inclusive pixel bounds). Tall enough that the engine does
# not shrink the FFT search below the motion (it caps the search by the ROI
# size: 60 px tall gave 14 px, this one 29 px).
X0, X1, Y0, Y1 = 50, 129, 30, 149


def _translating_frames() -> list[np.ndarray]:
    """A reference speckle frame and the same speckle moved ``SHIFT_PX`` px right."""
    from scipy.ndimage import gaussian_filter

    rng = np.random.default_rng(3)
    base = gaussian_filter(rng.standard_normal((H, W + 2 * PAD)), sigma=2.0)
    base = 20.0 + 215.0 * (base - base.min()) / (base.max() - base.min())
    return [
        np.ascontiguousarray(base[:, PAD - SHIFT_PX * k : PAD - SHIFT_PX * k + W]) for k in (0, 1)
    ]


def _track(masks_for):
    outline = np.zeros((H, W), dtype=np.float64)
    outline[Y0 : Y1 + 1, X0 : X1 + 1] = 1.0
    para = make_dicpara(
        img_size=(H, W),
        roi=(X0, X1, Y0, Y1),
        winsize=16,
        winstepsize=8,
        img_ref_mask=outline,
        fft_search=24,
    )
    mesh = build_grid_mesh(para, H, W)
    tf = temporal_track(_translating_frames(), mesh, para, masks=masks_for(outline))
    leaving = tf.ref_coords[:, 0] + SHIFT_PX > X1 + 0.5  # lands outside the outline
    assert leaving.any() and (~leaving).any()
    return tf, leaving


def test_nodes_that_leave_the_frame1_outline_keep_tracking():
    tf, leaving = _track(lambda outline: reference_frame_masks(outline, 2, "accumulative"))
    assert tf.valid[1].all()
    u = tf.u_accum[1][leaving]
    assert np.allclose(u[:, 0], SHIFT_PX, atol=0.05)
    assert np.allclose(u[:, 1], 0.0, atol=0.05)


def test_a_static_outline_on_every_frame_kills_them():
    # The scenario above really exercises the engine's crack-aware kill: the old
    # per-frame repetition of the outline loses exactly the nodes that left it.
    tf, leaving = _track(lambda outline: [outline, outline])
    assert not tf.valid[1][leaving].any()
    assert tf.valid[1][~leaving].all()


# --- the runner hands the strategy the reference-frame list -----------------------

cv2 = pytest.importorskip("cv2")


class _Captured(Exception):
    pass


def _left_masks_seen(cfg, monkeypatch) -> list:
    from al_dic_3d.matching.strategies import track_both
    from al_dic_3d.runner import run_pipeline

    seen: list = []

    def spy(self, seq, *args, **kwargs):
        seen.extend(seq.masks["L"])
        raise _Captured

    monkeypatch.setattr(track_both.TrackBothStrategy, "compute", spy)
    with pytest.raises(_Captured):
        run_pipeline(cfg)
    return seen


@pytest.mark.parametrize(
    ("mode", "masked_frames"), [("accumulative", [0]), ("incremental", [0, 1])]
)
def test_run_pipeline_gives_the_roi_mask_to_reference_frames_only(
    tmp_path, monkeypatch, mode, masked_frames
):
    from al_dic_3d.runner import load_config
    from tests import synth_stereo

    scene = synth_stereo.build_scene(tmp_path, n_frames=3)
    cfg = load_config(synth_stereo.write_config(tmp_path, scene))
    img = cv2.imread(str(tmp_path / "L_000.png"), cv2.IMREAD_UNCHANGED)
    disc = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.circle(disc, (110, 130), 55, 255, -1)
    cv2.imwrite(str(tmp_path / "roi_mask.png"), disc)
    cfg = replace(cfg, roi_mask=tmp_path / "roi_mask.png", roi=(0, 0, 0, 0), reference_mode=mode)

    masks = _left_masks_seen(cfg, monkeypatch)
    assert len(masks) == 3
    for k in range(3):
        if k in masked_frames:
            assert np.array_equal(masks[k] > 0.5, disc > 0), k
        else:
            assert np.all(np.asarray(masks[k]) == 1.0), k


def test_explicit_per_frame_masks_still_take_precedence(tmp_path, monkeypatch):
    from al_dic_3d.runner import load_config
    from tests import synth_stereo

    scene = synth_stereo.build_scene(tmp_path, n_frames=3)
    cfg = load_config(synth_stereo.write_config(tmp_path, scene))
    img = cv2.imread(str(tmp_path / "L_000.png"), cv2.IMREAD_UNCHANGED)
    full = np.full(img.shape[:2], 255, dtype=np.uint8)
    cv2.imwrite(str(tmp_path / "roi_mask.png"), full)
    for k in range(3):
        m = np.zeros(img.shape[:2], dtype=np.uint8)
        m[40 + k : 200, 40:200] = 255  # a different mask on every frame
        cv2.imwrite(str(tmp_path / f"mL_{k:03d}.png"), m)
    cfg = replace(cfg, roi_mask=tmp_path / "roi_mask.png", left_masks="mL_*.png")

    masks = _left_masks_seen(cfg, monkeypatch)
    rows = [int(np.argmax(np.asarray(m)[:, 100] > 0.5)) for m in masks]
    assert rows == [40, 41, 42]


# --- the right camera's derived crack barrier follows the same rule ---------------


@pytest.mark.parametrize(
    ("mode", "barrier_frames"), [("accumulative", [0]), ("incremental", [0, 1])]
)
def test_right_crack_barrier_goes_to_reference_frames_only(monkeypatch, mode, barrier_frames):
    import al_dic_3d.matching.strategies.track_both as tb
    from al_dic_3d.matching import get_strategy
    from al_dic_3d.matching.contracts import CorrespondenceConfig
    from al_dic_3d.sequence import ArrayFrameProvider, StereoSequence
    from tests.test_crack_batch_c import _stereo_scene

    left, right, rig, img = _stereo_scene(n_frames=3)
    para = make_dicpara(img_size=(img, img), roi=(45, img - 45, 45, img - 45), winstepsize=16)
    mesh_L = build_grid_mesh(para, img, img)
    crack = np.ones((img, img), dtype=np.float64)
    crack[:, img // 2 - 1 : img // 2 + 2] = 0.0
    seq = StereoSequence(
        providers={"L": ArrayFrameProvider(left), "R": ArrayFrameProvider(right)},
        masks={"L": reference_frame_masks(crack, 3, mode)},
    )
    right_masks: list = []
    real = tb.temporal_track

    def spy(frames, mesh, para, **kw):
        right_masks.append(kw.get("masks"))
        return real(frames, mesh, para, **kw)

    monkeypatch.setattr(tb, "temporal_track", spy)  # serial track_both: the right camera
    get_strategy("track_both")().compute(
        seq, rig, mesh_L, CorrespondenceConfig(strategy="track_both", reference_mode=mode)
    )
    (masks,) = right_masks
    assert len(masks) == 3
    for k in range(3):
        has_barrier = bool((np.asarray(masks[k]) < 0.5).any())
        assert has_barrier == (k in barrier_frames), k
