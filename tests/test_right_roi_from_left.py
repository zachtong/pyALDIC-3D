"""The right camera's region of interest is the left one seen through the frame-1 links.

With the ROI drawn on the left camera only, the right camera used to track the
whole bounding-box grid around its stereo links, background included. On a
low-texture background a few background nodes clipped the engine's FFT search,
the engine widened the search for every node up to half the image, and the
first deformed frame solved no node (1.2.1 dropped that frame; 1.1.0 aborted).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pytest

from al_dic_3d.matching.right_roi import RightReferenceMasks, derive_right_roi, right_camera_masks
from al_dic_3d.sequence import ArrayFrameProvider, StereoSequence

pytest.importorskip("cv2")


def _grid(x0, x1, y0, y1, step=8):
    xs, ys = np.meshgrid(
        np.arange(x0, x1 + 1, step, dtype=float), np.arange(y0, y1 + 1, step, dtype=float)
    )
    return np.column_stack([xs.ravel(), ys.ravel()])


def _strip_links(shape=(200, 240), disparity=(25.0, -3.0)):
    left = np.zeros(shape)
    left[40:161, 80:121] = 1.0  # a 41 px wide strip holding every node below
    coords = _grid(80, 120, 40, 160)
    right = coords + np.asarray(disparity) + 0.02 * (coords - coords.mean(axis=0))
    return left, coords, right


def _at(mask, pts):
    xi = np.clip(np.round(pts[:, 0]).astype(int), 0, mask.shape[1] - 1)
    yi = np.clip(np.round(pts[:, 1]).astype(int), 0, mask.shape[0] - 1)
    return mask[yi, xi]


def test_the_right_roi_covers_the_links_and_leaves_the_background_out():
    left, coords, right = _strip_links()
    roi = derive_right_roi(left, coords, right, left.shape)
    assert roi is not None and roi.dtype == np.float64
    assert set(np.unique(roi)) <= {0.0, 1.0}
    assert _at(roi, right).mean() == 1.0  # every linked node lies inside
    # the bounding box the right grid used to cover, 20 px outside the strip
    x0, y0 = right.min(axis=0) - 20
    x1, y1 = right.max(axis=0) + 20
    assert roi[int(y0), int(x0)] == 0.0 and roi[int(y1), int(x1)] == 0.0
    assert abs(roi.sum() - left.sum()) / left.sum() < 0.12  # same area, give or take the warp


def test_holes_in_the_left_roi_map_into_the_right_roi():
    left, coords, right = _strip_links()
    left[90:110, 92:110] = 0.0  # a hole inside the strip
    inside = np.ones(len(coords), bool)
    xi, yi = coords[:, 0].astype(int), coords[:, 1].astype(int)
    inside &= left[yi, xi] > 0
    roi = derive_right_roi(left, coords[inside], right[inside], left.shape)
    hole_centre = np.array([[101.0, 100.0]]) + (right - coords).mean(axis=0)
    assert _at(roi, hole_centre)[0] == 0.0


def test_without_a_left_mask_the_right_roi_is_the_hull_of_the_links():
    _, coords, right = _strip_links()
    roi = derive_right_roi(None, coords, right, (200, 240))
    assert _at(roi, right).mean() == 1.0
    assert roi[5, 5] == 0.0 and roi[195, 235] == 0.0


def test_degenerate_links_give_no_right_roi():
    pts = np.array([[10.0, 10.0], [20.0, 20.0], [np.nan, np.nan]])
    assert derive_right_roi(np.ones((50, 50)), pts, pts, (50, 50)) is None


def _seq(n, left_masks=None, right_masks=None, shape=(200, 240)):
    frames = ArrayFrameProvider([np.zeros(shape) for _ in range(n)])
    masks = {}
    if left_masks is not None:
        masks["L"] = left_masks
    if right_masks is not None:
        masks["R"] = right_masks
    return StereoSequence(providers={"L": frames, "R": frames}, masks=masks)


@pytest.mark.parametrize(
    ("mode", "refs"),
    [("accumulative", {0}), ("incremental", {0, 1, 2})],
)
def test_the_right_roi_applies_to_the_reference_frames_only(mode, refs):
    left, coords, right = _strip_links()
    seq = _seq(4, left_masks=[left] * 4)
    mask_r1, stream, note = right_camera_masks(seq, coords, right, reference_mode=mode)
    assert mask_r1 is not None and note
    assert len(stream) == 4
    for k in range(4):
        if k in refs:
            assert np.array_equal(stream[k], mask_r1), k
        else:
            assert stream[k].min() == 1.0, k


def test_explicit_right_masks_are_used_as_given():
    left, coords, right = _strip_links()
    own = [np.ones((200, 240)) * 0.0 + 1.0 for _ in range(3)]
    own[0][:10] = 0.0
    seq = _seq(3, left_masks=[left] * 3, right_masks=own)
    mask_r1, stream, note = right_camera_masks(seq, coords, right, reference_mode="accumulative")
    assert np.array_equal(mask_r1, own[0]) and note == ""
    assert np.array_equal(stream[0], own[0])


def test_per_frame_left_masks_are_warped_per_reference_frame():
    left, coords, right = _strip_links()
    later = np.zeros_like(left)
    later[40:160, 90:131] = 1.0  # the strip moved 10 px to the right
    seq = _seq(3, left_masks=[left, later, later])
    _, stream, _ = right_camera_masks(seq, coords, right, reference_mode="incremental")
    shift = (right - coords).mean(axis=0)
    probe = np.array([[125.0, 100.0]]) + shift  # inside the moved strip only
    assert _at(stream[0], probe)[0] == 0.0
    assert _at(stream[1], probe)[0] == 1.0


def test_the_stream_reuses_one_warp_for_a_shared_mask(monkeypatch):
    import al_dic_3d.matching.right_roi as rr

    left, coords, right = _strip_links()
    calls = []
    real = rr.derive_right_roi

    def spy(*a, **k):
        calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(rr, "derive_right_roi", spy)
    stream = RightReferenceMasks([left] * 5, coords, right, (200, 240), refs={0, 1, 2, 3})
    for k in range(5):
        stream[k]
    for k in range(5):
        stream[k]
    assert len(calls) == 1


class _FreshCopies(Sequence):
    """A mask stream that decodes a new array on every access, like LazyMaskList."""

    def __init__(self, masks):
        self._masks = masks

    def __len__(self):
        return len(self._masks)

    def __getitem__(self, idx):
        return np.array(self._masks[idx], copy=True)


def test_a_lazily_decoded_stream_warps_each_reference_frame_once(monkeypatch):
    import al_dic_3d.matching.right_roi as rr

    left, coords, right = _strip_links()
    calls = []
    real = rr.derive_right_roi

    def spy(*a, **k):
        calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(rr, "derive_right_roi", spy)
    stream = RightReferenceMasks(
        _FreshCopies([left] * 4), coords, right, (200, 240), refs={0, 1, 2}
    )
    for _ in range(5):  # the engine reads a reference mask several times per frame
        for k in range(4):
            stream[k]
    assert len(calls) == 3


def _wide_scene(step: int):
    """A narrow strip at full size: links on a step grid, a smooth disparity field."""
    shape = (640, 640)
    left = np.zeros(shape)
    left[80:561, 266:375] = 1.0
    coords = _grid(272, 368, 88, 552, step)
    right = coords + np.array([-40.0, 6.0]) + 0.03 * (coords - coords.mean(axis=0))
    return left, coords, right, shape


@pytest.mark.parametrize("step", [8, 16])
def test_the_rim_never_reads_as_a_crack(step):
    from al_dic_3d.matching.crack_mesh import mask_cuts_mesh
    from al_dic_3d.matching.primitives import make_dicpara
    from al_dic_3d.matching.right_roi import rim_width
    from al_dic_3d.matching.temporal import build_grid_mesh

    left, coords, right, shape = _wide_scene(step)
    roi = derive_right_roi(left, coords, right, shape, rim_px=rim_width(32, step))
    x0, y0 = np.floor(right.min(axis=0)).astype(int) - 32
    x1, y1 = np.ceil(right.max(axis=0)).astype(int) + 32
    para = make_dicpara(img_size=shape, roi=(x0, x1, y0, y1), winstepsize=step)
    assert not mask_cuts_mesh(build_grid_mesh(para, *shape), roi)


def test_a_crack_survives_the_rim():
    from al_dic_3d.matching.crack_mesh import mask_cuts_mesh
    from al_dic_3d.matching.primitives import make_dicpara
    from al_dic_3d.matching.temporal import build_grid_mesh

    left, coords, right, shape = _wide_scene(16)
    left[300:303, :] = 0.0  # a 3 px crack across the strip
    keep = left[coords[:, 1].astype(int), coords[:, 0].astype(int)] > 0
    roi = derive_right_roi(left, coords[keep], right[keep], shape, rim_px=16)
    x0, y0 = np.floor(right.min(axis=0)).astype(int) - 32
    x1, y1 = np.ceil(right.max(axis=0)).astype(int) + 32
    para = make_dicpara(img_size=shape, roi=(x0, x1, y0, y1), winstepsize=16)
    assert mask_cuts_mesh(build_grid_mesh(para, *shape), roi)


def test_a_hole_gets_a_rim_but_keeps_its_middle_out():
    left, coords, right, shape = _wide_scene(8)
    left[250:351, 290:351] = 0.0  # a 61 x 101 px hole, wider than twice the rim
    keep = left[coords[:, 1].astype(int), coords[:, 0].astype(int)] > 0
    roi = derive_right_roi(left, coords[keep], right[keep], shape, rim_px=16)
    shift = (right - coords).mean(axis=0)
    just_inside = np.array([[296.0, 300.0]]) + shift  # 6 px into the hole
    middle = np.array([[320.0, 300.0]]) + shift
    assert _at(roi, just_inside)[0] == 1.0 and _at(roi, middle)[0] == 0.0


def test_a_failed_warp_warns_and_keeps_the_whole_grid(monkeypatch):
    import al_dic_3d.viz3d.maskwarp as mw

    left, coords, right = _strip_links()

    def boom(*a, **k):
        raise RuntimeError("no warp")

    monkeypatch.setattr(mw, "warp_mask_left_to_right", boom)
    with pytest.warns(UserWarning, match="could not carry the region"):
        assert derive_right_roi(left, coords, right, left.shape) is None
    with pytest.warns(UserWarning, match="could not be carried"):
        mask_r1, stream, note = right_camera_masks(
            _seq(3, left_masks=[left] * 3), coords, right, reference_mode="accumulative"
        )
    assert mask_r1 is None and stream is None and note


@pytest.mark.parametrize(("winsize", "step"), [(32, 32), (16, 16)])
def test_coarse_node_steps_keep_the_outermost_links_accurate(tmp_path, winsize, step):
    """The rim keeps the next node ring, so links on the hull edge stay interpolated."""
    from dataclasses import replace

    from al_dic_3d.runner import load_config, run_pipeline
    from tests import synth_parity

    scene = synth_parity.build_parity_scene(tmp_path, img=320, n_frames=3, seed=7)
    cfg = replace(
        load_config(synth_parity.write_config(tmp_path, scene)),
        winsize=winsize,
        winstepsize=step,
        winsize_min=min(8, step),
    )
    res = run_pipeline(cfg)
    gt = synth_parity.gt_tracks(scene, res.ref_coords)
    P = res.reconstruction.points
    err = np.linalg.norm((P[-1] - P[0]) - (gt["world"][-1] - gt["world"][0]), axis=1)
    ref = res.ref_coords
    lo, hi = ref.min(axis=0), ref.max(axis=0)
    outer = (np.abs(ref - lo) < step / 2).any(axis=1) | (np.abs(ref - hi) < step / 2).any(axis=1)
    assert np.isfinite(err).all()
    assert np.percentile(err[outer], 90) < 1.3 * np.percentile(err[~outer], 90)


@pytest.mark.parametrize("mode", ["accumulative", "incremental"])
def test_left_only_roi_on_a_plain_background_keeps_the_first_deformed_frame(tmp_path, mode):
    """The reported set-up: before the fix frame 2 kept no point in either mode."""
    from al_dic_3d.runner import load_config, run_pipeline
    from tests.synth_strip import write_strip_dataset

    cfg = write_strip_dataset(
        tmp_path, img=640, width_px=108.0, length_px=480.0, reference_mode=mode
    )
    res = run_pipeline(load_config(cfg))
    valid = res.meta["summary"]["valid_frac"]
    assert min(valid) > 0.85, valid
