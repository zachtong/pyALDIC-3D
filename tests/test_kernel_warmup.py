"""Background JIT warm-up (H2): geometry, silence, coverage and GUI reporting.

The warm-up only helps if it compiles what the first real run needs. The
geometry test pins the node count that reaches the engine's batch subset
precompute; the subprocess test proves that, after the warm-up, a real
pipeline run compiles no numba signature at all.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import threading
import time
import warnings
from pathlib import Path

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from al_dic_3d.gui import kernel_warmup as kw  # noqa: E402  (after importorskip guard)

_REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def qapp():
    from al_dic_3d.gui.app import create_app

    return create_app([])


def _pump(app, until, timeout=10.0):
    deadline = time.monotonic() + timeout
    while not until() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()


def test_warmup_geometry_reaches_the_batch_kernels():
    ref, deformed, para, mesh = kw.warmup_problem()
    n_nodes = np.asarray(mesh.coordinates_fem).shape[0]
    assert ref.shape == deformed.shape == (kw.WARMUP_IMAGE_PX, kw.WARMUP_IMAGE_PX)
    assert kw.WARMUP_IMAGE_PX >= 192
    assert n_nodes >= kw.MIN_WARMUP_NODES == 50  # batch precompute threshold
    assert para.use_global_step and para.admm_max_iter == 2  # subproblem-1 solver runs
    assert np.allclose(np.roll(ref, 1, axis=(0, 1)), deformed)


def test_warm_kernels_runs_silently_and_compiles_the_kernels():
    pytest.importorskip("numba")
    from al_dic.solver import numba_kernels as nk

    from al_dic_3d.strain3d import kernels

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        kw.warm_kernels()
    # The engine reports through UserWarning (e.g. the FFT search auto-scale);
    # numba's own platform notices (NumbaWarning) are not the warm-up's doing.
    assert [str(w.message) for w in caught if issubclass(w.category, UserWarning)] == []
    for dispatcher in (
        nk.precompute_subsets_6dof_numba,
        nk.icgn_6dof_parallel,
        nk.precompute_subsets_2dof_numba,
        nk.icgn_2dof_parallel,
        kernels._fit_kernel,
    ):
        assert dispatcher.signatures, dispatcher


_COVERAGE_SCRIPT = textwrap.dedent(
    """
    import sys, tempfile, pathlib, json
    from dataclasses import replace
    from numba.core.registry import CPUDispatcher

    def signatures():
        out = {}
        for name, mod in list(sys.modules.items()):
            if not name.startswith("al_dic"):
                continue
            for value in list(vars(mod).values()):
                if isinstance(value, CPUDispatcher):
                    key = value.py_func.__module__ + "." + value.py_func.__qualname__
                    out[key] = {str(s) for s in value.signatures}
        return out

    from al_dic_3d.gui.kernel_warmup import warm_kernels
    from al_dic_3d import synthetic
    from al_dic_3d.runner import load_config, run_pipeline

    warm_kernels()
    before = signatures()
    root = pathlib.Path(tempfile.mkdtemp())
    scene = synthetic.build_scene(root, img=240, n_frames=3, seed=7)
    cfg = replace(load_config(synthetic.write_config(root, scene)), compute_strain=True)
    run_pipeline(cfg)
    after = signatures()
    new = {k: sorted(v - before.get(k, set())) for k, v in after.items()}
    print("NEW=" + json.dumps({k: v for k, v in new.items() if v}))
    """
)


@pytest.mark.slow
def test_real_run_compiles_nothing_after_the_warmup():
    pytest.importorskip("numba")
    proc = subprocess.run(
        [sys.executable, "-c", _COVERAGE_SCRIPT],
        capture_output=True,
        text=True,
        timeout=900,
        cwd=_REPO,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr[-3000:]
    line = next(ln for ln in proc.stdout.splitlines() if ln.startswith("NEW="))
    assert line == "NEW={}", f"the warm-up misses signatures the real run compiles: {line}"


def test_kernel_warmup_reports_on_the_gui_thread(qapp, monkeypatch):
    monkeypatch.setattr(kw, "REPORT_THRESHOLD_S", 0.0)
    warmup = kw.KernelWarmup(work=lambda: None)
    got: list[tuple[float, bool]] = []
    warmup.compiled.connect(
        lambda s: got.append((s, threading.current_thread() is threading.main_thread()))
    )
    thread = warmup.start()
    assert warmup.start() is thread  # at most one warm-up
    thread.join(10)
    _pump(qapp, lambda: bool(got))
    assert len(got) == 1 and got[0][0] >= 0.0 and got[0][1]  # queued onto the GUI thread
    assert not warmup.is_running()


def test_kernel_warmup_is_quiet_when_the_cache_is_warm(qapp):
    warmup = kw.KernelWarmup(work=lambda: None)  # instant: well below 1 s
    got: list[float] = []
    warmup.compiled.connect(got.append)
    warmup.start().join(10)
    _pump(qapp, lambda: False, timeout=0.2)
    assert got == []


def test_kernel_warmup_swallows_failures(qapp, monkeypatch, caplog):
    monkeypatch.setattr(kw, "REPORT_THRESHOLD_S", 0.0)

    def boom():
        raise RuntimeError("no LLVM today")

    warmup = kw.KernelWarmup(work=boom)
    got: list[float] = []
    warmup.compiled.connect(got.append)
    with caplog.at_level("ERROR", logger=kw.__name__):
        warmup.start().join(10)
    _pump(qapp, lambda: False, timeout=0.2)
    assert got == []
    assert any("Kernel warm-up failed" in r.getMessage() for r in caplog.records)
    assert any(r.exc_info and "no LLVM today" in str(r.exc_info[1]) for r in caplog.records)


# ---------------------------------------------------------------------------
# app.start_kernel_warmup -> GUI console
# ---------------------------------------------------------------------------


class _FakeWindow:
    def __init__(self):
        from PySide6.QtWidgets import QWidget

        from al_dic_3d.gui.state import GuiSignals

        self.widget = QWidget()
        self.signals = GuiSignals()


def _start_with(monkeypatch, work, *, threshold: float):
    from al_dic_3d.gui import app as app_mod

    monkeypatch.setattr(kw, "START_DELAY_MS", 0)
    monkeypatch.setattr(kw, "REPORT_THRESHOLD_S", threshold)
    monkeypatch.setattr(kw, "warm_kernels", work)
    win = _FakeWindow()
    logs: list[tuple[str, str]] = []
    win.signals.log.connect(lambda m, lvl: logs.append((m, lvl)))
    warmup = app_mod.start_kernel_warmup(win, parent=win.widget)
    return win, warmup, logs


def test_start_kernel_warmup_logs_a_slow_compile(qapp, monkeypatch):
    win, warmup, logs = _start_with(monkeypatch, lambda: time.sleep(1.0), threshold=0.05)
    _pump(qapp, lambda: len(logs) >= 2)
    assert logs[0] == ("Preparing compute kernels in the background…", "info")
    assert logs[1][1] == "info"
    assert logs[1][0].startswith("Compute kernels ready (") and logs[1][0].endswith(" s).")
    win.widget.deleteLater()


def test_start_kernel_warmup_says_nothing_when_cached(qapp, monkeypatch):
    win, warmup, logs = _start_with(monkeypatch, lambda: None, threshold=0.3)
    _pump(qapp, lambda: warmup.started and not warmup.is_running(), timeout=5)
    _pump(qapp, lambda: False, timeout=0.6)  # past the announce delay
    assert logs == []
    win.widget.deleteLater()
