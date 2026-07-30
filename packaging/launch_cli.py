"""Frozen console entry point (pyaldic3d-cli.exe).

Mirrors the ``al-dic-3d`` console script (``al_dic_3d.cli:main``) for the
headless ``run`` / ``calibrate`` commands, so MATLAB-style batch users get a
real console executable with stdout/stderr and exit codes. The GUI is served
by the separate windowed ``pyALDIC-3D.exe`` (see ``launch_gui.py``).
"""

import multiprocessing
import sys

if __name__ == "__main__":
    multiprocessing.freeze_support()

    from al_dic_3d.cli import main

    sys.exit(main())
