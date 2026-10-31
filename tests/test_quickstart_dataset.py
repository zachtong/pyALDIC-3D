"""The shipped quickstart keeps working: real data, end to end.

Runs ``quickstart/config.toml`` the way the quickstart README's command-line
option does (in memory, no files written) and checks the figures that README
quotes, with margins for platform differences. Skipped where the dataset is
absent: the sdist does not ship it.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

QUICKSTART = Path(__file__).resolve().parents[1] / "quickstart"

pytestmark = pytest.mark.skipif(
    not (QUICKSTART / "config.toml").is_file(), reason="quickstart dataset not present"
)


def test_quickstart_config_reproduces_the_readme_figures():
    from al_dic_3d.runner import load_config, run_pipeline

    result = run_pipeline(load_config(QUICKSTART / "config.toml"))

    assert result.reconstruction.n_frames == 3
    # README: 6,490 mesh points (the grid covers every reference frame's mask) ...
    assert result.ref_coords.shape[0] == 6490
    assert result.meta["n_pts_in_roi"] == 4542  # ... 4,542 on the specimen
    valid = result.meta["summary"]["valid_frac"]
    assert min(valid) > 0.93, valid  # README: 97.3 / 97.1 / 96.4 %
    w = result.reconstruction.displacement[2][:, 2]  # W on frame 3, mm
    p2, p98 = np.nanpercentile(w, [2, 98])
    assert -0.8 < p2 < -0.55 and 0.6 < p98 < 0.85, (p2, p98)  # README: -0.68 to +0.71
    assert result.strain is not None
