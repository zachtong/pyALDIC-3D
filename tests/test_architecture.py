"""Architecture guardrails (01 invariants + 02 §5.2).

Enforced by source scan so a future edit that breaks a layering rule fails CI:

1. Downstream modules (reconstruct/strain3d/viz3d/export) consume ONLY the
   ``CorrespondenceSet`` contract — never a concrete strategy or the registry.
2. Compute modules (and viz3d) stay Qt-free and never import
   ``al_dic.utils.locale_format``.
3. pyvista/VTK stays behind the ``[viz3d]`` extra: export/viz3d may import it
   only lazily inside functions, never at module top level.
4. UTF-8 discipline (alien-env batch G3): text-mode file I/O must pass
   ``encoding=`` explicitly — Windows otherwise defaults to the ANSI code
   page and mangles CJK content in logs/CSVs/session JSON.
5. Path-based OpenCV I/O is banned outside :mod:`al_dic_3d.pathsafe` (G3):
   ``cv2.imread``/``cv2.imwrite``/path-mode ``cv2.FileStorage`` silently fail
   on non-ASCII Windows paths — use the pathsafe wrappers.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src" / "al_dic_3d"

_DOWNSTREAM = ["reconstruct", "strain3d", "viz3d", "export"]
_COMPUTE = ["calibration", "sequence", "matching", "reconstruct", "strain3d", "export"]
_QT_FREE = [*_COMPUTE, "viz3d"]
_LAZY_PYVISTA = ["export", "viz3d"]

# Depending on a concrete strategy or the registry from downstream breaks the wall.
_FORBIDDEN_DOWNSTREAM = re.compile(
    r"matching\.strategy|STRATEGY_REGISTRY|register_strategy|get_strategy|\w+Strategy\b"
)
# Qt / display-layer imports forbidden in compute modules.
_FORBIDDEN_QT = re.compile(r"import\s+PySide6|from\s+PySide6|locale_format")


def _py_files(pkg: str) -> list[Path]:
    return list((_SRC / pkg).rglob("*.py"))


@pytest.mark.parametrize("pkg", _DOWNSTREAM)
def test_downstream_does_not_import_strategies(pkg: str):
    for f in _py_files(pkg):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("#", 1)[0]
            assert not _FORBIDDEN_DOWNSTREAM.search(code), (
                f"{f.relative_to(_SRC)}:{i} downstream module references a concrete "
                f"strategy/registry — it may consume only CorrespondenceSet: {line.strip()!r}"
            )


@pytest.mark.parametrize("pkg", _QT_FREE)
def test_compute_modules_are_qt_free(pkg: str):
    for f in _py_files(pkg):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            assert not _FORBIDDEN_QT.search(line), (
                f"{f.relative_to(_SRC)}:{i} compute module imports Qt: {line.strip()!r}"
            )


@pytest.mark.parametrize("pkg", _LAZY_PYVISTA)
def test_pyvista_is_imported_lazily(pkg: str):
    # Column-0 import = module level; indented imports (inside functions) are fine.
    top_level = re.compile(r"^(import pyvista|from pyvista)")
    for f in _py_files(pkg):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            assert not top_level.match(line), (
                f"{f.relative_to(_SRC)}:{i} pyvista must be a lazy in-function import "
                f"([viz3d] extra): {line.strip()!r}"
            )


def _has_encoding_kwarg(call: ast.Call) -> bool:
    return any(kw.arg == "encoding" for kw in call.keywords)


def _text_io_offences(tree: ast.AST) -> list[ast.Call]:
    """Text-mode I/O calls missing ``encoding=`` (precise, no false positives).

    Flags ``Path.read_text``/``write_text`` without ``encoding=`` and builtin
    ``open()`` in a text mode without ``encoding=``. Method ``.open(...)``
    calls are not flagged: the two in src are binary (``path.open("rb")``,
    zipfile member writes), and their modes are positionally ambiguous.
    """
    bad: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr in (
            "read_text",
            "write_text",
        ):
            if not _has_encoding_kwarg(node):
                bad.append(node)
        elif isinstance(node.func, ast.Name) and node.func.id == "open":
            mode = "r"
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = str(node.args[1].value)
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            if "b" not in mode and not _has_encoding_kwarg(node):
                bad.append(node)
    return bad


def test_text_io_specifies_encoding():
    """G3 UTF-8 discipline: every text write/read must pin ``encoding=``.

    Windows defaults text I/O to the ANSI code page (cp1252 / cp936 / ...),
    which corrupts CJK characters in exported CSV headers, session JSON and
    logs the moment a user's language differs from the author's.
    """
    offenders: list[str] = []
    for f in _SRC.rglob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for call in _text_io_offences(tree):
            offenders.append(f"{f.relative_to(_SRC)}:{call.lineno}")
    assert not offenders, (
        "text-mode I/O without encoding= (Windows would use the ANSI code page): "
        + ", ".join(offenders)
    )


def test_no_path_based_cv2_io_outside_pathsafe():
    """G3: cv2's char*-path APIs silently fail on non-ASCII Windows paths.

    ``cv2.imread`` returns None, ``cv2.imwrite`` returns False without
    writing, and path-mode ``cv2.FileStorage`` cannot open — every call site
    must go through :mod:`al_dic_3d.pathsafe` instead. (``cv2.VideoWriter``
    is exempt: its FFMPEG backend handles UTF-8 paths, regression-pinned in
    tests/test_alien_paths.py.)
    """
    banned = re.compile(r"cv2\.(imread|imwrite|FileStorage)\s*\(")
    offenders: list[str] = []
    for f in _SRC.rglob("*.py"):
        if f.name == "pathsafe.py":
            continue  # the single sanctioned home (memory-mode FileStorage)
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("#", 1)[0]
            if banned.search(code):
                offenders.append(f"{f.relative_to(_SRC)}:{i}")
    assert not offenders, (
        "path-based cv2 I/O outside pathsafe (fails on non-ASCII Windows paths): "
        + ", ".join(offenders)
    )
