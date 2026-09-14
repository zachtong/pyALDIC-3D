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
    return decode_gray(path).astype(np.float64)


def decode_gray(path: str | Path) -> NDArray:
    """:func:`load_gray` in the file's NATIVE dtype (uint8 / uint16 / float).

    The lazy providers cache this form: an 8-bit frame costs 1 byte per pixel
    instead of 8 (fix batch V: ~0.7 GB less resident at 12 Mpx). Converting to
    float64 on access is exact for every integer bit depth.
    """
    import cv2

    from al_dic_3d.pathsafe import imread_unicode

    img = imread_unicode(path)
    if img is None:
        raise ValueError(f"cannot read image: {path}")
    if img.ndim == 3:
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elif img.shape[2] == 4:  # BGRA: channel 0 alone is BLUE, not luminance
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        else:
            img = img[..., 0]
    return np.ascontiguousarray(img)


def as_binary_mask(mask) -> NDArray[np.float64]:
    """Return ``mask`` as a contiguous float64 array in ``{0, 1}`` (non-zero = valid).

    The 2D engine multiplies image gradients by the mask, so anything other than
    0/1 rescales the IC-GN step: a 0/255 mask file made every update 1/255 of its
    true size and let the solver "converge" on its integer seed (fix batch V).
    A float64 C-contiguous array already within ``[0, 1]`` is returned unchanged
    (no copy), so shared constant masks stay shared; anything else is
    thresholded at zero.
    """
    m = np.asarray(mask)
    if (
        m.dtype == np.float64
        and m.flags["C_CONTIGUOUS"]
        and m.size
        and float(m.min()) >= 0.0
        and float(m.max()) <= 1.0
    ):
        return m
    return np.ascontiguousarray(m > 0, dtype=np.float64)


class _BinaryMaskView(Sequence):
    """Indexed view that binarizes each mask of a foreign lazy sequence on access."""

    def __init__(self, base: Sequence) -> None:
        self._base = base

    def __len__(self) -> int:
        return len(self._base)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return [self[i] for i in range(*idx.indices(len(self)))]
        return as_binary_mask(self._base[idx])


def binary_mask_sequence(masks: Sequence) -> Sequence:
    """Return ``masks`` so that every element is a ``{0, 1}`` float64 array.

    Eager lists/tuples are coerced element-wise (binary float64 arrays are kept
    as the same objects, so a shared constant mask stays ONE array);
    :class:`LazyMaskList` already binarizes at decode and passes through
    unmaterialized; any other lazy sequence is wrapped in a binarizing view.
    """
    if isinstance(masks, (list, tuple)):
        return [as_binary_mask(m) for m in masks]
    if isinstance(masks, (LazyMaskList, _BinaryMaskView)):
        return masks
    return _BinaryMaskView(masks)


def _binary_u8(mask: NDArray) -> NDArray[np.uint8]:
    """``{0, 1}`` uint8 form of a decoded mask file (non-zero = valid)."""
    return np.ascontiguousarray(np.asarray(mask) > 0, dtype=np.uint8)


class _LruDecoder:
    """Shared decode-on-demand core: path list + bounded LRU of float64 arrays.

    Thread-safe (P3.6): the LRU map is mutated under a lock — the parallel
    track-both path runs the two camera tracks on worker threads while the
    GUI thread may scrub frames from the same provider. Decoding happens
    outside the lock (a rare concurrent double-decode is idempotent); callers
    treat returned arrays as read-only, so sharing cache hits stays safe.
    """

    def __init__(
        self,
        paths: Sequence[str | Path],
        capacity: int = _LRU_CAPACITY,
        transform=None,
        decode=None,
    ) -> None:
        self._decode = load_gray if decode is None else decode
        self._paths = [Path(p) for p in paths]
        self._capacity = max(1, int(capacity))
        self._cache: OrderedDict[int, NDArray[np.float64]] = OrderedDict()
        self._lock = threading.Lock()
        self._transform = transform  # applied once per decode (e.g. mask binarization)

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
        frame = self._decode(self._paths[idx])
        if self._transform is not None:
            frame = self._transform(frame)
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
        # The LRU holds frames in their native dtype; get_normalized returns a
        # float64 copy (exact), so callers can never write into the cache.
        super().__init__(paths, capacity, decode=decode_gray)
        self._shape: tuple[int, int] | None = None

    @property
    def shape(self) -> tuple[int, int]:
        if self._shape is None:
            self._shape = (0, 0) if not self._paths else tuple(self._get(0).shape)
        return self._shape

    def get_normalized(self, idx: int) -> NDArray[np.float64]:
        frame = self._get(idx)
        expected = self.shape
        if tuple(frame.shape) != tuple(expected):
            raise ValueError(
                f"image {self._paths[idx].name} is {frame.shape[1]}x{frame.shape[0]} but the "
                f"first frame is {expected[1]}x{expected[0]}: every frame of a camera "
                "must have the same size"
            )
        return frame.astype(np.float64)


class LazyMaskList(Sequence):
    """Path-backed per-frame mask stream: ``masks[i]`` decodes on demand (LRU).

    A drop-in replacement for a ``list`` of float64 mask arrays: the 2D engine
    only ever does ``len(masks)`` and ``masks[i].astype(...)``, and the 3D
    layer indexes single masks — so lazily decoding via ``__getitem__`` keeps
    at most a handful resident. Non-zero pixels mean valid; every mask is
    BINARIZED to ``{0.0, 1.0}`` at decode time (:func:`as_binary_mask`) and served
    as a float64 contiguous array — the engine multiplies gradients by the mask,
    so a raw 0/255 file must never reach it (fix batch V).
    """

    def __init__(self, paths: Sequence[str | Path], capacity: int = _LRU_CAPACITY) -> None:
        # The LRU holds uint8 {0, 1} (1/8 of float64: ~0.4 GB less per camera
        # at 12 Mpx); each access returns a fresh float64 copy.
        self._decoder = _LruDecoder(paths, capacity, transform=_binary_u8, decode=decode_gray)
        self._shape: tuple[int, int] | None = None

    @property
    def paths(self) -> list[Path]:
        return self._decoder.paths

    def __len__(self) -> int:
        return len(self._decoder)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return [self[i] for i in range(*idx.indices(len(self)))]
        m = self._decoder._get(idx).astype(np.float64, order="C")
        if self._shape is None:
            self._shape = tuple(m.shape)
        elif tuple(m.shape) != self._shape:
            raise ValueError(
                f"mask {self._decoder._paths[idx].name} is {m.shape[1]}x{m.shape[0]} but the "
                f"first mask is {self._shape[1]}x{self._shape[0]}: all masks of a camera "
                "must have the image size"
            )
        return m
