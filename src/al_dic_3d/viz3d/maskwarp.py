"""Warp the LEFT-camera ROI mask into the RIGHT camera (Qt-free) — Batch F2.3.

The user draws the ROI mask on the left camera's frame 1 only; the right-camera
dense render needs an equivalent support. The frame-1 correspondence gives a
scattered mapping ``xL[0] -> xR[0]`` per tracked node, so the mask is warped by
INVERSE lookup: for each right-image pixel, interpolate where it came from in
the left image and sample the left mask there. Inverse warping (vs forward
splatting) leaves no coverage gaps, and holes in the left mask map through as
holes — the renderer's transparency contract is preserved.

Implementation: ``LinearNDInterpolator`` of the backward displacement
``xL0 - xR0`` at the right positions, evaluated on a coarse pixel grid (cheap),
upsampled with ``cv2.resize``, then one full-resolution ``cv2.remap`` (nearest)
of the boolean mask. Pixels outside the correspondence hull have no mapping
(NaN) and become False — the warped support is naturally clipped to the tracked
region, mirroring the F1.5 edge-capped fallback's behavior at the rim.

Rim erosion (fix batch V, low): in the legacy mode the NaN coarse samples
outside the hull are pushed off-image BEFORE the bilinear upsampling, so every
fine pixel within one coarse step of the hull boundary blends in an off-image
coordinate and turns False — the support loses up to ``grid_step`` px at the
rim, and on a real rig ~12 % of the right nodes (the boundary ones) fell
outside it, dropping them from the right camera's auto colour range.
``fill_to_hull=True`` fills those samples with their nearest valid neighbour
before upsampling and clips to the exact hull instead. The display paths use it
through :func:`right_camera_mask`; the compute default is unchanged so the
track-both crack-barrier derivation stays byte-identical.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

#: Coarse-grid spacing (px) for the scattered-interpolation pass.
_GRID_STEP = 8


def _fill_nan_nearest(a: NDArray[np.float64], invalid: NDArray[np.bool_]) -> NDArray[np.float64]:
    """Replace ``invalid`` samples of a 2D array by their nearest valid sample."""
    if not invalid.any():
        return a
    from scipy.ndimage import distance_transform_edt

    idx = distance_transform_edt(invalid, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def _hull_mask(pts: NDArray[np.float64], out_shape: tuple[int, int]) -> NDArray[np.bool_]:
    """Convex hull of *pts* rasterized at full resolution (boundary included)."""
    import cv2

    h, w = int(out_shape[0]), int(out_shape[1])
    hull = cv2.convexHull(np.round(pts).astype(np.int32))
    mask = np.zeros((h, w), np.uint8)
    cv2.fillConvexPoly(mask, hull, 1)
    cv2.polylines(mask, [hull], True, 1, thickness=2)  # rounding never trims the rim
    return mask.astype(bool)


def warp_mask_left_to_right(
    mask_left: NDArray[np.bool_],
    xl0: NDArray[np.float64],
    xr0: NDArray[np.float64],
    out_shape: tuple[int, int],
    *,
    grid_step: int = _GRID_STEP,
    fill_to_hull: bool = False,
) -> NDArray[np.bool_] | None:
    """Warp a left-frame-1 boolean mask into right-frame-1 pixel space.

    Args:
        mask_left: ``(H, W)`` boolean left ROI mask (holes allowed).
        xl0 / xr0: ``(n, 2)`` frame-1 node positions in the left / right image
            (rows may be NaN for invalid correspondences).
        out_shape: ``(H, W)`` of the right image.
        grid_step: coarse-grid spacing for the scattered interpolation.
        fill_to_hull: keep the support up to the exact correspondence hull
            instead of losing up to ``grid_step`` px at the rim (see the module
            docstring). Default False = the legacy compute behaviour.

    Returns:
        ``(H, W)`` boolean right mask, or ``None`` when the correspondence is
        too degenerate to define a mapping (caller falls back to the
        valid-node support).
    """
    import cv2
    from scipy.interpolate import LinearNDInterpolator
    from scipy.spatial import QhullError

    xl = np.asarray(xl0, dtype=np.float64).reshape(-1, 2)
    xr = np.asarray(xr0, dtype=np.float64).reshape(-1, 2)
    if xl.shape != xr.shape:
        raise ValueError(f"xl0/xr0 must match; got {xl.shape} vs {xr.shape}")
    finite = np.isfinite(xl).all(axis=1) & np.isfinite(xr).all(axis=1)
    if finite.sum() < 3:
        return None

    try:
        # Backward displacement right -> left, interpolated at right positions.
        interp = LinearNDInterpolator(xr[finite], xl[finite] - xr[finite])
    except QhullError:
        return None  # collinear correspondence — no 2D mapping

    h, w = int(out_shape[0]), int(out_shape[1])
    step = max(1, int(grid_step))
    # Coarse samples at the BLOCK CENTERS cv2.resize assumes (pixel-center
    # convention): output pixel i reads input coordinate (i+0.5)*nc/n - 0.5,
    # so sample j must sit at fine position (j+0.5)*n/nc - 0.5 — otherwise the
    # upsampled map is shifted by ~step/2 px.
    nc_x = max(2, -(-w // step))  # ceil division
    nc_y = max(2, -(-h // step))
    gx = (np.arange(nc_x) + 0.5) * (w / nc_x) - 0.5
    gy = (np.arange(nc_y) + 0.5) * (h / nc_y) - 0.5
    gxx, gyy = np.meshgrid(gx, gy)
    d = interp(np.column_stack([gxx.ravel(), gyy.ravel()]))  # (m, 2) [dx, dy]
    dx = d[:, 0].reshape(gyy.shape)
    dy = d[:, 1].reshape(gyy.shape)
    if not np.isfinite(dx).any():
        return None

    if fill_to_hull:
        # Nearest-valid fill keeps the bilinear upsampling finite right up to
        # the hull; the exact hull below then decides the support boundary.
        invalid = ~(np.isfinite(dx) & np.isfinite(dy))
        src_x = (gxx + _fill_nan_nearest(dx, invalid)).astype(np.float32)
        src_y = (gyy + _fill_nan_nearest(dy, invalid)).astype(np.float32)
    else:
        # Left source coordinates per coarse right pixel; NaN (outside the hull)
        # becomes an out-of-image coordinate so remap's border fills False.
        src_x = np.nan_to_num(gxx + dx, nan=-1e4).astype(np.float32)
        src_y = np.nan_to_num(gyy + dy, nan=-1e4).astype(np.float32)
    map_x = cv2.resize(src_x, (w, h), interpolation=cv2.INTER_LINEAR)
    map_y = cv2.resize(src_y, (w, h), interpolation=cv2.INTER_LINEAR)

    warped = cv2.remap(
        (np.asarray(mask_left) > 0).astype(np.uint8),
        map_x,
        map_y,
        interpolation=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    ).astype(bool)
    if fill_to_hull:
        warped &= _hull_mask(xr[finite], (h, w))
    return warped


def right_camera_mask(
    mask_left: NDArray[np.bool_] | None,
    xl0: NDArray[np.float64],
    xr0: NDArray[np.float64],
    out_shape: tuple[int, int],
) -> NDArray[np.bool_] | None:
    """The drawn LEFT ROI as the RIGHT camera's display support (never raises).

    The one helper every right-camera DISPLAY path should call — canvas,
    image / animation export and the export Preview — so they all show the same
    support. Uses the rim-preserving warp (``fill_to_hull=True``). Returns None
    (callers fall back to the valid-node hull support) when there is no mask,
    the correspondence is degenerate, or the warp fails.
    """
    if mask_left is None:
        return None
    try:
        return warp_mask_left_to_right(mask_left, xl0, xr0, out_shape, fill_to_hull=True)
    except Exception:  # noqa: BLE001 - display support only; the caller falls back
        return None
