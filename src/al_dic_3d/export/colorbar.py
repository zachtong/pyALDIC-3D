"""Styled colorbar rendering for exported images and animations (Qt-free).

Ported from the 2D platform's ``al_dic.export.colorbar`` (consulted read-only).
The default :class:`ColorbarStyle` reproduces the historical look (a vertical
bar on the right, black background, white text); position, font size, bar
thickness and background are configurable.

3D adaptation: displacement labels carry the METRIC unit ``(mm)`` — 3D
displacements come straight from the calibrated triangulation, so there is no
pixel-size machinery — and strain labels are dimensionless.

matplotlib renders with the Agg backend only inside the bar renderer, so this
module stays importable in headless / worker-thread contexts.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

# Field id -> colorbar base label (math notation, not translated prose).
_COLORBAR_FIELD_LABELS: dict[str, str] = {
    "U": "U",
    "V": "V",
    "W": "W",
    "mag": "|D|",
    "exx": "εxx",
    "eyy": "εyy",
    "exy": "εxy",
    "e1": "ε₁",
    "e2": "ε₂",
    "max_shear": "γ max",
    "von_mises": "von Mises",
}

_DISPLACEMENT_FIELDS = {"U", "V", "W", "mag"}


def colorbar_label(field_id: str, unit: str = "mm") -> str:
    """Build a colorbar label with the appropriate unit suffix.

    Displacement fields (``U``/``V``/``W``/``mag``) are metric world-frame
    quantities from the calibrated reconstruction -> ``(mm)``. Strain fields
    are dimensionless — no unit suffix.
    """
    base = _COLORBAR_FIELD_LABELS.get(field_id, field_id)
    if field_id in _DISPLACEMENT_FIELDS:
        return f"{base} ({unit})"
    return base


@dataclass(frozen=True)
class ColorbarStyle:
    """Appearance of the colorbar appended to exported frames.

    Attributes
    ----------
    position : {"right", "left", "top", "bottom"}
        Where the bar is placed relative to the image.
    font_size : float
        Axis-label font size in points; tick labels are ~85% of this.
    width_ratio : float
        Bar thickness as a fraction of the perpendicular image edge, so the
        bar scales with the image instead of being a fixed number of inches.
    background : {"black", "white"}
        Strip background colour (text/ticks use the contrasting colour).
    """

    position: str = "right"
    font_size: float = 9.0
    width_ratio: float = 0.05
    background: str = "black"
    font_family: str = "sans-serif"

    POSITIONS = ("right", "left", "top", "bottom")
    BACKGROUNDS = ("black", "white")
    # Generic matplotlib families -> always resolvable, never a missing font.
    FONT_FAMILIES = ("sans-serif", "serif", "monospace")


def _render_bar(
    length_px: int,
    thickness_px: int,
    orientation: str,
    cmap_name: str,
    vmin: float,
    vmax: float,
    label: str,
    font_size: float,
    background: str,
    dpi: int,
    font_family: str = "sans-serif",
) -> NDArray:
    """Render a colorbar as a BGR uint8 image via matplotlib (Agg).

    ``orientation`` is ``"vertical"`` (output ``(length, thickness, 3)``) or
    ``"horizontal"`` (output ``(thickness, length, 3)``).
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize

    fg = "white" if background == "black" else "black"
    face = "black" if background == "black" else "white"
    if orientation == "vertical":
        fig_w, fig_h = thickness_px / dpi, length_px / dpi
        adjust = dict(left=0.06, right=0.42, top=0.97, bottom=0.03)
    else:
        fig_w, fig_h = length_px / dpi, thickness_px / dpi
        adjust = dict(left=0.03, right=0.97, top=0.60, bottom=0.40)

    fig, ax = plt.subplots(figsize=(max(0.3, fig_w), max(0.3, fig_h)), dpi=dpi)
    fig.patch.set_facecolor(face)
    try:
        cmap = plt.get_cmap(cmap_name)
    except ValueError:
        cmap = plt.get_cmap("turbo")
    sm = plt.cm.ScalarMappable(norm=Normalize(vmin=vmin, vmax=vmax), cmap=cmap)
    sm.set_array([])
    cb = fig.colorbar(sm, cax=ax, orientation=orientation)
    fam = font_family if font_family in ColorbarStyle.FONT_FAMILIES else "sans-serif"
    cb.set_label(label, fontsize=font_size, color=fg, fontfamily=fam)
    cb.ax.tick_params(colors=fg, labelsize=font_size * 0.85)
    ticklabels = cb.ax.get_yticklabels() if orientation == "vertical" else cb.ax.get_xticklabels()
    for t in ticklabels:
        t.set_fontfamily(fam)
    cb.outline.set_edgecolor(fg)
    cb.outline.set_linewidth(0.5)
    fig.subplots_adjust(**adjust)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=face)
    plt.close(fig)
    buf.seek(0)
    bgr = cv2.imdecode(np.frombuffer(buf.read(), np.uint8), cv2.IMREAD_COLOR)
    # cv2.resize takes (W, H)
    target = (thickness_px, length_px) if orientation == "vertical" else (length_px, thickness_px)
    if bgr is None:
        return np.zeros((target[1], target[0], 3), np.uint8)
    return cv2.resize(bgr, target)


def render_colorbar_strip(
    height: int,
    cmap_name: str,
    vmin: float,
    vmax: float,
    label: str,
    dpi: int = 150,
    font_size: float = 9.0,
    background: str = "black",
    thickness_px: int | None = None,
    font_family: str = "sans-serif",
) -> NDArray:
    """Vertical colorbar strip of the given pixel *height*.

    Plain entry point for callers/tests that want a bare vertical bar.
    ``thickness_px`` defaults to the historical ~1.2 inch width.
    """
    if thickness_px is None:
        thickness_px = int(round(1.2 * dpi))
    return _render_bar(
        height,
        thickness_px,
        "vertical",
        cmap_name,
        vmin,
        vmax,
        label,
        font_size,
        background,
        dpi,
        font_family,
    )


def add_margin(image: NDArray, ratio: float, color: str = "white") -> NDArray:
    """Pad *image* with a uniform border of ``ratio`` * long-edge pixels.

    Used to expand the exported canvas outward (whitespace around the content
    + colorbar) for publication layouts. ``ratio <= 0`` returns the image
    unchanged. ``color`` is ``"white"`` or ``"black"``.
    """
    if ratio <= 0:
        return image
    m = int(round(max(image.shape[:2]) * ratio))
    if m <= 0:
        return image
    value = (255, 255, 255) if color == "white" else (0, 0, 0)
    return cv2.copyMakeBorder(image, m, m, m, m, cv2.BORDER_CONSTANT, value=value)


def attach_colorbar(
    image: NDArray,
    style: ColorbarStyle,
    cmap_name: str,
    vmin: float,
    vmax: float,
    label: str,
    dpi: int = 150,
) -> NDArray:
    """Render a colorbar per *style* and composite it onto *image* (BGR).

    Returns a new image with the colorbar appended on the styled side. On any
    rendering failure the original image is returned unchanged.
    """
    H, W = image.shape[:2]
    pos = style.position if style.position in ColorbarStyle.POSITIONS else "right"
    bg = style.background if style.background in ColorbarStyle.BACKGROUNDS else "black"
    try:
        if pos in ("right", "left"):
            bar = max(10, int(round(W * style.width_ratio)))
            thickness = bar + int(round(style.font_size * 6.0))
            cb = _render_bar(
                H,
                thickness,
                "vertical",
                cmap_name,
                vmin,
                vmax,
                label,
                style.font_size,
                bg,
                dpi,
                style.font_family,
            )
            if cb.shape[0] != H:
                cb = cv2.resize(cb, (cb.shape[1], H))
            return np.hstack([cb, image] if pos == "left" else [image, cb])
        bar = max(10, int(round(H * style.width_ratio)))
        thickness = bar + int(round(style.font_size * 4.5))
        cb = _render_bar(
            W,
            thickness,
            "horizontal",
            cmap_name,
            vmin,
            vmax,
            label,
            style.font_size,
            bg,
            dpi,
            style.font_family,
        )
        if cb.shape[1] != W:
            cb = cv2.resize(cb, (W, cb.shape[0]))
        return np.vstack([cb, image] if pos == "top" else [image, cb])
    except Exception:
        return image
