"""View3D graceful degradation without pyvista / OpenGL (alien-env batch G3).

Two real failure modes on user machines:

1. the ``[viz3d]`` extra is simply not installed (headless installs, minimal
   pip environments) — ``import pyvistaqt`` raises ``ImportError``;
2. pyvista imports fine but the machine cannot create an OpenGL context
   (remote desktop, VMs, old drivers) — ``QtInteractor(...)`` RAISES at
   construction time.

Both must degrade to the styled placeholder message, never crash the app,
and never retry-storm. Neither test needs pyvista installed: the module is
faked/blocked in ``sys.modules``.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import sys
import types

import numpy as np
import pytest

pytest.importorskip("PySide6")

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.widgets.view3d import View3D  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def _points(n: int = 9) -> np.ndarray:
    rng = np.random.default_rng(1)
    xy = rng.uniform(-10, 10, size=(n, 2))
    return np.column_stack([xy, np.full(n, 800.0)])


def _unavailable_prefix(view: View3D) -> str:
    """The locale-CURRENT '3D view unavailable: {0}' template up to the slot.

    Earlier suite tests (test_i18n) may leave a translator installed on the
    shared QApplication, so the placeholder can legitimately be Chinese/
    Korean/... here — asserting the English literal would couple this test to
    suite ordering and the host locale. Asking the widget's own ``tr()`` for
    the template keeps the assertion locale-agnostic.
    """
    return view.tr("3D view unavailable: {0}").split("{0}")[0]


def test_missing_viz3d_extra_shows_message_not_crash(qapp, monkeypatch) -> None:
    # None in sys.modules makes ``from pyvistaqt import QtInteractor`` raise
    # ImportError — exactly what a machine without the [viz3d] extra sees.
    monkeypatch.setitem(sys.modules, "pyvistaqt", None)
    view = View3D()
    pts = _points()
    view.update_view(pts, pts[:, 0], field_label="U", cmap="turbo", vmin=0.0, vmax=1.0)
    assert view._plotter is None and view._failed
    assert view._placeholder.text().startswith(_unavailable_prefix(view))
    assert view._placeholder.isVisibleTo(view)
    # A second update must short-circuit quietly (no re-import, no crash).
    view.update_view(pts, pts[:, 0], field_label="U", cmap="turbo", vmin=0.0, vmax=1.0)
    assert view._plotter is None
    view.deleteLater()


def test_opengl_context_failure_shows_message_not_crash(qapp, monkeypatch) -> None:
    # pyvistaqt imports fine, but plotter CONSTRUCTION raises — the remote
    # desktop / no-GL failure mode. The widget must catch it and degrade.
    fake = types.ModuleType("pyvistaqt")

    class _NoGLInteractor:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("failed to create OpenGL context")

    fake.QtInteractor = _NoGLInteractor
    monkeypatch.setitem(sys.modules, "pyvistaqt", fake)

    view = View3D()
    assert view._ensure_plotter() is False
    assert view._failed
    text = view._placeholder.text()
    assert text.startswith(_unavailable_prefix(view))
    assert "failed to create OpenGL context" in text  # the exception is quoted verbatim
    # update_view goes through the same guard and must not raise.
    pts = _points()
    view.update_view(pts, pts[:, 0], field_label="U", cmap="turbo", vmin=0.0, vmax=1.0)
    assert view._plotter is None
    view.deleteLater()
