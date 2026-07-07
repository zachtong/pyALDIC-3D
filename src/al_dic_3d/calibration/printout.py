"""Printable calibration-board PDF at exact physical scale (Qt-free).

The board must print at 100% scale — a silently rescaled printout corrupts
every calibration made with it. The PDF page therefore embeds the board image
at its true millimetre size (matplotlib figure sized in inches = mm / 25.4)
and carries a legend with the spec plus a scale-check instruction so the user
can verify the print with calipers before use.

Lazy matplotlib import (available transitively via the al-dic dependency).
"""

from __future__ import annotations

from pathlib import Path

from al_dic_3d.calibration.boards import (
    BoardSpec,
    CharucoSpec,
    ChessboardSpec,
    CircleGridSpec,
    CodedCircleGridSpec,
)

# Usable page area (mm) with a 12 mm printer margin already subtracted.
_PAGES = {"a4": (210.0, 297.0), "letter": (215.9, 279.4)}
_MARGIN_MM = 12.0


def spec_summary(spec: BoardSpec) -> str:
    """One-line human description of a board spec (for legends/logs)."""
    if isinstance(spec, ChessboardSpec):
        return f"chessboard {spec.cols}x{spec.rows} inner corners, square {spec.square_size:g} mm"
    if isinstance(spec, CharucoSpec):
        return (
            f"ChArUco {spec.squares_x}x{spec.squares_y} squares, square "
            f"{spec.square_size:g} mm, marker {spec.marker_size:g} mm, {spec.dictionary}"
        )
    if isinstance(spec, CodedCircleGridSpec):
        return (
            f"coded dot target {spec.cols}x{spec.rows}, pitch {spec.spacing:g} mm, "
            f"dot {spec.dot_mm:g} mm, ring fiducials at {spec.fiducials}"
        )
    if isinstance(spec, CircleGridSpec):
        kind = "asymmetric" if spec.asymmetric else "symmetric"
        return (
            f"{kind} circle grid {spec.cols}x{spec.rows}, pitch {spec.spacing:g} mm, "
            f"dot {spec.dot_mm:g} mm"
        )
    raise TypeError(f"unknown board spec type: {type(spec).__name__}")


def _scale_check(spec: BoardSpec) -> str:
    """A caliper-verifiable distance printed on the page."""
    if isinstance(spec, ChessboardSpec):
        n, pitch, what = spec.cols - 1, spec.square_size, "first to last inner corner, top row"
    elif isinstance(spec, CharucoSpec):
        n, pitch, what = spec.squares_x, spec.square_size, "board width over all squares"
    else:
        n, pitch, what = spec.cols - 1, spec.spacing, "first to last dot center, top row"
    return f"SCALE CHECK: {what} must measure {n * pitch:g} mm (print at 100%, no fit-to-page)"


def save_board_pdf(
    spec: BoardSpec,
    path: str | Path,
    *,
    px_per_mm: float = 12.0,
    page: str = "a4",
) -> Path:
    """Write a 1:1-scale printable PDF of ``spec``; raises if it exceeds the page."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if page not in _PAGES:
        raise ValueError(f"unknown page {page!r}; choose from {sorted(_PAGES)}")
    img = spec.render(px_per_mm)
    h_px, w_px = img.shape
    w_mm, h_mm = w_px / px_per_mm, h_px / px_per_mm
    page_w, page_h = _PAGES[page]
    avail_w, avail_h = page_w - 2 * _MARGIN_MM, page_h - 2 * _MARGIN_MM - 14.0  # legend strip
    if w_mm > avail_w or h_mm > avail_h:
        raise ValueError(
            f"board {w_mm:.0f}x{h_mm:.0f} mm exceeds the printable {page} area "
            f"{avail_w:.0f}x{avail_h:.0f} mm — reduce the board size or use a larger page"
        )

    fig = plt.figure(figsize=(page_w / 25.4, page_h / 25.4))
    # Axes rectangle in figure fractions, board centered horizontally, top-aligned.
    left = (page_w - w_mm) / 2.0 / page_w
    bottom = (page_h - _MARGIN_MM - h_mm) / page_h
    ax = fig.add_axes((left, bottom, w_mm / page_w, h_mm / page_h))
    ax.imshow(img, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
    ax.axis("off")
    fig.text(0.5, _MARGIN_MM / page_h + 0.010, _scale_check(spec), ha="center", fontsize=9)
    fig.text(
        0.5,
        _MARGIN_MM / page_h - 0.008,
        f"pyALDIC-3D calibration board — {spec_summary(spec)}",
        ha="center",
        fontsize=8,
        color="0.35",
    )
    path = Path(path)
    fig.savefig(path, format="pdf")
    plt.close(fig)
    return path
