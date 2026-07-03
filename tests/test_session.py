"""`.aldic3d` session save/load round-trip (Phase 4 gate: session round-trip).

A project (RunConfig + a completed RunResult incl. strain + UI view state) must
survive a save -> load cycle byte-faithfully, so closing the GUI never loses a run.
Also checks schema-version and non-bundle rejection.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from al_dic_3d.project import (
    SCHEMA_VERSION,
    AppState3D,
    SessionError,
    load_session,
    parse_session,
    save_session,
)

cv2 = pytest.importorskip("cv2")

from tests import synth_parity  # noqa: E402  (after importorskip guard)


@pytest.fixture(scope="module")
def computed(tmp_path_factory):
    d = tmp_path_factory.mktemp("session_src")
    scene = synth_parity.build_parity_scene(d, img=300, n_frames=3, seed=7)
    from al_dic_3d.runner import load_config, run_pipeline

    cfg = replace(load_config(synth_parity.write_config(d, scene)), compute_strain=True)
    result = run_pipeline(cfg)
    return cfg, result


def test_config_only_round_trip(tmp_path, computed):
    cfg, _ = computed
    state = AppState3D(config=cfg, view_state={"field": "exx", "frame": 2}, workflow_step=4)
    path = save_session(state, tmp_path / "proj.aldic3d")

    loaded = load_session(path)
    assert loaded.config == cfg  # frozen RunConfig equality (paths/tuples restored)
    assert loaded.view_state == {"field": "exx", "frame": 2}
    assert loaded.workflow_step == 4
    assert loaded.result is None
    assert loaded.dirty is False
    assert loaded.project_path == path


def test_full_round_trip_with_results(tmp_path, computed):
    cfg, result = computed
    state = AppState3D(config=cfg, result=result, workflow_step=6)
    loaded = load_session(save_session(state, tmp_path / "full.aldic3d"))

    assert loaded.has_results
    r0, r1 = result, loaded.result
    assert r1.strategy == r0.strategy
    assert np.array_equal(r1.correspondence.xL, r0.correspondence.xL, equal_nan=True)
    assert np.array_equal(r1.correspondence.source, r0.correspondence.source)
    assert np.array_equal(
        r1.reconstruction.displacement, r0.reconstruction.displacement, equal_nan=True
    )
    assert np.array_equal(r1.reconstruction.source, r0.reconstruction.source)
    # strain survives the round-trip
    assert r1.strain is not None
    assert np.array_equal(r1.strain.von_mises, r0.strain.von_mises, equal_nan=True)
    assert r1.meta.get("strategy") == r0.meta.get("strategy")


def test_parse_separates_from_apply(tmp_path, computed):
    cfg, result = computed
    data = parse_session(
        save_session(AppState3D(config=cfg, result=result), tmp_path / "p.aldic3d")
    )
    assert data.schema_version == SCHEMA_VERSION
    assert data.config == cfg
    assert data.result_arrays is not None and "points3D" in data.result_arrays


def test_non_bundle_rejected(tmp_path):
    plain = tmp_path / "not.aldic3d"
    plain.write_text("just text", encoding="utf-8")
    with pytest.raises(SessionError, match="not a .aldic3d bundle"):
        parse_session(plain)


def test_unknown_schema_rejected(tmp_path):
    import json
    import zipfile

    bad = tmp_path / "future.aldic3d"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("session.json", json.dumps({"schema_version": 999, "has_results": False}))
    with pytest.raises(SessionError, match="unsupported session schema"):
        parse_session(bad)
