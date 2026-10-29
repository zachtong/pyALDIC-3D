"""The right camera's region of interest, seen through the frame-1 links (Qt-free).

The region of interest is drawn on the LEFT camera. A right camera without masks
of its own used to track the whole bounding-box grid around its frame-1 stereo
links, background included. On a low-texture background a few background nodes
clip the engine's integer FFT search; the engine then widens the search for
every node, up to half the image, and on the first deformed frame no node was
solved (1.2.1 dropped that frame, 1.1.0 aborted the run).

The right camera now gets the left masks warped into the right image through
the frame-1 links (:func:`al_dic_3d.viz3d.maskwarp.warp_mask_left_to_right`, the
warp the right-camera display already uses) on its reference frames, and ones
on the others: the rule the left camera follows
(:func:`al_dic_3d.matching.temporal.reference_frame_masks`). The warped region
is widened by a rim, so the grid nodes next to it, which carry the outermost
links, stay in the track; thin gaps (cracks) keep no rim. A per-frame left mask
is warped through the same frame-1 links, which holds while the stereo
disparity changes little over the test. Masks the user gives for the right
camera are used as given.
"""

from __future__ import annotations

import threading
import warnings
from collections import OrderedDict
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from al_dic import FrameSchedule  # type-only; ledgered in DEPENDS_ON_2D.md

    from al_dic_3d.sequence import StereoSequence

#: Warped reference masks kept per stream (boolean, one image each).
_CACHE_SIZE = 4

ROI_NOTE = "right-camera region: the left one through the frame-1 links"
NO_ROI_NOTE = "the region could not be carried into the right camera, which tracks its whole grid"


def rim_width(winsize: int, winstepsize: int) -> int:
    """Rim (px) keeping every grid node whose subset reaches the region, and the next ring."""
    return max(int(winsize) // 2, int(winstepsize))


def derive_right_roi(
    mask_left: NDArray | None,
    coords_left: NDArray[np.float64],
    right_pts: NDArray[np.float64],
    out_shape: tuple[int, int],
    *,
    extrapolate: bool = False,
    rim_px: int = 0,
) -> NDArray[np.float64] | None:
    """The left mask warped into the right image through the frame-1 links, or None.

    ``mask_left`` None stands for "all the left mesh covers": the result is then
    the hull of the linked right positions. Rows of ``right_pts`` that are NaN
    (links that failed) are ignored. ``extrapolate`` carries the warp past the
    links with the nearest link's disparity, for a later frame's mask that
    reaches beyond the frame-1 region. ``rim_px`` widens the region by that many
    pixels, outward and into holes, but not across gaps narrower than about
    twice the rim, which stay masked (a crack keeps cutting the grid). Returns a
    ``float64`` 0/1 mask, or None when the links are too few or too degenerate
    to define the warp (a warning names an unexpected failure).
    """
    from al_dic_3d.viz3d.maskwarp import warp_mask_left_to_right

    shape = (int(out_shape[0]), int(out_shape[1]))
    left = np.ones(shape, dtype=bool) if mask_left is None else np.asarray(mask_left) > 0.5
    extrapolate = bool(extrapolate) and mask_left is not None
    try:
        warped = warp_mask_left_to_right(
            left, coords_left, right_pts, shape, fill_to_hull=True, extrapolate=extrapolate
        )
        if warped is None or not warped.any():
            return None
        if rim_px > 0:
            warped = _with_rim(warped, int(rim_px))
    except Exception as exc:  # noqa: BLE001 - a failed warp keeps the whole-grid behaviour
        warnings.warn(
            f"could not carry the region into the right camera "
            f"({type(exc).__name__}: {exc}); the right camera tracks its whole grid.",
            UserWarning,
            stacklevel=2,
        )
        return None
    return warped.astype(np.float64)


def _with_rim(mask: NDArray[np.bool_], rim_px: int) -> NDArray[np.bool_]:
    """``mask`` dilated by ``rim_px``, except over gaps a closing would fill (cracks)."""
    import cv2

    side = 2 * rim_px + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (side, side))
    m = mask.astype(np.uint8)
    grown = cv2.dilate(m, kernel)
    thin_gaps = cv2.erode(grown, kernel).astype(bool) & ~mask  # what a closing fills
    return mask | (grown.astype(bool) & ~thin_gaps)


class RightReferenceMasks(Sequence):
    """Right-camera mask stream: the warped left mask on reference frames, ones elsewhere.

    Lazy: a reference frame's mask is warped when the engine first asks for it.
    For a list of left masks one warp serves every frame holding the same mask
    object (the region drawn on frame 1); a lazily decoded stream is keyed by
    frame. A few warps are kept, as booleans. Thread-safe.
    """

    def __init__(
        self,
        left_masks: Sequence[NDArray] | None,
        coords_left: NDArray[np.float64],
        right_pts: NDArray[np.float64],
        out_shape: tuple[int, int],
        refs: Iterable[int],
        *,
        n_frames: int | None = None,
        rim_px: int = 0,
    ) -> None:
        if left_masks is None and n_frames is None:
            raise ValueError("n_frames is required without left masks")
        self._rim = int(rim_px)
        self._left = left_masks
        # A list holds its masks, so their ids stay valid keys; a lazy stream
        # decodes a fresh array per access and is keyed by frame instead.
        self._by_object = left_masks is None or isinstance(left_masks, (list, tuple))
        self._first = left_masks[0] if self._by_object and left_masks is not None else None
        self._coords = np.asarray(coords_left, dtype=np.float64)
        self._right = np.asarray(right_pts, dtype=np.float64)
        self._shape = (int(out_shape[0]), int(out_shape[1]))
        self._refs = frozenset(int(k) for k in refs)
        self._n = int(n_frames) if n_frames is not None else len(left_masks)
        self._ones = np.ones(self._shape, dtype=np.float64)
        self._cache: OrderedDict[tuple, NDArray[np.bool_] | None] = OrderedDict()
        self._lock = threading.Lock()
        self._warned = False

    def __len__(self) -> int:
        return self._n

    def reference(self, idx: int) -> NDArray[np.float64] | None:
        """The warped left mask of frame ``idx`` (None when the warp is impossible)."""
        left_k = None if self._left is None else self._left[idx]
        # Frame 1's mask lies within its own links; a later one may reach past
        # them, unless it is frame 1's own mask (the drawn region, reused).
        extrapolate = idx != 0 and not (self._by_object and left_k is self._first)
        key = (id(left_k) if self._by_object else idx, extrapolate)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                hit = self._cache[key]
                return None if hit is None else hit.astype(np.float64)
        warped = derive_right_roi(
            left_k,
            self._coords,
            self._right,
            self._shape,
            extrapolate=extrapolate,
            rim_px=self._rim,
        )
        stored = None if warped is None else warped > 0.5
        with self._lock:
            self._cache[key] = stored
            if len(self._cache) > _CACHE_SIZE:
                self._cache.popitem(last=False)
        return warped

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return [self[i] for i in range(*idx.indices(self._n))]
        if idx < 0:
            idx += self._n
        if not 0 <= idx < self._n:
            raise IndexError(idx)
        if idx not in self._refs:
            return self._ones
        warped = self.reference(idx)
        if warped is None:
            if not self._warned:
                self._warned = True
                warnings.warn(
                    f"could not carry the left mask of frame {idx + 1} into the right "
                    f"camera; that frame's right camera is not masked.",
                    UserWarning,
                    stacklevel=2,
                )
            return self._ones
        return warped


def right_camera_masks(
    seq: StereoSequence,
    coords_left: NDArray[np.float64],
    right_pts: NDArray[np.float64],
    *,
    reference_mode: str,
    schedule: FrameSchedule | None = None,
    rim_px: int = 0,
    cam_left: str = "L",
    cam_right: str = "R",
) -> tuple[NDArray[np.float64] | None, Sequence[NDArray[np.float64]] | None, str]:
    """``(frame-1 mask, mask stream, note)`` for the right camera's temporal track.

    Masks given for the right camera are returned as given (and an empty note).
    Otherwise the left masks (or, without any, the left mesh's footprint) are
    carried into the right image through the frame-1 links ``coords_left ->
    right_pts`` on the reference frames of ``schedule`` (default: the one
    ``reference_mode`` implies), widened by ``rim_px`` (see
    :func:`derive_right_roi` and :func:`rim_width`). ``(None, None, note)``, with
    a warning, when that is impossible: the right camera then tracks its whole
    grid as before.
    """
    own = seq.masks.get(cam_right)
    if own is not None:
        from al_dic_3d.sequence.lazy import binary_mask_sequence

        return seq.mask(cam_right, 0), binary_mask_sequence(own), ""
    n = seq.n_frames
    if schedule is None:
        from al_dic.core.data_structures import FrameSchedule  # DEPENDS_ON_2D.md

        schedule = FrameSchedule.from_mode(reference_mode, n)
    out_shape = tuple(seq.providers[cam_right].shape)
    stream = RightReferenceMasks(
        seq.masks.get(cam_left),
        coords_left,
        right_pts,
        out_shape,
        schedule.ref_frame_set,
        n_frames=n,
        rim_px=rim_px,
    )
    first = stream.reference(0)
    if first is None:
        warnings.warn(NO_ROI_NOTE + ".", UserWarning, stacklevel=2)
        return None, None, NO_ROI_NOTE
    return first, stream, ROI_NOTE
