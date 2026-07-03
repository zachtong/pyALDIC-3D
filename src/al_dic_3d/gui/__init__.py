"""GUI — application shell, state, and controllers (imports Qt).

``MainWindow3D`` + the workflow ``WorkflowController`` over the Qt-free
``AppState3D``. Reuses individual ``al_dic.gui`` widgets where they are generic,
but the shell, state, and controllers are 3D's own implementation (not a "3D mode"
of the 2D app).

This package's ``__init__`` stays Qt-free (only the controller), so the workflow
logic is importable without a display; ``main_window`` / ``pages`` / ``app`` pull
in PySide6. The compute layer never imports any of it.

Layer: presentation (GUI, imports Qt).  Lands: Phase 4.
Spec: docs/architecture/01 §B.1, §F.
"""

from al_dic_3d.gui.controller import N_STEPS, STEP_TITLES, WorkflowController

__all__ = ["N_STEPS", "STEP_TITLES", "WorkflowController"]
