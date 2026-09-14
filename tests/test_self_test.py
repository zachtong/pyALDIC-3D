"""``al-dic-3d self-test`` -- the frozen-bundle gate (task 5).

packaging/build_installer.ps1 and .github/workflows/build-exe.yml depend on the
contract: one ``[ok]/[FAIL]/[skip] name: detail`` line per check, exit 0 when
nothing failed (skips pass) and 1 otherwise, ``--json`` report, ASCII-only
stdout even from a non-ASCII working directory through a legacy code page, and
``ALDIC3D_SELFTEST_SKIP_GL=1`` skipping only the OpenGL render check.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

import al_dic_3d  # noqa: E402
from al_dic_3d import self_test as st  # noqa: E402
from al_dic_3d.cli import main as cli_main  # noqa: E402

_CHECK_LINE = re.compile(r"^\[(ok|FAIL|skip)\] ([a-z0-9_]+): (.+)$")
_NAMES = [name for name, _ in st.CHECKS]


def _skip(reason: str):
    def check() -> str:
        raise st.CheckSkipped(reason)

    return check


def _fail(detail: str):
    def check() -> str:
        raise st.CheckFailed(detail)

    return check


def _boom() -> str:
    raise RuntimeError("unexpected ü failure")


# ---------------------------------------------------------------------------
# The command, end to end, the way the installer build runs it
# ---------------------------------------------------------------------------


def test_self_test_command_passes_from_a_hostile_directory(tmp_path):
    hostile = tmp_path / "self-test 自检 été"
    hostile.mkdir()
    report = tmp_path / "报告 report.json"
    env = {
        **os.environ,
        "ALDIC3D_SELFTEST_SKIP_GL": "1",  # the CI runner setting
        "PYTHONIOENCODING": "ascii",  # stricter than any legacy code page
    }
    proc = subprocess.run(
        [sys.executable, "-m", "al_dic_3d", "self-test", "--json", str(report)],
        cwd=hostile,
        env=env,
        capture_output=True,
        timeout=900,
        check=False,
    )
    out = proc.stdout.decode("ascii")  # raises on any non-ASCII byte
    assert proc.returncode == 0, out + proc.stderr.decode("utf-8", "replace")
    lines = [ln for ln in out.splitlines() if ln.startswith("[")]
    matches = [_CHECK_LINE.match(ln) for ln in lines]
    assert all(matches), lines
    assert [m.group(2) for m in matches] == _NAMES  # exactly one line per check, in order
    statuses = {m.group(2): m.group(1) for m in matches}
    assert statuses["render3d_offscreen"] == "skip"
    assert all(s == "ok" for n, s in statuses.items() if n != "render3d_offscreen")
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["passed"] is True and data["version"] == al_dic_3d.__version__
    assert [c["name"] for c in data["checks"]] == _NAMES


def test_version_flag_is_exact():
    proc = subprocess.run(
        [sys.executable, "-m", "al_dic_3d", "--version"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == f"al-dic-3d {al_dic_3d.__version__}"


# ---------------------------------------------------------------------------
# Driver contract (fast, in-process)
# ---------------------------------------------------------------------------


def test_a_failing_check_exits_1_and_is_reported(tmp_path, capsys):
    report = tmp_path / "r.json"
    checks = [("good", lambda: "fine"), ("bad", _fail("disk says 不")), ("boom", _boom)]
    assert st.run_self_test(report, checks=checks) == 1
    out = capsys.readouterr().out
    out.encode("ascii")  # ASCII only
    assert "[ok] good: fine" in out
    assert "[FAIL] bad: disk says \\u4e0d" in out
    assert "[FAIL] boom: RuntimeError: unexpected \\xfc failure" in out
    assert "\n    Traceback (most recent call last):" in out  # indented, not a check line
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["passed"] is False
    assert [c["status"] for c in data["checks"]] == ["ok", "FAIL", "FAIL"]
    assert data["checks"][1]["detail"] == "disk says 不"  # the JSON keeps the real text
    assert "RuntimeError" in data["checks"][2]["traceback"]


def test_skipped_checks_count_as_passes(capsys):
    assert st.run_self_test(None, checks=[("a", lambda: "x"), ("b", _skip("no GPU"))]) == 0
    out = capsys.readouterr().out
    assert "[ok] a: x" in out and "[skip] b: no GPU" in out
    assert "1 passed, 1 skipped, 0 failed" in out


def test_multiline_details_stay_on_one_line():
    result = st.CheckResult("x", "FAIL", "first\n  second 试\n", 0.0)
    assert st.format_line(result) == "[FAIL] x: first | second \\u8bd5"


def test_an_unwritable_json_report_fails_the_run(tmp_path, capsys):
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")
    assert st.run_self_test(blocker / "sub" / "r.json", checks=[("a", lambda: "x")]) == 1
    out = capsys.readouterr().out
    assert "[FAIL] json_report:" in out
    assert "1 passed, 0 skipped, 1 failed" in out  # the summary never says "0 failed" here


def test_cli_forwards_the_json_path(monkeypatch, tmp_path):
    seen: dict = {}

    def fake(json_path=None, checks=None):
        seen["json"] = json_path
        return 0

    monkeypatch.setattr(st, "run_self_test", fake)
    assert cli_main(["self-test", "--json", str(tmp_path / "r.json")]) == 0
    assert seen["json"] == str(tmp_path / "r.json")


def test_cli_exits_1_when_a_check_fails(monkeypatch, capsys):
    monkeypatch.setattr(st, "CHECKS", [("ok_one", lambda: "fine"), ("broken", _fail("forced"))])
    assert cli_main(["self-test"]) == 1
    assert "[FAIL] broken: forced" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Individual checks, in-process
# ---------------------------------------------------------------------------


@pytest.fixture
def scratch(monkeypatch, tmp_path):
    monkeypatch.setattr(st, "_SCRATCH", tmp_path)
    return tmp_path


_FAST = [n for n in _NAMES if n not in ("render3d_offscreen", "mini_stereo")]


@pytest.mark.parametrize("name", _FAST)
def test_check_passes_here(name, scratch):
    detail = dict(st.CHECKS)[name]()
    assert isinstance(detail, str) and detail


def test_all_locales_leaves_the_app_in_english(scratch):
    from PySide6.QtCore import QCoreApplication

    st.check_all_locales()
    assert QCoreApplication.translate(*st.PROBE_3D) == st.PROBE_3D[1]


def test_packaged_data_catches_a_missing_catalog(scratch, monkeypatch, tmp_path):
    import al_dic_3d.i18n as i18n

    monkeypatch.setattr(i18n, "compiled_qm", lambda loc: tmp_path / f"gone_{loc}.qm")
    with pytest.raises(st.CheckFailed, match="zh_CN"):
        st.check_packaged_data()


def test_mini_stereo_check_passes(scratch):
    detail = st.check_mini_stereo()
    assert "coverage" in detail and "um" in detail


def test_mini_stereo_check_fails_on_poor_accuracy(scratch, monkeypatch):
    monkeypatch.setitem(st.MINI_TOL, "disp_median_mm", 1e-9)
    with pytest.raises(st.CheckFailed, match="displacement error"):
        st.check_mini_stereo()


def test_render_check_honours_the_skip_variable(monkeypatch):
    monkeypatch.setenv(st.SKIP_GL_ENV, "1")
    with pytest.raises(st.CheckSkipped, match=st.SKIP_GL_ENV):
        st.check_render3d_offscreen()


def test_self_test_render3d_check_renders(monkeypatch):
    # "render3d" in the name: skipped on GL-less hosted Windows/macOS runners.
    monkeypatch.delenv(st.SKIP_GL_ENV, raising=False)
    assert "VTK" in st.check_render3d_offscreen()
