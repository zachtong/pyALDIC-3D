"""Matching — pluggable correspondence strategies.

The ``CorrespondenceStrategy`` protocol plus concrete strategies (``track_both``,
``stereo_each_frame``, ``ref_direct``, ...) and resampling utilities. Produces the
central, strategy- and mode-agnostic ``CorrespondenceSet`` contract; downstream
modules must depend only on that, never on a concrete strategy.

Layer: compute (**Qt-free**).  Lands: Phase 1 (S1) / Phase 2 (S2–S3).
Spec: docs/architecture/01 §B.1, §E and 02_correspondence_strategies.md §5.
"""

from al_dic_3d.matching.contracts import (
    INVALID,
    RESCUED,
    STEREO_REFRESH,
    TRACKED,
    CorrespondenceConfig,
    CorrespondenceSet,
    DisparityField,
    QualityGate,
)
from al_dic_3d.matching.quality import apply_znssd_gate
from al_dic_3d.matching.strategy import (
    STRATEGY_REGISTRY,
    CorrespondenceStrategy,
    get_strategy,
    register_strategy,
)

__all__ = [
    "INVALID",
    "RESCUED",
    "STEREO_REFRESH",
    "STRATEGY_REGISTRY",
    "TRACKED",
    "CorrespondenceConfig",
    "CorrespondenceSet",
    "CorrespondenceStrategy",
    "DisparityField",
    "QualityGate",
    "apply_znssd_gate",
    "get_strategy",
    "register_strategy",
]
