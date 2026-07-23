<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="sd_PK">
<context>
    <name>AboutDialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="36"/>
        <source>About pyALDIC-3D</source>
        <translation>關於 pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="47"/>
        <source>Version {0}</source>
        <translation>版本 {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="52"/>
        <source>Stereo (3D) digital image correlation — full-field displacement and surface strain from a calibrated camera pair.</source>
        <translation>立體（3D）數位影像相關——由已標定的相機對取得全場位移與表面應變。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="63"/>
        <source>Citation: Zenodo DOI pending release.</source>
        <translation>引用：Zenodo DOI 待發佈。</translation>
    </message>
</context>
<context>
    <name>AdvancedSection3D</name>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="34"/>
        <source>Track Both</source>
        <translation>雙相機追蹤</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="35"/>
        <source>Stereo Each Frame</source>
        <translation>逐幀立體匹配</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="36"/>
        <source>Reference Direct</source>
        <translation>參考幀直接匹配</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="39"/>
        <source>How stereo correspondences are propagated through time.
Track Both (default): match stereo once at frame 1, then
track each camera temporally — fastest, one stereo solve.
Stereo Each Frame: re-match stereo at every frame — robust
when temporal tracking drifts, slower.
Reference Direct: match every frame directly to frame 1 in
both cameras — no drift accumulation, small motions only.</source>
        <translation>立體對應關係隨時間傳播的方式。
雙相機追蹤（預設）：僅在第 1 幀做一次立體匹配，之後在每台相機內做時序追蹤 — 最快，只需一次立體求解。
逐幀立體匹配：每幀重新做立體匹配 — 時序追蹤漂移時更穩健，但更慢。
參考幀直接匹配：兩台相機的每一幀都直接與第 1 幀匹配 — 不累積漂移，僅適用於小運動。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="48"/>
        <source>Strategy</source>
        <translation>策略</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="55"/>
        <source>1 = single global pass (fastest), 3 = default, 5+ = diminishing returns</source>
        <translation>1 = 單次全域求解（最快），3 = 預設值，5 次以上收益遞減</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="57"/>
        <source>AL-DIC Iterations</source>
        <translation>AL-DIC 迭代次數</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="59"/>
        <source>Only affects AL-DIC solver. Ignored by Local DIC.</source>
        <translation>僅對 AL-DIC 求解器生效，Local DIC 會忽略。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="65"/>
        <source>Parallel camera tracking</source>
        <translation>並行相機追蹤</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="68"/>
        <source>Track both cameras concurrently — modest speedup (the solver already uses all cores), doubles peak memory</source>
        <translation>並行追蹤兩台相機——提速有限（求解器本已用滿全部核心），峰值記憶體加倍</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="75"/>
        <source>Auto-expand FFT search on clipped peaks</source>
        <translation>FFT 峰值被截斷時自動擴大搜尋區域</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="79"/>
        <source>When the temporal FFT integer peak lands on the search-region
boundary, retry with a larger region (engine default on).
Disable for strictly bounded runtimes; then Temporal Search
must cover the largest per-frame motion by itself.</source>
        <translation>當時序 FFT 整數峰值落在搜尋區域邊界上時，
自動以更大的區域重試（引擎預設開啟）。
如需嚴格限定執行時間可關閉；此時「時序搜尋」必須
自行涵蓋最大的幀間運動。</translation>
    </message>
</context>
<context>
    <name>AnimationTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="54"/>
        <source>Fields</source>
        <translation>場變數</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="71"/>
        <source>Format</source>
        <translation>格式</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="78"/>
        <source>Frames per second</source>
        <translation>每秒影格數</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="85"/>
        <source>Frame step</source>
        <translation>抽幀間隔</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="86"/>
        <source>Keep every Nth frame (1 = all)</source>
        <translation>每 N 影格保留一格（1 = 全部保留）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="93"/>
        <source>Resolution (long edge)</source>
        <translation>解析度（長邊）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="101"/>
        <source>Include colorbar</source>
        <translation>包含色條</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="106"/>
        <source>Background</source>
        <translation>背景</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="120"/>
        <source>Export Animation</source>
        <translation>匯出動畫</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="131"/>
        <source>Load an image sequence first (open the project in the main window).</source>
        <translation>請先載入影像序列（在主視窗中開啟專案）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="146"/>
        <source>Choose an output folder first.</source>
        <translation>請先選擇輸出資料夾。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="150"/>
        <source>No fields enabled.</source>
        <translation>未啟用任何場變數。</translation>
    </message>
</context>
<context>
    <name>BackgroundRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="416"/>
        <source>Original (frame 1 background)</source>
        <translation>原始配置（第 1 影格作背景）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="417"/>
        <source>Deformed (current frame background)</source>
        <translation>變形配置（當前影格作背景）</translation>
    </message>
</context>
<context>
    <name>CalibrationDialog</name>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="81"/>
        <source>Stereo Calibration</source>
        <translation>立體校正</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="112"/>
        <source>CALIBRATION IMAGE PAIRS</source>
        <translation>校正影像對</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="115"/>
        <source>Add left images…</source>
        <translation>加入左相機影像…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="117"/>
        <source>Add right images…</source>
        <translation>加入右相機影像…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="119"/>
        <source>Clear</source>
        <translation>清除</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="121"/>
        <source>Save detections…</source>
        <translation>儲存偵測結果…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="124"/>
        <source>Load detections…</source>
        <translation>載入偵測結果…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="131"/>
        <source>No images loaded</source>
        <translation>尚未載入影像</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="139"/>
        <source>Left</source>
        <translation>左</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="140"/>
        <source>Right</source>
        <translation>右</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="141"/>
        <source>Points</source>
        <translation>點數</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="142"/>
        <source>RMS L/R</source>
        <translation>RMS 左/右</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="143"/>
        <source>Max E</source>
        <translation>最大誤差</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="144"/>
        <source>Status</source>
        <translation>狀態</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="155"/>
        <source>SELECTED PAIR (L | R)</source>
        <translation>選中的影像對（左 | 右）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="156"/>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="388"/>
        <source>select a pair to preview detected points</source>
        <translation>選擇一對影像以預覽偵測到的點</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="163"/>
        <source>Click to enlarge the annotated detection</source>
        <translation>點擊放大標註偵測結果</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="167"/>
        <source>PER-PAIR REPROJECTION ERROR</source>
        <translation>逐對重投影誤差</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="172"/>
        <source>Reject threshold (px)</source>
        <translation>剔除閾值（像素）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="181"/>
        <source>Recalibrate</source>
        <translation>重新校正</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="193"/>
        <source>CALIBRATION BOARD</source>
        <translation>校正板</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="201"/>
        <source>Chessboard</source>
        <translation>棋盤格</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="202"/>
        <source>ChArUco</source>
        <translation>ChArUco</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="203"/>
        <source>Circle grid</source>
        <translation>圓點陣列</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="204"/>
        <source>Coded dot target (3 ring markers)</source>
        <translation>編碼圓點靶（3 個環形標記）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="206"/>
        <source>Type</source>
        <translation>類型</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="211"/>
        <source>Columns x Rows</source>
        <translation>行數 × 列數</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="218"/>
        <source>Square size (mm)</source>
        <translation>方格邊長（mm）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="223"/>
        <source>Marker size (mm)</source>
        <translation>標記邊長（mm）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="228"/>
        <source>Dot pitch (mm)</source>
        <translation>圓點間距（mm）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="233"/>
        <source>Dot diameter (mm)</source>
        <translation>圓點直徑（mm）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="237"/>
        <source>Asymmetric grid</source>
        <translation>非對稱陣列</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="239"/>
        <source>Board printed with OpenCV &lt; 4.7</source>
        <translation>使用 OpenCV &lt; 4.7 列印的校正板</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="243"/>
        <source>Print board… (1:1 PDF)</source>
        <translation>列印校正板…（1:1 PDF）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="247"/>
        <source>SOLVER OPTIONS</source>
        <translation>求解選項</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="248"/>
        <source>Jointly refine intrinsics (advanced)</source>
        <translation>聯合精化內參（進階）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="249"/>
        <source>Estimate tangential distortion p1/p2</source>
        <translation>估計切向畸變 p1/p2</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="250"/>
        <source>Fix k3 = 0 (low-distortion lens)</source>
        <translation>固定 k3 = 0（低畸變鏡頭）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="251"/>
        <source>Release-object method (printed boards)</source>
        <translation>Release-object 方法（列印校正板）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="252"/>
        <source>Dot eccentricity correction</source>
        <translation>圓點偏心修正</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="254"/>
        <source>Joint bundle adjustment (robust, uses mono views)</source>
        <translation>聯合光束平差（穩健，可利用單相機視圖）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="255"/>
        <source>Optimize board shape (printed boards)</source>
        <translation>最佳化校正板形貌（列印板）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="270"/>
        <source>Calibrate</source>
        <translation>校正</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="281"/>
        <source>RESULT</source>
        <translation>結果</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="282"/>
        <source>No calibration yet</source>
        <translation>尚未校正</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="287"/>
        <source>Verify with board images…</source>
        <translation>用校正板影像驗證…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="299"/>
        <source>Accept &amp;&amp; Save…</source>
        <translation>接受並儲存…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="305"/>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="364"/>
        <source>Choose {0} calibration images</source>
        <translation>選擇 {0} 相機校正影像</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="366"/>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="702"/>
        <source>Images (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)</source>
        <translation>影像檔 (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="412"/>
        <source>{0} left / {1} right images</source>
        <translation>左 {0} 張 / 右 {1} 張</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="422"/>
        <source>Load equal, &gt;= 3 left/right image sets first.</source>
        <translation>請先載入數量相等且 ≥ 3 組的左右影像。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="453"/>
        <source>Working… {0}</source>
        <translation>處理中… {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="462"/>
        <source>Calibration failed: {0}</source>
        <translation>校正失敗：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="486"/>
        <source>used</source>
        <translation>已採用</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="488"/>
        <source>L: {0}</source>
        <translation>左：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="490"/>
        <source>R: {0}</source>
        <translation>右：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="506"/>
        <source>Stereo RMS {0:.3f} px | epipolar {1:.3f} px</source>
        <translation>立體 RMS {0:.3f} px | 極線 {1:.3f} px</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="509"/>
        <source>Baseline {0:.2f} mm | pairs {1}/{2}</source>
        <translation>基線 {0:.2f} mm | 影像對 {1}/{2}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="512"/>
        <source>fx {0:.1f}  fy {1:.1f}  cx {2:.1f}  cy {3:.1f}</source>
        <translation>fx {0:.1f}  fy {1:.1f}  cx {2:.1f}  cy {3:.1f}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="515"/>
        <source>Coverage L {0:.0%} / R {1:.0%} | tilt {2:.0f}-{3:.0f}°</source>
        <translation>覆蓋率 左 {0:.0%} / 右 {1:.0%} | 傾角 {2:.0f}-{3:.0f}°</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="524"/>
        <source>Bundle adjustment: RMS {0:.3f} -&gt; {1:.3f} px ({2:.0f} mono views)</source>
        <translation>光束平差：RMS {0:.3f} -&gt; {1:.3f} px（單相機視圖 {2:.0f} 個）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="530"/>
        <source>Board flatness: z-range {0:.3f} mm</source>
        <translation>校正板平整度：z 範圍 {0:.3f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="533"/>
        <source>Warning: {0}</source>
        <translation>警告：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="548"/>
        <source>Save detections</source>
        <translation>儲存偵測結果</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="548"/>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="567"/>
        <source>NumPy detections (*.npz)</source>
        <translation>NumPy 偵測結果 (*.npz)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="563"/>
        <source>Detections saved: {0}</source>
        <translation>偵測結果已儲存：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="567"/>
        <source>Load detections</source>
        <translation>載入偵測結果</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="589"/>
        <source>Loaded {0} detection pairs — Recalibrate re-solves without re-detecting</source>
        <translation>已載入 {0} 組偵測結果——點擊重新校正即可免偵測重解</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="676"/>
        <source>Save board PDF</source>
        <translation>儲存校正板 PDF</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="676"/>
        <source>PDF (*.pdf)</source>
        <translation>PDF (*.pdf)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="687"/>
        <source>Board PDF written: {0}</source>
        <translation>校正板 PDF 已寫入：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="704"/>
        <source>Choose LEFT verification image</source>
        <translation>選擇左相機驗證影像</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="709"/>
        <source>Choose RIGHT verification image</source>
        <translation>選擇右相機驗證影像</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="718"/>
        <source>Verification failed: {0}</source>
        <translation>驗證失敗：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="724"/>
        <source>Verify: pitch {0:.4f} mm vs {1:g} mm — scale error {2:.3%}, plane RMS {3:.4f} mm</source>
        <translation>驗證：間距 {0:.4f} mm 對比 {1:g} mm——尺度誤差 {2:.3%}，平面 RMS {3:.4f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="738"/>
        <source>Save calibration as</source>
        <translation>校正另存為</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="740"/>
        <source>OpenCV YAML (*.yml *.yaml *.xml)</source>
        <translation>OpenCV YAML (*.yml *.yaml *.xml)</translation>
    </message>
</context>
<context>
    <name>CalibrationSection3D</name>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="50"/>
        <source>Calibrate from images…</source>
        <translation>從影像校正…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="54"/>
        <source>Run the built-in stereo calibrator on your target photos
(checkerboard / ChArUco / dot grid). Writes an opencv_yaml
file and loads it — the recommended path when you have
calibration images.</source>
        <translation>對您的標定靶照片執行內建立體標定器（棋盤格 / ChArUco / 圓點網格）。
寫出 opencv_yaml 檔案並載入 — 有標定影像時推薦使用此方式。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="65"/>
        <source>Format</source>
        <translation>格式</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="74"/>
        <source>File format of the calibration to import. Default opencv_yaml
(written by the built-in calibrator). Pick the format matching
your source: dice (DICe XML), matchid (MatchID .caldat),
opencorr (OpenCorr CSV), mmc (MultiDIC/MMC .mat), matlabcv
(MATLAB stereoParams .mat).</source>
        <translation>要匯入的標定檔案格式。預設 opencv_yaml（內建標定器寫出的格式）。
請按來源選擇：dice（DICe XML）、matchid（MatchID .caldat）、
opencorr（OpenCorr CSV）、mmc（MultiDIC/MMC .mat）、
matlabcv（MATLAB stereoParams .mat）。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="85"/>
        <source>Import calibration…</source>
        <translation>匯入標定…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="88"/>
        <source>Load an existing stereo calibration file in the selected
Format. The status line below shows fx / fy and the baseline
as a sanity check.</source>
        <translation>以所選格式載入既有的立體標定檔案。
下方狀態行會顯示 fx / fy 與基線，用作合理性檢查。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="96"/>
        <source>Manual parameters…</source>
        <translation>手動輸入參數…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="99"/>
        <source>Type intrinsics and extrinsics by hand (fx, fy, cx, cy,
distortion, R, T) — the fallback when no calibration file
exists. Writes an opencv_yaml file and loads it.</source>
        <translation>手動輸入內參與外參（fx、fy、cx、cy、畸變、R、T）
— 沒有任何標定檔案時的後備方案。寫出 opencv_yaml 檔案並載入。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="107"/>
        <source>No calibration loaded</source>
        <translation>尚未載入標定</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="148"/>
        <source>Choose calibration file</source>
        <translation>選擇標定檔案</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="150"/>
        <source>Calibration files (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)</source>
        <translation>標定檔案 (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="168"/>
        <source>Error: {0}</source>
        <translation>錯誤：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="176"/>
        <source>{0}
fx {1:.0f}  fy {2:.0f}  |  baseline {3:.1f} mm</source>
        <translation>{0}
fx {1:.0f}  fy {2:.0f}  |  基線 {3:.1f} mm</translation>
    </message>
</context>
<context>
    <name>CameraDropZone</name>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="76"/>
        <source>{0} frames</source>
        <translation>{0} 幀</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="103"/>
        <source>Click to pick this camera&apos;s image folder, or drag the folder here. Both cameras need the same number of frames.</source>
        <translation>點擊選擇該相機的影像資料夾，或將資料夾拖到此處。兩台相機的幀數必須一致。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="114"/>
        <source>Select image folder</source>
        <translation>選擇影像資料夾</translation>
    </message>
</context>
<context>
    <name>CameraRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="384"/>
        <source>Camera</source>
        <translation>相機</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="388"/>
        <source>Left</source>
        <translation>左</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="389"/>
        <source>Right</source>
        <translation>右</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="390"/>
        <source>Left + Right</source>
        <translation>左 + 右</translation>
    </message>
</context>
<context>
    <name>CanvasArea3D</name>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="96"/>
        <source>Fit</source>
        <translation>適配</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="99"/>
        <source>Fit the image to the viewport (Ctrl+0)</source>
        <translation>將影像適配到視口 (Ctrl+0)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="106"/>
        <source>Current zoom — click to reset to 100% (1:1 pixels).
Wheel: zoom · Right/middle drag: pan · Space: pan mode</source>
        <translation>當前縮放 — 點擊恢復 100%（1:1 像素）。
滾輪：縮放 · 右鍵/中鍵拖動：平移 · 空白鍵：平移模式</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="113"/>
        <source>Zoom in (Ctrl+=)</source>
        <translation>放大 (Ctrl+=)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="117"/>
        <source>Zoom out (Ctrl+-)</source>
        <translation>縮小 (Ctrl+-)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="122"/>
        <source>Show Grid</source>
        <translation>顯示網格</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="125"/>
        <source>Show the computational mesh preview on the reference view
(left camera, frame 1). Rebuilt live from the current Subset
Step / refinement settings — what you see is the run&apos;s mesh.
Default on; turn off to declutter the canvas.</source>
        <translation>在參考視圖（左相機第 1 幀）上顯示計算網格預覽。
隨當前子集步長/加密設定即時重建 — 所見即執行時使用的網格。
預設開啟；關閉可讓畫布更簡潔。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="138"/>
        <source>Hovering a mesh node shows its correlation subset window
(the Subset Size box). Needs Show Grid. Use it to judge
whether the subset spans enough speckle texture.</source>
        <translation>懸停在網格節點上時顯示其相關子集視窗（子集尺寸框）。
需先開啟「顯示網格」。可用來判斷子集是否涵蓋足夠的散斑紋理。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="151"/>
        <source>Switch the canvas to the reconstructed 3D surface (colored by
the selected field, with the camera frusta). Uncheck to return
to the 2D image view. Requires results.</source>
        <translation>將畫布切換為重建的 3D 曲面（依所選場變數著色，並顯示相機視錐）。
取消勾選可返回 2D 影像視圖。需要有結果。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="135"/>
        <source>Show Subset</source>
        <translation>顯示子集</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="148"/>
        <source>3D View</source>
        <translation>3D 檢視</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="339"/>
        <source>Save Mask</source>
        <translation>儲存掩模</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="339"/>
        <source>PNG image (*.png)</source>
        <translation>PNG 影像 (*.png)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="532"/>
        <source>Analysis produced no valid points — nothing to display. See the log.</source>
        <translation>分析未產生任何有效點——沒有可顯示的內容。請查看日誌。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="605"/>
        <source>3D view — run an analysis to see the reconstructed surface.</source>
        <translation>3D 檢視 — 執行分析後即可檢視重建曲面。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="611"/>
        <source>Selected field is not available.</source>
        <translation>所選場變量不可用。</translation>
    </message>
</context>
<context>
    <name>CanvasToolsMixin</name>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="105"/>
        <source>Fit</source>
        <translation>適配</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="107"/>
        <source>Zoom to 100%</source>
        <translation>縮放至 100%</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="110"/>
        <source>Copy image to clipboard</source>
        <translation>複製影像到剪貼簿</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="113"/>
        <source>Clear ROI</source>
        <translation>清除 ROI</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="116"/>
        <source>Clear seed point</source>
        <translation>清除種子點</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="141"/>
        <source>1. Drop the left/right camera folders in the sidebar
2. Calibrate or import calibration
3. Draw the ROI and Run</source>
        <translation>1. 將左/右相機資料夾拖入側邊欄
2. 標定或匯入標定
3. 繪製 ROI 並執行</translation>
    </message>
</context>
<context>
    <name>ConfigOverlay3D</name>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="39"/>
        <source>Mode</source>
        <translation>模式</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="40"/>
        <source>Solver</source>
        <translation>求解器</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="41"/>
        <source>Init</source>
        <translation>初始猜測</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="42"/>
        <source>Subset</source>
        <translation>子集</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="78"/>
        <source>ADMM ({0} iter)</source>
        <translation>ADMM（{0} 次迭代）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="80"/>
        <source>Local DIC</source>
        <translation>Local DIC</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="83"/>
        <source>Starting Point</source>
        <translation>種子點</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="84"/>
        <source>Previous frame</source>
        <translation>上一幀</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="85"/>
        <location filename="../../gui/widgets/config_overlay.py" line="87"/>
        <source>FFT</source>
        <translation>FFT</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="75"/>
        <source>Accumulative</source>
        <translation>累積式</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="75"/>
        <source>Incremental</source>
        <translation>增量式</translation>
    </message>
</context>
<context>
    <name>ConsoleLog3D</name>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="41"/>
        <source>Copy all</source>
        <translation>複製全部</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="44"/>
        <source>Save log to file…</source>
        <translation>將日誌儲存至檔案…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="46"/>
        <source>Clear</source>
        <translation>清除</translation>
    </message>
</context>
<context>
    <name>DataTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="43"/>
        <source>Format</source>
        <translation>格式</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="45"/>
        <source>NumPy archive (.npz)</source>
        <translation>NumPy 封存 (.npz)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="47"/>
        <source>MATLAB (.mat)</source>
        <translation>MATLAB (.mat)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="49"/>
        <source>CSV (one file per frame)</source>
        <translation>CSV（每幀一個檔案）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="50"/>
        <source>PLY point clouds (per frame)</source>
        <translation>PLY 點雲（逐幀）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="51"/>
        <source>VTU mesh series (ParaView)</source>
        <translation>VTU 網格序列（ParaView）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="54"/>
        <source>✓ Parameters file (JSON) always exported</source>
        <translation>✓ 參數檔案（JSON）始終會被匯出</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="61"/>
        <source>Displacement</source>
        <translation>位移</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="65"/>
        <source>Strain</source>
        <translation>應變</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="72"/>
        <source>3D points, reprojection error, and source flags are always exported.</source>
        <translation>3D 點、重投影誤差與來源旗標始終會被匯出。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="81"/>
        <source>Export Data</source>
        <translation>匯出資料</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="98"/>
        <source>Select:</source>
        <translation>選擇：</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="101"/>
        <source>All</source>
        <translation>全選</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="102"/>
        <source>None</source>
        <translation>全不選</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="139"/>
        <source>Choose an output folder first.</source>
        <translation>請先選擇輸出資料夾。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="160"/>
        <source>Wrote: {0}</source>
        <translation>已寫入：{0}</translation>
    </message>
</context>
<context>
    <name>DetectionZoomDialog</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="213"/>
        <source>Detection preview — pair {0}</source>
        <translation>偵測預覽 — 影像對 {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="222"/>
        <source>Wheel: zoom · Right/middle drag: pan</source>
        <translation>滾輪：縮放 · 右鍵/中鍵拖曳：平移</translation>
    </message>
</context>
<context>
    <name>ExportDialog</name>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="94"/>
        <source>Export Results</source>
        <translation>匯出結果</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="101"/>
        <source>OUTPUT FOLDER</source>
        <translation>輸出資料夾</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="104"/>
        <source>Select output folder…</source>
        <translation>選擇輸出資料夾…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="106"/>
        <source>Browse…</source>
        <translation>瀏覽…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="107"/>
        <source>Choose the folder all exports are written into</source>
        <translation>選擇所有匯出內容寫入的資料夾</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="110"/>
        <source>Open Folder</source>
        <translation>開啟資料夾</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="111"/>
        <source>Open the output folder in the file explorer</source>
        <translation>在檔案總管中開啟輸出資料夾</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="123"/>
        <source>Data</source>
        <translation>資料</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="124"/>
        <source>Images</source>
        <translation>影像</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="125"/>
        <source>Animation</source>
        <translation>動畫</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="126"/>
        <source>Preview &amp; Colorbar</source>
        <translation>預覽與色條</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="127"/>
        <source>3D View</source>
        <translation>3D 檢視</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="131"/>
        <source>Numeric results: field-selective NPZ / MAT / CSV tables plus PLY / VTU meshes for external tools.</source>
        <translation>數值結果：可按場變數選擇的 NPZ / MAT / CSV 表格，以及供外部工具使用的 PLY / VTU 網格。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="135"/>
        <source>Rendered per-camera field overlays as PNG images, one per frame, using the Preview &amp; Colorbar style.</source>
        <translation>按相機渲染的場疊加圖 PNG 影像（每幀一張），使用「預覽與色條」樣式。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="139"/>
        <source>GIF / MP4 animations of the field overlay across frames, using the Preview &amp; Colorbar style.</source>
        <translation>場疊加圖跨幀的 GIF / MP4 動畫，使用「預覽與色條」樣式。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="143"/>
        <source>WYSIWYG style source: the colorbar and margins configured here are used by every Images / Animation export.</source>
        <translation>所見即所得的樣式來源：此處設定的色條與邊距將用於所有影像/動畫匯出。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="147"/>
        <source>Offscreen renders of the 3D surface view (camera frusta included) as images or turntable animations.</source>
        <translation>3D 曲面視圖的離屏渲染（含相機視錐），可匯出為影像或環繞動畫。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="301"/>
        <source>Export Running</source>
        <translation>匯出進行中</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="302"/>
        <source>An export is still running — cancel it and close?</source>
        <translation>仍有匯出工作正在執行 — 取消並關閉？</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="305"/>
        <source>Yes</source>
        <translation>是</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="306"/>
        <source>No</source>
        <translation>否</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="338"/>
        <source>Folder does not exist: {0}</source>
        <translation>資料夾不存在：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="159"/>
        <source>Close</source>
        <translation>關閉</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="325"/>
        <source>Choose output folder</source>
        <translation>選擇輸出資料夾</translation>
    </message>
</context>
<context>
    <name>ExportTabBase</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="150"/>
        <source>Cancelling…</source>
        <translation>正在取消…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="159"/>
        <source>Export cancelled — {0} file(s) kept</source>
        <translation>匯出已取消 — 已保留 {0} 個檔案</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="167"/>
        <source>Error: {0}</source>
        <translation>錯誤：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="171"/>
        <source>Wrote {0} file(s)</source>
        <translation>已寫入 {0} 個檔案</translation>
    </message>
</context>
<context>
    <name>ExportTabs</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="403"/>
        <source>Full resolution</source>
        <translation>原始解析度</translation>
    </message>
</context>
<context>
    <name>FieldRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="237"/>
        <source>Auto</source>
        <translation>自動</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="238"/>
        <source>Auto range</source>
        <translation>自動範圍</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="254"/>
        <source>Opacity</source>
        <translation>不透明度</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="255"/>
        <source>Field opacity (0 = transparent, 1 = fully opaque)</source>
        <translation>場變數不透明度（0 = 透明，1 = 完全不透明）</translation>
    </message>
</context>
<context>
    <name>FieldSelector3D</name>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="47"/>
        <source>DISPLACEMENT</source>
        <translation>位移</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="69"/>
        <source>U — world-frame displacement along X (left camera&apos;s +X, image right), in mm</source>
        <translation>U — 世界座標系沿 X 的位移（左相機 +X，影像向右），單位 mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="72"/>
        <source>V — world-frame displacement along Y (left camera&apos;s +Y, image down), in mm</source>
        <translation>V — 世界座標系沿 Y 的位移（左相機 +Y，影像向下），單位 mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="75"/>
        <source>W — world-frame displacement along Z (left camera&apos;s optical axis, toward the scene): out-of-plane motion, in mm</source>
        <translation>W — 世界座標系沿 Z 的位移（左相機光軸，指向場景）：離面運動，單位 mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="78"/>
        <source>|D| — displacement magnitude √(U²+V²+W²), in mm</source>
        <translation>|D| — 位移幅值 √(U²+V²+W²)，單位 mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="80"/>
        <location filename="../../gui/widgets/field_selector.py" line="107"/>
        <source>Velocity — per-node speed |D(k) − D(k−1)| × frame rate, in the display unit per second. Depends on the frame rate set in the UNITS section; frame 1 has no predecessor (empty).</source>
        <translation>速度 — 每節點速率 |D(k) − D(k−1)| × 幀率，以每秒顯示單位表示。取決於 UNITS 區域中設定的幀率；第 1 幀沒有前一幀（顯示為空）。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="103"/>
        <source>Run an analysis first — velocity needs results.</source>
        <translation>請先執行分析 — 速度場需要結果。</translation>
    </message>
</context>
<context>
    <name>FrameNavigator3D</name>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="39"/>
        <source>Previous frame (←)</source>
        <translation>上一幀 (←)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="46"/>
        <location filename="../../gui/widgets/frame_navigator.py" line="124"/>
        <source>Play animation (Space)</source>
        <translation>播放動畫 (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="53"/>
        <source>Next frame (→)</source>
        <translation>下一幀 (→)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="62"/>
        <source>Playback speed (frames per second). Default 2 fps.</source>
        <translation>播放速度（幀/秒）。預設 2 fps。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="117"/>
        <source>Pause animation (Space)</source>
        <translation>暫停動畫 (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="139"/>
        <source>FRAME {0}/{1}</source>
        <translation>幀 {0}/{1}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="141"/>
        <source>FRAME 0/0</source>
        <translation>幀 0/0</translation>
    </message>
</context>
<context>
    <name>FrameRangeRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="434"/>
        <source>All frames</source>
        <translation>所有影格</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="438"/>
        <source>From frame</source>
        <translation>起始影格</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="448"/>
        <source>to</source>
        <translation>至</translation>
    </message>
</context>
<context>
    <name>ImagesTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="54"/>
        <source>Fields</source>
        <translation>場變數</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="71"/>
        <source>Format</source>
        <translation>格式</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="80"/>
        <source>JPEG quality</source>
        <translation>JPEG 品質</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="87"/>
        <source>Resolution (long edge)</source>
        <translation>解析度（長邊）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="96"/>
        <source>Include colorbar</source>
        <translation>包含色條</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="101"/>
        <source>Background</source>
        <translation>背景</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="115"/>
        <source>Export Images</source>
        <translation>匯出影像</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="126"/>
        <source>Load an image sequence first (open the project in the main window).</source>
        <translation>請先載入影像序列（在主視窗中開啟專案）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="152"/>
        <source>Choose an output folder first.</source>
        <translation>請先選擇輸出資料夾。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="156"/>
        <source>No fields enabled.</source>
        <translation>未啟用任何場變數。</translation>
    </message>
</context>
<context>
    <name>InitGuessSection3D</name>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="59"/>
        <source>Starting Point</source>
        <translation>種子點</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="62"/>
        <source>Click ONE point on the LEFT camera, frame 1. Its neighborhood
is matched automatically into the right camera (stereo offset)
and into frame 2 (motion seed) — no search tuning needed.
Best for wide stereo baselines or large first-frame motion.
If no point is placed, the run falls back to FFT.</source>
        <translation>在左相機第 1 幀上點擊一個點。軟體會自動將其鄰域
匹配到右相機（立體偏移）以及第 2 幀（運動種子）——
無需調整搜尋參數。適合寬基線立體或首幀大位移場景。
若未放置種子點，執行時將回退為 FFT。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="77"/>
        <location filename="../../gui/widgets/init_guess_section.py" line="161"/>
        <source>Place point…</source>
        <translation>放置種子點…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="81"/>
        <source>Enter placement mode on the canvas. Click once on the LEFT
camera, frame 1 — a new click replaces the point; Esc cancels.</source>
        <translation>進入畫布放置模式。在左相機第 1 幀上點擊一次——
新的點擊會取代舊點；按 Esc 取消。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="86"/>
        <source>Clear</source>
        <translation>清除</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="87"/>
        <source>Remove the Starting Point</source>
        <translation>移除種子點</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="96"/>
        <source>FFT (cross-correlation)</source>
        <translation>FFT（互相關）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="99"/>
        <source>Full-grid cross-correlation seeds frame 1 (and every reference
switch in incremental mode); later frames warm-start from the
previous solution. Robust default — the search radius is the
Temporal Search parameter.</source>
        <translation>全網格互相關為第 1 幀（增量模式下每次參考幀切換時也會）
提供初值；後續幀從上一幀的解熱啟動。穩健的預設選項——
搜尋半徑由「時序搜尋」參數決定。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="108"/>
        <source>Previous frame</source>
        <translation>上一幀</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="111"/>
        <source>Start every frame from the previous frame&apos;s solution — no
cross-correlation at all. Fastest; can silently freeze on large
motion or decorrelation — the validity gate will flag affected
frames.</source>
        <translation>每一幀都從上一幀的解開始——完全不做互相關。
速度最快；在大位移或散斑退相關時可能靜默凍結——
有效性門檻會標記受影響的幀。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="161"/>
        <source>Placing… (click to exit)</source>
        <translation>放置中…（再次點擊離開）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="167"/>
        <source>No point placed — FFT fallback at run</source>
        <translation>未放置種子點——執行時回退為 FFT</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="170"/>
        <source>Point: ({0}, {1}) px</source>
        <translation>點：({0}, {1}) px</translation>
    </message>
</context>
<context>
    <name>Issues</name>
    <message>
        <location filename="../../gui/issue_text.py" line="25"/>
        <source>calibration file not set</source>
        <translation>未設定標定檔</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="28"/>
        <source>left/right sequences not set</source>
        <translation>未設定左/右影像序列</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="31"/>
        <source>need at least 2 frames</source>
        <translation>至少需要 2 幀</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="32"/>
        <source>ROI not set</source>
        <translation>未設定 ROI</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="33"/>
        <source>ROI is empty (xmin&lt;xmax, ymin&lt;ymax required)</source>
        <translation>ROI 為空（需 xmin&lt;xmax 且 ymin&lt;ymax）</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="49"/>
        <source>sequence length mismatch: {0} vs {1}</source>
        <translation>序列長度不符：左 {0} 幀，右 {1} 幀</translation>
    </message>
</context>
<context>
    <name>LeftSidebar3D</name>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="80"/>
        <source>IMAGES</source>
        <translation>影像</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="87"/>
        <source>Drop LEFT camera
folder or click</source>
        <translation>拖入左相機資料夾
或點擊選擇</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="88"/>
        <source>Drop RIGHT camera
folder or click</source>
        <translation>拖入右相機資料夾
或點擊選擇</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="93"/>
        <source>Natural Sort (1, 2, …, 10)</source>
        <translation>自然排序 (1, 2, …, 10)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="96"/>
        <source>Sort file names numerically (img2 before img10). Default on; turn off for strict alphabetical order. Applies to the next folder load.</source>
        <translation>按數字大小排序檔名（img2 在 img10 之前）。預設開啟；關閉則使用嚴格字母序。對下一次載入的資料夾生效。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="114"/>
        <location filename="../../gui/panels/left_sidebar.py" line="717"/>
        <source>No images loaded</source>
        <translation>尚未載入影像</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="140"/>
        <source>CALIBRATION</source>
        <translation>標定</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="144"/>
        <source>WORKFLOW TYPE</source>
        <translation>工作流類型</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="151"/>
        <source>INITIAL GUESS</source>
        <translation>初始猜測</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="155"/>
        <source>REGION OF INTEREST</source>
        <translation>感興趣區域</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="159"/>
        <source>PARAMETERS</source>
        <translation>參數</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="163"/>
        <source>ADVANCED</source>
        <translation>高級</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="294"/>
        <source>Incremental: each frame is compared to the previous reference frame.
Suitable for large accumulated deformation, required for large rotations.

Accumulative: every frame is compared to frame 1.
Accurate for small, monotonic deformation only.</source>
        <translation>增量式：每幀與前一個參考幀比較。
適用於大量累積變形，大旋轉場景必須使用。

累積式：每幀都與第 1 幀比較。
僅適用於小的、單調的變形。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="312"/>
        <source>Local DIC</source>
        <translation>Local DIC</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="314"/>
        <source>Local DIC: Independent subset matching (IC-GN). Fast,
preserves sharp local features. Best for small
deformations or high-quality images.

AL-DIC: Augmented Lagrangian with global FEM
regularization. Enforces displacement compatibility
between subsets. Best for large deformations, noisy
images, or when strain accuracy matters.</source>
        <translation>Local DIC：獨立子集匹配（IC-GN）。速度快，
保留局部銳利特徵。適合小變形
或高質量影像。

AL-DIC：全局 FEM 正則化的增廣拉格朗日方法。
強制子集間的位移相容性。適合大變形、
噪聲影像，或對應變精度要求高的場景。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="324"/>
        <source>Solver</source>
        <translation>求解器</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="332"/>
        <source>Post-run filters: demote points whose ZNSSD correlation,
reprojection error or 3D-outlier distance fails the gate to
NaN. Default off (keep every tracked point); enable for noisy
data when a few bad points pollute the fields. The log
reports how many points each gate removed.</source>
        <translation>執行後的過濾器：將 ZNSSD 相關性、重投影誤差或 3D 外點距離未通過門控的點設為 NaN。
預設關閉（保留所有跟蹤點）；資料雜訊較大、個別壞點污染場時可啟用。
日誌會報告每個門控剔除的點數。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="397"/>
        <location filename="../../gui/panels/left_sidebar.py" line="415"/>
        <source>bbox: not set</source>
        <translation>包圍盒：未設定</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="418"/>
        <source>bbox: {0}–{1}, {2}–{3} px</source>
        <translation>包圍盒：{0}–{1}，{2}–{3} 像素</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="438"/>
        <source>IC-GN subset window size in pixels (odd number). Default 33.
Larger = more robust on sparse speckle, smoother fields;
smaller = finer spatial detail but noisier. The subset must
span several speckles.</source>
        <translation>IC-GN 子集視窗尺寸（像素，奇數）。預設 33。
更大 = 對稀疏散斑更穩健、場更平滑；更小 = 空間細節更精細但雜訊更大。
子集必須涵蓋若干散斑。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="289"/>
        <source>Accumulative</source>
        <translation>累積式</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="232"/>
        <source>Remove Image Pairs</source>
        <translation>移除影像對</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="235"/>
        <source>Removing {0} pair(s) changes the sequence — the current results will be discarded. Continue?</source>
        <translation>移除 {0} 個影像對將改變序列 — 目前結果將被捨棄。是否繼續？</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="241"/>
        <source>Yes</source>
        <translation>是</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="242"/>
        <source>No</source>
        <translation>否</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="290"/>
        <source>Incremental</source>
        <translation>增量式</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="301"/>
        <source>Tracking Mode</source>
        <translation>追蹤模式</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="329"/>
        <source>Quality gates (ZNSSD / outliers)</source>
        <translation>品質門檻（ZNSSD / 離群點）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="379"/>
        <source>Draw on the LEFT camera, frame 1 — all later frames and the right camera follow from it.</source>
        <translation>在左相機第 1 幀上繪製——所有後續幀與右相機都由它推算。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="444"/>
        <source>Subset Size</source>
        <translation>子集尺寸</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="452"/>
        <source>Node spacing in pixels (power of 2). Default 16. Smaller =
denser measurement grid and longer runs; larger = faster but
coarser fields. Typically ¼–½ of the Subset Size.</source>
        <translation>節點間距（像素，2 的冪）。預設 16。更小 = 測量網格更密、執行更久；
更大 = 更快但場更粗糙。通常取子集尺寸的 1/4 到 1/2。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="457"/>
        <source>Subset Step</source>
        <translation>子集步長</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="463"/>
        <source>Stereo Search</source>
        <translation>立體搜尋</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="476"/>
        <source>Temporal Search</source>
        <translation>時序搜尋</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="482"/>
        <source>Mesh refinement</source>
        <translation>網格加密</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="489"/>
        <source>Refine at mask boundaries (holes)</source>
        <translation>在遮罩邊界（孔洞）處加密</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="492"/>
        <source>Quadtree-subdivide mesh elements crossing interior mask
holes so the mesh hugs the hole edges. Default off (uniform
grid); enable when the ROI mask has cut-outs whose rims you
care about.</source>
        <translation>對穿過掩膜內部孔洞的網格單元做四叉樹細分，使網格貼合孔洞邊緣。
預設關閉（均勻網格）；當 ROI 掩膜有需要關注邊緣的挖空時可啟用。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="499"/>
        <source>Refine at ROI edges</source>
        <translation>在 ROI 邊緣處加密</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="502"/>
        <source>Quadtree-subdivide mesh elements along the outer ROI
boundary. Default off; enable for curved / irregular ROI
outlines where the uniform grid staircases.</source>
        <translation>沿 ROI 外邊界對網格單元做四叉樹細分。
預設關閉；ROI 輪廓彎曲/不規則、均勻網格出現鋸齒時可啟用。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="514"/>
        <source>How aggressively refined elements shrink: the minimum element
is step / 2^level. Default 1 (light); 3 is heavy — finer
boundary detail but many more nodes and a slower run.</source>
        <translation>控制加密單元縮小的程度：最小單元為 step / 2^level。
預設 1（輕度）；3 為重度 — 邊界細節更精細，但節點大幅增加、執行更慢。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="519"/>
        <source>Refinement Level</source>
        <translation>加密級別</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="622"/>
        <source>NCC search half-width (pixels) around each node for the
left-to-right stereo match. Set larger than the largest
expected stereo disparity.</source>
        <translation>左→右立體匹配時圍繞每個節點的 NCC 搜尋半寬（像素）。
應大於預期的最大立體視差。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="627"/>
        <source>Half-width (pixels) of the temporal FFT integer search that seeds
each per-frame match. Set comfortably larger than the expected
inter-frame motion; with Auto-expand on (default) the engine can
still grow the search past this on a boundary-clipped peak.</source>
        <translation>時序 FFT 整數搜尋的半寬（像素），用於為每一幀的匹配提供初始值。
請設定為明顯大於預期的幀間運動；當「自動擴大」開啟（預設）時，
峰值觸及搜尋邊界時引擎仍可將搜尋範圍擴大到超過此值。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="643"/>
        <source>Current images: the engine starts the FFT search clamped to
{0} px (max(10, min(H, W) / 4 - subset)); Auto-expand can grow
it to {1} px (max(32, min(H, W) / 2)) on clipped peaks.</source>
        <translation>目前影像：引擎在執行開始時會將 FFT 搜尋限制為 {0} px
（max(10, min(H, W) / 4 - 子區)）；當峰值被截斷時，「自動擴大」
可將其增大到 {1} px（max(32, min(H, W) / 2)）。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="665"/>
        <source>Inactive with the current Initial Guess / Tracking Mode: the
temporal FFT runs only when Initial Guess = FFT, or at reference
switches in Incremental mode; in Accumulative + Starting Point /
Previous frame no FFT runs, so this control has no effect.</source>
        <translation>在目前的初始猜測 / 追蹤模式下無效：僅當初始猜測 = FFT，
或在增量式模式的參考幀切換處，才會執行時序 FFT。在累積式 +
種子點 / 上一幀下不會執行 FFT，因此此控制項不起作用。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="639"/>
        <source>Current images: values above {0} px cannot widen the search
(the window is clamped at the image borders).</source>
        <translation>目前影像：超過 {0} px 的取值無法再擴大搜尋
（搜尋視窗在影像邊界處被裁剪）。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="722"/>
        <source>Paired: {0} frames per camera</source>
        <translation>已配對：每相機 {0} 幀</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="728"/>
        <source>Mismatch: {0} left vs {1} right</source>
        <translation>數量不符：左 {0} 幀，右 {1} 幀</translation>
    </message>
</context>
<context>
    <name>MainWindow3D</name>
    <message>
        <location filename="../../gui/main_window.py" line="193"/>
        <source>Strain window available — open it from the sidebar</source>
        <translation>應變視窗已就緒 — 可從側邊欄開啟</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="241"/>
        <source>Analysis Running</source>
        <translation>分析執行中</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="242"/>
        <source>An analysis is running — cancel it and quit?</source>
        <translation>有分析正在執行——取消並結束？</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="247"/>
        <location filename="../../gui/main_window.py" line="690"/>
        <source>Yes</source>
        <translation>是</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="248"/>
        <location filename="../../gui/main_window.py" line="691"/>
        <source>No</source>
        <translation>否</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="266"/>
        <source>Unsaved Changes</source>
        <translation>未儲存的變更</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="267"/>
        <source>The project has unsaved changes. Save them before continuing?</source>
        <translation>專案有未儲存的變更。是否在繼續前儲存？</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="274"/>
        <source>Save</source>
        <translation>儲存</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="275"/>
        <source>Discard</source>
        <translation>捨棄</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="276"/>
        <location filename="../../gui/main_window.py" line="692"/>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="297"/>
        <source>Switched to left camera, frame 1 for ROI editing</source>
        <translation>已切換到左相機第 1 幀以編輯 ROI</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="335"/>
        <source>&amp;File</source>
        <translation>檔案(&amp;F)</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="337"/>
        <source>New Project</source>
        <translation>新建專案</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="342"/>
        <source>Open Project…</source>
        <translation>開啟專案…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="348"/>
        <source>Recent Projects</source>
        <translation>最近的專案</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="359"/>
        <source>Save Project As…</source>
        <translation>另存專案為…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="369"/>
        <source>Associate .aldic3d files with pyALDIC-3D…</source>
        <translation>將 .aldic3d 檔案關聯到 pyALDIC-3D…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="372"/>
        <source>Register .aldic3d so double-clicking a project file opens pyALDIC-3D (current user only, no admin rights needed).</source>
        <translation>註冊 .aldic3d 關聯後，雙擊專案檔案即可在 pyALDIC-3D 中開啟（僅目前使用者，無需管理員權限）。</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="416"/>
        <source>&amp;Help</source>
        <translation>說明(&amp;H)</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="417"/>
        <source>Keyboard Shortcuts</source>
        <translation>鍵盤快速鍵</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="420"/>
        <source>About pyALDIC-3D</source>
        <translation>關於 pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="433"/>
        <location filename="../../gui/main_window.py" line="439"/>
        <source>File Association</source>
        <translation>檔案關聯</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="434"/>
        <source>Could not register the .aldic3d association: {0}</source>
        <translation>無法註冊 .aldic3d 關聯：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="441"/>
        <source>Done — double-clicking a .aldic3d file now opens it in pyALDIC-3D (registered for the current user).</source>
        <translation>完成 — 現在雙擊 .aldic3d 檔案即可在 pyALDIC-3D 中開啟（已為目前使用者註冊）。</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="472"/>
        <source>No recent projects</source>
        <translation>尚無最近專案</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="476"/>
        <source>Clear list</source>
        <translation>清空清單</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="569"/>
        <source>Loading project…</source>
        <translation>正在載入專案…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="614"/>
        <location filename="../../gui/main_window.py" line="624"/>
        <source>Locate Images</source>
        <translation>定位影像</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="616"/>
        <source>The selected folder does not contain this project&apos;s camera {0} frames. Pick the folder holding the original image files, or cancel to abort opening.</source>
        <translation>所選資料夾中不包含本專案相機 {0} 的影像幀。請選擇存放原始影像檔案的資料夾，或取消以中止開啟。</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="626"/>
        <source>The image folder saved with this project was not found:
{0}

Select the folder that now contains the camera {1} frames (file names must match).</source>
        <translation>隨專案儲存的影像資料夾未找到：
{0}

請選擇目前存放相機 {1} 影像幀的資料夾（檔案名稱必須一致）。</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="633"/>
        <source>Locate images for camera {0}</source>
        <translation>定位相機 {0} 的影像</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="675"/>
        <source>Include Results?</source>
        <translation>包含結果？</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="676"/>
        <source>Include the analysis results in this project file?</source>
        <translation>在此專案檔案中包含分析結果嗎？</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="679"/>
        <source>Including results (about {0} uncompressed) lets you reopen the project without recomputing. Choose No to save a small configuration-only file for sharing.</source>
        <translation>包含結果（未壓縮約 {0}）可在重新開啟專案時無需重新計算。選擇「否」則儲存一個便於分享的小型純設定檔。</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="717"/>
        <source>unknown size</source>
        <translation>未知大小</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="727"/>
        <source>Saving project…</source>
        <translation>正在儲存專案…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="380"/>
        <source>Quit</source>
        <translation>離開</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="386"/>
        <source>&amp;Settings</source>
        <translation>設定(&amp;S)</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="387"/>
        <source>Language</source>
        <translation>語言</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="501"/>
        <source>Untitled</source>
        <translation>未命名</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="502"/>
        <source>{0}[*] — pyALDIC-3D</source>
        <translation>{0}[*] — pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="554"/>
        <source>Open Project</source>
        <translation>開啟專案</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="556"/>
        <location filename="../../gui/main_window.py" line="661"/>
        <source>pyALDIC-3D project (*.aldic3d)</source>
        <translation>pyALDIC-3D 專案 (*.aldic3d)</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="354"/>
        <location filename="../../gui/main_window.py" line="659"/>
        <source>Save Project</source>
        <translation>儲存專案</translation>
    </message>
</context>
<context>
    <name>ManualParamsDialog</name>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="53"/>
        <source>Manual Camera Parameters</source>
        <translation>手動輸入相機參數</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="61"/>
        <source>Left camera (world frame)</source>
        <translation>左相機（世界座標系）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="62"/>
        <source>Right camera</source>
        <translation>右相機</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="67"/>
        <source>Stereo extrinsics  (X_R = R · X_L + T)</source>
        <translation>立體外參（X_R = R · X_L + T）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="71"/>
        <source>{0} (deg)</source>
        <translation>{0}（度）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="78"/>
        <source>{0} (mm)</source>
        <translation>{0}（mm）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="87"/>
        <source>Euler composition R = Rz·Ry·Rx in degrees (MatchID/OpenCorr convention); distortion order k1, k2, p1, p2, k3 (OpenCV).</source>
        <translation>尤拉角組合 R = Rz·Ry·Rx（度，MatchID/OpenCorr 約定）；畸變係數順序 k1, k2, p1, p2, k3（OpenCV）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="101"/>
        <source>Save as YAML…</source>
        <translation>另存為 YAML…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="106"/>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="142"/>
        <source>Baseline |T| = {0:.2f} mm</source>
        <translation>基線 |T| = {0:.2f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="147"/>
        <source>Baseline is zero — enter the translation T first.</source>
        <translation>基線為零——請先輸入平移向量 T。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="152"/>
        <source>Save calibration as</source>
        <translation>校正另存為</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="154"/>
        <source>OpenCV YAML (*.yml *.yaml *.xml)</source>
        <translation>OpenCV YAML (*.yml *.yaml *.xml)</translation>
    </message>
</context>
<context>
    <name>MeshAppearanceControls</name>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="33"/>
        <source>Mesh overlay line color — click to choose</source>
        <translation>網格疊加線顏色 — 點擊選擇</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="42"/>
        <source>Mesh overlay line width (screen pixels)</source>
        <translation>網格疊加線寬（螢幕像素）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="68"/>
        <source>Choose mesh line color</source>
        <translation>選擇網格線顏色</translation>
    </message>
</context>
<context>
    <name>NextStepHint</name>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="48"/>
        <source>Load the left and right camera folders</source>
        <translation>載入左右相機資料夾</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="53"/>
        <source>Calibrate from images or import a calibration</source>
        <translation>從影像標定或匯入標定</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="54"/>
        <source>Draw the ROI on the left camera, frame 1</source>
        <translation>在左相機第 1 幀上繪製 ROI</translation>
    </message>
</context>
<context>
    <name>PairBars</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="125"/>
        <source>no solve yet</source>
        <translation>尚未求解</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="147"/>
        <source>worst-camera RMS per pair; dashed = reject threshold</source>
        <translation>每對影像的最差相機 RMS；虛線 = 剔除閾值</translation>
    </message>
</context>
<context>
    <name>PairListWidget</name>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="25"/>
        <source>Left</source>
        <translation>左</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="25"/>
        <source>Right</source>
        <translation>右</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="70"/>
        <source>Remove {0} selected pair(s)</source>
        <translation>移除選取的 {0} 個影像對</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="73"/>
        <source>Reveal in Explorer</source>
        <translation>在檔案總管中顯示</translation>
    </message>
</context>
<context>
    <name>PreviewTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="61"/>
        <source>Open this tab to render a preview.</source>
        <translation>開啟此分頁以算繪預覽。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="69"/>
        <source>Field</source>
        <translation>場變數</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="76"/>
        <source>Frame</source>
        <translation>影格</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="85"/>
        <source>Camera</source>
        <translation>相機</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="89"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="168"/>
        <source>Left</source>
        <translation>左</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="90"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="167"/>
        <source>Right</source>
        <translation>右</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="120"/>
        <source>FIELD APPEARANCE</source>
        <translation>欄位外觀</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="125"/>
        <source>Colormap</source>
        <translation>色彩對映</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="127"/>
        <source>Auto</source>
        <translation>自動</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="128"/>
        <source>Auto range</source>
        <translation>自動範圍</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="131"/>
        <source>Range</source>
        <translation>範圍</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="139"/>
        <source>Min</source>
        <translation>最小</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="140"/>
        <source>Max</source>
        <translation>最大</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="147"/>
        <source>Opacity</source>
        <translation>不透明度</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="149"/>
        <source>Apply to all fields</source>
        <translation>套用到所有欄位</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="152"/>
        <source>Apply this field&apos;s colormap, opacity and auto-range to every enabled field (each field keeps its own min/max).</source>
        <translation>將該欄位的 colormap、不透明度和自動範圍套用到所有已啟用欄位（每個欄位保留各自的 min/max）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="162"/>
        <source>COLORBAR STYLE</source>
        <translation>色條樣式</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="169"/>
        <source>Top</source>
        <translation>上</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="170"/>
        <source>Bottom</source>
        <translation>下</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="174"/>
        <source>Position</source>
        <translation>位置</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="180"/>
        <source>Font size</source>
        <translation>字級</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="186"/>
        <source>Font family</source>
        <translation>字型</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="194"/>
        <source>Bar thickness</source>
        <translation>色條粗細</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="197"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="216"/>
        <source>Black</source>
        <translation>黑色</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="197"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="216"/>
        <source>White</source>
        <translation>白色</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="200"/>
        <source>Background</source>
        <translation>背景</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="208"/>
        <source>Add a blank border around the exported content, as a fraction of the long edge (0 = none).</source>
        <translation>在匯出內容外圍加一圈空白邊框，寬度為長邊的比例（0 = 無）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="213"/>
        <source>Margin</source>
        <translation>邊距</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="219"/>
        <source>Margin color</source>
        <translation>邊距顏色</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="221"/>
        <source>Refresh preview</source>
        <translation>重新整理預覽</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="363"/>
        <source>Preview failed: </source>
        <translation>預覽失敗：</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="374"/>
        <source>Enable a field on the Images tab to preview.</source>
        <translation>在 Images 頁啟用一個欄位以進行預覽。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="404"/>
        <source>No data for this field/frame.</source>
        <translation>該欄位/影格沒有資料。</translation>
    </message>
</context>
<context>
    <name>ProgressRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="81"/>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="98"/>
        <source>Exporting…</source>
        <translation>正在匯出…</translation>
    </message>
</context>
<context>
    <name>ROIToolbar</name>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="72"/>
        <source>+ Add</source>
        <translation>+ 添加</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="74"/>
        <source>Add region to the Region of Interest (Polygon / Rectangle / Circle)</source>
        <translation>向感興趣區域添加形狀（多邊形 / 矩形 / 圓形）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="78"/>
        <source>Cut</source>
        <translation>裁剪</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="80"/>
        <source>Cut region from the Region of Interest (Polygon / Rectangle / Circle)</source>
        <translation>從感興趣區域裁剪形狀（多邊形 / 矩形 / 圓形）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="84"/>
        <source>+ Refine</source>
        <translation>+ 加密</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="87"/>
        <source>Paint extra mesh-refinement zones with a brush
(on the LEFT camera, frame 1 — the reference mesh geometry)</source>
        <translation>用畫筆繪製額外的網格加密區域
（在左相機第 1 幀上 — 參考網格幾何）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="109"/>
        <source>Import</source>
        <translation>匯入</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="110"/>
        <source>Import mask from image file</source>
        <translation>從影像檔案匯入掩模</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="119"/>
        <source>Save</source>
        <translation>儲存</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="120"/>
        <source>Save current mask to PNG file</source>
        <translation>將當前掩模儲存為 PNG 檔案</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="125"/>
        <source>Invert</source>
        <translation>反選</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="126"/>
        <source>Invert the Region of Interest mask</source>
        <translation>反轉感興趣區域掩模</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="131"/>
        <source>Clear</source>
        <translation>清除</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="132"/>
        <source>Clear all Region of Interest masks</source>
        <translation>清除所有感興趣區域掩模</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="158"/>
        <source>Polygon</source>
        <translation>多邊形</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="162"/>
        <source>Rectangle</source>
        <translation>矩形</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="166"/>
        <source>Circle</source>
        <translation>圓形</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="170"/>
        <source>Circle (3-point)</source>
        <translation>圓（三點）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="184"/>
        <source>Radius</source>
        <translation>半徑</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="201"/>
        <source>Paint</source>
        <translation>繪製</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="205"/>
        <source>Erase</source>
        <translation>擦除</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="214"/>
        <source>Clear Brush</source>
        <translation>清除畫筆</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="252"/>
        <source>Import Mask Image</source>
        <translation>匯入掩模影像</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="254"/>
        <source>Images (*.png *.bmp *.tif *.tiff *.jpg *.jpeg);;All Files (*)</source>
        <translation>影像 (*.png *.bmp *.tif *.tiff *.jpg *.jpeg);;所有檔案 (*)</translation>
    </message>
</context>
<context>
    <name>RefUpdateSection3D</name>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="55"/>
        <source>Reference Update</source>
        <translation>參考幀更新</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="60"/>
        <source>Every Frame</source>
        <translation>每幀</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="61"/>
        <source>Every N Frames</source>
        <translation>每 N 幀</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="62"/>
        <source>Custom Frames</source>
        <translation>自定義幀</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="65"/>
        <source>How often the incremental reference frame advances.
Every Frame (default): frame k matches against k−1 — tracks
large accumulated deformation, but drift can accumulate.
Every N Frames: the reference advances only every N frames —
less drift, needs correlation to survive N frames of motion.
Custom Frames: reference updates exactly at the listed frames.</source>
        <translation>增量模式下參考幀推進的頻率。
每幀（預設）：第 k 幀與第 k−1 幀匹配 — 可追蹤大量累積變形，
但漂移會累積。
每 N 幀：參考幀每 N 幀才推進一次 — 漂移更小，但相關性需要
經受 N 幀的運動。
自定義幀：參考幀僅在列出的幀處更新。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="78"/>
        <source>Update every</source>
        <translation>更新間隔</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="85"/>
        <source> frames</source>
        <translation> 幀</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="87"/>
        <source>Reference-update interval N: frames k use the last reference at i·N &lt; k</source>
        <translation>參考幀更新間隔 N：第 k 幀使用 i·N &lt; k 的最近參考幀</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="93"/>
        <source>e.g. 5, 10, 20 (0-based frame indices)</source>
        <translation>例如 5, 10, 20（從 0 開始的幀索引）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="96"/>
        <source>Comma-separated 0-based frame indices that become reference
frames (frame 0 always is one). The last frame cannot be a
reference.</source>
        <translation>以逗號分隔的從 0 開始的幀索引，這些幀將成為參考幀
（第 0 幀始終是參考幀）。最後一幀不能作為參考幀。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="141"/>
        <source>Enter comma-separated 0-based frame numbers, e.g. 5, 10, 20</source>
        <translation>請輸入以逗號分隔、從 0 開始的幀編號，例如 5, 10, 20</translation>
    </message>
</context>
<context>
    <name>RightSidebar3D</name>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="82"/>
        <source>Run 3D Analysis</source>
        <translation>執行 3D 分析</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="88"/>
        <location filename="../../gui/panels/right_sidebar.py" line="428"/>
        <source>Run the full stereo correspondence + triangulation pipeline on the loaded image pairs (F5).</source>
        <translation>對已載入的影像對執行完整的立體對應 + 三角化流程（F5）。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="95"/>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="110"/>
        <source>Export Results</source>
        <translation>匯出結果</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="118"/>
        <source>Open Strain Window</source>
        <translation>開啟應變窗口</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="131"/>
        <source>Parameters changed since this result — re-run to update</source>
        <translation>參數在此結果之後已變更 — 重新執行以更新</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="139"/>
        <source>PROGRESS</source>
        <translation>進度</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="146"/>
        <location filename="../../gui/panels/right_sidebar.py" line="660"/>
        <source>Ready</source>
        <translation>就緒</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="151"/>
        <source>ELAPSED  --:--</source>
        <translation>已用  --:--</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="154"/>
        <source>REMAINING  --:--</source>
        <translation>剩餘  --:--</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="160"/>
        <source>FIELD</source>
        <translation>場變量</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="166"/>
        <source>Show on deformed frame</source>
        <translation>在變形幀上顯示</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="170"/>
        <source>When checked, overlay results on the deformed (current) frame instead of the reference frame</source>
        <translation>勾選後，將結果疊加在變形（當前）幀上，而非參考幀</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="179"/>
        <source>Camera</source>
        <translation>相機</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="183"/>
        <source>Left</source>
        <translation>左</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="186"/>
        <source>Show the LEFT camera&apos;s images (the reference view: ROI, seed and mesh live here). Default.</source>
        <translation>顯示左相機的影像（參考視圖：ROI、起始點與網格都定義在這裡）。預設。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="190"/>
        <source>Right</source>
        <translation>右</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="193"/>
        <source>Show the RIGHT camera&apos;s images with the field warped onto them — a cross-check that the stereo match is sound.</source>
        <translation>顯示右相機的影像，並將場變數映射到其上 — 用於檢查立體匹配是否可靠。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="209"/>
        <source>VISUALIZATION</source>
        <translation>可視化</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="212"/>
        <source>Colormap</source>
        <translation>色彩對映</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="220"/>
        <source>Colormap for the field overlay and the 3D surface. Default turbo (perceptually ordered, high contrast); pick RdBu_r or coolwarm for signed fields centered on zero.</source>
        <translation>場疊加圖與 3D 曲面使用的顏色映射。預設 turbo（感知有序、高對比）；對以零為中心的有符號場可選 RdBu_r 或 coolwarm。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="229"/>
        <source>Auto range</source>
        <translation>自動範圍</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="233"/>
        <source>Rescale the color range to each frame&apos;s data range (2–98 percentile of the visible values). Default on; uncheck to type fixed Min/Max bounds that hold across frames.</source>
        <translation>根據每幀的資料範圍自動縮放顏色範圍（取可見值的 2–98 百分位）。預設開啟；取消勾選可輸入對所有幀生效的固定最小/最大值。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="245"/>
        <source>Min</source>
        <translation>最小</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="249"/>
        <source>Lower color-range bound (only with Auto range off)</source>
        <translation>顏色範圍下限（僅在關閉自動範圍時可用）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="250"/>
        <source>Upper color-range bound (only with Auto range off)</source>
        <translation>顏色範圍上限（僅在關閉自動範圍時可用）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="259"/>
        <source>Max</source>
        <translation>最大</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="265"/>
        <source>Opacity</source>
        <translation>不透明度</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="272"/>
        <source>Overlay opacity (0 = transparent, 100 = opaque)</source>
        <translation>疊加圖透明度（0 = 透明，100 = 不透明）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="279"/>
        <source>UNITS</source>
        <translation>單位</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="286"/>
        <source>LOG</source>
        <translation>日誌</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="295"/>
        <source>All messages</source>
        <translation>全部訊息</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="296"/>
        <source>Info</source>
        <translation>資訊</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="297"/>
        <source>Warnings + errors</source>
        <translation>警告與錯誤</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="298"/>
        <source>Errors only</source>
        <translation>僅錯誤</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="301"/>
        <source>Show only log messages of this severity</source>
        <translation>僅顯示此嚴重程度的日誌訊息</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="304"/>
        <source>Save…</source>
        <translation>儲存…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="309"/>
        <source>Save the full log to a text file</source>
        <translation>將完整日誌儲存為文字檔</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="312"/>
        <source>Clear</source>
        <translation>清除</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="317"/>
        <source>Clear the log console (messages are not recoverable)</source>
        <translation>清空日誌主控台（訊息不可恢復）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="394"/>
        <source>Save log</source>
        <translation>儲存日誌</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="394"/>
        <source>Text files (*.txt)</source>
        <translation>文字檔 (*.txt)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="424"/>
        <location filename="../../gui/panels/right_sidebar.py" line="435"/>
        <source>Not ready — {0}</source>
        <translation>尚未就緒 — {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="437"/>
        <source>Ready to run.</source>
        <translation>就緒，可以執行。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="472"/>
        <source>Export displacement and strain results to NPZ / MAT / CSV</source>
        <translation>將位移和應變結果匯出為 NPZ / MAT / CSV</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="476"/>
        <source>Compute and visualize strain in a separate post-processing window. Requires displacement results from a completed Run.</source>
        <translation>在獨立的後處理窗口中計算並可視化應變。需先完成一次運行以獲得位移結果。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="482"/>
        <source>Available after the running analysis finishes.</source>
        <translation>待正在執行的分析完成後可用。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="484"/>
        <source>Run an analysis first — there are no results yet.</source>
        <translation>請先執行分析 — 目前還沒有結果。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="502"/>
        <source>Not ready: {0}</source>
        <translation>尚未就緒：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="517"/>
        <source>Starting 3D analysis…</source>
        <translation>正在啟動 3D 分析…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="536"/>
        <source>Cancelling — finishing current frame…</source>
        <translation>正在取消 — 正在完成當前幀…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="537"/>
        <source>Cancelling…</source>
        <translation>正在取消…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="555"/>
        <source>Stopped early — partial results kept</source>
        <translation>提前停止——已保留部分結果</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="572"/>
        <source>Analysis complete</source>
        <translation>分析完成</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="584"/>
        <source>Stopped early at frame {0}/{1} — kept {2} computed frames (later frames are empty)</source>
        <translation>在第 {0}/{1} 幀提前停止——已保留 {2} 個已計算幀（其後幀為空）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="590"/>
        <source>Run interrupted: {0}</source>
        <translation>執行被中斷：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="594"/>
        <source>Frame-1 stereo match: {0}/{1} points matched ({2}%)</source>
        <translation>第 1 幀立體匹配：{0}/{1} 個點匹配成功（{2}%）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="602"/>
        <source>Camera {0}: validity gate removed {1} node-frames (correlation vs frame 1 failed)</source>
        <translation>相機 {0}：有效性門檻移除了 {1} 個節點幀（與第 1 幀的相關性驗證失敗）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="609"/>
        <source>Frame {0}: only {1}% of points valid</source>
        <translation>第 {0} 幀：僅 {1}% 的點有效</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="616"/>
        <source>Quality gate (ZNSSD) removed {0} positions</source>
        <translation>品質門檻（ZNSSD）移除了 {0} 個位置</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="617"/>
        <source>Reprojection gate removed {0} positions</source>
        <translation>重投影門檻移除了 {0} 個位置</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="618"/>
        <source>3D outlier filter removed {0} positions</source>
        <translation>3D 離群點過濾移除了 {0} 個位置</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="626"/>
        <source>No valid points in ANY frame — the run produced an empty result. Check ROI, masks and seeding (details above).</source>
        <translation>所有幀均無有效點——本次執行產生了空結果。請檢查 ROI、遮罩與種子點設定（詳見上方訊息）。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="634"/>
        <source>Analysis complete — {0} frames, median validity {1}%, {2} frame(s) below {3}% (see above)</source>
        <translation>分析完成——共 {0} 幀，中位有效率 {1}%，{2} 幀低於 {3}%（見上方）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="402"/>
        <location filename="../../gui/panels/right_sidebar.py" line="650"/>
        <source>Failed: {0}</source>
        <translation>失敗：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="101"/>
        <source>Cancel the current analysis. Frames computed so far are kept as a partial result; only when nothing was computed yet does the run return to IDLE.</source>
        <translation>取消目前分析。已計算的幀將作為部分結果保留；僅當尚未計算任何幀時，執行才會恢復為閒置狀態。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="663"/>
        <source>Run cancelled</source>
        <translation>執行已取消</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="514"/>
        <location filename="../../gui/panels/right_sidebar.py" line="661"/>
        <location filename="../../gui/panels/right_sidebar.py" line="670"/>
        <source>ELAPSED  {0}</source>
        <translation>已用  {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="515"/>
        <location filename="../../gui/panels/right_sidebar.py" line="548"/>
        <location filename="../../gui/panels/right_sidebar.py" line="662"/>
        <location filename="../../gui/panels/right_sidebar.py" line="676"/>
        <source>REMAINING  {0}</source>
        <translation>剩餘  {0}</translation>
    </message>
</context>
<context>
    <name>ShortcutsDialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="74"/>
        <source>Keyboard Shortcuts</source>
        <translation>鍵盤快速鍵</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="86"/>
        <source>Run the 3D analysis</source>
        <translation>執行 3D 分析</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="87"/>
        <source>Fit the image to the viewport</source>
        <translation>使影像符合檢視區</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="88"/>
        <source>Zoom in / out</source>
        <translation>放大 / 縮小</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="89"/>
        <source>Previous / next frame</source>
        <translation>上一幀 / 下一幀</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="90"/>
        <source>Play / pause (on the canvas: hold to pan)</source>
        <translation>播放 / 暫停（在畫布上：按住以平移）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="91"/>
        <source>New project</source>
        <translation>新建專案</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="92"/>
        <source>Open a project</source>
        <translation>開啟專案</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="93"/>
        <source>Save the project</source>
        <translation>儲存專案</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="94"/>
        <source>Save the project as…</source>
        <translation>另存專案為…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="95"/>
        <source>Cancel the active drawing tool</source>
        <translation>取消目前的繪製工具</translation>
    </message>
</context>
<context>
    <name>StrainFieldSelector3D</name>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="46"/>
        <source>εxx — normal strain along the strain frame&apos;s x axis</source>
        <translation>εxx — 沿應變座標系 x 軸的正應變</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="47"/>
        <source>εyy — normal strain along the strain frame&apos;s y axis</source>
        <translation>εyy — 沿應變座標系 y 軸的正應變</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="48"/>
        <source>εxy — in-plane shear strain (tensor component)</source>
        <translation>εxy — 面內剪應變（張量分量）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="49"/>
        <source>ε₁ — major principal strain (largest in-plane eigenvalue)</source>
        <translation>ε₁ — 最大主應變（面內最大特徵值）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="50"/>
        <source>ε₂ — minor principal strain (smallest in-plane eigenvalue)</source>
        <translation>ε₂ — 最小主應變（面內最小特徵值）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="51"/>
        <source>γ max — maximum shear strain, (ε₁ − ε₂) / 2</source>
        <translation>γ max — 最大剪應變，(ε₁ − ε₂) / 2</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="52"/>
        <source>von Mises — equivalent strain (plane-stress invariant)</source>
        <translation>von Mises — 等效應變（平面應力不變量）</translation>
    </message>
</context>
<context>
    <name>StrainNavigator3D</name>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="46"/>
        <source>Previous frame (←)</source>
        <translation>上一幀 (←)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="53"/>
        <location filename="../../gui/widgets/strain_navigator.py" line="112"/>
        <source>Play animation (Space)</source>
        <translation>播放動畫 (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="60"/>
        <source>Next frame (→)</source>
        <translation>下一幀 (→)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="69"/>
        <source>Playback speed (frames per second). Default 2 fps.</source>
        <translation>播放速度（幀/秒）。預設 2 fps。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="73"/>
        <location filename="../../gui/widgets/strain_navigator.py" line="165"/>
        <source>FRAME 0/0</source>
        <translation>幀 0/0</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="148"/>
        <source>Pause animation (Space)</source>
        <translation>暫停動畫 (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="163"/>
        <source>FRAME {0}/{1}</source>
        <translation>幀 {0}/{1}</translation>
    </message>
</context>
<context>
    <name>StrainParamPanel3D</name>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="81"/>
        <source>Side length, in pixels, of the square window around each node used to fit the local displacement gradient (the virtual strain gauge).

• Larger window → smoother strain, lower spatial resolution.
• Smaller window → sharper strain, more noise.
• Must span at least 3×3 nodes: use ≥ 2 × node spacing + 1 px.</source>
        <translation>以像素為單位的方形視窗邊長，用於在每個節點周圍擬合局部位移梯度（虛擬應變計）。

• 視窗越大 → 應變越平滑，空間解析度越低。
• 視窗越小 → 應變越銳利，雜訊越大。
• 至少需涵蓋 3×3 個節點：請使用 ≥ 2 × 節點間距 + 1 px。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="89"/>
        <source>Strain window</source>
        <translation>應變窗（VSG）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="101"/>
        <source>Number of mesh nodes per axis inside the square strain window — the local plane fit uses every valid node in it. The mm size maps the pixel window through the median 3D spacing of adjacent nodes on the reference surface.</source>
        <translation>方形應變窗內每個座標軸方向涵蓋的網格節點數——局部平面擬合會使用窗內的所有有效節點。毫米尺寸透過參考表面上相鄰節點三維間距的中位數將像素視窗換算為實體尺寸。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="119"/>
        <source>Green-Lagrange (default)</source>
        <translation>Green-Lagrange（預設）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="120"/>
        <source>Infinitesimal</source>
        <translation>無窮小應變</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="124"/>
        <source>Almansi (Eulerian, true tensor)</source>
        <translation>Almansi（歐拉，真實張量）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="128"/>
        <source>Finite-strain measure derived from the SAME displacement-
gradient fit, in the same tangent frame:
Green-Lagrange E = ½(FᵀF − I) — finite strain, reference
configuration (default).
Infinitesimal e = ½(∇u + ∇uᵀ) — small-strain linearization.
Almansi (Eulerian, true tensor) e = ½(I − F⁻ᵀF⁻¹) — the EXACT
finite-strain tensor in the deformed configuration. This is NOT
the 2D app&apos;s linearized per-axis &apos;Eulerian-Almansi&apos; formula
(1/(1−∂u/∂x)−1, …), which differs by ~22% at 10% strain.</source>
        <translation>由同一位移梯度擬合、在同一切平面座標系中導出的有限應變度量：
Green-Lagrange E = ½(FᵀF − I) — 參考組態下的有限應變（預設）。
Infinitesimal e = ½(∇u + ∇uᵀ) — 小應變線性化。
Almansi（歐拉，真實張量）e = ½(I − F⁻ᵀF⁻¹) — 變形組態下的
精確有限應變張量。這不是 2D 應用中線性化的逐軸「歐拉-阿爾曼西」
公式（1/(1−∂u/∂x)−1, …），後者在 10% 應變時相差約 22%。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="139"/>
        <source>Strain type</source>
        <translation>應變類型</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="148"/>
        <source>Hides low-confidence strain near invalid or missing nodes, where
the strain window loses support on one side and the local plane
fit becomes unreliable.
Coefficient × window radius = width of the trimmed band (in px,
on the reference grid).
0.00 = keep every node (no trimming) · 0.70 = recommended ·
1.00 = strictest. Displacement is never affected.</source>
        <translation>隱藏無效或缺失節點附近的低可信度應變——在這些位置應變視窗
單側失去支撐，局部平面擬合不再可靠。
係數 × 視窗半徑 = 被裁剪帶的寬度（以參考網格像素計）。
0.00 = 保留所有節點（不裁剪） · 0.70 = 建議值 · 1.00 = 最嚴格。
位移不受影響。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="161"/>
        <source>Trim low-confidence edges</source>
        <translation>裁剪低可信度邊緣</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="178"/>
        <source>Off</source>
        <translation>關閉</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="179"/>
        <source>Light (σ = 0.5 × step)</source>
        <translation>輕度（σ = 0.5 × step）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="180"/>
        <source>Medium (σ = 1 × step)</source>
        <translation>中等（σ = 1 × step）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="181"/>
        <source>Strong (σ = 2 × step) ⚠</source>
        <translation>強（σ = 2 × step）⚠</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="187"/>
        <source>Gaussian smoothing of the displacement field before the gradient fit.
σ is the kernel width; step = DIC node spacing.
  Light  (0.5 × step): subtle, preserves fine features.
  Medium (1 × step): balanced, for noisy data.
  Strong (2 × step) ⚠: aggressive, may blur real gradients.</source>
        <translation>在梯度擬合前對位移場進行高斯平滑。
σ 為核寬度；step = DIC 節點間距。
  輕度（0.5 × step）：細微，保留精細特徵。
  中等（1 × step）：均衡，適合雜訊數據。
  強（2 × step）⚠：激進，可能模糊真實梯度。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="194"/>
        <source>Strain field smoothing</source>
        <translation>應變場平滑</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="198"/>
        <source>Surface tangent plane</source>
        <translation>表面切平面</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="199"/>
        <source>Left camera frame</source>
        <translation>左相機座標系</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="200"/>
        <source>Custom (3 points)</source>
        <translation>自訂（三點）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="203"/>
        <source>Per-node tangent plane fitted to the reference surface: z is the surface normal pointing toward the camera, x is the left-camera +X projected onto the plane, y = z × x. The right default for curved specimens.</source>
        <translation>對參考曲面逐節點擬合的切平面：z 為指向相機的表面法線，x 為左相機 +X 在該平面上的投影，y = z × x。曲面試樣的最佳預設選擇。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="209"/>
        <source>Report strain in the fixed left-camera (world) axes. Meaningful for flat specimens aligned with the image plane.</source>
        <translation>在固定的左相機（世界）座標軸中回報應變。適用於與像平面對齊的平面試樣。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="213"/>
        <source>A fixed specimen frame built from 3 picked points on the reference image: Origin, a point along +X, and a point on the +Y side.</source>
        <translation>由參考影像上拾取的 3 個點構建的固定試樣座標系：原點、+X 方向上的一點、以及 +Y 一側的一點。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="231"/>
        <source>Coordinate system</source>
        <translation>座標系</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="236"/>
        <source>Pick 3 points…</source>
        <translation>拾取 3 個點…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="241"/>
        <source>Click three points on the reference image: the Origin, a point along +X, then a point on the +Y side. Each click snaps to the nearest valid mesh node. Enabled only for Custom (3 points).</source>
        <translation>在參考影像上依次點擊三個點：原點、+X 方向上的一點、+Y 一側的一點。每次點擊都會吸附到最近的有效網格節點。僅在「自訂（3 點）」模式下可用。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="297"/>
        <source>Trimmed: {0} nodes ({1}%)</source>
        <translation>已裁剪：{0} 個節點 ({1}%)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="387"/>
        <source>Strain window ≈ {0}×{1} nodes</source>
        <translation>應變窗 ≈ {0}×{1} 個節點</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="391"/>
        <source>≈ {0} × {1} mm</source>
        <translation>≈ {0} × {1} mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="401"/>
        <source>⚠ Window radius ({0} px) &lt; node spacing ({1} px); the plane fit needs a 3×3 node gauge. Use ≥ {2} px.</source>
        <translation>⚠ 視窗半徑（{0} px）&lt; 節點間距（{1} px）；平面擬合至少需要 3×3 節點的應變計。請使用 ≥ {2} px。</translation>
    </message>
</context>
<context>
    <name>StrainVizPanel3D</name>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="36"/>
        <source>Show on deformed frame</source>
        <translation>在變形幀上顯示</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="40"/>
        <source>When checked, overlay results on the deformed (current) frame instead of the reference frame</source>
        <translation>勾選後，將結果疊加在變形（當前）幀上，而非參考幀</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="50"/>
        <source>Colormap for the strain overlay. Default turbo; pick RdBu_r or coolwarm for signed strain centered on zero.</source>
        <translation>應變疊加圖使用的顏色映射。預設 turbo；對以零為中心的有符號應變可選 RdBu_r 或 coolwarm。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="54"/>
        <source>Colormap</source>
        <translation>色彩對映</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="56"/>
        <source>Auto range</source>
        <translation>自動範圍</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="60"/>
        <source>Rescale the color range to each frame&apos;s data range (2–98 percentile of the visible values). Default on; uncheck to type fixed Min/Max bounds that hold across frames.</source>
        <translation>根據每幀的資料範圍自動縮放顏色範圍（取可見值的 2–98 百分位）。預設開啟；取消勾選可輸入對所有幀生效的固定最小/最大值。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="72"/>
        <source>Lower color-range bound (only with Auto range off)</source>
        <translation>顏色範圍下限（僅在關閉自動範圍時可用）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="73"/>
        <source>Upper color-range bound (only with Auto range off)</source>
        <translation>顏色範圍上限（僅在關閉自動範圍時可用）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="83"/>
        <source>Min</source>
        <translation>最小</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="85"/>
        <source>Max</source>
        <translation>最大</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="94"/>
        <source>Overlay opacity (0 = transparent, 100 = opaque)</source>
        <translation>疊加圖透明度（0 = 透明，100 = 不透明）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="95"/>
        <source>Opacity</source>
        <translation>不透明度</translation>
    </message>
</context>
<context>
    <name>StrainWindow3D</name>
    <message>
        <location filename="../../gui/strain_window.py" line="111"/>
        <source>Strain Post-Processing</source>
        <translation>應變後處理</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="150"/>
        <source>STRAIN PARAMETERS</source>
        <translation>應變參數</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="159"/>
        <source>Compute Strain</source>
        <translation>計算應變</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="165"/>
        <source>Export Results</source>
        <translation>匯出結果</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="169"/>
        <location filename="../../gui/strain_window.py" line="658"/>
        <source>Export displacement and strain results to NPZ / MAT / CSV</source>
        <translation>將位移和應變結果匯出為 NPZ / MAT / CSV</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="188"/>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="190"/>
        <source>Stop the strain computation at the next frame.</source>
        <translation>在下一幀處停止應變計算。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="199"/>
        <source>FIELD</source>
        <translation>場變量</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="205"/>
        <source>VISUALIZATION</source>
        <translation>可視化</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="209"/>
        <source>LOG</source>
        <translation>日誌</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="328"/>
        <source>Computation Running</source>
        <translation>計算執行中</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="329"/>
        <source>A strain computation is running — cancel it and close?</source>
        <translation>應變計算正在執行——是否取消並關閉？</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="334"/>
        <source>Yes</source>
        <translation>是</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="335"/>
        <source>No</source>
        <translation>否</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="395"/>
        <location filename="../../gui/strain_window.py" line="460"/>
        <location filename="../../gui/strain_window.py" line="563"/>
        <source>Strain compute failed: {0}</source>
        <translation>應變計算失敗：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="407"/>
        <location filename="../../gui/strain_window.py" line="527"/>
        <source>Run 3D analysis first — no results to post-process.</source>
        <translation>請先執行 3D 分析——沒有可後處理的結果。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="410"/>
        <location filename="../../gui/strain_window.py" line="538"/>
        <location filename="../../gui/strain_window.py" line="565"/>
        <source>Click Origin, then +X, then +Y on the image</source>
        <translation>請在影像上依次點擊原點、+X 點、+Y 點</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="417"/>
        <source>Computing strain…</source>
        <translation>正在計算應變…</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="434"/>
        <source>Cancelling…</source>
        <translation>正在取消…</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="439"/>
        <source>Computing strain… {0}%</source>
        <translation>正在計算應變… {0}%</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="451"/>
        <source>Complete</source>
        <translation>完成</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="465"/>
        <source>Strain computation cancelled.</source>
        <translation>應變計算已取消。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="470"/>
        <source>Strain computation complete.</source>
        <translation>應變計算完成。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="475"/>
        <source>⚠ Params changed -- click Compute Strain</source>
        <translation>⚠ 參數已變更 — 請點擊「計算應變」</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="556"/>
        <location filename="../../gui/strain_window.py" line="573"/>
        <source>Picked {0}/3 points</source>
        <translation>已拾取 {0}/3 個點</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="575"/>
        <source>x→{0}  y→{1}  z→{2}</source>
        <translation>x→{0}  y→{1}  z→{2}</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="586"/>
        <source>O</source>
        <translation>O</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="586"/>
        <source>+X</source>
        <translation>+X</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="586"/>
        <source>+Y</source>
        <translation>+Y</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="643"/>
        <source>Run a 3D analysis first — strain needs displacement results.</source>
        <translation>請先執行 3D 分析 — 應變計算需要位移結果。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="647"/>
        <source>Pick the 3 specimen-frame points first (Origin, +X, +Y).</source>
        <translation>請先揀取 3 個試件座標系點（原點、+X、+Y）。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="652"/>
        <source>Compute Green-Lagrange surface strain from the displacement field with the parameters above.</source>
        <translation>使用上方參數由位移場計算 Green-Lagrange 表面應變。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="662"/>
        <source>Run an analysis first — there are no results yet.</source>
        <translation>請先執行分析 — 目前還沒有結果。</translation>
    </message>
</context>
<context>
    <name>UnitsSection3D</name>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="37"/>
        <source>Display unit for displacement and velocity values (colorbar,
3D scalar bar). Display only — the data and every export stay
in millimetres. Strain is dimensionless and unaffected.</source>
        <translation>位移與速度數值的顯示單位（顏色條、3D 純量條）。
僅影響顯示 — 資料和所有匯出始終以毫米為單位。
應變為無因次量，不受影響。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="42"/>
        <source>Display unit</source>
        <translation>顯示單位</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="52"/>
        <source>Acquisition frame rate. Used only by the Velocity field:
velocity = |D(k) − D(k−1)| × frame rate, shown in the
display unit per second.</source>
        <translation>擷取幀率。僅用於速度場：
速度 = |D(k) − D(k−1)| × 幀率，以每秒顯示單位表示。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="57"/>
        <source>Frame rate</source>
        <translation>幀率</translation>
    </message>
</context>
<context>
    <name>View3D</name>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="97"/>
        <source>3D view — run an analysis to see the reconstructed surface.</source>
        <translation>3D 檢視 — 執行分析後即可檢視重建曲面。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="121"/>
        <source>3D view unavailable: {0}</source>
        <translation>3D 檢視不可用：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="154"/>
        <source>No valid 3D points in this frame — nothing to display.</source>
        <translation>此幀沒有有效的 3D 點——沒有可顯示的內容。</translation>
    </message>
</context>
<context>
    <name>View3DTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="56"/>
        <source>Field</source>
        <translation>場變數</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="69"/>
        <source>Colormap</source>
        <translation>色彩對映</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="78"/>
        <source>Resolution</source>
        <translation>解析度</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="89"/>
        <source>Frame sequence</source>
        <translation>影格序列</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="92"/>
        <source>Per-frame image sequence (PNG)</source>
        <translation>逐幀影像序列（PNG）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="97"/>
        <source>Animation</source>
        <translation>動畫</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="104"/>
        <source>Frames per second</source>
        <translation>每秒影格數</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="111"/>
        <source>Frame step</source>
        <translation>抽幀間隔</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="125"/>
        <source>Turntable</source>
        <translation>環繞旋轉</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="130"/>
        <source>Turntable (360° orbit at frame {0})</source>
        <translation>環繞旋轉（在第 {0} 影格繞 360°）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="133"/>
        <source>Orbit frames</source>
        <translation>環繞影格數</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="147"/>
        <source>Export 3D View</source>
        <translation>匯出 3D 視圖</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="160"/>
        <source>Choose an output folder first.</source>
        <translation>請先選擇輸出資料夾。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="166"/>
        <source>Nothing selected to export.</source>
        <translation>未選擇任何要匯出的內容。</translation>
    </message>
</context>
<context>
    <name>ZoomBar</name>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="60"/>
        <source>Fit</source>
        <translation>適配</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="61"/>
        <source>Fit image to viewport</source>
        <translation>將影像適配到視口</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="68"/>
        <source>Current zoom — click to reset to 100% (1:1 pixels).
Wheel: zoom · Right/middle drag: pan · Space: pan mode</source>
        <translation>當前縮放 — 點擊恢復 100%（1:1 像素）。
滾輪：縮放 · 右鍵/中鍵拖動：平移 · 空白鍵：平移模式</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="74"/>
        <source>Zoom in</source>
        <translation>放大</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="78"/>
        <source>Zoom out</source>
        <translation>縮小</translation>
    </message>
</context>
<context>
    <name>dialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="24"/>
        <source>Close</source>
        <translation>關閉</translation>
    </message>
</context>
</TS>
