"""Architecture guardrails (01 invariants + 02 §5.2).

Enforced by source scan so a future edit that breaks a layering rule fails CI:

1. Downstream modules (reconstruct/strain3d/viz3d/export) consume ONLY the
   ``CorrespondenceSet`` contract — never a concrete strategy or the registry.
2. Compute modules stay Qt-free and never import ``al_dic.utils.locale_format``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src" / "al_dic_3d"

_DOWNSTREAM = ["reconstruct", "strain3d", "viz3d", "export"]
_COMPUTE = ["calibration", "sequence", "matching", "reconstruct", "strain3d", "export"]

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


@pytest.mark.parametrize("pkg", _COMPUTE)
def test_compute_modules_are_qt_free(pkg: str):
    for f in _py_files(pkg):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            assert not _FORBIDDEN_QT.search(line), (
                f"{f.relative_to(_SRC)}:{i} compute module imports Qt: {line.strip()!r}"
            )
