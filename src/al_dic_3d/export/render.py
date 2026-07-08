"""Per-camera rendered field frames — dense overlay over the camera image.

Qt-free (architecture test enforced). The dense compute REUSES the GUI's exact
renderer, :class:`al_dic_3d.viz3d.fieldmap.FieldmapRenderer` — the same
scatter -> grid -> mask -> colormap pipeline the canvas shows — so exported
images are WYSIWYG. Composition follows the 2D ``export_png`` idiom: the RGBA
overlay blends over the grayscale camera image with ``cv2.addWeighted`` at the
field opacity, then an optional matplotlib colorbar strip is attached and the
long edge is capped by the resolution preset.

Directory structure (2D naming idiom, one folder per camera x field)::

    dest_dir/
      {prefix}_images_{timestamp}/
        L_U/frame_01.png
        R_exx/frame_01.png
        ...
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from numpy.typing import NDArray

from al_dic_3d.export.colorbar import ColorbarStyle, attach_colorbar, colorbar_label
from al_dic_3d.export.tables import field_frame
from al_dic_3d.export.utils import ensure_dir, frame_tag
from al_dic_3d.viz3d.fieldmap import FieldmapRenderer, visible_values

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult

ProgressCb = Callable[[int, int, str], None]

# Long-edge resolution presets offered by the export dialog (0 = full).
RESOLUTION_PRESETS = (1024, 768, 512, 1536, 2048, 0)


@dataclass(frozen=True)
class VizExportHint:
    """Snapshot of the calling window's live display settings (dialog prefill).

    Constructed at BOTH GUI call sites (main right sidebar and the strain
    window) so the export dialog opens showing what the user is looking at —
    the Qt-free home for this type fixes the 2D wart where the hint lived
    inside the dialog module.
    """

    colormap: str = "turbo"
    show_deformed: bool = True
    overlay_alpha: float = 0.85
    current_field: str = "U"
    auto_range: bool = True
    vmin: float = 0.0
    vmax: float = 1.0
    current_frame: int = 0


@dataclass(frozen=True)
class FieldImageConfig:
    """Per-field render settings for image/animation export (Qt-free)."""

    field_id: str
    enabled: bool = True
    colormap: str = "turbo"
    auto_range: bool = True
    vmin: float = 0.0
    vmax: float = 1.0
    opacity: float = 0.85


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
    """Load a background image as (H, W) uint8 grayscale; None on failure."""
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    return img


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
) -> tuple[float, float]:
    """Auto color range from the VISIBLE nodes of one frame (GUI contract)."""
    vals = field_frame(result, field_id, frame_k)
    if vals is None:
        return 0.0, 1.0
    cs = result.correspondence
    ref_pts = (cs.xL if camera == "L" else cs.xR)[0]
    vis = visible_values(vals, ref_pts, roi_mask)
    finite = vis[np.isfinite(vis)]
    if finite.size:
        return float(finite.min()), float(finite.max())
    return 0.0, 1.0


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
) -> tuple[NDArray[np.uint8], float, float] | None:
    """Render one field frame composited over the camera image -> BGR uint8.

    Args:
        result: the completed run.
        camera: ``"L"`` or ``"R"`` — selects the node cloud and background.
        field_id: one of the selectable export field ids (``U``/``exx``/...).
        frame_k: 0-based frame index (0 = reference frame).
        bg_image: (H, W) uint8 grayscale background, or None for black at the
            run's recorded image size.
        cfg: colormap / range / opacity for this field.
        mesh_step: node spacing in px (``winstepsize``) — grid density.
        roi_mask: drawn reference ROI mask (LEFT camera only, pass None for
            the RIGHT camera — the renderer falls back to the hull support).
        show_deformed: plot geometry at frame-k node positions (True) or the
            frame-1 reference positions (False); values stay frame k's.
        output_max_dim: cap the long edge of the output (0 = native).
        renderer: shared :class:`FieldmapRenderer` for cross-frame caching
            (batch exporters pass one; a fresh instance is used otherwise).

    Returns:
        ``(bgr, vmin, vmax)`` — the composited frame and the color range used
        (for the colorbar) — or None when the field is unavailable or the node
        set is degenerate.
    """
    vals = field_frame(result, field_id, frame_k)
    if vals is None:
        return None

    if bg_image is not None:
        img_shape = tuple(int(v) for v in bg_image.shape[:2])
    else:
        img_shape = tuple(int(v) for v in result.meta.get("image_size", (0, 0)))
        if img_shape == (0, 0):
            return None

    pts, ref_pts, ref_uv, deformed = _frame_geometry(result, camera, frame_k, show_deformed)

    if cfg.auto_range:
        vmin, vmax = field_color_range(result, camera, field_id, frame_k, roi_mask)
    else:
        vmin, vmax = float(cfg.vmin), float(cfg.vmax)

    if renderer is None:
        renderer = FieldmapRenderer()
    rgba, xg, yg, out_step = renderer.render_field_rgba(
        frame_k,
        f"{camera}:{field_id}",
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


def _composite_overlay(
    bg_bgr: NDArray[np.uint8],
    rgba: NDArray[np.uint8],
    xg: NDArray,
    yg: NDArray,
    out_step: int,
    opacity: float,
) -> NDArray[np.uint8]:
    """Blend the grid-resolution RGBA overlay onto the full-size background.

    Mirrors the GUI geometry contract: the overlay pixmap sits at
    ``(xg.min(), yg.min())`` scaled by ``out_step``. The colormap alpha is
    binary (opaque inside the support, 0 outside), so one SIMD ``addWeighted``
    blend plus a restore-background select reproduces the GUI's
    ``setOpacity(overlay_alpha)`` compositing.
    """
    H, W = bg_bgr.shape[:2]
    gh, gw = rgba.shape[:2]
    ov_w, ov_h = max(1, int(round(gw * out_step))), max(1, int(round(gh * out_step)))
    overlay_bgr = cv2.resize(
        np.ascontiguousarray(rgba[:, :, [2, 1, 0]]),
        (ov_w, ov_h),
        interpolation=cv2.INTER_LINEAR,
    )
    alpha = cv2.resize(rgba[:, :, 3], (ov_w, ov_h), interpolation=cv2.INTER_LINEAR)

    # Clip the overlay rectangle to the image bounds.
    x0, y0 = int(round(float(xg.min()))), int(round(float(yg.min())))
    bx0, by0 = max(0, x0), max(0, y0)
    bx1, by1 = min(W, x0 + ov_w), min(H, y0 + ov_h)
    if bx1 <= bx0 or by1 <= by0:
        return bg_bgr.copy()
    ox0, oy0 = bx0 - x0, by0 - y0
    ox1, oy1 = ox0 + (bx1 - bx0), oy0 + (by1 - by0)

    result = bg_bgr.copy()
    roi_bg = result[by0:by1, bx0:bx1]
    roi_ov = overlay_bgr[oy0:oy1, ox0:ox1]
    inside = alpha[oy0:oy1, ox0:ox1] >= 128
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
    show_deformed: bool = True,
    frame_start: int = 0,
    frame_end: int = -1,
    image_format: str = "png",
    jpeg_quality: int = 92,
    output_max_dim: int = 1024,
    include_colorbar: bool = True,
    colorbar_style: ColorbarStyle | None = None,
    stop_event: threading.Event | None = None,
    progress_cb: ProgressCb | None = None,
) -> list[Path]:
    """Render and save images for each camera, enabled field, and frame.

    Layout: ``{prefix}_images_{timestamp}/{camera}_{field}/frame_XX.{ext}``.

    Args:
        image_files: camera id -> ordered background image paths; frame k uses
            index k in deformed mode and index 0 (reference) otherwise.
        configs: per-field settings; disabled fields are skipped.
        cameras: subset of ``("L", "R")`` to render.
        roi_mask: drawn LEFT reference ROI mask; applied to the L camera only
            (the R camera falls back to the hull support, GUI contract).
        frame_start / frame_end: inclusive 0-based range; ``frame_end < 0``
            means the last frame.
        stop_event: cooperative cancel — checked before every frame.
        progress_cb: called with ``(frames_done, total_frames, label)``.

    Returns:
        Paths of the written image files (partial list when cancelled).
    """
    n_frames = int(result.reconstruction.n_frames)
    if frame_end < 0 or frame_end >= n_frames:
        frame_end = n_frames - 1
    enabled = [c for c in configs if c.enabled]
    if not enabled or frame_end < frame_start:
        return []

    ext = {"png": ".png", "jpeg": ".jpg", "jpg": ".jpg", "tiff": ".tif", "tif": ".tif"}.get(
        image_format.lower(), ".png"
    )
    enc_params = encode_params_for(ext, jpeg_quality)
    cb_style = colorbar_style if colorbar_style is not None else ColorbarStyle()
    images_dir = dest_dir / f"{prefix}_images_{timestamp}"

    # Pre-decode reference backgrounds (frame 0 reused for every frame when
    # plotting on the reference configuration).
    ref_bg: dict[str, NDArray | None] = {}
    if not show_deformed:
        for cam in cameras:
            files = list(image_files.get(cam) or [])
            ref_bg[cam] = _load_gray_u8(files[0]) if files else None

    renderer = FieldmapRenderer()  # shared: reference Delaunay reused across frames
    frames = list(range(frame_start, frame_end + 1))
    total = len(frames)
    done = 0
    paths: list[Path] = []

    for k in frames:
        if stop_event is not None and stop_event.is_set():
            break
        for cam in cameras:
            files = list(image_files.get(cam) or [])
            if show_deformed:
                bg = _load_gray_u8(files[min(k, len(files) - 1)]) if files else None
            else:
                bg = ref_bg.get(cam)
            cam_mask = roi_mask if cam == "L" else None
            for cfg in enabled:
                rendered = render_field_frame(
                    result,
                    cam,
                    cfg.field_id,
                    k,
                    bg,
                    cfg,
                    mesh_step=mesh_step,
                    roi_mask=cam_mask,
                    show_deformed=show_deformed,
                    output_max_dim=output_max_dim,
                    renderer=renderer,
                )
                if rendered is None:
                    continue
                img, vmin, vmax = rendered
                if include_colorbar:
                    img = attach_colorbar(
                        img, cb_style, cfg.colormap, vmin, vmax, colorbar_label(cfg.field_id)
                    )
                field_dir = ensure_dir(images_dir / f"{cam}_{cfg.field_id}")
                out = field_dir / f"{frame_tag(k, n_frames)}{ext}"
                cv2.imwrite(str(out), img, enc_params)
                paths.append(out)
        renderer.clear_frame_caches()  # bound memory; keep the ref Delaunay
        done += 1
        if progress_cb is not None:
            progress_cb(done, total, frame_tag(k, n_frames))

    return paths
