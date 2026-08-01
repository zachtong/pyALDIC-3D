"""The honesty gate catching a silent solver failure -> ``assets/honesty_gate.png``.

A DIC solver can converge on garbage. pyALDIC-3D therefore re-derives, for every
node of every frame, the ZNSSD between the frame-0 subset at ``X`` and frame k at
``X + U^k`` — an INDEPENDENT check of the shipped quantity, not a reading of the
solver's own convergence flag — and NaNs out whatever fails it.

This figure runs the real gate (``al_dic_3d.matching.temporal._gate_by_znssd``,
via ``primitives._znssd``) on a constructed failure that is easy to verify by
eye: a speckle frame is translated by a known amount, and inside one disc the
pattern is REPLACED by fresh, uncorrelated speckle (the decorrelation shape that
paint loss, glare or a growing crack produces). The "solver output" fed to the
gate is the honest translation everywhere plus a frozen (zero-update) field
inside the disc — exactly the accumulative sibling-warm-start freeze the gate was
built for. Nothing about which nodes fail is authored: the gate decides.

Run:  python tools/marketing/fig_honesty_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from _style import (  # noqa: E402
    ACCENT_LIGHT,
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
from scipy.ndimage import gaussian_filter, shift  # noqa: E402

from al_dic_3d.matching.primitives import _znssd  # noqa: E402

H = W = 420
WINSIZE = 32
STEP = 10
SHIFT_X, SHIFT_Y = 4.0, 2.0  # the true rigid translation (px)
BLOB_C, BLOB_R = (250.0, 165.0), 62.0  # the decorrelated disc
THRESHOLD = 1.0  # the shipping default (temporal_gate_znssd)


def _speckle(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    s = gaussian_filter(rng.standard_normal((H, W)), sigma=2.0)
    s = (s - s.min()) / (s.max() - s.min())
    return 40.0 + 180.0 * s


def _scene() -> tuple[np.ndarray, np.ndarray]:
    ref = _speckle(3)
    dfm = shift(ref, (SHIFT_Y, SHIFT_X), order=3, mode="nearest")
    yy, xx = np.mgrid[0:H, 0:W]
    disc = (xx - BLOB_C[0]) ** 2 + (yy - BLOB_C[1]) ** 2 < BLOB_R**2
    dfm = np.where(disc, _speckle(97), dfm)  # pattern destroyed inside the disc
    return ref, dfm


def main() -> int:
    ref, dfm = _scene()

    half = WINSIZE // 2 + 2
    ys = np.arange(half, H - half, STEP)
    xs = np.arange(half, W - half, STEP)
    X, Y = np.meshgrid(xs, ys)
    pts = np.column_stack([X.ravel().astype(float), Y.ravel().astype(float)])
    n = pts.shape[0]

    # The "solver output": correct translation outside the disc, frozen inside it.
    frozen = (pts[:, 0] - BLOB_C[0]) ** 2 + (pts[:, 1] - BLOB_C[1]) ** 2 < (BLOB_R * 0.8) ** 2
    u = np.zeros((n, 2))
    u[:, 0] = np.where(frozen, 0.0, SHIFT_X)
    u[:, 1] = np.where(frozen, 0.0, SHIFT_Y)

    z = _znssd(
        ref,
        dfm,
        pts,
        u,
        np.zeros((n, 4)),
        WINSIZE,
        np.ones(n, dtype=bool),
        np.ones((H, W), dtype=np.float64),
    )
    killed = ~(z <= THRESHOLD)  # the gate's exact rule (NaN also fails)
    print(f"  gate killed {killed.sum()}/{n} nodes ({100 * killed.mean():.1f}%)")
    print(
        f"  ZNSSD median kept {np.nanmedian(z[~killed]):.4f} | killed {np.nanmedian(z[killed]):.3f}"
    )

    fig, axes = plt.subplots(1, 3, figsize=(13.6, 5.0), dpi=110, facecolor=BG_DARKEST)

    # 1 — what the solver returned
    ax = axes[0]
    ax.imshow(dfm, cmap="gray", interpolation="bilinear")
    sc = ax.scatter(
        pts[:, 0],
        pts[:, 1],
        c=np.hypot(u[:, 0], u[:, 1]),
        cmap="turbo",
        s=13,
        vmin=0,
        vmax=np.hypot(SHIFT_X, SHIFT_Y),
    )
    cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.02)
    cb.set_label(
        "|u| shipped by the solver (px)", color=TEXT_SECONDARY, fontsize=9, fontfamily=MONO
    )
    cb.ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    ax.set_title(
        "raw solver field — finite everywhere,\nsmooth, and wrong in the disc",
        color=BAD,
        fontsize=11,
        fontfamily=MONO,
        pad=8,
    )

    # 2 — the independent metric
    ax = axes[1]
    sc = ax.scatter(pts[:, 0], pts[:, 1], c=np.log10(np.clip(z, 1e-4, None)), cmap="magma", s=16)
    cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.02)
    cb.set_label(
        "log10 ZNSSD  (frame 0 -> k, re-derived)", color=TEXT_SECONDARY, fontsize=9, fontfamily=MONO
    )
    cb.ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    ax.set_facecolor("#0f1424")
    ax.set_title(
        "independent re-verification of every\nshipped displacement",
        color=ACCENT_LIGHT,
        fontsize=11,
        fontfamily=MONO,
        pad=8,
    )

    # 3 — what actually ships
    ax = axes[2]
    ax.imshow(dfm, cmap="gray", interpolation="bilinear", alpha=0.65)
    ax.scatter(pts[~killed, 0], pts[~killed, 1], c=GOOD, s=13, label="kept")
    ax.scatter(
        pts[killed, 0],
        pts[killed, 1],
        c=BAD,
        s=22,
        marker="x",
        linewidths=1.4,
        label=f"NaN-ed by the gate ({killed.sum()})",
    )
    leg = ax.legend(facecolor="#141929", edgecolor=TEXT_SECONDARY, fontsize=9, loc="lower left")
    for t in leg.get_texts():
        t.set_color(TEXT_PRIMARY)
    ax.set_title(
        f"gated result — threshold ZNSSD <= {THRESHOLD}\ninvalid propagates to every export",
        color=GOOD,
        fontsize=11,
        fontfamily=MONO,
        pad=8,
    )

    for ax in axes:
        ax.set_xlim(0, W)
        ax.set_ylim(H, 0)
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(TEXT_SECONDARY)

    fig.text(
        0.5,
        0.955,
        "The honesty gate — a failure the solver reports as success",
        color=TEXT_PRIMARY,
        fontsize=14,
        fontweight="bold",
        ha="center",
        fontfamily=MONO,
    )
    fig.text(
        0.5,
        0.035,
        "Speckle translated by a known (4, 2) px; inside the disc the pattern is replaced by "
        "uncorrelated speckle and the tracker freezes.\n"
        "The gate is the shipping code and picks the failing nodes itself — no node is "
        "labelled by hand.",
        color=TEXT_SECONDARY,
        fontsize=9.5,
        ha="center",
        fontfamily=MONO,
        linespacing=1.6,
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.855, bottom=0.135, wspace=0.16)
    optimize_png(save(fig, "honesty_gate.png", dpi=110), max_width=1500)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
