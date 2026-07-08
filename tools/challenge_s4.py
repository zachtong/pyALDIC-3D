"""Challenge 1.0 Sample 4 (simulated D-specimen tension) vs MatchID reference.

170 rendered stereo pairs, ~7% gauge strain, per-frame increment ~0.4 px
(accumulative mode is right: small consecutive steps keep warm-start seeds
valid and IC-GN's affine shape function absorbs the strain). No masks — the
ROI is set to MatchID's own region so fields compare point-for-point.
MatchIDResults = vendor output (sigma 2-9 um), a parity reference, not truth.

Writes reports/challenge/s4.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

S4 = Path(
    r"C:/Users/13014/OneDrive - The University of Texas at Austin/Documents"
    r"/MATLABCodes/StereoDIC_Challenge_1/StereoSample4 - Simulated D-Tension"
)
OUT = Path(__file__).resolve().parents[1] / "reports" / "challenge"
CHECK_FRAMES = (1, 50, 100, 169)


def load_grid(field: str, frame: int) -> np.ndarray:
    p = S4 / "MatchIDResults" / field / f"DSpecimenSim {frame:03d}_0.tif_{field}.csv"
    rows = [
        [float(v) for v in line.split(",") if v.strip() != ""]
        for line in p.read_text().splitlines()
        if line.strip()
    ]
    return np.asarray(rows, dtype=np.float64)


def main() -> None:
    from al_dic_3d.runner import RunConfig, run_pipeline

    OUT.mkdir(parents=True, exist_ok=True)
    cfg = RunConfig(
        calibration_file=S4 / "Calibration.csv",
        calibration_format="matchid",
        left=str(S4 / "SimulatedExp" / "*_0.tif"),
        right=str(S4 / "SimulatedExp" / "*_1.tif"),
        roi=(674, 1054, 476, 681),  # MatchID's ROI for point-for-point parity
        strategy="track_both",
        reference_mode="accumulative",
        winsize=24,
        winstepsize=8,
        stereo_search=60,
        fft_search=60,
        output_dir=OUT / "s4_run",
        output_prefix="s4",
    )
    t0 = time.perf_counter()

    def prog(f: float, m: str) -> None:
        if "frame" in m and int(f * 170) % 20 == 0:
            print(f"  [{f * 100:5.1f}%] {m}", flush=True)

    res = run_pipeline(cfg, progress=prog)
    wall = time.perf_counter() - t0
    print(f"pipeline wall: {wall:.0f} s")

    rec = res.reconstruction
    xL0 = np.asarray(res.correspondence.xL[0], dtype=np.float64)

    # MatchID grid pixel coordinates (step 5, ROI origin from recon).
    gx = load_grid("x_pic", 0)
    gy = load_grid("y_pic", 0)

    from scipy.interpolate import LinearNDInterpolator

    out = {"wall_s": wall, "frames": {}}
    for k in CHECK_FRAMES:
        d = np.asarray(rec.displacement[k], dtype=np.float64)
        fin = np.isfinite(d).all(axis=1) & np.isfinite(xL0).all(axis=1)
        sig = load_grid("sigma", k)
        valid_m = sig != 0.0
        row = {"valid_ours": int(fin.sum()), "valid_matchid": int(valid_m.sum())}
        for ax, name in enumerate(("u", "v", "w")):
            ref = load_grid(name, k)
            interp = LinearNDInterpolator(xL0[fin], d[fin, ax])
            ours_at = interp(gx[valid_m], gy[valid_m])
            good = np.isfinite(ours_at)
            diff = ours_at[good] - ref[valid_m][good]
            row[name] = {
                "med_um": float(np.median(np.abs(diff)) * 1000),
                "p95_um": float(np.percentile(np.abs(diff), 95) * 1000),
                "n": int(good.sum()),
                "matchid_med_mm": float(np.median(ref[valid_m])),
                "ours_med_mm": float(np.median(d[fin, ax])),
            }
        out["frames"][k] = row
        print(
            f"frame {k:3d}: |d(u,v,w)| med = "
            f"{row['u']['med_um']:6.1f} / {row['v']['med_um']:6.1f} / "
            f"{row['w']['med_um']:6.1f} um  (n={row['u']['n']}, "
            f"ours valid {row['valid_ours']})",
            flush=True,
        )

    (OUT / "s4.json").write_text(json.dumps(out, indent=1))
    print("saved s4.json")


if __name__ == "__main__":
    main()
