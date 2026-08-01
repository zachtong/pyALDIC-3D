"""The one picture of what stereo-DIC does -> ``assets/stereo_principle.png``.

Two calibrated cameras, one speckled surface point: the LEFT camera defines the
world frame (R = I, T = 0), correlation finds the same material point in the
RIGHT image, and the two back-projected rays are triangulated into a metric 3D
point. Tracking that point through the sequence gives the displacement;
differentiating a fitted local tangent plane gives the surface strain.

The camera frusta and the epipolar line are drawn from a REAL stereo rig
(``al_dic_3d.calibration``) with the real projection code, so the geometry in
the figure is the geometry the software solves — only the styling is decorative.

Run:  python tools/marketing/fig_stereo_principle.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from _style import (  # noqa: E402
    ACCENT_LIGHT,
    BG_DARKEST,
    DEPTH,
    GOOD,
    MONO,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    optimize_png,
    save,
)
from matplotlib import pyplot as plt  # noqa: E402

from al_dic_3d.calibration import CameraIntrinsics, StereoRig, project_points  # noqa: E402

FX = FY = 1500.0
IMG = 900
BASELINE = 260.0  # mm
CONVERGE_DEG = 16.0


def _rig() -> StereoRig:
    """A converging two-camera rig — the standard stereo-DIC arrangement."""
    intr = dict(fx=FX, fy=FY, cx=IMG / 2, cy=IMG / 2, width=IMG, height=IMG)
    left = CameraIntrinsics(**intr)
    right = CameraIntrinsics(**intr)
    th = np.deg2rad(CONVERGE_DEG)
    R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]])
    T = np.array([-BASELINE, 0.0, 0.0])
    return StereoRig(cameras={"L": left, "R": right}, extrinsics={("L", "R"): (R, T)})


def _frustum(ax, R: np.ndarray, T: np.ndarray, color: str, label: str, depth: float = 190.0):
    """Draw a camera as a pyramid from its optical centre through its image corners."""
    centre = -R.T @ T
    half_x = depth * (IMG / 2) / FX
    half_y = depth * (IMG / 2) / FY
    corners_cam = np.array(
        [
            [-half_x, -half_y, depth],
            [half_x, -half_y, depth],
            [half_x, half_y, depth],
            [-half_x, half_y, depth],
        ]
    )
    corners = (corners_cam @ R) + centre  # row-wise R.T @ x + centre
    for c in corners:
        ax.plot(*zip(centre, c, strict=True), color=color, lw=1.1, alpha=0.85)
    loop = np.vstack([corners, corners[0]])
    ax.plot(loop[:, 0], loop[:, 1], loop[:, 2], color=color, lw=1.4, alpha=0.95)
    ax.scatter(*centre, color=color, s=42, depthshade=False)
    ax.text(
        centre[0],
        centre[1],
        centre[2] - 55,
        label,
        color=color,
        fontsize=11,
        fontfamily=MONO,
        ha="center",
    )
    return centre, corners


def _surface(ax):
    """The specimen surface: a gently curved patch ~800 mm in front of the rig."""
    u = np.linspace(-115, 115, 42)
    X, Y = np.meshgrid(u, u)
    Z = 800.0 - 42.0 * np.exp(-(X**2 + Y**2) / 7000.0) + 0.10 * X
    ax.plot_surface(
        X,
        Y,
        Z,
        rstride=2,
        cstride=2,
        cmap="turbo",
        alpha=0.92,
        linewidth=0,
        antialiased=True,
        shade=False,
        zorder=1,
    )
    return X, Y, Z


def main() -> int:
    rig = _rig()
    R_r, T_r = rig.pose("R")

    fig = plt.figure(figsize=(13.0, 6.2), dpi=110, facecolor=BG_DARKEST)
    ax = fig.add_subplot(1, 2, 1, projection="3d", facecolor=BG_DARKEST)

    _surface(ax)
    cL, _ = _frustum(ax, np.eye(3), np.zeros(3), ACCENT_LIGHT, "LEFT  (world origin)")
    cR, _ = _frustum(ax, R_r, T_r, DEPTH, "RIGHT")

    # The material point both cameras see, and its two back-projected rays.
    P = np.array([-18.0, 26.0, 800.0 - 42.0 * np.exp(-(18.0**2 + 26.0**2) / 7000.0) - 1.8])
    for c, col in ((cL, ACCENT_LIGHT), (cR, DEPTH)):
        ax.plot(*zip(c, P, strict=True), color=col, lw=2.0, ls="-", alpha=0.95, zorder=5)
    ax.scatter(*P, color="white", s=70, depthshade=False, zorder=6, edgecolors=GOOD, linewidths=2)
    ax.text(
        P[0] + 30,
        P[1] + 10,
        P[2] - 40,
        "X  (mm, world)",
        color=TEXT_PRIMARY,
        fontsize=11,
        fontfamily=MONO,
    )

    ax.set_axis_off()
    ax.set_box_aspect((1.35, 1.0, 1.0))
    ax.view_init(elev=17, azim=-72)
    ax.set_title(
        "1 · calibrated rig  ->  triangulate every node",
        color=TEXT_SECONDARY,
        fontsize=12.5,
        fontfamily=MONO,
        pad=-4,
    )

    # ---- right half: what each camera actually measures ----
    xs = np.linspace(-110, 110, 15)
    grid = np.stack(
        [
            np.repeat(xs, 15),
            np.tile(xs, 15),
            800.0
            - 42.0 * np.exp(-(np.repeat(xs, 15) ** 2 + np.tile(xs, 15) ** 2) / 7000.0)
            + 0.10 * np.repeat(xs, 15),
        ],
        axis=1,
    )
    pL = project_points(grid, rig.cameras["L"], np.eye(3), np.zeros(3))
    pR = project_points(grid, rig.cameras["R"], R_r, T_r)
    disparity = pL[:, 0] - pR[:, 0]

    for i, (pts, col, name, extra) in enumerate(
        (
            (pL, ACCENT_LIGHT, "LEFT image", "subset grid on the ROI"),
            (pR, DEPTH, "RIGHT image", "found by correlation"),
        ),
    ):
        axi = fig.add_subplot(2, 2, 2 * (i + 1), facecolor="#0f1424")
        sc = axi.scatter(pts[:, 0], pts[:, 1], c=disparity, cmap="turbo", s=17)
        axi.set_xlim(0, IMG)
        axi.set_ylim(IMG, 0)
        axi.set_xticks([])
        axi.set_yticks([])
        for sp in axi.spines.values():
            sp.set_color(col)
            sp.set_linewidth(1.5)
        axi.set_title(f"{name} — {extra}", color=col, fontsize=11, fontfamily=MONO, pad=5)
        if i == 1:
            cb = fig.colorbar(sc, ax=axi, fraction=0.045, pad=0.02)
            cb.set_label(
                "disparity xL − xR  (px)", color=TEXT_SECONDARY, fontsize=9.5, fontfamily=MONO
            )
            cb.ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
            cb.outline.set_edgecolor(TEXT_SECONDARY)

    fig.text(
        0.755,
        0.505,
        "2 · match on RAW images — distortion is removed on point\n"
        "     coordinates only, immediately before triangulation,\n"
        "     so the speckle pattern is never resampled.",
        color=TEXT_SECONDARY,
        fontsize=10.5,
        fontfamily=MONO,
        ha="center",
        va="center",
        linespacing=1.6,
    )
    fig.subplots_adjust(left=0.0, right=0.96, top=0.94, bottom=0.03, wspace=0.02, hspace=0.42)
    fig.text(
        0.02,
        0.965,
        "How pyALDIC-3D measures",
        color=TEXT_PRIMARY,
        fontsize=15,
        fontweight="bold",
        fontfamily=MONO,
    )
    optimize_png(save(fig, "stereo_principle.png", dpi=110), max_width=1500)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
