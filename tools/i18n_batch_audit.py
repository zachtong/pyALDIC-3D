"""New-user audit messages (2026-11-25): run errors, readiness, run-log advice, 7 locales.

``BATCH`` maps locale -> {English source -> translation}, merged by
``tools/fill_translations.py``. Terms follow the existing catalog
("Starting Point" = 种子点 / 種子點 / シード点 / 시드점 / Startpunkt / Point de
départ / Punto de inicio; "Subset Step" = 子集步长 / 子集步長 / サブセットステップ /
서브셋 간격 / Subset-Schrittweite / Pas d'imagette / Paso del subconjunto;
"stereo check" = 立体校验 / 立體校驗 / ステレオチェック / 스테레오 검사 /
Stereoprüfung / contrôle stéréo / comprobación estéreo; the epipolar wording of
``i18n_batch_advice.py``).
"""
# ruff: noqa: E501, RUF001

from __future__ import annotations

_LOCALES = ("zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es")

# (source, zh_CN, zh_TW, ja, ko, de, fr, es)
_ROWS: list[tuple[str, str, str, str, str, str, str, str]] = [
    (
        "{0}: the calibration was made for {1} images, but the images are {2}. Use the "
        "calibration of this setup (binned or cropped images need their own calibration).",
        "{0}：标定是针对 {1} 的图像做的，但这些图像为 {2}。请使用本套装置的标定"
        "（像素合并或裁剪过的图像需要各自的标定）。",
        "{0}：標定是針對 {1} 的影像做的，但這些影像為 {2}。請使用本套裝置的標定"
        "（像素合併或裁切過的影像需要各自的標定）。",
        "{0}：キャリブレーションは {1} の画像用ですが、画像は {2} です。このセットアップの"
        "キャリブレーションを使用してください（ビニングやトリミングをした画像には専用の"
        "キャリブレーションが必要です）。",
        "{0}: 보정은 {1} 이미지용인데 이미지는 {2}입니다. 이 셋업의 보정을 사용하세요"
        "(비닝하거나 잘라 낸 이미지에는 별도의 보정이 필요합니다).",
        "{0}: Die Kalibrierung wurde für Bilder mit {1} erstellt, die Bilder haben aber {2}. "
        "Die Kalibrierung dieses Aufbaus verwenden (gebinnte oder beschnittene Bilder brauchen "
        "eine eigene Kalibrierung).",
        "{0} : l'étalonnage a été fait pour des images de {1}, mais les images font {2}. "
        "Utilisez l'étalonnage de ce montage (des images binnées ou recadrées ont besoin de "
        "leur propre étalonnage).",
        "{0}: la calibración se hizo para imágenes de {1}, pero las imágenes miden {2}. Use la "
        "calibración de este montaje (las imágenes con binning o recortadas necesitan su propia "
        "calibración).",
    ),
    (
        "No point of frame 1 could be matched between the left and right images: the stereo "
        "check rejected {0} links for their distance from the epipolar line (median {1} px). "
        "The calibration probably does not match these images (a camera moved, a wrong file, "
        "or left and right swapped). Check or redo the calibration.",
        "第 1 帧没有任何点能在左右图像之间匹配：立体校验因偏离极线剔除了 {0} 个匹配"
        "（中位数 {1} px）。标定很可能与这些图像不符（相机移动过、用错了文件，或左右相机颠倒）。"
        "请检查或重新标定。",
        "第 1 幀沒有任何點能在左右影像之間匹配：立體校驗因偏離極線剔除了 {0} 個匹配"
        "（中位數 {1} px）。標定很可能與這些影像不符（相機移動過、用錯了檔案，或左右相機顛倒）。"
        "請檢查或重新標定。",
        "フレーム 1 のどの点も左右の画像間で対応付けできませんでした：ステレオチェックが"
        "エピポーラ線からの距離により {0} 個の対応を除外しました（中央値 {1} px）。"
        "キャリブレーションがこれらの画像と合っていない可能性があります（カメラが動いた、"
        "ファイルの取り違え、左右の入れ替わり）。キャリブレーションを確認するかやり直してください。",
        "프레임 1의 어떤 점도 왼쪽과 오른쪽 이미지 사이에서 대응시키지 못했습니다: 스테레오 "
        "검사가 에피폴라 선과의 거리 때문에 {0}개의 대응을 제외했습니다(중앙값 {1} px). 보정이 "
        "이 이미지와 맞지 않을 가능성이 큽니다(카메라 이동, 잘못된 파일, 좌우 뒤바뀜). 보정을 "
        "확인하거나 다시 하세요.",
        "Kein Punkt von Bild 1 konnte zwischen dem linken und dem rechten Bild zugeordnet "
        "werden: Die Stereoprüfung hat {0} Zuordnungen wegen ihres Abstands von der "
        "Epipolarlinie verworfen (Median {1} px). Die Kalibrierung passt vermutlich nicht zu "
        "diesen Bildern (Kamera bewegt, falsche Datei oder links und rechts vertauscht). "
        "Kalibrierung prüfen oder neu erstellen.",
        "Aucun point de l'image 1 n'a pu être apparié entre les images gauche et droite : le "
        "contrôle stéréo a rejeté {0} correspondances pour leur distance à la droite épipolaire "
        "(médiane {1} px). L'étalonnage ne correspond probablement pas à ces images (caméra "
        "déplacée, mauvais fichier, ou gauche et droite inversées). Vérifiez ou refaites "
        "l'étalonnage.",
        "Ningún punto del fotograma 1 pudo emparejarse entre las imágenes izquierda y derecha: "
        "la comprobación estéreo rechazó {0} correspondencias por su distancia a la línea "
        "epipolar (mediana {1} px). La calibración probablemente no corresponde a estas "
        "imágenes (una cámara se movió, un archivo equivocado o izquierda y derecha "
        "intercambiadas). Compruebe o rehaga la calibración.",
    ),
    (
        "No point of frame 1 could be matched between the left and right images. Likely "
        "causes, most likely first: (1) left and right are swapped: load the left camera's "
        "images as the left camera; (2) the calibration does not belong to these images "
        "(another rig or session, or binned or cropped images); (3) the region of interest "
        "has no speckle texture. Otherwise check the Starting Point and that both cameras "
        "see the region.",
        "第 1 帧没有任何点能在左右图像之间匹配。可能的原因（按可能性排序）：(1) 左右相机颠倒："
        "请把左相机的图像作为左相机载入；(2) 标定不属于这些图像（来自其他装置或其他时段，"
        "或图像经过像素合并或裁剪）；(3) 感兴趣区域内没有散斑纹理。否则请检查种子点，"
        "并确认两台相机都能看到该区域。",
        "第 1 幀沒有任何點能在左右影像之間匹配。可能的原因（按可能性排序）：(1) 左右相機顛倒："
        "請把左相機的影像作為左相機載入；(2) 標定不屬於這些影像（來自其他裝置或其他時段，"
        "或影像經過像素合併或裁切）；(3) 感興趣區域內沒有散斑紋理。否則請檢查種子點，"
        "並確認兩台相機都能看到該區域。",
        "フレーム 1 のどの点も左右の画像間で対応付けできませんでした。考えられる原因"
        "（可能性の高い順）：(1) 左右が入れ替わっている：左カメラの画像を左カメラとして"
        "読み込んでください。(2) キャリブレーションがこれらの画像のものではない（別のリグや"
        "別のセッション、またはビニングやトリミングをした画像）。(3) 関心領域にスペックル模様が"
        "ない。それ以外の場合は、シード点と、両方のカメラにその領域が写っていることを確認して"
        "ください。",
        "프레임 1의 어떤 점도 왼쪽과 오른쪽 이미지 사이에서 대응시키지 못했습니다. 가능성이 "
        "높은 순서의 원인: (1) 좌우가 뒤바뀜: 왼쪽 카메라의 이미지를 왼쪽 카메라로 불러오세요; "
        "(2) 보정이 이 이미지의 것이 아님(다른 장비나 다른 세션, 또는 비닝하거나 잘라 낸 "
        "이미지); (3) 관심 영역에 스페클 무늬가 없음. 그 밖에는 시드점과 두 카메라 모두 그 "
        "영역을 보는지 확인하세요.",
        "Kein Punkt von Bild 1 konnte zwischen dem linken und dem rechten Bild zugeordnet "
        "werden. Wahrscheinliche Ursachen, die wahrscheinlichste zuerst: (1) links und rechts "
        "sind vertauscht: die Bilder der linken Kamera als linke Kamera laden; (2) die "
        "Kalibrierung gehört nicht zu diesen Bildern (anderer Aufbau oder andere Sitzung, oder "
        "gebinnte bzw. beschnittene Bilder); (3) der Interessenbereich hat keine "
        "Speckle-Textur. Andernfalls den Startpunkt prüfen und ob beide Kameras den Bereich "
        "sehen.",
        "Aucun point de l'image 1 n'a pu être apparié entre les images gauche et droite. Causes "
        "probables, la plus probable d'abord : (1) gauche et droite sont inversées : chargez "
        "les images de la caméra gauche comme caméra gauche ; (2) l'étalonnage n'appartient pas "
        "à ces images (autre montage ou autre séance, ou images binnées ou recadrées) ; (3) la "
        "région d'intérêt n'a pas de texture de mouchetis. Sinon, vérifiez le point de départ "
        "et que les deux caméras voient la région.",
        "Ningún punto del fotograma 1 pudo emparejarse entre las imágenes izquierda y derecha. "
        "Causas probables, la más probable primero: (1) izquierda y derecha están "
        "intercambiadas: cargue las imágenes de la cámara izquierda como cámara izquierda; "
        "(2) la calibración no pertenece a estas imágenes (otro montaje u otra sesión, o "
        "imágenes con binning o recortadas); (3) la región de interés no tiene textura de "
        "moteado. Si no, compruebe el punto de inicio y que ambas cámaras vean la región.",
    ),
    (
        "This run would need about {0} GB of memory, more than {1} of the {2} GB available, "
        "for {3} frames. Analyse fewer frames, choose a coarser PARAMETERS > Subset Step, or "
        "draw a smaller region of interest; closing other applications also helps.",
        "此次运行约需 {0} GB 内存，超过可用 {2} GB 的 {1}（共 {3} 帧）。请分析更少的帧、"
        "在 参数 > 子集步长 中选择更大的步长，或绘制更小的感兴趣区域；关闭其他程序也有帮助。",
        "此次執行約需 {0} GB 記憶體，超過可用 {2} GB 的 {1}（共 {3} 幀）。請分析更少的幀、"
        "在 參數 > 子集步長 中選擇更大的步長，或繪製更小的感興趣區域；關閉其他程式也有幫助。",
        "この実行には約 {0} GB のメモリが必要で、使用可能な {2} GB の {1} を超えます"
        "（{3} フレーム）。解析するフレームを減らすか、パラメータ > サブセットステップ を"
        "より粗くするか、関心領域を小さく描いてください。他のアプリケーションを閉じることも"
        "有効です。",
        "이 실행에는 약 {0} GB의 메모리가 필요해 사용 가능한 {2} GB의 {1}을(를) 넘습니다"
        "({3}프레임). 분석할 프레임 수를 줄이거나, 매개변수 > 서브셋 간격을 더 크게 하거나, "
        "관심 영역을 더 작게 그리세요. 다른 프로그램을 닫는 것도 도움이 됩니다.",
        "Dieser Lauf bräuchte etwa {0} GB Arbeitsspeicher, mehr als {1} der verfügbaren "
        "{2} GB, für {3} Bilder. Weniger Bilder auswerten, unter PARAMETER > "
        "Subset-Schrittweite einen gröberen Wert wählen oder einen kleineren Interessenbereich "
        "zeichnen; auch das Schließen anderer Anwendungen hilft.",
        "Ce calcul demanderait environ {0} Go de mémoire, plus de {1} des {2} Go disponibles, "
        "pour {3} images. Analysez moins d'images, choisissez un PARAMÈTRES > Pas d'imagette "
        "plus grand ou dessinez une région d'intérêt plus petite ; fermer d'autres applications "
        "aide aussi.",
        "Este cálculo necesitaría unos {0} GB de memoria, más del {1} de los {2} GB "
        "disponibles, para {3} fotogramas. Analice menos fotogramas, elija un PARÁMETROS > "
        "Paso del subconjunto más grueso o dibuje una región de interés más pequeña; cerrar "
        "otras aplicaciones también ayuda.",
    ),
    (
        "The frame-1 stereo links lie a median {0} px from their epipolar lines (a calibration "
        "that fits the images gives under 0.3 px): a camera has probably moved since the "
        "calibration (bumped, refocused or re-aimed), which biases the 3D shape and "
        "displacements. Recalibrate the rig as it stands now.",
        "第 1 帧的立体匹配与其极线的距离中位数为 {0} px（与图像相符的标定应小于 0.3 px）："
        "自标定以来很可能有相机移动过（被碰到、重新对焦或重新调整方向），这会使三维形貌和位移"
        "产生偏差。请按装置当前状态重新标定。",
        "第 1 幀的立體匹配與其極線的距離中位數為 {0} px（與影像相符的標定應小於 0.3 px）："
        "自標定以來很可能有相機移動過（被碰到、重新對焦或重新調整方向），這會使三維形貌和位移"
        "產生偏差。請按裝置目前狀態重新標定。",
        "フレーム 1 のステレオ対応はエピポーラ線から中央値で {0} px 離れています（画像に合った"
        "キャリブレーションなら 0.3 px 未満）：キャリブレーション後にカメラが動いた可能性が"
        "あります（ぶつかった、ピントを合わせ直した、向きを変えた）。これは 3D 形状と変位に"
        "偏りを生じます。現在の状態のリグでキャリブレーションをやり直してください。",
        "프레임 1의 스테레오 대응이 에피폴라 선에서 중앙값 {0} px 떨어져 있습니다(이미지에 "
        "맞는 보정이면 0.3 px 미만): 보정 이후 카메라가 움직였을 가능성이 큽니다(부딪힘, 초점 "
        "재조정, 방향 변경). 이는 3D 형상과 변위에 편향을 줍니다. 현재 상태의 장비로 다시 "
        "보정하세요.",
        "Die Stereozuordnungen von Bild 1 liegen im Median {0} px neben ihren Epipolarlinien "
        "(eine zu den Bildern passende Kalibrierung ergibt unter 0,3 px): Vermutlich hat sich "
        "seit der Kalibrierung eine Kamera bewegt (angestoßen, neu fokussiert oder neu "
        "ausgerichtet), was die 3D-Form und die Verschiebungen verfälscht. Den Aufbau in seinem "
        "jetzigen Zustand neu kalibrieren.",
        "Les correspondances stéréo de l'image 1 s'écartent en médiane de {0} px de leurs "
        "droites épipolaires (un étalonnage adapté aux images donne moins de 0,3 px) : une "
        "caméra a probablement bougé depuis l'étalonnage (heurtée, refocalisée ou réorientée), "
        "ce qui biaise la forme 3D et les déplacements. Refaites l'étalonnage du montage tel "
        "qu'il est maintenant.",
        "Las correspondencias estéreo del fotograma 1 se apartan una mediana de {0} px de sus "
        "líneas epipolares (una calibración que corresponde a las imágenes da menos de "
        "0,3 px): probablemente una cámara se movió desde la calibración (golpeada, reenfocada "
        "o reorientada), lo que sesga la forma 3D y los desplazamientos. Recalibre el montaje "
        "tal como está ahora.",
    ),
    (
        "Partial result — {0} of {1} frames computed, median validity {2}%",
        "部分结果——已计算 {1} 帧中的 {0} 帧，有效率中位数 {2}%",
        "部分結果——已計算 {1} 幀中的 {0} 幀，有效率中位數 {2}%",
        "部分的な結果：{1} フレーム中 {0} フレームを計算、有効率の中央値 {2}%",
        "부분 결과 — {1}프레임 중 {0}프레임 계산됨, 유효율 중앙값 {2}%",
        "Teilergebnis — {0} von {1} Bildern berechnet, mittlere Gültigkeit {2} %",
        "Résultat partiel — {0} images calculées sur {1}, validité médiane {2} %",
        "Resultado parcial: {0} de {1} fotogramas calculados, validez mediana {2} %",
    ),
]

BATCH: dict[str, dict[str, str]] = {
    loc: {row[0]: row[1 + i] for row in _ROWS} for i, loc in enumerate(_LOCALES)
}
