"""Default-option calibration results are pinned (calibration diagnostics brief, 7.3).

The diagnostics only add information. With default options the rig, the RMS,
the pair QC, the warnings and the YAML nodes other than ``meta_*`` must not
change. The reference was captured from the solver before the diagnostics work
began; regenerate it (``python -m tests.test_calib_pinning``) only for a change
that is meant to move these numbers, and say so in the commit.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

import tests.synth_calib as sc
import tests.synth_calib_points as sp
from al_dic_3d.calibration import ChessboardSpec, CircleGridSpec, calibrate_stereo, to_opencv_yaml

REFERENCE = Path(__file__).with_name("data") / "calib_pinning_reference.json"
CHESS = ChessboardSpec(cols=9, rows=7, square_size=12.0)
DOTS = CircleGridSpec(cols=9, rows=7, spacing=12.0, dot_diameter=6.0)
# OpenCV 4.14 and 5.0 differ by up to 3.4e-6 relative on these cases (per-pair
# RMS, R); a changed option or data flow moves them by 1e-4 or more.
RTOL, ATOL = 2e-5, 1e-7
_INTRINSIC_FIELDS = ("fx", "fy", "cx", "cy", "skew", "k1", "k2", "p1", "p2", "k3")


def _extent(spec) -> tuple[float, float]:
    pts = spec.object_points()
    return float(np.ptp(pts[:, 0])), float(np.ptp(pts[:, 1]))


def _solve(spec, *, dot_radius_mm=None):
    rig = sc.make_rig()
    poses = sc.board_poses(_extent(spec), n=12)
    left = sp.detections(spec, rig, poses, "L", noise_px=0.02, seed=1)
    right = sp.detections(spec, rig, poses, "R", noise_px=0.02, seed=2)
    return calibrate_stereo(left, right, (sc.IMG_W, sc.IMG_H), dot_radius_mm=dot_radius_mm)


def _yaml_nodes(path: Path) -> dict[str, list[float]]:
    import cv2

    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    try:
        return {
            name: np.asarray(fs.getNode(name).mat(), np.float64).ravel().tolist()
            for name in fs.root().keys()
            if not name.startswith("meta_")
        }
    finally:
        fs.release()


def _record(result, workdir: Path) -> dict:
    rot, t = result.rig.pose("R")
    yaml_path = to_opencv_yaml(result.rig, workdir / "pin.yml", meta={"source": "pinning"})
    return {
        "cameras": {
            key: {f: float(getattr(cam, f)) for f in _INTRINSIC_FIELDS}
            for key, cam in sorted(result.rig.cameras.items())
        },
        "R": np.asarray(rot).ravel().tolist(),
        "T": np.asarray(t).ravel().tolist(),
        "rms": result.rms,
        "epipolar_rms": result.epipolar_rms,
        "pairs": [
            [p.index, p.used, p.rms_left, p.rms_right, p.n_common, p.note] for p in result.pairs
        ],
        "mono": {
            key: {"rms": m.rms, "views": [int(i) for i in m.view_indices]}
            for key, m in sorted(result.mono.items())
        },
        "warnings": list(result.warnings),
        "yaml": _yaml_nodes(yaml_path),
    }


CASES = {
    "chessboard": dict(spec=CHESS),
    "circle_grid_eccentricity": dict(spec=DOTS, dot_radius_mm=DOTS.dot_mm / 2.0),
}


def _assert_same(actual, expected, where: str = "") -> None:
    if isinstance(expected, dict):
        assert sorted(actual) == sorted(expected), where
        for key in expected:
            _assert_same(actual[key], expected[key], f"{where}.{key}")
    elif isinstance(expected, list):
        assert len(actual) == len(expected), where
        for i, (a, e) in enumerate(zip(actual, expected, strict=True)):
            _assert_same(a, e, f"{where}[{i}]")
    elif isinstance(expected, float) and not isinstance(expected, bool):
        if math.isnan(expected):
            assert math.isnan(actual), where
        else:
            assert actual == pytest.approx(expected, rel=RTOL, abs=ATOL), where
    else:
        assert actual == expected, where


@pytest.mark.parametrize("name", sorted(CASES))
def test_default_calibration_is_unchanged(name, tmp_path):
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))[name]
    case = CASES[name]
    result = _solve(case["spec"], dot_radius_mm=case.get("dot_radius_mm"))
    _assert_same(_record(result, tmp_path), reference, name)


def _write_reference() -> None:  # pragma: no cover - maintenance entry point
    import tempfile

    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        for name, case in sorted(CASES.items()):
            result = _solve(case["spec"], dot_radius_mm=case.get("dot_radius_mm"))
            out[name] = _record(result, Path(tmp))
    REFERENCE.parent.mkdir(exist_ok=True)
    REFERENCE.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {REFERENCE}")


if __name__ == "__main__":  # pragma: no cover
    _write_reference()
