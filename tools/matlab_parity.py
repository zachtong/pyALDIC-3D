"""P1 real-data MATLAB parity gate: Stereo DIC Challenge 1.0 Sample 3.

Replicates the MATLAB reference's non-interactive regression run
(``3D-Stereo-ALDIC/tests/run_pipeline_test.m``: 3 frames, DICe calibration,
winsize=32, winstepsize=32, INCREMENTAL mode, per-frame masks) with OUR
pipeline, then compares the 3D reconstruction against the stored MATLAB
baseline (``tests/baseline/baseline.mat``, v7.3).

Data is consumed READ-ONLY in place. The baseline, the right camera, the masks
and the calibration live in the MATLAB reference repo (the documented sibling
``../3D-Stereo-ALDIC``). The left frames are not in its working tree; they are
read from the D-specimen dataset under the data root (--data-root DIR, else
$ALDIC3D_DATA_ROOT, else the repo's examples/ folder), first layout that has
them wins:

    example2_Ch1.0_S3_D_specimen_tensile/images/left/          curated examples/
    StereoDIC_Challenge_1/StereoSample3_D_Specimen_Experimental/Images_All/

Each left frame is checked against the SHA-256 of the copy the baseline was
produced from, so a different D-specimen copy fails loudly instead of
producing a wrong gate.

Comparison: both meshes sample the same physical surface, so fields are
compared as functions of the frame-1 world (X, Y): the MATLAB per-frame
U/V/W and Z are interpolated (Delaunay-linear) at OUR frame-1 (X, Y) and
differenced on the common support.

Run:  python tools/matlab_parity.py [--data-root DIR]
      (PARITY_MODE=accumulative|incremental, PARITY_GLOBAL=0|1 as before)
Exit: 0 gates passed, 1 a gate failed, 2 input data missing.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import time
from pathlib import Path
from typing import NoReturn

import numpy as np

REPO = Path(__file__).resolve().parents[1]
CODES = REPO.parent
ML = CODES / "3D-Stereo-ALDIC"
S3 = ML / "examples" / "Stereo_DIC_Challenge_1.0_S3"
BASELINE = ML / "tests" / "baseline" / "baseline.mat"
DATA_ROOT_ENV = "ALDIC3D_DATA_ROOT"

# The three parity frames are named 0000/0001/0002 but are NOT consecutive:
# verified by checksum against the full 34-frame D-specimen sequence in
# examples/example2_Ch1.0_S3_D_specimen_tensile/, they are frames 0, 7 and 14.
# The real inter-frame spacing is therefore 7, and each "step" carries ~7x the
# displacement a consecutive reading would imply — size search ranges
# accordingly, and do not treat this as a small-increment test.
PARITY_SOURCE_FRAMES = (0, 7, 14)

# Where the D-specimen left frames sit under the data root: the curated
# examples/ layout first, then the original Challenge 1.0 distribution.
LEFT_LAYOUTS = (
    Path("example2_Ch1.0_S3_D_specimen_tensile") / "images" / "left",
    Path("StereoDIC_Challenge_1") / "StereoSample3_D_Specimen_Experimental" / "Images_All",
)

# SHA-256 of the left frames the MATLAB baseline was produced from (the former
# 3D_ALDIC_unused L/0000..0002_0.tif), keyed by source frame. Both layouts
# above hold byte-identical copies (verified 2026-09-13).
PARITY_LEFT_SHA256 = {
    0: "c541a096b7f587f45e70ab0076aa9f4bffd1e2d12c2db6c3f0b224263b37f75f",
    7: "13b190da8512fdff476aad48471370464a861514c51f7df0491a62077b85f6fd",
    14: "f31649384410d1eed98dbbb0e7d1e5da390e9dac027881829b99b46364bd81c3",
}

sys.path.insert(0, str(REPO / "src"))


def _data_error(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def resolve_data_root(cli_root: str | None = None) -> tuple[Path, str]:
    """``--data-root`` wins over ``$ALDIC3D_DATA_ROOT``, which wins over examples/."""
    if cli_root:
        return Path(cli_root).expanduser(), "--data-root"
    if os.environ.get(DATA_ROOT_ENV):
        return Path(os.environ[DATA_ROOT_ENV]).expanduser(), DATA_ROOT_ENV
    return REPO / "examples", "default: the repo's examples/ folder"


def left_frame_paths(cli_root: str | None = None) -> list[Path]:
    """The three LEFT parity frames (source frames 0, 7, 14), checksum-verified.

    Exits with status 2 and a clear message when they are missing or differ
    from the frames the MATLAB baseline was produced from.
    """
    root, origin = resolve_data_root(cli_root)
    names = [f"{k:04d}_0.tif" for k in PARITY_SOURCE_FRAMES]
    looked = []
    for rel in LEFT_LAYOUTS:
        folder = root / rel
        paths = [folder / name for name in names]
        missing = [p.name for p in paths if not p.is_file()]
        if missing:
            state = "missing " + ", ".join(missing) if folder.is_dir() else "folder does not exist"
            looked.append(f"  {folder}  ({state})")
            continue
        for k, p in zip(PARITY_SOURCE_FRAMES, paths, strict=True):
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if digest != PARITY_LEFT_SHA256[k]:
                _data_error(
                    f"{p} is not the parity frame {k} the MATLAB baseline was made from "
                    f"(sha256 {digest[:12]}..., expected {PARITY_LEFT_SHA256[k][:12]}...)"
                )
        return paths
    _data_error(
        f"the D-specimen left frames {', '.join(names)} were not found under the data root "
        f"{root} ({origin}). Looked in:\n" + "\n".join(looked) + "\n"
        f"Point --data-root (or {DATA_ROOT_ENV}) at the folder that holds them "
        "(examples/README.md, example2)."
    )


def stage_left_frames(left_files: list[Path], work: Path) -> list[Path]:
    """Copy the parity frames into ``work`` under the numbers the baseline used.

    The sources are frames 0, 7 and 14 of the D-specimen sequence, but the
    MATLAB reference's right frames and masks are numbered 0000..0002, and the
    stereo sequence check pairs the cameras by that number (a left 0007_0 next
    to a right 0001_1 is refused as a name-pattern mismatch). The copies take
    the reference's numbers; the dataset itself is only read.
    """
    folder = work / "left"
    folder.mkdir(parents=True, exist_ok=True)
    staged = []
    for i, src in enumerate(left_files):
        dst = folder / f"{i:04d}_0.tif"
        shutil.copyfile(src, dst)
        staged.append(dst)
    return staged


def load_baseline() -> dict:
    """baseline.mat -> {'coords': [f][axis] arrays, 'disp': ..., 'reproj': (3,)}.

    v7.3/h5py note: MATLAB cell {frame, axis} appears transposed as [axis, frame].
    """
    try:
        import h5py
    except ImportError:
        _data_error(
            "reading the MATLAB baseline (a v7.3 MAT file) needs h5py: "
            'pip install h5py (it is part of the "dev" extra)'
        )

    out: dict = {"coords": [], "disp": []}
    with h5py.File(BASELINE, "r") as f:
        for frame in range(3):
            c = [np.array(f[f["Coordinates"][ax, frame]]).ravel() for ax in range(3)]
            d = [np.array(f[f["Displacement"][ax, frame]]).ravel() for ax in range(3)]
            out["coords"].append(np.column_stack(c))
            out["disp"].append(np.column_stack(d))
        out["reproj"] = np.array(f["reprojErr_mean"]).ravel()
    return out


def build_config(work: Path, left_files: list[Path], mode: str = "incremental") -> Path:
    """Write the parity config.toml replicating run_pipeline_test.m parameters."""
    import cv2

    mask = cv2.imread(str(S3 / "Images_Stereo_Sample3_maskfiles" / "Left" / "0000_0.tif"), 0)
    ys, xs = np.nonzero(mask > 0)
    roi = (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))

    def q(p: Path) -> str:
        return str(p).replace("\\", "/")

    # An explicit list in frame order (source frames 0, 7, 14, staged as
    # 0000..0002 by stage_left_frames), paired with the Right/*_1.tif and
    # mask globs below.
    left = ", ".join(f'"{q(p)}"' for p in left_files)
    cfg = f"""
[calibration]
file = "{q(S3 / "calibration_DICe.xml")}"
format = "dice"

[sequence]
left = [{left}]
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
use_global_step = {"true" if os.environ.get("PARITY_GLOBAL", "1") != "0" else "false"}
fft_search = 60
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


def run_ours(work: Path, left_files: list[Path], mode: str = "incremental"):
    from al_dic_3d.runner import load_config, run_pipeline

    cfg = load_config(build_config(work, left_files, mode))

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
            if diff.size == 0:
                # e.g. the honesty gate invalidated the whole frame (frozen /
                # untrackable) — report NaN metrics instead of crashing.
                rows[name] = (float("nan"), float("nan"), 0, float("nan"), float("nan"))
                continue
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
        if z_diff.size == 0:
            z_diff = np.array([np.nan])
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="P1/P2 real-data MATLAB parity gate: Stereo DIC Challenge 1.0 Sample 3."
    )
    parser.add_argument(
        "--data-root",
        help=f"dataset root for the left frames (default: ${DATA_ROOT_ENV}, else examples/)",
    )
    args = parser.parse_args(argv)
    needed = (
        (BASELINE, "baseline.mat"),
        (S3 / "calibration_DICe.xml", "DICe calibration"),
        (S3 / "Images_Stereo_Sample3_images" / "Right", "right image set"),
        (S3 / "Images_Stereo_Sample3_maskfiles", "mask set"),
    )
    for p, what in needed:
        if not p.exists():
            print(
                f"missing {what}: {p}\n"
                f"The MATLAB reference repo is expected at {ML} (a sibling of this repo; "
                "clone github.com/zachtong/3D-Stereo-ALDIC there, see CLAUDE.md).",
                file=sys.stderr,
            )
            return 2
    left_files = left_frame_paths(args.data_root)
    work = REPO / "reports" / "parity_s3"
    work.mkdir(parents=True, exist_ok=True)
    left_files = stage_left_frames(left_files, work)

    print("running our pipeline on Challenge 1.0 S3 (3 frames, incremental, masks)...")
    print("left frames: " + ", ".join(str(p) for p in left_files))
    mode = os.environ.get("PARITY_MODE", "incremental")
    global_on = os.environ.get("PARITY_GLOBAL", "1") != "0"
    print(f"reference_mode = {mode}  |  AL global step = {'ON' if global_on else 'OFF'}")
    t0 = time.perf_counter()
    result = run_ours(work, left_files, mode)
    print(f"pipeline wall time: {time.perf_counter() - t0:.1f} s")
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

    if mode == "incremental":
        ok = _p2_template_gate(result, left_files) and ok
    return 0 if ok else 1


def _p2_template_gate(result, left_files: list[Path]) -> bool:
    """P2 gate (inc mode): frame-3 cumulative track vs template-matching truth.

    The MATLAB baseline for this frame is arbitrated invalid, so arbitration is
    fully independent: 80x80 template matching L0 -> L2 at scattered anchors,
    compared POINTWISE against our tracked left-camera shift at the nearest
    valid node (median support differs — a field-median comparison is a trap on
    this strongly non-uniform motion). Also asserts the honesty gate left a
    usable valid fraction rather than laundering the decorrelated regions.
    """
    import cv2
    from scipy.spatial import cKDTree

    L0 = cv2.imread(str(left_files[0]), 0).astype(np.float32)
    L2 = cv2.imread(str(left_files[2]), 0).astype(np.float32)
    h, w = L0.shape
    anchors = []
    for y in range(150, h - 150, 80):
        for x in range(250, w - 250, 120):
            tpl = L0[y - 40 : y + 40, x - 40 : x + 40]
            if tpl.std() < 8:
                continue
            res = cv2.matchTemplate(L2, tpl, cv2.TM_CCOEFF_NORMED)
            _mn, mx, _l, loc = cv2.minMaxLoc(res)
            if mx > 0.62:
                anchors.append((x, y, loc[0] + 40 - x, loc[1] + 40 - y))
    anc = np.asarray(anchors, dtype=np.float64)

    xL = np.asarray(result.correspondence.xL, dtype=np.float64)
    d = xL[2] - xL[0]
    fin = np.isfinite(d).all(axis=1)
    tree = cKDTree(xL[0][fin])
    dist, idx = tree.query(anc[:, :2], k=1)
    near = dist < 24
    diff = np.abs(d[fin][idx[near]] - anc[near, 2:4])
    med = np.median(diff, axis=0)
    n_pt = int(near.sum())
    checks = [
        (f"anchors with valid node nearby >= 10 (got {n_pt})", n_pt >= 10),
        (f"pointwise dx median <= 1.0 px (got {med[0]:.2f})", bool(med[0] <= 1.0)),
        (f"pointwise dy median <= 1.0 px (got {med[1]:.2f})", bool(med[1] <= 1.0)),
        (f"valid fraction frame 2 >= 20% (got {fin.mean():.0%})", bool(fin.mean() >= 0.2)),
    ]
    print()
    print("P2 INC-COMPOSITION GATE (frame 0->2 vs template-matching truth):")
    ok = True
    for name, good in checks:
        print(f"  [{'PASS' if good else 'FAIL'}] {name}")
        ok = ok and good
    print("P2 GATE " + ("PASSED" if ok else "FAILED"))
    return ok


if __name__ == "__main__":
    raise SystemExit(main())
