"""Crack barriers reach the renderers as the drawn ROI itself (fix batch V, H3).

The renderers read bool or float masks without copying; a float copy of a
12 Mpx ROI was 96 MB per render / export frame.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from al_dic_3d.export.render import crack_barrier
from al_dic_3d.export.render3d import _surface_barrier
from al_dic_3d.gui.strain_render import prepare_strain_render
from tests.test_strain_window import _synthetic_result


def _roi(shape=(400, 420)) -> np.ndarray:
    roi = np.ones(shape, bool)
    roi[:, shape[1] // 2] = False  # a thin crack
    return roi


def test_export_barriers_are_the_roi_itself():
    roi = _roi()
    crack_run = SimpleNamespace(meta={"crack_aware": True})
    plain_run = SimpleNamespace(meta={"crack_aware": False})
    assert crack_barrier(crack_run, roi) is roi
    assert _surface_barrier(crack_run, roi) is roi
    assert crack_barrier(plain_run, roi) is None
    assert _surface_barrier(plain_run, roi) is None
    assert crack_barrier(crack_run, None) is None


def test_strain_render_barrier_is_the_roi_itself():
    result = _synthetic_result()
    roi = _roi()
    kw = dict(roi_mask=roi, auto_range_on=True, manual_vmin=0.0, manual_vmax=1.0)
    rd = prepare_strain_render(result, "U", 1, deformed=False, crack_aware=True, **kw)
    assert rd.barrier_mask is roi
    rd = prepare_strain_render(result, "U", 1, deformed=True, crack_aware=True, **kw)
    assert rd.barrier_mask is None  # the crack is not warped: reference view only
    rd = prepare_strain_render(result, "U", 1, deformed=False, crack_aware=False, **kw)
    assert rd.barrier_mask is None
