"""Multi-seed F-aware propagation initial guess (Qt-free) — Batch S.

pyALDIC-3D always hands the 2D engine an EXTERNAL frame-1 mesh, which SKIPS the
engine's own ``init_guess_mode='seed_propagation'`` path (that only runs when the
engine builds its own internal mesh). The only lever left on an external-mesh run
is the ``U0`` array passed to ``run_aldic`` (via
:func:`al_dic_3d.matching.temporal.temporal_track`). So seed propagation for 3D is
orchestrated HERE: from sparse user-placed seeds we build a FULL per-node ``U0``
displacement field and hand it to the engine — generalizing the single-seed
uniform ``U0`` of :mod:`al_dic_3d.matching.seed` to many seeds with F-aware
first-order propagation.

The propagation MATH is the 2D engine's, reused verbatim (never reinvented,
D11): :func:`al_dic.solver.seed_propagation.propagate_from_seeds` runs a
layer-synchronous, F-aware BFS — each solved node's IC-GN gives ``(U, F)`` and
predicts an unsolved neighbour ``j`` from parent ``i`` via the first-order
predictor (spec_A4 §5.5, F layout ``[dudx, dvdx, dudy, dvdy]``)::

    u0_j = U_i[0] + F_i[0]·dx + F_i[2]·dy      # dx = x_j − x_i, dy = y_j − y_i
    v0_j = U_i[1] + F_i[1]·dx + F_i[3]·dy

with the engine's real acceptance test (IC-GN converged) and the seed bootstrap
gate ``ncc_threshold`` (default 0.55; the internal expand gate 0.85 is stricter).
This module only DRIVES that routine (build the IC-GN context / adjacency /
region map, snap seed pixels to nodes, auto-place a seed in any region the user
left empty, then interleave the solved ``U_2d`` into ``U0``). Nodes the BFS never
reaches stay ``NaN``. On the external-mesh path these are NOT handled identically
to the FFT path: the engine's INPUT-side inpaint (``init_disp``) that gives every
FFT node a finite IC-GN start is SKIPPED (it runs only when the engine builds its
own mesh), so unsolved nodes get only OUTPUT-side ``fill_nan_idw`` — pure IDW of
the solved neighbours, with no independent IC-GN refinement on the first frame.
Callers therefore reject a low-coverage propagation and degrade to FFT (see
``matching.strategies._common``); frame-2 onward recovers via warm-start.

Every ``al_dic`` symbol imported here is recorded in ``docs/DEPENDS_ON_2D.md``.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

# --- 2D engine (al_dic) imports — see docs/DEPENDS_ON_2D.md -------------------
from al_dic.io.image_ops import compute_image_gradient
from al_dic.solver.local_icgn import local_icgn_precompute
from al_dic.solver.seed_auto_place import AutoPlaceConfig, auto_place_seeds_on_mesh
from al_dic.solver.seed_propagation import (
    Seed,
    SeedPropagationError,
    SeedSet,
    build_node_adjacency,
    covered_region_ids,
    propagate_from_seeds,
)
from al_dic.utils.region_analysis import precompute_node_regions
from numpy.typing import NDArray

if TYPE_CHECKING:
    from al_dic.core.data_structures import DICMesh, DICPara

#: Seed-bootstrap accept/reject NCC floor — the engine ``SeedSet.ncc_threshold``
#: default (seed_propagation.py:137). Below it a seed is dropped (then rescued).
SEED_PROP_NCC = 0.55
#: The engine ``AutoPlaceConfig.high_quality_ncc`` strict bar (0.85) — kept for
#: callers/tests that want to name it; auto-place uses it internally by default.
SEED_PROP_HQ_NCC = 0.85


@dataclass(frozen=True)
class SeedU0Result:
    """A full per-node ``U0`` field built by F-aware seed propagation.

    ``u0`` is interleaved ``[u0, v0, u1, v1, ...]`` of length ``2 * n_nodes``
    (the layout ``run_aldic`` expects for an external mesh), with ``NaN`` on
    nodes the BFS never reached (absorbed by the engine's OUTPUT ``fill_nan_idw``
    — NOT the FFT path's input-side inpaint; see the module docstring). The
    remaining fields are run diagnostics (never silent — F3.1): how many nodes
    the propagation solved, how many trackable region nodes there were (the
    coverage denominator the caller gates on), how many connected regions the
    ROI split into, how many seeds ended up active, plus the auto-place / rescue
    / drop accounting.
    """

    u0: NDArray[np.float64]  # (2 * n_nodes,), NaN at unsolved
    n_nodes: int
    n_solved: int
    n_region_nodes: int  # nodes inside a trackable region (coverage denominator)
    n_regions: int
    n_seeds: int  # active seeds after snap + auto-fill + rescue
    auto_placed: int  # seeds auto-placed into regions the user left empty
    rescued: int  # seeds auto-placed to rescue regions whose seeds all failed
    seed_ncc_min: float
    dropped: tuple[tuple[int, str], ...]

    @property
    def u0_2d(self) -> NDArray[np.float64]:
        """The ``U0`` field as ``(n_nodes, 2)`` ``[u, v]`` (NaN rows = unsolved)."""
        return self.u0.reshape(self.n_nodes, 2)


def resolve_seeds_to_nodes(
    coordinates_fem: NDArray[np.float64],
    region_map,
    seed_points,
) -> tuple[Seed, ...]:
    """Snap each ``(x, y)`` seed pixel to the nearest mesh node in its region.

    Each seed lives on the LEFT camera, frame 1 (image pixels). It is bound to
    the closest mesh node; the node's actual region (via ``region_map``) becomes
    the seed's ``region_id`` (so the engine's per-region validation is
    consistent). Seeds whose nearest node lies outside every tracked region
    (mask hole / the gap between disconnected ROI blobs) are dropped. Duplicate
    snapped nodes collapse to one (first wins), so the returned seeds have
    unique ``node_idx``.
    """
    coords = np.asarray(coordinates_fem, dtype=np.float64).reshape(-1, 2)
    n = coords.shape[0]
    node_to_region = np.full(n, -1, dtype=np.int64)
    for region_idx, nodes in enumerate(region_map.region_node_lists):
        node_to_region[nodes] = region_idx

    seeds: list[Seed] = []
    seen: set[int] = set()
    for xy in seed_points:
        p = np.asarray(xy, dtype=np.float64).reshape(2)
        node = int(np.argmin(np.sum((coords - p) ** 2, axis=1)))
        region = int(node_to_region[node])
        if region < 0 or node in seen:
            continue
        seen.add(node)
        seeds.append(Seed(node_idx=node, region_id=region, user_hint_uv=None))
    return tuple(seeds)


def seed_region_readiness(
    mask: NDArray[np.float64],
    seed_points,
    *,
    min_area: int = 20,
) -> tuple[int, int]:
    """``(#regions with >= 1 seed, #connected regions)`` — the GUI readiness readout.

    Regions are the connected components of ``mask`` (8-connectivity) with area
    ``> min_area``, matching the engine's ``precompute_node_regions`` component
    rule. A seed pixel is attributed to the region label under its rounded
    coordinate; a seed over background (or too-small a component) counts for no
    region. Mesh-free on purpose: the sidebar has the ROI mask and the placed
    seeds before any run/mesh exists, and only needs a "how many regions are
    seeded" hint (the run itself re-derives regions against the real mesh).
    """
    from scipy.ndimage import label

    m = np.asarray(mask) > 0.5
    if m.ndim != 2 or not m.any():
        return (0, 0)
    labeled, n_labels = label(m, structure=np.ones((3, 3), dtype=np.int32))
    h, w = m.shape
    valid_labels = [lbl for lbl in range(1, n_labels + 1) if int(np.sum(labeled == lbl)) > min_area]
    n_regions = len(valid_labels)
    if n_regions == 0:
        return (0, 0)
    seeded: set[int] = set()
    for xy in seed_points:
        x = int(np.clip(round(float(xy[0])), 0, w - 1))
        y = int(np.clip(round(float(xy[1])), 0, h - 1))
        lbl = int(labeled[y, x])
        if lbl in valid_labels:
            seeded.add(lbl)
    return (len(seeded), n_regions)


def seed_region_readiness_mesh(
    mask: NDArray[np.float64],
    seed_points,
    *,
    winsize: int,
    winstepsize: int,
    winsize_min: int,
) -> tuple[int, int]:
    """``(#regions with >= 1 seed, #regions)`` using the RUNNER's node-region logic.

    Unlike :func:`seed_region_readiness` (a mesh-free mask-only heuristic), this
    reproduces exactly what the run enforces, so the GUI readout can never
    disagree with the actual propagation in either direction:

    * builds the same uniform reference grid the runner tracks on
      (:func:`al_dic_3d.matching.temporal.build_grid_mesh`, over the mask's
      ``> 0`` bounding box — the runner's ``_mask_bbox``);
    * maps nodes to connected regions with the engine's
      :func:`al_dic.utils.region_analysis.precompute_node_regions`, which keeps a
      component only if its area ``> min_area`` **and** it holds ``>= 2`` mesh
      nodes (so a blob too small to carry two nodes is dropped, as the runner
      drops it);
    * attributes each seed by node-snapping (:func:`resolve_seeds_to_nodes`), so a
      seed just outside a blob still counts for the region whose nearest node it
      snaps to — exactly as the run seeds it.

    Refinement (which only subdivides elements) never merges or splits a
    connected region, so the uniform grid gives the same region COUNT as the
    refined mesh the runner would build. ``(0, 0)`` when the mask is empty.
    """
    from al_dic_3d.matching.primitives import make_dicpara
    from al_dic_3d.matching.temporal import build_grid_mesh

    m = np.asarray(mask, dtype=np.float64)
    mask_bool = m > 0.5
    if m.ndim != 2 or not mask_bool.any():
        return (0, 0)
    h, w = m.shape
    ys, xs = np.nonzero(mask_bool)
    roi = (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))
    para = make_dicpara(
        img_size=(h, w),
        roi=roi,
        winsize=int(winsize),
        winstepsize=int(winstepsize),
        winsize_min=int(winsize_min),
        img_ref_mask=m,
    )
    mesh = build_grid_mesh(para, h, w)
    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64).reshape(-1, 2)
    region_map = precompute_node_regions(coords, m, (h, w))
    if region_map.n_regions == 0:
        return (0, 0)
    seeds = resolve_seeds_to_nodes(coords, region_map, seed_points)
    covered = {int(s.region_id) for s in seeds}
    return (len(covered), int(region_map.n_regions))


def build_seed_u0(
    f_img: NDArray[np.float64],
    g_img: NDArray[np.float64],
    mesh: DICMesh,
    mask: NDArray[np.float64] | None,
    seed_points,
    para: DICPara,
    *,
    search_radius: int,
    tol: float = 1e-3,
    ncc_threshold: float = SEED_PROP_NCC,
    auto_fill: bool = True,
) -> SeedU0Result | None:
    """Build a full per-node ``U0`` field from sparse seeds via F-aware propagation.

    Drives the engine's ``propagate_from_seeds`` on the EXTERNAL ``mesh`` for one
    reference/deformed pair (e.g. left frame 0 -> frame 1 for the temporal U0, or
    left frame 0 -> right frame 0 for the stereo pair) and interleaves the solved
    node displacements into the ``U0`` vector ``run_aldic`` consumes.

    Args:
        f_img, g_img: reference / deformed ``(H, W)`` float64 images (RAW,
            unmasked — masking is applied at node level, mirroring the engine).
        mesh: the external reference mesh (its ``coordinates_fem`` are the tracked
            nodes; ``elements_fem`` gives the Q8 adjacency for the BFS).
        mask: ``(H, W)`` float64 ROI mask (1 = valid); gates the IC-GN reference
            gradient and splits the ROI into connected regions.
        seed_points: iterable of ``(x, y)`` seed pixels on ``f_img`` (frame 1).
        para: the local ``DICPara`` for this camera (``winsize`` / ``icgn_max_iter``
            size the IC-GN context + NCC template).
        search_radius: initial single-point NCC search half-width for the seed
            bootstrap (auto-expands on clipped peaks inside the engine).
        tol: IC-GN convergence tolerance.
        ncc_threshold: seed accept/reject NCC floor (default 0.55).
        auto_fill: auto-place one seed in each connected region the user left
            unseeded (preserving the placed seeds) so the engine's
            one-seed-per-region requirement is met — the 3D analogue of the
            engine pipeline's uncovered-region rescue.

    Returns:
        A :class:`SeedU0Result`, or ``None`` when propagation cannot produce a
        usable field (no seeds land in a region, a region cannot be seeded even
        after auto-place, the ROI has no valid region, or the seed NCC fails).
        ``None`` is the caller's cue to fall back to FFT seeding — a warning is
        emitted so the degrade is never silent.
    """
    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64).reshape(-1, 2)
    n_nodes = coords.shape[0]
    f_img = np.ascontiguousarray(f_img, dtype=np.float64)
    g_img = np.ascontiguousarray(g_img, dtype=np.float64)
    # No ROI mask (or a shape mismatch) -> track the whole image as one region,
    # exactly as temporal_track defaults an absent mask to all-ones.
    if mask is None:
        mask = np.ones(f_img.shape, dtype=np.float64)
    else:
        mask = np.ascontiguousarray(mask, dtype=np.float64)
        if mask.shape != f_img.shape:
            mask = np.ones(f_img.shape, dtype=np.float64)

    region_map = precompute_node_regions(coords, mask, f_img.shape)
    if region_map.n_regions == 0:
        warnings.warn(
            "seed propagation: the ROI mask has no trackable region — falling back to FFT seeding.",
            UserWarning,
            stacklevel=2,
        )
        return None

    seeds = resolve_seeds_to_nodes(coords, region_map, seed_points)
    if not seeds:
        warnings.warn(
            "seed propagation: no placed seed lies inside a trackable region — "
            "falling back to FFT seeding.",
            UserWarning,
            stacklevel=2,
        )
        return None
    seed_set = SeedSet(seeds=seeds, ncc_threshold=float(ncc_threshold))

    adjacency = build_node_adjacency(mesh.elements_fem, n_nodes)

    # Auto-fill: every connected region needs at least one seed before
    # propagate_from_seeds' region validation runs (it is fatal on an unseeded
    # region). Auto-place a seed in each region the user left empty, keeping the
    # placed seeds untouched (skip_region_ids = already covered). This is the 3D
    # analogue of the engine pipeline's uncovered-region rescue.
    auto_placed = 0
    if auto_fill:
        covered = covered_region_ids(seed_set, region_map, n_nodes)
        uncovered = set(range(region_map.n_regions)) - covered
        if uncovered:
            ap = auto_place_seeds_on_mesh(
                coordinates_fem=coords,
                elements_fem=mesh.elements_fem,
                node_region_map=region_map,
                f_img=f_img,
                g_img=g_img,
                mask=mask,
                winsize=int(para.winsize),
                search_radius=int(search_radius),
                config=AutoPlaceConfig(ncc_threshold=float(ncc_threshold)),
                adjacency=adjacency,
                skip_region_ids=frozenset(covered),
            )
            if ap.seed_set.seeds:
                auto_placed = len(ap.seed_set.seeds)
                seed_set = SeedSet(
                    seeds=seed_set.seeds + tuple(ap.seed_set.seeds),
                    ncc_threshold=seed_set.ncc_threshold,
                    max_bfs_depth=seed_set.max_bfs_depth,
                )
            for msg in ap.warnings:
                warnings.warn(f"seed auto-place: {msg}", UserWarning, stacklevel=2)

    # IC-GN reference-side context (same construction as matching.primitives:
    # gradient on the masked reference, raw reference for sampling).
    grad = compute_image_gradient(f_img * mask, mask, img_raw=f_img)
    ctx = local_icgn_precompute(coords, grad, f_img, para)

    try:
        result = propagate_from_seeds(
            ctx,
            seed_set,
            adjacency,
            f_img,
            g_img,
            search_radius=int(search_radius),
            tol=float(tol),
            node_region_map=region_map,
            mask=mask,
        )
    except SeedPropagationError as exc:
        warnings.warn(
            f"seed propagation failed ({exc}) — falling back to FFT seeding.",
            UserWarning,
            stacklevel=2,
        )
        return None

    u0 = np.empty(2 * n_nodes, dtype=np.float64)
    u0[0::2] = result.U_2d[:, 0]
    u0[1::2] = result.U_2d[:, 1]
    if result.unsolved_nodes.size > 0:
        u0[2 * result.unsolved_nodes] = np.nan
        u0[2 * result.unsolved_nodes + 1] = np.nan

    n_solved = int(n_nodes - result.unsolved_nodes.size)
    n_region_nodes = int(sum(len(nodes) for nodes in region_map.region_node_lists))
    return SeedU0Result(
        u0=u0,
        n_nodes=n_nodes,
        n_solved=n_solved,
        n_region_nodes=n_region_nodes,
        n_regions=int(region_map.n_regions),
        n_seeds=int(result.n_seeds),
        auto_placed=int(auto_placed),
        rescued=int(len(result.rescued_seeds)),
        seed_ncc_min=float(result.seed_ncc_min),
        dropped=tuple((int(i), str(m)) for i, m in result.dropped_seeds),
    )
