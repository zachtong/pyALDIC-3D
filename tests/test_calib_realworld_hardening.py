"""Hardening found on the real D-shape target photos (Challenge 1.0 Sample 3).

Four regressions locked in:
- donut-style fiducials (solid dot with a SMALL concentric hole, VIC-3D style)
  are detected — the synthetic ring-around-dot style was the only one before;
- a misassigned fiducial triangle is rejected by the lattice match-fraction
  gate instead of surviving as a sheared 24%-matched "detection";
- calibrate_mono drops a catastrophically bad view (it biased fx by +7.6%
  while the pooled RMS still looked plausible);
- the MatchID importer parses unit-suffixed keys ('Cam0_Fx [pixels];...')
  and fails loudly when intrinsics are missing.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from al_dic_3d.calibration.boards import CodedCircleGridSpec
from al_dic_3d.calibration.detect import BoardDetection, detect_board
from al_dic_3d.calibration.solve import calibrate_mono

SPEC = CodedCircleGridSpec(cols=14, rows=10, spacing=7.0, fiducials=((2, 2), (7, 2), (7, 11)))


def _draw_donut_target(
    pitch_px: float = 60.0,
    dot_r: int = 14,
    hole_r: int = 4,
    fiducials: tuple[tuple[int, int], ...] = SPEC.fiducials,
    off_lattice_donuts: bool = False,
) -> np.ndarray:
    """White board, dark dot grid; fiducials are dots with a small center hole."""
    h = int(pitch_px * (SPEC.rows + 1))
    w = int(pitch_px * (SPEC.cols + 1))
    img = np.full((h, w), 235, np.uint8)
    for r in range(SPEC.rows):
        for c in range(SPEC.cols):
            cx = int(pitch_px * (c + 1))
            cy = int(pitch_px * (r + 1))
            cv2.circle(img, (cx, cy), dot_r, 25, -1, cv2.LINE_AA)
            if not off_lattice_donuts and (r, c) in fiducials:
                cv2.circle(img, (cx, cy), hole_r, 235, -1, cv2.LINE_AA)
    if off_lattice_donuts:
        # Donuts BETWEEN lattice sites: the affine from this triangle predicts
        # a shifted lattice that only accidentally snags a few dots.
        for r, c in fiducials:
            cx = int(pitch_px * (c + 1.5))
            cy = int(pitch_px * (r + 1.5))
            cv2.circle(img, (cx, cy), dot_r, 25, -1, cv2.LINE_AA)
            cv2.circle(img, (cx, cy), hole_r, 235, -1, cv2.LINE_AA)
    return img


def test_donut_fiducial_target_detected():
    det = detect_board(_draw_donut_target(), SPEC)
    assert det.ok, det.reason
    assert det.n_points >= 135  # all 140 dots, minor edge losses tolerated
    fid_ids = {r * SPEC.cols + c for r, c in SPEC.fiducials}
    assert fid_ids.issubset(set(det.ids.tolist()))
    # fiducial dots are calibration points too — centers on the lattice
    obj = det.object_points
    assert np.allclose(obj[:, 0] % SPEC.spacing, 0, atol=1e-9)


def test_misassigned_fiducial_triangle_is_rejected():
    det = detect_board(_draw_donut_target(off_lattice_donuts=True), SPEC)
    assert not det.ok
    assert "fraction" in det.reason or "fiducial" in det.reason


def _project_views(K, n_views: int = 10, noise_px: float = 0.05, seed: int = 7):
    rng = np.random.default_rng(seed)
    obj = np.ascontiguousarray(SPEC.object_points(), dtype=np.float64)  # (140, 3) mm
    dets = []
    for v in range(n_views):
        rvec = np.deg2rad(rng.uniform(-18, 18, 3))
        tvec = np.array([rng.uniform(-15, 15), rng.uniform(-10, 10), 420 + 12 * v % 60])
        img, _ = cv2.projectPoints(obj, rvec, tvec, K, np.zeros(5))
        pts = img.reshape(-1, 2) + rng.normal(0, noise_px, (len(obj), 2))
        dets.append(
            BoardDetection(
                ok=True,
                image_points=pts,
                object_points=obj.copy(),
                ids=np.arange(len(obj)),
                method="synthetic",
            )
        )
    return dets


def test_mono_per_view_rejection_recovers_fx():
    fx_true = 6650.0
    K = np.array([[fx_true, 0, 960.0], [0, fx_true, 600.0], [0, 0, 1.0]])
    dets = _project_views(K)
    # Poison ONE view the way a sheared lattice misassignment does: roll the
    # correspondence by 3 (wraps across rows — NOT a rigid board motion, so
    # no pose can explain it; a reversed grid would just be a 180-deg board).
    bad = dets[4]
    dets[4] = BoardDetection(
        ok=True,
        image_points=np.roll(bad.image_points, 3, axis=0).copy(),
        object_points=bad.object_points,
        ids=bad.ids,
        method="synthetic",
    )
    res = calibrate_mono(dets, (1920, 1200))
    assert len(res.view_indices) < len(dets)  # the poisoned view was dropped
    assert abs(res.intrinsics.fx - fx_true) / fx_true < 0.005
    assert res.rms < 0.3


def test_matchid_unit_suffixed_keys(tmp_path):
    from al_dic_3d.calibration.importers import load_calibration

    p = tmp_path / "cal.caldat"
    p.write_text(
        "Cam0_Fx [pixels];6651.97\nCam0_Fy [pixels];6648.81\n"
        "Cam0_Cx [pixels];902.85\nCam0_Cy [pixels];586.14\nCam0_Kappa 1;0.041\n"
        "Cam1_Fx [pixels];6607.28\nCam1_Fy [pixels];6603.14\n"
        "Cam1_Cx [pixels];935.32\nCam1_Cy [pixels];553.99\nCam1_Kappa 1;0.053\n"
        "Tx [mm];174.15\nTy [mm];0.65\nTz [mm];27.26\n"
        "Theta [deg];0.069\nPhi [deg];-18.97\nPsi [deg];0.263\n"
    )
    rig = load_calibration(p, "matchid")
    assert rig.cameras["L"].fx == pytest.approx(6651.97)
    _r, t = rig.pose("R")
    assert np.linalg.norm(t) == pytest.approx(176.27, abs=0.05)


def test_matchid_missing_fx_raises(tmp_path):
    from al_dic_3d.calibration.importers import load_calibration

    p = tmp_path / "bad.caldat"
    p.write_text("SomeKey;1.0\nTx [mm];174.15\n")
    with pytest.raises(ValueError, match="Fx"):
        load_calibration(p, "matchid")


def test_flatfield_rung_survives_illumination_gradient():
    """S5 real-photo failure shape: strong lighting gradient + donut fiducials.

    A global threshold merges/loses dots on one side; the adaptive rung erases
    the small fiducial holes. The flat-field rung must recover the detection.
    """
    img = _draw_donut_target().astype(np.float64)
    h, w = img.shape
    yy, xx = np.mgrid[0:h, 0:w]
    gradient = 0.35 + 0.65 * (xx / w) * (yy / h)  # dark corner -> bright corner
    shaded = np.clip(img * gradient, 0, 255).astype(np.uint8)
    det = detect_board(shaded, SPEC)
    assert det.ok, det.reason
    assert det.n_points >= 120
