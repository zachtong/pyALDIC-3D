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

Findings carry a stable ``code``, a ``severity``, the camera, the numbers and
an English default message. The GUI builds its translated text from the code
and the values; the English text is for the CLI and logs.

Evidence for every threshold: the calibration diagnostics brief of 2026-09-14
(``stereo_gt`` project, riley-raster fork), section 3.6, built on noise-free
Riley renders of the Stereo-DIC Challenge 2.0 rig (16 evaluations). Pre-check
A (free-k3 against fixed-k3 disagreement) is the normative definition the
construction below follows.
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

# ---- codes and severities -------------------------------------------------------------

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
EXTRAPOLATION_UNDETERMINED = "EXTRAPOLATION_UNDETERMINED"
EXTRAPOLATION_CHECK_SKIPPED = "EXTRAPOLATION_CHECK_SKIPPED"
LOW_COVERAGE = "LOW_COVERAGE"

# ---- construction constants (pre-check A) ----------------------------------------------

RAY_GRID = (49, 41)  # sensor grid (columns, rows) the two models are compared on
_UNDISTORT_CRITERIA = (3, 200, 1e-12)  # COUNT | EPS, as in pre-check A
_AFFINE_MIN_NODES = 3  # a 2D affine map needs three non-collinear nodes
_MIN_VIEWS = 3  # calibrate_mono's own minimum
_MIN_POINTS = 6


@dataclass(frozen=True)
class DiagnosticThresholds:
    """The decision thresholds, overridable per call (defaults = the constants above)."""

    extrapolation_px: float = EXTRAPOLATION_THRESHOLD_PX
    low_coverage_ratio: float = LOW_COVERAGE_RATIO


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
    )
    if not findings:
        if np.isfinite(diag.disagreement_outside_px) and (
            diag.disagreement_outside_px > th.extrapolation_px
        ):
            findings.append(_extrapolation_finding(diag, th.extrapolation_px))
        elif np.isfinite(diag.cover_ratio) and diag.cover_ratio < th.low_coverage_ratio:
            findings.append(_low_coverage_finding(diag, th.low_coverage_ratio))
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
