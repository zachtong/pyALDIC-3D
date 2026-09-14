"""Challenge 2.0 Task 1 (elastic series) — cross-code parity vs DICe.

Scope for the Phase-5 sweep: the elastic frames with the provided 123.caldat,
compared point-for-point against the shipped DICe solutions (Cam0 pixel
displacements — frame-convention-free) plus the protocol's two anchors:
frames 1-5 = zero-strain noise floor, frame 50 eyy = 0.26 %. The full official
protocol (5 VSG sizes, every-pixel export, standard coordinate system) is a
separate deliverable, deferred.

Data: the Stereo-DIC Challenge 2.0 distribution. It is NOT part of the curated
examples/ collection (examples/README.md: example4 is the same dogbone, but
without frame 50, 123.caldat and the DICe solutions), so it is looked up in its
original layout under the data root:

    <data root>/StereoDIC_Challenge_2/
        123.caldat
        Calculation Images/task1/Elastic/*_0.tif, *_1.tif
        Pre-comparion_matchid_ALDIC_DICe/Task1/DICe_results/DICe_solution_NN.txt

The data root is --data-root DIR, else $ALDIC3D_DATA_ROOT, else the repo's
examples/ folder.

Usage: python tools/challenge_c2_task1.py [--data-root DIR]
Writes reports/challenge/c2_task1.json.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parents[1]
DATA_ROOT_ENV = "ALDIC3D_DATA_ROOT"
C2_REL = Path("StereoDIC_Challenge_2")
ELASTIC_REL = Path("Calculation Images") / "task1" / "Elastic"
DICE_REL = Path("Pre-comparion_matchid_ALDIC_DICe") / "Task1" / "DICe_results"
CALIB_NAME = "123.caldat"
OUT = REPO / "reports" / "challenge"


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


def load_dice(dice_dir: Path, frame: int) -> dict[str, np.ndarray]:
    p = dice_dir / f"DICe_solution_{frame}.txt"
    if not p.exists():
        p = dice_dir / f"DICe_solution_{frame:02d}.txt"
    rows = np.genfromtxt(p, delimiter=",", names=True)
    ok = rows["STATUS_FLAG"] == 4.0
    return {k: rows[k][ok] for k in rows.dtype.names}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Challenge 2.0 Task 1 (elastic series): cross-code parity vs DICe."
    )
    parser.add_argument(
        "--data-root", help=f"dataset root (default: ${DATA_ROOT_ENV}, else the repo's examples/)"
    )
    args = parser.parse_args(argv)
    c2 = find_dataset(
        args.data_root,
        [(C2_REL, (CALIB_NAME, str(ELASTIC_REL), str(DICE_REL)))],
        "Stereo-DIC Challenge 2.0 (Task 1 elastic frames + DICe solutions)",
    )
    elastic = c2 / ELASTIC_REL
    dice_dir = c2 / DICE_REL

    from al_dic_3d.runner import RunConfig, run_pipeline

    OUT.mkdir(parents=True, exist_ok=True)
    lefts = sorted(glob.glob(str(elastic / "*_0.tif")))
    rights = sorted(glob.glob(str(elastic / "*_1.tif")))
    frames = [int(Path(f).stem.split("-")[-1].split("_")[0]) for f in lefts]
    print(f"elastic frames: {frames}")

    d0 = load_dice(dice_dir, 0)
    xmin, xmax = d0["COORDINATE_X"].min(), d0["COORDINATE_X"].max()
    ymin, ymax = d0["COORDINATE_Y"].min(), d0["COORDINATE_Y"].max()
    roi = (int(xmin), int(xmax), int(ymin), int(ymax))
    print(f"ROI from DICe support: {roi}")

    l0 = cv2.imread(lefts[0], 0)
    r0 = cv2.imread(rights[0], 0)
    hits = []
    for (x, y) in ((1000, 1200), (1300, 1800), (1100, 2100)):
        tpl = l0[y - 60 : y + 60, x - 60 : x + 60].astype(np.float32)
        res = cv2.matchTemplate(r0.astype(np.float32), tpl, cv2.TM_CCOEFF_NORMED)
        _mn, mx, _l, loc = cv2.minMaxLoc(res)
        if mx > 0.45:
            hits.append((loc[0] + 60 - x, loc[1] + 60 - y))
    offset = tuple(np.median(np.asarray(hits, float), axis=0)) if hits else (0.0, 0.0)
    print(f"disparity prior ({offset[0]:+.0f}, {offset[1]:+.0f}) px")

    cfg = RunConfig(
        calibration_file=c2 / CALIB_NAME,
        calibration_format="matchid",
        left=lefts,
        right=rights,
        roi=roi,
        strategy="track_both",
        reference_mode="accumulative",  # elastic: < 5 px total motion
        winsize=24,
        winstepsize=8,
        stereo_search=80,
        disparity_offset=offset,
        fft_search=40,
        compute_strain=True,
        output_dir=OUT / "c2_run",
        output_prefix="c2",
    )
    t0 = time.perf_counter()
    res = run_pipeline(cfg)
    wall = time.perf_counter() - t0
    print(f"pipeline wall {wall:.0f} s")

    cs = res.correspondence
    xL0 = np.asarray(cs.xL[0], dtype=np.float64)
    from scipy.interpolate import LinearNDInterpolator

    out = {"wall_s": wall, "frames": frames, "vs_dice": {}, "eyy_med": {}, "noise": {}}
    eyy = res.strain.eyy
    for k, fr in enumerate(frames):
        e = eyy[k]
        fin = np.isfinite(e)
        out["eyy_med"][fr] = float(np.median(e[fin])) if fin.any() else None

        try:
            dice = load_dice(dice_dir, fr)
        except OSError:
            continue
        du = np.asarray(cs.xL[k], dtype=np.float64) - xL0
        fin2 = np.isfinite(du).all(axis=1) & np.isfinite(xL0).all(axis=1)
        if fin2.sum() < 100:
            continue
        q = np.column_stack([dice["COORDINATE_X"], dice["COORDINATE_Y"]])
        cmp_row = {}
        for ax, (ours_col, dice_col) in enumerate(
            (("dx", "DISPLACEMENT_X"), ("dy", "DISPLACEMENT_Y"))
        ):
            interp = LinearNDInterpolator(xL0[fin2], du[fin2, ax])
            mine = interp(q)
            good = np.isfinite(mine)
            diff = mine[good] - dice[dice_col][good]
            cmp_row[ours_col] = {
                "med_px": float(np.median(np.abs(diff))),
                "p95_px": float(np.percentile(np.abs(diff), 95)),
                "n": int(good.sum()),
            }
        out["vs_dice"][fr] = cmp_row
        print(
            f"frame {fr:2d}: vs DICe |ddx| med {cmp_row['dx']['med_px']:.4f} px, "
            f"|ddy| med {cmp_row['dy']['med_px']:.4f} px (n={cmp_row['dx']['n']}) | "
            f"eyy med {out['eyy_med'][fr]:.2e}",
            flush=True,
        )

    noise_eyy = [
        out["eyy_med"][fr]
        for fr in frames
        if 1 <= fr <= 5 and out["eyy_med"].get(fr) is not None
    ]
    out["noise"] = {
        "eyy_std": float(np.std(noise_eyy)) if noise_eyy else None,
        "eyy_at_50": out["eyy_med"].get(50),
        "protocol_expect_eyy_50": 0.0026,
    }
    (OUT / "c2_task1.json").write_text(json.dumps(out, indent=1))
    print(f"noise eyy std {out['noise']['eyy_std']:.2e} | eyy@50 {out['noise']['eyy_at_50']:.2e} "
          f"(protocol 2.6e-3)")
    print("saved c2_task1.json")


if __name__ == "__main__":
    main()
