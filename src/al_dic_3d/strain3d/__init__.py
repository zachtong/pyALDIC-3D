"""Strain3D — surface strain on the reconstructed 3D field.

Local plane fitting + tangent-plane (Green–Lagrange) strain, 3D displacement
smoothing, and 3D outlier removal.

Layer: compute (**Qt-free**).  Lands: Phase 3.  Spec: docs/architecture/01 §B.1, §E
(write ``strain3d_math.md`` before implementing).
"""
