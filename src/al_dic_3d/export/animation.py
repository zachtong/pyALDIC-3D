"""Animated GIF / MP4 export of rendered field frames (Qt-free, streaming).

Ported from the 2D platform's ``al_dic.export.export_animation`` (consulted
read-only): frames stream straight into the encoder one at a time — hundreds
of 4K frames would otherwise pin tens of GB of RAM. MP4 goes through
``cv2.VideoWriter`` (fourcc ``mp4v``) with an XVID/.avi fallback; GIF through
:class:`al_dic_3d.export.gifstream.GifStreamWriter` (imageio's GIF writer
buffered every frame until close and ignored fps — see that module). The
writer opens lazily on the first frame (whose size — including any attached
colorbar strip — fixes the output size; later frames are resized to match).

Honesty (fix batch V; the 2D app fixed the first point in 0.8.0):

* an encoder that cannot open RAISES ``OSError`` — it used to ``break`` and
  return an empty list, which the dialog showed as a green "Wrote 0 file(s)";
* a frame with nothing to draw keeps its time slot as a background-only frame
  (what the canvas shows) and is reported in ``ExportOutcome.skipped``;
* on cancel the unfinished file is DELETED and listed in ``discarded`` — a
  partial video is not a written file; ``cancelled`` is set only when frames
  were really left undone;
* MP4 frames with odd sizes are padded to even (edge-replicated), never cropped.

One file per enabled ``(camera, field)`` pair::

    dest_dir/
      {prefix}_animation_{timestamp}/
        L_U.mp4
        R_exx.gif
        ...

``frame_step`` keeps every Nth frame; the playback fps scales down by the same
factor (``out_fps = round(fps / frame_step)``) so the real-time duration of
the sequence is preserved.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from numpy.typing import NDArray

from al_dic_3d.export.colorbar import ColorbarStyle, add_margin, attach_colorbar
from al_dic_3d.export.gifstream import GifStreamWriter
from al_dic_3d.export.outcome import ExportOutcome, stop_requested, unlink_quietly
from al_dic_3d.export.render import (
    FieldImageConfig,
    _load_gray_u8,
    background_only_frame,
    camera_roi_masks,
    crack_barrier,
    render_field_frame,
)
from al_dic_3d.export.utils import ensure_dir, frame_tag
from al_dic_3d.viz3d.fieldmap import FieldmapRenderer

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult

ProgressCb = Callable[[int, int, str], None]


class StreamingAnimWriter:
    """Append BGR frames to a GIF/MP4/AVI encoder one at a time.

    The output frame size is fixed by the first frame; later frames are
    resized to match. For MP4 the ``mp4v`` codec is tried first, falling back
    to XVID/.avi; when neither opens, the constructor RAISES ``OSError`` (so
    does a GIF whose file cannot be created). ``ok`` stays for older callers
    and is always True on a constructed writer.

    Path note (G3): unlike ``cv2.imread``/``imwrite``, ``cv2.VideoWriter``'s
    FFMPEG backend converts UTF-8 paths itself on Windows, so non-ASCII
    output directories work WITHOUT a pathsafe wrapper (verified on
    opencv-python 5.0.0; regression-pinned by
    tests/test_alien_paths.py::test_animation_writer_under_alien_path).
    The GIF writer uses Python file I/O and is unicode-clean too.
    """

    def __init__(
        self, fmt: str, anim_dir: Path, stem: str, fps: int, frame_hw: tuple[int, int]
    ) -> None:
        self.fmt = str(fmt).lower()
        self.h, self.w = int(frame_hw[0]), int(frame_hw[1])
        self.fps = fps
        self.ok = True
        self.frames_written = 0
        self._closed = False
        anim_dir = Path(anim_dir)
        if self.fmt == "gif":
            self.out = anim_dir / f"{stem}.gif"
            self._w = GifStreamWriter(self.out, fps)  # OSError when not creatable
            return
        if self.fmt not in ("mp4", "avi"):
            raise ValueError(f"unknown animation format {fmt!r} (expected 'mp4' or 'gif')")
        # MPEG-4 encoders need even dimensions; the FFMPEG backend silently
        # CROPPED odd sizes (401x301 -> 400x300). Pad instead (see append).
        self.enc_w, self.enc_h = self.w + (self.w & 1), self.h + (self.h & 1)
        tried: list[str] = []
        for fourcc, ext in (("mp4v", ".mp4"), ("XVID", ".avi")):
            out = anim_dir / f"{stem}{ext}"
            writer = cv2.VideoWriter(
                str(out), cv2.VideoWriter_fourcc(*fourcc), float(fps), (self.enc_w, self.enc_h)
            )
            if writer.isOpened():
                self.out, self._w = out, writer
                return
            writer.release()
            if out.exists() and out.stat().st_size == 0:
                unlink_quietly(out)  # a refused open can leave an empty file
            tried.append(f"{fourcc} {ext}")
        raise OSError(
            f"Could not open a video encoder for {anim_dir / stem} (tried "
            f"{', '.join(tried)}): the FFmpeg backend may be missing, or the "
            "destination is not writable"
        )

    def append(self, frame: NDArray) -> None:
        if frame.shape[:2] != (self.h, self.w):
            frame = cv2.resize(frame, (self.w, self.h), interpolation=cv2.INTER_AREA)
        if self.fmt == "gif":
            self._w.append_rgb(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            if (self.enc_h, self.enc_w) != (self.h, self.w):
                frame = cv2.copyMakeBorder(
                    frame,
                    0,
                    self.enc_h - self.h,
                    0,
                    self.enc_w - self.w,
                    cv2.BORDER_REPLICATE,
                )
            self._w.write(np.ascontiguousarray(frame))
        self.frames_written += 1

    def close(self) -> None:
        """Finalize the file (idempotent)."""
        if self._closed:
            return
        self._closed = True
        if self.fmt == "gif":
            self._w.close()
        else:
            self._w.release()

    def discard(self) -> Path:
        """Close and DELETE the (partial) file; returns its path."""
        self.close()
        unlink_quietly(self.out)
        return self.out


def animation_fps(fps: int, frame_step: int) -> tuple[int, int]:
    """(effective frame_step, playback fps) preserving real duration."""
    frame_step = max(1, int(frame_step))
    return frame_step, max(1, round(fps / frame_step))


def _decorate(
    img: NDArray[np.uint8],
    cfg: FieldImageConfig,
    vmin: float,
    vmax: float,
    *,
    include_colorbar: bool,
    cb_style: ColorbarStyle,
    margin_ratio: float,
    margin_color: str,
) -> NDArray[np.uint8]:
    if include_colorbar:
        img = attach_colorbar(img, cb_style, cfg.colormap, vmin, vmax, cfg.colorbar_text())
    return add_margin(img, margin_ratio, margin_color)


def _background_for(
    k: int, files: Sequence[str], ref_bg: NDArray | None, show_deformed: bool
) -> NDArray | None:
    """Frame k's background (deformed mode) or the shared reference image."""
    if not show_deformed:
        return ref_bg
    return _load_gray_u8(files[min(k, len(files) - 1)]) if files else None


def _placeholder_frame(
    result: RunResult,
    bg: NDArray | None,
    cfg: FieldImageConfig,
    last_range: tuple[float, float],
    output_max_dim: int,
    writer: StreamingAnimWriter,
    decorate: dict,
) -> NDArray[np.uint8]:
    """A no-data frame: the background alone, decorated like its neighbours."""
    shape = (getattr(result, "meta", None) or {}).get("image_size", (0, 0))
    img = background_only_frame(bg, shape, output_max_dim)
    if img is None:  # nothing known about the image: black at the video size
        return np.zeros((writer.h, writer.w, 3), np.uint8)
    return _decorate(img, cfg, *last_range, **decorate)


def export_animation(
    dest_dir: Path,
    prefix: str,
    timestamp: str,
    result: RunResult,
    image_files: dict[str, Sequence[str]],
    configs: Sequence[FieldImageConfig],
    *,
    cameras: Sequence[str] = ("L",),
    fmt: str = "mp4",
    fps: int = 10,
    frame_step: int = 1,
    mesh_step: int = 16,
    roi_mask: NDArray[np.bool_] | None = None,
    right_roi_mask: NDArray[np.bool_] | None = None,
    show_deformed: bool = True,
    frame_start: int = 0,
    frame_end: int = -1,
    output_max_dim: int = 1024,
    include_colorbar: bool = True,
    colorbar_style: ColorbarStyle | None = None,
    margin_ratio: float = 0.0,
    margin_color: str = "white",
    stop_event: threading.Event | None = None,
    progress_cb: ProgressCb | None = None,
) -> ExportOutcome:
    """Export one animation file per enabled ``(camera, field)`` pair.

    Args:
        image_files: camera id -> ordered background image paths (frame k uses
            index k when deformed, index 0 otherwise).
        configs: per-field settings; disabled fields are skipped.
        fmt: ``"mp4"`` or ``"gif"``.
        fps: timeline frames per second BEFORE decimation; playback fps is
            ``round(fps / frame_step)`` so real duration is preserved (a GIF
            plays at most :data:`al_dic_3d.export.gifstream.GIF_MAX_FPS`).
        frame_step: keep every Nth frame (1 = all).
        roi_mask / right_roi_mask: drawn LEFT ROI; the right camera uses it
            warped through the frame-1 correspondence (warped once here unless
            the caller passes ``right_roi_mask``).
        margin_ratio / margin_color: blank border around every encoded frame
            (colorbar included) as a fraction of the long edge (0 = none) —
            the Preview & Colorbar tab's margin settings (2D idiom).
        stop_event: cooperative cancel — checked before every frame.
        progress_cb: called with ``(frames_done, total_frames, label)`` over
            ALL passes, where label is the ``{camera}_{field}`` encoding now.

    Returns:
        The finished animation files as an :class:`ExportOutcome` (see the
        module docstring for ``skipped`` / ``unavailable`` / ``discarded``).

    Raises:
        OSError: an encoder could not be opened.
    """
    outcome = ExportOutcome()
    n_frames = int(result.reconstruction.n_frames)
    if frame_end < 0 or frame_end >= n_frames:
        frame_end = n_frames - 1
    enabled = [c for c in configs if c.enabled]
    if not enabled or frame_end < frame_start:
        return outcome

    fmt = fmt.lower()
    frame_step, out_fps = animation_fps(fps, frame_step)
    frame_indices = list(range(frame_start, frame_end + 1, frame_step))
    total = len(frame_indices) * len(cameras) * len(enabled)
    cb_style = colorbar_style if colorbar_style is not None else ColorbarStyle()
    anim_dir = ensure_dir(dest_dir / f"{prefix}_animation_{timestamp}")
    masks, warnings = camera_roi_masks(result, cameras, roi_mask, image_files, right_roi_mask)
    outcome.warnings += warnings
    decorate = dict(
        include_colorbar=include_colorbar,
        cb_style=cb_style,
        margin_ratio=margin_ratio,
        margin_color=margin_color,
    )

    renderer = FieldmapRenderer()
    done = 0
    # Item 4 WYSIWYG: when the run was crack-aware, the drawn L ROI mask doubles
    # as the crack barrier for the dense render's cell blanking — mirror the
    # still-image path (export/render.py) so video frames match the PNG export
    # and the strain canvas. None (crack-free) leaves frames byte-identical.
    barrier = crack_barrier(result, roi_mask)

    for cam in cameras:
        if outcome.cancelled:
            break
        files = list(image_files.get(cam) or [])
        ref_bg = _load_gray_u8(files[0]) if (files and not show_deformed) else None

        for cfg in enabled:
            if outcome.cancelled:
                break
            label = f"{cam}_{cfg.field_id}"
            writer: StreamingAnimWriter | None = None
            pending: list[int] = []  # no-data frames before the writer could open
            missing: list[str] = []
            last_range = (float(cfg.vmin), float(cfg.vmax)) if not cfg.auto_range else (0.0, 1.0)

            try:
                for k in frame_indices:
                    if stop_requested(stop_event):
                        outcome.cancelled = True
                        break
                    bg = _background_for(k, files, ref_bg, show_deformed)
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
                        missing.append(f"{label} {frame_tag(k, n_frames)}")
                        if writer is None:
                            pending.append(k)
                        else:
                            writer.append(
                                _placeholder_frame(
                                    result, bg, cfg, last_range, output_max_dim, writer, decorate
                                )
                            )
                    else:
                        img, vmin, vmax = rendered
                        last_range = (vmin, vmax)
                        img = _decorate(img, cfg, vmin, vmax, **decorate)
                        # Lazily open the encoder once the first frame's size is
                        # known (that size includes the colorbar strip).
                        if writer is None:
                            writer = StreamingAnimWriter(
                                fmt, anim_dir, label, out_fps, img.shape[:2]
                            )
                            for kp in pending:  # keep the no-data frames' slots
                                kbg = _background_for(kp, files, ref_bg, show_deformed)
                                writer.append(
                                    _placeholder_frame(
                                        result,
                                        kbg,
                                        cfg,
                                        last_range,
                                        output_max_dim,
                                        writer,
                                        decorate,
                                    )
                                )
                            pending = []
                        writer.append(img)

                    # P3.1: drop this frame's Tier-1 grids + support masks NOW.
                    # Each (frame, field) is rendered exactly once per animation,
                    # so the entries provide zero reuse — leaving the clear
                    # outside the frame loop let ~2 GB of dense grids accumulate
                    # over a 200-frame encode. The reference-frame Delaunay
                    # interpolators survive the clear.
                    renderer.clear_frame_caches()
                    done += 1
                    if progress_cb is not None:
                        progress_cb(done, total, label)
            except BaseException:
                if writer is not None:
                    writer.discard()  # never leave a truncated file behind
                raise

            if outcome.cancelled:
                if writer is not None:
                    outcome.discarded.append(writer.discard())
                break
            if writer is None:
                outcome.unavailable.append(label)  # no frame of this pass had data
                continue
            writer.close()
            outcome.append(writer.out)
            outcome.skipped += missing

    return outcome
