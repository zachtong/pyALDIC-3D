"""Run metadata tells the truth about what was run (fix batch V, M4 / H7 / low).

* Validity was reported against EVERY mesh node, but the mesh covers the ROI's
  bounding box; nodes outside a shaped ROI can never be valid, so a perfect run
  on the Challenge 1.0 S3 D-specimen read "71%" and "34/34 frames below 70%".
* The run's own mesh step / subset size were not recorded anywhere: exports and
  the parameters JSON read whatever the project draft said AFTER the run.
* The parameters JSON recorded the placeholder ROI ``[0, 0, 0, 0]`` for runs
  driven by an ROI mask instead of the effective bounding box.
"""

from __future__ import annotations

import json

import cv2
import numpy as np
import pytest

pytest.importorskip("al_dic")

from al_dic_3d.matching.diagnostics import summarize_run  # noqa: E402
from al_dic_3d.runner import load_config, run_pipeline, write_results  # noqa: E402
from tests import synth_stereo  # noqa: E402


def _disc_roi(tmp_path, shape) -> str:
    m = np.zeros(shape, np.uint8)
    cv2.circle(m, (shape[1] // 2, shape[0] // 2), min(shape) // 3, 255, -1)
    cv2.imwrite(str(tmp_path / "roi_disc.png"), m)
    return "roi_disc.png"


def _masked_run(tmp_path):
    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    cfg_path = synth_stereo.write_config(tmp_path, scene)
    img = cv2.imread(str(sorted(tmp_path.glob("L_*.png"))[0]), cv2.IMREAD_UNCHANGED)
    text = cfg_path.read_text(encoding="utf-8").replace(
        "[roi]", f'[roi]\nmask = "{_disc_roi(tmp_path, img.shape[:2])}"'
    )
    cfg_path.write_text(text, encoding="utf-8")
    cfg = load_config(cfg_path)
    return cfg, run_pipeline(cfg)


def test_summary_uses_the_nodes_inside_the_roi_as_denominator(tmp_path):
    cfg, result = _masked_run(tmp_path)
    m = result.meta
    assert 0 < m["n_pts_in_roi"] < m["n_pts"]
    assert m["summary"]["median_valid_frac"] > 0.9  # was ~0.5 against all nodes
    s = summarize_run(result.correspondence, result.reconstruction.points)
    assert s.median_valid_frac < m["summary"]["median_valid_frac"]  # the old denominator


def test_run_parameters_are_recorded_in_the_result(tmp_path):
    cfg, result = _masked_run(tmp_path)
    rp = result.meta["run_params"]
    assert rp["winstepsize"] == cfg.winstepsize and rp["winsize"] == cfg.winsize
    assert rp["reference_mode"] == cfg.reference_mode and rp["strategy"] == cfg.strategy
    json.dumps(rp)  # JSON-safe for the session file and the parameters export


def test_parameters_json_records_the_effective_roi(tmp_path):
    cfg, result = _masked_run(tmp_path)
    paths = write_results(result, cfg, formats=("npz",))
    params = json.loads(paths["params"].read_text(encoding="utf-8"))
    flat = json.dumps(params)
    assert "[0, 0, 0, 0]" not in flat.replace(" ", " ")
    roi = result.meta["run_params"]["roi"]
    assert roi[0] < roi[1] and roi[2] < roi[3]


def test_a_validity_collapse_comes_with_advice():
    from al_dic_3d.matching.diagnostics import RunSummary, collapse_advice, summary_lines

    def summary(fracs):
        return RunSummary(
            n_frames=len(fracs),
            n_pts=100,
            valid_frac=tuple(fracs),
            median_valid_frac=sorted(fracs)[len(fracs) // 2],
            low_frames=(),
            all_empty=False,
            stereo_n_pts=None,
            stereo_n_valid=None,
            gated_by_cam={},
        )

    collapsed = summary([0.97, 0.9, 0.05, 0.02])
    assert collapse_advice(collapsed, "accumulative") == "incremental"
    assert collapse_advice(collapsed, "incremental") == "masks"
    assert collapse_advice(summary([0.97, 0.9, 0.8, 0.7]), "accumulative") is None
    lines = summary_lines(collapsed, stopped={"run_params": {"reference_mode": "accumulative"}})
    assert any("incremental" in text for _, text in lines)
