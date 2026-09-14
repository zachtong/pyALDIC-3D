"""Cheap, cached facts about project input files (Qt-free) — fix batch V, M8.

The GUI's readiness used to check only that inputs were SET: a calibration file
that fails to load, a folder of images that are all the same file for both
cameras, frames of different sizes, or an ROI mask drawn for other images all
showed "Ready to run" and failed later. These helpers let the readiness check
validity without slowing the interface: an image's size is read from its
header, a calibration is parsed once, and both are cached by path, size and
modification time, so a changed file is re-checked automatically.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


def _stamp(path: Path) -> tuple[str, int, int] | None:
    try:
        st = path.stat()
    except OSError:
        return None
    return (str(path), int(st.st_size), int(st.st_mtime_ns))


@lru_cache(maxsize=512)
def _image_size_cached(stamp: tuple[str, int, int]) -> tuple[int, int] | None:
    path = stamp[0]
    try:
        from PIL import Image

        with Image.open(path) as im:  # reads the header only
            return (int(im.size[0]), int(im.size[1]))
    except Exception:  # noqa: BLE001 - fall back to a full decode below
        pass
    try:
        from al_dic_3d.sequence.lazy import decode_gray

        img = decode_gray(path)
        return (int(img.shape[1]), int(img.shape[0]))
    except Exception:  # noqa: BLE001 - unreadable -> unknown size
        return None


def image_size(path: str | Path) -> tuple[int, int] | None:
    """``(width, height)`` of an image file, or ``None`` if it cannot be read."""
    stamp = _stamp(Path(path))
    return None if stamp is None else _image_size_cached(stamp)


@lru_cache(maxsize=32)
def _calibration_problem_cached(stamp: tuple[str, int, int], fmt: str) -> str | None:
    from al_dic_3d.calibration import load_calibration

    try:
        rig = load_calibration(stamp[0], fmt)
    except Exception as exc:  # noqa: BLE001 - any import failure is the answer
        text = str(exc).strip().splitlines()
        return (text[0] if text else type(exc).__name__)[:200]
    if len(getattr(rig, "cameras", {}) or {}) < 2:
        return "it does not describe two cameras"
    return None


def calibration_problem(path: str | Path, fmt: str) -> str | None:
    """Why the calibration file cannot be used (English), or ``None`` if it loads."""
    p = Path(path)
    stamp = _stamp(p)
    if stamp is None:
        return "the file does not exist"
    return _calibration_problem_cached(stamp, str(fmt))
