"""``al-dic-3d run`` reports ordinary user errors in one line (new-user audit, 2026-11-25).

A missing file, an image-size or frame-count mismatch and a run that matched
nothing all printed a full Python traceback. They now print
``error: <message>`` and exit 2; ``--debug`` keeps the traceback for bug
reports, and a genuine bug still raises.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from al_dic_3d import cli
from al_dic_3d.calibration import CameraIntrinsics, StereoRig, to_opencv_yaml


def _config(tmp_path: Path, *, calib: str = "calib.yml", n_right: int = 2) -> Path:
    for cam, n in (("L", 2), ("R", n_right)):
        for k in range(n):
            cv2.imwrite(str(tmp_path / f"{cam}_{k}.png"), np.full((60, 80), 100, np.uint8))
    intr = CameraIntrinsics(fx=900.0, fy=900.0, cx=40.0, cy=30.0, width=160, height=120)
    rig = StereoRig(
        cameras={"L": intr, "R": intr},
        extrinsics={("L", "R"): (np.eye(3), np.array([-100.0, 0.0, 0.0]))},
    )
    to_opencv_yaml(rig, tmp_path / "calib.yml")  # made for 160x120 images
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f'[calibration]\nfile = "{calib}"\nformat = "opencv_yaml"\n'
        '[sequence]\nleft = "L_*.png"\nright = "R_*.png"\n'
        "[roi]\nxmin = 10\nxmax = 70\nymin = 10\nymax = 50\n",
        encoding="utf-8",
    )
    return cfg


def _run(capsys, *argv: str) -> tuple[int, str]:
    code = cli.main(["run", *argv])
    err = capsys.readouterr().err
    return code, err


@pytest.mark.parametrize(
    ("kwargs", "needle"),
    [
        ({"calib": "missing.yml"}, "missing.yml"),  # missing calibration file
        ({}, "made for 160x120 images"),  # images of another size
    ],
)
def test_user_errors_print_one_line_and_exit_2(tmp_path, capsys, kwargs, needle):
    code, err = _run(capsys, str(_config(tmp_path, **kwargs)))
    assert code == 2
    assert "Traceback" not in err
    line = next(e for e in err.splitlines() if e.startswith("error: "))
    assert needle in line


def test_a_missing_config_file_is_a_user_error(tmp_path, capsys):
    code, err = _run(capsys, str(tmp_path / "nope.toml"))
    assert code == 2 and err.startswith("error: ") and "Traceback" not in err


def test_a_frame_count_mismatch_is_a_user_error(tmp_path, capsys, monkeypatch):
    from al_dic_3d.calibration import importers

    real = importers.from_opencv_yaml

    def unsized(path):  # let the run get past the size guard to the sequence check
        rig = real(path)
        from dataclasses import replace

        cams = {k: replace(v, width=None, height=None) for k, v in rig.cameras.items()}
        return replace(rig, cameras=cams)

    monkeypatch.setitem(importers.IMPORTERS, "opencv_yaml", unsized)
    code, err = _run(capsys, str(_config(tmp_path, n_right=3)))
    assert code == 2 and "Traceback" not in err
    assert "frame-count mismatch" in err


def test_debug_keeps_the_traceback(tmp_path):
    with pytest.raises(ValueError, match="made for 160x120"):
        cli.main(["run", "--debug", str(_config(tmp_path))])


def test_a_genuine_bug_still_raises(tmp_path, monkeypatch):
    import al_dic_3d.runner as runner

    def broken(*_a, **_k):
        raise TypeError("a bug")

    monkeypatch.setattr(runner, "run_pipeline", broken)
    with pytest.raises(TypeError, match="a bug"):
        cli.main(["run", str(_config(tmp_path))])
