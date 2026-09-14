"""Synthetic *parity-gate* dataset -- a thin re-export of :mod:`al_dic_3d.synthetic`.

The generator (distorted convergent stereo rig, calibration file, config.toml,
analytic ground truth) moved into the package so ``al-dic-3d demo`` and
``al-dic-3d self-test`` can use it; the parity-gate tests keep importing it
from here unchanged.

NOT collected by pytest (no ``test_`` prefix).
"""

from __future__ import annotations

from al_dic_3d.synthetic import (  # noqa: F401 - re-exported for the tests
    DIST_L,
    DIST_R,
    FX,
    FY,
    GATE,
    PLANE_D,
    PLANE_N,
    Z0,
    _backproject,
    _on_plane,
    _plane_z,
    _render,
    _speckle,
    _u16,
    _write_calib,
    accuracy_summary,
    affine,
    build_parity_scene,
    build_scene,
    cameras,
    gate_passed,
    gate_rows,
    gt_tracks,
    metrics,
    write_config,
)
