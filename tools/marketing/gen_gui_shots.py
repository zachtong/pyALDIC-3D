"""Real pyALDIC-3D GUI screenshots for the README -> ``assets/*.png``.

Every shot is the ACTUAL application rendered offscreen (``QT_QPA_PLATFORM=
offscreen``) after a REAL end-to-end run: a curved synthetic stereo scene
(``tests/synth_surface.py`` — Gaussian-bump surface under a known 3D Lagrangian
displacement, rendered through two distorted converging cameras) is loaded,
correlated, reconstructed and post-processed by the shipping code path. Nothing
here is drawn by hand.

Produces:
    assets/main_page.png     three-column main window with the displacement field
    assets/strain_window.png the strain post-processing window
    assets/export_window.png the tabbed export dialog (3D View tab)
    assets/i18n_zh.png       the same window under the zh_CN translation

The interactive 3D view is NOT captured here: the Qt offscreen platform has no
OpenGL context, so the embedded VTK widget cannot render. The 3D surface figure
comes from the Qt-free export path instead — see ``fig_surface_3d.py``.

Run:  python tools/marketing/gen_gui_shots.py
"""
# ruff: noqa: E402  (Qt platform must be selected before any Qt import)

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# The offscreen platform ships no font database on Windows -> tofu boxes.
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _style import ASSETS, optimize_png

SIZE = (2124, 1485)  # 16:11 desktop-ish; downscaled on save
IMG = 900  # synthetic camera resolution (px)
N_FRAMES = 6
DEFORM = 0.30
SUBSET, STEP = 33, 16  # subset is the GUI's ODD display convention (32 internally)
ROI_LO, ROI_HI = 0.23, 0.77


def _grab(widget, name: str, *, size: tuple[int, int] = SIZE) -> Path:
    from PySide6.QtWidgets import QApplication

    widget.resize(*size)
    for _ in range(3):
        QApplication.processEvents()
    out = ASSETS / name
    out.parent.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(out))
    print(f"  grabbed {name}")
    return out


def _settle(n: int = 4) -> None:
    from PySide6.QtWidgets import QApplication

    for _ in range(n):
        QApplication.processEvents()


def main() -> int:
    from al_dic_3d.gui.app import create_app
    from al_dic_3d.gui.main_window import MainWindow3D

    app = create_app([])

    import synth_surface

    workdir = Path(tempfile.mkdtemp(prefix="aldic3d_mkt_"))
    print(f"rendering synthetic stereo scene in {workdir} ...")
    scene = synth_surface.build_surface_scene(
        workdir, img=IMG, n_frames=N_FRAMES, deform=DEFORM, seed=7
    )

    win = MainWindow3D()
    win.show()

    draft = win.controller.state.draft
    draft.left = sorted(str(p) for p in scene["dir"].glob("L_*.png"))
    draft.right = sorted(str(p) for p in scene["dir"].glob("R_*.png"))
    draft.calibration_file = scene["dir"] / "calib.yml"
    draft.calibration_format = "opencv_yaml"
    lo, hi = int(ROI_LO * IMG), int(ROI_HI * IMG)
    draft.roi = (lo, hi, lo, hi)
    draft.winsize = SUBSET
    draft.winstepsize = STEP
    draft.stereo_search = 96
    draft.fft_search = 48
    win._left.refresh_all()
    win.signals.images_changed.emit()
    win.signals.roi_changed.emit()
    _settle()

    print("running the pipeline through the GUI controller ...")
    win.controller.run()
    win._right._on_done()
    # Show W (out-of-plane) — the quantity only a stereo rig can give. Go through
    # the selector so its toggle buttons stay in sync with the canvas colorbar.
    win.signals.set_display_field("W")
    win._right._field_selector._sync_checked()
    win.signals.set_current_frame(N_FRAMES - 1, N_FRAMES)
    win._canvas_area._canvas.fit_to_view()
    win._canvas_area.render()
    _settle()
    main_png = _grab(win, "main_page.png")

    # ---- strain post-processing window ----
    strain_win = win._strain_window
    strain_win.trigger_compute()
    _settle(6)
    strain_win.set_strain_frame(N_FRAMES - 1)
    _settle(4)
    strain_png = _grab(strain_win, "strain_window.png", size=(1450, 1000))

    # ---- export dialog, parked on the 3D View tab (a 2D-app-free capability) ----
    from al_dic_3d.export import VizExportHint
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog, draft_export_params

    dlg = ExportDialog(
        win.controller.state.result,
        draft_export_params(draft),
        parent=win,
        draft=draft,
        hint=VizExportHint(),
    )
    dlg.show()
    _settle()
    for i in range(dlg._tabs.count()):
        if "3D" in dlg._tabs.tabText(i):
            dlg._tabs.setCurrentIndex(i)
            break
    _settle()
    export_png = _grab(dlg, "export_window.png", size=(1000, 640))
    dlg.close()

    # ---- i18n proof: a fresh window under the zh_CN translation ----
    from al_dic_3d.i18n import install_translators

    install_translators(app, locale="zh_CN")
    win_zh = MainWindow3D()
    win_zh.show()
    win_zh.controller.state.draft = draft
    win_zh.controller.state.result = win.controller.state.result
    win_zh._left.refresh_all()
    win_zh.signals.images_changed.emit()
    win_zh.signals.roi_changed.emit()
    win_zh._right._on_done()
    win_zh.signals.set_current_frame(N_FRAMES - 1, N_FRAMES)
    win_zh._canvas_area._canvas.fit_to_view()
    win_zh._canvas_area.render()
    _settle()
    zh_png = _grab(win_zh, "i18n_zh.png")

    for path, width in (
        (main_png, 1700),
        (zh_png, 1500),
        (strain_png, 1500),
        (export_png, 1000),
    ):
        optimize_png(path, max_width=width)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
