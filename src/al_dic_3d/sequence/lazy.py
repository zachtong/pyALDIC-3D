"""Lazy, path-backed frame and mask streams (Qt-free) — perf batch P1.2.

The eager path materializes every frame of both cameras as float64 up front
(~16 GB for 200 x 5 Mpx x 2 cameras) before a single subset is matched. The
providers here decode on demand and keep only a small bounded LRU resident, so
peak memory is a few frames per camera regardless of sequence length.

Semantics note: in the 3D layer, frames flow **RAW** end to end (stereo match,
seeds, and the temporal honesty gate all consume raw intensities; the 2D
engine's ROI-based normalization happens later, inside
:func:`al_dic_3d.matching.temporal.temporal_track`, via an engine-protocol
adapter). ``get_normalized`` is therefore the *protocol* name shared with the
2D engine's providers — here it serves the raw decoded frame, exactly like
:class:`al_dic_3d.sequence.model.ArrayFrameProvider` serves the raw arrays it
was built from.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

_LRU_CAPACITY = 4  # frames resident per stream (ref + current pair + slack)


def load_gray(path: str | Path) -> NDArray[np.float64]:
    """Decode one image file to a float64 grayscale ``(H, W)`` array.

    ``IMREAD_UNCHANGED`` preserves the native bit depth (scientific DIC images
    are often 16-bit or float); colour input collapses to a single channel.
    Decoding goes through :func:`al_dic_3d.pathsafe.imread_unicode` (G3):
    byte-identical to ``cv2.imread`` but survives non-ASCII Windows paths.
    """
    import cv2

    from al_dic_3d.pathsafe import imread_unicode

    img = imread_unicode(path)
    if img is None:
        raise ValueError(f"cannot read image: {path}")
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.shape[2] == 3 else img[..., 0]
    return img.astype(np.float64)


class _LruDecoder:
    """Shared decode-on-demand core: path list + bounded LRU of float64 arrays.

    Thread-safe (P3.6): the LRU map is mutated under a lock — the parallel
    track-both path runs the two camera tracks on worker threads while the
    GUI thread may scrub frames from the same provider. Decoding happens
    outside the lock (a rare concurrent double-decode is idempotent); callers
    treat returned arrays as read-only, so sharing cache hits stays safe.
    """

    def __init__(self, paths: Sequence[str | Path], capacity: int = _LRU_CAPACITY) -> None:
        self._paths = [Path(p) for p in paths]
        self._capacity = max(1, int(capacity))
        self._cache: OrderedDict[int, NDArray[np.float64]] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def paths(self) -> list[Path]:
        return list(self._paths)

    def __len__(self) -> int:
        return len(self._paths)

    def _get(self, idx: int) -> NDArray[np.float64]:
        with self._lock:
            cached = self._cache.get(idx)
            if cached is not None:
                self._cache.move_to_end(idx)
                return cached
        frame = load_gray(self._paths[idx])
        with self._lock:
            self._cache[idx] = frame
            while len(self._cache) > self._capacity:
                self._cache.popitem(last=False)
        return frame


class LazyFrameProvider(_LruDecoder):
    """Path-backed :class:`~al_dic_3d.sequence.model.FrameProvider` (raw frames).

    Decodes frames on demand with a bounded LRU (default 4) instead of holding
    the whole camera stream. ``shape`` lazily decodes frame 0 on first access.
    Serves each frame as loaded (see module docstring for the raw-frame
    convention); callers must treat returned arrays as read-only — they may be
    shared with other cache hits.
    """

    def __init__(self, paths: Sequence[str | Path], capacity: int = _LRU_CAPACITY) -> None:
        super().__init__(paths, capacity)
        self._shape: tuple[int, int] | None = None

    @property
    def shape(self) -> tuple[int, int]:
        if self._shape is None:
            self._shape = (0, 0) if not self._paths else tuple(self._get(0).shape)
        return self._shape

    def get_normalized(self, idx: int) -> NDArray[np.float64]:
        return self._get(idx)


class LazyMaskList(Sequence):
    """Path-backed per-frame mask stream: ``masks[i]`` decodes on demand (LRU).

    A drop-in replacement for a ``list`` of float64 mask arrays: the 2D engine
    only ever does ``len(masks)`` and ``masks[i].astype(...)``, and the 3D
    layer indexes single masks — so lazily decoding via ``__getitem__`` keeps
    at most a handful resident. Non-zero pixels mean valid, matching the eager
    loader; values are served as float64 contiguous arrays.
    """

    def __init__(self, paths: Sequence[str | Path], capacity: int = _LRU_CAPACITY) -> None:
        self._decoder = _LruDecoder(paths, capacity)

    @property
    def paths(self) -> list[Path]:
        return self._decoder.paths

    def __len__(self) -> int:
        return len(self._decoder)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return [self[i] for i in range(*idx.indices(len(self)))]
        return np.ascontiguousarray(self._decoder._get(idx), dtype=np.float64)
