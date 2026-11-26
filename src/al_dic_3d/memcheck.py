"""RAM pre-check for pipeline runs (Qt-free) — perf batch P1.4, fail fast.

Before the runner touches a single frame it projects the run's peak memory from
the sequence geometry and compares it against the machine's available physical
RAM. A run that would have crawled into the pagefile (or died OOM an hour in)
instead fails in milliseconds with an actionable sizing message. Set
``ignore_memory_check = true`` (``[advanced]`` or ``[matching]`` in the TOML)
to override.

The constants come from the 2026-07 stress audit of the lazy pipeline: the 2D
engine's per-run transient (gradients, IC-GN subset cubes, FFT scratch, ADMM
buffers) scales with image area at roughly 150 MB per megapixel, while the
resident frame count is bounded by the decode/normalize LRUs plus the engine's
reference-bundle cache instead of the sequence length.
"""

from __future__ import annotations

import sys

# Engine per-run transient, bytes per megapixel (stress-audit fit, see module
# docstring). Covers gradients + subset cubes + FFT scratch for ONE track; by
# default the two per-camera tracks run sequentially so the transient does not
# double — parallel camera tracking (P3.6) doubles it via ``parallel=True``.
ENGINE_TRANSIENT_BYTES_PER_MPX = 150 * 1024**2

# Frames resident under the lazy providers, in float64-frame equivalents: per
# camera the engine adapter's normalized LRU (4), x2 cameras, plus the engine's
# reference bundles (~4 frame-sized arrays per cached ref, cache size 2) = 16.
# The raw decode LRUs (4 per camera) hold the NATIVE dtype since fix batch V:
# 16-bit frames cost a quarter of a float64 frame each, so 8 x 1/4 = 2 more.
LAZY_RESIDENT_FRAMES = 18

# Frame-sized float64 working arrays outside the engine and the LRUs: the
# frame-1 stereo match (float32 template copies, image gradients), the honesty
# gate (the deformed frame's spline coefficients, the reference, the mask), the
# right-camera mask/barrier warp and the per-camera mask LRUs. Fix batch V fit:
# measured peaks at 5 / 12 / 24 Mpx (200 / 40 / 8 frames) exceeded the older
# projection by 24 / 23 / 23 %, i.e. by 12 to 13 frame-sized arrays at every
# size, so the term scales with the image, not with the frame count. After the
# native-dtype frame cache, with the left gate overlapping the right engine,
# 12 Mpx x 6 frames peaked at 4.72 GiB above the process baseline; 16 keeps
# the projection (4.83 GiB) above that with a little headroom.
SETUP_AND_GATE_FRAMES = 16

# float64 values stored per (frame, point) across the result payloads: per-cam
# u_accum/valid (2 x ~3), correspondence xL/xR/quality/source (~6), points /
# displacement / reproj (~7), strain + export staging headroom.
RESULT_DOUBLES_PER_POINT_FRAME = 24

# Engine + gate working set per mesh node, independent of the frame count
# (2026-11-26 audit of the measured peaks, see estimate_peak_bytes). Dense
# meshes were projected 1.8-1.9x too low without it: 12 Mpx with winsize 24 /
# step 8 (108,300 nodes, 20 frames) peaked at 9.4 GB against 5.2 projected,
# 5 Mpx at 45,695 nodes at 4.1 against 2.2. The extra memory grows with the
# node count at 41-45 KiB per node at both image sizes (real 5 Mpx data,
# 37,230 nodes: 44 KiB); 46 KiB keeps every measured run below its projection.
ENGINE_BYTES_PER_NODE = 46 * 1024

# The incremental mode's extra working set: the reference frame changes, so
# the engine keeps a mesh, a pair solution and the cumulative-transform
# bookkeeping per reference on top of the accumulative set. It does not grow
# with the frame count (5 Mpx, 11,532 nodes: 4.14 / 4.16 / 4.19 GB peak at
# 5 / 10 / 20 frames, against 2.46 accumulative) but with the image and the
# mesh: +1.7 GB there, +3.3 GB on real 5 Mpx data at 39,260 nodes, +9.5 GB at
# 12 Mpx and 108,300 nodes (18.9 GB peak, 5.0 projected before).
INCREMENTAL_BYTES_PER_MPX = 240 * 1024**2
INCREMENTAL_BYTES_PER_NODE = 66 * 1024

DEFAULT_RAM_FRACTION = 0.70


def available_ram_bytes() -> int | None:
    """Available physical RAM in bytes, or ``None`` when it cannot be queried.

    Windows: ``GlobalMemoryStatusEx`` via ctypes (no dependency). Elsewhere:
    ``psutil`` when importable. ``None`` disables the pre-check (never block a
    run because the probe itself is unsupported).
    """
    if sys.platform == "win32":
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_uint64),
                ("ullAvailPhys", ctypes.c_uint64),
                ("ullTotalPageFile", ctypes.c_uint64),
                ("ullAvailPageFile", ctypes.c_uint64),
                ("ullTotalVirtual", ctypes.c_uint64),
                ("ullAvailVirtual", ctypes.c_uint64),
                ("ullAvailExtendedVirtual", ctypes.c_uint64),
            ]

        try:
            fn = ctypes.windll.kernel32.GlobalMemoryStatusEx
            fn.argtypes = [ctypes.POINTER(MEMORYSTATUSEX)]
            fn.restype = ctypes.c_int
            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if not fn(ctypes.byref(status)):
                return None
            return int(status.ullAvailPhys)
        except (AttributeError, OSError):
            return None
    try:
        import psutil
    except ImportError:
        return None
    return int(psutil.virtual_memory().available)


def estimate_peak_bytes(
    n_frames: int,
    img_h: int,
    img_w: int,
    n_cameras: int = 2,
    *,
    lazy: bool = True,
    n_pts: int = 0,
    parallel: bool = False,
    incremental: bool = False,
) -> int:
    """Projected peak process memory (bytes) for one pipeline run.

    ``lazy=True`` models the path-backed providers (P1.2): resident frames are
    LRU-bounded, independent of ``n_frames``. ``lazy=False`` models the legacy
    eager path — raw stacks for every camera plus the engine's normalized copy
    and a worst-case per-frame mask stack — and is kept for sizing comparisons.
    ``n_pts`` (mesh nodes) sizes the per-(frame, point) result arrays.
    ``parallel`` (P3.6) doubles the engine transient: with concurrent camera
    tracking both engine working sets are live at once. ``SETUP_AND_GATE_FRAMES``
    covers the frame-sized arrays outside the engine (see its comment).
    ``ENGINE_BYTES_PER_NODE`` sizes the per-node working set (doubled by
    ``parallel``), and ``incremental`` adds the incremental mode's per-run
    extra (:data:`INCREMENTAL_BYTES_PER_MPX`, :data:`INCREMENTAL_BYTES_PER_NODE`).
    """
    bytes_per_frame = int(img_h) * int(img_w) * 8
    mpx = img_h * img_w / 1e6
    nodes = max(int(n_pts), 0)
    transient = int(ENGINE_TRANSIENT_BYTES_PER_MPX * mpx) + nodes * ENGINE_BYTES_PER_NODE
    if incremental:
        transient += int(INCREMENTAL_BYTES_PER_MPX * mpx) + nodes * INCREMENTAL_BYTES_PER_NODE
    if parallel:
        transient *= 2
    if lazy:
        resident = LAZY_RESIDENT_FRAMES * bytes_per_frame
    else:
        resident = n_frames * bytes_per_frame * (n_cameras + 2)
    resident += SETUP_AND_GATE_FRAMES * bytes_per_frame
    results = n_frames * max(int(n_pts), 1) * 8 * RESULT_DOUBLES_PER_POINT_FRAME
    return transient + resident + results


def check_run_memory(
    n_frames: int,
    img_h: int,
    img_w: int,
    n_cameras: int = 2,
    *,
    lazy: bool = True,
    n_pts: int = 0,
    parallel: bool = False,
    incremental: bool = False,
    fraction: float = DEFAULT_RAM_FRACTION,
) -> None:
    """Raise :class:`MemoryBudgetError` (a ``ValueError``) when the peak exceeds RAM.

    The threshold is ``fraction`` (default 70%) of *currently available*
    physical memory. Silently returns when availability cannot be probed.
    English by contract (compute-layer error strings are not translated).
    """
    available = available_ram_bytes()
    if available is None:
        return
    projected = estimate_peak_bytes(
        n_frames,
        img_h,
        img_w,
        n_cameras,
        lazy=lazy,
        n_pts=n_pts,
        parallel=parallel,
        incremental=incremental,
    )
    budget = fraction * available
    if projected <= budget:
        return
    raise MemoryBudgetError(projected, available, fraction, n_frames, img_w, img_h, n_cameras)


class MemoryBudgetError(ValueError):
    """A run whose projected peak memory exceeds the budget (a ``ValueError``).

    ``str()`` is the CLI / config wording, which names the
    ``ignore_memory_check`` override; the GUI has no such switch, so it words
    its own message from the numbers carried here (fewer frames, a coarser
    step, a smaller ROI).
    """

    def __init__(
        self,
        projected: float,
        available: float,
        fraction: float,
        n_frames: int,
        img_w: int,
        img_h: int,
        n_cameras: int,
    ) -> None:
        gib = 1024**3
        super().__init__(
            f"Projected peak memory {projected / gib:.1f} GB exceeds "
            f"{fraction:.0%} of available RAM ({available / gib:.1f} GB available) "
            f"for {n_frames} frames x {img_w}x{img_h} px x {n_cameras} cameras. "
            f"Reduce the number of frames, use a coarser winstepsize, shrink the ROI / "
            f"downsample the images, close other applications, or set "
            f"ignore_memory_check = true under [advanced] in the config to run anyway."
        )
        self.projected_gb = projected / gib
        self.available_gb = available / gib
        self.fraction = float(fraction)
        self.n_frames = int(n_frames)
