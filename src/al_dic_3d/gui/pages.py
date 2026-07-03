"""Workflow page skeletons (Qt view layer; 01 §F).

One page per workflow step. These are STRUCTURAL skeletons — a titled panel with
the step's purpose and the affordances it will host — wired to the controller.
The rich interactive widgets (reusing the 2D ``image_list`` / ``roi_toolbar`` /
canvas, the pyvista 3D tab) are filled in during visual iteration on a display.

Every user-facing string is a LITERAL inside ``self.tr(...)`` (so ``lupdate``
extracts it and the i18n scan sees it). Compute never runs here — pages only
read/write the ``AppState3D`` via the
:class:`~al_dic_3d.gui.controller.WorkflowController`.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from al_dic_3d.gui.controller import WorkflowController


class WorkflowPage(QWidget):
    """Base page: a bold title + a wrapped description, both translatable."""

    def __init__(self, controller: WorkflowController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._layout = QVBoxLayout(self)
        self._title = QLabel(self)
        self._title.setStyleSheet("font-size: 16px; font-weight: 600;")
        self._body = QLabel(self)
        self._body.setWordWrap(True)
        self._body.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout.addWidget(self._title)
        self._layout.addWidget(self._body)
        self._layout.addStretch(1)
        self.build()

    def _set(self, title: str, body: str) -> None:
        self._title.setText(title)
        self._body.setText(body)

    def build(self) -> None:  # pragma: no cover - overridden
        """Subclasses set the (translated) title/body and add affordances."""

    def on_enter(self) -> None:
        """Called when this page becomes visible; refresh from the state."""


class ProjectPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("New / Open Project"),
            self.tr(
                "Create a new .aldic3d project or open an existing one. "
                "Double-clicking a .aldic3d file resumes it on this page."
            ),
        )


class ImportPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Import left / right sequences"),
            self.tr(
                "Load the two camera image streams. Pairing (frame count, size, and "
                "name pattern) is validated; a mismatch is flagged immediately."
            ),
        )


class CalibrationPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Calibration"),
            self.tr(
                "Import calibration in one of six formats, then review the "
                "intrinsics/extrinsics summary, baseline, and an epipolar sanity "
                "overlay. Calibration errors must be caught here."
            ),
        )


class RoiPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Region of interest"),
            self.tr(
                "Draw the ROI on the left camera, frame 1 (reusing the 2D ROI tools: "
                "shapes, mask import, batch ROI)."
            ),
        )


class CorrespondencePage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Correspondence settings"),
            self.tr(
                "Choose the strategy (default track_both) and its parameters. A "
                "frame-1 stereo-match preview shows the disparity field + ZNSSD "
                "quality before committing to a full run."
            ),
        )


class RunPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Run"),
            self.tr(
                "Execute the pipeline with staged, cancellable progress "
                "(correspondence stages, triangulation, strain)."
            ),
        )


class ResultsPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Results"),
            self.tr(
                "Per-camera 2D fields, a 3D view (deformed surface, scalar coloring, "
                "camera frusta, timeline), strain fields, and a QC page "
                "(quality/source maps, reprojection-vs-frame drift)."
            ),
        )


class ExportPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Export"),
            self.tr(
                "Export point clouds / meshes (PLY, VTU), tables (CSV, MAT), and "
                "screenshots / animations."
            ),
        )


#: Page classes in workflow order (index == workflow step).
PAGE_CLASSES = (
    ProjectPage,
    ImportPage,
    CalibrationPage,
    RoiPage,
    CorrespondencePage,
    RunPage,
    ResultsPage,
    ExportPage,
)
