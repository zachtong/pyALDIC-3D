"""Static i18n scan — the enforceable proxy for the pseudo-locale gate.

A user-facing string literal that reaches a Qt view sink (``setText``,
``addAction``, ``showMessage``, a ``QLabel(...)`` ctor, ...) WITHOUT being wrapped
in ``tr()`` / ``translate()`` would show up untranslated under any locale. This
AST scan flags exactly those bare literals so a test can assert the GUI is clean
(the static equivalent of a runtime pseudo-locale sweep).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

# The 8-locale contract (en is the source language; the rest are translated).
LOCALES = ("en", "zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es")
TARGET_LOCALES = tuple(loc for loc in LOCALES if loc != "en")

# Method calls whose string argument is shown to the user.
_SINK_METHODS = frozenset(
    {
        "setText",
        "setWindowTitle",
        "setToolTip",
        "setStatusTip",
        "setPlaceholderText",
        "setTitle",
        "setLabel",
        "setLabelText",
        "setWhatsThis",
        "showMessage",
        "addItem",
        "insertItem",
        "addTab",
        "addAction",
        "addMenu",
        "setTabText",
        "_set",  # this package's WorkflowPage helper
    }
)
# Widget constructors whose first string argument is user-facing.
_SINK_CTORS = frozenset(
    {
        "QLabel",
        "QPushButton",
        "QCheckBox",
        "QRadioButton",
        "QGroupBox",
        "QAction",
        "QMenu",
        "QToolButton",
        "QCommandLinkButton",
    }
)


@dataclass(frozen=True)
class Leak:
    """An untranslated user-facing string literal."""

    file: Path
    line: int
    sink: str
    text: str


def _is_user_facing(s: str) -> bool:
    return any(ch.isalpha() for ch in s)


def scan_file(path: Path) -> list[Leak]:
    """Return the untranslated user-facing literals in one Python source file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    leaks: list[Leak] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in _SINK_METHODS:
            sink = func.attr
        elif isinstance(func, ast.Name) and func.id in _SINK_CTORS:
            sink = func.id
        else:
            continue
        for arg in node.args:
            if (
                isinstance(arg, ast.Constant)
                and isinstance(arg.value, str)
                and _is_user_facing(arg.value)
            ):
                leaks.append(Leak(path, arg.lineno, sink, arg.value))
    return leaks


def scan_tree(root: Path) -> list[Leak]:
    """Scan every ``.py`` under ``root`` for untranslated user-facing literals."""
    leaks: list[Leak] = []
    for path in sorted(Path(root).rglob("*.py")):
        leaks.extend(scan_file(path))
    return leaks
