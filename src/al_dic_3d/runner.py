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
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import tomllib
from numpy.typing import NDArray

from al_dic_3d.calibration import load_calibration
from al_dic_3d.matching import CorrespondenceConfig, apply_znssd_gate, get_strategy
from al_dic_3d.matching.primitives import make_local_dicpara
from al_dic_3d.matching.temporal import build_grid_mesh
from al_dic_3d.reconstruct import (
    Reconstruction3D,
    apply_reproj_gate,
    reconstruct_correspondence,
    remove_3d_outliers,
)
from al_dic_3d.sequence import ArrayFrameProvider, StereoSequence
from al_dic_3d.strain3d import STRAIN_FIELDS, compute_surface_strain

ProgressFn = Callable[[float, str], None]


@dataclass(frozen=True)
class RunConfig:
    """Parsed + validated ``config.toml`` for a headless run.

    Image/mask specs are either a glob string (sorted) or an explicit list; the
    ROI is ``(xmin, xmax, ymin, ymax)`` in pixels. Matching-scale fields are
    forwarded to the strategy so a run can match a MATLAB baseline's parameters.
    """

    calibration_file: Path
    calibration_format: str
    left: str | list[str]
    right: str | list[str]
    roi: tuple[int, int, int, int]
    output_dir: Path
    left_masks: str | list[str] | None = None
    right_masks: str | list[str] | None = None
    strategy: str = "track_both"
    reference_mode: str = "accumulative"
    winsize: int = 32
    winstepsize: int = 16
    winsize_min: int = 8
    stereo_search: int = 48
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
    for key in ("xmin", "xmax", "ymin", "ymax"):
        if key not in roi_tbl:
            raise ValueError(f"config missing [roi].{key}")
    roi = (int(roi_tbl["xmin"]), int(roi_tbl["xmax"]), int(roi_tbl["ymin"]), int(roi_tbl["ymax"]))

    match = table.get("matching", {})
    offset = match.get("disparity_offset")
    disparity_offset = (float(offset[0]), float(offset[1])) if offset is not None else None
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
        output_dir=_resolve(str(out.get("dir", "results"))),
        left_masks=seq.get("left_mask"),
        right_masks=seq.get("right_mask"),
        strategy=str(match.get("strategy", "track_both")),
        reference_mode=str(match.get("reference_mode", "accumulative")),
        winsize=int(match.get("winsize", 32)),
        winstepsize=int(match.get("winstepsize", 16)),
        winsize_min=int(match.get("winsize_min", 8)),
        stereo_search=int(match.get("stereo_search", 48)),
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


def run_pipeline(cfg: RunConfig, progress: ProgressFn | None = None) -> RunResult:
    """Execute the full headless correspondence + reconstruction pipeline."""
    seq_base = cfg.base_dir  # image/mask specs resolve against the config-file dir

    rig = load_calibration(cfg.calibration_file, cfg.calibration_format)

    left_frames, left_names = _load_stream(cfg.left, seq_base)
    right_frames, right_names = _load_stream(cfg.right, seq_base)
    left_masks, _ = _load_stream(cfg.left_masks, seq_base)
    right_masks, _ = _load_stream(cfg.right_masks, seq_base)

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
    para = make_local_dicpara(
        img_size=(img_h, img_w),
        roi=cfg.roi,
        winsize=cfg.winsize,
        winstepsize=cfg.winstepsize,
        winsize_min=cfg.winsize_min,
    )
    mesh_L = build_grid_mesh(para, img_h, img_w)

    strategy_cls = get_strategy(cfg.strategy)
    try:
        strategy = strategy_cls(
            winsize=cfg.winsize,
            winstepsize=cfg.winstepsize,
            winsize_min=cfg.winsize_min,
            stereo_search=cfg.stereo_search,
        )
    except TypeError:
        strategy = strategy_cls()  # strategy without tunable matching scale

    corr_cfg = CorrespondenceConfig(
        strategy=cfg.strategy,
        reference_mode=cfg.reference_mode,
        disparity_offset=cfg.disparity_offset,
    )
    cs = strategy.compute(seq, rig, mesh_L, corr_cfg, progress=progress)
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


def _arrays(result: RunResult) -> dict:
    cs = result.correspondence
    rec = result.reconstruction
    arrays = {
        "strategy": result.strategy,
        "ref_coords": result.ref_coords,
        "xL": cs.xL,
        "xR": cs.xR,
        "quality": cs.quality,
        "source": cs.source,
        "points3D": rec.points,
        "displacement3D": rec.displacement,
        "reproj_error": rec.reproj_error,
        "n_frames": np.int64(cs.n_frames),
        "n_pts": np.int64(cs.n_pts),
    }
    if result.strain is not None:
        for name in STRAIN_FIELDS:
            arrays[f"strain_{name}"] = getattr(result.strain, name)
    return arrays


def write_results(result: RunResult, cfg: RunConfig) -> dict[str, Path]:
    """Write ``<output_dir>/<prefix>.npz`` and ``.mat``; return the two paths."""
    import scipy.io

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    arrays = _arrays(result)
    npz_path = cfg.output_dir / f"{cfg.output_prefix}.npz"
    mat_path = cfg.output_dir / f"{cfg.output_prefix}.mat"
    np.savez_compressed(npz_path, **arrays)
    scipy.io.savemat(str(mat_path), arrays, do_compression=True)
    return {"npz": npz_path, "mat": mat_path}
