"""Unicode-path robustness of the ``pathsafe`` wrappers (alien-env batch G3).

OpenCV's ``char*``-path APIs fail on Windows paths containing characters
outside the ANSI code page (CJK user names, accented letters, emoji):
``cv2.imread`` returns ``None``, ``cv2.imwrite`` returns ``False`` WITHOUT
writing anything, and ``cv2.FileStorage`` cannot open in either direction
(all verified against opencv-python 5.0.0 on Windows 11). These tests pin

(a) that every ``pathsafe`` wrapper survives such paths on every OS, and
(b) BYTE-IDENTITY of the ``imdecode`` replacement against ``cv2.imread`` on
    ASCII paths — swapping the decoder must not change pipeline inputs.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d.pathsafe import (  # noqa: E402
    filestorage_read,
    filestorage_write,
    imread_unicode,
    imwrite_unicode,
)

# CJK + space + accented latin — the canonical "alien" directory name.
ALIEN = "试样 数据 ünïcode"


@pytest.fixture()
def alien_dir(tmp_path: Path) -> Path:
    d = tmp_path / ALIEN
    d.mkdir()
    return d


def _img16(h: int = 24, w: int = 32) -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.integers(0, 65535, (h, w)).astype(np.uint16)


# ---------------------------------------------------------------------------
# imread / imwrite
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ext", [".png", ".tif"])
@pytest.mark.parametrize("dtype", [np.uint8, np.uint16])
def test_imwrite_imread_roundtrip_unicode(alien_dir: Path, ext: str, dtype) -> None:
    arr = _img16().astype(dtype) if dtype == np.uint16 else (_img16() // 256).astype(np.uint8)
    path = alien_dir / f"帧 001{ext}"
    imwrite_unicode(path, arr)
    assert path.exists() and path.stat().st_size > 0
    back = imread_unicode(path)
    assert back is not None
    assert back.dtype == arr.dtype
    assert np.array_equal(back, arr)


def test_imread_flags_forwarded(alien_dir: Path) -> None:
    color = np.dstack([(_img16() // 256).astype(np.uint8)] * 3)
    path = alien_dir / "color.png"
    imwrite_unicode(path, color)
    gray = imread_unicode(path, cv2.IMREAD_GRAYSCALE)
    assert gray is not None and gray.ndim == 2


def test_imread_missing_or_unreadable_returns_none(alien_dir: Path) -> None:
    assert imread_unicode(alien_dir / "нет такого.png") is None
    assert imread_unicode(alien_dir) is None  # a directory, not a file
    corrupt = alien_dir / "junk.png"
    corrupt.write_bytes(b"this is not a PNG")
    assert imread_unicode(corrupt) is None
    empty = alien_dir / "empty.png"
    empty.write_bytes(b"")
    assert imread_unicode(empty) is None


def test_imwrite_bad_extension_raises(alien_dir: Path) -> None:
    arr = (_img16() // 256).astype(np.uint8)
    with pytest.raises(OSError):
        imwrite_unicode(alien_dir / "image.notanimage", arr)
    with pytest.raises(OSError):
        imwrite_unicode(alien_dir / "no_extension", arr)


def test_imwrite_encode_params_respected(alien_dir: Path) -> None:
    arr = (_img16(64, 64) // 256).astype(np.uint8)
    lo = alien_dir / "lo.jpg"
    hi = alien_dir / "hi.jpg"
    imwrite_unicode(lo, arr, [cv2.IMWRITE_JPEG_QUALITY, 10])
    imwrite_unicode(hi, arr, [cv2.IMWRITE_JPEG_QUALITY, 98])
    assert lo.stat().st_size < hi.stat().st_size  # quality param really applied


@pytest.mark.parametrize("flags", [cv2.IMREAD_UNCHANGED, cv2.IMREAD_GRAYSCALE])
@pytest.mark.parametrize("name", ["gray16.tif", "gray16.png", "gray8.png", "color8.png"])
def test_byte_identity_against_cv2_imread(tmp_path: Path, name: str, flags: int) -> None:
    """The decode-path swap (imread -> fromfile+imdecode) is byte-identical.

    ``load_gray`` feeds the DIC pipeline, so this is the parity anchor: for
    every dtype/layout/flag combination the wrapper must return EXACTLY what
    ``cv2.imread`` returned before the G3 hardening.
    """
    if name == "gray16.tif" or name == "gray16.png":
        arr: np.ndarray = _img16()
    elif name == "gray8.png":
        arr = (_img16() // 256).astype(np.uint8)
    else:
        arr = np.dstack([(_img16() // 256).astype(np.uint8)] * 3)
    path = tmp_path / name  # ASCII path: cv2.imread works and is the oracle
    assert cv2.imwrite(str(path), arr)
    old = cv2.imread(str(path), flags)
    new = imread_unicode(path, flags)
    assert old is not None and new is not None
    assert old.dtype == new.dtype and old.shape == new.shape
    assert np.array_equal(old, new)


# ---------------------------------------------------------------------------
# cv2.FileStorage (memory mode)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("suffix", [".yml", ".yaml", ".xml"])
def test_filestorage_roundtrip_unicode(alien_dir: Path, suffix: str) -> None:
    path = alien_dir / f"标定 결과{suffix}"
    K = np.array([[1200.0, 0, 320.5], [0, 1180.0, 240.25], [0, 0, 1]])
    with filestorage_write(path) as fs:
        fs.write("K", K)
        fs.write("rms", 0.125)
        fs.write("note", "hello wörld")
    assert path.exists() and path.stat().st_size > 0

    fr = filestorage_read(path)
    try:
        assert np.allclose(fr.getNode("K").mat(), K)
        assert fr.getNode("rms").real() == pytest.approx(0.125)
        assert fr.getNode("note").string() == "hello wörld"
    finally:
        fr.release()


def test_filestorage_read_missing_raises(alien_dir: Path) -> None:
    with pytest.raises((OSError, ValueError)):
        filestorage_read(alien_dir / "缺失.yaml")


def test_filestorage_read_garbage_raises(alien_dir: Path) -> None:
    bad = alien_dir / "bad.yaml"
    bad.write_text("not: [valid: yaml", encoding="utf-8")
    with pytest.raises(ValueError):
        filestorage_read(bad)


def test_filestorage_write_failure_leaves_no_file(alien_dir: Path) -> None:
    target = alien_dir / "missing dir" / "out.yaml"  # parent does not exist
    with pytest.raises(OSError):
        with filestorage_write(target) as fs:
            fs.write("x", 1.0)
    assert not target.exists()


def test_filestorage_write_aborts_on_body_exception(alien_dir: Path) -> None:
    target = alien_dir / "aborted.yaml"
    with pytest.raises(RuntimeError):
        with filestorage_write(target) as fs:
            fs.write("x", 1.0)
            raise RuntimeError("caller failed mid-write")
    assert not target.exists()  # a half-written file must never appear
