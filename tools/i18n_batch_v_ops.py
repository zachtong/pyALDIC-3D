"""Batch V "frozen-application operations" translations, for merging into the catalogs.

The H2 fix (crash dialog + background kernel warm-up, ``src/al_dic_3d/gui/app.py``)
adds these user-facing strings, all in the ``Application`` translation context.
Merge ``BATCH`` into ``tools/fill_translations.py``'s ``TRANSLATIONS`` table, then
refresh and compile the catalogs (``python tools/i18n.py``). Placeholders
(``{0}``) must survive verbatim; terminology follows the existing al_dic_3d
catalogs (project = 项目 / 專案 / プロジェクト / 프로젝트 / Projekt / projet /
proyecto). tests/test_i18n_batch_v_ops.py keeps this table in step with app.py.
"""
# ruff: noqa: E501, RUF001  (long translation lines; intentional full-width punctuation)

from __future__ import annotations

BATCH: dict[str, dict[str, str]] = {
    "zh_CN": {
        "pyALDIC-3D has hit an error": "pyALDIC-3D 遇到错误",
        "An unexpected error occurred. The application may not behave correctly from here on, so saving your project and restarting is recommended.": "发生了意外错误。此后程序可能无法正常工作，建议保存项目并重新启动。",
        "Details were written to {0}": "详细信息已写入 {0}",
        "Preparing compute kernels in the background…": "正在后台准备计算内核…",
        "Compute kernels ready ({0} s).": "计算内核已就绪（{0} 秒）。",
    },
    "zh_TW": {
        "pyALDIC-3D has hit an error": "pyALDIC-3D 發生錯誤",
        "An unexpected error occurred. The application may not behave correctly from here on, so saving your project and restarting is recommended.": "發生了未預期的錯誤。此後程式可能無法正常運作，建議儲存專案並重新啟動。",
        "Details were written to {0}": "詳細資訊已寫入 {0}",
        "Preparing compute kernels in the background…": "正在背景準備計算核心…",
        "Compute kernels ready ({0} s).": "計算核心已就緒（{0} 秒）。",
    },
    "ja": {
        "pyALDIC-3D has hit an error": "pyALDIC-3D でエラーが発生しました",
        "An unexpected error occurred. The application may not behave correctly from here on, so saving your project and restarting is recommended.": "予期しないエラーが発生しました。この後アプリケーションが正しく動作しない可能性があるため、プロジェクトを保存して再起動することをお勧めします。",
        "Details were written to {0}": "詳細は {0} に書き込まれました",
        "Preparing compute kernels in the background…": "バックグラウンドで計算カーネルを準備しています…",
        "Compute kernels ready ({0} s).": "計算カーネルの準備ができました（{0} 秒）。",
    },
    "ko": {
        "pyALDIC-3D has hit an error": "pyALDIC-3D에서 오류가 발생했습니다",
        "An unexpected error occurred. The application may not behave correctly from here on, so saving your project and restarting is recommended.": "예기치 않은 오류가 발생했습니다. 이후 애플리케이션이 올바르게 동작하지 않을 수 있으므로 프로젝트를 저장하고 다시 시작하는 것이 좋습니다.",
        "Details were written to {0}": "자세한 내용이 {0}에 기록되었습니다",
        "Preparing compute kernels in the background…": "백그라운드에서 계산 커널을 준비하는 중…",
        "Compute kernels ready ({0} s).": "계산 커널 준비 완료({0}초).",
    },
    "de": {
        "pyALDIC-3D has hit an error": "pyALDIC-3D ist auf einen Fehler gestoßen",
        "An unexpected error occurred. The application may not behave correctly from here on, so saving your project and restarting is recommended.": "Ein unerwarteter Fehler ist aufgetreten. Die Anwendung verhält sich möglicherweise nicht mehr korrekt; es wird empfohlen, das Projekt zu speichern und die Anwendung neu zu starten.",
        "Details were written to {0}": "Details wurden in {0} gespeichert",
        "Preparing compute kernels in the background…": "Rechenkernel werden im Hintergrund vorbereitet…",
        "Compute kernels ready ({0} s).": "Rechenkernel bereit ({0} s).",
    },
    "fr": {
        "pyALDIC-3D has hit an error": "pyALDIC-3D a rencontré une erreur",
        "An unexpected error occurred. The application may not behave correctly from here on, so saving your project and restarting is recommended.": "Une erreur inattendue s'est produite. L'application risque de ne plus fonctionner correctement ; il est recommandé d'enregistrer votre projet et de redémarrer.",
        "Details were written to {0}": "Les détails ont été enregistrés dans {0}",
        "Preparing compute kernels in the background…": "Préparation des noyaux de calcul en arrière-plan…",
        "Compute kernels ready ({0} s).": "Noyaux de calcul prêts ({0} s).",
    },
    "es": {
        "pyALDIC-3D has hit an error": "pyALDIC-3D ha encontrado un error",
        "An unexpected error occurred. The application may not behave correctly from here on, so saving your project and restarting is recommended.": "Se ha producido un error inesperado. Es posible que la aplicación no funcione correctamente a partir de ahora, por lo que se recomienda guardar el proyecto y reiniciar.",
        "Details were written to {0}": "Los detalles se han guardado en {0}",
        "Preparing compute kernels in the background…": "Preparando los núcleos de cálculo en segundo plano…",
        "Compute kernels ready ({0} s).": "Núcleos de cálculo listos ({0} s).",
    },
}
