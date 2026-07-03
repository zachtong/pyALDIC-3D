"""Generate ``reports/phase3_strain.pdf`` — Phase-3 surface-strain validation.

Pages: analytic gate (rigid rotation -> 0; uniaxial stretch on plane/cylinder ->
known strain), strain maps on the synthetic non-planar surface (recovered vs the
ground-truth-displacement strain), and a VSG-size sensitivity study (RMS strain
error vs virtual-strain-gauge size on a noisy strain-gradient field — the classic
noise-vs-blur U-curve).

Self-verifying: exits non-zero if the analytic gate fails.

Run:  python tools/phase3_report.py
"""
# ruff: noqa: E402, E501, E702, B905  (report script: sys.path setup, long strings, compact plotting)

from __future__ import annotations

import sys
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
from al_dic_3d.matching.contracts import TRACKED
from al_dic_3d.reconstruct import Reconstruction3D
from al_dic_3d.runner import load_config, run_pipeline
from al_dic_3d.strain3d import compute_surface_strain

Z0 = 800.0
EPS = 0.02


def _recon(ref_3d, disp1):
    points = np.stack([ref_3d, ref_3d + disp1])
    return Reconstruction3D(points, points - points[0][None], np.zeros(points.shape[:2]),
                            np.full(points.shape[:2], TRACKED, np.uint8))


def _grid(nx=19, ny=19, step_px=16.0, step_mm=2.0):
    ii, jj = np.meshgrid(np.arange(nx), np.arange(ny))
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * step_px + 40.0, jj * step_px + 40.0])
    xw = (ii - (nx - 1) / 2.0) * step_mm
    yw = (jj - (ny - 1) / 2.0) * step_mm
    interior = (ii >= 3) & (ii <= nx - 4) & (jj >= 3) & (jj <= ny - 4)
    return ref_2d, xw, yw, interior


def _analytic_validation():
    ref_2d, xw, yw, interior = _grid()
    flat = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    expected = EPS + 0.5 * EPS**2

    # rigid rotation -> zero strain
    th = np.deg2rad(8.0)
    rot = np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1.0]])
    s_rot = compute_surface_strain(_recon(flat, flat @ rot.T - flat), ref_2d, strain_size=5, winstepsize=16)
    rot_max = max(np.nanmax(np.abs(getattr(s_rot, c)[1][interior])) for c in ("exx", "eyy", "exy"))

    # uniaxial stretch on a plane
    disp = np.column_stack([EPS * xw, np.zeros_like(xw), np.zeros_like(xw)])
    s_pl = compute_surface_strain(_recon(flat, disp), ref_2d, strain_size=5, winstepsize=16)
    plane_err = float(np.nanmax(np.abs(s_pl.exx[1][interior] - expected)))

    # axial stretch on a cylinder (about world Y)
    r_cyl = 400.0
    theta = xw / r_cyl
    cyl = np.column_stack([r_cyl * np.sin(theta), yw, Z0 - r_cyl * (1 - np.cos(theta))])
    dz = np.column_stack([np.zeros_like(yw), EPS * yw, np.zeros_like(yw)])
    s_cy = compute_surface_strain(_recon(cyl, dz), ref_2d, strain_size=5, winstepsize=16)
    cyl_err = float(np.nanmedian(np.abs(s_cy.eyy[1][interior] - expected)))

    rows = [
        ("rigid rotation -> 0 strain", f"{rot_max:.2e}", "< 1e-9", rot_max < 1e-9),
        ("uniaxial plane exx", f"{np.nanmedian(s_pl.exx[1][interior]):.6f}", f"= {expected:.6f}", plane_err < 1e-6),
        ("uniaxial cylinder eyy", f"{np.nanmedian(s_cy.eyy[1][interior]):.6f}", f"~ {expected:.6f}", cyl_err < 0.02 * expected + 5e-5),
    ]
    return rows, all(r[3] for r in rows)


def _vsg_sensitivity():
    # Strain-gradient field + measurement noise: small VSG is noisy, large VSG blurs
    # the gradient -> RMS strain error is a U-curve in the VSG size.
    ref_2d, xw, yw, interior = _grid(nx=31, ny=31)
    flat = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    a, b = 0.01, 0.0009  # exx_true = a + 2 b X  (linear strain gradient)
    disp_u = a * xw + b * xw**2
    rng = np.random.default_rng(0)
    noise = rng.normal(0.0, 0.004, size=xw.shape)  # 4 um displacement noise
    disp = np.column_stack([disp_u + noise, np.zeros_like(xw), np.zeros_like(xw)])
    exx_true = (a + 2 * b * xw) + 0.5 * (a + 2 * b * xw) ** 2

    sizes = [3, 5, 7, 9, 11, 13, 15]
    vsg_len, rms = [], []
    for ssize in sizes:
        strain = compute_surface_strain(_recon(flat, disp), ref_2d, strain_size=ssize, winstepsize=16)
        err = strain.exx[1][interior] - exx_true[interior]
        rms.append(float(np.sqrt(np.nanmean(err**2))))
        vsg_len.append((ssize - 1) * 16 + 1)
    return np.array(vsg_len), np.array(rms), sizes


def _realistic(workdir):
    scene = ss.build_surface_scene(workdir, img=320, n_frames=5, deform=0.6, seed=7)
    cfg = load_config(ss.write_config(workdir, scene))
    result = run_pipeline(replace(cfg, compute_strain=True, strain_size=7))
    gt = ss.gt_tracks(scene, result.ref_coords)
    gt_world = gt["world"]
    gt_rec = Reconstruction3D(gt_world, gt_world - gt_world[0][None],
                              np.zeros(gt_world.shape[:2]), np.full(gt_world.shape[:2], TRACKED, np.uint8))
    gt_strain = compute_surface_strain(gt_rec, result.ref_coords, strain_size=7, winstepsize=16)
    return result, gt_strain


# --- pages -------------------------------------------------------------------


def _page_summary(pdf, rows, passed):
    fig = plt.figure(figsize=(8.5, 11))
    fig.suptitle("pyALDIC-3D - Phase 3: 3D Surface Strain Validation", fontsize=14, y=0.96)
    fig.text(0.08, 0.88,
             f"al_dic_3d {__version__}   |   Green-Lagrange strain in the local tangent frame\n"
             "Local neighbourhood plane fit -> tangent-frame displacement gradients -> E = (FᵀF−I)/2\n"
             "(docs/strain3d_math.md; ported from PlaneFit3_Quadtree.m + computeStrain3D.m).",
             fontsize=9.5, va="top")

    ax0 = fig.add_axes([0.08, 0.80, 0.84, 0.05]); ax0.axis("off")
    ax0.text(0.5, 0.5, "ANALYTIC GATE PASSED" if passed else "ANALYTIC GATE FAILED",
             ha="center", va="center", fontsize=18, fontweight="bold", color="white",
             bbox=dict(boxstyle="round,pad=0.5", fc=("#2e7d32" if passed else "#c62828"), ec="none"))

    ax = fig.add_axes([0.08, 0.50, 0.84, 0.26]); ax.axis("off")
    ax.set_title("Analytic-field validation (eps = 0.02)", fontsize=11, loc="left")
    cells = [[r[0], r[1], r[2], "PASS" if r[3] else "FAIL"] for r in rows]
    colors = [["#f5f5f5"] * 3 + ["#c8e6c9" if r[3] else "#ffcdd2"] for r in rows]
    t = ax.table(cellText=cells, colLabels=["test", "recovered", "expected", "result"],
                 cellColours=colors, colWidths=[0.42, 0.22, 0.20, 0.16], loc="upper center")
    t.auto_set_font_size(False); t.set_fontsize(9); t.scale(1, 1.6)

    fig.text(0.08, 0.44,
             "Green-Lagrange strain is rotation-invariant (rigid motion -> 0) and matches the\n"
             "closed-form uniaxial value eps + eps²/2 on both a flat plane and a curved cylinder\n"
             "(the tangent-frame plane fit handles curvature). MATLAB strainPerFrame parity is\n"
             "deferred with the other MATLAB-baseline gates until the user's dataset is provided.",
             fontsize=9.5, va="top", family="monospace")
    pdf.savefig(fig); plt.close(fig)


def _page_maps(pdf, result, gt_strain):
    st = result.strain
    nodes = result.ref_coords
    k = st.n_frames - 1
    fig, axes = plt.subplots(2, 3, figsize=(11, 7))
    fig.suptitle(f"Surface strain maps on the synthetic non-planar scene (frame {k})", fontsize=13)
    panels = [
        ("exx", st.exx[k], "RdBu_r"), ("eyy", st.eyy[k], "RdBu_r"), ("exy", st.exy[k], "RdBu_r"),
        ("von_mises", st.von_mises[k], "viridis"),
        ("exx error vs GT-disp", st.exx[k] - gt_strain.exx[k], "coolwarm"),
        ("|von_mises error|", np.abs(st.von_mises[k] - gt_strain.von_mises[k]), "magma"),
    ]
    for ax, (title, vals, cmap) in zip(axes.ravel(), panels):
        finite = np.isfinite(vals)
        sc = ax.scatter(nodes[finite, 0], nodes[finite, 1], c=vals[finite], s=12, cmap=cmap)
        ax.set_title(title, fontsize=10); ax.invert_yaxis(); ax.set_aspect("equal")
        fig.colorbar(sc, ax=ax, shrink=0.8)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig); plt.close(fig)


def _page_vsg(pdf, vsg_len, rms, sizes):
    fig, ax = plt.subplots(1, 1, figsize=(8.5, 5.5))
    fig.suptitle("VSG-size sensitivity (noise vs blur trade-off)", fontsize=13)
    ax.plot(vsg_len, rms * 1000, "-o", color="#1565c0")
    best = int(np.argmin(rms))
    ax.plot(vsg_len[best], rms[best] * 1000, "o", ms=12, mfc="none", mec="#c62828", mew=2,
            label=f"optimum: strain_size={sizes[best]} (VSG={vsg_len[best]}px)")
    ax.set_xlabel("VSG size (px)"); ax.set_ylabel("RMS exx error (x1e-3 strain)")
    ax.set_title("noisy linear strain-gradient field: small VSG = noise, large VSG = blur")
    ax.grid(alpha=0.3); ax.legend(fontsize=9)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig); plt.close(fig)


def _page_notes(pdf):
    fig = plt.figure(figsize=(8.5, 11))
    fig.suptitle("Method, limitations & scope", fontsize=13, y=0.96)
    fig.text(0.07, 0.88,
             "METHOD\n"
             "  - Per node: square (Chebyshev) VSG neighbourhood in the reference image; plane fit on\n"
             "    the reference 3D coords -> local tangent frame; plain least-squares in-plane\n"
             "    displacement gradients; F = I + grad^T; E = (F^T F - I)/2; principal/shear/vonMises.\n\n"
             "VALIDATION\n"
             "  - Analytic gate (this report): rigid rotation -> 0; uniaxial stretch on plane and\n"
             "    cylinder -> eps + eps^2/2. VSG sensitivity: RMS error is a U-curve in gauge size.\n"
             "  - MATLAB strainPerFrame parity is deferred (needs the user's dataset), like the P1/P2\n"
             "    MATLAB-baseline gates.\n\n"
             "LIMITATIONS\n"
             "  - Single connected ROI (MATLAB's per-region bwconncomp split is deferred).\n"
             "  - Void nodes (< 9 neighbours) report NaN (MATLAB fills 0); near-vertical facets make\n"
             "    the [1,0,0]-seeded tangent x-axis ill-conditioned (not expected on a DIC surface).\n"
             "  - Optional displacement smoothing + specimen-frame transform provided; default off.\n",
             fontsize=10, va="top", family="monospace")
    pdf.savefig(fig); plt.close(fig)


def main() -> int:
    import tempfile

    print("analytic validation...")
    rows, passed = _analytic_validation()
    print("VSG sensitivity...")
    vsg_len, rms, sizes = _vsg_sensitivity()
    print("realistic non-planar strain maps...")
    workdir = Path(tempfile.mkdtemp(prefix="aldic3d_phase3_"))
    result, gt_strain = _realistic(workdir)

    out = REPO / "reports"; out.mkdir(exist_ok=True)
    pdf_path = out / "phase3_strain.pdf"
    with PdfPages(pdf_path) as pdf:
        _page_summary(pdf, rows, passed)
        _page_maps(pdf, result, gt_strain)
        _page_vsg(pdf, vsg_len, rms, sizes)
        _page_notes(pdf)

    print(f"wrote {pdf_path}")
    for r in rows:
        print(f"  [{'PASS' if r[3] else 'FAIL'}] {r[0]}: {r[1]} (expect {r[2]})")
    print(f"  VSG optimum: strain_size={sizes[int(np.argmin(rms))]} (RMS {rms.min() * 1000:.3f}e-3)")
    if not passed:
        print("PHASE-3 ANALYTIC GATE FAILED", file=sys.stderr)
        return 1
    print("PHASE-3 ANALYTIC GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
