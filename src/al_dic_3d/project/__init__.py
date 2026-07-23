"""Project / session layer — ``AppState3D`` and the ``.aldic3d`` session bundle.

Owns the workflow state (:class:`AppState3D`) and its persistence: a versioned ZIP
envelope (``session.json`` config/view-state + ``results.npz`` payload, following
the 2D ``.aldic`` design). Qt-free and unit-testable (session round-trip).

Layer: data (Qt-free).  Lands: Phase 4–5.  Spec: docs/architecture/01 §B.1, §F.
"""

from al_dic_3d.project.draft import ProjectDraft
from al_dic_3d.project.relocate import (
    CameraRelocation,
    RelocationCancelled,
    relocate_draft_images,
)
from al_dic_3d.project.session import (
    SCHEMA_VERSION,
    Session3DData,
    SessionError,
    load_session,
    parse_session,
    save_session,
)
from al_dic_3d.project.state import AppState3D

__all__ = [
    "SCHEMA_VERSION",
    "AppState3D",
    "CameraRelocation",
    "ProjectDraft",
    "RelocationCancelled",
    "Session3DData",
    "SessionError",
    "load_session",
    "parse_session",
    "relocate_draft_images",
    "save_session",
]
