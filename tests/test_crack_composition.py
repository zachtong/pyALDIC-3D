"""Batch C item 0 — crack-aware CUMULATIVE COMPOSITION is INHERITED, not ported.

We do NOT reimplement the 2D crack-aware composition: our
``matching.temporal.temporal_track`` already hands ``run_aldic`` a per-frame
``masks`` list, and the 0.7 engine computes ``crack_radius = 2*winstepsize``
internally and runs the crack-aware transform when ``masks`` is a per-frame list
(DEPENDS_ON_2D.md). This test PROVES the inheritance is live on our path: a thin
crack barrier in the ROI mask makes the engine's crack-aware composition kill the
on-crack nodes (born-dead / majority-masked), so displacement never smears across
the crack — while the SAME run with the crack absent tracks those nodes normally.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.matching.primitives import make_local_dicpara
from al_dic_3d.matching.temporal import build_grid_mesh, temporal_track

cv2 = pytest.importorskip("cv2")


def _speckle(h: int, w: int, sigma: float = 2.3, seed: int = 7) -> np.ndarray:
    from scipy.ndimage import gaussian_filter

    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((h, w)), sigma=sigma, mode="nearest")
    f -= f.min()
    f /= f.max()
    return 20.0 + 215.0 * f


def _shift(img: np.ndarray, tx: float, ty: float) -> np.ndarray:
    h, w = img.shape
    m = np.array([[1.0, 0.0, tx], [0.0, 1.0, ty]], dtype=np.float64)
    return cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def test_temporal_composition_is_crack_aware():
    h = w = 260
    f0 = _speckle(h, w)
    f1 = _shift(f0, 2.0, 0.0)  # uniform small shift -> ICGN converges everywhere
    frames = [f0, f1]

    para = make_local_dicpara(img_size=(h, w), roi=(48, w - 48, 48, h - 48), winsize=32)
    mesh = build_grid_mesh(para, h, w)
    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)
    xs = np.unique(coords[:, 0])
    xc = int(round(xs[len(xs) // 2]))  # a node column near the ROI centre
    on_crack = np.abs(coords[:, 0] - xc) < 1.0  # nodes sitting on the crack column
    assert on_crack.any()

    # A thin (3-px) vertical crack barrier covering that node column, else material.
    crack = np.ones((h, w), dtype=np.float64)
    crack[:, xc - 1 : xc + 2] = 0.0
    ones = np.ones((h, w), dtype=np.float64)

    # Honesty gate OFF so the ONLY source of a NaN track is the engine's
    # crack-aware composition (isolates the effect under test).
    tf_crack = temporal_track(frames, mesh, para, masks=[crack, crack], gate_znssd=0.0)
    tf_plain = temporal_track(frames, mesh, para, masks=[ones, ones], gate_znssd=0.0)

    # Far-from-crack nodes track the uniform shift correctly in BOTH runs.
    far = coords[:, 0] < xc - 3 * 16
    gt = np.tile([2.0, 0.0], (coords.shape[0], 1))
    for tf in (tf_crack, tf_plain):
        good = tf.valid[1] & far
        assert tf.valid[1][far].mean() > 0.5
        err = np.linalg.norm(tf.u_accum[1][good] - gt[good], axis=1)
        assert np.median(err) < 0.2

    # The crack barrier makes the engine's crack-aware composition kill the
    # on-crack nodes (born-dead), so displacement does not smear across the crack;
    # without the barrier those SAME nodes are tracked normally.
    assert tf_plain.valid[1][on_crack].any(), "crack-free run should track the column"
    assert not tf_crack.valid[1][on_crack].any(), (
        "crack-aware composition did not fire on our path — masks/crack_radius wiring broken"
    )
