"""The quickstart walkthrough on the real GUI -> ``assets/quickstart_result.jpg``.

Follows ``quickstart/README.md`` step by step on the actual application rendered
offscreen: the LEFT and RIGHT drop zones, Format = dice and Import calibration…,
Tracking Mode = Incremental, the two Per-frame masks Import… buttons and Run 3D
Analysis. Only the file dialogs are answered by this script. The capture shows W
(the out-of-plane displacement) on the last frame, the view the README
describes, so a reader can check their window against it.

Saved as a JPEG, not through ``optimize_png``: a 256-colour palette bands the
colour field, and this picture is there to be compared against.

Run:  python tools/marketing/gen_quickstart_shot.py
"""
# ruff: noqa: E402  (Qt platform must be selected before any Qt import)

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# The offscreen platform ships no font database on Windows -> tofu boxes.
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _style import ASSETS

QUICKSTART = REPO / "quickstart"
SIZE = (1600, 1000)
RUN_TIMEOUT_S = 600


def _settle(n: int = 4) -> None:
    from PySide6.QtWidgets import QApplication

    for _ in range(n):
        QApplication.processEvents()


def _settle_for(seconds: float) -> None:
    """Pump events for a while: frames and overlays render on worker threads."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        _settle(1)
        time.sleep(0.02)


def main() -> int:
    from PySide6.QtWidgets import QFileDialog, QPushButton

    from al_dic_3d.gui.app import create_app
    from al_dic_3d.gui.main_window import MainWindow3D

    answers: list[str] = []  # what the user would pick in each file dialog, in order
    QFileDialog.getExistingDirectory = staticmethod(lambda *a, **k: answers.pop(0))
    QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: (answers.pop(0), ""))

    create_app([])
    win = MainWindow3D()
    win.resize(*SIZE)
    win.show()
    left = win._left

    # 1. Load the images: click the LEFT and RIGHT drop zones.
    answers.append(str(QUICKSTART / "left"))
    left._left_drop.mousePressEvent(None)
    answers.append(str(QUICKSTART / "right"))
    left._right_drop.mousePressEvent(None)
    # 2. Load the calibration: Format = dice, then Import calibration…
    left._calib_widget.format_combo.setCurrentText("dice")
    answers.append(str(QUICKSTART / "calibration.xml"))
    left._calib_widget.import_btn.click()
    # 3. Tracking Mode = Incremental.
    left._mode_combo.setCurrentIndex(left._mode_combo.findData("incremental"))
    # 4. Per-frame masks: Import… for the left camera, then the right.
    imports = [
        b for b in left._frame_masks.findChildren(QPushButton) if b.text().startswith("Import")
    ]
    for button, cam in zip(imports, ("left", "right"), strict=True):
        answers.append(str(QUICKSTART / "masks" / cam))
        button.click()
    _settle()

    # 5. Run 3D Analysis, then wait for the worker the way the window does.
    print("running the quickstart through the GUI ...")
    win._right._run_btn.click()
    deadline = time.monotonic() + RUN_TIMEOUT_S
    while win._right.active_worker() is not None or win.signals.run_state == "running":
        if time.monotonic() > deadline:
            raise RuntimeError(f"the quickstart run did not finish in {RUN_TIMEOUT_S} s")
        _settle(1)
        time.sleep(0.05)
    _settle()
    if win.controller.state.result is None:
        raise RuntimeError("the quickstart run produced no result")

    # 6. The strain window opens by itself after the first run; show W instead.
    _settle_for(1.5)
    strain = getattr(win, "_strain_window", None)
    if strain is not None:
        strain.hide()
    n = len(win.controller.state.draft.left)
    (w_button,) = [
        b for b in win._right._field_selector.findChildren(QPushButton) if b.text() == "W"
    ]
    w_button.click()
    win.signals.set_current_frame(n - 1, n)
    _settle_for(4.0)

    from PIL import Image

    png = ASSETS / "quickstart_result.png"
    png.parent.mkdir(parents=True, exist_ok=True)
    win.grab().save(str(png))
    out = png.with_suffix(".jpg")
    Image.open(png).convert("RGB").save(out, quality=88, optimize=True, progressive=True)
    png.unlink()
    print(f"  wrote {out.relative_to(REPO)}  ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
