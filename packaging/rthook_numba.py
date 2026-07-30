"""PyInstaller runtime hook: redirect the numba JIT cache to a writable dir.

Both the 2D engine (``al_dic.solver.*``) and the 3D strain kernel
(``al_dic_3d.strain3d.kernels``) compile ``@njit(cache=True)`` functions. In a
frozen onedir install the package directory lives under
``Program Files``/``LocalAppData\\Programs`` and must be treated as read-only,
so numba's default on-disk cache location (``__pycache__`` next to the source)
is not writable. Runtime hooks execute before the entry script imports
anything, so setting ``NUMBA_CACHE_DIR`` here redirects every kernel's cache
to a per-user writable directory. First launch JIT-compiles (~tens of
seconds for the first DIC run); subsequent launches load from this cache.

Note: numba's cache *also* requires the kernel functions' ``co_filename`` to
point at an existing ``.py`` file. Modules imported from the PYZ archive get a
RELATIVE ``co_filename`` (resolved against the CWD -> "missing"), which makes
numba ignore ``NUMBA_CACHE_DIR`` and fall back to its frozen-app user-wide
cache (``%LOCALAPPDATA%\\numba\\Cache``) with a CWD-dependent subpath. The
spec therefore collects ``al_dic`` and ``al_dic_3d`` with
``module_collection_mode='py'`` (source on disk, outside the PYZ) so the
redirect below actually takes effect.
"""

import os
import tempfile

if "NUMBA_CACHE_DIR" not in os.environ:
    _base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    _cache = os.path.join(_base, "pyALDIC-3D", "numba_cache")
    try:
        os.makedirs(_cache, exist_ok=True)
        os.environ["NUMBA_CACHE_DIR"] = _cache
    except OSError:
        # Fall back to numba's default behaviour (caching disabled with a
        # NumbaWarning); the app still works, just JIT-compiles every launch.
        pass
