"""The central correspondence contracts (02 §5.2 + 01 §E), Qt-free.

``CorrespondenceSet`` is the isolation wall: upstream absorbs all strategy/mode
complexity (acc/inc, reference scheduling, resampling, rescue); downstream
(``reconstruct``/``strain3d``/``viz3d``/``export``) sees only per-frame positions.
Downstream must import THESE contracts, never a concrete strategy.

``al_dic.FrameSchedule`` is referenced in a type-only import (see DEPENDS_ON_2D.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from al_dic import FrameSchedule  # type-only coupling; ledgered in DEPENDS_ON_2D.md

# ``source`` codes (uint8) — how each per-frame position was obtained.
TRACKED = 0
STEREO_REFRESH = 1
RESCUED = 2
INVALID = 3


@dataclass(frozen=True)
class QualityGate:
    """Thresholds that demote a point to ``INVALID`` (enforced in Phase 2)."""

    znssd_max: float = 0.5
    reproj_max_px: float = 2.0
    min_valid_frac: float = 0.5


@dataclass(frozen=True)
class DisparityField:
    """Cross-camera match for one frame (01 §E).

    Not assumed to belong only to frame 1 (strategy S2 produces one per frame).
    ``d`` is the left->right pixel disparity, so ``right_pts == left_pts + d``.
    """

    frame_idx: int
    left_pts: NDArray[np.float64]  # (n, 2) pixels in the left camera
    d: NDArray[np.float64]  # (n, 2) disparity
    znssd: NDArray[np.float64]  # (n,)
    valid: NDArray[np.bool_]  # (n,)

    @property
    def right_pts(self) -> NDArray[np.float64]:
        return self.left_pts + self.d


@dataclass(frozen=True)
class CorrespondenceConfig:
    """Strategy-agnostic configuration (02 §5.2)."""

    strategy: str = "track_both"
    reference_mode: Literal["accumulative", "incremental"] = "accumulative"
    schedule_L: FrameSchedule | None = None  # None -> derive from reference_mode
    schedule_R: FrameSchedule | None = None  # track_both only
    stereo_solver: Literal["local_only", "full_aldic"] = "local_only"
    epipolar_seed: bool = True  # bound the FFT search to an epipolar band
    disparity_offset: tuple[float, float] | None = None  # coarse prior, big baselines
    # Initial-guess mode (F2): "seed" needs seed_point (left frame-1 pixel);
    # without one it falls back to "fft" with a warning. Mapping to the engine:
    # al_dic_3d.matching.seed module docstring.
    init_guess: Literal["seed", "fft", "previous"] = "fft"
    seed_point: tuple[float, float] | None = None  # (x, y) on LEFT frame 1
    refresh_interval: int | None = None  # adaptive: periodic re-anchor
    quality: QualityGate = field(default_factory=QualityGate)


@dataclass(frozen=True)
class CorrespondenceSet:
    """Per-frame image-plane positions of the reference points in both cameras.

    ``NaN`` marks invalid; arrays are ``float64`` (positions/quality) and ``uint8``
    (source). This is the ONLY type downstream modules may consume.

    ``diagnostics`` (F3.1) carries the strategy's per-frame failure accounting
    as plain JSON-serializable row dicts (see
    :mod:`al_dic_3d.matching.diagnostics`); downstream compute ignores it —
    only the runner/CLI/GUI read it to report WHY points went invalid.
    """

    strategy: str
    xL: NDArray[np.float64]  # (n_frames, n_pts, 2), NaN = invalid
    xR: NDArray[np.float64]  # (n_frames, n_pts, 2)
    quality: NDArray[np.float64]  # (n_frames, n_pts) ZNSSD
    source: NDArray[np.uint8]  # (n_frames, n_pts): TRACKED/STEREO_REFRESH/RESCUED/INVALID
    diagnostics: tuple[dict, ...] = ()  # JSON-serializable failure accounting

    def __post_init__(self) -> None:
        if self.xL.shape != self.xR.shape or self.xL.ndim != 3 or self.xL.shape[2] != 2:
            raise ValueError(
                f"xL/xR must be equal (n_frames, n_pts, 2); got {self.xL.shape}, {self.xR.shape}"
            )
        expected = self.xL.shape[:2]
        if self.quality.shape != expected or self.source.shape != expected:
            raise ValueError(
                f"quality/source must be {expected}; got {self.quality.shape}, {self.source.shape}"
            )

    @property
    def n_frames(self) -> int:
        return int(self.xL.shape[0])

    @property
    def n_pts(self) -> int:
        return int(self.xL.shape[1])

    @classmethod
    def empty(cls, strategy: str, n_frames: int, n_pts: int) -> CorrespondenceSet:
        """An all-invalid set (NaN positions, INVALID source) to fill in."""
        nan = np.full((n_frames, n_pts, 2), np.nan, dtype=np.float64)
        return cls(
            strategy=strategy,
            xL=nan.copy(),
            xR=nan.copy(),
            quality=np.full((n_frames, n_pts), np.nan, dtype=np.float64),
            source=np.full((n_frames, n_pts), INVALID, dtype=np.uint8),
        )
