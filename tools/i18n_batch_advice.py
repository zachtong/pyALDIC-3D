"""Run-log advice translations (validity collapse, FFT search widening, stereo check), 7 locales.

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
    (
        "Camera {0}: the initial-guess search had to widen on {1} frames (up to {2} px), "
        "which slows the run. If the motion between reference frames is that large, raise "
        "PARAMETERS > Temporal Search.",
        "相机 {0}：初始估计的搜索范围在 {1} 帧上不得不扩大（最大 {2} px），这会拖慢运行。"
        "若参考帧之间的运动确实这么大，请增大 参数 > 时序搜索。",
        "相機 {0}：初始估計的搜尋範圍在 {1} 幀上不得不擴大（最大 {2} px），這會拖慢執行。"
        "若參考幀之間的運動確實這麼大，請增大 參數 > 時序搜尋。",
        "カメラ {0}：初期推定の探索範囲を {1} フレームで広げる必要がありました（最大 {2} px）。"
        "実行が遅くなります。参照フレーム間の動きが実際にこれほど大きい場合は、"
        "パラメータ > 時系列探索 を大きくしてください。",
        "카메라 {0}: 초기 추정 탐색 범위를 {1}개 프레임에서 넓혀야 했습니다(최대 {2} px). "
        "실행이 느려집니다. 기준 프레임 사이의 움직임이 실제로 이만큼 크다면 "
        "매개변수 > 시간 탐색을 늘리세요.",
        "Kamera {0}: Die Suche für die Anfangsschätzung musste auf {1} Bildern erweitert "
        "werden (bis {2} px), was den Lauf verlangsamt. Ist die Bewegung zwischen den "
        "Referenzbildern wirklich so groß, PARAMETER > Zeitliche Suche erhöhen.",
        "Caméra {0} : la recherche de l'estimation initiale a dû être élargie sur {1} images "
        "(jusqu'à {2} px), ce qui ralentit le calcul. Si le mouvement entre images de "
        "référence est vraiment aussi grand, augmentez PARAMÈTRES > Recherche temporelle.",
        "Cámara {0}: la búsqueda de la estimación inicial tuvo que ampliarse en {1} "
        "fotogramas (hasta {2} px), lo que ralentiza el cálculo. Si el movimiento entre "
        "fotogramas de referencia es realmente tan grande, aumente PARÁMETROS > Búsqueda "
        "temporal.",
    ),
    (
        "Camera {0}: the initial-guess search had to widen on {1} frames (up to {2} px), "
        "which slows the run. In incremental mode this usually means the frame-1 region no "
        "longer covers the specimen at later reference frames: import per-frame masks "
        "(REGION OF INTEREST) or use WORKFLOW TYPE > Accumulative.",
        "相机 {0}：初始估计的搜索范围在 {1} 帧上不得不扩大（最大 {2} px），这会拖慢运行。"
        "在增量模式下，这通常说明第 1 帧绘制的区域在之后的参考帧上已不再覆盖试件："
        "请导入逐帧掩膜（感兴趣区域），或改用 工作流类型 > 累积式。",
        "相機 {0}：初始估計的搜尋範圍在 {1} 幀上不得不擴大（最大 {2} px），這會拖慢執行。"
        "在增量模式下，這通常表示第 1 幀繪製的區域在之後的參考幀上已不再覆蓋試件："
        "請匯入逐幀遮罩（感興趣區域），或改用 工作流類型 > 累積式。",
        "カメラ {0}：初期推定の探索範囲を {1} フレームで広げる必要がありました（最大 {2} px）。"
        "実行が遅くなります。逐次式では通常、フレーム 1 の領域が後の参照フレームで試験片を"
        "覆わなくなったことを意味します：フレームごとのマスクを読み込むか（関心領域）、"
        "ワークフロー種別 > 累積式 を使用してください。",
        "카메라 {0}: 초기 추정 탐색 범위를 {1}개 프레임에서 넓혀야 했습니다(최대 {2} px). "
        "실행이 느려집니다. 증분형에서는 보통 프레임 1 영역이 이후 기준 프레임에서 시편을 "
        "더 이상 덮지 못한다는 뜻입니다: 프레임별 마스크를 가져오거나(관심 영역) "
        "워크플로 유형 > 누적형을 사용하세요.",
        "Kamera {0}: Die Suche für die Anfangsschätzung musste auf {1} Bildern erweitert "
        "werden (bis {2} px), was den Lauf verlangsamt. Im inkrementellen Modus heißt das "
        "meist, dass der Bereich aus Bild 1 die Probe in späteren Referenzbildern nicht mehr "
        "abdeckt: Masken pro Bild importieren (INTERESSENBEREICH) oder WORKFLOW-TYP > "
        "Akkumulativ verwenden.",
        "Caméra {0} : la recherche de l'estimation initiale a dû être élargie sur {1} images "
        "(jusqu'à {2} px), ce qui ralentit le calcul. En mode incrémental, cela signifie "
        "généralement que la région de l'image 1 ne couvre plus l'éprouvette dans les images "
        "de référence suivantes : importez des masques par image (RÉGION D'INTÉRÊT) ou "
        "utilisez TYPE DE FLUX > Cumulatif.",
        "Cámara {0}: la búsqueda de la estimación inicial tuvo que ampliarse en {1} "
        "fotogramas (hasta {2} px), lo que ralentiza el cálculo. En modo incremental esto "
        "suele significar que la región del fotograma 1 ya no cubre la probeta en los "
        "fotogramas de referencia posteriores: importe máscaras por fotograma (REGIÓN DE "
        "INTERÉS) o use TIPO DE FLUJO > Acumulativo.",
    ),
    (
        "Stereo check removed {0} links for weak left-right correlation (ZNSSD above {1}) "
        "and {2} for epipolar distance (above {3} px).",
        "立体校验因左右相关性偏弱（ZNSSD 高于 {1}）移除了 {0} 个匹配，"
        "因极线距离（超过 {3} px）移除了 {2} 个。",
        "立體校驗因左右相關性偏弱（ZNSSD 高於 {1}）移除了 {0} 個匹配，"
        "因極線距離（超過 {3} px）移除了 {2} 個。",
        "ステレオチェックで、左右の相関が弱い（ZNSSD が {1} を超える）{0} 個の対応と、"
        "エピポーラ距離が {3} px を超える {2} 個の対応を除外しました。",
        "스테레오 검사가 좌우 상관이 약한(ZNSSD {1} 초과) 대응 {0}개와 "
        "에피폴라 거리({3} px 초과) 때문에 {2}개를 제거했습니다.",
        "Die Stereoprüfung hat {0} Zuordnungen wegen schwacher Links-rechts-Korrelation "
        "(ZNSSD über {1}) und {2} wegen des Epipolarabstands (über {3} px) entfernt.",
        "Le contrôle stéréo a retiré {0} correspondances pour une corrélation gauche-droite "
        "faible (ZNSSD au-dessus de {1}) et {2} pour la distance épipolaire (au-dessus de {3} px).",
        "La comprobación estéreo eliminó {0} correspondencias por correlación izquierda-derecha "
        "débil (ZNSSD por encima de {1}) y {2} por distancia epipolar (por encima de {3} px).",
    ),
    (
        "The frame-1 stereo links lie a median {0} px from their epipolar lines: the "
        "calibration probably does not match these images (a camera moved, a wrong file, or "
        "left and right swapped). Check or redo the calibration.",
        "第 1 帧的立体匹配到其极线的距离中位数为 {0} px：标定很可能与这些图像不符"
        "（相机移动过、用错了文件，或左右相机颠倒）。请检查或重新标定。",
        "第 1 幀的立體匹配到其極線的距離中位數為 {0} px：標定很可能與這些影像不符"
        "（相機移動過、用錯了檔案，或左右相機顛倒）。請檢查或重新標定。",
        "フレーム 1 のステレオ対応はエピポーラ線から中央値 {0} px 離れています：キャリブレーションが"
        "これらの画像と合っていない可能性があります（カメラが動いた、ファイルの取り違え、"
        "左右の入れ替わり）。キャリブレーションを確認するかやり直してください。",
        "프레임 1의 스테레오 대응이 에피폴라 선에서 중앙값 {0} px 떨어져 있습니다: 보정이 "
        "이 이미지와 맞지 않을 가능성이 큽니다(카메라 이동, 잘못된 파일, 좌우 뒤바뀜). "
        "보정을 확인하거나 다시 하세요.",
        "Die Stereozuordnungen von Bild 1 liegen im Median {0} px neben ihren Epipolarlinien: "
        "Die Kalibrierung passt vermutlich nicht zu diesen Bildern (Kamera bewegt, falsche Datei "
        "oder links und rechts vertauscht). Kalibrierung prüfen oder neu erstellen.",
        "Les correspondances stéréo de l'image 1 sont à {0} px (médiane) de leurs droites "
        "épipolaires : l'étalonnage ne correspond probablement pas à ces images (caméra déplacée, "
        "mauvais fichier, ou gauche et droite inversées). Vérifiez ou refaites l'étalonnage.",
        "Las correspondencias estéreo del fotograma 1 están a una mediana de {0} px de sus "
        "líneas epipolares: la calibración probablemente no corresponde a estas imágenes (una "
        "cámara se movió, un archivo equivocado o izquierda y derecha intercambiadas). "
        "Compruebe o rehaga la calibración.",
    ),
    (
        "Many frame-1 stereo links lie off their epipolar lines: the calibration probably does "
        "not match these images (a camera moved, a wrong file, or left and right swapped). Check "
        "or redo the calibration.",
        "第 1 帧的许多立体匹配偏离其极线：标定很可能与这些图像不符"
        "（相机移动过、用错了文件，或左右相机颠倒）。请检查或重新标定。",
        "第 1 幀的許多立體匹配偏離其極線：標定很可能與這些影像不符"
        "（相機移動過、用錯了檔案，或左右相機顛倒）。請檢查或重新標定。",
        "フレーム 1 の多くのステレオ対応がエピポーラ線から外れています：キャリブレーションが"
        "これらの画像と合っていない可能性があります（カメラが動いた、ファイルの取り違え、"
        "左右の入れ替わり）。キャリブレーションを確認するかやり直してください。",
        "프레임 1의 많은 스테레오 대응이 에피폴라 선에서 벗어나 있습니다: 보정이 이 이미지와 "
        "맞지 않을 가능성이 큽니다(카메라 이동, 잘못된 파일, 좌우 뒤바뀜). 보정을 확인하거나 "
        "다시 하세요.",
        "Viele Stereozuordnungen von Bild 1 liegen neben ihren Epipolarlinien: Die Kalibrierung "
        "passt vermutlich nicht zu diesen Bildern (Kamera bewegt, falsche Datei oder links und "
        "rechts vertauscht). Kalibrierung prüfen oder neu erstellen.",
        "De nombreuses correspondances stéréo de l'image 1 s'écartent de leurs droites "
        "épipolaires : l'étalonnage ne correspond probablement pas à ces images (caméra déplacée, "
        "mauvais fichier, ou gauche et droite inversées). Vérifiez ou refaites l'étalonnage.",
        "Muchas correspondencias estéreo del fotograma 1 se apartan de sus líneas epipolares: la "
        "calibración probablemente no corresponde a estas imágenes (una cámara se movió, un "
        "archivo equivocado o izquierda y derecha intercambiadas). Compruebe o rehaga la "
        "calibración.",
    ),
    (
        "Correct stereo links can correlate weakly on a rough or strongly inclined surface. If "
        "points are missing, raise ADVANCED > Result checks > Stereo check (for example to 1.0).",
        "在粗糙或明显倾斜的表面上，正确的立体匹配也可能相关性偏弱。若缺点较多，"
        "请调高 高级 > 结果校验 > 立体校验（例如调到 1.0）。",
        "在粗糙或明顯傾斜的表面上，正確的立體匹配也可能相關性偏弱。若缺點較多，"
        "請調高 高級 > 結果校驗 > 立體校驗（例如調到 1.0）。",
        "粗い面や大きく傾いた面では、正しいステレオ対応でも相関が弱くなることがあります。"
        "点が欠ける場合は、詳細設定 > 結果のチェック > ステレオチェック を上げてください（例：1.0）。",
        "거칠거나 크게 기울어진 표면에서는 올바른 스테레오 대응도 상관이 약할 수 있습니다. "
        "점이 빠진다면 고급 설정 > 결과 검사 > 스테레오 검사 값을 올리세요(예: 1.0).",
        "Auf einer rauen oder stark geneigten Oberfläche können auch richtige Stereozuordnungen "
        "schwach korrelieren. Fehlen Punkte, ERWEITERT > Ergebnisprüfungen > Stereoprüfung "
        "erhöhen (zum Beispiel auf 1.0).",
        "Sur une surface rugueuse ou très inclinée, des correspondances stéréo correctes peuvent "
        "corréler faiblement. S'il manque des points, augmentez AVANCÉ > Contrôles des résultats > "
        "Contrôle stéréo (par exemple à 1.0).",
        "En una superficie rugosa o muy inclinada, las correspondencias estéreo correctas pueden "
        "correlacionar débilmente. Si faltan puntos, aumente AVANZADO > Comprobaciones de "
        "resultados > Comprobación estéreo (por ejemplo a 1.0).",
    ),
]

BATCH: dict[str, dict[str, str]] = {
    loc: {row[0]: row[1 + i] for row in _ROWS} for i, loc in enumerate(_LOCALES)
}
