"""3D-view export — offscreen pyvista renders of the reconstructed surface.

No 2D counterpart (the 2D app has no 3D scene). The surface is the SAME
geometry the interactive ``View3D`` widget shows: the regular-grid quad
connectivity from :mod:`al_dic_3d.viz3d.surface` over ``points[k]`` with the
drawn ROI knocked out, colored by the selected field, falling back to a
Delaunay triangulation when no usable quad lattice exists. Rendering happens on
an offscreen ``pyvista.Plotter`` — no Qt, no window — so it is safe inside
worker threads and headless runs.

Consistency with the interactive view (fix batch V, M4): the colour range is
the view's rule — per frame, the 2nd-98th percentile of the nodes inside the
ROI (:func:`view3d_color_range`), or the user's fixed range; the surface honours
the ROI; the camera is the user's view when the caller passes one (the
isometric default otherwise); values/labels follow the display unit through
``value_scale`` / ``field_label``. An encoder that cannot open raises, and a
cancelled animation is deleted rather than reported as written.

pyvista/VTK is imported lazily inside functions (architecture test enforced).

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
from al_dic_3d.export.outcome import ExportOutcome, stop_requested
from al_dic_3d.export.render import CameraTuple
from al_dic_3d.export.tables import display_field_frame
from al_dic_3d.export.utils import ensure_dir, frame_tag
from al_dic_3d.viz3d.fieldmap import auto_range as _percentile_range
from al_dic_3d.viz3d.fieldmap import visible_values
from al_dic_3d.viz3d.surface import build_surface_polydata

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult

ProgressCb = Callable[[int, int, str], None]

# Window-size presets offered by the 3D View tab (W, H).
VIEW3D_RESOLUTIONS = ((1024, 768), (1280, 960), (1920, 1080), (800, 600))

__all__ = [
    "VIEW3D_RESOLUTIONS",
    "CameraTuple",
    "build_surface",
    "export_view3d_frames",
    "export_view3d_turntable",
    "render_view3d_frame",
    "view3d_color_range",
]


def build_surface(
    points_3d: NDArray,
    values: NDArray,
    name: str,
    ref_coords: NDArray | None = None,
    barrier_mask: NDArray | None = None,
    roi_mask: NDArray | None = None,
):
    """Surface (``pv.PolyData``) from finite 3D points + scalars (Qt-free).

    Same construction as the interactive ``View3D`` — both delegate to the
    shared :func:`al_dic_3d.viz3d.surface.build_surface_polydata` (F3.2), so
    exported frames carry the exact geometry the canvas shows: ``roi_mask``
    (the drawn LEFT ROI) knocks out cells outside it / its holes, and
    ``barrier_mask`` (Batch C item 4) drops cells whose edges bridge a thin
    crack; ``None`` for both keeps the surface byte-identical to the unmasked
    build. Returns ``None`` when fewer than 3 finite points exist.
    """
    return build_surface_polydata(points_3d, values, name, ref_coords, roi_mask, barrier_mask)


def _surface_barrier(result: RunResult, roi_mask: NDArray | None) -> NDArray | None:
    """The crack barrier for the 3D surface: the drawn ROI mask on crack-aware runs.

    Mirrors ``export/render.py``: the drawn LEFT ROI mask doubles as the crack
    barrier (0-band = crack). ``None`` when no mask or the run was not crack-aware,
    so crack-free surfaces stay byte-identical.
    """
    if roi_mask is None or not bool(result.meta.get("crack_aware", False)):
        return None
    return np.asarray(roi_mask)  # read as is (bool or float), never copied


def view3d_color_range(
    values: NDArray, ref_coords: NDArray, roi_mask: NDArray | None
) -> tuple[float, float]:
    """The interactive 3D view's auto range for one frame (M4).

    2nd-98th percentile of the values of the nodes inside the drawn ROI
    (reference coordinates), exactly what ``CanvasArea3D._render_3d`` computes.
    """
    return _percentile_range(visible_values(values, ref_coords, roi_mask))


def _safe_clim(lo: float, hi: float) -> tuple[float, float]:
    """A renderable colour range (VTK rejects an empty or non-finite one)."""
    lo, hi = float(lo), float(hi)
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return 0.0, 1.0
    if hi > lo:
        return lo, hi
    pad = max(abs(lo) * 1e-6, 1e-12)
    return lo - pad, hi + pad


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


def _set_clim(actor, clim: tuple[float, float]) -> None:
    """Move a live actor's colour range (the in-place update path)."""
    mapper = getattr(actor, "mapper", None)
    if mapper is None:
        return
    mapper.scalar_range = clim
    lut = getattr(mapper, "lookup_table", None)
    if lut is not None:
        lut.scalar_range = clim  # the scalar bar follows the lookup table


def _screenshot_bgr(pl) -> NDArray[np.uint8]:
    # Render FIRST: an in-place point/scalar update (and a camera Azimuth())
    # does not repaint the framebuffer, and pyvista only renders inside
    # screenshot() on the first call — without this every sequence frame after
    # the first was a copy of it (fix batch V; the turntable's copy of this bug
    # was fixed in 1bfe769).
    pl.render()
    img = pl.screenshot(return_img=True)  # (H, W, 3) RGB
    return np.ascontiguousarray(img[:, :, ::-1])  # -> BGR


def _blank_frame(writer: StreamingAnimWriter) -> NDArray[np.uint8]:
    """A no-surface frame (the empty white scene) that keeps its time slot."""
    return np.full((writer.h, writer.w, 3), 255, np.uint8)


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
    roi_mask: NDArray | None = None,
) -> NDArray[np.uint8] | None:
    """Render one 3D surface frame offscreen -> BGR uint8 array.

    ``camera`` is a pyvista ``(position, focal_point, view_up)`` tuple; the
    default is the isometric view. ``roi_mask`` knocks out cells outside the
    drawn ROI; ``barrier_mask`` (Batch C item 4) drops crack-bridging cells.
    Returns None when no surface can be built.
    """
    surf = build_surface(points_3d, values, field_label, ref_coords, barrier_mask, roi_mask)
    if surf is None:
        return None
    pl = _make_plotter(window_size, background)
    try:
        _add_surface(pl, surf, field_label, cmap, *_safe_clim(vmin, vmax))
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
    """Min/max over ALL frames — a playback-stable range for callers that want one.

    The exporters follow the interactive view instead (per-frame percentile,
    :func:`view3d_color_range`). Uses the display-masked field (frame-k strain
    validity — the surface always shows the deformed geometry) so trimmed
    strain nodes never stretch the range.
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
    value_scale: float = 1.0,
    field_label: str | None = None,
    stop_event: threading.Event | None = None,
    progress_cb: ProgressCb | None = None,
) -> ExportOutcome:
    """Render the deforming surface per frame -> PNGs and/or an animation.

    Args:
        field_id: selectable field id (``U``/``W``/``exx``/...) coloring the
            surface.
        roi_mask: the drawn LEFT ROI mask (bool): the surface keeps only the
            cells inside it, the auto range only its nodes; on a crack-aware
            run it also doubles as the crack barrier (item 4).
        auto_range: per-frame 2nd-98th percentile over the nodes inside the
            ROI (the interactive view's rule) when True; the explicit
            ``vmin``/``vmax`` (display units) otherwise.
        camera: fixed ``(position, focal_point, view_up)`` for every frame —
            pass the user's 3D-view camera — or None for the isometric view.
        write_frames: write ``{field}/frame_XX.png`` per frame.
        animation_format: ``"mp4"`` / ``"gif"`` to also stream the frames into
            ``{field}.{ext}``; None disables the animation.
        value_scale / field_label: display-unit factor applied to the values
            and the scalar-bar title (default: native mm label).
        stop_event: cooperative cancel — checked before every frame.
        progress_cb: ``(frames_done, total_frames, label)``.

    Returns:
        An :class:`ExportOutcome` of the frame PNGs + the animation. Frames
        without a surface are ``skipped`` (no PNG; the animation keeps their
        slot with an empty frame); on cancel the PNGs written so far are kept
        and the unfinished animation is deleted (``discarded``).

    Raises:
        OSError: the animation encoder could not be opened.

    Performance (P3.2): ONE offscreen plotter serves the whole sequence — a
    fresh plotter per frame costs 100-300 ms of GL-context churn each. When a
    frame's surface topology matches the previous one (same points/faces —
    the common case; the NaN pattern rarely changes), the live mesh's points,
    scalars and colour range are updated in place like the interactive
    ``View3D`` (P2.4); otherwise the scene is rebuilt on the same plotter.
    Each frame's field values are computed ONCE (range and render share them).
    """
    from al_dic_3d.pathsafe import imwrite_unicode

    outcome = ExportOutcome()
    n_frames = int(result.reconstruction.n_frames)
    if frame_end < 0 or frame_end >= n_frames:
        frame_end = n_frames - 1
    if frame_end < frame_start or (not write_frames and animation_format is None):
        return outcome
    frame_step, out_fps = animation_fps(fps, frame_step)
    frame_indices = list(range(frame_start, frame_end + 1, frame_step))
    total = len(frame_indices)
    label = field_label or colorbar_label(field_id)
    barrier = _surface_barrier(result, roi_mask)
    view_dir = ensure_dir(dest_dir / f"{prefix}_view3d_{timestamp}")
    frames_dir = ensure_dir(view_dir / field_id) if write_frames else None

    rec = result.reconstruction
    pl = None
    actor = None
    live_surf = None  # PolyData attached to the live actor (in-place updates)
    writer: StreamingAnimWriter | None = None
    pending_blank = 0  # surface-less frames before the encoder could open
    drawn = 0
    done = 0
    try:
        for k in frame_indices:
            if stop_requested(stop_event):
                outcome.cancelled = True
                break
            tag = frame_tag(k, n_frames)
            vals = display_field_frame(result, field_id, k, deformed=True)
            surf = None
            if vals is not None:
                if value_scale != 1.0:
                    vals = vals * float(value_scale)
                surf = build_surface(
                    rec.points[k], vals, label, result.ref_coords, barrier, roi_mask
                )
            if surf is None:
                outcome.skipped.append(f"{field_id} {tag}")
                if animation_format is not None:
                    if writer is None:
                        pending_blank += 1
                    else:
                        writer.append(_blank_frame(writer))
            else:
                if auto_range:
                    clim = _safe_clim(*view3d_color_range(vals, result.ref_coords, roi_mask))
                else:
                    clim = _safe_clim(vmin, vmax)
                if pl is None:
                    pl = _make_plotter(window_size, background="white")
                if (
                    live_surf is not None
                    and live_surf.n_points == surf.n_points
                    and live_surf.n_cells == surf.n_cells
                    and np.array_equal(live_surf.faces, surf.faces)
                ):
                    # Same topology: mutate the live mesh (camera persists).
                    live_surf.points[:] = surf.points
                    live_surf[label][:] = surf[label]
                    _set_clim(actor, clim)
                else:
                    pl.clear()
                    actor = _add_surface(pl, surf, label, cmap, *clim)
                    live_surf = surf
                    if camera is not None:
                        pl.camera_position = camera
                    else:
                        pl.view_isometric()
                img = _screenshot_bgr(pl)
                drawn += 1
                if frames_dir is not None:
                    out = frames_dir / f"{tag}.png"
                    # G3: raises on failure instead of cv2.imwrite's silent False.
                    imwrite_unicode(out, img)
                    outcome.append(out)
                if animation_format is not None:
                    if writer is None:
                        writer = StreamingAnimWriter(
                            animation_format.lower(), view_dir, field_id, out_fps, img.shape[:2]
                        )
                        for _ in range(pending_blank):
                            writer.append(_blank_frame(writer))
                        pending_blank = 0
                    writer.append(img)
            done += 1
            if progress_cb is not None:
                progress_cb(done, total, tag)
    except BaseException:
        if writer is not None:
            writer.discard()  # never leave a truncated video behind
        raise
    finally:
        if pl is not None:
            pl.close()

    if writer is not None:
        if outcome.cancelled:
            outcome.discarded.append(writer.discard())
        else:
            writer.close()
            outcome.append(writer.out)
    if drawn == 0 and not outcome.cancelled:
        outcome.unavailable.append(field_id)
        outcome.skipped.clear()  # folded into "unavailable"
    return outcome


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
    camera: CameraTuple | None = None,
    value_scale: float = 1.0,
    field_label: str | None = None,
    stop_event: threading.Event | None = None,
    progress_cb: ProgressCb | None = None,
) -> ExportOutcome:
    """Orbit the surface of a FIXED frame 360° -> ``{field}_turntable.{ext}``.

    One offscreen plotter is built once; the camera azimuth advances by
    ``360 / n_orbit`` per rendered frame, starting from ``camera`` (the user's
    view) when given, else the isometric view. The colour range is frame
    ``frame_k``'s percentile inside ``roi_mask`` (or the fixed range); the ROI
    bounds the surface and doubles as the crack barrier on a crack-aware run.

    Returns:
        An :class:`ExportOutcome` with the animation path; empty with
        ``unavailable`` set when there is no surface, empty with ``cancelled``
        (and the partial file deleted) on cancel.

    Raises:
        OSError: the animation encoder could not be opened.
    """
    outcome = ExportOutcome()
    name = f"{field_id}_turntable"
    n_frames = int(result.reconstruction.n_frames)
    frame_k = max(0, min(int(frame_k), n_frames - 1))
    n_orbit = max(1, int(n_orbit))
    vals = display_field_frame(result, field_id, frame_k, deformed=True)
    if vals is None:
        outcome.unavailable.append(name)
        return outcome
    if value_scale != 1.0:
        vals = vals * float(value_scale)
    if auto_range:
        clim = _safe_clim(*view3d_color_range(vals, result.ref_coords, roi_mask))
    else:
        clim = _safe_clim(vmin, vmax)

    label = field_label or colorbar_label(field_id)
    surf = build_surface(
        result.reconstruction.points[frame_k],
        vals,
        label,
        result.ref_coords,
        _surface_barrier(result, roi_mask),
        roi_mask,
    )
    if surf is None:
        outcome.unavailable.append(name)
        return outcome
    view_dir = ensure_dir(dest_dir / f"{prefix}_view3d_{timestamp}")

    pl = _make_plotter(window_size, "white")
    writer: StreamingAnimWriter | None = None
    try:
        _add_surface(pl, surf, label, cmap, *clim)
        if camera is not None:
            pl.camera_position = camera
        else:
            pl.view_isometric()
        step_deg = 360.0 / n_orbit
        for i in range(n_orbit):
            if stop_requested(stop_event):
                outcome.cancelled = True
                break
            # _screenshot_bgr renders first: Azimuth() moves the camera but does
            # NOT redraw, so without it every orbit frame was pixel-identical.
            img = _screenshot_bgr(pl)
            if writer is None:
                writer = StreamingAnimWriter(
                    animation_format.lower(), view_dir, name, max(1, int(fps)), img.shape[:2]
                )
            writer.append(img)
            pl.camera.Azimuth(step_deg)
            if progress_cb is not None:
                progress_cb(i + 1, n_orbit, name)
    except BaseException:
        if writer is not None:
            writer.discard()
        raise
    finally:
        pl.close()

    if writer is not None:
        if outcome.cancelled:
            outcome.discarded.append(writer.discard())
        else:
            writer.close()
            outcome.append(writer.out)
    return outcome
