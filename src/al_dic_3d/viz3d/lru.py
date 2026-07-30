"""Bounded LRU mapping for the render/display caches (Qt-free).

The viz caches (dense-grid interpolations, warp masks, support masks, colored
pixmaps, decoded frames) used to be unbounded dicts: browsing hundreds of
frames grew them without limit (P2.1 audit: 15+ GB theoretical). Every
consumer recomputes an entry on miss — that is the cache contract — so
least-recently-used eviction is always SAFE: a cap trades an occasional
recompute for bounded memory, never a different result.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TypeVar

K = TypeVar("K")
V = TypeVar("V")


class LRUCache(OrderedDict[K, V]):
    """``OrderedDict`` with a size cap and least-recently-used eviction.

    ``get``/``__getitem__`` refresh recency; ``__setitem__`` inserts as most
    recent and evicts the oldest entries beyond ``maxsize``. ``in`` does NOT
    refresh recency (membership probes must not promote stale entries).
    """

    def __init__(self, maxsize: int) -> None:
        if maxsize < 1:
            raise ValueError(f"LRUCache maxsize must be >= 1, got {maxsize}")
        super().__init__()
        self.maxsize = int(maxsize)

    def __getitem__(self, key: K) -> V:
        value = super().__getitem__(key)
        # py3.10's C OrderedDict dispatches internal lookups (e.g. from
        # popitem) to this override while the key is mid-removal from the
        # linked list; move_to_end then raises KeyError although the hash
        # lookup above succeeded (py3.12 no longer dispatches). Skipping the
        # recency refresh for a key that is being evicted is semantically
        # correct, so tolerate it.
        try:
            self.move_to_end(key)
        except KeyError:
            pass
        return value

    def get(self, key: K, default: V | None = None) -> V | None:  # type: ignore[override]
        if key in self:
            return self[key]
        return default

    def __setitem__(self, key: K, value: V) -> None:
        super().__setitem__(key, value)
        self.move_to_end(key)
        while len(self) > self.maxsize:
            # NOT popitem(last=False): py3.10's popitem re-enters the subclass
            # __getitem__ mid-removal (see above). Plain del via the oldest
            # linked-list key never dispatches back into this class.
            del self[next(iter(self))]
