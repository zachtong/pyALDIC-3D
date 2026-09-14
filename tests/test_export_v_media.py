"""Rendered-media export honesty (fix batch V: H4, H5, M3, M6 and the export lows).

* A video/GIF writer that cannot open RAISES — it used to ``break`` and return
  an empty list, which the dialog showed as a green "Wrote 0 file(s)".
* GIF: frames stream to disk (imageio buffered every frame until close) and the
  frame delay is honoured (``duration`` was passed in seconds to a writer that
  expects milliseconds, so every GIF had no delay at all).
* MP4: odd frame sizes are padded to even, never cropped.
* Frames that cannot be rendered keep the animation's timing and are reported;
  a cancelled animation's partial file is deleted, not counted as written.
* The right camera uses the left ROI warped through the frame-1 correspondence
  (what the canvas shows), not the bare node hull.
* Backgrounds keep their bit depth and get the canvas's min/max stretch (12-bit
  data in 16-bit files came out black).
"""

from __future__ import annotations

import threading

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d.export import (  # noqa: E402
    ExportOutcome,
    FieldImageConfig,
    StreamingAnimWriter,
    export_animation,
    export_image_frames,
    render_field_frame,
)
from tests.synth_export import grid_result, write_gray_frames  # noqa: E402


def _gif_delays(path) -> list[int]:
    from PIL import Image

    im = Image.open(path)
    delays = []
    try:
        while True:
            delays.append(int(im.info.get("duration", 0)))
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    return delays


def _frames(n: int, h: int = 48, w: int = 64) -> list[np.ndarray]:
    out = []
    for i in range(n):
        f = np.zeros((h, w, 3), np.uint8)
        f[:, :, 1] = 40
        f[8:24, (3 * i) % w : (3 * i) % w + 10] = (0, 0, 255)
        out.append(f)
    return out


# ---------------------------------------------------------------------------
# Writer open failures raise (H5)
# ---------------------------------------------------------------------------


class _ClosedVideoWriter:
    def __init__(self, *args, **kwargs):
        pass

    def isOpened(self):  # noqa: N802 - cv2 API
        return False

    def release(self):
        pass


def test_mp4_writer_that_cannot_open_raises(tmp_path, monkeypatch):
    from al_dic_3d.export import animation

    monkeypatch.setattr(animation.cv2, "VideoWriter", _ClosedVideoWriter)
    with pytest.raises(OSError, match="video encoder"):
        StreamingAnimWriter("mp4", tmp_path, "L_U", 10, (32, 40))


def test_gif_writer_on_missing_folder_raises(tmp_path):
    with pytest.raises(OSError):
        StreamingAnimWriter("gif", tmp_path / "missing" / "deeper", "L_U", 10, (32, 40))


def test_export_animation_raises_when_the_encoder_cannot_open(tmp_path, monkeypatch):
    from al_dic_3d.export import animation

    monkeypatch.setattr(animation.cv2, "VideoWriter", _ClosedVideoWriter)
    result = grid_result(n_frames=2)
    with pytest.raises(OSError):
        export_animation(
            tmp_path,
            "p",
            "20260913000000",
            result,
            {},
            [FieldImageConfig(field_id="U")],
            fmt="mp4",
            mesh_step=16,
            include_colorbar=False,
        )


# ---------------------------------------------------------------------------
# GIF: timing + streaming (H4)
# ---------------------------------------------------------------------------


def test_gif_frame_delay_follows_fps(tmp_path):
    w = StreamingAnimWriter("gif", tmp_path, "slow", 5, (48, 64))
    for f in _frames(4):
        w.append(f)
    w.close()
    assert _gif_delays(w.out) == [200, 200, 200, 200]

    w = StreamingAnimWriter("gif", tmp_path, "fast", 30, (48, 64))
    for f in _frames(30):
        w.append(f)
    w.close()
    delays = _gif_delays(w.out)
    assert len(delays) == 30
    assert sum(delays) == 1000  # 30 frames at 30 fps last exactly one second
    assert set(delays) <= {30, 40}


def test_gif_frames_stream_to_disk_before_close(tmp_path):
    w = StreamingAnimWriter("gif", tmp_path, "stream", 10, (48, 64))
    sizes = []
    for f in _frames(5):
        w.append(f)
        sizes.append(w.out.stat().st_size)
    w.close()
    assert sizes[0] > 0
    assert all(b > a for a, b in zip(sizes, sizes[1:], strict=False)), sizes


def test_gif_faster_than_50_fps_is_clamped_and_misuse_is_refused(tmp_path):
    from al_dic_3d.export import GIF_MAX_FPS, GifStreamWriter

    assert GIF_MAX_FPS == 50
    w = StreamingAnimWriter("gif", tmp_path, "fast", 120, (48, 64))
    for f in _frames(4):
        w.append(f)
    w.close()
    assert _gif_delays(w.out) == [20, 20, 20, 20]  # 2 cs floor: viewers slow 0-1 cs

    g = GifStreamWriter(tmp_path / "g.gif", 10)
    g.append_rgb(np.zeros((8, 8, 3), np.uint8))
    with pytest.raises(ValueError, match="size"):
        g.append_rgb(np.zeros((9, 8, 3), np.uint8))
    g.close()
    g.close()  # idempotent
    with pytest.raises(ValueError, match="closed"):
        g.append_rgb(np.zeros((8, 8, 3), np.uint8))


def test_outcome_bookkeeping_merges_and_cleans_up(tmp_path):
    from al_dic_3d.export import ExportOutcome
    from al_dic_3d.export.outcome import raise_if_stopped, unlink_quietly

    a = ExportOutcome([tmp_path / "a.png"], skipped=["L_U frame_2"])
    b = ExportOutcome([tmp_path / "b.gif"], cancelled=True, unavailable=["R_exx"], warnings=["w"])
    b.discarded.append(tmp_path / "c.gif")
    a.absorb(b).absorb([tmp_path / "d.png"])
    assert len(a) == 3 and a.cancelled
    assert a.skipped == ["L_U frame_2"] and a.unavailable == ["R_exx"]
    assert a.discarded == [tmp_path / "c.gif"] and a.warnings == ["w"]
    unlink_quietly(None)
    unlink_quietly(tmp_path / "never-existed.tmp")
    (tmp_path / "busy").mkdir()
    unlink_quietly(tmp_path / "busy")  # a folder: OSError swallowed, nothing raised
    raise_if_stopped(None)
    raise_if_stopped(threading.Event())


def test_display_gray_handles_colour_float_and_unreadable_images(tmp_path):
    from al_dic_3d.pathsafe import imwrite_unicode
    from al_dic_3d.viz3d.background import image_shape, load_display_gray, stretch_to_u8

    colour = np.zeros((10, 12, 3), np.uint8)
    colour[:, 6:] = (40, 120, 200)
    imwrite_unicode(tmp_path / "c.png", colour)
    gray = load_display_gray(tmp_path / "c.png")
    assert gray.shape == (10, 12) and gray.min() == 0 and gray.max() == 255
    assert image_shape(tmp_path / "c.png") == (10, 12)

    ramp = np.linspace(-1.0, 3.0, 20, dtype=np.float32).reshape(4, 5)
    np.testing.assert_array_equal(
        stretch_to_u8(ramp),
        np.clip((ramp.astype(np.float64) + 1.0) / 4.0 * 255.0, 0, 255).astype(np.uint8),
    )
    assert stretch_to_u8(np.full((3, 3), 7, np.uint16)).max() == 0  # flat image -> black
    assert stretch_to_u8(np.zeros((0, 4), np.uint8)).shape == (0, 4)
    assert load_display_gray(tmp_path / "missing.png") is None
    assert image_shape(tmp_path / "missing.png") is None


def test_gif_decodes_to_the_appended_frames(tmp_path):
    from PIL import Image

    frames = _frames(6)
    frames.insert(3, frames[2].copy())  # an unchanged frame keeps its slot
    w = StreamingAnimWriter("gif", tmp_path, "exact", 10, (48, 64))
    for f in frames:
        w.append(f)
    w.close()
    im = Image.open(w.out)
    decoded = []
    try:
        while True:
            decoded.append(np.asarray(im.convert("RGB")))
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    assert len(decoded) == len(frames)
    for got, want in zip(decoded, frames, strict=True):
        np.testing.assert_array_equal(got, cv2.cvtColor(want, cv2.COLOR_BGR2RGB))


# ---------------------------------------------------------------------------
# MP4 odd sizes are padded (low)
# ---------------------------------------------------------------------------


def test_mp4_odd_frame_size_is_padded_not_cropped(tmp_path):
    h, w = 301, 401
    frame = np.zeros((h, w, 3), np.uint8)
    frame[:, w - 1] = (255, 255, 255)  # last column: cropped away before the fix
    frame[h - 1, :] = (255, 255, 255)  # last row
    wr = StreamingAnimWriter("mp4", tmp_path, "odd", 5, (h, w))
    for _ in range(3):
        wr.append(frame)
    wr.close()
    cap = cv2.VideoCapture(str(wr.out))
    ok, got = cap.read()
    cap.release()
    assert ok
    assert got.shape[:2] == (h + 1, w + 1)
    assert got[h // 2, w - 1].mean() > 150  # the last source column survived
    assert got[h - 1, w // 2].mean() > 150  # ... and the last source row


# ---------------------------------------------------------------------------
# Frames without data, cancel, zero output (H5 / lows)
# ---------------------------------------------------------------------------


def _result_with_empty_frame(k_empty: int = 1):
    from dataclasses import replace

    result = grid_result(n_frames=3)
    cs = result.correspondence
    xl = cs.xL.copy()
    xl[k_empty] = np.nan  # the left camera lost every node at this frame
    return replace(result, correspondence=replace(cs, xL=xl))


def test_animation_keeps_timing_when_a_frame_has_no_data(tmp_path):
    result = _result_with_empty_frame(1)
    out = export_animation(
        tmp_path,
        "p",
        "20260913000001",
        result,
        {},
        [FieldImageConfig(field_id="U")],
        fmt="mp4",
        fps=5,
        mesh_step=16,
        include_colorbar=True,
        show_deformed=True,
    )
    assert isinstance(out, ExportOutcome)
    assert len(out) == 1 and not out.cancelled
    cap = cv2.VideoCapture(str(out[0]))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    assert n == 3  # the empty frame was written (background only), timing intact
    assert len(out.skipped) == 1 and "L_U" in out.skipped[0]


def test_cancelled_animation_deletes_its_partial_file(tmp_path):
    stop = threading.Event()
    result = grid_result(n_frames=3)
    out = export_animation(
        tmp_path,
        "p",
        "20260913000002",
        result,
        {},
        [FieldImageConfig(field_id="U")],
        fmt="gif",
        mesh_step=16,
        include_colorbar=False,
        stop_event=stop,
        progress_cb=lambda d, t, s: stop.set(),  # cancel after the first frame
    )
    assert out == [] and out.cancelled
    assert out.discarded and not out.discarded[0].exists()
    assert not list(tmp_path.rglob("*.gif"))


def test_stop_after_the_last_frame_is_not_a_cancel(tmp_path):
    stop = threading.Event()
    result = grid_result(n_frames=2)

    def stop_at_end(done, total, label):
        if done == total:
            stop.set()

    out = export_animation(
        tmp_path,
        "p",
        "20260913000003",
        result,
        {},
        [FieldImageConfig(field_id="U")],
        fmt="gif",
        mesh_step=16,
        include_colorbar=False,
        stop_event=stop,
        progress_cb=stop_at_end,
    )
    assert len(out) == 1 and out[0].exists() and not out.cancelled


def test_image_export_reports_an_unavailable_field(tmp_path):
    result = grid_result(n_frames=2, with_strain=False)
    out = export_image_frames(
        tmp_path,
        "p",
        "20260913000004",
        result,
        {},
        [FieldImageConfig(field_id="exx")],
        mesh_step=16,
        include_colorbar=False,
    )
    assert out == [] and not out.cancelled
    assert out.unavailable == ["L_exx"]


def test_image_export_reports_frames_without_data(tmp_path):
    result = _result_with_empty_frame(1)
    out = export_image_frames(
        tmp_path,
        "p",
        "20260913000005",
        result,
        {},
        [FieldImageConfig(field_id="U")],
        mesh_step=16,
        include_colorbar=False,
        show_deformed=True,
    )
    assert len(out) == 2  # frames 1 and 3 written
    assert len(out.skipped) == 1 and "frame_2" in out.skipped[0]


# ---------------------------------------------------------------------------
# Right camera uses the warped left ROI (M3)
# ---------------------------------------------------------------------------


def _half_roi(shape=(200, 200)) -> np.ndarray:
    roi = np.zeros(shape, bool)
    roi[:, :110] = True  # keeps only the left part of the node grid
    return roi


def test_right_camera_export_uses_the_warped_left_roi(tmp_path):
    from al_dic_3d.viz3d.maskwarp import right_camera_mask

    result = grid_result(n_frames=2)
    roi = _half_roi()
    cs = result.correspondence
    warped = right_camera_mask(roi, cs.xL[0], cs.xR[0], roi.shape)
    assert warped is not None and warped.sum() < roi.sum() + 5000

    cfg = FieldImageConfig(field_id="U", opacity=1.0)
    out = export_image_frames(
        tmp_path,
        "p",
        "20260913000006",
        result,
        {},
        [cfg],
        cameras=("R",),
        mesh_step=16,
        roi_mask=roi,
        include_colorbar=False,
        output_max_dim=0,
        frame_start=1,
        frame_end=1,
        show_deformed=False,
    )
    assert len(out) == 1
    from al_dic_3d.pathsafe import imread_unicode

    got = imread_unicode(out[0], cv2.IMREAD_COLOR)
    want, *_ = render_field_frame(
        result, "R", "U", 1, None, cfg, mesh_step=16, roi_mask=warped, show_deformed=False
    )
    hull_only, *_ = render_field_frame(
        result, "R", "U", 1, None, cfg, mesh_step=16, roi_mask=None, show_deformed=False
    )
    np.testing.assert_array_equal(got, want)
    assert (got != hull_only).any()  # the ROI really bounds the right camera now


def test_display_warp_keeps_the_boundary_nodes_visible():
    from al_dic_3d.viz3d.fieldmap import visible_values
    from al_dic_3d.viz3d.maskwarp import right_camera_mask, warp_mask_left_to_right

    h, w = 400, 500
    roi = np.zeros((h, w), np.uint8)
    cv2.circle(roi, (250, 200), 150, 1, -1)
    roi = roi.astype(bool)
    xs, ys = np.meshgrid(np.arange(0, w, 16.0), np.arange(0, h, 16.0))
    nodes = np.column_stack([xs.ravel(), ys.ravel()])
    inside = roi[nodes[:, 1].astype(int), nodes[:, 0].astype(int)]
    xl = nodes[inside]
    xr = xl @ np.array([[0.97, -0.015], [0.02, 1.01]]) + np.array([-30.0, 5.0])

    legacy = warp_mask_left_to_right(roi, xl, xr, (h, w))
    display = right_camera_mask(roi, xl, xr, (h, w))
    vals = np.ones(len(xr))
    n_legacy = int(np.isfinite(visible_values(vals, xr, legacy)).sum())
    n_display = int(np.isfinite(visible_values(vals, xr, display)).sum())
    assert n_display == len(xr)  # every tracked right node sits inside the support
    assert n_legacy < n_display  # the coarse-grid band used to erode the rim
    assert (display | legacy).sum() == display.sum()  # only ever adds rim pixels


# ---------------------------------------------------------------------------
# Backgrounds keep their bit depth + the canvas stretch (M6)
# ---------------------------------------------------------------------------


def test_twelve_bit_frames_in_sixteen_bit_files_are_not_black(tmp_path):
    from al_dic_3d.viz3d.background import load_display_gray

    (p,) = write_gray_frames(tmp_path, "b", 1, (60, 80), dtype=np.uint16, hi=4095)
    img = load_display_gray(p)
    assert img.dtype == np.uint8 and img.shape == (60, 80)
    assert img.min() == 0 and img.max() == 255  # full canvas stretch, not max 15


def test_background_matches_the_canvas_pixel_for_pixel(tmp_path):
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.gui.widgets.image_view import gray_to_qimage, load_gray_image
    from al_dic_3d.viz3d.background import load_display_gray

    QApplication.instance() or QApplication([])
    for dtype, hi in ((np.uint16, 4095), (np.uint8, 180)):
        (p,) = write_gray_frames(tmp_path, f"c{hi}", 1, (37, 53), dtype=dtype, hi=hi)
        qimg = gray_to_qimage(load_gray_image(p))
        ptr = qimg.constBits()
        canvas = np.frombuffer(ptr, np.uint8).reshape(qimg.height(), qimg.bytesPerLine())
        canvas = canvas[:, : qimg.width()]
        np.testing.assert_array_equal(load_display_gray(p), canvas)


def test_image_export_composites_over_the_stretched_background(tmp_path):
    result = grid_result(n_frames=2, image_size=(200, 200))
    files = write_gray_frames(tmp_path, "L", 2, (200, 200), dtype=np.uint16, hi=4095)
    out = export_image_frames(
        tmp_path,
        "p",
        "20260913000007",
        result,
        {"L": files},
        [FieldImageConfig(field_id="U")],
        mesh_step=16,
        include_colorbar=False,
        output_max_dim=0,
        frame_start=0,
        frame_end=0,
    )
    from al_dic_3d.pathsafe import imread_unicode

    img = imread_unicode(out[0], cv2.IMREAD_COLOR)
    corner = img[:20, :20]  # outside the node hull: pure background
    assert corner.max() > 100  # was ~15 (12-bit data squeezed by /256)
