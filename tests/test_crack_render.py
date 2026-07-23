"""Batch C item 4 — crack-aware dense-field rendering (fieldmap + surface).

A field over a cracked ROI must NOT interpolate across the crack: the Delaunay
behind the dense overlay reconnects nodes the mesh split, so cells inside a
barrier-crossing triangle are blanked. None/no-op when no barrier -> bit-exact.
"""

from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d.viz3d.fieldmap import FieldmapRenderer  # noqa: E402


def _grid_nodes(nx=13, step=16, origin=40):
    ii, jj = np.meshgrid(np.arange(nx), np.arange(nx))
    ii, jj = ii.ravel(), jj.ravel()
    return np.column_stack([ii * step + origin, jj * step + origin]).astype(float)


def _alpha(rgba):
    return rgba[..., 3]


def test_fieldmap_blanks_cells_crossing_crack():
    nodes = _grid_nodes()
    # A field that is smooth across the whole ROI (so a bridging triangle would
    # happily interpolate over the crack if not blanked).
    values = nodes[:, 0] * 1e-3
    img_shape = (260, 260)
    xc = 40 + 6 * 16 + 8  # crack column mid-element
    barrier = np.ones(img_shape, dtype=np.float64)
    barrier[:, xc - 1 : xc + 2] = 0.0

    plain = FieldmapRenderer()
    crack = FieldmapRenderer()
    rgba_plain, xg, yg, _ = plain.render_field_rgba(
        0, "L:f", nodes, values, img_shape, 16, vmin=0.0, vmax=0.5
    )
    rgba_crack, _, _, _ = crack.render_field_rgba(
        0, "L:f", nodes, values, img_shape, 16, vmin=0.0, vmax=0.5, barrier_mask=barrier
    )
    assert rgba_plain is not None and rgba_crack is not None

    # The crack render blanks a band of cells the plain render leaves opaque.
    new_blank = (_alpha(rgba_plain) > 0) & (_alpha(rgba_crack) == 0)
    assert int(new_blank.sum()) > 0, "crack cells were not blanked"

    # The blanked cells straddle the crack column (mapped to grid coords).
    ys, xs = np.nonzero(new_blank)
    blank_x = xg[ys, xs]
    assert (np.abs(blank_x - xc) < 24).mean() > 0.5


def test_fieldmap_no_barrier_is_bit_exact():
    nodes = _grid_nodes()
    values = nodes[:, 1] * 1e-3
    img_shape = (260, 260)
    a = FieldmapRenderer().render_field_rgba(0, "L:f", nodes, values, img_shape, 16)[0]
    # An all-material mask has no crossing triangle -> identical to no barrier.
    allmat = np.ones(img_shape, dtype=np.float64)
    b = FieldmapRenderer().render_field_rgba(
        0, "L:f", nodes, values, img_shape, 16, barrier_mask=allmat
    )[0]
    np.testing.assert_array_equal(a, b)


def test_surface_cells_dropped_across_crack():
    from al_dic_3d.viz3d.surface import build_quad_connectivity, filter_cells_cross_barrier

    ref = _grid_nodes()
    cells = build_quad_connectivity(ref)
    assert len(cells) > 0
    xc = 40 + 6 * 16 + 8
    barrier = np.ones((260, 260), dtype=np.float64)
    barrier[:, xc - 1 : xc + 2] = 0.0

    kept = filter_cells_cross_barrier(cells, ref, barrier)
    assert len(kept) < len(cells), "crack-bridging quads must be dropped"
    # No surviving quad straddles the crack column.
    cx = ref[kept, 0]
    assert not ((cx.min(axis=1) < xc) & (cx.max(axis=1) > xc)).any()
    # No barrier -> identical cells (bit-exact).
    np.testing.assert_array_equal(filter_cells_cross_barrier(cells, ref, None), cells)
