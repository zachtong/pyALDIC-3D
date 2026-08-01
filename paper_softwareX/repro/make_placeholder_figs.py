"""Generate PLACEHOLDER figure PDFs so the manuscript compiles before the real
figures exist.

Every figure of the pyALDIC-3D SoftwareX manuscript is produced by its own
``repro/figN_*.py`` script (see ``figs/README.md``). Until those scripts are
run against real data, this module emits a labelled grey placeholder PDF at each
expected path, carrying the figure's intended message and the data it needs, so
that ``pdflatex`` succeeds and the layout can be judged.

Figure numbers here match the order of appearance in the manuscript, so the
file name, the ``figs/README.md`` entry and the printed figure number agree.

Usage (from ``paper_softwareX/``)::

    python repro/make_placeholder_figs.py

The script NEVER overwrites a real figure: a target that already exists and is
not a placeholder (checked via the ``PLACEHOLDER`` marker written into the PDF)
is skipped.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper_style  # noqa: E402

FIGS = Path(__file__).resolve().parent.parent / "figs"

# (filename, figure size, short title, what the final figure must show, data needed)
SPEC = [
    (
        "fig1_architecture.pdf", (10.0, 5.6),
        "Fig. 1 - Architecture and data flow",
        "Left-to-right schematic: stereo image pairs + calibration -> pluggable\n"
        "correspondence strategy -> CorrespondenceSet isolation wall -> DLT\n"
        "triangulation -> 3D displacement -> plane-fit Green-Lagrange strain ->\n"
        "visualization/export. Qt-free compute core banded separately from the\n"
        "GUI/viz layer; al-dic 2D engine shown as a pinned external library.",
        "No data - schematic (repro/fig1_architecture.py).",
    ),
    (
        "fig2_calibration.pdf", (10.0, 5.0),
        "Fig. 2 - Built-in calibration and QC",
        "(a) Coded circular target with the three ring fiducials + detected dots.\n"
        "(b) Board-pose coverage and tilt range over the image frame.\n"
        "(c) Per-pair reprojection RMS bar chart with rejected pairs marked.\n"
        "(d) QC summary: stereo RMS, epipolar RMS, baseline, pairs used/total,\n"
        "pitch closure 7.0005 mm and the +0.06% baseline agreement with DICe.",
        "tools/calib_report.py on the author's real coded-target photo set.",
    ),
    (
        "fig3_geometry.pdf", (10.0, 4.6),
        "Fig. 3 - Stereo geometry and conventions",
        "(a) Two-camera rig, left camera = world frame (R=I, T=0), X_R = R X_L + T,\n"
        "epipolar line bounding the stereo search, DLT triangulation of a surface\n"
        "point; px in the image planes, mm in the world.\n"
        "(b) The three correspondence strategies as arrow diagrams over a frame grid.",
        "No data - schematic drawn to scale from the Sample 3 calibration\n"
        "(repro/fig3_geometry.py).",
    ),
    (
        "fig4_crack_aware.pdf", (10.0, 4.6),
        "Fig. 4 - Crack-aware stereo DIC",
        "Same frame, shared colour scale: (a) ROI with the thin barrier cut along\n"
        "the crack; (b) naive strain field smeared across the crack; (c) crack-aware\n"
        "field with cross-barrier neighbours excluded and the crack band blanked.\n"
        "Inset: eyy line profile across the crack for (b) and (c).",
        "Cracked-specimen stereo pair + two runs (barrier off / on).",
    ),
    (
        "fig5_honesty_gate.pdf", (10.0, 4.6),
        "Fig. 5 - Independent ZNSSD re-verification",
        "(a) Per-frame ZNSSD of the SHIPPED cumulative displacement for a healthy\n"
        "run (flat, low) and for a run whose warm start froze (rising past the\n"
        "threshold).  (b) The displacement fields at the flagged frame.\n"
        "(c) The per-frame validity ledger the GUI reports.",
        "tools/matlab_parity.py P2 gate output + a deliberately frozen-seed run.",
    ),
    (
        "fig6_gui.pdf", (10.0, 6.0),
        "Fig. 6 - Desktop GUI",
        "Screenshot of the three-column main window on a real stereo dataset, with\n"
        "callouts (i)/(ii)/(iii) for the left workflow sidebar, the centre canvas\n"
        "with ROI + W field overlay, and the right run/visualization sidebar;\n"
        "insets of the PyVista 3D View and the Strain Post-Processing window.",
        "tools/gui_screenshot.py offscreen capture + examples/Images_Stereo_Sample3.",
    ),
    (
        "fig7_validation.pdf", (10.0, 5.6),
        "Fig. 7 - MATLAB parity and Challenge validation",
        "(a-c) Node-wise scatter of pyALDIC-3D vs the MATLAB 3D-Stereo-ALDIC\n"
        "reference for U, V, W on Stereo-DIC Challenge Sample 3, with the fitted\n"
        "regression slope.  (d) Histogram of |diff| with the medians.\n"
        "(e) Challenge 2.0 Task 1 eyy vs the published anchor.",
        "tools/matlab_parity.py, tools/challenge_c2_task1.py, tools/challenge_s2.py.",
    ),
    (
        "fig8_scale.pdf", (10.0, 4.6),
        "Fig. 8 - Scale and performance",
        "(a) Peak RSS vs frame index for the 150 x 12 Mpx and 400 x 5 Mpx runs\n"
        "(lazy streaming keeps memory flat).  (b) Per-frame tracking time.\n"
        "(c) End-frame error vs frame index (no drift).  (d) Kernel speedups:\n"
        "strain 6.5-19x (agreement < 1e-9), verification 3.29x (bit-identical).",
        "tools/stress_synth.py logs + tools/bench_strain3d.py.",
    ),
]


def _is_placeholder(path: Path) -> bool:
    """True if the PDF was written by this script (PLACEHOLDER marker)."""
    try:
        head = path.read_bytes()
    except OSError:
        return False
    return b"PLACEHOLDER" in head[:200_000]


def main() -> None:
    paper_style.apply(base=13.0)
    FIGS.mkdir(parents=True, exist_ok=True)
    for name, size, title, message, data in SPEC:
        out = FIGS / name
        if out.exists() and not _is_placeholder(out):
            print(f"  keep (real figure) {name}")
            continue
        fig = plt.figure(figsize=size)
        fig.patch.set_facecolor("white")
        ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
        ax.set_facecolor("#f2f2f2")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_linestyle((0, (6, 4)))
            spine.set_linewidth(2.0)
            spine.set_color("#888888")
        ax.text(0.5, 0.88, "PLACEHOLDER", ha="center", va="center",
                fontsize=20, fontweight="bold", color="#b03030",
                transform=ax.transAxes)
        ax.text(0.5, 0.76, title, ha="center", va="center",
                fontsize=16, fontweight="bold", color="#222222",
                transform=ax.transAxes)
        ax.text(0.5, 0.46, message, ha="center", va="center",
                fontsize=12, color="#222222", linespacing=1.6,
                transform=ax.transAxes)
        ax.text(0.5, 0.10, f"Data / script: {data}", ha="center", va="center",
                fontsize=10.5, style="italic", color="#555555",
                transform=ax.transAxes)
        with PdfPages(out) as pdf:
            pdf.savefig(fig)
            pdf.infodict()["Subject"] = "PLACEHOLDER"
        plt.close(fig)
        print(f"  wrote placeholder {name}")


if __name__ == "__main__":
    main()
