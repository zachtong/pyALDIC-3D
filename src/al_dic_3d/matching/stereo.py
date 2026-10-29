"""Frame-1 cross-camera stereo matcher (Qt-free) — the L1->R1 correspondence.

Ports the *math* of ``StereoMatch_STAQ.m`` without its MATLAB quadtree/RD
bookkeeping: given the reference material points in the left image, seed each
one with an integer NCC disparity (``cv2.matchTemplate`` TM_CCOEFF_NORMED,
honoring a coarse ``disparity_offset`` prior for wide baselines), then refine to
sub-pixel with the scattered-point local IC-GN primitive :func:`match_points`.

With a calibrated rig the integer search runs along each point's epipolar line
(a band ``band_px`` wide, ``search_radius`` long) instead of a square window:
the match lies on the line up to the calibration error, and only its position
along the line depends on the unknown depth. The images are never rectified;
the line is traced through the full distortion model and linearised locally.

Reference = LEFT image, deformed = RIGHT image; the displacement solved IS the
left->right disparity, so ``right_pts == left_pts + d`` (01 §E). Invalid points
propagate as ``NaN`` with ``valid=False``.
"""

from __future__ import annotations

import numpy as np
from al_dic.core.data_structures import DICPara
from numpy.typing import NDArray

from al_dic_3d.matching.contracts import DisparityField
from al_dic_3d.matching.primitives import match_points

# Points per task of the threaded NCC seed search.
_NCC_SEED_CHUNK = 256

#: Default half-width (px) of the epipolar band the frame-1 seed search scans;
#: 0 searches the full square window. A genuine link sits ~0.1 px from its line
#: on a good calibration; the band is never narrower than the epipolar limit
#: (:func:`search_band_px`), so a link the limit would accept can be found.
STEREO_BAND_PX = 3.0

#: (foot points (n, 2), unit tangents (n, 2), half-widths px (n,) or scalar).
Band = tuple[NDArray[np.float64], NDArray[np.float64], "float | NDArray[np.float64]"]


def search_band_px(band_px: float | None, epipolar_max_px: float | None) -> float:
    """The band half-width to search, or 0 for the square window.

    The band trusts the calibration, so it is off (0) whenever the epipolar
    check is off; otherwise it is never narrower than the epipolar limit.
    """
    band = float(band_px or 0.0)
    limit = float(epipolar_max_px or 0.0)
    if not (np.isfinite(band) and np.isfinite(limit)) or band <= 0 or limit <= 0:
        return 0.0
    return max(band, limit)


def epipolar_line_frames(
    rig,
    left_pts: NDArray[np.float64],
    centres: NDArray[np.float64],
    cam_left: str = "L",
    cam_right: str = "R",
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Each left point's right-image epipolar line, linearised near its search centre.

    Returns ``(foot, tangent)``: the point of the epipolar curve (raw pixels,
    full distortion model) at the depth that best explains ``centres``, and the
    curve's unit tangent there. Rows are NaN where a point or centre is not
    finite or the best depth is not in front of the camera.
    """
    foot, tangent, _ = _line_frames(rig, left_pts, centres, cam_left, cam_right, search=None)
    return foot, tangent


def epipolar_band(
    rig,
    left_pts: NDArray[np.float64],
    centres: NDArray[np.float64],
    search: int,
    band_px: float,
    cam_left: str = "L",
    cam_right: str = "R",
) -> Band:
    """The band the seed search scans for each point (see :func:`_ncc_seed`).

    The straight band along the tangent is widened, point by point, by how far
    the true (distorted) epipolar curve bows away from that tangent within
    ``search`` px of the foot, so a strongly distorted lens and a long search
    keep the curve inside the band.
    """
    foot, tangent, bow = _line_frames(rig, left_pts, centres, cam_left, cam_right, search=search)
    return foot, tangent, float(band_px) + np.nan_to_num(bow, nan=0.0)


def _line_frames(rig, left_pts, centres, cam_left, cam_right, *, search):
    """``(foot, tangent, bow)``; ``bow`` (n,) is 0 without ``search``."""
    from al_dic_3d.calibration import project_points, undistort_points

    pl = np.asarray(left_pts, dtype=np.float64).reshape(-1, 2)
    pc = np.asarray(centres, dtype=np.float64).reshape(-1, 2)
    n = pl.shape[0]
    foot = np.full((n, 2), np.nan)
    tangent = np.full((n, 2), np.nan)
    bow = np.zeros(n)
    ok = np.isfinite(pl).all(axis=1) & np.isfinite(pc).all(axis=1)
    if not ok.any():
        return foot, tangent, bow
    intr_l, intr_r = rig.cameras[cam_left], rig.cameras[cam_right]
    R_l, T_l = rig.pose(cam_left)
    R_r, T_r = rig.pose(cam_right)
    R = R_r @ R_l.T  # X_R = R X_L + T
    T = T_r - R @ T_l
    m = int(ok.sum())
    ray = np.column_stack([undistort_points(pl[ok], intr_l), np.ones(m)]) @ R.T
    xr = undistort_points(pc[ok], intr_r)
    # Depth along the left ray whose right projection is nearest the centre:
    # (R x_L lam + T)_xy - x_R (R x_L lam + T)_z = 0, solved in least squares.
    a = ray[:, :2] - xr * ray[:, 2:3]
    b = T[None, :2] - xr * T[2]
    with np.errstate(invalid="ignore", divide="ignore"):
        lam = -(a * b).sum(axis=1) / (a * a).sum(axis=1)

    def project(scale) -> NDArray[np.float64]:
        pts = (lam * scale)[:, None] * ray + T[None, :]
        return project_points(pts, intr_r, np.eye(3), np.zeros(3))

    good = np.isfinite(lam) & (lam > 0)
    step = project(1.0 + 1e-3) - project(1.0 - 1e-3)
    norm = np.linalg.norm(step, axis=1, keepdims=True)
    good &= np.isfinite(norm[:, 0]) & (norm[:, 0] > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        t = step / norm
    f = project(1.0)
    idx = np.flatnonzero(ok)
    foot[idx[good]] = f[good]
    tangent[idx[good]] = t[good]
    if search:
        # Depth change that moves the projection ~search px, then the distance
        # of the curve's points there from the tangent line through the foot.
        with np.errstate(invalid="ignore", divide="ignore"):
            ds = np.clip(float(search) * 2e-3 / norm[:, 0], 0.0, 0.9)
        dev = np.zeros(m)
        for sign in (-1.0, 1.0):
            rel = project(1.0 + sign * ds) - f
            dev = np.fmax(dev, np.abs(rel[:, 0] * t[:, 1] - rel[:, 1] * t[:, 0]))
        bow[idx[good]] = dev[good]
    return foot, tangent, bow


def _ncc_seed(
    left: NDArray[np.float64],
    right: NDArray[np.float64],
    points: NDArray[np.float64],
    offset: tuple[float, float] | NDArray[np.float64],
    search: int,
    half: int,
    band: Band | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """Per-point integer disparity via local NCC template matching.

    For each left point ``p`` a ``(2*half+1)`` template from ``left`` is matched
    inside a ``+/- search`` window of ``right`` centered at ``round(p + offset)``.
    ``offset`` is one ``(dx, dy)`` for every point, or an ``(n, 2)`` array of
    per-point centres (the automatic disparity prior; non-finite rows centre on
    zero disparity). With ``band = (foot, tangent, width)`` only the positions
    within ``width`` px (one value, or one per point) of the point's epipolar
    line and ``search`` px along it of ``foot`` are candidates
    (:func:`epipolar_band`). Returns
    ``(seed (n,2), ok (n,))`` — the integer ``[du, dv]`` seed and whether the
    template and search windows fit inside both images.
    """
    import cv2

    hL, wL = left.shape
    hR, wR = right.shape
    lf = left.astype(np.float32)
    rf = right.astype(np.float32)
    n = points.shape[0]
    off = np.asarray(offset, dtype=np.float64)
    if off.ndim == 1:
        off = np.tile(off.reshape(2), (n, 1))
    if off.shape != (n, 2):
        raise ValueError(f"offset must be (dx, dy) or ({n}, 2), got {off.shape}")
    off = np.where(np.isfinite(off), off, 0.0)

    side = 2 * half + 1  # template edge
    seed = np.zeros((n, 2), dtype=np.float64)
    ok = np.zeros(n, dtype=bool)
    geo = None if band is None else _BandGeometry(band, search, half, rf.shape)

    def one(i: int) -> None:
        x, y = points[i]
        if not (np.isfinite(x) and np.isfinite(y)):
            return
        xi, yi = int(round(x)), int(round(y))
        # Template around p in the LEFT image.
        if xi - half < 0 or yi - half < 0 or xi + half >= wL or yi + half >= hL:
            return
        tmpl = lf[yi - half : yi + half + 1, xi - half : xi + half + 1]

        if geo is not None and geo.usable[i]:
            hit = geo.peak(i, rf, tmpl)
            if hit is not None:
                seed[i] = (hit[0] - x, hit[1] - y)
                ok[i] = True
            return

        # Search window in the RIGHT image, centered at round(p + offset) and
        # CLAMPED to image bounds (asymmetric near edges, like seed_single_point_fft)
        # so a point whose one-sided disparity would push a symmetric window
        # off-image stays alive as long as the clamped window still holds the match.
        cx, cy = int(round(x + off[i, 0])), int(round(y + off[i, 1]))
        x_lo = max(0, cx - half - search)
        x_hi = min(wR, cx + half + search + 1)
        y_lo = max(0, cy - half - search)
        y_hi = min(hR, cy + half + search + 1)
        if x_hi - x_lo < side or y_hi - y_lo < side:
            return  # clamped window smaller than the template — no valid position
        win = rf[y_lo:y_hi, x_lo:x_hi]

        ncc = cv2.matchTemplate(win, tmpl, cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(ncc)  # max_loc = (col, row) of top-left
        pc, pr = max_loc
        # Matched template center in RIGHT pixel coords.
        matched_x = x_lo + pc + half
        matched_y = y_lo + pr + half
        seed[i, 0] = matched_x - x  # du
        seed[i, 1] = matched_y - y  # dv
        ok[i] = True

    # Points are independent and cv2.matchTemplate releases the GIL, so the
    # per-point search runs on a small pool (fix batch V: 27k points took ~6 s
    # single-threaded before the first progress message). Each task writes its
    # own row, so the result is identical to the serial loop.
    from al_dic_3d.matching.gate import _gate_workers

    def run(lo: int) -> None:
        for i in range(lo, min(n, lo + _NCC_SEED_CHUNK)):
            one(i)

    workers = _gate_workers()
    if workers <= 1 or n <= _NCC_SEED_CHUNK:
        for lo in range(0, n, _NCC_SEED_CHUNK):
            run(lo)
    else:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=workers) as pool:
            # list() re-raises the first worker exception, if any.
            list(pool.map(run, range(0, n, _NCC_SEED_CHUNK)))
    return seed, ok


class _BandGeometry:
    """Every point's band, laid out once (vectorised) for the per-point search.

    A band is the segment ``foot ± search·t`` widened by ``width`` px to both
    sides. Its pixel box (template centres that fit in the image) is matched in
    one ``cv2.matchTemplate`` call; for a slanted band the NCC map is then masked
    to the band. A band within half a pixel of its box (the usual side-by-side or
    stacked rig, whose lines run nearly along the image axes) needs no mask.
    """

    def __init__(self, band: Band, search: int, half: int, shape: tuple[int, int]) -> None:
        foot, tangent, width = band
        h, w = shape
        self.usable = np.isfinite(foot).all(axis=1) & np.isfinite(tangent).all(axis=1)
        f = np.where(self.usable[:, None], foot, 0.0)
        t = np.where(self.usable[:, None], tangent, np.array([1.0, 0.0]))
        along = float(search) * t
        widths = np.broadcast_to(np.asarray(width, dtype=np.float64), (t.shape[0],))
        across = widths[:, None] * np.column_stack([-t[:, 1], t[:, 0]])
        corners = np.stack(
            [f - along - across, f + along - across, f + along + across, f - along + across], axis=1
        )
        self.x0 = np.maximum(half, np.floor(corners[..., 0].min(axis=1))).astype(np.int64)
        self.x1 = np.minimum(w - 1 - half, np.ceil(corners[..., 0].max(axis=1))).astype(np.int64)
        self.y0 = np.maximum(half, np.floor(corners[..., 1].min(axis=1))).astype(np.int64)
        self.y1 = np.minimum(h - 1 - half, np.ceil(corners[..., 1].max(axis=1))).astype(np.int64)
        origin = np.stack([self.x0, self.y0], axis=1)[:, None, :]
        # Outlines in the NCC map's frame, 1/16 px precision (cv2 shift=4).
        self.quads = np.round((corners - origin) * 16).astype(np.int32)
        self.ends = np.round((np.stack([f - along, f + along], axis=1) - origin) * 16).astype(
            np.int32
        )
        self.boxed = float(search) * np.minimum(np.abs(t[:, 0]), np.abs(t[:, 1])) <= 0.5
        self.half = int(half)

    def peak(
        self, i: int, rf: NDArray[np.float32], tmpl: NDArray[np.float32]
    ) -> tuple[int, int] | None:
        """Template-centre pixel of the best NCC inside band ``i``, or None if none fits."""
        import cv2

        x0, x1, y0, y1 = int(self.x0[i]), int(self.x1[i]), int(self.y0[i]), int(self.y1[i])
        if x1 < x0 or y1 < y0:
            return None
        hf = self.half
        ncc = cv2.matchTemplate(
            rf[y0 - hf : y1 + hf + 1, x0 - hf : x1 + hf + 1], tmpl, cv2.TM_CCOEFF_NORMED
        )
        if self.boxed[i]:
            _, _, _, (col, row) = cv2.minMaxLoc(ncc)
        else:
            allowed = np.zeros(ncc.shape, dtype=np.uint8)
            cv2.fillConvexPoly(allowed, self.quads[i], 1, cv2.LINE_8, 4)
            # The line itself, so that a band thinner than a pixel keeps candidates.
            a, b = self.ends[i]
            cv2.line(allowed, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1, 1, cv2.LINE_8, 4)
            _, _, _, (col, row) = cv2.minMaxLoc(ncc, mask=allowed)
            if col < 0:  # the band lies wholly off the image
                return None
        return x0 + col, y0 + row


def stereo_match_pair(
    left: NDArray[np.float64],
    right: NDArray[np.float64],
    points_left: NDArray[np.float64],
    para: DICPara,
    *,
    disparity_offset: tuple[float, float] | NDArray[np.float64] | None = None,
    search_radius: int = 40,
    tol: float = 1e-3,
    frame_idx: int = 0,
    seed_u0: NDArray[np.float64] | None = None,
    rig=None,
    band_px: float = 0.0,
) -> DisparityField:
    """Match reference left points into the right image (frame-1 stereo).

    Args:
        left, right: ``(H, W)`` float64 images (same intensity scale). ``left`` is
            the reference; ``right`` is where correspondences are found.
        points_left: ``(n, 2)`` ``[x, y]`` reference material points in ``left``.
        para: local-only ``DICPara`` (see :func:`make_local_dicpara`); its
            ``winsize`` sizes both the NCC template and the IC-GN subset, and its
            ``img_ref_mask`` (if any) gates reference-subset validity.
        disparity_offset: coarse ``(dx, dy)`` prior recentering the NCC search
            (for large baselines), or an ``(n, 2)`` per-point centre (see
            :mod:`al_dic_3d.matching.disparity_prior`). ``None`` -> zero offset.
        search_radius: NCC half-window (pixels) around the (offset) center; with
            a band, the half-length searched along the epipolar line.
        tol: IC-GN convergence tolerance (``1e-3``, matching StereoMatch_STAQ).
        frame_idx: frame this disparity belongs to (``0`` for the frame-1 match).
        seed_u0: optional ``(n, 2)`` per-point disparity prior from multi-seed
            F-aware propagation (Batch S). Where a row is finite it REPLACES the
            integer NCC seed for that point (a strong, spatially-varying prior
            for wide baselines); NaN rows keep the per-point NCC seed. ``None``
            (the default, single-seed / FFT path) is byte-identical to before.
        rig, band_px: with a calibrated ``rig`` and ``band_px > 0`` the NCC
            search covers only the positions within ``band_px`` of each point's
            epipolar line (see :func:`search_band_px` for the width to pass);
            otherwise the square window.

    Returns:
        A :class:`DisparityField` with ``left_pts``, disparity ``d`` (``right_pts
        = left_pts + d``), per-point ``znssd`` and ``valid``. Points whose NCC
        window falls off the image, or whose IC-GN fails, are ``NaN``/invalid.
    """
    left = np.ascontiguousarray(left, dtype=np.float64)
    right = np.ascontiguousarray(right, dtype=np.float64)
    pts = np.ascontiguousarray(points_left, dtype=np.float64).reshape(-1, 2)
    half = int(para.winsize) // 2
    offset = (0.0, 0.0) if disparity_offset is None else disparity_offset

    # (1) integer NCC seed per point (spatially-varying disparity prior), along
    # the epipolar line when the rig is known.
    band = None
    if rig is not None and band_px and band_px > 0:
        off = np.asarray(offset, dtype=np.float64)
        if off.ndim == 1:
            off = np.tile(off.reshape(2), (pts.shape[0], 1))
        off = np.where(np.isfinite(off), off, 0.0)
        band = epipolar_band(rig, pts, pts + off, int(search_radius), float(band_px))
    seed, seed_ok = _ncc_seed(left, right, pts, offset, int(search_radius), half, band=band)

    # (1b) override with the propagated per-point disparity where it exists — a
    # far stronger prior than the recentred NCC search on wide-baseline gradients.
    if seed_u0 is not None:
        su = np.asarray(seed_u0, dtype=np.float64).reshape(-1, 2)
        if su.shape[0] == seed.shape[0]:
            fin = np.isfinite(su).all(axis=1)
            seed[fin] = su[fin]

    # (2) sub-pixel local IC-GN refinement at the scattered points.
    u, znssd, valid = match_points(left, right, pts, seed, para, tol=tol)

    # A point is only a real correspondence if BOTH the NCC seed fit and IC-GN
    # converged. Seed-failed points carry NaN disparity.
    d = u.astype(np.float64).copy()
    good = valid & seed_ok
    d[~good] = np.nan
    znssd = znssd.copy()
    znssd[~good] = np.nan

    return DisparityField(
        frame_idx=int(frame_idx),
        left_pts=pts,
        d=d,
        znssd=znssd,
        valid=good,
    )


# --------------------------------------------------------------------------- #
# Stereo-link acceptance (fix batch V, finding H4)
# --------------------------------------------------------------------------- #

#: Default ZNSSD ceiling for a stereo link (ZNCC >= 0.7). Genuine links on real
#: stereo data score a median ~0.02 (p90 < 0.1); the garbage links the old
#: "converged == accepted" rule let through scored > 1.
STEREO_ZNSSD_MAX = 0.6
#: Default ceiling on a link's distance to its epipolar line, in right-image
#: pixels. Genuine links sit at ~0.1 px (p90 0.16 px on Challenge 1.0 S3); the
#: rejected ones were tens of pixels off. 2 px leaves room for a mediocre
#: calibration while still catching every false lock.
STEREO_EPIPOLAR_MAX_PX = 2.0


def epipolar_distance_px(
    rig,
    left_pts: NDArray[np.float64],
    right_pts: NDArray[np.float64],
    cam_left: str = "L",
    cam_right: str = "R",
) -> NDArray[np.float64]:
    """Distance of each right point to the epipolar line of its left point (px).

    Both points are undistorted to normalized coordinates first (the rig's full
    distortion model), the line ``l = E x_L`` comes from the essential matrix
    ``E = [T]_x R`` of ``X_R = R X_L + T``, and the normalized distance is scaled
    to pixels by the right camera's mean focal length. ``NaN`` where either
    point is non-finite.
    """
    from al_dic_3d.calibration import undistort_points

    pl = np.asarray(left_pts, dtype=np.float64).reshape(-1, 2)
    pr = np.asarray(right_pts, dtype=np.float64).reshape(-1, 2)
    out = np.full(pl.shape[0], np.nan, dtype=np.float64)
    ok = np.isfinite(pl).all(axis=1) & np.isfinite(pr).all(axis=1)
    if not ok.any():
        return out
    intr_l, intr_r = rig.cameras[cam_left], rig.cameras[cam_right]
    R_l, T_l = rig.pose(cam_left)
    R_r, T_r = rig.pose(cam_right)
    # Relative pose left -> right: X_R = R X_L + T.
    R = R_r @ R_l.T
    T = T_r - R @ T_l
    tx = np.array([[0.0, -T[2], T[1]], [T[2], 0.0, -T[0]], [-T[1], T[0], 0.0]])
    E = tx @ R
    nl = undistort_points(pl[ok], intr_l)
    nr = undistort_points(pr[ok], intr_r)
    hl = np.column_stack([nl, np.ones(nl.shape[0])])
    hr = np.column_stack([nr, np.ones(nr.shape[0])])
    line = hl @ E.T  # (m, 3) epipolar lines in the right normalized plane
    norm = np.hypot(line[:, 0], line[:, 1])
    with np.errstate(invalid="ignore", divide="ignore"):
        d = np.abs((hr * line).sum(axis=1)) / norm
    out[ok] = d * 0.5 * (intr_r.fx + intr_r.fy)
    return out


def accept_links(
    left_pts: NDArray[np.float64],
    right_pts: NDArray[np.float64],
    znssd: NDArray[np.float64],
    valid: NDArray[np.bool_],
    *,
    rig=None,
    znssd_max: float | None = STEREO_ZNSSD_MAX,
    epipolar_max_px: float | None = STEREO_EPIPOLAR_MAX_PX,
) -> tuple[NDArray[np.bool_], int, int]:
    """Reject converged-but-wrong stereo links.

    IC-GN convergence alone is not evidence of a correspondence: a subset can
    "converge" on a false local optimum with a poor correlation, and a
    wide-baseline false lock lands far from the epipolar line. Returns
    ``(valid_new, n_rejected_znssd, n_rejected_epipolar)``; a threshold ``None``
    or ``<= 0`` disables that check, and the epipolar check needs ``rig``.
    """
    v = np.asarray(valid, dtype=bool).copy()
    n_z = n_e = 0
    if znssd_max is not None and znssd_max > 0:
        bad_z = v & ~(np.asarray(znssd, dtype=np.float64) <= float(znssd_max))
        n_z = int(bad_z.sum())
        v &= ~bad_z
    if rig is not None and epipolar_max_px is not None and epipolar_max_px > 0 and v.any():
        dist = np.full(v.shape[0], np.nan)
        dist[v] = epipolar_distance_px(rig, np.asarray(left_pts)[v], np.asarray(right_pts)[v])
        bad_e = v & ~(dist <= float(epipolar_max_px))
        n_e = int(bad_e.sum())
        v &= ~bad_e
    return v, n_z, n_e


def accept_field(
    field: DisparityField,
    *,
    rig=None,
    znssd_max: float | None = STEREO_ZNSSD_MAX,
    epipolar_max_px: float | None = STEREO_EPIPOLAR_MAX_PX,
) -> tuple[DisparityField, int, int]:
    """:func:`accept_links` applied to a :class:`DisparityField` (NaNs the rejects)."""
    import dataclasses

    right = field.left_pts + field.d
    v, n_z, n_e = accept_links(
        field.left_pts,
        right,
        field.znssd,
        field.valid,
        rig=rig,
        znssd_max=znssd_max,
        epipolar_max_px=epipolar_max_px,
    )
    if n_z == 0 and n_e == 0:
        return field, 0, 0
    d = field.d.copy()
    z = field.znssd.copy()
    d[~v] = np.nan
    z[~v] = np.nan
    return dataclasses.replace(field, d=d, znssd=z, valid=v), n_z, n_e
