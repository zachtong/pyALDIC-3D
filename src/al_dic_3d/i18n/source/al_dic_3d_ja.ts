<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="sd_PK">
<context>
    <name>AboutDialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="36"/>
        <source>About pyALDIC-3D</source>
        <translation>pyALDIC-3D について</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="47"/>
        <source>Version {0}</source>
        <translation>バージョン {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="55"/>
        <source>Stereo (3D) digital image correlation — full-field displacement and surface strain from a calibrated camera pair.</source>
        <translation>ステレオ（3D）デジタル画像相関 — 校正済みカメラペアから全視野の変位と表面ひずみを取得します。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="63"/>
        <source>Citation: Zenodo DOI pending release.</source>
        <translation>引用：Zenodo DOI は公開待ちです。</translation>
    </message>
</context>
<context>
    <name>AdvancedSection3D</name>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="38"/>
        <source>Track Both</source>
        <translation>両カメラ追跡</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="39"/>
        <source>Stereo Each Frame</source>
        <translation>毎フレームステレオマッチング</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="40"/>
        <source>Reference Direct</source>
        <translation>参照フレーム直接マッチング</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="51"/>
        <source>How stereo correspondences are propagated through time.
Track Both (default): match stereo once at frame 1, then
track each camera temporally — fastest, one stereo solve.
Stereo Each Frame: re-match stereo at every frame — robust
when temporal tracking drifts, slower.
Reference Direct: match every frame directly to frame 1 in
both cameras — no drift accumulation, small motions only.</source>
        <translation>ステレオ対応を時間方向へどう伝播させるか。
両カメラ追跡（既定）: フレーム 1 で一度だけステレオマッチングし、以後は各カメラで時系列追跡 — 最速、ステレオ求解は 1 回。
毎フレームステレオマッチング: 毎フレームでステレオを再マッチング — 時系列追跡がドリフトする場合に頑健、ただし低速。
参照フレーム直接マッチング: 両カメラとも各フレームをフレーム 1 と直接マッチング — ドリフトは蓄積しないが小さな運動のみ。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="52"/>
        <source>Strategy</source>
        <translation>戦略</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="60"/>
        <source>1 = single global pass (fastest), 3 = default, 5+ = diminishing returns</source>
        <translation>1 = 単一パス（最速）、3 = デフォルト、5 以上は効果逓減</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="61"/>
        <source>AL-DIC Iterations</source>
        <translation>AL-DIC 反復回数</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="63"/>
        <source>Only affects AL-DIC solver. Ignored by Local DIC.</source>
        <translation>AL-DIC ソルバーにのみ影響します。Local DIC では無視されます。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="69"/>
        <source>Parallel camera tracking</source>
        <translation>カメラの並列追跡</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="75"/>
        <source>Track both cameras concurrently — modest speedup (the solver already uses all cores), doubles peak memory</source>
        <translation>両カメラを同時に追跡 — 高速化は限定的（ソルバーは既に全コアを使用）、ピークメモリは 2 倍</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="79"/>
        <source>Auto-expand FFT search on clipped peaks</source>
        <translation>FFT ピークがクリップされたとき検索領域を自動拡大</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="88"/>
        <source>When the temporal FFT integer peak lands on the search-region
boundary, retry with a larger region (engine default on).
Disable for strictly bounded runtimes; then Temporal Search
must cover the largest per-frame motion by itself.</source>
        <translation>時系列 FFT の整数ピークが検索領域の境界に達した場合、
より大きな領域で再試行します（エンジン既定でオン）。
実行時間を厳密に抑えたい場合は無効化してください。その際は
「時間検索」だけで最大のフレーム間移動を覆う必要があります。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="92"/>
        <source>Result checks</source>
        <translation>結果のチェック</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="107"/>
        <source>Tracking check: every tracked point must still look like its
reference-frame subset (correlation mismatch, 0 = perfect, 4 = worst).
Points below 60 % of this value always pass; points up to it
pass when their neighbours agree; the rest are dropped as
failed tracks. Default 1.0 (correlation 0.5). Raise it (e.g.
1.5) for very large strains, lower it for stricter results;
0 turns the check off.</source>
        <translation>追跡チェック：追跡した各点は、参照フレームのサブセットと
まだ似ている必要があります（相関の不一致、0 = 完全、4 = 最悪）。
この値の 60% 未満の点は常に合格、この値までの点は
近傍と一致すれば合格、それ以外は追跡失敗として除外します。
既定 1.0（相関 0.5）。非常に大きなひずみでは上げ（例 1.5）、
より厳しい結果には下げます。
0 でチェックをオフにします。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="109"/>
        <source>Tracking check</source>
        <translation>追跡チェック</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="117"/>
        <source>Stereo check: a left/right match is kept only if its
correlation mismatch is at most this value. Default 0.6
(correlation 0.7); 0 turns the check off.</source>
        <translation>ステレオチェック：左右の対応は、相関の不一致が
この値以下のときだけ保持します。既定 0.6
（相関 0.7）。0 でチェックをオフにします。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="119"/>
        <source>Stereo check</source>
        <translation>ステレオチェック</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="127"/>
        <source>Epipolar limit: a left/right match must lie within this many
pixels of the line the calibration predicts. Default 2 px;
raise it only for a poor calibration; 0 turns the check off.</source>
        <translation>エピポーラ制限：左右の対応点は、キャリブレーションが予測する線から
このピクセル数以内になければなりません。既定 2 px。
キャリブレーションが悪いときだけ上げます。0 でチェックをオフにします。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="130"/>
        <source>Epipolar limit</source>
        <translation>エピポーラ制限</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="140"/>
        <source>off</source>
        <translation>オフ</translation>
    </message>
</context>
<context>
    <name>AnimationTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="57"/>
        <source>Fields</source>
        <translation>フィールド</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="77"/>
        <source>Format</source>
        <translation>形式</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="84"/>
        <source>Frames per second</source>
        <translation>毎秒フレーム数</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="91"/>
        <source>Frame step</source>
        <translation>フレーム間引き</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="92"/>
        <source>Keep every Nth frame (1 = all)</source>
        <translation>N フレームごとに 1 枚残す（1 = すべて）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="99"/>
        <source>Resolution (long edge)</source>
        <translation>解像度（長辺）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="119"/>
        <source>Include colorbar</source>
        <translation>カラーバーを含める</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="124"/>
        <source>Background</source>
        <translation>背景</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="138"/>
        <source>Export Animation</source>
        <translation>アニメーションをエクスポート</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="150"/>
        <source>Load an image sequence first (open the project in the main window).</source>
        <translation>先に画像シーケンスを読み込んでください（メインウィンドウでプロジェクトを開いてください）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="160"/>
        <source>GIF timing has 1/100 s steps: {0} fps will play at {1} fps. Choose MP4 for faster playback.</source>
        <translation>GIF のフレーム間隔は 1/100 秒単位です：{0} fps は {1} fps で再生されます。より速い再生には MP4 を選択してください。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="178"/>
        <source>Choose an output folder first.</source>
        <translation>先に出力フォルダを選択してください。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="182"/>
        <source>No fields enabled.</source>
        <translation>有効なフィールドがありません。</translation>
    </message>
</context>
<context>
    <name>Application</name>
    <message>
        <location filename="../../gui/app.py" line="288"/>
        <source>pyALDIC-3D has hit an error</source>
        <translation>pyALDIC-3D でエラーが発生しました</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="294"/>
        <source>An unexpected error occurred. The application may not behave correctly from here on, so saving your project and restarting is recommended.</source>
        <translation>予期しないエラーが発生しました。この後アプリケーションが正しく動作しない可能性があるため、プロジェクトを保存して再起動することをお勧めします。</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="299"/>
        <source>Details were written to {0}</source>
        <translation>詳細は {0} に書き込まれました</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="350"/>
        <source>Preparing compute kernels in the background…</source>
        <translation>バックグラウンドで計算カーネルを準備しています…</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="361"/>
        <source>Compute kernels ready ({0} s).</source>
        <translation>計算カーネルの準備ができました（{0} 秒）。</translation>
    </message>
</context>
<context>
    <name>BackgroundRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="638"/>
        <source>Original (frame 1 background)</source>
        <translation>原形（第 1 フレームを背景）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="639"/>
        <source>Deformed (current frame background)</source>
        <translation>変形後（現在のフレームを背景）</translation>
    </message>
</context>
<context>
    <name>CalibrationDialog</name>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="92"/>
        <source>Stereo Calibration</source>
        <translation>ステレオキャリブレーション</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="131"/>
        <source>CALIBRATION IMAGE PAIRS</source>
        <translation>キャリブレーション画像ペア</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="134"/>
        <source>Add left images…</source>
        <translation>左画像を追加…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="136"/>
        <source>Add right images…</source>
        <translation>右画像を追加…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="138"/>
        <source>Clear</source>
        <translation>クリア</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="140"/>
        <source>Save detections…</source>
        <translation>検出結果を保存…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="143"/>
        <source>Load detections…</source>
        <translation>検出結果を読み込み…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="150"/>
        <source>No images loaded</source>
        <translation>画像が読み込まれていません</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="158"/>
        <source>Left</source>
        <translation>左</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="159"/>
        <source>Right</source>
        <translation>右</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="160"/>
        <source>Points</source>
        <translation>点数</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="161"/>
        <source>RMS L/R</source>
        <translation>RMS 左/右</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="162"/>
        <source>Max E</source>
        <translation>最大誤差</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="163"/>
        <source>Status</source>
        <translation>状態</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="174"/>
        <source>SELECTED PAIR (L | R)</source>
        <translation>選択中のペア（左 | 右）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="175"/>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="408"/>
        <source>select a pair to preview detected points</source>
        <translation>ペアを選択すると検出点をプレビューします</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="182"/>
        <source>Click to enlarge the annotated detection</source>
        <translation>クリックで注釈付き検出を拡大表示</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="186"/>
        <source>PER-PAIR REPROJECTION ERROR</source>
        <translation>ペアごとの再投影誤差</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="191"/>
        <source>Reject threshold (px)</source>
        <translation>棄却しきい値（px）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="200"/>
        <source>Recalibrate</source>
        <translation>再キャリブレーション</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="212"/>
        <source>CALIBRATION BOARD</source>
        <translation>キャリブレーションボード</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="220"/>
        <source>Chessboard</source>
        <translation>チェスボード</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="221"/>
        <source>ChArUco</source>
        <translation>ChArUco</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="222"/>
        <source>Circle grid</source>
        <translation>円形ドットグリッド</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="223"/>
        <source>Coded dot target (3 ring markers)</source>
        <translation>コード化ドットターゲット（リングマーカー 3 個）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="225"/>
        <source>Type</source>
        <translation>種類</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="230"/>
        <source>Columns x Rows</source>
        <translation>列数 × 行数</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="237"/>
        <source>Square size (mm)</source>
        <translation>正方形サイズ（mm）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="242"/>
        <source>Marker size (mm)</source>
        <translation>マーカーサイズ（mm）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="247"/>
        <source>Dot pitch (mm)</source>
        <translation>ドットピッチ（mm）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="252"/>
        <source>Dot diameter (mm)</source>
        <translation>ドット直径（mm）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="256"/>
        <source>Asymmetric grid</source>
        <translation>非対称グリッド</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="258"/>
        <source>Board printed with OpenCV &lt; 4.7</source>
        <translation>OpenCV &lt; 4.7 で印刷したボード</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="262"/>
        <source>Print board… (1:1 PDF)</source>
        <translation>ボードを印刷…（原寸 PDF）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="266"/>
        <source>SOLVER OPTIONS</source>
        <translation>ソルバーオプション</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="267"/>
        <source>Jointly refine intrinsics (advanced)</source>
        <translation>内部パラメータを同時精密化（上級）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="268"/>
        <source>Estimate tangential distortion p1/p2</source>
        <translation>接線歪み p1/p2 を推定</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="269"/>
        <source>Fix k3 = 0 (low-distortion lens)</source>
        <translation>k3 = 0 に固定（低歪みレンズ）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="270"/>
        <source>Release-object method (printed boards)</source>
        <translation>Release-object 法（印刷ボード）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="271"/>
        <source>Dot eccentricity correction</source>
        <translation>ドット偏心補正</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="273"/>
        <source>Joint bundle adjustment (robust, uses mono views)</source>
        <translation>バンドル調整（ロバスト、単眼ビューも利用）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="274"/>
        <source>Optimize board shape (printed boards)</source>
        <translation>ボード形状を最適化（印刷ボード）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="289"/>
        <source>Calibrate</source>
        <translation>キャリブレーション実行</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="300"/>
        <source>RESULT</source>
        <translation>結果</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="301"/>
        <source>No calibration yet</source>
        <translation>まだキャリブレーションがありません</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="306"/>
        <source>Verify with board images…</source>
        <translation>ボード画像で検証…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="318"/>
        <source>Accept &amp;&amp; Save…</source>
        <translation>承認して保存…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="324"/>
        <source>Cancel</source>
        <translation>キャンセル</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="383"/>
        <source>Choose {0} calibration images</source>
        <translation>{0} カメラの校正画像を選択</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="385"/>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="718"/>
        <source>Images (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)</source>
        <translation>画像 (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="430"/>
        <source>{0} left / {1} right images</source>
        <translation>左 {0} 枚 / 右 {1} 枚</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="440"/>
        <source>Load equal, &gt;= 3 left/right image sets first.</source>
        <translation>左右同数(3 組以上)の画像を先に読み込んでください。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="471"/>
        <source>Working… {0}</source>
        <translation>処理中… {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="480"/>
        <source>Calibration failed: {0}</source>
        <translation>キャリブレーション失敗:{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="505"/>
        <source>used</source>
        <translation>使用</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="507"/>
        <source>L: {0}</source>
        <translation>左:{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="509"/>
        <source>R: {0}</source>
        <translation>右:{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="525"/>
        <source>Stereo RMS {0:.3f} px | epipolar {1:.3f} px</source>
        <translation>ステレオ RMS {0:.3f} px | エピポーラ {1:.3f} px</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="528"/>
        <source>Baseline {0:.2f} mm | pairs {1}/{2}</source>
        <translation>基線 {0:.2f} mm | ペア {1}/{2}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="531"/>
        <source>fx {0:.1f}  fy {1:.1f}  cx {2:.1f}  cy {3:.1f}</source>
        <translation>fx {0:.1f}  fy {1:.1f}  cx {2:.1f}  cy {3:.1f}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="534"/>
        <source>Coverage L {0:.0%} / R {1:.0%} | tilt {2:.0f}-{3:.0f}°</source>
        <translation>カバレッジ 左 {0:.0%} / 右 {1:.0%} | 傾き {2:.0f}-{3:.0f}°</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="543"/>
        <source>Bundle adjustment: RMS {0:.3f} -&gt; {1:.3f} px ({2:.0f} mono views)</source>
        <translation>バンドル調整：RMS {0:.3f} -&gt; {1:.3f} px（単眼ビュー {2:.0f} 件）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="549"/>
        <source>Board flatness: z-range {0:.3f} mm</source>
        <translation>ボード平面度：z 範囲 {0:.3f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="552"/>
        <source>Warning: {0}</source>
        <translation>警告:{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="690"/>
        <source>Save board PDF</source>
        <translation>ボード PDF を保存</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="692"/>
        <source>PDF (*.pdf)</source>
        <translation>PDF (*.pdf)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="703"/>
        <source>Board PDF written: {0}</source>
        <translation>ボード PDF を書き込みました：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="719"/>
        <source>Choose LEFT verification image</source>
        <translation>左カメラの検証画像を選択</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="724"/>
        <source>Choose RIGHT verification image</source>
        <translation>右カメラの検証画像を選択</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="733"/>
        <source>Verification failed: {0}</source>
        <translation>検証に失敗しました：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="740"/>
        <source>Verify: pitch {0:.4f} mm vs {1:g} mm — scale error {2:.3%}, plane RMS {3:.4f} mm</source>
        <translation>検証：ピッチ {0:.4f} mm 対 {1:g} mm — スケール誤差 {2:.3%}、平面 RMS {3:.4f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="753"/>
        <source>Save calibration as</source>
        <translation>キャリブレーションを保存</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="755"/>
        <source>OpenCV YAML (*.yml *.yaml *.xml)</source>
        <translation>OpenCV YAML (*.yml *.yaml *.xml)</translation>
    </message>
</context>
<context>
    <name>CalibrationFindings</name>
    <message>
        <location filename="../../gui/calibration_findings.py" line="55"/>
        <source>Camera {0}: the board reached {1:.0%} of the image-corner radius. Beyond it the lens model is a guess: two equally good fits differ by up to {2:.2f} px there. Add views with the board near the image corners, keep the region of interest inside the covered area, or fix k3 for a low-distortion lens.</source>
        <translation>カメラ {0}：ボードは画像コーナー半径の {1:.0%} までしか届いていません。その外側のレンズモデルは推測です。同じくらい良い 2 つのフィットがそこで最大 {2:.2f} px 異なります。画像の隅近くにボードを置いたビューを追加するか、関心領域を覆われた範囲内に収めるか、低歪みレンズでは k3 を固定してください。</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="61"/>
        <source>Camera {0}: the board reached {1:.0%} of the image-corner radius; the lens model is fitted only inside that radius.</source>
        <translation>カメラ {0}：ボードは画像コーナー半径の {1:.0%} まで届いています。レンズモデルはこの半径の内側だけでフィットされています。</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="47"/>
        <source>Camera {0}: the board reached {1:.0%} of the image-corner radius. Beyond it the lens model is a guess: two equally good fits differ by up to {2:.2f} px there. With k3 fixed, the corners are right only if the lens has no k3 distortion: add views with the board near the image corners, or keep the region of interest inside the covered area.</source>
        <translation>カメラ {0}：ボードは画像コーナー半径の {1:.0%} までしか届いていません。その外側のレンズモデルは推測です。同じくらい良い 2 つのフィットがそこで最大 {2:.2f} px 異なります。k3 を固定した場合、コーナーが正しいのはレンズに k3 歪みがないときだけです。画像の隅近くにボードを置いたビューを追加するか、関心領域を覆われた範囲内に収めてください。</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="70"/>
        <source>Camera {0}: the residuals follow a pattern the lens model does not explain (binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model fits), although the board shape is already optimised. A lens the model cannot describe, a board that bends differently from view to view, or detector bias can cause this.</source>
        <translation>カメラ {0}：ボード形状はすでに最適化されていますが、残差にレンズモデルでは説明できないパターンがあります（ビン超過 {1:.1f}、フィット場 {2:.1f} × ノイズ。モデルが合っていれば約 1）。モデルで表せないレンズ、ビューごとに曲がり方が変わるボード、または検出の偏りが原因になり得ます。</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="80"/>
        <source>Camera {0}: the residuals follow a pattern the lens model does not explain (binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model fits). Often the board is the cause (not flat, or its points not exactly where the board description puts them): tick Joint bundle adjustment and Optimize board shape. A lens the model cannot describe or detector bias can also cause this.</source>
        <translation>カメラ {0}：残差にレンズモデルでは説明できないパターンがあります（ビン超過 {1:.1f}、フィット場 {2:.1f} × ノイズ。モデルが合っていれば約 1）。原因はボードであることが多いです（平らでない、または点がボードの記述どおりの位置にない）。「バンドル調整」と「ボード形状を最適化」にチェックを入れてください。モデルで表せないレンズや検出の偏りが原因のこともあります。</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="85"/>
        <source>Camera {0}: the extrapolation check was skipped (too few usable views).</source>
        <translation>カメラ {0}：外挿チェックはスキップされました（使えるビューが少なすぎます）。</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="91"/>
        <source>Camera {0}: the lens-model check was skipped: the points fill only {1} image cells.</source>
        <translation>カメラ {0}：レンズモデルのチェックはスキップされました。点が {1} 個の画像セルにしかありません。</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="103"/>
        <source>Warning: {0}</source>
        <translation>警告:{0}</translation>
    </message>
</context>
<context>
    <name>CalibrationSection3D</name>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="50"/>
        <source>Calibrate from images…</source>
        <translation>画像からキャリブレーション…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="59"/>
        <source>Run the built-in stereo calibrator on your target photos
(checkerboard / ChArUco / dot grid). Writes an opencv_yaml
file and loads it — the recommended path when you have
calibration images.</source>
        <translation>ターゲット写真（チェッカーボード / ChArUco / ドットグリッド）に対して内蔵ステレオキャリブレーターを実行します。
opencv_yaml ファイルを書き出して読み込みます — キャリブレーション画像がある場合の推奨手順です。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="65"/>
        <source>Format</source>
        <translation>形式</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="80"/>
        <source>File format of the calibration to import. Default opencv_yaml
(written by the built-in calibrator). Pick the format matching
your source: dice (DICe XML), matchid (MatchID .caldat),
opencorr (OpenCorr CSV), mmc (MultiDIC/MMC .mat), matlabcv
(MATLAB stereoParams .mat).</source>
        <translation>インポートするキャリブレーションのファイル形式。既定は opencv_yaml（内蔵キャリブレーターの出力形式）。
ソースに合わせて選択してください: dice（DICe XML）、matchid（MatchID .caldat）、
opencorr（OpenCorr CSV）、mmc（MultiDIC/MMC .mat）、matlabcv（MATLAB stereoParams .mat）。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="85"/>
        <source>Import calibration…</source>
        <translation>キャリブレーションを読み込む…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="92"/>
        <source>Load an existing stereo calibration file in the selected
Format. The status line below shows fx / fy and the baseline
as a sanity check.</source>
        <translation>選択した形式で既存のステレオキャリブレーションファイルを読み込みます。
下のステータス行に fx / fy と基線長が表示され、妥当性確認に使えます。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="96"/>
        <source>Manual parameters…</source>
        <translation>パラメータを手動入力…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="103"/>
        <source>Type intrinsics and extrinsics by hand (fx, fy, cx, cy,
distortion, R, T) — the fallback when no calibration file
exists. Writes an opencv_yaml file and loads it.</source>
        <translation>内部・外部パラメーター（fx、fy、cx、cy、歪み、R、T）を手入力します
— キャリブレーションファイルがない場合の代替手段。opencv_yaml ファイルを書き出して読み込みます。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="107"/>
        <source>No calibration loaded</source>
        <translation>キャリブレーションが未読み込みです</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="151"/>
        <source>Choose calibration file</source>
        <translation>キャリブレーションファイルを選択</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="153"/>
        <source>Calibration files (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)</source>
        <translation>キャリブレーションファイル (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="171"/>
        <source>Error: {0}</source>
        <translation>エラー：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="179"/>
        <source>{0}
fx {1:.0f}  fy {2:.0f}  |  baseline {3:.1f} mm</source>
        <translation>{0}
fx {1:.0f}  fy {2:.0f}  |  基線長 {3:.1f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="185"/>
        <source>calibration loaded: baseline {0:.1f} mm</source>
        <translation>キャリブレーションを読み込みました：基線長 {0:.1f} mm</translation>
    </message>
</context>
<context>
    <name>CameraDropZone</name>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="76"/>
        <source>{0} frames</source>
        <translation>{0} フレーム</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="106"/>
        <source>Click to pick this camera&apos;s image folder, or drag the folder here. Both cameras need the same number of frames.</source>
        <translation>クリックしてこのカメラの画像フォルダーを選択するか、フォルダーをここにドラッグします。両カメラのフレーム数は一致している必要があります。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="114"/>
        <source>Select image folder</source>
        <translation>画像フォルダを選択</translation>
    </message>
</context>
<context>
    <name>CameraRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="606"/>
        <source>Camera</source>
        <translation>カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="610"/>
        <source>Left</source>
        <translation>左</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="611"/>
        <source>Right</source>
        <translation>右</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="612"/>
        <source>Left + Right</source>
        <translation>左 + 右</translation>
    </message>
</context>
<context>
    <name>CanvasArea3D</name>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="93"/>
        <source>Fit</source>
        <translation>フィット</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="96"/>
        <source>Fit the image to the viewport (Ctrl+0)</source>
        <translation>画像をビューポートに合わせる (Ctrl+0)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="106"/>
        <source>Current zoom — click to reset to 100% (1:1 pixels).
Wheel: zoom · Right/middle drag: pan · Space: pan mode</source>
        <translation>現在のズーム — クリックで 100%（1:1 ピクセル）に戻します。
ホイール: ズーム · 右/中ドラッグ: パン · スペース: パンモード</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="110"/>
        <source>Zoom in (Ctrl+=)</source>
        <translation>拡大 (Ctrl+=)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="114"/>
        <source>Zoom out (Ctrl+-)</source>
        <translation>縮小 (Ctrl+-)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="135"/>
        <source>Show Grid</source>
        <translation>グリッドを表示</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="143"/>
        <source>Show the computational mesh preview on the reference view
(left camera, frame 1). Rebuilt live from the current Subset
Step / refinement settings — what you see is the run&apos;s mesh.
Default on; turn off to declutter the canvas.</source>
        <translation>参照ビュー（左カメラ、フレーム 1）に計算メッシュのプレビューを表示します。
現在のサブセットステップ／細分化設定から即時に再構築され、表示どおりのメッシュが実行に使われます。
既定はオン。キャンバスを整理したいときはオフにします。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="155"/>
        <source>Hovering a mesh node shows its correlation subset window
(the Subset Size box). Needs Show Grid. Use it to judge
whether the subset spans enough speckle texture.</source>
        <translation>メッシュ節点にカーソルを合わせると、その相関サブセットウィンドウ（サブセットサイズの枠）を表示します。
「グリッド表示」が必要です。サブセットが十分なスペックル模様を含むかの判断に使えます。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="168"/>
        <source>Switch the canvas to the reconstructed 3D surface (colored by
the selected field, with the camera frusta). Uncheck to return
to the 2D image view. Requires results.</source>
        <translation>キャンバスを再構築された 3D 表面に切り替えます（選択中のフィールドで着色、カメラ視錐台つき）。
オフにすると 2D 画像ビューに戻ります。結果が必要です。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="148"/>
        <source>Show Subset</source>
        <translation>サブセットを表示</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="122"/>
        <source>Show ROI</source>
        <translation>ROI を表示</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="130"/>
        <source>Show the drawn region of interest (blue) and refinement zones
on the reference view (left camera, frame 1). Turned off when
an analysis finishes so the results are not tinted; drawing
with an ROI or brush tool turns it back on.</source>
        <translation>参照ビュー（左カメラ、フレーム 1）に、描画した関心領域（青）
と細分化領域を表示します。解析が終わると、結果に色が
重ならないよう自動でオフになります。ROI ツールや
ブラシで描くと再びオンになります。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="161"/>
        <source>3D View</source>
        <translation>3D ビュー</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="351"/>
        <source>Load images before importing an ROI mask</source>
        <translation>ROI マスクを読み込む前に画像を読み込んでください</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="356"/>
        <source>Could not import the mask: {0}</source>
        <translation>マスクを読み込めませんでした：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="359"/>
        <source>ROI mask imported from {0}</source>
        <translation>{0} から ROI マスクを読み込みました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="364"/>
        <source>No ROI mask to save — draw one first</source>
        <translation>保存する ROI マスクがありません — 先に描いてください</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="372"/>
        <source>Save Mask</source>
        <translation>マスクを保存</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="373"/>
        <source>PNG image (*.png)</source>
        <translation>PNG 画像 (*.png)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="379"/>
        <source>Could not save the mask: {0}</source>
        <translation>マスクを保存できませんでした：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="382"/>
        <source>ROI mask saved to {0}</source>
        <translation>ROI マスクを {0} に保存しました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="585"/>
        <source>Analysis produced no valid points — nothing to display. See the log.</source>
        <translation>解析で有効な点が得られませんでした — 表示できる内容がありません。ログを確認してください。</translation>
    </message>
</context>
<context>
    <name>CanvasRenderMixin</name>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="71"/>
        <source>Could not map the ROI into the right camera: {0}</source>
        <translation>ROI を右カメラに写せませんでした：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="208"/>
        <source>3D view — run an analysis to see the reconstructed surface.</source>
        <translation>3D ビュー — 解析を実行すると再構成曲面が表示されます。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="214"/>
        <source>Selected field is not available.</source>
        <translation>選択した項目は利用できません。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="405"/>
        <source>Could not draw the overlay: {0}</source>
        <translation>オーバーレイを描画できませんでした：{0}</translation>
    </message>
</context>
<context>
    <name>CanvasToolsMixin</name>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="55"/>
        <source>Starting points cleared</source>
        <translation>シード点をクリアしました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="83"/>
        <source>Starting points are placed on the LEFT camera, frame 1 — switch there to add a point</source>
        <translation>シード点は左カメラの第 1 フレームに配置します — その表示に切り替えてから追加してください</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="92"/>
        <source>Starting point {0} placed at ({1}, {2})</source>
        <translation>シード点 {0} を ({1}, {2}) に配置しました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="112"/>
        <source>Starting point removed at ({0}, {1})</source>
        <translation>({0}, {1}) のシード点を削除しました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="170"/>
        <source>Fit</source>
        <translation>フィット</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="172"/>
        <source>Zoom to 100%</source>
        <translation>100% にズーム</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="175"/>
        <source>Copy image to clipboard</source>
        <translation>画像をクリップボードにコピー</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="178"/>
        <source>Clear ROI</source>
        <translation>ROI をクリア</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="181"/>
        <source>Clear seed points</source>
        <translation>シード点をクリア</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="191"/>
        <source>Canvas image copied to the clipboard</source>
        <translation>キャンバスの画像をクリップボードにコピーしました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="210"/>
        <source>1. Drop the left/right camera folders in the sidebar
2. Calibrate or import calibration
3. Draw the ROI and Run</source>
        <translation>1. サイドバーに左/右カメラのフォルダーをドロップ
2. 校正するか校正を読み込む
3. ROI を描いて実行</translation>
    </message>
</context>
<context>
    <name>ConfigOverlay3D</name>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="39"/>
        <source>Mode</source>
        <translation>モード</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="40"/>
        <source>Solver</source>
        <translation>ソルバー</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="41"/>
        <source>Init</source>
        <translation>初期推定</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="42"/>
        <source>Subset</source>
        <translation>サブセット</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="79"/>
        <source>AL-DIC ({0} iter)</source>
        <translation>AL-DIC（{0} 回反復）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="94"/>
        <source>FFT (no starting point)</source>
        <translation>FFT（シード点なし）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="82"/>
        <source>Local DIC</source>
        <translation>Local DIC</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="84"/>
        <source>Starting Point</source>
        <translation>シード点</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="85"/>
        <source>Previous frame</source>
        <translation>前フレーム</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="86"/>
        <location filename="../../gui/widgets/config_overlay.py" line="96"/>
        <source>FFT</source>
        <translation>FFT</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="75"/>
        <source>Accumulative</source>
        <translation>累積式</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="76"/>
        <source>Incremental</source>
        <translation>逐次式</translation>
    </message>
</context>
<context>
    <name>ConsoleLog3D</name>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="41"/>
        <source>Copy all</source>
        <translation>すべてコピー</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="44"/>
        <source>Save log to file…</source>
        <translation>ログをファイルに保存…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="46"/>
        <source>Clear</source>
        <translation>クリア</translation>
    </message>
</context>
<context>
    <name>DataTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="50"/>
        <source>Format</source>
        <translation>形式</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="52"/>
        <source>NumPy archive (.npz)</source>
        <translation>NumPy アーカイブ (.npz)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="54"/>
        <source>MATLAB (.mat)</source>
        <translation>MATLAB (.mat)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="56"/>
        <source>CSV (one file per frame)</source>
        <translation>CSV（フレームごとに 1 ファイル）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="57"/>
        <source>PLY point clouds (per frame)</source>
        <translation>PLY 点群（フレームごと）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="58"/>
        <source>VTU mesh series (ParaView)</source>
        <translation>VTU メッシュ時系列（ParaView）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="61"/>
        <source>✓ Parameters file (JSON) always exported</source>
        <translation>✓ パラメータファイル（JSON）は常にエクスポートされます</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="68"/>
        <source>Displacement</source>
        <translation>変位</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="72"/>
        <source>Strain</source>
        <translation>ひずみ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="80"/>
        <source>3D points, reprojection error, and source flags are always exported.</source>
        <translation>3D 点・再投影誤差・ソースフラグは常にエクスポートされます。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="88"/>
        <source>Export Data</source>
        <translation>データをエクスポート</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="105"/>
        <source>Select:</source>
        <translation>選択：</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="108"/>
        <source>All</source>
        <translation>全選択</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="109"/>
        <source>None</source>
        <translation>全解除</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="158"/>
        <source>Choose an output folder first.</source>
        <translation>先に出力フォルダを選択してください。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="189"/>
        <source>Wrote: {0}</source>
        <translation>書き込みました：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="193"/>
        <source>Export cancelled — kept: {0}</source>
        <translation>エクスポートをキャンセルしました — 保持：{0}</translation>
    </message>
</context>
<context>
    <name>DetectionFilesMixin</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="215"/>
        <source>Save detections</source>
        <translation>検出結果を保存</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="217"/>
        <location filename="../../gui/dialogs/calibration_support.py" line="238"/>
        <source>NumPy detections (*.npz)</source>
        <translation>NumPy 検出結果 (*.npz)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="231"/>
        <source>Detections saved: {0}</source>
        <translation>検出結果を保存しました：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="236"/>
        <source>Load detections</source>
        <translation>検出結果を読み込み</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="261"/>
        <source>Loaded {0} detection pairs — Recalibrate re-solves without re-detecting</source>
        <translation>{0} ペアの検出結果を読み込みました — 再キャリブレーションで検出なしに再計算できます</translation>
    </message>
</context>
<context>
    <name>DetectionZoomDialog</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="274"/>
        <source>Detection preview — pair {0}</source>
        <translation>検出プレビュー — ペア {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="283"/>
        <source>Wheel: zoom · Right/middle drag: pan</source>
        <translation>ホイール：ズーム · 右/中ボタンドラッグ：パン</translation>
    </message>
</context>
<context>
    <name>ExportDialog</name>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="145"/>
        <source>Export Results</source>
        <translation>結果をエクスポート</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="152"/>
        <source>OUTPUT FOLDER</source>
        <translation>出力フォルダ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="155"/>
        <source>Select output folder…</source>
        <translation>出力フォルダを選択…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="157"/>
        <source>Browse…</source>
        <translation>参照…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="158"/>
        <source>Choose the folder all exports are written into</source>
        <translation>すべてのエクスポートの書き込み先フォルダーを選択します</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="161"/>
        <source>Open Folder</source>
        <translation>フォルダを開く</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="162"/>
        <source>Open the output folder in the file explorer</source>
        <translation>出力フォルダーをエクスプローラーで開きます</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="174"/>
        <source>Data</source>
        <translation>データ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="175"/>
        <source>Images</source>
        <translation>画像</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="176"/>
        <source>Animation</source>
        <translation>アニメーション</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="177"/>
        <source>Preview &amp; Colorbar</source>
        <translation>プレビューとカラーバー</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="178"/>
        <source>3D View</source>
        <translation>3D ビュー</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="184"/>
        <source>Numeric results: field-selective NPZ / MAT / CSV tables plus PLY / VTU meshes for external tools.</source>
        <translation>数値結果: フィールドを選択できる NPZ / MAT / CSV テーブルと、外部ツール向けの PLY / VTU メッシュ。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="188"/>
        <source>Rendered per-camera field overlays as PNG images, one per frame, using the Preview &amp; Colorbar style.</source>
        <translation>カメラごとのフィールドオーバーレイを PNG 画像として書き出します（各フレーム 1 枚、「プレビューとカラーバー」のスタイルを使用）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="192"/>
        <source>GIF / MP4 animations of the field overlay across frames, using the Preview &amp; Colorbar style.</source>
        <translation>フィールドオーバーレイのフレーム間 GIF / MP4 アニメーション（「プレビューとカラーバー」のスタイルを使用）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="196"/>
        <source>WYSIWYG style source: the colorbar and margins configured here are used by every Images / Animation export.</source>
        <translation>WYSIWYG のスタイル設定元: ここで設定したカラーバーと余白が、すべての画像／アニメーションのエクスポートに使われます。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="484"/>
        <source>Export Running</source>
        <translation>エクスポート実行中</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="485"/>
        <source>An export is still running — cancel it and close?</source>
        <translation>エクスポートが実行中です — キャンセルして閉じますか？</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="488"/>
        <source>Yes</source>
        <translation>はい</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="489"/>
        <source>No</source>
        <translation>いいえ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="521"/>
        <source>Folder does not exist: {0}</source>
        <translation>フォルダーが存在しません：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="210"/>
        <source>Close</source>
        <translation>閉じる</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="200"/>
        <source>Offscreen renders of the 3D surface as images, a deforming animation or a turntable, from your current 3D view.</source>
        <translation>3D 表面のオフスクリーンレンダリング。現在の 3D ビューの視点で、画像・変形アニメーション・ターンテーブルとして書き出します。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="508"/>
        <source>Choose output folder</source>
        <translation>出力フォルダを選択</translation>
    </message>
</context>
<context>
    <name>ExportTabBase</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="250"/>
        <source>Cancelling…</source>
        <translation>キャンセルしています…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="287"/>
        <source>Export cancelled — {0} file(s) kept</source>
        <translation>エクスポートをキャンセルしました — {0} 個のファイルを保持</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="290"/>
        <source>(the unfinished animation was deleted)</source>
        <translation>（未完了のアニメーションは削除しました）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="296"/>
        <source>Nothing was written: no data to draw for {0}.</source>
        <translation>何も書き出されませんでした：{0} には描画できるデータがありません。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="301"/>
        <source>Nothing was written — the export produced no files.</source>
        <translation>何も書き出されませんでした — エクスポートでファイルが作成されませんでした。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="307"/>
        <source>{0} frame(s) had no data to draw ({1})</source>
        <translation>{0} フレームに描画できるデータがありませんでした（{1}）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="313"/>
        <source>no data for {0}</source>
        <translation>{0} のデータなし</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="318"/>
        <source>the right-camera ROI could not be derived; the tracked area was used</source>
        <translation>右カメラの ROI を導出できなかったため、追跡領域を使用しました</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="278"/>
        <source>Error: {0}</source>
        <translation>エラー：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="282"/>
        <source>Wrote {0} file(s)</source>
        <translation>{0} 個のファイルを書き出しました</translation>
    </message>
</context>
<context>
    <name>ExportTabs</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="625"/>
        <source>Full resolution</source>
        <translation>フル解像度</translation>
    </message>
</context>
<context>
    <name>FieldRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="420"/>
        <source>Auto</source>
        <translation>自動</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="421"/>
        <source>Auto range</source>
        <translation>自動レンジ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="436"/>
        <source>Opacity</source>
        <translation>不透明度</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="437"/>
        <source>Field opacity (0 = transparent, 1 = fully opaque)</source>
        <translation>フィールドの不透明度（0 = 透明、1 = 完全に不透明）</translation>
    </message>
</context>
<context>
    <name>FieldSelector3D</name>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="47"/>
        <source>DISPLACEMENT</source>
        <translation>変位</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="70"/>
        <source>U — world-frame displacement along X (left camera&apos;s +X, image right), in mm</source>
        <translation>U — ワールド座標系 X 方向の変位（左カメラの +X、画像右向き）、単位 mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="73"/>
        <source>V — world-frame displacement along Y (left camera&apos;s +Y, image down), in mm</source>
        <translation>V — ワールド座標系 Y 方向の変位（左カメラの +Y、画像下向き）、単位 mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="77"/>
        <source>W — world-frame displacement along Z (left camera&apos;s optical axis, toward the scene): out-of-plane motion, in mm</source>
        <translation>W — ワールド座標系 Z 方向の変位（左カメラの光軸、シーン向き）: 面外運動、単位 mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="78"/>
        <source>|D| — displacement magnitude √(U²+V²+W²), in mm</source>
        <translation>|D| — 変位の大きさ √(U²+V²+W²)、単位 mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="83"/>
        <location filename="../../gui/widgets/field_selector.py" line="111"/>
        <source>Velocity — per-node speed |D(k) − D(k−1)| × frame rate, in the display unit per second. Depends on the frame rate set in the UNITS section; frame 1 has no predecessor (empty).</source>
        <translation>速度 — 節点ごとの速さ |D(k) − D(k−1)| × フレームレート。表示単位毎秒で表示します。UNITS セクションのフレームレート設定に依存します。フレーム 1 には前フレームがありません（空表示）。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="103"/>
        <source>Run an analysis first — velocity needs results.</source>
        <translation>先に解析を実行してください — 速度場には結果が必要です。</translation>
    </message>
</context>
<context>
    <name>FrameMasksSection3D</name>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="65"/>
        <source>Per-frame masks</source>
        <translation>フレームごとのマスク</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="74"/>
        <source>Optional: one mask image per frame (non-zero = valid), for
specimens whose valid region changes, e.g. a crack or a
boundary that moves. Without them the ROI of frame 1 is used
for every frame.</source>
        <translation>任意：フレームごとに 1 枚のマスク画像（非ゼロ = 有効）。
き裂や移動する境界など、有効領域が変わる試験片に使います。
ない場合は、すべてのフレームで
フレーム 1 の ROI を使います。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="83"/>
        <source>Import…</source>
        <translation>読み込み…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="84"/>
        <source>Choose the folder holding this camera&apos;s mask images</source>
        <translation>このカメラのマスク画像があるフォルダーを選択します</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="87"/>
        <source>Clear</source>
        <translation>クリア</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="97"/>
        <source>Left</source>
        <translation>左</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="99"/>
        <source>Right</source>
        <translation>右</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="104"/>
        <source>{0}: {1} masks</source>
        <translation>{0}：マスク {1} 枚</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="106"/>
        <source>{0}: none</source>
        <translation>{0}：なし</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="114"/>
        <source>Choose the mask folder</source>
        <translation>マスクのフォルダーを選択</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="128"/>
        <source>Masks not imported for the {0} camera: {1}</source>
        <translation>{0}カメラのマスクを読み込めませんでした：{1}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="142"/>
        <source>{0} camera: {1} per-frame masks from {2}</source>
        <translation>{0}カメラ：{2} からフレームごとのマスク {1} 枚</translation>
    </message>
</context>
<context>
    <name>FrameNavigator3D</name>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="45"/>
        <source>Previous frame (←)</source>
        <translation>前フレーム (←)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="52"/>
        <location filename="../../gui/widgets/frame_navigator.py" line="160"/>
        <source>Play animation (Space)</source>
        <translation>アニメーションを再生 (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="59"/>
        <source>Next frame (→)</source>
        <translation>次のフレーム (→)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="68"/>
        <source>Playback speed (frames per second). Default 2 fps.</source>
        <translation>再生速度（フレーム/秒）。既定は 2 fps。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="153"/>
        <source>Pause animation (Space)</source>
        <translation>アニメーションを一時停止 (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="175"/>
        <source>FRAME {0}/{1}</source>
        <translation>フレーム {0}/{1}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="177"/>
        <source>FRAME 0/0</source>
        <translation>フレーム 0/0</translation>
    </message>
</context>
<context>
    <name>FrameRangeRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="656"/>
        <source>All frames</source>
        <translation>すべてのフレーム</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="660"/>
        <source>From frame</source>
        <translation>開始フレーム</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="670"/>
        <source>to</source>
        <translation>〜</translation>
    </message>
</context>
<context>
    <name>ImageCanvas3D</name>
    <message>
        <location filename="../../gui/widgets/image_view.py" line="763"/>
        <source>The three points are nearly in a line — spread them around the edge</source>
        <translation>3 点がほぼ一直線上にあります — 円周に沿って離して選んでください</translation>
    </message>
</context>
<context>
    <name>ImagesTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="55"/>
        <source>Fields</source>
        <translation>フィールド</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="75"/>
        <source>Format</source>
        <translation>形式</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="84"/>
        <source>JPEG quality</source>
        <translation>JPEG 品質</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="91"/>
        <source>Resolution (long edge)</source>
        <translation>解像度（長辺）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="100"/>
        <source>Include colorbar</source>
        <translation>カラーバーを含める</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="105"/>
        <source>Background</source>
        <translation>背景</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="119"/>
        <source>Export Images</source>
        <translation>画像をエクスポート</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="131"/>
        <source>Load an image sequence first (open the project in the main window).</source>
        <translation>先に画像シーケンスを読み込んでください（メインウィンドウでプロジェクトを開いてください）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="156"/>
        <source>Choose an output folder first.</source>
        <translation>先に出力フォルダを選択してください。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="160"/>
        <source>No fields enabled.</source>
        <translation>有効なフィールドがありません。</translation>
    </message>
</context>
<context>
    <name>InitGuessSection3D</name>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="112"/>
        <source>Clear</source>
        <translation>クリア</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="74"/>
        <source>Starting Points</source>
        <translation>シード点</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="85"/>
        <source>Click one or more points on the LEFT camera, frame 1 — at least
one per connected ROI region. Each point&apos;s neighborhood is matched
automatically into the right camera (stereo offset) and into
frame 2 (motion seed), then a first-order deformation field is
propagated to every mesh node — no search tuning needed. Best for
wide stereo baselines, large first-frame motion, or discontinuous
fields. If no point is placed, the run falls back to FFT.</source>
        <translation>左カメラの第 1 フレーム上で 1 つ以上の点をクリックします — 連結した
ROI 領域ごとに少なくとも 1 点。各点の近傍は右カメラ（ステレオオフセット）
と第 2 フレーム（運動シード）へ自動的にマッチングされ、続いて一次の変形場が
すべてのメッシュ節点へ伝播されます — 探索パラメータの調整は不要です。
広い基線長、第 1 フレームの大きな運動、不連続場に適しています。点が未配置の
場合、実行時は FFT にフォールバックします。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="94"/>
        <location filename="../../gui/widgets/init_guess_section.py" line="192"/>
        <source>Place points…</source>
        <translation>シード点を配置…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="101"/>
        <source>Enter placement mode on the canvas. Left-click the LEFT camera,
frame 1 to ADD a point; right-click removes the nearest; Esc exits.</source>
        <translation>キャンバスの配置モードに入ります。左カメラの第 1 フレームを左クリックで
点を追加、右クリックで最も近い点を削除、Esc で終了します。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="103"/>
        <source>Auto-place</source>
        <translation>自動配置</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="110"/>
        <source>Place one Starting Point automatically, deep inside the ROI on
the LEFT camera, frame 1. Add more by hand for disconnected
regions or strongly varying motion.</source>
        <translation>左カメラ・フレーム 1 の ROI の奥にシード点を 1 つ
自動配置します。つながっていない領域や動きが大きく
変わる場合は、手動で追加してください。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="113"/>
        <source>Remove all Starting Points</source>
        <translation>すべてのシード点を削除</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="122"/>
        <source>FFT (cross-correlation)</source>
        <translation>FFT(相互相関)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="130"/>
        <source>Full-grid cross-correlation seeds frame 1 (and every reference
switch in incremental mode); later frames warm-start from the
previous solution. Robust default — the search radius is the
Temporal Search parameter.</source>
        <translation>全グリッドの相互相関が第 1 フレーム（逐次モードでは参照フレーム
切替時にも）の初期値を与えます。以降のフレームは前フレームの解から
ウォームスタートします。堅牢な既定 — 探索半径は「時系列探索」
パラメータで決まります。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="134"/>
        <source>Previous frame</source>
        <translation>前フレーム</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="142"/>
        <source>Start every frame from the previous frame&apos;s solution — no
cross-correlation at all. Fastest; can silently freeze on large
motion or decorrelation — the validity gate will flag affected
frames.</source>
        <translation>各フレームを前フレームの解から開始します — 相互相関は一切
実行しません。最速ですが、大きな運動やスペックルの相関低下では
沈黙のまま凍結することがあります — 有効性ゲートが該当フレームに
フラグを立てます。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="191"/>
        <source>Placing… (click to exit)</source>
        <translation>配置中…(クリックで終了)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="237"/>
        <source>No point placed: the run finds the stereo offset from probe patches and seeds frame 1 by FFT. Place a point (or Auto-place) for large first-frame motion.</source>
        <translation>シード点なし：実行時にプローブ領域からステレオのずれを求め、フレーム 1 を FFT で初期化します。最初のフレームの動きが大きい場合は点を配置（または自動配置）してください。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="240"/>
        <location filename="../../gui/widgets/init_guess_section.py" line="273"/>
        <source>{0} point(s) placed</source>
        <translation>{0} 点を配置</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="276"/>
        <source>{0} point(s) · {1}/{2} regions ready</source>
        <translation>{0} 点 · {1}/{2} 領域が準備完了</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="283"/>
        <source>{0} point(s) · {1}/{2} regions seeded — rest auto-seeded at run</source>
        <translation>{0} 点 · {1}/{2} 領域にシード — 残りは実行時に自動シード</translation>
    </message>
</context>
<context>
    <name>Issues</name>
    <message>
        <location filename="../../gui/issue_text.py" line="28"/>
        <source>left camera</source>
        <translation>左カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="31"/>
        <source>right camera</source>
        <translation>右カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="38"/>
        <source>calibration file not set</source>
        <translation>校正ファイルが未設定です</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="41"/>
        <source>left/right sequences not set</source>
        <translation>左/右シーケンスが未設定です</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="42"/>
        <source>need at least 2 frames</source>
        <translation>少なくとも 2 フレーム必要です</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="43"/>
        <source>ROI not set</source>
        <translation>ROI が未設定です</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="46"/>
        <source>ROI is empty (xmin&lt;xmax, ymin&lt;ymax required)</source>
        <translation>ROI が空です(xmin&lt;xmax かつ ymin&lt;ymax が必要)</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="49"/>
        <source>left and right sequences use the same image files</source>
        <translation>左右のシーケンスが同じ画像ファイルを使っています</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="64"/>
        <source>sequence length mismatch: {0} vs {1}</source>
        <translation>シーケンス長が一致しません：{0} 対 {1}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="68"/>
        <source>calibration file cannot be read: {0}</source>
        <translation>キャリブレーションファイルを読み込めません：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="72"/>
        <source>{0}: image not readable: {1}</source>
        <translation>{0}：画像を読み込めません：{1}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="76"/>
        <source>{0}: frame sizes differ ({1} vs {2})</source>
        <translation>{0}：フレームサイズが異なります（{1} と {2}）</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="82"/>
        <source>ROI mask is {0} but the images are {1}: redraw or import it again</source>
        <translation>ROI マスクは {0} ですが画像は {1} です：描き直すか再度読み込んでください</translation>
    </message>
</context>
<context>
    <name>LeftSidebar3D</name>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="83"/>
        <source>IMAGES</source>
        <translation>画像</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="90"/>
        <source>Drop LEFT camera
folder or click</source>
        <translation>左カメラのフォルダを
ドロップまたはクリック</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="91"/>
        <source>Drop RIGHT camera
folder or click</source>
        <translation>右カメラのフォルダを
ドロップまたはクリック</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="96"/>
        <source>Natural Sort (1, 2, …, 10)</source>
        <translation>自然順ソート (1, 2, …, 10)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="103"/>
        <source>Sort file names numerically (img2 before img10). Default on; turn off for strict alphabetical order. Applies to the next folder load.</source>
        <translation>ファイル名を数値順に並べ替えます（img2 が img10 の前）。既定はオン。オフにすると厳密なアルファベット順になります。次のフォルダー読み込みから適用されます。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="117"/>
        <location filename="../../gui/panels/left_sidebar.py" line="710"/>
        <source>No images loaded</source>
        <translation>画像が読み込まれていません</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="143"/>
        <source>CALIBRATION</source>
        <translation>キャリブレーション</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="147"/>
        <source>WORKFLOW TYPE</source>
        <translation>ワークフロー種別</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="154"/>
        <source>INITIAL GUESS</source>
        <translation>初期推定</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="158"/>
        <source>REGION OF INTEREST</source>
        <translation>関心領域</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="162"/>
        <source>PARAMETERS</source>
        <translation>パラメータ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="166"/>
        <source>ADVANCED</source>
        <translation>詳細設定</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="238"/>
        <source>Incremental: each frame is compared to the previous reference frame.
Suitable for large accumulated deformation, required for large rotations.

Accumulative: every frame is compared to frame 1.
Accurate for small, monotonic deformation only.</source>
        <translation>逐次: 各フレームを直前の参照フレームと比較します。
大きな累積変形に適し、大回転では必須です。

累積: 各フレームを第 1 フレームと比較します。
小さく単調な変形にのみ適します。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="250"/>
        <source>Local DIC</source>
        <translation>Local DIC</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="260"/>
        <source>Local DIC: Independent subset matching (IC-GN). Fast,
preserves sharp local features. Best for small
deformations or high-quality images.

AL-DIC: Augmented Lagrangian with global FEM
regularization. Enforces displacement compatibility
between subsets. Best for large deformations, noisy
images, or when strain accuracy matters.</source>
        <translation>Local DIC: 独立サブセットマッチング(IC-GN)。高速で
局所特徴を保持します。小変形や高品質画像に最適です。

AL-DIC: 全体 FEM 正則化付き拡張ラグランジュ。
サブセット間の変位適合性を強制します。
大変形・ノイズ画像・ひずみ精度重視の場合に最適です。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="262"/>
        <source>Solver</source>
        <translation>ソルバー</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="336"/>
        <location filename="../../gui/panels/left_sidebar.py" line="360"/>
        <source>bbox: not set</source>
        <translation>境界ボックス: 未設定</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="363"/>
        <source>bbox: {0}–{1}, {2}–{3} px</source>
        <translation>境界ボックス: {0}–{1}, {2}–{3} px</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="388"/>
        <source>IC-GN subset window size in pixels (odd number). Default 33.
Larger = more robust on sparse speckle, smoother fields;
smaller = finer spatial detail but noisier. The subset must
span several speckles.</source>
        <translation>IC-GN サブセットウィンドウのサイズ（ピクセル、奇数）。既定は 33。
大きいほど疎なスペックルに強く滑らかに、小さいほど空間分解能が高くノイズが増えます。
サブセットは複数のスペックルを含む必要があります。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="227"/>
        <source>Accumulative</source>
        <translation>累積式</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="228"/>
        <source>Incremental</source>
        <translation>逐次式</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="239"/>
        <source>Tracking Mode</source>
        <translation>追跡モード</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="321"/>
        <source>Draw on the LEFT camera, frame 1 — all later frames and the right camera follow from it.</source>
        <translation>左カメラの第 1 フレームに描画します——以降のフレームと右カメラはそこから導かれます。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="389"/>
        <source>Subset Size</source>
        <translation>サブセットサイズ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="401"/>
        <source>Node spacing in pixels (power of 2). Default 16. Smaller =
denser measurement grid and longer runs; larger = faster but
coarser fields. Typically ¼–½ of the Subset Size.</source>
        <translation>節点間隔（ピクセル、2 のべき乗）。既定は 16。小さいほど計測グリッドが密になり実行が長く、
大きいほど速い代わりに場が粗くなります。通常はサブセットサイズの 1/4〜1/2。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="402"/>
        <source>Subset Step</source>
        <translation>サブセットステップ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="408"/>
        <source>Stereo Search</source>
        <translation>ステレオ探索</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="417"/>
        <source>off</source>
        <translation>オフ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="427"/>
        <source>Epipolar Band</source>
        <translation>エピポーラ帯</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="440"/>
        <source>Temporal Search</source>
        <translation>時系列探索</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="446"/>
        <source>Mesh refinement</source>
        <translation>メッシュ細分化</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="453"/>
        <source>Refine at mask boundaries (holes)</source>
        <translation>マスク境界（穴）で細分化</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="461"/>
        <source>Quadtree-subdivide mesh elements crossing interior mask
holes so the mesh hugs the hole edges. Default off (uniform
grid); enable when the ROI mask has cut-outs whose rims you
care about.</source>
        <translation>マスク内部の穴を横切るメッシュ要素を四分木細分化し、メッシュを穴の縁に沿わせます。
既定はオフ（一様グリッド）。ROI マスクに縁が重要な切り抜きがある場合に有効化してください。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="463"/>
        <source>Refine at ROI edges</source>
        <translation>ROI の縁で細分化</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="470"/>
        <source>Quadtree-subdivide mesh elements along the outer ROI
boundary. Default off; enable for curved / irregular ROI
outlines where the uniform grid staircases.</source>
        <translation>ROI の外側境界に沿ってメッシュ要素を四分木細分化します。
既定はオフ。ROI の輪郭が曲線的・不規則で、一様グリッドが階段状になる場合に有効化してください。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="482"/>
        <source>How aggressively refined elements shrink: the minimum element
is step / 2^level. Default 1 (light); 3 is heavy — finer
boundary detail but many more nodes and a slower run.</source>
        <translation>細分化された要素をどこまで小さくするか: 最小要素は step / 2^level。
既定は 1（軽度）。3 は重度で、境界の細部は精細になりますが節点が大幅に増え実行が遅くなります。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="483"/>
        <source>Refinement Level</source>
        <translation>細分化レベル</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="608"/>
        <source>Half-width (pixels) of the temporal FFT integer search that seeds
each per-frame match. Set comfortably larger than the expected
inter-frame motion; with Auto-expand on (default) the engine can
still grow the search past this on a boundary-clipped peak.</source>
        <translation>各フレームのマッチングを初期化する時系列 FFT 整数探索の半幅（ピクセル）。
予想されるフレーム間の動きより十分に大きく設定してください。自動拡大が
オン（既定）の場合、ピークが探索境界に達するとエンジンは探索範囲をこの
値を超えて広げることができます。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="622"/>
        <source>Current images: the engine starts the FFT search clamped to
{0} px (max(10, min(H, W) / 4 - subset)); Auto-expand can grow
it to {1} px (max(32, min(H, W) / 2)) on clipped peaks.</source>
        <translation>現在の画像：エンジンは実行開始時に FFT 探索を {0} px
（max(10, min(H, W) / 4 - サブセット)）に制限します。ピークがクリップ
されると、自動拡大により {1} px（max(32, min(H, W) / 2)）まで拡大できます。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="646"/>
        <source>Inactive with the current Initial Guess / Tracking Mode: the
temporal FFT runs only when Initial Guess = FFT, or at reference
switches in Incremental mode; in Accumulative + Starting Point /
Previous frame no FFT runs, so this control has no effect.</source>
        <translation>現在の初期推定 / 追跡モードでは無効です。時系列 FFT は初期推定 = FFT
のとき、または逐次式モードの参照フレーム切り替え時にのみ実行されます。
累積式 + シード点 / 前フレームでは FFT は実行されないため、この
コントロールは効果がありません。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="617"/>
        <source>Current images: values above {0} px cannot widen the search
(the window is clamped at the image borders).</source>
        <translation>現在の画像では {0} px を超える値にしても探索範囲は広がりません
（探索ウィンドウは画像境界でクリップされます）。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="268"/>
        <source>Extra filters (correlation, outliers)</source>
        <translation>追加フィルター（相関・外れ値）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="277"/>
        <source>Post-run filters: drop points whose correlation (ZNSSD),
reprojection error or 3D-outlier distance is too poor.
Default off (keep every tracked point); enable for noisy
data when a few bad points pollute the fields. The log
reports how many points each filter removed.</source>
        <translation>解析後のフィルター：相関（ZNSSD）、再投影誤差、
3D 外れ値距離が悪すぎる点を除外します。
既定はオフ（追跡した点をすべて保持）。ノイズの多いデータで
少数の不良点が場を乱すときに有効にします。
各フィルターが除外した点の数はログに表示されます。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="426"/>
        <source>Epipolar band: the left-to-right match is searched only within
this many pixels of the line the calibration predicts for each
node, over the Stereo Search distance along it, so a look-alike
off the line cannot be picked. Default 15 px; never narrower
than the Epipolar limit; 0 searches a square window instead.</source>
        <translation>エピポーラ帯：左右の対応は、キャリブレーションが各節点に
予測する線からこの画素数以内だけを、線に沿ってはステレオ
探索の距離だけ探索するため、線から外れた似た模様を選ぶ
ことはありません。既定 15 px。エピポーラ制限より狭く
なりません。0 の場合は正方形ウィンドウで探索します。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="602"/>
        <source>How far (pixels) the left-to-right stereo match searches around
each node&apos;s expected position: along the epipolar line, or in a
square window when the Epipolar Band is off. Set it larger than
the error expected in that position.</source>
        <translation>左右ステレオ対応が各節点の予想位置の周りを探索する距離
（画素）：エピポーラ線に沿って探索し、エピポーラ帯がオフの
ときは正方形ウィンドウで探索します。その予想位置の誤差より
大きく設定してください。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="657"/>
        <source>No images found in {0}</source>
        <translation>{0} に画像が見つかりません</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="665"/>
        <source>left camera</source>
        <translation>左カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="666"/>
        <source>right camera</source>
        <translation>右カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="669"/>
        <source>This folder holds both cameras ({0}): using its {1} images for the {2}</source>
        <translation>このフォルダーには両方のカメラの画像があります（{0}）：{2}には {1} 枚を使います</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="679"/>
        <source>{0}: {1} images from {2}</source>
        <translation>{0}：{2} から画像 {1} 枚</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="715"/>
        <source>Paired: {0} frames per camera</source>
        <translation>ペアリング済み：各カメラ {0} フレーム</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="721"/>
        <source>Mismatch: {0} left vs {1} right</source>
        <translation>不一致：左 {0} フレーム、右 {1} フレーム</translation>
    </message>
</context>
<context>
    <name>MainMenuMixin</name>
    <message>
        <location filename="../../gui/main_menu.py" line="58"/>
        <source>&amp;File</source>
        <translation>ファイル(&amp;F)</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="60"/>
        <source>New Project</source>
        <translation>新規プロジェクト</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="66"/>
        <source>Open Project…</source>
        <translation>プロジェクトを開く…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="73"/>
        <source>Recent Projects</source>
        <translation>最近使ったプロジェクト</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="79"/>
        <source>Save Project</source>
        <translation>プロジェクトを保存</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="84"/>
        <source>Save Project As…</source>
        <translation>プロジェクトに名前を付けて保存…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="94"/>
        <source>Associate .aldic3d files with pyALDIC-3D…</source>
        <translation>.aldic3d ファイルを pyALDIC-3D に関連付け…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="100"/>
        <source>Register .aldic3d so double-clicking a project file opens pyALDIC-3D (current user only, no admin rights needed).</source>
        <translation>.aldic3d を登録すると、プロジェクトファイルのダブルクリックで pyALDIC-3D が開きます（現在のユーザーのみ、管理者権限不要）。</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="105"/>
        <source>Quit</source>
        <translation>終了</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="113"/>
        <source>&amp;Help</source>
        <translation>ヘルプ(&amp;H)</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="114"/>
        <source>User Guide</source>
        <translation>ユーザーガイド</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="118"/>
        <source>Keyboard Shortcuts</source>
        <translation>キーボードショートカット</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="121"/>
        <source>About pyALDIC-3D</source>
        <translation>pyALDIC-3D について</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="132"/>
        <source>&amp;Settings</source>
        <translation>設定(&amp;S)</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="133"/>
        <location filename="../../gui/main_menu.py" line="180"/>
        <source>Language</source>
        <translation>言語</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="157"/>
        <location filename="../../gui/main_menu.py" line="163"/>
        <source>File Association</source>
        <translation>ファイルの関連付け</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="158"/>
        <source>Could not register the .aldic3d association: {0}</source>
        <translation>.aldic3d の関連付けを登録できませんでした: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="167"/>
        <source>Done — double-clicking a .aldic3d file now opens it in pyALDIC-3D (registered for the current user).</source>
        <translation>完了 — .aldic3d ファイルをダブルクリックすると pyALDIC-3D で開くようになりました（現在のユーザーに登録済み）。</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="175"/>
        <source>The interface language changes to {0} after pyALDIC-3D restarts.</source>
        <translation>pyALDIC-3D を再起動すると表示言語が {0} に切り替わります。</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="188"/>
        <source>Could not open a web browser. The user guide is at {0}</source>
        <translation>Web ブラウザーを開けませんでした。ユーザーガイドはこちら：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="215"/>
        <source>(not reachable)</source>
        <translation>（アクセスできません）</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="220"/>
        <source>No recent projects</source>
        <translation>最近のプロジェクトはありません</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="224"/>
        <source>Clear list</source>
        <translation>リストをクリア</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="232"/>
        <source>The project file is not reachable right now: {0}</source>
        <translation>現在プロジェクトファイルにアクセスできません：{0}</translation>
    </message>
</context>
<context>
    <name>MainWindow3D</name>
    <message>
        <location filename="../../gui/main_window.py" line="144"/>
        <source>pyALDIC-3D ready</source>
        <translation>pyALDIC-3D の準備ができました</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="185"/>
        <source>Run an analysis first — there are no results to post-process</source>
        <translation>先に解析を実行してください。後処理できる結果がありません</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="217"/>
        <source>Strain window available — open it from the sidebar</source>
        <translation>ひずみウィンドウが利用可能です — サイドバーから開けます</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="279"/>
        <location filename="../../gui/main_window.py" line="297"/>
        <source>Analysis Running</source>
        <translation>解析を実行中</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="280"/>
        <source>An analysis is running — cancel it and quit?</source>
        <translation>解析が実行中です — キャンセルして終了しますか？</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="285"/>
        <location filename="../../gui/main_window.py" line="301"/>
        <location filename="../../gui/main_window.py" line="685"/>
        <source>Yes</source>
        <translation>はい</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="286"/>
        <location filename="../../gui/main_window.py" line="302"/>
        <location filename="../../gui/main_window.py" line="686"/>
        <source>No</source>
        <translation>いいえ</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="298"/>
        <source>An analysis is running — cancel it and switch projects?</source>
        <translation>解析を実行中です。中止してプロジェクトを切り替えますか？</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="332"/>
        <source>Unsaved Changes</source>
        <translation>未保存の変更</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="333"/>
        <source>The project has unsaved changes. Save them before continuing?</source>
        <translation>プロジェクトに未保存の変更があります。続行する前に保存しますか？</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="340"/>
        <source>Save</source>
        <translation>保存</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="341"/>
        <source>Discard</source>
        <translation>破棄</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="342"/>
        <location filename="../../gui/main_window.py" line="601"/>
        <location filename="../../gui/main_window.py" line="687"/>
        <source>Cancel</source>
        <translation>キャンセル</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="363"/>
        <source>Switched to left camera, frame 1 for ROI editing</source>
        <translation>ROI 編集のため左カメラのフレーム 1 に切り替えました</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="368"/>
        <source>Load images first, then draw the region of interest</source>
        <translation>先に画像を読み込んでから関心領域を描いてください</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="381"/>
        <source>Load images first, then place a starting point</source>
        <translation>先に画像を読み込んでからシード点を配置してください</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="399"/>
        <source>Starting points are already placed; clear them to auto-place</source>
        <translation>シード点はすでに配置されています。自動配置するには先にクリアしてください</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="405"/>
        <source>Draw the ROI first: the point is placed inside it</source>
        <translation>先に ROI を描いてください。点は ROI の内側に配置されます</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="412"/>
        <source>Starting point placed automatically at ({0:.0f}, {1:.0f})</source>
        <translation>シード点を自動配置しました：({0:.0f}, {1:.0f})</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="420"/>
        <source>Load images first, then use the brush</source>
        <translation>先に画像を読み込んでからブラシを使ってください</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="507"/>
        <source>Loading project…</source>
        <translation>プロジェクトを読み込み中…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="509"/>
        <source>Could not open the project: {0}</source>
        <translation>プロジェクトを開けませんでした：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="512"/>
        <source>Could not open the project:
{0}

{1}</source>
        <translation>プロジェクトを開けませんでした：
{0}

{1}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="524"/>
        <source>Opened {0}</source>
        <translation>{0} を開きました</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="547"/>
        <source>Open cancelled: {0}</source>
        <translation>開くのを中止しました：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="556"/>
        <source>Camera {0}: {1} image(s) not found (was {2}). Results stay viewable and exportable; running again needs the images.</source>
        <translation>カメラ {0}：画像 {1} 枚が見つかりません（元の場所 {2}）。結果は表示・エクスポートできますが、再実行には画像が必要です。</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="561"/>
        <source>Relocated {0} camera-{1} images: {2} -&gt; {3}</source>
        <translation>カメラ {1} の画像 {0} 枚の場所を更新しました：{2} -&gt; {3}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="568"/>
        <source>Calibration file found at {0}</source>
        <translation>キャリブレーションファイルが見つかりました：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="576"/>
        <source>The calibration file was not found; using the copy saved in the project: {0}</source>
        <translation>キャリブレーションファイルが見つからないため、プロジェクトに保存されたコピーを使います：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="580"/>
        <source>The rigid motion was not removed (the results are shown as measured): {0}</source>
        <translation>剛体運動は除去されませんでした（結果は測定値のまま表示）：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="591"/>
        <source>Images Not Found</source>
        <translation>画像が見つかりません</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="597"/>
        <source>Some of this project&apos;s images cannot be found. Open it anyway? Results stay viewable and exportable; running again needs the images.</source>
        <translation>このプロジェクトの画像の一部が見つかりません。それでも開きますか？結果は表示・エクスポートできますが、再実行には画像が必要です。</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="600"/>
        <source>Open anyway</source>
        <translation>それでも開く</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="609"/>
        <location filename="../../gui/main_window.py" line="619"/>
        <source>Locate Images</source>
        <translation>画像の場所を指定</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="614"/>
        <source>The selected folder does not contain this project&apos;s camera {0} frames. Pick the folder holding the original image files, or cancel to abort opening.</source>
        <translation>選択したフォルダーには本プロジェクトのカメラ {0} のフレームが含まれていません。元の画像ファイルがあるフォルダーを選択するか、キャンセルして開く操作を中止してください。</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="624"/>
        <source>The image folder saved with this project was not found:
{0}

Select the folder that now contains the camera {1} frames (file names must match).</source>
        <translation>プロジェクトと共に保存された画像フォルダーが見つかりません:
{0}

カメラ {1} のフレームが現在あるフォルダーを選択してください（ファイル名が一致する必要があります）。</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="628"/>
        <source>Locate images for camera {0}</source>
        <translation>カメラ {0} の画像の場所を指定</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="670"/>
        <source>Include Results?</source>
        <translation>結果を含めますか？</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="671"/>
        <source>Include the analysis results in this project file?</source>
        <translation>このプロジェクトファイルに解析結果を含めますか？</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="677"/>
        <source>Including results (about {0} uncompressed) lets you reopen the project without recomputing. Choose No to save a small configuration-only file for sharing.</source>
        <translation>結果を含める（非圧縮で約 {0}）と、再計算せずにプロジェクトを再度開けます。「いいえ」を選ぶと共有向けの小さな設定のみのファイルを保存します。</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="713"/>
        <source>unknown size</source>
        <translation>サイズ不明</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="722"/>
        <source>Saving project…</source>
        <translation>プロジェクトを保存中…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="726"/>
        <source>Could not save the project: {0}</source>
        <translation>プロジェクトを保存できませんでした：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="732"/>
        <source>Could not save the project:
{0}

{1}

The previous version of the file, if any, is unchanged.</source>
        <translation>プロジェクトを保存できませんでした：
{0}

{1}

以前のファイル（ある場合）は変更されていません。</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="738"/>
        <source>Saved {0}</source>
        <translation>{0} を保存しました</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="438"/>
        <source>Untitled</source>
        <translation>無題</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="438"/>
        <source>{0}[*] — pyALDIC-3D</source>
        <translation>{0}[*] — pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="483"/>
        <source>New project</source>
        <translation>新規プロジェクト</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="492"/>
        <location filename="../../gui/main_window.py" line="511"/>
        <source>Open Project</source>
        <translation>プロジェクトを開く</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="494"/>
        <location filename="../../gui/main_window.py" line="656"/>
        <source>pyALDIC-3D project (*.aldic3d)</source>
        <translation>pyALDIC-3D プロジェクト (*.aldic3d)</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="654"/>
        <location filename="../../gui/main_window.py" line="728"/>
        <source>Save Project</source>
        <translation>プロジェクトを保存</translation>
    </message>
</context>
<context>
    <name>ManualParamsDialog</name>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="53"/>
        <source>Manual Camera Parameters</source>
        <translation>カメラパラメータの手動入力</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="61"/>
        <source>Left camera (world frame)</source>
        <translation>左カメラ（世界座標系）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="62"/>
        <source>Right camera</source>
        <translation>右カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="67"/>
        <source>Stereo extrinsics  (X_R = R · X_L + T)</source>
        <translation>ステレオ外部パラメータ（X_R = R · X_L + T）</translation>
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
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="90"/>
        <source>Euler composition R = Rz·Ry·Rx in degrees (MatchID/OpenCorr convention); distortion order k1, k2, p1, p2, k3 (OpenCV).</source>
        <translation>オイラー角合成 R = Rz·Ry·Rx（度、MatchID/OpenCorr 規約）。歪み係数の順序は k1, k2, p1, p2, k3（OpenCV）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="101"/>
        <source>Save as YAML…</source>
        <translation>YAML として保存…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="106"/>
        <source>Cancel</source>
        <translation>キャンセル</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="142"/>
        <source>Baseline |T| = {0:.2f} mm</source>
        <translation>基線 |T| = {0:.2f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="147"/>
        <source>Baseline is zero — enter the translation T first.</source>
        <translation>基線がゼロです — 先に並進 T を入力してください。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="154"/>
        <source>Save calibration as</source>
        <translation>キャリブレーションを保存</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="156"/>
        <source>OpenCV YAML (*.yml *.yaml *.xml)</source>
        <translation>OpenCV YAML (*.yml *.yaml *.xml)</translation>
    </message>
</context>
<context>
    <name>MeshAppearanceControls</name>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="39"/>
        <source>Mesh:</source>
        <translation>メッシュ：</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="40"/>
        <source>Line color and width of the mesh overlay (Show Grid)</source>
        <translation>メッシュオーバーレイの線の色と太さ（グリッドを表示）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="45"/>
        <source>Mesh overlay line color — click to choose</source>
        <translation>メッシュオーバーレイの線色 — クリックして選択</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="53"/>
        <source>Mesh overlay line width (screen pixels)</source>
        <translation>メッシュオーバーレイの線幅（画面ピクセル）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="79"/>
        <source>Choose mesh line color</source>
        <translation>メッシュ線の色を選択</translation>
    </message>
</context>
<context>
    <name>NextStepHint</name>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="50"/>
        <source>Load the left and right camera folders</source>
        <translation>左右カメラのフォルダーを読み込んでください</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="55"/>
        <source>Calibrate from images or import a calibration</source>
        <translation>画像から校正するか、校正を読み込んでください</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="58"/>
        <source>Draw the ROI on the left camera, frame 1</source>
        <translation>左カメラのフレーム 1 に ROI を描いてください</translation>
    </message>
</context>
<context>
    <name>PairActionsMixin</name>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="58"/>
        <source>Removed {0} image pair(s)</source>
        <translation>画像ペアを {0} 組削除しました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="69"/>
        <source>Remove Image Pairs</source>
        <translation>画像ペアの削除</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="74"/>
        <source>Removing {0} pair(s) changes the sequence — the current results will be discarded. Continue?</source>
        <translation>{0} 組のペアを削除するとシーケンスが変わります — 現在の結果は破棄されます。続行しますか？</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="78"/>
        <source>Yes</source>
        <translation>はい</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="79"/>
        <source>No</source>
        <translation>いいえ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="94"/>
        <source>Folder does not exist: {0}</source>
        <translation>フォルダーが存在しません：{0}</translation>
    </message>
</context>
<context>
    <name>PairBars</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="106"/>
        <source>no solve yet</source>
        <translation>まだ解がありません</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="128"/>
        <source>worst-camera RMS per pair; dashed = reject threshold</source>
        <translation>ペアごとの最悪カメラ RMS。破線 = 棄却しきい値</translation>
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
        <translation>選択した {0} 組のペアを削除</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="73"/>
        <source>Reveal in Explorer</source>
        <translation>エクスプローラーで表示</translation>
    </message>
</context>
<context>
    <name>PreviewTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="120"/>
        <source>Open this tab to render a preview.</source>
        <translation>このタブを開くとプレビューが描画されます。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="128"/>
        <source>Field</source>
        <translation>フィールド</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="135"/>
        <source>Frame</source>
        <translation>フレーム</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="144"/>
        <source>Camera</source>
        <translation>カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="148"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="226"/>
        <source>Left</source>
        <translation>左</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="149"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="225"/>
        <source>Right</source>
        <translation>右</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="180"/>
        <source>FIELD APPEARANCE</source>
        <translation>フィールドの外観</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="185"/>
        <source>Colormap</source>
        <translation>カラーマップ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="187"/>
        <source>Auto</source>
        <translation>自動</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="188"/>
        <source>Auto range</source>
        <translation>自動レンジ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="191"/>
        <source>Range</source>
        <translation>範囲</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="197"/>
        <source>Min</source>
        <translation>最小</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="198"/>
        <source>Max</source>
        <translation>最大</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="205"/>
        <source>Opacity</source>
        <translation>不透明度</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="207"/>
        <source>Apply to all fields</source>
        <translation>すべてのフィールドに適用</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="213"/>
        <source>Apply this field&apos;s colormap, opacity and auto-range to every enabled field (each field keeps its own min/max).</source>
        <translation>このフィールドの colormap・不透明度・自動範囲を、有効なすべてのフィールドに適用します（各フィールドの min/max は保持）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="220"/>
        <source>COLORBAR STYLE</source>
        <translation>カラーバーのスタイル</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="227"/>
        <source>Top</source>
        <translation>上</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="228"/>
        <source>Bottom</source>
        <translation>下</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="232"/>
        <source>Position</source>
        <translation>位置</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="238"/>
        <source>Font size</source>
        <translation>フォントサイズ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="244"/>
        <source>Font family</source>
        <translation>フォント</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="252"/>
        <source>Bar thickness</source>
        <translation>バーの太さ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="255"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="274"/>
        <source>Black</source>
        <translation>黒</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="255"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="274"/>
        <source>White</source>
        <translation>白</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="258"/>
        <source>Background</source>
        <translation>背景</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="269"/>
        <source>Add a blank border around the exported content, as a fraction of the long edge (0 = none).</source>
        <translation>書き出す内容の周囲に空白の枠を追加します。幅は長辺に対する割合です（0 = なし）。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="271"/>
        <source>Margin</source>
        <translation>余白</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="277"/>
        <source>Margin color</source>
        <translation>余白の色</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="279"/>
        <source>Refresh preview</source>
        <translation>プレビューを更新</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="531"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="545"/>
        <source>Preview failed: </source>
        <translation>プレビューに失敗しました：</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="431"/>
        <source>Enable a field on the Images tab to preview.</source>
        <translation>プレビューするには Images タブでフィールドを有効にしてください。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="549"/>
        <source>No data for this field/frame.</source>
        <translation>このフィールド/フレームにはデータがありません。</translation>
    </message>
</context>
<context>
    <name>Progress</name>
    <message>
        <location filename="../../gui/progress_text.py" line="32"/>
        <source>Preparing: checking the images and building the mesh</source>
        <translation>準備中：画像を確認してメッシュを作成しています</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="35"/>
        <source>Preparing: initial guess for the left camera</source>
        <translation>準備中：左カメラの初期値</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="38"/>
        <source>Preparing: mesh and initial guess for the right camera</source>
        <translation>準備中：右カメラのメッシュと初期値</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="41"/>
        <source>Preparing: estimating the stereo offset</source>
        <translation>準備中：ステレオのずれを推定しています</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="42"/>
        <location filename="../../gui/progress_text.py" line="53"/>
        <source>tracking complete</source>
        <translation>追跡完了</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="45"/>
        <source>normalizing images</source>
        <translation>画像を正規化中</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="48"/>
        <location filename="../../gui/progress_text.py" line="51"/>
        <source>composing displacements</source>
        <translation>変位を合成中</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="52"/>
        <source>assembling results</source>
        <translation>結果を集計中</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="63"/>
        <source>Left camera</source>
        <translation>左カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="65"/>
        <source>Right camera</source>
        <translation>右カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="66"/>
        <source>{0}: {1}</source>
        <translation>{0}：{1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="74"/>
        <source>tracking frame {0} of {1}</source>
        <translation>フレーム {0}/{1} を追跡中</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="84"/>
        <source>verifying frame {0} of {1} (keeping the frames tracked before the stop)</source>
        <translation>フレーム {0}/{1} を検証中（停止前に追跡したフレームを保持）</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="86"/>
        <source>verifying frame {0} of {1}</source>
        <translation>フレーム {0}/{1} を検証中</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="89"/>
        <source>assembling frame {0} of {1}</source>
        <translation>フレーム {0}/{1} を集計中</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="94"/>
        <source>strain: frame {0} of {1}</source>
        <translation>ひずみ：フレーム {0}/{1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="101"/>
        <source>Preparing: matching the two cameras at {0} nodes</source>
        <translation>準備中：{0} 節点で 2 台のカメラを対応付けています</translation>
    </message>
</context>
<context>
    <name>ProgressRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="156"/>
        <source>Cancel</source>
        <translation>キャンセル</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="173"/>
        <source>Exporting…</source>
        <translation>エクスポート中…</translation>
    </message>
</context>
<context>
    <name>ROIToolbar</name>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="75"/>
        <source>+ Add</source>
        <translation>+ 追加</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="78"/>
        <source>Add region to the Region of Interest (Polygon / Rectangle / Circle)</source>
        <translation>関心領域に形状を追加します(多角形 / 矩形 / 円)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="81"/>
        <source>Cut</source>
        <translation>切り取り</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="84"/>
        <source>Cut region from the Region of Interest (Polygon / Rectangle / Circle)</source>
        <translation>関心領域から形状を切り取ります(多角形 / 矩形 / 円)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="87"/>
        <source>+ Refine</source>
        <translation>+ 細分化</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="93"/>
        <source>Paint extra mesh-refinement zones with a brush
(on the LEFT camera, frame 1 — the reference mesh geometry)</source>
        <translation>ブラシで追加の細分化領域を塗ります
（左カメラのフレーム 1 — 参照メッシュ形状）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="110"/>
        <source>Import</source>
        <translation>インポート</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="111"/>
        <source>Import mask from image file</source>
        <translation>画像ファイルからマスクをインポート</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="120"/>
        <source>Save</source>
        <translation>保存</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="121"/>
        <source>Save current mask to PNG file</source>
        <translation>現在のマスクを PNG ファイルに保存</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="126"/>
        <source>Invert</source>
        <translation>反転</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="127"/>
        <source>Invert the Region of Interest mask</source>
        <translation>関心領域マスクを反転</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="132"/>
        <source>Clear</source>
        <translation>クリア</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="133"/>
        <source>Clear all Region of Interest masks</source>
        <translation>すべての関心領域マスクをクリア</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="159"/>
        <source>Polygon</source>
        <translation>多角形</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="163"/>
        <source>Rectangle</source>
        <translation>矩形</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="167"/>
        <source>Circle</source>
        <translation>円</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="171"/>
        <source>Circle (3-point)</source>
        <translation>円（3 点）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="185"/>
        <source>Radius</source>
        <translation>半径</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="202"/>
        <source>Paint</source>
        <translation>塗り</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="206"/>
        <source>Erase</source>
        <translation>消去</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="215"/>
        <source>Clear Brush</source>
        <translation>ブラシをクリア</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="247"/>
        <source>Import Mask Image</source>
        <translation>マスク画像をインポート</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="249"/>
        <source>Images (*.png *.bmp *.tif *.tiff *.jpg *.jpeg);;All Files (*)</source>
        <translation>画像 (*.png *.bmp *.tif *.tiff *.jpg *.jpeg);;すべてのファイル (*)</translation>
    </message>
</context>
<context>
    <name>RefUpdateSection3D</name>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="55"/>
        <source>Reference Update</source>
        <translation>参照フレーム更新</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="60"/>
        <source>Every Frame</source>
        <translation>毎フレーム</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="61"/>
        <source>Every N Frames</source>
        <translation>N フレームごと</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="62"/>
        <source>Custom Frames</source>
        <translation>カスタムフレーム</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="72"/>
        <source>How often the incremental reference frame advances.
Every Frame (default): frame k matches against k−1 — tracks
large accumulated deformation, but drift can accumulate.
Every N Frames: the reference advances only every N frames —
less drift, needs correlation to survive N frames of motion.
Custom Frames: reference updates exactly at the listed frames.</source>
        <translation>逐次モードで参照フレームを進める頻度。
毎フレーム（既定）: フレーム k を k−1 と照合 — 大きな累積変形を
追跡できますが、ドリフトが蓄積します。
N フレームごと: 参照は N フレームごとにのみ進みます — ドリフトは
減りますが、相関が N フレーム分の移動に耐える必要があります。
カスタムフレーム: 指定したフレームでのみ参照を更新します。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="78"/>
        <source>Update every</source>
        <translation>更新間隔</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="85"/>
        <source> frames</source>
        <translation> フレーム</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="88"/>
        <source>Reference-update interval N: frames k use the last reference at i·N &lt; k</source>
        <translation>参照更新間隔 N: フレーム k は i·N &lt; k の最新の参照を使用します</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="93"/>
        <source>e.g. 5, 10, 20 (0-based frame indices)</source>
        <translation>例: 5, 10, 20（0 始まりのフレーム番号）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="100"/>
        <source>Comma-separated 0-based frame indices that become reference
frames (frame 0 always is one). The last frame cannot be a
reference.</source>
        <translation>参照フレームになる 0 始まりのフレーム番号をカンマ区切りで指定します
（フレーム 0 は常に参照です）。最終フレームは参照にできません。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="142"/>
        <source>Enter comma-separated 0-based frame numbers, e.g. 5, 10, 20</source>
        <translation>カンマ区切りの 0 始まりのフレーム番号を入力してください（例: 5, 10, 20）</translation>
    </message>
</context>
<context>
    <name>RightSidebar3D</name>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="99"/>
        <source>Run 3D Analysis</source>
        <translation>3D 解析を実行</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="108"/>
        <location filename="../../gui/panels/right_sidebar.py" line="460"/>
        <source>Run the full stereo correspondence + triangulation pipeline on the loaded image pairs (F5).</source>
        <translation>読み込んだ画像ペアに対してステレオ対応付け＋三角測量のパイプライン全体を実行します（F5）。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="112"/>
        <source>Cancel</source>
        <translation>キャンセル</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="127"/>
        <source>Export Results</source>
        <translation>結果をエクスポート</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="135"/>
        <source>Open Strain Window</source>
        <translation>ひずみウィンドウを開く</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="148"/>
        <source>Parameters changed since this result — re-run to update</source>
        <translation>この結果の後にパラメーターが変更されました — 再実行して更新してください</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="156"/>
        <source>PROGRESS</source>
        <translation>進捗</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="163"/>
        <location filename="../../gui/panels/right_sidebar.py" line="639"/>
        <source>Ready</source>
        <translation>準備完了</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="168"/>
        <source>ELAPSED  --:--</source>
        <translation>経過  --:--</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="171"/>
        <source>REMAINING  --:--</source>
        <translation>残り  --:--</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="177"/>
        <source>FIELD</source>
        <translation>表示項目</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="183"/>
        <source>Show on deformed frame</source>
        <translation>変形後フレームに表示</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="190"/>
        <source>When checked, overlay results on the deformed (current) frame instead of the reference frame</source>
        <translation>オンにすると、結果を参照フレームではなく変形後(現在)フレームに重ねて表示します</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="196"/>
        <source>Camera</source>
        <translation>カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="200"/>
        <source>Left</source>
        <translation>左</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="206"/>
        <source>Show the LEFT camera&apos;s images (the reference view: ROI, seed and mesh live here). Default.</source>
        <translation>左カメラの画像を表示します（参照ビュー: ROI・開始点・メッシュはここに定義されます）。既定。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="207"/>
        <source>Right</source>
        <translation>右</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="213"/>
        <source>Show the RIGHT camera&apos;s images with the field warped onto them — a cross-check that the stereo match is sound.</source>
        <translation>右カメラの画像に、フィールドをワープして重ねて表示します — ステレオマッチングの健全性チェックに使えます。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="226"/>
        <source>VISUALIZATION</source>
        <translation>可視化</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="229"/>
        <source>Colormap</source>
        <translation>カラーマップ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="241"/>
        <source>Colormap for the field overlay and the 3D surface. Default turbo (perceptually ordered, high contrast); pick RdBu_r or coolwarm for signed fields centered on zero.</source>
        <translation>フィールドオーバーレイと 3D 表面のカラーマップ。既定は turbo（知覚的に順序付き、高コントラスト）。ゼロ中心の符号付きフィールドには RdBu_r か coolwarm を選んでください。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="246"/>
        <source>Auto range</source>
        <translation>自動レンジ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="254"/>
        <source>Rescale the color range to each frame&apos;s data range (2–98 percentile of the visible values). Default on; uncheck to type fixed Min/Max bounds that hold across frames.</source>
        <translation>各フレームのデータ範囲に合わせてカラーレンジを再スケールします（可視値の 2–98 パーセンタイル）。既定はオン。オフにすると全フレームで保持される固定の最小/最大値を入力できます。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="262"/>
        <source>Min</source>
        <translation>最小</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="270"/>
        <source>Lower color-range bound (only with Auto range off)</source>
        <translation>カラーレンジの下限（自動範囲がオフのときのみ）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="271"/>
        <source>Upper color-range bound (only with Auto range off)</source>
        <translation>カラーレンジの上限（自動範囲がオフのときのみ）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="277"/>
        <source>Max</source>
        <translation>最大</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="283"/>
        <source>Opacity</source>
        <translation>不透明度</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="290"/>
        <source>Overlay opacity (0 = transparent, 100 = opaque)</source>
        <translation>オーバーレイの不透明度(0 = 透明、100 = 不透明)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="297"/>
        <source>UNITS</source>
        <translation>単位</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="304"/>
        <source>LOG</source>
        <translation>ログ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="313"/>
        <source>All messages</source>
        <translation>すべてのメッセージ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="314"/>
        <source>Info</source>
        <translation>情報</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="315"/>
        <source>Warnings + errors</source>
        <translation>警告とエラー</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="316"/>
        <source>Errors only</source>
        <translation>エラーのみ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="319"/>
        <source>Show only log messages of this severity</source>
        <translation>この重要度のログメッセージのみ表示</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="322"/>
        <source>Save…</source>
        <translation>保存…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="327"/>
        <source>Save the full log to a text file</source>
        <translation>全ログをテキストファイルに保存</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="330"/>
        <source>Clear</source>
        <translation>クリア</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="335"/>
        <source>Clear the log console (messages are not recoverable)</source>
        <translation>ログコンソールをクリアします（メッセージは元に戻せません）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="420"/>
        <source>Save log</source>
        <translation>ログを保存</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="421"/>
        <source>Text files (*.txt)</source>
        <translation>テキストファイル (*.txt)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="431"/>
        <source>Log saved to {0}</source>
        <translation>ログを保存しました：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="453"/>
        <location filename="../../gui/panels/right_sidebar.py" line="469"/>
        <source>Not ready — {0}</source>
        <translation>未準備 — {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="476"/>
        <source>Ready to run. No starting point: the stereo offset is found automatically and frame 1 is seeded by FFT.</source>
        <translation>実行できます。シード点なし：ステレオのずれは自動で求め、フレーム 1 は FFT で初期化します。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="478"/>
        <source>Ready to run.</source>
        <translation>実行できます。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="514"/>
        <source>Export displacement and strain results to NPZ / MAT / CSV</source>
        <translation>変位とひずみ結果を NPZ / MAT / CSV にエクスポート</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="520"/>
        <source>Compute and visualize strain in a separate post-processing window. Requires displacement results from a completed Run.</source>
        <translation>別ウィンドウでひずみを計算・可視化します。完了した実行結果の変位データが必要です。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="524"/>
        <source>Available after the running analysis finishes.</source>
        <translation>実行中の解析が完了すると利用できます。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="526"/>
        <source>Run an analysis first — there are no results yet.</source>
        <translation>まず解析を実行してください — まだ結果がありません。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="543"/>
        <source>Not ready: {0}</source>
        <translation>未準備：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="560"/>
        <source>Starting 3D analysis…</source>
        <translation>3D 解析を開始しています…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="579"/>
        <source>Cancelling — finishing current frame…</source>
        <translation>キャンセル中 — 現在のフレームを処理し終えています…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="580"/>
        <source>Cancelling…</source>
        <translation>キャンセルしています…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="605"/>
        <source>Stopped early — partial results kept</source>
        <translation>早期停止 — 部分的な結果を保持しました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="598"/>
        <source>Analysis complete</source>
        <translation>解析が完了しました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="428"/>
        <location filename="../../gui/panels/right_sidebar.py" line="617"/>
        <source>Failed: {0}</source>
        <translation>失敗：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="122"/>
        <source>Cancel the current analysis. Frames computed so far are kept as a partial result; only when nothing was computed yet does the run return to IDLE.</source>
        <translation>現在の解析をキャンセルします。計算済みのフレームは部分的な結果として保持されます。まだ何も計算されていない場合のみ、実行はアイドル状態に戻ります。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="616"/>
        <source>Analysis failed</source>
        <translation>解析に失敗しました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="621"/>
        <source>Analysis Failed</source>
        <translation>解析に失敗しました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="624"/>
        <source>The analysis stopped with an error:

{0}

The log has the details.</source>
        <translation>解析はエラーで停止しました：

{0}

詳細はログを参照してください。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="642"/>
        <source>Run cancelled</source>
        <translation>実行をキャンセルしました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="557"/>
        <location filename="../../gui/panels/right_sidebar.py" line="640"/>
        <location filename="../../gui/panels/right_sidebar.py" line="649"/>
        <source>ELAPSED  {0}</source>
        <translation>経過  {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="558"/>
        <location filename="../../gui/panels/right_sidebar.py" line="597"/>
        <location filename="../../gui/panels/right_sidebar.py" line="641"/>
        <location filename="../../gui/panels/right_sidebar.py" line="655"/>
        <source>REMAINING  {0}</source>
        <translation>残り  {0}</translation>
    </message>
</context>
<context>
    <name>RigidMotion</name>
    <message>
        <location filename="../../gui/rigid_motion_text.py" line="18"/>
        <source>translation</source>
        <translation>並進</translation>
    </message>
    <message>
        <location filename="../../gui/rigid_motion_text.py" line="20"/>
        <source>translation + rotation</source>
        <translation>並進 + 回転</translation>
    </message>
    <message>
        <location filename="../../gui/rigid_motion_text.py" line="22"/>
        <source>off</source>
        <translation>オフ</translation>
    </message>
    <message>
        <location filename="../../gui/rigid_motion_text.py" line="30"/>
        <source> · rigid motion removed ({0})</source>
        <translation> · 剛体運動を除去（{0}）</translation>
    </message>
</context>
<context>
    <name>RigidMotionPanel3D</name>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="51"/>
        <source>Remove</source>
        <translation>除去</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="55"/>
        <source>Off</source>
        <translation>オフ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="55"/>
        <source>Translation only</source>
        <translation>並進のみ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="55"/>
        <source>Translation + rotation</source>
        <translation>並進 + 回転</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="66"/>
        <source>Remove each frame&apos;s best-fit rigid-body motion (relative to frame 1)
from the displacement everywhere: the field maps, the 3D view,
the strain and every export. Green-Lagrange strain is unchanged
by it; the displacement and the slopes ∂w/∂x, ∂w/∂y are not.</source>
        <translation>各フレーム（フレーム 1 基準）の最適な剛体運動を、
あらゆる箇所の変位から除去します：場の表示、3D ビュー、
ひずみ、すべてのエクスポート。Green-Lagrange ひずみは
変わりませんが、変位と傾き ∂w/∂x、∂w/∂y は変わります。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="80"/>
        <source>+ Rectangle</source>
        <translation>+ 矩形</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="81"/>
        <source>+ Polygon</source>
        <translation>+ 多角形</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="82"/>
        <source>− Rectangle</source>
        <translation>− 矩形</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="83"/>
        <source>− Polygon</source>
        <translation>− 多角形</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="90"/>
        <source>Add an area to the fit region (drawn on frame 1)</source>
        <translation>フィット領域に範囲を追加（フレーム 1 上で描画）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="92"/>
        <source>Remove an area from the fit region</source>
        <translation>フィット領域から範囲を除外</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="98"/>
        <source>Use all valid points</source>
        <translation>すべての有効点を使用</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="100"/>
        <source>Clear the drawn region: fit on every valid point</source>
        <translation>描画した領域を消去：すべての有効点でフィット</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="104"/>
        <source>Show fit region</source>
        <translation>フィット領域を表示</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/rigid_motion_panel.py" line="118"/>
        <source>Per frame: shift of the fitted points&apos; centroid ΔX/ΔY/ΔZ (µm), rotation θ (mrad), fit residual RMS (µm), points used N.</source>
        <translation>フレームごと：フィット点の重心移動 ΔX/ΔY/ΔZ（µm）、回転 θ（mrad）、フィット残差 RMS（µm）、使用点数 N。</translation>
    </message>
</context>
<context>
    <name>RunSummaryMixin</name>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="25"/>
        <source>Analysis complete</source>
        <translation>解析が完了しました</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="43"/>
        <source>Stopped early at frame {0}/{1} — kept {2} computed frames (later frames are empty)</source>
        <translation>フレーム {0}/{1} で早期停止 — 計算済みの {2} フレームを保持しました（以降のフレームは空です）</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="47"/>
        <source>Run interrupted: {0}</source>
        <translation>実行が中断されました: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="51"/>
        <source>Frame-1 stereo match: {0}/{1} points matched ({2}%)</source>
        <translation>第 1 フレームのステレオマッチング: {0}/{1} 点が一致 ({2}%)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="62"/>
        <source>Camera {0}: validity gate removed {1} node-frames (correlation with the reference frame failed)</source>
        <translation>カメラ {0}: 有効性ゲートが {1} 個のノードフレームを除外 (参照フレームとの相関検証に失敗)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="67"/>
        <source>Frame {0}: only {1}% of points valid</source>
        <translation>フレーム {0}: 有効な点は {1}% のみ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="74"/>
        <source>Quality gate (ZNSSD) removed {0} positions</source>
        <translation>品質ゲート (ZNSSD) が {0} 個の位置を除外</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="75"/>
        <source>Reprojection gate removed {0} positions</source>
        <translation>再投影ゲートが {0} 個の位置を除外</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="76"/>
        <source>3D outlier filter removed {0} positions</source>
        <translation>3D 外れ値フィルタが {0} 個の位置を除外</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="91"/>
        <source>Camera {0}: the initial-guess search had to widen on {1} frames (up to {2} px), which slows the run. If the motion between reference frames is that large, raise PARAMETERS &gt; Temporal Search.</source>
        <translation>カメラ {0}：初期推定の探索範囲を {1} フレームで広げる必要がありました（最大 {2} px）。実行が遅くなります。参照フレーム間の動きが実際にこれほど大きい場合は、パラメータ &gt; 時系列探索 を大きくしてください。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="99"/>
        <source>Camera {0}: the initial-guess search had to widen on {1} frames (up to {2} px), which slows the run. In incremental mode this usually means the frame-1 region no longer covers the specimen at later reference frames: import per-frame masks (REGION OF INTEREST) or use WORKFLOW TYPE &gt; Accumulative.</source>
        <translation>カメラ {0}：初期推定の探索範囲を {1} フレームで広げる必要がありました（最大 {2} px）。実行が遅くなります。逐次式では通常、フレーム 1 の領域が後の参照フレームで試験片を覆わなくなったことを意味します：フレームごとのマスクを読み込むか（関心領域）、ワークフロー種別 &gt; 累積式 を使用してください。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="115"/>
        <source>Validity falls from {0}% (frame 1) to {1}%: tracking every frame against frame 1 cannot follow large deformation. Try WORKFLOW TYPE &gt; Incremental.</source>
        <translation>有効率がフレーム 1 の {0}% から {1}% に下がりました：すべてのフレームをフレーム 1 と比べる追跡は大変形に追従できません。ワークフロー種別 &gt; 逐次式 を試してください。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="121"/>
        <source>Validity falls from {0}% (frame 1) to {1}%: the motion between reference frames is too large to track. Update the reference every frame (Reference Update &gt; Every Frame).</source>
        <translation>有効率がフレーム 1 の {0}% から {1}% に下がりました：参照フレーム間の動きが大きすぎて追跡できません。参照フレームを毎フレーム更新してください（参照フレーム更新 &gt; 毎フレーム）。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="127"/>
        <source>Validity falls from {0}% (frame 1) to {1}%: if the valid region changes during the test (cracks, failure), import per-frame masks (REGION OF INTEREST).</source>
        <translation>有効率がフレーム 1 の {0}% から {1}% に下がりました：試験中に有効領域が変わる場合（き裂、破断）は、フレームごとのマスクを読み込んでください（関心領域）。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="133"/>
        <source>No valid points in ANY frame — the run produced an empty result. Check ROI, masks and seeding (details above).</source>
        <translation>どのフレームにも有効な点がありません — 実行結果は空です。ROI・マスク・シード設定を確認してください (詳細は上記)。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="141"/>
        <source>Analysis complete — {0} frames, median validity {1}%, {2} frame(s) below {3}% (see above)</source>
        <translation>解析完了 — {0} フレーム、有効率の中央値 {1}%、{2} フレームが {3}% 未満 (上記参照)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="152"/>
        <source>Analysis complete — {0} frames, median validity {1}%</source>
        <translation>解析が完了しました：{0} フレーム、有効率の中央値 {1}%</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="176"/>
        <source>Stereo check removed {0} links for weak left-right correlation (ZNSSD above {1}) and {2} for epipolar distance (above {3} px).</source>
        <translation>ステレオチェックで、左右の相関が弱い（ZNSSD が {1} を超える）{0} 個の対応と、エピポーラ距離が {3} px を超える {2} 個の対応を除外しました。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="190"/>
        <source>The frame-1 stereo links lie a median {0} px from their epipolar lines: the calibration probably does not match these images (a camera moved, a wrong file, or left and right swapped). Check or redo the calibration.</source>
        <translation>フレーム 1 のステレオ対応はエピポーラ線から中央値 {0} px 離れています：キャリブレーションがこれらの画像と合っていない可能性があります（カメラが動いた、ファイルの取り違え、左右の入れ替わり）。キャリブレーションを確認するかやり直してください。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="198"/>
        <source>Many frame-1 stereo links lie off their epipolar lines: the calibration probably does not match these images (a camera moved, a wrong file, or left and right swapped). Check or redo the calibration.</source>
        <translation>フレーム 1 の多くのステレオ対応がエピポーラ線から外れています：キャリブレーションがこれらの画像と合っていない可能性があります（カメラが動いた、ファイルの取り違え、左右の入れ替わり）。キャリブレーションを確認するかやり直してください。</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="206"/>
        <source>Correct stereo links can correlate weakly on a rough or strongly inclined surface. If points are missing, raise ADVANCED &gt; Result checks &gt; Stereo check (for example to 1.0).</source>
        <translation>粗い面や大きく傾いた面では、正しいステレオ対応でも相関が弱くなることがあります。点が欠ける場合は、詳細設定 &gt; 結果のチェック &gt; ステレオチェック を上げてください（例：1.0）。</translation>
    </message>
</context>
<context>
    <name>RunWarnings</name>
    <message>
        <location filename="../../gui/warning_text.py" line="29"/>
        <source>No Starting Point placed: frame 1 is seeded by an FFT search (place a point for large first-frame motion)</source>
        <translation>シード点なし：フレーム 1 は FFT 探索で初期化されます（最初のフレームの動きが大きい場合は点を配置してください）</translation>
    </message>
    <message>
        <location filename="../../gui/warning_text.py" line="35"/>
        <source>FFT search range reduced from {0} to {1} px to fit the {2} × {3} px images</source>
        <translation>{2} × {3} px の画像に合わせて FFT 探索範囲を {0} px から {1} px に縮小しました</translation>
    </message>
</context>
<context>
    <name>ShortcutsDialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="74"/>
        <source>Keyboard Shortcuts</source>
        <translation>キーボードショートカット</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="86"/>
        <source>Run the 3D analysis</source>
        <translation>3D 解析を実行</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="87"/>
        <source>Fit the image to the viewport</source>
        <translation>画像をビューポートに合わせる</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="88"/>
        <source>Zoom in / out</source>
        <translation>拡大 / 縮小</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="89"/>
        <source>Previous / next frame</source>
        <translation>前のフレーム / 次のフレーム</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="90"/>
        <source>Play / pause (on the canvas: hold to pan)</source>
        <translation>再生 / 一時停止（キャンバス上では長押しでパン）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="91"/>
        <source>New project</source>
        <translation>新規プロジェクト</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="92"/>
        <source>Open a project</source>
        <translation>プロジェクトを開く</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="93"/>
        <source>Save the project</source>
        <translation>プロジェクトを保存</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="94"/>
        <source>Save the project as…</source>
        <translation>プロジェクトに名前を付けて保存…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="95"/>
        <source>Cancel the active drawing tool</source>
        <translation>使用中の描画ツールをキャンセル</translation>
    </message>
</context>
<context>
    <name>StrainFieldSelector3D</name>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="51"/>
        <source>U — displacement along the world X axis (left camera)</source>
        <translation>U — ワールド座標系 X 軸方向の変位（左カメラ）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="52"/>
        <source>V — displacement along the world Y axis (left camera)</source>
        <translation>V — ワールド座標系 Y 軸方向の変位（左カメラ）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="53"/>
        <source>W — displacement along the world Z axis (left camera)</source>
        <translation>W — ワールド座標系 Z 軸方向の変位（左カメラ）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="54"/>
        <source>|D| — displacement magnitude</source>
        <translation>|D| — 変位の大きさ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="55"/>
        <source>∂w/∂x — out-of-plane slope along the strain frame&apos;s x axis</source>
        <translation>∂w/∂x — ひずみ座標系 x 軸方向の面外傾き</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="56"/>
        <source>∂w/∂y — out-of-plane slope along the strain frame&apos;s y axis</source>
        <translation>∂w/∂y — ひずみ座標系 y 軸方向の面外傾き</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="59"/>
        <source>εxx — normal strain along the strain frame&apos;s x axis</source>
        <translation>εxx — ひずみ座標系 x 軸方向の垂直ひずみ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="60"/>
        <source>εyy — normal strain along the strain frame&apos;s y axis</source>
        <translation>εyy — ひずみ座標系 y 軸方向の垂直ひずみ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="61"/>
        <source>εxy — in-plane shear strain (tensor component)</source>
        <translation>εxy — 面内せん断ひずみ（テンソル成分）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="62"/>
        <source>ε₁ — major principal strain (largest in-plane eigenvalue)</source>
        <translation>ε₁ — 最大主ひずみ（面内の最大固有値）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="63"/>
        <source>ε₂ — minor principal strain (smallest in-plane eigenvalue)</source>
        <translation>ε₂ — 最小主ひずみ（面内の最小固有値）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="64"/>
        <source>γ max — maximum shear strain, (ε₁ − ε₂) / 2</source>
        <translation>γ max — 最大せん断ひずみ、(ε₁ − ε₂) / 2</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="65"/>
        <source>von Mises — equivalent strain (plane-stress invariant)</source>
        <translation>von Mises — 相当ひずみ（平面応力不変量）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="71"/>
        <source>Displacement</source>
        <translation>変位</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="72"/>
        <source>Slope</source>
        <translation>傾き</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="73"/>
        <source>Strain</source>
        <translation>ひずみ</translation>
    </message>
</context>
<context>
    <name>StrainNavigator3D</name>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="52"/>
        <source>Previous frame (←)</source>
        <translation>前フレーム (←)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="59"/>
        <location filename="../../gui/widgets/strain_navigator.py" line="128"/>
        <source>Play animation (Space)</source>
        <translation>アニメーションを再生 (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="66"/>
        <source>Next frame (→)</source>
        <translation>次のフレーム (→)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="75"/>
        <source>Playback speed (frames per second). Default 2 fps.</source>
        <translation>再生速度（フレーム/秒）。既定は 2 fps。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="79"/>
        <location filename="../../gui/widgets/strain_navigator.py" line="198"/>
        <source>FRAME 0/0</source>
        <translation>フレーム 0/0</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="181"/>
        <source>Pause animation (Space)</source>
        <translation>アニメーションを一時停止 (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="196"/>
        <source>FRAME {0}/{1}</source>
        <translation>フレーム {0}/{1}</translation>
    </message>
</context>
<context>
    <name>StrainParamPanel3D</name>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="88"/>
        <source>Side length, in pixels, of the square window around each node used to fit the local displacement gradient (the virtual strain gauge).

• Larger window → smoother strain, lower spatial resolution.
• Smaller window → sharper strain, more noise.
• Must span at least 3×3 nodes: use ≥ 2 × node spacing + 1 px.</source>
        <translation>各ノードの周囲で局所変位勾配を当てはめる正方形ウィンドウの一辺の長さ（ピクセル単位、仮想ひずみゲージ）。

• 大きいウィンドウ → ひずみは滑らか、空間分解能は低下。
• 小さいウィンドウ → ひずみは鮮明、ノイズは増加。
• 少なくとも 3×3 ノードを含む必要があります：≥ 2 × ノード間隔 + 1 px を使用してください。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="89"/>
        <source>Strain window</source>
        <translation>VSGウィンドウ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="106"/>
        <source>Number of mesh nodes per axis inside the square strain window — the local plane fit uses every valid node in it. The mm size maps the pixel window through the median 3D spacing of adjacent nodes on the reference surface.</source>
        <translation>正方形のひずみウィンドウ内で各軸方向に含まれるメッシュ節点数 — 局所平面フィットはウィンドウ内のすべての有効節点を使用します。mm サイズは、参照表面上の隣接節点の 3D 間隔の中央値でピクセルウィンドウを換算したものです。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="119"/>
        <source>Green-Lagrange (default)</source>
        <translation>Green-Lagrange（既定）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="120"/>
        <source>Infinitesimal</source>
        <translation>微小ひずみ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="124"/>
        <source>Almansi (Eulerian, true tensor)</source>
        <translation>Almansi（オイラー、真のテンソル）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="138"/>
        <source>Finite-strain measure derived from the SAME displacement-
gradient fit, in the same tangent frame:
Green-Lagrange E = ½(FᵀF − I) — finite strain, reference
configuration (default).
Infinitesimal e = ½(∇u + ∇uᵀ) — small-strain linearization.
Almansi (Eulerian, true tensor) e = ½(I − F⁻ᵀF⁻¹) — the EXACT
finite-strain tensor in the deformed configuration. This is NOT
the 2D app&apos;s linearized per-axis &apos;Eulerian-Almansi&apos; formula
(1/(1−∂u/∂x)−1, …), which differs by ~22% at 10% strain.</source>
        <translation>同じ変位勾配フィットから、同じ接平面座標系で導出される有限ひずみ尺度：
Green-Lagrange E = ½(FᵀF − I) — 参照配置の有限ひずみ（既定）。
Infinitesimal e = ½(∇u + ∇uᵀ) — 微小ひずみ線形化。
Almansi（オイラー、真のテンソル）e = ½(I − F⁻ᵀF⁻¹) — 変形配置における
厳密な有限ひずみテンソル。これは 2D アプリの線形化された軸ごとの
「Euler-Almansi」式（1/(1−∂u/∂x)−1, …）ではなく、10% ひずみで約 22%
異なります。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="139"/>
        <source>Strain type</source>
        <translation>ひずみの種類</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="156"/>
        <source>Hides low-confidence strain near invalid or missing nodes, where
the strain window loses support on one side and the local plane
fit becomes unreliable.
Coefficient × window radius = width of the trimmed band (in px,
on the reference grid).
0.00 = keep every node (no trimming) · 0.70 = recommended ·
1.00 = strictest. Displacement is never affected.</source>
        <translation>無効または欠損した節点付近の低信頼度ひずみを非表示にします。
そこではひずみウィンドウが片側の支持を失い、局所平面フィットが
信頼できなくなります。
係数 × ウィンドウ半径 = 除去される帯の幅（参照グリッド上のピクセル）。
0.00 = すべて保持（除去なし） · 0.70 = 推奨 · 1.00 = 最も厳格。
変位には影響しません。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="161"/>
        <source>Trim low-confidence edges</source>
        <translation>低信頼度のエッジを除去</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="188"/>
        <source>Off</source>
        <translation>オフ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="189"/>
        <source>Light (σ = 0.5 × step)</source>
        <translation>軽度（σ = 0.5 × step）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="190"/>
        <source>Medium (σ = 1 × step)</source>
        <translation>中程度（σ = 1 × step）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="191"/>
        <source>Strong (σ = 2 × step) ⚠</source>
        <translation>強（σ = 2 × step）⚠</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="203"/>
        <source>Gaussian smoothing of the displacement field before the gradient fit.
σ is the kernel width; step = DIC node spacing.
  Light  (0.5 × step): subtle, preserves fine features.
  Medium (1 × step): balanced, for noisy data.
  Strong (2 × step) ⚠: aggressive, may blur real gradients.</source>
        <translation>勾配フィット前に変位場へガウス平滑化を適用します。
σ はカーネル幅、step = DIC ノード間隔。
  軽度（0.5 × step）：控えめ、微細な特徴を保持。
  中程度（1 × step）：バランス型、ノイズの多いデータ向け。
  強（2 × step）⚠：強力、実際の勾配をぼかす恐れ。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="204"/>
        <source>Strain field smoothing</source>
        <translation>ひずみ場の平滑化</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="208"/>
        <source>Surface tangent plane</source>
        <translation>表面接平面</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="209"/>
        <source>Left camera frame</source>
        <translation>左カメラ座標系</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="210"/>
        <source>Custom (3 points)</source>
        <translation>カスタム（3点）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="217"/>
        <source>Per-node tangent plane fitted to the reference surface: z is the surface normal pointing toward the camera, x is the left-camera +X projected onto the plane, y = z × x. The right default for curved specimens.</source>
        <translation>参照曲面にノードごとに当てはめた接平面：z はカメラ側を向く表面法線、x は左カメラ +X の平面への射影、y = z × x。曲面試験片に最適な既定値です。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="221"/>
        <source>Report strain in the fixed left-camera (world) axes. Meaningful for flat specimens aligned with the image plane.</source>
        <translation>固定された左カメラ（世界）座標軸でひずみを報告します。像平面に揃った平板試験片に有効です。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="226"/>
        <source>A fixed specimen frame built from 3 picked points on the reference image: Origin, a point along +X, and a point on the +Y side.</source>
        <translation>参照画像上で選択した 3 点から構築する固定の試験片座標系：原点、+X 方向の点、+Y 側の点。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="241"/>
        <source>Coordinate system</source>
        <translation>座標系</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="246"/>
        <source>Pick 3 points…</source>
        <translation>3点を選択…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="255"/>
        <source>Click three points on the reference image: the Origin, a point along +X, then a point on the +Y side. Each click snaps to the nearest valid mesh node. Enabled only for Custom (3 points).</source>
        <translation>参照画像上で 3 点をクリックします: 原点、+X 方向の点、+Y 側の点。クリックは最も近い有効なメッシュ節点にスナップします。「カスタム（3 点）」でのみ有効です。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="307"/>
        <source>Trimmed: {0} nodes ({1}%)</source>
        <translation>トリミング: {0} ノード ({1}%)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="316"/>
        <source>Crack-aware: ROI barrier honored (mesh, strain, render)</source>
        <translation>亀裂対応：ROI バリアを尊重（メッシュ・ひずみ・描画）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="405"/>
        <source>Strain window ≈ {0}×{1} nodes</source>
        <translation>VSGウィンドウ ≈ {0}×{1} 節点</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="409"/>
        <source>≈ {0} × {1} mm</source>
        <translation>≈ {0} × {1} mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="421"/>
        <source>⚠ Window radius ({0} px) &lt; node spacing ({1} px); the plane fit needs a 3×3 node gauge. Use ≥ {2} px.</source>
        <translation>⚠ ウィンドウ半径（{0} px）&lt; ノード間隔（{1} px）：平面フィットには 3×3 ノードのゲージが必要です。≥ {2} px を使用してください。</translation>
    </message>
</context>
<context>
    <name>StrainRenderMixin</name>
    <message>
        <location filename="../../gui/strain_canvas.py" line="245"/>
        <source>Could not draw the overlay: {0}</source>
        <translation>オーバーレイを描画できませんでした：{0}</translation>
    </message>
</context>
<context>
    <name>StrainRigidMotionMixin</name>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="59"/>
        <source>RIGID MOTION</source>
        <translation>剛体運動</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="82"/>
        <source>Run 3D analysis first — no results to post-process.</source>
        <translation>先に 3D 解析を実行してください — 後処理する結果がありません。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="105"/>
        <source>Rigid motion not removed: {0}</source>
        <translation>剛体運動は除去されていません：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="147"/>
        <source>Fit region: all valid points</source>
        <translation>フィット領域：すべての有効点</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="149"/>
        <source>Fit region: drawn</source>
        <translation>フィット領域：描画済み</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="151"/>
        <source>Fit region: drawn ({0} nodes)</source>
        <translation>フィット領域：描画済み（{0} ノード）</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="154"/>
        <source>Rigid motion is not removed.</source>
        <translation>剛体運動は除去していません。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="157"/>
        <source>Removed ({0}), fitted on {1} points.</source>
        <translation>除去済み（{0}）、{1} 点でフィット。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="163"/>
        <source>the fit region does not cover this run</source>
        <translation>フィット領域がこの解析を覆っていません</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="163"/>
        <source>Not removed: {0}</source>
        <translation>未除去：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="165"/>
        <source>It will be removed once the analysis has run.</source>
        <translation>解析の実行後に除去されます。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="166"/>
        <source>Not fitted on this frame: {0}</source>
        <translation>このフレームはフィットできません：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/strain_rigid_motion.py" line="170"/>
        <source>⚠ Rigid-motion setting changed -- click Compute Strain</source>
        <translation>⚠ 剛体運動の設定が変更されました — 「ひずみを計算」をクリックしてください</translation>
    </message>
</context>
<context>
    <name>StrainVizPanel3D</name>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="35"/>
        <source>Show on deformed frame</source>
        <translation>変形後フレームに表示</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="42"/>
        <source>When checked, overlay results on the deformed (current) frame instead of the reference frame</source>
        <translation>オンにすると、結果を参照フレームではなく変形後(現在)フレームに重ねて表示します</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="52"/>
        <source>Colormap for the strain overlay. Default turbo; pick RdBu_r or coolwarm for signed strain centered on zero.</source>
        <translation>ひずみオーバーレイのカラーマップ。既定は turbo。ゼロ中心の符号付きひずみには RdBu_r か coolwarm を選んでください。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="53"/>
        <source>Colormap</source>
        <translation>カラーマップ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="55"/>
        <source>Auto range</source>
        <translation>自動レンジ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="63"/>
        <source>Rescale the color range to each frame&apos;s data range (2–98 percentile of the visible values). Default on; uncheck to type fixed Min/Max bounds that hold across frames.</source>
        <translation>各フレームのデータ範囲に合わせてカラーレンジを再スケールします（可視値の 2–98 パーセンタイル）。既定はオン。オフにすると全フレームで保持される固定の最小/最大値を入力できます。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="74"/>
        <source>Lower color-range bound (only with Auto range off)</source>
        <translation>カラーレンジの下限（自動範囲がオフのときのみ）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="75"/>
        <source>Upper color-range bound (only with Auto range off)</source>
        <translation>カラーレンジの上限（自動範囲がオフのときのみ）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="82"/>
        <source>Min</source>
        <translation>最小</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="84"/>
        <source>Max</source>
        <translation>最大</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="93"/>
        <source>Overlay opacity (0 = transparent, 100 = opaque)</source>
        <translation>オーバーレイの不透明度(0 = 透明、100 = 不透明)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="94"/>
        <source>Opacity</source>
        <translation>不透明度</translation>
    </message>
</context>
<context>
    <name>StrainWindow3D</name>
    <message>
        <location filename="../../gui/strain_window.py" line="115"/>
        <source>Strain Post-Processing</source>
        <translation>ひずみ後処理</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="156"/>
        <source>STRAIN PARAMETERS</source>
        <translation>ひずみパラメータ</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="166"/>
        <source>Compute Strain</source>
        <translation>ひずみを計算</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="172"/>
        <source>Export Results</source>
        <translation>結果をエクスポート</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="177"/>
        <location filename="../../gui/strain_window.py" line="695"/>
        <source>Export displacement and strain results to NPZ / MAT / CSV</source>
        <translation>変位とひずみ結果を NPZ / MAT / CSV にエクスポート</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="195"/>
        <source>Cancel</source>
        <translation>キャンセル</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="197"/>
        <source>Stop the strain computation at the next frame.</source>
        <translation>次のフレームでひずみ計算を停止します。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="206"/>
        <source>FIELD</source>
        <translation>表示項目</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="212"/>
        <source>VISUALIZATION</source>
        <translation>可視化</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="216"/>
        <source>LOG</source>
        <translation>ログ</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="339"/>
        <source>Computation Running</source>
        <translation>計算を実行中</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="340"/>
        <source>A strain computation is running — cancel it and close?</source>
        <translation>ひずみ計算が実行中です — キャンセルして閉じますか？</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="345"/>
        <source>Yes</source>
        <translation>はい</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="346"/>
        <source>No</source>
        <translation>いいえ</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="406"/>
        <location filename="../../gui/strain_window.py" line="473"/>
        <location filename="../../gui/strain_window.py" line="588"/>
        <source>Strain compute failed: {0}</source>
        <translation>ひずみ計算に失敗しました：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="418"/>
        <location filename="../../gui/strain_window.py" line="550"/>
        <source>Run 3D analysis first — no results to post-process.</source>
        <translation>先に 3D 解析を実行してください — 後処理する結果がありません。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="421"/>
        <location filename="../../gui/strain_window.py" line="562"/>
        <location filename="../../gui/strain_window.py" line="591"/>
        <source>Click Origin, then +X, then +Y on the image</source>
        <translation>画像上で原点、+X、+Y の順にクリックしてください</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="429"/>
        <source>Computing strain…</source>
        <translation>ひずみを計算中…</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="446"/>
        <source>Cancelling…</source>
        <translation>キャンセルしています…</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="451"/>
        <source>Computing strain… {0}%</source>
        <translation>ひずみを計算中… {0}%</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="464"/>
        <source>Complete</source>
        <translation>完了</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="478"/>
        <source>Strain computation cancelled.</source>
        <translation>ひずみ計算をキャンセルしました。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="483"/>
        <source>Strain computation complete.</source>
        <translation>ひずみ計算が完了しました。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="488"/>
        <source>⚠ Params changed -- click Compute Strain</source>
        <translation>⚠ パラメータが変更されました — 「ひずみを計算」をクリックしてください</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="574"/>
        <source>No valid point near the click — pick on the result field</source>
        <translation>クリック位置の近くに有効な点がありません — 結果の場の上で選んでください</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="581"/>
        <location filename="../../gui/strain_window.py" line="598"/>
        <source>Picked {0}/3 points</source>
        <translation>{0}/3 点を選択済み</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="600"/>
        <source>x→{0}  y→{1}  z→{2}</source>
        <translation>x→{0}  y→{1}  z→{2}</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="611"/>
        <source>O</source>
        <translation>O</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="611"/>
        <source>+X</source>
        <translation>+X</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="611"/>
        <source>+Y</source>
        <translation>+Y</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="680"/>
        <source>Run a 3D analysis first — strain needs displacement results.</source>
        <translation>まず 3D 解析を実行してください — ひずみには変位結果が必要です。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="684"/>
        <source>Pick the 3 specimen-frame points first (Origin, +X, +Y).</source>
        <translation>まず試料座標系の 3 点（原点、+X、+Y）を選んでください。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="691"/>
        <source>Compute Green-Lagrange surface strain from the displacement field with the parameters above.</source>
        <translation>上のパラメーターで変位場から Green-Lagrange 表面ひずみを計算します。</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="699"/>
        <source>Run an analysis first — there are no results yet.</source>
        <translation>まず解析を実行してください — まだ結果がありません。</translation>
    </message>
</context>
<context>
    <name>UnitsSection3D</name>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="41"/>
        <source>Display unit for displacement and velocity values (colorbar,
3D scalar bar). Display only — the data and every export stay
in millimetres. Strain is dimensionless and unaffected.</source>
        <translation>変位・速度値の表示単位（カラーバー、3D スカラーバー）。
表示のみに適用 — データとすべてのエクスポートはミリメートルの
ままです。ひずみは無次元で影響を受けません。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="42"/>
        <source>Display unit</source>
        <translation>表示単位</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="49"/>
        <source>not set (per frame)</source>
        <translation>未設定（フレームあたり）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="59"/>
        <source>Acquisition frame rate. Used only by the Velocity field:
velocity = |D(k) − D(k−1)| × frame rate, shown in the
display unit per second. Leave it at &apos;not set&apos; to see the
velocity per frame.</source>
        <translation>撮影フレームレート。速度場だけに使います：
速度 = |D(k) − D(k−1)| × フレームレート（表示単位/秒）。
「未設定」のままにすると、速度を
フレームあたりで表示します。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="60"/>
        <source>Frame rate</source>
        <translation>フレームレート</translation>
    </message>
</context>
<context>
    <name>View3D</name>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="157"/>
        <source>3D view — run an analysis to see the reconstructed surface.</source>
        <translation>3D ビュー — 解析を実行すると再構成曲面が表示されます。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="226"/>
        <location filename="../../gui/widgets/view3d.py" line="362"/>
        <source>3D view unavailable: {0}</source>
        <translation>3D ビューを利用できません：{0}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="310"/>
        <source>Starting the 3D view…</source>
        <translation>3D ビューを起動しています…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="367"/>
        <source>No valid 3D points in this frame — nothing to display.</source>
        <translation>このフレームに有効な 3D 点がありません — 表示できる内容がありません。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="409"/>
        <source>Save 3D view image</source>
        <translation>3D ビュー画像を保存</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="411"/>
        <source>PNG image (*.png)</source>
        <translation>PNG 画像 (*.png)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="419"/>
        <source>Could not save the image: {0}</source>
        <translation>画像を保存できませんでした：{0}</translation>
    </message>
</context>
<context>
    <name>View3DTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="76"/>
        <source>Field</source>
        <translation>フィールド</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="88"/>
        <source>Colormap</source>
        <translation>カラーマップ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="97"/>
        <source>Resolution</source>
        <translation>解像度</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="110"/>
        <source>Auto range</source>
        <translation>自動レンジ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="116"/>
        <source>Like the 3D view: each frame&apos;s 2–98 percentile of the values inside the ROI. Untick to use a fixed Min/Max for every frame.</source>
        <translation>3D ビューと同じく、各フレームで ROI 内の値の 2–98 パーセンタイルを使用します。オフにすると全フレームで固定の最小/最大値を使用します。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="120"/>
        <source>Min</source>
        <translation>最小</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="126"/>
        <source>Max</source>
        <translation>最大</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="139"/>
        <source>Frame sequence</source>
        <translation>フレームシーケンス</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="142"/>
        <source>Per-frame image sequence (PNG)</source>
        <translation>フレームごとの画像シーケンス（PNG）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="147"/>
        <source>Animation</source>
        <translation>アニメーション</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="154"/>
        <source>Frames per second</source>
        <translation>毎秒フレーム数</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="161"/>
        <source>Frame step</source>
        <translation>フレーム間引き</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="175"/>
        <source>Turntable</source>
        <translation>ターンテーブル</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="180"/>
        <source>Turntable (360° orbit at frame {0})</source>
        <translation>ターンテーブル（フレーム {0} で 360° 周回）</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="183"/>
        <source>Orbit frames</source>
        <translation>周回フレーム数</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="208"/>
        <source>Export 3D View</source>
        <translation>3D ビューをエクスポート</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="268"/>
        <source>GIF timing has 1/100 s steps: {0} fps will play at {1} fps. Choose MP4 for faster playback.</source>
        <translation>GIF のフレーム間隔は 1/100 秒単位です：{0} fps は {1} fps で再生されます。より速い再生には MP4 を選択してください。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="279"/>
        <source>Choose an output folder first.</source>
        <translation>先に出力フォルダを選択してください。</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="285"/>
        <source>Nothing selected to export.</source>
        <translation>エクスポートする項目が選択されていません。</translation>
    </message>
</context>
<context>
    <name>View3DToolbar</name>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="54"/>
        <source>Reset</source>
        <translation>リセット</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="54"/>
        <source>Back to the view from the left camera, framed</source>
        <translation>左カメラからの視点に戻して全体を表示</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="55"/>
        <source>Camera</source>
        <translation>カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="55"/>
        <source>Look from the left camera (as in the images)</source>
        <translation>左カメラから見る（画像と同じ向き）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="56"/>
        <source>Normal</source>
        <translation>正面</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="56"/>
        <source>Look straight at the specimen surface</source>
        <translation>試験片の表面を真正面から見る</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="57"/>
        <source>Side</source>
        <translation>側面</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="57"/>
        <source>Edge-on: the out-of-plane profile</source>
        <translation>真横から：面外の輪郭</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="58"/>
        <source>Iso</source>
        <translation>等角</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="58"/>
        <source>Oblique view of the specimen</source>
        <translation>試験片の斜め方向からのビュー</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="67"/>
        <source>Save image…</source>
        <translation>画像を保存…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="68"/>
        <source>Save the 3D view as a PNG image</source>
        <translation>3D ビューを PNG 画像として保存</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="76"/>
        <source>Deformation ×</source>
        <translation>変形倍率 ×</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="86"/>
        <source>Exaggerate the displacement in the 3D geometry (reference shape plus
factor × displacement) so a micron-scale change is visible. The
colours always show the true values.</source>
        <translation>3D 形状の変位を誇張します（参照形状 +
倍率 × 変位）。ミクロン単位の変化も見えます。
色は常に実際の値を表します。</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="91"/>
        <source>Auto</source>
        <translation>自動</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="92"/>
        <source>Pick a factor that makes the change visible</source>
        <translation>変化が見える倍率を自動で選ぶ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="97"/>
        <source>Out-of-plane only</source>
        <translation>面外のみ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="101"/>
        <source>Exaggerate only the displacement along the specimen normal
(in-plane noise stays at true scale)</source>
        <translation>試験片の法線方向の変位だけを誇張
（面内のノイズは実寸のまま）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="105"/>
        <source>Reference shape</source>
        <translation>参照形状</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="105"/>
        <source>Show the frame-1 surface as a wireframe</source>
        <translation>フレーム 1 の表面をワイヤーフレームで表示</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="108"/>
        <source>Cameras</source>
        <translation>カメラ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="108"/>
        <source>Show the two camera frusta (zooms the view out)</source>
        <translation>2 台のカメラの視錐台を表示（ビューが縮小）</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="111"/>
        <source>Shading</source>
        <translation>陰影</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d_toolbar.py" line="112"/>
        <source>Light the surface so its shape reads; off shows the exact colormap colours</source>
        <translation>表面に光を当てて形を見やすく。オフで色マップの正確な色</translation>
    </message>
</context>
<context>
    <name>ZoomBar</name>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="81"/>
        <source>Fit</source>
        <extracomment>The rigid-motion fit region&apos;s fill (amber), distinct from the blue ROI.</extracomment>
        <translation>フィット</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="82"/>
        <source>Fit image to viewport</source>
        <translation>画像をビューポートに合わせる</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="92"/>
        <source>Current zoom — click to reset to 100% (1:1 pixels).
Wheel: zoom · Right/middle drag: pan · Space: pan mode</source>
        <translation>現在のズーム — クリックで 100%（1:1 ピクセル）に戻します。
ホイール: ズーム · 右/中ドラッグ: パン · スペース: パンモード</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="95"/>
        <source>Zoom in</source>
        <translation>拡大</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="99"/>
        <source>Zoom out</source>
        <translation>縮小</translation>
    </message>
</context>
<context>
    <name>dialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="24"/>
        <source>Close</source>
        <translation>閉じる</translation>
    </message>
</context>
</TS>
