"""C3 enhancement gates: board printout, known-distance verify, bundle adjust."""

import dataclasses

import numpy as np
import pytest

from al_dic_3d.calibration import (
    BoardDetection,
    ChessboardSpec,
    CircleGridSpec,
    bundle_refine,
    calibrate_stereo,
    detect_board,
    save_board_pdf,
    spec_summary,
    verify_known_distance,
)
from tests import synth_calib as sc

CHESS = ChessboardSpec(cols=9, rows=7, square_size=12.0)


@pytest.fixture(scope="module")
def rig():
    return sc.make_rig()


@pytest.fixture(scope="module")
def chess_set(rig):
    extent = ((CHESS.cols - 1) * CHESS.square_size, (CHESS.rows - 1) * CHESS.square_size)
    poses = sc.board_poses(extent, n=18)
    lefts, rights = sc.render_stereo_set(CHESS, rig, poses)
    dl = [detect_board(im, CHESS) for im in lefts]
    dr = [detect_board(im, CHESS) for im in rights]
    return dl, dr


@pytest.fixture(scope="module")
def base_result(chess_set):
    dl, dr = chess_set
    return calibrate_stereo(dl, dr, (sc.IMG_W, sc.IMG_H))


# --------------------------------------------------------------------------- #
# printout
# --------------------------------------------------------------------------- #


def test_board_pdf_written_at_scale(tmp_path):
    path = save_board_pdf(CHESS, tmp_path / "board.pdf")
    assert path.exists() and path.stat().st_size > 5_000
    assert "chessboard" in spec_summary(CHESS)


def test_board_pdf_rejects_oversize():
    huge = ChessboardSpec(cols=30, rows=22, square_size=15.0)
    with pytest.raises(ValueError, match="exceeds"):
        save_board_pdf(huge, "never_written.pdf")


# --------------------------------------------------------------------------- #
# known-distance verification
# --------------------------------------------------------------------------- #


def test_verification_confirms_good_calibration(rig, chess_set, base_result):
    dl, dr = chess_set
    v = verify_known_distance(base_result.rig, dl[0], dr[0], CHESS)
    assert v.n_points == 63
    assert abs(v.scale_error) < 1e-3  # < 0.1% pitch error on the synthetic gate
    assert v.distance_rmse < 0.05  # mm
    assert v.plane_rms < 0.05  # flat board reconstructs flat


def test_verification_flags_bad_baseline(rig, chess_set, base_result):
    # A 2% baseline error must show up as ~2% scale error — the iDICs point:
    # reprojection RMS alone would NOT catch a mis-scaled calibration.
    dl, dr = chess_set
    r, t = base_result.rig.pose("R")
    bad_rig = dataclasses.replace(base_result.rig, extrinsics={("L", "R"): (r, t * 1.02)})
    v = verify_known_distance(bad_rig, dl[0], dr[0], CHESS)
    assert abs(v.scale_error) > 0.015


def test_verification_input_validation(rig, chess_set, base_result):
    dl, _dr = chess_set
    with pytest.raises(ValueError, match="not detected"):
        verify_known_distance(base_result.rig, dl[0], BoardDetection(ok=False, reason="x"), CHESS)
    with pytest.raises(ValueError, match="asymmetric"):
        verify_known_distance(
            base_result.rig,
            dl[0],
            dl[0],
            CircleGridSpec(cols=4, rows=5, spacing=10, asymmetric=True),
        )


# --------------------------------------------------------------------------- #
# bundle adjustment
# --------------------------------------------------------------------------- #


def _fx_err(rig_est, rig_gt) -> float:
    return abs(rig_est.cameras["L"].fx - rig_gt.cameras["L"].fx) / rig_gt.cameras["L"].fx


def test_bundle_keeps_gate_accuracy(rig, chess_set, base_result):
    dl, dr = chess_set
    new_rig, info = bundle_refine(dl, dr, base_result)
    assert info["rms_after"] <= info["rms_before"] + 1e-9
    assert info["n_views"] == 18
    assert _fx_err(new_rig, rig) < 5e-4
    assert abs(new_rig.cameras["L"].cx - rig.cameras["L"].cx) < 0.5
    r_gt, t_gt = rig.pose("R")
    r_e, t_e = new_rig.pose("R")
    assert abs(np.linalg.norm(t_e) - np.linalg.norm(t_gt)) < 0.05
    ang = np.degrees(np.arccos(np.clip((np.trace(r_e @ r_gt.T) - 1) / 2, -1, 1)))
    assert ang < 0.05


def test_bundle_robust_to_point_outliers(rig, chess_set):
    # Corrupt 5 individual corners in ONE left view by 8 px. The robust
    # per-point loss must hold the solve near truth.
    dl, dr = chess_set
    rng = np.random.default_rng(11)
    pts = dl[3].image_points.copy()
    idx = rng.choice(len(pts), 5, replace=False)
    pts[idx] += 8.0
    dl_bad = [*dl[:3], dataclasses.replace(dl[3], image_points=pts), *dl[4:]]

    base = calibrate_stereo(dl_bad, dr, (sc.IMG_W, sc.IMG_H), reject_rms=50.0)
    new_rig, _info = bundle_refine(dl_bad, dr, base)
    assert _fx_err(new_rig, rig) < 1e-3
    assert abs(new_rig.cameras["L"].cx - rig.cameras["L"].cx) < 1.0


def test_bundle_uses_mono_only_views(rig, chess_set, base_result):
    # Blind the right camera on 4 views: stereoCalibrate loses those pairs
    # entirely, but the bundle keeps their LEFT mono residuals.
    dl, dr = chess_set
    dr_holes = list(dr)
    for i in (2, 5, 9, 14):
        dr_holes[i] = BoardDetection(ok=False, reason="blinded")
    base = calibrate_stereo(dl, dr_holes, (sc.IMG_W, sc.IMG_H))
    new_rig, info = bundle_refine(dl, dr_holes, base)
    assert info["n_views"] == 18
    assert info["n_mono_views"] == 4
    assert _fx_err(new_rig, rig) < 5e-4


def test_bundle_input_validation(chess_set, base_result):
    dl, dr = chess_set
    with pytest.raises(ValueError, match="view counts differ"):
        bundle_refine(dl[:4], dr[:5], base_result)
    empty = [BoardDetection(ok=False, reason="x")] * 4
    with pytest.raises(ValueError, match="usable views"):
        bundle_refine(empty, empty, base_result)


# --------------------------------------------------------------------------- #
# board morphology (MMC-inspired)
# --------------------------------------------------------------------------- #


def _warp_z(obj: np.ndarray, amp: float) -> np.ndarray:
    """Paper-warp height field vanishing on the board edges (and thus anchors)."""
    w, h = obj[:, 0].max(), obj[:, 1].max()
    return amp * np.sin(np.pi * obj[:, 0] / w) * np.sin(np.pi * obj[:, 1] / h)


def _analytic_detections(rig, poses, obj_nominal, warp_amp, noise, seed):
    """Detections whose measurements come from a WARPED board while the solver
    is only told the NOMINAL flat object points."""
    from al_dic_3d.calibration import project_points

    rng = np.random.default_rng(seed)
    warped = obj_nominal.copy()
    warped[:, 2] += _warp_z(obj_nominal, warp_amp)
    ids = np.arange(len(obj_nominal), dtype=np.int64)
    dl, dr = [], []
    for r_b, t_b in poses:
        world = warped @ r_b.T + t_b
        for cam, out in (("L", dl), ("R", dr)):
            r_c, t_c = rig.pose(cam)
            px = project_points(world, rig.cameras[cam], r_c, t_c)
            px = px + rng.normal(0.0, noise, px.shape)
            out.append(BoardDetection(ok=True, image_points=px, object_points=obj_nominal, ids=ids))
    return dl, dr


def _detrend(z: np.ndarray, xy: np.ndarray) -> np.ndarray:
    a = np.column_stack([xy[:, 0], xy[:, 1], np.ones(len(xy))])
    return z - a @ np.linalg.lstsq(a, z, rcond=None)[0]


def test_morphology_recovers_warped_board(rig):
    # 0.5 mm sinusoidal warp (typical paper/mount flatness error at 100 mm scale)
    obj = CHESS.object_points()
    poses = sc.board_poses(((CHESS.cols - 1) * 12.0, (CHESS.rows - 1) * 12.0), n=18)
    dl, dr = _analytic_detections(rig, poses, obj, warp_amp=0.5, noise=0.01, seed=5)
    base = calibrate_stereo(dl, dr, (sc.IMG_W, sc.IMG_H))

    rig_rigid, info_rigid = bundle_refine(dl, dr, base)
    rig_morph, info = bundle_refine(dl, dr, base, board_morphology=True)

    # morphology absorbs the warp into board points instead of the residual
    assert info["rms_after"] < 0.5 * info_rigid["rms_after"]
    # recovered out-of-plane shape matches the truth after plane detrending
    pts = info["board_points"]
    truth = _warp_z(obj, 0.5)
    err = _detrend(pts[:, 2], obj[:, :2]) - _detrend(truth, obj[:, :2])
    assert np.sqrt(np.mean(err**2)) < 0.08  # mm
    assert info["board_z_range"] > 0.3  # the warp is actually seen
    # camera parameters at least as good as the rigid solve
    assert _fx_err(rig_morph, rig) <= _fx_err(rig_rigid, rig) + 1e-4


def test_morphology_on_flat_board_stays_flat(rig, chess_set, base_result):
    dl, dr = chess_set
    new_rig, info = bundle_refine(dl, dr, base_result, board_morphology=True)
    assert info["board_max_dev"] < 0.08  # mm — no phantom warp from a flat board
    assert _fx_err(new_rig, rig) < 5e-4
    assert "cost_history" in info and len(info["cost_history"]) > 0


def test_bundle_progress_callback(chess_set, base_result):
    dl, dr = chess_set
    lines: list[str] = []
    bundle_refine(dl, dr, base_result, progress=lines.append)
    assert lines and all("rms" in ln for ln in lines)


# --------------------------------------------------------------------------- #
# stability jackknife + residual scatter (MMC-inspired QC)
# --------------------------------------------------------------------------- #


def test_stability_jackknife_tight_on_clean_data(chess_set, base_result):
    from al_dic_3d.calibration import stability_jackknife

    dl, dr = chess_set
    st = stability_jackknife(
        dl, dr, (sc.IMG_W, sc.IMG_H), base_result, drop_fraction=0.25, n_samples=4, seed=3
    )
    assert len(st.samples["fx"]) >= 3
    std_fx, lo, hi = st.spread("fx")
    assert std_fx / st.reference["fx"] < 2e-3  # clean synthetic: subsets agree
    assert lo <= st.reference["fx"] <= hi or std_fx < 1.0
    assert st.spread("baseline")[0] < 0.2  # mm


def test_stability_jackknife_validates_drop(chess_set, base_result):
    from al_dic_3d.calibration import stability_jackknife

    dl, dr = chess_set
    with pytest.raises(ValueError, match="min_pairs"):
        stability_jackknife(dl, dr, (sc.IMG_W, sc.IMG_H), base_result, drop_fraction=0.9)


def test_detections_npz_round_trip(tmp_path, chess_set):
    from al_dic_3d.calibration import load_detections, save_detections

    dl, dr = chess_set
    files_l = [f"L_{k:02d}.png" for k in range(len(dl))]
    files_r = [f"R_{k:02d}.png" for k in range(len(dr))]
    path = save_detections(
        tmp_path / "det.npz", files_l, files_r, dl, dr, image_size=(sc.IMG_W, sc.IMG_H)
    )
    fl, fr, dl2, dr2, size = load_detections(path)
    assert fl == files_l and fr == files_r
    assert size == (sc.IMG_W, sc.IMG_H)
    assert len(dl2) == len(dl)
    for a, b in zip(dl + dr, dl2 + dr2, strict=True):
        assert a.ok == b.ok and a.method == b.method
        assert np.array_equal(a.image_points, b.image_points)
        assert np.array_equal(a.ids, b.ids)
    # the reloaded detections re-solve identically without any images on disk
    res = calibrate_stereo(dl2, dr2, size)
    assert res.n_pairs_used == 18


def test_pair_max_errors(chess_set, base_result):
    from al_dic_3d.calibration import pair_max_errors

    dl, dr = chess_set
    mx = pair_max_errors(base_result, dl, dr)
    assert len(mx) == 18
    assert all(0.0 < v < 0.2 for v in mx.values())  # clean synthetic


def test_point_residuals_scatter(chess_set, base_result):
    from al_dic_3d.calibration import point_residuals

    dl, dr = chess_set
    res = point_residuals(base_result, dl, dr)
    for cam in ("L", "R"):
        r = res[cam]
        assert r.shape[1] == 2 and len(r) >= 63 * 15
        assert np.isfinite(r).all()
        assert np.abs(r.mean(axis=0)).max() < 0.05  # unbiased
        assert np.sqrt((r**2).sum(axis=1)).mean() < 0.1  # px, clean synthetic
