"""Shared matplotlib style for all pyALDIC-3D SoftwareX paper figures.

Mirrors ``paper_softwareX/repro/paper_style.py`` of the 2D paper: Arial
everywhere, large legible fonts, 300 dpi. Call ``apply()`` at the top of every
figure script before plotting.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager


def apply(base: float = 17.0) -> str:
    """Apply Arial + large-font rcParams. Returns the resolved family name."""
    family = "DejaVu Sans"
    # Register Arial from the Windows font directory if available.
    for cand in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\Arial.ttf"):
        if Path(cand).exists():
            try:
                font_manager.fontManager.addfont(cand)
                family = font_manager.FontProperties(fname=cand).get_name()
            except Exception:
                pass
            break

    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [family, "Arial", "DejaVu Sans"],
        "font.size": base,
        "axes.titlesize": base + 3,
        "axes.titleweight": "bold",
        "axes.labelsize": base,
        "xtick.labelsize": base - 2,
        "ytick.labelsize": base - 2,
        "legend.fontsize": base - 2,
        "figure.titlesize": base + 5,
        "figure.titleweight": "bold",
        "axes.linewidth": 1.2,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })
    return family
