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
