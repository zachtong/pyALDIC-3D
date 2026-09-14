"""Calibration diagnostics translations (WP6 of the 2026-09-14 brief), 7 locales.

``BATCH`` maps locale -> {English source -> translation}, merged by
``tools/fill_translations.py``. Terms follow the existing catalog ("Optimize
board shape" = 优化标定板形貌 / 最佳化校正板形貌 / ボード形状を最適化 / 보드 형상 최적화 /
Tafelform optimieren / Optimiser la forme de la mire / Optimizar la forma del
tablero). Placeholders keep their format specs ({1:.0%}, {2:.2f}).
"""
# ruff: noqa: E501, RUF001

from __future__ import annotations

_LOCALES = ("zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es")

# (source, zh_CN, zh_TW, ja, ko, de, fr, es)
_ROWS: list[tuple[str, str, str, str, str, str, str, str]] = [
    (
        "Camera {0}: the board reached {1:.0%} of the image-corner radius. Beyond it the lens model is a guess: two equally good fits differ by up to {2:.2f} px there. Add views with the board near the image corners, keep the region of interest inside the covered area, or fix k3 for a low-distortion lens.",
        "相机 {0}：标定板只覆盖到图像角点半径的 {1:.0%}。在此之外，镜头模型是推测的：两个同样好的拟合在那里最多相差 {2:.2f} px。请补拍标定板靠近图像四角的视图，把感兴趣区域限制在覆盖范围内，或者对低畸变镜头固定 k3。",
        "相機 {0}：校正板只覆蓋到影像角點半徑的 {1:.0%}。在此之外，鏡頭模型是推測的：兩個同樣好的擬合在那裡最多相差 {2:.2f} px。請補拍校正板靠近影像四角的視圖，把感興趣區域限制在覆蓋範圍內，或者對低畸變鏡頭固定 k3。",
        "カメラ {0}：ボードは画像コーナー半径の {1:.0%} までしか届いていません。その外側のレンズモデルは推測です。同じくらい良い 2 つのフィットがそこで最大 {2:.2f} px 異なります。画像の隅近くにボードを置いたビューを追加するか、関心領域を覆われた範囲内に収めるか、低歪みレンズでは k3 を固定してください。",
        "카메라 {0}: 보드가 이미지 모서리 반경의 {1:.0%}까지만 닿았습니다. 그 바깥의 렌즈 모델은 추측입니다. 똑같이 좋은 두 피팅이 그곳에서 최대 {2:.2f} px 차이 납니다. 이미지 모서리 근처에 보드를 둔 뷰를 추가하거나, 관심 영역을 덮인 범위 안에 두거나, 저왜곡 렌즈라면 k3를 고정하세요.",
        "Kamera {0}: Die Tafel reichte bis {1:.0%} des Bildeckenradius. Darüber hinaus ist das Objektivmodell geraten: Zwei gleich gute Anpassungen weichen dort um bis zu {2:.2f} px ab. Fügen Sie Ansichten mit der Tafel nahe den Bildecken hinzu, halten Sie den interessierenden Bereich im abgedeckten Gebiet oder fixieren Sie k3 bei einem verzeichnungsarmen Objektiv.",
        "Caméra {0} : la mire n'a atteint que {1:.0%} du rayon des coins de l'image. Au-delà, le modèle d'objectif est une supposition : deux ajustements aussi bons y diffèrent jusqu'à {2:.2f} px. Ajoutez des vues avec la mire près des coins de l'image, gardez la région d'intérêt dans la zone couverte ou, pour un objectif à faible distorsion, fixez k3.",
        "Cámara {0}: el tablero solo alcanzó el {1:.0%} del radio de las esquinas de la imagen. Más allá, el modelo de lente es una suposición: dos ajustes igual de buenos difieren allí hasta {2:.2f} px. Añada vistas con el tablero cerca de las esquinas de la imagen, mantenga la región de interés dentro de la zona cubierta o, con una lente de baja distorsión, fije k3.",
    ),
    (
        "Camera {0}: the board reached {1:.0%} of the image-corner radius; the lens model is fitted only inside that radius.",
        "相机 {0}：标定板覆盖到图像角点半径的 {1:.0%}；镜头模型只在这个半径以内拟合。",
        "相機 {0}：校正板覆蓋到影像角點半徑的 {1:.0%}；鏡頭模型只在這個半徑以內擬合。",
        "カメラ {0}：ボードは画像コーナー半径の {1:.0%} まで届いています。レンズモデルはこの半径の内側だけでフィットされています。",
        "카메라 {0}: 보드가 이미지 모서리 반경의 {1:.0%}까지 닿았습니다. 렌즈 모델은 이 반경 안쪽에서만 피팅됩니다.",
        "Kamera {0}: Die Tafel reichte bis {1:.0%} des Bildeckenradius; das Objektivmodell ist nur innerhalb dieses Radius angepasst.",
        "Caméra {0} : la mire a atteint {1:.0%} du rayon des coins de l'image ; le modèle d'objectif n'est ajusté qu'à l'intérieur de ce rayon.",
        "Cámara {0}: el tablero alcanzó el {1:.0%} del radio de las esquinas de la imagen; el modelo de lente solo se ajusta dentro de ese radio.",
    ),
    (
        "Camera {0}: the board reached {1:.0%} of the image-corner radius. Beyond it the lens model is a guess: two equally good fits differ by up to {2:.2f} px there. With k3 fixed, the corners are right only if the lens has no k3 distortion: add views with the board near the image corners, or keep the region of interest inside the covered area.",
        "相机 {0}：标定板只覆盖到图像角点半径的 {1:.0%}。在此之外，镜头模型是推测的：两个同样好的拟合在那里最多相差 {2:.2f} px。固定 k3 后，只有当镜头确实没有 k3 畸变时角点区域才准确：请补拍标定板靠近图像四角的视图，或者把感兴趣区域限制在覆盖范围内。",
        "相機 {0}：校正板只覆蓋到影像角點半徑的 {1:.0%}。在此之外，鏡頭模型是推測的：兩個同樣好的擬合在那裡最多相差 {2:.2f} px。固定 k3 後，只有當鏡頭確實沒有 k3 畸變時角點區域才準確：請補拍校正板靠近影像四角的視圖，或者把感興趣區域限制在覆蓋範圍內。",
        "カメラ {0}：ボードは画像コーナー半径の {1:.0%} までしか届いていません。その外側のレンズモデルは推測です。同じくらい良い 2 つのフィットがそこで最大 {2:.2f} px 異なります。k3 を固定した場合、コーナーが正しいのはレンズに k3 歪みがないときだけです。画像の隅近くにボードを置いたビューを追加するか、関心領域を覆われた範囲内に収めてください。",
        "카메라 {0}: 보드가 이미지 모서리 반경의 {1:.0%}까지만 닿았습니다. 그 바깥의 렌즈 모델은 추측입니다. 똑같이 좋은 두 피팅이 그곳에서 최대 {2:.2f} px 차이 납니다. k3를 고정하면 렌즈에 k3 왜곡이 없을 때만 모서리가 정확합니다. 이미지 모서리 근처에 보드를 둔 뷰를 추가하거나 관심 영역을 덮인 범위 안에 두세요.",
        "Kamera {0}: Die Tafel reichte bis {1:.0%} des Bildeckenradius. Darüber hinaus ist das Objektivmodell geraten: Zwei gleich gute Anpassungen weichen dort um bis zu {2:.2f} px ab. Mit fixiertem k3 stimmen die Ecken nur, wenn das Objektiv keine k3-Verzeichnung hat: Fügen Sie Ansichten mit der Tafel nahe den Bildecken hinzu oder halten Sie den interessierenden Bereich im abgedeckten Gebiet.",
        "Caméra {0} : la mire n'a atteint que {1:.0%} du rayon des coins de l'image. Au-delà, le modèle d'objectif est une supposition : deux ajustements aussi bons y diffèrent jusqu'à {2:.2f} px. Avec k3 fixé, les coins ne sont justes que si l'objectif n'a pas de distorsion k3 : ajoutez des vues avec la mire près des coins de l'image ou gardez la région d'intérêt dans la zone couverte.",
        "Cámara {0}: el tablero solo alcanzó el {1:.0%} del radio de las esquinas de la imagen. Más allá, el modelo de lente es una suposición: dos ajustes igual de buenos difieren allí hasta {2:.2f} px. Con k3 fijado, las esquinas solo son correctas si la lente no tiene distorsión k3: añada vistas con el tablero cerca de las esquinas de la imagen o mantenga la región de interés dentro de la zona cubierta.",
    ),
    (
        "Camera {0}: the residuals follow a pattern the lens model does not explain (binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model fits). Often the board is the cause (not flat, or its points not exactly where the board description puts them): tick Joint bundle adjustment and Optimize board shape. A lens the model cannot describe or detector bias can also cause this.",
        "相机 {0}：残差呈现镜头模型解释不了的规律（分格超额 {1:.1f}，拟合场 {2:.1f} × 噪声；模型合适时约为 1）。常见原因是标定板本身（不平，或者点的实际位置与标定板描述不完全一致）：请勾选“联合光束平差”和“优化标定板形貌”。模型描述不了的镜头或检测偏差也可能导致这种情况。",
        "相機 {0}：殘差呈現鏡頭模型解釋不了的規律（分格超額 {1:.1f}，擬合場 {2:.1f} × 雜訊；模型合適時約為 1）。常見原因是校正板本身（不平，或者點的實際位置與校正板描述不完全一致）：請勾選「聯合光束平差」和「最佳化校正板形貌」。模型描述不了的鏡頭或偵測偏差也可能導致這種情況。",
        "カメラ {0}：残差にレンズモデルでは説明できないパターンがあります（ビン超過 {1:.1f}、フィット場 {2:.1f} × ノイズ。モデルが合っていれば約 1）。原因はボードであることが多いです（平らでない、または点がボードの記述どおりの位置にない）。「バンドル調整」と「ボード形状を最適化」にチェックを入れてください。モデルで表せないレンズや検出の偏りが原因のこともあります。",
        "카메라 {0}: 잔차에 렌즈 모델이 설명하지 못하는 패턴이 있습니다(구간 초과 {1:.1f}, 적합 장 {2:.1f} × 노이즈, 모델이 맞으면 약 1). 원인은 보드인 경우가 많습니다(평평하지 않거나 점이 보드 설명과 정확히 같은 위치에 있지 않음). '번들 조정'과 '보드 형상 최적화'를 선택하세요. 모델이 표현할 수 없는 렌즈나 검출 편향도 원인일 수 있습니다.",
        "Kamera {0}: Die Residuen folgen einem Muster, das das Objektivmodell nicht erklärt (Zellenüberschuss {1:.1f}, angepasstes Feld {2:.1f} × Rauschen; etwa 1, wenn das Modell passt). Oft ist die Tafel die Ursache (nicht eben, oder ihre Punkte liegen nicht genau dort, wo die Tafelbeschreibung sie annimmt): Aktivieren Sie „Bündelausgleich“ und „Tafelform optimieren“. Auch ein Objektiv, das das Modell nicht beschreibt, oder ein Detektorfehler kann dies verursachen.",
        "Caméra {0} : les résidus suivent un motif que le modèle d'objectif n'explique pas (excès par cellule {1:.1f}, champ ajusté {2:.1f} × bruit ; environ 1 quand le modèle convient). Souvent la mire en est la cause (pas plane, ou ses points pas exactement là où sa description les place) : cochez « Ajustement de faisceaux » et « Optimiser la forme de la mire ». Un objectif que le modèle ne sait pas décrire ou un biais du détecteur peuvent aussi en être la cause.",
        "Cámara {0}: los residuos siguen un patrón que el modelo de lente no explica (exceso por celda {1:.1f}, campo ajustado {2:.1f} × ruido; cerca de 1 cuando el modelo encaja). A menudo la causa es el tablero (no es plano, o sus puntos no están exactamente donde indica su descripción): marque «Ajuste de haces» y «Optimizar la forma del tablero». Una lente que el modelo no describe o un sesgo del detector también pueden causarlo.",
    ),
    (
        "Camera {0}: the residuals follow a pattern the lens model does not explain (binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model fits), although the board shape is already optimised. A lens the model cannot describe, a board that bends differently from view to view, or detector bias can cause this.",
        "相机 {0}：残差呈现镜头模型解释不了的规律（分格超额 {1:.1f}，拟合场 {2:.1f} × 噪声；模型合适时约为 1），尽管标定板形貌已经优化过。可能的原因：模型描述不了的镜头、在不同视图中弯曲程度不同的标定板，或检测偏差。",
        "相機 {0}：殘差呈現鏡頭模型解釋不了的規律（分格超額 {1:.1f}，擬合場 {2:.1f} × 雜訊；模型合適時約為 1），儘管校正板形貌已經最佳化過。可能的原因：模型描述不了的鏡頭、在不同視圖中彎曲程度不同的校正板，或偵測偏差。",
        "カメラ {0}：ボード形状はすでに最適化されていますが、残差にレンズモデルでは説明できないパターンがあります（ビン超過 {1:.1f}、フィット場 {2:.1f} × ノイズ。モデルが合っていれば約 1）。モデルで表せないレンズ、ビューごとに曲がり方が変わるボード、または検出の偏りが原因になり得ます。",
        "카메라 {0}: 보드 형상을 이미 최적화했는데도 잔차에 렌즈 모델이 설명하지 못하는 패턴이 있습니다(구간 초과 {1:.1f}, 적합 장 {2:.1f} × 노이즈, 모델이 맞으면 약 1). 모델이 표현할 수 없는 렌즈, 뷰마다 다르게 휘는 보드 또는 검출 편향이 원인일 수 있습니다.",
        "Kamera {0}: Die Residuen folgen einem Muster, das das Objektivmodell nicht erklärt (Zellenüberschuss {1:.1f}, angepasstes Feld {2:.1f} × Rauschen; etwa 1, wenn das Modell passt), obwohl die Tafelform bereits optimiert ist. Ursachen können ein Objektiv sein, das das Modell nicht beschreibt, eine Tafel, die sich von Ansicht zu Ansicht anders biegt, oder ein Detektorfehler.",
        "Caméra {0} : les résidus suivent un motif que le modèle d'objectif n'explique pas (excès par cellule {1:.1f}, champ ajusté {2:.1f} × bruit ; environ 1 quand le modèle convient), bien que la forme de la mire soit déjà optimisée. Un objectif que le modèle ne sait pas décrire, une mire qui se courbe différemment d'une vue à l'autre ou un biais du détecteur peuvent en être la cause.",
        "Cámara {0}: los residuos siguen un patrón que el modelo de lente no explica (exceso por celda {1:.1f}, campo ajustado {2:.1f} × ruido; cerca de 1 cuando el modelo encaja), aunque la forma del tablero ya está optimizada. Puede deberse a una lente que el modelo no describe, a un tablero que se curva de forma distinta en cada vista o a un sesgo del detector.",
    ),
    (
        "Camera {0}: the extrapolation check was skipped (too few usable views).",
        "相机 {0}：外推检查已跳过（可用视图太少）。",
        "相機 {0}：外推檢查已略過（可用視圖太少）。",
        "カメラ {0}：外挿チェックはスキップされました（使えるビューが少なすぎます）。",
        "카메라 {0}: 외삽 검사를 건너뛰었습니다(사용 가능한 뷰가 너무 적음).",
        "Kamera {0}: Die Extrapolationsprüfung wurde übersprungen (zu wenige nutzbare Ansichten).",
        "Caméra {0} : la vérification d'extrapolation a été ignorée (trop peu de vues utilisables).",
        "Cámara {0}: se omitió la comprobación de extrapolación (demasiado pocas vistas utilizables).",
    ),
    (
        "Camera {0}: the lens-model check was skipped: the points fill only {1} image cells.",
        "相机 {0}：镜头模型检查已跳过：标定点只落在 {1} 个图像格子里。",
        "相機 {0}：鏡頭模型檢查已略過：校正點只落在 {1} 個影像格子裡。",
        "カメラ {0}：レンズモデルのチェックはスキップされました。点が {1} 個の画像セルにしかありません。",
        "카메라 {0}: 렌즈 모델 검사를 건너뛰었습니다. 점이 {1}개의 이미지 셀에만 있습니다.",
        "Kamera {0}: Die Prüfung des Objektivmodells wurde übersprungen: Die Punkte füllen nur {1} Bildzellen.",
        "Caméra {0} : la vérification du modèle d'objectif a été ignorée : les points ne remplissent que {1} cellules de l'image.",
        "Cámara {0}: se omitió la comprobación del modelo de lente: los puntos solo ocupan {1} celdas de la imagen.",
    ),
]

BATCH: dict[str, dict[str, str]] = {
    loc: {row[0]: row[1 + i] for row in _ROWS} for i, loc in enumerate(_LOCALES)
}
