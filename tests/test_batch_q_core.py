"""Batch Q — Qt-free core: strain types (Q3), edge trim (Q4), reference-update
schedules (Q5), config-only sessions (Q7), CLI session launch (Q6), engine
knob plumbing (Q8)."""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.matching.contracts import TRACKED, CorrespondenceSet
from al_dic_3d.matching.primitives import make_dicpara
from al_dic_3d.matching.temporal import build_frame_schedule
from al_dic_3d.project import AppState3D, estimated_result_nbytes, save_session
from al_dic_3d.project.draft import ProjectDraft
from al_dic_3d.project.session import load_session, parse_session
from al_dic_3d.reconstruct import Reconstruction3D
from al_dic_3d.runner import RunConfig, RunResult
from al_dic_3d.strain3d import (
    STRAIN_TYPES,
    compute_surface_strain,
    edge_trim_mask,
    green_lagrange_strain,
    strain_tensor,
)

Z0 = 800.0


# ---------------------------------------------------------------------------
# Shared synthetic geometry (mirrors test_strain3d helpers)
# ---------------------------------------------------------------------------


def _grid(nx: int = 17, step_px: float = 16.0, step_mm: float = 2.0):
    ii, jj = np.meshgrid(np.arange(nx), np.arange(nx))
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * step_px + 40.0, jj * step_px + 40.0])
    xw = (ii - (nx - 1) / 2.0) * step_mm
    yw = (jj - (nx - 1) / 2.0) * step_mm
    interior = (ii >= 3) & (ii <= nx - 4) & (jj >= 3) & (jj <= nx - 4)
    return ref_2d, xw, yw, interior


def _recon(ref_3d: np.ndarray, disp1: np.ndarray) -> Reconstruction3D:
    points = np.stack([ref_3d, ref_3d + disp1])
    displacement = points - points[0][None]
    reproj = np.zeros(points.shape[:2])
    source = np.full(points.shape[:2], TRACKED, np.uint8)
    return Reconstruction3D(points, displacement, reproj, source)


def _tiny_result(n_frames: int = 2, nx: int = 5) -> RunResult:
    """A small, fully synthetic RunResult (session tests, no pipeline)."""
    ref_2d, xw, yw, _ = _grid(nx=nx)
    ref_3d = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    n_pts = ref_3d.shape[0]
    points = np.stack([ref_3d + 0.1 * k for k in range(n_frames)])
    rec = Reconstruction3D(
        points,
        points - points[0][None],
        np.zeros((n_frames, n_pts)),
        np.full((n_frames, n_pts), TRACKED, np.uint8),
    )
    x_img = np.stack([ref_2d] * n_frames)
    cs = CorrespondenceSet(
        strategy="track_both",
        xL=x_img.copy(),
        xR=x_img.copy(),
        quality=np.zeros((n_frames, n_pts)),
        source=np.full((n_frames, n_pts), TRACKED, np.uint8),
    )
    return RunResult(
        strategy="track_both",
        ref_coords=ref_2d,
        correspondence=cs,
        reconstruction=rec,
        strain=None,
        meta={"n_frames": n_frames},
    )


# ---------------------------------------------------------------------------
# Q3 — strain-type selection
# ---------------------------------------------------------------------------


def _uniaxial_coef(eps: float) -> np.ndarray:
    coef = np.zeros((1, 3, 3))
    coef[0, 0, 0] = eps  # dU/dx = eps
    return coef


def test_strain_tensor_uniaxial_analytic_all_types():
    eps = 0.05
    gl = strain_tensor(_uniaxial_coef(eps), "green_lagrange")
    assert gl["exx"][0] == pytest.approx(eps + 0.5 * eps**2, abs=1e-12)
    inf = strain_tensor(_uniaxial_coef(eps), "infinitesimal")
    assert inf["exx"][0] == pytest.approx(eps, abs=1e-12)
    ea = strain_tensor(_uniaxial_coef(eps), "almansi")
    assert ea["exx"][0] == pytest.approx(0.5 * (1.0 - 1.0 / (1.0 + eps) ** 2), abs=1e-12)
    for s in (gl, inf, ea):
        assert s["eyy"][0] == pytest.approx(0.0, abs=1e-12)
        assert s["exy"][0] == pytest.approx(0.0, abs=1e-12)


def test_strain_tensor_simple_shear_symmetrizes():
    # G = [[0, g], [0, 0]]: infinitesimal exy = g/2 exactly.
    g = 0.04
    coef = np.zeros((1, 3, 3))
    coef[0, 1, 0] = g  # dU/dy = g (row = derivative axis y, col = component U)
    inf = strain_tensor(coef, "infinitesimal")
    assert inf["exy"][0] == pytest.approx(g / 2.0, abs=1e-12)
    assert inf["exx"][0] == pytest.approx(0.0, abs=1e-12)


def test_green_lagrange_alias_matches_strain_tensor():
    rng = np.random.default_rng(3)
    coef = rng.normal(scale=0.02, size=(8, 3, 3))
    a = green_lagrange_strain(coef)
    b = strain_tensor(coef, "green_lagrange")
    for name in a:
        assert np.array_equal(a[name], b[name], equal_nan=True)


def test_strain_tensor_nan_and_bad_type():
    coef = np.full((2, 3, 3), np.nan)
    for kind in STRAIN_TYPES:
        s = strain_tensor(coef, kind)
        assert np.isnan(s["exx"]).all()
    with pytest.raises(ValueError, match="strain_type"):
        strain_tensor(np.zeros((1, 3, 3)), "nope")


def test_compute_surface_strain_threads_strain_type():
    eps = 0.05
    ref_2d, xw, yw, interior = _grid()
    ref_3d = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    disp = np.column_stack([eps * xw, np.zeros_like(xw), np.zeros_like(xw)])
    rec = _recon(ref_3d, disp)

    expected = {
        "green_lagrange": eps + 0.5 * eps**2,
        "infinitesimal": eps,
        "almansi": 0.5 * (1.0 - 1.0 / (1.0 + eps) ** 2),
    }
    for kind, want in expected.items():
        strain = compute_surface_strain(
            rec, ref_2d, strain_size=5, winstepsize=16, strain_type=kind
        )
        got = np.nanmedian(strain.exx[1][interior])
        assert got == pytest.approx(want, rel=1e-6), kind


# ---------------------------------------------------------------------------
# Q4 — explicit strain edge trim
# ---------------------------------------------------------------------------


def _hole_mask(ref_2d: np.ndarray, center: np.ndarray, radius_px: float) -> np.ndarray:
    return np.linalg.norm(ref_2d - center, axis=1) < radius_px


def test_edge_trim_mask_outer_boundary_and_disable():
    # A6-1: even with NO invalid nodes, the node-grid outer boundary ring is
    # trimmed (its one-sided VSG fits are biased, like the 2D outer-ROI edge);
    # the deep interior is untouched and alpha=0 disables everything.
    ref_2d, *_ = _grid()
    finite = np.ones(ref_2d.shape[0], dtype=bool)
    trim = edge_trim_mask(ref_2d, finite, 32.0, 0.7)
    assert trim.any()  # outer ring trimmed even though nothing is invalid
    center = ref_2d.mean(axis=0)
    ci = int(np.argmin(np.linalg.norm(ref_2d - center, axis=1)))
    assert not trim[ci]  # deep interior stays
    assert not edge_trim_mask(ref_2d, finite, 32.0, 0.0).any()  # alpha 0 disables


def test_edge_trim_band_scales_with_alpha():
    from scipy.spatial import cKDTree

    ref_2d, *_ = _grid(nx=21)
    center = ref_2d.mean(axis=0)
    hole = _hole_mask(ref_2d, center, 24.0)
    finite = ~hole
    vsg_radius = 32.0

    # Outer boundary of the full node lattice = the grid perimeter (nodes on the
    # min/max row or column), computed independently of edge_trim_mask.
    x, y = ref_2d[:, 0], ref_2d[:, 1]
    perim = (x == x.min()) | (x == x.max()) | (y == y.min()) | (y == y.max())
    d_hole, _ = cKDTree(ref_2d[hole]).query(ref_2d[finite])
    d_perim, _ = cKDTree(ref_2d[perim]).query(ref_2d[finite])

    counts = []
    for alpha in (0.25, 0.5, 0.75, 1.0):
        trim = edge_trim_mask(ref_2d, finite, vsg_radius, alpha)
        assert not trim[hole].any()  # already-invalid nodes are never "trimmed"
        # New semantics (A6-1): trimmed iff within alpha*R of the hole OR the
        # outer boundary.
        expected = np.minimum(d_hole, d_perim) < alpha * vsg_radius
        assert np.array_equal(trim[finite], expected)
        counts.append(int(trim.sum()))
    assert counts == sorted(counts) and counts[0] < counts[-1]  # band grows


def test_compute_surface_strain_trims_around_hole():
    eps = 0.02
    ref_2d, xw, yw, _ = _grid(nx=21)
    ref_3d = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    disp = np.column_stack([eps * xw, np.zeros_like(xw), np.zeros_like(xw)])
    hole = _hole_mask(ref_2d, ref_2d.mean(axis=0), 24.0)
    disp[hole] = np.nan  # plate with a hole: invalid displacement inside
    rec = _recon(ref_3d, disp)

    plain = compute_surface_strain(rec, ref_2d, strain_size=5, winstepsize=16)
    assert plain.n_trimmed is None  # default: trimming off, no bookkeeping

    trimmed = compute_surface_strain(
        rec, ref_2d, strain_size=5, winstepsize=16, edge_trim_alpha=0.7
    )
    assert trimmed.n_trimmed is not None
    # A6-1: the outer boundary ring is trimmed on EVERY frame, including the
    # fully-valid reference frame (pre-fix this was 0).
    assert int(trimmed.n_trimmed[0]) > 0
    # Frame 1 adds the hole band on top of the outer ring.
    assert int(trimmed.n_trimmed[1]) > int(trimmed.n_trimmed[0])
    # Batch C A5-2: strain VALUES stay DENSE — trimming only flags strain_valid,
    # it never NaNs a value the fit produced. strain_valid == ~trim, so its
    # False count is exactly n_trimmed.
    assert trimmed.strain_valid is not None
    assert int((~trimmed.strain_valid[1]).sum()) == int(trimmed.n_trimmed[1])
    fitted = np.isfinite(trimmed.exx[1])
    newly_trimmed = fitted & ~trimmed.strain_valid[1]
    assert int(newly_trimmed.sum()) > 0
    # The dense values equal the plain (untrimmed) run wherever both fits succeeded.
    both = fitted & np.isfinite(plain.exx[1])
    assert np.allclose(plain.exx[1][both], trimmed.exx[1][both])
    # ... and the displacement input is untouched by construction (frozen rec).
    assert np.isfinite(rec.displacement[1][~hole]).all()


# ---------------------------------------------------------------------------
# Q5 — reference-update schedules
# ---------------------------------------------------------------------------


def test_build_frame_schedule_default_paths_are_none():
    assert build_frame_schedule("accumulative", 6) is None
    assert build_frame_schedule("accumulative", 6, ref_update_mode="every_n") is None
    assert build_frame_schedule("incremental", 6) is None  # every_frame default


def test_build_frame_schedule_every_n_and_custom_match_engine():
    from al_dic.core.data_structures import FrameSchedule

    sched = build_frame_schedule("incremental", 6, ref_update_mode="every_n", ref_update_n=2)
    assert sched == FrameSchedule.from_every_n(2, 6)
    assert sched.ref_indices == (0, 0, 2, 2, 4)

    sched = build_frame_schedule("incremental", 6, ref_update_mode="custom", ref_update_frames=[3])
    assert sched == FrameSchedule.from_custom([3], 6)
    assert sched.ref_indices == (0, 0, 0, 3, 3)

    with pytest.raises(ValueError, match="ref_update_mode"):
        build_frame_schedule("incremental", 6, ref_update_mode="bogus")


def test_draft_forwards_ref_update_and_fft_expand(tmp_path):
    draft = ProjectDraft(
        calibration_file=tmp_path / "calib.yml",
        left=["a0.png", "a1.png"],
        right=["b0.png", "b1.png"],
        roi=(0, 10, 0, 10),
        reference_mode="incremental",
        ref_update_mode="every_n",
        ref_update_n=3,
        fft_auto_expand=False,
    )
    (tmp_path / "calib.yml").write_text("x", encoding="utf-8")
    cfg = draft.build()
    assert cfg.ref_update_mode == "every_n"
    assert cfg.ref_update_n == 3
    assert cfg.ref_update_frames is None
    assert cfg.fft_auto_expand is False
    # Both knobs are result-affecting: the G2.7 staleness hash must move.
    sig = draft.result_signature()
    draft.ref_update_n = 4
    assert draft.result_signature() != sig


def test_ref_update_fields_survive_session_round_trip(tmp_path):
    cfg = RunConfig(
        calibration_file=tmp_path / "c.yml",
        calibration_format="opencv_yaml",
        left=["l0.png"],
        right=["r0.png"],
        roi=(0, 10, 0, 10),
        output_dir=tmp_path / "out",
        reference_mode="incremental",
        ref_update_mode="custom",
        ref_update_frames=(2, 4),
        fft_auto_expand=False,
    )
    state = AppState3D(config=cfg)
    loaded = load_session(save_session(state, tmp_path / "s.aldic3d"))
    assert loaded.config == cfg  # tuple restore incl. ref_update_frames


def test_load_config_parses_ref_update_and_fft_expand(tmp_path):
    (tmp_path / "cal.yml").write_text("x", encoding="utf-8")
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
[calibration]
file = "cal.yml"
format = "opencv_yaml"
[sequence]
left = "L*.png"
right = "R*.png"
[roi]
xmin = 0
xmax = 10
ymin = 0
ymax = 10
[matching]
reference_mode = "incremental"
ref_update_mode = "every_n"
ref_update_n = 4
fft_auto_expand = false
""",
        encoding="utf-8",
    )
    from al_dic_3d.runner import load_config

    cfg = load_config(cfg_path)
    assert cfg.ref_update_mode == "every_n"
    assert cfg.ref_update_n == 4
    assert cfg.fft_auto_expand is False


@pytest.mark.slow
def test_every_n_schedule_matches_accumulative_end_to_end(tmp_path_factory):
    """Q5 e2e: an incremental every-2 run agrees with the accumulative run.

    Small-deformation synthetic scene (the acc-vs-inc self-consistency bar of
    test_incremental_mode): switching the reference only every 2 frames must
    keep the reconstructed displacement within the same tolerance.
    """
    from dataclasses import replace

    pytest.importorskip("cv2")
    from tests import synth_parity

    d = tmp_path_factory.mktemp("refupd")
    scene = synth_parity.build_parity_scene(d, img=300, n_frames=4, seed=7)
    from al_dic_3d.runner import load_config, run_pipeline

    cfg = load_config(synth_parity.write_config(d, scene))
    acc = run_pipeline(replace(cfg, reference_mode="accumulative"))
    inc2 = run_pipeline(
        replace(cfg, reference_mode="incremental", ref_update_mode="every_n", ref_update_n=2)
    )

    assert np.array_equal(acc.ref_coords, inc2.ref_coords)
    diffs = []
    ta = acc.correspondence.source != 3  # INVALID
    ti = inc2.correspondence.source != 3
    for k in range(acc.reconstruction.n_frames):
        common = ta[k] & ti[k]
        delta = np.linalg.norm(
            acc.reconstruction.displacement[k][common]
            - inc2.reconstruction.displacement[k][common],
            axis=1,
        )
        diffs.append(delta[np.isfinite(delta)])
    med_um = float(np.median(np.concatenate(diffs))) * 1000.0
    assert med_um < 20.0, f"acc vs inc(every_n=2) median diff {med_um:.1f} um"


# ---------------------------------------------------------------------------
# Q8 — engine knob plumbing
# ---------------------------------------------------------------------------


def test_make_dicpara_fft_auto_expand_and_schedule():
    from al_dic.core.data_structures import FrameSchedule

    sched = FrameSchedule.from_every_n(2, 5)
    para = make_dicpara(
        img_size=(100, 100),
        roi=(10, 90, 10, 90),
        fft_auto_expand=False,
        frame_schedule=sched,
        reference_mode="incremental",
    )
    assert para.fft_auto_expand_search is False
    assert para.frame_schedule == sched
    # Defaults preserved: engine default is auto-expand ON, no schedule.
    para = make_dicpara(img_size=(100, 100), roi=(10, 90, 10, 90))
    assert para.fft_auto_expand_search is True
    assert para.frame_schedule is None


def test_strategies_accept_fft_auto_expand():
    from al_dic_3d.matching import get_strategy

    for name in ("track_both", "stereo_each_frame", "ref_direct"):
        strategy = get_strategy(name)(fft_auto_expand=False)
        assert strategy.fft_auto_expand is False


# ---------------------------------------------------------------------------
# Q7 — config-only sessions
# ---------------------------------------------------------------------------


def test_save_session_include_results_false_is_config_only(tmp_path):
    result = _tiny_result()
    state = AppState3D(result=result, workflow_step=6)

    full = save_session(state, tmp_path / "full.aldic3d")
    lite = save_session(state, tmp_path / "lite.aldic3d", include_results=False)

    assert parse_session(full).result_arrays is not None
    lite_data = parse_session(lite)
    assert lite_data.result_arrays is None
    loaded = load_session(lite)
    assert loaded.result is None and loaded.has_results is False
    assert full.stat().st_size > lite.stat().st_size


def test_estimated_result_nbytes_positive_and_plausible():
    result = _tiny_result()
    est = estimated_result_nbytes(result)
    # at least the raw reconstruction + correspondence payloads
    floor = (
        result.reconstruction.points.nbytes
        + result.reconstruction.displacement.nbytes
        + result.correspondence.xL.nbytes
        + result.correspondence.xR.nbytes
    )
    assert est >= floor


# ---------------------------------------------------------------------------
# Q6 — CLI session-path launch + file association (pure parts)
# ---------------------------------------------------------------------------


def test_cli_normalize_argv_folds_session_into_gui():
    from al_dic_3d.cli import normalize_argv

    assert normalize_argv(["C:/x/proj.aldic3d"]) == ["gui", "C:/x/proj.aldic3d"]
    assert normalize_argv(["run", "cfg.toml"]) == ["run", "cfg.toml"]
    assert normalize_argv([]) == []


def test_cli_gui_accepts_optional_session():
    from al_dic_3d.cli import build_parser

    args = build_parser().parse_args(["gui", "proj.aldic3d"])
    assert args.command == "gui" and args.session == "proj.aldic3d"
    args = build_parser().parse_args(["gui"])
    assert args.session is None


def test_session_path_from_argv_requires_existing_file(tmp_path):
    from al_dic_3d.gui.app import session_path_from_argv

    missing = str(tmp_path / "nope.aldic3d")
    assert session_path_from_argv([missing]) is None
    real = tmp_path / "yes.aldic3d"
    real.write_bytes(b"zip?")
    assert session_path_from_argv(["other.txt", str(real)]) == str(real)
    assert session_path_from_argv(None) is None


def test_file_association_constants_and_command():
    from al_dic_3d.gui import file_association as fa

    assert fa.EXT == ".aldic3d"
    assert fa.PROGID == "pyALDIC3D.Session"
    cmd = fa.open_command()
    assert "-m al_dic_3d" in cmd and '"%1"' in cmd
    import sys

    assert fa.is_supported() == (sys.platform == "win32")
