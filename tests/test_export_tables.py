"""Field-selective export (NPZ / MAT / per-frame CSV) + the export dialog."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d.export import export_csv_frames, export_mat, export_npz  # noqa: E402
from al_dic_3d.runner import load_config, run_pipeline  # noqa: E402


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    from dataclasses import replace

    from tests import synth_parity

    d = tmp_path_factory.mktemp("export_src")
    scene = synth_parity.build_parity_scene(d, img=200, n_frames=3, seed=7)
    cfg = replace(load_config(synth_parity.write_config(d, scene)), compute_strain=True)
    return run_pipeline(cfg)


def test_npz_export_respects_selection(result, tmp_path):
    path = export_npz(result, ["U", "von_mises"], tmp_path, "sel")
    npz = np.load(path)
    assert "U" in npz and "von_mises" in npz
    assert "V" not in npz  # unselected field is absent
    assert "points3D" in npz and "source" in npz  # core arrays always present
    n_frames, n_pts = result.reconstruction.n_frames, result.reconstruction.n_pts
    assert npz["U"].shape == (n_frames, n_pts)


def test_mat_and_csv_exports(result, tmp_path):
    import scipy.io

    mat_path = export_mat(result, ["mag"], tmp_path, "sel")
    mat = scipy.io.loadmat(str(mat_path))
    assert "mag" in mat

    csvs = export_csv_frames(result, ["U", "exx"], tmp_path, "sel")
    assert len(csvs) == result.reconstruction.n_frames
    header = csvs[0].read_text(encoding="utf-8").splitlines()[0]
    assert header.startswith("x_px,y_px,X_mm,Y_mm,Z_mm")
    assert "U" in header and "exx" in header
    data = np.genfromtxt(csvs[1], delimiter=",", skip_header=1)
    assert data.shape[0] == result.reconstruction.n_pts


def test_export_dialog_offscreen(result, tmp_path):
    pytest.importorskip("PySide6")
    from al_dic_3d.gui.app import create_app
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog

    create_app([])
    dialog = ExportDialog(result, extra_params={"winsize": 32})
    # default selection = all displacement + all strain (strain available)
    fields = dialog.selected_fields()
    assert "U" in fields and "von_mises" in fields
    assert not dialog._ply_cb.isChecked() and not dialog._vtu_cb.isChecked()  # default off
    dialog._folder_edit.setText(str(tmp_path))
    dialog._csv_cb.setChecked(True)
    dialog._ply_cb.setChecked(True)
    dialog._vtu_cb.setChecked(True)
    dialog._on_export()
    # Timestamped names (fresh per export, never overwriting) + params always.
    assert len(list(tmp_path.glob("*.npz"))) == 1
    assert len(list(tmp_path.glob("*.mat"))) == 1
    assert len(list(tmp_path.glob("*_frame000.csv"))) == 1
    params = list(tmp_path.glob("*_parameters_*.json"))
    assert len(params) == 1
    assert '"winsize": 32' in params[0].read_text(encoding="utf-8")
    ply_dir = next(tmp_path.glob("*_ply_*"))
    n_frames = result.reconstruction.n_frames
    assert len(list(ply_dir.glob("*.ply"))) == n_frames
    vtu_dir = next(tmp_path.glob("*_vtu_*"))
    assert len(list(vtu_dir.glob("*.vtu"))) == n_frames
    assert len(list(vtu_dir.glob("*.pvd"))) == 1
    assert "Wrote" in dialog._status.text()
