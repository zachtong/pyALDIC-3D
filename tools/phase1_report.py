"""Generate ``reports/phase1_report.pdf`` — Phase-1 headless-MVP validation report.

Builds the synthetic parity dataset (a distorted, tilted-plane stereo scene with
analytic ground truth), drives it through the real ``run_pipeline`` (the same path
as ``al-dic-3d run``), and renders a multi-page PDF: gate summary, frame-1
disparity QC, reprojection-error maps, the reconstructed 3D surface + displacement
field, and parity tables (recovered vs analytic truth) with a per-frame drift
monitor.

Self-verifying: exits non-zero if the parity gate fails, so the PDF can never
claim green falsely (mirrors ``tools/phase0_report.py``).

Run:  python tools/phase1_report.py
"""
# ruff: noqa: E402  (imports intentionally follow sys.path + matplotlib backend setup)

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))  # for the synth_parity generator

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

import synth_parity as sp
from al_dic_3d import __version__
from al_dic_3d.matching.contracts import INVALID
from al_dic_3d.runner import load_config, run_pipeline

IMG = 380
N_FRAMES = 6
SEED = 7


def _build():
    import tempfile

    workdir = Path(tempfile.mkdtemp(prefix="aldic3d_phase1_"))
    scene = sp.build_parity_scene(workdir, img=IMG, n_frames=N_FRAMES, seed=SEED)
    cfg = load_config(sp.write_config(workdir, scene))
    result = run_pipeline(cfg)
    gt = sp.gt_tracks(scene, result.ref_coords)
    return scene, result, gt


def _per_frame_stats(result, gt):
    cs, rec = result.correspondence, result.reconstruction
    tracked = cs.source != INVALID
    frames, pt_med, pt_p90, d_med, d_p90 = [], [], [], [], []
    for k in range(cs.n_frames):
        tr = tracked[k]
        pe = np.linalg.norm(rec.points[k][tr] - gt["world"][k][tr], axis=1) * 1000.0
        frames.append(k)
        pt_med.append(np.median(pe))
        pt_p90.append(np.percentile(pe, 90))
        if k > 0:
            com = tr & tracked[0]
            de = (
                np.linalg.norm(rec.displacement[k][com] - gt["displacement"][k][com], axis=1)
                * 1000.0
            )
            d_med.append(np.median(de))
            d_p90.append(np.percentile(de, 90))
        else:
            d_med.append(0.0)
            d_p90.append(0.0)
    return dict(frames=frames, pt_med=pt_med, pt_p90=pt_p90, d_med=d_med, d_p90=d_p90)


def _page_summary(pdf, scene, result, m):
    rows = sp.gate_rows(m)
    passed = all(r["pass"] for r in rows)
    fig = plt.figure(figsize=(8.5, 11))
    fig.suptitle("pyALDIC-3D - Phase 1 Headless MVP Validation Report", fontsize=15, y=0.97)

    ax0 = fig.add_axes([0.08, 0.86, 0.84, 0.06])
    ax0.axis("off")
    verdict = "GATE PASSED" if passed else "GATE FAILED"
    ax0.text(
        0.5,
        0.5,
        verdict,
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color="white",
        bbox=dict(boxstyle="round,pad=0.5", fc=("#2e7d32" if passed else "#c62828"), ec="none"),
    )

    ctx = (
        f"al_dic_3d {__version__}   |   strategy = {result.strategy}   |   "
        f"frames = {result.reconstruction.n_frames}   |   points = {result.reconstruction.n_pts}\n"
        f"Synthetic parity dataset: {IMG}x{IMG}px, 18-deg converging rig, tilted textured "
        f"plane + lens distortion,\nknown affine material deformation. Ground truth is analytic "
        f"(stands in for the MATLAB baseline until a real dataset is provided)."
    )
    fig.text(0.08, 0.80, ctx, fontsize=9.5, va="top")

    ax = fig.add_axes([0.08, 0.10, 0.84, 0.62])
    ax.axis("off")
    ax.set_title("Parity gate: recovered vs analytic ground truth", fontsize=11, loc="left")
    cell_text, colors = [], []
    for r in rows:
        cell_text.append(
            [
                r["name"],
                f"{r['value']:.4g}",
                f"{r['op']} {r['tol']:g}",
                "PASS" if r["pass"] else "FAIL",
            ]
        )
        colors.append(["#f5f5f5", "#f5f5f5", "#f5f5f5", "#c8e6c9" if r["pass"] else "#ffcdd2"])
    table = ax.table(
        cellText=cell_text,
        colLabels=["metric", "value", "tolerance", "result"],
        cellColours=colors,
        colWidths=[0.46, 0.18, 0.20, 0.16],
        loc="upper center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    pdf.savefig(fig)
    plt.close(fig)
    return passed


def _page_disparity_qc(pdf, result):
    cs = result.correspondence
    nodes = cs.xL[0]
    disp = cs.xR[0] - cs.xL[0]
    mag = np.linalg.norm(disp, axis=1)
    znssd = cs.quality[0]

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
    fig.suptitle("Frame-1 stereo match QC (L1 -> R1)", fontsize=13)
    sc0 = axes[0].scatter(nodes[:, 0], nodes[:, 1], c=mag, s=14, cmap="viridis")
    axes[0].quiver(
        nodes[:, 0],
        nodes[:, 1],
        disp[:, 0],
        disp[:, 1],
        angles="xy",
        scale_units="xy",
        scale=1,
        width=0.002,
        alpha=0.5,
    )
    axes[0].set_title("L->R disparity (px)")
    axes[0].invert_yaxis()
    axes[0].set_aspect("equal")
    fig.colorbar(sc0, ax=axes[0], shrink=0.8)

    sc1 = axes[1].scatter(nodes[:, 0], nodes[:, 1], c=znssd, s=16, cmap="magma_r")
    axes[1].set_title("ZNSSD (0 = perfect match)")
    axes[1].invert_yaxis()
    axes[1].set_aspect("equal")
    fig.colorbar(sc1, ax=axes[1], shrink=0.8)
    for a in axes:
        a.set_xlabel("u (px)")
        a.set_ylabel("v (px)")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)


def _page_reproj(pdf, result):
    rec = result.reconstruction
    nodes = result.correspondence.xL[0]
    nf = rec.n_frames
    last = nf - 1
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
    fig.suptitle("Reprojection error (undistort + DLT consistency)", fontsize=13)
    err_last = rec.reproj_error[last]
    finite = np.isfinite(err_last)
    sc = axes[0].scatter(
        nodes[finite, 0], nodes[finite, 1], c=err_last[finite] * 1e6, s=16, cmap="cividis"
    )
    axes[0].set_title(f"per-point reproj error, frame {last} (x1e-6 px)")
    axes[0].invert_yaxis()
    axes[0].set_aspect("equal")
    axes[0].set_xlabel("u (px)")
    axes[0].set_ylabel("v (px)")
    fig.colorbar(sc, ax=axes[0], shrink=0.8)

    per_frame = [rec.reproj_error[k][np.isfinite(rec.reproj_error[k])] * 1e6 for k in range(nf)]
    axes[1].boxplot(per_frame, positions=range(nf), showfliers=False)
    axes[1].set_title("reproj error distribution per frame")
    axes[1].set_xlabel("frame")
    axes[1].set_ylabel("reproj error (x1e-6 px)")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)


def _page_surface(pdf, result):
    rec = result.reconstruction
    P0 = rec.points[0]
    D = rec.displacement[rec.n_frames - 1]
    ok = np.isfinite(P0).all(axis=1) & np.isfinite(D).all(axis=1)
    P0, D = P0[ok], D[ok]
    dmag = np.linalg.norm(D, axis=1)

    fig = plt.figure(figsize=(11, 5.4))
    fig.suptitle("Reconstructed 3D surface + displacement (final frame)", fontsize=13)
    ax3d = fig.add_subplot(1, 2, 1, projection="3d")
    s0 = ax3d.scatter(P0[:, 0], P0[:, 1], P0[:, 2], c=P0[:, 2], s=10, cmap="terrain")
    ax3d.set_title("surface P^1 (colour = Z, mm)")
    ax3d.set_xlabel("X (mm)")
    ax3d.set_ylabel("Y (mm)")
    ax3d.set_zlabel("Z (mm)")
    fig.colorbar(s0, ax=ax3d, shrink=0.55, pad=0.1)

    ax = fig.add_subplot(1, 2, 2)
    s1 = ax.scatter(P0[:, 0], P0[:, 1], c=dmag * 1000.0, s=16, cmap="inferno")
    ax.quiver(P0[:, 0], P0[:, 1], D[:, 0], D[:, 1], angles="xy", alpha=0.5, width=0.003)
    ax.set_title("|displacement| (um) + in-plane quiver")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_aspect("equal")
    fig.colorbar(s1, ax=ax, shrink=0.8)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)


def _page_parity(pdf, result, gt, m):
    stats = _per_frame_stats(result, gt)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    fig.suptitle("Parity: recovered vs analytic ground truth", fontsize=13)

    axes[0, 0].hist(m["xL"], bins=30, color="#1565c0", alpha=0.8)
    axes[0, 0].axvline(np.median(m["xL"]), color="k", ls="--", lw=1)
    axes[0, 0].set_title(f"2D left-track error (median {np.median(m['xL']):.3f} px)")
    axes[0, 0].set_xlabel("|xL - xL_gt| (px)")

    axes[0, 1].hist(m["point"] * 1000.0, bins=30, color="#6a1b9a", alpha=0.8)
    axes[0, 1].axvline(np.median(m["point"]) * 1000, color="k", ls="--", lw=1)
    axes[0, 1].set_title(f"3D point error (median {np.median(m['point']) * 1000:.0f} um)")
    axes[0, 1].set_xlabel("|P - P_gt| (um)")

    axes[1, 0].hist(m["disp"] * 1000.0, bins=30, color="#ad1457", alpha=0.8)
    axes[1, 0].axvline(np.median(m["disp"]) * 1000, color="k", ls="--", lw=1)
    axes[1, 0].set_title(f"3D displacement error (median {np.median(m['disp']) * 1000:.0f} um)")
    axes[1, 0].set_xlabel("|D - D_gt| (um)")

    axes[1, 1].plot(stats["frames"], stats["pt_med"], "-o", label="3D point median")
    axes[1, 1].plot(stats["frames"], stats["pt_p90"], "--o", label="3D point p90")
    axes[1, 1].plot(stats["frames"][1:], stats["d_med"][1:], "-s", label="disp median")
    axes[1, 1].set_title("error drift vs frame (accumulative)")
    axes[1, 1].set_xlabel("frame")
    axes[1, 1].set_ylabel("error (um)")
    axes[1, 1].legend(fontsize=8)
    axes[1, 1].grid(alpha=0.3)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)


def _page_notes(pdf):
    fig = plt.figure(figsize=(8.5, 11))
    fig.suptitle("Boundary conditions, limitations & scope", fontsize=13, y=0.96)
    notes = (
        "EFFECT\n"
        "  - Full headless pipeline (calibration -> stereo match -> per-camera temporal track\n"
        "    -> resample -> DLT reconstruction) recovers 3D displacement to tens of microns on\n"
        "    a distorted synthetic stereo dataset, validated against analytic ground truth.\n\n"
        "PERFORMANCE\n"
        "  - track_both, accumulative; one frame-1 stereo match links two per-camera tracks.\n"
        "  - Error is geometry-limited (seed-independent): the 3D floor is set by the stereo\n"
        "    conditioning (18-deg converging rig, ~1500 px focal, 800 mm depth), not by noise.\n\n"
        "BOUNDARY CONDITIONS\n"
        "  - Left = world frame; matching on RAW images; distortion removed at point level only\n"
        "    (undistortPoints) before triangulation. NaN = invalid, propagated end to end.\n"
        "  - Stereo search window is edge-clamped, so nodes near the field border stay alive.\n\n"
        "LIMITATIONS / SCOPE\n"
        "  - This is a SYNTHETIC parity gate (analytic truth). The real Phase-1 gate is parity\n"
        "    vs a MATLAB baseline .mat on the user's dataset; it is deferred until that dataset\n"
        "    is provided, and the numeric envelope will be re-tuned to the real data then.\n"
        "  - The rendered surface is planar (tilted); a non-planar surface with a Lagrangian\n"
        "    fixed-point warp is the Phase-2 synthetic generator.\n"
        "  - Accumulative mode only; incremental mode + strategies S2/S3 land in Phase 2.\n"
        "  - Per-frame temporal ZNSSD is not yet surfaced (quality = frame-1 stereo ZNSSD);\n"
        "    QualityGate enforcement is Phase 2.\n"
    )
    fig.text(0.07, 0.88, notes, fontsize=10, va="top", family="monospace")
    pdf.savefig(fig)
    plt.close(fig)


def main() -> int:
    scene, result, gt = _build()
    m = sp.metrics(result, gt)
    out = REPO / "reports"
    out.mkdir(exist_ok=True)
    pdf_path = out / "phase1_report.pdf"
    with PdfPages(pdf_path) as pdf:
        passed = _page_summary(pdf, scene, result, m)
        _page_disparity_qc(pdf, result)
        _page_reproj(pdf, result)
        _page_surface(pdf, result)
        _page_parity(pdf, result, gt, m)
        _page_notes(pdf)

    print(f"wrote {pdf_path}")
    for r in sp.gate_rows(m):
        flag = "PASS" if r["pass"] else "FAIL"
        print(f"  [{flag}] {r['name']}: {r['value']:.4g} {r['op']} {r['tol']:g}")
    if not passed:
        print("PARITY GATE FAILED", file=sys.stderr)
        return 1
    print("PARITY GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
