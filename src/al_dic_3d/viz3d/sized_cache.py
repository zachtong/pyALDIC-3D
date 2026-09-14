"""Byte-bounded LRU cache for the render/display caches (Qt-free).

:class:`~al_dic_3d.viz3d.lru.LRUCache` caps the NUMBER of entries, but a dense
render entry's size depends on the image, the ROI and the node step: the same
32-entry cap measured 14 MB per entry at 36k nodes and ~290 MB per entry at a
node step <= 7 on a 12 Mpx image (~9 GB per renderer). :class:`SizedLRUCache`
keeps the entry cap (existing contracts) and adds a BYTE budget: inserting
evicts least-recently-used entries until the payload fits, and an entry larger
than the whole budget is never stored (callers recompute it on demand — the
same recompute-on-miss contract every render cache already honors).

Sizes come from :func:`nbytes_of` (numpy arrays inside tuples / lists / dicts,
or any object exposing ``nbytes``); pass ``sizer=`` for other payloads.
"""

from __future__ import annotations

import hashlib
import threading
import weakref
from collections import OrderedDict
from collections.abc import Callable, Hashable
from typing import Any, TypeVar

import numpy as np

from al_dic_3d.viz3d.lru import LRUCache

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

_MISSING = object()


def nbytes_of(value: Any) -> int:
    """Approximate payload bytes of a cache value.

    Counts ``nbytes`` of numpy arrays (and of any object exposing an integer
    ``nbytes``) found directly or inside tuples, lists and dict values.
    Scalars, strings and ``None`` count as 0 (they are negligible next to the
    image-sized arrays the budget exists for).
    """
    if value is None:
        return 0
    nb = getattr(value, "nbytes", None)
    if isinstance(nb, int):
        return nb
    if isinstance(value, (tuple, list)):
        return sum(nbytes_of(v) for v in value)
    if isinstance(value, dict):
        return sum(nbytes_of(v) for v in value.values())
    return 0


class SizedLRUCache(LRUCache[K, V]):
    """:class:`LRUCache` with an additional total-bytes budget.

    ``total_bytes`` tracks the sum of the stored entries' sizes. Mutations go
    through ``__setitem__`` / ``__delitem__`` / ``pop`` / ``clear`` so the
    accounting never drifts; ``popitem`` is intentionally unsupported (the
    LRU contract evicts through ``del``).
    """

    def __init__(
        self,
        maxsize: int,
        max_bytes: int,
        sizer: Callable[[Any], int] = nbytes_of,
    ) -> None:
        if max_bytes < 1:
            raise ValueError(f"SizedLRUCache max_bytes must be >= 1, got {max_bytes}")
        super().__init__(maxsize)
        self.max_bytes = int(max_bytes)
        self._sizer = sizer
        self._sizes: dict[K, int] = {}
        self.total_bytes = 0

    def __setitem__(self, key: K, value: V) -> None:
        size = max(0, int(self._sizer(value)))
        if key in self:
            del self[key]  # release the old payload before re-inserting
        if size > self.max_bytes:
            return  # larger than the whole budget: recompute on demand instead
        super().__setitem__(key, value)  # entry-count eviction runs through __delitem__
        self._sizes[key] = size
        self.total_bytes += size
        while self.total_bytes > self.max_bytes and len(self) > 1:
            del self[next(iter(self))]

    def __delitem__(self, key: K) -> None:
        super().__delitem__(key)
        self.total_bytes -= self._sizes.pop(key, 0)

    def pop(self, key: K, default: Any = _MISSING) -> Any:  # type: ignore[override]
        if key in self:
            value = super().__getitem__(key)
            del self[key]
            return value
        if default is _MISSING:
            raise KeyError(key)
        return default

    def popitem(self, last: bool = True) -> tuple[K, V]:  # type: ignore[override]
        raise NotImplementedError("SizedLRUCache evicts through del; popitem is unsupported")

    def clear(self) -> None:
        super().clear()
        self._sizes.clear()
        self.total_bytes = 0


# ---------------------------------------------------------------------------
# Content digests for cache keys
# ---------------------------------------------------------------------------


def array_digest(arr: Any) -> bytes:
    """16-byte content digest of an array (values, shape and dtype)."""
    a = np.ascontiguousarray(arr)
    h = hashlib.blake2b(digest_size=16)
    h.update(str((a.shape, a.dtype.str)).encode("ascii"))
    h.update(a.view(np.uint8).reshape(-1) if a.size else b"")
    return h.digest()


def mask_digest(mask: Any, *, barrier: bool = False) -> bytes | None:
    """Digest of a mask's BOOLEAN meaning (``None`` passes through).

    ROI masks mean ``> 0`` (inside); crack barriers mean ``>= 0.5`` (material).
    Only the thresholded content is hashed (bit-packed), so a bool mask and its
    float image — which every consumer treats identically — share one key.
    """
    if mask is None:
        return None
    m = np.asarray(mask)
    inside = m if m.dtype == np.bool_ else (m >= 0.5 if barrier else m > 0)
    h = hashlib.blake2b(digest_size=16)
    h.update(str(inside.shape).encode("ascii"))
    h.update(np.packbits(inside, axis=None).tobytes())
    return h.digest()


class DigestMemo:
    """Identity memo in front of a digest function (thread-safe, bounded).

    Render inputs (ROI masks, node arrays) are treated as immutable once handed
    to a renderer — every ROI edit stores a FRESH array — so an object seen
    before maps to the digest computed then, for as long as it is alive
    (checked through a weak reference, so a recycled ``id`` never aliases).
    """

    def __init__(self, fn: Callable[[Any], Any], capacity: int = 16) -> None:
        self._fn = fn
        self._capacity = int(capacity)
        self._memo: OrderedDict[int, tuple[weakref.ref, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def __call__(self, obj: Any) -> Any:
        key = id(obj)
        with self._lock:
            hit = self._memo.get(key)
            if hit is not None and hit[0]() is obj:
                self._memo.move_to_end(key)
                return hit[1]
        value = self._fn(obj)
        try:
            ref = weakref.ref(obj)
        except TypeError:  # not weak-referenceable: never memoised
            return value
        with self._lock:
            self._memo[key] = (ref, value)
            self._memo.move_to_end(key)
            while len(self._memo) > self._capacity:
                self._memo.popitem(last=False)
        return value
