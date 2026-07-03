"""Tests for StereoSequence pairing validation (Phase 1, step 3)."""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.sequence import ArrayFrameProvider, FrameProvider, StereoSequence


def _frames(n: int, h: int = 32, w: int = 40) -> list[np.ndarray]:
    rng = np.random.default_rng(0)
    return [rng.random((h, w)) for _ in range(n)]


def _seq(nL=3, nR=3, hw=(32, 40), masks=None, names=None) -> StereoSequence:
    return StereoSequence(
        providers={
            "L": ArrayFrameProvider(_frames(nL, *hw)),
            "R": ArrayFrameProvider(_frames(nR, *hw)),
        },
        masks=masks or {},
        names=names or {},
    )


def test_array_provider_conforms_to_protocol():
    p = ArrayFrameProvider(_frames(2))
    assert isinstance(p, FrameProvider)
    assert len(p) == 2
    assert p.shape == (32, 40)
    assert p.get_normalized(1).shape == (32, 40)


def test_valid_sequence_passes():
    seq = _seq()
    assert seq.issues() == []
    seq.validate()  # no raise
    assert seq.n_frames == 3
    assert seq.cameras == ("L", "R")
    assert seq.frame("R", 2).shape == (32, 40)
    assert seq.mask("L", 0) is None


def test_frame_count_mismatch():
    seq = _seq(nL=3, nR=4)
    problems = seq.issues()
    assert any("frame-count mismatch" in p for p in problems)
    with pytest.raises(ValueError, match="frame-count mismatch"):
        seq.validate()


def test_empty_sequence():
    seq = StereoSequence(providers={"L": ArrayFrameProvider([]), "R": ArrayFrameProvider([])})
    assert any("empty sequence" in p for p in seq.issues())


def test_mask_shape_mismatch():
    good = [np.ones((32, 40)) for _ in range(3)]
    bad = [np.ones((32, 40)), np.ones((16, 20)), np.ones((32, 40))]  # frame 1 wrong size
    seq = _seq(masks={"L": good, "R": bad})
    problems = seq.issues()
    assert any("mask" in p and "frame 1" in p for p in problems)


def test_mask_count_mismatch():
    seq = _seq(masks={"L": [np.ones((32, 40))]})  # 1 mask, 3 frames
    assert any("masks for" in p for p in seq.issues())
    assert seq.mask("L", 0) is not None


def test_valid_masks_pass():
    masks = {"L": [np.ones((32, 40)) for _ in range(3)], "R": [np.ones((32, 40)) for _ in range(3)]}
    assert _seq(masks=masks).issues() == []


def test_name_pattern_match_and_mismatch():
    ok = {
        "L": ["camL_0001.tif", "camL_0002.tif", "camL_0003.tif"],
        "R": ["camR_0001.tif", "camR_0002.tif", "camR_0003.tif"],
    }
    assert _seq(names=ok).issues() == []

    swapped = {
        "L": ["L_1.tif", "L_2.tif", "L_3.tif"],
        "R": ["R_1.tif", "R_3.tif", "R_2.tif"],
    }  # frames 2/3 swapped in R
    assert any("name-pattern mismatch" in p for p in _seq(names=swapped).issues())
