r"""Numba availability and JIT-cache probing for this package's kernels.

Ported from al_dic 0.8.0's ``_numba_compat`` (the 2D fix for locked-down
Windows profiles), because the pinned range still admits al_dic 0.7.2, which
does not ship it.

``@njit(cache=True)`` builds numba's ``FunctionCache`` at *decoration* time —
while the module is being imported — and raises ``RuntimeError`` (not
``ImportError``) when no cache locator applies. Inside a frozen build the source
files do not exist, so only the user-wide locator (``%LOCALAPPDATA%\numba``)
remains; on a redirected or policy-locked profile it declines too, and the
import of ``al_dic_3d.strain3d`` would fail before any window exists. Probing
once here lets the kernels fall back to ``cache=False``: a slower first run in
exchange for still having an application.
"""

from __future__ import annotations

try:
    from numba import njit, prange

    HAS_NUMBA = True
except ImportError:  # pragma: no cover - numba is a core dependency
    HAS_NUMBA = False

    def njit(*args, **kwargs):
        """Pass-through stand-in so kernel modules still import."""

        def decorator(func):
            return func

        if args and callable(args[0]):
            return args[0]
        return decorator

    def prange(*args):
        return range(*args)


def probe_jit_cache() -> bool:
    """Return True when ``@njit(cache=True)`` can be applied safely.

    Decorating is the whole test: the cache locator chain is walked during
    decoration, so a decorator that returns without raising proves the same chain
    resolves for the real kernels. Compilation stays lazy (no LLVM work here).
    """
    if not HAS_NUMBA:
        return False
    try:

        @njit(cache=True)
        def _probe(x):  # pragma: no cover - never called
            return x

    except Exception:  # noqa: BLE001 - any locator failure means "no cache"
        return False
    return True


#: Value to pass as ``cache=`` on every kernel decorator in this package.
JIT_CACHE = probe_jit_cache()

__all__ = ["HAS_NUMBA", "JIT_CACHE", "njit", "prange", "probe_jit_cache"]
