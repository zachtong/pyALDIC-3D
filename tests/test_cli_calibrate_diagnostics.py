"""WP6: ``al-dic-3d calibrate`` prints the diagnostics, stores them, and ``--strict``.

The same findings must appear in the command's output and in the saved
calibration's ``meta_*`` nodes; ``--strict`` makes a warning fail the command
(for scripted pipelines) after the calibration has still been written.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.calibration.diagnostics import EXTRAPOLATION_UNDETERMINED
from tests.test_calib_extrapolation import SIZE, _central_poses, _corner_poses
from tests.test_calib_pipeline import wide_stereo


def _run_cli(tmp_path, monkeypatch, capsys, poses, *extra):
    import al_dic_3d.calibration as calib
    import al_dic_3d.pathsafe as pathsafe
    from al_dic_3d.cli import main

    left, right = wide_stereo(poses)
    queue = iter([*left, *right])  # every left image is detected first, then every right one
    monkeypatch.setattr(calib, "detect_board", lambda _img, _spec: next(queue))
    blank = np.zeros((SIZE[1], SIZE[0]), np.uint8)
    monkeypatch.setattr(pathsafe, "imread_unicode", lambda _f: blank)
    for i in range(len(left)):
        (tmp_path / f"L_{i:02d}.png").touch()
        (tmp_path / f"R_{i:02d}.png").touch()
    out = tmp_path / "rig.yml"
    code = main(
        [
            "calibrate",
            "--left", str(tmp_path / "L_*.png"),
            "--right", str(tmp_path / "R_*.png"),
            "--output", str(out),
            "--board", "chessboard", "--cols", "9", "--rows", "7", "--square", "20",
            *extra,
        ]
    )  # fmt: skip
    captured = capsys.readouterr()
    return code, captured.out + captured.err, out


def _meta(path, name: str):
    import cv2

    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    try:
        node = fs.getNode(name)
        return node.string() if node.isString() else node.real()
    finally:
        fs.release()


def test_findings_are_printed_and_saved(tmp_path, monkeypatch, capsys):
    code, out, yml = _run_cli(tmp_path, monkeypatch, capsys, _central_poses())
    assert code == 0
    assert "warning: camera L: the calibration points reach" in out
    assert f"{EXTRAPOLATION_UNDETERMINED}:L" in _meta(yml, "meta_findings")
    assert _meta(yml, "meta_cover_ratio_left") == pytest.approx(
        float(out.split("camera L: covered to ")[1].split("%")[0]) / 100.0, abs=0.006
    )


def test_strict_fails_on_a_warning_but_still_writes(tmp_path, monkeypatch, capsys):
    code, out, yml = _run_cli(tmp_path, monkeypatch, capsys, _central_poses(), "--strict")
    assert code == 1
    assert yml.exists()
    assert "error: --strict" in out


def test_board_shape_runs_the_bundle_with_the_board_shape(tmp_path, monkeypatch, capsys):
    import al_dic_3d.calibration.pipeline as pl

    seen = {}

    def bundle(_left, _right, base, **kwargs):
        seen.update(kwargs)
        info = {"rms_before": 0.5, "rms_after": 0.4, "n_views": 12, "n_mono_views": 0,
                "board_z_range": 0.123, "board_max_dev": 0.2}  # fmt: skip
        return base.rig, info

    monkeypatch.setattr(pl, "bundle_refine", bundle)
    code, out, _yml = _run_cli(tmp_path, monkeypatch, capsys, _corner_poses(), "--board-shape")
    assert code == 0
    assert seen["board_morphology"] is True
    assert "bundle adjustment: rms 0.5000 -> 0.4000" in out
    assert "board shape: out-of-plane range 0.123 mm" in out


def test_strict_passes_without_warnings(tmp_path, monkeypatch, capsys):
    code, out, yml = _run_cli(tmp_path, monkeypatch, capsys, _corner_poses(), "--strict")
    assert code == 0
    assert "warning: camera" not in out
    findings = _meta(yml, "meta_findings")
    assert "UNDETERMINED" not in findings and "INADEQUATE" not in findings
