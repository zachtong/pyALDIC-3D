"""``al-dic-3d calibrate`` refuses image sets it cannot calibrate, and says why.

Without image files: ``detect_files`` is replaced by a stand-in returning
point-level synthetic detections with chosen per-file image sizes.
"""

from __future__ import annotations

import pytest

from al_dic_3d.calibration import BoardDetection, FileDetections
from tests.test_calib_image_sizes import SIZE_L, SIZE_R, _two_resolution_views


def _fake_detect(detections, sizes):
    def fake(paths, _spec, *, workers=None, on_result=None) -> FileDetections:
        assert len(paths) == len(detections) == len(sizes)
        for k, det in enumerate(detections):
            if on_result is not None:
                on_result(k, det)
        return FileDetections(tuple(detections), tuple(sizes))

    return fake


def _run(tmp_path, monkeypatch, capsys, left, right, sizes, board=("chessboard",)):
    import al_dic_3d.calibration as calib
    from al_dic_3d.cli import main

    written: dict = {}

    def capture_yaml(rig, path, meta=None):
        written["rig"] = rig
        return path

    monkeypatch.setattr(calib, "detect_files", _fake_detect([*left, *right], sizes))
    monkeypatch.setattr(calib, "to_opencv_yaml", capture_yaml)
    for i in range(len(left)):
        (tmp_path / f"L_{i:02d}.png").touch()
        (tmp_path / f"R_{i:02d}.png").touch()
    args = [
        "calibrate",
        "--left", str(tmp_path / "L_*.png"),
        "--right", str(tmp_path / "R_*.png"),
        "--output", str(tmp_path / "rig.yml"),
        "--board", *board, "--cols", "9", "--rows", "7", "--square", "12",
    ]  # fmt: skip
    try:
        code = main(args)
    except SystemExit as exc:  # the command's fail() exits with code 2
        code = exc.code
    captured = capsys.readouterr()
    return code, captured.out, captured.err, written.get("rig")


def test_each_camera_is_recorded_at_its_own_size(tmp_path, monkeypatch, capsys):
    _truth, left, right = _two_resolution_views()
    sizes = [SIZE_L] * len(left) + [SIZE_R] * len(right)
    code, out, err, rig = _run(tmp_path, monkeypatch, capsys, left, right, sizes)
    assert code == 0, err
    assert (rig.cameras["L"].width, rig.cameras["L"].height) == SIZE_L
    assert (rig.cameras["R"].width, rig.cameras["R"].height) == SIZE_R
    # The board distances let a user check the square size against a tape measure.
    line = next(t for t in out.splitlines() if t.startswith("board distance from the left camera"))
    low, high = (float(v) for v in line.split()[6].split("-"))
    assert 300.0 < low < high < 700.0


def test_images_of_two_sizes_in_one_camera_are_refused(tmp_path, monkeypatch, capsys):
    _truth, left, right = _two_resolution_views()
    sizes = [SIZE_L] * len(left) + [SIZE_R] * len(right)
    sizes[len(left) + 4] = (400, 300)  # one cropped right image
    code, _out, err, rig = _run(tmp_path, monkeypatch, capsys, left, right, sizes)
    assert code == 2 and rig is None
    assert "right board images are not all the same size" in err
    assert "R_04.png is 400x300" in err


def test_no_board_found_names_the_board_size_first(tmp_path, monkeypatch, capsys):
    missing = BoardDetection(ok=False, method="sb", reason="chessboard not found")
    left, right = [missing] * 8, [missing] * 8
    sizes = [SIZE_L] * 16
    code, _out, err, rig = _run(tmp_path, monkeypatch, capsys, left, right, sizes)
    assert code == 2 and rig is None
    message = err.strip().splitlines()[-1]
    assert message.startswith("error: the board was not found in any image")
    assert "count the INNER corners: a board of 10 x 8 squares has 9 x 7" in message


def test_too_few_pairs_found_says_how_many(tmp_path, monkeypatch, capsys):
    _truth, left, right = _two_resolution_views()
    missing = BoardDetection(ok=False, method="sb", reason="chessboard not found")
    left = [d if k < 4 else missing for k, d in enumerate(left)]
    sizes = [SIZE_L] * len(left) + [SIZE_R] * len(right)
    code, _out, err, _rig = _run(tmp_path, monkeypatch, capsys, left, right, sizes)
    assert code == 2
    assert f"the board was found in both images of only 4 of {len(left)} pairs" in err
    assert "INNER corners" in err


@pytest.mark.parametrize(
    ("board", "expected"),
    [
        (("charuco", "--marker", "9"), "count the SQUARES"),
        (("circles", "--spacing", "12"), "count the DOTS"),
    ],
)
def test_the_hint_follows_the_board_type(tmp_path, monkeypatch, capsys, board, expected):
    missing = BoardDetection(ok=False, method="x", reason="not found")
    code, _out, err, _rig = _run(
        tmp_path, monkeypatch, capsys, [missing] * 8, [missing] * 8, [SIZE_L] * 16, board
    )
    assert code == 2
    assert expected in err


def test_shortfall_counts_pairs_found_in_both_images():
    from al_dic_3d.calibration import ChessboardSpec
    from al_dic_3d.calibration.batch_detect import count_detections, detection_shortfall

    spec = ChessboardSpec(cols=9, rows=7, square_size=12.0)
    _truth, left, right = _two_resolution_views()
    missing = BoardDetection(ok=False, method="sb", reason="chessboard not found")
    assert detection_shortfall(left, right, spec, 6) is None
    # Four pairs given in all: the solver's own "need >= 6 pairs" says it best.
    assert detection_shortfall(left[:4], right[:4], spec, 6) is None
    half = [d if k % 2 else missing for k, d in enumerate(left)]
    other_half = [missing if k % 2 else d for k, d in enumerate(right)]
    count = count_detections(half, other_half)
    assert (count.images, count.pairs, count.total_pairs) == (len(left), 0, len(left))
    assert detection_shortfall(half, other_half, spec, 6).startswith(
        f"the board was found in both images of only 0 of {len(left)} pairs"
    )
