"""Surface-strain result container (frozen dataclass, Qt-free; see docs/strain3d_math.md).

Per-frame, per-node Green-Lagrange surface strain in the local tangent frame, plus
principal / shear / von-Mises invariants and the out-of-plane slope diagnostics.
``NaN`` = invalid / void (a node with too few neighbours for a stable gauge).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

# The nine per-node fields carried by a StrainResult3D, in a fixed order.
STRAIN_FIELDS = (
    "exx",
    "eyy",
    "exy",
    "e1",
    "e2",
    "max_shear",
    "von_mises",
    "dwdx",
    "dwdy",
)


@dataclass(frozen=True)
class StrainResult3D:
    """Green-Lagrange surface strain per frame per node (01 §E, docs/strain3d_math.md)."""

    exx: NDArray[np.float64]  # (n_frames, n_pts) tangent-frame Green-Lagrange strain
    eyy: NDArray[np.float64]
    exy: NDArray[np.float64]
    e1: NDArray[np.float64]  # major principal strain
    e2: NDArray[np.float64]  # minor principal strain
    max_shear: NDArray[np.float64]
    von_mises: NDArray[np.float64]
    dwdx: NDArray[np.float64]  # out-of-plane slope diagnostics
    dwdy: NDArray[np.float64]
    # Q4 edge-trim bookkeeping: per-frame count of VALID nodes whose strain was
    # trimmed near invalid/missing nodes or a crack barrier (alpha * VSG-radius
    # band). ``None`` when trimming was disabled (or after a session reload — the
    # counts are a UI readout, not part of the persisted result arrays).
    n_trimmed: NDArray[np.int64] | None = None
    # Batch C item 3 (A5-2): per-frame, per-node ``(n_frames, n_pts)`` bool — the
    # 2D contract. Strain VALUES stay DENSE; ``strain_valid`` carries the edge-trim
    # UNION crack-trim (``True`` = show, ``False`` = trimmed). Consumers NaN-out
    # ``~strain_valid`` for display / export, and the reference view can apply
    # frame-0 validity while the deformed view applies frame-k validity. ``None``
    # when trimming was disabled (all nodes valid).
    strain_valid: NDArray[np.bool_] | None = None

    def __post_init__(self) -> None:
        shape = self.exx.shape
        if len(shape) != 2:
            raise ValueError(f"strain fields must be (n_frames, n_pts); got {shape}")
        for name in STRAIN_FIELDS:
            arr = getattr(self, name)
            if arr.shape != shape:
                raise ValueError(f"field {name!r} shape {arr.shape} != {shape}")
        if self.strain_valid is not None and self.strain_valid.shape != shape:
            raise ValueError(f"strain_valid shape {self.strain_valid.shape} != {shape}")

    @property
    def n_frames(self) -> int:
        return int(self.exx.shape[0])

    @property
    def n_pts(self) -> int:
        return int(self.exx.shape[1])
