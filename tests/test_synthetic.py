"""``al_dic_3d.synthetic`` -- the packaged synthetic stereo scene (demo / self-test).

The generator moved out of ``tests/synth_parity.py``; these tests pin what the
move promised: deterministic output, unicode-safe files, a calibration the
importer reads back exactly, configs that load, and the unchanged re-export.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from al_dic_3d import synthetic

_SRC = Path(synthetic.__file__)


def test_synthetic_module_is_qt_free():
    text = _SRC.read_text(encoding="utf-8")
    assert not re.search(r"import\s+PySide6|from\s+PySide6", text)


def test_scene_is_deterministic(tmp_path):
    a = synthetic.build_scene(tmp_path / "a", img=96, n_frames=2, seed=3)
    b = synthetic.build_scene(tmp_path / "b", img=96, n_frames=2, seed=3)
    assert a["left"] == ["L_000.png", "L_001.png"] and a["right"] == b["right"]
    for name in [*a["left"], *a["right"], synthetic.CALIB_NAME]:
        assert (a["dir"] / name).read_bytes() == (b["dir"] / name).read_bytes(), name


def test_scene_depends_on_the_seed(tmp_path):
    a = synthetic.build_scene(tmp_path / "a", img=96, n_frames=2, seed=3)
    b = synthetic.build_scene(tmp_path / "b", img=96, n_frames=2, seed=4)
    assert (a["dir"] / "L_000.png").read_bytes() != (b["dir"] / "L_000.png").read_bytes()


def test_scene_in_a_non_ascii_folder_with_brackets(tmp_path):
    from al_dic_3d.calibration import load_calibration
    from al_dic_3d.pathsafe import imread_unicode

    out = tmp_path / "试样 été [1]"
    scene = synthetic.build_scene(out, img=96, n_frames=3, seed=7)
    img = imread_unicode(out / "R_002.png")
    assert img is not None and img.shape == (96, 96) and img.dtype == np.uint16
    rig = load_calibration(out / synthetic.CALIB_NAME, "opencv_yaml")
    R, T = rig.extrinsics[("L", "R")]
    np.testing.assert_allclose(R, scene["R"], atol=1e-12)
    np.testing.assert_allclose(np.ravel(T), scene["T"], atol=1e-12)
    np.testing.assert_allclose(rig.cameras["L"].K, scene["intr_L"].K, atol=1e-12)
    np.testing.assert_allclose(
        rig.cameras["R"].dist_coeffs, scene["intr_R"].dist_coeffs, atol=1e-12
    )


def test_reference_frames_differ_between_cameras_and_frames(tmp_path):
    from al_dic_3d.pathsafe import imread_unicode

    scene = synthetic.build_scene(tmp_path, img=96, n_frames=2, seed=7)
    l0 = imread_unicode(scene["dir"] / "L_000.png").astype(float)
    l1 = imread_unicode(scene["dir"] / "L_001.png").astype(float)
    r0 = imread_unicode(scene["dir"] / "R_000.png").astype(float)
    assert np.abs(l0 - l1).mean() > 100.0  # the material moved
    assert np.abs(l0 - r0).mean() > 100.0  # the second viewpoint differs


@pytest.mark.parametrize(("img", "frames"), [(32, 3), (96, 1)])
def test_build_scene_rejects_degenerate_requests(tmp_path, img, frames):
    with pytest.raises(ValueError):
        synthetic.build_scene(tmp_path, img=img, n_frames=frames)


def test_gt_tracks_reference_frame_has_zero_displacement(tmp_path):
    scene = synthetic.build_scene(tmp_path, img=96, n_frames=3, seed=7)
    ref = np.array([[30.0, 40.0], [60.0, 50.0]])
    gt = synthetic.gt_tracks(scene, ref)
    assert gt["displacement"].shape == (3, 2, 3)
    np.testing.assert_allclose(gt["displacement"][0], 0.0)
    np.testing.assert_allclose(gt["xL"][0], ref, atol=1e-6)  # left frame 1 is the reference
    assert np.linalg.norm(gt["displacement"][2], axis=1).min() > 0.5  # 0.35/0.18 mm per frame


def test_glob_config_loads(tmp_path):
    from al_dic_3d.runner import load_config

    scene = synthetic.build_scene(tmp_path, img=96, n_frames=2, seed=7)
    cfg = load_config(synthetic.write_config(tmp_path, scene))
    assert cfg.left == "L_*.png" and cfg.strategy == "track_both"
    assert cfg.roi == (15, 81, 15, 81) and not cfg.compute_strain
    assert cfg.output_dir == tmp_path.resolve() / "out"
    assert synthetic.is_synthetic_dataset(tmp_path)


def test_explicit_file_config_loads_in_unicode_folder(tmp_path):
    from al_dic_3d.runner import load_config

    out = tmp_path / "demo 数据 [x]"
    scene = synthetic.build_scene(out, img=96, n_frames=3, seed=7)
    path = synthetic.write_config(
        out, scene, prefix="demo", explicit_files=True, output_dir="results", strain=True
    )
    cfg = load_config(path)
    assert cfg.left == ["L_000.png", "L_001.png", "L_002.png"]
    assert cfg.right == ["R_000.png", "R_001.png", "R_002.png"]
    assert cfg.compute_strain and cfg.output_prefix == "demo"
    assert cfg.output_dir == out.resolve() / "results"


def test_frame_files_lists_only_this_modules_frames(tmp_path):
    synthetic.build_scene(tmp_path, img=96, n_frames=3, seed=7)
    (tmp_path / "L_1.png").write_bytes(b"")  # not the L_000 naming
    (tmp_path / "notes.png").write_bytes(b"")
    names = [p.name for p in synthetic.frame_files(tmp_path)]
    assert names == ["L_000.png", "L_001.png", "L_002.png", "R_000.png", "R_001.png", "R_002.png"]
    assert [p.name for p in synthetic.frame_files(tmp_path, first=2)] == ["L_002.png", "R_002.png"]
    assert synthetic.frame_files(tmp_path / "missing") == []


def test_is_synthetic_dataset_rejects_foreign_or_missing_config(tmp_path):
    assert not synthetic.is_synthetic_dataset(tmp_path)  # no config at all
    (tmp_path / "config.toml").write_text("[calibration]\n", encoding="utf-8")
    assert not synthetic.is_synthetic_dataset(tmp_path)


def test_synth_parity_is_a_thin_reexport():
    from tests import synth_parity

    assert synth_parity.build_parity_scene is synthetic.build_scene
    assert synth_parity.write_config is synthetic.write_config
    assert synth_parity.gt_tracks is synthetic.gt_tracks
    assert synth_parity.metrics is synthetic.metrics
    assert synth_parity.GATE is synthetic.GATE
    assert synth_parity._speckle is synthetic.speckle


def test_accuracy_summary_on_a_perfect_result(tmp_path):
    """Feeding the analytic truth back in gives zero error and full coverage."""
    from types import SimpleNamespace

    from al_dic_3d.matching.contracts import TRACKED

    scene = synthetic.build_scene(tmp_path, img=96, n_frames=3, seed=7)
    ref = np.array([[30.0, 40.0], [60.0, 50.0], [45.0, 45.0]])
    gt = synthetic.gt_tracks(scene, ref)
    source = np.full((3, 3), TRACKED, dtype=np.uint8)
    result = SimpleNamespace(
        ref_coords=ref,
        correspondence=SimpleNamespace(
            xL=gt["xL"], xR=gt["xR"], source=source, n_frames=3, n_pts=3
        ),
        reconstruction=SimpleNamespace(
            points=gt["world"],
            displacement=gt["displacement"],
            reproj_error=np.zeros((3, 3)),
        ),
    )
    acc = synthetic.accuracy_summary(result, scene)
    assert acc["coverage_min"] == 1.0
    assert acc["disp_median_mm"] == pytest.approx(0.0, abs=1e-9)
    assert acc["disp_p90_mm"] == pytest.approx(0.0, abs=1e-9)
    assert acc["n_points"] == 3 and acc["n_frames"] == 3
