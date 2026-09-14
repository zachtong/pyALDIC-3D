"""Keep the GUI thread free while browsing results (V-view performance batch).

Two small presenters shared by the main canvas and the strain window:

:class:`OverlayPresenter`
    Shows one dense-field overlay request. A Tier-2 pixmap hit is applied at
    once; a render estimated below ``async_min_grid_points`` runs inline (no
    latency, no flicker, and the synchronous contract small scenes and tests
    rely on); anything larger is computed by the Qt-free
    :meth:`FieldmapRenderer.render_field_rgba` on a private single-thread pool.
    Every request bumps a GENERATION: a queued job that is already stale when
    it reaches the worker is skipped, a finished stale result is dropped, and
    the last good overlay stays on screen until the newest one lands.

:class:`FrameShower`
    Shows a background frame: a prefetched frame is blitted, a small cold
    frame is decoded inline, and a large cold frame is decoded by the
    :class:`~al_dic_3d.gui.widgets.frame_prefetcher.FramePrefetcher` at
    priority while the last good image stays up (it lands through
    ``frame_ready``; a wanted-path check drops frames the user moved past).

``is_idle()`` / ``wait_idle()`` let tests and benchmarks join the work.

An :class:`OverlayRequest` may carry a ``roi_mask_factory`` (a
:class:`LazyValue`) instead of a ready ``roi_mask``: expensive mask derivations
(the right-camera ROI warp, ~0.6 s at 12 Mpx) then run inside the worker job,
once, shared by every job that needs them.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PySide6.QtCore import QCoreApplication, QObject, QThreadPool, Signal

from al_dic_3d.gui.workers import PoolTask

# Renders with more output-grid points than this leave the GUI thread (~20 ms
# inline at this size; a 12 Mpx frame at node step 16 is ~450k points).
ASYNC_MIN_GRID_POINTS = 150_000
# Cold frames larger than this decode on a worker (1.5 Mpx ~ 15 ms inline).
ASYNC_MIN_FRAME_PIXELS = 1_500_000

_STALE = object()  # worker result marker: the request was superseded before it ran
_MASK_PENDING = object()  # pixmap-key stand-in for a mask a factory will provide


class LazyValue:
    """Thread-safe compute-once value (a failure is remembered as ``None``)."""

    def __init__(self, fn: Callable[[], Any]) -> None:
        self._fn = fn
        self._lock = threading.Lock()
        self._done = False
        self._value: Any = None

    def ready(self) -> bool:
        return self._done

    def __call__(self) -> Any:
        with self._lock:
            if not self._done:
                try:
                    self._value = self._fn()
                finally:
                    self._done = True  # never retry-storm a failing derivation
            return self._value


@dataclass(frozen=True)
class OverlayRequest:
    """Everything one dense overlay render needs (``render_field`` kwargs)."""

    frame_idx: int
    field_name: str
    nodes: NDArray[np.float64]
    values: NDArray[np.float64]
    img_shape: tuple[int, int]
    mesh_step: int
    cmap: str
    vmin: float
    vmax: float
    roi_mask: NDArray | None = None
    deformed: bool = False
    ref_uv: tuple[NDArray[np.float64], NDArray[np.float64]] | None = None
    ref_pts: NDArray[np.float64] | None = None
    barrier_mask: NDArray | None = None
    roi_mask_factory: LazyValue | None = None  # resolves ``roi_mask`` off the GUI thread

    def resolved(self) -> OverlayRequest:
        """This request with its mask factory evaluated (runs the factory)."""
        if self.roi_mask_factory is None:
            return self
        return replace(self, roi_mask=self.roi_mask_factory(), roi_mask_factory=None)

    def kwargs(self) -> dict[str, Any]:
        return {
            "frame_idx": self.frame_idx,
            "field_name": self.field_name,
            "nodes": self.nodes,
            "values": self.values,
            "img_shape": self.img_shape,
            "mesh_step": self.mesh_step,
            "cmap": self.cmap,
            "vmin": self.vmin,
            "vmax": self.vmax,
            "roi_mask": self.roi_mask,
            "deformed": self.deformed,
            "ref_uv": self.ref_uv,
            "ref_pts": self.ref_pts,
            "barrier_mask": self.barrier_mask,
        }

    def grid_points_estimate(self) -> int:
        """Upper bound of the output grid size (full image at the grid step)."""
        h, w = self.img_shape
        step = max(1, int(self.mesh_step) // 4)
        return int(h) * int(w) // (step * step)


OverlayCallback = Callable[[tuple], None]  # receives (pixmap | None, xg, yg, out_step)
ErrorCallback = Callable[[str], None]


class OverlayPresenter(QObject):
    """Inline-or-worker dense overlay rendering with generation tags."""

    def __init__(self, viz, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._viz = viz  # VizController3D (Tier-2 API + thread-safe compute)
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)  # renders share caches; latest wins anyway
        self._gen = 0
        self._pending: tuple[int, tuple, OverlayCallback, ErrorCallback | None] | None = None
        # In-flight tasks by generation, held until their delivery lands: they
        # count as outstanding work for is_idle(), and each task's signal
        # emitter is released here on the GUI thread, not by the pool worker.
        self._tasks: dict[int, PoolTask] = {}
        self.async_min_grid_points = ASYNC_MIN_GRID_POINTS

    def request(
        self,
        req: OverlayRequest,
        on_ready: OverlayCallback,
        on_error: ErrorCallback | None = None,
    ) -> bool:
        """Show *req*; returns True when it was applied synchronously."""
        self._gen += 1
        gen = self._gen
        self._pending = None
        viz = self._viz
        mask_flag = req.roi_mask
        if mask_flag is None and req.roi_mask_factory is not None:
            mask_flag = _MASK_PENDING  # a factory will provide the mask
        key = viz.pixmap_key(
            req.frame_idx,
            req.field_name,
            req.cmap,
            req.vmin,
            req.vmax,
            mask_flag,
            req.deformed,
            req.barrier_mask,
            req.mesh_step,
        )
        hit = viz.cached_pixmap(key)
        if hit is not None:
            on_ready(hit)
            return True
        if req.grid_points_estimate() < self.async_min_grid_points:
            try:
                out = viz.render_field(**req.resolved().kwargs())
            except Exception as exc:  # noqa: BLE001 - a render bug must not kill the GUI
                if on_error is None:
                    raise
                on_error(f"{type(exc).__name__}: {exc}")
                return True
            on_ready(out)
            return True
        self._pending = (gen, key, on_ready, on_error)
        task = PoolTask(self._compute, gen, req, tag=gen)
        task.signals.done.connect(self._on_done)
        task.signals.failed.connect(self._on_failed)
        self._tasks[gen] = task
        self._pool.start(task)
        return False

    def cancel(self) -> None:
        """Drop whatever is queued or computing (e.g. the view was cleared)."""
        self._gen += 1
        self._pending = None

    def is_idle(self) -> bool:
        return not self._tasks and self._pending is None

    def wait_idle(self, timeout_ms: int = 30_000) -> bool:
        """Join worker renders and deliver their results (tests / benchmarks)."""
        return pump_until(self.is_idle, timeout_ms, self._pool.waitForDone)

    # -- worker ---------------------------------------------------------------

    def _compute(self, gen: int, req: OverlayRequest):
        if gen != self._gen:  # superseded while queued: skip the work
            return _STALE
        return self._viz.render_field_rgba(**req.resolved().kwargs())

    # -- queued deliveries (GUI thread) ---------------------------------------

    def _take(self, gen: int):
        self._tasks.pop(gen, None)
        pending = self._pending
        if pending is None or pending[0] != gen or gen != self._gen:
            return None
        self._pending = None
        return pending

    def _on_done(self, gen: int, out) -> None:
        pending = self._take(gen)
        if pending is None or out is _STALE:
            return
        _gen, key, on_ready, _on_error = pending
        on_ready(self._viz.adopt_rgba(key, *out))

    def _on_failed(self, gen: int, message: str) -> None:
        pending = self._take(gen)
        if pending is not None and pending[3] is not None:
            pending[3](message)


class FrameShower(QObject):
    """Background frames: blit when prefetched, decode inline or on a worker."""

    shown_async = Signal(str, bool)  # (path, image size changed) after a deferred frame lands
    failed_async = Signal(str, str)  # (path, message) a deferred decode failed

    def __init__(self, canvas, prefetcher, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._canvas = canvas
        self._prefetcher = prefetcher
        self._wanted: str | None = None
        self.async_min_pixels = ASYNC_MIN_FRAME_PIXELS
        prefetcher.frame_ready.connect(self._on_ready)
        prefetcher.frame_failed.connect(self._on_failed)

    def show(self, path) -> bool:
        """Show *path*; True when it is on screen now, False while it decodes.

        Raises whatever the inline decode raises (the caller clears the view).
        """
        key = str(path)
        self._wanted = None
        if self._canvas.shown_path() == key:
            return True
        pixmap = self._prefetcher.get(key)
        if pixmap is not None:
            self._canvas.set_image_pixmap(key, pixmap)
            return True
        if self._can_defer():
            self._wanted = key
            self._prefetcher.request_now(key)
            return False
        image = self._canvas.set_image_file(key)
        if image is not None:
            self._prefetcher.store_image(key, image)
        return True

    def cancel(self) -> None:
        self._wanted = None

    def is_idle(self) -> bool:
        return self._wanted is None

    def _can_defer(self) -> bool:
        if not self._canvas.has_image:
            return False  # nothing to keep on screen: decode now (correctness first)
        current = self._canvas.background_pixmap()
        return current.width() * current.height() >= self.async_min_pixels

    def _on_ready(self, key: str) -> None:
        if key != self._wanted:
            return
        pixmap = self._prefetcher.get(key)
        if pixmap is None:
            return
        self._wanted = None
        resized = pixmap.size() != self._canvas.background_pixmap().size()
        self._canvas.set_image_pixmap(key, pixmap)
        self.shown_async.emit(key, resized)

    def _on_failed(self, key: str, message: str) -> None:
        if key == self._wanted:
            self._wanted = None
            self.failed_async.emit(key, message)


def pump_until(
    done: Callable[[], bool],
    timeout_ms: int,
    wait: Callable[[int], object] | None = None,
) -> bool:
    """Deliver queued GUI-thread work until ``done()`` or the timeout (tests).

    ``wait(ms)`` (e.g. a pool's ``waitForDone``) is called between event
    passes to join worker jobs without spinning.
    """
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        if done():
            return True
        if wait is not None:
            wait(20)
        else:
            time.sleep(0.005)
        QCoreApplication.processEvents()
    return done()
