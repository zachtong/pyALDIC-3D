"""Epipolar-band stereo search translations (the Epipolar Band setting), 7 locales.

``BATCH`` maps locale -> {English source -> translation}, merged by
``tools/fill_translations.py``. Terms follow the existing catalog ("Stereo
Search" = 立体搜索 / 立體搜尋 / ステレオ探索 / 스테레오 탐색 / Stereo-Suche /
Recherche stéréo / Búsqueda estéreo; "Epipolar limit" = 极线限制 / 極線限制 /
エピポーラ制限 / 에피폴라 한계 / Epipolargrenze / Limite épipolaire / Límite
epipolar). Tooltip line breaks are kept at similar widths.
"""
# ruff: noqa: E501, RUF001

from __future__ import annotations

_LOCALES = ("zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es")

# (source, zh_CN, zh_TW, ja, ko, de, fr, es)
_ROWS: list[tuple[str, str, str, str, str, str, str, str]] = [
    (
        "Epipolar Band",
        "极线带",
        "極線帶",
        "エピポーラ帯",
        "에피폴라 밴드",
        "Epipolarband",
        "Bande épipolaire",
        "Banda epipolar",
    ),
    (
        "Epipolar band: the left-to-right match is searched only within\n"
        "this many pixels of the line the calibration predicts for each\n"
        "node, over the Stereo Search distance along it, so a look-alike\n"
        "off the line cannot be picked. Default 15 px; never narrower\n"
        "than the Epipolar limit; 0 searches a square window instead.",
        "极线带：左右匹配只在标定为每个节点预测的极线\n"
        "两侧这么多像素以内搜索，沿极线方向的范围为\n"
        "立体搜索距离，因此极线外的相似纹理不会被误选。\n"
        "默认 15 px；不会窄于极线限制；为 0 时改用\n"
        "正方形窗口搜索。",
        "極線帶：左右匹配只在校正為每個節點預測的極線\n"
        "兩側這麼多像素以內搜尋，沿極線方向的範圍為\n"
        "立體搜尋距離，因此極線外的相似紋理不會被誤選。\n"
        "預設 15 px；不會窄於極線限制；為 0 時改用\n"
        "正方形視窗搜尋。",
        "エピポーラ帯：左右の対応は、キャリブレーションが各節点に\n"
        "予測する線からこの画素数以内だけを、線に沿ってはステレオ\n"
        "探索の距離だけ探索するため、線から外れた似た模様を選ぶ\n"
        "ことはありません。既定 15 px。エピポーラ制限より狭く\n"
        "なりません。0 の場合は正方形ウィンドウで探索します。",
        "에피폴라 밴드: 좌우 매칭은 캘리브레이션이 각 노드에 대해\n"
        "예측한 선에서 이 픽셀 수 이내만, 선을 따라서는 스테레오\n"
        "탐색 거리만큼만 탐색하므로 선 밖의 비슷한 무늬를 잘못\n"
        "고르지 않습니다. 기본값 15 px, 에피폴라 한계보다 좁아지지\n"
        "않으며, 0이면 정사각형 창에서 탐색합니다.",
        "Epipolarband: Die Links-rechts-Zuordnung wird nur innerhalb\n"
        "dieser Pixelzahl um die Linie gesucht, die die Kalibrierung für\n"
        "jeden Knoten vorhersagt, entlang der Linie über die Distanz der\n"
        "Stereo-Suche; ein ähnliches Muster abseits der Linie wird so nicht\n"
        "gewählt. Standard 15 px; nie schmaler als die Epipolargrenze;\n"
        "0 sucht stattdessen in einem quadratischen Fenster.",
        "Bande épipolaire : la correspondance gauche-droite n'est cherchée\n"
        "qu'à ce nombre de pixels au plus de la ligne que l'étalonnage\n"
        "prédit pour chaque nœud, sur la distance de la Recherche stéréo\n"
        "le long de celle-ci ; un motif semblable hors de la ligne ne peut\n"
        "donc pas être retenu. 15 px par défaut ; jamais plus étroite que la\n"
        "Limite épipolaire ; 0 cherche plutôt dans une fenêtre carrée.",
        "Banda epipolar: la correspondencia izquierda-derecha solo se busca\n"
        "a esta distancia en píxeles de la línea que la calibración predice\n"
        "para cada nodo, a lo largo de la distancia de Búsqueda estéreo;\n"
        "así no se puede elegir un patrón parecido fuera de la línea.\n"
        "15 px por defecto; nunca más estrecha que el Límite epipolar;\n"
        "0 busca en una ventana cuadrada.",
    ),
    (
        "How far (pixels) the left-to-right stereo match searches around\n"
        "each node's expected position: along the epipolar line, or in a\n"
        "square window when the Epipolar Band is off. Set it larger than\n"
        "the error expected in that position.",
        "左右立体匹配在每个节点的预期位置周围搜索的\n"
        "距离（像素）：沿极线方向搜索；极线带关闭时\n"
        "在正方形窗口内搜索。应大于该预期位置可能的误差。",
        "左右立體匹配在每個節點的預期位置周圍搜尋的\n"
        "距離（像素）：沿極線方向搜尋；極線帶關閉時\n"
        "在正方形視窗內搜尋。應大於該預期位置可能的誤差。",
        "左右ステレオ対応が各節点の予想位置の周りを探索する距離\n"
        "（画素）：エピポーラ線に沿って探索し、エピポーラ帯がオフの\n"
        "ときは正方形ウィンドウで探索します。その予想位置の誤差より\n"
        "大きく設定してください。",
        "좌우 스테레오 매칭이 각 노드의 예상 위치 주변을 탐색하는\n"
        "거리(픽셀): 에피폴라 선을 따라 탐색하며, 에피폴라 밴드가\n"
        "꺼져 있으면 정사각형 창에서 탐색합니다. 그 위치의 예상\n"
        "오차보다 크게 설정하십시오.",
        "Wie weit (Pixel) die Links-rechts-Stereozuordnung um die\n"
        "erwartete Position jedes Knotens sucht: entlang der Epipolarlinie\n"
        "oder, wenn das Epipolarband aus ist, in einem quadratischen\n"
        "Fenster. Größer wählen als der erwartete Fehler dieser Position.",
        "Distance (pixels) sur laquelle la correspondance stéréo gauche-droite\n"
        "cherche autour de la position attendue de chaque nœud : le long de la\n"
        "ligne épipolaire, ou dans une fenêtre carrée si la Bande épipolaire\n"
        "est désactivée. À choisir plus grande que l'erreur attendue sur cette\n"
        "position.",
        "Distancia (píxeles) que la correspondencia estéreo izquierda-derecha\n"
        "busca alrededor de la posición esperada de cada nodo: a lo largo de la\n"
        "línea epipolar, o en una ventana cuadrada si la Banda epipolar está\n"
        "desactivada. Debe superar el error esperado en esa posición.",
    ),
]

BATCH: dict[str, dict[str, str]] = {
    loc: {row[0]: row[1 + i] for row in _ROWS} for i, loc in enumerate(_LOCALES)
}
