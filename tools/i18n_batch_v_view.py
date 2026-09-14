"""Translation batch V-view (viewer performance): new user-facing strings.

``BATCH`` maps locale -> {English source -> translation}, in the format the
maintainers merge into ``tools/fill_translations.py``. Terminology follows the
existing catalog entries ("3D View" = 3D 视图 / 3D 檢視 / 3D ビュー / 3D 보기 /
3D-Ansicht / Vue 3D / Vista 3D).

Strings moved between modules by this batch keep their exact English source
(``CanvasArea3D`` -> ``CanvasRenderMixin``), so the source-keyed fill table
already covers them and they need no entry here.
"""

# ruff: noqa: RUF001  (intentional full-width punctuation)

from __future__ import annotations

BATCH: dict[str, dict[str, str]] = {
    "zh_CN": {
        "Starting the 3D view…": "正在启动 3D 视图…",
    },
    "zh_TW": {
        "Starting the 3D view…": "正在啟動 3D 檢視…",
    },
    "ja": {
        "Starting the 3D view…": "3D ビューを起動しています…",
    },
    "ko": {
        "Starting the 3D view…": "3D 보기를 시작하는 중…",
    },
    "de": {
        "Starting the 3D view…": "3D-Ansicht wird gestartet…",
    },
    "fr": {
        "Starting the 3D view…": "Démarrage de la vue 3D…",
    },
    "es": {
        "Starting the 3D view…": "Iniciando la vista 3D…",
    },
}
