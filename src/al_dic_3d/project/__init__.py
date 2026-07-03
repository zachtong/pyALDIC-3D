"""Project / session layer — ``StereoProject`` and the ``.aldic3d`` package.

Owns the session envelope (dedup-npz payload + JSON manifest, following the
2D ``.aldic`` design) and project-level state persistence.

Layer: data (Qt-free).  Lands: Phase 4–5.  Spec: docs/architecture/01 §B.1, §E.
"""
