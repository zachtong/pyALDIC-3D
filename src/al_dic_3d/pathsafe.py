"""Unicode-safe wrappers for OpenCV's path-based file I/O (Qt-free).

OpenCV's C++ file APIs receive ``char*`` narrow paths; on Windows those are
decoded with the ANSI code page, so any path containing characters outside it
— Chinese/Japanese/Korean user names, accented letters, non-ASCII OneDrive
folders — makes ``cv2.imread`` return ``None``, ``cv2.imwrite`` return
``False`` WITHOUT writing anything (the batch-Z silent-failure bug class),
and ``cv2.FileStorage`` fail to open in both directions. All verified against
opencv-python 5.0.0 on Windows 11 (alien-env batch G3).

Every filesystem touch here therefore goes through Python's own
(unicode-clean) I/O plus OpenCV's in-memory codecs:

- images:   ``np.fromfile`` + ``cv2.imdecode`` / ``cv2.imencode`` +
  ``Path.write_bytes`` — byte-identical to ``cv2.imread``/``cv2.imwrite``
  (pinned by tests/test_pathsafe.py, so the pipeline input path is unchanged);
- YAML/XML: ``cv2.FileStorage`` in ``FILE_STORAGE_MEMORY`` mode bridged by
  Python text I/O.

``cv2.VideoWriter`` needs no wrapper: its FFMPEG backend converts UTF-8 paths
itself on Windows (verified; regression-pinned by
tests/test_alien_paths.py::test_animation_writer_under_alien_path).

Related: the canvas-mask PNG codec (``encode_mask_png``/``decode_mask_png``)
lives in :mod:`al_dic_3d.project.draft` — it is a byte-level codec, callers
pair it with ``Path.read_bytes``/``write_bytes`` and stay unicode-safe.

cv2 is imported lazily so importing this module stays free for code paths
that never touch OpenCV.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from numpy.typing import NDArray


def imread_unicode(path: str | Path, flags: int | None = None) -> NDArray[Any] | None:
    """Drop-in ``cv2.imread`` that survives non-ASCII paths on Windows.

    Mirrors ``cv2.imread`` semantics exactly: returns ``None`` when the file
    is missing, unreadable, empty, or not a decodable image. ``flags``
    defaults to ``cv2.IMREAD_UNCHANGED`` (the codebase-wide convention:
    scientific DIC images are often 16-bit).
    """
    import cv2

    if flags is None:
        flags = cv2.IMREAD_UNCHANGED
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
    except OSError:  # missing file, directory, permission, ... -> imread contract
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, flags)


def imwrite_unicode(path: str | Path, image: NDArray[Any], params: list[int] | None = None) -> None:
    """Unicode-safe ``cv2.imwrite`` that RAISES instead of failing silently.

    ``cv2.imwrite`` returns ``False`` without writing anything on a non-ANSI
    Windows path — the exact silent-failure class batch Z found. Encoding in
    memory and writing with ``Path.write_bytes`` removes the path problem;
    raising ``OSError`` on encode/write failure removes the silence (GUI
    callers run inside workers that surface exceptions to the user).
    """
    import cv2

    path = Path(path)
    ext = path.suffix
    if not ext:
        raise OSError(f"cannot infer image format: no file extension on {path}")
    try:
        ok, buf = cv2.imencode(ext, image, params if params is not None else [])
    except cv2.error as exc:
        raise OSError(f"cannot encode image as {ext!r}: {path} ({exc})") from exc
    if not ok:
        raise OSError(f"cannot encode image as {ext!r}: {path}")
    path.write_bytes(buf.tobytes())


def filestorage_read(path: str | Path) -> Any:
    """Open a ``cv2.FileStorage`` for reading via Python file I/O.

    ``cv2.FileStorage(path, FILE_STORAGE_READ)`` cannot open non-ANSI Windows
    paths, so the file CONTENT is read with Python and parsed in
    ``FILE_STORAGE_MEMORY`` mode (format auto-detected from the content).

    Returns an OPENED ``cv2.FileStorage``; the caller must ``release()`` it.

    Raises:
        OSError: the file cannot be read.
        ValueError: the content is not parseable OpenCV YAML/XML/JSON.
    """
    import cv2

    # Calibration files are ASCII/UTF-8 in practice; ``replace`` keeps a stray
    # legacy-encoded comment from failing the whole (numeric) parse.
    content = Path(path).read_text(encoding="utf-8", errors="replace")
    try:
        fs = cv2.FileStorage(content, cv2.FILE_STORAGE_READ | cv2.FILE_STORAGE_MEMORY)
    except Exception as exc:  # cv2.error, sometimes wrapped in SystemError
        raise ValueError(f"cannot parse OpenCV FileStorage content: {path}") from exc
    if not fs.isOpened():
        raise ValueError(f"cannot parse OpenCV FileStorage content: {path}")
    return fs


@contextmanager
def filestorage_write(path: str | Path) -> Iterator[Any]:
    """Context manager yielding a WRITE ``cv2.FileStorage`` that lands at ``path``.

    The storage is memory-backed (format chosen from the path suffix:
    ``.yml``/``.yaml`` -> YAML, ``.xml`` -> XML, ``.json`` -> JSON; default
    YAML); on clean exit the serialized text is written with Python I/O, so
    non-ASCII destinations work. If the body raises, NOTHING is written — a
    half-written calibration file must never appear.

    Raises:
        OSError: the serialized text cannot be written to ``path``.
    """
    import cv2

    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in (".yml", ".yaml", ".xml", ".json"):
        suffix = ".yml"
    fs = cv2.FileStorage(f"mem{suffix}", cv2.FILE_STORAGE_WRITE | cv2.FILE_STORAGE_MEMORY)
    try:
        yield fs
        content = fs.releaseAndGetString()
    except BaseException:
        fs.release()
        raise
    path.write_text(content, encoding="utf-8")
