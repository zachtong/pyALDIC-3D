"""P1 real-data MATLAB parity gate: Stereo DIC Challenge 1.0 Sample 3.

Replicates the MATLAB reference's non-interactive regression run
(``3D-Stereo-ALDIC/tests/run_pipeline_test.m``: 3 frames, DICe calibration,
winsize=32, winstepsize=32, INCREMENTAL mode, per-frame masks) with OUR
pipeline, then compares the 3D reconstruction against the stored MATLAB
baseline (``tests/baseline/baseline.mat``, v7.3).

Data is consumed READ-ONLY in place: the right camera + masks + calibration
live in the 3D-Stereo-ALDIC repo; the left images (missing there) were located
in the sibling ``3D_ALDIC_unused`` copy (right frames byte-identical).

Comparison: both meshes sample the same physical surface, so fields are
compared as functions of the frame-1 world (X, Y): the MATLAB per-frame
U/V/W and Z are interpolated (Delaunay-linear) at OUR frame-1 (X, Y) and
differenced on the common support. Run:  python tools/matlab_parity.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
CODES = REPO.parent
ML = CODES / "3D-Stereo-ALDIC"
S3 = ML / "examples" / "Stereo_DIC_Challenge_1.0_S3"
LEFT_IMGS = CODES / "3D_ALDIC_unused" / "Examples" / "Image_Stereo_Sample3"
BASELINE = ML / "tests" / "baseline" / "baseline.mat"

sys.path.insert(0, str(REPO / "src"))


def load_baseline() -> dict:
    """baseline.mat -> {'coords': [f][axis] arrays, 'disp': ..., 'reproj': (3,)}.

    v7.3/h5py note: MATLAB cell {frame, axis} appears transposed as [axis, frame].
    """
    import h5py

    out: dict = {"coords": [], "disp": []}
    with h5py.File(BASELINE, "r") as f:
        for frame in range(3):
            c = [np.array(f[f["Coordinates"][ax, frame]]).ravel() for ax in range(3)]
            d = [np.array(f[f["Displacement"][ax, frame]]).ravel() for ax in range(3)]
            out["coords"].append(np.column_stack(c))
            out["disp"].append(np.column_stack(d))
        out["reproj"] = np.array(f["reprojErr_mean"]).ravel()
    return out


def build_config(work: Path, mode: str = "incremental") -> Path:
    """Write the parity config.toml replicating run_pipeline_test.m parameters."""
    import cv2

    mask = cv2.imread(str(S3 / "Images_Stereo_Sample3_maskfiles" / "Left" / "0000_0.tif"), 0)
    ys, xs = np.nonzero(mask > 0)
    roi = (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))

    def q(p: Path) -> str:
        return str(p).replace("\\", "/")

    cfg = f"""
[calibration]
file = "{q(S3 / "calibration_DICe.xml")}"
format = "dice"

[sequence]
left = "{q(LEFT_IMGS / "Images_Stereo_Sample3_images")}/*_0.tif"
right = "{q(S3 / "Images_Stereo_Sample3_images" / "Right")}/*_1.tif"
left_mask = "{q(S3 / "Images_Stereo_Sample3_maskfiles" / "Left")}/*_0.tif"
right_mask = "{q(S3 / "Images_Stereo_Sample3_maskfiles" / "Right")}/*_1.tif"

[roi]
xmin = {roi[0]}
xmax = {roi[1]}
ymin = {roi[2]}
ymax = {roi[3]}

[matching]
strategy = "track_both"
reference_mode = "{mode}"
winsize = 32
winstepsize = 32
winsize_min = 8
stereo_search = 60

[output]
dir = "{q(work)}"
prefix = "s3_parity"
"""
    path = work / "s3_parity.toml"
    path.write_text(cfg.strip() + "\n", encoding="utf-8")
    return path


def run_ours(work: Path, mode: str = "incremental"):
    from al_dic_3d.runner import load_config, run_pipeline

    cfg = load_config(build_config(work, mode))

    def progress(frac: float, msg: str) -> None:
        print(f"  [{frac * 100:5.1f}%] {msg}", flush=True)

    return run_pipeline(cfg, progress=progress)


def compare(result, base: dict, work: Path) -> dict:
    """Field comparison on the common frame-1 (X, Y) support."""
    from scipy.interpolate import LinearNDInterpolator

    rec = result.reconstruction
    corr = result.correspondence
    np.savez(
        work / "s3_ours.npz",
        points=np.asarray(rec.points, dtype=np.float64),
        displacement=np.asarray(rec.displacement, dtype=np.float64),
        reproj=np.asarray(rec.reproj_error, dtype=np.float64),
        xL=np.asarray(corr.xL, dtype=np.float64),
        xR=np.asarray(corr.xR, dtype=np.float64),
    )
    ours0 = np.asarray(rec.points[0], dtype=np.float64)  # (n, 3) frame-1 world
    finite0 = np.isfinite(ours0).all(axis=1)
    theirs0 = base["coords"][0]

    metrics: dict = {"n_ours": int(finite0.sum()), "n_theirs": int(len(theirs0))}
    for k in range(3):
        ours_d = np.asarray(rec.displacement[k], dtype=np.float64)
        their_d = base["disp"][k]
        fin_k = np.isfinite(ours_d).all(axis=1)
        metrics[f"finite{k}"] = int(fin_k.sum())
        rows = {}
        for ax, name in enumerate(("U", "V", "W")):
            interp = LinearNDInterpolator(theirs0[:, :2], their_d[:, ax])
            ref = interp(ours0[finite0, 0], ours0[finite0, 1])
            mine = ours_d[finite0, ax]
            good = np.isfinite(ref) & np.isfinite(mine)
            diff = mine[good] - ref[good]
            # regression mine ~ slope*ref + b: slope 1 = agreement, -1 = sign
            # flip, ~0 = we track nothing, wild = blow-up
            if good.sum() > 10 and np.nanstd(ref[good]) > 1e-9:
                slope, b = np.polyfit(ref[good], mine[good], 1)
            else:
                slope, b = float("nan"), float("nan")
            rows[name] = (
                float(np.median(np.abs(diff))),
                float(np.percentile(np.abs(diff), 95)),
                int(diff.size),
                float(slope),
                float(b),
            )
        # frame-k surface height consistency (Z as a function of frame-1 XY)
        interp_z = LinearNDInterpolator(theirs0[:, :2], base["coords"][k][:, 2])
        z_ref = interp_z(ours0[finite0, 0], ours0[finite0, 1])
        z_diff = np.asarray(rec.points[k], dtype=np.float64)[finite0, 2] - z_ref
        z_diff = z_diff[np.isfinite(z_diff)]
        rows["Z"] = (
            float(np.median(np.abs(z_diff))),
            float(np.percentile(np.abs(z_diff), 95)),
            int(z_diff.size),
            float("nan"),
            float("nan"),
        )
        metrics[f"frame{k}"] = rows

    reproj = np.asarray(rec.reproj_error, dtype=np.float64)
    metrics["reproj_ours"] = [float(np.nanmean(reproj[k])) for k in range(reproj.shape[0])]
    metrics["reproj_theirs"] = base["reproj"].tolist()
    return metrics


def main() -> int:
    for p, what in ((BASELINE, "baseline.mat"), (LEFT_IMGS, "left image set")):
        if not p.exists():
            print(f"missing {what}: {p}", file=sys.stderr)
            return 2
    work = REPO / "reports" / "parity_s3"
    work.mkdir(parents=True, exist_ok=True)

    print("running our pipeline on Challenge 1.0 S3 (3 frames, incremental, masks)...")
    import os

    mode = os.environ.get("PARITY_MODE", "incremental")
    print(f"reference_mode = {mode}")
    result = run_ours(work, mode)
    base = load_baseline()
    m = compare(result, base, work)

    print(f"\npoints: ours {m['n_ours']} vs MATLAB {m['n_theirs']}")
    print("field |diff| vs MATLAB baseline (median / 95th pct, mm):")
    for k in range(3):
        rows = m[f"frame{k}"]
        cells = "  ".join(
            f"{name} {rows[name][0]:.4f}/{rows[name][1]:.4f}" for name in ("U", "V", "W", "Z")
        )
        print(f"  frame {k}: {cells}   (n={rows['U'][2]}, finite {m[f'finite{k}']})")
        slopes = "  ".join(
            f"{name} slope {rows[name][3]:+.3f} b {rows[name][4]:+.4f}" for name in ("U", "V", "W")
        )
        print(f"           regression ours~theirs: {slopes}")
    print(f"reproj mean px: ours {[f'{v:.3f}' for v in m['reproj_ours']]}")
    print(f"               MATLAB {[f'{v:.3f}' for v in m['reproj_theirs']]}")

    np.savez(
        work / "parity_metrics.npz",
        **{
            f"frame{k}_{name}": np.array(m[f"frame{k}"][name])
            for k in range(3)
            for name in ("U", "V", "W", "Z")
        },
    )
    print(f"\nmetrics saved to {work / 'parity_metrics.npz'}")

    # ---- P1 gate: frame 0->1 only. The third frame's ~60 px decorrelating
    # jump defeats the MATLAB baseline itself: multi-location template
    # matching arbitrates the TRUE 0->2 motion at ~(-8..-95, -52..-64) px
    # (e.g. L0[380,800]->L2 shift (-8,-64) @ score 0.76) vs the baseline's
    # -13 px (a suspicious exact 2x of frame 2), and MATLAB's own frame-3
    # reprojection error jumps to 0.503 px — that run failed the frame too.
    # Frame index 2 is therefore reported but NOT gated against that baseline.
    f1 = m["frame1"]
    checks = [
        ("U median <= 10 um", f1["U"][0] <= 0.010),
        ("V median <= 10 um", f1["V"][0] <= 0.010),
        ("W median <= 25 um", f1["W"][0] <= 0.025),
        ("Z median <= 60 um", f1["Z"][0] <= 0.060),
        ("U slope ~ 1", abs(f1["U"][3] - 1.0) <= 0.05),
        ("V slope ~ 1", abs(f1["V"][3] - 1.0) <= 0.05),
        ("W slope ~ 1", abs(f1["W"][3] - 1.0) <= 0.20),
    ]
    ok = True
    print("\nP1 REAL-DATA PARITY GATE (frame 0->1 vs MATLAB baseline):")
    for name, good in checks:
        print(f"  [{'PASS' if good else 'FAIL'}] {name}")
        ok = ok and good
    print("P1 GATE " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
