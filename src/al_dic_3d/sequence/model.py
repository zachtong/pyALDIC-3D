"""StereoSequence over dual camera streams (Qt-free).

Holds one frame provider per camera plus optional per-camera mask streams and
file names, and validates the pairing (frame counts, mask shapes, name patterns)
before any matching runs — a mispaired sequence must fail here, not silently
corrupt correspondence.

The provider is a **structural** ``FrameProvider`` protocol matching the 2D
engine's interface (``__len__`` / ``shape`` / ``get_normalized``), so the real
pipeline's ``al_dic.io.ListFrameProvider`` conforms by duck typing without this
compute module importing Qt or the 2D package.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


@runtime_checkable
class FrameProvider(Protocol):
    """The frame-access surface shared with the 2D engine's providers."""

    def __len__(self) -> int: ...

    @property
    def shape(self) -> tuple[int, int]: ...

    def get_normalized(self, idx: int) -> NDArray[np.float64]: ...


@dataclass
class ArrayFrameProvider:
    """A minimal in-memory :class:`FrameProvider` over a list of frames.

    Frames are treated as already-normalized ``float64`` ``(H, W)`` arrays. Used
    for tests and headless callers that hold raw arrays; the production path may
    instead use the 2D ``ListFrameProvider`` (same protocol).
    """

    frames: list[NDArray[np.float64]]

    def __len__(self) -> int:
        return len(self.frames)

    @property
    def shape(self) -> tuple[int, int]:
        return tuple(self.frames[0].shape) if self.frames else (0, 0)  # type: ignore[return-value]

    def get_normalized(self, idx: int) -> NDArray[np.float64]:
        return self.frames[idx]


_INDEX_RE = re.compile(r"(\d+)")


def _trailing_index(name: str) -> str | None:
    """Return the last run of digits in a file name (its frame index), or None."""
    matches = _INDEX_RE.findall(name)
    return matches[-1] if matches else None


@dataclass(frozen=True)
class StereoSequence:
    """Dual-camera image streams with mask streams and pairing validation.

    ``providers`` maps a camera key (``"L"``, ``"R"``) to a :class:`FrameProvider`.
    ``masks`` optionally maps a camera to a per-frame mask stream (``(H, W)`` arrays,
    non-zero = valid). ``names`` optionally maps a camera to per-frame file names,
    used only for the name-pattern pairing check.
    """

    providers: Mapping[str, FrameProvider]
    masks: Mapping[str, Sequence[NDArray[np.float64]] | None] = field(default_factory=dict)
    names: Mapping[str, Sequence[str] | None] = field(default_factory=dict)

    @property
    def cameras(self) -> tuple[str, ...]:
        return tuple(self.providers)

    @property
    def n_frames(self) -> int:
        """Frame count (from the left/first camera). Use :meth:`validate` first —
        counts may disagree across cameras until validation passes."""
        if not self.providers:
            return 0
        first = next(iter(self.providers.values()))
        return len(first)

    def frame(self, cam: str, idx: int) -> NDArray[np.float64]:
        return self.providers[cam].get_normalized(idx)

    def mask(self, cam: str, idx: int) -> NDArray[np.float64] | None:
        stream = self.masks.get(cam)
        return None if stream is None else stream[idx]

    def issues(self) -> list[str]:
        """Return a list of pairing problems (empty list == a valid pairing)."""
        problems: list[str] = []
        if not self.providers:
            return ["no camera providers"]

        counts = {cam: len(p) for cam, p in self.providers.items()}
        n = next(iter(counts.values()))
        if any(c != n for c in counts.values()):
            problems.append(f"frame-count mismatch: {counts}")
        if n == 0:
            problems.append("empty sequence (0 frames)")

        for cam, provider in self.providers.items():
            stream = self.masks.get(cam)
            if stream is None:
                continue
            if len(stream) != len(provider):
                problems.append(f"camera {cam!r}: {len(stream)} masks for {len(provider)} frames")
            for i, m in enumerate(stream):
                if tuple(m.shape) != tuple(provider.shape):
                    problems.append(
                        f"camera {cam!r} frame {i}: mask {m.shape} != image {provider.shape}"
                    )
                    break

        # Name-pattern check: the per-frame trailing indices must line up across
        # cameras (a common mispair is L/R lists sorted differently).
        named = {cam: list(v) for cam, v in self.names.items() if v is not None}
        if len(named) >= 2:
            index_lists = {cam: [_trailing_index(x) for x in v] for cam, v in named.items()}
            ref_cam, ref_idx = next(iter(index_lists.items()))
            for cam, idx_list in index_lists.items():
                if idx_list != ref_idx:
                    problems.append(f"name-pattern mismatch between {ref_cam!r} and {cam!r}")
                    break
        return problems

    def validate(self) -> None:
        """Raise :class:`ValueError` if the pairing is invalid."""
        problems = self.issues()
        if problems:
            raise ValueError("invalid stereo sequence: " + "; ".join(problems))
