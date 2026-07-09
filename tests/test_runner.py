"""Validate the headless runner + CLI: config.toml -> pipeline -> .npz/.mat.

Uses an on-disk synthetic converging-stereo dataset (plane-induced homographies,
zero modeling error) so the whole CLI path — config parse, calibration import,
image loading, strategy, reconstruction, serialization — is exercised end to end
and checked against analytic 3D ground truth.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.matching.contracts import INVALID
from al_dic_3d.runner import RunConfig, load_config, run_pipeline, write_results

cv2 = pytest.importorskip("cv2")

from tests import synth_stereo  # noqa: E402  (after importorskip guard)


def test_load_config_parses_and_resolves_paths(tmp_path):
    (tmp_path / "calib.yml").write_text("", encoding="utf-8")
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
[calibration]
file = "calib.yml"
format = "opencv_yaml"
[sequence]
left = "L_*.png"
right = "R_*.png"
[roi]
xmin = 45
xmax = 175
ymin = 45
ymax = 215
[matching]
strategy = "track_both"
winsize = 48
disparity_offset = [12.0, -1.0]
[output]
dir = "out"
prefix = "case1"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    assert cfg.calibration_format == "opencv_yaml"
    assert cfg.calibration_file == (tmp_path / "calib.yml").resolve()
    assert cfg.roi == (45, 175, 45, 215)
    assert cfg.winsize == 48
    assert cfg.disparity_offset == (12.0, -1.0)
    assert cfg.output_dir == (tmp_path / "out").resolve()
    assert cfg.output_prefix == "case1"
    assert cfg.base_dir == tmp_path.resolve()


def test_load_config_missing_required_raises(tmp_path):
    # Valid everywhere except the required [calibration].file, to isolate that path.
    cfg_path = tmp_path / "bad.toml"
    cfg_path.write_text(
        """
[calibration]
format = "opencv_yaml"
[sequence]
left = "L_*.png"
right = "R_*.png"
[roi]
xmin = 0
xmax = 10
ymin = 0
ymax = 10
""".strip()
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"\[calibration\].file"):
        load_config(cfg_path)


def test_resolve_paths_sorts_frames_numerically(tmp_path):
    # Non-zero-padded frame names must order numerically, not lexicographically,
    # or the temporal axis (and cumulative displacement) would be scrambled.
    from al_dic_3d.runner import _resolve_paths

    for i in (1, 2, 10, 11, 100):
        (tmp_path / f"f_{i}.png").write_bytes(b"x")
    names = [p.name for p in _resolve_paths("f_*.png", tmp_path)]
    assert names == ["f_1.png", "f_2.png", "f_10.png", "f_11.png", "f_100.png"]


def test_run_pipeline_end_to_end_recovers_3d(tmp_path):
    scene = synth_stereo.build_scene(tmp_path, n_frames=3)
    cfg_path = synth_stereo.write_config(tmp_path, scene)
    cfg = load_config(cfg_path)

    seen = []
    result = run_pipeline(cfg, progress=lambda frac, msg: seen.append(frac))

    rec = result.reconstruction
    assert rec.n_frames == 3
    assert result.meta["n_tracked_positions"] > 0
    assert seen and seen[-1] == pytest.approx(1.0)  # progress reached 100%

    # F3.1: the failure accounting rides in meta and is JSON-serializable
    # (session.json writes meta verbatim; the parameters export sanitises it).
    import json

    m = result.meta
    assert m["summary"]["n_frames"] == 3 and not m["summary"]["all_empty"]
    cams = {r["cam"] for r in m["diagnostics"]}
    assert "stereo" in cams and "L" in cams  # frame-1 match + temporal rows
    assert all(r["n_valid"] <= r["n_pts"] for r in m["diagnostics"])
    json.dumps({"diagnostics": m["diagnostics"], "summary": m["summary"], "gates": m["gates"]})

    gt = synth_stereo.gt_world_points(scene, result.ref_coords)
    tracked = result.correspondence.source != INVALID  # (nf, n)

    disp_err, coverage = [], []
    for k in range(1, rec.n_frames):
        common = tracked[k] & tracked[0]
        coverage.append(common.mean())
        d_rec = rec.displacement[k][common]
        d_gt = (gt[k] - gt[0])[common]
        disp_err.append(np.linalg.norm(d_rec - d_gt, axis=1))
    disp_err = np.concatenate(disp_err)

    assert min(coverage) > 0.9
    # Slightly looser than the in-memory E2E (0.054 mm p90) because images are
    # round-tripped through 16-bit PNG, but still well sub-0.1 mm.
    assert np.median(disp_err) < 0.06, f"median 3D disp err {np.median(disp_err):.4f} mm"
    assert np.percentile(disp_err, 90) < 0.15


def test_write_results_roundtrips_npz_and_mat(tmp_path):
    import json

    import scipy.io

    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    cfg = load_config(synth_stereo.write_config(tmp_path, scene))
    result = run_pipeline(cfg)
    paths = write_results(result, cfg)

    assert paths["npz"].exists() and paths["mat"].exists()

    rec = result.reconstruction
    npz = np.load(paths["npz"])
    assert npz["points3D"].shape == (2, result.correspondence.n_pts, 3)
    # Compare VALUES (not just shapes) so a swapped/mangled payload is caught, and
    # confirm NaN invalids survive both serializers.
    assert np.allclose(npz["points3D"], rec.points, equal_nan=True)
    assert np.allclose(npz["displacement3D"], rec.displacement, equal_nan=True)
    assert np.array_equal(npz["source"], result.correspondence.source)
    # Unified schema (E1): the archive is a SUPERSET — per-component stacks from
    # export.tables.selected_arrays live next to the legacy keys.
    for key in ("U", "V", "W", "mag", "xL", "xR", "quality", "ref_coords"):
        assert key in npz, f"unified archive missing {key!r}"
    assert np.allclose(npz["U"], rec.displacement[:, :, 0], equal_nan=True)
    assert np.allclose(npz["xL"], result.correspondence.xL, equal_nan=True)

    mat = scipy.io.loadmat(str(paths["mat"]))
    assert mat["displacement3D"].shape == (2, result.correspondence.n_pts, 3)
    assert np.allclose(mat["points3D"], rec.points, equal_nan=True)
    assert np.allclose(mat["displacement3D"], rec.displacement, equal_nan=True)
    assert str(mat["strategy"][0]) == "track_both"

    # The parameters JSON is always written and records the RunConfig.
    params = json.loads(paths["params"].read_text(encoding="utf-8"))
    assert params["strategy"] == "track_both"
    assert params["winsize"] == cfg.winsize and params["winstepsize"] == cfg.winstepsize


def test_write_results_rejects_unknown_format(tmp_path):
    cfg = RunConfig(
        calibration_file=tmp_path / "calib.yml",
        calibration_format="opencv_yaml",
        left=[],
        right=[],
        roi=(0, 1, 0, 1),
        output_dir=tmp_path,
    )
    with pytest.raises(ValueError, match="unknown output format"):
        write_results(None, cfg, formats=("npz", "bogus"))  # validated before any I/O


def test_cli_run_creates_outputs(tmp_path):
    from al_dic_3d.cli import main

    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    cfg_path = synth_stereo.write_config(tmp_path, scene)
    rc = main(["run", str(cfg_path), "-q", "--formats", "npz,mat,csv,ply,vtu"])
    assert rc == 0
    out = tmp_path / "out"
    assert (out / "run.npz").exists()
    assert (out / "run.mat").exists()
    assert len(list(out.glob("run_parameters_*.json"))) == 1
    csv_dir = next(out.glob("run_csv_*"))
    assert len(list(csv_dir.glob("*.csv"))) == 2
    ply_dir = next(out.glob("run_ply_*"))
    assert len(list(ply_dir.glob("*.ply"))) == 2
    vtu_dir = next(out.glob("run_vtu_*"))
    assert len(list(vtu_dir.glob("*.vtu"))) == 2 and (vtu_dir / "run.pvd").exists()


def test_run_pipeline_cooperative_cancel(tmp_path):
    scene = synth_stereo.build_scene(tmp_path, n_frames=3)
    cfg = load_config(synth_stereo.write_config(tmp_path, scene))
    with pytest.raises(RuntimeError, match="cancelled"):
        run_pipeline(cfg, stop=lambda: True)  # stop trips at the first checkpoint


def test_run_pipeline_computes_and_writes_strain(tmp_path):
    from dataclasses import replace

    scene = synth_stereo.build_scene(tmp_path, n_frames=3)
    cfg = load_config(synth_stereo.write_config(tmp_path, scene))
    result = run_pipeline(replace(cfg, compute_strain=True, strain_size=5))

    assert result.strain is not None
    assert result.strain.n_frames == 3 and result.meta["compute_strain"] is True
    assert np.nanmax(np.abs(result.strain.exx[0])) < 1e-9  # reference frame: zero strain
    assert np.isfinite(result.strain.exx[1]).any()  # some finite strain later

    paths = write_results(result, replace(cfg, compute_strain=True))
    npz = np.load(paths["npz"])
    assert "strain_exx" in npz
    assert npz["strain_von_mises"].shape == (3, result.correspondence.n_pts)


def test_reference_mesh_quadtree_refinement():
    # 2D-app levers (inner/outer/brush + level): default OFF -> uniform grid;
    # inner refinement splits hole-boundary elements down to step // 2**level.
    from pathlib import Path

    import numpy as np

    from al_dic_3d.runner import RunConfig, _build_reference_mesh

    base = dict(
        calibration_file=Path("x"),
        calibration_format="opencv_yaml",
        left="",
        right="",
        roi=(40, 360, 40, 260),
        output_dir=Path("."),
        winstepsize=16,
    )
    mask = np.ones((300, 400))
    mask[120:180, 150:250] = 0  # a hole the mesh must refine around

    uniform = _build_reference_mesh(RunConfig(**base), 300, 400, [mask])
    refined = _build_reference_mesh(
        RunConfig(**base, refine_inner=True, refinement_level=2), 300, 400, [mask]
    )
    n_u = np.asarray(uniform.coordinates_fem).shape[0]
    n_r = np.asarray(refined.coordinates_fem).shape[0]
    assert n_r > 1.5 * n_u  # boundary elements got quadtree-split
    # refined nodes appear BETWEEN uniform grid lines (finer than winstepsize)
    xs = np.unique(np.asarray(refined.coordinates_fem)[:, 0])
    assert np.diff(np.sort(xs)).min() < 16


def test_load_config_roi_mask_key(tmp_path):
    # [roi].mask makes the pixel bounds optional (mask bbox overrides them).
    (tmp_path / "calib.yml").write_text("", encoding="utf-8")
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
[calibration]
file = "calib.yml"
format = "opencv_yaml"
[sequence]
left = "L_*.png"
right = "R_*.png"
[roi]
mask = "roi_mask.png"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    assert cfg.roi_mask == tmp_path / "roi_mask.png"
    assert cfg.roi == (0, 0, 0, 0)  # placeholder — replaced by the mask bbox


def test_mask_bbox_and_roi_mask_validation(tmp_path):
    from al_dic_3d.runner import _load_roi_mask, _mask_bbox

    mask = np.zeros((60, 80), dtype=bool)
    mask[10:31, 20:51] = True
    assert _mask_bbox(mask) == (20, 50, 10, 30)

    ok = np.zeros((60, 80), dtype=np.uint8)
    ok[10:30, 20:50] = 255
    cv2.imwrite(str(tmp_path / "ok.png"), ok)
    loaded = _load_roi_mask(tmp_path / "ok.png", (60, 80))
    assert loaded.dtype == bool and loaded[15, 30] and not loaded[0, 0]

    with pytest.raises(ValueError, match="does not match"):
        _load_roi_mask(tmp_path / "ok.png", (61, 80))

    cv2.imwrite(str(tmp_path / "empty.png"), np.zeros((60, 80), dtype=np.uint8))
    with pytest.raises(ValueError, match="empty"):
        _load_roi_mask(tmp_path / "empty.png", (60, 80))


def test_run_pipeline_roi_mask_confines_grid(tmp_path):
    # An arbitrary-shape [roi].mask: bbox override + constant left mask.
    from dataclasses import replace

    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    cfg = load_config(synth_stereo.write_config(tmp_path, scene))

    img = cv2.imread(str(tmp_path / "L_000.png"), cv2.IMREAD_UNCHANGED)
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.circle(mask, (110, 130), 55, 255, -1)  # disc inside the default ROI
    cv2.imwrite(str(tmp_path / "roi_mask.png"), mask)

    cfg = replace(cfg, roi_mask=tmp_path / "roi_mask.png", roi=(0, 0, 0, 0))
    result = run_pipeline(cfg)

    # Reference grid is confined to the mask's bounding box (55..165, 75..185).
    xs, ys = result.ref_coords[:, 0], result.ref_coords[:, 1]
    assert xs.min() >= 55 and xs.max() <= 165
    assert ys.min() >= 75 and ys.max() <= 185
    assert result.meta["n_tracked_positions"] > 0
