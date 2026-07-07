"""Board detection: one image + one spec -> :class:`BoardDetection` (Qt-free).

Detectors per board family (D12):

- Chessboard: ``findChessboardCornersSB`` (NORMALIZE|EXHAUSTIVE|ACCURACY —
  sub-pixel accurate, Duda&Frese 2018) with the classic
  ``findChessboardCorners`` + ``cornerSubPix`` as fallback; the two are never
  mixed silently (``method`` records which ran, the solver reports mixes).
  Orientation is canonicalized so the 180-degree ambiguity cannot desync the
  L/R corner indexing.
- ChArUco: 4.7+ OO API (``CharucoDetector.detectBoard`` +
  ``board.matchImagePoints``); corners carry unique ids -> partial views OK.
- Circle grid: ``findCirclesGrid`` with a tuned ``SimpleBlobDetector``.
- Coded circle grid: custom detector — Otsu binarize, contour hierarchy finds
  the three concentric-ring fiducials, affine hypotheses over the 6 fiducial
  assignments are scored by lattice match count, then a homography refine
  indexes every visible dot (partial views OK).

Failures never raise: they return ``ok=False`` with a ``reason`` so the GUI /
report can show per-image status. Qt-free; cv2 imported lazily.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration.boards import (
    BoardSpec,
    CharucoSpec,
    ChessboardSpec,
    CircleGridSpec,
    CodedCircleGridSpec,
)

_EMPTY2 = np.empty((0, 2), dtype=np.float64)
_EMPTY3 = np.empty((0, 3), dtype=np.float64)
_EMPTY_I = np.empty((0,), dtype=np.int64)


@dataclass(frozen=True)
class BoardDetection:
    """Detected control points of one board view (or a diagnosed failure)."""

    ok: bool
    image_points: NDArray[np.float64] = field(default_factory=lambda: _EMPTY2)  # (n, 2) px
    object_points: NDArray[np.float64] = field(default_factory=lambda: _EMPTY3)  # (n, 3) mm
    ids: NDArray[np.int64] = field(default_factory=lambda: _EMPTY_I)  # (n,) point ids
    method: str = ""  # detector that produced the points ("sb", "classic", ...)
    reason: str = ""  # failure reason when not ok
    sharpness: float = float("nan")  # px edge rise distance (chessboard only)

    @property
    def n_points(self) -> int:
        return int(self.image_points.shape[0])


def _fail(reason: str, method: str = "") -> BoardDetection:
    return BoardDetection(ok=False, method=method, reason=reason)


def to_gray_u8(image: NDArray) -> NDArray[np.uint8]:
    """Normalize any 2D array (or BGR) to a uint8 grayscale image."""
    arr = np.asarray(image)
    if arr.ndim == 3:
        import cv2

        arr = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY) if arr.shape[2] == 3 else arr[..., 0]
    if arr.ndim != 2:
        raise ValueError(f"expected a 2D image, got shape {arr.shape}")
    if arr.dtype == np.uint8:
        return arr
    a = arr.astype(np.float64)
    lo, hi = float(np.nanmin(a)), float(np.nanmax(a))
    if not np.isfinite(lo) or hi <= lo:
        return np.zeros(a.shape, dtype=np.uint8)
    return np.clip((a - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)


def detect_board(image: NDArray, spec: BoardSpec) -> BoardDetection:
    """Dispatch to the detector for ``spec``'s board family."""
    gray = to_gray_u8(image)
    if isinstance(spec, ChessboardSpec):
        return _detect_chessboard(gray, spec)
    if isinstance(spec, CharucoSpec):
        return _detect_charuco(gray, spec)
    if isinstance(spec, CodedCircleGridSpec):
        return _detect_coded_grid(gray, spec)
    if isinstance(spec, CircleGridSpec):
        return _detect_circle_grid(gray, spec)
    raise TypeError(f"unknown board spec type: {type(spec).__name__}")


# --------------------------------------------------------------------------- #
# Chessboard
# --------------------------------------------------------------------------- #


def _canonicalize(corners: NDArray[np.float64]) -> NDArray[np.float64]:
    """Resolve the 180-degree ordering ambiguity of a plain checkerboard.

    OpenCV may return the corner sequence starting from either end depending on
    board pose. Enforce: the first corner is the one closer to the image
    top-left (by x+y sum), so both cameras of a pair index the same physical
    corner as long as neither camera is rotated ~90+ degrees w.r.t. the other.
    """
    if corners[0].sum() > corners[-1].sum():
        return corners[::-1].copy()
    return corners


def _detect_chessboard(gray: NDArray[np.uint8], spec: ChessboardSpec) -> BoardDetection:
    import cv2

    flags = cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_EXHAUSTIVE | cv2.CALIB_CB_ACCURACY
    found, corners = cv2.findChessboardCornersSB(gray, spec.pattern_size, flags=flags)
    method = "sb"
    if not found:
        method = "classic"
        found, corners = cv2.findChessboardCorners(
            gray,
            spec.pattern_size,
            flags=cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE,
        )
        if not found:
            return _fail("chessboard not found (SB and classic detectors)", method)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3)
        corners = cv2.cornerSubPix(gray, np.float32(corners), (11, 11), (-1, -1), criteria)

    pts = _canonicalize(np.asarray(corners, dtype=np.float64).reshape(-1, 2))
    n = spec.cols * spec.rows
    if pts.shape[0] != n:
        return _fail(f"expected {n} corners, got {pts.shape[0]}", method)

    # Gradient-based sub-pixel refinement on top of either detector. SB's Radon
    # localization is tuned for sharp real images and leaves ~0.1-0.3 px of
    # error on band-limited/blurred edges, where cornerSubPix converges to
    # ~0.01 px (measured on the synthetic gate); on sharp images the refinement
    # moves corners negligibly. Window adapts to the projected square size.
    grid = pts.reshape(spec.rows, spec.cols, 2)
    spacing = float(np.median(np.linalg.norm(np.diff(grid, axis=1), axis=2)))
    win = int(np.clip(spacing * 0.4, 4, 15))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 1e-4)
    pts = np.asarray(
        cv2.cornerSubPix(gray, np.float32(pts).reshape(-1, 1, 2), (win, win), (-1, -1), criteria),
        dtype=np.float64,
    ).reshape(-1, 2)

    try:
        sharp = float(
            cv2.estimateChessboardSharpness(gray, spec.pattern_size, np.float32(pts))[0][0]
        )
    except cv2.error:
        sharp = float("nan")

    return BoardDetection(
        ok=True,
        image_points=pts,
        object_points=spec.object_points(),
        ids=np.arange(n, dtype=np.int64),
        method=method,
        sharpness=sharp,
    )


# --------------------------------------------------------------------------- #
# ChArUco
# --------------------------------------------------------------------------- #


def _detect_charuco(gray: NDArray[np.uint8], spec: CharucoSpec) -> BoardDetection:
    import cv2

    board = spec.board()
    detector = cv2.aruco.CharucoDetector(board)
    corners, ids, _mk_corners, _mk_ids = detector.detectBoard(gray)
    if corners is None or ids is None or len(corners) < spec.min_corners:
        got = 0 if corners is None else len(corners)
        return _fail(f"only {got} ChArUco corners (need >= {spec.min_corners})", "charuco")
    if board.checkCharucoCornersCollinear(np.asarray(ids)):
        return _fail("ChArUco corners are collinear (degenerate view)", "charuco")
    obj, img = board.matchImagePoints(corners, ids)
    return BoardDetection(
        ok=True,
        image_points=np.asarray(img, dtype=np.float64).reshape(-1, 2),
        object_points=np.asarray(obj, dtype=np.float64).reshape(-1, 3),
        ids=np.asarray(ids, dtype=np.int64).reshape(-1),
        method="charuco",
    )


# --------------------------------------------------------------------------- #
# Plain circle grid
# --------------------------------------------------------------------------- #


def _blob_detector(gray_shape: tuple[int, ...], spec: CircleGridSpec):
    import cv2

    p = cv2.SimpleBlobDetector_Params()
    p.filterByArea = True
    p.minArea = 9.0
    p.maxArea = float(np.pi / 4.0 * (min(gray_shape) / 6.0) ** 2)
    p.filterByCircularity = True
    p.minCircularity = 0.5
    p.filterByConvexity = False
    p.filterByInertia = False
    p.filterByColor = True
    p.blobColor = 0 if spec.dark_dots else 255
    p.minDistBetweenBlobs = 3.0
    return cv2.SimpleBlobDetector_create(p)


def _detect_circle_grid(gray: NDArray[np.uint8], spec: CircleGridSpec) -> BoardDetection:
    import cv2

    flags = cv2.CALIB_CB_ASYMMETRIC_GRID if spec.asymmetric else cv2.CALIB_CB_SYMMETRIC_GRID
    if spec.clustering:
        flags |= cv2.CALIB_CB_CLUSTERING
    found, centers = cv2.findCirclesGrid(
        gray, spec.pattern_size, flags=flags, blobDetector=_blob_detector(gray.shape, spec)
    )
    if not found:
        return _fail("circle grid not found", "circles")
    pts = np.asarray(centers, dtype=np.float64).reshape(-1, 2)
    n = spec.cols * spec.rows
    return BoardDetection(
        ok=True,
        image_points=pts,
        object_points=spec.object_points(),
        ids=np.arange(n, dtype=np.int64),
        method="circles",
    )


# --------------------------------------------------------------------------- #
# Coded circle grid (three concentric-ring fiducials)
# --------------------------------------------------------------------------- #


def _weighted_center(
    gray: NDArray[np.uint8], contour: NDArray, dark: bool
) -> tuple[float, float] | None:
    """Sub-pixel dot center: intensity-weighted centroid inside the contour."""
    import cv2

    x, y, w, h = cv2.boundingRect(contour)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.drawContours(mask, [contour - (x, y)], -1, 255, -1)
    patch = gray[y : y + h, x : x + w].astype(np.float64)
    weight = (255.0 - patch if dark else patch) * (mask > 0)
    total = weight.sum()
    if total <= 0:
        return None
    jj, ii = np.meshgrid(np.arange(w, dtype=np.float64), np.arange(h, dtype=np.float64))
    return (x + float((weight * jj).sum() / total), y + float((weight * ii).sum() / total))


def _find_dots_and_fiducials(
    gray: NDArray[np.uint8], spec: CodedCircleGridSpec
) -> tuple[NDArray[np.float64], NDArray[np.float64], str]:
    """Segment the target: return (dot_centers (n,2), fiducial_centers (m,2), err)."""
    import cv2

    thresh_type = cv2.THRESH_BINARY_INV if spec.dark_dots else cv2.THRESH_BINARY
    _t, binary = cv2.threshold(gray, 0, 255, thresh_type + cv2.THRESH_OTSU)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hierarchy is None or len(contours) < spec.rows:  # far too few blobs
        return _EMPTY2, _EMPTY2, "too few blobs after thresholding"
    hierarchy = hierarchy.reshape(-1, 4)  # [next, prev, first_child, parent]

    a_max = np.pi / 4.0 * (min(gray.shape) / 4.0) ** 2
    h_img, w_img = gray.shape
    rings: list[tuple[float, float, float]] = []  # (cx, cy, hole_area)
    blobs: list[tuple[float, float, float]] = []  # (cx, cy, area)
    for i, cnt in enumerate(contours):
        if hierarchy[i][3] != -1:  # holes are handled through their parents
            continue
        area = cv2.contourArea(cnt)
        if not 9.0 <= area <= a_max:
            continue
        bx, by, bw, bh = cv2.boundingRect(cnt)
        if bx <= 1 or by <= 1 or bx + bw >= w_img - 1 or by + bh >= h_img - 1:
            continue  # clipped by the image border — centroid would be biased
        child = hierarchy[i][2]
        hole_area = cv2.contourArea(contours[child]) if child != -1 else 0.0
        if child != -1 and hole_area > 0.25 * area:  # annulus -> fiducial ring
            m = cv2.moments(cnt)
            if m["m00"] > 0:
                rings.append((m["m10"] / m["m00"], m["m01"] / m["m00"], hole_area))
            continue
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        if hull_area <= 0 or area / hull_area < 0.8:  # not a solid dot
            continue
        center = _weighted_center(gray, cnt, spec.dark_dots)
        if center is not None:
            blobs.append((center[0], center[1], area))

    if not blobs:
        return _EMPTY2, _EMPTY2, "no dot-like blobs found"
    dots = np.array([(x, y) for x, y, _a in blobs], dtype=np.float64)

    # A fiducial center is the dot inside a ring's hole (nearest dot to ring center).
    fid: list[tuple[float, float]] = []
    for rx, ry, hole_area in rings:
        d2 = ((dots - (rx, ry)) ** 2).sum(axis=1)
        j = int(np.argmin(d2))
        if d2[j] <= hole_area:  # generous: within the hole's characteristic scale
            fid.append((dots[j, 0], dots[j, 1]))
    return dots, np.asarray(fid, dtype=np.float64).reshape(-1, 2), ""


def _match_lattice(
    dots: NDArray[np.float64],
    predicted: NDArray[np.float64],
    tol: float,
) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
    """Greedy unique nearest matching: predicted node k -> dot index (or -1)."""
    from scipy.spatial import cKDTree

    tree = cKDTree(dots)
    dist, idx = tree.query(predicted, k=1)
    order = np.argsort(dist)
    taken = np.zeros(len(dots), dtype=bool)
    node_ids: list[int] = []
    dot_ids: list[int] = []
    for k in order:
        if dist[k] > tol or taken[idx[k]]:
            continue
        taken[idx[k]] = True
        node_ids.append(int(k))
        dot_ids.append(int(idx[k]))
    return np.asarray(node_ids, dtype=np.int64), np.asarray(dot_ids, dtype=np.int64)


def _detect_coded_grid(gray: NDArray[np.uint8], spec: CodedCircleGridSpec) -> BoardDetection:
    from itertools import permutations

    import cv2

    dots, fid, err = _find_dots_and_fiducials(gray, spec)
    if err:
        return _fail(err, "coded")
    if fid.shape[0] != 3:
        return _fail(f"found {fid.shape[0]} ring fiducials (need exactly 3)", "coded")

    grid_rc = np.array(spec.fiducials, dtype=np.float64)  # (3, 2) (row, col)
    grid_xy = grid_rc[:, ::-1].copy()  # (col, row) grid units
    jj, ii = np.meshgrid(np.arange(spec.cols), np.arange(spec.rows))
    all_nodes = np.column_stack([jj.ravel(), ii.ravel()]).astype(np.float64)  # (col, row)

    # Pitch estimate from the dot cloud (median nearest-neighbor distance).
    from scipy.spatial import cKDTree

    nn = cKDTree(dots).query(dots, k=2)[0][:, 1]
    pitch_px = float(np.median(nn))

    best: tuple[int, NDArray, NDArray] | None = None  # (score, node_ids, dot_ids)
    for perm in permutations(range(3)):
        src = np.float32(grid_xy)
        dst = np.float32(fid[list(perm)])
        affine = cv2.getAffineTransform(src, dst)
        if np.linalg.det(affine[:, :2]) <= 0:  # mirror image — physically impossible
            continue
        scale = np.sqrt(abs(np.linalg.det(affine[:, :2])))
        if not 0.4 * pitch_px <= scale <= 2.5 * pitch_px:  # implausible lattice scale
            continue
        pred = all_nodes.astype(np.float64) @ affine[:, :2].T + affine[:, 2]
        node_ids, dot_ids = _match_lattice(dots, pred, 0.35 * pitch_px)
        if best is None or len(node_ids) > best[0]:
            best = (len(node_ids), node_ids, dot_ids)

    if best is None or best[0] < 6:
        got = 0 if best is None else best[0]
        return _fail(f"fiducial assignment failed (best lattice match {got} dots)", "coded")

    # Homography refine: re-predict every node projectively, re-match twice.
    _score, node_ids, dot_ids = best
    for _round in range(2):
        h_mat, _mask = cv2.findHomography(np.float64(all_nodes[node_ids]), dots[dot_ids], 0)
        if h_mat is None:
            break
        ph = np.column_stack([all_nodes, np.ones(len(all_nodes))]) @ h_mat.T
        pred = ph[:, :2] / ph[:, 2:3]
        node_ids, dot_ids = _match_lattice(dots, pred, 0.3 * pitch_px)

    if len(node_ids) < 6:
        return _fail("lattice indexing collapsed during homography refine", "coded")

    cols_f = all_nodes[node_ids, 0]
    rows_f = all_nodes[node_ids, 1]
    ids = (rows_f * spec.cols + cols_f).astype(np.int64)
    obj = np.column_stack(
        [cols_f * spec.spacing, rows_f * spec.spacing, np.zeros(len(node_ids))]
    ).astype(np.float64)
    return BoardDetection(
        ok=True,
        image_points=dots[dot_ids],
        object_points=obj,
        ids=ids,
        method="coded",
    )
