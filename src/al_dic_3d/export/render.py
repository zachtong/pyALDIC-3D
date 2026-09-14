"""Per-camera rendered field frames — dense overlay over the camera image.

Qt-free (architecture test enforced). The dense compute REUSES the GUI's exact
renderer, :class:`al_dic_3d.viz3d.fieldmap.FieldmapRenderer` — the same
scatter -> grid -> mask -> colormap pipeline the canvas shows — so exported
images are WYSIWYG. Composition follows the 2D ``export_png`` idiom: the RGBA
overlay blends over the grayscale camera image with ``cv2.addWeighted`` at the
field opacity, then an optional matplotlib colorbar strip is attached and the
long edge is capped by the resolution preset.

What "WYSIWYG" covers (fix batch V):

* **values and labels** follow the canvas's display unit: the GUI passes a
  ``value_scale`` (mm -> µm/cm/m, and frame rate for velocity) and the canvas's
  own colorbar label in each :class:`FieldImageConfig`; a fixed range typed in
  display units therefore applies to display-unit values (M1);
* **the right camera** is bounded by the drawn left ROI warped through the
  frame-1 correspondence, warped ONCE per export (:func:`camera_roi_masks`) —
  the support the canvas uses — instead of the bare node hull (M3);
* **backgrounds** keep their bit depth and get the canvas's min/max stretch
  (:func:`al_dic_3d.viz3d.background.load_display_gray`, M6);
* **honesty**: a frame with nothing to draw is reported in the returned
  :class:`~al_dic_3d.export.outcome.ExportOutcome` (never silently dropped), a
  (camera, field) pass that produced nothing is listed as ``unavailable``, and
  a cancel sets ``cancelled`` only when frames were really left undone.

Directory structure (2D naming idiom, one folder per camera x field)::

    dest_dir/
      {prefix}_images_{timestamp}/
        L_U/frame_01.png
        R_exx/frame_01.png
        ...
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from numpy.typing import NDArray

from al_dic_3d.export.colorbar import (
    ColorbarStyle,
    add_margin,
    attach_colorbar,
    colorbar_label,
)
from al_dic_3d.export.outcome import WARN_RIGHT_ROI, ExportOutcome, stop_requested
from al_dic_3d.export.tables import display_field_frame
from al_dic_3d.export.utils import ensure_dir, frame_tag
from al_dic_3d.pathsafe import imwrite_unicode
from al_dic_3d.viz3d.background import image_shape, load_display_gray
from al_dic_3d.viz3d.fieldmap import FieldmapRenderer, auto_range, visible_values
from al_dic_3d.viz3d.maskwarp import right_camera_mask

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult

ProgressCb = Callable[[int, int, str], None]

# Long-edge resolution presets offered by the export dialog (0 = full).
RESOLUTION_PRESETS = (1024, 768, 512, 1536, 2048, 0)

# (position, focal_point, view_up) — a pyvista camera snapshot.
CameraTuple = tuple[
    tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]
]


@dataclass(frozen=True)
class VizExportHint:
    """Snapshot of the calling window's live display settings (dialog prefill).

    Constructed at BOTH GUI call sites (main right sidebar and the strain
    window) so the export dialog opens showing what the user is looking at —
    the Qt-free home for this type fixes the 2D wart where the hint lived
    inside the dialog module.

    ``auto_range`` / ``vmin`` / ``vmax`` belong to ``current_field`` only, in
    ``display_unit``. ``frame_rate`` scales the velocity field to unit/s when
    ``frame_rate_known``; otherwise velocity stays per frame (the canvas rule).
    ``view3d_camera`` is the interactive 3D view's camera when one exists.
    """

    colormap: str = "turbo"
    show_deformed: bool = True
    overlay_alpha: float = 0.85
    current_field: str = "U"
    auto_range: bool = True
    vmin: float = 0.0
    vmax: float = 1.0
    current_frame: int = 0
    display_unit: str = "mm"
    frame_rate: float = 1.0
    frame_rate_known: bool = True
    view3d_camera: CameraTuple | None = None


@dataclass(frozen=True)
class FieldImageConfig:
    """Per-field render settings for image/animation export (Qt-free).

    ``value_scale`` multiplies the field's native values (mm, mm/frame,
    dimensionless strain) into the display unit before the range and colormap
    are applied, so ``vmin`` / ``vmax`` are in display units; ``label`` is the
    colorbar text (``None`` = the native-unit :func:`colorbar_label`).
    """

    field_id: str
    enabled: bool = True
    colormap: str = "turbo"
    auto_range: bool = True
    vmin: float = 0.0
    vmax: float = 1.0
    opacity: float = 0.85
    value_scale: float = 1.0
    label: str | None = None

    def colorbar_text(self) -> str:
        return self.label if self.label else colorbar_label(self.field_id)


def output_shape_for(image_shape: tuple[int, int], max_dim: int) -> tuple[int, int]:
    """Scale *image_shape* (H, W) so its long edge is <= *max_dim*.

    Returns *image_shape* unchanged when *max_dim* is 0/negative or already
    within the cap. Aspect ratio preserved. (2D ``export_png`` port.)
    """
    H, W = image_shape
    if max_dim <= 0 or max(H, W) <= max_dim:
        return image_shape
    s = max_dim / max(H, W)
    return (max(1, round(H * s)), max(1, round(W * s)))


def encode_params_for(ext: str, jpeg_quality: int) -> list[int]:
    """cv2.imwrite params for a file extension: JPEG quality, fast PNG."""
    e = ext.lower()
    if e in (".jpg", ".jpeg"):
        return [cv2.IMWRITE_JPEG_QUALITY, int(jpeg_quality)]
    if e == ".png":
        # Level 1 = fast; higher levels are far slower for marginal size gain
        # on speckle-heavy DIC frames.
        return [cv2.IMWRITE_PNG_COMPRESSION, 1]
    return []


def _load_gray_u8(path: str | Path) -> NDArray[np.uint8] | None:
    """Background as the canvas shows it: native bit depth, min/max stretched.

    Unicode-safe; None on failure. (Was ``IMREAD_GRAYSCALE``, which turned
    12-bit data in 16-bit files black — fix batch V, M6.)
    """
    return load_display_gray(path)


def _frame_geometry(
    result: RunResult, camera: str, frame_k: int, show_deformed: bool
) -> tuple[NDArray, NDArray, tuple[NDArray, NDArray] | None, bool]:
    """(pts, ref_pts, ref_uv, deformed) for one camera/frame — GUI contract.

    Geometry follows the deformed toggle (frame-k vs frame-1 node positions)
    while the field VALUES always belong to frame k; ``ref_uv = x_k - x_1``
    warps the reference support in deformed mode.
    """
    cs = result.correspondence
    x_cam = cs.xL if camera == "L" else cs.xR
    deformed = bool(show_deformed) and frame_k > 0
    pts = x_cam[frame_k] if deformed else x_cam[0]
    ref_pts = x_cam[0]
    ref_uv = None
    if deformed:
        d = x_cam[frame_k] - x_cam[0]
        ref_uv = (d[:, 0], d[:, 1])
    return pts, ref_pts, ref_uv, deformed


def field_color_range(
    result: RunResult,
    camera: str,
    field_id: str,
    frame_k: int,
    roi_mask: NDArray[np.bool_] | None,
    *,
    deformed: bool = False,
    value_scale: float = 1.0,
) -> tuple[float, float]:
    """Auto color range from the VISIBLE nodes of one frame (GUI contract).

    A5-3: shares the canvas/strain-window reduction — ``visible_values`` then
    :func:`al_dic_3d.viz3d.fieldmap.auto_range` (2–98 percentile) — so an
    exported frame is truly WYSIWYG (same range and colorbar end-labels the
    live canvas shows). This is a deliberate improvement over the 2D app, whose
    PNG export uses plain min/max while its canvas uses the percentile; routing
    all three consumers through the one helper keeps them from drifting again.
    Uses the display-masked field so trimmed strain nodes never stretch the
    range (Batch C, C3): the ``deformed`` flag selects frame-k vs frame-0
    validity to match the render. ``value_scale`` puts the range in display
    units (``roi_mask`` must be the support of ``camera``).
    """
    vals = display_field_frame(result, field_id, frame_k, deformed=deformed)
    if vals is None:
        return 0.0, 1.0
    if value_scale != 1.0:
        vals = vals * float(value_scale)
    cs = result.correspondence
    ref_pts = (cs.xL if camera == "L" else cs.xR)[0]
    return auto_range(visible_values(vals, ref_pts, roi_mask))


def crack_barrier(result: RunResult, roi_mask: NDArray[np.bool_] | None) -> NDArray | None:
    """The drawn LEFT ROI as the crack barrier on a crack-aware run, else None.

    The mask itself, not a float copy: the renderers read bool or float masks
    (``>= 0.5`` = material) without copying (a 12 Mpx float copy was 96 MB).
    """
    if roi_mask is None or not bool((getattr(result, "meta", None) or {}).get("crack_aware")):
        return None
    return np.asarray(roi_mask)


def right_image_shape(
    image_files: Mapping[str, Sequence[str]] | None, fallback: tuple[int, int]
) -> tuple[int, int]:
    """(H, W) of the right camera's first image (header only), else *fallback*."""
    files = list((image_files or {}).get("R") or [])
    if files:
        shape = image_shape(files[0])
        if shape is not None:
            return shape
    return (int(fallback[0]), int(fallback[1]))


def camera_roi_masks(
    result: RunResult,
    cameras: Sequence[str],
    roi_mask: NDArray[np.bool_] | None,
    image_files: Mapping[str, Sequence[str]] | None = None,
    right_roi_mask: NDArray[np.bool_] | None = None,
) -> tuple[dict[str, NDArray[np.bool_] | None], list[str]]:
    """Per-camera display support, the right one warped ONCE (M3).

    LEFT: the drawn reference ROI. RIGHT: ``right_roi_mask`` when the caller
    already has it, else the left ROI warped through the frame-1
    correspondence with :func:`al_dic_3d.viz3d.maskwarp.right_camera_mask` —
    the support the canvas shows. Returns ``(masks, warning_codes)``; a failed
    warp falls back to the node-hull support with :data:`WARN_RIGHT_ROI`.
    """
    masks: dict[str, NDArray[np.bool_] | None] = {}
    warnings: list[str] = []
    for cam in cameras:
        if cam == "L":
            masks[cam] = roi_mask
            continue
        if roi_mask is None:
            masks[cam] = None
            continue
        if right_roi_mask is None:
            cs = result.correspondence
            shape = right_image_shape(image_files, roi_mask.shape)
            right_roi_mask = right_camera_mask(roi_mask, cs.xL[0], cs.xR[0], shape)
            if right_roi_mask is None:
                warnings.append(WARN_RIGHT_ROI)
        masks[cam] = right_roi_mask
    return masks, warnings


def render_field_frame(
    result: RunResult,
    camera: str,
    field_id: str,
    frame_k: int,
    bg_image: NDArray[np.uint8] | None,
    cfg: FieldImageConfig,
    *,
    mesh_step: int,
    roi_mask: NDArray[np.bool_] | None = None,
    show_deformed: bool = True,
    output_max_dim: int = 0,
    renderer: FieldmapRenderer | None = None,
    barrier_mask: NDArray | None = None,
) -> tuple[NDArray[np.uint8], float, float] | None:
    """Render one field frame composited over the camera image -> BGR uint8.

    Args:
        result: the completed run.
        camera: ``"L"`` or ``"R"`` — selects the node cloud and background.
        field_id: one of the selectable export field ids (``U``/``exx``/...).
        frame_k: 0-based frame index (0 = reference frame).
        bg_image: (H, W) uint8 grayscale background, or None for black at the
            run's recorded image size.
        cfg: colormap / range / opacity / display scale for this field.
        mesh_step: node spacing in px (``winstepsize``) — grid density.
        roi_mask: the display support of THIS camera — the drawn ROI for the
            left camera, the warped ROI (:func:`camera_roi_masks`) for the
            right one; None falls back to the node-hull support.
        show_deformed: plot geometry at frame-k node positions (True) or the
            frame-1 reference positions (False); values stay frame k's.
        output_max_dim: cap the long edge of the output (0 = native).
        renderer: shared :class:`FieldmapRenderer` for cross-frame caching
            (batch exporters pass one; a fresh instance is used otherwise).

    Returns:
        ``(bgr, vmin, vmax)`` — the composited frame and the color range used
        (for the colorbar, in display units) — or None when the field is
        unavailable or the node set is degenerate.
    """
    pts, ref_pts, ref_uv, deformed = _frame_geometry(result, camera, frame_k, show_deformed)
    # WYSIWYG (Batch C, C3): the exported field hides ~strain_valid nodes exactly
    # like the canvas, using frame-k validity in the deformed view and frame-0 in
    # the reference view. Displacement fields pass through unchanged.
    vals = display_field_frame(result, field_id, frame_k, deformed=deformed)
    if vals is None:
        return None
    scale = float(cfg.value_scale)
    if scale != 1.0:
        vals = vals * scale  # display units (M1): range + colormap apply to these

    if bg_image is not None:
        img_shape = tuple(int(v) for v in bg_image.shape[:2])
    else:
        img_shape = tuple(int(v) for v in result.meta.get("image_size", (0, 0)))
        if img_shape == (0, 0):
            return None

    if cfg.auto_range:
        vmin, vmax = auto_range(visible_values(vals, ref_pts, roi_mask))
    else:
        vmin, vmax = float(cfg.vmin), float(cfg.vmax)

    if renderer is None:
        renderer = FieldmapRenderer()
    cache_name = f"{camera}:{field_id}" if scale == 1.0 else f"{camera}:{field_id}@{scale:g}"
    rgba, xg, yg, out_step = renderer.render_field_rgba(
        frame_k,
        cache_name,
        pts,
        vals,
        img_shape=img_shape,
        mesh_step=int(mesh_step),
        cmap=cfg.colormap,
        vmin=vmin,
        vmax=vmax,
        roi_mask=roi_mask,
        deformed=deformed,
        ref_uv=ref_uv,
        ref_pts=ref_pts,
        # Item 4 WYSIWYG: blank crack-bridging cells (reference-space barrier
        # only — the deformed crack is not warped, so barrier applies at frame 1).
        barrier_mask=None if deformed else barrier_mask,
    )
    if rgba is None:
        return None

    H, W = img_shape
    bg_bgr = (
        cv2.cvtColor(bg_image, cv2.COLOR_GRAY2BGR)
        if bg_image is not None
        else np.zeros((H, W, 3), dtype=np.uint8)
    )
    composed = _composite_overlay(bg_bgr, rgba, xg, yg, out_step, float(cfg.opacity))

    out_h, out_w = output_shape_for((H, W), output_max_dim)
    if (out_h, out_w) != (H, W):
        composed = cv2.resize(composed, (out_w, out_h), interpolation=cv2.INTER_AREA)
    return composed, vmin, vmax


def background_only_frame(
    bg_image: NDArray[np.uint8] | None,
    img_shape: tuple[int, int],
    output_max_dim: int,
) -> NDArray[np.uint8] | None:
    """The frame the canvas shows when there is no field to draw: the image alone.

    Used as an animation placeholder so a frame without data keeps its time
    slot. None when neither a background nor a recorded image size exists.
    """
    if bg_image is not None:
        bgr = cv2.cvtColor(bg_image, cv2.COLOR_GRAY2BGR)
    else:
        h, w = (int(v) for v in img_shape)
        if h <= 0 or w <= 0:
            return None
        bgr = np.zeros((h, w, 3), dtype=np.uint8)
    out_h, out_w = output_shape_for(bgr.shape[:2], output_max_dim)
    if (out_h, out_w) != bgr.shape[:2]:
        bgr = cv2.resize(bgr, (out_w, out_h), interpolation=cv2.INTER_AREA)
    return bgr


def _composite_overlay(
    bg_bgr: NDArray[np.uint8],
    rgba: NDArray[np.uint8],
    xg: NDArray,
    yg: NDArray,
    out_step: int,
    opacity: float,
) -> NDArray[np.uint8]:
    """Blend the grid-resolution RGBA overlay onto the full-size background.

    Same geometry as the canvas (:func:`~al_dic_3d.viz3d.raster.overlay_origin`):
    grid sample (i, j) belongs to image pixel ``(xg[j], yg[i])`` and covers an
    ``out_step``-pixel block centred there, so the grid is resampled with its
    samples on those pixels (one affine warp of the covered box). The colormap
    alpha is binary (opaque inside the support, 0 outside), so one SIMD
    ``addWeighted`` blend plus a restore-background select reproduces the GUI's
    ``setOpacity(overlay_alpha)`` compositing.
    """
    H, W = bg_bgr.shape[:2]
    gh, gw = rgba.shape[:2]
    s = float(out_step)
    x0, y0 = float(np.min(xg)), float(np.min(yg))
    # The blocks span half a step beyond the outer samples; clip to the image.
    bx0, by0 = max(0, int(np.ceil(x0 - s / 2))), max(0, int(np.ceil(y0 - s / 2)))
    bx1 = min(W, int(np.floor(x0 + (gw - 0.5) * s)) + 1)
    by1 = min(H, int(np.floor(y0 + (gh - 0.5) * s)) + 1)
    if bx1 <= bx0 or by1 <= by0:
        return bg_bgr.copy()
    # Box pixel (u, v) samples grid coordinate ((bx0 + u - x0) / s, (by0 + v - y0) / s).
    warp = np.array([[1.0 / s, 0.0, (bx0 - x0) / s], [0.0, 1.0 / s, (by0 - y0) / s]])
    size = (bx1 - bx0, by1 - by0)
    flags = cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP
    roi_ov = cv2.warpAffine(
        np.ascontiguousarray(rgba[:, :, [2, 1, 0]]),
        warp,
        size,
        flags=flags,
        borderMode=cv2.BORDER_REPLICATE,
    )
    alpha = cv2.warpAffine(
        np.ascontiguousarray(rgba[:, :, 3]),
        warp,
        size,
        flags=flags,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )

    result = bg_bgr.copy()
    roi_bg = result[by0:by1, bx0:bx1]
    inside = alpha >= 128
    op = float(np.clip(opacity, 0.0, 1.0))
    blended = cv2.addWeighted(roi_bg, 1.0 - op, roi_ov, op, 0.0)
    result[by0:by1, bx0:bx1] = np.where(inside[:, :, None], blended, roi_bg)
    return result


def export_image_frames(
    dest_dir: Path,
    prefix: str,
    timestamp: str,
    result: RunResult,
    image_files: dict[str, Sequence[str]],
    configs: Sequence[FieldImageConfig],
    *,
    cameras: Sequence[str] = ("L",),
    mesh_step: int = 16,
    roi_mask: NDArray[np.bool_] | None = None,
    right_roi_mask: NDArray[np.bool_] | None = None,
    show_deformed: bool = True,
    frame_start: int = 0,
    frame_end: int = -1,
    image_format: str = "png",
    jpeg_quality: int = 92,
    output_max_dim: int = 1024,
    include_colorbar: bool = True,
    colorbar_style: ColorbarStyle | None = None,
    margin_ratio: float = 0.0,
    margin_color: str = "white",
    stop_event: threading.Event | None = None,
    progress_cb: ProgressCb | None = None,
) -> ExportOutcome:
    """Render and save images for each camera, enabled field, and frame.

    Layout: ``{prefix}_images_{timestamp}/{camera}_{field}/frame_XX.{ext}``.

    Args:
        image_files: camera id -> ordered background image paths; frame k uses
            index k in deformed mode and index 0 (reference) otherwise.
        configs: per-field settings; disabled fields are skipped.
        cameras: subset of ``("L", "R")`` to render.
        roi_mask: drawn LEFT reference ROI mask. The right camera uses it
            warped through the frame-1 correspondence (``right_roi_mask`` when
            the caller already warped it) — the canvas's support (M3).
        frame_start / frame_end: inclusive 0-based range; ``frame_end < 0``
            means the last frame.
        margin_ratio / margin_color: blank border around the final frame
            (colorbar included) as a fraction of the long edge (0 = none) —
            the Preview & Colorbar tab's margin settings (2D idiom).
        stop_event: cooperative cancel — checked before every frame.
        progress_cb: called with ``(frames_done, total_frames, label)``.

    Returns:
        The written image files as an :class:`ExportOutcome`: frames with
        nothing to draw are listed in ``skipped`` (no file), passes that drew
        nothing at all in ``unavailable``, and ``cancelled`` is set only when
        frames were left undone.
    """
    outcome = ExportOutcome()
    n_frames = int(result.reconstruction.n_frames)
    if frame_end < 0 or frame_end >= n_frames:
        frame_end = n_frames - 1
    enabled = [c for c in configs if c.enabled]
    if not enabled or frame_end < frame_start:
        return outcome

    ext = {"png": ".png", "jpeg": ".jpg", "jpg": ".jpg", "tiff": ".tif", "tif": ".tif"}.get(
        image_format.lower(), ".png"
    )
    enc_params = encode_params_for(ext, jpeg_quality)
    cb_style = colorbar_style if colorbar_style is not None else ColorbarStyle()
    images_dir = dest_dir / f"{prefix}_images_{timestamp}"
    masks, warnings = camera_roi_masks(result, cameras, roi_mask, image_files, right_roi_mask)
    outcome.warnings += warnings

    # Pre-decode reference backgrounds (frame 0 reused for every frame when
    # plotting on the reference configuration).
    ref_bg: dict[str, NDArray | None] = {}
    if not show_deformed:
        for cam in cameras:
            files = list(image_files.get(cam) or [])
            ref_bg[cam] = _load_gray_u8(files[0]) if files else None

    renderer = FieldmapRenderer()  # shared: reference Delaunay reused across frames
    # Item 4 WYSIWYG: when the run was crack-aware, the drawn L ROI mask doubles
    # as the crack barrier (0-band = crack) for the dense render's cell blanking.
    barrier = crack_barrier(result, roi_mask)
    frames = list(range(frame_start, frame_end + 1))
    total = len(frames)
    done = 0
    drew: dict[str, bool] = {}  # "{cam}_{field}" -> rendered at least one frame
    missing: dict[str, list[str]] = {}

    for k in frames:
        if stop_requested(stop_event):
            outcome.cancelled = True
            break
        tag = frame_tag(k, n_frames)
        for cam in cameras:
            files = list(image_files.get(cam) or [])
            if show_deformed:
                bg = _load_gray_u8(files[min(k, len(files) - 1)]) if files else None
            else:
                bg = ref_bg.get(cam)
            for cfg in enabled:
                label = f"{cam}_{cfg.field_id}"
                rendered = render_field_frame(
                    result,
                    cam,
                    cfg.field_id,
                    k,
                    bg,
                    cfg,
                    mesh_step=mesh_step,
                    roi_mask=masks.get(cam),
                    show_deformed=show_deformed,
                    output_max_dim=output_max_dim,
                    renderer=renderer,
                    barrier_mask=barrier if cam == "L" else None,
                )
                if rendered is None:
                    drew.setdefault(label, False)
                    missing.setdefault(label, []).append(f"{label} {tag}")
                    continue
                drew[label] = True
                img, vmin, vmax = rendered
                if include_colorbar:
                    img = attach_colorbar(
                        img, cb_style, cfg.colormap, vmin, vmax, cfg.colorbar_text()
                    )
                img = add_margin(img, margin_ratio, margin_color)
                field_dir = ensure_dir(images_dir / f"{cam}_{cfg.field_id}")
                out = field_dir / f"{tag}{ext}"
                # G3: raises on failure instead of cv2.imwrite's silent False.
                imwrite_unicode(out, img, enc_params)
                outcome.append(out)
        renderer.clear_frame_caches()  # bound memory; keep the ref Delaunay
        done += 1
        if progress_cb is not None:
            progress_cb(done, total, tag)

    for label, ok in drew.items():
        if ok:
            outcome.skipped += missing.get(label, [])
        else:
            outcome.unavailable.append(label)
    return outcome
