"""P0 gate: the package and every module skeleton import cleanly.

These tests encode the first half of the Phase 0 gate ("import al_dic_3d works").
They must stay green through every later phase — a broken module import or a
compute module that accidentally grows a Qt dependency will fail here.
"""

from __future__ import annotations

import importlib

import pytest

# The ten modules of the §B.1 package layout.
SUBMODULES = [
    "project",
    "calibration",
    "sequence",
    "matching",
    "reconstruct",
    "strain3d",
    "export",
    "viz3d",
    "gui",
    "i18n",
]


def test_package_imports_and_has_version() -> None:
    import al_dic_3d

    assert isinstance(al_dic_3d.__version__, str)
    assert al_dic_3d.__version__  # non-empty


@pytest.mark.parametrize("name", SUBMODULES)
def test_submodule_imports(name: str) -> None:
    module = importlib.import_module(f"al_dic_3d.{name}")
    assert module is not None
