"""One unusable frame must not throw away the whole run (fix batch V, finding H3).

The 2D engine zero-fills a frame on which it solved no node at all, with only a
UserWarning. 3D promoted that warning to a hard error for the WHOLE track, so a
single black / blown-out frame in a long sequence discarded every other frame.
The zero-filled frame itself must still never be trusted (a frozen camera looks
perfectly valid), so it is invalidated — and only it.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

pytest.importorskip("al_dic")

from al_dic_3d.runner import load_config, run_pipeline  # noqa: E402
from tests import synth_stereo  # noqa: E402


def test_a_black_frame_is_invalidated_and_the_rest_is_kept(tmp_path):
    scene = synth_stereo.build_scene(tmp_path, n_frames=4)
    black = tmp_path / "L_002.png"
    img = cv2.imread(str(black), cv2.IMREAD_UNCHANGED)
    cv2.imwrite(str(black), np.zeros_like(img))

    result = run_pipeline(load_config(synth_stereo.write_config(tmp_path, scene)))
    pts = result.reconstruction.points
    valid = np.isfinite(pts).all(axis=2)  # (frames, nodes)
    assert valid[0].mean() > 0.9
    assert valid[1].mean() > 0.9, "frames before the bad one must survive"
    assert not valid[2].any(), "the zero-filled frame must never be shipped"
    rows = [r for r in result.meta["diagnostics"] if r["cam"] == "L" and r["frame"] == 2]
    assert rows and "no node" in rows[0]["note"], rows


def test_parallel_cameras_also_drop_only_the_bad_frame(tmp_path):
    # In parallel-camera mode the warning recorder is process-wide; it now pins
    # the zero-fill to the emitting camera's frame instead of failing the run.
    import sys
    from dataclasses import replace

    if sys.platform == "darwin":
        pytest.skip("parallel camera tracking runs sequentially on macOS")
    scene = synth_stereo.build_scene(tmp_path, n_frames=4)
    black = tmp_path / "L_002.png"
    img = cv2.imread(str(black), cv2.IMREAD_UNCHANGED)
    cv2.imwrite(str(black), np.zeros_like(img))

    cfg = replace(load_config(synth_stereo.write_config(tmp_path, scene)), parallel_cameras=True)
    result = run_pipeline(cfg)
    valid = np.isfinite(result.reconstruction.points).all(axis=2)
    assert valid[1].mean() > 0.9 and not valid[2].any()
    rows = [r for r in result.meta["diagnostics"] if r["cam"] == "L" and r["frame"] == 2]
    assert rows and "no node" in rows[0]["note"], rows
