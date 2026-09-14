"""Compile the Numba kernels in the background, before the user needs them (H2).

The 2D engine's solver kernels and this package's surface-strain kernel are
JIT-compiled on first use. Numba caches the result on disk, so this is a
once-per-installation cost -- but it is a large one (the 2D project measured
32 s for its first correlation; the 3D packaging notes put the extra first-run
time at 40-60 s), and it lands at the worst possible moment: the user clicks
*Run 3D Analysis* and the progress bar sits at 0% with nothing to explain it.
Killing the process then makes the cost permanent, because the cache is only
written once compilation finishes.

So compilation starts a couple of seconds after the window appears and
overlaps what the user does first (loading images and a calibration, drawing a
region of interest). Numba's compiler holds the GIL, so the interface is less
responsive while this runs; that is a better trade than a dead window after a
button press, and it is not repeated once the cache is warm.

3D path, not 2D's: the 3D layer never calls ``run_aldic`` the way 2D does. It
hands the engine an external reference mesh and a seed through
:func:`al_dic_3d.matching.temporal.temporal_track`, matches the two cameras
with scattered-point IC-GN (:func:`al_dic_3d.matching.primitives.match_points`)
and fits surface strain with :mod:`al_dic_3d.strain3d.kernels`. Compilation is
per type signature and the engine dispatches on problem size, so the warm-up
takes exactly those calls with the production argument types.

Why a daemon ``threading.Thread`` and not a ``QThread`` (the 2D rationale):
compilation cannot be interrupted part-way, so a QThread would leave the
application choosing between aborting on close -- Qt calls ``abort()`` when a
running QThread is destroyed -- and blocking the exit for however long
compilation has left. A daemon thread is reclaimed at interpreter shutdown with
neither problem. The one Qt object here is the signal carrier, created on the
GUI thread, so a slot connected there receives the emission queued.

Thread safety: ``warnings.catch_warnings`` mutates process-global state, so the
warm-up never uses it (a Run started meanwhile installs its own warning
forwarder). Instead the warm-up geometry is chosen to raise no warning at all
(see ``WARMUP_FFT_SEARCH``); the seed ``U0`` skips the engine's FFT search.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

# How long after the window appears to begin, in milliseconds. Long enough for
# the first paint, and for the user to reach for the mouse.
START_DELAY_MS = 2000

# Below this, the cache was already warm and there is nothing worth saying.
REPORT_THRESHOLD_S = 1.0

# Image size of the warm-up pair. Not free to lower: the engine's batch subset
# precompute -- the largest single compilation -- only runs for frames with at
# least 50 nodes (al_dic solver/icgn_batch.py). With winsize 32 and step 16 a
# 192 px ROI gives a 10 x 10 = 100-node mesh; 128 px would give 36 and skip it
# (the 2D project measured exactly that failure: a quick warm-up that left the
# first real run as slow as before). tests/test_kernel_warmup.py pins it.
WARMUP_IMAGE_PX = 192
WARMUP_WINSIZE = 32
WARMUP_STEP = 16
MIN_WARMUP_NODES = 50
# Rigid shift of the deformed image (px); also the seed, so IC-GN converges at once.
WARMUP_SHIFT_PX = 1
# The engine clamps the FFT search half-width to ``min_dim // 4 - winsize`` and
# warns when it does -- even though the seed skips the FFT. Asking for exactly
# that bound keeps the warm-up silent (it never compiles anything in the FFT).
WARMUP_FFT_SEARCH = max(10, WARMUP_IMAGE_PX // 4 - WARMUP_WINSIZE)


def warmup_problem():
    """The warm-up correlation: ``(ref, deformed, para, mesh)``.

    A 192 px speckle pair shifted by one pixel, the production ``DICPara``
    factory with the AL-DIC global step on and two ADMM iterations (one would
    return before the subproblem-1 solver runs and leave its 2-DOF kernel
    uncompiled), and the uniform reference mesh the runner builds.
    """
    import numpy as np

    from al_dic_3d.matching.primitives import make_dicpara
    from al_dic_3d.matching.temporal import build_grid_mesh
    from al_dic_3d.synthetic import speckle

    size = WARMUP_IMAGE_PX
    ref = speckle(size, seed=0, sigma=3.0)
    shift = WARMUP_SHIFT_PX
    deformed = np.ascontiguousarray(np.roll(ref, shift=(shift, shift), axis=(0, 1)))
    para = make_dicpara(
        (size, size),
        (0, size - 1, 0, size - 1),
        winsize=WARMUP_WINSIZE,
        winstepsize=WARMUP_STEP,
        use_global_step=True,
        admm_max_iter=2,
        fft_search=WARMUP_FFT_SEARCH,
    )
    mesh = build_grid_mesh(para, size, size)
    return ref, deformed, para, mesh


def warm_kernels() -> None:
    """Run the warm-up synchronously: compiles the kernels, or loads their cache.

    Temporal tracking (engine: subset precompute, 6-DOF IC-GN, ADMM + 2-DOF
    IC-GN) with the ZNSSD honesty gate on, the frame-1 stereo match, then the
    strain kernel with its production signature.
    """
    import numpy as np

    from al_dic_3d.matching.primitives import match_points
    from al_dic_3d.matching.temporal import temporal_track
    from al_dic_3d.strain3d import kernels

    ref, deformed, para, mesh = warmup_problem()
    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)
    n = coords.shape[0]
    u0 = np.full(2 * n, float(WARMUP_SHIFT_PX))  # interleaved (u, v) per node
    temporal_track(
        [ref, deformed],
        mesh,
        para,
        u0=u0,
        gate_znssd=1.0,
        capture_warnings=False,  # never touch the global warnings state off-thread
    )
    match_points(ref, deformed, coords, np.full((n, 2), float(WARMUP_SHIFT_PX)), para)
    kernels.warmup()


class KernelWarmup(QObject):
    """Runs :func:`warm_kernels` once on a daemon thread to populate the JIT cache."""

    # Emitted with the elapsed seconds when the warm-up took long enough to be
    # worth reporting. Not emitted when the kernels were already cached, nor
    # when the warm-up failed.
    compiled = Signal(float)

    def __init__(self, parent: QObject | None = None, work: Callable[[], None] | None = None):
        super().__init__(parent)
        self._work = warm_kernels if work is None else work
        self._thread: threading.Thread | None = None

    def start(self) -> threading.Thread:
        """Start the warm-up (at most once); returns the daemon thread."""
        if self._thread is None:
            self._thread = threading.Thread(
                target=self._run, name="pyALDIC-3D-kernel-warmup", daemon=True
            )
            self._thread.start()
        return self._thread

    @property
    def started(self) -> bool:
        """True once :meth:`start` has been called."""
        return self._thread is not None

    def is_running(self) -> bool:
        """True while the warm-up thread is still compiling."""
        return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        started = time.perf_counter()
        try:
            self._work()
        except Exception:  # noqa: BLE001 - a warm-up failure must never reach the user
            # The real run compiles the same kernels itself and reports its own
            # errors; the log keeps the traceback for bug reports.
            logger.exception("Kernel warm-up failed; continuing without it")
            return
        elapsed = time.perf_counter() - started
        logger.info("Kernel warm-up finished in %.1f s", elapsed)
        if elapsed >= REPORT_THRESHOLD_S:
            try:
                self.compiled.emit(elapsed)
            except RuntimeError:  # the window (and this carrier) closed meanwhile
                pass
