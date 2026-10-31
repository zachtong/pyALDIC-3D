"""End to end: an incremental run whose per-frame masks follow a moving specimen.

The specimen stretches along x, more at its free end (a quadratic field, 42 px
at the right edge by the last frame), and both cameras get masks that move with
it. Each reference frame trims the external mesh to its own mask (al-dic >=
1.0.4), so the mesh must also cover where the masks go. Without that, the
material that leaves the frame-1 extent has no cells at the later reference
frames and the engine extrapolates its increments from the cells it has: exact
for an affine field, wrong for a curved one — the mechanism behind a notched
specimen (necking) pulled 400 px keeping a fifth of its points.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("al_dic")
cv2 = pytest.importorskip("cv2")

from al_dic_3d.runner import load_config, run_pipeline  # noqa: E402
from tests import synth_stereo as ss  # noqa: E402

N_FRAMES = 4
X0, X1, Y0, Y1 = 60, 140, 60, 200  # frame-1 material, inclusive (left pixels)
EDGE_PX = 14.0  # extra x-displacement of the right edge per frame
PX_PER_MM = ss.FX / ss.Z0
XW0 = (X0 - ss.CX) / PX_PER_MM  # world-plane x of the material's left edge (mm)
C1 = EDGE_PX / PX_PER_MM / ((X1 - X0) / PX_PER_MM) ** 2  # 1/mm, per frame
EXTRA_LINES = {
    'right = "R_*.png"': ['left_mask = "ML_*.png"', 'right_mask = "MR_*.png"'],
    'strategy = "track_both"': ['reference_mode = "incremental"'],
}


def _x_at(x, k: int):
    """Left-image x, at frame ``k``, of the material at frame-1 x."""
    xw = (x - ss.CX) / PX_PER_MM
    return ss.CX + PX_PER_MM * (xw + C1 * k * np.maximum(xw - XW0, 0.0) ** 2)


def _source_map(h_cam: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """For every pixel of camera ``h_cam`` at frame ``k``, the frame-1 left pixel
    showing the same material (the deformation is x' = x + c (x - x0)^2 in the
    world plane, right of x0)."""
    c = C1 * k
    v, u = np.mgrid[0 : ss.IMG, 0 : ss.IMG].astype(np.float64)
    w = np.linalg.inv(h_cam) @ np.stack([u.ravel(), v.ravel(), np.ones(u.size)])
    xw, yw = w[0] / w[2], w[1] / w[2]
    d = xw - XW0
    if c > 0:
        inv = np.where(d > 0, (-1.0 + np.sqrt(1.0 + 4.0 * c * np.maximum(d, 0.0))) / (2.0 * c), d)
    else:
        inv = d
    xs = ss.CX + PX_PER_MM * (XW0 + inv)
    ys = ss.CY + PX_PER_MM * yw
    return xs.reshape(u.shape).astype(np.float32), ys.reshape(u.shape).astype(np.float32)


def _scene(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    l1 = ss._speckle()
    R, T = ss.rig_rt()
    h_wl, h_wr = ss._homographies(R, T)
    material = np.zeros((ss.IMG, ss.IMG), dtype=np.uint8)
    material[Y0 : Y1 + 1, X0 : X1 + 1] = 255
    for k in range(N_FRAMES):
        for cam, h in (("L", h_wl), ("R", h_wr)):
            mx, my = _source_map(h, k)
            img = cv2.remap(l1, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
            mask = cv2.remap(material, mx, my, cv2.INTER_NEAREST, borderValue=0)
            cv2.imwrite(str(tmp_path / f"{cam}_{k:03d}.png"), ss._u16(img))
            cv2.imwrite(str(tmp_path / f"M{cam}_{k:03d}.png"), mask)
    ss._write_opencv_yaml(tmp_path / "calib.yml", R, T)
    scene = {"calib": "calib.yml", "left_glob": "L_*.png", "right_glob": "R_*.png"}
    path = ss.write_config(tmp_path, scene, roi=(X0, X1, Y0, Y1))
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        lines.append(line.replace("winstepsize = 16", "winstepsize = 8"))
        lines.extend(EXTRA_LINES.get(line, []))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return load_config(path)


def _errors(result) -> tuple[np.ndarray, np.ndarray]:
    """Last-frame position errors (px) of the material that sits, at the last
    reference frame, at least a grid step beyond the frame-1 extent ("leaving"),
    and of the material that stays inside it; NaN where a point was dropped."""
    ref = np.asarray(result.correspondence.xL[0])
    x, y = ref[:, 0], ref[:, 1]
    rows = np.isfinite(x) & (y >= Y0 + 16) & (y <= Y1 - 16)
    leaving = rows & (x <= X1 - 8) & (_x_at(x, N_FRAMES - 2) > X1 + 8)
    staying = rows & (x >= X0 + 16) & (_x_at(x, N_FRAMES - 2) <= X1)
    last = np.asarray(result.correspondence.xL[-1])
    err = np.hypot(last[:, 0] - _x_at(x, N_FRAMES - 1), last[:, 1] - y)
    return err[leaving], err[staying]


def test_material_that_leaves_the_frame1_extent_is_tracked_like_the_rest(tmp_path, monkeypatch):
    """With the cover the leaving material is as accurate as the material that
    stays; with the frame-1 grid alone (cover disabled) it is several times worse.
    Comparing the two runs cancels the incremental chain's own drift (~0.5 px
    here, the same in both)."""
    leaving, staying = _errors(run_pipeline(_scene(tmp_path / "cover")))
    assert leaving.size >= 10
    assert np.isfinite(leaving).mean() >= 0.9
    assert np.nanmedian(leaving) <= np.nanmedian(staying) + 0.15

    from al_dic_3d.matching import mesh_cover
    from al_dic_3d.matching.strategies import track_both

    monkeypatch.setattr(mesh_cover, "reference_cover_roi", lambda roi, *a, **k: roi)
    monkeypatch.setattr(track_both, "right_cover_roi", lambda roi, **k: roi)
    bare, _ = _errors(run_pipeline(_scene(tmp_path / "bare")))
    bare = np.where(np.isfinite(bare), bare, np.inf)  # a dropped point counts as wrong
    assert np.median(bare) > 4 * np.nanmedian(leaving)
