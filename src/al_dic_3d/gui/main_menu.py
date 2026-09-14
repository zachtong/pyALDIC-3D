"""Menu bar of the main window: File / Settings / Help (mixin for MainWindow3D).

Split out of :mod:`al_dic_3d.gui.main_window` (fix batch V, file-size rule).
Fix batch V also changed three behaviours here:

* the Language menu checks the language the interface is actually shown in
  (it used to check English whenever no preference was saved, even when the
  interface followed a non-English system language), and a change says, in the
  new language's absence, that it applies after a restart;
* Recent Projects keeps entries whose drive or share is unreachable right now
  (an unplugged disk used to drop them for good) and shows them disabled;
* Help gains a User Guide entry (the online guide the installer also links).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMessageBox

from al_dic_3d.gui import persistence

# The online user guide (the installer's Start-menu shortcut opens it too).
USER_GUIDE_URL = "https://github.com/zachtong/pyALDIC-3D/blob/main/docs/user-guide/index.md"

_LANGUAGE_NAMES = {
    "en": "English",
    "zh_CN": "简体中文",
    "zh_TW": "繁體中文",
    "ja": "日本語",
    "ko": "한국어",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
}


def effective_language(saved: str | None, system_name: str, locales) -> str:
    """The locale the interface is shown in: the saved choice, else the system's.

    Mirrors :func:`al_dic_3d.i18n.install_translators`, which tries the full
    system name (``zh_CN``) and then its language part (``de`` for ``de_DE``);
    anything without a catalog is shown in English.
    """
    if saved:
        return str(saved)
    for candidate in (system_name, system_name.split("_")[0]):
        if candidate in locales:
            return candidate
    return "en"


class MainMenuMixin:
    """File / Settings / Help menus for :class:`~al_dic_3d.gui.main_window.MainWindow3D`."""

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr("&File"))

        new_action = QAction(self.tr("New Project"), self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        self._new_action = new_action

        open_action = QAction(self.tr("Open Project…"), self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        self._open_action = open_action

        # G3.2: last-8 recent .aldic3d files, rebuilt on show.
        self._recent_menu = file_menu.addMenu(self.tr("Recent Projects"))
        self._recent_menu.aboutToShow.connect(self._populate_recent_menu)
        self._populate_recent_menu()

        # G2.8: Save writes straight to the bound .aldic3d (no dialog); Save As
        # is the explicit re-target with its own shortcut.
        save_action = QAction(self.tr("Save Project"), self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)  # Ctrl+S
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)

        save_as_action = QAction(self.tr("Save Project As…"), self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)

        # Q6: Windows per-user .aldic3d file association (2D port; HKCU only).
        from al_dic_3d.gui import file_association

        if file_association.is_supported():
            file_menu.addSeparator()
            assoc_action = QAction(self.tr("Associate .aldic3d files with pyALDIC-3D…"), self)
            assoc_action.setToolTip(
                self.tr(
                    "Register .aldic3d so double-clicking a project file opens "
                    "pyALDIC-3D (current user only, no admin rights needed)."
                )
            )
            assoc_action.triggered.connect(self._on_register_association)
            file_menu.addAction(assoc_action)

        file_menu.addSeparator()
        quit_action = QAction(self.tr("Quit"), self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        self._build_language_menu()

        # G3.9: Help menu — the user guide, the shortcut reference and About.
        help_menu = self.menuBar().addMenu(self.tr("&Help"))
        guide_action = QAction(self.tr("User Guide"), self)
        guide_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        guide_action.triggered.connect(self._show_user_guide)
        help_menu.addAction(guide_action)
        shortcuts_action = QAction(self.tr("Keyboard Shortcuts"), self)
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)
        about_action = QAction(self.tr("About pyALDIC-3D"), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_language_menu(self) -> None:
        """Settings > Language (8-locale contract; catalogs compile via tools/i18n.py)."""
        from PySide6.QtCore import QLocale
        from PySide6.QtGui import QActionGroup

        from al_dic_3d.i18n import LOCALES

        settings_menu = self.menuBar().addMenu(self.tr("&Settings"))
        language_menu = settings_menu.addMenu(self.tr("Language"))
        # G3.11: exclusive QActionGroup — radio look, and the check state moves
        # to the clicked locale immediately (the restart note still applies).
        self._language_group = QActionGroup(self)
        self._language_group.setExclusive(True)
        saved = persistence.settings().value("language", None)
        current = effective_language(saved, QLocale.system().name(), LOCALES)
        for code in LOCALES:
            act = QAction(_LANGUAGE_NAMES.get(code, code), self)
            act.setCheckable(True)
            act.setChecked(code == current)
            act.triggered.connect(lambda _c=False, code=code: self._on_language(code))
            self._language_group.addAction(act)
            language_menu.addAction(act)

    def _on_register_association(self) -> None:
        """Q6: register the per-user .aldic3d association; report the outcome."""
        from al_dic_3d.gui import file_association

        try:
            file_association.register_association()
        except (OSError, RuntimeError) as exc:
            QMessageBox.warning(
                self,
                self.tr("File Association"),
                self.tr("Could not register the .aldic3d association: {0}").format(exc),
            )
            return
        QMessageBox.information(
            self,
            self.tr("File Association"),
            self.tr(
                "Done — double-clicking a .aldic3d file now opens it in "
                "pyALDIC-3D (registered for the current user)."
            ),
        )

    def _on_language(self, code: str) -> None:
        """Persist the language preference; it applies on the next launch."""
        persistence.settings().setValue("language", code)
        name = _LANGUAGE_NAMES.get(code, code)
        message = self.tr("The interface language changes to {0} after pyALDIC-3D restarts.")
        self.signals.log.emit(message.format(name), "info")
        self._notify_language_change(message.format(name))

    def _notify_language_change(self, message: str) -> None:
        """Modal note (split out so tests can stub it)."""
        QMessageBox.information(self, self.tr("Language"), message)

    def _show_user_guide(self) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        if not QDesktopServices.openUrl(QUrl(USER_GUIDE_URL)):
            self.signals.log.emit(
                self.tr("Could not open a web browser. The user guide is at {0}").format(
                    USER_GUIDE_URL
                ),
                "warning",
            )

    def _show_about(self) -> None:
        from al_dic_3d.gui.dialogs.about_dialog import AboutDialog

        AboutDialog(self).exec()

    def _show_shortcuts(self) -> None:
        from al_dic_3d.gui.dialogs.about_dialog import ShortcutsDialog

        ShortcutsDialog(self).exec()

    # ---- recent projects (G3.2) --------------------------------------------------

    def _populate_recent_menu(self) -> None:
        """Rebuild Recent Projects; unreachable entries stay, disabled."""
        self._recent_menu.clear()
        paths = persistence.recent_projects()
        for i, path in enumerate(paths):
            reachable = Path(path).exists()
            label = f"&{i + 1}  {path}"
            if not reachable:
                label += "  " + self.tr("(not reachable)")
            act = QAction(label, self)
            act.setEnabled(reachable)
            act.triggered.connect(lambda _c=False, p=path: self._open_recent(p))
            self._recent_menu.addAction(act)
        if not paths:
            empty = QAction(self.tr("No recent projects"), self)
            empty.setEnabled(False)
            self._recent_menu.addAction(empty)
        self._recent_menu.addSeparator()
        clear = QAction(self.tr("Clear list"), self)
        clear.setEnabled(bool(paths))
        clear.triggered.connect(persistence.clear_recent_projects)
        self._recent_menu.addAction(clear)

    def _open_recent(self, path: str) -> None:
        if not Path(path).exists():  # unreachable since the menu was built
            self.signals.log.emit(
                self.tr("The project file is not reachable right now: {0}").format(path),
                "warning",
            )
            return
        if not self._stop_run_before_switch():
            return
        if not self._confirm_unsaved():
            return
        self._open_project_path(path)
