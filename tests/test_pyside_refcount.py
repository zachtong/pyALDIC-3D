"""PySide6 must keep the reference counts of None, True and False balanced.

PySide6 6.12.0 decrements the bool that ``Signal.emit`` returns once too often.
From Python 3.12 these singletons are immortal and nothing happens; on 3.10 and
3.11 their count reaches zero after a few thousand signals and the interpreter
aborts ("deallocating None" / "deallocating True or False"): the GUI died within
minutes of use and the CI suite aborted in the mesh-preview tests. The package
excludes that release below Python 3.12 (pyproject.toml); this test fails with
a clear message, instead of a crash much later, if a release brings it back.
"""

from __future__ import annotations

import sys

import pytest

pytest.importorskip("PySide6")

# A broken release drifts by one per emit; a few counts move with one-time setup.
EMITS = 50
TOLERANCE = 5


@pytest.mark.skipif(
    sys.version_info >= (3, 12), reason="None/True/False are immortal from Python 3.12"
)
def test_signal_emit_keeps_the_singleton_reference_counts():
    from PySide6 import __version__ as pyside_version
    from PySide6.QtCore import QCoreApplication, QObject, Signal

    _app = QCoreApplication.instance() or QCoreApplication([])

    class Carrier(QObject):
        two = Signal(object, object)
        bare = Signal()

    carrier = Carrier()
    singletons = {"None": None, "True": True, "False": False}
    before = {name: sys.getrefcount(obj) for name, obj in singletons.items()}
    for _ in range(EMITS):
        carrier.two.emit(1, "x")
        carrier.bare.emit()
    drift = {name: sys.getrefcount(obj) - before[name] for name, obj in singletons.items()}
    assert all(abs(d) <= TOLERANCE for d in drift.values()), (
        f"PySide6 {pyside_version} leaks singleton references on Signal.emit "
        f"({drift} over {EMITS} x 2 emits); on Python < 3.12 this aborts the "
        "interpreter after a few thousand signals — exclude this release"
    )
