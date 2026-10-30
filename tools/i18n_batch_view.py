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
    (
        "Save 3D view image",
        "保存 3D 视图图像",
        "儲存 3D 視圖影像",
        "3D ビュー画像を保存",
        "3D 뷰 이미지 저장",
        "3D-Ansicht als Bild speichern",
        "Enregistrer l'image de la vue 3D",
        "Guardar imagen de la vista 3D",
    ),
    (
        "PNG image (*.png)",
        "PNG 图像 (*.png)",
        "PNG 影像 (*.png)",
        "PNG 画像 (*.png)",
        "PNG 이미지 (*.png)",
        "PNG-Bild (*.png)",
        "Image PNG (*.png)",
        "Imagen PNG (*.png)",
    ),
    (
        "Could not save the image: {0}",
        "无法保存图像：{0}",
        "無法儲存影像：{0}",
        "画像を保存できませんでした：{0}",
        "이미지를 저장할 수 없음: {0}",
        "Bild konnte nicht gespeichert werden: {0}",
        "Impossible d'enregistrer l'image : {0}",
        "No se pudo guardar la imagen: {0}",
    ),
    (
        "Reset",
        "重置",
        "重設",
        "リセット",
        "재설정",
        "Zurücksetzen",
        "Réinitialiser",
        "Restablecer",
    ),
    (
        "Back to the view from the left camera, framed",
        "回到从左相机看的视角并重新取景",
        "回到從左相機看的視角並重新取景",
        "左カメラからの視点に戻して全体を表示",
        "왼쪽 카메라 시점으로 돌아가 다시 맞춤",
        "Zurück zur Ansicht der linken Kamera, eingepasst",
        "Revenir à la vue de la caméra gauche, cadrée",
        "Volver a la vista de la cámara izquierda, encuadrada",
    ),
    (
        "Camera",
        "相机",
        "相機",
        "カメラ",
        "카메라",
        "Kamera",
        "Caméra",
        "Cámara",
    ),
    (
        "Look from the left camera (as in the images)",
        "从左相机方向看（与图像一致）",
        "從左相機方向看（與影像一致）",
        "左カメラから見る（画像と同じ向き）",
        "왼쪽 카메라에서 보기(이미지와 같은 방향)",
        "Aus Sicht der linken Kamera (wie in den Bildern)",
        "Vue depuis la caméra gauche (comme sur les images)",
        "Ver desde la cámara izquierda (como en las imágenes)",
    ),
    (
        "Normal",
        "正视",
        "正視",
        "正面",
        "정면",
        "Normal",
        "Normale",
        "Normal",
    ),
    (
        "Look straight at the specimen surface",
        "垂直正对试件表面看",
        "垂直正對試件表面看",
        "試験片の表面を真正面から見る",
        "시편 표면을 정면으로 보기",
        "Senkrecht auf die Probenoberfläche blicken",
        "Regarder la surface de l'éprouvette de face",
        "Mirar la superficie de la probeta de frente",
    ),
    (
        "Side",
        "侧视",
        "側視",
        "側面",
        "측면",
        "Seite",
        "Côté",
        "Lateral",
    ),
    (
        "Edge-on: the out-of-plane profile",
        "侧向平视：离面变形轮廓",
        "側向平視：離面變形輪廓",
        "真横から：面外の輪郭",
        "옆에서: 면외 윤곽",
        "Kantenansicht: das Profil aus der Ebene",
        "Vue de profil : le profil hors plan",
        "De canto: el perfil fuera del plano",
    ),
    (
        "Iso",
        "斜视",
        "斜視",
        "等角",
        "등각",
        "Iso",
        "Iso",
        "Iso",
    ),
    (
        "Oblique view of the specimen",
        "试件的斜视图",
        "試件的斜視圖",
        "試験片の斜め方向からのビュー",
        "시편의 비스듬한 보기",
        "Schrägansicht der Probe",
        "Vue oblique de l'éprouvette",
        "Vista oblicua de la probeta",
    ),
    (
        "Save image…",
        "保存图像…",
        "儲存影像…",
        "画像を保存…",
        "이미지 저장…",
        "Bild speichern…",
        "Enregistrer l'image…",
        "Guardar imagen…",
    ),
    (
        "Save the 3D view as a PNG image",
        "将 3D 视图保存为 PNG 图像",
        "將 3D 視圖儲存為 PNG 影像",
        "3D ビューを PNG 画像として保存",
        "3D 뷰를 PNG 이미지로 저장",
        "Die 3D-Ansicht als PNG-Bild speichern",
        "Enregistrer la vue 3D en image PNG",
        "Guardar la vista 3D como imagen PNG",
    ),
    (
        "Deformation ×",
        "变形放大 ×",
        "變形放大 ×",
        "変形倍率 ×",
        "변형 배율 ×",
        "Verformung ×",
        "Déformation ×",
        "Deformación ×",
    ),
    (
        "Exaggerate the displacement in the 3D geometry (reference shape plus\nfactor × displacement) so a micron-scale change is visible. The\ncolours always show the true values.",
        "在 3D 几何中放大位移（参考形状加上\n倍数 × 位移），让微米级的变化也能看清。\n颜色始终表示真实数值。",
        "在 3D 幾何中放大位移（參考形狀加上\n倍數 × 位移），讓微米級的變化也能看清。\n顏色始終表示真實數值。",
        "3D 形状の変位を誇張します（参照形状 +\n倍率 × 変位）。ミクロン単位の変化も見えます。\n色は常に実際の値を表します。",
        "3D 형상에서 변위를 과장합니다(기준 형상 +\n배율 × 변위). 마이크론 단위 변화도 보입니다.\n색은 항상 실제 값을 나타냅니다.",
        "Überhöht die Verschiebung in der 3D-Geometrie (Referenzform plus\nFaktor × Verschiebung), damit Änderungen im Mikrometerbereich sichtbar\nwerden. Die Farben zeigen immer die wahren Werte.",
        "Exagère le déplacement dans la géométrie 3D (forme de référence plus\nfacteur × déplacement) pour rendre visible un changement micrométrique.\nLes couleurs montrent toujours les vraies valeurs.",
        "Exagera el desplazamiento en la geometría 3D (forma de referencia más\nfactor × desplazamiento) para que se vea un cambio micrométrico.\nLos colores muestran siempre los valores reales.",
    ),
    (
        "Auto",
        "自动",
        "自動",
        "自動",
        "자동",
        "Auto",
        "Auto",
        "Auto",
    ),
    (
        "Pick a factor that makes the change visible",
        "自动选择一个能看清变化的倍数",
        "自動選擇一個能看清變化的倍數",
        "変化が見える倍率を自動で選ぶ",
        "변화가 보이는 배율을 자동 선택",
        "Einen Faktor wählen, der die Änderung sichtbar macht",
        "Choisir un facteur qui rend le changement visible",
        "Elegir un factor que haga visible el cambio",
    ),
    (
        "Out-of-plane only",
        "仅离面",
        "僅離面",
        "面外のみ",
        "면외만",
        "Nur aus der Ebene",
        "Hors plan seulement",
        "Solo fuera del plano",
    ),
    (
        "Exaggerate only the displacement along the specimen normal\n(in-plane noise stays at true scale)",
        "只放大沿试件法向的位移\n（面内噪声保持真实比例）",
        "只放大沿試件法向的位移\n（面內雜訊保持真實比例）",
        "試験片の法線方向の変位だけを誇張\n（面内のノイズは実寸のまま）",
        "시편 법선 방향 변위만 과장\n(면내 노이즈는 실제 크기 유지)",
        "Nur die Verschiebung entlang der Probennormalen überhöhen\n(Rauschen in der Ebene bleibt maßstabsgetreu)",
        "N'exagérer que le déplacement selon la normale de l'éprouvette\n(le bruit dans le plan reste à l'échelle réelle)",
        "Exagerar solo el desplazamiento según la normal de la probeta\n(el ruido en el plano se queda a escala real)",
    ),
    (
        "Reference shape",
        "参考形状",
        "參考形狀",
        "参照形状",
        "기준 형상",
        "Referenzform",
        "Forme de référence",
        "Forma de referencia",
    ),
    (
        "Show the frame-1 surface as a wireframe",
        "以线框显示第 1 帧表面",
        "以線框顯示第 1 幀表面",
        "フレーム 1 の表面をワイヤーフレームで表示",
        "프레임 1 표면을 와이어프레임으로 표시",
        "Die Oberfläche von Bild 1 als Drahtgitter zeigen",
        "Afficher la surface de l'image 1 en fil de fer",
        "Mostrar la superficie del fotograma 1 como malla de alambre",
    ),
    (
        "Cameras",
        "相机",
        "相機",
        "カメラ",
        "카메라",
        "Kameras",
        "Caméras",
        "Cámaras",
    ),
    (
        "Show the two camera frusta (zooms the view out)",
        "显示两台相机的视锥（视图会缩小）",
        "顯示兩台相機的視錐（視圖會縮小）",
        "2 台のカメラの視錐台を表示（ビューが縮小）",
        "두 카메라의 절두체 표시(뷰가 축소됨)",
        "Die beiden Kamerapyramiden zeigen (zoomt heraus)",
        "Afficher les deux pyramides des caméras (dézoome la vue)",
        "Mostrar las dos pirámides de las cámaras (aleja la vista)",
    ),
    (
        "Shading",
        "光照",
        "光照",
        "陰影",
        "음영",
        "Schattierung",
        "Ombrage",
        "Sombreado",
    ),
    (
        "Light the surface so its shape reads; off shows the exact colormap colours",
        "为表面打光以看清形状；关闭时显示准确的色图颜色",
        "為表面打光以看清形狀；關閉時顯示準確的色圖顏色",
        "表面に光を当てて形を見やすく。オフで色マップの正確な色",
        "표면에 조명을 주어 형상이 보이게; 끄면 정확한 컬러맵 색",
        "Die Oberfläche beleuchten, damit die Form lesbar ist; aus zeigt die exakten Farben",
        "Éclairer la surface pour lire sa forme ; désactivé donne les couleurs exactes",
        "Iluminar la superficie para leer su forma; apagado da los colores exactos",
    ),
]

BATCH: dict[str, dict[str, str]] = {
    loc: {row[0]: row[1 + i] for row in _ROWS} for i, loc in enumerate(_LOCALES)
}
