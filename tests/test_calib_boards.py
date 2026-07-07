"""Unit tests for calibration board specs (boards.py) — no rendering needed."""

import numpy as np
import pytest

from al_dic_3d.calibration import (
    CharucoSpec,
    ChessboardSpec,
    CircleGridSpec,
    CodedCircleGridSpec,
)


def test_chessboard_object_points_lattice():
    spec = ChessboardSpec(cols=9, rows=7, square_size=12.0)
    obj = spec.object_points()
    assert obj.shape == (63, 3)
    assert obj.dtype == np.float64
    # row-major OpenCV corner order: index i*cols + j -> (j*sq, i*sq, 0)
    assert np.allclose(obj[0], [0, 0, 0])
    assert np.allclose(obj[8], [8 * 12.0, 0, 0])
    assert np.allclose(obj[9], [0, 12.0, 0])
    assert np.all(obj[:, 2] == 0)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(cols=2, rows=7, square_size=12.0),
        dict(cols=9, rows=7, square_size=0.0),
    ],
)
def test_chessboard_validation(kwargs):
    with pytest.raises(ValueError):
        ChessboardSpec(**kwargs)


def test_chessboard_render_has_quiet_border():
    spec = ChessboardSpec(cols=4, rows=3, square_size=10.0)
    img = spec.render(px_per_mm=2.0)
    assert img.dtype == np.uint8
    sq = 20
    assert np.all(img[:sq] == 255) and np.all(img[:, :sq] == 255)  # white border


def test_charuco_validation_and_points():
    with pytest.raises(ValueError):
        CharucoSpec(squares_x=10, squares_y=8, square_size=12.0, marker_size=12.5)
    spec = CharucoSpec(squares_x=10, squares_y=8, square_size=12.0, marker_size=9.0)
    obj = spec.object_points()
    assert obj.shape == (9 * 7, 3)  # interior corners
    # ChArUco object frame originates at the board's OUTER corner.
    assert np.allclose(obj[0], [12.0, 12.0, 0.0])


def test_circle_grid_asymmetric_object_points():
    spec = CircleGridSpec(cols=4, rows=5, spacing=10.0, asymmetric=True)
    obj = spec.object_points()
    assert obj.shape == (20, 3)
    # OpenCV sample convention: ((2*col + row%2) * spacing, row * spacing, 0)
    assert np.allclose(obj[0], [0, 0, 0])
    assert np.allclose(obj[4], [10.0, 10.0, 0])  # row 1 staggers by one spacing


def test_coded_grid_default_fiducials_are_asymmetric():
    spec = CodedCircleGridSpec(cols=11, rows=9, spacing=12.0)
    assert len(spec.fiducials) == 3
    d = [
        (r1 - r2) ** 2 + (c1 - c2) ** 2
        for i, (r1, c1) in enumerate(spec.fiducials)
        for r2, c2 in spec.fiducials[i + 1 :]
    ]
    assert len(set(d)) == 3  # all pairwise distances distinct -> unambiguous
    assert all(0 <= r < 9 and 0 <= c < 11 for r, c in spec.fiducials)


def test_coded_grid_rejects_symmetric_fiducials():
    with pytest.raises(ValueError, match="distinct"):
        CodedCircleGridSpec(cols=11, rows=9, spacing=12.0, fiducials=((4, 3), (4, 7), (2, 5)))


def test_coded_grid_point_ids():
    spec = CodedCircleGridSpec(cols=11, rows=9, spacing=12.0)
    assert spec.point_id(0, 0) == 0
    assert spec.point_id(1, 0) == 11
    assert len(set(spec.fiducial_ids)) == 3


def test_dot_boards_render_dark_dots_on_white():
    for spec in (
        CircleGridSpec(cols=5, rows=4, spacing=10.0),
        CodedCircleGridSpec(cols=7, rows=6, spacing=10.0),
    ):
        img = spec.render(px_per_mm=4.0)
        assert img.dtype == np.uint8
        assert img.min() < 60 and img.max() == 255
