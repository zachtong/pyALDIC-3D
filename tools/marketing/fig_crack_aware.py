"""Crack-aware stereo DIC, side by side -> ``assets/crack_aware.png``.

Both panels are produced by the SHIPPING renderer
(:class:`al_dic_3d.viz3d.fieldmap.FieldmapRenderer`, the same object that paints
the canvas, the strain window and every exported frame) from the SAME nodal
field. The only difference is the ``barrier_mask`` argument:

* left  — barrier not supplied: the interpolation triangulates straight across
  the crack and smears the two lips into one continuous field;
* right — the drawn ROI mask doubles as the crack barrier: mesh cells that
  bridge it are dropped, so the discontinuity survives to the screen.

The nodal displacements are the analytic Mode-I-like opening of two rigid lips
(each side translates away from the crack), so any smoothing across the barrier
is unambiguously an artefact rather than physics.

Run:  python tools/marketing/fig_crack_aware.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from _style import (  # noqa: E402
    BAD,
    BG_DARKEST,
    GOOD,
    MONO,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    optimize_png,
    save,
)
from matplotlib import pyplot as plt  # noqa: E402

from al_dic_3d.viz3d.fieldmap import FieldmapRenderer  # noqa: E402

H = W = 420
STEP = 12
CRACK_X = W // 2
CRACK_HALF_WIDTH = 3  # px — the "thin barrier" the mesh is cut at
CRACK_TIP_Y = int(0.33 * H)  # the crack runs from the bottom edge up to here
ZOOM = 105  # half-width of the crop shown in the two field panels


def _roi_masks() -> tuple[np.ndarray, np.ndarray]:
    """Two ROIs: the plain one a user draws, and the one with the crack cut out."""
    plain = np.ones((H, W), dtype=np.float64)
    plain[:40] = plain[-40:] = 0.0
    plain[:, :40] = plain[:, -40:] = 0.0
    with_barrier = plain.copy()
    with_barrier[CRACK_TIP_Y:, CRACK_X - CRACK_HALF_WIDTH : CRACK_X + CRACK_HALF_WIDTH + 1] = 0.0
    return plain, with_barrier


def _nodes_and_field(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Mesh nodes inside the ROI + an opening displacement with a real jump."""
    ys = np.arange(44, H - 44, STEP)
    xs = np.arange(44, W - 44, STEP)
    X, Y = np.meshgrid(xs, ys)
    nodes = np.column_stack([X.ravel().astype(float), Y.ravel().astype(float)])
    keep = mask[nodes[:, 1].astype(int), nodes[:, 0].astype(int)] > 0.5
    nodes = nodes[keep]

    # Opening: below the tip the two lips separate; above it the field is continuous.
    side = np.sign(nodes[:, 0] - CRACK_X)
    below = nodes[:, 1] > CRACK_TIP_Y
    taper = np.clip((nodes[:, 1] - CRACK_TIP_Y) / (H - 44 - CRACK_TIP_Y), 0, 1) ** 0.5
    u = np.where(below, side * 0.42 * taper, 0.0)
    u += 0.10 * (nodes[:, 1] - H / 2) / H  # a mild global gradient on both lips
    return nodes, u


def _render(renderer: FieldmapRenderer, nodes, values, mask, barrier, tag: str):
    rgba, xg, yg, _ = renderer.render_field_rgba(
        0,
        tag,
        nodes,
        values,
        (H, W),
        STEP,
        cmap="turbo",
        vmin=float(np.nanmin(values)),
        vmax=float(np.nanmax(values)),
        roi_mask=mask > 0.5,
        barrier_mask=barrier,
    )
    return rgba, xg, yg


def main() -> int:
    plain, barrier = _roi_masks()
    nodes, values = _nodes_and_field(barrier)
    renderer = FieldmapRenderer()

    # Same nodes, same values. Left: the ROI a user draws without declaring the
    # crack. Right: the ROI with the crack cut, doubling as the barrier mask.
    naive = _render(renderer, nodes, values, plain, None, "naive:U")
    aware = _render(renderer, nodes, values, barrier, barrier, "crack:U")

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 5.2), dpi=110, facecolor=BG_DARKEST)

    for ax, (rgba, xg, yg), title, col in (
        (axes[0], naive, "crack NOT declared — smeared across", BAD),
        (axes[1], aware, "crack-aware — mesh cut at the barrier", GOOD),
    ):
        ax.set_facecolor("#0f1424")
        ax.imshow(rgba, extent=[xg.min(), xg.max(), yg.max(), yg.min()], interpolation="nearest")
        ax.plot(
            [CRACK_X, CRACK_X],
            [CRACK_TIP_Y, H - 44],
            color="white",
            lw=1.0,
            ls=(0, (4, 3)),
            alpha=0.55,
        )
        ax.annotate(
            "crack tip",
            xy=(CRACK_X, CRACK_TIP_Y),
            xytext=(CRACK_X + 0.5 * ZOOM, CRACK_TIP_Y - 28),
            color="white",
            fontsize=9.5,
            fontfamily=MONO,
            arrowprops=dict(arrowstyle="->", color="white", lw=1.1),
        )
        ax.set_xlim(CRACK_X - ZOOM, CRACK_X + ZOOM)
        ax.set_ylim(H - 44, 44)
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(col)
            sp.set_linewidth(1.8)
        ax.set_title(title, color=col, fontsize=11.5, fontfamily=MONO, pad=8)

    fig.text(
        0.5,
        0.955,
        "Crack-aware stereo DIC — the discontinuity survives",
        color=TEXT_PRIMARY,
        fontsize=14,
        fontweight="bold",
        ha="center",
        fontfamily=MONO,
    )
    fig.text(
        0.5,
        0.045,
        "Same nodes, same values, same shipping renderer — only the barrier declaration differs.\n"
        "That barrier also cuts the mesh so the AL-DIC global step never bridges the crack, and\n"
        "excludes strain neighbours whose line of sight would cross it.",
        color=TEXT_SECONDARY,
        fontsize=9.5,
        ha="center",
        fontfamily=MONO,
        linespacing=1.7,
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.885, bottom=0.185, wspace=0.06)
    optimize_png(save(fig, "crack_aware.png", dpi=110), max_width=1500)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
