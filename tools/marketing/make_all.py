"""Regenerate every README figure -> ``assets/``.

Each generator is a standalone script and is run in its own subprocess, because
they disagree about their environment: the Qt screenshots need
``QT_QPA_PLATFORM=offscreen`` set before any Qt import, while the pyvista 3D
renders need a process WITHOUT the Qt offscreen platform (the embedded VTK
widget cannot obtain an OpenGL context under it, but a plain offscreen
``pv.Plotter`` can).

Run:  python tools/marketing/make_all.py [name ...]
      python tools/marketing/make_all.py --list
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (script, what it produces) — ordered cheapest first so failures surface fast.
GENERATORS: tuple[tuple[str, str], ...] = (
    ("gen_banner.py", "banner_3d.png"),
    ("fig_stereo_principle.py", "stereo_principle.png"),
    ("fig_crack_aware.py", "crack_aware.png"),
    ("fig_honesty_gate.py", "honesty_gate.png"),
    ("fig_calibration.py", "calibration.png"),
    ("fig_surface_3d.py", "surface_3d.png + surface_orbit.gif"),
    ("gen_gui_shots.py", "main_page.png, strain_window.png, export_window.png, i18n_zh.png"),
)


def main(argv: list[str]) -> int:
    if "--list" in argv:
        for script, produces in GENERATORS:
            print(f"{script:26s} -> {produces}")
        return 0

    wanted = [a for a in argv if not a.startswith("-")]
    selected = [g for g in GENERATORS if not wanted or g[0] in wanted or g[0][:-3] in wanted]
    if not selected:
        print(f"nothing matched {wanted}; try --list")
        return 2

    failures: list[str] = []
    for script, produces in selected:
        print(f"\n=== {script}  ->  {produces} ===", flush=True)
        t0 = time.perf_counter()
        proc = subprocess.run([sys.executable, str(HERE / script)], check=False)
        dt = time.perf_counter() - t0
        if proc.returncode != 0:
            failures.append(script)
            print(f"!!! {script} FAILED (exit {proc.returncode}) after {dt:.0f} s")
        else:
            print(f"--- {script} ok in {dt:.0f} s")

    if failures:
        print(f"\n{len(failures)} generator(s) failed: {', '.join(failures)}")
        return 1
    print(f"\nall {len(selected)} generator(s) ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
