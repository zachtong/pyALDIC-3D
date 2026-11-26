"""Calibration dialog new-user strings (board counts, failure guidance), 7 locales.

``BATCH`` maps locale -> {English source -> translation}, merged by
``tools/fill_translations.py``. Terms follow the existing catalog: calibration
标定 / 校正 / キャリブレーション / 캘리브레이션 / Kalibrierung / étalonnage /
calibración; board 标定板 / 校正板 / ボード / 보드 / Tafel / mire / tablero;
square 方格 / 方格 / 正方形 / 정사각형 / Quadrat / case / casilla. In zh_TW a
column is 行 and a row is 列 (as in its "Columns x Rows" = 行數 × 列數).
Placeholders keep their format specs ({0:.0f}).
"""
# ruff: noqa: E501, RUF001

from __future__ import annotations

_LOCALES = ("zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es")

# (source, zh_CN, zh_TW, ja, ko, de, fr, es)
_ROWS: list[tuple[str, str, str, str, str, str, str, str]] = [
    (
        "Inner corners (columns x rows)",
        "内角点（列 × 行）",
        "內角點（行 × 列）",
        "内側コーナー（列 × 行）",
        "내부 코너 (열 × 행)",
        "Innere Ecken (Spalten × Zeilen)",
        "Coins intérieurs (colonnes × lignes)",
        "Esquinas interiores (columnas × filas)",
    ),
    (
        "Squares (columns x rows)",
        "方格（列 × 行）",
        "方格（行 × 列）",
        "正方形（列 × 行）",
        "정사각형 (열 × 행)",
        "Quadrate (Spalten × Zeilen)",
        "Cases (colonnes × lignes)",
        "Casillas (columnas × filas)",
    ),
    (
        "Dots (columns x rows)",
        "圆点（列 × 行）",
        "圓點（行 × 列）",
        "ドット（列 × 行）",
        "도트 (열 × 행)",
        "Punkte (Spalten × Zeilen)",
        "Points (colonnes × lignes)",
        "Puntos (columnas × filas)",
    ),
    (
        "For a chessboard, count the INNER corners: a board of 10 x 8 squares has 9 x 7.",
        "棋盘格请数内角点：10 × 8 个方格的标定板有 9 × 7 个内角点。",
        "棋盤格請數內角點：10 × 8 個方格的校正板有 9 × 7 個內角點。",
        "チェスボードでは内側のコーナーを数えてください。正方形が 10 × 8 個のボードなら 9 × 7 です。",
        "체스보드는 내부 코너를 세세요. 정사각형이 10 × 8개인 보드는 9 × 7입니다.",
        "Zählen Sie bei einem Schachbrett die INNEREN Ecken: Eine Tafel mit 10 × 8 Quadraten hat 9 × 7.",
        "Pour un damier, comptez les coins INTÉRIEURS : une mire de 10 × 8 cases en a 9 × 7.",
        "En un tablero de ajedrez, cuente las esquinas INTERIORES: un tablero de 10 × 8 casillas tiene 9 × 7.",
    ),
    (
        "For ChArUco, count the SQUARES (not the inner corners), and check the marker size and the OpenCV < 4.7 setting.",
        "ChArUco 请数方格（不是内角点），并检查标记边长和“OpenCV < 4.7”选项。",
        "ChArUco 請數方格（不是內角點），並檢查標記邊長和「OpenCV < 4.7」選項。",
        "ChArUco では正方形を数えてください（内側のコーナーではありません）。マーカーサイズと「OpenCV < 4.7」の設定も確認してください。",
        "ChArUco는 정사각형을 세세요(내부 코너가 아님). 마커 크기와 'OpenCV < 4.7' 설정도 확인하세요.",
        "Zählen Sie bei ChArUco die QUADRATE (nicht die inneren Ecken) und prüfen Sie die Markergröße und die Einstellung „OpenCV < 4.7“.",
        "Pour ChArUco, comptez les CASES (pas les coins intérieurs) et vérifiez la taille des marqueurs et l'option « OpenCV < 4.7 ».",
        "En ChArUco, cuente las CASILLAS (no las esquinas interiores) y compruebe el tamaño del marcador y la opción «OpenCV < 4.7».",
    ),
    (
        "For a dot grid, count the DOTS in one row and in one column.",
        "圆点板请数一行和一列中的圆点个数。",
        "圓點板請數一列和一行中的圓點個數。",
        "ドットグリッドでは、1 行と 1 列のドットの数を数えてください。",
        "도트 그리드는 한 행과 한 열의 도트 개수를 세세요.",
        "Zählen Sie bei einem Punktraster die PUNKTE in einer Zeile und in einer Spalte.",
        "Pour une grille de points, comptez les POINTS d'une ligne et d'une colonne.",
        "En una malla de puntos, cuente los PUNTOS de una fila y de una columna.",
    ),
    (
        "The board was not found in any image.",
        "在所有图像中都没有找到标定板。",
        "在所有影像中都沒有找到校正板。",
        "どの画像にもボードが見つかりませんでした。",
        "어느 이미지에서도 보드를 찾지 못했습니다.",
        "Die Tafel wurde in keinem Bild gefunden.",
        "La mire n'a été trouvée dans aucune image.",
        "No se encontró el tablero en ninguna imagen.",
    ),
    (
        "The board was found in both images of only {0} of {1} pairs (the solve needs {2}).",
        "只有 {0}/{1} 对图像的左右两幅中都找到了标定板（求解至少需要 {2} 对）。",
        "只有 {0}/{1} 對影像的左右兩幅中都找到了校正板（求解至少需要 {2} 對）。",
        "左右両方の画像でボードが見つかったのは {1} ペア中 {0} ペアだけです（解くには {2} ペア必要です）。",
        "양쪽 이미지 모두에서 보드를 찾은 쌍은 {1}쌍 중 {0}쌍뿐입니다(계산에는 {2}쌍이 필요합니다).",
        "Die Tafel wurde nur in {0} von {1} Paaren in beiden Bildern gefunden (die Lösung braucht {2}).",
        "La mire n'a été trouvée dans les deux images que pour {0} paires sur {1} (la résolution en demande {2}).",
        "El tablero solo se encontró en ambas imágenes en {0} de {1} pares (el cálculo necesita {2}).",
    ),
    (
        "{0}: the board images are not all the same size ({1} is {2}, {3} is {4}). Use images of one size for each camera.",
        "{0}：标定板图像的尺寸不一致（{1} 为 {2}，{3} 为 {4}）。每个相机请使用同一尺寸的图像。",
        "{0}：校正板影像的尺寸不一致（{1} 為 {2}，{3} 為 {4}）。每個相機請使用同一尺寸的影像。",
        "{0}：ボード画像のサイズが揃っていません（{1} は {2}、{3} は {4}）。カメラごとに同じサイズの画像を使ってください。",
        "{0}: 보드 이미지의 크기가 모두 같지 않습니다({1}은(는) {2}, {3}은(는) {4}). 카메라마다 같은 크기의 이미지를 사용하세요.",
        "{0}: Die Tafelbilder sind nicht alle gleich groß ({1} ist {2}, {3} ist {4}). Verwenden Sie für jede Kamera Bilder einer Größe.",
        "{0} : les images de la mire n'ont pas toutes la même taille ({1} fait {2}, {3} fait {4}). Utilisez des images d'une seule taille pour chaque caméra.",
        "{0}: las imágenes del tablero no tienen todas el mismo tamaño ({1} mide {2}, {3} mide {4}). Use imágenes de un solo tamaño para cada cámara.",
    ),
    (
        "Load the same number of left and right images, at least {0} pairs: the solve needs {0} usable pairs.",
        "请加载数量相同的左、右图像，至少 {0} 对：求解需要 {0} 对可用的图像对。",
        "請載入數量相同的左、右影像，至少 {0} 對：求解需要 {0} 對可用的影像對。",
        "左右同じ枚数の画像を少なくとも {0} ペア読み込んでください。解くには使えるペアが {0} 組必要です。",
        "왼쪽과 오른쪽 이미지를 같은 수로, 최소 {0}쌍 불러오세요. 계산에는 사용 가능한 쌍이 {0}쌍 필요합니다.",
        "Laden Sie gleich viele linke und rechte Bilder, mindestens {0} Paare: Die Lösung braucht {0} nutzbare Paare.",
        "Chargez autant d'images gauches que droites, au moins {0} paires : la résolution a besoin de {0} paires utilisables.",
        "Cargue el mismo número de imágenes izquierdas y derechas, al menos {0} pares: el cálculo necesita {0} pares utilizables.",
    ),
    (
        "Board distance from the left camera {0:.0f}-{1:.0f} mm",
        "标定板到左相机的距离 {0:.0f}-{1:.0f} mm",
        "校正板到左相機的距離 {0:.0f}-{1:.0f} mm",
        "左カメラからのボード距離 {0:.0f}-{1:.0f} mm",
        "왼쪽 카메라에서 보드까지의 거리 {0:.0f}-{1:.0f} mm",
        "Abstand der Tafel von der linken Kamera {0:.0f}-{1:.0f} mm",
        "Distance de la mire à la caméra gauche {0:.0f}-{1:.0f} mm",
        "Distancia del tablero a la cámara izquierda {0:.0f}-{1:.0f} mm",
    ),
    (
        "Discard calibration?",
        "放弃标定结果？",
        "捨棄校正結果？",
        "キャリブレーションを破棄しますか？",
        "캘리브레이션을 버릴까요?",
        "Kalibrierung verwerfen?",
        "Abandonner l'étalonnage ?",
        "¿Descartar la calibración?",
    ),
    (
        "This calibration has not been saved. Close the dialog and discard it?",
        "此标定结果尚未保存。要关闭对话框并放弃它吗？",
        "此校正結果尚未儲存。要關閉對話框並捨棄它嗎？",
        "このキャリブレーションはまだ保存されていません。ダイアログを閉じて破棄しますか？",
        "이 캘리브레이션은 아직 저장되지 않았습니다. 대화 상자를 닫고 버릴까요?",
        "Diese Kalibrierung wurde nicht gespeichert. Dialog schließen und sie verwerfen?",
        "Cet étalonnage n'a pas été enregistré. Fermer la boîte de dialogue et l'abandonner ?",
        "Esta calibración no se ha guardado. ¿Cerrar el diálogo y descartarla?",
    ),
]

BATCH: dict[str, dict[str, str]] = {
    loc: {row[0]: row[1 + i] for row in _ROWS} for i, loc in enumerate(_LOCALES)
}
