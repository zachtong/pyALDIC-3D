"""Drive a whole ``Reconstruction3D`` through surface-strain (Qt-free).

Per frame: (optionally smooth the displacement,) fit local tangent-frame
displacement gradients, and reduce to Green-Lagrange strain + invariants. The VSG
is a square pixel window of side ``strain_length = (strain_size-1)*winstepsize+1``
(docs/strain3d_math.md §1). Downstream of ``reconstruct``; consumes only the
``Reconstruction3D`` + the reference 2D node coords.

P3.5: the per-frame gradient fits share ONE neighbour cache (the VSG table is
rebuilt only when the validity pattern changes), the fits themselves are
batched (see :mod:`al_dic_3d.strain3d.gradients`), and the frame loop reports
``progress_cb(frac, msg)`` and honours a cooperative ``stop_event``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.strain3d import kernels
from al_dic_3d.strain3d.edgetrim import edge_trim_mask
from al_dic_3d.strain3d.gradients import MIN_NEIGHBORS, fit_gradients, strain_tensor
from al_dic_3d.strain3d.model import STRAIN_FIELDS, StrainResult3D

if TYPE_CHECKING:
    import threading

    from al_dic_3d.reconstruct import Reconstruction3D

ProgressCb = Callable[[float, str], None]


def _smooth_displacement_loop(
    ref_2d: NDArray[np.float64],
    disp: NDArray[np.float64],
    sigma: float,
) -> NDArray[np.float64]:
    """Reference per-node smoothing implementation (pre-P3.5; parity tests)."""
    from scipy.spatial import cKDTree

    ref_2d = np.asarray(ref_2d, dtype=np.float64).reshape(-1, 2)
    disp = np.asarray(disp, dtype=np.float64).reshape(-1, 3)
    out = np.full_like(disp, np.nan)
    finite = np.isfinite(disp).all(axis=1) & np.isfinite(ref_2d).all(axis=1)
    if not finite.any():
        return out

    src_idx = np.where(finite)[0]
    tree = cKDTree(ref_2d[finite])
    for i in src_idx:
        nbr = tree.query_ball_point(ref_2d[i], r=3.0 * sigma, p=2)
        if not nbr:
            out[i] = disp[i]
            continue
        sel = src_idx[nbr]
        d2 = np.sum((ref_2d[sel] - ref_2d[i]) ** 2, axis=1)
        w = np.exp(-d2 / (2.0 * sigma**2))
        out[i] = (w[:, None] * disp[sel]).sum(axis=0) / w.sum()
    return out


def smooth_displacement(
    ref_2d: NDArray[np.float64],
    disp: NDArray[np.float64],
    sigma: float,
) -> NDArray[np.float64]:
    """NaN-aware Gaussian smoothing of a scattered displacement field (funSmoothDisp idea).

    Row-normalized Gaussian weights over the ``3*sigma`` pixel neighbourhood (in the
    reference image), applied per component. Invalid (NaN) nodes neither contribute
    nor receive an estimate. Vectorized (P3.5): one batched ``query_ball_point``
    plus a mask-padded weighted reduction instead of a per-node Python loop.
    """
    from scipy.spatial import cKDTree

    ref_2d = np.asarray(ref_2d, dtype=np.float64).reshape(-1, 2)
    disp = np.asarray(disp, dtype=np.float64).reshape(-1, 3)
    out = np.full_like(disp, np.nan)
    finite = np.isfinite(disp).all(axis=1) & np.isfinite(ref_2d).all(axis=1)
    if not finite.any():
        return out

    src_idx = np.where(finite)[0]
    pts = ref_2d[finite]
    vals = disp[finite]
    lists = cKDTree(pts).query_ball_point(pts, r=3.0 * sigma, p=2)
    counts = np.fromiter((len(x) for x in lists), dtype=np.int64, count=len(lists))
    k_max = int(counts.max()) if counts.size else 0
    if k_max == 0:  # no neighbourhood anywhere: identity (matches the loop)
        out[src_idx] = vals
        return out
    nbr = np.full((len(lists), k_max), -1, dtype=np.int64)
    for row, lst in enumerate(lists):
        nbr[row, : len(lst)] = lst

    pad = nbr < 0
    safe = np.where(pad, 0, nbr)
    d2 = ((pts[safe] - pts[:, None, :]) ** 2).sum(axis=2)  # (m, k_max)
    w = np.exp(-d2 / (2.0 * sigma**2))
    w[pad] = 0.0
    smoothed = (w[..., None] * vals[safe]).sum(axis=1) / w.sum(axis=1)[:, None]
    # A node with no neighbour keeps its own value (loop-parity; r > 0 always
    # includes the node itself, so this is defensive).
    empty = counts == 0
    if empty.any():
        smoothed[empty] = vals[empty]
    out[src_idx] = smoothed
    return out


def compute_surface_strain(
    reconstruction: Reconstruction3D,
    ref_2d: NDArray[np.float64],
    *,
    strain_size: int = 5,
    winstepsize: int = 16,
    coordinate: str = "local",
    specimen_R: NDArray[np.float64] | None = None,
    min_neighbors: int = MIN_NEIGHBORS,
    smooth_sigma: float = 0.0,
    strain_type: str = "green_lagrange",
    edge_trim_alpha: float = 0.0,
    progress_cb: ProgressCb | None = None,
    stop_event: threading.Event | Callable[[], bool] | None = None,
) -> StrainResult3D:
    """Compute surface strain for every frame of a reconstruction.

    Args:
        reconstruction: the 3D points/displacement (``points[0]`` = reference surface).
        ref_2d: ``(n_pts, 2)`` reference node coords in the left image (VSG search).
        strain_size: VSG size in grid steps (odd). ``strain_length =
            (strain_size-1)*winstepsize+1`` px; the gauge radius is half of that.
        winstepsize: node grid spacing in pixels.
        coordinate: ``"local"`` (default), ``"camera0"``, or ``"specific"``.
        specimen_R: specimen frame for ``coordinate="specific"``.
        smooth_sigma: if > 0, Gaussian-smooth the displacement first (px).
        strain_type: finite-strain measure (Q3): ``"green_lagrange"``
            (default), ``"infinitesimal"``, or ``"almansi"`` — same gradient
            fit / tangent frame, different reduction (see
            :func:`al_dic_3d.strain3d.gradients.strain_tensor`).
        edge_trim_alpha: Q4 edge trim — NaN the strain of nodes closer than
            ``alpha * VSG-radius`` (px, on ``ref_2d``) to any invalid/missing
            node (one-sided gauge support). ``0`` (default) disables; the GUI
            panel defaults to the 2D-calibrated 0.7. ``min_neighbors`` stays
            the hard floor beneath this.
        progress_cb: optional ``(fraction, message)`` callback, one tick per frame.
        stop_event: cooperative cancel — a ``threading.Event`` (or any
            ``() -> bool`` callable), checked before every frame; tripping it
            raises ``RuntimeError("cancelled")``.

    Returns:
        A :class:`StrainResult3D`; frame 0 is all-zero strain (zero displacement).
    """
    ref_2d = np.asarray(ref_2d, dtype=np.float64).reshape(-1, 2)
    ref_3d = np.asarray(reconstruction.points[0], dtype=np.float64)
    n_frames, n_pts = reconstruction.n_frames, reconstruction.n_pts

    strain_length = (strain_size - 1) * winstepsize + 1
    vsg_radius = 0.5 * strain_length
    stop_fn = stop_event.is_set if hasattr(stop_event, "is_set") else stop_event
    neighbor_cache: dict = {}  # one VSG table per validity pattern (P3.5)
    kernels.warmup()  # R3: JIT compile/cache-load BEFORE the loop (honest frame ETAs)

    fields = {name: np.full((n_frames, n_pts), np.nan, dtype=np.float64) for name in STRAIN_FIELDS}
    trim_cache: dict = {}  # one trim mask per (validity pattern, alpha)
    n_trimmed = np.zeros(n_frames, dtype=np.int64) if edge_trim_alpha > 0 else None
    for k in range(n_frames):
        if stop_fn is not None and stop_fn():
            raise RuntimeError("cancelled")
        disp = np.asarray(reconstruction.displacement[k], dtype=np.float64)
        if smooth_sigma > 0:
            disp = smooth_displacement(ref_2d, disp, smooth_sigma)
        coef = fit_gradients(
            ref_2d,
            ref_3d,
            disp,
            vsg_radius,
            coordinate=coordinate,
            specimen_R=specimen_R,
            min_neighbors=min_neighbors,
            neighbor_cache=neighbor_cache,
        )
        strain = strain_tensor(coef, strain_type)
        for name in STRAIN_FIELDS:
            fields[name][k] = strain[name]
        if n_trimmed is not None:
            # Q4: NaN the strain (never the displacement) inside the
            # alpha * VSG-radius band around invalid/missing nodes — the
            # same finite mask fit_gradients used for this frame.
            finite = (
                np.isfinite(ref_2d).all(1) & np.isfinite(ref_3d).all(1) & np.isfinite(disp).all(1)
            )
            trim = edge_trim_mask(ref_2d, finite, vsg_radius, edge_trim_alpha, cache=trim_cache)
            if trim.any():
                for name in STRAIN_FIELDS:
                    fields[name][k, trim] = np.nan
            n_trimmed[k] = int(trim.sum())
        if progress_cb is not None:
            progress_cb((k + 1) / n_frames, f"strain frame {k + 1}/{n_frames}")

    return StrainResult3D(**fields, n_trimmed=n_trimmed)
