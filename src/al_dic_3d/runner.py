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
from al_dic_3d.sequence import ArrayFrameProvider, StereoSequence
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
    winsize: int = 32
    winstepsize: int = 16
    winsize_min: int = 8
    stereo_search: int = 48
    use_global_step: bool = True
    admm_max_iter: int = 3
    fft_search: int = 20  # temporal FFT integer-search half-width (px)
    # Initial guess (F2): "seed" | "fft" | "previous". "seed" template-matches
    # the seed_point patch for the stereo offset + first-pair motion; without a
    # seed_point it falls back to "fft" with a warning (never blocks). Engine
    # mapping: al_dic_3d.matching.seed module docstring. Headless default stays
    # "fft" (pre-F2 behavior); the GUI draft defaults to "seed".
    init_guess: str = "fft"
    seed_point: tuple[float, float] | None = None  # (x, y) on LEFT frame 1
    temporal_gate_znssd: float = 1.0  # honesty gate on cumulative tracks; <=0 off
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
    seq = table.get("sequence", {})
    out = table.get("output", {})
    qual = table.get("quality", {})
    strain = table.get("strain", {})

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
        winsize=int(match.get("winsize", 32)),
        winstepsize=int(match.get("winstepsize", 16)),
        winsize_min=int(match.get("winsize_min", 8)),
        stereo_search=int(match.get("stereo_search", 48)),
        use_global_step=bool(match.get("use_global_step", True)),
        admm_max_iter=int(match.get("admm_max_iter", 3)),
        fft_search=int(match.get("fft_search", 20)),
        init_guess=init_guess,
        seed_point=seed_point,
        temporal_gate_znssd=float(match.get("temporal_gate_znssd", 1.0)),
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


def _load_gray(path: Path) -> NDArray[np.float64]:
    import cv2

    # IMREAD_UNCHANGED preserves the native bit depth (scientific DIC images are
    # often 16-bit or float); collapse any colour input to a single channel.
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"cannot read image: {path}")
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.shape[2] == 3 else img[..., 0]
    return img.astype(np.float64)


def _load_stream(
    spec: str | Sequence[str] | None, base: Path
) -> tuple[list[NDArray[np.float64]] | None, list[str] | None]:
    if spec is None:
        return None, None
    paths = _resolve_paths(spec, base)
    return [_load_gray(p) for p in paths], [p.name for p in paths]


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

        img = cv2.imread(str(cfg.refinement_mask), cv2.IMREAD_GRAYSCALE)
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

    ``stop`` is a cooperative-cancel poll: when it returns True the strategy
    aborts between stages/frames and the run raises ``RuntimeError("cancelled")``.
    """
    seq_base = cfg.base_dir  # image/mask specs resolve against the config-file dir

    rig = load_calibration(cfg.calibration_file, cfg.calibration_format)

    left_frames, left_names = _load_stream(cfg.left, seq_base)
    right_frames, right_names = _load_stream(cfg.right, seq_base)
    left_masks, _ = _load_stream(cfg.left_masks, seq_base)
    right_masks, _ = _load_stream(cfg.right_masks, seq_base)

    if cfg.roi_mask is not None:
        # Arbitrary-shape ROI (toolbox-drawn): its bounding box overrides the
        # rectangular roi, and — unless explicit per-frame left masks were
        # given, which take precedence — the mask applies as a constant left
        # mask on every frame (all geometry keys off the frame-1 reference).
        path = cfg.roi_mask if cfg.roi_mask.is_absolute() else seq_base / cfg.roi_mask
        roi_mask = _load_roi_mask(path, left_frames[0].shape)
        cfg = replace(cfg, roi=_mask_bbox(roi_mask))
        if left_masks is None:
            left_masks = [roi_mask.astype(np.float64)] * len(left_frames)

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
            cfg.cam_left: ArrayFrameProvider(left_frames),
            cfg.cam_right: ArrayFrameProvider(right_frames),
        },
        masks=masks,
        names=names,
    )
    seq.validate()

    img_h, img_w = seq.providers[cfg.cam_left].shape
    mesh_L = _build_reference_mesh(cfg, img_h, img_w, masks.get(cfg.cam_left))

    strategy_cls = get_strategy(cfg.strategy)
    try:
        strategy = strategy_cls(
            winsize=cfg.winsize,
            winstepsize=cfg.winstepsize,
            winsize_min=cfg.winsize_min,
            stereo_search=cfg.stereo_search,
            use_global_step=cfg.use_global_step,
            admm_max_iter=cfg.admm_max_iter,
            fft_search=cfg.fft_search,
            temporal_gate_znssd=cfg.temporal_gate_znssd,
        )
    except TypeError:
        strategy = strategy_cls()  # strategy without tunable matching scale

    corr_cfg = CorrespondenceConfig(
        strategy=cfg.strategy,
        reference_mode=cfg.reference_mode,
        disparity_offset=cfg.disparity_offset,
        init_guess=cfg.init_guess,  # type: ignore[arg-type]
        seed_point=cfg.seed_point,
    )
    cs = strategy.compute(seq, rig, mesh_L, corr_cfg, progress=progress, stop=stop)
    if stop is not None and stop():
        raise RuntimeError("cancelled")
    ref_coords = np.asarray(mesh_L.coordinates_fem, dtype=np.float64)

    # Optional robustness gates: ZNSSD on the correspondence (pre-reconstruction),
    # then reprojection + 3D-outlier on the reconstruction (post).
    if cfg.quality_gate:
        cs = apply_znssd_gate(cs, cfg.znssd_max)
    rec = reconstruct_correspondence(cs, rig, cam_left=cfg.cam_left, cam_right=cfg.cam_right)
    if cfg.quality_gate:
        focals = [
            f
            for cam in (cfg.cam_left, cfg.cam_right)
            for f in (rig.cameras[cam].fx, rig.cameras[cam].fy)
        ]
        max_reproj_norm = cfg.reproj_max_px / float(np.mean(focals))  # px -> normalized
        rec = apply_reproj_gate(rec, max_reproj_norm)
        rec = remove_3d_outliers(rec, ref_coords, threshold=cfg.outlier_threshold)

    strain = None
    if cfg.compute_strain:
        strain = compute_surface_strain(
            rec,
            ref_coords,
            strain_size=cfg.strain_size,
            winstepsize=cfg.winstepsize,
            smooth_sigma=cfg.strain_smooth_sigma,
        )

    tracked = int((rec.source != 3).sum())  # 3 == INVALID
    meta = {
        "strategy": cfg.strategy,
        "n_frames": cs.n_frames,
        "n_pts": cs.n_pts,
        "n_tracked_positions": tracked,
        "quality_gate": cfg.quality_gate,
        "compute_strain": cfg.compute_strain,
        "image_size": (img_h, img_w),
        "base_dir": str(seq_base),
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


def _arrays(result: RunResult) -> dict:
    """The unified archive: GUI selection schema + correspondence extras.

    Built on :func:`al_dic_3d.export.tables.selected_arrays` with ALL field ids
    (strategy / ref_coords / points3D / reproj_error / source + one
    ``(n_frames, n_pts)`` stack per field: U, V, W, mag, exx, ...), merged with
    the correspondence extras ``xL`` / ``xR`` / ``quality``. The LEGACY keys
    (``displacement3D``, ``strain_<name>`` incl. dwdx/dwdy, ``n_frames``,
    ``n_pts``) are still written so parity tools keep reading — the archive is
    a SUPERSET of both the old CLI layout and the GUI export schema.
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
            arrays[f"strain_{name}"] = getattr(result.strain, name)
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
    paths: dict[str, Path] = {
        "params": export_params(cfg.output_dir, prefix, ts, result, extra=asdict(cfg))
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
