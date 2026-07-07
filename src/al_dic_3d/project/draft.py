"""``ProjectDraft`` — the mutable, incrementally-edited project configuration.

The GUI fills the reproducible inputs across several workflow pages (calibration,
sequences, ROI, correspondence settings), so it needs a MUTABLE draft; the frozen
:class:`~al_dic_3d.runner.RunConfig` is assembled from it via :meth:`build` only
once every requirement is present. :meth:`issues` reports what is still missing so
a page can enable/disable its "next"/"run" affordance. Qt-free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from al_dic_3d.runner import RunConfig


@dataclass
class ProjectDraft:
    """User-editable project inputs, assembled into a RunConfig on demand."""

    calibration_file: Path | None = None
    calibration_format: str = "opencv_yaml"
    left: list[str] = field(default_factory=list)  # explicit image paths (sorted)
    right: list[str] = field(default_factory=list)
    left_masks: list[str] | None = None
    right_masks: list[str] | None = None
    roi: tuple[int, int, int, int] | None = None  # (xmin, xmax, ymin, ymax)
    strategy: str = "track_both"
    reference_mode: str = "accumulative"
    winsize: int = 32
    winstepsize: int = 16
    winsize_min: int = 8
    stereo_search: int = 48
    disparity_offset: tuple[float, float] | None = None
    quality_gate: bool = False
    use_global_step: bool = True  # AL-DIC global step (ADMM), audit default
    admm_max_iter: int = 3
    refine_inner: bool = False  # quadtree: refine mask-boundary elements
    refine_outer: bool = False  # quadtree: refine ROI-edge elements
    refinement_level: int = 1  # 1=light .. 3=heavy (min elem = step // 2**level)
    refinement_mask_array: object | None = field(default=None, repr=False)
    # ^ brush-painted (H, W) array from the canvas; written to a PNG at build()
    compute_strain: bool = True
    strain_size: int = 5
    output_dir: Path | None = None
    output_prefix: str = "run"

    def issues(self) -> list[str]:
        """English descriptions of what is missing/invalid (empty == ready)."""
        problems: list[str] = []
        if self.calibration_file is None:
            problems.append("calibration file not set")
        if not self.left or not self.right:
            problems.append("left/right sequences not set")
        elif len(self.left) != len(self.right):
            problems.append(f"sequence length mismatch: {len(self.left)} vs {len(self.right)}")
        elif len(self.left) < 2:
            problems.append("need at least 2 frames")
        if self.roi is None:
            problems.append("ROI not set")
        elif not (self.roi[0] < self.roi[1] and self.roi[2] < self.roi[3]):
            problems.append("ROI is empty (xmin<xmax, ymin<ymax required)")
        return problems

    def is_ready(self) -> bool:
        return not self.issues()

    def _write_refinement_mask(self, out_dir: Path) -> Path | None:
        """Persist the brush-painted refinement mask (if any) next to the run."""
        if self.refinement_mask_array is None:
            return None
        import cv2
        import numpy as np

        arr = (np.asarray(self.refinement_mask_array) > 0).astype("uint8") * 255
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "refinement_mask.png"
        cv2.imwrite(str(path), arr)
        return path

    def build(self) -> RunConfig:
        """Assemble a validated :class:`RunConfig`; raise if requirements are unmet."""
        problems = self.issues()
        if problems:
            raise ValueError("project not ready: " + "; ".join(problems))
        from al_dic_3d.runner import RunConfig

        assert self.calibration_file is not None and self.roi is not None
        out_dir = self.output_dir or self.calibration_file.parent / "out"
        return RunConfig(
            calibration_file=self.calibration_file,
            calibration_format=self.calibration_format,
            left=list(self.left),
            right=list(self.right),
            roi=tuple(self.roi),  # type: ignore[arg-type]
            output_dir=out_dir,
            left_masks=list(self.left_masks) if self.left_masks else None,
            right_masks=list(self.right_masks) if self.right_masks else None,
            strategy=self.strategy,
            reference_mode=self.reference_mode,
            winsize=self.winsize,
            winstepsize=self.winstepsize,
            winsize_min=self.winsize_min,
            stereo_search=self.stereo_search,
            disparity_offset=self.disparity_offset,
            quality_gate=self.quality_gate,
            use_global_step=self.use_global_step,
            admm_max_iter=self.admm_max_iter,
            refine_inner=self.refine_inner,
            refine_outer=self.refine_outer,
            refinement_level=self.refinement_level,
            refinement_mask=self._write_refinement_mask(out_dir),
            compute_strain=self.compute_strain,
            strain_size=self.strain_size,
            output_prefix=self.output_prefix,
            base_dir=self.calibration_file.parent,
        )
