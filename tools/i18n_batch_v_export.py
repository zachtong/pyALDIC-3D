"""Translations for the fix-batch-V export strings (export dialog + tabs).

``BATCH`` maps locale -> {English source: translation} for every user-facing
string the export-correctness batch added or changed (``gui/dialogs/
export_dialog.py`` and ``gui/dialogs/export_tabs/*.py``), plus the existing
strings that now also appear in a new translation context (the 3D View tab's
range controls), repeated with their established translations. Placeholders
(``{0}``, ``{1}``) are kept verbatim; "ROI", "GIF" and "MP4" stay untranslated
like everywhere else in the catalogs.

Merge into ``tools/fill_translations.py`` (or read it from there), then run
``python tools/i18n.py extract`` / ``fill_translations.py`` / ``i18n.py compile``.
"""
# ruff: noqa: E501, RUF001  (long translation lines; intentional full-width chars)

from __future__ import annotations

_TIP_3D_TAB = (
    "Offscreen renders of the 3D surface as images, a deforming animation or a "
    "turntable, from your current 3D view."
)
_GIF_NOTE = (
    "GIF timing has 1/100 s steps: {0} fps will play at {1} fps. Choose MP4 for faster playback."
)
_NOTHING = "Nothing was written — the export produced no files."
_DELETED = "(the unfinished animation was deleted)"
_NO_DATA_FOR_ALL = "Nothing was written: no data to draw for {0}."
_RIGHT_ROI = "the right-camera ROI could not be derived; the tracked area was used"
_SKIPPED = "{0} frame(s) had no data to draw ({1})"
_NO_DATA_FOR = "no data for {0}"
_KEPT = "Export cancelled — kept: {0}"
_AUTO_3D_TIP = (
    "Like the 3D view: each frame's 2–98 percentile of the values inside the ROI. "
    "Untick to use a fixed Min/Max for every frame."
)

BATCH: dict[str, dict[str, str]] = {
    "zh_CN": {
        _TIP_3D_TAB: "3D 曲面的离屏渲染，可导出为图像、变形动画或环绕动画，使用您当前的 3D 视角。",
        _GIF_NOTE: "GIF 的帧间隔精度为 1/100 秒：{0} fps 将以 {1} fps 播放。如需更高帧率请选择 MP4。",
        _NOTHING: "未写入任何文件 — 导出没有生成文件。",
        _DELETED: "（未完成的动画已删除）",
        _NO_DATA_FOR_ALL: "未写入任何文件：{0} 没有可绘制的数据。",
        _RIGHT_ROI: "无法推算右相机的 ROI；已改用跟踪区域",
        _SKIPPED: "{0} 帧没有可绘制的数据（{1}）",
        _NO_DATA_FOR: "{0} 没有数据",
        _KEPT: "导出已取消 — 已保留：{0}",
        _AUTO_3D_TIP: "与 3D 视图相同：每帧取 ROI 内数值的 2–98 百分位。取消勾选则对所有帧使用固定的最小/最大值。",
        "Auto range": "自动范围",
        "Min": "最小",
        "Max": "最大",
    },
    "zh_TW": {
        _TIP_3D_TAB: "3D 曲面的離屏渲染，可匯出為影像、變形動畫或環繞動畫，使用您目前的 3D 視角。",
        _GIF_NOTE: "GIF 的影格間隔精度為 1/100 秒：{0} fps 將以 {1} fps 播放。如需更高影格率請選擇 MP4。",
        _NOTHING: "未寫入任何檔案 — 匯出沒有產生檔案。",
        _DELETED: "（未完成的動畫已刪除）",
        _NO_DATA_FOR_ALL: "未寫入任何檔案：{0} 沒有可繪製的資料。",
        _RIGHT_ROI: "無法推算右相機的 ROI；已改用追蹤區域",
        _SKIPPED: "{0} 幀沒有可繪製的資料（{1}）",
        _NO_DATA_FOR: "{0} 沒有資料",
        _KEPT: "匯出已取消 — 已保留：{0}",
        _AUTO_3D_TIP: "與 3D 視圖相同：每幀取 ROI 內數值的 2–98 百分位。取消勾選則對所有幀使用固定的最小/最大值。",
        "Auto range": "自動範圍",
        "Min": "最小",
        "Max": "最大",
    },
    "ja": {
        _TIP_3D_TAB: "3D 表面のオフスクリーンレンダリング。現在の 3D ビューの視点で、画像・変形アニメーション・ターンテーブルとして書き出します。",
        _GIF_NOTE: "GIF のフレーム間隔は 1/100 秒単位です：{0} fps は {1} fps で再生されます。より速い再生には MP4 を選択してください。",
        _NOTHING: "何も書き出されませんでした — エクスポートでファイルが作成されませんでした。",
        _DELETED: "（未完了のアニメーションは削除しました）",
        _NO_DATA_FOR_ALL: "何も書き出されませんでした：{0} には描画できるデータがありません。",
        _RIGHT_ROI: "右カメラの ROI を導出できなかったため、追跡領域を使用しました",
        _SKIPPED: "{0} フレームに描画できるデータがありませんでした（{1}）",
        _NO_DATA_FOR: "{0} のデータなし",
        _KEPT: "エクスポートをキャンセルしました — 保持：{0}",
        _AUTO_3D_TIP: "3D ビューと同じく、各フレームで ROI 内の値の 2–98 パーセンタイルを使用します。オフにすると全フレームで固定の最小/最大値を使用します。",
        "Auto range": "自動レンジ",
        "Min": "最小",
        "Max": "最大",
    },
    "ko": {
        _TIP_3D_TAB: "현재 3D 뷰의 시점으로 3D 표면을 오프스크린 렌더링하여 이미지, 변형 애니메이션 또는 턴테이블로 내보냅니다.",
        _GIF_NOTE: "GIF의 프레임 간격은 1/100초 단위입니다: {0} fps는 {1} fps로 재생됩니다. 더 빠른 재생에는 MP4를 선택하세요.",
        _NOTHING: "아무것도 기록되지 않았습니다 — 내보내기에서 파일이 생성되지 않았습니다.",
        _DELETED: "(완료되지 않은 애니메이션은 삭제되었습니다)",
        _NO_DATA_FOR_ALL: "아무것도 기록되지 않았습니다: {0}에 그릴 데이터가 없습니다.",
        _RIGHT_ROI: "오른쪽 카메라의 ROI를 도출할 수 없어 추적 영역을 사용했습니다",
        _SKIPPED: "{0}개 프레임에 그릴 데이터가 없었습니다({1})",
        _NO_DATA_FOR: "{0} 데이터 없음",
        _KEPT: "내보내기 취소됨 — 유지: {0}",
        _AUTO_3D_TIP: "3D 뷰와 같이 각 프레임에서 ROI 안 값의 2–98 백분위수를 사용합니다. 체크를 해제하면 모든 프레임에 고정 최소/최대 값을 사용합니다.",
        "Auto range": "자동 범위",
        "Min": "최소",
        "Max": "최대",
    },
    "de": {
        _TIP_3D_TAB: "Offscreen-Renderings der 3D-Oberfläche als Bilder, Verformungsanimation oder Turntable, aus Ihrer aktuellen 3D-Ansicht.",
        _GIF_NOTE: "GIF-Bildzeiten haben 1/100-s-Schritte: {0} fps werden mit {1} fps abgespielt. Für schnellere Wiedergabe MP4 wählen.",
        _NOTHING: "Nichts geschrieben — der Export hat keine Dateien erzeugt.",
        _DELETED: "(die unvollständige Animation wurde gelöscht)",
        _NO_DATA_FOR_ALL: "Nichts geschrieben: keine darstellbaren Daten für {0}.",
        _RIGHT_ROI: "die ROI der rechten Kamera ließ sich nicht ableiten; der verfolgte Bereich wurde verwendet",
        _SKIPPED: "{0} Frame(s) ohne darstellbare Daten ({1})",
        _NO_DATA_FOR: "keine Daten für {0}",
        _KEPT: "Export abgebrochen — behalten: {0}",
        _AUTO_3D_TIP: "Wie in der 3D-Ansicht: pro Frame das 2–98-Perzentil der Werte innerhalb der ROI. Abwählen, um für alle Frames feste Min/Max-Werte zu verwenden.",
        "Auto range": "Auto-Bereich",
        "Min": "Min",
        "Max": "Max",
    },
    "fr": {
        _TIP_3D_TAB: "Rendus hors écran de la surface 3D en images, animation de déformation ou rotation orbitale, depuis votre vue 3D actuelle.",
        _GIF_NOTE: "La temporisation GIF a des pas de 1/100 s : {0} fps seront lus à {1} fps. Choisissez MP4 pour une lecture plus rapide.",
        _NOTHING: "Rien n'a été écrit — l'export n'a produit aucun fichier.",
        _DELETED: "(l'animation inachevée a été supprimée)",
        _NO_DATA_FOR_ALL: "Rien n'a été écrit : aucune donnée à afficher pour {0}.",
        _RIGHT_ROI: "la ROI de la caméra droite n'a pas pu être déduite ; la zone suivie a été utilisée",
        _SKIPPED: "{0} image(s) sans donnée à afficher ({1})",
        _NO_DATA_FOR: "aucune donnée pour {0}",
        _KEPT: "Export annulé — conservé : {0}",
        _AUTO_3D_TIP: "Comme la vue 3D : pour chaque image, les percentiles 2–98 des valeurs dans la ROI. Décochez pour utiliser un Min/Max fixe pour toutes les images.",
        "Auto range": "Plage automatique",
        "Min": "Min",
        "Max": "Max",
    },
    "es": {
        _TIP_3D_TAB: "Renderizados fuera de pantalla de la superficie 3D como imágenes, animación de deformación o rotación orbital, desde su vista 3D actual.",
        _GIF_NOTE: "La temporización GIF tiene pasos de 1/100 s: {0} fps se reproducirán a {1} fps. Elija MP4 para una reproducción más rápida.",
        _NOTHING: "No se escribió nada — la exportación no produjo archivos.",
        _DELETED: "(la animación inacabada se eliminó)",
        _NO_DATA_FOR_ALL: "No se escribió nada: no hay datos que dibujar para {0}.",
        _RIGHT_ROI: "no se pudo derivar la ROI de la cámara derecha; se usó el área seguida",
        _SKIPPED: "{0} fotograma(s) sin datos que dibujar ({1})",
        _NO_DATA_FOR: "sin datos para {0}",
        _KEPT: "Exportación cancelada — conservado: {0}",
        _AUTO_3D_TIP: "Como la vista 3D: en cada fotograma, los percentiles 2–98 de los valores dentro de la ROI. Desmarque para usar un Mín/Máx fijo en todos los fotogramas.",
        "Auto range": "Rango automático",
        "Min": "Mín",
        "Max": "Máx",
    },
}


def _check() -> None:
    """Every locale covers every source string and keeps its placeholders."""
    import re

    sources = set(BATCH["zh_CN"])
    for locale, table in BATCH.items():
        assert set(table) == sources, f"{locale}: {sorted(sources ^ set(table))}"
        for src, text in table.items():
            want = sorted(re.findall(r"\{\d\}", src))
            assert sorted(re.findall(r"\{\d\}", text)) == want, (locale, src)


_check()
