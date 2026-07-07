"""Render the S3 parity-run displacement fields + 3D reconstruction to PNGs."""

# ruff: noqa: E402

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

from matlab_parity import LEFT_IMGS, load_baseline

WORK = REPO / "reports" / "parity_s3"
FIELDS = ("U", "V", "W")


def main() -> None:
    ours = np.load(WORK / "s3_ours.npz")
    pts, disp, x_left = ours["points"], ours["displacement"], ours["xL"]
    base = load_baseline()
    fin = np.isfinite(pts[0]).all(axis=1)
    o_xy = pts[0][fin, :2]
    t_xy = base["coords"][0][:, :2]

    # ---- displacement fields, ours vs MATLAB, per frame ----------------------
    for k in (1, 2):
        fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True, sharey=True)
        tag = "" if k == 1 else "  [baseline itself unreliable at this frame]"
        fig.suptitle(
            f"Stereo DIC Challenge 1.0 S3 — frame 0→{k} displacement (mm){tag}",
            fontsize=14,
        )
        for j, name in enumerate(FIELDS):
            o_val = disp[k][fin, j]
            t_val = base["disp"][k][:, j]
            lo = np.nanpercentile(np.concatenate([o_val, t_val]), 2)
            hi = np.nanpercentile(np.concatenate([o_val, t_val]), 98)
            for row, (xy, val, who) in enumerate(
                ((o_xy, o_val, "pyALDIC-3D (ours)"), (t_xy, t_val, "MATLAB baseline"))
            ):
                ax = axes[row, j]
                sc = ax.scatter(
                    xy[:, 0], xy[:, 1], c=val, s=(16 if row == 0 else 4),
                    cmap="turbo", vmin=lo, vmax=hi,
                )
                ax.set_aspect("equal")
                ax.invert_yaxis()
                ax.set_title(f"{who} — {name}", fontsize=10)
                fig.colorbar(sc, ax=ax, shrink=0.85, label="mm")
        for ax in axes[1]:
            ax.set_xlabel("X (mm)")
        for row in axes:
            row[0].set_ylabel("Y (mm)")
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        out = WORK / f"fields_frame{k}.png"
        fig.savefig(out, dpi=140)
        plt.close(fig)
        print("wrote", out)

    # ---- 3D reconstruction ----------------------------------------------------
    fig = plt.figure(figsize=(15, 6.5))
    fig.suptitle("S3 — 3D reconstruction (world = left camera, mm)", fontsize=14)
    p0 = pts[0][fin]
    mag1 = np.linalg.norm(disp[1][fin], axis=1)
    for i, (cval, label, ttl) in enumerate(
        (
            (p0[:, 2], "Z (mm)", "frame 1 surface, colored by depth Z"),
            (mag1, "|D| (mm)", "frame 1 surface, colored by |displacement| 0→1"),
        )
    ):
        ax = fig.add_subplot(1, 2, i + 1, projection="3d")
        sc = ax.scatter(p0[:, 0], p0[:, 1], p0[:, 2], c=cval, cmap="turbo", s=10)
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_zlabel("Z (mm)")
        ax.set_title(ttl, fontsize=10)
        ax.view_init(elev=28, azim=-60)
        fig.colorbar(sc, ax=ax, shrink=0.6, label=label)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out = WORK / "reconstruction_3d.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", out)

    # ---- tracked points over the left image ------------------------------------
    import cv2

    img = cv2.imread(str(LEFT_IMGS / "Images_Stereo_Sample3_images" / "0000_0.tif"), 0)
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.imshow(img, cmap="gray")
    xl0 = x_left[0][fin]
    sc = ax.scatter(xl0[:, 0], xl0[:, 1], c=disp[1][fin, 1], cmap="turbo", s=12)
    ax.set_title(
        "Tracked mesh points on left frame 1 (533 in-mask nodes), colored by V (mm), 0→1"
    )
    fig.colorbar(sc, ax=ax, shrink=0.8, label="V (mm)")
    ax.set_axis_off()
    fig.tight_layout()
    out = WORK / "tracked_points_left.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
