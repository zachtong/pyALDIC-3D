"""Streaming animated-GIF writer (Qt-free): one frame in memory, exact timing.

Why not imageio: its GIF writer (Pillow backend, imageio 2.37) keeps EVERY frame
in a list until ``close()`` — measured +192 MB per 60 frames at 1024x768 with
nothing on disk until the end, i.e. gigabytes for a long full-resolution
export — and its ``duration`` is in MILLISECONDS. The historical
``duration=1/fps`` (seconds) wrote a frame delay of 0, so the fps setting had
no effect at all (verified by reading the delays back; fix batch V).

This writer streams through Pillow's frame-level GIF helpers
(``GifImagePlugin.getheader`` / ``getdata``): the header is written with the
first frame and every later frame goes to disk as soon as it arrives. Only the
previous frame is retained, to encode each new frame as the bounding box of
the pixels that changed ("leave in place" disposal) — for a static background
this keeps files as small as the buffered writer's. Each frame gets its own
adaptive 256-colour palette, the same quantizer Pillow's own save path uses.

Timing: GIF delays are integer centiseconds. Frame ``k`` is shown from
``round(k * 100 / fps)`` to ``round((k + 1) * 100 / fps)`` cs, so the AVERAGE
rate is exact (30 fps alternates 3/4/3 cs) instead of drifting. Delays below
2 cs are raised to 2 cs because browsers and most viewers slow 0-1 cs frames
down to 10 cs: a GIF therefore plays at most :data:`GIF_MAX_FPS` (MP4 has no
such limit).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

#: Smallest frame delay (centiseconds) viewers honour; faster GIFs get slowed.
GIF_MIN_DELAY_CS = 2
#: Highest frame rate a GIF can play at (1 / GIF_MIN_DELAY_CS).
GIF_MAX_FPS = 100 // GIF_MIN_DELAY_CS


class GifStreamWriter:
    """Append RGB frames to an animated GIF, writing each one immediately.

    Raises ``OSError`` when the file cannot be created (missing folder,
    read-only destination). Python file I/O is used, so non-ASCII paths work.
    """

    def __init__(self, path: Path, fps: float, *, loop: int = 0) -> None:
        self.path = Path(path)
        self.fps = max(float(fps), 1e-6)
        self.n_frames = 0
        self._loop = int(loop)
        self._prev: NDArray[np.uint8] | None = None
        self._fh = open(self.path, "wb")  # noqa: SIM115 - closed in close()

    def _next_delay_ms(self) -> int:
        k = self.n_frames
        cs = round((k + 1) * 100.0 / self.fps) - round(k * 100.0 / self.fps)
        return max(GIF_MIN_DELAY_CS, cs) * 10

    def append_rgb(self, rgb: NDArray[np.uint8]) -> None:
        """Encode one ``(H, W, 3)`` uint8 RGB frame (same size as the first)."""
        from PIL import GifImagePlugin, Image

        if self._fh is None:
            raise ValueError("GIF writer is closed")
        rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
        delay = self._next_delay_ms()
        if self._prev is None:
            region, offset = rgb, (0, 0)
        else:
            if rgb.shape != self._prev.shape:
                raise ValueError(f"GIF frame size {rgb.shape} != first frame {self._prev.shape}")
            changed = np.any(rgb != self._prev, axis=2)
            rows = np.flatnonzero(changed.any(axis=1))
            if rows.size == 0:
                # Unchanged frame: a 1x1 patch keeps its time slot on screen.
                y0, y1, x0, x1 = 0, 1, 0, 1
            else:
                cols = np.flatnonzero(changed.any(axis=0))
                y0, y1, x0, x1 = int(rows[0]), int(rows[-1]) + 1, int(cols[0]), int(cols[-1]) + 1
            region, offset = np.ascontiguousarray(rgb[y0:y1, x0:x1]), (x0, y0)

        # Image.Palette arrived in Pillow 9.1 (the bare constant left in 10).
        adaptive = getattr(getattr(Image, "Palette", None), "ADAPTIVE", None)
        if adaptive is None:
            adaptive = Image.ADAPTIVE
        im = Image.fromarray(region).convert("P", palette=adaptive)  # (h, w, 3) uint8 -> RGB
        if self._prev is None:
            header, _ = GifImagePlugin.getheader(im, info={"loop": self._loop})
            for chunk in header:
                self._fh.write(chunk)
        for chunk in GifImagePlugin.getdata(
            im, offset=offset, duration=delay, disposal=1, include_color_table=True
        ):
            self._fh.write(chunk)
        self._fh.flush()
        self._prev = rgb
        self.n_frames += 1

    def close(self) -> None:
        """Write the trailer and close (idempotent)."""
        if self._fh is None:
            return
        try:
            if self.n_frames:
                self._fh.write(b";")
        finally:
            self._fh.close()
            self._fh = None
            self._prev = None
