"""Generate the README banner -> ``assets/banner_3d.png`` (1280x400).

A deliberate sibling of the pyALDIC-2D banner (same 1280x400 strip, same dark
palette, same "chips + arrows + wordmark" grammar) with a distinctly stereo
story: LEFT camera and RIGHT camera speckle views converge on a reconstructed
3D surface.

Run:  python tools/marketing/gen_banner.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from _style import (  # noqa: E402
    ACCENT,
    ACCENT_LIGHT,
    ASSETS,
    BG_DARKEST,
    DEPTH,
    MONO,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from matplotlib import pyplot as plt  # noqa: E402
from scipy.ndimage import gaussian_filter, map_coordinates  # noqa: E402

W_PX, H_PX = 1280, 400
DPI = 80

N = 160  # speckle chip resolution


def _speckle(rng: np.random.Generator, n: int, sigma: float = 1.6) -> np.ndarray:
    s = gaussian_filter(rng.standard_normal((n, n)), sigma=sigma)
    return (s - s.min()) / (s.max() - s.min())


def _stereo_pair(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """One speckle texture seen from two viewpoints (a real disparity warp).

    The right view samples the same texture through a horizontal disparity that
    grows with the surface height — the geometric signature of a stereo pair,
    not two unrelated noise fields.
    """
    tex = _speckle(rng, N * 2)
    yy, xx = np.mgrid[0:N, 0:N].astype(float)
    a, b = (xx - N / 2) / N, (yy - N / 2) / N
    height = np.exp(-(a**2 + b**2) / 0.10)  # a bump on the specimen surface
    left_x, left_y = xx + N / 2, yy + N / 2
    right_x = left_x + 10.0 + 14.0 * height  # disparity ~ depth
    left = map_coordinates(tex, [left_y, left_x], order=1, mode="reflect")
    right = map_coordinates(tex, [left_y, right_x], order=1, mode="reflect")
    return left, right


def _surface(ax) -> None:
    """A 3D wireframe surface coloured by out-of-plane displacement."""
    n = 34
    u = np.linspace(-1, 1, n)
    X, Y = np.meshgrid(u, u)
    Z = 0.55 * np.exp(-(X**2 + Y**2) / 0.35) - 0.18 * X
    ax.plot_surface(
        X,
        Y,
        Z,
        rstride=1,
        cstride=1,
        cmap="turbo",
        linewidth=0.25,
        edgecolors=(1, 1, 1, 0.18),
        antialiased=True,
        shade=False,
    )
    ax.set_axis_off()
    ax.set_box_aspect((1, 1, 0.62))
    ax.view_init(elev=32, azim=-58)
    ax.set_facecolor((0, 0, 0, 0))
    ax.patch.set_alpha(0.0)


def _logo(ax) -> None:
    """A rounded 'AL DIC 3D' tile — the 2D icon's grammar, plus the 3D suffix."""
    from matplotlib.patches import FancyBboxPatch

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(
        FancyBboxPatch(
            (0.06, 0.06),
            0.88,
            0.88,
            boxstyle="round,pad=0,rounding_size=0.22",
            linewidth=1.6,
            edgecolor=ACCENT,
            facecolor="#1b2136",
        )
    )
    ax.text(
        0.5,
        0.68,
        "AL",
        color=TEXT_PRIMARY,
        fontsize=21,
        fontweight="bold",
        ha="center",
        va="center",
        fontfamily=MONO,
    )
    ax.text(
        0.36,
        0.32,
        "DIC",
        color=DEPTH,
        fontsize=17,
        fontweight="bold",
        style="italic",
        ha="center",
        va="center",
        fontfamily=MONO,
    )
    ax.text(
        0.76,
        0.32,
        "3D",
        color=ACCENT_LIGHT,
        fontsize=17,
        fontweight="bold",
        ha="center",
        va="center",
        fontfamily=MONO,
    )


def main() -> int:
    rng = np.random.default_rng(11)
    fig = plt.figure(figsize=(W_PX / DPI, H_PX / DPI), dpi=DPI, facecolor=BG_DARKEST)

    # --- background: radial glow + faint speckle (2D banner recipe) ---
    ax_bg = fig.add_axes([0, 0, 1, 1])
    ax_bg.set_xlim(0, 1)
    ax_bg.set_ylim(0, 1)
    ax_bg.axis("off")
    Y, X = np.mgrid[0:200, 0:400] / 200.0
    R = np.sqrt((X - 0.35) ** 2 + (Y - 0.5) ** 2)
    grad = np.zeros((*R.shape, 4))
    base = np.array([0.043, 0.059, 0.102])
    glow = np.array([0.388, 0.400, 0.945])
    for i in range(3):
        grad[:, :, i] = base[i] + (glow[i] - base[i]) * np.exp(-(R**2) / 0.15) * 0.12
    grad[:, :, 3] = 1.0
    ax_bg.imshow(grad, extent=[0, 1, 0, 1], aspect="auto", interpolation="bicubic")
    ax_bg.imshow(
        _speckle(rng, 200, 2.0),
        extent=[0, 1, 0, 1],
        aspect="auto",
        cmap="gray",
        alpha=0.03,
        interpolation="bicubic",
    )

    # --- chips: LEFT / RIGHT camera views, then the 3D surface ---
    left, right = _stereo_pair(rng)
    cam_w, cam_h = 0.118, 0.295
    x_cam, y_top, y_bot = 0.045, 0.520, 0.125
    ax_l = fig.add_axes([x_cam, y_top, cam_w, cam_h])
    ax_l.imshow(left, cmap="gray", interpolation="bicubic")
    ax_r = fig.add_axes([x_cam, y_bot, cam_w, cam_h])
    ax_r.imshow(right, cmap="gray", interpolation="bicubic")
    for ax, label, col in ((ax_l, "LEFT CAM", ACCENT_LIGHT), (ax_r, "RIGHT CAM", DEPTH)):
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(col)
            sp.set_linewidth(1.6)
        ax.text(
            0.5,
            1.055,
            label,
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            color=col,
            fontsize=10.5,
            fontfamily=MONO,
        )

    ax_s = fig.add_axes([0.275, 0.105, 0.235, 0.755], projection="3d")
    _surface(ax_s)

    # --- foreground overlay: converging rays drawn ON TOP of the 3D axes ---
    ax_fg = fig.add_axes([0, 0, 1, 1], zorder=5)
    ax_fg.set_xlim(0, 1)
    ax_fg.set_ylim(0, 1)
    ax_fg.axis("off")
    ax_fg.patch.set_alpha(0.0)
    apex = (0.333, 0.545)
    for y_src, col in ((y_top + cam_h / 2, ACCENT_LIGHT), (y_bot + cam_h / 2, DEPTH)):
        ax_fg.annotate(
            "",
            xy=apex,
            xytext=(x_cam + cam_w + 0.008, y_src),
            arrowprops=dict(
                arrowstyle="-|>", color=col, lw=2.2, mutation_scale=16, alpha=0.9, shrinkB=7
            ),
        )
    ax_fg.plot(
        [apex[0]],
        [apex[1]],
        marker="o",
        ms=6.5,
        color="white",
        markeredgecolor="#0b0f1a",
        markeredgewidth=1.2,
    )
    ax_fg.text(
        0.245,
        0.575,
        "triangulate",
        ha="center",
        va="bottom",
        color=TEXT_SECONDARY,
        fontsize=10,
        fontfamily=MONO,
        alpha=0.95,
    )
    ax_fg.text(
        0.393,
        0.895,
        "3D SURFACE + STRAIN",
        ha="center",
        va="bottom",
        color=TEXT_SECONDARY,
        fontsize=11,
        fontfamily=MONO,
    )

    # --- wordmark ---
    ax_logo = fig.add_axes([0.545, 0.315, 0.098, 0.315])
    _logo(ax_logo)
    ax_bg.text(
        0.665,
        0.585,
        "pyALDIC-3D",
        color=TEXT_PRIMARY,
        fontsize=44,
        fontweight="bold",
        fontfamily=MONO,
        ha="left",
        va="center",
    )
    ax_bg.text(
        0.667,
        0.375,
        "Stereo Digital Image Correlation\n"
        "3D shape, displacement and surface strain\n"
        "in millimetres — calibration to export",
        color=TEXT_SECONDARY,
        fontsize=14.5,
        fontfamily="sans-serif",
        linespacing=1.45,
        ha="left",
        va="center",
    )
    ax_bg.plot([0.04, 0.96], [0.075, 0.075], color=ACCENT, lw=1.5, alpha=0.4)

    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / "banner_3d.png"
    fig.savefig(out, dpi=DPI, facecolor=BG_DARKEST, pad_inches=0)
    plt.close(fig)
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
