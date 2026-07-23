"""Workflow controller — the Qt-free logic behind the GUI (headless-testable).

Owns an :class:`AppState3D` and drives the 8-step workflow (01 §F): new/open/save
project, step navigation with per-step validation, and running the headless
pipeline. The GUI (``MainWindow3D``) is a thin view over this controller, so the
whole workflow can be exercised in tests without a display.

Raises plain exceptions with **English** messages (the i18n contract forbids
``tr()`` outside the Qt view layer; the GUI catches and translates).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from al_dic_3d.project import AppState3D, load_session, save_session
from al_dic_3d.project.state import (
    STEP_CALIBRATION,
    STEP_CORRESPONDENCE,
    STEP_EXPORT,
    STEP_IMPORT,
    STEP_PROJECT,
    STEP_RESULTS,
    STEP_ROI,
    STEP_RUN,
)

ProgressFn = Callable[[float, str], None]

# English step titles (translated in the view via tr()).
STEP_TITLES = {
    STEP_PROJECT: "Project",
    STEP_IMPORT: "Import L/R sequences",
    STEP_CALIBRATION: "Calibration",
    STEP_ROI: "ROI",
    STEP_CORRESPONDENCE: "Correspondence",
    STEP_RUN: "Run",
    STEP_RESULTS: "Results",
    STEP_EXPORT: "Export",
}
N_STEPS = len(STEP_TITLES)


class WorkflowController:
    """Drives the AppState3D through the workflow; no Qt."""

    def __init__(self, state: AppState3D | None = None) -> None:
        self.state = state or AppState3D()

    # --- project lifecycle ---------------------------------------------------

    def new_project(self) -> None:
        self.state = AppState3D()

    def open_project(self, path: str | Path) -> None:
        self.state = load_session(path)

    def adopt_state(self, state: AppState3D) -> None:
        """Adopt a session parsed elsewhere (e.g. on a GUI worker thread, P2.5)."""
        self.state = state

    def save_project(self, path: str | Path, *, include_results: bool = True) -> Path:
        """Save the state; ``include_results=False`` writes config-only (Q7)."""
        saved = save_session(self.state, path, include_results=include_results)
        self.state.project_path = saved
        self.state.dirty = False
        return saved

    def set_config(self, config) -> None:
        self.state.config = config
        self.state.mark_dirty()

    def build_config(self):
        """Assemble the frozen RunConfig from the current draft; raise if not ready."""
        self.state.config = self.state.draft.build()
        self.state.mark_dirty()
        return self.state.config

    # --- navigation ----------------------------------------------------------

    def can_advance(self) -> bool:
        """Whether the 'Next' action may move to the following step.

        Setup transitions (project..run) are free — the draft is filled
        incrementally and validated at Run. Advancing INTO Results/Export requires
        a completed run.
        """
        nxt = self.state.workflow_step + 1
        if nxt >= N_STEPS:
            return False
        if nxt in (STEP_RESULTS, STEP_EXPORT):
            return self.state.has_results
        return True

    def can_run(self) -> bool:
        """Whether the draft has everything needed to assemble a RunConfig."""
        return self.state.draft.is_ready()

    def goto(self, step: int) -> None:
        if not 0 <= step < N_STEPS:
            raise ValueError(f"workflow step out of range: {step}")
        self.state.workflow_step = step

    def advance(self) -> bool:
        """Advance to the next step if allowed; return whether it moved."""
        if self.state.workflow_step >= N_STEPS - 1 or not self.can_advance():
            return False
        self.state.workflow_step += 1
        return True

    # --- run -----------------------------------------------------------------

    def run(self, progress: ProgressFn | None = None, stop: Callable[[], bool] | None = None):
        """Execute the headless pipeline and store the result on the state.

        Rebuilds the RunConfig from the draft when the draft is ready (so sidebar
        edits after a previous run take effect); an explicitly set config (the
        headless path) is used as-is when the draft is untouched. ``stop`` polls
        for cooperative cancel.
        """
        if self.state.draft.is_ready() or self.state.config is None:
            self.build_config()
        from al_dic_3d.runner import run_pipeline

        self.state.result = run_pipeline(self.state.config, progress=progress, stop=stop)
        self.state.mark_dirty()
        self.state.workflow_step = STEP_RESULTS
        return self.state.result
