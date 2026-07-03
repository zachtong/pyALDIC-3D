"""Workflow controller — headless full-workflow smoke (Phase 4 gate foundation).

The controller is Qt-free, so the whole 8-step workflow (config -> run -> results
-> save/reopen session) is exercised without a display. This backs the Phase-4
full-workflow-smoke gate; the Qt view is tested separately (offscreen).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from al_dic_3d.gui.controller import N_STEPS, WorkflowController
from al_dic_3d.project.state import STEP_IMPORT, STEP_PROJECT, STEP_RESULTS

cv2 = pytest.importorskip("cv2")

from tests import synth_parity  # noqa: E402  (after importorskip guard)


def _config(tmp_path):
    from al_dic_3d.runner import load_config

    scene = synth_parity.build_parity_scene(tmp_path, img=300, n_frames=3, seed=7)
    return replace(load_config(synth_parity.write_config(tmp_path, scene)), compute_strain=True)


def test_navigation_validation_gates_on_config():
    c = WorkflowController()
    assert c.state.workflow_step == STEP_PROJECT
    assert c.can_advance() and c.advance()  # project -> import
    assert c.state.workflow_step == STEP_IMPORT
    assert not c.can_advance()  # import onward needs a config
    with pytest.raises(ValueError):
        c.goto(N_STEPS)  # out of range


def test_full_workflow_run_then_session_round_trip(tmp_path):
    cfg = _config(tmp_path)
    c = WorkflowController()
    c.set_config(cfg)
    assert c.state.dirty
    result = c.run()

    assert c.state.has_results
    assert c.state.workflow_step == STEP_RESULTS
    assert result.strain is not None

    path = c.save_project(tmp_path / "proj.aldic3d")
    assert not c.state.dirty and c.state.project_path == path

    reopened = WorkflowController()
    reopened.open_project(path)
    assert reopened.state.has_results
    assert reopened.state.result.strategy == result.strategy
    assert reopened.state.config == cfg


def test_run_without_config_raises():
    with pytest.raises(RuntimeError, match="no configuration"):
        WorkflowController().run()
