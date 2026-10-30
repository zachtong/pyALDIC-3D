"""Qt-free set-up shared by the interactive 3D view and the 3D exports.

Camera presets aligned to the specimen, deformation magnification, the colour
range guard and the scalar-bar look live in one place, so what the user frames
on screen and what an export renders agree.

Conventions: the world frame is the LEFT camera (OpenCV: x right, y DOWN, z into
the scene), so the left camera sits at the origin looking along +z and the
image's "up" is world -y. The specimen frame comes from the best-fit plane of
the reference surface: ``n`` its normal pointing back toward the cameras,
``ex`` the world x axis projected into the plane, ``ey = n x ex`` (image-up for
a specimen facing the camera).
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

#: Preset view names: from the left camera, square onto the specimen, edge-on
#: along the specimen's x axis (the out-of-plane profile), and an oblique view.
PRESET_VIEWS = ("camera", "normal", "side", "iso")

#: Deformation-magnification choices offered by the view (1 = true scale).
MAGNIFICATIONS = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000)

_ISO_ELEVATION = math.radians(35.0)
_ISO_AZIMUTH = math.radians(45.0)


def _finite_rows(points: NDArray) -> NDArray[np.float64]:
    p = np.asarray(points, dtype=np.float64).reshape(-1, 3)
    return p[np.isfinite(p).all(axis=1)]


def _unit(v: NDArray) -> NDArray[np.float64]:
    n = float(np.linalg.norm(v))
    return np.asarray(v, dtype=np.float64) / n if n > 0 else np.asarray(v, dtype=np.float64)


def specimen_axes(points: NDArray) -> tuple[NDArray, NDArray, NDArray, NDArray] | None:
    """``(centroid, ex, ey, n)`` of the best-fit plane; ``None`` with < 3 points."""
    p = _finite_rows(points)
    if p.shape[0] < 3:
        return None
    c = p.mean(axis=0)
    _, _, vt = np.linalg.svd(p - c, full_matrices=False)
    n = vt[2]
    if float(n @ (-c)) < 0.0:  # point back toward the left camera (the origin)
        n = -n
    ex = np.array([1.0, 0.0, 0.0]) - n[0] * n
    if np.linalg.norm(ex) < 1e-6:  # specimen edge-on to world x: use world -y
        ex = np.array([0.0, -1.0, 0.0]) - (-n[1]) * n
    ex = _unit(ex)
    ey = np.cross(n, ex)
    return c, ex, ey, _unit(n)


def preset_direction(name: str, points: NDArray) -> tuple[NDArray, NDArray] | None:
    """``(direction, view_up)`` of a preset view; direction points focal -> eye."""
    if name not in PRESET_VIEWS:
        raise ValueError(f"unknown 3D view preset {name!r}; expected one of {PRESET_VIEWS}")
    axes = specimen_axes(points)
    if axes is None:
        return None
    c, ex, ey, n = axes
    if name == "camera":
        direction = _unit(-c)  # toward the left camera centre (the origin)
        up = np.array([0.0, -1.0, 0.0])
    elif name == "normal":
        direction, up = n, ey
    elif name == "side":
        direction, up = -ex, n
    else:
        horizontal = -math.cos(_ISO_AZIMUTH) * ex - math.sin(_ISO_AZIMUTH) * ey
        direction = math.cos(_ISO_ELEVATION) * horizontal + math.sin(_ISO_ELEVATION) * n
        up = n
    up = _unit(up - float(up @ direction) * direction)
    return _unit(direction), up


def preset_camera(name: str, points: NDArray):
    """A pyvista ``(position, focal_point, view_up)`` for ``name``; ``None`` if empty.

    The distance only sets the direction: the caller frames the surface after
    (``reset_camera(bounds=...)``), so the distance is generous on purpose.
    """
    dir_up = preset_direction(name, points)
    if dir_up is None:
        return None
    p = _finite_rows(points)
    c = p.mean(axis=0)
    span = float(np.linalg.norm(p.max(axis=0) - p.min(axis=0))) or 1.0
    direction, up = dir_up
    eye = c + direction * 3.0 * span
    return tuple(tuple(float(v) for v in part) for part in (eye, c, up))


def magnify(
    ref_points: NDArray,
    points: NDArray,
    factor: float,
    *,
    normal_only: bool = False,
) -> NDArray[np.float64]:
    """Geometry ``P1 + factor * D`` (``D = P - P1``); optionally only D along the normal.

    ``factor == 1`` without ``normal_only`` returns ``points`` unchanged (true
    scale). ``normal_only`` keeps the component of ``D`` along the best-fit
    normal of the reference surface — the out-of-plane shape change, without the
    in-plane noise a large factor would otherwise blow up.
    """
    ref = np.asarray(ref_points, dtype=np.float64)
    cur = np.asarray(points, dtype=np.float64)
    if factor == 1.0 and not normal_only:
        return cur
    disp = cur - ref
    if normal_only:
        axes = specimen_axes(ref)
        if axes is not None:
            n = axes[3]
            disp = (disp @ n)[:, None] * n[None, :]
    return ref + float(factor) * disp


def auto_magnification(
    ref_points: NDArray, points: NDArray, *, normal_only: bool = False, target: float = 0.1
) -> float:
    """A 1-2-5 factor that makes the shape change about ``target`` of the specimen size."""
    ref = _finite_rows(ref_points)
    if ref.shape[0] < 3:
        return 1.0
    shown = magnify(ref_points, points, 1.0, normal_only=normal_only) - np.asarray(ref_points)
    lengths = np.linalg.norm(shown, axis=1)
    lengths = lengths[np.isfinite(lengths)]
    if lengths.size == 0:
        return 1.0
    change = float(np.percentile(lengths, 98))
    size = float(np.linalg.norm(ref.max(axis=0) - ref.min(axis=0)))
    if change <= 0.0 or size <= 0.0:
        return 1.0
    wanted = target * size / change
    choices = [m for m in MAGNIFICATIONS if m <= wanted]
    return float(choices[-1]) if choices else 1.0


def safe_clim(lo: float, hi: float) -> tuple[float, float]:
    """A renderable colour range (VTK rejects an empty or non-finite one)."""
    lo, hi = float(lo), float(hi)
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return 0.0, 1.0
    if hi > lo:
        return lo, hi
    pad = max(abs(lo) * 1e-6, 1e-12)
    return lo - pad, hi + pad


def tick_format(vmin: float, vmax: float) -> str:
    """printf format for the scalar-bar labels: enough decimals for the range."""
    span = abs(float(vmax) - float(vmin))
    biggest = max(abs(float(vmin)), abs(float(vmax)))
    if not np.isfinite(span) or span == 0.0 or biggest >= 1e5 or biggest < 1e-4:
        return "%.3g"
    decimals = int(min(6, max(0, 2 - math.floor(math.log10(span)))))
    return f"%.{decimals}f"


def scalar_bar_args(title: str, color: str, vmin: float, vmax: float) -> dict:
    """The scalar bar used on screen and in the exports (fits, readable)."""
    return {
        "title": title,
        "color": color,
        "vertical": True,
        "position_x": 0.86,
        "position_y": 0.12,
        "width": 0.05,
        "height": 0.76,
        "title_font_size": 14,
        "label_font_size": 12,
        "n_labels": 5,
        "fmt": tick_format(vmin, vmax),
    }


def frustum_size(points: NDArray) -> float:
    """Camera-frustum size in proportion to the stand-off (left camera at the origin)."""
    p = _finite_rows(points)
    if p.shape[0] == 0:
        return 60.0
    return max(1e-3, 0.12 * float(np.linalg.norm(p.mean(axis=0))))
