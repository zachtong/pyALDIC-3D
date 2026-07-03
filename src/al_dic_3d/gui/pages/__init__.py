"""Workflow pages (Qt view layer) — one per workflow step (01 §F).

``PAGE_CLASSES`` is in workflow order (index == workflow step). Each page is wired
to the :class:`~al_dic_3d.gui.controller.WorkflowController` and populates the
``AppState3D`` draft; every user-facing string is a literal ``self.tr(...)``.
"""

from al_dic_3d.gui.pages.base import WorkflowPage
from al_dic_3d.gui.pages.calibration import CalibrationPage
from al_dic_3d.gui.pages.correspondence import CorrespondencePage
from al_dic_3d.gui.pages.export import ExportPage
from al_dic_3d.gui.pages.import_page import ImportPage
from al_dic_3d.gui.pages.project import ProjectPage
from al_dic_3d.gui.pages.results import ResultsPage
from al_dic_3d.gui.pages.roi import RoiPage
from al_dic_3d.gui.pages.run import RunPage

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

__all__ = [
    "PAGE_CLASSES",
    "CalibrationPage",
    "CorrespondencePage",
    "ExportPage",
    "ImportPage",
    "ProjectPage",
    "ResultsPage",
    "RoiPage",
    "RunPage",
    "WorkflowPage",
]
