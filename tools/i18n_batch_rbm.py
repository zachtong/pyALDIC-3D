"""Rigid-motion removal translations (Strain window RIGID MOTION section), 7 locales.

``BATCH`` maps locale -> {English source -> translation}, merged by
``tools/fill_translations.py``. Terms follow the existing catalog
("Compute Strain" = 计算应变 / 計算應變 / ひずみを計算 / 변형률 계산 /
Dehnung berechnen / Calculer la déformation / Calcular deformación; "frame" =
帧 / 幀 / フレーム / 프레임 / Bild / image / fotograma) and introduce "rigid-body
motion" = 刚体运动 / 剛體運動 / 剛体運動 / 강체 운동 / Starrkörperbewegung /
mouvement de corps rigide / movimiento de sólido rígido, "fit region" = 拟合区域 /
擬合區域 / フィット領域 / 피팅 영역 / Anpassungsbereich / région d'ajustement /
región de ajuste, "slope" = 斜率 / 斜率 / 傾き / 기울기 / Neigung / pente /
pendiente.
"""
# ruff: noqa: E501, RUF001

from __future__ import annotations

_LOCALES = ("zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es")

# (source, zh_CN, zh_TW, ja, ko, de, fr, es)
_ROWS: list[tuple[str, str, str, str, str, str, str, str]] = [
    # --- RIGID MOTION panel -------------------------------------------------------
    ("Remove", "去除", "去除", "除去", "제거", "Entfernen", "Retirer", "Eliminar"),
    ("Off", "关闭", "關閉", "オフ", "끔", "Aus", "Désactivé", "Desactivado"),
    (
        "Translation only",
        "仅平移",
        "僅平移",
        "並進のみ",
        "병진만",
        "Nur Translation",
        "Translation seule",
        "Solo traslación",
    ),
    (
        "Translation + rotation",
        "平移 + 转动",
        "平移 + 轉動",
        "並進 + 回転",
        "병진 + 회전",
        "Translation + Rotation",
        "Translation + rotation",
        "Traslación + rotación",
    ),
    (
        "Remove each frame's best-fit rigid-body motion (relative to frame 1)\n"
        "from the displacement everywhere: the field maps, the 3D view,\n"
        "the strain and every export. Green-Lagrange strain is unchanged\n"
        "by it; the displacement and the slopes ∂w/∂x, ∂w/∂y are not.",
        "从各处的位移中去除每帧（相对第 1 帧）的最佳拟合刚体运动：\n"
        "场图、3D 视图、应变以及所有导出。Green-Lagrange 应变\n"
        "不受其影响；位移和斜率 ∂w/∂x、∂w/∂y 会随之变化。",
        "從各處的位移中去除每幀（相對第 1 幀）的最佳擬合剛體運動：\n"
        "場圖、3D 視圖、應變以及所有匯出。Green-Lagrange 應變\n"
        "不受其影響；位移和斜率 ∂w/∂x、∂w/∂y 會隨之變化。",
        "各フレーム（フレーム 1 基準）の最適な剛体運動を、\n"
        "あらゆる箇所の変位から除去します：場の表示、3D ビュー、\n"
        "ひずみ、すべてのエクスポート。Green-Lagrange ひずみは\n"
        "変わりませんが、変位と傾き ∂w/∂x、∂w/∂y は変わります。",
        "각 프레임(프레임 1 기준)의 최적 강체 운동을 모든 곳의\n"
        "변위에서 제거합니다: 필드 맵, 3D 뷰, 변형률, 모든 내보내기.\n"
        "Green-Lagrange 변형률은 변하지 않지만,\n"
        "변위와 기울기 ∂w/∂x, ∂w/∂y는 달라집니다.",
        "Entfernt die bestangepasste Starrkörperbewegung jedes Bildes\n"
        "(relativ zu Bild 1) überall aus der Verschiebung: Feldkarten,\n"
        "3D-Ansicht, Dehnung und jeder Export. Die Green-Lagrange-Dehnung\n"
        "bleibt gleich; Verschiebung und Neigungen ∂w/∂x, ∂w/∂y nicht.",
        "Retire partout le mouvement de corps rigide le mieux ajusté de\n"
        "chaque image (par rapport à l'image 1) : cartes de champ, vue 3D,\n"
        "déformation et chaque export. La déformation de Green-Lagrange\n"
        "n'en dépend pas ; le déplacement et les pentes ∂w/∂x, ∂w/∂y, si.",
        "Elimina en todas partes el movimiento de sólido rígido mejor ajustado\n"
        "de cada fotograma (respecto al fotograma 1): mapas de campo, vista 3D,\n"
        "deformación y cada exportación. La deformación de Green-Lagrange\n"
        "no cambia; el desplazamiento y las pendientes ∂w/∂x, ∂w/∂y sí.",
    ),
    (
        "+ Rectangle",
        "+ 矩形",
        "+ 矩形",
        "+ 矩形",
        "+ 사각형",
        "+ Rechteck",
        "+ Rectangle",
        "+ Rectángulo",
    ),
    (
        "+ Polygon",
        "+ 多边形",
        "+ 多邊形",
        "+ 多角形",
        "+ 다각형",
        "+ Polygon",
        "+ Polygone",
        "+ Polígono",
    ),
    (
        "− Rectangle",
        "− 矩形",
        "− 矩形",
        "− 矩形",
        "− 사각형",
        "− Rechteck",
        "− Rectangle",
        "− Rectángulo",
    ),
    (
        "− Polygon",
        "− 多边形",
        "− 多邊形",
        "− 多角形",
        "− 다각형",
        "− Polygon",
        "− Polygone",
        "− Polígono",
    ),
    (
        "Add an area to the fit region (drawn on frame 1)",
        "向拟合区域添加一块区域（在第 1 帧上绘制）",
        "向擬合區域新增一塊區域（在第 1 幀上繪製）",
        "フィット領域に範囲を追加（フレーム 1 上で描画）",
        "피팅 영역에 범위 추가(프레임 1에서 그림)",
        "Fläche zum Anpassungsbereich hinzufügen (auf Bild 1 gezeichnet)",
        "Ajouter une zone à la région d'ajustement (tracée sur l'image 1)",
        "Añadir un área a la región de ajuste (dibujada en el fotograma 1)",
    ),
    (
        "Remove an area from the fit region",
        "从拟合区域挖除一块区域",
        "從擬合區域挖除一塊區域",
        "フィット領域から範囲を除外",
        "피팅 영역에서 범위 제외",
        "Fläche aus dem Anpassungsbereich entfernen",
        "Retirer une zone de la région d'ajustement",
        "Quitar un área de la región de ajuste",
    ),
    (
        "Use all valid points",
        "使用全部有效点",
        "使用全部有效點",
        "すべての有効点を使用",
        "모든 유효 점 사용",
        "Alle gültigen Punkte verwenden",
        "Utiliser tous les points valides",
        "Usar todos los puntos válidos",
    ),
    (
        "Clear the drawn region: fit on every valid point",
        "清除绘制的区域：在全部有效点上拟合",
        "清除繪製的區域：在全部有效點上擬合",
        "描画した領域を消去：すべての有効点でフィット",
        "그린 영역 지우기: 모든 유효 점으로 피팅",
        "Gezeichneten Bereich löschen: an allen gültigen Punkten anpassen",
        "Effacer la région tracée : ajuster sur tous les points valides",
        "Borrar la región dibujada: ajustar con todos los puntos válidos",
    ),
    (
        "Show fit region",
        "显示拟合区域",
        "顯示擬合區域",
        "フィット領域を表示",
        "피팅 영역 표시",
        "Anpassungsbereich anzeigen",
        "Afficher la région d'ajustement",
        "Mostrar la región de ajuste",
    ),
    (
        "Per frame: shift of the fitted points' centroid ΔX/ΔY/ΔZ (µm), rotation θ (mrad), fit residual RMS (µm), points used N.",
        "逐帧：拟合点形心的位移 ΔX/ΔY/ΔZ（µm）、转角 θ（mrad）、拟合残差 RMS（µm）、所用点数 N。",
        "逐幀：擬合點形心的位移 ΔX/ΔY/ΔZ（µm）、轉角 θ（mrad）、擬合殘差 RMS（µm）、所用點數 N。",
        "フレームごと：フィット点の重心移動 ΔX/ΔY/ΔZ（µm）、回転 θ（mrad）、フィット残差 RMS（µm）、使用点数 N。",
        "프레임별: 피팅 점 중심의 이동 ΔX/ΔY/ΔZ(µm), 회전 θ(mrad), 피팅 잔차 RMS(µm), 사용된 점 수 N.",
        "Pro Bild: Verschiebung des Schwerpunkts der angepassten Punkte ΔX/ΔY/ΔZ (µm), Drehung θ (mrad), Anpassungsresiduum RMS (µm), verwendete Punkte N.",
        "Par image : décalage du centroïde des points ajustés ΔX/ΔY/ΔZ (µm), rotation θ (mrad), résidu d'ajustement RMS (µm), points utilisés N.",
        "Por fotograma: desplazamiento del centroide de los puntos ajustados ΔX/ΔY/ΔZ (µm), rotación θ (mrad), residuo del ajuste RMS (µm), puntos usados N.",
    ),
    # --- Strain window FIELD groups -----------------------------------------------------
    (
        "U — displacement along the world X axis (left camera)",
        "U — 沿世界坐标系 X 轴的位移（左相机）",
        "U — 沿世界座標系 X 軸的位移（左相機）",
        "U — ワールド座標系 X 軸方向の変位（左カメラ）",
        "U — 월드 좌표계 X축 방향 변위(왼쪽 카메라)",
        "U — Verschiebung entlang der Welt-X-Achse (linke Kamera)",
        "U — déplacement selon l'axe X du repère monde (caméra gauche)",
        "U — desplazamiento según el eje X del sistema mundo (cámara izquierda)",
    ),
    (
        "V — displacement along the world Y axis (left camera)",
        "V — 沿世界坐标系 Y 轴的位移（左相机）",
        "V — 沿世界座標系 Y 軸的位移（左相機）",
        "V — ワールド座標系 Y 軸方向の変位（左カメラ）",
        "V — 월드 좌표계 Y축 방향 변위(왼쪽 카메라)",
        "V — Verschiebung entlang der Welt-Y-Achse (linke Kamera)",
        "V — déplacement selon l'axe Y du repère monde (caméra gauche)",
        "V — desplazamiento según el eje Y del sistema mundo (cámara izquierda)",
    ),
    (
        "W — displacement along the world Z axis (left camera)",
        "W — 沿世界坐标系 Z 轴的位移（左相机）",
        "W — 沿世界座標系 Z 軸的位移（左相機）",
        "W — ワールド座標系 Z 軸方向の変位（左カメラ）",
        "W — 월드 좌표계 Z축 방향 변위(왼쪽 카메라)",
        "W — Verschiebung entlang der Welt-Z-Achse (linke Kamera)",
        "W — déplacement selon l'axe Z du repère monde (caméra gauche)",
        "W — desplazamiento según el eje Z del sistema mundo (cámara izquierda)",
    ),
    (
        "|D| — displacement magnitude",
        "|D| — 位移大小",
        "|D| — 位移大小",
        "|D| — 変位の大きさ",
        "|D| — 변위 크기",
        "|D| — Betrag der Verschiebung",
        "|D| — norme du déplacement",
        "|D| — magnitud del desplazamiento",
    ),
    (
        "∂w/∂x — out-of-plane slope along the strain frame's x axis",
        "∂w/∂x — 沿应变坐标系 x 轴的离面斜率",
        "∂w/∂x — 沿應變座標系 x 軸的離面斜率",
        "∂w/∂x — ひずみ座標系 x 軸方向の面外傾き",
        "∂w/∂x — 변형률 좌표계 x축 방향의 면외 기울기",
        "∂w/∂x — Neigung aus der Ebene entlang der x-Achse des Dehnungskoordinatensystems",
        "∂w/∂x — pente hors plan selon l'axe x du repère de déformation",
        "∂w/∂x — pendiente fuera del plano según el eje x del sistema de deformación",
    ),
    (
        "∂w/∂y — out-of-plane slope along the strain frame's y axis",
        "∂w/∂y — 沿应变坐标系 y 轴的离面斜率",
        "∂w/∂y — 沿應變座標系 y 軸的離面斜率",
        "∂w/∂y — ひずみ座標系 y 軸方向の面外傾き",
        "∂w/∂y — 변형률 좌표계 y축 방향의 면외 기울기",
        "∂w/∂y — Neigung aus der Ebene entlang der y-Achse des Dehnungskoordinatensystems",
        "∂w/∂y — pente hors plan selon l'axe y du repère de déformation",
        "∂w/∂y — pendiente fuera del plano según el eje y del sistema de deformación",
    ),
    (
        "Displacement",
        "位移",
        "位移",
        "変位",
        "변위",
        "Verschiebung",
        "Déplacement",
        "Desplazamiento",
    ),
    ("Slope", "斜率", "斜率", "傾き", "기울기", "Neigung", "Pente", "Pendiente"),
    ("Strain", "应变", "應變", "ひずみ", "변형률", "Dehnung", "Déformation", "Deformación"),
    # --- RIGID MOTION status (strain window) ---------------------------------------------
    (
        "RIGID MOTION",
        "刚体运动",
        "剛體運動",
        "剛体運動",
        "강체 운동",
        "STARRKÖRPERBEWEGUNG",
        "MOUVEMENT DE CORPS RIGIDE",
        "MOVIMIENTO DE SÓLIDO RÍGIDO",
    ),
    (
        "Run 3D analysis first — no results to post-process.",
        "请先运行 3D 分析——没有可后处理的结果。",
        "請先執行 3D 分析——沒有可後處理的結果。",
        "先に 3D 解析を実行してください — 後処理する結果がありません。",
        "먼저 3D 분석을 실행하세요 — 후처리할 결과가 없습니다.",
        "Zuerst die 3D-Analyse ausführen — keine Ergebnisse zur Nachbearbeitung.",
        "Exécutez d'abord l'analyse 3D — aucun résultat à post-traiter.",
        "Ejecute primero el análisis 3D — no hay resultados para posprocesar.",
    ),
    (
        "Rigid motion not removed: {0}",
        "未去除刚体运动：{0}",
        "未去除剛體運動：{0}",
        "剛体運動は除去されていません：{0}",
        "강체 운동을 제거하지 않음: {0}",
        "Starrkörperbewegung nicht entfernt: {0}",
        "Mouvement de corps rigide non retiré : {0}",
        "Movimiento de sólido rígido no eliminado: {0}",
    ),
    (
        "Fit region: all valid points",
        "拟合区域：全部有效点",
        "擬合區域：全部有效點",
        "フィット領域：すべての有効点",
        "피팅 영역: 모든 유효 점",
        "Anpassungsbereich: alle gültigen Punkte",
        "Région d'ajustement : tous les points valides",
        "Región de ajuste: todos los puntos válidos",
    ),
    (
        "Fit region: drawn",
        "拟合区域：已绘制",
        "擬合區域：已繪製",
        "フィット領域：描画済み",
        "피팅 영역: 그림",
        "Anpassungsbereich: gezeichnet",
        "Région d'ajustement : tracée",
        "Región de ajuste: dibujada",
    ),
    (
        "Fit region: drawn ({0} nodes)",
        "拟合区域：已绘制（{0} 个节点）",
        "擬合區域：已繪製（{0} 個節點）",
        "フィット領域：描画済み（{0} ノード）",
        "피팅 영역: 그림({0}개 노드)",
        "Anpassungsbereich: gezeichnet ({0} Knoten)",
        "Région d'ajustement : tracée ({0} nœuds)",
        "Región de ajuste: dibujada ({0} nodos)",
    ),
    (
        "Rigid motion is not removed.",
        "未去除刚体运动。",
        "未去除剛體運動。",
        "剛体運動は除去していません。",
        "강체 운동을 제거하지 않습니다.",
        "Die Starrkörperbewegung wird nicht entfernt.",
        "Le mouvement de corps rigide n'est pas retiré.",
        "No se elimina el movimiento de sólido rígido.",
    ),
    (
        "Removed ({0}), fitted on {1} points.",
        "已去除（{0}），基于 {1} 个点拟合。",
        "已去除（{0}），基於 {1} 個點擬合。",
        "除去済み（{0}）、{1} 点でフィット。",
        "제거됨({0}), {1}개 점으로 피팅.",
        "Entfernt ({0}), angepasst an {1} Punkten.",
        "Retiré ({0}), ajusté sur {1} points.",
        "Eliminado ({0}), ajustado con {1} puntos.",
    ),
    (
        "the fit region does not cover this run",
        "拟合区域没有覆盖本次运算",
        "擬合區域沒有覆蓋本次運算",
        "フィット領域がこの解析を覆っていません",
        "피팅 영역이 이번 분석을 덮지 않습니다",
        "der Anpassungsbereich deckt diese Analyse nicht ab",
        "la région d'ajustement ne couvre pas cette analyse",
        "la región de ajuste no cubre este análisis",
    ),
    (
        "Not removed: {0}",
        "未去除：{0}",
        "未去除：{0}",
        "未除去：{0}",
        "제거되지 않음: {0}",
        "Nicht entfernt: {0}",
        "Non retiré : {0}",
        "No eliminado: {0}",
    ),
    (
        "It will be removed once the analysis has run.",
        "运行分析后将去除刚体运动。",
        "執行分析後將去除剛體運動。",
        "解析の実行後に除去されます。",
        "분석을 실행하면 제거됩니다.",
        "Sie wird entfernt, sobald die Analyse gelaufen ist.",
        "Il sera retiré une fois l'analyse exécutée.",
        "Se eliminará cuando se haya ejecutado el análisis.",
    ),
    (
        "Not fitted on this frame: {0}",
        "此帧未能拟合：{0}",
        "此幀未能擬合：{0}",
        "このフレームはフィットできません：{0}",
        "이 프레임은 피팅되지 않음: {0}",
        "In diesem Bild nicht angepasst: {0}",
        "Non ajusté sur cette image : {0}",
        "No ajustado en este fotograma: {0}",
    ),
    (
        "⚠ Rigid-motion setting changed -- click Compute Strain",
        "⚠ 刚体运动设置已变更 — 请点击“计算应变”",
        "⚠ 剛體運動設定已變更 — 請點擊「計算應變」",
        "⚠ 剛体運動の設定が変更されました — 「ひずみを計算」をクリックしてください",
        "⚠ 강체 운동 설정이 변경됨 — 「변형률 계산」을 클릭하세요",
        "⚠ Starrkörper-Einstellung geändert — „Dehnung berechnen“ klicken",
        "⚠ Réglage du mouvement de corps rigide modifié — cliquez sur « Calculer la déformation »",
        "⚠ Ajuste de movimiento rígido modificado — haga clic en «Calcular deformación»",
    ),
    # --- shared wording (RigidMotion context: labels everywhere) -------------------------
    ("translation", "平移", "平移", "並進", "병진", "Translation", "translation", "traslación"),
    (
        "translation + rotation",
        "平移 + 转动",
        "平移 + 轉動",
        "並進 + 回転",
        "병진 + 회전",
        "Translation + Rotation",
        "translation + rotation",
        "traslación + rotación",
    ),
    ("off", "关闭", "關閉", "オフ", "끔", "aus", "désactivé", "desactivado"),
    (
        " · rigid motion removed ({0})",
        " · 已去除刚体运动（{0}）",
        " · 已去除剛體運動（{0}）",
        " · 剛体運動を除去（{0}）",
        " · 강체 운동 제거됨({0})",
        " · Starrkörperbewegung entfernt ({0})",
        " · mouvement de corps rigide retiré ({0})",
        " · movimiento rígido eliminado ({0})",
    ),
    # --- main window (project open note) -----------------------------------------------
    (
        "The rigid motion was not removed (the results are shown as measured): {0}",
        "未去除刚体运动（结果按测量值显示）：{0}",
        "未去除剛體運動（結果按量測值顯示）：{0}",
        "剛体運動は除去されませんでした（結果は測定値のまま表示）：{0}",
        "강체 운동을 제거하지 않았습니다(결과는 측정값 그대로 표시): {0}",
        "Die Starrkörperbewegung wurde nicht entfernt (Ergebnisse wie gemessen): {0}",
        "Le mouvement de corps rigide n'a pas été retiré (résultats tels que mesurés) : {0}",
        "No se eliminó el movimiento de sólido rígido (resultados tal como se midieron): {0}",
    ),
]

BATCH: dict[str, dict[str, str]] = {
    loc: {row[0]: row[1 + i] for row in _ROWS} for i, loc in enumerate(_LOCALES)
}
