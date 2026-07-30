"""A saved ``.aldic3d`` must come back exactly as it was left (batch Z).

Save/load is how a user parks a project, so anything that silently fails to
round-trip is a data-loss bug. Two shapes of that bug are covered here:

* **The canvas-painted masks.** A shaped ROI (polygon / circle / cut shapes /
  brush / imported PNG) and the freehand refinement brush lived only as
  ndarrays on the draft and were dropped at save time. A reloaded session then
  correlated the ROI's BOUNDING BOX — cut-out regions included — and built a
  DIFFERENT mesh than the one that produced the results it was saved with,
  without saying so. Crack-aware runs lost their barrier entirely.
* **A future field forgotten the same way.** The completeness audits below fail
  when a ``ProjectDraft`` / ``RunConfig`` / ``AppState3D`` field appears that is
  neither persisted nor declared deliberately transient with a reason.

The GUI half of the audit (canvas toggles, view-state capture/restore symmetry)
lives in ``test_session_fidelity_gui.py``.
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import fields
from pathlib import Path

import numpy as np
import pytest

from al_dic_3d.project import SCHEMA_VERSION, AppState3D, ProjectDraft, load_session, save_session
from al_dic_3d.project.session import _MASK_MEMBERS, _draft_to_json

cv2 = pytest.importorskip("cv2")

H, W = 120, 160


# ---------------------------------------------------------------------------
# mask builders (the shapes the ROI toolbox actually produces)
# ---------------------------------------------------------------------------


def _shaped_roi_mask() -> np.ndarray:
    """A polygon ROI with a circular bite cut out of it (bool, (H, W)).

    Deliberately NOT a rectangle: its bounding box covers pixels the user
    excluded, so a bbox-only restore is detectable.
    """
    from al_dic_3d.gui.controllers.roi_controller import ROIController

    ctrl = ROIController((H, W))
    ctrl.add_polygon([(20, 20), (140, 30), (130, 100), (25, 90)], "add")
    ctrl.add_circle(80, 60, 18, "cut")
    return ctrl.mask.copy()


def _brush_mask() -> np.ndarray:
    """A freehand brush stroke as the canvas stores it: uint8, 255 = refine."""
    arr = np.zeros((H, W), dtype=np.uint8)
    cv2.line(arr, (30, 40), (120, 75), 255, thickness=9)
    return arr


def _cracked_roi_mask() -> np.ndarray:
    """All-material ROI band with a 1-px vertical crack barrier (bool)."""
    mask = np.zeros((H, W), dtype=bool)
    mask[20:100, 20:140] = True
    mask[20:100, 80] = False  # the thin barrier
    return mask


def _bbox_of(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(np.asarray(mask) > 0)
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def _saved(tmp_path: Path, draft: ProjectDraft, name: str = "s.aldic3d") -> ProjectDraft:
    """Save a draft-only state and return the reloaded draft."""
    path = save_session(AppState3D(draft=draft), tmp_path / name)
    return load_session(path).draft


# ---------------------------------------------------------------------------
# Z1 — the canvas-painted masks ride inside the bundle
# ---------------------------------------------------------------------------


def test_shaped_roi_mask_round_trips(tmp_path):
    """A polygon-with-a-cut ROI must come back pixel-for-pixel, not as its bbox."""
    mask = _shaped_roi_mask()
    draft = ProjectDraft(roi_mask_array=mask, roi=_bbox_of(mask))

    back = _saved(tmp_path, draft)

    assert back.roi_mask_array is not None, "shaped ROI mask was lost on reload"
    got = np.asarray(back.roi_mask_array)
    assert got.shape == mask.shape
    assert got.dtype == np.bool_  # the form every consumer thresholds with > 0
    assert np.array_equal(got, mask)
    # The bite is still a hole — a bbox-only restore would have filled it in.
    assert int(np.count_nonzero(got)) < int(np.prod(mask.shape))
    assert not got[60, 80]
    assert back.roi == draft.roi


def test_refinement_brush_round_trips(tmp_path):
    """The freehand brush is NOT rebuildable, so losing it changes the mesh."""
    brush = _brush_mask()
    back = _saved(tmp_path, ProjectDraft(refinement_mask_array=brush))

    assert back.refinement_mask_array is not None, "refinement brush was lost on reload"
    got = np.asarray(back.refinement_mask_array)
    assert got.shape == brush.shape
    assert np.array_equal(got, brush > 0)  # binary semantics preserved exactly


def test_result_signature_survives_the_round_trip(tmp_path):
    """The staleness hash covers both mask arrays by content.

    Same signature in == same mesh out: this is the canary for "a reloaded
    session re-runs with a different mesh, silently".
    """
    draft = ProjectDraft(
        roi_mask_array=_shaped_roi_mask(),
        roi=_bbox_of(_shaped_roi_mask()),
        refinement_mask_array=_brush_mask(),
        refine_inner=True,
        refinement_level=3,
    )
    assert _saved(tmp_path, draft).result_signature() == draft.result_signature()


def test_crack_barrier_survives_the_round_trip(tmp_path):
    """A crack-aware session must still be crack-aware after reopening.

    ``crack_aware`` is decided by ``mask_cuts_mesh`` on the frame-1 mesh; the
    barrier is a 1-px band inside the mask, so a bbox-only restore erases it and
    the reloaded session would run (and render, and strain) crack-blind.
    """
    from al_dic_3d.matching.crack_mesh import mask_cuts_mesh
    from al_dic_3d.runner import build_reference_mesh

    mask = _cracked_roi_mask()
    roi = _bbox_of(mask)
    back = _saved(tmp_path, ProjectDraft(roi_mask_array=mask, roi=roi))

    assert back.roi_mask_array is not None
    restored = (np.asarray(back.roi_mask_array) > 0).astype(np.float64)
    mesh = build_reference_mesh(H, W, roi, winsize=16, winstepsize=8, mask=restored)
    assert mask_cuts_mesh(mesh, restored), "crack barrier lost — run would be crack-blind"
    # Proof the assertion above has teeth: the bbox-only degradation is blind.
    bbox_only = np.zeros((H, W), dtype=np.float64)
    bbox_only[roi[2] : roi[3] + 1, roi[0] : roi[1] + 1] = 1.0
    assert not mask_cuts_mesh(mesh, bbox_only)


def test_mask_members_are_deflated_pngs(tmp_path):
    """Both masks are optional, DEFLATE-compressed PNG members of the zip."""
    draft = ProjectDraft(roi_mask_array=_shaped_roi_mask(), refinement_mask_array=_brush_mask())
    path = save_session(AppState3D(draft=draft), tmp_path / "members.aldic3d")

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        assert set(_MASK_MEMBERS.values()) <= names
        for member in _MASK_MEMBERS.values():
            info = zf.getinfo(member)
            assert info.compress_type == zipfile.ZIP_DEFLATED
            blob = zf.read(member)
            assert blob[:8] == b"\x89PNG\r\n\x1a\n"  # a real PNG, not a pickle
            decoded = cv2.imdecode(np.frombuffer(blob, np.uint8), cv2.IMREAD_UNCHANGED)
            assert decoded.shape[:2] == (H, W)
    # The JSON never carries the arrays (they are not JSON-serializable).
    assert not set(_MASK_MEMBERS) & set(_draft_to_json(draft))


def test_no_mask_members_when_nothing_was_painted(tmp_path):
    """An unpainted project writes neither member and reloads with both None."""
    path = save_session(AppState3D(draft=ProjectDraft(roi=(10, 100, 10, 100))), tmp_path / "p")
    with zipfile.ZipFile(path) as zf:
        assert not set(_MASK_MEMBERS.values()) & set(zf.namelist())
    back = load_session(path).draft
    assert back.roi_mask_array is None and back.refinement_mask_array is None


def test_pre_batch_z_session_without_mask_members_still_loads(tmp_path):
    """Back-compat: the members are optional, so schema_version stays 1.

    A session written before the masks were persisted has no PNG members at
    all; it must load unchanged, with both array fields None.
    """
    path = tmp_path / "legacy.aldic3d"
    session = {
        "schema_version": SCHEMA_VERSION,
        "config": None,
        "draft": {"roi": [10, 100, 20, 90], "winsize": 24},
        "view_state": {"display_field": "W"},
        "workflow_step": 3,
        "has_results": False,
    }
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("session.json", json.dumps(session))

    state = load_session(path)
    assert state.draft.roi == (10, 100, 20, 90)
    assert state.draft.winsize == 24
    assert state.draft.roi_mask_array is None
    assert state.draft.refinement_mask_array is None
    assert state.view_state == {"display_field": "W"}
    assert state.workflow_step == 3


def test_corrupt_mask_member_is_reported_not_swallowed(tmp_path):
    """A damaged PNG member must raise, never come back as a silent None."""
    from al_dic_3d.project.session import SessionError, parse_session

    path = save_session(
        AppState3D(draft=ProjectDraft(roi_mask_array=_shaped_roi_mask())),
        tmp_path / "bad.aldic3d",
    )
    member = _MASK_MEMBERS["roi_mask_array"]
    with zipfile.ZipFile(path) as zf:
        keep = {n: zf.read(n) for n in zf.namelist() if n != member}
    with zipfile.ZipFile(path, "w") as zf:
        for name, blob in keep.items():
            zf.writestr(name, blob)
        zf.writestr(member, b"not a png at all")
    with pytest.raises(SessionError, match="mask"):
        parse_session(path)


# ---------------------------------------------------------------------------
# Z2 — completeness audits: no field may silently skip persistence
# ---------------------------------------------------------------------------

# ProjectDraft fields that are deliberately NOT written to session.json, with
# the reason. The two mask arrays are not "transient" — they ride in the bundle
# as PNG members (_MASK_MEMBERS) because ndarrays are not JSON-serializable.
DRAFT_TRANSIENT: dict[str, str] = {}

# A distinctive, non-default value for EVERY ProjectDraft field. The
# completeness assertion below fails when a field is added without one, so a
# new field cannot be introduced without proving it round-trips.
DRAFT_DISTINCTIVE: dict[str, object] = {
    "calibration_file": Path("calib") / "stereo.yml",
    "calibration_format": "matlab_mat",
    "left": ["L_0.png", "L_1.png", "L_2.png"],
    "right": ["R_0.png", "R_1.png", "R_2.png"],
    "left_masks": ["ml_0.png", "ml_1.png", "ml_2.png"],
    "right_masks": ["mr_0.png", "mr_1.png", "mr_2.png"],
    "roi": (11, 131, 13, 97),
    "roi_mask_array": _shaped_roi_mask(),
    "strategy": "stereo_each_frame",
    "reference_mode": "incremental",
    "ref_update_mode": "custom",
    "ref_update_n": 4,
    "ref_update_frames": [0, 2, 5],
    "winsize": 40,
    "winstepsize": 12,
    "winsize_min": 6,
    "stereo_search": 61,
    "disparity_offset": (-7.5, 2.25),
    "init_guess": "previous",
    "seed_point": (33.5, 44.5),
    "seed_points": [(33.5, 44.5), (55.5, 66.5)],
    "quality_gate": True,
    "use_global_step": False,
    "admm_max_iter": 9,
    "fft_search": 27,
    "fft_auto_expand": False,
    "parallel_cameras": True,
    "refine_inner": True,
    "refine_outer": True,
    "refinement_level": 3,
    "refinement_mask_array": _brush_mask(),
    "compute_strain": False,
    "strain_size": 11,
    "output_dir": Path("out") / "runA",
    "output_prefix": "zbatch",
}


def test_every_draft_field_is_persisted_or_declared_transient():
    """The guard that would have caught the dropped masks.

    A new ``ProjectDraft`` field must land in ``session.json``, be carried as a
    bundle member, or be listed in ``DRAFT_TRANSIENT`` with a reason.
    """
    persisted = set(_draft_to_json(ProjectDraft())) | set(_MASK_MEMBERS)
    unaccounted = {f.name for f in fields(ProjectDraft)} - persisted - set(DRAFT_TRANSIENT)
    assert not unaccounted, (
        f"ProjectDraft field(s) {sorted(unaccounted)} are neither persisted in a "
        f"session nor declared transient. Persist them, or add them to "
        f"DRAFT_TRANSIENT with the reason."
    )


def test_draft_distinctive_values_cover_every_field():
    """Adding a draft field must force a distinctive value for the audit below."""
    missing = {f.name for f in fields(ProjectDraft)} - set(DRAFT_DISTINCTIVE)
    extra = set(DRAFT_DISTINCTIVE) - {f.name for f in fields(ProjectDraft)}
    assert not missing, f"give {sorted(missing)} a distinctive value in DRAFT_DISTINCTIVE"
    assert not extra, f"DRAFT_DISTINCTIVE lists unknown field(s) {sorted(extra)}"


@pytest.mark.parametrize("name", sorted(DRAFT_DISTINCTIVE))
def test_every_draft_field_round_trips(tmp_path, name):
    """Field by field: a distinctive value in comes back out."""
    draft = ProjectDraft(**DRAFT_DISTINCTIVE)  # type: ignore[arg-type]
    back = _saved(tmp_path, draft, f"draft_{name}.aldic3d")

    expected, got = getattr(draft, name), getattr(back, name)
    if name in _MASK_MEMBERS:
        assert np.array_equal(np.asarray(got) > 0, np.asarray(expected) > 0)
    else:
        assert got == expected
        assert type(got) is type(expected)  # tuple must not come back a list


# --- RunConfig -------------------------------------------------------------

CONFIG_DISTINCTIVE: dict[str, object] = {
    "calibration_file": Path("c") / "stereo.yml",
    "calibration_format": "matlab_mat",
    "left": ["L_0.png", "L_1.png"],
    "right": ["R_0.png", "R_1.png"],
    "roi": (11, 131, 13, 97),
    "output_dir": Path("out") / "runB",
    "roi_mask": Path("out") / "roi_mask.png",
    "left_masks": ["ml_0.png", "ml_1.png"],
    "right_masks": ["mr_0.png", "mr_1.png"],
    "strategy": "ref_direct",
    "reference_mode": "incremental",
    "ref_update_mode": "every_n",
    "ref_update_n": 4,
    "ref_update_frames": (0, 3, 7),
    "winsize": 40,
    "winstepsize": 12,
    "winsize_min": 6,
    "stereo_search": 61,
    "use_global_step": False,
    "admm_max_iter": 9,
    "fft_search": 27,
    "fft_auto_expand": False,
    "init_guess": "seed",
    "seed_point": (33.5, 44.5),
    "seed_points": ((33.5, 44.5), (55.5, 66.5)),
    "temporal_gate_znssd": 0.75,
    "parallel_cameras": True,
    "refine_inner": True,
    "refine_outer": True,
    "refinement_level": 3,
    "refinement_mask": Path("out") / "refinement_mask.png",
    "disparity_offset": (-7.5, 2.25),
    "quality_gate": True,
    "znssd_max": 0.42,
    "reproj_max_px": 1.25,
    "outlier_threshold": 2.5,
    "compute_strain": True,
    "strain_size": 11,
    "strain_smooth_sigma": 1.5,
    "ignore_memory_check": True,
    "output_prefix": "zbatch",
    "cam_left": "cam0",
    "cam_right": "cam1",
    "base_dir": Path("base") / "dir",
}


def test_config_distinctive_values_cover_every_field():
    from al_dic_3d.runner import RunConfig

    names = {f.name for f in fields(RunConfig)}
    assert not names - set(CONFIG_DISTINCTIVE), (
        f"give {sorted(names - set(CONFIG_DISTINCTIVE))} a distinctive value in "
        f"CONFIG_DISTINCTIVE so the round-trip audit covers it"
    )
    assert not set(CONFIG_DISTINCTIVE) - names


def test_every_runconfig_field_round_trips(tmp_path):
    """Frozen-dataclass equality covers every field at once (types included)."""
    from al_dic_3d.runner import RunConfig

    cfg = RunConfig(**CONFIG_DISTINCTIVE)  # type: ignore[arg-type]
    back = load_session(save_session(AppState3D(config=cfg), tmp_path / "cfg.aldic3d")).config

    assert back == cfg
    for name in sorted(CONFIG_DISTINCTIVE):
        got, expected = getattr(back, name), getattr(cfg, name)
        assert got == expected, name
        assert type(got) is type(expected), name


# --- AppState3D ------------------------------------------------------------

APPSTATE_PERSISTED = {"draft", "config", "result", "view_state", "workflow_step"}
APPSTATE_TRANSIENT = {
    "project_path": "set to the file just loaded, not read from it",
    "dirty": "loading yields a clean state by definition",
}


def test_every_appstate_field_is_accounted_for():
    names = {f.name for f in fields(AppState3D)}
    unaccounted = names - APPSTATE_PERSISTED - set(APPSTATE_TRANSIENT)
    assert not unaccounted, (
        f"AppState3D field(s) {sorted(unaccounted)} are neither persisted in a "
        f"session nor declared transient with a reason."
    )
    assert not (APPSTATE_PERSISTED | set(APPSTATE_TRANSIENT)) - names
