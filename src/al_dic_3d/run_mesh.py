"""The frame-1 LEFT reference mesh for a run (Qt-free).

Moved out of :mod:`al_dic_3d.runner` (the 800-line cap); the runner re-exports
both names, so ``from al_dic_3d.runner import build_reference_mesh`` keeps
working for the GUI's mesh preview and the tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.matching.primitives import make_dicpara
from al_dic_3d.matching.temporal import build_grid_mesh

if TYPE_CHECKING:
    from al_dic.core.data_structures import DICMesh

    from al_dic_3d.runner import RunConfig


def build_reference_mesh(
    img_h: int,
    img_w: int,
    roi: tuple[int, int, int, int],
    *,
    winsize: int = 32,
    winstepsize: int = 16,
    winsize_min: int = 8,
    refine_inner: bool = False,
    refine_outer: bool = False,
    refinement_level: int = 1,
    refinement_brush: NDArray[np.float64] | None = None,
    mask: NDArray[np.float64] | None = None,
) -> DICMesh:
    """The frame-1 LEFT reference mesh: uniform grid, optionally quadtree-refined.

    Refinement follows the 2D app's levers verbatim (build_refinement_policy):
    inner mask-boundary / outer ROI-edge / user-painted brush criteria with
    min element size ``max(2, winstepsize // 2**level)``. The refined mesh is
    built ONCE and passed to the strategies as the external mesh — the engine's
    per-frame refinement hook is deliberately NOT used (the mesh-built-once
    invariant; MATLAB's acc-mode per-frame quadtree is identical per frame
    anyway).

    Plain-args and Qt-free on purpose: the GUI's live mesh PREVIEW calls this
    exact function with the draft's parameters, so preview == pipeline.

    Args:
        roi: ``(xmin, xmax, ymin, ymax)`` pixel bounds of the grid.
        refinement_brush: optional ``(H, W)`` user-painted refine-here mask
            (``> 0`` = refine), already in frame-1 left image coordinates.
        mask: optional ``(H, W)`` float frame-1 left ROI mask (1 = valid) used
            by the refinement criteria/trim.
    """
    para = make_dicpara(
        img_size=(img_h, img_w),
        roi=roi,
        winsize=winsize,
        winstepsize=winstepsize,
        winsize_min=winsize_min,
    )
    mesh = build_grid_mesh(para, img_h, img_w)

    if not (refine_inner or refine_outer or refinement_brush is not None):
        return mesh

    # See docs/DEPENDS_ON_2D.md for these engine imports.
    from al_dic.mesh.refinement import (
        RefinementContext,
        build_refinement_policy,
        refine_mesh,
    )

    mask_l1 = None
    if mask is not None:
        mask_l1 = np.ascontiguousarray(np.asarray(mask, dtype=np.float64))
    min_size = max(2, winstepsize // (2 ** max(1, refinement_level)))
    policy = build_refinement_policy(
        refine_inner_boundary=refine_inner,
        refine_outer_boundary=refine_outer,
        refinement_mask=refinement_brush,
        min_element_size=min_size,
        half_win=winsize // 2,
    )
    if policy is None:
        return mesh
    ctx = RefinementContext(mesh=mesh, mask=mask_l1)
    u0 = np.zeros(2 * np.asarray(mesh.coordinates_fem).shape[0], dtype=np.float64)
    refined, _u0 = refine_mesh(
        mesh, policy.pre_solve, ctx, u0, mask=mask_l1, img_size=(img_h, img_w)
    )
    return refined


def mesh_for_config(cfg: RunConfig, img_h: int, img_w: int, left_masks) -> DICMesh:
    """Config-driven wrapper over :func:`build_reference_mesh` (loads the brush PNG)."""
    brush = None
    if cfg.refinement_mask is not None:
        import cv2

        from al_dic_3d.pathsafe import imread_unicode

        img = imread_unicode(cfg.refinement_mask, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"cannot read refinement mask: {cfg.refinement_mask}")
        brush = (img > 0).astype(np.float64)
    return build_reference_mesh(
        img_h,
        img_w,
        cfg.roi,
        winsize=cfg.winsize,
        winstepsize=cfg.winstepsize,
        winsize_min=cfg.winsize_min,
        refine_inner=cfg.refine_inner,
        refine_outer=cfg.refine_outer,
        refinement_level=cfg.refinement_level,
        refinement_brush=brush,
        mask=left_masks[0] if left_masks is not None else None,
    )
