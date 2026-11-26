"""The image size a calibration was made for travels with the built-in YAML.

New-user audit (2026-11-25): ``to_opencv_yaml`` wrote no image size and
``from_opencv_yaml`` read none, so the run's size guard only fired for DICe
files; binned or cropped images then ran with the built-in calibration and
gave wrong results. The YAML now records each camera's width and height
(extra nodes, ignored by OpenCV readers and older builds), the importer reads
them back, and the project readiness blocks Run up front on a mismatch.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from al_dic_3d.calibration import CameraIntrinsics, StereoRig, from_opencv_yaml, to_opencv_yaml
from al_dic_3d.project import ProjectDraft


def _rig(size: tuple[int, int] | None) -> StereoRig:
    w, h = size if size is not None else (None, None)
    left = CameraIntrinsics(fx=900.0, fy=901.0, cx=40.0, cy=30.0, width=w, height=h)
    right = CameraIntrinsics(fx=905.0, fy=906.0, cx=41.0, cy=29.0, width=w, height=h)
    return StereoRig(
        cameras={"L": left, "R": right},
        extrinsics={("L", "R"): (np.eye(3), np.array([-100.0, 0.0, 0.0]))},
    )


def test_yaml_round_trips_each_cameras_image_size(tmp_path: Path):
    left = CameraIntrinsics(fx=900.0, fy=900.0, cx=959.5, cy=599.5, width=1920, height=1200)
    right = CameraIntrinsics(fx=900.0, fy=900.0, cx=819.5, cy=599.5, width=1640, height=1200)
    rig = StereoRig(
        cameras={"L": left, "R": right},
        extrinsics={("L", "R"): (np.eye(3), np.array([-100.0, 0.0, 0.0]))},
    )
    back = from_opencv_yaml(to_opencv_yaml(rig, tmp_path / "rig.yml"))
    assert (back.cameras["L"].width, back.cameras["L"].height) == (1920, 1200)
    assert (back.cameras["R"].width, back.cameras["R"].height) == (1640, 1200)


def test_the_size_nodes_stay_readable_by_plain_opencv(tmp_path: Path):
    path = to_opencv_yaml(_rig((80, 60)), tmp_path / "rig.yml")
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    try:
        assert fs.getNode("cameraMatrix1").mat().shape == (3, 3)  # the stereo contract
        assert fs.getNode("imageSize1").mat().ravel().tolist() == [80, 60]
        # Every calibration node stays a matrix: code reading each with .mat() works.
        for name in fs.root().keys():
            if not name.startswith("meta_"):
                assert fs.getNode(name).mat() is not None, name
    finally:
        fs.release()


def test_a_cv_size_sequence_is_read_too(tmp_path: Path):
    path = to_opencv_yaml(_rig(None), tmp_path / "cpp.yml")
    text = path.read_text(encoding="utf-8")
    path.write_text(text + "imageSize1: [ 1920, 1200 ]\n", encoding="utf-8")
    back = from_opencv_yaml(path)
    assert (back.cameras["L"].width, back.cameras["L"].height) == (1920, 1200)
    assert back.cameras["R"].width is None


def test_a_yaml_without_a_size_keeps_working(tmp_path: Path):
    back = from_opencv_yaml(to_opencv_yaml(_rig(None), tmp_path / "old.yml"))
    assert back.cameras["L"].width is None and back.cameras["R"].height is None


def test_an_invalid_size_node_is_refused(tmp_path: Path):
    path = to_opencv_yaml(_rig(None), tmp_path / "rig.yml")
    text = path.read_text(encoding="utf-8")
    path.write_text(text + "imageSize2: [ -3, 60 ]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="imageSize2"):
        from_opencv_yaml(path)


def _images(folder: Path, cam: str, size: tuple[int, int], n: int = 2) -> list[str]:
    w, h = size
    out = []
    for k in range(n):
        p = folder / f"{cam}_{k:03d}.png"
        cv2.imwrite(str(p), np.full((h, w), 100, np.uint8))
        out.append(str(p))
    return out


def _draft(tmp_path: Path, calib_size, left_size, right_size) -> ProjectDraft:
    calib = to_opencv_yaml(_rig(calib_size), tmp_path / f"calib_{calib_size}.yml")
    return ProjectDraft(
        calibration_file=calib,
        calibration_format="opencv_yaml",
        left=_images(tmp_path, "L", left_size),
        right=_images(tmp_path, "R", right_size),
        roi=(5, 30, 5, 25),
    )


def test_readiness_blocks_images_of_another_size(tmp_path: Path):
    draft = _draft(tmp_path, (80, 60), (40, 30), (80, 60))  # left binned 2x
    issues = draft.readiness_issues()
    assert "left calibration was made for 80x60 images, but the left images are 40x30" in issues
    assert not any(i.startswith("right calibration") for i in issues)


def test_readiness_accepts_matching_or_unrecorded_sizes(tmp_path: Path):
    assert _draft(tmp_path, (80, 60), (80, 60), (80, 60)).readiness_issues() == []
    assert _draft(tmp_path, None, (40, 30), (40, 30)).readiness_issues() == []


def test_the_readiness_message_reads_like_the_run_refusal(tmp_path: Path):
    pytest.importorskip("PySide6")
    from al_dic_3d.gui.issue_text import issue_text

    text = issue_text("right calibration was made for 80x60 images, but the right images are 40x30")
    assert "80x60" in text and "40x30" in text
    assert "binned or cropped images need their own calibration" in text
