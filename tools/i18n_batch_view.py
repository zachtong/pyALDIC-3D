"""Canvas-view translations (Show ROI toggle, 3D View controls), 7 locales.

``BATCH`` maps locale -> {English source -> translation}, merged by
``tools/fill_translations.py``. Terms follow the existing catalog ("Show Grid" =
显示网格 / 顯示網格 / グリッドを表示 / 격자 표시 / Gitter anzeigen / Afficher la
grille / Mostrar cuadrícula; "reference view (left camera, frame 1)" = 参考视图
（左相机第 1 帧）/ 參考視圖（左相機第 1 幀）/ 参照ビュー（左カメラ、フレーム 1）/
기준 뷰(왼쪽 카메라, 프레임 1) / Referenzansicht (linke Kamera, Bild 1) / vue de
référence (caméra gauche, image 1) / vista de referencia (cámara izquierda,
fotograma 1)).
"""
# ruff: noqa: E501, RUF001

from __future__ import annotations

_LOCALES = ("zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es")

# (source, zh_CN, zh_TW, ja, ko, de, fr, es)
_ROWS: list[tuple[str, str, str, str, str, str, str, str]] = [
    (
        "Show ROI",
        "显示 ROI",
        "顯示 ROI",
        "ROI を表示",
        "ROI 표시",
        "ROI anzeigen",
        "Afficher la ROI",
        "Mostrar ROI",
    ),
    (
        "Show the drawn region of interest (blue) and refinement zones\n"
        "on the reference view (left camera, frame 1). Turned off when\n"
        "an analysis finishes so the results are not tinted; drawing\n"
        "with an ROI or brush tool turns it back on.",
        "在参考视图（左相机第 1 帧）上显示绘制的感兴趣区域（蓝色）\n"
        "和细化区域。分析完成时自动关闭，\n"
        "以免结果被染上颜色；使用 ROI 或画笔工具\n"
        "绘制时会重新打开。",
        "在參考視圖（左相機第 1 幀）上顯示繪製的感興趣區域（藍色）\n"
        "和細化區域。分析完成時自動關閉，\n"
        "以免結果被染上顏色；使用 ROI 或畫筆工具\n"
        "繪製時會重新開啟。",
        "参照ビュー（左カメラ、フレーム 1）に、描画した関心領域（青）\n"
        "と細分化領域を表示します。解析が終わると、結果に色が\n"
        "重ならないよう自動でオフになります。ROI ツールや\n"
        "ブラシで描くと再びオンになります。",
        "기준 뷰(왼쪽 카메라, 프레임 1)에 그린 관심 영역(파란색)과\n"
        "세분화 영역을 표시합니다. 분석이 끝나면 결과에 색이\n"
        "겹치지 않도록 자동으로 꺼지고, ROI 도구나 브러시로\n"
        "그리면 다시 켜집니다.",
        "Zeigt den gezeichneten Interessenbereich (blau) und die\n"
        "Verfeinerungszonen auf der Referenzansicht (linke Kamera, Bild 1).\n"
        "Wird nach einer Analyse ausgeschaltet, damit die Ergebnisse nicht\n"
        "eingefärbt werden; Zeichnen mit ROI- oder Pinselwerkzeug schaltet ihn ein.",
        "Affiche la région d'intérêt tracée (bleu) et les zones de raffinement\n"
        "sur la vue de référence (caméra gauche, image 1). Désactivé à la fin\n"
        "d'une analyse pour ne pas teinter les résultats ; tracer avec un outil\n"
        "ROI ou le pinceau le réactive.",
        "Muestra la región de interés dibujada (azul) y las zonas de refinamiento\n"
        "sobre la vista de referencia (cámara izquierda, fotograma 1). Se apaga al\n"
        "terminar un análisis para no teñir los resultados; dibujar con una\n"
        "herramienta de ROI o el pincel la vuelve a encender.",
    ),
]

BATCH: dict[str, dict[str, str]] = {
    loc: {row[0]: row[1 + i] for row in _ROWS} for i, loc in enumerate(_LOCALES)
}
