"""Post-run surface-strain controller (Qt-free, headless-testable).

The GUI pipeline runs with ``compute_strain=False`` (strain is post-processing,
Batch C); this controller offers the user-driven path: read the completed
:class:`~al_dic_3d.runner.RunResult`, run
:func:`~al_dic_3d.strain3d.compute_surface_strain` with an isolated, whitelisted
override, and write the strain back via :func:`dataclasses.replace` (the result
is a frozen dataclass — a NEW result object replaces the old one).

Mirrors the 2D ``StrainController`` design principles:

* No new state fields — strain lives inside the existing ``RunResult.strain``.
* Overrides are restricted to a whitelist so callers cannot accidentally
  re-tune the displacement pipeline from the strain window.
* Holds the :class:`WorkflowController` (not a state snapshot) because
  new/open-project REPLACES the ``AppState3D`` instance.

The 3-point specimen-frame helpers (node snapping +
:func:`~al_dic_3d.strain3d.specimen.specimen_frame`) also live here so the
window's pick flow stays a thin view.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.strain3d import compute_surface_strain
from al_dic_3d.strain3d.specimen import specimen_frame

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.runner import RunResult
    from al_dic_3d.strain3d.model import StrainResult3D

# Whitelist of compute_surface_strain knobs the strain window may override.
# Anything else would re-tune the displacement pipeline and is rejected.
ALLOWED_OVERRIDES: frozenset[str] = frozenset(
    {
        "strain_size",
        "smooth_sigma",
        "coordinate",
        "specimen_R",
        "strain_type",  # Q3: GL / infinitesimal / Eulerian-Almansi
        "edge_trim_alpha",  # Q4: VSG-support edge trim
    }
)


class StrainController3D:
    """Drive ``compute_surface_strain`` over an existing ``RunResult``."""

    def __init__(self, workflow: WorkflowController) -> None:
        self._workflow = workflow

    # ------------------------------------------------------------------
    # Compute + writeback
    # ------------------------------------------------------------------

    def compute(
        self,
        override: dict[str, object],
        progress_cb=None,
        stop_event=None,
    ) -> StrainResult3D:
        """Compute surface strain for every frame of the current result.

        Args:
            override: strain-only knobs; keys must be in
                :data:`ALLOWED_OVERRIDES` (``ValueError`` otherwise).
            progress_cb: optional ``(fraction, message)`` per-frame callback (P3.5).
            stop_event: optional ``threading.Event`` (or ``() -> bool``) —
                cancelling raises ``RuntimeError("cancelled")``.

        Raises:
            RuntimeError: when no run result is available, or on cancel.
        """
        result = self._require_result()
        self._validate_override(override)
        # Batch C items 2/3: when the run was crack-aware, thread the drawn ROI
        # mask (0-band = crack) into the gradient fit + edge trim so the strain
        # gauge honours the crack. Off otherwise -> byte-identical.
        roi_mask = None
        if bool(result.meta.get("crack_aware", False)):
            drawn = self._workflow.state.draft.roi_mask_array
            if drawn is not None:
                roi_mask = (np.asarray(drawn) > 0).astype(np.float64)
        return compute_surface_strain(
            result.reconstruction,
            result.ref_coords,
            strain_size=int(override.get("strain_size", 5)),
            winstepsize=int(self._workflow.state.draft.winstepsize),
            smooth_sigma=float(override.get("smooth_sigma", 0.0)),
            coordinate=str(override.get("coordinate", "local")),
            specimen_R=override.get("specimen_R"),  # type: ignore[arg-type]
            strain_type=str(override.get("strain_type", "green_lagrange")),  # Q3
            edge_trim_alpha=float(override.get("edge_trim_alpha", 0.0)),  # Q4
            roi_mask=roi_mask,
            progress_cb=progress_cb,
            stop_event=stop_event,
        )

    def apply(self, strain: StrainResult3D) -> RunResult:
        """Replace ``state.result`` with a copy carrying ``strain`` (frozen-safe)."""
        state = self._workflow.state
        new_result = replace(self._require_result(), strain=strain)
        state.result = new_result
        state.mark_dirty()
        return new_result

    def compute_and_store(self, override: dict[str, object]) -> RunResult:
        """Synchronous compute + writeback (the tests' blocking path)."""
        return self.apply(self.compute(override))

    # ------------------------------------------------------------------
    # Geometry info (R1.4: physical VSG size readout)
    # ------------------------------------------------------------------

    def node_spacing_mm(self) -> float | None:
        """Median 3D distance between adjacent reference-mesh nodes (mm).

        The robust per-node spacing estimate the strain window uses to
        translate the pixel VSG into a physical gauge size; ``None`` when no
        result exists or too few nodes have finite reference coordinates.
        """
        result = self._workflow.state.result
        if result is None:
            return None
        from al_dic_3d.viz3d.surface import median_nn_spacing

        pts = np.asarray(result.reconstruction.points[0], dtype=np.float64)
        pts = pts[np.isfinite(pts).all(axis=1)]
        if pts.shape[0] < 2:
            return None
        spacing = median_nn_spacing(pts)
        return float(spacing) if spacing > 0.0 else None

    # ------------------------------------------------------------------
    # 3-point specimen frame
    # ------------------------------------------------------------------

    def nearest_valid_node(self, x: float, y: float) -> int | None:
        """Index of the closest node with finite 2D and frame-1 3D coords."""
        result = self._workflow.state.result
        if result is None:
            return None
        ref_2d = np.asarray(result.ref_coords, dtype=np.float64)
        ref_3d = np.asarray(result.reconstruction.points[0], dtype=np.float64)
        valid = np.isfinite(ref_2d).all(axis=1) & np.isfinite(ref_3d).all(axis=1)
        if not valid.any():
            return None
        d2 = (ref_2d[:, 0] - x) ** 2 + (ref_2d[:, 1] - y) ** 2
        d2 = np.where(valid, d2, np.inf)
        return int(np.argmin(d2))

    def specimen_frame_from_nodes(
        self, node_indices: tuple[int, int, int] | list[int]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Build the specimen ``(R, T)`` from three picked node indices (O, +X, +Y)."""
        result = self._require_result()
        idx = list(node_indices)
        if len(idx) != 3:
            raise ValueError(f"need exactly 3 picked nodes, got {len(idx)}")
        base_2d = np.asarray(result.ref_coords, dtype=np.float64)[idx]
        return specimen_frame(result.ref_coords, result.reconstruction.points[0], base_2d)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _require_result(self) -> RunResult:
        result = self._workflow.state.result
        if result is None:
            raise RuntimeError(
                "StrainController3D: no run result available. "
                "Run the 3D analysis before computing strain."
            )
        return result

    @staticmethod
    def _validate_override(override: dict[str, object]) -> None:
        unknown = set(override) - ALLOWED_OVERRIDES
        if unknown:
            joined = ", ".join(sorted(unknown))
            raise ValueError(
                f"Override keys not allowed for strain post-processing: {joined}. "
                f"Allowed keys: {sorted(ALLOWED_OVERRIDES)}."
            )
