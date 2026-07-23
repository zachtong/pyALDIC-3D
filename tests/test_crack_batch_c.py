"""Batch C — crack-aware stereo DIC (Qt-free compute items).

Covers: crack geometry primitives (crack.py), external-mesh barrier cutting
(item 1), strain crack-aware neighbour exclusion (item 2), and the strain_valid
data-model refactor (item 3). Rendering (item 4) lives in test_crack_render.py;
the composition-inheritance proof (item 0) in test_crack_composition.py.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.matching.crack_mesh import (
    bridging_elements,
    cut_mesh_at_barriers,
    mask_cuts_mesh,
)
from al_dic_3d.matching.primitives import make_dicpara
from al_dic_3d.matching.temporal import build_grid_mesh
from al_dic_3d.strain3d.crack import node_boundary_distance, segment_hits_barrier

# ---------------------------------------------------------------------------
# crack.py primitives — exact 2D rule
# ---------------------------------------------------------------------------


def _thin_vline_mask(h: int, w: int, xcol: int) -> np.ndarray:
    """All-material mask (1.0) with a 1-px vertical barrier band at column xcol."""
    m = np.ones((h, w), dtype=np.float64)
    m[:, xcol] = 0.0
    return m


def test_segment_hits_barrier_matches_rule():
    mask = _thin_vline_mask(50, 50, 25)
    # A horizontal segment straddling the barrier crosses it.
    assert segment_hits_barrier(20.0, 25.0, 30.0, 25.0, mask)
    # A segment entirely on one side never crosses.
    assert not segment_hits_barrier(10.0, 25.0, 20.0, 25.0, mask)
    # Adjacent nodes (n < 2) can never be excluded, even across the line.
    assert not segment_hits_barrier(24.6, 25.0, 25.4, 25.0, mask)
    # A vertical segment ALONG a clear column never crosses.
    assert not segment_hits_barrier(10.0, 5.0, 10.0, 45.0, mask)


def test_node_boundary_distance_thin_barrier():
    mask = _thin_vline_mask(60, 60, 30)
    coords = np.array([[30.0, 30.0], [31.0, 30.0], [5.0, 30.0]], dtype=np.float64)
    d = node_boundary_distance(coords, mask)
    assert d[0] == 0.0  # node on the barrier pixel
    assert 0.0 < d[1] <= 1.5  # one column away
    assert d[2] > 20.0  # far from the barrier
    # No background anywhere -> +inf.
    allmat = np.ones((20, 20), dtype=np.float64)
    assert np.isinf(node_boundary_distance(np.array([[10.0, 10.0]]), allmat)).all()


# ---------------------------------------------------------------------------
# item 1 — external-mesh barrier cutting
# ---------------------------------------------------------------------------


def _grid_mesh(h=220, w=220, step=16):
    para = make_dicpara(img_size=(h, w), roi=(40, w - 40, 40, h - 40), winstepsize=step)
    return build_grid_mesh(para, h, w)


def test_cut_mesh_drops_bridging_elements():
    h = w = 220
    mesh = _grid_mesh(h, w)
    n0 = mesh.elements_fem.shape[0]
    # Thin vertical crack through the ROI interior, mid-element (nodes fall on
    # 16-px multiples off the grid origin, so 102 lies between two columns).
    xcrack = 102
    mask = _thin_vline_mask(h, w, xcrack)
    bridging = bridging_elements(mesh, mask)
    assert bridging.any(), "a thin interior crack must bridge some elements"

    cut = cut_mesh_at_barriers(mesh, mask)
    assert cut is not mesh
    assert cut.elements_fem.shape[0] == n0 - int(bridging.sum())
    # No surviving element straddles the crack column.
    corners = cut.elements_fem[:, :4]
    cx = cut.coordinates_fem[corners, 0]
    straddles = (cx.min(axis=1) < xcrack) & (cx.max(axis=1) > xcrack)
    assert not straddles.any()
    # Nodes are untouched (orphans harmless).
    assert cut.coordinates_fem.shape == mesh.coordinates_fem.shape


def test_cut_mesh_hole_free_is_identical_object():
    mesh = _grid_mesh()
    allmat = np.ones((220, 220), dtype=np.float64)
    assert not mask_cuts_mesh(mesh, allmat)
    assert cut_mesh_at_barriers(mesh, allmat) is mesh
    assert cut_mesh_at_barriers(mesh, None) is mesh


# ---------------------------------------------------------------------------
# item 2 — strain crack-aware neighbour exclusion (fit_gradients)
# ---------------------------------------------------------------------------


def _cracked_gradient_case(sl: float, sr: float):
    """Grid with a bilinear-per-side displacement discontinuity across a crack.

    Left of the crack column ``dU/dX = sl``, right of it ``dU/dX = sr``; a plane
    fit that spans the crack blends the two, one that respects it recovers the
    node's own side exactly. Returns (ref_2d, ref_3d, disp, mask, xcrack, cols).
    """
    nx, step_px, origin, step_mm = 15, 16, 40, 2.0
    ii, jj = np.meshgrid(np.arange(nx), np.arange(nx))
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * step_px + origin, jj * step_px + origin]).astype(float)
    xw = (ii - (nx - 1) / 2.0) * step_mm
    yw = (jj - (nx - 1) / 2.0) * step_mm
    ref_3d = np.column_stack([xw, yw, np.full_like(xw, 800.0)])
    xcrack = origin + 8 * step_px + 8  # between node columns 8 and 9
    slope = np.where(ref_2d[:, 0] < xcrack, sl, sr)
    disp = np.column_stack([slope * xw, np.zeros_like(xw), np.zeros_like(xw)])
    mask = np.ones((260, 260), dtype=np.float64)
    mask[:, xcrack] = 0.0
    return ref_2d, ref_3d, disp, mask, xcrack, ii


def test_strain_crack_exclusion_numeric():
    from al_dic_3d.strain3d.gradients import fit_gradients

    sl, sr = 1e-3, 5e-3
    ref_2d, ref_3d, disp, mask, xcrack, ii = _cracked_gradient_case(sl, sr)
    vsg = 32.5  # strain_size 5, winstepsize 16

    plain = fit_gradients(ref_2d, ref_3d, disp, vsg, coordinate="camera0", engine="batched")
    crack = fit_gradients(
        ref_2d, ref_3d, disp, vsg, coordinate="camera0", engine="batched", barrier_mask=mask
    )

    # A node one column LEFT of the crack: with exclusion dU/dX == the left
    # slope; without it the fit blends both sides toward sr.
    left_col = ref_2d[:, 0] == xcrack - 8  # node column 8
    idx = int(np.flatnonzero(left_col)[np.flatnonzero(left_col).size // 2])
    assert np.isfinite(crack[idx, 0, 0])
    assert abs(crack[idx, 0, 0] - sl) < 1e-9, "crack fit must recover the left slope"
    assert abs(plain[idx, 0, 0] - sl) > 1e-4, "plain fit must blend across the crack"

    # A far interior node (>= vsg from the crack) is byte-identical.
    far = (ref_2d[:, 0] < xcrack - 3 * 16) & (ref_2d[:, 0] > 40 + 16)
    far &= (ref_2d[:, 1] > 40 + 2 * 16) & (ref_2d[:, 1] < 40 + 12 * 16)
    far_idx = np.flatnonzero(far)
    assert far_idx.size > 0
    assert np.allclose(plain[far_idx], crack[far_idx], atol=1e-12, rtol=0.0, equal_nan=True), (
        "interior fits must be unchanged to 1e-12"
    )


def test_c1_square_window_corner_neighbour_dropped():
    """Regression: a cross-crack neighbour in the diagonal CORNER of the square
    window (Euclidean reach in (vsg_radius, vsg_radius*sqrt(2)]) must be filtered.

    The near-barrier gate uses a Chebyshev-widened radius; a Euclidean
    ``< vsg_radius`` gate silently skips the corner node (see C1).
    """
    from al_dic_3d.strain3d.crack import node_boundary_distance
    from al_dic_3d.strain3d.gradients import _barrier_filtered_table, _neighbor_table

    vsg = 10.0
    # A 7x7 step-3 patch centred on Q=(100,100); the far corner is N=(109,109),
    # Chebyshev dist 9 (<=10, a valid VSG neighbour) at Euclidean 9*sqrt(2)~=12.73.
    axis = np.arange(91, 110, 3)  # 91,94,...,109
    xx, yy = np.meshgrid(axis, axis)
    nodes = np.column_stack([xx.ravel(), yy.ravel()]).astype(np.float64)
    q_idx = int(np.flatnonzero((nodes[:, 0] == 100) & (nodes[:, 1] == 100))[0])
    n_idx = int(np.flatnonzero((nodes[:, 0] == 109) & (nodes[:, 1] == 109))[0])

    # A thin anti-diagonal barrier tick crossing the Q->N segment near (108,108),
    # whose nearest barrier pixel to Q sits at ~11.3 px: OUTSIDE vsg_radius=10 but
    # INSIDE vsg_radius*sqrt(2)~=14.14 — the exact metric-mismatch band.
    mask = np.ones((160, 160), dtype=np.float64)
    for px, py in ((107, 109), (108, 108), (109, 107)):
        mask[py, px] = 0.0
    d_q = float(node_boundary_distance(nodes[q_idx : q_idx + 1], mask)[0])
    assert vsg < d_q < vsg * np.sqrt(2.0), f"geometry off: node_boundary_distance={d_q}"

    finite = np.ones(len(nodes), dtype=bool)
    idx_map, nbr, counts = _neighbor_table(nodes, finite, vsg, None)
    assert n_idx in nbr[q_idx, : counts[q_idx]], "N must be a base square-window neighbour of Q"

    _im, nbr_f, counts_f = _barrier_filtered_table(
        idx_map, nbr, counts, nodes, finite, vsg, mask, None
    )
    kept = set(int(j) for j in nbr_f[q_idx, : counts_f[q_idx]])
    assert n_idx not in kept, "corner neighbour across the crack must be dropped"
    # Q's own-side neighbours survive (only the crossing corner is removed).
    assert counts_f[q_idx] == counts[q_idx] - 1


def test_c1_interior_fit_unchanged_to_1e12():
    """The widened gate leaves nodes far from any barrier byte-identical."""
    from al_dic_3d.strain3d.gradients import fit_gradients

    ref_2d, ref_3d, disp, mask, xcrack, _ii = _cracked_gradient_case(1e-3, 5e-3)
    vsg = 32.5
    plain = fit_gradients(ref_2d, ref_3d, disp, vsg, coordinate="camera0", engine="batched")
    crack = fit_gradients(
        ref_2d, ref_3d, disp, vsg, coordinate="camera0", engine="batched", barrier_mask=mask
    )
    far = (ref_2d[:, 0] < xcrack - 3 * 16) & (ref_2d[:, 0] > 40 + 16)
    far &= (ref_2d[:, 1] > 40 + 2 * 16) & (ref_2d[:, 1] < 40 + 12 * 16)
    far_idx = np.flatnonzero(far)
    assert far_idx.size > 0
    assert np.allclose(plain[far_idx], crack[far_idx], atol=1e-12, rtol=0.0, equal_nan=True)


def test_strain_crack_exclusion_engines_agree():
    from al_dic_3d.strain3d import kernels
    from al_dic_3d.strain3d.gradients import fit_gradients

    if not kernels.HAS_NUMBA:
        pytest.skip("numba unavailable")
    ref_2d, ref_3d, disp, mask, _xc, _ii = _cracked_gradient_case(1e-3, 4e-3)
    a = fit_gradients(ref_2d, ref_3d, disp, 32.5, engine="numba", barrier_mask=mask)
    b = fit_gradients(ref_2d, ref_3d, disp, 32.5, engine="batched", barrier_mask=mask)
    assert np.allclose(a, b, atol=1e-9, equal_nan=True)


# ---------------------------------------------------------------------------
# C2 — right camera crack-awareness from a left-only crack mask
# ---------------------------------------------------------------------------


def test_c2_derive_right_barrier_warps_left_crack():
    """A LEFT-only crack barrier warps into the right camera and cuts mesh_R;
    a plain rectangular ROI (no thin barrier) derives NOTHING (byte-identity)."""
    pytest.importorskip("cv2")
    from al_dic_3d.matching.crack_mesh import mask_cuts_mesh
    from al_dic_3d.matching.strategies.track_both import _derive_right_barrier

    h = w = 240
    para_L = make_dicpara(img_size=(h, w), roi=(48, 168, 48, 168), winstepsize=16)
    coords_L = np.asarray(build_grid_mesh(para_L, h, w).coordinates_fem, dtype=np.float64)

    disparity = 12.0
    right_pts = coords_L + np.array([disparity, 0.0])
    x0, x1 = int(right_pts[:, 0].min()), int(right_pts[:, 0].max())
    y0, y1 = int(right_pts[:, 1].min()), int(right_pts[:, 1].max())
    para_R = make_dicpara(img_size=(h, w), roi=(x0 - 16, x1 + 16, y0 - 16, y1 + 16), winstepsize=16)
    mesh_R = build_grid_mesh(para_R, h, w)

    xcrack = 104  # thin 3-px vertical crack, ROI interior
    left_mask = np.ones((h, w), dtype=np.float64)
    left_mask[:, xcrack - 1 : xcrack + 2] = 0.0

    barrier = _derive_right_barrier(left_mask, coords_L, right_pts, mesh_R, (h, w))
    assert barrier is not None, "a warped left crack must cut the fresh right grid"
    assert mask_cuts_mesh(mesh_R, barrier)
    masked_cols = np.flatnonzero((barrier < 0.5).any(axis=0))
    assert masked_cols.size > 0
    assert abs(masked_cols.mean() - (xcrack + disparity)) < 12, "warped crack near xcrack+disparity"

    # A plain rectangular ROI (no interior thin band) -> None -> right unchanged.
    roi_only = np.zeros((h, w), dtype=np.float64)
    roi_only[48:168, 48:168] = 1.0
    assert _derive_right_barrier(roi_only, coords_L, right_pts, mesh_R, (h, w)) is None


def _stereo_scene(n_frames: int = 2, img: int = 220):
    """Compact in-memory converging-stereo scene (planar speckle, exact homographies)."""
    cv2 = pytest.importorskip("cv2")
    from scipy.ndimage import gaussian_filter

    from al_dic_3d.calibration import CameraIntrinsics, StereoRig

    fx = fy = 1400.0
    cx = cy = img / 2.0
    z0 = 800.0
    rng = np.random.default_rng(5)
    f = gaussian_filter(rng.standard_normal((img, img)), sigma=2.2, mode="nearest")
    f -= f.min()
    f /= f.max()
    l1 = 20.0 + 215.0 * f
    k = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float64)
    th = np.deg2rad(18.0)
    R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]])
    T = np.array([-z0 * np.sin(th), 0.0, z0 * (1.0 - np.cos(th))])
    h_wl = k @ np.diag([1.0, 1.0, z0])
    h_wr = k @ np.column_stack([R[:, 0], R[:, 1], z0 * R[:, 2] + T])
    h_wl_inv = np.linalg.inv(h_wl)

    def _warp(m):
        return cv2.warpPerspective(
            l1, m, (img, img), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT
        )

    left, right = [], []
    for i in range(n_frames):
        a = 1.0 + 0.0006 * i
        aff = np.array([[a, 0, 0.30 * i], [0, a, 0.15 * i], [0, 0, 1]], dtype=np.float64)
        left.append(_warp(h_wl @ aff @ h_wl_inv))
        right.append(_warp(h_wr @ aff @ h_wl_inv))
    intr = CameraIntrinsics(fx=fx, fy=fy, cx=cx, cy=cy, width=img, height=img)
    rig = StereoRig(cameras={"L": intr, "R": intr}, extrinsics={("L", "R"): (R, T)}, world_cam="L")
    return left, right, rig, img


def _run_track_both_capturing_masks(seq, rig, mesh_L, monkeypatch):
    """Run track_both.compute, returning the per-camera ``masks`` kwargs (L, R)."""
    import al_dic_3d.matching.strategies.track_both as tb
    from al_dic_3d.matching import get_strategy
    from al_dic_3d.matching.contracts import CorrespondenceConfig

    real = tb.temporal_track
    captured: list = []

    def spy(frames, mesh, para, **kw):
        captured.append(kw.get("masks"))
        return real(frames, mesh, para, **kw)

    monkeypatch.setattr(tb, "temporal_track", spy)
    cs = get_strategy("track_both")().compute(
        seq, rig, mesh_L, CorrespondenceConfig(strategy="track_both")
    )
    return captured, cs


def test_c2_track_both_right_camera_crack_aware(monkeypatch):
    """A LEFT-only crack mask makes the RIGHT temporal track crack-aware (per-frame
    masks feed the engine's crack-aware composition); crack-free -> R masks stay None."""
    from al_dic_3d.sequence import ArrayFrameProvider, StereoSequence

    left, right, rig, img = _stereo_scene()
    para = make_dicpara(img_size=(img, img), roi=(45, img - 45, 45, img - 45), winstepsize=16)
    mesh_L = build_grid_mesh(para, img, img)

    xc = img // 2
    crack = np.ones((img, img), dtype=np.float64)
    crack[:, xc - 1 : xc + 2] = 0.0

    seq = StereoSequence(
        providers={"L": ArrayFrameProvider(left), "R": ArrayFrameProvider(right)},
        masks={"L": [crack] * len(left)},
    )
    captured, cs = _run_track_both_capturing_masks(seq, rig, mesh_L, monkeypatch)
    assert len(captured) == 2, "serial track_both calls temporal_track once per camera"
    _l_masks, r_masks = captured
    assert r_masks is not None, "right track must receive a crack-aware per-frame mask stream"
    assert len(r_masks) == cs.n_frames
    assert (np.asarray(r_masks[0]) < 0.5).any(), "warped right mask carries the crack barrier"

    # Crack-free (no left mask): the right track's masks stay None (byte-identical).
    seq_plain = StereoSequence(
        providers={"L": ArrayFrameProvider(left), "R": ArrayFrameProvider(right)}
    )
    captured_plain, _cs = _run_track_both_capturing_masks(seq_plain, rig, mesh_L, monkeypatch)
    assert captured_plain[1] is None, "crack-free run must leave the right mask stream None"


# ---------------------------------------------------------------------------
# item 3 — strain_valid data model (dense values + per-frame validity)
# ---------------------------------------------------------------------------


def _recon_from_case(ref_3d, disp):
    from al_dic_3d.matching.contracts import TRACKED
    from al_dic_3d.reconstruct import Reconstruction3D

    points = np.stack([ref_3d, ref_3d + disp])
    displacement = points - points[0][None]
    reproj = np.zeros(points.shape[:2])
    source = np.full(points.shape[:2], TRACKED, np.uint8)
    return Reconstruction3D(points, displacement, reproj, source)


def test_strain_values_stay_dense_and_strain_valid_carries_trim():
    from al_dic_3d.strain3d import compute_surface_strain

    ref_2d, ref_3d, disp, _mask, _xc, _ii = _cracked_gradient_case(1e-3, 1e-3)
    rec = _recon_from_case(ref_3d, disp)

    s = compute_surface_strain(rec, ref_2d, strain_size=5, winstepsize=16, edge_trim_alpha=0.7)
    assert s.strain_valid is not None
    assert s.strain_valid.shape == (2, ref_2d.shape[0])
    assert s.strain_valid.dtype == np.bool_
    # A5-2: values are DENSE — the trim never NaNs a value that the fit produced.
    fit_ok = np.isfinite(s.exx[1])
    assert (fit_ok & ~s.strain_valid[1]).any(), "some fitted nodes are trimmed (flag only)"
    assert np.isfinite(s.exx[1][fit_ok]).all()
    # n_trimmed == count of trimmed valid nodes == (~strain_valid) among finite.
    assert int(s.n_trimmed[1]) == int((~s.strain_valid[1] & fit_ok).sum())

    # Trimming disabled -> strain_valid is None (all-valid convention).
    plain = compute_surface_strain(rec, ref_2d, strain_size=5, winstepsize=16)
    assert plain.strain_valid is None and plain.n_trimmed is None


def test_strain_valid_crack_trim_adds_band():
    from al_dic_3d.strain3d import compute_surface_strain

    ref_2d, ref_3d, disp, mask, xcrack, _ii = _cracked_gradient_case(1e-3, 5e-3)
    rec = _recon_from_case(ref_3d, disp)

    no_crack = compute_surface_strain(
        rec, ref_2d, strain_size=5, winstepsize=16, edge_trim_alpha=0.7
    )
    with_crack = compute_surface_strain(
        rec, ref_2d, strain_size=5, winstepsize=16, edge_trim_alpha=0.7, roi_mask=mask
    )
    # The crack barrier trims strictly MORE nodes (the two crack faces).
    assert int(with_crack.n_trimmed[1]) > int(no_crack.n_trimmed[1])
    # Nodes adjacent to the crack column are flagged invalid with the crack mask.
    adj = np.abs(ref_2d[:, 0] - xcrack) < 16
    assert not with_crack.strain_valid[1][adj].all()


def _result_with_strain(strain_valid):
    from al_dic_3d.matching.contracts import TRACKED, CorrespondenceSet
    from al_dic_3d.reconstruct import Reconstruction3D
    from al_dic_3d.runner import RunResult
    from al_dic_3d.strain3d.model import STRAIN_FIELDS, StrainResult3D

    nf, npts = 2, 9
    ref_2d = np.random.default_rng(0).uniform(0, 100, (npts, 2))
    pts = np.stack([np.column_stack([ref_2d, np.full(npts, 800.0)])] * nf)
    rec = Reconstruction3D(
        pts, pts - pts[0][None], np.zeros((nf, npts)), np.full((nf, npts), TRACKED, np.uint8)
    )
    xL = np.stack([ref_2d] * nf)
    cs = CorrespondenceSet(
        strategy="track_both",
        xL=xL.copy(),
        xR=xL.copy(),
        quality=np.zeros((nf, npts)),
        source=np.full((nf, npts), TRACKED, np.uint8),
    )
    fields = {n: np.full((nf, npts), 1e-3) for n in STRAIN_FIELDS}
    strain = StrainResult3D(**fields, strain_valid=strain_valid)
    return RunResult("track_both", ref_2d, cs, rec, strain=strain, meta={"n_frames": nf})


def test_strain_valid_export_and_session_round_trip(tmp_path):
    from al_dic_3d.export.tables import field_frame, field_stack
    from al_dic_3d.project import AppState3D, save_session
    from al_dic_3d.project.session import load_session
    from al_dic_3d.runner import _arrays

    valid = np.ones((2, 9), dtype=bool)
    valid[1, :3] = False  # some trimmed nodes
    result = _result_with_strain(valid)

    # Export contract: strain_valid is a first-class exportable field + npz key.
    np.testing.assert_array_equal(field_frame(result, "strain_valid", 1), valid[1])
    np.testing.assert_array_equal(field_stack(result, "strain_valid"), valid)
    assert "strain_valid" in _arrays(result)

    # Session round-trip preserves strain_valid.
    state = AppState3D()
    state.result = result
    reloaded = load_session(save_session(state, tmp_path / "s.aldic3d"))
    np.testing.assert_array_equal(reloaded.result.strain.strain_valid, valid)


def test_session_back_compat_missing_strain_valid(tmp_path):
    from al_dic_3d.project import AppState3D, save_session
    from al_dic_3d.project.session import load_session

    # A result with no strain_valid (pre-Batch-C / no-trim) reloads as None.
    result = _result_with_strain(None)
    state = AppState3D()
    state.result = result
    reloaded = load_session(save_session(state, tmp_path / "old.aldic3d"))
    assert reloaded.result.strain is not None
    assert reloaded.result.strain.strain_valid is None
