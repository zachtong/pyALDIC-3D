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
        "addRow",
        "_set",  # this package's WorkflowPage helper
    }
)
# Brand-specific literals kept identical across ALL locales by design (the 2D
# app's convention): wrapping them in tr() would invite translators to vary a
# product acronym. Exact-match only — longer strings mentioning the brand are
# still prose and must be translated.
_LOCALE_INVARIANT = frozenset({"AL-DIC"})

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
    return any(ch.isalpha() for ch in s) and s not in _LOCALE_INVARIANT


_TR_NAMES = frozenset({"tr", "translate"})


def scan_file(path: Path) -> list[Leak]:
    """Return the untranslated / non-extractable strings in one Python source file.

    Two kinds of finding:
      * a bare user-facing string literal reaching a Qt view sink (unwrapped), and
      * a ``tr()`` / ``translate()`` call whose argument is NOT a literal — lupdate
        cannot extract it, so it would go untranslated in every locale.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    leaks: list[Leak] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func

        # tr()/translate() must take a string literal (lupdate extraction).
        tr_name = (
            func.attr
            if isinstance(func, ast.Attribute)
            else (func.id if isinstance(func, ast.Name) else None)
        )
        if tr_name in _TR_NAMES:
            first = node.args[-1] if node.args else None  # translate(ctx, text); tr(text)
            if first is not None and not (
                isinstance(first, ast.Constant) and isinstance(first.value, str)
            ):
                leaks.append(Leak(path, node.lineno, tr_name, "<non-literal tr() argument>"))
            continue

        if isinstance(func, ast.Attribute) and func.attr in _SINK_METHODS:
            sink = func.attr
        elif isinstance(func, ast.Name) and func.id in _SINK_CTORS:
            sink = func.id
        else:
            continue
        # Only the FIRST argument is the user-visible text (later args are
        # userData / widgets, e.g. addItem(tr("Label"), "id")); the WorkflowPage
        # helper ``_set(title, body)`` takes two user strings.
        check_args = node.args if sink == "_set" else node.args[:1]
        for arg in check_args:
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
