"""Calibration diagnostics: where the fitted lens model can be trusted (Qt-free).

A low reprojection RMS says how well a calibration fits its points, not where
it can be trusted. This module runs on the FINAL calibration (after bundle
adjustment when that was used) with the detections the final solve used
(:attr:`~al_dic_3d.calibration.solve.StereoResult.detections`) and reports,
per camera:

* **extrapolation**: how far the calibration points reach (``r_cover``, an
  undistorted normalised radius) and whether two equally good lens models, k3
  free and k3 fixed, disagree beyond it. Where they do, the data do not
  determine the projection (``EXTRAPOLATION_UNDETERMINED``). The alternative
  fits use the mono solver even when the final rig came from bundle
  adjustment: both see the same views, so the check still answers whether the
  data determine the corners.
* **model adequacy**: whether the point residuals of the final calibration
  have spatial structure the lens model leaves unexplained
  (``LENS_MODEL_INADEQUATE``). Residuals are correlated within a view and the
  per-view pose re-fit absorbs part of any field, so the check sees only the
  part it cannot absorb.

Findings carry a stable ``code``, a ``severity``, the camera, the numbers and
an English default message. The GUI builds its translated text from the code
and the values; the English text is for the CLI and logs.

Evidence for every threshold: the calibration diagnostics brief of 2026-09-14
(``stereo_gt`` project, riley-raster fork), section 3.6, built on noise-free
Riley renders of the Stereo-DIC Challenge 2.0 rig (16 evaluations). Pre-check
A (free-k3 against fixed-k3 disagreement) and pre-check B (residual structure)
are the normative definitions the constructions below follow.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration.detect import BoardDetection
from al_dic_3d.calibration.geometry import _undistort_cv
from al_dic_3d.calibration.model import CameraIntrinsics, StereoRig
from al_dic_3d.calibration.report import coverage_fraction
from al_dic_3d.calibration.solve import MonoCalibration, calibrate_mono

# ---- thresholds (named, evidence-referenced, overridable) ---------------------------

# Largest free-k3 / fixed-k3 ray disagreement outside r_cover (px) the data may
# leave. Pre-check A: at 0.3 px every camera whose true k3-free error outside
# r_cover was 0.31-4.73 px exceeded it and every camera below 0.2 px stayed
# under it (14 cameras). To be confirmed on the held-out E1 datasets (brief 7.5).
EXTRAPOLATION_THRESHOLD_PX = 0.3

# cover_ratio below which an info finding says the corners are not covered.
# Provisional and informational only: the brief keeps LOW_COVERAGE an ``info``
# until E1 shows the coverage level below which results degrade. The dry-run
# protocol reached 0.62-0.72.
LOW_COVERAGE_RATIO = 0.8

# Residual-structure statistics above which the lens model does not describe
# the data; both must exceed their threshold. Pre-check B: every camera whose
# distortion the model can represent stayed at or below 1.10 (excess) and 0.8
# (field ratio), the two mismatch cameras reached at least 22.9 and 7.6.
RESIDUAL_EXCESS_THRESHOLD = 3.0
RESIDUAL_FIELD_THRESHOLD = 3.0

# ---- codes and severities -------------------------------------------------------------

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
EXTRAPOLATION_UNDETERMINED = "EXTRAPOLATION_UNDETERMINED"
EXTRAPOLATION_CHECK_SKIPPED = "EXTRAPOLATION_CHECK_SKIPPED"
LOW_COVERAGE = "LOW_COVERAGE"
LENS_MODEL_INADEQUATE = "LENS_MODEL_INADEQUATE"
MODEL_CHECK_SKIPPED = "MODEL_CHECK_SKIPPED"

# ---- construction constants (pre-check A) ----------------------------------------------

RAY_GRID = (49, 41)  # sensor grid (columns, rows) the two models are compared on
_UNDISTORT_CRITERIA = (3, 200, 1e-12)  # COUNT | EPS, as in pre-check A
_AFFINE_MIN_NODES = 3  # a 2D affine map needs three non-collinear nodes
_MIN_VIEWS = 3  # calibrate_mono's own minimum
_MIN_POINTS = 6

# ---- construction constants (pre-check B) ----------------------------------------------

RESIDUAL_GRID = (6, 5)  # image cells (columns, rows) the residuals are averaged in
RESIDUAL_MIN_CELL_POINTS = 10  # cells with fewer points are skipped
RESIDUAL_MIN_CELLS = 3  # fewer usable cells: the model check is skipped


@dataclass(frozen=True)
class DiagnosticThresholds:
    """The decision thresholds, overridable per call (defaults = the constants above)."""

    extrapolation_px: float = EXTRAPOLATION_THRESHOLD_PX
    low_coverage_ratio: float = LOW_COVERAGE_RATIO
    residual_excess: float = RESIDUAL_EXCESS_THRESHOLD
    residual_field: float = RESIDUAL_FIELD_THRESHOLD


@dataclass(frozen=True)
class Finding:
    """One diagnostic outcome for one camera."""

    code: str  # stable identifier, e.g. EXTRAPOLATION_UNDETERMINED
    severity: str  # "info" | "warning"
    camera: str  # "L" | "R"
    values: Mapping[str, float | str]  # the numbers the message is built from
    message_en: str  # English default text (CLI, logs); the GUI translates from code + values


@dataclass(frozen=True)
class CameraDiagnostics:
    """The per-camera numbers behind the findings (all radii undistorted, normalised)."""

    camera: str
    n_views: int
    n_points: int
    r_cover: float  # largest radius the used calibration points reach
    r_corner: float  # largest radius of the sensor corners
    cover_ratio: float  # r_cover / r_corner
    coverage_fraction: float  # share of an 8 x 8 sensor tiling hit by points
    disagreement_inside_px: float  # free vs fixed k3, inside r_cover (max)
    disagreement_outside_px: float  # ... outside r_cover (max); nan: nothing outside
    disagreement_gradient_ue: float  # largest gradient of that field (1e-6 px/px); info only
    affine_fit: str  # "inside r_cover" | "whole sensor" | "not computed"
    chosen_model: str  # the k3 choice of the calibration: "k3 free" | "k3 fixed"
    residual_rms_px: float = float("nan")  # final-calibration residuals of the used points
    residual_excess: float = float("nan")  # binned excess, about 1 for pure noise
    residual_field_ratio: float = float("nan")  # cubic-field rms over its pure-noise value
    residual_cells: int = 0  # image cells the excess was computed over


@dataclass(frozen=True)
class CameraReport:
    """``diagnose_camera``'s result: the numbers and the findings for one camera."""

    camera_diagnostics: CameraDiagnostics
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class CalibrationDiagnostics:
    """Everything the diagnostics found for one calibration."""

    cameras: dict[str, CameraDiagnostics]
    findings: tuple[Finding, ...]
    thresholds: DiagnosticThresholds = field(default_factory=DiagnosticThresholds)
    seconds: float = 0.0  # runtime of the diagnostics

    @property
    def worst_severity(self) -> str | None:
        """``"warning"``, ``"info"`` or None when nothing was found."""
        severities = {f.severity for f in self.findings}
        for level in (SEVERITY_WARNING, SEVERITY_INFO):
            if level in severities:
                return level
        return None


@dataclass(frozen=True)
class Disagreement:
    """Two lens models compared on the sensor grid (see ``alternative_model_disagreement``)."""

    inside_px: float
    outside_px: float
    affine_fit: str
    gradient_ue: float


# ---- geometry helpers ---------------------------------------------------------------------


def _normalised(uv: NDArray[np.float64], intr: CameraIntrinsics) -> NDArray[np.float64]:
    """Undistorted normalised coordinates of pixel positions (tight criteria, any model length)."""
    pts = np.ascontiguousarray(np.asarray(uv, np.float64)).reshape(-1, 1, 2)
    if intr.skew != 0.0:  # OpenCV ignores K's skew: remove it first (as undistort_points does)
        p = pts.reshape(-1, 2)
        y_d = (p[:, 1] - intr.cy) / intr.fy
        x_d = (p[:, 0] - intr.cx - intr.skew * y_d) / intr.fx
        pts, K = np.column_stack([x_d, y_d]).reshape(-1, 1, 2), np.eye(3)
    else:
        K = intr.K
    return _undistort_cv(pts, K, intr.dist_coeffs, _UNDISTORT_CRITERIA).reshape(-1, 2)


def _used_points(
    detections: Sequence[BoardDetection], view_indices: Sequence[int] | None
) -> NDArray[np.float64]:
    views = (
        range(len(detections)) if view_indices is None else [int(i) for i in view_indices]
    )
    pts = [
        detections[i].image_points
        for i in views
        if detections[i].ok and detections[i].n_points >= _MIN_POINTS
    ]
    return np.vstack(pts) if pts else np.empty((0, 2))


def coverage_radius(intr: CameraIntrinsics, points_uv: NDArray[np.float64]) -> float:
    """Largest undistorted normalised radius of ``points_uv`` (nan without points)."""
    if len(points_uv) == 0:
        return float("nan")
    xy = _normalised(points_uv, intr)
    return float(np.nanmax(np.hypot(xy[:, 0], xy[:, 1])))


def corner_radius(intr: CameraIntrinsics, image_size: tuple[int, int]) -> float:
    """Largest undistorted normalised radius of the four sensor corners."""
    w, h = float(image_size[0]) - 1.0, float(image_size[1]) - 1.0
    corners = np.array([[0.0, 0.0], [w, 0.0], [0.0, h], [w, h]])
    xy = _normalised(corners, intr)
    return float(np.max(np.hypot(xy[:, 0], xy[:, 1])))


def _max_or_nan(values: NDArray[np.float64]) -> float:
    return float(values.max()) if values.size else float("nan")


def _gradient_ue(diff: NDArray[np.float64], image_size: tuple[int, int]) -> float:
    """Largest spectral norm of the disagreement field's Jacobian, in 1e-6 px/px."""
    cols, rows = RAY_GRID
    du = (float(image_size[0]) - 1.0) / (cols - 1)
    dv = (float(image_size[1]) - 1.0) / (rows - 1)
    dx = diff[:, 0].reshape(rows, cols)
    dy = diff[:, 1].reshape(rows, cols)
    dx_dv, dx_du = np.gradient(dx, dv, du)
    dy_dv, dy_du = np.gradient(dy, dv, du)
    frob2 = dx_du**2 + dx_dv**2 + dy_du**2 + dy_dv**2
    det = dx_du * dy_dv - dx_dv * dy_du
    sigma_max = np.sqrt(0.5 * (frob2 + np.sqrt(np.maximum(frob2**2 - 4.0 * det**2, 0.0))))
    return float(np.nanmax(sigma_max) * 1e6)


def alternative_model_disagreement(
    model: CameraIntrinsics,
    other: CameraIntrinsics,
    image_size: tuple[int, int],
    r_cover: float,
    *,
    fx: float | None = None,
) -> Disagreement:
    """How far two lens models' viewing rays differ, inside and outside ``r_cover``.

    Both models undistort a :data:`RAY_GRID` pixel grid over the whole sensor.
    The affine map between the two sets of normalised coordinates is fitted on
    the nodes inside ``r_cover`` only: focal length, principal point and skew
    trade against the extrinsics, so they are not a lens-model difference, and
    a whole-sensor fit would leak the corner difference into the inside region.
    The residual difference times ``fx`` (``model.fx`` by default), maximised
    inside and outside ``r_cover``, is the disagreement in pixels.

    Degenerate cases: ``r_cover`` not finite -> nothing is computed; fewer than
    three (or collinear) nodes inside -> the affine map is fitted on the whole
    sensor instead (reported in ``affine_fit``); no node outside -> the outside
    value is nan.
    """
    if not np.isfinite(r_cover):
        nan = float("nan")
        return Disagreement(nan, nan, "not computed", nan)
    cols, rows = RAY_GRID
    us = np.linspace(0.0, float(image_size[0]) - 1.0, cols)
    vs = np.linspace(0.0, float(image_size[1]) - 1.0, rows)
    uu, vv = np.meshgrid(us, vs)
    uv = np.column_stack([uu.ravel(), vv.ravel()])
    a = _normalised(uv, model)
    b = _normalised(uv, other)
    inside = np.hypot(a[:, 0], a[:, 1]) <= r_cover
    design = np.column_stack([a, np.ones(len(a))])
    fit_inside = (
        int(inside.sum()) >= _AFFINE_MIN_NODES
        and np.linalg.matrix_rank(design[inside]) == design.shape[1]
    )
    fit = inside if fit_inside else np.ones_like(inside)
    coef, *_ = np.linalg.lstsq(design[fit], b[fit], rcond=None)
    diff = (b - design @ coef) * float(model.fx if fx is None else fx)
    dist = np.linalg.norm(diff, axis=1)
    return Disagreement(
        inside_px=_max_or_nan(dist[inside]),
        outside_px=_max_or_nan(dist[~inside]),
        affine_fit="inside r_cover" if fit_inside else "whole sensor",
        gradient_ue=_gradient_ue(diff, image_size),
    )


# ---- residual structure (pre-check B) ------------------------------------------------------


def final_residuals(
    intrinsics: CameraIntrinsics,
    detections: Sequence[BoardDetection],
    view_indices: Sequence[int] | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Reprojection residuals of the used points under the final calibration.

    Each view's board pose is re-estimated by ``solvePnP`` with the final
    intrinsics (as :func:`~al_dic_3d.calibration.report.point_residuals`), so
    the residuals judge the lens model, not the solve's own poses. Returns
    ``(uv, residual)``: the detected positions and ``projected - detected``.
    """
    import cv2

    views = range(len(detections)) if view_indices is None else [int(i) for i in view_indices]
    K, dist = intrinsics.K, intrinsics.dist_coeffs
    uv_chunks, res_chunks = [], []
    for i in views:
        det = detections[i]
        if not (det.ok and det.n_points >= _MIN_POINTS):
            continue
        ok, rvec, tvec = cv2.solvePnP(det.object_points, det.image_points, K, dist)
        if not ok:
            continue
        proj, _ = cv2.projectPoints(det.object_points, rvec, tvec, K, dist)
        uv_chunks.append(np.asarray(det.image_points, np.float64))
        res_chunks.append(proj.reshape(-1, 2) - det.image_points)
    if not uv_chunks:
        return np.empty((0, 2)), np.empty((0, 2))
    return np.vstack(uv_chunks), np.vstack(res_chunks)


def binned_excess(
    uv: NDArray[np.float64], residuals: NDArray[np.float64], image_size: tuple[int, int]
) -> tuple[float, int]:
    """``(excess, cells)``: residuals averaged in :data:`RESIDUAL_GRID` image cells.

    ``excess = sum(n_c |mean_c|^2) / (2 C sigma^2)`` over the ``C`` cells with at
    least :data:`RESIDUAL_MIN_CELL_POINTS` points, ``sigma^2`` the per-coordinate
    residual variance: about 1 for pure noise, large when the residuals share a
    direction within cells. nan when no cell qualifies.
    """
    cols, rows = RESIDUAL_GRID
    sigma2 = float(np.mean(residuals**2)) if len(residuals) else 0.0
    if not sigma2 > 0.0:
        return float("nan"), 0
    ix = np.clip((uv[:, 0] / float(image_size[0]) * cols).astype(int), 0, cols - 1)
    iy = np.clip((uv[:, 1] / float(image_size[1]) * rows).astype(int), 0, rows - 1)
    cell = ix * rows + iy
    stat, cells = 0.0, 0
    for c in np.unique(cell):
        members = cell == c
        n = int(members.sum())
        if n < RESIDUAL_MIN_CELL_POINTS:
            continue
        stat += n * float((residuals[members].mean(axis=0) ** 2).sum()) / sigma2
        cells += 1
    return (stat / (2 * cells) if cells else float("nan")), cells


def _cubic_basis(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
    one = np.ones_like(x)
    return np.column_stack([one, x, y, x * x, x * y, y * y, x**3, x * x * y, x * y * y, y**3])


def field_ratio(
    uv: NDArray[np.float64], residuals: NDArray[np.float64], intrinsics: CameraIntrinsics
) -> float:
    """rms of a cubic vector field fitted to the residuals, over its pure-noise value.

    The field has 10 terms per component in normalised image coordinates
    ``((u - cx) / fx, (v - cy) / fy)``; a least-squares fit of ``p`` terms to
    ``N`` points of pure noise has rms ``sqrt(2 p sigma^2 / N)``, which the fitted
    rms is divided by. nan when there are too few points or no spread.
    """
    x = (uv[:, 0] - intrinsics.cx) / intrinsics.fx
    y = (uv[:, 1] - intrinsics.cy) / intrinsics.fy
    basis = _cubic_basis(x, y)
    n_terms = basis.shape[1]
    sigma2 = float(np.mean(residuals**2)) if len(residuals) else 0.0
    if len(x) <= n_terms or not sigma2 > 0.0:
        return float("nan")
    coef, *_ = np.linalg.lstsq(basis, residuals, rcond=None)
    fitted = basis @ coef
    field_rms = float(np.sqrt(np.mean((fitted**2).sum(axis=1))))
    return field_rms / float(np.sqrt(2.0 * n_terms * sigma2 / len(x)))


@dataclass(frozen=True)
class _ResidualStats:
    rms_px: float
    excess: float
    field_ratio: float
    cells: int

    @property
    def usable(self) -> bool:
        return self.cells >= RESIDUAL_MIN_CELLS


def _residual_statistics(
    intrinsics: CameraIntrinsics,
    detections: Sequence[BoardDetection],
    view_indices: Sequence[int] | None,
    image_size: tuple[int, int],
) -> _ResidualStats:
    uv, res = final_residuals(intrinsics, detections, view_indices)
    if not len(res):
        return _ResidualStats(float("nan"), float("nan"), float("nan"), 0)
    rms = float(np.sqrt(np.mean((res**2).sum(axis=1))))
    excess, cells = binned_excess(uv, res, image_size)
    if cells < RESIDUAL_MIN_CELLS:
        return _ResidualStats(rms, float("nan"), float("nan"), cells)
    return _ResidualStats(rms, excess, field_ratio(uv, res, intrinsics), cells)


# ---- per-camera diagnosis ------------------------------------------------------------------


def _model_name(fix_k3: bool) -> str:
    return "k3 fixed" if fix_k3 else "k3 free"


def _extrapolation_finding(d: CameraDiagnostics, threshold: float) -> Finding:
    values = {
        "r_cover": d.r_cover,
        "r_corner": d.r_corner,
        "cover_ratio": d.cover_ratio,
        "disagreement_inside_px": d.disagreement_inside_px,
        "disagreement_outside_px": d.disagreement_outside_px,
        "threshold_px": threshold,
        "chosen_model": d.chosen_model,
    }
    message = (
        f"camera {d.camera}: the calibration points reach {d.cover_ratio:.0%} of the "
        f"image-corner radius; beyond that the lens model is extrapolated, and two "
        f"equally good fits (k3 free and k3 fixed) differ by up to "
        f"{d.disagreement_outside_px:.2f} px there. Add views with the board near the "
        f"image corners, keep the region of interest inside the covered area, or, for a "
        f"low-distortion lens, fix k3."
    )
    return Finding(EXTRAPOLATION_UNDETERMINED, SEVERITY_WARNING, d.camera, values, message)


def _low_coverage_finding(d: CameraDiagnostics, ratio: float) -> Finding:
    values = {"r_cover": d.r_cover, "r_corner": d.r_corner, "cover_ratio": d.cover_ratio,
              "threshold_ratio": ratio}  # fmt: skip
    message = (
        f"camera {d.camera}: the calibration points reach {d.cover_ratio:.0%} of the "
        f"image-corner radius; the lens model is fitted only inside that radius."
    )
    return Finding(LOW_COVERAGE, SEVERITY_INFO, d.camera, values, message)


def _model_finding(camera: str, stats: _ResidualStats, th: DiagnosticThresholds) -> Finding:
    values = {
        "residual_excess": stats.excess,
        "residual_field_ratio": stats.field_ratio,
        "residual_rms_px": stats.rms_px,
        "cells": stats.cells,
        "threshold_excess": th.residual_excess,
        "threshold_field": th.residual_field,
    }
    message = (
        f"camera {camera}: the residuals have a spatial pattern the lens model leaves "
        f"unexplained (binned excess {stats.excess:.1f}, fitted field "
        f"{stats.field_ratio:.1f} x noise; about 1 for a model that fits). Possible "
        f"causes: a lens the model cannot describe, a board that is not flat (try the "
        f"board-shape option of the bundle adjustment), or detector bias (very sharp "
        f"chessboard images, uneven lighting)."
    )
    return Finding(LENS_MODEL_INADEQUATE, SEVERITY_WARNING, camera, values, message)


def _model_skipped_finding(camera: str, stats: _ResidualStats) -> Finding:
    message = (
        f"camera {camera}: the lens-model check was skipped: the points fill only "
        f"{stats.cells} image cells with at least {RESIDUAL_MIN_CELL_POINTS} points "
        f"(it needs {RESIDUAL_MIN_CELLS})."
    )
    values = {"cells": stats.cells, "min_cells": RESIDUAL_MIN_CELLS}
    return Finding(MODEL_CHECK_SKIPPED, SEVERITY_INFO, camera, values, message)


def _skipped_finding(camera: str, reason: str) -> Finding:
    message = f"camera {camera}: the extrapolation check was skipped ({reason})."
    return Finding(EXTRAPOLATION_CHECK_SKIPPED, SEVERITY_INFO, camera, {"reason": reason}, message)


def diagnose_camera(
    camera: str,
    intrinsics: CameraIntrinsics,
    detections: Sequence[BoardDetection],
    image_size: tuple[int, int],
    *,
    fix_k3: bool = False,
    zero_tangent: bool = True,
    fix_aspect: bool = False,
    release_object: bool = False,
    mono: MonoCalibration | None = None,
    thresholds: DiagnosticThresholds | None = None,
) -> CameraReport:
    """Diagnose one camera of a final calibration.

    ``intrinsics`` is the camera as calibrated (after bundle adjustment when
    used); ``detections`` are the ones the final solve used. The solve options
    are the user's. ``mono``, when given, is the solve's own mono fit of this
    camera (same options, same detections): it is reused as the fit of the
    user's k3 choice, so only the alternative fit is solved here.
    """
    th = thresholds or DiagnosticThresholds()
    options = dict(zero_tangent=zero_tangent, fix_aspect=fix_aspect, release_object=release_object)
    r_corner = corner_radius(intrinsics, image_size)
    findings: list[Finding] = []
    try:
        chosen = mono or calibrate_mono(detections, image_size, fix_k3=fix_k3, **options)
        other = calibrate_mono(detections, image_size, fix_k3=not fix_k3, **options)
    except ValueError as exc:  # fewer than three usable views
        chosen = other = None
        findings.append(_skipped_finding(camera, str(exc)))
    views = chosen.view_indices if chosen is not None else None
    points = _used_points(detections, views)
    r_cover = coverage_radius(intrinsics, points)
    if chosen is not None and other is not None:
        free, fixed = (other, chosen) if fix_k3 else (chosen, other)
        dis = alternative_model_disagreement(
            free.intrinsics, fixed.intrinsics, image_size, r_cover, fx=intrinsics.fx
        )
    else:
        nan = float("nan")
        dis = Disagreement(nan, nan, "not computed", nan)
    n_views = len(views) if views is not None else sum(
        1 for d in detections if d.ok and d.n_points >= _MIN_POINTS
    )
    if chosen is not None:  # the model check judges the views of a solve
        stats = _residual_statistics(intrinsics, detections, views, image_size)
    else:
        stats = _ResidualStats(float("nan"), float("nan"), float("nan"), 0)
    diag = CameraDiagnostics(
        camera=camera,
        n_views=int(n_views),
        n_points=int(len(points)),
        r_cover=r_cover,
        r_corner=r_corner,
        cover_ratio=r_cover / r_corner if r_corner > 0 else float("nan"),
        coverage_fraction=coverage_fraction(detections, image_size),
        disagreement_inside_px=dis.inside_px,
        disagreement_outside_px=dis.outside_px,
        disagreement_gradient_ue=dis.gradient_ue,
        affine_fit=dis.affine_fit,
        chosen_model=_model_name(fix_k3),
        residual_rms_px=stats.rms_px,
        residual_excess=stats.excess,
        residual_field_ratio=stats.field_ratio,
        residual_cells=stats.cells,
    )
    if not findings:
        if np.isfinite(diag.disagreement_outside_px) and (
            diag.disagreement_outside_px > th.extrapolation_px
        ):
            findings.append(_extrapolation_finding(diag, th.extrapolation_px))
        elif np.isfinite(diag.cover_ratio) and diag.cover_ratio < th.low_coverage_ratio:
            findings.append(_low_coverage_finding(diag, th.low_coverage_ratio))
        if not stats.usable:
            findings.append(_model_skipped_finding(camera, stats))
        elif stats.excess > th.residual_excess and stats.field_ratio > th.residual_field:
            findings.append(_model_finding(camera, stats, th))
    return CameraReport(diag, tuple(findings))


def diagnose_calibration(
    rig: StereoRig,
    left: Sequence[BoardDetection],
    right: Sequence[BoardDetection],
    image_size: tuple[int, int],
    *,
    fix_k3: bool = False,
    zero_tangent: bool = True,
    fix_aspect: bool = False,
    release_object: bool = False,
    mono: Mapping[str, MonoCalibration] | None = None,
    thresholds: DiagnosticThresholds | None = None,
) -> CalibrationDiagnostics:
    """Diagnose a final stereo calibration, camera by camera.

    ``rig`` is the calibration the user saves (after bundle adjustment when
    used); ``left`` / ``right`` are the detections the final solve used
    (``StereoResult.detections``: eccentricity-corrected for dot targets). The
    solve options are the user's. Pass ``mono=result.mono`` when the rig comes
    from ``calibrate_stereo`` with those options, so the diagnostics add one
    mono solve per camera instead of two.
    """
    t0 = time.perf_counter()
    th = thresholds or DiagnosticThresholds()
    cameras: dict[str, CameraDiagnostics] = {}
    findings: list[Finding] = []
    for key, dets in (("L", left), ("R", right)):
        report = diagnose_camera(
            key,
            rig.cameras[key],
            dets,
            image_size,
            fix_k3=fix_k3,
            zero_tangent=zero_tangent,
            fix_aspect=fix_aspect,
            release_object=release_object,
            mono=(mono or {}).get(key),
            thresholds=th,
        )
        cameras[key] = report.camera_diagnostics
        findings.extend(report.findings)
    return CalibrationDiagnostics(cameras, tuple(findings), th, time.perf_counter() - t0)
