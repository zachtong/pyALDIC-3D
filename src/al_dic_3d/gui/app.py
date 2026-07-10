"""Qt application entry point for the pyALDIC-3D GUI.

``create_app`` builds (or reuses) the ``QApplication`` and installs the
translators; ``main`` shows the :class:`MainWindow3D`. Kept split so a headless
test can build the app (offscreen) without entering the event loop.
"""

from __future__ import annotations


def create_app(argv: list[str] | None = None):
    """Return a configured ``QApplication`` (reusing an existing instance)."""
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.i18n import install_translators

    app = QApplication.instance() or QApplication(argv if argv is not None else [])
    app.setApplicationName("pyALDIC-3D")
    app.setOrganizationName("pyALDIC")
    _apply_theme(app)

    from PySide6.QtCore import QSettings

    saved = QSettings("pyALDIC", "pyALDIC-3D").value("language", None)
    install_translators(app, locale=str(saved) if saved else None)
    return app


def _apply_theme(app) -> None:
    """Apply the shared pyALDIC dark-navy theme (reused from the 2D repo)."""
    try:
        from al_dic.gui.theme import build_stylesheet
    except ImportError:
        return  # theme is cosmetic; run un-themed if the 2D theme is unavailable
    app.setStyle("Fusion")  # QSS renders correctly on the Fusion style
    app.setStyleSheet(build_stylesheet())


def install_excepthook(signals):
    """Install a ``sys.excepthook`` that reports instead of dying silently (G1.7).

    2D port (``al_dic`` gui/app.py): an unhandled exception in a Qt slot would
    otherwise kill or zombify the GUI with nothing on screen. The hook prints
    the full traceback to stderr (bug reports) AND surfaces a one-line CRASH
    message in the GUI console via ``signals.log``. Re-entrant crashes (the
    logging path itself failing) fall back to stderr only. Returns the hook.
    """
    import sys
    import traceback

    handling = False

    def _hook(exc_type, exc_value, exc_tb) -> None:
        nonlocal handling
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(f"\n{'=' * 60}", file=sys.stderr, flush=True)
        print("UNHANDLED EXCEPTION — this would normally crash the GUI:", file=sys.stderr)
        print(tb_str, file=sys.stderr, flush=True)
        print(f"{'=' * 60}\n", file=sys.stderr, flush=True)
        if handling:
            return  # re-entrancy guard: the GUI logging path itself crashed
        handling = True
        try:
            signals.log.emit(f"CRASH: {exc_type.__name__}: {exc_value}", "error")
        except Exception:  # noqa: BLE001, S110 - the hook must never raise
            pass
        finally:
            handling = False

    sys.excepthook = _hook
    return _hook


def main(argv: list[str] | None = None) -> int:
    """Launch the GUI (blocks in the Qt event loop). Returns the exit code."""
    from al_dic_3d.gui.main_window import MainWindow3D

    app = create_app(argv)
    window = MainWindow3D()  # sizes itself to the available screen (G1.4)
    install_excepthook(window.signals)  # G1.7: crashes are reported, not silent
    window.show()
    return int(app.exec())
