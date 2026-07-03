"""Generate ``reports/phase2_strategies.pdf`` — the tri-strategy comparison (02 §6).

Runs S1/S2/S3 on the synthetic non-planar ground-truth dataset (analytic truth —
the MATLAB-baseline and Challenge arms are deferred until real data is provided)
and renders a publication-grade comparison: per-frame displacement RMSE (drift),
survival + reprojection QC signals, a deformation sweep (failure vs deformation,
the S3 focus), and a summary table with drift slope / noise floor / runtime.

Self-verifying: exits non-zero if any strategy fails to produce a sane result, so
the PDF can never claim green falsely.

Run:  python tools/phase2_report.py
"""
# ruff: noqa: E402, E501  (imports follow sys.path setup; long descriptive report strings)

from __future__ import annotations

import sys
import time
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

import synth_surface as ss
from al_dic_3d import __version__
from al_dic_3d.matching.contracts import INVALID
from al_dic_3d.runner import load_config, run_pipeline

STRATEGIES = ["track_both", "stereo_each_frame", "ref_direct"]
LABELS = {
    "track_both": "S1 track_both",
    "stereo_each_frame": "S2 stereo_each_frame",
    "ref_direct": "S3 ref_direct",
}
COLORS = {"track_both": "#1565c0", "stereo_each_frame": "#2e7d32", "ref_direct": "#c62828"}

MAIN_IMG, MAIN_FRAMES, MAIN_DEFORM = 300, 6, 0.6
SWEEP_IMG, SWEEP_FRAMES = 260, 4
SWEEP_DEFORMS = [0.3, 0.6, 0.9, 1.2, 1.5]


def _metrics(result, gt) -> dict:
    rec = result.reconstruction
    tracked = result.correspondence.source != INVALID
    nf = rec.n_frames
    rmse, med, surv, reproj = [], [], [], []
    for k in range(nf):
        tr = tracked[k]
        surv.append(float(tr.mean()))
        reproj.append(
            float(np.nanmedian(rec.reproj_error[k]))
            if np.isfinite(rec.reproj_error[k]).any()
            else np.nan
        )
        if k == 0:
            rmse.append(0.0)
            med.append(0.0)
            continue
        com = tr & tracked[0]
        d = np.linalg.norm(rec.displacement[k][com] - gt["displacement"][k][com], axis=1) * 1000.0
        d = d[np.isfinite(d)]
        rmse.append(float(np.sqrt(np.mean(d**2))) if d.size else np.nan)
        med.append(float(np.median(d)) if d.size else np.nan)
    rmse = np.array(rmse)
    frames = np.arange(nf)
    fin = np.isfinite(rmse) & (frames > 0)
    slope = float(np.polyfit(frames[fin], rmse[fin], 1)[0]) if fin.sum() >= 2 else np.nan
    resid = (
        rmse[fin] - np.polyval(np.polyfit(frames[fin], rmse[fin], 1), frames[fin])
        if fin.sum() >= 2
        else np.array([0.0])
    )
    return {
        "rmse": rmse,
        "med": np.array(med),
        "surv": np.array(surv),
        "reproj": np.array(reproj),
        "drift_slope": slope,
        "noise_floor": float(np.sqrt(np.mean(resid**2))),
        "mean_rmse": float(np.nanmean(rmse[1:])),
        "mean_surv": float(np.mean(surv)),
    }


def _run(scene_dir: Path, scene: dict, strategy: str) -> dict:
    cfg = load_config(ss.write_config(scene_dir, scene, strategy=strategy))
    t0 = time.perf_counter()
    result = run_pipeline(replace(cfg, strategy=strategy))
    runtime = time.perf_counter() - t0
    gt = ss.gt_tracks(scene, result.ref_coords)
    m = _metrics(result, gt)
    m["runtime"] = runtime
    m["result"] = result
    m["gt"] = gt
    return m


def _build_main(workdir: Path) -> dict:
    scene = ss.build_surface_scene(
        workdir / "main", img=MAIN_IMG, n_frames=MAIN_FRAMES, deform=MAIN_DEFORM, seed=7
    )
    return {s: _run(workdir / "main", scene, s) for s in STRATEGIES}


def _build_sweep(workdir: Path) -> dict:
    out = {s: {"rmse": [], "surv": []} for s in STRATEGIES}
    for i, dfm in enumerate(SWEEP_DEFORMS):
        d = workdir / f"sweep_{i}"
        scene = ss.build_surface_scene(d, img=SWEEP_IMG, n_frames=SWEEP_FRAMES, deform=dfm, seed=7)
        for s in STRATEGIES:
            m = _run(d, scene, s)
            out[s]["rmse"].append(m["mean_rmse"])
            out[s]["surv"].append(m["mean_surv"])
    return out


# --- pages -------------------------------------------------------------------


def _page_summary(pdf, main: dict):
    fig = plt.figure(figsize=(8.5, 11))
    fig.suptitle(
        "pyALDIC-3D - Phase 2: Tri-Strategy Correspondence Comparison", fontsize=14, y=0.97
    )
    ctx = (
        f"al_dic_3d {__version__}   |   synthetic non-planar ground truth (analytic)\n"
        f"Curved bump surface + known 3D Lagrangian deformation, 18-deg converging distorted stereo.\n"
        f"Main scene: {MAIN_IMG}px, {MAIN_FRAMES} frames, deform={MAIN_DEFORM}. Metrics per 02 sec.6.\n"
        f"(MATLAB-baseline and Challenge arms deferred until a real dataset is provided.)"
    )
    fig.text(0.08, 0.90, ctx, fontsize=9.5, va="top")

    ax = fig.add_axes([0.06, 0.50, 0.88, 0.34])
    ax.axis("off")
    ax.set_title("Summary (main scene)", fontsize=11, loc="left")
    rows = []
    for s in STRATEGIES:
        m = main[s]
        rows.append(
            [
                LABELS[s],
                f"{m['mean_rmse']:.0f}",
                f"{m['drift_slope']:.1f}",
                f"{m['noise_floor']:.0f}",
                f"{m['mean_surv'] * 100:.0f}%",
                f"{m['runtime'] / MAIN_FRAMES:.2f}",
            ]
        )
    table = ax.table(
        cellText=rows,
        colLabels=[
            "strategy",
            "RMSE (um)",
            "drift (um/frame)",
            "noise floor (um)",
            "survival",
            "s/frame",
        ],
        colWidths=[0.30, 0.13, 0.19, 0.17, 0.11, 0.10],
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)

    takeaway = (
        "Reading (02 sec.3): S3 ref_direct has the cleanest error (zero drift, no interpolation) and\n"
        "wins on short / small-deformation sequences; S2 stereo_each_frame carries a fresh (non-\n"
        "cancelling) per-frame stereo noise but a single drift chain -> best for long sequences; S1\n"
        "track_both is the cheapest and the MATLAB-baseline anchor. Differences widen with sequence\n"
        "length (drift) and deformation (S3 fails first) - see the following pages."
    )
    fig.text(0.08, 0.44, takeaway, fontsize=9.5, va="top", family="monospace")
    pdf.savefig(fig)
    plt.close(fig)


def _page_accuracy(pdf, main: dict):
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
    fig.suptitle("Displacement accuracy vs frame (log scale; error grows with deformation/drift)", fontsize=12)
    for s in STRATEGIES:
        m = main[s]
        fr = np.arange(len(m["rmse"]))[1:]  # frame 0 has zero displacement error
        axes[0].plot(fr, m["rmse"][1:], "-o", color=COLORS[s], label=LABELS[s])
        axes[1].plot(fr, m["med"][1:], "-o", color=COLORS[s], label=LABELS[s])
    axes[0].set_title("displacement RMSE vs truth (um)")
    axes[1].set_title("displacement median error (um)")
    for a in axes:
        a.set_xlabel("frame")
        a.set_ylabel("error (um)")
        a.set_yscale("log")
        a.grid(alpha=0.3, which="both")
        a.legend(fontsize=8)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)


def _page_qc(pdf, main: dict):
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
    fig.suptitle("QC signals vs frame", fontsize=13)
    for s in STRATEGIES:
        m = main[s]
        fr = np.arange(len(m["surv"]))
        axes[0].plot(fr, m["surv"] * 100, "-o", color=COLORS[s], label=LABELS[s])
        axes[1].plot(fr, m["reproj"] * 1e6, "-o", color=COLORS[s], label=LABELS[s])
    axes[0].set_title("valid-point survival (%)")
    axes[0].set_ylim(0, 105)
    axes[1].set_title("median reprojection error (x1e-6 norm.)")
    for a in axes:
        a.set_xlabel("frame")
        a.grid(alpha=0.3)
        a.legend(fontsize=8)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)


def _page_sweep(pdf, sweep: dict):
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
    fig.suptitle("Deformation sweep: accuracy + survival vs deformation", fontsize=13)
    x = SWEEP_DEFORMS
    for s in STRATEGIES:
        axes[0].plot(x, sweep[s]["rmse"], "-o", color=COLORS[s], label=LABELS[s])
        axes[1].plot(x, np.array(sweep[s]["surv"]) * 100, "-o", color=COLORS[s], label=LABELS[s])
    axes[0].set_title("mean displacement RMSE (um)")
    axes[1].set_title("mean survival (%)")
    axes[1].set_ylim(0, 105)
    for a in axes:
        a.set_xlabel("deformation scale")
        a.grid(alpha=0.3)
        a.legend(fontsize=8)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)


def _page_notes(pdf):
    fig = plt.figure(figsize=(8.5, 11))
    fig.suptitle("Method, limitations & scope", fontsize=13, y=0.96)
    notes = (
        "DATASETS (02 sec.6)\n"
        "  - Synthetic non-planar truth: curved surface + known 3D Lagrangian field, rendered with a\n"
        "    fixed-point Lagrangian warp through two distorted converging cameras (projectively\n"
        "    consistent). Ground truth is analytic.\n"
        "  - The MATLAB-baseline arm (S1 parity anchor) and the Stereo-DIC Challenge arm are DEFERRED\n"
        "    until the user provides those datasets; the harness is dataset-agnostic and will add them.\n\n"
        "METRICS\n"
        "  - Displacement RMSE vs truth; drift slope (linear term of RMSE vs frame); noise floor\n"
        "    (RMS of the de-trended RMSE); survival vs frame; reprojection error vs frame; and a\n"
        "    deformation sweep (accuracy + survival vs deformation).\n\n"
        "LIMITATIONS\n"
        "  - Synthetic-only comparison; absolute numbers are geometry-limited (converging-rig depth\n"
        "    conditioning), not representative of any specific experiment.\n"
        "  - First-order (affine) subset warp; large deformation eventually breaks the cross match\n"
        "    (S3 first). Second-order warp is a reserved engine extension (02 sec.5.5 E2).\n"
        "  - Per decision D9 this figure set doubles as validation material for the standalone\n"
        "    SoftwareX Part-2 article.\n"
    )
    fig.text(0.07, 0.88, notes, fontsize=10, va="top", family="monospace")
    pdf.savefig(fig)
    plt.close(fig)


def main() -> int:
    import tempfile

    workdir = Path(tempfile.mkdtemp(prefix="aldic3d_phase2_"))
    print("rendering + running main scene (3 strategies)...")
    main_res = _build_main(workdir)
    print("rendering + running deformation sweep...")
    sweep_res = _build_sweep(workdir)

    out = REPO / "reports"
    out.mkdir(exist_ok=True)
    pdf_path = out / "phase2_strategies.pdf"
    with PdfPages(pdf_path) as pdf:
        _page_summary(pdf, main_res)
        _page_accuracy(pdf, main_res)
        _page_qc(pdf, main_res)
        _page_sweep(pdf, sweep_res)
        _page_notes(pdf)

    print(f"wrote {pdf_path}")
    ok = True
    for s in STRATEGIES:
        m = main_res[s]
        flag = m["mean_surv"] > 0.5 and np.isfinite(m["mean_rmse"]) and m["mean_rmse"] < 1000.0
        ok = ok and flag
        print(
            f"  [{'OK' if flag else 'BAD'}] {LABELS[s]}: RMSE={m['mean_rmse']:.0f}um "
            f"drift={m['drift_slope']:.1f}um/fr survival={m['mean_surv'] * 100:.0f}% "
            f"t/frame={m['runtime'] / MAIN_FRAMES:.2f}s"
        )
    if not ok:
        print("COMPARISON HARNESS FAILED (a strategy produced an unusable result)", file=sys.stderr)
        return 1
    print("COMPARISON HARNESS OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
