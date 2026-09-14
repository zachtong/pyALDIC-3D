"""Data export progress + cooperative cancel (fix batch V, M5 / GUI-review M2).

The Data tab dropped its worker's progress callback and stop event: a 500-frame
CSV/NPZ/MAT export showed no progress, Cancel did nothing, and the tab then
reported "cancelled" for an export that had written everything. The writers
now take ``progress_cb`` / ``stop_event``, stop between arrays / frames / files,
never leave a truncated NPZ/MAT behind, and the job reports "cancelled" only
when it really stopped early.
"""

from __future__ import annotations

import os
import threading

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

from al_dic_3d.export import (
    ExportCancelled,
    export_csv_frames,
    export_mat,
    export_npz,
    selected_arrays,
)
from tests.synth_export import grid_result

FIELDS = ["U", "V", "W", "mag", "exx", "von_mises"]


def test_npz_streams_with_progress_and_loads_identically(tmp_path):
    result = grid_result(n_frames=4)
    seen: list[tuple[int, int, str]] = []
    path = export_npz(result, FIELDS, tmp_path, "s", progress_cb=lambda *a: seen.append(a))
    loaded = np.load(path)
    want = selected_arrays(result, FIELDS)
    assert sorted(loaded.files) == sorted(want)
    for key, arr in want.items():
        np.testing.assert_array_equal(loaded[key], arr)
    assert seen and seen[-1][0] == seen[-1][1]  # progress reaches 100 %
    dones = [d for d, _t, _s in seen]
    assert dones == sorted(dones)
    assert not list(tmp_path.glob("*.tmp"))


def test_npz_cancel_leaves_nothing_behind(tmp_path):
    result = grid_result(n_frames=4)
    stop = threading.Event()

    def cancel(*_args):
        stop.set()

    with pytest.raises(ExportCancelled):
        export_npz(result, FIELDS, tmp_path, "c", stop_event=stop, progress_cb=cancel)
    assert list(tmp_path.iterdir()) == []  # no truncated .npz, no temp file


def test_mat_cancel_leaves_nothing_behind_and_progress_completes(tmp_path):
    import scipy.io

    result = grid_result(n_frames=3)
    seen: list[tuple[int, int, str]] = []
    path = export_mat(result, FIELDS, tmp_path, "m", progress_cb=lambda *a: seen.append(a))
    mat = scipy.io.loadmat(str(path))
    np.testing.assert_array_equal(mat["exx"], result.strain.exx)
    assert seen[-1][0] == seen[-1][1]

    stop = threading.Event()

    def cancel(*_args):
        stop.set()

    with pytest.raises(ExportCancelled):
        export_mat(result, FIELDS, tmp_path / "c", "m", stop_event=stop, progress_cb=cancel)
    assert not (tmp_path / "c").exists() or list((tmp_path / "c").iterdir()) == []


def test_mat_written_per_variable_is_byte_identical_to_one_savemat(tmp_path):
    import scipy.io

    result = grid_result(n_frames=3)
    arrays = selected_arrays(result, FIELDS)
    path = export_mat(result, FIELDS, tmp_path, "m", arrays=arrays)
    with open(tmp_path / "ref.mat", "wb") as fh:
        scipy.io.savemat(fh, arrays, do_compression=True)
    # Same bytes except the 116-byte text header, which carries a timestamp.
    assert path.read_bytes()[116:] == (tmp_path / "ref.mat").read_bytes()[116:]


def test_csv_stops_between_frames(tmp_path):
    result = grid_result(n_frames=4)
    stop = threading.Event()
    out = export_csv_frames(
        result, ["U"], tmp_path, "c", stop_event=stop, progress_cb=lambda d, t, s: stop.set()
    )
    assert len(out) == 1 and out.cancelled
    assert len(list(tmp_path.glob("*.csv"))) == 1


def _job(tmp_path, result, want, *, stop=None, on_progress=None):
    from al_dic_3d.gui.dialogs.export_tabs.data_tab import _run_data_export

    stop = stop or threading.Event()
    seen: list[tuple[int, int, str]] = []

    def progress(done, total, label):
        seen.append((done, total, label))
        if on_progress is not None:
            on_progress(done, total, label, stop)

    out = _run_data_export(
        tmp_path,
        "p",
        "20260913000000",
        result,
        {},
        FIELDS,
        want,
        progress_cb=progress,
        stop_event=stop,
    )
    return out, seen


ALL = {"npz": True, "mat": True, "csv": True, "ply": True, "vtu": True}


def test_data_job_reports_monotonic_progress_within_qt_int_range(tmp_path):
    result = grid_result(n_frames=3)
    out, seen = _job(tmp_path, result, ALL)
    assert not out.cancelled
    assert seen[-1][0] == seen[-1][1]
    assert all(0 <= d <= t < 2**31 for d, t, _ in seen)
    dones = [d for d, _t, _s in seen]
    assert dones == sorted(dones)
    assert any(name.endswith(".npz") for name in out)


def test_data_job_cancel_stops_early_and_says_so(tmp_path):
    result = grid_result(n_frames=3)

    def cancel_in_csv(done, total, label, stop):
        if label.startswith("CSV"):
            stop.set()

    out, _ = _job(tmp_path, result, ALL, on_progress=cancel_in_csv)
    assert out.cancelled
    assert not list(tmp_path.glob("*_ply_*"))  # stages after the cancel never ran
    assert not list(tmp_path.glob("*_vtu_*"))
    assert not list(tmp_path.glob("*_csv_*"))  # stopped before frame 1: no empty folder
    assert any(name.endswith(".json") for name in out)  # params always kept
    assert any(name.endswith(".npz") for name in out) and not any("CSV" in n for n in out)


def test_cancel_inside_a_frame_series_keeps_the_complete_frames(tmp_path):
    result = grid_result(n_frames=4)

    def cancel_after_first_ply(done, total, label, stop):
        if label.startswith("PLY frame_1"):
            stop.set()

    out, _ = _job(tmp_path, result, {"ply": True}, on_progress=cancel_after_first_ply)
    assert out.cancelled
    (ply_dir,) = tmp_path.glob("*_ply_*")
    assert len(list(ply_dir.glob("*.ply"))) == 1  # the finished frame is kept ...
    assert any(name.endswith("/") for name in out)  # ... and reported as kept


def test_stop_requested_after_the_last_file_is_not_a_cancel(tmp_path):
    result = grid_result(n_frames=2)

    def stop_at_end(done, total, label, stop):
        if done == total:
            stop.set()

    out, _ = _job(tmp_path, result, {**ALL, "ply": False, "vtu": False}, on_progress=stop_at_end)
    assert not out.cancelled


# ---------------------------------------------------------------------------
# GUI: the tab wires progress + cancel and reports honestly
# ---------------------------------------------------------------------------


@pytest.fixture()
def qapp():
    pytest.importorskip("PySide6")
    from al_dic_3d.gui.app import create_app

    return create_app([])


def test_data_tab_wires_progress_and_stop_into_the_job(qapp, tmp_path, monkeypatch):
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog
    from al_dic_3d.gui.dialogs.export_tabs import data_tab

    captured = {}

    def fake(out, prefix, ts, result, extra, fields, want, *, progress_cb=None, stop_event=None):
        captured["progress_cb"] = progress_cb
        captured["stop_event"] = stop_event
        progress_cb(1, 2, "NPZ")
        return data_tab.ExportOutcome(["x.json"])

    monkeypatch.setattr(data_tab, "_run_data_export", fake)
    dlg = ExportDialog(grid_result(n_frames=2), extra_params={})
    dlg._folder_edit.setText(str(tmp_path))
    dlg._data_tab.start_export()
    assert dlg.wait_for_export()
    assert callable(captured["progress_cb"]) and captured["stop_event"] is not None
    assert "Wrote" in dlg._data_tab.status_label.text()
    dlg.close()


def test_data_tab_cancel_message_only_when_the_job_stopped(qapp, tmp_path, monkeypatch):
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog
    from al_dic_3d.gui.dialogs.export_tabs import data_tab

    release = threading.Event()

    def finishes_anyway(out, prefix, ts, result, extra, fields, want, **kw):
        release.wait(5)
        return data_tab.ExportOutcome(["a.json", "b.npz"])  # completed everything

    monkeypatch.setattr(data_tab, "_run_data_export", finishes_anyway)
    dlg = ExportDialog(grid_result(n_frames=2), extra_params={})
    dlg._folder_edit.setText(str(tmp_path))
    tab = dlg._data_tab
    tab.start_export()
    tab._on_cancel()  # user clicks Cancel, but the job still finishes everything
    release.set()
    assert dlg.wait_for_export()
    assert "cancel" not in tab.status_label.text().lower()
    assert "Wrote" in tab.status_label.text()
    dlg.close()
