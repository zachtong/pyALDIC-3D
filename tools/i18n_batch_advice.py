"""Run-log advice translations (validity collapse under frequent reference updates), 7 locales.

``BATCH`` maps locale -> {English source -> translation}, merged by
``tools/fill_translations.py``. Terms follow the existing catalog ("Reference
Update" = 参考帧更新 / 參考幀更新 / 参照フレーム更新 / 기준 프레임 갱신 /
Referenz-Update / Mise à jour de la référence / Actualización de referencia;
"Every N Frames" = 每 N 帧 / 每 N 幀 / N フレームごと / N 프레임마다 / Alle N Frames /
Toutes les N images / Cada N fotogramas; "Accumulative" = 累积式 / 累積式 / 累積式 /
누적형 / Akkumulativ / Cumulatif / Acumulativo; the "Validity falls from" opening
of the sibling messages in ``i18n_batch_v_main.py``).
"""
# ruff: noqa: E501, RUF001

from __future__ import annotations

_LOCALES = ("zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es")

# (source, zh_CN, zh_TW, ja, ko, de, fr, es)
_ROWS: list[tuple[str, str, str, str, str, str, str, str]] = [
    (
        "Validity falls from {0}% (frame 1) to {1}%: every reference update adds a small "
        "tracking error, and over a long sequence they add up. Try fewer updates (Reference "
        "Update > Every N Frames, e.g. 10) or WORKFLOW TYPE > Accumulative.",
        "有效率从 {0}%（第 1 帧）降至 {1}%：每次参考帧更新都会带来少量跟踪误差，"
        "长序列中这些误差会累加。请减少更新次数（参考帧更新 > 每 N 帧，例如 10），"
        "或改用 工作流类型 > 累积式。",
        "有效率從 {0}%（第 1 幀）降至 {1}%：每次參考幀更新都會帶來少量追蹤誤差，"
        "長序列中這些誤差會累加。請減少更新次數（參考幀更新 > 每 N 幀，例如 10），"
        "或改用 工作流類型 > 累積式。",
        "有効率がフレーム 1 の {0}% から {1}% に下がりました：参照フレームの更新ごとに"
        "わずかな追跡誤差が生じ、長い系列ではそれが積み重なります。更新回数を減らす"
        "（参照フレーム更新 > N フレームごと、例：10）か、ワークフロー種別 > 累積式 を"
        "試してください。",
        "유효율이 {0}%(프레임 1)에서 {1}%로 떨어집니다: 기준 프레임을 갱신할 때마다 작은 "
        "추적 오차가 생기고, 긴 시퀀스에서는 이것이 누적됩니다. 갱신 횟수를 줄이거나"
        "(기준 프레임 갱신 > N 프레임마다, 예: 10) 워크플로 유형 > 누적형을 사용해 보세요.",
        "Die Gültigkeit fällt von {0} % (Bild 1) auf {1} %: Jedes Referenz-Update fügt einen "
        "kleinen Verfolgungsfehler hinzu, und über eine lange Sequenz summieren sie sich. "
        "Weniger Updates (Referenz-Update > Alle N Frames, z. B. 10) oder WORKFLOW-TYP > "
        "Akkumulativ versuchen.",
        "La validité chute de {0} % (image 1) à {1} % : chaque mise à jour de la référence "
        "ajoute une petite erreur de suivi, et sur une longue séquence elles s'additionnent. "
        "Essayez moins de mises à jour (Mise à jour de la référence > Toutes les N images, "
        "par ex. 10) ou TYPE DE FLUX > Cumulatif.",
        "La validez cae del {0} % (fotograma 1) al {1} %: cada actualización de la referencia "
        "añade un pequeño error de seguimiento y, en una secuencia larga, se acumulan. Pruebe "
        "menos actualizaciones (Actualización de referencia > Cada N fotogramas, p. ej. 10) o "
        "TIPO DE FLUJO > Acumulativo.",
    ),
]

BATCH: dict[str, dict[str, str]] = {
    loc: {row[0]: row[1 + i] for row in _ROWS} for i, loc in enumerate(_LOCALES)
}
