"""Rigid-motion removal for the Strain window (Qt-free).

The project draft holds the setting (mode + drawn fit region), so it is saved with
the project and survives re-runs; the run result is swapped through
:func:`al_dic_3d.run_rigid.with_rigid_motion`, so the main canvas, the 3D view,
the strain window and every export read one corrected result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.run_rigid import region_nodes, rigid_motion_signature, with_rigid_motion

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController

STATE_OFF = "off"  # the setting is off
STATE_WAITING = "waiting"  # on, but there is no run result yet
STATE_REMOVED = "removed"  # the displayed result has it removed
STATE_NOT_REMOVED = "not_removed"  # on, but the region cannot be fitted on this run

#: Margin (px) around the nodes when a result does not record its image size.
_SHAPE_MARGIN = 64


@dataclass(frozen=True)
class RigidMotionStatus:
    state: str
    mode: str
    n_used: int = 0  # reference-frame points in the fit
    drawn: bool = False  # fitted on a drawn region (else every valid point)
    reason: str = ""  # why it is not removed (STATE_NOT_REMOVED)


@dataclass(frozen=True)
class RigidMotionRow:
    frame: int  # 1-based, as shown
    shift_um: tuple[float, float, float]  # centroid shift of the fitted points
    angle_mrad: float
    rms_um: float
    n_used: int
    status: str  # al_dic_3d.reconstruct.rigid FIT_* code


class RigidMotionController3D:
    """Reads and writes the rigid-motion setting of the controller's project."""

    def __init__(self, controller: WorkflowController) -> None:
        self._controller = controller

    @property
    def _state(self):
        return self._controller.state

    def mode(self) -> str:
        return str(self._state.draft.rigid_motion_mode)

    def region(self) -> NDArray[np.bool_] | None:
        arr = self._state.draft.rigid_motion_region_array
        return None if arr is None else np.asarray(arr) > 0

    def image_shape(self) -> tuple[int, int] | None:
        """``(H, W)`` of the left reference image the region is drawn on."""
        result = self._state.result
        if result is None:
            return None
        size = result.meta.get("image_size")
        if size:
            return int(size[0]), int(size[1])
        xy = np.asarray(result.ref_coords, dtype=np.float64).reshape(-1, 2)
        finite = np.isfinite(xy).all(axis=1)
        if not finite.any():
            return None
        x_max, y_max = np.ceil(xy[finite].max(axis=0)).astype(int)
        return int(y_max) + _SHAPE_MARGIN, int(x_max) + _SHAPE_MARGIN

    def apply(self, mode: str, region: NDArray[np.bool_] | None) -> None:
        """Store the setting and swap the result.

        Raises ``ValueError`` — and changes nothing — when the region cannot
        support ``mode`` on the current run.
        """
        state = self._state
        result = state.result
        updated = None if result is None else with_rigid_motion(result, mode, region)
        state.draft.rigid_motion_mode = mode
        state.draft.rigid_motion_region_array = (
            None if region is None else np.asarray(region, dtype=bool).copy()
        )
        if updated is not None:
            state.result = updated
        state.mark_dirty()

    def status(self) -> RigidMotionStatus:
        mode, region = self.mode(), self.region()
        drawn = region is not None
        if mode == "off":
            return RigidMotionStatus(STATE_OFF, mode, drawn=drawn)
        result = self._state.result
        if result is None:
            return RigidMotionStatus(STATE_WAITING, mode, drawn=drawn)
        state = result.rigid_motion
        if state is not None:
            return RigidMotionStatus(
                STATE_REMOVED, state.fit.mode, int(state.fit.n_used[0]), state.region is not None
            )
        reason = ""
        try:
            region_nodes(result.ref_coords, region, mode)
        except ValueError as exc:
            reason = str(exc)
        return RigidMotionStatus(STATE_NOT_REMOVED, mode, drawn=drawn, reason=reason)

    def region_node_count(self) -> int | None:
        """Mesh nodes inside the drawn region (``None`` without a region or a result)."""
        result, region = self._state.result, self.region()
        if result is None or region is None:
            return None
        from al_dic_3d.reconstruct import region_to_nodes

        return int(region_to_nodes(result.ref_coords, region).sum())

    def rows(self) -> list[RigidMotionRow]:
        """The per-frame table of the removed motion (empty when nothing is removed)."""
        result = self._state.result
        state = None if result is None else result.rigid_motion
        if state is None:
            return []
        fit = state.fit
        angle = fit.angle_rad() * 1e3
        rows = []
        for k in range(fit.n_frames):
            sx, sy, sz = (fit.centroid_shift[k] * 1e3).tolist()
            rows.append(
                RigidMotionRow(
                    frame=k + 1,
                    shift_um=(sx, sy, sz),
                    angle_mrad=float(angle[k]),
                    rms_um=float(fit.rms[k] * 1e3),
                    n_used=int(fit.n_used[k]),
                    status=fit.status[k],
                )
            )
        return rows

    def strain_is_stale(self) -> bool:
        """The strain on display was computed under another rigid-motion setting.

        ``False`` when unknown (strain computed before the setting was recorded).
        """
        result = self._state.result
        if result is None or result.strain is None:
            return False
        recorded = result.meta.get("strain_rigid_motion")
        return recorded is not None and recorded != rigid_motion_signature(result)
