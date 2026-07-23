"""Batch C — WYSIWYG parity of strain_valid + crack blanking across consumers.

Covers the C3/C4 "under-wired" fixes: every export/render path applies the same
``strain_valid`` display mask the strain canvas does (C3-1/C3-2/C3-3) and the
crack-barrier blanking reaches the animation and 3D-surface consumers (C4). The
crack-FREE path stays untouched everywhere (byte-identity), so these only assert
new behavior on crack-aware / trimmed data.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")


def _result(
    img: int = 200, *, crack_aware: bool = True, trim_band: bool = True, band_val: float = 0.5
):
    """A synthetic RunResult: grid nodes, a uniform U shift, and (optionally) a
    strain field whose trimmed left band carries biased (extreme) values."""
    from al_dic_3d.matching.contracts import TRACKED, CorrespondenceSet
    from al_dic_3d.reconstruct import Reconstruction3D
    from al_dic_3d.runner import RunResult
    from al_dic_3d.strain3d.model import STRAIN_FIELDS, StrainResult3D

    step = 16
    axis = np.arange(24, img - 24, step)
    xx, yy = np.meshgrid(axis, axis)
    ref_2d = np.column_stack([xx.ravel(), yy.ravel()]).astype(np.float64)
    npts = ref_2d.shape[0]
    nf = 2
    base = np.column_stack([ref_2d, np.full(npts, 800.0)])
    pts = np.stack([base, base + np.array([0.5, 0.0, 0.0])])  # uniform +0.5 U shift
    disp = pts - pts[0][None]
    rec = Reconstruction3D(pts, disp, np.zeros((nf, npts)), np.full((nf, npts), TRACKED, np.uint8))
    xL = np.stack([ref_2d, ref_2d + np.array([0.5, 0.0])])
    cs = CorrespondenceSet(
        strategy="track_both",
        xL=xL.copy(),
        xR=xL.copy(),
        quality=np.zeros((nf, npts)),
        source=np.full((nf, npts), TRACKED, np.uint8),
    )
    strain = None
    if trim_band:
        band = ref_2d[:, 0] < np.median(ref_2d[:, 0])  # left ~half of nodes
        # A gentle spatial gradient on the VALID nodes (so the visible range is
        # non-degenerate) with a large biased value in the trimmed band.
        grad = 1e-3 + 2e-3 * (ref_2d[:, 0] - ref_2d[:, 0].min()) / np.ptp(ref_2d[:, 0])
        fields = {n: np.full((nf, npts), 1e-3, dtype=np.float64) for n in STRAIN_FIELDS}
        fields["exx"][:] = grad
        fields["exx"][1, band] = band_val  # biased one-sided-gauge values (frame 1)
        valid = np.ones((nf, npts), dtype=bool)
        valid[1, band] = False
        n_trimmed = np.array([0, int(band.sum())], dtype=np.int64)
        strain = StrainResult3D(**fields, strain_valid=valid, n_trimmed=n_trimmed)
    meta = {"crack_aware": crack_aware, "image_size": (img, img), "n_frames": nf}
    return RunResult("track_both", ref_2d, cs, rec, strain=strain, meta=meta)


# ---------------------------------------------------------------------------
# C3-1 — image / animation / 3D-view exports apply strain_valid before range
# ---------------------------------------------------------------------------


def test_c3_display_field_frame_masks_trimmed_nodes():
    from al_dic_3d.export import display_field_frame, field_frame

    r = _result(band_val=0.5)
    band = r.ref_coords[:, 0] < np.median(r.ref_coords[:, 0])
    dense = field_frame(r, "exx", 1)
    masked = display_field_frame(r, "exx", 1, deformed=True)
    assert np.isnan(masked[band]).all(), "trimmed nodes NaN-masked for display"
    assert np.isfinite(masked[~band]).all()
    np.testing.assert_array_equal(masked[~band], dense[~band])  # values stay dense
    # Reference view (deformed=False) uses frame-0 validity (all valid here).
    assert np.isfinite(display_field_frame(r, "exx", 0, deformed=False)).all()
    # Displacement fields pass through unchanged.
    np.testing.assert_array_equal(
        display_field_frame(r, "U", 1, deformed=True), field_frame(r, "U", 1)
    )


def test_c3_export_range_excludes_trimmed_band():
    from al_dic_3d.export import field_color_range
    from al_dic_3d.export.render3d import _stable_field_range

    r = _result(band_val=0.5)  # trimmed band carries 0.5, valid nodes 1e-3
    # Image/animation export auto-range (2-98 percentile of VISIBLE nodes).
    _lo, hi = field_color_range(r, "L", "exx", 1, None, deformed=True)
    assert hi < 0.1, "trimmed one-sided-gauge band must not stretch the export range"
    # 3D-view stable range (nanmax over frames) likewise excludes the trimmed band.
    _lo3, hi3 = _stable_field_range(r, "exx")
    assert hi3 < 0.1


# ---------------------------------------------------------------------------
# C3-2 — GUI data export carries strain_valid on every format
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def qapp():
    from al_dic_3d.gui.app import create_app

    return create_app([])


def test_c3_gui_data_export_carries_strain_valid(qapp, tmp_path):
    from types import SimpleNamespace

    from al_dic_3d.export import export_csv_frames, export_npz
    from al_dic_3d.gui.dialogs.export_tabs.data_tab import DataTab

    r = _result()
    tab = DataTab(SimpleNamespace(result=r))
    fields = tab.selected_fields()
    assert "strain_valid" in fields, "GUI data export must request strain_valid"

    npz = np.load(export_npz(r, fields, tmp_path, "sel"))
    assert "strain_valid" in npz
    np.testing.assert_array_equal(npz["strain_valid"], r.strain.strain_valid)

    csvs = export_csv_frames(r, fields, tmp_path, "sel")
    header = csvs[0].read_text(encoding="utf-8").splitlines()[0]
    assert "strain_valid" in header

    # Strain-free result: nothing extra appended (byte-identity with pre-C3).
    plain = _result(trim_band=False)
    assert "strain_valid" not in DataTab(SimpleNamespace(result=plain)).selected_fields()


# ---------------------------------------------------------------------------
# C3-3 — trim readout survives a reload where only strain_valid persisted
# ---------------------------------------------------------------------------


def test_c3_trim_count_derived_after_reload():
    from al_dic_3d.gui.strain_render import trim_count
    from al_dic_3d.strain3d.model import STRAIN_FIELDS, StrainResult3D

    valid = np.ones((2, 9), dtype=bool)
    valid[1, :3] = False
    fields = {n: np.zeros((2, 9), dtype=np.float64) for n in STRAIN_FIELDS}
    # Reload: strain_valid persisted, n_trimmed is None -> derive the count.
    reloaded = StrainResult3D(**fields, strain_valid=valid, n_trimmed=None)
    assert trim_count(reloaded, 1) == 3
    assert trim_count(reloaded, 0) == 0
    # Fresh compute: n_trimmed present -> used directly.
    fresh = StrainResult3D(**fields, strain_valid=valid, n_trimmed=np.array([0, 3]))
    assert trim_count(fresh, 1) == 3
    # No trimming at all -> None (readout hidden).
    assert trim_count(StrainResult3D(**fields), 1) is None


# ---------------------------------------------------------------------------
# C4 — barrier blanking reaches animation, 3D surface, and the main canvas
# ---------------------------------------------------------------------------


def test_c4_animation_passes_barrier_when_crack_aware(tmp_path, monkeypatch):
    import al_dic_3d.export.animation as anim
    from al_dic_3d.export import FieldImageConfig

    roi = np.ones((200, 200), dtype=bool)
    roi[:, 95:98] = False  # thin crack band (interior)
    captured: dict[str, list] = {}
    real = anim.render_field_frame

    def spy(result, cam, field, k, bg, cfg, **kw):
        captured.setdefault(cam, []).append(kw.get("barrier_mask"))
        return real(result, cam, field, k, bg, cfg, **kw)

    monkeypatch.setattr(anim, "render_field_frame", spy)

    r = _result(crack_aware=True)
    anim.export_animation(
        tmp_path,
        "a",
        "ts",
        r,
        {},
        [FieldImageConfig("U")],
        cameras=("L",),
        fmt="mp4",
        show_deformed=False,
        roi_mask=roi,
    )
    assert captured.get("L"), "animation must render the L camera"
    assert all(b is not None for b in captured["L"]), "video frames must blank the crack"

    # Crack-free: no barrier passed (byte-identical video frames).
    captured.clear()
    anim.export_animation(
        tmp_path,
        "b",
        "ts",
        _result(crack_aware=False),
        {},
        [FieldImageConfig("U")],
        cameras=("L",),
        fmt="mp4",
        show_deformed=False,
        roi_mask=roi,
    )
    assert all(b is None for b in captured["L"])


def test_c4_surface_wrappers_forward_barrier():
    pytest.importorskip("pyvista")
    from al_dic_3d.export.render3d import build_surface
    from al_dic_3d.gui.widgets.view3d import build_surface_mesh

    step, origin, nx = 16, 40, 13
    ii, jj = np.meshgrid(np.arange(nx), np.arange(nx))
    ref = np.column_stack([ii.ravel() * step + origin, jj.ravel() * step + origin]).astype(float)
    pts = np.column_stack([ref * 0.1, np.full(len(ref), 800.0)])
    vals = ref[:, 0] * 1e-3
    xc = origin + 6 * step + 8
    barrier = np.ones((260, 260), dtype=np.float64)
    barrier[:, xc - 1 : xc + 2] = 0.0

    # Interactive View3D wrapper: barrier drops crack-bridging quads.
    s_plain = build_surface_mesh(pts, vals, "U", ref)
    s_crack = build_surface_mesh(pts, vals, "U", ref, barrier_mask=barrier)
    assert s_crack.n_cells < s_plain.n_cells

    # Qt-free exporter wrapper: same.
    e_plain = build_surface(pts, vals, "U", ref)
    e_crack = build_surface(pts, vals, "U", ref, barrier)
    assert e_crack.n_cells < e_plain.n_cells

    # No barrier -> byte-identical cell count (crack-free surfaces untouched).
    assert build_surface_mesh(pts, vals, "U", ref, barrier_mask=None).n_cells == s_plain.n_cells


@pytest.fixture(scope="module")
def canvas_image(tmp_path_factory):
    d = tmp_path_factory.mktemp("crack_canvas")
    rng = np.random.default_rng(1)
    p = d / "L_000.png"
    cv2.imwrite(str(p), rng.integers(0, 255, size=(200, 200), dtype=np.uint8))
    return str(p)


def _canvas(qapp, image):
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.panels.canvas_area import CanvasArea3D
    from al_dic_3d.gui.state import GuiSignals

    controller = WorkflowController()
    signals = GuiSignals()
    area = CanvasArea3D(controller, signals)
    area.show()
    controller.state.draft.left = [image]
    signals.images_changed.emit()  # loads the background -> valid scene rect
    return area, signals


def test_c4_canvas_displacement_passes_barrier(qapp, canvas_image, monkeypatch):
    area, signals = _canvas(qapp, canvas_image)
    signals.show_deformed = False
    signals.current_camera = "L"
    roi = np.ones((200, 200), dtype=bool)
    roi[:, 95:98] = False

    def _drive(result):
        area.controller.state.result = result
        area.controller.state.draft.roi_mask_array = roi
        area._right_mask_dirty = True
        captured: list = []
        real = area._viz_ctrl.render_field

        def spy(*args, **kwargs):
            captured.append(kwargs.get("barrier_mask"))
            return real(*args, **kwargs)

        monkeypatch.setattr(area._viz_ctrl, "render_field", spy)
        area._render_overlay(0)
        monkeypatch.undo()
        return captured

    crack = _drive(_result(crack_aware=True))
    assert crack and crack[-1] is not None, "crack-aware L reference overlay must blank the crack"

    plain = _drive(_result(crack_aware=False))
    assert plain and plain[-1] is None, "crack-free overlay passes no barrier (byte-identical)"
