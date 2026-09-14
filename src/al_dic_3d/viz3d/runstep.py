"""The node step (px) a RUN's mesh was built with — never the live draft (H3).

Every result consumer that needs the mesh node spacing (dense-overlay grid
density and edge cap, the right-camera / maskless support fallback, the strain
gauge) must use the step that PRODUCED the result. Reading the project draft
instead breaks as soon as the user edits Subset Step after a run: with a run at
step 16 and the draft at 8, the fallback support mask covered 0 % of the image
and right-camera / maskless overlays went blank.

Runs record ``meta["run_params"]["winstepsize"]`` (see ``runner.py``); older
sessions fall back to the median nearest-neighbour spacing of the reference
node coordinates, which equals the step on the regular reference lattice.
Qt-free.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from al_dic_3d.viz3d.surface import median_nn_spacing


def run_node_step(result: Any, default: int = 16) -> int:
    """The run's node step in pixels (``>= 1``).

    Order: ``result.meta["run_params"]["winstepsize"]`` when positive, else
    the rounded median nearest-neighbour spacing of the finite
    ``result.ref_coords``, else ``default``.
    """
    if result is None:
        return int(default)
    meta = getattr(result, "meta", None) or {}
    run_params = meta.get("run_params") or {}
    try:
        step = int(run_params.get("winstepsize", 0) or 0)
    except (TypeError, ValueError):
        step = 0
    if step > 0:
        return step
    ref = getattr(result, "ref_coords", None)
    if ref is not None:
        pts = np.asarray(ref, dtype=np.float64).reshape(-1, 2)
        pts = pts[np.isfinite(pts).all(axis=1)]
        spacing = median_nn_spacing(pts)
        if spacing > 0.0:
            return max(1, int(round(spacing)))
    return int(default)
