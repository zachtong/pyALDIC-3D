"""Application state for the pyALDIC-3D workflow (Qt-free data layer).

``AppState3D`` is the single mutable holder the GUI controllers read and write as
the user moves through the workflow (01 §F): the reproducible inputs
(a :class:`~al_dic_3d.runner.RunConfig`), the computed results
(a :class:`~al_dic_3d.runner.RunResult`, populated after a run), plus the UI view
state and the current workflow step. It carries NO Qt — the GUI layer owns it but
it stays serializable and unit-testable (see :mod:`al_dic_3d.project.session`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from al_dic_3d.project.draft import ProjectDraft

if TYPE_CHECKING:
    from al_dic_3d.runner import RunConfig, RunResult

# Workflow steps (01 §F), used as the current-page index.
STEP_PROJECT = 0
STEP_IMPORT = 1
STEP_CALIBRATION = 2
STEP_ROI = 3
STEP_CORRESPONDENCE = 4
STEP_RUN = 5
STEP_RESULTS = 6
STEP_EXPORT = 7


@dataclass
class AppState3D:
    """Mutable workflow state (GUI layer; Qt-free)."""

    draft: ProjectDraft = field(default_factory=ProjectDraft)  # user-edited inputs (pages fill)
    config: RunConfig | None = None  # frozen inputs assembled from the draft at run
    result: RunResult | None = None  # computed correspondence/reconstruction/strain
    view_state: dict = field(default_factory=dict)  # UI: current field/frame/colormap/ranges
    workflow_step: int = STEP_PROJECT
    project_path: Path | None = None  # the .aldic3d file this state is bound to
    dirty: bool = False  # unsaved changes since the last save/load

    @property
    def has_results(self) -> bool:
        return self.result is not None

    def mark_dirty(self) -> None:
        self.dirty = True
