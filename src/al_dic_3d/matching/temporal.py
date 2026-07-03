"""Per-camera temporal tracking and scattered resampling (Qt-free).

Drives the 2D engine's accumulative pipeline (:func:`al_dic.run_aldic`) on ONE
camera stream from a fixed reference mesh, reading the **cumulative** node
displacement (``FrameResult.U_accum``) on the frame-1 mesh — never rebuilding the
mesh per frame (the MATLAB per-frame rebuild is a known hazard). The right camera
is tracked on its own dense grid; :func:`resample_to_points` then interpolates
that field onto the scattered correspondence points.

Every ``al_dic`` symbol imported here is recorded in ``docs/DEPENDS_ON_2D.md``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from al_dic.core.data_structures import DICMesh, DICPara, split_uv
from al_dic.core.pipeline import run_aldic
from al_dic.mesh.mesh_setup import mesh_setup
from al_dic.solver.seed_prop_pipeline import build_grid_for_roi
from numpy.typing import NDArray


@dataclass(frozen=True)
class TemporalField:
    """Cumulative per-frame node displacement from one accumulative DIC run.

    ``u_accum[0]`` is all-zero (the reference frame); ``u_accum[k]`` is the
    frame-0 -> frame-k cumulative displacement on ``ref_coords`` nodes.
    """

    ref_coords: NDArray[np.float64]  # (n, 2) [x, y] frame-1 mesh nodes
    u_accum: NDArray[np.float64]  # (n_frames, n, 2) [u, v]; [0] == 0
    valid: NDArray[np.bool_]  # (n_frames, n)

    @property
    def n_frames(self) -> int:
        return int(self.u_accum.shape[0])


def build_grid_mesh(
    para: DICPara,
    img_h: int,
    img_w: int,
) -> DICMesh:
    """Build a uniform Q8 reference mesh over ``para``'s ROI (frame-1 material points).

    Reuses the exact FFT-path grid (:func:`build_grid_for_roi` + :func:`mesh_setup`)
    so node coordinates match what ``run_aldic`` would generate internally.
    """
    x0, y0 = build_grid_for_roi(para, img_h, img_w)
    return mesh_setup(x0, y0, para)


def temporal_track(
    frames: list[NDArray[np.float64]],
    mesh: DICMesh,
    para: DICPara,
    masks: list[NDArray[np.float64]] | None = None,
    u0: NDArray[np.float64] | None = None,
) -> TemporalField:
    """Track one camera's frames from a fixed reference mesh (accumulative).

    Args:
        frames: ``[f0, f1, ...]`` raw ``(H, W)`` float64 images; ``f0`` is the
            reference and must correspond to ``mesh``'s coordinate frame.
        mesh: the external reference mesh (its ``coordinates_fem`` are the tracked
            material points). Not rebuilt per frame.
        para: local-only accumulative ``DICPara``.
        masks: optional per-frame masks (same length as ``frames``). Default
            all-ones — which keeps the external mesh byte-identical so the
            returned ``ref_coords`` equal ``mesh.coordinates_fem`` exactly.
        u0: optional frame-0->frame-1 seed of length ``2*n_nodes``. ``None`` lets
            ``run_aldic`` compute an FFT integer guess (robust to larger motion).

    Returns:
        A :class:`TemporalField`. Raises ``RuntimeError`` if a frame fails to
        solve (``run_aldic`` None-filters failures, breaking positional
        alignment — a partial run is surfaced rather than silently misaligned).
    """
    if len(frames) < 2:
        raise ValueError(f"need >=2 frames, got {len(frames)}")
    h, w = frames[0].shape
    if masks is None:
        masks = [np.ones((h, w), dtype=np.float64) for _ in frames]
    if len(masks) != len(frames):
        raise ValueError(f"masks ({len(masks)}) must match frames ({len(frames)})")

    result = run_aldic(
        para,
        [np.ascontiguousarray(f, dtype=np.float64) for f in frames],
        [np.ascontiguousarray(m, dtype=np.float64) for m in masks],
        compute_strain=False,
        mesh=mesh,
        U0=u0,
    )

    ref_coords = np.asarray(result.dic_mesh.coordinates_fem, dtype=np.float64)
    n = ref_coords.shape[0]
    n_frames = len(frames)
    if len(result.result_disp) != n_frames - 1:
        raise RuntimeError(
            f"run_aldic returned {len(result.result_disp)} deformed frames for "
            f"{n_frames - 1} expected — a frame failed and positional alignment "
            f"is unreliable (partial-run handling is deferred to Phase 2)."
        )

    u_accum = np.zeros((n_frames, n, 2), dtype=np.float64)
    valid = np.zeros((n_frames, n), dtype=bool)
    valid[0] = True  # reference frame: zero displacement, all valid
    for k, fr in enumerate(result.result_disp, start=1):
        vec = fr.U_accum if fr.U_accum is not None else fr.U
        uu, vv = split_uv(np.asarray(vec, dtype=np.float64))
        u_accum[k, :, 0] = uu
        u_accum[k, :, 1] = vv
        valid[k] = np.isfinite(uu) & np.isfinite(vv)

    return TemporalField(ref_coords=ref_coords, u_accum=u_accum, valid=valid)


def resample_to_points(
    ref_coords: NDArray[np.float64],
    values: NDArray[np.float64],
    query: NDArray[np.float64],
    *,
    fill_nearest: bool = True,
) -> NDArray[np.float64]:
    """Interpolate a scattered vector field onto arbitrary query points (NaN-aware).

    Builds a Delaunay-based linear interpolant from the FINITE rows of ``values``
    (so NaN/invalid nodes never contaminate a neighborhood) and evaluates it at
    ``query``. Points outside the convex hull are ``NaN`` from the linear pass; if
    ``fill_nearest`` they are back-filled with the nearest finite node (a mild,
    clearly-bounded extrapolation for corr points that drift just past the hull).

    Args:
        ref_coords: ``(n, 2)`` field node coordinates ``[x, y]``.
        values: ``(n, 2)`` field values ``[u, v]`` (rows may be ``NaN``).
        query: ``(m, 2)`` points to sample at.

    Returns:
        ``(m, 2)`` interpolated values; ``NaN`` rows where no estimate exists.
    """
    from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

    ref = np.asarray(ref_coords, dtype=np.float64).reshape(-1, 2)
    val = np.asarray(values, dtype=np.float64).reshape(-1, 2)
    q = np.asarray(query, dtype=np.float64).reshape(-1, 2)

    finite = np.isfinite(val).all(axis=1) & np.isfinite(ref).all(axis=1)
    out = np.full((q.shape[0], 2), np.nan, dtype=np.float64)
    if finite.sum() < 3:
        return out  # Delaunay needs >=3 non-collinear points

    src = ref[finite]
    dst = val[finite]
    lin = LinearNDInterpolator(src, dst)
    out[:] = lin(q)

    if fill_nearest:
        # Only fill FINITE queries that fell outside the hull; a non-finite query
        # row has no estimate and must stay NaN (documented contract) — never
        # feed it to the KD-tree (scipy raises on non-finite query points).
        missing = (~np.isfinite(out).all(axis=1)) & np.isfinite(q).all(axis=1)
        if missing.any():
            nearest = NearestNDInterpolator(src, dst)
            out[missing] = nearest(q[missing])
    return out
