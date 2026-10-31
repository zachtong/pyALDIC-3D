"""Post-run summary written into the log console (mixin for RightSidebar3D).

Split out of :mod:`al_dic_3d.gui.panels.right_sidebar` (fix batch V, file-size
rule). ``self.tr`` resolves through the class hierarchy at runtime, so the
strings keep working under this class's translation context.
"""

from __future__ import annotations


class RunSummaryMixin:
    """F3.1 post-run accounting for :class:`RightSidebar3D`."""

    def _log_run_summary(self) -> None:
        """F3.1: the post-run failure accounting, written into the log console.

        Mirrors :func:`al_dic_3d.matching.diagnostics.summary_lines` (the CLI
        wording) with tr()-wrapped templates: frame-1 stereo stats, honesty-gate
        kills with the reason, low-validity frames, quality-gate demotions, and
        a one-line verdict. An all-empty run logs an ERROR, never a quiet
        'complete'.
        """
        result = self.controller.state.result
        if result is None:
            self._append_log(self.tr("Analysis complete"), "success")
            return
        from al_dic_3d.matching.diagnostics import LOW_VALIDITY_FRAC, summarize_run

        s = summarize_run(
            result.correspondence,
            result.reconstruction.points,
            n_eligible=(result.meta or {}).get("n_pts_in_roi"),
        )
        # R2 (engine 0.7 partial results): a cancelled-but-kept run announces
        # itself FIRST — one honest line saying how many frames survived.
        meta = result.meta or {}
        if meta.get("stopped_early"):
            k = int(meta.get("stopped_at_frame") or 0)
            self._append_log(
                self.tr(
                    "Stopped early at frame {0}/{1} — kept {2} computed frames "
                    "(later frames are empty)"
                ).format(k, s.n_frames, k),
                "warn",
            )
        elif meta.get("stop_reason"):
            self._append_log(self.tr("Run interrupted: {0}").format(meta["stop_reason"]), "warn")
        if s.stereo_n_pts:
            frac = s.stereo_n_valid / s.stereo_n_pts
            self._append_log(
                self.tr("Frame-1 stereo match: {0}/{1} points matched ({2}%)").format(
                    s.stereo_n_valid, s.stereo_n_pts, f"{frac * 100:.0f}"
                ),
                "warn" if frac < LOW_VALIDITY_FRAC else "info",
            )
        self._log_stereo_check(s, meta.get("run_params") or {})
        for cam, n in sorted(s.gated_by_cam.items()):
            self._append_log(
                self.tr(
                    "Camera {0}: validity gate removed {1} node-frames "
                    "(correlation vs frame 1 failed)"
                ).format(cam, n),
                "warn",
            )
        for k in s.low_frames:
            self._append_log(
                self.tr("Frame {0}: only {1}% of points valid").format(
                    k, f"{s.valid_frac[k] * 100:.0f}"
                ),
                "warn",
            )
        gates = result.meta.get("gates") or {}
        for key, template in (
            ("znssd_demoted", self.tr("Quality gate (ZNSSD) removed {0} positions")),
            ("reproj_demoted", self.tr("Reprojection gate removed {0} positions")),
            ("outliers_removed", self.tr("3D outlier filter removed {0} positions")),
        ):
            n = int(gates.get(key, 0))
            if n:
                self._append_log(template.format(n), "info")
        from al_dic_3d.matching.diagnostics import collapse_advice, widening_advice

        run_params = meta.get("run_params") or {}
        for cam, n in widening_advice(s).items():
            if run_params.get("per_frame_masks"):
                text = self.tr(
                    "Camera {0}: the initial-guess search had to widen on {1} frames "
                    "(up to {2} px), which slows the run. If the motion between "
                    "reference frames is that large, raise PARAMETERS > Temporal Search."
                )
            else:
                text = self.tr(
                    "Camera {0}: the initial-guess search had to widen on {1} frames "
                    "(up to {2} px), which slows the run. In incremental mode this "
                    "usually means the frame-1 region no longer covers the specimen at "
                    "later reference frames: import per-frame masks (REGION OF "
                    "INTEREST) or use WORKFLOW TYPE > Accumulative."
                )
            self._append_log(text.format(cam, n, s.fft_max_search_px), "warn")
        advice = collapse_advice(
            s,
            run_params.get("reference_mode"),
            run_params.get("ref_update_mode"),
            bool(run_params.get("per_frame_masks", False)),
        )
        if advice is not None:
            start = f"{s.valid_frac[1] * 100:.0f}"
            worst = f"{min(s.valid_frac[2:]) * 100:.0f}"
            if advice == "incremental":
                text = self.tr(
                    "Validity falls from {0}% (frame 1) to {1}%: tracking every frame "
                    "against frame 1 cannot follow large deformation. Try WORKFLOW "
                    "TYPE > Incremental."
                )
            elif advice == "fewer_updates":
                text = self.tr(
                    "Validity falls from {0}% (frame 1) to {1}%: every reference update "
                    "adds a small tracking error, and over a long sequence they add up. "
                    "Try fewer updates (Reference Update > Every N Frames, e.g. 10) or "
                    "WORKFLOW TYPE > Accumulative."
                )
            else:
                text = self.tr(
                    "Validity falls from {0}% (frame 1) to {1}%: if the valid region "
                    "changes during the test (cracks, failure), import per-frame masks "
                    "(REGION OF INTEREST)."
                )
            self._append_log(text.format(start, worst), "warn")
        if s.all_empty:
            self._append_log(
                self.tr(
                    "No valid points in ANY frame — the run produced an empty "
                    "result. Check ROI, masks and seeding (details above)."
                ),
                "error",
            )
        elif s.low_frames:
            self._append_log(
                self.tr(
                    "Analysis complete — {0} frames, median validity {1}%, "
                    "{2} frame(s) below {3}% (see above)"
                ).format(
                    s.n_frames,
                    f"{s.median_valid_frac * 100:.0f}",
                    len(s.low_frames),
                    f"{LOW_VALIDITY_FRAC * 100:.0f}",
                ),
                "success",
            )
        else:
            # Nothing flagged: no "(see above)" pointing at nothing (fix batch V).
            self._append_log(
                self.tr("Analysis complete — {0} frames, median validity {1}%").format(
                    s.n_frames, f"{s.median_valid_frac * 100:.0f}"
                ),
                "success",
            )

    def _log_stereo_check(self, s, run_params: dict) -> None:
        """The frame-1 stereo check's removals and, when they are many, the cause.

        GitHub issue #1: the check compares the two cameras, not frame k with
        frame 1, and on a rough surface seen at a large stereo angle it removed
        most of the correct links without naming the threshold; a calibration
        that does not match the images shows as a large median epipolar residual.
        """
        from al_dic_3d.matching.diagnostics import stereo_check_advice
        from al_dic_3d.matching.stereo import STEREO_EPIPOLAR_MAX_PX, STEREO_ZNSSD_MAX

        zmax = float(run_params.get("stereo_znssd_max") or STEREO_ZNSSD_MAX)
        emax = float(run_params.get("stereo_epipolar_max_px") or STEREO_EPIPOLAR_MAX_PX)
        if s.stereo_rejected_znssd or s.stereo_rejected_epipolar:
            self._append_log(
                self.tr(
                    "Stereo check removed {0} links for weak left-right correlation "
                    "(ZNSSD above {1}) and {2} for epipolar distance (above {3} px)."
                ).format(
                    s.stereo_rejected_znssd, f"{zmax:g}", s.stereo_rejected_epipolar, f"{emax:g}"
                ),
                "info",
            )
        advice = stereo_check_advice(s, emax)
        if advice == "calibration":
            median = s.stereo_epipolar_median_px
            text = (
                self.tr(
                    "The frame-1 stereo links lie a median {0} px from their epipolar "
                    "lines: the calibration probably does not match these images (a "
                    "camera moved, a wrong file, or left and right swapped). Check or "
                    "redo the calibration."
                ).format(f"{median:.1f}")
                if median is not None
                else self.tr(
                    "Many frame-1 stereo links lie off their epipolar lines: the "
                    "calibration probably does not match these images (a camera moved, "
                    "a wrong file, or left and right swapped). Check or redo the "
                    "calibration."
                )
            )
            self._append_log(text, "warn")
        elif advice == "raise_znssd":
            self._append_log(
                self.tr(
                    "Correct stereo links can correlate weakly on a rough or strongly "
                    "inclined surface. If points are missing, raise ADVANCED > Result "
                    "checks > Stereo check (for example to 1.0)."
                ),
                "warn",
            )
