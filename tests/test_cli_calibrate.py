"""End-to-end test of the ``al-dic-3d calibrate`` sub-command."""

import numpy as np
import pytest

from al_dic_3d.calibration import ChessboardSpec, from_opencv_yaml
from al_dic_3d.cli import main
from tests import synth_calib as sc

SPEC = ChessboardSpec(cols=9, rows=7, square_size=12.0)


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    """Render a small on-disk chessboard calibration set (8 pairs)."""
    import cv2

    out = tmp_path_factory.mktemp("calib_imgs")
    rig = sc.make_rig()
    extent = ((SPEC.cols - 1) * SPEC.square_size, (SPEC.rows - 1) * SPEC.square_size)
    poses = sc.board_poses(extent, n=8)
    lefts, rights = sc.render_stereo_set(SPEC, rig, poses)
    for k, (im_l, im_r) in enumerate(zip(lefts, rights, strict=True)):
        cv2.imwrite(str(out / f"L_{k:02d}.png"), np.clip(im_l * 256, 0, 65535).astype(np.uint16))
        cv2.imwrite(str(out / f"R_{k:02d}.png"), np.clip(im_r * 256, 0, 65535).astype(np.uint16))
    return out, rig


def test_calibrate_command_writes_valid_yaml(dataset, tmp_path, capsys):
    imgdir, rig = dataset
    out_yaml = tmp_path / "cal.yml"
    code = main(
        [
            "calibrate",
            "--left",
            str(imgdir / "L_*.png"),
            "--right",
            str(imgdir / "R_*.png"),
            "--board",
            "chessboard",
            "--cols",
            "9",
            "--rows",
            "7",
            "--square",
            "12.0",
            "-o",
            str(out_yaml),
        ]
    )
    assert code == 0
    text = capsys.readouterr().out
    assert "stereo rms" in text and "wrote" in text

    back = from_opencv_yaml(out_yaml)
    gt_l = rig.cameras["L"]
    assert abs(back.cameras["L"].fx - gt_l.fx) / gt_l.fx < 0.01
    _r, t = back.pose("R")
    _rg, tg = rig.pose("R")
    assert abs(np.linalg.norm(t) - np.linalg.norm(tg)) < 1.0


def test_calibrate_command_validates_args(dataset, tmp_path):
    imgdir, _rig = dataset
    with pytest.raises(SystemExit):  # missing --square for chessboard
        main(
            [
                "calibrate",
                "--left",
                str(imgdir / "L_*.png"),
                "--right",
                str(imgdir / "R_*.png"),
                "--board",
                "chessboard",
                "--cols",
                "9",
                "--rows",
                "7",
            ]
        )
    with pytest.raises(SystemExit):  # empty glob
        main(
            [
                "calibrate",
                "--left",
                str(tmp_path / "nope_*.png"),
                "--right",
                str(tmp_path / "nope_*.png"),
                "--board",
                "chessboard",
                "--cols",
                "9",
                "--rows",
                "7",
                "--square",
                "12.0",
            ]
        )
