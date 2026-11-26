"""A calibration imported with the wrong Format, or one that cannot work, is refused.

The OpenCorr reader used to accept any text file (every missing value became
0), so the sidebar showed a green "fx 0  fy 0 | baseline 0.0 mm" and Run was
enabled. ``load_calibration`` is the one door every caller uses (sidebar,
readiness check, run, 3D view): it now rejects a rig no reconstruction can
use, puts the reason before the file name, and names the format the file
looks like when it is not the chosen one.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from al_dic_3d.calibration import from_opencorr_csv, load_calibration
from al_dic_3d.calibration.importers import guess_format
from al_dic_3d.calibration.model import CameraIntrinsics, StereoRig, rig_problem
from tests.test_calibration_importers import _DICE_SYNTH, _OPENCORR

_QUICKSTART_DICE = Path(__file__).resolve().parents[1] / "quickstart" / "calibration.xml"
_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _write_yaml(path: Path, fx: float = 1200.0, T=(-120.0, 0.0, 0.0)) -> Path:
    import cv2

    K = np.array([[fx, 0.0, 640.0], [0.0, fx, 512.0], [0.0, 0.0, 1.0]])
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    for key, value in (
        ("cameraMatrix1", K),
        ("distCoeffs1", np.zeros(5)),
        ("cameraMatrix2", K),
        ("distCoeffs2", np.zeros(5)),
        ("R", np.eye(3)),
        ("T", np.asarray(T, np.float64).reshape(3, 1)),
    ):
        fs.write(key, value)
    fs.release()
    return path


# ---- OpenCorr: missing fields are an error, not zeros ------------------------------


def test_opencorr_reader_refuses_a_dice_xml(tmp_path):
    f = tmp_path / "dice.xml"
    f.write_text(_DICE_SYNTH, encoding="utf-8")
    with pytest.raises(ValueError, match="not an OpenCorr calibration CSV") as info:
        from_opencorr_csv(f)
    assert "Fx" in str(info.value) and "Tx" in str(info.value)


def test_opencorr_reader_refuses_pyproject_toml():
    with pytest.raises(ValueError, match="not an OpenCorr calibration CSV"):
        from_opencorr_csv(_PYPROJECT)


def test_opencorr_reader_names_the_missing_rows(tmp_path):
    f = tmp_path / "cal.csv"
    f.write_text(
        "\n".join(r for r in _OPENCORR.splitlines() if not r.startswith(("Cy", "Tz"))),
        encoding="utf-8",
    )
    with pytest.raises(ValueError) as info:
        from_opencorr_csv(f)
    text = str(info.value)
    assert "Cy" in text and "Tz" in text and "Fx" not in text


def test_opencorr_optional_rows_may_be_absent(tmp_path):
    f = tmp_path / "cal.csv"
    f.write_text(
        "\n".join(r for r in _OPENCORR.splitlines() if not r.startswith(("K", "P", "Fs"))),
        encoding="utf-8",
    )
    rig = from_opencorr_csv(f)
    assert rig.cameras["L"].fx == 1200.0 and rig.cameras["L"].k1 == 0.0


# ---- a rig no reconstruction can use -------------------------------------------------


def _rig(fx=1200.0, fy=1200.0, T=(-120.0, 0.0, 0.0), cx=640.0) -> StereoRig:
    cam = CameraIntrinsics(fx=fx, fy=fy, cx=cx, cy=512.0)
    return StereoRig(
        cameras={"L": cam, "R": cam},
        extrinsics={("L", "R"): (np.eye(3), np.asarray(T, np.float64))},
    )


def test_rig_problem_accepts_a_sound_rig():
    assert rig_problem(_rig()) is None


@pytest.mark.parametrize(
    ("rig", "expected"),
    [
        (_rig(fx=0.0), "focal length"),
        (_rig(fy=-5.0), "focal length"),
        (_rig(fx=float("nan")), "focal length"),
        (_rig(cx=float("inf")), "not finite"),
        (_rig(T=(0.0, 0.0, 0.0)), "baseline"),
        (_rig(T=(float("nan"), 0.0, 0.0)), "not finite"),
    ],
)
def test_rig_problem_names_what_is_wrong(rig, expected):
    assert expected in rig_problem(rig)


def test_load_calibration_rejects_a_zero_focal_length(tmp_path):
    path = _write_yaml(tmp_path / "zero_fx.yml", fx=0.0)
    with pytest.raises(ValueError, match=r"^camera L: the focal length"):
        load_calibration(path, "opencv_yaml")


def test_load_calibration_rejects_a_zero_baseline(tmp_path):
    path = _write_yaml(tmp_path / "zero_T.yml", T=(0.0, 0.0, 0.0))
    with pytest.raises(ValueError, match=r"^the baseline .* is zero") as info:
        load_calibration(path, "opencv_yaml")
    assert "zero_T.yml" in str(info.value)


def test_load_calibration_passes_a_sound_file(tmp_path):
    rig = load_calibration(_write_yaml(tmp_path / "ok.yml"), "opencv_yaml")
    assert rig.cameras["L"].fx == 1200.0


def test_opencorr_format_on_the_quickstart_dice_file_is_refused():
    with pytest.raises(ValueError) as info:
        load_calibration(_QUICKSTART_DICE, "opencorr")
    text = str(info.value)
    assert text.startswith("not an OpenCorr calibration CSV")
    assert "choose the format 'dice'" in text


# ---- reason first, file name only, and the format the file looks like --------------


def test_a_dice_file_read_as_opencv_yaml_says_why_first(tmp_path):
    deep = tmp_path / ("a_long_folder_name_" * 3) / "nested"
    deep.mkdir(parents=True)
    f = deep / "calibration_DICe.xml"
    f.write_text(_QUICKSTART_DICE.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError) as info:
        load_calibration(f, "opencv_yaml")
    text = str(info.value)
    assert text.startswith("not an OpenCV YAML/XML calibration file")
    assert "calibration_DICe.xml" in text and str(deep) not in text
    assert "it looks like a DICe XML file: choose the format 'dice'" in text


def test_a_missing_file_is_named(tmp_path):
    with pytest.raises(ValueError, match=r"^the file does not exist \(gone.yml\)"):
        load_calibration(tmp_path / "gone.yml", "opencv_yaml")


def test_a_text_file_read_as_mat_is_explained(tmp_path):
    f = tmp_path / "calib.mat"
    f.write_text("not a mat file", encoding="utf-8")
    with pytest.raises(ValueError, match="^not a MATLAB .mat file"):
        load_calibration(f, "mmc")


# ---- format from the file's name or first bytes ----------------------------------------


def test_guess_format_from_the_extension(tmp_path):
    for name, fmt in (("a.caldat", "matchid"), ("a.csv", "opencorr"), ("a.yml", "opencv_yaml"),
                      ("a.YAML", "opencv_yaml"), ("a.txt", None), ("a", None)):  # fmt: skip
        f = tmp_path / name
        f.write_text("x", encoding="utf-8")
        assert guess_format(f) == fmt, name


def test_guess_format_tells_the_two_xml_formats_apart(tmp_path):
    assert guess_format(_QUICKSTART_DICE) == "dice"
    assert guess_format(_write_yaml(tmp_path / "rig.xml")) == "opencv_yaml"
    other = tmp_path / "other.xml"
    other.write_text("<root><a/></root>", encoding="utf-8")
    assert guess_format(other) is None


def test_guess_format_tells_the_two_mat_formats_apart(tmp_path):
    from scipy.io import savemat

    K = np.eye(3)
    savemat(str(tmp_path / "mmc.mat"), {"Camera_0001_Group_0001_IntrinsicMatrix": K})
    savemat(str(tmp_path / "cv.mat"), {"K_left": K, "K_right": K})
    savemat(str(tmp_path / "x.mat"), {"something": K})
    (tmp_path / "bad.mat").write_text("text", encoding="utf-8")
    assert guess_format(tmp_path / "mmc.mat") == "mmc"
    assert guess_format(tmp_path / "cv.mat") == "matlabcv"
    assert guess_format(tmp_path / "x.mat") is None
    assert guess_format(tmp_path / "bad.mat") is None
    assert guess_format(tmp_path / "missing.mat") is None
