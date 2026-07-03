"""GUI — application shell, state, and controllers.

``MainWindow``, ``AppState3D``, and workflow controllers. Reuses individual
``al_dic.gui`` widgets where they are generic, but the shell, state, and
controllers are 3D's own implementation (not a "3D mode" of the 2D app).

Layer: presentation (GUI, imports Qt).  Lands: Phase 4.
Spec: docs/architecture/01 §B.1, §F.
"""
