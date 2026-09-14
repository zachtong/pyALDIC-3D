"""Image-folder listing helpers for the left sidebar (Qt-free, no user strings).

Extracted from :mod:`al_dic_3d.gui.panels.left_sidebar` to keep that file under
the 800-line cap. Pure path/sort utilities with no ``tr()`` strings, so no Qt
translation context is involved.
"""

from __future__ import annotations

import re
from pathlib import Path

IMAGE_EXTS = {".png", ".tif", ".tiff", ".jpg", ".jpeg", ".bmp"}


def natural_key(name: str) -> list:
    """Split ``name`` into int / lowercased-text runs so ``img2`` sorts before ``img10``."""
    return [int(t) if t.isdigit() else t.lower() for t in re.findall(r"\d+|\D+", name)]


def list_images(folder: str, natural: bool) -> list[str]:
    """Sorted image paths in ``folder`` (natural or plain alphabetical)."""
    paths = [p for p in Path(folder).iterdir() if p.suffix.lower() in IMAGE_EXTS]
    key = (lambda p: natural_key(p.name)) if natural else (lambda p: p.name)
    return [str(p) for p in sorted(paths, key=key)]


# ---- both cameras in one folder (fix batch V, finding H10) ----------------------

# (name, left pattern, right pattern) on the lowercased file STEM. A folder is
# split by the first family that assigns EVERY image to exactly one camera.
_STEREO_FAMILIES = (
    ("L_ / R_ prefix", r"^l(?=[_\-\s.]|\d)", r"^r(?=[_\-\s.]|\d)"),
    ("left / right", r"(?:^|[_\-\s.])left(?=$|[_\-\s.\d])", r"(?:^|[_\-\s.])right(?=$|[_\-\s.\d])"),
    (
        "cam0 / cam1",
        r"(?:^|[_\-\s.])cam(?:era)?[_\-\s]?0(?!\d)",
        r"(?:^|[_\-\s.])cam(?:era)?[_\-\s]?1(?!\d)",
    ),
    (
        "cam1 / cam2",
        r"(?:^|[_\-\s.])cam(?:era)?[_\-\s]?1(?!\d)",
        r"(?:^|[_\-\s.])cam(?:era)?[_\-\s]?2(?!\d)",
    ),
    ("_0 / _1 suffix", r"[_\-]0$", r"[_\-]1$"),
    ("_L / _R suffix", r"[_\-]l$", r"[_\-]r$"),
)


def split_stereo_names(paths: list[str]) -> tuple[list[str], list[str], str] | None:
    """``(left, right, pattern)`` when one folder holds both cameras, else ``None``.

    Recognises the common layouts: ``L_0001`` / ``R_0001``, ``left`` /
    ``right``, ``cam0`` / ``cam1`` (or ``cam1`` / ``cam2``), the DICe
    ``0000_0`` / ``0000_1`` suffix and ``_L`` / ``_R``. Order is preserved.
    """
    stems = [Path(p).stem.lower() for p in paths]
    for name, left_pat, right_pat in _STEREO_FAMILIES:
        lre, rre = re.compile(left_pat), re.compile(right_pat)
        left: list[str] = []
        right: list[str] = []
        for path, stem in zip(paths, stems, strict=True):
            is_l, is_r = bool(lre.search(stem)), bool(rre.search(stem))
            if is_l == is_r:  # neither, or ambiguous: this family does not fit
                break
            (left if is_l else right).append(path)
        else:
            if left and right:
                return left, right, name
    return None
