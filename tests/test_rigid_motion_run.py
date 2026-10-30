"""Rigid-motion removal through a whole run: config, pipeline, archive and session."""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import replace

import numpy as np
import pytest

from al_dic_3d.project.draft import ProjectDraft, encode_mask_png
from al_dic_3d.project.session import load_session, save_session
from al_dic_3d.project.state import AppState3D
from al_dic_3d.run_rigid import raw_reconstruction, with_rigid_motion
from al_dic_3d.runner import ARCHIVE_SCHEMA, load_config, run_pipeline
from tests import synth_stereo


@pytest.fixture(scope="module")
def scene(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("rbm_scene")
    data = synth_stereo.build_scene(tmp, n_frames=3)
    return tmp, synth_stereo.write_config(tmp, data)


@pytest.fixture(scope="module")
def cfg(scene):
    return load_config(scene[1])


@pytest.fixture(scope="module")
def off_result(cfg):
    return run_pipeline(cfg)


def _with_section(cfg_path, text: str):
    """A copy of the scene config (same folder) with ``text`` appended."""
    path = cfg_path.with_name(f"rbm_{abs(hash(text))}.toml")
    path.write_text(cfg_path.read_text("utf-8") + "\n" + text + "\n", encoding="utf-8")
    return path


def _left_half_mask(result) -> np.ndarray:
    h, w = result.meta["image_size"]
    mask = np.zeros((h, w), dtype=bool)
    mask[:, : int(np.nanmedian(result.ref_coords[:, 0]))] = True
    return mask


# --- config -----------------------------------------------------------------------


def test_config_reads_the_rigid_motion_section(scene):
    folder, cfg_path = scene
    plain = load_config(cfg_path)
    section = '[rigid_motion]\nmode = "rigid"\nregion_mask = "fit.png"'
    cfg = load_config(_with_section(cfg_path, section))

    assert (plain.rigid_motion_mode, plain.rigid_motion_region) == ("off", None)
    assert cfg.rigid_motion_mode == "rigid"
    assert cfg.rigid_motion_region == folder / "fit.png"


def test_config_rejects_an_unknown_mode(scene):
    with pytest.raises(ValueError, match="rigid_motion"):
        load_config(_with_section(scene[1], '[rigid_motion]\nmode = "affine"'))


# --- pipeline ---------------------------------------------------------------------


def test_off_leaves_the_run_untouched(off_result):
    assert off_result.rigid_motion is None
    assert "rigid_motion" not in off_result.meta


def test_translation_mode_runs_in_the_pipeline_and_keeps_the_raw_data(cfg, off_result):
    result = run_pipeline(replace(cfg, rigid_motion_mode="translation"))

    raw = result.rigid_motion.raw
    np.testing.assert_allclose(raw.points, off_result.reconstruction.points, rtol=0, atol=1e-12)
    for k in range(1, result.reconstruction.n_frames):
        d = result.reconstruction.displacement[k]
        assert np.allclose(np.nanmean(d, axis=0), 0.0, atol=1e-9)
    meta = result.meta["rigid_motion"]
    assert meta["mode"] == "translation" and meta["region"] == "all"
    json.dumps(result.meta, allow_nan=False)  # session.json / params export stay strict
    # The run summary describes the measurement, not the correction.
    assert result.meta["n_tracked_positions"] == off_result.meta["n_tracked_positions"]


def test_a_bad_region_fails_before_tracking(cfg, scene, off_result, tmp_path):
    h, w = off_result.meta["image_size"]
    wrong = tmp_path / "wrong.png"
    wrong.write_bytes(encode_mask_png(np.ones((h // 2, w), dtype=bool)))
    with pytest.raises(ValueError, match="rigid-motion region"):
        run_pipeline(replace(cfg, rigid_motion_mode="rigid", rigid_motion_region=wrong))

    tiny = np.zeros((h, w), dtype=bool)
    x, y = np.round(off_result.ref_coords[0]).astype(int)
    tiny[y, x] = True  # one node: rigid mode needs three
    one = tmp_path / "one.png"
    one.write_bytes(encode_mask_png(tiny))
    with pytest.raises(ValueError, match="at least 3"):
        run_pipeline(replace(cfg, rigid_motion_mode="rigid", rigid_motion_region=one))


def test_a_gui_run_follows_the_live_draft_setting(cfg):
    from al_dic_3d.gui.controller import WorkflowController

    c = WorkflowController()
    c.set_config(cfg)  # rigid motion is off in the config the run starts with...
    c.state.draft.rigid_motion_mode = "translation"  # ...and switched on meanwhile

    result = c.run()

    assert result.rigid_motion is not None
    assert result.rigid_motion.fit.mode == "translation"


# --- result-level switch ------------------------------------------------------------


def test_switching_always_refits_on_the_raw_reconstruction(off_result):
    assert with_rigid_motion(off_result, "off", None) is off_result

    rigid = with_rigid_motion(off_result, "rigid", None)
    assert rigid.rigid_motion.raw is off_result.reconstruction
    assert rigid.correspondence is off_result.correspondence  # same run

    region = _left_half_mask(off_result)
    trans = with_rigid_motion(rigid, "translation", region)
    assert trans.rigid_motion.raw is off_result.reconstruction
    assert trans.meta["rigid_motion"]["region"] == "drawn"
    assert raw_reconstruction(trans) is off_result.reconstruction

    back = with_rigid_motion(trans, "off", None)
    assert back.reconstruction is off_result.reconstruction
    assert back.rigid_motion is None and "rigid_motion" not in back.meta


# --- archive ----------------------------------------------------------------------


def test_the_archive_carries_the_fit_and_the_raw_points(off_result):
    from al_dic_3d.run_output import _arrays

    rigid = with_rigid_motion(off_result, "rigid", None)
    arrays = _arrays(rigid)
    n_frames = rigid.reconstruction.n_frames

    assert ARCHIVE_SCHEMA == 4
    assert arrays["rbm_rotation"].shape == (n_frames, 3, 3)
    assert arrays["rbm_translation"].shape == (n_frames, 3)
    assert arrays["rbm_rms"].shape == arrays["rbm_n_used"].shape == (n_frames,)
    assert str(arrays["rbm_mode"]) == "rigid"
    np.testing.assert_array_equal(arrays["points3D_raw"], off_result.reconstruction.points)
    np.testing.assert_array_equal(arrays["points3D"], rigid.reconstruction.points)
    assert not any(k.startswith("rbm_") or k.endswith("_raw") for k in _arrays(off_result))


# --- session ----------------------------------------------------------------------


def _saved_points(path) -> np.ndarray:
    with zipfile.ZipFile(path) as zf:
        return np.load(io.BytesIO(zf.read("results.npz")))["points3D"]


def test_session_saves_the_raw_data_and_reapplies_on_open(off_result, tmp_path):
    region = _left_half_mask(off_result)
    result = with_rigid_motion(off_result, "rigid", region)
    draft = ProjectDraft(rigid_motion_mode="rigid", rigid_motion_region_array=region)
    path = save_session(AppState3D(draft=draft, result=result), tmp_path / "rbm.aldic3d")

    np.testing.assert_array_equal(_saved_points(path), off_result.reconstruction.points)
    back = load_session(path)
    assert back.draft.rigid_motion_mode == "rigid"
    assert np.array_equal(back.draft.rigid_motion_region_array > 0, region)
    np.testing.assert_allclose(
        back.result.reconstruction.points, result.reconstruction.points, rtol=0, atol=1e-12
    )
    assert back.result.meta["rigid_motion"]["region"] == "drawn"


def test_a_region_that_no_longer_fits_opens_raw_with_a_note(off_result, tmp_path):
    empty = np.zeros(off_result.meta["image_size"], dtype=bool)
    empty[0, 0] = True  # covers no mesh node
    draft = ProjectDraft(rigid_motion_mode="rigid", rigid_motion_region_array=empty)
    path = save_session(AppState3D(draft=draft, result=off_result), tmp_path / "bad.aldic3d")

    back = load_session(path)

    assert back.result.rigid_motion is None
    raw_points = off_result.reconstruction.points
    np.testing.assert_array_equal(back.result.reconstruction.points, raw_points)
    assert any("rigid motion" in note for note in back.open_notes)
