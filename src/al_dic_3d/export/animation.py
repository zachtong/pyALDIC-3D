"""Animated GIF / MP4 export of rendered field frames (Qt-free, streaming).

Ported from the 2D platform's ``al_dic.export.export_animation`` (consulted
read-only): frames stream straight into the encoder one at a time — hundreds
of 4K frames would otherwise pin tens of GB of RAM. GIF goes through imageio;
MP4 through ``cv2.VideoWriter`` (fourcc ``mp4v``) with an XVID/.avi fallback.
The writer opens lazily on the first frame (whose size — including any
attached colorbar strip — fixes the output size; later frames are resized to
match).

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

from al_dic_3d.export.colorbar import (
    ColorbarStyle,
    add_margin,
    attach_colorbar,
    colorbar_label,
)
from al_dic_3d.export.render import (
    FieldImageConfig,
    _load_gray_u8,
    render_field_frame,
)
from al_dic_3d.export.utils import ensure_dir
from al_dic_3d.viz3d.fieldmap import FieldmapRenderer

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult

ProgressCb = Callable[[int, int, str], None]


class StreamingAnimWriter:
    """Append BGR frames to a GIF/MP4/AVI encoder one at a time.

    The output frame size is fixed by the first frame; later frames are
    resized to match. For MP4 the ``mp4v`` codec is tried first, falling back
    to XVID/.avi. ``ok`` is False when no encoder could be opened.

    Path note (G3): unlike ``cv2.imread``/``imwrite``, ``cv2.VideoWriter``'s
    FFMPEG backend converts UTF-8 paths itself on Windows, so non-ASCII
    output directories work WITHOUT a pathsafe wrapper (verified on
    opencv-python 5.0.0; regression-pinned by
    tests/test_alien_paths.py::test_animation_writer_under_alien_path).
    imageio's GIF writer uses Python file I/O and is unicode-clean too.
    """

    def __init__(
        self, fmt: str, anim_dir: Path, stem: str, fps: int, frame_hw: tuple[int, int]
    ) -> None:
        self.fmt = fmt
        self.h, self.w = frame_hw
        self.fps = fps
        self.ok = True
        if fmt == "gif":
            import imageio

            self.out = anim_dir / f"{stem}.gif"
            self._w = imageio.get_writer(
                str(self.out), format="GIF", mode="I", duration=1.0 / max(fps, 1), loop=0
            )
            return
        # MP4 (mp4v) with AVI (XVID) fallback
        self.out = anim_dir / f"{stem}.mp4"
        self._w = cv2.VideoWriter(
            str(self.out), cv2.VideoWriter_fourcc(*"mp4v"), float(fps), (self.w, self.h)
        )
        if not self._w.isOpened():
            self.out = anim_dir / f"{stem}.avi"
            self._w = cv2.VideoWriter(
                str(self.out), cv2.VideoWriter_fourcc(*"XVID"), float(fps), (self.w, self.h)
            )
            self.ok = self._w.isOpened()

    def append(self, frame: NDArray) -> None:
        if frame.shape[:2] != (self.h, self.w):
            frame = cv2.resize(frame, (self.w, self.h))
        if self.fmt == "gif":
            self._w.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            self._w.write(frame)

    def close(self) -> None:
        if self.fmt == "gif":
            self._w.close()
        else:
            self._w.release()


def animation_fps(fps: int, frame_step: int) -> tuple[int, int]:
    """(effective frame_step, playback fps) preserving real duration."""
    frame_step = max(1, int(frame_step))
    return frame_step, max(1, round(fps / frame_step))


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
) -> list[Path]:
    """Export one animation file per enabled ``(camera, field)`` pair.

    Args:
        image_files: camera id -> ordered background image paths (frame k uses
            index k when deformed, index 0 otherwise).
        configs: per-field settings; disabled fields are skipped.
        fmt: ``"mp4"`` or ``"gif"``.
        fps: timeline frames per second BEFORE decimation; playback fps is
            ``round(fps / frame_step)`` so real duration is preserved.
        frame_step: keep every Nth frame (1 = all).
        margin_ratio / margin_color: blank border around every encoded frame
            (colorbar included) as a fraction of the long edge (0 = none) —
            the Preview & Colorbar tab's margin settings (2D idiom).
        stop_event: cooperative cancel — checked before every frame.
        progress_cb: called with ``(frames_done, total_frames, label)`` where
            label is the ``{camera}_{field}`` currently encoding.

    Returns:
        Paths of the written animation files (finished ones when cancelled).
    """
    n_frames = int(result.reconstruction.n_frames)
    if frame_end < 0 or frame_end >= n_frames:
        frame_end = n_frames - 1
    enabled = [c for c in configs if c.enabled]
    if not enabled or frame_end < frame_start:
        return []

    fmt = fmt.lower()
    frame_step, out_fps = animation_fps(fps, frame_step)
    frame_indices = list(range(frame_start, frame_end + 1, frame_step))
    total = len(frame_indices)
    cb_style = colorbar_style if colorbar_style is not None else ColorbarStyle()
    anim_dir = ensure_dir(dest_dir / f"{prefix}_animation_{timestamp}")

    renderer = FieldmapRenderer()
    paths: list[Path] = []
    cancelled = False
    # Item 4 WYSIWYG: when the run was crack-aware, the drawn L ROI mask doubles
    # as the crack barrier for the dense render's cell blanking — mirror the
    # still-image path (export/render.py) so video frames match the PNG export
    # and the strain canvas. None (crack-free) leaves frames byte-identical.
    barrier = (
        np.asarray(roi_mask, dtype=np.float64)
        if (roi_mask is not None and bool(result.meta.get("crack_aware", False)))
        else None
    )

    for cam in cameras:
        if cancelled:
            break
        files = list(image_files.get(cam) or [])
        ref_bg = _load_gray_u8(files[0]) if (files and not show_deformed) else None
        cam_mask = roi_mask if cam == "L" else None

        for cfg in enabled:
            if cancelled:
                break
            label = f"{cam}_{cfg.field_id}"
            writer: StreamingAnimWriter | None = None
            done = 0

            for k in frame_indices:
                if stop_event is not None and stop_event.is_set():
                    cancelled = True
                    break
                if show_deformed:
                    bg = _load_gray_u8(files[min(k, len(files) - 1)]) if files else None
                else:
                    bg = ref_bg
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
                    barrier_mask=barrier if cam == "L" else None,
                )
                if rendered is None:
                    continue
                img, vmin, vmax = rendered
                if include_colorbar:
                    img = attach_colorbar(
                        img, cb_style, cfg.colormap, vmin, vmax, colorbar_label(cfg.field_id)
                    )
                img = add_margin(img, margin_ratio, margin_color)

                # Lazily open the encoder once the first frame's size is known
                # (that size includes the colorbar strip when present).
                if writer is None:
                    w = StreamingAnimWriter(fmt, anim_dir, label, out_fps, img.shape[:2])
                    if not w.ok:
                        w.close()
                        break
                    writer = w
                writer.append(img)

                # P3.1: drop this frame's Tier-1 grids + support masks NOW
                # (mirrors export/render.py's per-frame clear). Each (frame,
                # field) is rendered exactly once per animation, so the entries
                # provide zero reuse — leaving the clear outside the frame loop
                # let ~2 GB of dense grids accumulate over a 200-frame encode.
                # The reference-frame Delaunay interpolators survive the clear.
                renderer.clear_frame_caches()
                done += 1
                if progress_cb is not None:
                    progress_cb(done, total, label)

            if writer is not None:
                writer.close()
                paths.append(writer.out)

    return paths
