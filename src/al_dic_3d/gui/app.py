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


def main(argv: list[str] | None = None) -> int:
    """Launch the GUI (blocks in the Qt event loop). Returns the exit code."""
    from al_dic_3d.gui.main_window import MainWindow3D

    app = create_app(argv)
    window = MainWindow3D()
    window.resize(1100, 720)
    window.show()
    return int(app.exec())
