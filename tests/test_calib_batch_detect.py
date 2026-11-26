"""``detect_files``: several images at a time, results and progress in input order.

Each image is decoded once (its size comes back with its detection), the
callback runs on the calling thread, and an unreadable file stops the run
after the files before it were reported, as the sequential loop did.
"""

from __future__ import annotations

import threading

import numpy as np
import pytest

pytest.importorskip("cv2")

from al_dic_3d.calibration import UnreadableImageError, detect_files  # noqa: E402
from al_dic_3d.calibration.batch_detect import MAX_WORKERS, default_workers  # noqa: E402
from al_dic_3d.pathsafe import imwrite_unicode  # noqa: E402
from tests.test_calib_fast_detection import SPEC, _render  # noqa: E402


@pytest.fixture(scope="module")
def image_files(tmp_path_factory):
    """Six 1400x1100 views (one without a board), 8- and 16-bit, on disk."""
    out = tmp_path_factory.mktemp("batch_detect")
    paths = []
    for k in range(6):
        if k == 3:
            image = np.full((1100, 1400), 200, np.uint8)
        else:
            image, _truth = _render(1400, 1100, 5.0 + 0.5 * k, seed=k)
        if k % 2:
            image = image.astype(np.uint16) * 16  # 12-bit data in a 16-bit file
        path = out / f"view_{k}.png"
        imwrite_unicode(path, image)
        paths.append(str(path))
    return paths


def test_detect_files_parallel_matches_sequential_in_input_order(image_files):
    calls: list[tuple[int, int]] = []

    def on_result(index, _det):
        calls.append((index, threading.get_ident()))

    found = detect_files(image_files, SPEC, workers=4, on_result=on_result)
    assert [k for k, _t in calls] == list(range(len(image_files)))
    assert {t for _k, t in calls} == {threading.get_ident()}  # on the calling thread
    assert found.sizes == tuple((1400, 1100) for _ in image_files)
    sequential = detect_files(image_files, SPEC, workers=1)
    for got, want, path in zip(found.detections, sequential.detections, image_files, strict=True):
        assert got.ok == want.ok, path
        # Same corners, but not always to the last bit: OpenCV splits its own
        # internal parallel work differently when several Python threads call
        # it at once (6e-5 px seen in a full-suite run), far below the corner
        # accuracy of 0.01-0.05 px.
        np.testing.assert_allclose(got.image_points, want.image_points, rtol=0, atol=1e-3)
    assert [d.ok for d in found.detections] == [True, True, True, False, True, True]
    assert found.detections[3].reason


def test_detect_files_stops_at_an_unreadable_image(image_files, tmp_path):
    missing = str(tmp_path / "missing.png")
    paths = [image_files[0], image_files[1], missing, image_files[2]]
    seen: list[int] = []
    with pytest.raises(UnreadableImageError) as info:
        detect_files(paths, SPEC, workers=3, on_result=lambda k, _d: seen.append(k))
    assert info.value.path == missing
    assert str(info.value) == f"cannot read image: {missing}"
    assert seen == [0, 1]  # the images before it are reported, nothing after


def test_default_workers_bounds():
    assert default_workers(1) == 1
    assert default_workers(0) == 1
    assert 1 <= default_workers(1000) <= MAX_WORKERS
