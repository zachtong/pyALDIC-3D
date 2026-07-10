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

# Frames resident under the lazy providers: per camera a raw decode LRU (4) +
# the engine adapter's normalized LRU (4), x2 cameras, plus the engine's
# reference bundles (~4 frame-sized arrays per cached ref, cache size 2).
LAZY_RESIDENT_FRAMES = 24

# float64 values stored per (frame, point) across the result payloads: per-cam
# u_accum/valid (2 x ~3), correspondence xL/xR/quality/source (~6), points /
# displacement / reproj (~7), strain + export staging headroom.
RESULT_DOUBLES_PER_POINT_FRAME = 24

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
) -> int:
    """Projected peak process memory (bytes) for one pipeline run.

    ``lazy=True`` models the path-backed providers (P1.2): resident frames are
    LRU-bounded, independent of ``n_frames``. ``lazy=False`` models the legacy
    eager path — raw stacks for every camera plus the engine's normalized copy
    and a worst-case per-frame mask stack — and is kept for sizing comparisons.
    ``n_pts`` (mesh nodes) sizes the per-(frame, point) result arrays.
    ``parallel`` (P3.6) doubles the engine transient: with concurrent camera
    tracking both engine working sets are live at once.
    """
    bytes_per_frame = int(img_h) * int(img_w) * 8
    transient = int(ENGINE_TRANSIENT_BYTES_PER_MPX * (img_h * img_w / 1e6))
    if parallel:
        transient *= 2
    if lazy:
        resident = LAZY_RESIDENT_FRAMES * bytes_per_frame
    else:
        resident = n_frames * bytes_per_frame * (n_cameras + 2)
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
    fraction: float = DEFAULT_RAM_FRACTION,
) -> None:
    """Raise ``ValueError`` when the projected peak exceeds available RAM.

    The threshold is ``fraction`` (default 70%) of *currently available*
    physical memory. Silently returns when availability cannot be probed.
    English by contract (compute-layer error strings are not translated).
    """
    available = available_ram_bytes()
    if available is None:
        return
    projected = estimate_peak_bytes(
        n_frames, img_h, img_w, n_cameras, lazy=lazy, n_pts=n_pts, parallel=parallel
    )
    budget = fraction * available
    if projected <= budget:
        return
    gib = 1024**3
    raise ValueError(
        f"Projected peak memory {projected / gib:.1f} GB exceeds "
        f"{fraction:.0%} of available RAM ({available / gib:.1f} GB available) "
        f"for {n_frames} frames x {img_w}x{img_h} px x {n_cameras} cameras. "
        f"Reduce the number of frames, shrink the ROI / downsample the images, "
        f"close other applications, or set ignore_memory_check = true under "
        f"[advanced] in the config to run anyway."
    )
