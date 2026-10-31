"""Grid coverage for incremental reference frames whose masks move.

In an incremental run each reference frame trims a camera's external mesh to
that frame's mask; since al-dic 1.0.4 the trim starts from the untrimmed mesh
every time, so cells that an earlier, narrower mask removed come back. The mesh
is still a fixed pixel lattice, though: material that a later reference mask
places outside it has no cells to be tracked in. A notched specimen pulled
~400 px lost most of its points that way in an incremental run with per-frame
masks.

:func:`cover_roi` extends a grid ROI to cover the union of the reference-frame
masks by WHOLE grid steps. The engine centres its lattice in the ROI with an
offset of ``(span mod step) // 2``, which whole-step moves leave unchanged, so
the frame-1 nodes stay exactly where they were and only rings of nodes are
added around them (outside the frame-1 mask they are invalid from the start).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

import numpy as np
from numpy.typing import NDArray

Box = tuple[int, int, int, int]  # (xmin, xmax, ymin, ymax), inclusive pixels


def masks_bbox(masks: Sequence, frames: Iterable[int]) -> Box | None:
    """Bounding box of the union of ``masks[k] > 0`` over ``frames``; None if empty."""
    box = None
    for k in sorted(set(frames)):
        m = np.asarray(masks[k]) > 0
        rows = np.flatnonzero(m.any(axis=1))
        if rows.size == 0:
            continue
        cols = np.flatnonzero(m.any(axis=0))
        b = (int(cols[0]), int(cols[-1]), int(rows[0]), int(rows[-1]))
        box = (
            b
            if box is None
            else (min(box[0], b[0]), max(box[1], b[1]), min(box[2], b[2]), max(box[3], b[3]))
        )
    return box


def _extend(lo: int, hi: int, cover_lo: int, cover_hi: int, step: int, floor: int, ceil: int):
    """``(lo, hi)`` moved outwards by whole steps to reach the cover, within the bounds."""
    down = max(0, math.ceil((lo - cover_lo) / step))
    down = min(down, max(0, (lo - floor) // step))
    up = max(0, math.ceil((cover_hi - hi) / step))
    up = min(up, max(0, (ceil - hi) // step))
    return lo - down * step, hi + up * step


def cover_roi(
    roi: Box, cover: Box | None, *, step: int, winsize: int, img_shape: tuple[int, int]
) -> Box:
    """``roi`` extended by whole grid steps to cover ``cover`` (never shrunk).

    The bounds are first clamped exactly as the engine clamps them (a subset
    must fit in the image), so the extension keeps the grid phase even when it
    stops short at the image border.
    """
    if cover is None:
        return roi
    h, w = int(img_shape[0]), int(img_shape[1])
    half = int(winsize) // 2
    x_floor, x_ceil, y_floor, y_ceil = half, w - 1 - half, half, h - 1 - half
    x0, x1 = max(int(roi[0]), x_floor), min(int(roi[1]), x_ceil)
    y0, y1 = max(int(roi[2]), y_floor), min(int(roi[3]), y_ceil)
    nx0, nx1 = _extend(x0, x1, int(cover[0]), int(cover[1]), int(step), x_floor, x_ceil)
    ny0, ny1 = _extend(y0, y1, int(cover[2]), int(cover[3]), int(step), y_floor, y_ceil)
    if (nx0, nx1, ny0, ny1) == (x0, x1, y0, y1):
        return roi
    return (nx0, nx1, ny0, ny1)


def map_box_affine(
    box: Box, src: NDArray[np.float64], dst: NDArray[np.float64], min_links: int = 6
) -> Box | None:
    """``box`` carried through the least-squares affine ``src -> dst`` (frame-1 links).

    Used for a right camera whose masks are derived from the left ones: its
    reference masks are the left masks carried through the same links, so the
    left union box mapped this way bounds them. None with too few links.
    """
    src = np.asarray(src, dtype=np.float64)
    dst = np.asarray(dst, dtype=np.float64)
    ok = np.isfinite(src).all(axis=1) & np.isfinite(dst).all(axis=1)
    if int(ok.sum()) < min_links:
        return None
    design = np.column_stack([src[ok], np.ones(int(ok.sum()))])
    coef, *_ = np.linalg.lstsq(design, dst[ok], rcond=None)  # (3, 2)
    corners = np.array(
        [[box[0], box[2], 1.0], [box[1], box[2], 1.0], [box[0], box[3], 1.0], [box[1], box[3], 1.0]]
    )
    mapped = corners @ coef
    return (
        int(np.floor(mapped[:, 0].min())),
        int(np.ceil(mapped[:, 0].max())),
        int(np.floor(mapped[:, 1].min())),
        int(np.ceil(mapped[:, 1].max())),
    )


def reference_frames(reference_mode: str, n_frames: int, schedule=None) -> frozenset[int]:
    """The frames a camera is correlated FROM: ``schedule``'s, or the mode's default."""
    from al_dic.core.data_structures import FrameSchedule  # DEPENDS_ON_2D.md

    if schedule is None:
        schedule = FrameSchedule.from_mode(reference_mode, n_frames)
    return frozenset(int(k) for k in schedule.ref_frame_set)


def moving_union(masks: Sequence, refs: Iterable[int]) -> Box | None:
    """Union box of the reference masks, or None when they do not move.

    "Moving" means the union reaches past the first reference frame's own box.
    Static masks (the frame-1 outline repeated, or one mask imported for every
    frame) leave the grid exactly as it was.
    """
    refs = sorted(set(refs))
    union = masks_bbox(masks, refs)
    return None if union is None or union == masks_bbox(masks, refs[:1]) else union


def reference_cover_roi(
    roi: Box,
    masks: Sequence | None,
    refs: Iterable[int],
    *,
    step: int,
    winsize: int,
    img_shape: tuple[int, int],
) -> Box:
    """``roi`` covering the union of ``masks`` on the reference frames ``refs``.

    A single reference frame (accumulative runs) or no masks leaves ``roi`` as
    it is without decoding any mask; so do masks that do not move.
    """
    refs = set(refs)
    if masks is None or len(refs) <= 1:
        return roi
    return cover_roi(
        roi, moving_union(masks, refs), step=step, winsize=winsize, img_shape=img_shape
    )


def right_cover_roi(
    roi: Box,
    *,
    right_masks: Sequence | None,
    left_masks: Sequence | None,
    left_pts: NDArray[np.float64],
    right_pts: NDArray[np.float64],
    refs: Iterable[int],
    step: int,
    winsize: int,
    img_shape: tuple[int, int],
    rim_px: int = 0,
) -> Box:
    """The right camera's grid ROI covering its reference masks.

    Masks given for the right camera count as they are. Without them the right
    masks are the left ones carried through the frame-1 links (widened by
    ``rim_px``), so the left union box is mapped through the same links.
    """
    refs = set(refs)
    if len(refs) <= 1:
        return roi
    if right_masks is not None:
        cover = moving_union(right_masks, refs)
    elif left_masks is not None:
        left_box = moving_union(left_masks, refs)
        cover = None if left_box is None else map_box_affine(left_box, left_pts, right_pts)
        if cover is not None and rim_px:
            cover = (cover[0] - rim_px, cover[1] + rim_px, cover[2] - rim_px, cover[3] + rim_px)
    else:
        return roi
    return cover_roi(roi, cover, step=step, winsize=winsize, img_shape=img_shape)
