"""``al-dic-3d demo OUT`` -- a first run with zero downloads (task 4).

The command writes a synthetic stereo dataset (images, calibration,
config.toml) and prints the exact next command; ``--run`` also runs it and
reports the accuracy against the analytic ground truth. Folders with spaces,
non-ASCII characters and glob metacharacters must work, and a folder holding
someone else's files is never written into.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

import numpy as np
import pytest

from al_dic_3d import synthetic
from al_dic_3d.cli import build_parser, main
from al_dic_3d.pathsafe import imread_unicode
from al_dic_3d.runner import load_config


def test_demo_is_a_registered_command():
    args = build_parser().parse_args(["demo", "out", "--frames", "3", "--size", "200", "--run"])
    assert (args.command, args.out, args.frames, args.size, args.run) == (
        "demo",
        "out",
        3,
        200,
        True,
    )


def test_demo_writes_a_dataset_and_prints_the_next_command(tmp_path, capsys):
    out = tmp_path / "demo 数据 été [1]"
    assert main(["demo", str(out), "--frames", "3", "--size", "192"]) == 0
    printed = capsys.readouterr().out
    for name in ("config.toml", "calib.yml", "L_000.png", "L_002.png", "R_000.png", "R_002.png"):
        assert (out / name).is_file(), name
    assert not (out / "L_003.png").exists()
    assert imread_unicode(out / "L_001.png").shape == (192, 192)
    config = out / "config.toml"
    run_line = next(ln for ln in printed.splitlines() if "al-dic-3d run " in ln)
    assert str(config) in run_line  # the exact next command, quoted for the shell
    cfg = load_config(config)
    assert cfg.left == ["L_000.png", "L_001.png", "L_002.png"]  # explicit: no glob pitfalls
    assert cfg.compute_strain and cfg.output_dir == config.resolve().parent / "results"


def test_demo_defaults_are_small(tmp_path):
    out = tmp_path / "defaults"
    assert main(["demo", str(out)]) == 0
    frames = sorted(p.name for p in out.glob("L_*.png"))
    assert len(frames) == 4
    assert imread_unicode(out / frames[0]).shape == (320, 320)


def test_demo_run_reports_the_accuracy(tmp_path, capsys):
    out = tmp_path / "试样 run"
    assert main(["demo", str(out), "--frames", "3", "--size", "240", "--run"]) == 0
    printed = capsys.readouterr().out
    line = next(ln for ln in printed.splitlines() if "accuracy vs analytic ground truth" in ln)
    median_um = float(re.search(r"median ([0-9.]+) um", line).group(1))
    assert 0.0 <= median_um < 80.0  # the synthetic parity gate's tolerance
    assert "coverage 100%" in line
    assert (out / "results" / "demo.npz").is_file()
    with np.load(out / "results" / "demo.npz") as npz:
        assert npz["points3D"].shape[0] == 3


def test_demo_can_rewrite_its_own_folder(tmp_path):
    out = tmp_path / "again"
    assert main(["demo", str(out), "--frames", "4", "--size", "160"]) == 0
    (out / "notes.txt").write_text("mine", encoding="utf-8")  # not a demo frame
    assert main(["demo", str(out), "--frames", "2", "--size", "160"]) == 0
    assert load_config(out / "config.toml").left == ["L_000.png", "L_001.png"]
    assert synthetic.is_synthetic_dataset(out)
    # the frames of the larger earlier run are gone; anything else is left alone
    assert sorted(p.name for p in out.glob("*.png")) == [
        "L_000.png",
        "L_001.png",
        "R_000.png",
        "R_001.png",
    ]
    assert (out / "notes.txt").read_text(encoding="utf-8") == "mine"


def test_demo_run_reports_a_pipeline_failure_cleanly(tmp_path, monkeypatch, capsys):
    from al_dic_3d import runner

    def broken(cfg, progress=None, stop=None, **kwargs):  # noqa: ARG001
        raise RuntimeError("numba kernels unavailable")

    monkeypatch.setattr(runner, "run_pipeline", broken)
    assert main(["demo", str(tmp_path / "x"), "--frames", "2", "--size", "160", "--run"]) == 1
    err = capsys.readouterr().err
    assert "error: the demo run failed: RuntimeError: numba kernels unavailable" in err
    assert "al-dic-3d self-test" in err


def test_demo_refuses_a_folder_with_other_files(tmp_path, capsys):
    out = tmp_path / "my project"
    out.mkdir()
    (out / "calib.yml").write_text("precious", encoding="utf-8")
    assert main(["demo", str(out)]) == 2
    assert "not empty" in capsys.readouterr().err
    assert (out / "calib.yml").read_text(encoding="utf-8") == "precious"
    assert not (out / "config.toml").exists()


def test_demo_refuses_a_file(tmp_path, capsys):
    target = tmp_path / "a file.txt"
    target.write_text("x", encoding="utf-8")
    assert main(["demo", str(target)]) == 2
    assert "not a folder" in capsys.readouterr().err


@pytest.mark.parametrize(
    "extra",
    [["--frames", "1"], ["--frames", "101"], ["--size", "100"], ["--size", "5000"]],
)
def test_demo_rejects_out_of_range_options(tmp_path, capsys, extra):
    assert main(["demo", str(tmp_path / "x"), *extra]) == 2
    assert "error:" in capsys.readouterr().err
    assert not (tmp_path / "x").exists()


def test_demo_reports_a_write_failure(tmp_path, monkeypatch, capsys):
    def refuse(*args, **kwargs):  # noqa: ARG001
        raise OSError("disk full")

    monkeypatch.setattr(synthetic, "build_scene", refuse)
    assert main(["demo", str(tmp_path / "x")]) == 1
    assert "could not write the demo dataset: disk full" in capsys.readouterr().err


def test_echo_escapes_what_the_console_cannot_encode(monkeypatch):
    import io

    from al_dic_3d import cli

    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1252", errors="strict")
    monkeypatch.setattr(sys, "stdout", stream)
    cli._echo("wrote 试样 été")
    stream.flush()
    assert raw.getvalue().decode("cp1252").strip() == "wrote \\u8bd5\\u6837 été"
    monkeypatch.setattr(sys, "stdout", None)  # pythonw: printing is a no-op
    cli._echo("nothing to print to")


def test_quote_follows_the_platform_shell(monkeypatch):
    from pathlib import Path

    from al_dic_3d import cli

    config = Path("C:/data/my demo/config.toml")
    monkeypatch.setattr(sys, "platform", "win32")
    assert cli._quote(config) == f'"{config}"'
    assert cli._quote(Path("C:/data/demo/config.toml")) == str(Path("C:/data/demo/config.toml"))
    monkeypatch.setattr(sys, "platform", "linux")
    assert cli._quote(Path("my demo/config.toml")) in (
        "'my demo/config.toml'",
        "'my demo\\config.toml'",
    )


def test_demo_output_survives_a_legacy_code_page(tmp_path):
    out = tmp_path / "demo 自检 été"
    env = {**os.environ, "PYTHONIOENCODING": "cp1252"}  # cannot encode the CJK characters
    proc = subprocess.run(
        [sys.executable, "-m", "al_dic_3d", "demo", str(out), "--frames", "2", "--size", "160"],
        capture_output=True,
        env=env,
        timeout=300,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert (out / "config.toml").is_file()
    assert b"al-dic-3d run" in proc.stdout
