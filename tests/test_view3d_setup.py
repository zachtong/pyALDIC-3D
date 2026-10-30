"""Qt-free 3D view set-up: specimen-aligned presets, magnification, colour range, bar."""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.viz3d.view_setup import (
    MAGNIFICATIONS,
    auto_magnification,
    frustum_size,
    magnify,
    preset_camera,
    preset_direction,
    safe_clim,
    scalar_bar_args,
    specimen_axes,
    tick_format,
)

Z0 = 245.0


def _plate(tilt_deg: float = 10.0, n: int = 15) -> np.ndarray:
    """A flat 7 mm plate in front of the left camera, tilted about world y."""
    ii, jj = np.meshgrid(np.linspace(-3.5, 3.5, n), np.linspace(-3.5, 3.5, n))
    pts = np.column_stack([ii.ravel(), jj.ravel(), np.zeros(n * n)])
    t = np.radians(tilt_deg)
    rot = np.array([[np.cos(t), 0, np.sin(t)], [0, 1, 0], [-np.sin(t), 0, np.cos(t)]])
    return pts @ rot.T + [0.0, 0.0, Z0]


def test_specimen_axes_face_the_camera_and_keep_image_up():
    c, ex, ey, n = specimen_axes(_plate())
    assert n @ (-c) > 0  # the normal points back toward the left camera
    assert ex[0] > 0.9  # world +x, projected into the plate
    assert ey[1] < -0.9  # image-up is world -y
    assert np.allclose([ex @ ey, ex @ n, ey @ n], 0.0, atol=1e-12)


def test_presets_look_from_the_expected_sides():
    pts = _plate()
    _, ex, ey, n = specimen_axes(pts)
    cam_dir, cam_up = preset_direction("camera", pts)
    assert cam_dir[2] < -0.99 and cam_up[1] < -0.99  # from the camera, image-up = -y
    normal_dir, normal_up = preset_direction("normal", pts)
    assert np.allclose(normal_dir, n) and np.allclose(normal_up, ey)
    side_dir, side_up = preset_direction("side", pts)
    assert np.allclose(side_dir, -ex) and np.allclose(side_up, n)  # profile: normal up
    iso_dir, iso_up = preset_direction("iso", pts)
    assert iso_dir @ n > 0.5 and abs(iso_dir @ iso_up) < 1e-12
    with pytest.raises(ValueError, match="preset"):
        preset_direction("back", pts)


def test_preset_camera_is_a_plain_tuple_on_the_centroid():
    pts = _plate()
    position, focal, up = preset_camera("normal", pts)
    assert np.allclose(focal, pts.mean(axis=0))
    assert all(isinstance(v, float) for part in (position, focal, up) for v in part)
    assert preset_camera("camera", np.full((5, 3), np.nan)) is None


def test_magnify_scales_the_change_and_can_keep_only_the_normal_part():
    ref = _plate(tilt_deg=0.0)
    disp = np.zeros_like(ref)
    disp[:, 2] = 1e-3 * (ref[:, 0] ** 2)  # out-of-plane bowl
    disp[:, 0] = 2e-4  # a small in-plane shift
    cur = ref + disp

    assert magnify(ref, cur, 1.0) is not None
    np.testing.assert_array_equal(magnify(ref, cur, 1.0), cur)  # true scale untouched
    np.testing.assert_allclose(magnify(ref, cur, 100.0), ref + 100.0 * disp)
    normal_only = magnify(ref, cur, 100.0, normal_only=True)
    np.testing.assert_allclose(normal_only[:, :2], ref[:, :2], atol=1e-12)  # no in-plane part
    np.testing.assert_allclose(normal_only[:, 2], ref[:, 2] + 100.0 * disp[:, 2], atol=1e-9)


def test_auto_magnification_makes_a_micron_bowl_visible():
    ref = _plate(tilt_deg=0.0)
    cur = ref.copy()
    cur[:, 2] += 7e-3 * (ref[:, 0] ** 2 + ref[:, 1] ** 2) / 24.5  # ~7 µm over 7 mm
    factor = auto_magnification(ref, cur)
    assert factor in MAGNIFICATIONS and factor >= 50
    assert auto_magnification(ref, ref) == 1.0  # nothing moved: true scale


def test_colour_range_and_scalar_bar():
    assert safe_clim(0.0, 0.0)[1] > safe_clim(0.0, 0.0)[0]  # frame 1: all-zero field
    assert safe_clim(np.nan, 1.0) == (0.0, 1.0)
    assert tick_format(-2.92, 3.31) == "%.2f"
    assert tick_format(0.0, 0.0012) == "%.5f"
    assert tick_format(0.0, 0.0) == "%.3g"
    args = scalar_bar_args("W (µm)", "white", -2.9, 3.3)
    assert args["title"] == "W (µm)" and args["fmt"] == "%.2f"
    assert args["position_x"] + args["width"] <= 0.95  # the bar stays inside the view


def test_frustum_size_follows_the_stand_off():
    assert frustum_size(_plate()) == pytest.approx(0.12 * Z0, rel=0.01)
