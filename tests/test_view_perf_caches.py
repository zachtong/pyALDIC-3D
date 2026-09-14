"""Viewer performance batch V-view: byte-bounded caches, rasterizer, run step.

Qt-free units behind the 12 Mpx viewing fixes:

* :class:`SizedLRUCache` bounds render caches by BYTES as well as entries;
* :func:`rasterize_mesh` locates a regular output grid in a (possibly warped)
  triangle mesh — the reference triangulation reused at deformed positions;
* :class:`GridSpec` reproduces ``scatter_to_grid``'s "auto" grid exactly while
  storing only 1D axes;
* :func:`run_node_step` reads the RUN's node step (never the live draft).
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from al_dic_3d.viz3d.sized_cache import SizedLRUCache, nbytes_of

# ---------------------------------------------------------------------------
# SizedLRUCache
# ---------------------------------------------------------------------------


def test_nbytes_of_counts_arrays_in_containers():
    a = np.zeros(10, dtype=np.float64)  # 80 B
    b = np.zeros((2, 5), dtype=np.int32)  # 40 B
    assert nbytes_of(a) == 80
    assert nbytes_of((a, b, None, 3)) == 120
    assert nbytes_of([a, (b,)]) == 120
    assert nbytes_of({"x": a}) == 80
    assert nbytes_of(SimpleNamespace(nbytes=7)) == 7
    assert nbytes_of(None) == 0


def test_sized_cache_evicts_by_bytes_lru_order():
    c = SizedLRUCache(maxsize=100, max_bytes=250)
    c["a"] = np.zeros(10)  # 80 B
    c["b"] = np.zeros(10)
    c["c"] = np.zeros(10)  # 240 B total: fits
    assert list(c) == ["a", "b", "c"] and c.total_bytes == 240
    assert c["a"] is not None  # refresh "a"
    c["d"] = np.zeros(10)  # 320 B > 250: evict LRU ("b")
    assert list(c) == ["c", "a", "d"]
    assert c.total_bytes == 240


def test_sized_cache_entry_cap_still_applies():
    c = SizedLRUCache(maxsize=2, max_bytes=10**9)
    c["a"], c["b"], c["c"] = np.zeros(1), np.zeros(1), np.zeros(1)
    assert list(c) == ["b", "c"] and c.total_bytes == 16


def test_sized_cache_replace_and_delete_keep_accounting():
    c = SizedLRUCache(maxsize=10, max_bytes=1000)
    c["a"] = np.zeros(10)
    c["a"] = np.zeros(20)  # replace: old size released
    assert c.total_bytes == 160
    del c["a"]
    assert c.total_bytes == 0 and len(c) == 0
    c["x"] = np.zeros(5)
    assert c.pop("x").shape == (5,) and c.total_bytes == 0
    assert c.pop("missing", None) is None
    c["y"] = np.zeros(5)
    c.clear()
    assert c.total_bytes == 0 and len(c) == 0


def test_sized_cache_never_stores_an_entry_larger_than_budget():
    c = SizedLRUCache(maxsize=10, max_bytes=100)
    c["small"] = np.zeros(5)  # 40 B
    c["huge"] = np.zeros(100)  # 800 B > budget: recompute-on-demand, not cached
    assert "huge" not in c and "small" in c
    assert c.total_bytes == 40


def test_sized_cache_custom_sizer():
    c = SizedLRUCache(maxsize=10, max_bytes=10, sizer=lambda v: v)
    c["a"], c["b"] = 4, 4
    c["c"] = 4  # 12 > 10: evicts "a"
    assert list(c) == ["b", "c"]


# ---------------------------------------------------------------------------
# content digests for cache keys
# ---------------------------------------------------------------------------


def test_array_digest_tracks_content_shape_and_dtype():
    from al_dic_3d.viz3d.sized_cache import array_digest

    a = np.arange(12, dtype=np.float64).reshape(6, 2)
    assert array_digest(a) == array_digest(a.copy())
    b = a.copy()
    b[3, 1] += 1e-9
    assert array_digest(b) != array_digest(a)
    assert array_digest(a.reshape(3, 4)) != array_digest(a)
    assert array_digest(a.astype(np.float32)) != array_digest(a)
    assert array_digest(a[::2]) == array_digest(np.ascontiguousarray(a[::2]))


def test_mask_digest_uses_the_thresholded_content():
    from al_dic_3d.viz3d.sized_cache import mask_digest

    m = np.zeros((40, 50), dtype=np.uint8)
    m[5:20, 5:30] = 1
    as_bool = m > 0
    # ROI semantics (> 0) and barrier semantics (>= 0.5) agree on 0/1 masks,
    # whatever the dtype, so a bool mask and its float image share one key
    assert mask_digest(m, barrier=False) == mask_digest(as_bool, barrier=False)
    assert mask_digest(as_bool.astype(np.float64), barrier=True) == mask_digest(
        as_bool, barrier=True
    )
    edited = as_bool.copy()
    edited[30, 40] = True
    assert mask_digest(edited) != mask_digest(as_bool)
    assert mask_digest(None) is None


def test_digest_memo_reuses_by_identity_only_while_alive():
    from al_dic_3d.viz3d.sized_cache import DigestMemo

    calls = []

    def fn(arr):
        calls.append(1)
        return bytes([int(arr.sum()) % 256])

    memo = DigestMemo(fn, capacity=2)
    a = np.ones(4)
    assert memo(a) == memo(a) and len(calls) == 1  # identity hit
    b = np.ones(4)  # equal content, new object: computed again
    memo(b)
    assert len(calls) == 2
    c = np.ones(4)
    memo(c)  # capacity 2: "a" evicted
    memo(a)
    assert len(calls) == 4


# ---------------------------------------------------------------------------
# run node step (H3): the RUN's step, never the live draft
# ---------------------------------------------------------------------------


def _result(meta, ref):
    return SimpleNamespace(meta=meta, ref_coords=ref)


def test_run_node_step_prefers_run_params():
    from al_dic_3d.viz3d.runstep import run_node_step

    ref = np.column_stack([np.arange(10) * 16.0, np.zeros(10)])
    assert run_node_step(_result({"run_params": {"winstepsize": 8}}, ref)) == 8


def test_run_node_step_falls_back_to_reference_spacing_for_old_sessions():
    from al_dic_3d.viz3d.runstep import run_node_step

    xs, ys = np.meshgrid(100 + 12.0 * np.arange(8), 50 + 12.0 * np.arange(6))
    ref = np.column_stack([xs.ravel(), ys.ravel()])
    ref[3] = np.nan  # invalid rows are ignored
    assert run_node_step(_result({}, ref)) == 12
    assert run_node_step(_result({"run_params": {"winstepsize": 0}}, ref)) == 12
    assert run_node_step(_result(None, ref)) == 12


def test_run_node_step_default_when_nothing_is_known():
    from al_dic_3d.viz3d.runstep import run_node_step

    assert run_node_step(_result({}, np.full((1, 2), np.nan)), default=16) == 16
    assert run_node_step(None, default=24) == 24
