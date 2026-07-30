"""PyInstaller runtime hook: pin the Qt binding for qtpy.

``pyvistaqt`` (the VTK render widget host) selects its Qt binding through
``qtpy``, which probes PyQt5/PyQt6/PySide2/PySide6 in order. Only PySide6 is
bundled; pinning ``QT_API`` skips the probe (and any confusing ImportError
chains inside the frozen app) and makes the choice explicit.
"""

import os

os.environ.setdefault("QT_API", "pyside6")
