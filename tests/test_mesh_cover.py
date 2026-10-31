"""Incremental reference frames whose masks move get a grid that covers them.

al-dic 1.0.4 trims a caller's mesh from its untrimmed copy at every reference
frame, so cells a narrower mask removed come back. The mesh is still a fixed
pixel lattice: material that a later reference mask places outside it has no
cells to be tracked in (a notched specimen pulled 400 px lost most points in
an incremental run with per-frame masks). The grid ROI is therefore extended
to the union of the reference masks, by whole grid steps, so the frame-1 nodes
stay exactly where they were.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.matching.mesh_cover import cover_roi, map_box_affine, masks_bbox
from al_dic_3d.matching.primitives import make_dicpara
from al_dic_3d.matching.temporal import build_grid_mesh

H, W = 240, 320
STEP, WIN = 8, 16


def _nodes(roi) -> set[tuple[float, float]]:
    para = make_dicpara(img_size=(H, W), roi=roi, winsize=WIN, winstepsize=STEP)
    return {tuple(p) for p in np.asarray(build_grid_mesh(para, H, W).coordinates_fem)}


def test_the_frame1_nodes_stay_and_the_union_is_covered():
    roi = (100, 181, 90, 151)
    cover = (60, 230, 70, 190)
    new = cover_roi(roi, cover, step=STEP, winsize=WIN, img_shape=(H, W))
    assert _nodes(roi) <= _nodes(new)  # nothing moved, rings were added
    xs = np.array([p[0] for p in _nodes(new)])
    ys = np.array([p[1] for p in _nodes(new)])
    # Every pixel of the cover lies within half a step of the grid's extent.
    assert xs.min() <= cover[0] + STEP / 2 and xs.max() >= cover[1] - STEP / 2
    assert ys.min() <= cover[2] + STEP / 2 and ys.max() >= cover[3] - STEP / 2


def test_it_never_shrinks_and_ignores_a_cover_inside():
    roi = (100, 181, 90, 151)
    assert cover_roi(roi, (120, 150, 100, 140), step=STEP, winsize=WIN, img_shape=(H, W)) == roi
    assert cover_roi(roi, None, step=STEP, winsize=WIN, img_shape=(H, W)) == roi


def test_at_the_image_border_it_stops_short_and_keeps_the_nodes():
    roi = (100, 181, 90, 151)
    new = cover_roi(roi, (0, W - 1, 0, H - 1), step=STEP, winsize=WIN, img_shape=(H, W))
    assert _nodes(roi) <= _nodes(new)
    half = WIN // 2
    assert new[0] >= half and new[1] <= W - 1 - half
    assert new[2] >= half and new[3] <= H - 1 - half


def test_only_the_reference_frames_count():
    masks = [np.zeros((H, W)) for _ in range(4)]
    masks[0][50:60, 40:70] = 1
    masks[1][10:20, 200:210] = 1  # not a reference frame: ignored
    masks[2][100:150, 30:45] = 1
    assert masks_bbox(masks, {0, 2}) == (30, 69, 50, 149)
    assert masks_bbox([np.zeros((H, W))], {0}) is None


def test_a_box_maps_through_the_frame1_links():
    rng = np.random.default_rng(0)
    src = rng.uniform(50, 200, (40, 2))
    A = np.array([[0.9, 0.05], [-0.04, 1.02]])
    t = np.array([35.0, -12.0])
    dst = src @ A.T + t
    box = map_box_affine((60, 160, 70, 180), src, dst)
    corners = np.array([[60, 70], [160, 70], [60, 180], [160, 180]], dtype=float) @ A.T + t
    assert box[0] == pytest.approx(np.floor(corners[:, 0].min()), abs=1)
    assert box[1] == pytest.approx(np.ceil(corners[:, 0].max()), abs=1)
    assert box[2] == pytest.approx(np.floor(corners[:, 1].min()), abs=1)
    assert box[3] == pytest.approx(np.ceil(corners[:, 1].max()), abs=1)
    assert map_box_affine((60, 160, 70, 180), src[:2], dst[:2]) is None  # too few links


def test_a_right_camera_with_static_left_masks_keeps_its_grid():
    """Without per-frame masks every reference frame carries the same frame-1
    outline: nothing moves, so the right grid must stay exactly as it was even
    though the mapped outline (plus the rim) may poke past it."""
    from al_dic_3d.matching.mesh_cover import right_cover_roi

    outline = np.zeros((H, W))
    outline[60:180, 80:200] = 1.0
    rng = np.random.default_rng(1)
    left_pts = rng.uniform([80, 60], [200, 180], (50, 2))
    right_pts = left_pts + np.array([30.0, 0.0])
    roi_r = (120, 220, 70, 170)  # narrower than the mapped outline
    kwargs = dict(
        right_masks=None,
        left_pts=left_pts,
        right_pts=right_pts,
        refs={0, 1, 2},
        step=STEP,
        winsize=WIN,
        img_shape=(H, W),
        rim_px=12,
    )
    assert right_cover_roi(roi_r, left_masks=[outline] * 3, **kwargs) == roi_r
    moved = [outline, np.roll(outline, 40, axis=1), np.roll(outline, 60, axis=1)]
    assert right_cover_roi(roi_r, left_masks=moved, **kwargs)[1] > roi_r[1]


def test_static_left_masks_keep_the_grid_even_past_a_drawn_rectangle():
    """One mask imported for every frame, larger than the drawn rectangle: it does
    not move, so the run keeps the rectangle's grid (as before the cover)."""
    from al_dic_3d.matching.mesh_cover import reference_cover_roi

    mask = np.zeros((H, W))
    mask[40:200, 40:280] = 1.0
    roi = (100, 181, 90, 151)
    kwargs = dict(step=STEP, winsize=WIN, img_shape=(H, W))
    assert reference_cover_roi(roi, [mask] * 4, {0, 1, 2}, **kwargs) == roi
    moving = [mask, np.roll(mask, 8, axis=1), np.roll(mask, 16, axis=1), mask]
    assert reference_cover_roi(roi, moving, {0, 1, 2}, **kwargs) != roi
