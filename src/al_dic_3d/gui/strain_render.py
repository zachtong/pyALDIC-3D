"""Qt-free render-data prep for the strain window (extracted for the 800-line cap).

Holds the strain window's per-frame render math so :mod:`al_dic_3d.gui.strain_window`
stays under the file-size cap. Everything here is pure numpy + the Qt-free display
helpers, so it carries NO ``self.tr()`` (the window keeps all user-facing strings).

The display mask routes through :func:`al_dic_3d.export.display_field_frame` — the
ONE helper the canvas, image export, animation, and 3D view share — so a trimmed
strain node (``~strain_valid``) is hidden identically everywhere (Batch C, C3).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.export import display_field_frame
from al_dic_3d.viz3d.fieldmap import auto_range, visible_values


@dataclass(frozen=True)
class StrainRenderData:
    """The per-frame inputs the strain canvas hands to the dense renderer."""

    vals: NDArray[np.float64]
    pts: NDArray[np.float64]
    ref_pts: NDArray[np.float64]
    ref_uv: tuple[NDArray[np.float64], NDArray[np.float64]] | None
    barrier_mask: NDArray[np.float64] | None
    vmin: float
    vmax: float


def trim_count(strain, k: int) -> int | None:
    """Frame-k trimmed-node count for the live 'Trimmed: N nodes' readout.

    Prefers the fresh-compute ``n_trimmed`` (a UI readout that is not persisted),
    and falls back to ``(~strain_valid[k]).sum()`` after a session/archive reload
    where only ``strain_valid`` survived (Batch C, C3-3) — so the readout does not
    blank even though the trim is still applied to the canvas. ``None`` when
    trimming was disabled (both are absent).
    """
    if strain.n_trimmed is not None:
        return int(strain.n_trimmed[k])
    if strain.strain_valid is not None:
        return int((~np.asarray(strain.strain_valid[k])).sum())
    return None


def prepare_strain_render(
    result,
    field: str,
    k: int,
    *,
    deformed: bool,
    roi_mask: NDArray[np.bool_] | None,
    crack_aware: bool,
    auto_range_on: bool,
    manual_vmin: float,
    manual_vmax: float,
) -> StrainRenderData:
    """The strain window's per-frame render inputs (values, geometry, range).

    * ``vals`` is the display-masked field (``~strain_valid`` -> NaN via
      :func:`display_field_frame`), so the canvas and every export hide the same
      trimmed nodes and auto-range over the same visible set.
    * geometry follows the deformed toggle (``ref_uv = x_k - x_1`` warps the
      reference support in deformed mode; values always belong to frame k).
    * ``barrier_mask`` blanks crack-bridging cells in the reference view only
      (item 4); the deformed crack is not warped, so no barrier there.
    * the range is the 2-98 percentile of the VISIBLE nodes (2D parity) when auto,
      else the caller's manual bounds.
    """
    cs = result.correspondence
    vals = display_field_frame(result, field, k, deformed=deformed)
    pts = cs.xL[k] if deformed else cs.xL[0]
    ref_pts = cs.xL[0]
    ref_uv = None
    if deformed:
        d = cs.xL[k] - cs.xL[0]  # 2D ref_uv contract: x_k - x_1 per node
        ref_uv = (d[:, 0], d[:, 1])
    barrier_mask = (
        roi_mask.astype(np.float64)
        if (crack_aware and roi_mask is not None and not deformed)
        else None
    )
    if auto_range_on:
        vmin, vmax = auto_range(visible_values(vals, ref_pts, roi_mask))
    else:
        vmin, vmax = float(manual_vmin), float(manual_vmax)
    return StrainRenderData(vals, pts, ref_pts, ref_uv, barrier_mask, float(vmin), float(vmax))
