"""A failed run tells GUI users what to do, in GUI terms (new-user audit, 2026-11-25).

The run worker showed ``RuntimeError: frame-1 stereo match found no valid
correspondences (0/6160 candidates matched L1->R1; search_radius=48,
disparity offset=None) ...`` and then advised raising a threshold that does
not help. The worker now emits the plain, translated message.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from al_dic_3d.gui.run_error_text import run_error_text  # noqa: E402
from al_dic_3d.matching.diagnostics import NoStereoLinksError  # noqa: E402


def test_no_stereo_links_is_a_runtime_error_with_its_numbers():
    exc = NoStereoLinksError(6160, 48, None, rejected=(2309, 0))
    assert isinstance(exc, RuntimeError)
    assert exc.cause == "no_match" and exc.rejected == (2309, 0) and exc.n_pts == 6160
    epi = NoStereoLinksError(500, 48, (1.0, 2.0), rejected=(3, 480), epipolar_median_px=7.04)
    assert epi.cause == "calibration"


def test_the_gui_names_the_likely_causes_in_order():
    text = run_error_text(NoStereoLinksError(6160, 48, None, rejected=(2309, 0)))
    order = [text.index(k) for k in ("swapped", "calibration does not belong", "speckle")]
    assert order == sorted(order)
    assert "RuntimeError" not in text and "L1->R1" not in text and "offset" not in text
    assert "stereo_znssd_max" not in text and "Starting Point" in text


def test_the_gui_names_the_calibration_when_links_miss_their_epipolar_lines():
    exc = NoStereoLinksError(500, 48, None, rejected=(3, 480), epipolar_median_px=7.04)
    text = run_error_text(exc)
    assert "480" in text and "7.0 px" in text and "calibration" in text


def test_the_memory_refusal_gives_gui_users_gui_actions(monkeypatch):
    from al_dic_3d import memcheck

    monkeypatch.setattr(memcheck, "available_ram_bytes", lambda: 1024**3)  # 1 GB
    with pytest.raises(memcheck.MemoryBudgetError) as info:
        memcheck.check_run_memory(400, 2048, 2448, 2, lazy=True, n_pts=60000)
    assert isinstance(info.value, ValueError)
    assert "ignore_memory_check" in str(info.value)  # the CLI / config wording keeps it
    text = run_error_text(info.value)
    assert "ignore_memory_check" not in text and "[advanced]" not in text
    assert "400 frames" in text and "Subset Step" in text and "region of interest" in text


def test_user_errors_show_their_message_and_bugs_their_type():
    assert run_error_text(ValueError("frame-count mismatch")) == "frame-count mismatch"
    assert run_error_text(FileNotFoundError("no such file: a.tif")) == "no such file: a.tif"
    assert run_error_text(KeyError("x")) == "KeyError: 'x'"


class _FailingController:
    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def run(self, progress=None, stop=None):  # noqa: ARG002
        raise self._exc


def test_the_run_worker_emits_the_plain_message():
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.gui.run_worker import RunWorker

    QApplication.instance() or QApplication([])
    worker = RunWorker(_FailingController(NoStereoLinksError(312, 48, None, rejected=(171, 0))))
    got: list[str] = []
    worker.failed.connect(got.append)
    worker.run()  # synchronously, on this thread
    assert len(got) == 1
    assert not got[0].startswith("RuntimeError") and "swapped" in got[0]
