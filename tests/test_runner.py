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
from al_dic_3d.runner import load_config, run_pipeline, write_results

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

    mat = scipy.io.loadmat(str(paths["mat"]))
    assert mat["displacement3D"].shape == (2, result.correspondence.n_pts, 3)
    assert np.allclose(mat["points3D"], rec.points, equal_nan=True)
    assert np.allclose(mat["displacement3D"], rec.displacement, equal_nan=True)
    assert str(mat["strategy"][0]) == "track_both"


def test_cli_run_creates_outputs(tmp_path):
    from al_dic_3d.cli import main

    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    cfg_path = synth_stereo.write_config(tmp_path, scene)
    rc = main(["run", str(cfg_path), "-q"])
    assert rc == 0
    assert (tmp_path / "out" / "run.npz").exists()
    assert (tmp_path / "out" / "run.mat").exists()
