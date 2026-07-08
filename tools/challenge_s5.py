"""Challenge 1.0 Sample 5 (experimental tension, system 2) validation.

A) Built-in dot-target calibration on Cal12x9-3.5mm (donut fiducials, close-up
   views never show the full board -> use an ENLARGED virtual grid with the
   fiducial triangle mid-grid; absolute lattice offset is absorbed by the board
   pose and does not affect the solve). Cross-check vs the vendor xlsx numbers.
B) 54-frame INCREMENTAL 3D-DIC (10 static noise-floor frames + 44 loading
   steps to ~10% strain, ~+320 px total; NCC vs frame 0 decays to ~0.4 so
   fixed-reference matching is not viable). Honesty gate widened to 1.5:
   the translation-only ZNSSD check inflates under legitimate 10% strain.
C) Median exx vs the synchronized load cell (Smp62.csv) — physics check.

Writes reports/challenge/s5.json.
"""

from __future__ import annotations

import glob
import json
import pickle
import time
from pathlib import Path

import cv2
import numpy as np

S5 = Path(
    r"C:/Users/13014/OneDrive - The University of Texas at Austin/Documents"
    r"/MATLABCodes/StereoDIC_Challenge_1/StereoSample5 - Experimental Tension"
)
OUT = Path(__file__).resolve().parents[1] / "reports" / "challenge"

# Vendor solution (Sample1CalibrationInfo.xlsx, recon 2026-07-07).
VENDOR = {"fx0": 12577.405, "fx1": 12584.015, "angle_y_deg": 27.622, "tx_mm": -86.494}


def calibrate() -> tuple[Path, dict]:
    from al_dic_3d.calibration.boards import CodedCircleGridSpec
    from al_dic_3d.calibration.detect import detect_board
    from al_dic_3d.calibration.report import to_opencv_yaml
    from al_dic_3d.calibration.solve import calibrate_stereo

    spec = CodedCircleGridSpec(
        cols=16, rows=13, spacing=3.5, fiducials=((4, 4), (7, 4), (7, 9))
    )
    lefts = sorted(glob.glob(str(S5 / "Cal12x9-3.5mm" / "*_0.tif")))
    rights = sorted(glob.glob(str(S5 / "Cal12x9-3.5mm" / "*_1.tif")))
    cache = OUT / "s5_detcache.pkl"
    if cache.exists():
        det_l, det_r = pickle.loads(cache.read_bytes())
    else:
        det_l = [detect_board(cv2.imread(f, 0), spec) for f in lefts]
        det_r = [detect_board(cv2.imread(f, 0), spec) for f in rights]
        cache.write_bytes(pickle.dumps((det_l, det_r)))
    ok_l = sum(d.ok for d in det_l)
    ok_r = sum(d.ok for d in det_r)
    print(f"detections: L {ok_l}/{len(det_l)}  R {ok_r}/{len(det_r)}")

    img0 = cv2.imread(lefts[0], 0)
    h, w = img0.shape
    res = calibrate_stereo(det_l, det_r, (w, h), dot_radius_mm=0.875)  # ~d/2 = pitch/4
    rig = res.rig
    L, R = rig.cameras["L"], rig.cameras["R"]
    Rm, T = rig.pose("R")
    ang = np.degrees(np.arccos(np.clip((np.trace(Rm) - 1) / 2, -1, 1)))
    stats = {
        "rms_stereo": float(res.rms),
        "epipolar": float(res.epipolar_rms),
        "pairs_used": res.n_pairs_used,
        "fx0": L.fx,
        "fx1": R.fx,
        "angle_deg": float(ang),
        "T_mm": T.tolist(),
        "baseline_mm": float(np.linalg.norm(T)),
        "vendor": VENDOR,
        "d_fx0_pct": 100 * (L.fx / VENDOR["fx0"] - 1),
        "d_fx1_pct": 100 * (R.fx / VENDOR["fx1"] - 1),
        "d_angle_deg": float(ang) - VENDOR["angle_y_deg"],
    }
    print(
        f"OURS: rms {res.rms:.3f} px | fx0 {L.fx:.1f} ({stats['d_fx0_pct']:+.2f}%) "
        f"fx1 {R.fx:.1f} ({stats['d_fx1_pct']:+.2f}%) | angle {ang:.2f} deg "
        f"(vendor {VENDOR['angle_y_deg']}) | Tx {T[0]:.2f} (vendor {VENDOR['tx_mm']})"
    )
    yaml_path = OUT / "s5_calib_ours.yaml"
    to_opencv_yaml(rig, yaml_path)
    return yaml_path, stats


def estimate_disparity(l0: np.ndarray, r0: np.ndarray) -> tuple[float, float]:
    hits = []
    for (x, y) in ((600, 1000), (1200, 1050), (1900, 1100)):
        tpl = l0[y - 60 : y + 60, x - 60 : x + 60].astype(np.float32)
        res = cv2.matchTemplate(r0.astype(np.float32), tpl, cv2.TM_CCOEFF_NORMED)
        _mn, mx, _l, loc = cv2.minMaxLoc(res)
        if mx > 0.45:
            hits.append((loc[0] + 60 - x, loc[1] + 60 - y))
    arr = np.asarray(hits, dtype=np.float64)
    return float(np.median(arr[:, 0])), float(np.median(arr[:, 1]))


def main() -> None:
    from al_dic_3d.runner import RunConfig, run_pipeline

    OUT.mkdir(parents=True, exist_ok=True)
    yaml_path, calib_stats = calibrate()

    lefts = sorted(glob.glob(str(S5 / "StereoTensile" / "*_0.tif")))
    rights = sorted(glob.glob(str(S5 / "StereoTensile" / "*_1.tif")))
    l0 = cv2.imread(lefts[0], 0)
    r0 = cv2.imread(rights[0], 0)
    offset = estimate_disparity(l0, r0)
    print(f"disparity prior ({offset[0]:+.0f}, {offset[1]:+.0f}) px")

    cfg = RunConfig(
        calibration_file=yaml_path,
        calibration_format="opencv_yaml",
        left=lefts,
        right=rights,
        roi=(80, 2380, 700, 1400),  # gauge band interior
        strategy="track_both",
        reference_mode="incremental",
        winsize=32,
        winstepsize=16,
        stereo_search=80,
        disparity_offset=offset,
        fft_search=60,
        temporal_gate_znssd=1.5,  # translation-only check under ~10% strain
        compute_strain=True,
        output_dir=OUT / "s5_run",
        output_prefix="s5",
    )
    t0 = time.perf_counter()

    def prog(f: float, m: str) -> None:
        if int(f * 100) % 20 == 0:
            print(f"  [{f * 100:5.1f}%] {m}", flush=True)

    res = run_pipeline(cfg, progress=prog)
    wall = time.perf_counter() - t0
    print(f"pipeline wall {wall:.0f} s")

    # exx per frame vs load (Smp62.csv count == image number).
    frames = [int(Path(f).stem.split("-")[-1].split("_")[0]) for f in lefts]
    loads = {}
    for line in (S5 / "Smp62.csv").read_text().splitlines()[1:]:
        parts = line.split(",")
        try:
            loads[int(parts[0])] = float(parts[-1])
        except (ValueError, IndexError):
            continue

    exx = res.strain.exx  # (n_frames, n_pts)
    valid_frac, exx_med, load_lb = [], [], []
    for k, fr in enumerate(frames):
        e = exx[k]
        fin = np.isfinite(e)
        valid_frac.append(float(fin.mean()))
        exx_med.append(float(np.median(e[fin])) if fin.any() else float("nan"))
        load_lb.append(loads.get(fr, float("nan")))
    noise = [e for e, f in zip(exx_med, frames, strict=True) if f <= 9]
    out = {
        "calibration": calib_stats,
        "wall_s": wall,
        "frames": frames,
        "exx_med": exx_med,
        "load_lb": load_lb,
        "valid_frac": valid_frac,
        "noise_floor_exx_std": float(np.std(noise)),
        "exx_final": exx_med[-1],
    }
    (OUT / "s5.json").write_text(json.dumps(out, indent=1))
    print(f"noise-floor exx std (10 static frames): {out['noise_floor_exx_std']:.2e}")
    print(f"final exx {out['exx_final']:.4f} at load {load_lb[-1]:.0f} lb; "
          f"valid frac last frame {valid_frac[-1]:.0%}")
    print("saved s5.json")


if __name__ == "__main__":
    main()
