"""3D surface + strain, rendered by the product itself -> ``assets/surface_3d.*``.

A curved synthetic stereo scene (``tests/synth_surface.py``: a Gaussian-bump
surface under a KNOWN 3D Lagrangian displacement field, imaged by two distorted
converging cameras) is pushed through the real headless pipeline
(``al_dic_3d.runner.run_pipeline``) and then rendered by the real 3D export
path (``al_dic_3d.export.render3d``) — the same ``build_surface_polydata``
geometry and the same offscreen pyvista plotter the desktop 3D view uses.

Because the scene has analytic ground truth, the script also PRINTS the
end-frame accuracy it achieved, so the numbers quoted next to the figure can be
re-derived by anyone who runs it.

Outputs:
    assets/surface_3d.png          W displacement | exx strain, isometric
    assets/surface_orbit.gif       the same surface from a sweep of viewpoints

The orbit GIF drives ``render_view3d_frame(..., camera=...)`` — the shipping
offscreen renderer — once per viewpoint. It deliberately does NOT go through
``export_view3d_turntable``: on pyvista 0.48 that function's
``pl.camera.Azimuth(...)`` mutates a COPY of the camera and never re-renders, so
every "orbit" frame is identical and the encoder collapses them into a single
still. See the note in the task report; until that is fixed the turntable button
does not actually orbit.

Run:  python tools/marketing/fig_surface_3d.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from _style import ASSETS, BG_DARKEST, MONO, TEXT_PRIMARY, TEXT_SECONDARY, optimize_png, save
from matplotlib import pyplot as plt

from al_dic_3d.export.render3d import render_view3d_frame
from al_dic_3d.export.tables import display_field_frame
from al_dic_3d.runner import load_config, run_pipeline

IMG = 900
N_FRAMES = 6
DEFORM = 0.30
WINSIZE, STEP = 32, 16
WINDOW = (1150, 950)
ORBIT_SIZE = (520, 450)  # kept small: the repo rejects assets over 1 MB
ORBIT_FRAMES = 30

CONFIG = """
[calibration]
file = "calib.yml"
format = "opencv_yaml"

[sequence]
left = "L_*.png"
right = "R_*.png"

[roi]
xmin = {lo}
xmax = {hi}
ymin = {lo}
ymax = {hi}

[matching]
strategy = "track_both"
reference_mode = "accumulative"
winsize = {winsize}
winstepsize = {step}
stereo_search = 96
fft_search = 48

[strain]
enabled = true
strain_size = 5

[output]
dir = "out"
prefix = "surface"
"""


def _run(workdir: Path):
    import synth_surface

    print(f"rendering the synthetic curved stereo scene ({IMG} px, {N_FRAMES} frames) ...")
    scene = synth_surface.build_surface_scene(
        workdir, img=IMG, n_frames=N_FRAMES, deform=DEFORM, seed=7
    )
    lo, hi = int(0.23 * IMG), int(0.77 * IMG)
    (workdir / "config.toml").write_text(
        CONFIG.format(lo=lo, hi=hi, winsize=WINSIZE, step=STEP).strip() + "\n", encoding="utf-8"
    )
    print("running the real pipeline ...")
    result = run_pipeline(load_config(workdir / "config.toml"))
    return scene, result, synth_surface


def _report_accuracy(scene, result, synth_surface) -> str:
    """Compare the end frame against the scene's analytic ground truth."""
    gt = synth_surface.gt_tracks(scene, result.ref_coords)
    k = result.reconstruction.n_frames - 1
    got = result.reconstruction.displacement[k]
    want = gt["displacement"][k]
    ok = np.isfinite(got).all(axis=1)
    err = np.linalg.norm(got[ok] - want[ok], axis=1)
    valid = 100.0 * ok.mean()
    line = (
        f"frame {k}: {ok.sum()}/{ok.size} nodes valid ({valid:.1f}%), "
        f"|3D displacement error| median {np.median(err) * 1000:.1f} um, "
        f"p95 {np.percentile(err, 95) * 1000:.1f} um"
    )
    print("  " + line)
    return line


def _crop_white(img: np.ndarray, pad: int = 8) -> np.ndarray:
    """Trim the plotter's white margin so the surface fills the panel."""
    ink = (img < 245).any(axis=2)
    if not ink.any():
        return img
    ys, xs = np.where(ink)
    y0, y1 = max(0, ys.min() - pad), min(img.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(img.shape[1], xs.max() + pad + 1)
    return img[y0:y1, x0:x1]


def _panel(ax, img, title, color):
    ax.imshow(_crop_white(img)[:, :, ::-1])  # render3d returns BGR
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color(color)
        sp.set_linewidth(1.6)
    ax.set_title(title, color=color, fontsize=12, fontfamily=MONO, pad=8)


def _isometric_camera(points: np.ndarray, values: np.ndarray, label: str, ref_coords):
    """Read the plotter's own isometric camera for this surface, then close it."""
    import pyvista as pv

    from al_dic_3d.export.render3d import build_surface

    surf = build_surface(points, values, label, ref_coords)
    pl = pv.Plotter(off_screen=True, window_size=[ORBIT_SIZE[0], ORBIT_SIZE[1]])
    try:
        pl.add_mesh(surf, scalars=label)
        pl.view_isometric()
        pos, focal, up = (np.asarray(c, dtype=float) for c in pl.camera_position)
    finally:
        pl.close()
    return pos, focal, up


def _orbit_cameras(pos, focal, up, n: int):
    """``n`` camera tuples orbiting ``focal`` about the view-up axis."""
    axis = up / np.linalg.norm(up)
    offset = pos - focal
    for i in range(n):
        th = 2.0 * np.pi * i / n
        c, s = np.cos(th), np.sin(th)
        # Rodrigues rotation of the camera offset about the up axis.
        rot = offset * c + np.cross(axis, offset) * s + axis * float(axis @ offset) * (1.0 - c)
        yield (tuple(focal + rot), tuple(focal), tuple(up))


def _orbit_gif(result, k: int) -> None:
    """A viewpoint sweep of the reconstructed surface -> ``assets/surface_orbit.gif``."""
    import imageio

    label = "W (mm)"
    vals = display_field_frame(result, "W", k, deformed=True)
    finite = vals[np.isfinite(vals)]
    lo, hi = (float(v) for v in np.percentile(finite, [2, 98]))
    pts = result.reconstruction.points[k]

    print(f"rendering the {ORBIT_FRAMES}-viewpoint orbit (shipping offscreen renderer) ...")
    pos, focal, up = _isometric_camera(pts, vals, label, result.ref_coords)
    dest = ASSETS / "surface_orbit.gif"
    writer = imageio.get_writer(str(dest), format="GIF", mode="I", duration=1 / 14, loop=0)
    prev = None
    try:
        for cam in _orbit_cameras(pos, focal, up, ORBIT_FRAMES):
            bgr = render_view3d_frame(
                pts,
                vals,
                field_label=label,
                cmap="turbo",
                vmin=lo,
                vmax=hi,
                ref_coords=result.ref_coords,
                window_size=ORBIT_SIZE,
                camera=cam,
                background="white",
            )
            if bgr is None:
                continue
            rgb = bgr[:, :, ::-1]
            if prev is not None and np.array_equal(prev, rgb):
                raise RuntimeError("orbit frames are identical — the camera is not moving")
            prev = rgb
            writer.append_data(rgb)
    finally:
        writer.close()
    print(f"  wrote {dest} ({dest.stat().st_size / 1024:.0f} KB)")


def main() -> int:
    workdir = Path(tempfile.mkdtemp(prefix="aldic3d_surface_"))
    try:
        scene, result, synth_surface = _run(workdir)
        acc = _report_accuracy(scene, result, synth_surface)

        k = result.reconstruction.n_frames - 1
        pts = result.reconstruction.points[k]
        panels = []
        for field, label, cmap in (
            ("W", "W (mm)", "turbo"),
            ("exx", "exx", "coolwarm"),
        ):
            vals = display_field_frame(result, field, k, deformed=True)
            finite = vals[np.isfinite(vals)]
            lo, hi = np.percentile(finite, [2, 98])
            img = render_view3d_frame(
                pts,
                vals,
                field_label=label,
                cmap=cmap,
                vmin=float(lo),
                vmax=float(hi),
                ref_coords=result.ref_coords,
                window_size=WINDOW,
                background="white",
            )
            panels.append((img, label))

        fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.4), dpi=110, facecolor=BG_DARKEST)
        _panel(axes[0], panels[0][0], "3D shape + out-of-plane motion", "#818cf8")
        _panel(axes[1], panels[1][0], "surface strain on the same mesh", "#22d3ee")
        fig.text(
            0.5,
            0.045,
            "Rendered by the shipping 3D export path on a synthetic scene with analytic truth.\n"
            + acc,
            color=TEXT_SECONDARY,
            fontsize=10,
            ha="center",
            fontfamily=MONO,
            linespacing=1.6,
        )
        fig.text(
            0.5,
            0.955,
            "Metric 3D surface, displacement and strain — one run",
            color=TEXT_PRIMARY,
            fontsize=14,
            fontweight="bold",
            ha="center",
            fontfamily=MONO,
        )
        fig.subplots_adjust(left=0.015, right=0.985, top=0.90, bottom=0.145, wspace=0.05)
        out = save(fig, "surface_3d.png", dpi=110)
        optimize_png(out, max_width=1500)

        _orbit_gif(result, k)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
