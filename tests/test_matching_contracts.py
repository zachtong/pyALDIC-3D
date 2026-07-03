"""Tests for the correspondence contracts + strategy registry (Phase 1, step 4)."""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.matching import (
    INVALID,
    RESCUED,
    STEREO_REFRESH,
    STRATEGY_REGISTRY,
    TRACKED,
    CorrespondenceConfig,
    CorrespondenceSet,
    DisparityField,
    QualityGate,
    get_strategy,
)


def _set(n_frames=4, n_pts=10) -> CorrespondenceSet:
    return CorrespondenceSet.empty("track_both", n_frames, n_pts)


def test_source_codes_distinct():
    assert {TRACKED, STEREO_REFRESH, RESCUED, INVALID} == {0, 1, 2, 3}


def test_empty_set_is_all_invalid():
    cs = _set(4, 10)
    assert cs.n_frames == 4 and cs.n_pts == 10
    assert np.isnan(cs.xL).all() and np.isnan(cs.xR).all()
    assert (cs.source == INVALID).all()
    assert cs.source.dtype == np.uint8


def test_set_shape_validation():
    good = _set()
    CorrespondenceSet(good.strategy, good.xL, good.xR, good.quality, good.source)  # ok
    with pytest.raises(ValueError, match="xL/xR must be equal"):
        CorrespondenceSet(
            "s",
            np.zeros((2, 3, 2)),
            np.zeros((2, 4, 2)),
            np.zeros((2, 3)),
            np.zeros((2, 3), np.uint8),
        )
    with pytest.raises(ValueError, match="quality/source must be"):
        CorrespondenceSet(
            "s",
            np.zeros((2, 3, 2)),
            np.zeros((2, 3, 2)),
            np.zeros((2, 5)),
            np.zeros((2, 3), np.uint8),
        )


def test_disparity_field_right_pts():
    left = np.array([[10.0, 20.0], [30.0, 40.0]])
    d = np.array([[-5.0, 0.5], [-6.0, -0.2]])
    df = DisparityField(frame_idx=0, left_pts=left, d=d, znssd=np.zeros(2), valid=np.ones(2, bool))
    assert np.allclose(df.right_pts, left + d)
    assert df.frame_idx == 0


def test_config_defaults_and_frozen():
    cfg = CorrespondenceConfig()
    assert cfg.strategy == "track_both"
    assert cfg.stereo_solver == "local_only"
    assert cfg.epipolar_seed is True
    assert isinstance(cfg.quality, QualityGate)
    with pytest.raises(AttributeError):
        cfg.strategy = "other"  # type: ignore[misc]


def test_quality_gate_defaults():
    q = QualityGate()
    assert q.znssd_max > 0 and q.reproj_max_px > 0 and 0 < q.min_valid_frac <= 1


def test_strategy_registry(monkeypatch):
    # Isolate the global registry so the dummy does not leak into other tests.
    monkeypatch.setattr("al_dic_3d.matching.strategy.STRATEGY_REGISTRY", {}, raising=True)

    from al_dic_3d.matching import strategy as strat_mod

    @strat_mod.register_strategy
    class _Dummy:
        name = "dummy"

        def compute(self, seq, rig, mesh_L, cfg, progress=None, stop=None):  # noqa: D401
            return None

    assert strat_mod.get_strategy("dummy") is _Dummy
    with pytest.raises(ValueError, match="unknown strategy"):
        strat_mod.get_strategy("nope")
    with pytest.raises(ValueError, match="already registered"):
        strat_mod.register_strategy(type("Other", (), {"name": "dummy"}))


def test_track_both_resolves_via_registry():
    # track_both self-registers on demand; unknown names still raise.
    assert isinstance(STRATEGY_REGISTRY, dict)
    cls = get_strategy("track_both")
    assert cls.name == "track_both"
    assert hasattr(cls, "compute")
    with pytest.raises(ValueError, match="unknown strategy"):
        get_strategy("definitely_not_a_strategy")
