"""Rigid-body-motion removal on a reconstruction (Qt-free).

For every frame ``k >= 1`` the best-fit rigid motion carrying the reference
surface ``P^1`` onto ``P^k`` is estimated over a node subset and removed::

    R_k P^1 + t_k ~= P^k            (least squares over the subset S_k)
    P'^k = R_k^T (P^k - t_k),       D'^k = P'^k - P^1

``translation`` mode fixes ``R_k = I`` (``t_k`` = mean displacement of ``S_k``);
``rigid`` mode solves ``R_k`` by the Kabsch / SVD method with a reflection guard
(DIC surfaces are near-planar, where an unguarded SVD can return a mirror).
``S_k`` is the nodes finite in frames 0 and ``k``, intersected with an optional
region. A frame whose fit is impossible (too few or collinear points) becomes
invalid (``NaN``) rather than silently uncorrected. Displacement is cumulative on
the frame-1 mesh for every frame schedule, so fitting each frame against frame 1
is valid in incremental and accumulative runs alike.

Green-Lagrange strain is invariant to this step; the displacement, its
out-of-plane slopes and the other strain measures are not.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.matching.contracts import INVALID
from al_dic_3d.reconstruct.outliers import rebuild_reconstruction
from al_dic_3d.reconstruct.reconstruction import Reconstruction3D

RIGID_MOTION_MODES = ("off", "translation", "rigid")
_FIT_MODES = ("translation", "rigid")
_MIN_POINTS = {"translation": 1, "rigid": 3}

FIT_REFERENCE = "reference"
FIT_OK = "ok"
FIT_TOO_FEW = "too_few_points"
FIT_DEGENERATE = "degenerate"

#: Second over first principal spread of the subset below which the points are
#: treated as collinear: a rotation about that line is then undetermined.
COLLINEAR_TOL = 1e-3


@dataclass(frozen=True)
class RigidMotionFit:
    """Per-frame rigid motion; frame 0 is the identity, failed frames are ``NaN``."""

    mode: str
    rotation: NDArray[np.float64]  # (n_frames, 3, 3) R_k
    translation: NDArray[np.float64]  # (n_frames, 3) t_k, world mm (origin = left camera)
    centroid_shift: NDArray[np.float64]  # (n_frames, 3) how far the subset centroid moved, mm
    rms: NDArray[np.float64]  # (n_frames,) residual of the fit, mm
    n_used: NDArray[np.int64]  # (n_frames,) nodes in the fit
    status: tuple[str, ...]  # FIT_REFERENCE / FIT_OK / FIT_TOO_FEW / FIT_DEGENERATE

    @property
    def n_frames(self) -> int:
        return len(self.status)

    def angle_rad(self) -> NDArray[np.float64]:
        """Rotation angle per frame (atan2 form: accurate for milliradian angles)."""
        trace = np.trace(self.rotation, axis1=1, axis2=2)
        return np.arctan2(np.linalg.norm(_vee(self.rotation), axis=1), trace - 1.0)

    def axis(self) -> NDArray[np.float64]:
        """Unit rotation axis per frame; ``NaN`` where the angle is zero or the fit failed."""
        vee = _vee(self.rotation)
        norm = np.linalg.norm(vee, axis=1, keepdims=True)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(norm > 0.0, vee / norm, np.nan)

    def to_meta(self) -> dict:
        """JSON-ready summary (lists only, ``NaN`` -> ``None``, units in the keys)."""
        return {
            "mode": self.mode,
            "status": list(self.status),
            "n_used": [int(n) for n in self.n_used],
            "centroid_shift_um": _plain(self.centroid_shift * 1e3),
            "rotation_angle_mrad": _plain(self.angle_rad() * 1e3),
            "rotation_axis": _plain(self.axis()),
            "rms_um": _plain(self.rms * 1e3),
            "rotation_matrix": _plain(self.rotation),
            "translation_mm": _plain(self.translation),
        }


@dataclass(frozen=True)
class RigidMotionState:
    """What a result carries while rigid motion is removed: enough to undo or redo it."""

    raw: Reconstruction3D  # the measured reconstruction, never modified
    fit: RigidMotionFit
    region: NDArray[np.bool_] | None  # (H, W) fit region in the left reference image; None = all


def fit_rigid_motion(
    rec: Reconstruction3D,
    mode: str,
    node_mask: NDArray[np.bool_] | None = None,
) -> RigidMotionFit:
    """Fit each frame's rigid motion against the reference frame.

    Args:
        rec: the reconstruction (``points[0]`` is the reference surface).
        mode: ``"translation"`` or ``"rigid"``.
        node_mask: optional ``(n_pts,)`` boolean subset to fit on (the region);
            ``None`` uses every valid node.
    """
    if mode not in _FIT_MODES:
        raise ValueError(f"rigid-motion mode must be one of {_FIT_MODES}, got {mode!r}")
    pts = rec.points
    n_frames, n_pts = rec.n_frames, rec.n_pts
    subset = _subset(node_mask, n_pts)
    ref = pts[0]
    ref_ok = subset & np.isfinite(ref).all(axis=1)

    rotation = np.full((n_frames, 3, 3), np.nan)
    translation = np.full((n_frames, 3), np.nan)
    shift = np.full((n_frames, 3), np.nan)
    rms = np.full(n_frames, np.nan)
    n_used = np.zeros(n_frames, dtype=np.int64)
    status = [FIT_REFERENCE]
    rotation[0], translation[0], shift[0], rms[0] = np.eye(3), 0.0, 0.0, 0.0
    n_used[0] = int(ref_ok.sum())

    for k in range(1, n_frames):
        use = ref_ok & np.isfinite(pts[k]).all(axis=1)
        n_used[k] = int(use.sum())
        a, b = ref[use], pts[k][use]
        rot, t, state = _fit_frame(a, b, mode)
        status.append(state)
        if state != FIT_OK:
            continue
        rotation[k], translation[k] = rot, t
        shift[k] = b.mean(axis=0) - a.mean(axis=0)
        resid = b - (a @ rot.T + t)
        rms[k] = float(np.sqrt(np.mean(np.sum(resid * resid, axis=1))))
    return RigidMotionFit(mode, rotation, translation, shift, rms, n_used, tuple(status))


def apply_rigid_motion(rec: Reconstruction3D, fit: RigidMotionFit) -> Reconstruction3D:
    """Remove ``fit`` from ``rec``: ``P'^k = R_k^T (P^k - t_k)``; a failed frame -> ``NaN``.

    Pure: returns a new reconstruction (frame 0 copied bit-exactly), ``D = P - P[0]``
    recomputed, ``reproj_error`` / ``source`` carried over except on failed frames,
    which are demoted to ``INVALID`` like the quality gates do.
    """
    if fit.n_frames != rec.n_frames:
        raise ValueError(f"fit covers {fit.n_frames} frames, reconstruction has {rec.n_frames}")
    points = rec.points.copy()
    reproj = rec.reproj_error.copy()
    source = rec.source.copy()
    for k in range(1, rec.n_frames):
        if fit.status[k] != FIT_OK:
            points[k] = np.nan
            reproj[k] = np.nan
            source[k] = INVALID
            continue
        points[k] = (rec.points[k] - fit.translation[k]) @ fit.rotation[k]  # row form of R^T(p - t)
    return rebuild_reconstruction(points, reproj, source)


def region_to_nodes(coords: NDArray[np.float64], mask: NDArray[np.bool_]) -> NDArray[np.bool_]:
    """Nodes whose nearest pixel lies inside ``mask`` (the display's rule).

    ``coords`` are ``(n, 2)`` reference pixel ``[x, y]``; non-finite or
    out-of-image nodes are outside.
    """
    m = np.asarray(mask)
    if m.dtype != np.bool_:
        m = m > 0
    h, w = m.shape
    xy = np.nan_to_num(np.asarray(coords, dtype=np.float64).reshape(-1, 2), nan=-1.0)
    ix = np.round(xy[:, 0]).astype(int)
    iy = np.round(xy[:, 1]).astype(int)
    inside = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
    out = np.zeros(xy.shape[0], dtype=bool)
    out[inside] = m[iy[inside], ix[inside]]
    return out


def _subset(node_mask: NDArray[np.bool_] | None, n_pts: int) -> NDArray[np.bool_]:
    if node_mask is None:
        return np.ones(n_pts, dtype=bool)
    sel = np.asarray(node_mask, dtype=bool)
    if sel.shape != (n_pts,):
        raise ValueError(f"node_mask must be ({n_pts},), got {sel.shape}")
    return sel


def _fit_frame(
    a: NDArray[np.float64], b: NDArray[np.float64], mode: str
) -> tuple[NDArray[np.float64] | None, NDArray[np.float64] | None, str]:
    """Rigid motion with ``R a + t ~= b`` (rows are points) and its status."""
    if a.shape[0] < _MIN_POINTS[mode]:
        return None, None, FIT_TOO_FEW
    ca, cb = a.mean(axis=0), b.mean(axis=0)
    if mode == "translation":
        return np.eye(3), cb - ca, FIT_OK
    a0, b0 = a - ca, b - cb
    spread = np.sqrt(np.clip(np.linalg.eigvalsh(a0.T @ a0), 0.0, None))[::-1]
    if spread[0] == 0.0 or spread[1] <= COLLINEAR_TOL * spread[0]:
        return None, None, FIT_DEGENERATE
    rot = _kabsch(a0, b0)
    return rot, cb - rot @ ca, FIT_OK


def _kabsch(a0: NDArray[np.float64], b0: NDArray[np.float64]) -> NDArray[np.float64]:
    """Proper rotation minimizing ``||R a0 - b0||`` for centred point rows."""
    u, _, vt = np.linalg.svd(a0.T @ b0)
    d = 1.0 if np.linalg.det(vt.T @ u.T) >= 0.0 else -1.0  # reflection guard
    return vt.T @ np.diag([1.0, 1.0, d]) @ u.T


def _vee(r: NDArray[np.float64]) -> NDArray[np.float64]:
    """``vee(R - R^T)`` per frame: ``2 sin(angle) * axis`` for a rotation."""
    return np.stack(
        [r[:, 2, 1] - r[:, 1, 2], r[:, 0, 2] - r[:, 2, 0], r[:, 1, 0] - r[:, 0, 1]], axis=1
    )


def _plain(arr: NDArray[np.float64]) -> list:
    """Nested lists with ``NaN`` replaced by ``None`` (strict JSON)."""
    obj = np.asarray(arr, dtype=np.float64).astype(object)
    obj[~np.isfinite(np.asarray(arr, dtype=np.float64))] = None
    return obj.tolist()
