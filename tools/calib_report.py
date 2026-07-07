"""Generate ``reports/calib_builtin.pdf`` — the D12 built-in calibration gate report.

Re-runs the synthetic parity gates live (chessboard + coded dot target), checks
the i18n contract, captures offscreen screenshots of both calibration dialogs,
and renders the annotated report. Self-verifying: exits non-zero if a gate
fails, so the PDF cannot claim green falsely.

Run:  python tools/calib_report.py
"""
# ruff: noqa: E402  (Qt/env setup before imports)

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from tests import synth_calib as sc

from al_dic_3d import __version__
from al_dic_3d.calibration import (
    ChessboardSpec,
    CodedCircleGridSpec,
    calibrate_stereo,
    detect_board,
    from_opencv_yaml,
    point_residuals,
    stability_jackknife,
    summarize,
    to_opencv_yaml,
)

SHOTS = REPO / "reports" / "gui_shots"
CHESS = ChessboardSpec(cols=9, rows=7, square_size=12.0)
CODED = CodedCircleGridSpec(cols=11, rows=9, spacing=12.0)


def _rot_err_deg(r_est, r_gt) -> float:
    return float(np.degrees(np.arccos(np.clip((np.trace(r_est @ r_gt.T) - 1) / 2, -1, 1))))


def _extent(spec):
    pitch = spec.square_size if isinstance(spec, ChessboardSpec) else spec.spacing
    return ((spec.cols - 1) * pitch, (spec.rows - 1) * pitch)


def _solve(spec, rig, **kw):
    poses = sc.board_poses(_extent(spec), n=18)
    lefts, rights = sc.render_stereo_set(spec, rig, poses)
    dl = [detect_board(im, spec) for im in lefts]
    dr = [detect_board(im, spec) for im in rights]
    res = calibrate_stereo(dl, dr, (sc.IMG_W, sc.IMG_H), **kw)
    return dl, dr, res, summarize(res, dl, dr, (sc.IMG_W, sc.IMG_H))


def _gates(rig, chess, coded, tmp: Path) -> list[tuple[str, bool, str]]:
    gates: list[tuple[str, bool, str]] = []
    gt_l = rig.cameras["L"]
    _r, t_gt = rig.pose("R")

    _dl, _dr, res, _stats = chess
    est = res.rig.cameras["L"]
    ok = (
        res.rms < 0.05
        and abs(est.fx - gt_l.fx) / gt_l.fx < 5e-4
        and abs(est.cx - gt_l.cx) < 0.5
        and abs(res.baseline - float(np.linalg.norm(t_gt))) < 0.05
        and _rot_err_deg(res.rig.pose("R")[0], rig.pose("R")[0]) < 0.05
        and res.n_pairs_used == 18
    )
    gates.append(
        (
            "Chessboard synthetic parity",
            ok,
            f"rms {res.rms:.3f}px, fx {abs(est.fx - gt_l.fx) / gt_l.fx * 100:.3f}%, "
            f"cx {abs(est.cx - gt_l.cx):.2f}px, pairs {res.n_pairs_used}/18",
        )
    )

    _dl2, _dr2, res_c, _stats2 = coded
    est_c = res_c.rig.cameras["L"]
    ok_c = (
        res_c.rms < 0.15
        and res_c.n_pairs_used == 18
        and abs(est_c.k1 - gt_l.k1) < 5e-3
        and abs(res_c.baseline - float(np.linalg.norm(t_gt))) < 0.1
    )
    gates.append(
        (
            "Coded dot target parity (ring fiducials)",
            ok_c,
            f"rms {res_c.rms:.3f}px, k1 {est_c.k1:+.4f} vs {gt_l.k1:+.3f}, "
            f"pairs {res_c.n_pairs_used}/18",
        )
    )

    path = to_opencv_yaml(res.rig, tmp / "gate.yml", meta={"rms_px": res.rms})
    back = from_opencv_yaml(path)
    rt = all(
        np.allclose(back.cameras[c].K, res.rig.cameras[c].K)
        and np.allclose(back.cameras[c].dist_coeffs, res.rig.cameras[c].dist_coeffs)
        for c in ("L", "R")
    ) and np.allclose(back.pose("R")[1], res.rig.pose("R")[1])
    gates.append(("opencv_yaml round-trip funnel", rt, "write -> from_opencv_yaml identical"))

    from al_dic_3d.i18n import TARGET_LOCALES, scan_tree, source_ts

    leaks = scan_tree(REPO / "src" / "al_dic_3d" / "gui")
    complete = all(
        source_ts(loc).exists()
        and 'type="unfinished"' not in source_ts(loc).read_text(encoding="utf-8")
        for loc in TARGET_LOCALES
    )
    gates.append(
        (
            "i18n scan clean + 8 locales 100%",
            not leaks and complete,
            f"{len(leaks)} leaks; catalogs complete={complete}",
        )
    )

    gates.append(
        (
            "Dialog screenshots (offscreen)",
            (SHOTS / "shot_calib_dialog.png").exists()
            and (SHOTS / "shot_manual_params.png").exists(),
            "calibration + manual dialogs rendered",
        )
    )
    return gates


def _screenshot_dialogs(imgdir: Path) -> None:
    """Offscreen shots of both dialogs, the calibrator populated with a solve."""
    from PySide6.QtCore import QCoreApplication

    from al_dic_3d.gui.app import create_app
    from al_dic_3d.gui.dialogs.calibration_dialog import CalibrationDialog
    from al_dic_3d.gui.dialogs.manual_params_dialog import ManualParamsDialog

    create_app([])
    SHOTS.mkdir(parents=True, exist_ok=True)

    dlg = CalibrationDialog()
    dlg.resize(1000, 700)
    dlg._files_l = sorted(str(p) for p in imgdir.glob("L_*.png"))
    dlg._files_r = sorted(str(p) for p in imgdir.glob("R_*.png"))
    dlg._refresh_table()
    dlg._start(recalibrate=False)
    if dlg._worker is not None:
        dlg._worker.wait(120_000)
        QCoreApplication.processEvents()
    dlg.show()
    dlg.grab().save(str(SHOTS / "shot_calib_dialog.png"))

    man = ManualParamsDialog()
    man.show()
    man.grab().save(str(SHOTS / "shot_manual_params.png"))


def main() -> int:
    import tempfile

    print("running synthetic gates (chessboard + coded target)...")
    rig = sc.make_rig()
    chess = _solve(CHESS, rig)
    coded = _solve(CODED, rig, dot_radius_mm=CODED.dot_mm / 2)

    print("stability jackknife (6 leave-25%-out recalibrations)...")
    dl_c, dr_c, res_chess, _st = chess
    stab = stability_jackknife(
        dl_c, dr_c, (sc.IMG_W, sc.IMG_H), res_chess, drop_fraction=0.25, n_samples=6, seed=1
    )
    residuals = point_residuals(res_chess, dl_c, dr_c)

    def _stability_gate() -> tuple[str, bool, str]:
        std_fx = stab.spread("fx")[0]
        std_base = stab.spread("baseline")[0]
        ok = std_fx / stab.reference["fx"] < 2e-3 and std_base < 0.2
        return (
            "Stability jackknife (leave-25%-out)",
            ok,
            f"std fx {std_fx:.3f}px, baseline {std_base:.4f}mm over "
            f"{len(stab.samples['fx'])} subsets",
        )

    print("rendering dialog screenshots...")
    with tempfile.TemporaryDirectory() as td:
        import cv2

        tmp = Path(td)
        poses = sc.board_poses(_extent(CHESS), n=8)
        lefts, rights = sc.render_stereo_set(CHESS, rig, poses)
        for k, (im_l, im_r) in enumerate(zip(lefts, rights, strict=True)):
            cv2.imwrite(str(tmp / f"L_{k:02d}.png"), np.clip(im_l * 256, 0, 65535).astype("u2"))
            cv2.imwrite(str(tmp / f"R_{k:02d}.png"), np.clip(im_r * 256, 0, 65535).astype("u2"))
        _screenshot_dialogs(tmp)
        gates = _gates(rig, chess, coded, tmp)
    gates.insert(4, _stability_gate())

    out = REPO / "reports"
    out.mkdir(exist_ok=True)
    pdf_path = out / "calib_builtin.pdf"
    _dl, _dr, res, stats = chess

    with PdfPages(pdf_path) as pdf:
        # page 1: gate summary
        fig = plt.figure(figsize=(8.5, 11))
        fig.suptitle("pyALDIC-3D - Built-in Stereo Calibration (D12)", fontsize=15, y=0.96)
        passed = all(ok for _n, ok, _d in gates)
        ax0 = fig.add_axes([0.08, 0.84, 0.84, 0.05])
        ax0.axis("off")
        ax0.text(
            0.5,
            0.5,
            "ALL GATES PASSED" if passed else "GATE FAILURES",
            ha="center",
            va="center",
            fontsize=18,
            fontweight="bold",
            color="white",
            bbox=dict(boxstyle="round,pad=0.5", fc=("#2e7d32" if passed else "#c62828"), ec="none"),
        )
        fig.text(
            0.08,
            0.78,
            f"al_dic_3d {__version__} - boards/detect/solve/report on pure OpenCV.\n"
            "Three entry modes: built-in calibrator (primary) / 6-format import / manual\n"
            "parameters - all converge on StereoRig -> opencv_yaml -> one QC funnel.",
            fontsize=9.5,
            va="top",
        )
        ax = fig.add_axes([0.06, 0.42, 0.88, 0.30])
        ax.axis("off")
        cells = [[n, "PASS" if ok else "FAIL", d] for n, ok, d in gates]
        colors = [["#f5f5f5", "#c8e6c9" if ok else "#ffcdd2", "#f5f5f5"] for _n, ok, _d in gates]
        table = ax.table(
            cellText=cells,
            colLabels=["gate", "result", "evidence"],
            cellColours=colors,
            colWidths=[0.34, 0.10, 0.56],
            loc="upper center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8.0)
        table.scale(1, 1.8)
        fig.text(
            0.08,
            0.36,
            "Solver defaults measured on analytic corners: zero-tangent (planar cx<->p1p2\n"
            "coupling amplifies noise ~3x), FIX_INTRINSIC stereo, rejection floor 1 px,\n"
            "eccentricity correction for dot targets. Real-target tuning follows once the\n"
            "user's coded-target photos are available.",
            fontsize=9,
            va="top",
            family="monospace",
        )
        pdf.savefig(fig)
        plt.close(fig)

        # page 2: per-pair QC + coverage
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
        fig.suptitle("Chessboard gate QC (18 synthetic pairs)", fontsize=13)
        pairs = [p for p in res.pairs]
        worst = [max(p.rms_left, p.rms_right) if p.n_common else 0.0 for p in pairs]
        axes[0, 0].bar(
            range(len(worst)),
            worst,
            color=["#6366f1" if p.used else "#dc2626" for p in pairs],
        )
        axes[0, 0].axhline(1.0, ls="--", c="orange", label="reject floor")
        axes[0, 0].set_title("worst-camera RMS per pair (px)")
        axes[0, 0].set_xlabel("pair")
        axes[0, 0].legend()

        pts = np.vstack([d.image_points for d in _dl if d.ok])
        h2, xe, ye = np.histogram2d(
            pts[:, 0], pts[:, 1], bins=8, range=[[0, sc.IMG_W], [0, sc.IMG_H]]
        )
        im = axes[0, 1].imshow(
            h2.T, origin="upper", extent=[0, sc.IMG_W, sc.IMG_H, 0], cmap="viridis"
        )
        axes[0, 1].set_title(f"left-sensor corner coverage ({stats['coverage_left']:.0%})")
        fig.colorbar(im, ax=axes[0, 1], shrink=0.8)

        tilts = [p.tilt_deg for p in pairs if p.used]
        dists = [p.distance for p in pairs if p.used]
        axes[1, 0].scatter(tilts, dists, c="#6366f1")
        axes[1, 0].set_xlabel("board tilt (deg)")
        axes[1, 0].set_ylabel("board distance (mm)")
        axes[1, 0].set_title("pose diversity")

        axes[1, 1].axis("off")
        gt_l = rig.cameras["L"]
        est = res.rig.cameras["L"]
        rows = [
            ("stereo RMS (px)", f"{res.rms:.4f}"),
            ("epipolar RMS (px)", f"{res.epipolar_rms:.4f}"),
            ("fx err", f"{abs(est.fx - gt_l.fx) / gt_l.fx * 100:.4f}%"),
            ("cx err (px)", f"{abs(est.cx - gt_l.cx):.3f}"),
            ("k1 est / true", f"{est.k1:+.4f} / {gt_l.k1:+.3f}"),
            ("baseline err (mm)", f"{abs(res.baseline - 104.5):.4f}"),
        ]
        t2 = axes[1, 1].table(cellText=rows, colWidths=[0.5, 0.4], loc="center")
        t2.auto_set_font_size(False)
        t2.set_fontsize(9)
        t2.scale(1, 1.6)
        axes[1, 1].set_title("recovered vs ground truth")
        fig.tight_layout(rect=(0, 0, 1, 0.95))
        pdf.savefig(fig)
        plt.close(fig)

        # page 3: residual scatter + stability spread (MMC-inspired QC)
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
        fig.suptitle("Residual structure + parameter stability", fontsize=13)
        for ax, cam in ((axes[0, 0], "L"), (axes[0, 1], "R")):
            r = residuals[cam]
            ax.scatter(r[:, 0], r[:, 1], s=2, alpha=0.4, c="#6366f1")
            mean_rad = float(np.sqrt((r**2).sum(axis=1)).mean())
            circle = plt.Circle(r.mean(axis=0), mean_rad, fill=False, color="red", ls="--", lw=1.2)
            ax.add_patch(circle)
            ax.axhline(0, c="0.6", lw=0.5)
            ax.axvline(0, c="0.6", lw=0.5)
            ax.set_aspect("equal")
            ax.set_title(f"{cam} residuals (n={len(r)}, mean |r| {mean_rad:.3f} px)")
            ax.set_xlabel("dx (px)")
            ax.set_ylabel("dy (px)")
        for ax, (kx, ky) in ((axes[1, 0], ("fx", "fy")), (axes[1, 1], ("cx", "cy"))):
            ax.scatter(stab.samples[kx], stab.samples[ky], c="#6366f1", label="subsets")
            ax.scatter(
                [stab.reference[kx]],
                [stab.reference[ky]],
                c="red",
                marker="x",
                s=80,
                label="full set",
            )
            ax.set_xlabel(f"{kx} (std {stab.spread(kx)[0]:.3f})")
            ax.set_ylabel(f"{ky} (std {stab.spread(ky)[0]:.3f})")
            ax.set_title(f"leave-{stab.n_dropped}-of-{stab.n_views}-out domain of solution")
            ax.legend(fontsize=8)
        fig.tight_layout(rect=(0, 0, 1, 0.95))
        pdf.savefig(fig)
        plt.close(fig)

        # pages 4+: dialog screenshots
        for name, title in (
            ("shot_calib_dialog.png", "Stereo Calibration dialog (populated by a live solve)"),
            ("shot_manual_params.png", "Manual Camera Parameters dialog (fallback entry)"),
        ):
            path = SHOTS / name
            if not path.exists():
                continue
            fig = plt.figure(figsize=(11, 8.5))
            fig.suptitle(title, fontsize=13, y=0.97)
            ax = fig.add_axes([0.03, 0.05, 0.94, 0.88])
            ax.imshow(plt.imread(str(path)))
            ax.axis("off")
            pdf.savefig(fig, dpi=150)
            plt.close(fig)

    print(f"wrote {pdf_path}")
    ok = True
    for name, good, detail in gates:
        print(f"  [{'PASS' if good else 'FAIL'}] {name}: {detail}")
        ok = ok and good
    print("D12 CALIBRATION GATES " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
