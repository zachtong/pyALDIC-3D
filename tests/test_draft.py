"""ProjectDraft — incremental config assembly + validation (Phase 4 GUI data layer)."""

from __future__ import annotations

from pathlib import Path

import pytest

from al_dic_3d.project import AppState3D, ProjectDraft, load_session, save_session


def _ready_draft(tmp_path: Path) -> ProjectDraft:
    return ProjectDraft(
        calibration_file=tmp_path / "calib.yml",
        calibration_format="opencv_yaml",
        left=["L_000.png", "L_001.png", "L_002.png"],
        right=["R_000.png", "R_001.png", "R_002.png"],
        roi=(20, 180, 20, 180),
    )


def test_empty_draft_reports_all_missing():
    d = ProjectDraft()
    assert not d.is_ready()
    issues = " ".join(d.issues())
    assert "calibration" in issues and "sequences" in issues and "ROI" in issues


def test_ready_draft_builds_runconfig(tmp_path):
    d = _ready_draft(tmp_path)
    assert d.is_ready()
    cfg = d.build()
    assert cfg.calibration_file == tmp_path / "calib.yml"
    assert cfg.left == ["L_000.png", "L_001.png", "L_002.png"]
    assert cfg.roi == (20, 180, 20, 180)
    # Batch C: the GUI pipeline never computes strain — it is post-processing
    # in the Strain window (the TOML/CLI path keeps its [strain].enabled switch).
    assert cfg.compute_strain is False
    assert cfg.base_dir == tmp_path


def test_build_raises_when_incomplete():
    with pytest.raises(ValueError, match="not ready"):
        ProjectDraft().build()


def test_length_mismatch_and_empty_roi_flagged(tmp_path):
    d = ProjectDraft(
        calibration_file=tmp_path / "c.yml", left=["a", "b"], right=["a"], roi=(10, 10, 0, 5)
    )
    issues = " ".join(d.issues())
    assert "mismatch" in issues


def test_draft_survives_session_round_trip(tmp_path):
    d = _ready_draft(tmp_path)
    d.strategy = "ref_direct"
    d.winsize = 48
    d.disparity_offset = (12.0, -1.0)
    loaded = load_session(save_session(AppState3D(draft=d), tmp_path / "p.aldic3d"))
    assert loaded.draft == d  # dataclass equality (paths/tuples restored)
    assert loaded.draft.build().strategy == "ref_direct"


def test_roi_mask_array_builds_png_and_survives_the_session(tmp_path):
    import numpy as np

    pytest.importorskip("cv2")
    d = _ready_draft(tmp_path)
    mask = np.zeros((40, 50), dtype=bool)
    mask[10:30, 5:45] = True
    mask[18:22, 24] = False  # a cut-out hole: a bbox-only restore would fill it in
    d.roi_mask_array = mask
    d.output_dir = tmp_path / "out"

    cfg = d.build()
    assert cfg.roi_mask == tmp_path / "out" / "roi_mask.png"
    assert cfg.roi_mask.exists()  # PNG materialized at build()

    # Session round-trip (batch Z): the drawn mask rides in the bundle as an
    # optional PNG member, so a reopened project correlates the SAME region
    # instead of degrading to the bounding box. The bbox roi and the config's
    # mask PATH survive alongside it.
    state = AppState3D(draft=d, config=cfg)
    loaded = load_session(save_session(state, tmp_path / "p.aldic3d"))
    assert loaded.draft.roi_mask_array is not None
    assert np.array_equal(np.asarray(loaded.draft.roi_mask_array), mask)
    assert loaded.draft.roi == d.roi
    assert loaded.config is not None
    assert loaded.config.roi_mask == cfg.roi_mask
