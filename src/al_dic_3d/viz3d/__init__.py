"""Viz3D — interactive 3D visualization.

pyvista / pyvistaqt scenes: deformed surface with scalar coloring, camera
frustums, and timeline playback.

Heavy dependencies (pyvista, VTK) live behind the ``al-dic-3d[viz3d]`` optional
extra and MUST be imported lazily inside functions, never at module import time,
so the compute layer and headless CLI stay installable without them.

Layer: visualization (GUI).  Lands: Phase 4.  Spec: docs/architecture/01 §B.1, §F.
"""
