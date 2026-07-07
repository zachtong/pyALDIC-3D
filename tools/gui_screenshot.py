"""Offscreen GUI screenshot harness — the visual self-check loop.

Renders MainWindow3D offscreen at the reference resolution, in three states
(empty / loaded / with results), and saves PNGs for comparison against the
pyALDIC target screenshots in assets/. Dev tool; not part of the app.

Run:  python tools/gui_screenshot.py [outdir]
"""
# ruff: noqa: E402  (Qt platform must be set before any Qt import)

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# The offscreen platform has no font database by default on Windows -> tofu.
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from al_dic_3d.gui.app import create_app
from al_dic_3d.gui.main_window import MainWindow3D

SIZE = (2124, 1485)  # assets/main_page.png resolution


def _grab(win, path: Path) -> None:
    from PySide6.QtWidgets import QApplication

    win.resize(*SIZE)
    QApplication.processEvents()
    QApplication.processEvents()
    pixmap = win.grab()
    path.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(str(path))
    print(f"wrote {path} ({pixmap.width()}x{pixmap.height()})")


def main(outdir: str | None = None) -> int:
    out = Path(outdir) if outdir else REPO / "reports" / "gui_shots"
    app = create_app([])  # noqa: F841 — keep the QApplication alive for the session

    # --- state 1: empty ---
    win = MainWindow3D()
    win.show()
    _grab(win, out / "shot_empty.png")

    # --- state 2: loaded project (images + calib + ROI) ---
    import synth_parity

    workdir = Path(tempfile.mkdtemp(prefix="aldic3d_shot_"))
    scene = synth_parity.build_parity_scene(workdir, img=320, n_frames=5, seed=7)
    draft = win.controller.state.draft
    draft.left = sorted(str(p) for p in scene["dir"].glob("L_*.png"))
    draft.right = sorted(str(p) for p in scene["dir"].glob("R_*.png"))
    draft.calibration_file = scene["dir"] / "calib.yml"
    draft.calibration_format = "opencv_yaml"
    draft.roi = (51, 269, 51, 269)
    win._left.refresh_all()
    win.signals.images_changed.emit()
    win.signals.roi_changed.emit()
    _grab(win, out / "shot_loaded.png")

    # --- state 3: after a run (field overlay + colorbar) ---
    win.controller.run()
    win._right._on_done()
    win.signals.set_current_frame(min(2, len(draft.left) - 1), len(draft.left))
    win._canvas_area.render()
    _grab(win, out / "shot_results.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
