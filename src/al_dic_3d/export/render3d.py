"""3D-view export — offscreen pyvista renders of the reconstructed surface.

No 2D counterpart (the 2D app has no 3D scene). The surface is the SAME
geometry the interactive ``View3D`` widget shows: the regular-grid quad
connectivity from :mod:`al_dic_3d.viz3d.surface` over ``points[k]``, colored
by the selected field, falling back to a Delaunay triangulation when no
usable quad lattice exists. Rendering happens on an offscreen
``pyvista.Plotter`` — no Qt, no window — so it is safe inside worker threads
and headless runs.

pyvista/VTK is imported lazily inside functions (``[viz3d]`` extra;
architecture test enforced).

Two modes:

* **sequence** — one render per frame ``k`` (the surface deforms through the
  sequence), written as per-frame PNGs and/or streamed into an MP4/GIF via
  :class:`al_dic_3d.export.animation.StreamingAnimWriter`.
* **turntable** — a fixed frame ``k`` orbited 360° in ``n_orbit`` azimuth
  steps (always an animation).

Layout::

    dest_dir/
      {prefix}_view3d_{timestamp}/
        U/frame_01.png ...       (sequence PNGs)
        U.mp4                    (sequence animation)
        U_turntable.mp4          (turntable animation)
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.export.animation import StreamingAnimWriter, animation_fps
from al_dic_3d.export.colorbar import colorbar_label
from al_dic_3d.export.tables import display_field_frame
from al_dic_3d.export.utils import ensure_dir, frame_tag
from al_dic_3d.viz3d.surface import build_surface_polydata

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult

ProgressCb = Callable[[int, int, str], None]

# Window-size presets offered by the 3D View tab (W, H).
VIEW3D_RESOLUTIONS = ((1024, 768), (1280, 960), (1920, 1080), (800, 600))

# (position, focal_point, view_up) — pass to override the default isometric view.
CameraTuple = tuple[
    tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]
]


def build_surface(
    points_3d: NDArray,
    values: NDArray,
    name: str,
    ref_coords: NDArray | None = None,
    barrier_mask: NDArray | None = None,
):
    """Surface (``pv.PolyData``) from finite 3D points + scalars (Qt-free).

    Same construction as the interactive ``View3D`` — both delegate to the
    shared :func:`al_dic_3d.viz3d.surface.build_surface_polydata` (F3.2), so
    exported frames carry the exact geometry the canvas shows. ``barrier_mask``
    (Batch C item 4) drops cells whose edges bridge a thin crack; ``None`` (the
    crack-free default) keeps the surface byte-identical. Returns ``None`` when
    fewer than 3 finite points exist.
    """
    return build_surface_polydata(points_3d, values, name, ref_coords, None, barrier_mask)


def _surface_barrier(result: RunResult, roi_mask: NDArray | None) -> NDArray | None:
    """The crack barrier for the 3D surface: the drawn ROI mask on crack-aware runs.

    Mirrors ``export/render.py``: the drawn LEFT ROI mask doubles as the crack
    barrier (0-band = crack). ``None`` when no mask or the run was not crack-aware,
    so crack-free surfaces stay byte-identical.
    """
    if roi_mask is None or not bool(result.meta.get("crack_aware", False)):
        return None
    return np.asarray(roi_mask, dtype=np.float64)


def _make_plotter(window_size: tuple[int, int], background: str):
    import pyvista as pv

    pl = pv.Plotter(off_screen=True, window_size=list(window_size))
    pl.set_background(background)
    return pl


def _add_surface(pl, surf, field_label: str, cmap: str, vmin: float, vmax: float):
    fg = "black"
    return pl.add_mesh(
        surf,
        scalars=field_label,
        cmap=cmap,
        clim=(vmin, vmax),
        show_edges=False,
        scalar_bar_args={"title": field_label, "color": fg, "vertical": True},
    )


def _screenshot_bgr(pl) -> NDArray[np.uint8]:
    img = pl.screenshot(return_img=True)  # (H, W, 3) RGB
    return np.ascontiguousarray(img[:, :, ::-1])  # -> BGR


def render_view3d_frame(
    points_3d: NDArray,
    values: NDArray,
    *,
    field_label: str,
    cmap: str = "turbo",
    vmin: float = 0.0,
    vmax: float = 1.0,
    ref_coords: NDArray | None = None,
    window_size: tuple[int, int] = (1024, 768),
    camera: CameraTuple | None = None,
    background: str = "white",
    barrier_mask: NDArray | None = None,
) -> NDArray[np.uint8] | None:
    """Render one 3D surface frame offscreen -> BGR uint8 array.

    ``camera`` is a pyvista ``(position, focal_point, view_up)`` tuple; the
    default is the isometric view. ``barrier_mask`` (Batch C item 4) drops
    crack-bridging cells. Returns None when no surface can be built.
    """
    surf = build_surface(points_3d, values, field_label, ref_coords, barrier_mask)
    if surf is None:
        return None
    pl = _make_plotter(window_size, background)
    try:
        _add_surface(pl, surf, field_label, cmap, vmin, vmax)
        if camera is not None:
            pl.camera_position = camera
        else:
            pl.view_isometric()
        return _screenshot_bgr(pl)
    finally:
        pl.close()


def _range_of(frames: list[NDArray | None]) -> tuple[float, float]:
    """Color range over the given per-frame value arrays (None entries skipped)."""
    lo, hi = np.inf, -np.inf
    for vals in frames:
        if vals is None or not np.isfinite(vals).any():
            continue
        lo = min(lo, float(np.nanmin(vals)))
        hi = max(hi, float(np.nanmax(vals)))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return 0.0, 1.0
    return lo, hi


def _stable_field_range(result: RunResult, field_id: str) -> tuple[float, float]:
    """Color range over ALL frames (GUI 3D-view contract: playback stable).

    Uses the display-masked field (frame-k strain validity — the surface always
    shows the deformed geometry) so trimmed strain nodes never stretch the range.
    """
    n_frames = int(result.reconstruction.n_frames)
    return _range_of(
        [display_field_frame(result, field_id, k, deformed=True) for k in range(n_frames)]
    )


def export_view3d_frames(
    dest_dir: Path,
    prefix: str,
    timestamp: str,
    result: RunResult,
    field_id: str,
    *,
    frame_start: int = 0,
    frame_end: int = -1,
    window_size: tuple[int, int] = (1024, 768),
    cmap: str = "turbo",
    auto_range: bool = True,
    vmin: float = 0.0,
    vmax: float = 1.0,
    camera: CameraTuple | None = None,
    write_frames: bool = True,
    animation_format: str | None = None,
    fps: int = 10,
    frame_step: int = 1,
    roi_mask: NDArray | None = None,
    stop_event: threading.Event | None = None,
    progress_cb: ProgressCb | None = None,
) -> list[Path]:
    """Render the deforming surface per frame -> PNGs and/or an animation.

    Args:
        field_id: selectable field id (``U``/``W``/``exx``/...) coloring the
            surface.
        roi_mask: the drawn LEFT ROI mask; on a crack-aware run it doubles as
            the crack barrier so cells bridging the crack are dropped (item 4).
        auto_range: color range from ALL frames (stable during playback) when
            True; the explicit ``vmin``/``vmax`` otherwise.
        camera: fixed ``(position, focal_point, view_up)`` for every frame, or
            None for the default isometric view.
        write_frames: write ``{field}/frame_XX.png`` per frame.
        animation_format: ``"mp4"`` / ``"gif"`` to also stream the frames into
            ``{field}.{ext}``; None disables the animation.
        stop_event: cooperative cancel — checked before every frame.
        progress_cb: ``(frames_done, total_frames, label)``.

    Returns:
        Written paths (frame PNGs + the animation file), partial on cancel.

    Performance (P3.2): ONE offscreen plotter serves the whole sequence — a
    fresh plotter per frame costs 100-300 ms of GL-context churn each. When a
    frame's surface topology matches the previous one (same points/faces —
    the common case; the NaN pattern rarely changes), the live mesh's points
    and scalars are updated in place like the interactive ``View3D`` (P2.4)
    and the turntable path; otherwise the scene is rebuilt on the same
    plotter. The per-frame field values are computed ONCE and shared between
    the color-range pass and the render loop.
    """
    from al_dic_3d.pathsafe import imwrite_unicode

    n_frames = int(result.reconstruction.n_frames)
    if frame_end < 0 or frame_end >= n_frames:
        frame_end = n_frames - 1
    if frame_end < frame_start or (not write_frames and animation_format is None):
        return []
    frame_step, out_fps = animation_fps(fps, frame_step)
    frame_indices = list(range(frame_start, frame_end + 1, frame_step))
    total = len(frame_indices)

    # Hoisted per-frame values (P3.2): field_frame recomputes derived fields
    # (e.g. |D| = norm) on every call — compute each frame's values once and
    # share them between the stable-range pass and the render loop.
    values: dict[int, NDArray | None] = (
        {k: display_field_frame(result, field_id, k, deformed=True) for k in range(n_frames)}
        if auto_range
        else {k: display_field_frame(result, field_id, k, deformed=True) for k in frame_indices}
    )
    if auto_range:
        vmin, vmax = _range_of([values[k] for k in range(n_frames)])
    label = colorbar_label(field_id)
    barrier = _surface_barrier(result, roi_mask)
    view_dir = ensure_dir(dest_dir / f"{prefix}_view3d_{timestamp}")
    frames_dir = ensure_dir(view_dir / field_id) if write_frames else None

    rec = result.reconstruction
    pl = None
    live_surf = None  # PolyData attached to the live actor (in-place updates)
    writer: StreamingAnimWriter | None = None
    paths: list[Path] = []
    done = 0
    try:
        for k in frame_indices:
            if stop_event is not None and stop_event.is_set():
                break
            vals = values[k]
            if vals is None:
                continue
            surf = build_surface(rec.points[k], vals, label, result.ref_coords, barrier)
            if surf is None:
                continue
            if pl is None:
                pl = _make_plotter(window_size, background="white")
            if (
                live_surf is not None
                and live_surf.n_points == surf.n_points
                and live_surf.n_cells == surf.n_cells
                and np.array_equal(live_surf.faces, surf.faces)
            ):
                # Same topology: mutate the live mesh (camera/clim persist).
                live_surf.points[:] = surf.points
                live_surf[label][:] = surf[label]
            else:
                pl.clear()
                _add_surface(pl, surf, label, cmap, vmin, vmax)
                live_surf = surf
                if camera is not None:
                    pl.camera_position = camera
                else:
                    pl.view_isometric()
            img = _screenshot_bgr(pl)
            if frames_dir is not None:
                out = frames_dir / f"{frame_tag(k, n_frames)}.png"
                # G3: raises on failure instead of cv2.imwrite's silent False.
                imwrite_unicode(out, img)
                paths.append(out)
            if animation_format is not None:
                if writer is None:
                    w = StreamingAnimWriter(
                        animation_format.lower(), view_dir, field_id, out_fps, img.shape[:2]
                    )
                    if not w.ok:
                        w.close()
                        break
                    writer = w
                writer.append(img)
            done += 1
            if progress_cb is not None:
                progress_cb(done, total, frame_tag(k, n_frames))
    finally:
        if pl is not None:
            pl.close()
        if writer is not None:
            writer.close()
            paths.append(writer.out)
    return paths


def export_view3d_turntable(
    dest_dir: Path,
    prefix: str,
    timestamp: str,
    result: RunResult,
    field_id: str,
    *,
    frame_k: int = 0,
    n_orbit: int = 36,
    window_size: tuple[int, int] = (1024, 768),
    cmap: str = "turbo",
    auto_range: bool = True,
    vmin: float = 0.0,
    vmax: float = 1.0,
    animation_format: str = "mp4",
    fps: int = 10,
    roi_mask: NDArray | None = None,
    stop_event: threading.Event | None = None,
    progress_cb: ProgressCb | None = None,
) -> list[Path]:
    """Orbit the surface of a FIXED frame 360° -> ``{field}_turntable.{ext}``.

    One offscreen plotter is built once; the camera azimuth advances by
    ``360 / n_orbit`` per rendered frame. ``roi_mask`` doubles as the crack
    barrier on a crack-aware run (item 4). Returns the animation path (empty
    on cancel-before-first-frame or when no surface exists).
    """
    n_frames = int(result.reconstruction.n_frames)
    frame_k = max(0, min(int(frame_k), n_frames - 1))
    n_orbit = max(1, int(n_orbit))
    vals = display_field_frame(result, field_id, frame_k, deformed=True)
    if vals is None:
        return []
    if auto_range:
        finite = vals[np.isfinite(vals)]
        vmin = float(finite.min()) if finite.size else 0.0
        vmax = float(finite.max()) if finite.size else 1.0

    label = colorbar_label(field_id)
    surf = build_surface(
        result.reconstruction.points[frame_k],
        vals,
        label,
        result.ref_coords,
        _surface_barrier(result, roi_mask),
    )
    if surf is None:
        return []
    view_dir = ensure_dir(dest_dir / f"{prefix}_view3d_{timestamp}")

    pl = _make_plotter(window_size, "white")
    writer: StreamingAnimWriter | None = None
    try:
        _add_surface(pl, surf, label, cmap, vmin, vmax)
        pl.view_isometric()
        step_deg = 360.0 / n_orbit
        for i in range(n_orbit):
            if stop_event is not None and stop_event.is_set():
                break
            img = _screenshot_bgr(pl)
            if writer is None:
                w = StreamingAnimWriter(
                    animation_format.lower(),
                    view_dir,
                    f"{field_id}_turntable",
                    max(1, int(fps)),
                    img.shape[:2],
                )
                if not w.ok:
                    w.close()
                    return []
                writer = w
            writer.append(img)
            pl.camera.Azimuth(step_deg)
            if progress_cb is not None:
                progress_cb(i + 1, n_orbit, f"{field_id}_turntable")
    finally:
        pl.close()
        if writer is not None:
            writer.close()
    return [writer.out] if writer is not None else []
