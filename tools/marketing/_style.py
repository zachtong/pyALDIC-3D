"""Shared look-and-feel + save helpers for the README marketing figures.

The palette is deliberately the pyALDIC-2D banner palette (``scripts/gen_banner.py``
in the sibling 2D repo) so the two projects read as one product family, with one
addition: a teal "depth" accent that only the 3D project uses.

Every generator under ``tools/marketing/`` must run **headless** (Agg for
matplotlib, ``off_screen=True`` for pyvista) and must write into ``assets/``.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "assets"

# --- palette (shared with the 2D banner) ---
BG_DARKEST = "#0b0f1a"
BG_PANEL = "#141929"
ACCENT = "#6366f1"  # indigo — the family accent
ACCENT_LIGHT = "#818cf8"
DEPTH = "#22d3ee"  # cyan — the 3D-only accent (depth / right camera)
DEPTH_DARK = "#0e7490"
WARN = "#f59e0b"
GOOD = "#22c55e"
BAD = "#ef4444"
TEXT_PRIMARY = "#e2e8f0"
TEXT_SECONDARY = "#94a3b8"

MONO = "monospace"


def dark_axes(ax, title: str = "", *, color: str = ACCENT, fontsize: int = 12) -> None:
    """Frame an image axis in the banner style (accent spines, no ticks)."""
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(color)
        spine.set_linewidth(1.5)
    if title:
        ax.set_title(title, color=TEXT_SECONDARY, fontsize=fontsize, pad=6, fontfamily=MONO)


def save(fig, name: str, *, dpi: int = 110, facecolor: str = BG_DARKEST) -> Path:
    """Save ``fig`` to ``assets/<name>`` and report the resulting size."""
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / name
    fig.savefig(out, dpi=dpi, facecolor=facecolor, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"  wrote {out.relative_to(REPO)}  ({out.stat().st_size / 1024:.0f} KB)")
    return out


def optimize_png(path: Path, max_width: int | None = None) -> None:
    """Down-scale (optional) and re-encode a PNG with palette quantization when safe.

    Marketing figures live in a README; a 1.5 MB screenshot is a bad first
    impression on a slow connection. Quantization is only applied when it keeps
    the file smaller AND the image is flat-colour enough for 256 colours.
    """
    from PIL import Image

    img = Image.open(path).convert("RGB")
    if max_width and img.width > max_width:
        h = round(img.height * max_width / img.width)
        img = img.resize((max_width, h), Image.LANCZOS)
    before = path.stat().st_size
    img.save(path, optimize=True)
    quant = img.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
    tmp = path.with_suffix(".quant.png")
    quant.save(tmp, optimize=True)
    if tmp.stat().st_size < path.stat().st_size:
        tmp.replace(path)
    else:
        tmp.unlink()
    print(f"  optimized {path.name}: {before / 1024:.0f} KB -> {path.stat().st_size / 1024:.0f} KB")
