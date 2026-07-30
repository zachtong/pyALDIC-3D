"""Headless run orchestration (Phase 1 item 6): ``config.toml`` -> results.

Glue that assembles the compute modules into one batch pipeline —
calibration -> sequence -> matching (strategy) -> reconstruct — and serializes
the result to ``.npz`` + ``.mat`` (the parity-comparison payload). Kept separate
from :mod:`al_dic_3d.cli` so the whole pipeline is unit-testable without spawning
a subprocess.

Qt-free. Uses the public strategy registry (``get_strategy``), so it is workflow
glue, not one of the mode-/strategy-agnostic downstream compute modules.
"""

from __future__ import annotations

import glob
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import tomllib
from numpy.typing import NDArray

from al_dic_3d import memcheck
from al_dic_3d.calibration import load_calibration
from al_dic_3d.matching import CorrespondenceConfig, apply_znssd_gate, get_strategy
from al_dic_3d.matching.primitives import make_dicpara
from al_dic_3d.matching.temporal import build_grid_mesh
from al_dic_3d.reconstruct import (
    Reconstruction3D,
    apply_reproj_gate,
    reconstruct_correspondence,
    remove_3d_outliers,
)
from al_dic_3d.sequence import LazyFrameProvider, LazyMaskList, StereoSequence, load_gray
from al_dic_3d.strain3d import STRAIN_FIELDS, compute_surface_strain

if TYPE_CHECKING:
    from al_dic.core.data_structures import DICMesh

ProgressFn = Callable[[float, str], None]


@dataclass(frozen=True)
class RunConfig:
    """Parsed + validated ``config.toml`` for a headless run.

    Image/mask specs are either a glob string (sorted) or an explicit list; the
    ROI is ``(xmin, xmax, ymin, ymax)`` in pixels. Matching-scale fields are
    forwarded to the strategy so a run can match a MATLAB baseline's parameters.

    ``roi_mask`` (``[roi].mask`` in TOML) is an arbitrary-shape ROI mask image
    drawn on the LEFT camera, frame 1. When set, its ``> 0`` bounding box
    OVERRIDES ``roi``, and — unless explicit ``left_masks`` are given, which
    take precedence — the mask is applied as a constant per-frame left mask
    (correct for the frame-1 reference mesh; accumulative tracking keys every
    frame off that same reference geometry).
    """

    calibration_file: Path
    calibration_format: str
    left: str | list[str]
    right: str | list[str]
    roi: tuple[int, int, int, int]
    output_dir: Path
    roi_mask: Path | None = None
    left_masks: str | list[str] | None = None
    right_masks: str | list[str] | None = None
    strategy: str = "track_both"
    reference_mode: str = "accumulative"
    # Q5 reference-update policy (incremental mode only): "every_frame"
    # (default) | "every_n" | "custom". Maps to the engine FrameSchedule via
    # al_dic_3d.matching.temporal.build_frame_schedule. ref_update_frames is a
    # 0-based reference-frame index list for "custom".
    ref_update_mode: str = "every_frame"
    ref_update_n: int = 2
    ref_update_frames: tuple[int, ...] | None = None
    winsize: int = 32
    winstepsize: int = 16
    winsize_min: int = 8
    stereo_search: int = 48
    use_global_step: bool = True
    admm_max_iter: int = 3
    fft_search: int = 20  # temporal FFT integer-search half-width (px)
    # Q8: auto-enlarge the FFT search region when the integer peak is clipped
    # at the region boundary (engine fft_auto_expand_search; default on).
    fft_auto_expand: bool = True
    # Initial guess (F2): "seed" | "fft" | "previous". "seed" template-matches
    # the seed_point patch for the stereo offset + first-pair motion; without a
    # seed_point it falls back to "fft" with a warning (never blocks). Engine
    # mapping: al_dic_3d.matching.seed module docstring. Headless default stays
    # "fft" (pre-F2 behavior); the GUI draft defaults to "seed".
    init_guess: str = "fft"
    seed_point: tuple[float, float] | None = None  # (x, y) on LEFT frame 1
    # Batch S — multi-seed Starting Points: the full list of LEFT frame-1 seed
    # pixels driving F-aware propagation. ``seed_point`` stays the back-compat
    # primary (= seed_points[0]); when only ``seed_point`` is set it acts as a
    # one-element list. TOML accepts either ``seed_point = [x, y]`` or
    # ``seed_points = [[x1,y1], [x2,y2], ...]``.
    seed_points: tuple[tuple[float, float], ...] = ()
    temporal_gate_znssd: float = 1.0  # honesty gate on cumulative tracks; <=0 off
    # P3.6 opt-in: track both cameras concurrently (track_both strategy).
    # ~2x faster on the numba/numpy-heavy engine, doubles peak memory.
    # TOML: [matching].parallel_cameras. Results are identical either way.
    parallel_cameras: bool = False
    refine_inner: bool = False
    refine_outer: bool = False
    refinement_level: int = 1
    refinement_mask: Path | None = None
    disparity_offset: tuple[float, float] | None = None
    quality_gate: bool = False
    znssd_max: float = 0.5
    reproj_max_px: float = 2.0
    outlier_threshold: float = 3.0
    compute_strain: bool = False
    strain_size: int = 5
    strain_smooth_sigma: float = 0.0
    # Skip the fail-fast RAM pre-check (P1.4). TOML: [advanced].ignore_memory_check
    # (also accepted under [matching] for one-table configs).
    ignore_memory_check: bool = False
    output_prefix: str = "run"
    cam_left: str = "L"
    cam_right: str = "R"
    base_dir: Path = Path(".")  # config-file directory; image/mask specs resolve here


@dataclass(frozen=True)
class RunResult:
    """Everything one run produces: the correspondence, the 3D, and QC metadata."""

    strategy: str
    ref_coords: NDArray[np.float64]  # (n_pts, 2) frame-1 left mesh nodes
    correspondence: object  # CorrespondenceSet (avoid importing to stay light)
    reconstruction: Reconstruction3D
    strain: object | None = None  # StrainResult3D if computed, else None
    meta: dict = field(default_factory=dict)


# --- config loading ----------------------------------------------------------


def _require(table: dict, section: str, key: str):
    if section not in table or key not in table[section]:
        raise ValueError(f"config missing [{section}].{key}")
    return table[section][key]


def load_config(path: str | Path) -> RunConfig:
    """Load and validate a ``config.toml`` into a :class:`RunConfig`.

    Relative ``calibration.file`` / ``output.dir`` paths resolve against the
    config file's own directory, so a config works regardless of the CWD.
    """
    path = Path(path)
    with path.open("rb") as fh:
        table = tomllib.load(fh)
    base = path.resolve().parent

    def _resolve(p: str) -> Path:
        pp = Path(p)
        return pp if pp.is_absolute() else base / pp

    roi_tbl = table.get("roi", {})
    roi_mask = _resolve(str(roi_tbl["mask"])) if "mask" in roi_tbl else None
    if roi_mask is None:
        for key in ("xmin", "xmax", "ymin", "ymax"):
            if key not in roi_tbl:
                raise ValueError(f"config missing [roi].{key}")
    # With [roi].mask the pixel bounds are optional — the mask's bounding box
    # overrides them in run_pipeline (any explicit values are placeholders).
    roi = (
        int(roi_tbl.get("xmin", 0)),
        int(roi_tbl.get("xmax", 0)),
        int(roi_tbl.get("ymin", 0)),
        int(roi_tbl.get("ymax", 0)),
    )

    match = table.get("matching", {})
    offset = match.get("disparity_offset")
    disparity_offset = (float(offset[0]), float(offset[1])) if offset is not None else None
    init_guess = str(match.get("init_guess", "fft"))
    from al_dic_3d.matching.seed import INIT_GUESS_MODES

    if init_guess not in INIT_GUESS_MODES:
        raise ValueError(
            f"[matching].init_guess must be one of {INIT_GUESS_MODES}, got {init_guess!r}"
        )
    seed = match.get("seed_point")
    seed_point = (float(seed[0]), float(seed[1])) if seed is not None else None
    seed_pts_raw = match.get("seed_points")
    if seed_pts_raw is not None:
        seed_points = tuple((float(p[0]), float(p[1])) for p in seed_pts_raw)
    elif seed_point is not None:
        seed_points = (seed_point,)
    else:
        seed_points = ()
    # Keep the primary seed in sync so single-seed consumers (and the readback)
    # always see seed_points[0] as seed_point.
    if seed_point is None and seed_points:
        seed_point = seed_points[0]
    seq = table.get("sequence", {})
    out = table.get("output", {})
    qual = table.get("quality", {})
    strain = table.get("strain", {})
    advanced = table.get("advanced", {})

    return RunConfig(
        calibration_file=_resolve(str(_require(table, "calibration", "file"))),
        calibration_format=str(_require(table, "calibration", "format")),
        left=_require(table, "sequence", "left"),
        right=_require(table, "sequence", "right"),
        roi=roi,
        roi_mask=roi_mask,
        output_dir=_resolve(str(out.get("dir", "results"))),
        left_masks=seq.get("left_mask"),
        right_masks=seq.get("right_mask"),
        strategy=str(match.get("strategy", "track_both")),
        reference_mode=str(match.get("reference_mode", "accumulative")),
        ref_update_mode=str(match.get("ref_update_mode", "every_frame")),
        ref_update_n=int(match.get("ref_update_n", 2)),
        ref_update_frames=(
            tuple(int(f) for f in match["ref_update_frames"])
            if match.get("ref_update_frames") is not None
            else None
        ),
        winsize=int(match.get("winsize", 32)),
        winstepsize=int(match.get("winstepsize", 16)),
        winsize_min=int(match.get("winsize_min", 8)),
        stereo_search=int(match.get("stereo_search", 48)),
        use_global_step=bool(match.get("use_global_step", True)),
        admm_max_iter=int(match.get("admm_max_iter", 3)),
        fft_search=int(match.get("fft_search", 20)),
        fft_auto_expand=bool(match.get("fft_auto_expand", True)),
        init_guess=init_guess,
        seed_point=seed_point,
        seed_points=seed_points,
        temporal_gate_znssd=float(match.get("temporal_gate_znssd", 1.0)),
        parallel_cameras=bool(match.get("parallel_cameras", False)),
        refine_inner=bool(match.get("refine_inner", False)),
        refine_outer=bool(match.get("refine_outer", False)),
        refinement_level=int(match.get("refinement_level", 1)),
        refinement_mask=(
            _resolve(str(match["refinement_mask"])) if "refinement_mask" in match else None
        ),
        disparity_offset=disparity_offset,
        quality_gate=bool(qual.get("enabled", False)),
        znssd_max=float(qual.get("znssd_max", 0.5)),
        reproj_max_px=float(qual.get("reproj_max_px", 2.0)),
        outlier_threshold=float(qual.get("outlier_threshold", 3.0)),
        compute_strain=bool(strain.get("enabled", False)),
        strain_size=int(strain.get("strain_size", 5)),
        strain_smooth_sigma=float(strain.get("smooth_sigma", 0.0)),
        ignore_memory_check=bool(
            advanced.get("ignore_memory_check", match.get("ignore_memory_check", False))
        ),
        output_prefix=str(out.get("prefix", "run")),
        cam_left=str(seq.get("cam_left", "L")),
        cam_right=str(seq.get("cam_right", "R")),
        base_dir=base,
    )


# --- image loading -----------------------------------------------------------


def _natural_key(name: str) -> list:
    """Natural-sort key: split into text/number chunks, compare numbers numerically.

    So ``frame_2`` sorts before ``frame_10`` — plain lexicographic ``sorted`` would
    scramble non-zero-padded frame sequences (``1, 10, 100, 11, ..., 2``) into the
    wrong temporal order, silently corrupting the cumulative displacement.
    """
    return [int(t) if t.isdigit() else t.lower() for t in re.findall(r"\d+|\D+", name)]


def _resolve_paths(spec: str | Sequence[str], base: Path) -> list[Path]:
    """Turn a glob string or explicit list into a naturally-sorted list of paths."""
    if isinstance(spec, str):
        matches = sorted(glob.glob(str(base / spec)), key=lambda p: _natural_key(Path(p).name))
        if not matches:
            raise FileNotFoundError(f"no files match {spec!r} under {base}")
        return [Path(m) for m in matches]
    paths = [Path(p) if Path(p).is_absolute() else base / p for p in spec]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"listed file does not exist: {p}")
    return paths


# Grayscale decode lives in sequence/lazy.py (shared with the lazy providers);
# kept under the old private name for the runner's single-image loads.
_load_gray = load_gray


def _open_stream(
    spec: str | Sequence[str] | None, base: Path
) -> tuple[LazyFrameProvider | None, list[str] | None]:
    """Resolve an image spec into a LAZY frame provider + file names (P1.2).

    Nothing is decoded here: frames stream from disk on demand behind a small
    LRU, so peak memory no longer scales with sequence length.
    """
    if spec is None:
        return None, None
    paths = _resolve_paths(spec, base)
    return LazyFrameProvider(paths), [p.name for p in paths]


def _open_masks(spec: str | Sequence[str] | None, base: Path) -> LazyMaskList | None:
    """Resolve a mask spec into a lazily-decoded per-frame mask sequence."""
    if spec is None:
        return None
    return LazyMaskList(_resolve_paths(spec, base))


# --- pipeline ----------------------------------------------------------------


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


def _build_reference_mesh(cfg: RunConfig, img_h: int, img_w: int, left_masks) -> DICMesh:
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


def _load_roi_mask(path: Path, img_shape: tuple[int, int]) -> NDArray[np.bool_]:
    """Load ``cfg.roi_mask`` as a boolean array; validate shape and non-emptiness."""
    mask = _load_gray(path) > 0
    if mask.shape != img_shape:
        raise ValueError(
            f"roi_mask shape {mask.shape} does not match the left images {img_shape}: {path}"
        )
    if not mask.any():
        raise ValueError(f"roi_mask is empty (no pixels > 0): {path}")
    return mask


def _mask_bbox(mask: NDArray[np.bool_]) -> tuple[int, int, int, int]:
    """``(xmin, xmax, ymin, ymax)`` bounding box of the True pixels."""
    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def run_pipeline(
    cfg: RunConfig,
    progress: ProgressFn | None = None,
    stop: Callable[[], bool] | None = None,
) -> RunResult:
    """Execute the full headless correspondence + reconstruction pipeline.

    ``stop`` is a cooperative-cancel poll. When it trips mid-run the frames
    tracked so far are KEPT (engine 0.7 partial-results semantics): the run
    returns a :class:`RunResult` whose meta records ``stopped_early`` /
    ``stopped_at_frame`` / ``stop_reason`` and whose later frames are all-NaN.
    Only when nothing beyond the reference frame survived does the run raise
    ``RuntimeError("cancelled")``.
    """
    seq_base = cfg.base_dir  # image/mask specs resolve against the config-file dir

    rig = load_calibration(cfg.calibration_file, cfg.calibration_format)

    # LAZY streams (P1.2): only frame 0 is decoded up front (for the image
    # shape); everything else streams from disk behind bounded LRUs.
    provider_left, left_names = _open_stream(cfg.left, seq_base)
    provider_right, right_names = _open_stream(cfg.right, seq_base)
    left_masks = _open_masks(cfg.left_masks, seq_base)
    right_masks = _open_masks(cfg.right_masks, seq_base)
    img_h, img_w = provider_left.shape
    n_frames = len(provider_left)

    if cfg.roi_mask is not None:
        # Arbitrary-shape ROI (toolbox-drawn): its bounding box overrides the
        # rectangular roi, and — unless explicit per-frame left masks were
        # given, which take precedence — the mask applies as a constant left
        # mask on every frame (ONE shared array: all geometry keys off the
        # frame-1 reference, and every consumer copies before writing).
        path = cfg.roi_mask if cfg.roi_mask.is_absolute() else seq_base / cfg.roi_mask
        roi_mask = _load_roi_mask(path, (img_h, img_w))
        cfg = replace(cfg, roi=_mask_bbox(roi_mask))
        if left_masks is None:
            left_masks = [roi_mask.astype(np.float64)] * n_frames

    # Fail-fast RAM pre-check (P1.4) BEFORE any stack touches memory: project
    # the run's peak from the sequence geometry and refuse runs that would
    # swap/OOM. [advanced].ignore_memory_check = true overrides.
    if not cfg.ignore_memory_check:
        xmin, xmax, ymin, ymax = cfg.roi
        step = max(1, cfg.winstepsize)
        n_pts_est = max(1, (max(0, xmax - xmin) // step + 1) * (max(0, ymax - ymin) // step + 1))
        memcheck.check_run_memory(
            n_frames,
            img_h,
            img_w,
            n_cameras=2,
            lazy=True,
            n_pts=n_pts_est,
            parallel=cfg.parallel_cameras,  # P3.6: both engine transients live
        )

    masks: dict = {}
    if left_masks is not None:
        masks[cfg.cam_left] = left_masks
    if right_masks is not None:
        masks[cfg.cam_right] = right_masks
    names: dict = {}
    if left_names is not None:
        names[cfg.cam_left] = left_names
    if right_names is not None:
        names[cfg.cam_right] = right_names

    seq = StereoSequence(
        providers={
            cfg.cam_left: provider_left,
            cfg.cam_right: provider_right,
        },
        masks=masks,
        names=names,
    )
    seq.validate()
    mesh_L = _build_reference_mesh(cfg, img_h, img_w, masks.get(cfg.cam_left))

    # Batch C item 1/5: cut the external frame-1 mesh at any thin crack barrier
    # (mark_bridging) so FEM/global-step elements do not bridge the crack.
    # crack_aware gates crack-aware strain + rendering; crack-free = byte-identical.
    from al_dic_3d.matching.crack_mesh import cut_mesh_at_barriers, mask_cuts_mesh

    left_seq = masks.get(cfg.cam_left)
    left_mask0 = (
        np.ascontiguousarray(np.asarray(left_seq[0], dtype=np.float64))
        if left_seq is not None
        else None
    )
    crack_aware = mask_cuts_mesh(mesh_L, left_mask0)
    if crack_aware:
        mesh_L = cut_mesh_at_barriers(mesh_L, left_mask0)

    strategy_cls = get_strategy(cfg.strategy)
    kwargs = dict(
        winsize=cfg.winsize,
        winstepsize=cfg.winstepsize,
        winsize_min=cfg.winsize_min,
        stereo_search=cfg.stereo_search,
        use_global_step=cfg.use_global_step,
        admm_max_iter=cfg.admm_max_iter,
        fft_search=cfg.fft_search,
        fft_auto_expand=cfg.fft_auto_expand,
        temporal_gate_znssd=cfg.temporal_gate_znssd,
        parallel_cameras=cfg.parallel_cameras,
    )
    try:
        # Forward only the kwargs this strategy's constructor accepts (P3.6:
        # parallel_cameras exists on track_both only — an unfiltered TypeError
        # fallback would silently drop ALL matching-scale parameters).
        import inspect

        accepted = inspect.signature(strategy_cls.__init__).parameters
        strategy = strategy_cls(**{k: v for k, v in kwargs.items() if k in accepted})
    except TypeError:
        strategy = strategy_cls()  # strategy without tunable matching scale

    # Q5: an explicit reference-update schedule (incremental every_n / custom);
    # None keeps the engine's reference_mode-derived default. Both cameras
    # track the full sequence, so one schedule serves L and R alike.
    from al_dic_3d.matching.temporal import build_frame_schedule

    schedule = build_frame_schedule(
        cfg.reference_mode,
        n_frames,
        ref_update_mode=cfg.ref_update_mode,
        ref_update_n=cfg.ref_update_n,
        ref_update_frames=cfg.ref_update_frames,
    )
    corr_cfg = CorrespondenceConfig(
        strategy=cfg.strategy,
        reference_mode=cfg.reference_mode,
        schedule_L=schedule,
        schedule_R=schedule,
        disparity_offset=cfg.disparity_offset,
        init_guess=cfg.init_guess,  # type: ignore[arg-type]
        seed_point=cfg.seed_point,
        seed_points=tuple(getattr(cfg, "seed_points", ()) or ()),
    )
    cs = strategy.compute(seq, rig, mesh_L, corr_cfg, progress=progress, stop=stop)
    # R2 (engine 0.7 partial-results): a cooperative cancel mid-run RETURNS a
    # partial CorrespondenceSet (frames [0, stopped_at_frame) kept, the rest
    # NaN). Keep it when at least one DEFORMED frame survived in both cameras;
    # with nothing beyond the reference there is nothing worth keeping and the
    # run cancels outright (the pre-0.7 contract). A complete set that merely
    # RACED the stop (stopped_early False) is likewise kept, never discarded.
    stopped_early = bool(getattr(cs, "stopped_early", False))
    stopped_at = getattr(cs, "stopped_at_frame", None)
    stop_reason = str(getattr(cs, "stop_reason", "") or "")
    if stopped_early and (stopped_at is None or stopped_at <= 1):
        raise RuntimeError("cancelled")
    ref_coords = np.asarray(mesh_L.coordinates_fem, dtype=np.float64)

    def _n_valid_positions(points) -> int:
        return int(np.isfinite(points).all(axis=2).sum())

    def _n_valid_pairs(c) -> int:
        return int((np.isfinite(c.xL).all(axis=2) & np.isfinite(c.xR).all(axis=2)).sum())

    # Optional robustness gates: ZNSSD on the correspondence (pre-reconstruction),
    # then reprojection + 3D-outlier on the reconstruction (post). Every gate's
    # demotion COUNT is recorded (F3.1) — a gate must never eat points silently.
    gates: dict[str, int] = {}
    if cfg.quality_gate:
        n0 = _n_valid_pairs(cs)
        cs = apply_znssd_gate(cs, cfg.znssd_max)
        gates["znssd_demoted"] = n0 - _n_valid_pairs(cs)
    rec = reconstruct_correspondence(cs, rig, cam_left=cfg.cam_left, cam_right=cfg.cam_right)
    if cfg.quality_gate:
        focals = [
            f
            for cam in (cfg.cam_left, cfg.cam_right)
            for f in (rig.cameras[cam].fx, rig.cameras[cam].fy)
        ]
        max_reproj_norm = cfg.reproj_max_px / float(np.mean(focals))  # px -> normalized
        n0 = _n_valid_positions(rec.points)
        rec = apply_reproj_gate(rec, max_reproj_norm)
        n1 = _n_valid_positions(rec.points)
        rec = remove_3d_outliers(rec, ref_coords, threshold=cfg.outlier_threshold)
        gates["reproj_demoted"] = n0 - n1
        gates["outliers_removed"] = n1 - _n_valid_positions(rec.points)

    strain = None
    if cfg.compute_strain and not stopped_early:
        # Skipped on a partial run: the stop is already tripped and the strain
        # loop's own cooperative cancel would abort at frame 0 anyway.
        try:
            strain = compute_surface_strain(
                rec,
                ref_coords,
                strain_size=cfg.strain_size,
                winstepsize=cfg.winstepsize,
                smooth_sigma=cfg.strain_smooth_sigma,
                # Batch C items 2/3: crack-aware neighbour exclusion + crack-trim,
                # only once a thin barrier was detected (else byte-identical).
                roi_mask=left_mask0 if crack_aware else None,
                edge_trim_alpha=0.7 if crack_aware else 0.0,
                progress_cb=progress,  # P3.5: per-frame ticks + cooperative cancel
                stop_event=stop,
            )
        except RuntimeError as exc:
            if "cancelled" not in str(exc):
                raise
            # A cancel DURING strain must not discard the finished displacement
            # / 3D results (R2 partial-keeping): drop strain, note the reason.
            strain = None
            stop_reason = stop_reason or (
                "Cancelled during strain computation — displacement results are complete."
            )

    # F3.1: the post-run failure accounting — per-stage rows from the strategy
    # plus a summary over the FINAL reconstructed points. JSON-serializable so
    # it survives the session file and the parameters export.
    from al_dic_3d.matching.diagnostics import summarize_run

    summary = summarize_run(cs, rec.points)

    tracked = int((rec.source != 3).sum())  # 3 == INVALID
    meta = {
        "strategy": cfg.strategy,
        "n_frames": cs.n_frames,
        "n_pts": cs.n_pts,
        "n_tracked_positions": tracked,
        "quality_gate": cfg.quality_gate,
        "compute_strain": cfg.compute_strain,
        # Batch C: ROI carried a thin crack barrier -> mesh cut + crack-aware
        # strain/rendering (item 5 GUI indicator reads this).
        "crack_aware": bool(crack_aware),
        "image_size": (img_h, img_w),
        "base_dir": str(seq_base),
        "diagnostics": [dict(r) for r in cs.diagnostics],
        "summary": summary.to_meta(),
        "gates": gates,
        # R2 partial-run bookkeeping (engine 0.7): frames [0, stopped_at_frame)
        # are kept, later frames are NaN. stop_reason is also set (with
        # stopped_early False) when only the strain pass was cancelled.
        "stopped_early": stopped_early,
        "stopped_at_frame": None if stopped_at is None else int(stopped_at),
        "stop_reason": stop_reason,
    }
    return RunResult(
        strategy=cfg.strategy,
        ref_coords=ref_coords,
        correspondence=cs,
        reconstruction=rec,
        strain=strain,
        meta=meta,
    )


# --- output ------------------------------------------------------------------


RESULT_FORMATS = ("npz", "mat", "csv", "ply", "vtu")

# Archive layout version recorded in the parameters JSON. Schema 2 (P3.3)
# dropped the doubled ``strain_<name>`` aliases: strain stacks live ONLY under
# their canonical GUI-selection ids (``exx`` ... ``von_mises`` plus ``dwdx`` /
# ``dwdy``). Schema 3 (Batch C item 3) adds an OPTIONAL ``strain_valid``
# ``(n_frames, n_pts)`` bool stack (edge-trim UNION crack-trim) alongside the
# now-DENSE strain values; readers that ignore unknown keys are unaffected.
ARCHIVE_SCHEMA = 3


def _arrays(result: RunResult) -> dict:
    """The unified archive: GUI selection schema + correspondence extras.

    Built on :func:`al_dic_3d.export.tables.selected_arrays` with ALL field ids
    (strategy / ref_coords / points3D / reproj_error / source + one
    ``(n_frames, n_pts)`` stack per field: U, V, W, mag, exx, ...), merged with
    the correspondence extras ``xL`` / ``xR`` / ``quality`` and the LEGACY keys
    ``displacement3D`` / ``n_frames`` / ``n_pts`` that parity tools read.
    Schema 2 (see :data:`ARCHIVE_SCHEMA`): ONE canonical key per strain field —
    ``dwdx`` / ``dwdy`` (not in the GUI picker) are added under their bare
    names and the old ``strain_<name>`` duplicates are gone.
    """
    from al_dic_3d.export import DISPLACEMENT_IDS, STRAIN_IDS, selected_arrays

    cs = result.correspondence
    arrays = selected_arrays(result, [*DISPLACEMENT_IDS, *STRAIN_IDS])
    arrays.update(
        {
            "xL": cs.xL,
            "xR": cs.xR,
            "quality": cs.quality,
            "displacement3D": result.reconstruction.displacement,
            "n_frames": np.int64(cs.n_frames),
            "n_pts": np.int64(cs.n_pts),
        }
    )
    if result.strain is not None:
        for name in STRAIN_FIELDS:
            arrays.setdefault(name, getattr(result.strain, name))
        # Schema 3: DENSE strain values + an optional validity stack (edge-trim
        # UNION crack-trim). Absent when trimming/crack-awareness was off.
        if getattr(result.strain, "strain_valid", None) is not None:
            arrays.setdefault("strain_valid", np.asarray(result.strain.strain_valid))
    return arrays


def write_results(
    result: RunResult, cfg: RunConfig, formats: Sequence[str] = ("npz", "mat")
) -> dict[str, Path]:
    """Write the run outputs under ``cfg.output_dir``; return format -> path.

    ``npz`` / ``mat`` carry the unified SUPERSET archive (see :func:`_arrays`)
    at the fixed ``<prefix>.npz`` / ``<prefix>.mat`` paths that the parity
    tooling reads. ``csv`` / ``ply`` / ``vtu`` route through the export package
    into ``<prefix>_{fmt}_{timestamp}`` folders — a fresh timestamp per call,
    so repeated runs never overwrite them. A ``<prefix>_parameters_{ts}.json``
    recording the full RunConfig is ALWAYS written (key ``"params"``).
    """
    from dataclasses import asdict

    from al_dic_3d.export import (
        DISPLACEMENT_IDS,
        STRAIN_IDS,
        export_csv_frames,
        export_params,
        export_ply_frames,
        export_vtu_series,
        make_timestamp,
    )

    unknown = sorted(set(formats) - set(RESULT_FORMATS))
    if unknown:
        raise ValueError(f"unknown output format(s): {', '.join(unknown)}")

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = cfg.output_prefix
    ts = make_timestamp()
    fields = list(DISPLACEMENT_IDS) + (list(STRAIN_IDS) if result.strain is not None else [])
    # Schema 3: csv/vtu/ply also carry the DENSE strain's validity column when present.
    if result.strain is not None and getattr(result.strain, "strain_valid", None) is not None:
        fields.append("strain_valid")
    # archive_schema documents the npz/mat key layout (P3.3 alias removal).
    extra = {**asdict(cfg), "archive_schema": ARCHIVE_SCHEMA}
    paths: dict[str, Path] = {
        "params": export_params(cfg.output_dir, prefix, ts, result, extra=extra)
    }

    if "npz" in formats or "mat" in formats:
        arrays = _arrays(result)
        if "npz" in formats:
            paths["npz"] = cfg.output_dir / f"{prefix}.npz"
            np.savez_compressed(paths["npz"], **arrays)
        if "mat" in formats:
            import scipy.io

            paths["mat"] = cfg.output_dir / f"{prefix}.mat"
            scipy.io.savemat(str(paths["mat"]), arrays, do_compression=True)
    if "csv" in formats:
        csv_dir = cfg.output_dir / f"{prefix}_csv_{ts}"
        export_csv_frames(result, fields, csv_dir, prefix)
        paths["csv"] = csv_dir
    if "ply" in formats:
        export_ply_frames(cfg.output_dir, prefix, ts, result, fields)
        paths["ply"] = cfg.output_dir / f"{prefix}_ply_{ts}"
    if "vtu" in formats:
        export_vtu_series(cfg.output_dir, prefix, ts, result, fields)
        paths["vtu"] = cfg.output_dir / f"{prefix}_vtu_{ts}"
    return paths
