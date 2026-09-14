"""The strain kernels must still import when numba's JIT cache is unavailable.

``@njit(cache=True)`` raises ``RuntimeError`` at decoration time when no cache
locator applies (frozen build on a policy-locked profile). ``probe_jit_cache``
must report that instead of letting the import of ``al_dic_3d.strain3d`` fail.
"""

from __future__ import annotations

import al_dic_3d._numba_compat as compat


def test_probe_reports_true_on_a_normal_machine():
    assert compat.probe_jit_cache() is True
    assert compat.JIT_CACHE is True


def test_probe_reports_false_when_cache_locators_decline(monkeypatch):
    real_njit = compat.njit

    def njit_without_cache(*args, **kwargs):
        if kwargs.get("cache"):
            raise RuntimeError("cannot cache function: no locator available")
        return real_njit(*args, **kwargs)

    monkeypatch.setattr(compat, "njit", njit_without_cache)
    assert compat.probe_jit_cache() is False


def test_strain_kernels_use_the_probed_cache_flag():
    from al_dic_3d.strain3d import kernels

    assert kernels.JIT_CACHE is compat.JIT_CACHE
    assert kernels.HAS_NUMBA is compat.HAS_NUMBA
