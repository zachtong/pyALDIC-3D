"""3D-view sequence export must render every frame (fix batch V, blocker B4).

``export_view3d_frames`` updates the live mesh in place when a frame keeps the
previous topology, but never re-rendered before the screenshot: pyvista only
renders inside ``screenshot()`` on the first call, so every later PNG/MP4/GIF
frame was a copy of the first (a clean run exported as a still image). The
same stale-framebuffer bug was fixed for the turntable only (1bfe769).
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("pyvista")
pytest.importorskip("al_dic")

import cv2  # noqa: E402

from al_dic_3d.export.render3d import export_view3d_frames  # noqa: E402
from al_dic_3d.runner import load_config, run_pipeline  # noqa: E402
from tests import synth_stereo  # noqa: E402


def test_consecutive_exported_3d_frames_differ(tmp_path):
    scene = synth_stereo.build_scene(tmp_path, n_frames=4)
    result = run_pipeline(load_config(synth_stereo.write_config(tmp_path, scene)))
    pts = result.reconstruction.points
    assert np.isfinite(pts).all(axis=2).all(axis=1).any()  # something to draw

    out = tmp_path / "view3d"
    paths = export_view3d_frames(out, "chk", "ts", result, "U", window_size=(320, 240))
    pngs = [p for p in paths if str(p).endswith(".png")]
    assert len(pngs) == 4
    imgs = [
        cv2.imdecode(np.fromfile(str(p), np.uint8), cv2.IMREAD_COLOR).astype(np.int16) for p in pngs
    ]
    diffs = [float(np.abs(b - a).mean()) for a, b in zip(imgs, imgs[1:], strict=False)]
    # Before the fix: [0.0, 0.0, 0.0] — every frame was the first one.
    assert all(d > 0.05 for d in diffs), diffs
