"""Per-frame mask files reach the solver as {0, 1} (fix batch V, blocker B2).

The 2D engine multiplies image gradients by the mask, so a mask file stored the
usual way (8-bit 0/255) scaled the IC-GN Hessian by 255^2 and the right-hand side
by 255: every update step came out 1/255 of its true size, the step-size stopping
test accepted the integer seed, and stereo links "converged" on it. On the Stereo
DIC Challenge 1.0 S3 data that halved the frame-0 stereo yield (47% instead of
97% of in-mask nodes) and left a 0.25 px median error on the survivors.
"""

from __future__ import annotations

import dataclasses

import cv2
import numpy as np
import pytest

pytest.importorskip("al_dic")

from al_dic_3d.matching.primitives import make_dicpara  # noqa: E402
from al_dic_3d.runner import load_config, run_pipeline  # noqa: E402
from al_dic_3d.sequence.lazy import LazyMaskList, as_binary_mask  # noqa: E402
from tests import synth_stereo  # noqa: E402


def _write(path, array) -> None:
    ok, buf = cv2.imencode(".png", array)
    assert ok
    buf.tofile(str(path))


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def test_as_binary_mask_keeps_a_binary_float64_array_without_copying():
    m = np.zeros((4, 5), dtype=np.float64)
    m[1:3, 1:4] = 1.0
    assert as_binary_mask(m) is m


@pytest.mark.parametrize(
    "raw",
    [
        np.array([[0, 255], [255, 0]], dtype=np.uint8),
        np.array([[0, 65535], [65535, 0]], dtype=np.uint16),
        np.array([[0.0, 255.0], [255.0, 0.0]]),
        np.array([[False, True], [True, False]]),
        np.array([[0, 7], [3, 0]], dtype=np.int32),
    ],
)
def test_as_binary_mask_maps_nonzero_to_one(raw):
    out = as_binary_mask(raw)
    assert out.dtype == np.float64 and out.flags["C_CONTIGUOUS"]
    assert np.array_equal(out, [[0.0, 1.0], [1.0, 0.0]])


def test_lazy_mask_list_serves_binary_masks_for_8_and_16_bit_files(tmp_path):
    m8 = np.zeros((6, 7), np.uint8)
    m8[2:5, 1:6] = 255
    m16 = (m8.astype(np.uint16) * 257).astype(np.uint16)
    _write(tmp_path / "a.png", m8)
    _write(tmp_path / "b.png", m16)
    masks = LazyMaskList([tmp_path / "a.png", tmp_path / "b.png"])
    for got in (masks[0], masks[1]):
        assert got.dtype == np.float64 and got.flags["C_CONTIGUOUS"]
        assert set(np.unique(got)) == {0.0, 1.0}
        assert np.array_equal(got > 0, m8 > 0)


def test_make_dicpara_binarizes_the_reference_mask():
    m = np.zeros((64, 64), np.uint8)
    m[8:56, 8:56] = 255
    para = make_dicpara(img_size=(64, 64), roi=(8, 55, 8, 55), img_ref_mask=m)
    assert set(np.unique(para.img_ref_mask)) == {0.0, 1.0}


# --------------------------------------------------------------------------- #
# end to end: 0/255 mask FILES must behave exactly like "everything valid"
# --------------------------------------------------------------------------- #


def _same_points(a, b) -> None:
    p0, p1 = a.reconstruction.points, b.reconstruction.points
    assert np.array_equal(np.isfinite(p0), np.isfinite(p1))
    fin = np.isfinite(p0)
    assert np.max(np.abs(p0[fin] - p1[fin])) < 1e-9


def test_full_frame_0_255_mask_files_match_0_1_and_unmasked_runs(tmp_path):
    scene = synth_stereo.build_scene(tmp_path, n_frames=3)
    cfg = load_config(synth_stereo.write_config(tmp_path, scene))
    left0 = sorted(tmp_path.glob("L_*.png"))[0]
    h, w = cv2.imread(str(left0), cv2.IMREAD_UNCHANGED).shape[:2]
    for k in range(3):
        for cam in "LR":
            _write(tmp_path / f"m{cam}_{k:03d}.png", np.full((h, w), 255, np.uint8))
            _write(tmp_path / f"o{cam}_{k:03d}.png", np.ones((h, w), np.uint8))

    # Before the fix 0/255 files gave ~62% stereo yield and a ~10x larger 3D
    # error on this scene than the same masks saved as 0/1.
    _same_points(
        run_pipeline(dataclasses.replace(cfg, left_masks="mL_*.png", right_masks="mR_*.png")),
        run_pipeline(dataclasses.replace(cfg, left_masks="oL_*.png", right_masks="oR_*.png")),
    )
    # Left masks only: the right camera derives its region from them, as it
    # does from the left mesh when there are no masks at all.
    _same_points(
        run_pipeline(dataclasses.replace(cfg, left_masks="mL_*.png")),
        run_pipeline(cfg),
    )
