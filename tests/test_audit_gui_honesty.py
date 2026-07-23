"""Adversarial-audit GUI/display honesty fixes (A4-1, A4-2, A6-2, A5-1, A5-3).

Pure (Qt-free) checks of the FFT-activity helper and the shared auto-range
reduction, plus offscreen GUI checks that the temporal-FFT knobs grey out when
inert, that the temporal tooltip reports the Auto-expand reach honestly, and
that the Almansi strain label is disambiguated from the 2D linearized form.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

from al_dic_3d.export.render import field_color_range
from al_dic_3d.gui.fft_activity import fft_controls_active
from al_dic_3d.matching.contracts import TRACKED, CorrespondenceSet
from al_dic_3d.project.draft import ProjectDraft
from al_dic_3d.reconstruct import Reconstruction3D
from al_dic_3d.runner import RunResult
from al_dic_3d.viz3d.fieldmap import auto_range, visible_values

Z0 = 800.0


# ---------------------------------------------------------------------------
# A4-1 — the FFT-activity predicate (Qt-free)
# ---------------------------------------------------------------------------


def test_fft_controls_active_truth_table():
    def draft(mode: str, guess: str) -> ProjectDraft:
        return ProjectDraft(reference_mode=mode, init_guess=guess)

    # Accumulative + seed/previous: external mesh + non-None U0 -> engine never
    # runs FFT -> knobs inert.
    assert not fft_controls_active(draft("accumulative", "seed"))
    assert not fft_controls_active(draft("accumulative", "previous"))
    # FFT seeding (U0=None) always runs FFT on frame 1.
    assert fft_controls_active(draft("accumulative", "fft"))
    # Incremental: every frame is a reference switch -> forced FFT regardless of
    # the init-guess selection.
    assert fft_controls_active(draft("incremental", "seed"))
    assert fft_controls_active(draft("incremental", "previous"))
    assert fft_controls_active(draft("incremental", "fft"))


# ---------------------------------------------------------------------------
# A5-1 / A5-3 — canvas, strain window and export share ONE auto-range rule
# ---------------------------------------------------------------------------


def _result_with_outliers(nx: int = 9, step_px: float = 16.0) -> RunResult:
    """Flat plane whose frame-1 U field carries two far outlier nodes."""
    ii, jj = np.meshgrid(np.arange(nx), np.arange(nx))
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * step_px + 40.0, jj * step_px + 40.0])
    ref_3d = np.column_stack([ii * 2.0, jj * 2.0, np.full(ii.shape, Z0, float)])
    n_pts = ref_2d.shape[0]

    u1 = np.full(n_pts, 0.5)
    u1[0] = 50.0  # a high outlier and ...
    u1[-1] = -50.0  # ... a low outlier: min/max != 2-98 percentile
    disp1 = np.column_stack([u1, np.zeros(n_pts), np.zeros(n_pts)])
    points = np.stack([ref_3d, ref_3d + disp1])
    displacement = points - points[0][None]
    n_frames = points.shape[0]

    rec = Reconstruction3D(
        points,
        displacement,
        np.zeros((n_frames, n_pts)),
        np.full((n_frames, n_pts), TRACKED, np.uint8),
    )
    x_img = np.stack([ref_2d] * n_frames)
    cs = CorrespondenceSet(
        strategy="track_both",
        xL=x_img.copy(),
        xR=x_img.copy(),
        quality=np.zeros((n_frames, n_pts)),
        source=np.full((n_frames, n_pts), TRACKED, np.uint8),
    )
    return RunResult(
        strategy="track_both",
        ref_coords=ref_2d,
        correspondence=cs,
        reconstruction=rec,
        strain=None,
        meta={},
    )


@pytest.mark.parametrize("with_mask", [False, True])
def test_canvas_export_strain_auto_ranges_agree(with_mask):
    result = _result_with_outliers()
    cs = result.correspondence
    ref_pts = cs.xL[0]
    vals = result.reconstruction.displacement[1][:, 0]  # field_frame(result,"U",1)

    roi_mask = None
    if with_mask:
        # A mask covering the whole node hull (still exercises visible_values).
        roi_mask = np.zeros((400, 400), bool)
        roi_mask[30:200, 30:200] = True

    # The one shared reduction the canvas AND the strain window both call.
    canvas_auto = auto_range(visible_values(vals, ref_pts, roi_mask))
    strain_auto = auto_range(visible_values(vals, ref_pts, roi_mask))
    export_auto = field_color_range(result, "L", "U", 1, roi_mask)

    assert canvas_auto == pytest.approx(export_auto)
    assert strain_auto == pytest.approx(export_auto)

    # A5-3: the fix is real — the shared range is the 2-98 percentile, NOT the
    # plain min/max the export used to compute (which the outliers stretch).
    finite = vals[np.isfinite(vals)]
    plain_minmax = (float(finite.min()), float(finite.max()))
    assert plain_minmax == pytest.approx((-50.0, 50.0))
    assert export_auto != pytest.approx(plain_minmax)
    assert -50.0 < export_auto[0] and export_auto[1] < 50.0  # outliers clipped


# ---------------------------------------------------------------------------
# Offscreen GUI checks (A4-1 enable-state, A4-2 tooltip, A6-2 label)
# ---------------------------------------------------------------------------

pytest.importorskip("PySide6")

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402
from al_dic_3d.gui.widgets.strain_param_panel import StrainParamPanel3D  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def test_fft_knobs_grey_out_when_inert(qapp):
    win = MainWindow3D()
    left = win._left

    # Default draft is accumulative + Starting Point -> knobs inert -> disabled.
    assert not left._temporal_spin.isEnabled()
    assert not left._fft_expand_cb.isEnabled()
    assert "no effect" in left._fft_expand_cb.toolTip()
    assert "Inactive" in left._temporal_spin.toolTip()

    # Selecting FFT seeding activates both, and clears the honest inactive note.
    left._init_guess_widget._rb_fft.setChecked(True)
    assert win.controller.state.draft.init_guess == "fft"
    assert left._temporal_spin.isEnabled() and left._fft_expand_cb.isEnabled()
    assert "no effect" not in left._fft_expand_cb.toolTip()

    # Back to Starting Point -> inert again; incremental mode re-activates them
    # (every frame is a reference switch -> forced FFT).
    left._init_guess_widget._rb_seed.setChecked(True)
    assert not left._temporal_spin.isEnabled()
    left._mode_combo.setCurrentIndex(left._mode_combo.findData("incremental"))
    assert win.controller.state.draft.reference_mode == "incremental"
    assert left._temporal_spin.isEnabled() and left._fft_expand_cb.isEnabled()
    win.close()


def test_temporal_tooltip_reports_autoexpand_reach(qapp, tmp_path):
    import cv2

    p = tmp_path / "L0.png"
    cv2.imwrite(str(p), np.zeros((200, 200), np.uint8))

    win = MainWindow3D()
    left = win._left
    draft = win.controller.state.draft
    draft.left = [str(p)]
    draft.winsize = 32
    # FFT mode so the tooltip shows the caps without the A4-1 inactive suffix.
    draft.init_guess = "fft"
    left._update_search_tooltips()
    tip = left._temporal_spin.toolTip()

    # A4-2: the run-start clamp (max(10, 200/4 - 32) = 18) must NOT be sold as
    # the detectable-motion cap; Auto-expand can grow to max(32, 200/2) = 100.
    assert "Auto-expand" in tip
    assert "18" in tip and "100" in tip
    win.close()


def test_almansi_label_disambiguated_but_code_unchanged(qapp):
    panel = StrainParamPanel3D(winstepsize=16)
    combo = panel._type_combo

    # A6-2: renamed so a 2D-vs-3D comparison cannot confuse it with the 2D
    # app's identically-labelled linearized 'Eulerian-Almansi' formula.
    assert combo.itemText(2) == "Almansi (Eulerian, true tensor)"
    assert combo.itemText(2) != "Eulerian-Almansi"
    assert "22%" in combo.toolTip()

    # The compute code path is untouched: index 2 still maps to 'almansi'.
    panel._type_combo.setCurrentIndex(2)
    assert panel.strain_type() == "almansi"
    assert panel.get_override()["strain_type"] == "almansi"
    panel.deleteLater()
