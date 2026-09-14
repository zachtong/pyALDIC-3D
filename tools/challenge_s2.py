"""Challenge 1.0 Sample 2 (simulated rigid translations) validation.

18 rendered steps with EXACT imposed (X, Z) plate translations (+-10/20 mm,
Y=0); truth calibration shipped per rig (MatchID caldat). Each step is run as
an independent 2-frame pipeline (reference + step) so every step gets a fresh
FFT seed — consecutive steps jump up to 30 mm, which defeats warm-start
seeding, and accumulative multi-frame runs would freeze (the S3 lesson).

Data: the Stereo-DIC Challenge 1.0 distribution. Sample 2 is NOT part of the
curated examples/ collection (examples/README.md: example1 is Sample 1), so it
is looked up in its original layout under the data root:

    <data root>/StereoDIC_Challenge_1/StereoSample2 - Simulated/SimulatedTranslate/
        16mm/Calibration.csv, "16-mm Step NN_0.tif", "16-mm Step NN_1.tif"
        35mm/...

The data root is --data-root DIR, else $ALDIC3D_DATA_ROOT, else the repo's
examples/ folder.

Usage: python tools/challenge_s2.py [16mm|35mm] [--data-root DIR]   (default 16mm)
Writes reports/challenge/s2_<rig>.json (+ per-step medians npz).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
DATA_ROOT_ENV = "ALDIC3D_DATA_ROOT"
C1_REL = Path("StereoDIC_Challenge_1") / "StereoSample2 - Simulated" / "SimulatedTranslate"
RIGS = ("16mm", "35mm")
OUT = REPO / "reports" / "challenge"

# Imposed plate-frame translations (X, Z) mm; Y = 0 (GlobalDataStatistics.xlsx
# step labels, independently verified <30 um by LK+triangulation during recon).
TRUTH_XZ = {
    0: (0, 0), 1: (0, -10), 2: (0, -20), 3: (0, 10), 4: (0, 20),
    5: (10, 0), 6: (20, 0), 7: (-10, 0), 8: (-20, 0),
    9: (10, 10), 10: (20, 20), 11: (-10, -10), 12: (-20, -20),
    13: (10, -10), 14: (20, -20), 15: (-10, 10), 16: (-20, 20),
    17: (0, 0),
}


def find_dataset(
    cli_root: str | None, layouts: Sequence[tuple[Path, Sequence[str]]], what: str
) -> Path:
    """First ``<root>/<rel>`` holding every listed entry; else exit 2 with a clear message.

    The data root is ``cli_root`` (--data-root), else ``$ALDIC3D_DATA_ROOT``, else
    the repo's examples/ folder (layout: examples/README.md).
    """
    if cli_root:
        root, origin = Path(cli_root).expanduser(), "--data-root"
    elif os.environ.get(DATA_ROOT_ENV):
        root, origin = Path(os.environ[DATA_ROOT_ENV]).expanduser(), DATA_ROOT_ENV
    else:
        root, origin = REPO / "examples", "default: the repo's examples/ folder"
    report = []
    for rel, entries in layouts:
        base = root / rel
        missing = [e for e in entries if not (base / e).exists()]
        if not missing:
            return base
        state = "missing " + ", ".join(missing) if base.is_dir() else "folder does not exist"
        report.append(f"  {base}  ({state})")
    print(
        f"error: {what} not found under the data root {root} ({origin}). Looked for:\n"
        + "\n".join(report)
        + f"\nPoint --data-root (or {DATA_ROOT_ENV}) at the folder that holds it.",
        file=sys.stderr,
    )
    raise SystemExit(2)


def rig_prefix(rig: str) -> str:
    """File-name prefix of a rig's images: ``16mm`` -> ``16-mm``."""
    return rig.replace("mm", "-mm")


def estimate_disparity(folder: Path, prefix: str) -> tuple[float, float]:
    """Coarse full-image L->R template match: convergent rigs here run ~+-300 px
    disparity, far beyond any local search window — the false in-window locks
    this prevents triangulated 16% short on the 16mm rig."""
    import cv2

    def rd(name):
        img = cv2.imread(str(folder / name), cv2.IMREAD_UNCHANGED)
        return img[..., 0] if img.ndim == 3 else img

    L0 = rd(f"{prefix} Step 00_0.tif").astype("float32")
    R0 = rd(f"{prefix} Step 00_1.tif").astype("float32")
    hits = []
    for (x, y) in ((900, 800), (1300, 1000), (1600, 1300)):
        tpl = L0[y - 50 : y + 50, x - 50 : x + 50]
        res = cv2.matchTemplate(R0, tpl, cv2.TM_CCOEFF_NORMED)
        _mn, mx, _l, loc = cv2.minMaxLoc(res)
        if mx > 0.5:
            hits.append((loc[0] + 50 - x, loc[1] + 50 - y))
    if not hits:
        raise RuntimeError("disparity prior estimation failed (no NCC anchor > 0.5)")
    arr = np.asarray(hits, dtype=np.float64)
    return float(np.median(arr[:, 0])), float(np.median(arr[:, 1]))


def run_rig(rig: str, c1: Path) -> dict:
    """Run all 17 moving steps of one rig; ``c1`` is the SimulatedTranslate folder."""
    from al_dic_3d.runner import RunConfig, run_pipeline

    folder = c1 / rig
    prefix = rig_prefix(rig)
    calib = folder / "Calibration.csv"
    OUT.mkdir(parents=True, exist_ok=True)
    offset = estimate_disparity(folder, prefix)
    print(f"stereo disparity prior: ({offset[0]:+.0f}, {offset[1]:+.0f}) px")

    roi = (500, 1900, 500, 1500)  # central plate region, on-plate at max motion
    med = {}
    t0 = time.perf_counter()
    for step in range(1, 18):
        cfg = RunConfig(
            calibration_file=calib,
            calibration_format="matchid",
            left=[
                str(folder / f"{prefix} Step 00_0.tif"),
                str(folder / f"{prefix} Step {step:02d}_0.tif"),
            ],
            right=[
                str(folder / f"{prefix} Step 00_1.tif"),
                str(folder / f"{prefix} Step {step:02d}_1.tif"),
            ],
            roi=roi,
            strategy="track_both",
            reference_mode="accumulative",
            winsize=32,
            winstepsize=32,
            stereo_search=80,
            disparity_offset=offset,
            fft_search=420,
            output_dir=OUT / f"s2_{rig}_tmp",
            output_prefix=f"step{step:02d}",
        )
        res = run_pipeline(cfg)
        d = np.asarray(res.reconstruction.displacement[1], dtype=np.float64)
        fin = np.isfinite(d).all(axis=1)
        med[step] = {
            "U": float(np.median(d[fin, 0])),
            "V": float(np.median(d[fin, 1])),
            "W": float(np.median(d[fin, 2])),
            "std": [float(np.std(d[fin, k])) for k in range(3)],
            "valid": int(fin.sum()),
            "n": int(len(d)),
        }
        print(
            f"  step {step:02d}: med (U,V,W) = ({med[step]['U']:+8.4f}, "
            f"{med[step]['V']:+8.4f}, {med[step]['W']:+8.4f}) mm  "
            f"valid {fin.sum()}/{len(d)}",
            flush=True,
        )
    wall = time.perf_counter() - t0

    # Fit the single cam0->plate rotation (the rig is yawed ~+-10 deg about Y
    # and the challenge frame flips signs); solve Procrustes on the 16 moving
    # steps, then report per-step residual vs the exact truth.
    steps = [s for s in range(1, 17)]
    ours = np.array([[med[s]["U"], med[s]["V"], med[s]["W"]] for s in steps])
    tru = np.array([[TRUTH_XZ[s][0], 0.0, TRUTH_XZ[s][1]] for s in steps])
    Uu, _s, Vt = np.linalg.svd(ours.T @ tru)
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ Uu.T))])
    R = Vt.T @ D @ Uu.T  # ours -> truth frame (proper rotation, no scale)
    aligned = ours @ R.T
    resid = aligned - tru
    err = np.linalg.norm(resid, axis=1)

    out = {
        "rig": rig,
        "wall_s": wall,
        "per_step": med,
        "rotation_cam0_to_plate": R.tolist(),
        "aligned_mm": aligned.tolist(),
        "truth_mm": tru.tolist(),
        "err_mm": err.tolist(),
        "err_med_um": float(np.median(err) * 1000),
        "err_max_um": float(np.max(err) * 1000),
        "noise_floor_step17_med_mm": [med[17]["U"], med[17]["V"], med[17]["W"]],
        "noise_floor_step17_std_mm": med[17]["std"],
    }
    (OUT / f"s2_{rig}.json").write_text(json.dumps(out, indent=1))
    print(f"\n{rig}: |err| median {out['err_med_um']:.1f} um, max {out['err_max_um']:.1f} um "
          f"over 16 moving steps ({wall:.0f} s)")
    print(f"  noise floor (step 17): med {out['noise_floor_step17_med_mm']} mm, "
          f"std {out['noise_floor_step17_std_mm']} mm")
    print("  vendor bar (Group02 Sys1): u/v-std 0.011-0.017 mm, w-std 0.056-0.089 mm")
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Challenge 1.0 Sample 2 (simulated rigid translations) validation."
    )
    parser.add_argument("rig", nargs="?", default="16mm", choices=RIGS, help="rig (default 16mm)")
    parser.add_argument(
        "--data-root", help=f"dataset root (default: ${DATA_ROOT_ENV}, else the repo's examples/)"
    )
    args = parser.parse_args(argv)
    prefix = rig_prefix(args.rig)
    c1 = find_dataset(
        args.data_root,
        [(C1_REL, (f"{args.rig}/Calibration.csv", f"{args.rig}/{prefix} Step 00_0.tif"))],
        f"Stereo-DIC Challenge 1.0 Sample 2 ({args.rig} rig)",
    )
    run_rig(args.rig, c1)


if __name__ == "__main__":
    main()
