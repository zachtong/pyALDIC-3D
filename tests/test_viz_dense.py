"""Unit tests for the dense full-field renderer (2D VizController port).

Covers the compute core without any widget: a synthetic node grid must render
to a dense RGBA image that is opaque inside the valid-node support, transparent
outside it, transparent inside NaN-node holes, and monotonic in color along a
value gradient. Also covers the deformed-mode inverse-displacement mask warp,
the ``visible_values`` auto-range helper, and the two-tier caching.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

pytest.importorskip("PySide6")
pytest.importorskip("cv2")

from al_dic_3d.gui.controllers.viz_controller import (  # noqa: E402
    VizController3D,
    valid_node_support_mask,
    visible_values,
)

IMG_SHAPE = (60, 70)  # (H, W)
STEP = 10  # node spacing -> output_step = STEP // 4 = 2


def _grid_nodes(nx: int = 5, ny: int = 4, step: float = STEP, origin: float = 10.0):
    """Regular (nx * ny, 2) node grid: x in [10, 50], y in [10, 40]."""
    xs, ys = np.meshgrid(origin + step * np.arange(nx), origin + step * np.arange(ny))
    return np.column_stack([xs.ravel(), ys.ravel()]).astype(np.float64)


def _rgba_at(rgba, xg, yg, out_step, x, y):
    """Sample the dense RGBA at image coordinates (x, y)."""
    col = int(round((x - float(xg.min())) / out_step))
    row = int(round((y - float(yg.min())) / out_step))
    return rgba[row, col]


def test_dense_rgba_support_hole_and_gradient():
    nodes = _grid_nodes()
    values = nodes[:, 0].copy()  # linear gradient along x
    hole_idx = 2 * 5 + 2  # node at (30, 30)
    values[hole_idx] = np.nan

    ctrl = VizController3D()
    rgba, xg, yg, out_step = ctrl.render_field_rgba(
        0, "t:U", nodes, values, IMG_SHAPE, STEP, cmap="gray", vmin=10.0, vmax=50.0
    )
    assert rgba is not None and rgba.dtype == np.uint8 and rgba.shape[2] == 4
    assert out_step == STEP // 4

    # Opaque inside the support (away from the hole).
    assert _rgba_at(rgba, xg, yg, out_step, 15, 15)[3] == 255
    # Transparent outside the hull (bbox margin exists but hull does not).
    assert _rgba_at(rgba, xg, yg, out_step, float(xg.min()), float(yg.min()))[3] == 0
    # NaN-node hole stays transparent (triangles touching it are dropped).
    assert _rgba_at(rgba, xg, yg, out_step, 30, 30)[3] == 0
    # Value -> color monotonic along the gradient ("gray": R rises with value).
    reds = [int(_rgba_at(rgba, xg, yg, out_step, x, 12)[0]) for x in range(12, 49, 2)]
    alphas = [int(_rgba_at(rgba, xg, yg, out_step, x, 12)[3]) for x in range(12, 49, 2)]
    assert all(a == 255 for a in alphas)
    assert all(b >= a for a, b in zip(reds, reds[1:], strict=False))
    assert reds[-1] > reds[0]


def test_drawn_roi_mask_hole_masks_pixels():
    nodes = _grid_nodes()
    values = nodes[:, 1].copy()
    mask = np.zeros(IMG_SHAPE, dtype=bool)
    mask[5:45, 5:55] = True
    mask[25:35, 25:35] = False  # drawn hole inside the ROI

    ctrl = VizController3D()
    rgba, xg, yg, out_step = ctrl.render_field_rgba(
        0, "t:V", nodes, values, IMG_SHAPE, STEP, roi_mask=mask
    )
    assert _rgba_at(rgba, xg, yg, out_step, 15, 15)[3] == 255
    assert _rgba_at(rgba, xg, yg, out_step, 30, 30)[3] == 0  # hole preserved


def test_deformed_mode_warps_reference_mask():
    ref = _grid_nodes()
    shift = 6.0
    deformed_nodes = ref + np.array([shift, 0.0])
    values = np.ones(len(ref))
    u = np.full(len(ref), shift)
    v = np.zeros(len(ref))
    mask = np.zeros(IMG_SHAPE, dtype=bool)
    mask[5:45, 5:55] = True
    mask[26:34, 26:34] = False  # reference-frame hole

    ctrl = VizController3D()
    rgba, xg, yg, out_step = ctrl.render_field_rgba(
        1,
        "t:U",
        deformed_nodes,
        values,
        IMG_SHAPE,
        STEP,
        roi_mask=mask,
        deformed=True,
        ref_uv=(u, v),
        ref_pts=ref,
    )
    # The hole travels WITH the material: transparent at ref + shift ...
    assert _rgba_at(rgba, xg, yg, out_step, 30 + shift, 30)[3] == 0
    # ... while a point inside the shifted support is opaque.
    assert _rgba_at(rgba, xg, yg, out_step, 20 + shift, 20)[3] == 255


def test_fallback_support_uses_reference_positions_in_deformed_mode():
    """Invalid nodes lose their deformed positions (NaN); the fallback support
    must locate their holes from ``ref_pts`` and warp them into place."""
    ref = _grid_nodes()
    shift = 6.0
    hole_idx = 2 * 5 + 2  # node at (30, 30)
    values = np.ones(len(ref))
    values[hole_idx] = np.nan
    deformed_nodes = ref + np.array([shift, 0.0])
    deformed_nodes[hole_idx] = np.nan  # invalid: no deformed position at all
    u = np.full(len(ref), shift)
    v = np.zeros(len(ref))
    u[hole_idx] = v[hole_idx] = np.nan  # ref_uv = x_k - x_1 is NaN there too

    ctrl = VizController3D()
    rgba, xg, yg, out_step = ctrl.render_field_rgba(
        1,
        "t:U",
        deformed_nodes,
        values,
        IMG_SHAPE,
        STEP,
        deformed=True,
        ref_uv=(u, v),
        ref_pts=ref,
    )
    assert _rgba_at(rgba, xg, yg, out_step, 30 + shift, 30)[3] == 0  # hole
    assert _rgba_at(rgba, xg, yg, out_step, 15 + shift, 15)[3] == 255


def test_degenerate_node_set_returns_none():
    nodes = np.array([[10.0, 10.0], [20.0, 10.0], [np.nan, np.nan]])
    values = np.array([1.0, 2.0, 3.0])
    ctrl = VizController3D()
    rgba, xg, yg, out_step = ctrl.render_field_rgba(0, "t:U", nodes, values, IMG_SHAPE, STEP)
    assert rgba is None and xg is None and yg is None and out_step == 1


def test_valid_node_support_mask_basics():
    nodes = _grid_nodes()
    values = np.ones(len(nodes))
    support = valid_node_support_mask(nodes, values, IMG_SHAPE)
    assert support.shape == IMG_SHAPE and support.dtype == np.bool_
    assert support[25, 25]  # inside the grid
    assert not support[2, 2]  # outside the hull
    values[2 * 5 + 2] = np.nan  # node at (30, 30)
    holey = valid_node_support_mask(nodes, values, IMG_SHAPE)
    assert not holey[30, 30]  # triangles touching the NaN node dropped
    assert holey[15, 15]


def test_support_edge_cap_keeps_node_free_holes_transparent():
    """A rectangular node-free ROI hole must NOT be spanned by the fallback
    support: Delaunay bridges it with long triangles, and the 2.5x-step edge
    cap drops them (the right-camera / maskless hole-fill fix, F1.5)."""
    step = 10.0
    xs, ys = np.meshgrid(5.0 + step * np.arange(6), 5.0 + step * np.arange(6))
    nodes = np.column_stack([xs.ravel(), ys.ravel()]).astype(np.float64)
    in_hole = (nodes[:, 0] >= 15) & (nodes[:, 0] <= 45) & (nodes[:, 1] >= 15) & (nodes[:, 1] <= 45)
    nodes = nodes[~in_hole]  # 4x4 interior block removed -> node-free hole
    values = np.ones(len(nodes))

    support = valid_node_support_mask(nodes, values, IMG_SHAPE, mesh_step=step)
    assert not support[30, 30]  # hole interior stays transparent
    assert support[8, 8]  # normal-density corner region keeps its support

    # Default step (median nearest-neighbor spacing) finds the same hole.
    support_auto = valid_node_support_mask(nodes, values, IMG_SHAPE)
    assert not support_auto[30, 30]
    assert support_auto[8, 8]


def test_visible_values_restricts_range_to_mask():
    nodes = _grid_nodes()
    values = nodes[:, 0].copy()  # 10 .. 50
    mask = np.zeros(IMG_SHAPE, dtype=bool)
    mask[:, :35] = True  # only nodes with x < 35 visible
    vis = visible_values(values, nodes, mask)
    assert np.nanmax(vis) == 30.0  # 40/50 columns masked out
    assert np.nanmin(vis) == 10.0
    # None mask and empty intersection both fall back to the full array.
    assert visible_values(values, nodes, None) is values
    empty = np.zeros(IMG_SHAPE, dtype=bool)
    np.testing.assert_array_equal(visible_values(values, nodes, empty), values)


def test_pixmap_tier2_cache_hits(qapp):
    nodes = _grid_nodes()
    values = nodes[:, 0].copy()
    ctrl = VizController3D()
    pm1, xg, yg, step = ctrl.render_field(
        0, "L:U", nodes, values, IMG_SHAPE, STEP, cmap="turbo", vmin=10, vmax=50
    )
    assert pm1 is not None and not pm1.isNull()
    pm2, _, _, _ = ctrl.render_field(
        0, "L:U", nodes, values, IMG_SHAPE, STEP, cmap="turbo", vmin=10, vmax=50
    )
    assert pm2 is pm1  # exact Tier-2 hit returns the same pixmap object
    pm3, _, _, _ = ctrl.render_field(
        0, "L:U", nodes, values, IMG_SHAPE, STEP, cmap="viridis", vmin=10, vmax=50
    )
    assert pm3 is not pm1  # colormap change bypasses Tier 2 (Tier-1 reused)
    ctrl.clear_all()
    pm4, _, _, _ = ctrl.render_field(
        0, "L:U", nodes, values, IMG_SHAPE, STEP, cmap="turbo", vmin=10, vmax=50
    )
    assert pm4 is not pm1


@pytest.fixture(scope="module")
def qapp():
    from al_dic_3d.gui.app import create_app

    return create_app([])
