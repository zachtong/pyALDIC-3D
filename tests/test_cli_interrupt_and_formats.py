"""Long headless runs keep what they computed (fix batch V, finding H3).

* Ctrl+C in ``al-dic-3d run`` used to kill the process and lose everything; the
  pipeline already supports a cooperative stop with partial results (the GUI
  used it), the CLI never wired it. The first Ctrl+C now finishes the frame in
  flight, writes the kept frames and exits 130.
* One failing output format (e.g. a MAT variable over MATLAB v5's 2 GB limit,
  discovered at the very end of a multi-hour run) no longer takes the other
  formats down with it, and the MAT writer checks the limit BEFORE writing.
"""

from __future__ import annotations

import dataclasses
import signal

import numpy as np
import pytest

pytest.importorskip("al_dic")

import al_dic_3d.runner as runner_mod  # noqa: E402
from al_dic_3d import cli  # noqa: E402
from al_dic_3d.export import tables  # noqa: E402
from al_dic_3d.runner import load_config, run_pipeline, write_results  # noqa: E402
from tests import synth_stereo  # noqa: E402


def test_first_ctrl_c_writes_partial_results_and_exits_130(tmp_path, monkeypatch, capsys):
    scene = synth_stereo.build_scene(tmp_path, n_frames=5)
    cfg_path = synth_stereo.write_config(tmp_path, scene)
    real = runner_mod.run_pipeline
    fired = {"done": False}

    def run_and_interrupt(cfg, progress=None, stop=None, **kw):
        def prog(frac, msg):
            if progress is not None:
                progress(frac, msg)
            # Deliver "Ctrl+C" once the LEFT track is past its second frame.
            if not fired["done"] and msg.startswith("L:") and "Frame 3/" in msg:
                fired["done"] = True
                signal.getsignal(signal.SIGINT)(signal.SIGINT, None)

        return real(cfg, progress=prog, stop=stop, **kw)

    monkeypatch.setattr(runner_mod, "run_pipeline", run_and_interrupt)
    code = cli.main(["run", str(cfg_path), "-q"])
    assert fired["done"]
    assert code == 130
    out_dir = load_config(cfg_path).output_dir
    npz = np.load(next(out_dir.glob("*.npz")))
    valid = np.isfinite(npz["points3D"]).all(axis=2).any(axis=1)
    # Every frame the left engine finished before the stop is kept (the gate
    # used to drop all but frame 1), and the right camera was tracked over them.
    assert valid[:3].all() and not valid.all()  # kept prefix, later frames empty
    assert "interrupt" in capsys.readouterr().err.lower()


def test_ctrl_c_handler_is_restored_after_the_run(tmp_path):
    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    cfg_path = synth_stereo.write_config(tmp_path, scene)
    before = signal.getsignal(signal.SIGINT)
    assert cli.main(["run", str(cfg_path), "-q"]) == 0
    assert signal.getsignal(signal.SIGINT) is before


def test_mat_limit_is_checked_before_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(tables, "MAT_V5_MAX_VAR_BYTES", 1024)
    arrays = {"small": np.zeros(10), "big": np.zeros(1000)}
    with pytest.raises(ValueError, match="big"):
        tables.save_mat_checked(tmp_path / "x.mat", arrays)
    assert not list(tmp_path.iterdir())  # no partial file


def test_one_failing_format_does_not_lose_the_others(tmp_path, monkeypatch):
    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    cfg = load_config(synth_stereo.write_config(tmp_path, scene))
    result = run_pipeline(cfg)
    monkeypatch.setattr(tables, "MAT_V5_MAX_VAR_BYTES", 8)
    errors: list[str] = []
    paths = write_results(
        result, dataclasses.replace(cfg), formats=("npz", "mat", "csv"), errors=errors
    )
    assert "npz" in paths and paths["npz"].exists()
    assert "csv" in paths and paths["csv"].exists()
    assert "mat" not in paths
    assert errors and errors[0].startswith("mat:")


def test_write_results_still_raises_without_an_error_list(tmp_path, monkeypatch):
    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    cfg = load_config(synth_stereo.write_config(tmp_path, scene))
    result = run_pipeline(cfg)
    monkeypatch.setattr(tables, "MAT_V5_MAX_VAR_BYTES", 8)
    with pytest.raises(ValueError):
        write_results(result, cfg, formats=("mat",))


def test_run_output_is_plain_ascii_when_redirected(tmp_path, monkeypatch):
    # Fix batch V: summary lines carry em dashes; redirected to a file on a
    # legacy code page they became mojibake (or crashed a cp437 console).
    import io

    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    cfg_path = synth_stereo.write_config(tmp_path, scene)
    raw = io.BytesIO()
    out = io.TextIOWrapper(raw, encoding="cp437", errors="strict")
    monkeypatch.setattr("sys.stdout", out)
    monkeypatch.setattr("sys.stderr", out)
    assert cli.main(["run", str(cfg_path)]) == 0
    out.flush()
    text = raw.getvalue().decode("cp437")
    assert "analysis complete - " in text and "\u2014" not in text
