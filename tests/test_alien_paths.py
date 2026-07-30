"""End-to-end I/O round-trips under a CJK + spaces + accents directory (G3).

Real users have Chinese/Korean/Japanese Windows user names, spaces in folder
names, OneDrive and network paths. Every filesystem artifact the app reads or
writes — pipeline images, canvas masks, calibration YAML, ``.aldic3d``
sessions, tabular/image/animation exports — must survive such a directory.
pytest's ``tmp_path`` itself is ASCII, so each test works inside
``tmp_path / "试样 数据 ünïcode"``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d.calibration import (  # noqa: E402
    CameraIntrinsics,
    StereoRig,
    from_opencv_yaml,
    load_calibration,
    load_detections,
    save_detections,
    to_opencv_yaml,
)
from al_dic_3d.calibration.detect import BoardDetection  # noqa: E402
from al_dic_3d.export import export_csv_frames, export_mat, export_npz  # noqa: E402
from al_dic_3d.export.animation import StreamingAnimWriter  # noqa: E402
from al_dic_3d.export.render import FieldImageConfig, export_image_frames  # noqa: E402
from al_dic_3d.matching.contracts import TRACKED, CorrespondenceSet  # noqa: E402
from al_dic_3d.pathsafe import imread_unicode, imwrite_unicode  # noqa: E402
from al_dic_3d.project import AppState3D  # noqa: E402
from al_dic_3d.project.draft import ProjectDraft, decode_mask_png  # noqa: E402
from al_dic_3d.project.session import load_session, save_session  # noqa: E402
from al_dic_3d.reconstruct import Reconstruction3D  # noqa: E402
from al_dic_3d.runner import RunResult  # noqa: E402
from al_dic_3d.sequence.lazy import LazyFrameProvider, load_gray  # noqa: E402

ALIEN = "试样 数据 ünïcode"
Z0 = 800.0


@pytest.fixture()
def alien_dir(tmp_path: Path) -> Path:
    d = tmp_path / ALIEN
    d.mkdir()
    return d


def _tiny_result(n_frames: int = 2, nx: int = 5) -> RunResult:
    """A small, fully synthetic RunResult (no pipeline run needed)."""
    ii, jj = np.meshgrid(np.arange(nx), np.arange(nx))
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * 16.0 + 40.0, jj * 16.0 + 40.0])
    ref_3d = np.column_stack([ii * 2.0, jj * 2.0, np.full(ii.size, Z0)])
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
        meta={"n_frames": n_frames, "image_size": (160, 160)},
    )


def _rig() -> StereoRig:
    intr = CameraIntrinsics(fx=1200.0, fy=1180.0, cx=320.0, cy=240.0, k1=-0.1, k2=0.05)
    th = np.deg2rad(12.0)
    R = np.array([[np.cos(th), 0.0, np.sin(th)], [0.0, 1.0, 0.0], [-np.sin(th), 0.0, np.cos(th)]])
    T = np.array([-250.0, 2.0, 30.0])
    return StereoRig(cameras={"L": intr, "R": intr}, extrinsics={("L", "R"): (R, T)})


# ---------------------------------------------------------------------------
# pipeline image loading (sequence layer)
# ---------------------------------------------------------------------------


def test_load_gray_and_lazy_provider_under_alien_path(alien_dir: Path) -> None:
    rng = np.random.default_rng(0)
    img = rng.integers(0, 65535, (24, 32)).astype(np.uint16)
    paths = []
    for k in range(2):
        p = alien_dir / f"帧 L_{k:03d}.png"
        imwrite_unicode(p, img)
        paths.append(p)

    arr = load_gray(paths[0])
    assert arr.dtype == np.float64
    assert np.array_equal(arr, img.astype(np.float64))

    provider = LazyFrameProvider(paths)
    assert provider.shape == (24, 32)
    assert np.array_equal(provider.get_normalized(1), img.astype(np.float64))


# ---------------------------------------------------------------------------
# canvas mask PNG (draft build artifacts)
# ---------------------------------------------------------------------------


def test_draft_mask_png_written_and_decoded_under_alien_path(alien_dir: Path) -> None:
    mask = np.zeros((30, 40), dtype=bool)
    mask[5:20, 10:35] = True
    draft = ProjectDraft()
    out = draft._write_mask_png(mask, alien_dir / "输出 out", "roi_mask.png")
    assert out is not None and out.exists() and out.stat().st_size > 0
    back = decode_mask_png(out.read_bytes())
    assert np.array_equal(back, mask)
    # and the generic image reader can open it too (runner reads the brush PNG)
    gray = imread_unicode(out, cv2.IMREAD_GRAYSCALE)
    assert gray is not None and (gray > 0).sum() == mask.sum()


# ---------------------------------------------------------------------------
# calibration YAML: our writer AND the importer funnel
# ---------------------------------------------------------------------------


def test_calibration_yaml_roundtrip_under_alien_path(alien_dir: Path) -> None:
    rig = _rig()
    path = to_opencv_yaml(
        rig, alien_dir / "标定 결과.yaml", meta={"rms_px": 0.21, "source": "gui builtin"}
    )
    assert path.exists() and path.stat().st_size > 0

    for back in (from_opencv_yaml(path), load_calibration(path, "opencv_yaml")):
        for cam in ("L", "R"):
            assert np.allclose(back.cameras[cam].K, rig.cameras[cam].K)
            assert np.allclose(back.cameras[cam].dist_coeffs, rig.cameras[cam].dist_coeffs)
        r0, t0 = rig.pose("R")
        r1, t1 = back.pose("R")
        assert np.allclose(r0, r1) and np.allclose(t0, t1)


def test_detections_npz_roundtrip_under_alien_path(alien_dir: Path) -> None:
    det = BoardDetection(
        ok=True,
        image_points=np.array([[1.0, 2.0], [3.0, 4.0]]),
        object_points=np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]),
        ids=np.array([0, 1], dtype=np.int64),
        method="chessboard",
        reason="",
    )
    path = save_detections(
        alien_dir / "检测 corners.npz", ["l0.png"], ["r0.png"], [det], [det], image_size=(64, 48)
    )
    files_l, _files_r, dl, _dr, size = load_detections(path)
    assert files_l == ["l0.png"] and size == (64, 48)
    assert dl[0].ok and np.allclose(dl[0].image_points, det.image_points)


# ---------------------------------------------------------------------------
# .aldic3d session save / load
# ---------------------------------------------------------------------------


def test_session_roundtrip_under_alien_path(alien_dir: Path) -> None:
    mask = np.zeros((20, 20), dtype=bool)
    mask[4:16, 4:16] = True
    draft = ProjectDraft(roi=(4, 16, 4, 16), roi_mask_array=mask)
    state = AppState3D(draft=draft, result=_tiny_result(), workflow_step=6)
    path = save_session(state, alien_dir / "项目 세션.aldic3d")
    assert path.exists()

    loaded = load_session(path)
    assert tuple(loaded.draft.roi) == (4, 16, 4, 16)
    assert loaded.draft.roi_mask_array is not None
    assert np.array_equal(np.asarray(loaded.draft.roi_mask_array) > 0, mask)
    assert loaded.result is not None
    assert np.allclose(loaded.result.reconstruction.points, state.result.reconstruction.points)


# ---------------------------------------------------------------------------
# exports: npz / mat / csv / png images / animation
# ---------------------------------------------------------------------------


def test_table_exports_under_alien_path(alien_dir: Path) -> None:
    result = _tiny_result()
    out = alien_dir / "导出 tables"

    npz_path = export_npz(result, ["U", "mag"], out, "run 结果")
    npz = np.load(npz_path)
    assert "U" in npz and npz["U"].shape == (2, 25)

    import scipy.io

    mat_path = export_mat(result, ["U"], out, "run 结果")
    assert "U" in scipy.io.loadmat(str(mat_path))

    csvs = export_csv_frames(result, ["U"], out, "run 结果")
    assert len(csvs) == 2
    header = csvs[0].read_text(encoding="utf-8").splitlines()[0]
    assert header.startswith("x_px,y_px")


def test_image_export_under_alien_path(alien_dir: Path) -> None:
    result = _tiny_result()
    paths = export_image_frames(
        alien_dir / "导出 images",
        "run",
        "20260729",
        result,
        {},  # no backgrounds: black canvas at meta["image_size"]
        [FieldImageConfig(field_id="U")],
        include_colorbar=False,
        output_max_dim=160,
    )
    assert paths, "image export produced no files under the alien path"
    for p in paths:
        assert p.exists() and p.stat().st_size > 0
        decoded = imread_unicode(p)
        assert decoded is not None and decoded.size > 0


def test_animation_writer_under_alien_path(alien_dir: Path) -> None:
    """cv2.VideoWriter (FFMPEG) handles UTF-8 paths itself on Windows — this
    regression test pins that, so an OpenCV build that loses the behavior is
    caught here instead of by a user with a CJK user name."""
    frame = np.zeros((32, 40, 3), dtype=np.uint8)
    frame[8:24, 10:30] = (0, 255, 0)
    w = StreamingAnimWriter("mp4", alien_dir, "动画 anim", 5, (32, 40))
    if not w.ok:
        w.close()
        pytest.skip("no mp4v/XVID encoder available in this OpenCV build")
    for _ in range(3):
        w.append(frame)
    w.close()
    assert w.out.exists() and w.out.stat().st_size > 0


def test_gif_writer_under_alien_path(alien_dir: Path) -> None:
    pytest.importorskip("imageio")
    frame = np.zeros((32, 40, 3), dtype=np.uint8)
    w = StreamingAnimWriter("gif", alien_dir, "动画 anim", 5, (32, 40))
    for _ in range(2):
        w.append(frame)
    w.close()
    assert w.out.exists() and w.out.stat().st_size > 0
