"""P0 gate: the ``al-dic-3d`` CLI is wired and ``--help`` / ``--version`` work.

The subprocess tests exercise the real ``python -m al_dic_3d`` entry point (the
same ``main`` the ``al-dic-3d`` console script calls), encoding the second half
of the Phase 0 gate ("al-dic-3d --help runs").
"""

from __future__ import annotations

import subprocess
import sys

import pytest

import al_dic_3d
from al_dic_3d.cli import build_parser, main


def test_help_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "al_dic_3d", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "al-dic-3d" in result.stdout


def test_version_flag_prints_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "al_dic_3d", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert al_dic_3d.__version__ in result.stdout


def test_main_no_args_returns_zero() -> None:
    # No sub-command in Phase 0 -> prints help and exits 0 (well-behaved no-op).
    assert main([]) == 0


def test_parser_exposes_version_action() -> None:
    parser = build_parser()
    # SystemExit(0) is argparse's contract for --version.
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])
    assert exc.value.code == 0
