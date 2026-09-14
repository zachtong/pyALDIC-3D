"""Smaller compute / export findings from the readiness audit (fix batch V)."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

pytest.importorskip("al_dic")

from al_dic_3d.calibration import CameraIntrinsics, StereoRig  # noqa: E402
from al_dic_3d.export.tables import export_csv_frames  # noqa: E402
from al_dic_3d.export.utils import make_timestamp  # noqa: E402
from al_dic_3d.matching import primitives  # noqa: E402
from al_dic_3d.matching.primitives import make_dicpara  # noqa: E402
from al_dic_3d.runner import _check_calibration_size, load_config, run_pipeline  # noqa: E402
from al_dic_3d.sequence.lazy import LazyFrameProvider, load_gray  # noqa: E402
from tests import synth_stereo  # noqa: E402


def test_admm_max_iter_zero_means_local_only():
    para = make_dicpara(img_size=(64, 64), roi=(8, 55, 8, 55), admm_max_iter=0)
    assert para.use_global_step is False
    para = make_dicpara(img_size=(64, 64), roi=(8, 55, 8, 55), admm_max_iter=3)
    assert para.use_global_step is True and para.admm_max_iter == 3


def test_znssd_chunks_are_bounded_by_bytes(monkeypatch):
    sizes: list[int] = []
    real = primitives._znssd_block

    def spy(ref, coeffs, idx, *a, **k):
        sizes.append(int(idx.size))
        return real(ref, coeffs, idx, *a, **k)

    monkeypatch.setattr(primitives, "_znssd_block", spy)
    rng = np.random.default_rng(0)
    img = rng.random((400, 400))
    pts = np.column_stack([rng.uniform(80, 320, 900), rng.uniform(80, 320, 900)])
    u = np.zeros((900, 2))
    primitives._znssd(
        img, img, pts, u, np.zeros((900, 4)), 128, np.ones(900, bool), np.ones_like(img)
    )
    per_point = primitives._ZNSSD_BYTES_PER_SAMPLE * 129**2
    assert max(sizes) * per_point <= primitives._ZNSSD_CHUNK_BYTES + per_point


def test_rgba_images_use_luminance_not_the_blue_channel(tmp_path):
    rgba = np.zeros((10, 12, 4), np.uint8)
    rgba[..., 0] = 10  # blue
    rgba[..., 1] = 200  # green
    rgba[..., 2] = 90  # red
    rgba[..., 3] = 255
    p = tmp_path / "rgba.png"
    cv2.imwrite(str(p), rgba)
    got = load_gray(p)
    want = cv2.cvtColor(rgba, cv2.COLOR_BGRA2GRAY).astype(np.float64)
    assert np.array_equal(got, want) and got.mean() > 100  # not the blue channel (10)


def test_a_frame_with_a_different_size_is_refused(tmp_path):
    a = np.full((20, 30), 100, np.uint8)
    b = np.full((20, 31), 100, np.uint8)
    cv2.imwrite(str(tmp_path / "f0.png"), a)
    cv2.imwrite(str(tmp_path / "f1.png"), b)
    prov = LazyFrameProvider([tmp_path / "f0.png", tmp_path / "f1.png"])
    prov.get_normalized(0)
    with pytest.raises(ValueError, match="same size"):
        prov.get_normalized(1)


def test_timestamps_are_unique_within_the_process():
    stamps = [make_timestamp() for _ in range(5)]
    assert len(set(stamps)) == 5 and all(len(s) == 14 for s in stamps)


def test_calibration_for_another_resolution_is_refused():
    intr = CameraIntrinsics(fx=1000, fy=1000, cx=960, cy=600, width=1920, height=1200)
    rig = StereoRig(
        cameras={"L": intr, "R": intr}, extrinsics={("L", "R"): (np.eye(3), np.ones(3))}
    )
    _check_calibration_size(rig, "L", (1200, 1920))  # matches
    with pytest.raises(ValueError, match="960x600"):
        _check_calibration_size(rig, "L", (600, 960))
    no_size = CameraIntrinsics(fx=1000, fy=1000, cx=960, cy=600)
    rig2 = StereoRig(
        cameras={"L": no_size, "R": no_size}, extrinsics={("L", "R"): (np.eye(3), np.ones(3))}
    )
    _check_calibration_size(rig2, "L", (1, 1))  # unknown size: nothing to check


@pytest.fixture(scope="module")
def run3(tmp_path_factory):
    d = tmp_path_factory.mktemp("small_fixes")
    scene = synth_stereo.build_scene(d, n_frames=3)
    return run_pipeline(load_config(synth_stereo.write_config(d, scene)))


def test_csv_frames_are_one_based_like_every_other_export(run3, tmp_path):
    paths = export_csv_frames(run3, ["U"], tmp_path, "run")
    assert [p.name for p in paths] == ["run_frame_1.csv", "run_frame_2.csv", "run_frame_3.csv"]


def test_quality_is_per_frame_not_the_frame1_score_copied(run3):
    q = run3.correspondence.quality
    both = np.isfinite(q[0]) & np.isfinite(q[2])
    assert both.any()
    assert (q[2][both] >= q[0][both]).all()  # worst of stereo + temporal scores
    assert not np.array_equal(q[0][both], q[2][both])


def test_a_config_in_a_bracketed_folder_finds_its_images(tmp_path):
    from al_dic_3d.runner import _resolve_paths

    folder = tmp_path / "test [1]"
    folder.mkdir()
    for k in range(2):
        cv2.imwrite(str(folder / f"L_{k}.png"), np.zeros((4, 4), np.uint8))
    found = _resolve_paths("L_*.png", folder)
    assert [p.name for p in found] == ["L_0.png", "L_1.png"]
