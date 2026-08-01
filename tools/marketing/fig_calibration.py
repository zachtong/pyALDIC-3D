"""Built-in stereo calibration, end to end -> ``assets/calibration.png``.

Three panels, all produced by the shipping calibration stack:

1. the coded circular target as pyALDIC-3D prints it
   (``CodedCircleGridSpec.render`` — the same geometry the 1:1 PDF printout
   uses), with the three concentric-ring fiducials called out;
2. the SELF-DEVELOPED detector's output on a perspective view of that target
   (``calibration.detect.detect_board``): every recovered dot centre plus the
   fiducial triangle that fixes the target frame, so partial views still key;
3. per-image QC from a real stereo solve
   (``calibration.solve.calibrate_stereo``) on the analytic synthetic rig from
   ``tests/synth_calib.py`` — the per-pair reprojection bars, the rejection
   threshold, and the recovered parameters versus the values the scene was
   rendered with.

Panel 3 is the differentiator: the MATLAB reference prints one frame's error
and gates nothing.

Run:  python tools/marketing/fig_calibration.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from _style import (  # noqa: E402
    ACCENT_LIGHT,
    BAD,
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

from al_dic_3d.calibration.boards import CodedCircleGridSpec  # noqa: E402
from al_dic_3d.calibration.detect import detect_board  # noqa: E402
from al_dic_3d.calibration.solve import calibrate_stereo  # noqa: E402

COLS, ROWS, SPACING = 12, 9, 7.0  # the author's real target: 12x9 dots at 7 mm
N_POSES = 12


def _spec() -> CodedCircleGridSpec:
    return CodedCircleGridSpec(cols=COLS, rows=ROWS, spacing=SPACING, dark_dots=True)


def _panel_board(ax, spec: CodedCircleGridSpec) -> None:
    board = spec.render(px_per_mm=10.0)
    ax.imshow(board, cmap="gray", interpolation="bilinear")
    m = SPACING * 10.0
    for r, c in spec.fiducials:
        ax.add_patch(
            plt.Circle(
                (m + c * SPACING * 10.0, m + r * SPACING * 10.0),
                SPACING * 10.0 * 0.62,
                fill=False,
                color=GOOD,
                lw=2.0,
            )
        )
    ax.set_title(
        f"1 · print — {COLS}x{ROWS} dots @ {SPACING:g} mm\n3 ring fiducials fix the frame",
        color=TEXT_SECONDARY,
        fontsize=10.5,
        fontfamily=MONO,
        pad=8,
    )


def _perspective_view(spec: CodedCircleGridSpec, size: int = 900) -> np.ndarray:
    """One oblique camera view of the printed target (the detector's real input)."""
    import cv2

    board = spec.render(px_per_mm=6.0)
    h, w = board.shape
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32(
        [
            [0.16 * size, 0.10 * size],
            [0.93 * size, 0.20 * size],
            [0.86 * size, 0.90 * size],
            [0.07 * size, 0.72 * size],
        ]
    )
    warped = cv2.warpPerspective(
        board,
        cv2.getPerspectiveTransform(src, dst),
        (size, size),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )
    return cv2.GaussianBlur(warped, (0, 0), 1.1)


def _panel_detect(ax, spec: CodedCircleGridSpec) -> str:
    view = _perspective_view(spec)
    det = detect_board(view, spec)
    ax.imshow(view, cmap="gray", interpolation="bilinear")
    if det.ok:
        pts = det.image_points.reshape(-1, 2)
        ax.scatter(pts[:, 0], pts[:, 1], s=13, facecolors="none", edgecolors=DEPTH, linewidths=1.1)
        ids = [int(i) for i in det.ids]
        fid_xy = [pts[ids.index(f)] for f in spec.fiducial_ids if f in ids]
        if len(fid_xy) == 3:
            tri = np.array(fid_xy + [fid_xy[0]])
            ax.plot(tri[:, 0], tri[:, 1], color=GOOD, lw=1.8, alpha=0.95)
            ax.scatter(
                [p[0] for p in fid_xy],
                [p[1] for p in fid_xy],
                s=70,
                facecolors="none",
                edgecolors=GOOD,
                linewidths=2.0,
            )
        note = f"{pts.shape[0]}/{COLS * ROWS} dots recovered"
        col = GOOD
    else:
        note = f"detection failed: {det.reason}"
        col = BAD
    ax.set_title(
        f"2 · detect (self-developed)\n{note} on an oblique view",
        color=col,
        fontsize=10.5,
        fontfamily=MONO,
        pad=8,
    )
    return note


def _panel_qc(ax) -> str:
    import synth_calib as sc

    spec = _spec()
    rig_true = sc.make_rig()
    poses = sc.board_poses((COLS * SPACING, ROWS * SPACING), n=N_POSES)
    lefts, rights = sc.render_stereo_set(spec, rig_true, poses)

    det_l = [detect_board(im, spec) for im in lefts]
    det_r = [detect_board(im, spec) for im in rights]
    res = calibrate_stereo(
        det_l, det_r, image_size=(sc.IMG_W, sc.IMG_H), dot_radius_mm=0.5 * spec.dot_mm
    )

    per = np.array([max(p.rms_left, p.rms_right) for p in res.pairs], dtype=float)
    keep = np.array([p.used for p in res.pairs], dtype=bool)
    idx = np.arange(len(per))
    ax.bar(idx[keep], per[keep], color=ACCENT_LIGHT, width=0.68, label="kept")
    if (~keep).any():
        ax.bar(idx[~keep], per[~keep], color=BAD, width=0.68, label="rejected")
    med = float(np.median(per[np.isfinite(per)]))
    ax.axhline(med, color=GOOD, lw=1.3, ls="--", label=f"median {med:.3f} px")
    ax.set_xlabel("image pair", color=TEXT_SECONDARY, fontsize=10, fontfamily=MONO)
    ax.set_ylabel("reprojection RMS (px)", color=TEXT_SECONDARY, fontsize=10, fontfamily=MONO)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8.5)
    ax.set_facecolor("#0f1424")
    for sp in ax.spines.values():
        sp.set_color(TEXT_SECONDARY)
    leg = ax.legend(facecolor="#141929", edgecolor=TEXT_SECONDARY, fontsize=9)
    for t in leg.get_texts():
        t.set_color(TEXT_PRIMARY)

    fx_true = rig_true.cameras["L"].fx
    fx_got = res.rig.cameras["L"].fx
    base_true = float(np.linalg.norm(rig_true.pose("R")[1]))
    line = (
        f"stereo RMS {res.rms:.3f} px | epipolar {res.epipolar_rms:.3f} px | "
        f"fx {100 * (fx_got / fx_true - 1):+.3f} % | "
        f"baseline {1000 * (res.baseline - base_true):+.1f} um vs {base_true:.1f} mm truth"
    )
    ax.set_title(
        "3 · solve with QC — every pair scored;\noutliers rejected, then re-solved",
        color=TEXT_SECONDARY,
        fontsize=10.5,
        fontfamily=MONO,
        pad=8,
    )
    print("  " + line)
    return line


def main() -> int:
    spec = _spec()
    fig, axes = plt.subplots(1, 3, figsize=(14.4, 5.0), dpi=110, facecolor=BG_DARKEST)
    for ax in axes[:2]:
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(TEXT_SECONDARY)

    _panel_board(axes[0], spec)
    note = _panel_detect(axes[1], spec)
    print(f"  {note}")
    line = _panel_qc(axes[2])

    fig.text(
        0.5,
        0.965,
        "Calibrate inside the app — print, shoot, solve, verify",
        color=TEXT_PRIMARY,
        fontsize=14,
        fontweight="bold",
        ha="center",
        fontfamily=MONO,
    )
    fig.text(
        0.5,
        0.045,
        "Synthetic rig with exactly known truth, solved by the shipping code\n" + line,
        color=TEXT_SECONDARY,
        fontsize=9.5,
        ha="center",
        fontfamily=MONO,
        linespacing=1.7,
    )
    fig.subplots_adjust(left=0.05, right=0.975, top=0.80, bottom=0.185, wspace=0.24)
    optimize_png(save(fig, "calibration.png", dpi=110), max_width=1600)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
