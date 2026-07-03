"""The pluggable ``CorrespondenceStrategy`` protocol and registry (02 §5.1).

A strategy turns ``(sequence, rig, reference mesh, config)`` into a
``CorrespondenceSet``. Concrete strategies register themselves via
:func:`register_strategy`; downstream code resolves them by name through
:func:`get_strategy` and never imports a concrete class.

``StereoRig``/``StereoSequence``/``DICMesh`` appear only in type hints
(``from __future__ import annotations`` keeps them un-evaluated at runtime), so
importing this module pulls in neither Qt nor ``al_dic``. ``al_dic.DICMesh`` is
recorded in DEPENDS_ON_2D.md.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar, Protocol, runtime_checkable

if TYPE_CHECKING:
    from al_dic import DICMesh  # type-only coupling; ledgered in DEPENDS_ON_2D.md

    from al_dic_3d.calibration import StereoRig
    from al_dic_3d.matching.contracts import CorrespondenceConfig, CorrespondenceSet
    from al_dic_3d.sequence import StereoSequence


@runtime_checkable
class CorrespondenceStrategy(Protocol):
    """Turn a sequence + rig + reference mesh into per-frame image positions."""

    name: ClassVar[str]

    def compute(
        self,
        seq: StereoSequence,
        rig: StereoRig,  # epipolar seeding / QC only — never a math shortcut
        mesh_L: DICMesh,  # reference material points (left camera, frame 1)
        cfg: CorrespondenceConfig,
        progress: Callable[[float, str], None] | None = None,
        stop: Callable[[], bool] | None = None,
    ) -> CorrespondenceSet: ...


STRATEGY_REGISTRY: dict[str, type[CorrespondenceStrategy]] = {}


def register_strategy(cls: type[CorrespondenceStrategy]) -> type[CorrespondenceStrategy]:
    """Class decorator: register a strategy under its ``name``."""
    name = cls.name
    if name in STRATEGY_REGISTRY and STRATEGY_REGISTRY[name] is not cls:
        raise ValueError(
            f"strategy name {name!r} already registered to {STRATEGY_REGISTRY[name]!r}"
        )
    STRATEGY_REGISTRY[name] = cls
    return cls


def get_strategy(name: str) -> type[CorrespondenceStrategy]:
    """Resolve a registered strategy class by name."""
    if name not in STRATEGY_REGISTRY:
        available = sorted(STRATEGY_REGISTRY) or ["(none registered yet)"]
        raise ValueError(f"unknown strategy {name!r}; available: {available}")
    return STRATEGY_REGISTRY[name]
