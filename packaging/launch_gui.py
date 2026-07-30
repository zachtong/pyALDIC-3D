"""Frozen windowed entry point (pyALDIC-3D.exe).

PyInstaller cannot freeze a console-script *entry point* directly, so this
thin script is the analysis root for the GUI executable. It boots straight
into the Qt application; a ``.aldic3d`` session path passed as argv (double
click via the file association, or ``pyALDIC-3D.exe session.aldic3d``) is
handled by :func:`al_dic_3d.gui.app.session_path_from_argv`.

``freeze_support()`` is a no-op today (the app uses threads, not processes)
but is the documented guard against fork-bombs should any dependency ever
spawn ``multiprocessing`` workers from inside the frozen binary.
"""

import multiprocessing
import sys

if __name__ == "__main__":
    multiprocessing.freeze_support()

    from al_dic_3d.gui.app import main

    sys.exit(main(sys.argv[1:]))
