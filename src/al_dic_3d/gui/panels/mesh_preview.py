"""Debounced, background-built mesh preview (P2.3).

``build_reference_mesh`` (including quadtree refinement) takes seconds on
large masks; running it on the debounce timeout froze the GUI thread. The
:class:`MeshPreviewBuilder` keeps the 300 ms debounce but runs the build on a
single-thread ``QThreadPool`` and coalesces bursts with a generation counter:
when params change while a build is in flight, the stale result is dropped on
arrival and a fresh build starts with the latest snapshot.

Inputs are SNAPSHOT on the GUI thread (:func:`snapshot_preview_params`) —
the refinement brush buffer mutates in place during strokes, so the worker
must never read live draft arrays. ``build_preview_mesh`` is the worker-side
function and calls the REAL pipeline grid code, so preview == pipeline.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import numpy as np
from PySide6.QtCore import QCoreApplication, QObject, QThreadPool, QTimer, Signal

from al_dic_3d.gui.workers import PoolTask

PREVIEW_DEBOUNCE_MS = 300


def snapshot_preview_params(draft, img_h: int, img_w: int) -> dict[str, Any]:
    """GUI-thread capture of everything the worker-side build needs.

    Mask arrays are converted to fresh float64 copies HERE so the worker never
    touches draft state that the GUI may mutate mid-build.
    """
    roi_mask = draft.roi_mask_array
    brush = draft.refinement_mask_array
    return dict(
        img_h=int(img_h),
        img_w=int(img_w),
        roi=tuple(int(v) for v in draft.roi),
        winsize=int(draft.winsize),
        winstepsize=int(draft.winstepsize),
        winsize_min=int(draft.winsize_min),
        refine_inner=bool(draft.refine_inner),
        refine_outer=bool(draft.refine_outer),
        refinement_level=int(draft.refinement_level),
        mask=(np.asarray(roi_mask) > 0).astype(np.float64) if roi_mask is not None else None,
        refinement_brush=(np.asarray(brush) > 0).astype(np.float64) if brush is not None else None,
    )


def node_valid_mask(coords: np.ndarray, roi_mask) -> np.ndarray:
    """Per-node boolean: True when the node lies inside the ROI mask."""
    n = coords.shape[0]
    if roi_mask is None:
        return np.ones(n, dtype=bool)
    m = np.asarray(roi_mask) > 0
    h, w = m.shape
    ix = np.clip(np.round(coords[:, 0]).astype(int), 0, w - 1)
    iy = np.clip(np.round(coords[:, 1]).astype(int), 0, h - 1)
    return m[iy, ix]


def build_preview_mesh(params: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Worker-side: the real pipeline grid code -> ``(coords, elements, valid)``."""
    from al_dic_3d.runner import build_reference_mesh

    mesh = build_reference_mesh(
        params["img_h"],
        params["img_w"],
        params["roi"],
        winsize=params["winsize"],
        winstepsize=params["winstepsize"],
        winsize_min=params["winsize_min"],
        refine_inner=params["refine_inner"],
        refine_outer=params["refine_outer"],
        refinement_level=params["refinement_level"],
        refinement_brush=params["refinement_brush"],
        mask=params["mask"],
    )
    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)
    elements = np.asarray(mesh.elements_fem, dtype=np.int64)
    return coords, elements, node_valid_mask(coords, params["mask"])


class MeshPreviewBuilder(QObject):
    """Debounce + worker pool + generation-counter coalescing for the preview.

    The owner supplies ``snapshot`` (returns the param dict, or None when the
    preview is not applicable) and connects :attr:`built` / :attr:`hidden`.
    ``built`` receivers must re-check applicability — the view state may have
    changed while the build was in flight.
    """

    built = Signal(object, object, object)  # coords, elements, valid
    hidden = Signal()  # not applicable / build failed -> hide the overlay

    def __init__(
        self, snapshot: Callable[[], dict[str, Any] | None], parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._snapshot = snapshot
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._generation = 0
        self._busy = False
        self._dirty = False
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(PREVIEW_DEBOUNCE_MS)
        self._timer.timeout.connect(self.kick_now)

    def schedule(self) -> None:
        """Debounced rebuild (params/ROI edits arrive in bursts)."""
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def kick_now(self) -> None:
        """Start a build with the CURRENT params (debounce timeout; tests)."""
        self._generation += 1
        params = self._snapshot()
        if params is None:
            self.hidden.emit()
            return
        if self._busy:
            self._dirty = True  # coalesce: rebuild when the in-flight build lands
            return
        self._busy = True
        task = PoolTask(build_preview_mesh, params, tag=self._generation)
        task.signals.done.connect(self._on_done)
        task.signals.failed.connect(self._on_failed)
        self._pool.start(task)

    def wait_idle(self, timeout_ms: int = 30_000) -> bool:
        """Join in-flight builds AND deliver their queued results (tests)."""
        deadline = time.monotonic() + timeout_ms / 1000.0
        while time.monotonic() < deadline:
            self._pool.waitForDone(50)
            QCoreApplication.processEvents()
            if (
                not self._busy
                and self._pool.activeThreadCount() == 0
                and not self._timer.isActive()
            ):
                return True
        return False

    # -- queued deliveries (GUI thread) ---------------------------------------

    def _handle_result(self, tag: object, deliver: Callable[[], None]) -> None:
        self._busy = False
        if tag != self._generation or self._dirty:
            self._dirty = False
            self.kick_now()  # params changed mid-build: rebuild with fresh ones
            return
        deliver()

    def _on_done(self, tag: object, out: object) -> None:
        self._handle_result(tag, lambda: self.built.emit(*out))

    def _on_failed(self, tag: object, _message: str) -> None:
        # The preview is best-effort — a failed build hides the overlay, never
        # blocks the GUI (same contract as the old synchronous try/except).
        self._handle_result(tag, self.hidden.emit)
