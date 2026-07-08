"""Rendered-media export (Batch E2): images, streaming animation, 3D view.

Runs the real pipeline once on the synthetic parity scene, then exercises the
Qt-free exporters end-to-end: per-camera field frames composited over the real
camera images, the streaming MP4/GIF writers with frame decimation, the
offscreen pyvista 3D-view render, and cooperative cancellation leaving partial
output. No Qt anywhere in this module — the exporters must work headless.
"""

from __future__ import annotations

import threading

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d.export import (  # noqa: E402
    FieldImageConfig,
    animation_fps,
    colorbar_label,
    export_animation,
    export_image_frames,
    output_shape_for,
    render_field_frame,
)


@pytest.fixture(scope="module")
def scene(tmp_path_factory):
    from tests import synth_parity

    d = tmp_path_factory.mktemp("render_src")
    return synth_parity.build_parity_scene(d, img=200, n_frames=3, seed=7)


@pytest.fixture(scope="module")
def result(scene):
    from dataclasses import replace

    from al_dic_3d.runner import load_config, run_pipeline
    from tests import synth_parity

    cfg = replace(
        load_config(synth_parity.write_config(scene["dir"], scene)),
        compute_strain=True,
    )
    return run_pipeline(cfg)


@pytest.fixture(scope="module")
def image_files(scene):
    return {
        "L": sorted(str(p) for p in scene["dir"].glob("L_*.png")),
        "R": sorted(str(p) for p in scene["dir"].glob("R_*.png")),
    }


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_output_shape_for_caps_long_edge():
    assert output_shape_for((2000, 1000), 1024) == (1024, 512)
    assert output_shape_for((1000, 2000), 500) == (250, 500)
    assert output_shape_for((300, 400), 1024) == (300, 400)  # already within cap
    assert output_shape_for((300, 400), 0) == (300, 400)  # 0 = full resolution


def test_colorbar_label_units():
    # 3D displacements are metric (calibrated triangulation) -> (mm).
    assert colorbar_label("U") == "U (mm)"
    assert colorbar_label("mag") == "|D| (mm)"
    # Strain is dimensionless -> bare math label.
    assert colorbar_label("exx") == "εxx"
    assert colorbar_label("von_mises") == "von Mises"


def test_animation_fps_preserves_duration():
    assert animation_fps(10, 1) == (1, 10)
    assert animation_fps(10, 2) == (2, 5)
    assert animation_fps(10, 4) == (4, 2)  # round(10/4) = 2
    assert animation_fps(10, 20) == (20, 1)  # floor at 1 fps
    assert animation_fps(10, 0) == (1, 10)  # step floored at 1


# ---------------------------------------------------------------------------
# Single-frame render
# ---------------------------------------------------------------------------


def test_render_field_frame_composites_over_background(result, image_files):
    bg = cv2.imread(image_files["L"][1], cv2.IMREAD_GRAYSCALE)
    cfg = FieldImageConfig(field_id="U", opacity=0.85)
    rendered = render_field_frame(result, "L", "U", 1, bg, cfg, mesh_step=16, show_deformed=True)
    assert rendered is not None
    img, vmin, vmax = rendered
    assert img.shape == (*bg.shape, 3) and img.dtype == np.uint8
    assert vmax > vmin
    # The overlay changed pixels vs the plain background (field visible)...
    bg_bgr = cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR)
    assert (img != bg_bgr).any()
    # ... but pixels outside the node hull keep the untouched background.
    assert (img[:5, :5] == bg_bgr[:5, :5]).all()


def test_render_field_frame_resolution_cap(result, image_files):
    bg = cv2.imread(image_files["L"][0], cv2.IMREAD_GRAYSCALE)
    cfg = FieldImageConfig(field_id="W")
    rendered = render_field_frame(result, "L", "W", 1, bg, cfg, mesh_step=16, output_max_dim=128)
    assert rendered is not None
    assert max(rendered[0].shape[:2]) == 128


def test_render_field_frame_right_camera_and_fixed_range(result, image_files):
    bg = cv2.imread(image_files["R"][2], cv2.IMREAD_GRAYSCALE)
    cfg = FieldImageConfig(field_id="V", auto_range=False, vmin=-1.0, vmax=1.0)
    rendered = render_field_frame(result, "R", "V", 2, bg, cfg, mesh_step=16, show_deformed=True)
    assert rendered is not None
    _, vmin, vmax = rendered
    assert (vmin, vmax) == (-1.0, 1.0)  # fixed range honored


def test_render_field_frame_unavailable_field_returns_none(result, image_files):
    from dataclasses import replace

    bg = cv2.imread(image_files["L"][0], cv2.IMREAD_GRAYSCALE)
    no_strain = replace(result, strain=None)
    cfg = FieldImageConfig(field_id="exx")
    assert render_field_frame(no_strain, "L", "exx", 1, bg, cfg, mesh_step=16) is None


# ---------------------------------------------------------------------------
# Batch image export
# ---------------------------------------------------------------------------


def test_export_image_frames_writes_camera_field_tree(result, image_files, tmp_path):
    configs = [
        FieldImageConfig(field_id="U"),
        FieldImageConfig(field_id="W"),
        FieldImageConfig(field_id="V", enabled=False),  # disabled -> skipped
    ]
    paths = export_image_frames(
        tmp_path,
        "run",
        "20260708000000",
        result,
        image_files,
        configs,
        cameras=("L", "R"),
        mesh_step=16,
        include_colorbar=False,
        output_max_dim=0,
    )
    n_frames = result.reconstruction.n_frames
    assert len(paths) == 2 * 2 * n_frames  # 2 cameras x 2 enabled fields
    root = tmp_path / "run_images_20260708000000"
    assert sorted(p.name for p in root.iterdir()) == ["L_U", "L_W", "R_U", "R_W"]
    for p in paths:
        assert p.exists() and p.stat().st_size > 0
    assert len(list((root / "L_U").glob("frame_*.png"))) == n_frames


def test_export_image_frames_colorbar_widens_frames(result, image_files, tmp_path):
    kw = dict(cameras=("L",), mesh_step=16, frame_start=1, frame_end=1, output_max_dim=256)
    cfgs = [FieldImageConfig(field_id="U")]
    (plain,) = export_image_frames(
        tmp_path,
        "p",
        "20260708000001",
        result,
        image_files,
        cfgs,
        include_colorbar=False,
        **kw,
    )
    (with_cb,) = export_image_frames(
        tmp_path,
        "p",
        "20260708000002",
        result,
        image_files,
        cfgs,
        include_colorbar=True,
        **kw,
    )
    w_plain = cv2.imread(str(plain)).shape[1]
    w_cb = cv2.imread(str(with_cb)).shape[1]
    assert w_cb > w_plain  # colorbar strip appended on the right


def test_export_image_frames_jpeg_and_progress(result, image_files, tmp_path):
    seen: list[tuple[int, int, str]] = []
    paths = export_image_frames(
        tmp_path,
        "q",
        "20260708000003",
        result,
        image_files,
        [FieldImageConfig(field_id="U")],
        cameras=("L",),
        mesh_step=16,
        image_format="jpeg",
        jpeg_quality=80,
        include_colorbar=False,
        output_max_dim=256,
        progress_cb=lambda d, t, s: seen.append((d, t, s)),
    )
    n_frames = result.reconstruction.n_frames
    assert all(p.suffix == ".jpg" for p in paths)
    assert seen[-1][:2] == (n_frames, n_frames)


def test_export_image_frames_stop_event_leaves_partial_output(result, image_files, tmp_path):
    stop = threading.Event()

    def cancel_after_first(done: int, total: int, label: str) -> None:
        stop.set()  # cancel after the first frame completes

    paths = export_image_frames(
        tmp_path,
        "c",
        "20260708000004",
        result,
        image_files,
        [FieldImageConfig(field_id="U")],
        cameras=("L",),
        mesh_step=16,
        include_colorbar=False,
        output_max_dim=256,
        stop_event=stop,
        progress_cb=cancel_after_first,
    )
    n_frames = result.reconstruction.n_frames
    assert 0 < len(paths) < n_frames  # partial output remains on disk
    assert all(p.exists() for p in paths)


# ---------------------------------------------------------------------------
# Animation export
# ---------------------------------------------------------------------------


def test_export_animation_mp4_with_frame_step(result, image_files, tmp_path):
    paths = export_animation(
        tmp_path,
        "a",
        "20260708000005",
        result,
        image_files,
        [FieldImageConfig(field_id="U")],
        cameras=("L",),
        fmt="mp4",
        fps=10,
        frame_step=2,
        mesh_step=16,
        include_colorbar=True,
        output_max_dim=256,
    )
    assert len(paths) == 1
    out = paths[0]
    assert out.name in ("L_U.mp4", "L_U.avi") and out.stat().st_size > 0
    cap = cv2.VideoCapture(str(out))
    assert cap.isOpened()
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    # 3 frames, step 2 -> indices [0, 2]; out_fps = round(10/2) = 5.
    assert n == 2
    assert fps == pytest.approx(5.0, abs=0.5)


def test_export_animation_gif_per_camera_field(result, image_files, tmp_path):
    paths = export_animation(
        tmp_path,
        "g",
        "20260708000006",
        result,
        image_files,
        [FieldImageConfig(field_id="U"), FieldImageConfig(field_id="W")],
        cameras=("L", "R"),
        fmt="gif",
        fps=5,
        mesh_step=16,
        include_colorbar=False,
        output_max_dim=128,
    )
    assert sorted(p.name for p in paths) == ["L_U.gif", "L_W.gif", "R_U.gif", "R_W.gif"]
    assert all(p.stat().st_size > 0 for p in paths)


def test_export_animation_stop_event(result, image_files, tmp_path):
    stop = threading.Event()
    stop.set()  # cancel immediately: no frame is ever rendered
    paths = export_animation(
        tmp_path,
        "s",
        "20260708000007",
        result,
        image_files,
        [FieldImageConfig(field_id="U")],
        cameras=("L",),
        fmt="mp4",
        fps=10,
        mesh_step=16,
        output_max_dim=128,
        stop_event=stop,
    )
    assert paths == []


# ---------------------------------------------------------------------------
# 3D view export (offscreen pyvista)
# ---------------------------------------------------------------------------


def _require_offscreen_gl():
    pv = pytest.importorskip("pyvista")
    try:  # a machine without any usable GL context cannot render offscreen
        pl = pv.Plotter(off_screen=True, window_size=[32, 32])
        pl.add_mesh(pv.Sphere())
        pl.screenshot(return_img=True)
        pl.close()
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"no offscreen GL context: {exc}")


def test_render_view3d_frame_offscreen(result):
    _require_offscreen_gl()
    from al_dic_3d.export import render_view3d_frame

    vals = result.reconstruction.displacement[1][:, 0]
    img = render_view3d_frame(
        result.reconstruction.points[1],
        vals,
        field_label="U (mm)",
        cmap="turbo",
        vmin=float(np.nanmin(vals)),
        vmax=float(np.nanmax(vals)),
        ref_coords=result.ref_coords,
        window_size=(320, 240),
    )
    assert img is not None and img.shape == (240, 320, 3) and img.dtype == np.uint8
    assert img.std() > 0  # an actual render, not a constant canvas


def test_export_view3d_sequence_and_animation(result, tmp_path):
    _require_offscreen_gl()
    from al_dic_3d.export import export_view3d_frames

    paths = export_view3d_frames(
        tmp_path,
        "v",
        "20260708000008",
        result,
        "U",
        window_size=(320, 240),
        write_frames=True,
        animation_format="mp4",
        fps=10,
    )
    n_frames = result.reconstruction.n_frames
    root = tmp_path / "v_view3d_20260708000008"
    pngs = sorted((root / "U").glob("frame_*.png"))
    assert len(pngs) == n_frames
    anim = [p for p in paths if p.suffix in (".mp4", ".avi")]
    assert len(anim) == 1 and anim[0].stat().st_size > 0


def test_export_view3d_turntable(result, tmp_path):
    _require_offscreen_gl()
    from al_dic_3d.export import export_view3d_turntable

    seen: list[int] = []
    paths = export_view3d_turntable(
        tmp_path,
        "t",
        "20260708000009",
        result,
        "W",
        frame_k=1,
        n_orbit=4,
        window_size=(320, 240),
        animation_format="mp4",
        progress_cb=lambda d, t, s: seen.append(d),
    )
    assert len(paths) == 1 and paths[0].stem == "W_turntable"
    assert seen == [1, 2, 3, 4]
    cap = cv2.VideoCapture(str(paths[0]))
    assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) == 4
    cap.release()


# ---------------------------------------------------------------------------
# Export dialog tabs (offscreen Qt; worker threads end-to-end)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def qapp():
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    pytest.importorskip("PySide6")
    from al_dic_3d.gui.app import create_app

    return create_app([])


@pytest.fixture()
def dialog(qapp, result, image_files, tmp_path):
    from al_dic_3d.export import VizExportHint
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog
    from al_dic_3d.project.draft import ProjectDraft

    draft = ProjectDraft(left=list(image_files["L"]), right=list(image_files["R"]))
    hint = VizExportHint(
        colormap="viridis",
        show_deformed=True,
        overlay_alpha=0.6,
        current_field="W",
        current_frame=1,
    )
    dlg = ExportDialog(result, extra_params={"winsize": 32}, draft=draft, hint=hint)
    dlg._folder_edit.setText(str(tmp_path))
    yield dlg
    dlg.close()


def test_dialog_has_four_tabs_and_hint_prefill(dialog):
    tabs = dialog._tabs
    assert tabs.count() == 4
    # Images tab prefilled from the VizExportHint (colormap/opacity/deformed).
    row = dialog._images_tab._rows._rows[0]
    assert row._cmap_combo.currentText() == "viridis"
    assert row._alpha_spin.value() == pytest.approx(0.6)
    assert dialog._images_tab._background_row.show_deformed()
    # Default-enabled media fields = U, V, W (mag + strain off).
    enabled = [c.field_id for c in dialog._images_tab._rows.enabled_configs()]
    assert enabled == ["U", "V", "W"]
    # 3D View tab preselects the hint's current field.
    assert dialog._view3d_tab._field_combo.currentData() == "W"


def test_images_tab_worker_exports(dialog, tmp_path):
    tab = dialog._images_tab
    # Enable only U to keep the run short; fixed small resolution.
    for row in tab._rows._rows:
        row._check.setChecked(row._field_id == "U")
    tab._resolution_combo.setCurrentIndex(tab._resolution_combo.findData(512))
    tab._colorbar_check.setChecked(False)
    tab.start_export()
    assert dialog.wait_for_export()
    root = next(tmp_path.glob("*_images_*"))
    n_frames = dialog.result.reconstruction.n_frames
    assert len(list((root / "L_U").glob("frame_*.png"))) == n_frames
    assert "file" in tab._progress._status.text()


def test_animation_tab_worker_exports(dialog, tmp_path):
    tab = dialog._animation_tab
    for row in tab._rows._rows:
        row._check.setChecked(row._field_id == "U")
    tab._resolution_combo.setCurrentIndex(tab._resolution_combo.findData(512))
    tab._colorbar_check.setChecked(False)
    tab.start_export()
    assert dialog.wait_for_export()
    root = next(tmp_path.glob("*_animation_*"))
    outs = list(root.glob("L_U.*"))
    assert len(outs) == 1 and outs[0].stat().st_size > 0


def test_images_tab_requires_folder(dialog):
    dialog._folder_edit.setText("")
    dialog._images_tab.start_export()
    assert not dialog._images_tab.is_busy()  # refused synchronously
    assert dialog._images_tab._progress._status.text()
