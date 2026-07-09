"""QualityGate enforcement on the ``CorrespondenceSet`` (Qt-free).

A pure filter that demotes low-quality per-frame positions to ``INVALID`` (NaN
positions, ``INVALID`` source) so downstream never triangulates a bad match. The
ZNSSD gate runs on the correspondence BEFORE reconstruction; the reprojection and
3D-outlier gates (``reconstruct.outliers``) run AFTER. Immutable: a new set is
returned.
"""

from __future__ import annotations

import numpy as np

from al_dic_3d.matching.contracts import INVALID, CorrespondenceSet


def apply_znssd_gate(cs: CorrespondenceSet, znssd_max: float) -> CorrespondenceSet:
    """Demote every ``(frame, point)`` whose ZNSSD exceeds ``znssd_max`` to INVALID.

    ``NaN`` quality (already invalid) is left untouched. Returns ``cs`` unchanged if
    nothing trips the gate.
    """
    bad = np.isfinite(cs.quality) & (cs.quality > float(znssd_max))
    if not bad.any():
        return cs

    xL = cs.xL.copy()
    xR = cs.xR.copy()
    quality = cs.quality.copy()
    source = cs.source.copy()
    xL[bad] = np.nan
    xR[bad] = np.nan
    quality[bad] = np.nan
    source[bad] = INVALID
    return CorrespondenceSet(
        strategy=cs.strategy,
        xL=xL,
        xR=xR,
        quality=quality,
        source=source,
        diagnostics=cs.diagnostics,  # F3.1: never lose the failure accounting
    )
