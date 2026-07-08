# ruff: noqa: E501  (report text lines)
"""Phase-5 validation sweep report — Challenge 1.0 S2/S4/S5 + Challenge 2.0 T1.

Draws from the JSON artifacts written by tools/challenge_{s2,s4,s5,c2_task1}.py.
Output: reports/challenge_sweep.pdf (gitignored).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

REPO = Path(__file__).resolve().parents[1]
CH = REPO / "reports" / "challenge"
PDF = REPO / "reports" / "challenge_sweep.pdf"

S2A = json.loads((CH / "s2_16mm.json").read_text())
S2B = json.loads((CH / "s2_35mm.json").read_text())
S4 = json.loads((CH / "s4.json").read_text())
S5 = json.loads((CH / "s5.json").read_text())
C2 = json.loads((CH / "c2_task1.json").read_text())


def _fig(title: str) -> plt.Figure:
    fig = plt.figure(figsize=(11, 8.5))
    fig.suptitle(title, fontsize=14, fontweight="bold")
    return fig


def page_title(pdf: PdfPages) -> None:
    fig = _fig("pyALDIC-3D Phase-5 validation sweep - Stereo DIC Challenge 1.0 + 2.0")
    lines = [
        "Four datasets, four independent accuracy anchors (2026-07-07):",
        "",
        "S2  simulated rigid translations, EXACT +-10/20 mm truth, 2 rigs",
        f"    16mm rig: |err| median {S2A['err_med_um']:.1f} um, max {S2A['err_max_um']:.1f} um (16 steps)",
        f"    35mm rig: |err| median {S2B['err_med_um']:.1f} um, max {S2B['err_max_um']:.1f} um",
        f"    noise floor stds (u,v,w) um: 16mm {[round(v*1000,2) for v in S2A['noise_floor_step17_std_mm']]},"
        f" 35mm {[round(v*1000,2) for v in S2B['noise_floor_step17_std_mm']]}",
        "    challenge participant bar (Group02): u/v 11-17 um, w 56-89 um -> 6-90x better",
        "",
        "S4  simulated D-specimen tension (~7% strain, 170 frames) vs MatchID",
        f"    v (tension axis) diff median: {S4['frames']['169']['v']['med_um']:.1f} um on 4.0 mm",
        f"    u {S4['frames']['169']['u']['med_um']:.1f} um | w {S4['frames']['169']['w']['med_um']:.1f} um"
        " (both codes' w uncertainty ~100 um; no absolute truth shipped)",
        "",
        "S5  EXPERIMENTAL tension to fracture (2448x2048, 54 frames, ~11% strain)",
        "    built-in calibration on REAL dot-target photos (47/47 after the",
        f"    flat-field fix): fx {S5['calibration']['d_fx0_pct']:+.2f}%/{S5['calibration']['d_fx1_pct']:+.2f}%"
        f" vs vendor, angle d {S5['calibration']['d_angle_deg']:+.3f} deg",
        f"    incremental DIC to {S5['exx_final']*100:.1f}% strain at 2070 lb, last-frame valid 98%",
        f"    strain noise floor (10 static frames): {S5['noise_floor_exx_std']:.1e} ({S5['noise_floor_exx_std']*1e6:.0f} ue)",
        "",
        "C2  Challenge 2.0 Task 1 (elastic, official 123.caldat) vs DICe",
        "    pixel-displacement diff median 0.003-0.015 px over 11300 pts/frame",
        f"    eyy at frame 50: {C2['noise']['eyy_at_50']*100:.3f}% vs protocol anchor 0.26%",
        f"    eyy noise (frames 1-5): {C2['noise']['eyy_std']*1e6:.0f} ue",
        "",
        "Hardening landed during the sweep (product code):",
        "  - flat-field binarization rung (S5 real photos: detections 7/47 -> 47/47)",
        "  - stereo disparity prior workflow for convergent rigs (S2: ~290 px true",
        "    disparity had silently aliased; triangulated scale was 16% short)",
        "Deferred: Challenge 2.0 full official protocol (5 VSGs, every-pixel export,",
        "standard coordinate system, RBM + necking series) - a dedicated deliverable.",
    ]
    fig.text(0.06, 0.92, "\n".join(lines), va="top", family="monospace", fontsize=9)
    pdf.savefig(fig)
    plt.close(fig)


def page_s2(pdf: PdfPages) -> None:
    fig = _fig("S2 - simulated rigid translations vs EXACT truth")
    for i, (data, rig) in enumerate(((S2A, "16 mm"), (S2B, "35 mm"))):
        ax = fig.add_subplot(2, 2, 1 + i)
        tru = np.asarray(data["truth_mm"])
        ali = np.asarray(data["aligned_mm"])
        steps = np.arange(1, 17)
        err = np.asarray(data["err_mm"]) * 1000
        ax.bar(steps, err, color="#4C72B0")
        ax.set_xlabel("step")
        ax.set_ylabel("|error| (um)")
        ax.set_title(f"{rig} rig: per-step 3D error after one global rotation fit", fontsize=9)

        ax = fig.add_subplot(2, 2, 3 + i)
        ax.plot(np.linalg.norm(tru, axis=1), np.linalg.norm(ali, axis=1), "o", ms=4)
        lim = [0, 30]
        ax.plot(lim, lim, "k--", lw=0.8)
        ax.set_xlabel("imposed |d| (mm)")
        ax.set_ylabel("measured |d| (mm)")
        ax.set_title(f"{rig}: magnitude parity (10/14.14/20/28.28 mm)", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    pdf.savefig(fig)
    plt.close(fig)


def page_s4(pdf: PdfPages) -> None:
    fig = _fig("S4 - simulated D-tension (~7% strain): parity vs MatchID reference")
    frames = sorted(int(k) for k in S4["frames"])
    ax = fig.add_subplot(2, 2, 1)
    for name, c in (("u", "#4C72B0"), ("v", "#55A868"), ("w", "#C44E52")):
        ax.plot(frames, [S4["frames"][str(f)][name]["med_um"] for f in frames],
                "o-", color=c, label=name)
    ax.set_xlabel("frame")
    ax.set_ylabel("|diff| median (um)")
    ax.set_title("displacement diff vs MatchID (3234-pt grid)", fontsize=9)
    ax.legend(fontsize=8)

    ax = fig.add_subplot(2, 2, 2)
    v_ours = [S4["frames"][str(f)]["v"]["ours_med_mm"] for f in frames]
    v_mid = [S4["frames"][str(f)]["v"]["matchid_med_mm"] for f in frames]
    ax.plot(frames, v_ours, "o-", label="ours")
    ax.plot(frames, v_mid, "s--", label="MatchID")
    ax.set_xlabel("frame")
    ax.set_ylabel("v median (mm)")
    ax.set_title("tension-axis displacement", fontsize=9)
    ax.legend(fontsize=8)

    ax = fig.add_subplot(2, 1, 2)
    ax.axis("off")
    ax.text(0, 0.9, "\n".join([
        "Notes",
        "- MatchID output is the only shipped reference (sigma 2-9 um); the FEA truth",
        "  behind the renders was never distributed. v-axis agreement is 0.5 um median",
        "  at 4 mm (0.012%); u 10.6 um; w departs linearly to ~109 um at frame 169 -",
        "  attribution between the two codes is not decidable without truth.",
        f"- accumulative mode, winsize 24 / step 8, {S4['wall_s']:.0f} s for 170 frames.",
    ]), va="top", family="monospace", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    pdf.savefig(fig)
    plt.close(fig)


def page_s5(pdf: PdfPages) -> None:
    fig = _fig("S5 - experimental tension to fracture (real cameras, real target)")
    frames = S5["frames"]
    load = np.asarray(S5["load_lb"], dtype=np.float64)
    exx = np.asarray(S5["exx_med"], dtype=np.float64)

    ax = fig.add_subplot(2, 2, 1)
    ax.plot(exx * 100, load, "o-", ms=3)
    ax.set_xlabel("median exx (%)")
    ax.set_ylabel("load (lb)")
    ax.set_title("stress-strain shape from DIC exx vs load cell", fontsize=9)

    ax = fig.add_subplot(2, 2, 2)
    ax.plot(frames, np.asarray(S5["valid_frac"]) * 100, "o-", ms=3)
    ax.set_xlabel("image number")
    ax.set_ylabel("valid nodes (%)")
    ax.set_ylim(0, 105)
    ax.set_title("honesty-gated validity (incremental mode)", fontsize=9)

    ax = fig.add_subplot(2, 1, 2)
    ax.axis("off")
    c = S5["calibration"]
    ax.text(0, 0.95, "\n".join([
        "Built-in calibration on the REAL 12x9 @ 3.5 mm donut-fiducial target",
        "  47/47 pairs detected (7/47 before the flat-field rung)",
        f"  stereo RMS {c['rms_stereo']:.3f} px | epipolar {c['epipolar']:.3f} px | {c['pairs_used']} pairs used",
        f"  fx0 {c['fx0']:.1f} vs vendor {c['vendor']['fx0']:.1f} ({c['d_fx0_pct']:+.2f}%)",
        f"  fx1 {c['fx1']:.1f} vs vendor {c['vendor']['fx1']:.1f} ({c['d_fx1_pct']:+.2f}%)",
        f"  stereo angle {c['angle_deg']:.2f} vs vendor {c['vendor']['angle_y_deg']:.2f} deg",
        f"  Tx {c['T_mm'][0]:.2f} vs vendor {c['vendor']['tx_mm']:.2f} mm",
        "",
        f"DIC: 54 frames incremental (gate widened to 1.5 for ~11% strain), {S5['wall_s']:.0f} s",
        f"  strain noise floor {S5['noise_floor_exx_std']*1e6:.0f} ue | final exx {S5['exx_final']*100:.1f}% at 2070 lb",
        "  fracture occurred right after the last archived frame (load log: 5 lb at count 1110)",
    ]), va="top", family="monospace", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    pdf.savefig(fig)
    plt.close(fig)


def page_c2(pdf: PdfPages) -> None:
    fig = _fig("Challenge 2.0 Task 1 (elastic) - cross-code parity vs DICe")
    frames = sorted(int(k) for k in C2["vs_dice"])
    ax = fig.add_subplot(2, 2, 1)
    ax.plot(frames, [C2["vs_dice"][str(f)]["dx"]["med_px"] for f in frames], "o-", label="|ddx|")
    ax.plot(frames, [C2["vs_dice"][str(f)]["dy"]["med_px"] for f in frames], "s-", label="|ddy|")
    ax.set_xlabel("frame")
    ax.set_ylabel("median |diff| (px)")
    ax.set_title("pixel-displacement diff vs DICe (11300 pts)", fontsize=9)
    ax.legend(fontsize=8)

    ax = fig.add_subplot(2, 2, 2)
    fr_all = sorted(int(k) for k in C2["eyy_med"] if C2["eyy_med"][k] is not None)
    ax.plot(fr_all, [C2["eyy_med"][str(f)] * 100 for f in fr_all], "o-")
    ax.axhline(0.26, color="k", ls="--", lw=0.8, label="protocol anchor 0.26% @ 50")
    ax.set_xlabel("frame")
    ax.set_ylabel("median eyy (%)")
    ax.set_title("elastic strain ramp", fontsize=9)
    ax.legend(fontsize=8)

    ax = fig.add_subplot(2, 1, 2)
    ax.axis("off")
    ax.text(0, 0.9, "\n".join([
        "Scope: Task-1 elastic series with the provided 123.caldat (MatchID import),",
        "ROI = DICe's own support, accumulative, winsize 24 / step 8, "
        f"{C2['wall_s']:.0f} s for 14 frames.",
        f"eyy noise floor (frames 1-5): {C2['noise']['eyy_std']*1e6:.0f} ue.",
        "Deferred to a dedicated deliverable: the full official protocol - 5 VSG sizes,",
        "strains at every pixel, the 3-point standard coordinate system, DICData [n,11]",
        ".mat exports, the RBM zero-strain series and the necking window (3892-3909).",
    ]), va="top", family="monospace", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    pdf.savefig(fig)
    plt.close(fig)


def main() -> None:
    with PdfPages(PDF) as pdf:
        page_title(pdf)
        page_s2(pdf)
        page_s4(pdf)
        page_s5(pdf)
        page_c2(pdf)
    print(f"wrote {PDF}")


if __name__ == "__main__":
    main()
