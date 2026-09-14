<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="sd_PK">
<context>
    <name>AboutDialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="36"/>
        <source>About pyALDIC-3D</source>
        <translation>Über pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="47"/>
        <source>Version {0}</source>
        <translation>Version {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="52"/>
        <source>Stereo (3D) digital image correlation — full-field displacement and surface strain from a calibrated camera pair.</source>
        <translation>Stereo-(3D-)digitale Bildkorrelation — vollflächige Verschiebungen und Oberflächendehnungen aus einem kalibrierten Kamerapaar.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="63"/>
        <source>Citation: Zenodo DOI pending release.</source>
        <translation>Zitation: Zenodo-DOI folgt mit der Veröffentlichung.</translation>
    </message>
</context>
<context>
    <name>AdvancedSection3D</name>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="38"/>
        <source>Track Both</source>
        <translation>Beide Kameras verfolgen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="39"/>
        <source>Stereo Each Frame</source>
        <translation>Stereo je Frame</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="40"/>
        <source>Reference Direct</source>
        <translation>Referenz direkt</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="43"/>
        <source>How stereo correspondences are propagated through time.
Track Both (default): match stereo once at frame 1, then
track each camera temporally — fastest, one stereo solve.
Stereo Each Frame: re-match stereo at every frame — robust
when temporal tracking drifts, slower.
Reference Direct: match every frame directly to frame 1 in
both cameras — no drift accumulation, small motions only.</source>
        <translation>Wie Stereokorrespondenzen über die Zeit fortgeführt werden.
Beide Kameras verfolgen (Standard): Stereo nur bei Frame 1 abgleichen, danach jede Kamera zeitlich verfolgen — am schnellsten, ein Stereoabgleich.
Stereo je Frame: Stereo in jedem Frame neu abgleichen — robust, wenn die zeitliche Verfolgung driftet, langsamer.
Referenz direkt: jeden Frame in beiden Kameras direkt mit Frame 1 abgleichen — keine Driftakkumulation, nur kleine Bewegungen.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="52"/>
        <source>Strategy</source>
        <translation>Strategie</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="59"/>
        <source>1 = single global pass (fastest), 3 = default, 5+ = diminishing returns</source>
        <translation>1 = einmaliger Durchlauf (schnellste), 3 = Standard, 5+ = abnehmender Ertrag</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="61"/>
        <source>AL-DIC Iterations</source>
        <translation>AL-DIC-Iterationen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="63"/>
        <source>Only affects AL-DIC solver. Ignored by Local DIC.</source>
        <translation>Betrifft nur den AL-DIC-Löser. Wird von Local DIC ignoriert.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="69"/>
        <source>Parallel camera tracking</source>
        <translation>Paralleles Kamera-Tracking</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="72"/>
        <source>Track both cameras concurrently — modest speedup (the solver already uses all cores), doubles peak memory</source>
        <translation>Beide Kameras gleichzeitig verfolgen — begrenzter Gewinn (der Löser nutzt bereits alle Kerne), doppelter Spitzenspeicher</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="79"/>
        <source>Auto-expand FFT search on clipped peaks</source>
        <translation>FFT-Suche bei abgeschnittenen Peaks automatisch erweitern</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="83"/>
        <source>When the temporal FFT integer peak lands on the search-region
boundary, retry with a larger region (engine default on).
Disable for strictly bounded runtimes; then Temporal Search
must cover the largest per-frame motion by itself.</source>
        <translation>Landet der ganzzahlige FFT-Peak auf dem Rand des Suchbereichs,
wird mit größerem Bereich erneut gesucht (Engine-Standard: an).
Für strikt begrenzte Laufzeiten deaktivieren; dann muss die
zeitliche Suche die größte Bewegung pro Frame selbst abdecken.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="92"/>
        <source>Result checks</source>
        <translation>Ergebnisprüfungen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="100"/>
        <source>Tracking check: every tracked point must still look like its
frame-1 subset (correlation mismatch, 0 = perfect, 4 = worst).
Points below 60 % of this value always pass; points up to it
pass when their neighbours agree; the rest are dropped as
failed tracks. Default 1.0 (correlation 0.5). Raise it (e.g.
1.5) for very large strains, lower it for stricter results;
0 turns the check off.</source>
        <translation>Verfolgungsprüfung: Jeder verfolgte Punkt muss seiner Teilmenge
aus Bild 1 noch ähneln (Korrelationsabweichung, 0 = perfekt, 4 = schlechtest).
Punkte unter 60 % dieses Werts bestehen immer; Punkte bis zu ihm
bestehen, wenn ihre Nachbarn übereinstimmen; der Rest wird als
fehlgeschlagene Spur verworfen. Standard 1.0 (Korrelation 0,5).
Für sehr große Dehnungen erhöhen (z. B. 1,5), für strengere
Ergebnisse senken; 0 schaltet die Prüfung aus.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="109"/>
        <source>Tracking check</source>
        <translation>Verfolgungsprüfung</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="114"/>
        <source>Stereo check: a left/right match is kept only if its
correlation mismatch is at most this value. Default 0.6
(correlation 0.7); 0 turns the check off.</source>
        <translation>Stereoprüfung: Eine Links-rechts-Zuordnung bleibt nur, wenn ihre
Korrelationsabweichung höchstens diesen Wert hat. Standard 0.6
(Korrelation 0,7); 0 schaltet die Prüfung aus.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="119"/>
        <source>Stereo check</source>
        <translation>Stereoprüfung</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="124"/>
        <source>Epipolar limit: a left/right match must lie within this many
pixels of the line the calibration predicts. Default 2 px;
raise it only for a poor calibration; 0 turns the check off.</source>
        <translation>Epipolargrenze: Eine Links-rechts-Zuordnung muss höchstens so viele
Pixel von der Linie liegen, die die Kalibrierung vorhersagt. Standard 2 px;
nur bei schlechter Kalibrierung erhöhen; 0 schaltet die Prüfung aus.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="130"/>
        <source>Epipolar limit</source>
        <translation>Epipolargrenze</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="140"/>
        <source>off</source>
        <translation>aus</translation>
    </message>
</context>
<context>
    <name>AnimationTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="57"/>
        <source>Fields</source>
        <translation>Felder</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="77"/>
        <source>Format</source>
        <translation>Format</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="84"/>
        <source>Frames per second</source>
        <translation>Bilder pro Sekunde</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="91"/>
        <source>Frame step</source>
        <translation>Bildschritt</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="92"/>
        <source>Keep every Nth frame (1 = all)</source>
        <translation>Nur jedes N-te Bild behalten (1 = alle)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="99"/>
        <source>Resolution (long edge)</source>
        <translation>Auflösung (lange Kante)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="119"/>
        <source>Include colorbar</source>
        <translation>Farbleiste einfügen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="124"/>
        <source>Background</source>
        <translation>Hintergrund</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="138"/>
        <source>Export Animation</source>
        <translation>Animation exportieren</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="149"/>
        <source>Load an image sequence first (open the project in the main window).</source>
        <translation>Zuerst eine Bildsequenz laden (Projekt im Hauptfenster öffnen).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="158"/>
        <source>GIF timing has 1/100 s steps: {0} fps will play at {1} fps. Choose MP4 for faster playback.</source>
        <translation>GIF-Bildzeiten haben 1/100-s-Schritte: {0} fps werden mit {1} fps abgespielt. Für schnellere Wiedergabe MP4 wählen.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="178"/>
        <source>Choose an output folder first.</source>
        <translation>Bitte zuerst einen Ausgabeordner wählen.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="182"/>
        <source>No fields enabled.</source>
        <translation>Keine Felder aktiviert.</translation>
    </message>
</context>
<context>
    <name>Application</name>
    <message>
        <location filename="../../gui/app.py" line="288"/>
        <source>pyALDIC-3D has hit an error</source>
        <translation>pyALDIC-3D ist auf einen Fehler gestoßen</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="289"/>
        <source>An unexpected error occurred. The application may not behave correctly from here on, so saving your project and restarting is recommended.</source>
        <translation>Ein unerwarteter Fehler ist aufgetreten. Die Anwendung verhält sich möglicherweise nicht mehr korrekt; es wird empfohlen, das Projekt zu speichern und die Anwendung neu zu starten.</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="299"/>
        <source>Details were written to {0}</source>
        <translation>Details wurden in {0} gespeichert</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="348"/>
        <source>Preparing compute kernels in the background…</source>
        <translation>Rechenkernel werden im Hintergrund vorbereitet…</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="361"/>
        <source>Compute kernels ready ({0} s).</source>
        <translation>Rechenkernel bereit ({0} s).</translation>
    </message>
</context>
<context>
    <name>BackgroundRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="638"/>
        <source>Original (frame 1 background)</source>
        <translation>Original (Bild 1 als Hintergrund)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="639"/>
        <source>Deformed (current frame background)</source>
        <translation>Verformt (aktuelles Bild als Hintergrund)</translation>
    </message>
</context>
<context>
    <name>CalibrationDialog</name>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="92"/>
        <source>Stereo Calibration</source>
        <translation>Stereokalibrierung</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="131"/>
        <source>CALIBRATION IMAGE PAIRS</source>
        <translation>KALIBRIERBILDPAARE</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="134"/>
        <source>Add left images…</source>
        <translation>Linke Bilder hinzufügen…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="136"/>
        <source>Add right images…</source>
        <translation>Rechte Bilder hinzufügen…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="138"/>
        <source>Clear</source>
        <translation>Leeren</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="140"/>
        <source>Save detections…</source>
        <translation>Detektionen speichern…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="143"/>
        <source>Load detections…</source>
        <translation>Detektionen laden…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="150"/>
        <source>No images loaded</source>
        <translation>Keine Bilder geladen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="158"/>
        <source>Left</source>
        <translation>Links</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="159"/>
        <source>Right</source>
        <translation>Rechts</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="160"/>
        <source>Points</source>
        <translation>Punkte</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="161"/>
        <source>RMS L/R</source>
        <translation>RMS L/R</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="162"/>
        <source>Max E</source>
        <translation>Max. Fehler</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="163"/>
        <source>Status</source>
        <translation>Status</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="174"/>
        <source>SELECTED PAIR (L | R)</source>
        <translation>AUSGEWÄHLTES PAAR (L | R)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="175"/>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="408"/>
        <source>select a pair to preview detected points</source>
        <translation>Paar auswählen, um erkannte Punkte anzuzeigen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="182"/>
        <source>Click to enlarge the annotated detection</source>
        <translation>Klicken, um die annotierte Detektion zu vergrößern</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="186"/>
        <source>PER-PAIR REPROJECTION ERROR</source>
        <translation>REPROJEKTIONSFEHLER PRO PAAR</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="191"/>
        <source>Reject threshold (px)</source>
        <translation>Ausschlussschwelle (px)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="200"/>
        <source>Recalibrate</source>
        <translation>Neu kalibrieren</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="212"/>
        <source>CALIBRATION BOARD</source>
        <translation>KALIBRIERTAFEL</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="220"/>
        <source>Chessboard</source>
        <translation>Schachbrett</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="221"/>
        <source>ChArUco</source>
        <translation>ChArUco</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="222"/>
        <source>Circle grid</source>
        <translation>Punktraster</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="223"/>
        <source>Coded dot target (3 ring markers)</source>
        <translation>Codiertes Punktziel (3 Ringmarker)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="225"/>
        <source>Type</source>
        <translation>Typ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="230"/>
        <source>Columns x Rows</source>
        <translation>Spalten × Zeilen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="237"/>
        <source>Square size (mm)</source>
        <translation>Quadratgröße (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="242"/>
        <source>Marker size (mm)</source>
        <translation>Markergröße (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="247"/>
        <source>Dot pitch (mm)</source>
        <translation>Punktabstand (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="252"/>
        <source>Dot diameter (mm)</source>
        <translation>Punktdurchmesser (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="256"/>
        <source>Asymmetric grid</source>
        <translation>Asymmetrisches Raster</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="258"/>
        <source>Board printed with OpenCV &lt; 4.7</source>
        <translation>Mit OpenCV &lt; 4.7 gedruckte Tafel</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="262"/>
        <source>Print board… (1:1 PDF)</source>
        <translation>Tafel drucken… (1:1-PDF)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="266"/>
        <source>SOLVER OPTIONS</source>
        <translation>SOLVER-OPTIONEN</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="267"/>
        <source>Jointly refine intrinsics (advanced)</source>
        <translation>Intrinsik gemeinsam verfeinern (erweitert)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="268"/>
        <source>Estimate tangential distortion p1/p2</source>
        <translation>Tangentiale Verzeichnung p1/p2 schätzen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="269"/>
        <source>Fix k3 = 0 (low-distortion lens)</source>
        <translation>k3 = 0 fixieren (verzeichnungsarmes Objektiv)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="270"/>
        <source>Release-object method (printed boards)</source>
        <translation>Release-Object-Methode (gedruckte Tafeln)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="271"/>
        <source>Dot eccentricity correction</source>
        <translation>Exzentrizitätskorrektur der Punkte</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="273"/>
        <source>Joint bundle adjustment (robust, uses mono views)</source>
        <translation>Bündelausgleich (robust, nutzt Mono-Ansichten)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="274"/>
        <source>Optimize board shape (printed boards)</source>
        <translation>Tafelform optimieren (gedruckte Tafeln)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="289"/>
        <source>Calibrate</source>
        <translation>Kalibrieren</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="300"/>
        <source>RESULT</source>
        <translation>ERGEBNIS</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="301"/>
        <source>No calibration yet</source>
        <translation>Noch keine Kalibrierung</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="306"/>
        <source>Verify with board images…</source>
        <translation>Mit Tafelbildern verifizieren…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="318"/>
        <source>Accept &amp;&amp; Save…</source>
        <translation>Übernehmen &amp;&amp; Speichern…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="324"/>
        <source>Cancel</source>
        <translation>Abbrechen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="383"/>
        <source>Choose {0} calibration images</source>
        <translation>{0}-Kalibrierbilder wählen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="385"/>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="717"/>
        <source>Images (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)</source>
        <translation>Bilder (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="430"/>
        <source>{0} left / {1} right images</source>
        <translation>{0} linke / {1} rechte Bilder</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="440"/>
        <source>Load equal, &gt;= 3 left/right image sets first.</source>
        <translation>Zuerst gleich viele (mind. 3) linke/rechte Bilder laden.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="471"/>
        <source>Working… {0}</source>
        <translation>Arbeitet… {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="480"/>
        <source>Calibration failed: {0}</source>
        <translation>Kalibrierung fehlgeschlagen: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="505"/>
        <source>used</source>
        <translation>verwendet</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="507"/>
        <source>L: {0}</source>
        <translation>L: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="509"/>
        <source>R: {0}</source>
        <translation>R: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="525"/>
        <source>Stereo RMS {0:.3f} px | epipolar {1:.3f} px</source>
        <translation>Stereo-RMS {0:.3f} px | epipolar {1:.3f} px</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="528"/>
        <source>Baseline {0:.2f} mm | pairs {1}/{2}</source>
        <translation>Basislinie {0:.2f} mm | Paare {1}/{2}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="531"/>
        <source>fx {0:.1f}  fy {1:.1f}  cx {2:.1f}  cy {3:.1f}</source>
        <translation>fx {0:.1f}  fy {1:.1f}  cx {2:.1f}  cy {3:.1f}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="534"/>
        <source>Coverage L {0:.0%} / R {1:.0%} | tilt {2:.0f}-{3:.0f}°</source>
        <translation>Abdeckung L {0:.0%} / R {1:.0%} | Neigung {2:.0f}-{3:.0f}°</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="543"/>
        <source>Bundle adjustment: RMS {0:.3f} -&gt; {1:.3f} px ({2:.0f} mono views)</source>
        <translation>Bündelausgleich: RMS {0:.3f} -&gt; {1:.3f} px ({2:.0f} Mono-Ansichten)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="549"/>
        <source>Board flatness: z-range {0:.3f} mm</source>
        <translation>Tafelebenheit: z-Bereich {0:.3f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="552"/>
        <source>Warning: {0}</source>
        <translation>Warnung: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="690"/>
        <source>Save board PDF</source>
        <translation>Tafel-PDF speichern</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="692"/>
        <source>PDF (*.pdf)</source>
        <translation>PDF (*.pdf)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="703"/>
        <source>Board PDF written: {0}</source>
        <translation>Tafel-PDF geschrieben: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="719"/>
        <source>Choose LEFT verification image</source>
        <translation>LINKES Verifikationsbild wählen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="724"/>
        <source>Choose RIGHT verification image</source>
        <translation>RECHTES Verifikationsbild wählen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="733"/>
        <source>Verification failed: {0}</source>
        <translation>Verifikation fehlgeschlagen: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="739"/>
        <source>Verify: pitch {0:.4f} mm vs {1:g} mm — scale error {2:.3%}, plane RMS {3:.4f} mm</source>
        <translation>Verifikation: Abstand {0:.4f} mm vs. {1:g} mm — Skalenfehler {2:.3%}, Ebenen-RMS {3:.4f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="753"/>
        <source>Save calibration as</source>
        <translation>Kalibrierung speichern unter</translation>
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
        <location filename="../../gui/calibration_findings.py" line="49"/>
        <source>Camera {0}: the board reached {1:.0%} of the image-corner radius. Beyond it the lens model is a guess: two equally good fits differ by up to {2:.2f} px there. Add views with the board near the image corners, keep the region of interest inside the covered area, or fix k3 for a low-distortion lens.</source>
        <translation>Kamera {0}: Die Tafel reichte bis {1:.0%} des Bildeckenradius. Darüber hinaus ist das Objektivmodell geraten: Zwei gleich gute Anpassungen weichen dort um bis zu {2:.2f} px ab. Fügen Sie Ansichten mit der Tafel nahe den Bildecken hinzu, halten Sie den interessierenden Bereich im abgedeckten Gebiet oder fixieren Sie k3 bei einem verzeichnungsarmen Objektiv.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="57"/>
        <source>Camera {0}: the board reached {1:.0%} of the image-corner radius; the lens model is fitted only inside that radius.</source>
        <translation>Kamera {0}: Die Tafel reichte bis {1:.0%} des Bildeckenradius; das Objektivmodell ist nur innerhalb dieses Radius angepasst.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="40"/>
        <source>Camera {0}: the board reached {1:.0%} of the image-corner radius. Beyond it the lens model is a guess: two equally good fits differ by up to {2:.2f} px there. With k3 fixed, the corners are right only if the lens has no k3 distortion: add views with the board near the image corners, or keep the region of interest inside the covered area.</source>
        <translation>Kamera {0}: Die Tafel reichte bis {1:.0%} des Bildeckenradius. Darüber hinaus ist das Objektivmodell geraten: Zwei gleich gute Anpassungen weichen dort um bis zu {2:.2f} px ab. Mit fixiertem k3 stimmen die Ecken nur, wenn das Objektiv keine k3-Verzeichnung hat: Fügen Sie Ansichten mit der Tafel nahe den Bildecken hinzu oder halten Sie den interessierenden Bereich im abgedeckten Gebiet.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="63"/>
        <source>Camera {0}: the residuals follow a pattern the lens model does not explain (binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model fits), although the board shape is already optimised. A lens the model cannot describe, a board that bends differently from view to view, or detector bias can cause this.</source>
        <translation>Kamera {0}: Die Residuen folgen einem Muster, das das Objektivmodell nicht erklärt (Zellenüberschuss {1:.1f}, angepasstes Feld {2:.1f} × Rauschen; etwa 1, wenn das Modell passt), obwohl die Tafelform bereits optimiert ist. Ursachen können ein Objektiv sein, das das Modell nicht beschreibt, eine Tafel, die sich von Ansicht zu Ansicht anders biegt, oder ein Detektorfehler.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="72"/>
        <source>Camera {0}: the residuals follow a pattern the lens model does not explain (binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model fits). Often the board is the cause (not flat, or its points not exactly where the board description puts them): tick Joint bundle adjustment and Optimize board shape. A lens the model cannot describe or detector bias can also cause this.</source>
        <translation>Kamera {0}: Die Residuen folgen einem Muster, das das Objektivmodell nicht erklärt (Zellenüberschuss {1:.1f}, angepasstes Feld {2:.1f} × Rauschen; etwa 1, wenn das Modell passt). Oft ist die Tafel die Ursache (nicht eben, oder ihre Punkte liegen nicht genau dort, wo die Tafelbeschreibung sie annimmt): Aktivieren Sie „Bündelausgleich“ und „Tafelform optimieren“. Auch ein Objektiv, das das Modell nicht beschreibt, oder ein Detektorfehler kann dies verursachen.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="82"/>
        <source>Camera {0}: the extrapolation check was skipped (too few usable views).</source>
        <translation>Kamera {0}: Die Extrapolationsprüfung wurde übersprungen (zu wenige nutzbare Ansichten).</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="88"/>
        <source>Camera {0}: the lens-model check was skipped: the points fill only {1} image cells.</source>
        <translation>Kamera {0}: Die Prüfung des Objektivmodells wurde übersprungen: Die Punkte füllen nur {1} Bildzellen.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="103"/>
        <source>Warning: {0}</source>
        <translation>Warnung: {0}</translation>
    </message>
</context>
<context>
    <name>CalibrationSection3D</name>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="50"/>
        <source>Calibrate from images…</source>
        <translation>Aus Bildern kalibrieren…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="54"/>
        <source>Run the built-in stereo calibrator on your target photos
(checkerboard / ChArUco / dot grid). Writes an opencv_yaml
file and loads it — the recommended path when you have
calibration images.</source>
        <translation>Führt den eingebauten Stereokalibrator auf Ihren Zielfotos aus (Schachbrett / ChArUco / Punktraster).
Schreibt eine opencv_yaml-Datei und lädt sie — der empfohlene Weg, wenn Kalibrierbilder vorliegen.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="65"/>
        <source>Format</source>
        <translation>Format</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="74"/>
        <source>File format of the calibration to import. Default opencv_yaml
(written by the built-in calibrator). Pick the format matching
your source: dice (DICe XML), matchid (MatchID .caldat),
opencorr (OpenCorr CSV), mmc (MultiDIC/MMC .mat), matlabcv
(MATLAB stereoParams .mat).</source>
        <translation>Dateiformat der zu importierenden Kalibrierung. Standard: opencv_yaml
(vom eingebauten Kalibrator geschrieben). Wählen Sie das Format Ihrer Quelle:
dice (DICe XML), matchid (MatchID .caldat), opencorr (OpenCorr CSV),
mmc (MultiDIC/MMC .mat), matlabcv (MATLAB stereoParams .mat).</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="85"/>
        <source>Import calibration…</source>
        <translation>Kalibrierung importieren…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="88"/>
        <source>Load an existing stereo calibration file in the selected
Format. The status line below shows fx / fy and the baseline
as a sanity check.</source>
        <translation>Vorhandene Stereokalibrierungsdatei im gewählten Format laden.
Die Statuszeile darunter zeigt fx / fy und die Basislinie zur Plausibilitätsprüfung.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="96"/>
        <source>Manual parameters…</source>
        <translation>Parameter manuell eingeben…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="99"/>
        <source>Type intrinsics and extrinsics by hand (fx, fy, cx, cy,
distortion, R, T) — the fallback when no calibration file
exists. Writes an opencv_yaml file and loads it.</source>
        <translation>Intrinsik und Extrinsik von Hand eingeben (fx, fy, cx, cy, Verzeichnung, R, T)
— der Rückfall, wenn keine Kalibrierdatei existiert. Schreibt eine opencv_yaml-Datei und lädt sie.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="107"/>
        <source>No calibration loaded</source>
        <translation>Keine Kalibrierung geladen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="151"/>
        <source>Choose calibration file</source>
        <translation>Kalibrierdatei wählen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="153"/>
        <source>Calibration files (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)</source>
        <translation>Kalibrierdateien (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="171"/>
        <source>Error: {0}</source>
        <translation>Fehler: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="179"/>
        <source>{0}
fx {1:.0f}  fy {2:.0f}  |  baseline {3:.1f} mm</source>
        <translation>{0}
fx {1:.0f}  fy {2:.0f}  |  Basislinie {3:.1f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="185"/>
        <source>calibration loaded: baseline {0:.1f} mm</source>
        <translation>Kalibrierung geladen: Basislinie {0:.1f} mm</translation>
    </message>
</context>
<context>
    <name>CameraDropZone</name>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="76"/>
        <source>{0} frames</source>
        <translation>{0} Frames</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="103"/>
        <source>Click to pick this camera&apos;s image folder, or drag the folder here. Both cameras need the same number of frames.</source>
        <translation>Klicken, um den Bildordner dieser Kamera zu wählen, oder den Ordner hierher ziehen. Beide Kameras brauchen dieselbe Frame-Anzahl.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="114"/>
        <source>Select image folder</source>
        <translation>Bildordner wählen</translation>
    </message>
</context>
<context>
    <name>CameraRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="606"/>
        <source>Camera</source>
        <translation>Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="610"/>
        <source>Left</source>
        <translation>Links</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="611"/>
        <source>Right</source>
        <translation>Rechts</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="612"/>
        <source>Left + Right</source>
        <translation>Links + Rechts</translation>
    </message>
</context>
<context>
    <name>CanvasArea3D</name>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="92"/>
        <source>Fit</source>
        <translation>Anpassen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="95"/>
        <source>Fit the image to the viewport (Ctrl+0)</source>
        <translation>Bild an den Ansichtsbereich anpassen (Ctrl+0)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="102"/>
        <source>Current zoom — click to reset to 100% (1:1 pixels).
Wheel: zoom · Right/middle drag: pan · Space: pan mode</source>
        <translation>Aktueller Zoom — Klick setzt auf 100 % (1:1 Pixel) zurück.
Rad: Zoom · Rechts-/Mittelklick-Ziehen: Verschieben · Leertaste: Verschiebemodus</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="109"/>
        <source>Zoom in (Ctrl+=)</source>
        <translation>Vergrößern (Ctrl+=)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="113"/>
        <source>Zoom out (Ctrl+-)</source>
        <translation>Verkleinern (Ctrl+-)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="118"/>
        <source>Show Grid</source>
        <translation>Gitter anzeigen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="121"/>
        <source>Show the computational mesh preview on the reference view
(left camera, frame 1). Rebuilt live from the current Subset
Step / refinement settings — what you see is the run&apos;s mesh.
Default on; turn off to declutter the canvas.</source>
        <translation>Zeigt die Vorschau des Berechnungsnetzes auf der Referenzansicht
(linke Kamera, Frame 1). Wird live aus den aktuellen Subset-Schritt-/
Verfeinerungseinstellungen neu aufgebaut — das angezeigte Netz ist das des Laufs.
Standard: an; ausschalten, um die Ansicht zu entlasten.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="134"/>
        <source>Hovering a mesh node shows its correlation subset window
(the Subset Size box). Needs Show Grid. Use it to judge
whether the subset spans enough speckle texture.</source>
        <translation>Beim Überfahren eines Netzknotens wird sein Korrelations-Subsetfenster
(die Subsetgrößen-Box) angezeigt. Erfordert „Gitter anzeigen“. Hilft zu beurteilen,
ob das Subset genügend Speckle-Textur umfasst.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="147"/>
        <source>Switch the canvas to the reconstructed 3D surface (colored by
the selected field, with the camera frusta). Uncheck to return
to the 2D image view. Requires results.</source>
        <translation>Schaltet die Ansicht auf die rekonstruierte 3D-Oberfläche um (eingefärbt nach dem
gewählten Feld, mit Kamera-Frusta). Abwählen kehrt zur 2D-Bildansicht zurück.
Erfordert Ergebnisse.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="131"/>
        <source>Show Subset</source>
        <translation>Subset anzeigen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="144"/>
        <source>3D View</source>
        <translation>3D-Ansicht</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="323"/>
        <source>Load images before importing an ROI mask</source>
        <translation>Vor dem Import einer ROI-Maske zuerst Bilder laden</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="328"/>
        <source>Could not import the mask: {0}</source>
        <translation>Maske konnte nicht importiert werden: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="331"/>
        <source>ROI mask imported from {0}</source>
        <translation>ROI-Maske importiert aus {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="336"/>
        <source>No ROI mask to save — draw one first</source>
        <translation>Keine ROI-Maske zum Speichern — zuerst eine zeichnen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="344"/>
        <source>Save Mask</source>
        <translation>Maske speichern</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="344"/>
        <source>PNG image (*.png)</source>
        <translation>PNG-Bild (*.png)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="351"/>
        <source>Could not save the mask: {0}</source>
        <translation>Maske konnte nicht gespeichert werden: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="354"/>
        <source>ROI mask saved to {0}</source>
        <translation>ROI-Maske gespeichert unter {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="540"/>
        <source>Analysis produced no valid points — nothing to display. See the log.</source>
        <translation>Die Analyse lieferte keine gültigen Punkte — nichts anzuzeigen. Siehe Protokoll.</translation>
    </message>
</context>
<context>
    <name>CanvasRenderMixin</name>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="67"/>
        <source>Could not map the ROI into the right camera: {0}</source>
        <translation>ROI konnte nicht auf die rechte Kamera übertragen werden: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="204"/>
        <source>3D view — run an analysis to see the reconstructed surface.</source>
        <translation>3D-Ansicht — führen Sie eine Analyse aus, um die rekonstruierte Oberfläche zu sehen.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="211"/>
        <source>Selected field is not available.</source>
        <translation>Das gewählte Feld ist nicht verfügbar.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="396"/>
        <source>Could not draw the overlay: {0}</source>
        <translation>Overlay konnte nicht gezeichnet werden: {0}</translation>
    </message>
</context>
<context>
    <name>CanvasToolsMixin</name>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="55"/>
        <source>Starting points cleared</source>
        <translation>Startpunkte entfernt</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="81"/>
        <source>Starting points are placed on the LEFT camera, frame 1 — switch there to add a point</source>
        <translation>Startpunkte werden auf der LINKEN Kamera, Frame 1 gesetzt — dorthin wechseln, um einen Punkt hinzuzufügen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="92"/>
        <source>Starting point {0} placed at ({1}, {2})</source>
        <translation>Startpunkt {0} gesetzt bei ({1}, {2})</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="112"/>
        <source>Starting point removed at ({0}, {1})</source>
        <translation>Startpunkt bei ({0}, {1}) entfernt</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="169"/>
        <source>Fit</source>
        <translation>Anpassen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="171"/>
        <source>Zoom to 100%</source>
        <translation>Auf 100 % zoomen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="174"/>
        <source>Copy image to clipboard</source>
        <translation>Bild in die Zwischenablage kopieren</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="177"/>
        <source>Clear ROI</source>
        <translation>ROI löschen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="180"/>
        <source>Clear seed points</source>
        <translation>Startpunkte löschen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="190"/>
        <source>Canvas image copied to the clipboard</source>
        <translation>Leinwandbild in die Zwischenablage kopiert</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="205"/>
        <source>1. Drop the left/right camera folders in the sidebar
2. Calibrate or import calibration
3. Draw the ROI and Run</source>
        <translation>1. Die Ordner der linken/rechten Kamera in die Seitenleiste ziehen
2. Kalibrieren oder Kalibrierung importieren
3. ROI zeichnen und starten</translation>
    </message>
</context>
<context>
    <name>ConfigOverlay3D</name>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="39"/>
        <source>Mode</source>
        <translation>Modus</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="40"/>
        <source>Solver</source>
        <translation>Löser</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="41"/>
        <source>Init</source>
        <translation>Startschätzung</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="42"/>
        <source>Subset</source>
        <translation>Subset</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="79"/>
        <source>AL-DIC ({0} iter)</source>
        <translation>AL-DIC ({0} Iter.)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="94"/>
        <source>FFT (no starting point)</source>
        <translation>FFT (kein Startpunkt)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="81"/>
        <source>Local DIC</source>
        <translation>Local DIC</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="84"/>
        <source>Starting Point</source>
        <translation>Startpunkt</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="85"/>
        <source>Previous frame</source>
        <translation>Vorheriger Frame</translation>
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
        <translation>Akkumulativ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="75"/>
        <source>Incremental</source>
        <translation>Inkrementell</translation>
    </message>
</context>
<context>
    <name>ConsoleLog3D</name>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="41"/>
        <source>Copy all</source>
        <translation>Alles kopieren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="44"/>
        <source>Save log to file…</source>
        <translation>Protokoll in Datei speichern…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="46"/>
        <source>Clear</source>
        <translation>Leeren</translation>
    </message>
</context>
<context>
    <name>DataTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="50"/>
        <source>Format</source>
        <translation>Format</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="52"/>
        <source>NumPy archive (.npz)</source>
        <translation>NumPy-Archiv (.npz)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="54"/>
        <source>MATLAB (.mat)</source>
        <translation>MATLAB (.mat)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="56"/>
        <source>CSV (one file per frame)</source>
        <translation>CSV (eine Datei pro Frame)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="57"/>
        <source>PLY point clouds (per frame)</source>
        <translation>PLY-Punktwolken (pro Frame)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="58"/>
        <source>VTU mesh series (ParaView)</source>
        <translation>VTU-Netzserie (ParaView)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="61"/>
        <source>✓ Parameters file (JSON) always exported</source>
        <translation>✓ Parameterdatei (JSON) wird immer exportiert</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="68"/>
        <source>Displacement</source>
        <translation>Verschiebung</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="72"/>
        <source>Strain</source>
        <translation>Dehnung</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="79"/>
        <source>3D points, reprojection error, and source flags are always exported.</source>
        <translation>3D-Punkte, Reprojektionsfehler und Quell-Flags werden immer exportiert.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="88"/>
        <source>Export Data</source>
        <translation>Daten exportieren</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="105"/>
        <source>Select:</source>
        <translation>Auswahl:</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="108"/>
        <source>All</source>
        <translation>Alle</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="109"/>
        <source>None</source>
        <translation>Keine</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="158"/>
        <source>Choose an output folder first.</source>
        <translation>Bitte zuerst einen Ausgabeordner wählen.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="189"/>
        <source>Wrote: {0}</source>
        <translation>Geschrieben: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="193"/>
        <source>Export cancelled — kept: {0}</source>
        <translation>Export abgebrochen — behalten: {0}</translation>
    </message>
</context>
<context>
    <name>DetectionFilesMixin</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="215"/>
        <source>Save detections</source>
        <translation>Detektionen speichern</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="217"/>
        <location filename="../../gui/dialogs/calibration_support.py" line="238"/>
        <source>NumPy detections (*.npz)</source>
        <translation>NumPy-Detektionen (*.npz)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="231"/>
        <source>Detections saved: {0}</source>
        <translation>Detektionen gespeichert: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="236"/>
        <source>Load detections</source>
        <translation>Detektionen laden</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="260"/>
        <source>Loaded {0} detection pairs — Recalibrate re-solves without re-detecting</source>
        <translation>{0} Detektionspaare geladen — Neu kalibrieren löst ohne erneute Detektion</translation>
    </message>
</context>
<context>
    <name>DetectionZoomDialog</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="274"/>
        <source>Detection preview — pair {0}</source>
        <translation>Detektionsvorschau — Paar {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="283"/>
        <source>Wheel: zoom · Right/middle drag: pan</source>
        <translation>Rad: Zoom · Ziehen mit rechter/mittlerer Taste: Verschieben</translation>
    </message>
</context>
<context>
    <name>ExportDialog</name>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="139"/>
        <source>Export Results</source>
        <translation>Ergebnisse exportieren</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="146"/>
        <source>OUTPUT FOLDER</source>
        <translation>AUSGABEORDNER</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="149"/>
        <source>Select output folder…</source>
        <translation>Ausgabeordner wählen…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="151"/>
        <source>Browse…</source>
        <translation>Durchsuchen…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="152"/>
        <source>Choose the folder all exports are written into</source>
        <translation>Ordner wählen, in den alle Exporte geschrieben werden</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="155"/>
        <source>Open Folder</source>
        <translation>Ordner öffnen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="156"/>
        <source>Open the output folder in the file explorer</source>
        <translation>Ausgabeordner im Datei-Explorer öffnen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="168"/>
        <source>Data</source>
        <translation>Daten</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="169"/>
        <source>Images</source>
        <translation>Bilder</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="170"/>
        <source>Animation</source>
        <translation>Animation</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="171"/>
        <source>Preview &amp; Colorbar</source>
        <translation>Vorschau &amp; Farbleiste</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="172"/>
        <source>3D View</source>
        <translation>3D-Ansicht</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="176"/>
        <source>Numeric results: field-selective NPZ / MAT / CSV tables plus PLY / VTU meshes for external tools.</source>
        <translation>Numerische Ergebnisse: feldselektive NPZ- / MAT- / CSV-Tabellen sowie PLY- / VTU-Netze für externe Tools.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="180"/>
        <source>Rendered per-camera field overlays as PNG images, one per frame, using the Preview &amp; Colorbar style.</source>
        <translation>Gerenderte Feld-Überlagerungen je Kamera als PNG-Bilder, eines pro Frame, im Stil von „Vorschau &amp; Farbleiste“.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="184"/>
        <source>GIF / MP4 animations of the field overlay across frames, using the Preview &amp; Colorbar style.</source>
        <translation>GIF- / MP4-Animationen der Feld-Überlagerung über die Frames, im Stil von „Vorschau &amp; Farbleiste“.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="188"/>
        <source>WYSIWYG style source: the colorbar and margins configured here are used by every Images / Animation export.</source>
        <translation>WYSIWYG-Stilquelle: Die hier konfigurierte Farbleiste und Ränder werden für jeden Bild- / Animationsexport verwendet.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="461"/>
        <source>Export Running</source>
        <translation>Export läuft</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="462"/>
        <source>An export is still running — cancel it and close?</source>
        <translation>Ein Export läuft noch — abbrechen und schließen?</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="465"/>
        <source>Yes</source>
        <translation>Ja</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="466"/>
        <source>No</source>
        <translation>Nein</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="498"/>
        <source>Folder does not exist: {0}</source>
        <translation>Ordner existiert nicht: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="204"/>
        <source>Close</source>
        <translation>Schließen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="192"/>
        <source>Offscreen renders of the 3D surface as images, a deforming animation or a turntable, from your current 3D view.</source>
        <translation>Offscreen-Renderings der 3D-Oberfläche als Bilder, Verformungsanimation oder Turntable, aus Ihrer aktuellen 3D-Ansicht.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="485"/>
        <source>Choose output folder</source>
        <translation>Ausgabeordner wählen</translation>
    </message>
</context>
<context>
    <name>ExportTabBase</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="250"/>
        <source>Cancelling…</source>
        <translation>Wird abgebrochen…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="287"/>
        <source>Export cancelled — {0} file(s) kept</source>
        <translation>Export abgebrochen — {0} Datei(en) behalten</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="289"/>
        <source>(the unfinished animation was deleted)</source>
        <translation>(die unvollständige Animation wurde gelöscht)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="296"/>
        <source>Nothing was written: no data to draw for {0}.</source>
        <translation>Nichts geschrieben: keine darstellbaren Daten für {0}.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="299"/>
        <source>Nothing was written — the export produced no files.</source>
        <translation>Nichts geschrieben — der Export hat keine Dateien erzeugt.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="307"/>
        <source>{0} frame(s) had no data to draw ({1})</source>
        <translation>{0} Frame(s) ohne darstellbare Daten ({1})</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="313"/>
        <source>no data for {0}</source>
        <translation>keine Daten für {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="317"/>
        <source>the right-camera ROI could not be derived; the tracked area was used</source>
        <translation>die ROI der rechten Kamera ließ sich nicht ableiten; der verfolgte Bereich wurde verwendet</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="278"/>
        <source>Error: {0}</source>
        <translation>Fehler: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="282"/>
        <source>Wrote {0} file(s)</source>
        <translation>{0} Datei(en) geschrieben</translation>
    </message>
</context>
<context>
    <name>ExportTabs</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="625"/>
        <source>Full resolution</source>
        <translation>Volle Auflösung</translation>
    </message>
</context>
<context>
    <name>FieldRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="420"/>
        <source>Auto</source>
        <translation>Auto</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="421"/>
        <source>Auto range</source>
        <translation>Auto-Bereich</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="436"/>
        <source>Opacity</source>
        <translation>Deckkraft</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="437"/>
        <source>Field opacity (0 = transparent, 1 = fully opaque)</source>
        <translation>Feld-Deckkraft (0 = transparent, 1 = vollständig deckend)</translation>
    </message>
</context>
<context>
    <name>FieldSelector3D</name>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="47"/>
        <source>DISPLACEMENT</source>
        <translation>VERSCHIEBUNG</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="69"/>
        <source>U — world-frame displacement along X (left camera&apos;s +X, image right), in mm</source>
        <translation>U — Verschiebung im Weltkoordinatensystem entlang X (+X der linken Kamera, im Bild nach rechts), in mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="72"/>
        <source>V — world-frame displacement along Y (left camera&apos;s +Y, image down), in mm</source>
        <translation>V — Verschiebung im Weltkoordinatensystem entlang Y (+Y der linken Kamera, im Bild nach unten), in mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="75"/>
        <source>W — world-frame displacement along Z (left camera&apos;s optical axis, toward the scene): out-of-plane motion, in mm</source>
        <translation>W — Verschiebung im Weltkoordinatensystem entlang Z (optische Achse der linken Kamera, zur Szene): Out-of-plane-Bewegung, in mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="78"/>
        <source>|D| — displacement magnitude √(U²+V²+W²), in mm</source>
        <translation>|D| — Verschiebungsbetrag √(U²+V²+W²), in mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="80"/>
        <location filename="../../gui/widgets/field_selector.py" line="107"/>
        <source>Velocity — per-node speed |D(k) − D(k−1)| × frame rate, in the display unit per second. Depends on the frame rate set in the UNITS section; frame 1 has no predecessor (empty).</source>
        <translation>Geschwindigkeit — Tempo je Knoten |D(k) − D(k−1)| × Bildrate, in der Anzeigeeinheit pro Sekunde. Hängt von der im Bereich UNITS gesetzten Bildrate ab; Frame 1 hat keinen Vorgänger (leer).</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="103"/>
        <source>Run an analysis first — velocity needs results.</source>
        <translation>Zuerst eine Analyse ausführen — Geschwindigkeit benötigt Ergebnisse.</translation>
    </message>
</context>
<context>
    <name>FrameMasksSection3D</name>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="65"/>
        <source>Per-frame masks</source>
        <translation>Masken pro Bild</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="69"/>
        <source>Optional: one mask image per frame (non-zero = valid), for
specimens whose valid region changes, e.g. a crack or a
boundary that moves. Without them the ROI of frame 1 is used
for every frame.</source>
        <translation>Optional: ein Maskenbild pro Bild (ungleich null = gültig) für
Proben, deren gültiger Bereich sich ändert, etwa durch einen Riss
oder eine wandernde Kante. Ohne sie gilt die ROI von Bild 1
für alle Bilder.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="83"/>
        <source>Import…</source>
        <translation>Importieren…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="84"/>
        <source>Choose the folder holding this camera&apos;s mask images</source>
        <translation>Den Ordner mit den Maskenbildern dieser Kamera wählen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="87"/>
        <source>Clear</source>
        <translation>Leeren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="97"/>
        <source>Left</source>
        <translation>Links</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="97"/>
        <source>Right</source>
        <translation>Rechts</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="104"/>
        <source>{0}: {1} masks</source>
        <translation>{0}: {1} Masken</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="106"/>
        <source>{0}: none</source>
        <translation>{0}: keine</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="114"/>
        <source>Choose the mask folder</source>
        <translation>Maskenordner wählen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="128"/>
        <source>Masks not imported for the {0} camera: {1}</source>
        <translation>Masken für die {0} Kamera nicht importiert: {1}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="142"/>
        <source>{0} camera: {1} per-frame masks from {2}</source>
        <translation>{0} Kamera: {1} Masken pro Bild aus {2}</translation>
    </message>
</context>
<context>
    <name>FrameNavigator3D</name>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="45"/>
        <source>Previous frame (←)</source>
        <translation>Vorheriger Frame (←)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="52"/>
        <location filename="../../gui/widgets/frame_navigator.py" line="160"/>
        <source>Play animation (Space)</source>
        <translation>Animation abspielen (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="59"/>
        <source>Next frame (→)</source>
        <translation>Nächster Frame (→)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="68"/>
        <source>Playback speed (frames per second). Default 2 fps.</source>
        <translation>Wiedergabegeschwindigkeit (Frames pro Sekunde). Standard 2 fps.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="153"/>
        <source>Pause animation (Space)</source>
        <translation>Animation pausieren (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="175"/>
        <source>FRAME {0}/{1}</source>
        <translation>FRAME {0}/{1}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="177"/>
        <source>FRAME 0/0</source>
        <translation>FRAME 0/0</translation>
    </message>
</context>
<context>
    <name>FrameRangeRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="656"/>
        <source>All frames</source>
        <translation>Alle Bilder</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="660"/>
        <source>From frame</source>
        <translation>Von Bild</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="670"/>
        <source>to</source>
        <translation>bis</translation>
    </message>
</context>
<context>
    <name>ImageCanvas3D</name>
    <message>
        <location filename="../../gui/widgets/image_view.py" line="762"/>
        <source>The three points are nearly in a line — spread them around the edge</source>
        <translation>Die drei Punkte liegen fast auf einer Linie — verteilen Sie sie über den Rand</translation>
    </message>
</context>
<context>
    <name>ImagesTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="55"/>
        <source>Fields</source>
        <translation>Felder</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="75"/>
        <source>Format</source>
        <translation>Format</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="84"/>
        <source>JPEG quality</source>
        <translation>JPEG-Qualität</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="91"/>
        <source>Resolution (long edge)</source>
        <translation>Auflösung (lange Kante)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="100"/>
        <source>Include colorbar</source>
        <translation>Farbleiste einfügen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="105"/>
        <source>Background</source>
        <translation>Hintergrund</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="119"/>
        <source>Export Images</source>
        <translation>Bilder exportieren</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="130"/>
        <source>Load an image sequence first (open the project in the main window).</source>
        <translation>Zuerst eine Bildsequenz laden (Projekt im Hauptfenster öffnen).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="156"/>
        <source>Choose an output folder first.</source>
        <translation>Bitte zuerst einen Ausgabeordner wählen.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="160"/>
        <source>No fields enabled.</source>
        <translation>Keine Felder aktiviert.</translation>
    </message>
</context>
<context>
    <name>InitGuessSection3D</name>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="112"/>
        <source>Clear</source>
        <translation>Leeren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="74"/>
        <source>Starting Points</source>
        <translation>Startpunkte</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="77"/>
        <source>Click one or more points on the LEFT camera, frame 1 — at least
one per connected ROI region. Each point&apos;s neighborhood is matched
automatically into the right camera (stereo offset) and into
frame 2 (motion seed), then a first-order deformation field is
propagated to every mesh node — no search tuning needed. Best for
wide stereo baselines, large first-frame motion, or discontinuous
fields. If no point is placed, the run falls back to FFT.</source>
        <translation>Klicken Sie einen oder mehrere Punkte auf der LINKEN Kamera, Frame 1 —
mindestens einen pro zusammenhängender ROI-Region. Die Umgebung jedes
Punkts wird automatisch in die rechte Kamera (Stereo-Versatz) und in Frame 2
(Bewegungs-Seed) eingepasst, dann wird ein Verschiebungsfeld erster Ordnung
auf jeden Netzknoten propagiert — keine Suchparameter nötig. Ideal für breite
Basislinien, große Bewegung im ersten Frame oder unstetige Felder. Ohne
gesetzten Punkt fällt der Lauf auf FFT zurück.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="94"/>
        <location filename="../../gui/widgets/init_guess_section.py" line="191"/>
        <source>Place points…</source>
        <translation>Punkte platzieren…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="98"/>
        <source>Enter placement mode on the canvas. Left-click the LEFT camera,
frame 1 to ADD a point; right-click removes the nearest; Esc exits.</source>
        <translation>Platzierungsmodus auf der Leinwand. Linksklick auf die LINKE Kamera,
Frame 1 fügt einen Punkt hinzu; Rechtsklick entfernt den nächsten; Esc beendet.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="103"/>
        <source>Auto-place</source>
        <translation>Automatisch setzen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="106"/>
        <source>Place one Starting Point automatically, deep inside the ROI on
the LEFT camera, frame 1. Add more by hand for disconnected
regions or strongly varying motion.</source>
        <translation>Setzt automatisch einen Startpunkt tief in der ROI der LINKEN
Kamera, Bild 1. Für getrennte Bereiche oder stark wechselnde
Bewegung weitere von Hand hinzufügen.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="113"/>
        <source>Remove all Starting Points</source>
        <translation>Alle Startpunkte entfernen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="122"/>
        <source>FFT (cross-correlation)</source>
        <translation>FFT (Kreuzkorrelation)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="125"/>
        <source>Full-grid cross-correlation seeds frame 1 (and every reference
switch in incremental mode); later frames warm-start from the
previous solution. Robust default — the search radius is the
Temporal Search parameter.</source>
        <translation>Die Kreuzkorrelation über das volle Gitter liefert den Startwert für
Frame 1 (und bei jedem Referenzwechsel im inkrementellen Modus);
spätere Frames starten warm von der vorherigen Lösung. Robuster
Standard — der Suchradius ist der Parameter „Zeitliche Suche“.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="134"/>
        <source>Previous frame</source>
        <translation>Vorheriger Frame</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="137"/>
        <source>Start every frame from the previous frame&apos;s solution — no
cross-correlation at all. Fastest; can silently freeze on large
motion or decorrelation — the validity gate will flag affected
frames.</source>
        <translation>Jeder Frame startet von der Lösung des vorherigen Frames — ganz
ohne Kreuzkorrelation. Am schnellsten; kann bei großer Bewegung
oder Dekorrelation still einfrieren — das Validitätsgate markiert
betroffene Frames.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="191"/>
        <source>Placing… (click to exit)</source>
        <translation>Platzieren… (zum Beenden klicken)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="233"/>
        <source>No point placed: the run finds the stereo offset from probe patches and seeds frame 1 by FFT. Place a point (or Auto-place) for large first-frame motion.</source>
        <translation>Kein Punkt gesetzt: Der Lauf bestimmt den Stereo-Versatz aus Probe-Ausschnitten und initialisiert Bild 1 per FFT. Bei großer Bewegung im ersten Bild einen Punkt setzen (oder automatisch setzen).</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="240"/>
        <location filename="../../gui/widgets/init_guess_section.py" line="273"/>
        <source>{0} point(s) placed</source>
        <translation>{0} Punkt(e) gesetzt</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="276"/>
        <source>{0} point(s) · {1}/{2} regions ready</source>
        <translation>{0} Punkt(e) · {1}/{2} Regionen bereit</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="283"/>
        <source>{0} point(s) · {1}/{2} regions seeded — rest auto-seeded at run</source>
        <translation>{0} Punkt(e) · {1}/{2} Regionen besät — Rest wird beim Lauf automatisch besät</translation>
    </message>
</context>
<context>
    <name>Issues</name>
    <message>
        <location filename="../../gui/issue_text.py" line="27"/>
        <source>left camera</source>
        <translation>linke Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="28"/>
        <source>right camera</source>
        <translation>rechte Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="36"/>
        <source>calibration file not set</source>
        <translation>Kalibrierdatei nicht gesetzt</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="39"/>
        <source>left/right sequences not set</source>
        <translation>linke/rechte Sequenzen nicht gesetzt</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="42"/>
        <source>need at least 2 frames</source>
        <translation>mindestens 2 Bilder erforderlich</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="43"/>
        <source>ROI not set</source>
        <translation>ROI nicht gesetzt</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="44"/>
        <source>ROI is empty (xmin&lt;xmax, ymin&lt;ymax required)</source>
        <translation>ROI ist leer (xmin&lt;xmax, ymin&lt;ymax erforderlich)</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="47"/>
        <source>left and right sequences use the same image files</source>
        <translation>linke und rechte Sequenz verwenden dieselben Bilddateien</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="63"/>
        <source>sequence length mismatch: {0} vs {1}</source>
        <translation>Sequenzlängen stimmen nicht überein: {0} vs. {1}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="67"/>
        <source>calibration file cannot be read: {0}</source>
        <translation>Kalibrierdatei nicht lesbar: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="71"/>
        <source>{0}: image not readable: {1}</source>
        <translation>{0}: Bild nicht lesbar: {1}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="75"/>
        <source>{0}: frame sizes differ ({1} vs {2})</source>
        <translation>{0}: Bildgrößen unterscheiden sich ({1} gegenüber {2})</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="79"/>
        <source>ROI mask is {0} but the images are {1}: redraw or import it again</source>
        <translation>ROI-Maske ist {0}, die Bilder sind {1}: neu zeichnen oder erneut importieren</translation>
    </message>
</context>
<context>
    <name>LeftSidebar3D</name>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="82"/>
        <source>IMAGES</source>
        <translation>BILDER</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="89"/>
        <source>Drop LEFT camera
folder or click</source>
        <translation>LINKEN Kameraordner
ablegen oder klicken</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="90"/>
        <source>Drop RIGHT camera
folder or click</source>
        <translation>RECHTEN Kameraordner
ablegen oder klicken</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="95"/>
        <source>Natural Sort (1, 2, …, 10)</source>
        <translation>Natürliche Sortierung (1, 2, …, 10)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="98"/>
        <source>Sort file names numerically (img2 before img10). Default on; turn off for strict alphabetical order. Applies to the next folder load.</source>
        <translation>Dateinamen numerisch sortieren (img2 vor img10). Standard: an; ausschalten für strikt alphabetische Reihenfolge. Gilt ab dem nächsten Ordnerladen.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="116"/>
        <location filename="../../gui/panels/left_sidebar.py" line="687"/>
        <source>No images loaded</source>
        <translation>Keine Bilder geladen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="142"/>
        <source>CALIBRATION</source>
        <translation>KALIBRIERUNG</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="146"/>
        <source>WORKFLOW TYPE</source>
        <translation>WORKFLOW-TYP</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="153"/>
        <source>INITIAL GUESS</source>
        <translation>STARTSCHÄTZUNG</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="157"/>
        <source>REGION OF INTEREST</source>
        <translation>INTERESSENBEREICH</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="161"/>
        <source>PARAMETERS</source>
        <translation>PARAMETER</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="165"/>
        <source>ADVANCED</source>
        <translation>ERWEITERT</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="231"/>
        <source>Incremental: each frame is compared to the previous reference frame.
Suitable for large accumulated deformation, required for large rotations.

Accumulative: every frame is compared to frame 1.
Accurate for small, monotonic deformation only.</source>
        <translation>Inkrementell: Jeder Frame wird mit dem vorherigen Referenzframe verglichen.
Geeignet für große kumulierte Verformungen, erforderlich bei großen Rotationen.

Akkumulativ: Jeder Frame wird mit Frame 1 verglichen.
Nur für kleine, monotone Verformungen genau.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="249"/>
        <source>Local DIC</source>
        <translation>Local DIC</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="251"/>
        <source>Local DIC: Independent subset matching (IC-GN). Fast,
preserves sharp local features. Best for small
deformations or high-quality images.

AL-DIC: Augmented Lagrangian with global FEM
regularization. Enforces displacement compatibility
between subsets. Best for large deformations, noisy
images, or when strain accuracy matters.</source>
        <translation>Local DIC: Unabhängiges Subset-Matching (IC-GN). Schnell,
erhält scharfe lokale Merkmale. Optimal für kleine
Verformungen oder hochwertige Bilder.

AL-DIC: Augmented Lagrangian mit globaler FEM-
Regularisierung. Erzwingt Verschiebungskompatibilität
zwischen Subsets. Optimal für große Verformungen,
verrauschte Bilder oder hohe Dehnungsgenauigkeit.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="261"/>
        <source>Solver</source>
        <translation>Löser</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="335"/>
        <location filename="../../gui/panels/left_sidebar.py" line="359"/>
        <source>bbox: not set</source>
        <translation>Begrenzungsrahmen: nicht gesetzt</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="362"/>
        <source>bbox: {0}–{1}, {2}–{3} px</source>
        <translation>Begrenzungsrahmen: {0}–{1}, {2}–{3} px</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="382"/>
        <source>IC-GN subset window size in pixels (odd number). Default 33.
Larger = more robust on sparse speckle, smoother fields;
smaller = finer spatial detail but noisier. The subset must
span several speckles.</source>
        <translation>IC-GN-Subsetfenstergröße in Pixeln (ungerade). Standard 33.
Größer = robuster bei spärlichem Speckle, glattere Felder; kleiner = feinere räumliche Details, aber mehr Rauschen.
Das Subset muss mehrere Speckles umfassen.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="226"/>
        <source>Accumulative</source>
        <translation>Akkumulativ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="227"/>
        <source>Incremental</source>
        <translation>Inkrementell</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="238"/>
        <source>Tracking Mode</source>
        <translation>Tracking-Modus</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="317"/>
        <source>Draw on the LEFT camera, frame 1 — all later frames and the right camera follow from it.</source>
        <translation>Auf der LINKEN Kamera, Frame 1 zeichnen — alle späteren Frames und die rechte Kamera folgen daraus.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="388"/>
        <source>Subset Size</source>
        <translation>Subset-Größe</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="396"/>
        <source>Node spacing in pixels (power of 2). Default 16. Smaller =
denser measurement grid and longer runs; larger = faster but
coarser fields. Typically ¼–½ of the Subset Size.</source>
        <translation>Knotenabstand in Pixeln (Zweierpotenz). Standard 16. Kleiner = dichteres Messgitter
und längere Läufe; größer = schneller, aber gröbere Felder. Üblich: ¼–½ der Subsetgröße.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="401"/>
        <source>Subset Step</source>
        <translation>Subset-Schrittweite</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="407"/>
        <source>Stereo Search</source>
        <translation>Stereo-Suche</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="420"/>
        <source>Temporal Search</source>
        <translation>Zeitliche Suche</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="426"/>
        <source>Mesh refinement</source>
        <translation>Netzverfeinerung</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="433"/>
        <source>Refine at mask boundaries (holes)</source>
        <translation>An Maskengrenzen (Löchern) verfeinern</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="436"/>
        <source>Quadtree-subdivide mesh elements crossing interior mask
holes so the mesh hugs the hole edges. Default off (uniform
grid); enable when the ROI mask has cut-outs whose rims you
care about.</source>
        <translation>Quadtree-Unterteilung der Netzelemente, die innere Masklöcher kreuzen, damit das Netz den
Lochrändern folgt. Standard: aus (gleichmäßiges Gitter); aktivieren, wenn die ROI-Maske
Aussparungen hat, deren Ränder wichtig sind.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="443"/>
        <source>Refine at ROI edges</source>
        <translation>An ROI-Rändern verfeinern</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="446"/>
        <source>Quadtree-subdivide mesh elements along the outer ROI
boundary. Default off; enable for curved / irregular ROI
outlines where the uniform grid staircases.</source>
        <translation>Quadtree-Unterteilung der Netzelemente entlang der äußeren ROI-Grenze.
Standard: aus; aktivieren bei gekrümmten / unregelmäßigen ROI-Konturen, wo das gleichmäßige Gitter Treppen bildet.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="458"/>
        <source>How aggressively refined elements shrink: the minimum element
is step / 2^level. Default 1 (light); 3 is heavy — finer
boundary detail but many more nodes and a slower run.</source>
        <translation>Wie stark verfeinerte Elemente schrumpfen: Das kleinste Element ist step / 2^Level.
Standard 1 (leicht); 3 ist stark — feinere Randdetails, aber deutlich mehr Knoten und ein langsamerer Lauf.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="463"/>
        <source>Refinement Level</source>
        <translation>Verfeinerungsstufe</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="575"/>
        <source>NCC search half-width (pixels) around each node for the
left-to-right stereo match. Set larger than the largest
expected stereo disparity.</source>
        <translation>NCC-Suchhalbweite (Pixel) um jeden Knoten für den
Links-rechts-Stereoabgleich. Größer als die größte
erwartete Stereo-Disparität wählen.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="580"/>
        <source>Half-width (pixels) of the temporal FFT integer search that seeds
each per-frame match. Set comfortably larger than the expected
inter-frame motion; with Auto-expand on (default) the engine can
still grow the search past this on a boundary-clipped peak.</source>
        <translation>Halbbreite (Pixel) der zeitlichen ganzzahligen FFT-Suche, die jede
Frame-Zuordnung initialisiert. Deutlich größer als die erwartete
Bewegung pro Frame wählen; bei aktivierter Auto-Erweiterung (Standard)
kann die Engine die Suche über diesen Wert hinaus vergrößern, wenn ein
Peak den Suchrand erreicht.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="596"/>
        <source>Current images: the engine starts the FFT search clamped to
{0} px (max(10, min(H, W) / 4 - subset)); Auto-expand can grow
it to {1} px (max(32, min(H, W) / 2)) on clipped peaks.</source>
        <translation>Aktuelle Bilder: Die Engine begrenzt die FFT-Suche zu Beginn auf
{0} px (max(10, min(H, W) / 4 - Subset)); bei abgeschnittenen Peaks
kann die Auto-Erweiterung sie auf {1} px (max(32, min(H, W) / 2))
vergrößern.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="618"/>
        <source>Inactive with the current Initial Guess / Tracking Mode: the
temporal FFT runs only when Initial Guess = FFT, or at reference
switches in Incremental mode; in Accumulative + Starting Point /
Previous frame no FFT runs, so this control has no effect.</source>
        <translation>Bei der aktuellen Anfangsschätzung / dem Tracking-Modus wirkungslos:
Die zeitliche FFT läuft nur bei Anfangsschätzung = FFT oder an
Referenzwechseln im inkrementellen Modus. Bei Akkumulativ + Startpunkt /
Vorheriger Frame läuft keine FFT, dieses Element hat also keine Wirkung.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="592"/>
        <source>Current images: values above {0} px cannot widen the search
(the window is clamped at the image borders).</source>
        <translation>Aktuelle Bilder: Werte über {0} px vergrößern die Suche nicht weiter
(das Suchfenster wird an den Bildrändern beschnitten).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="267"/>
        <source>Extra filters (correlation, outliers)</source>
        <translation>Zusatzfilter (Korrelation, Ausreißer)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="270"/>
        <source>Post-run filters: drop points whose correlation (ZNSSD),
reprojection error or 3D-outlier distance is too poor.
Default off (keep every tracked point); enable for noisy
data when a few bad points pollute the fields. The log
reports how many points each filter removed.</source>
        <translation>Filter nach dem Lauf: verwirft Punkte, deren Korrelation (ZNSSD),
Rückprojektionsfehler oder 3D-Ausreißerabstand zu schlecht ist.
Standardmäßig aus (alle verfolgten Punkte bleiben); für verrauschte
Daten einschalten, wenn einzelne schlechte Punkte die Felder stören.
Das Protokoll meldet, wie viele Punkte jeder Filter entfernt hat.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="634"/>
        <source>No images found in {0}</source>
        <translation>Keine Bilder in {0} gefunden</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="642"/>
        <source>left camera</source>
        <translation>linke Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="642"/>
        <source>right camera</source>
        <translation>rechte Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="645"/>
        <source>This folder holds both cameras ({0}): using its {1} images for the {2}</source>
        <translation>Dieser Ordner enthält beide Kameras ({0}): {1} Bilder werden für die {2} verwendet</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="656"/>
        <source>{0}: {1} images from {2}</source>
        <translation>{0}: {1} Bilder aus {2}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="692"/>
        <source>Paired: {0} frames per camera</source>
        <translation>Gepaart: {0} Frames pro Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="698"/>
        <source>Mismatch: {0} left vs {1} right</source>
        <translation>Nicht übereinstimmend: {0} links vs. {1} rechts</translation>
    </message>
</context>
<context>
    <name>MainMenuMixin</name>
    <message>
        <location filename="../../gui/main_menu.py" line="58"/>
        <source>&amp;File</source>
        <translation>&amp;Datei</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="60"/>
        <source>New Project</source>
        <translation>Neues Projekt</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="66"/>
        <source>Open Project…</source>
        <translation>Projekt öffnen…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="73"/>
        <source>Recent Projects</source>
        <translation>Zuletzt verwendete Projekte</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="79"/>
        <source>Save Project</source>
        <translation>Projekt speichern</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="84"/>
        <source>Save Project As…</source>
        <translation>Projekt speichern unter…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="94"/>
        <source>Associate .aldic3d files with pyALDIC-3D…</source>
        <translation>.aldic3d-Dateien mit pyALDIC-3D verknüpfen…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="97"/>
        <source>Register .aldic3d so double-clicking a project file opens pyALDIC-3D (current user only, no admin rights needed).</source>
        <translation>.aldic3d registrieren, damit ein Doppelklick auf eine Projektdatei pyALDIC-3D öffnet (nur aktueller Benutzer, keine Adminrechte nötig).</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="105"/>
        <source>Quit</source>
        <translation>Beenden</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="113"/>
        <source>&amp;Help</source>
        <translation>&amp;Hilfe</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="114"/>
        <source>User Guide</source>
        <translation>Benutzerhandbuch</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="118"/>
        <source>Keyboard Shortcuts</source>
        <translation>Tastenkürzel</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="121"/>
        <source>About pyALDIC-3D</source>
        <translation>Über pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="132"/>
        <source>&amp;Settings</source>
        <translation>&amp;Einstellungen</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="133"/>
        <location filename="../../gui/main_menu.py" line="180"/>
        <source>Language</source>
        <translation>Sprache</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="157"/>
        <location filename="../../gui/main_menu.py" line="163"/>
        <source>File Association</source>
        <translation>Dateiverknüpfung</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="158"/>
        <source>Could not register the .aldic3d association: {0}</source>
        <translation>Die .aldic3d-Verknüpfung konnte nicht registriert werden: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="165"/>
        <source>Done — double-clicking a .aldic3d file now opens it in pyALDIC-3D (registered for the current user).</source>
        <translation>Fertig — ein Doppelklick auf eine .aldic3d-Datei öffnet sie jetzt in pyALDIC-3D (für den aktuellen Benutzer registriert).</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="174"/>
        <source>The interface language changes to {0} after pyALDIC-3D restarts.</source>
        <translation>Die Oberflächensprache wechselt nach dem Neustart von pyALDIC-3D zu {0}.</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="188"/>
        <source>Could not open a web browser. The user guide is at {0}</source>
        <translation>Kein Webbrowser konnte geöffnet werden. Das Benutzerhandbuch liegt unter {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="214"/>
        <source>(not reachable)</source>
        <translation>(nicht erreichbar)</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="220"/>
        <source>No recent projects</source>
        <translation>Keine zuletzt verwendeten Projekte</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="224"/>
        <source>Clear list</source>
        <translation>Liste leeren</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="232"/>
        <source>The project file is not reachable right now: {0}</source>
        <translation>Die Projektdatei ist gerade nicht erreichbar: {0}</translation>
    </message>
</context>
<context>
    <name>MainWindow3D</name>
    <message>
        <location filename="../../gui/main_window.py" line="143"/>
        <source>pyALDIC-3D ready</source>
        <translation>pyALDIC-3D bereit</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="184"/>
        <source>Run an analysis first — there are no results to post-process</source>
        <translation>Zuerst eine Analyse starten — es gibt keine Ergebnisse zum Nachbearbeiten</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="216"/>
        <source>Strain window available — open it from the sidebar</source>
        <translation>Dehnungsfenster verfügbar — über die Seitenleiste öffnen</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="278"/>
        <location filename="../../gui/main_window.py" line="296"/>
        <source>Analysis Running</source>
        <translation>Analyse läuft</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="279"/>
        <source>An analysis is running — cancel it and quit?</source>
        <translation>Eine Analyse läuft — abbrechen und beenden?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="284"/>
        <location filename="../../gui/main_window.py" line="300"/>
        <location filename="../../gui/main_window.py" line="677"/>
        <source>Yes</source>
        <translation>Ja</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="285"/>
        <location filename="../../gui/main_window.py" line="301"/>
        <location filename="../../gui/main_window.py" line="678"/>
        <source>No</source>
        <translation>Nein</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="297"/>
        <source>An analysis is running — cancel it and switch projects?</source>
        <translation>Eine Analyse läuft — abbrechen und das Projekt wechseln?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="331"/>
        <source>Unsaved Changes</source>
        <translation>Ungespeicherte Änderungen</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="332"/>
        <source>The project has unsaved changes. Save them before continuing?</source>
        <translation>Das Projekt hat ungespeicherte Änderungen. Vor dem Fortfahren speichern?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="339"/>
        <source>Save</source>
        <translation>Speichern</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="340"/>
        <source>Discard</source>
        <translation>Verwerfen</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="341"/>
        <location filename="../../gui/main_window.py" line="593"/>
        <location filename="../../gui/main_window.py" line="679"/>
        <source>Cancel</source>
        <translation>Abbrechen</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="362"/>
        <source>Switched to left camera, frame 1 for ROI editing</source>
        <translation>Zur ROI-Bearbeitung auf linke Kamera, Frame 1 gewechselt</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="367"/>
        <source>Load images first, then draw the region of interest</source>
        <translation>Zuerst Bilder laden, dann den Interessenbereich zeichnen</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="380"/>
        <source>Load images first, then place a starting point</source>
        <translation>Zuerst Bilder laden, dann einen Startpunkt setzen</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="398"/>
        <source>Starting points are already placed; clear them to auto-place</source>
        <translation>Startpunkte sind bereits gesetzt; zum automatischen Setzen zuerst leeren</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="404"/>
        <source>Draw the ROI first: the point is placed inside it</source>
        <translation>Zuerst die ROI zeichnen: Der Punkt wird darin gesetzt</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="411"/>
        <source>Starting point placed automatically at ({0:.0f}, {1:.0f})</source>
        <translation>Startpunkt automatisch gesetzt bei ({0:.0f}, {1:.0f})</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="419"/>
        <source>Load images first, then use the brush</source>
        <translation>Zuerst Bilder laden, dann den Pinsel verwenden</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="506"/>
        <source>Loading project…</source>
        <translation>Projekt wird geladen…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="508"/>
        <source>Could not open the project: {0}</source>
        <translation>Projekt konnte nicht geöffnet werden: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="511"/>
        <source>Could not open the project:
{0}

{1}</source>
        <translation>Projekt konnte nicht geöffnet werden:
{0}

{1}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="523"/>
        <source>Opened {0}</source>
        <translation>{0} geöffnet</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="546"/>
        <source>Open cancelled: {0}</source>
        <translation>Öffnen abgebrochen: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="553"/>
        <source>Camera {0}: {1} image(s) not found (was {2}). Results stay viewable and exportable; running again needs the images.</source>
        <translation>Kamera {0}: {1} Bild(er) nicht gefunden (bisher {2}). Die Ergebnisse bleiben sichtbar und exportierbar; für einen neuen Lauf werden die Bilder gebraucht.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="560"/>
        <source>Relocated {0} camera-{1} images: {2} -&gt; {3}</source>
        <translation>{0} Bilder von Kamera {1} neu zugeordnet: {2} -&gt; {3}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="567"/>
        <source>Calibration file found at {0}</source>
        <translation>Kalibrierdatei gefunden unter {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="572"/>
        <source>The calibration file was not found; using the copy saved in the project: {0}</source>
        <translation>Die Kalibrierdatei wurde nicht gefunden; die im Projekt gespeicherte Kopie wird verwendet: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="583"/>
        <source>Images Not Found</source>
        <translation>Bilder nicht gefunden</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="586"/>
        <source>Some of this project&apos;s images cannot be found. Open it anyway? Results stay viewable and exportable; running again needs the images.</source>
        <translation>Einige Bilder dieses Projekts wurden nicht gefunden. Trotzdem öffnen? Die Ergebnisse bleiben sichtbar und exportierbar; für einen neuen Lauf werden die Bilder gebraucht.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="592"/>
        <source>Open anyway</source>
        <translation>Trotzdem öffnen</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="601"/>
        <location filename="../../gui/main_window.py" line="611"/>
        <source>Locate Images</source>
        <translation>Bilder lokalisieren</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="603"/>
        <source>The selected folder does not contain this project&apos;s camera {0} frames. Pick the folder holding the original image files, or cancel to abort opening.</source>
        <translation>Der gewählte Ordner enthält nicht die Frames von Kamera {0} dieses Projekts. Wählen Sie den Ordner mit den ursprünglichen Bilddateien, oder brechen Sie ab, um den Ladevorgang zu beenden.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="613"/>
        <source>The image folder saved with this project was not found:
{0}

Select the folder that now contains the camera {1} frames (file names must match).</source>
        <translation>Der mit diesem Projekt gespeicherte Bildordner wurde nicht gefunden:
{0}

Wählen Sie den Ordner, der jetzt die Frames von Kamera {1} enthält (Dateinamen müssen übereinstimmen).</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="620"/>
        <source>Locate images for camera {0}</source>
        <translation>Bilder für Kamera {0} lokalisieren</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="662"/>
        <source>Include Results?</source>
        <translation>Ergebnisse einbeziehen?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="663"/>
        <source>Include the analysis results in this project file?</source>
        <translation>Die Analyseergebnisse in diese Projektdatei aufnehmen?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="666"/>
        <source>Including results (about {0} uncompressed) lets you reopen the project without recomputing. Choose No to save a small configuration-only file for sharing.</source>
        <translation>Mit Ergebnissen (ca. {0} unkomprimiert) lässt sich das Projekt ohne Neuberechnung wieder öffnen. „Nein“ speichert eine kleine, nur die Konfiguration enthaltende Datei zum Teilen.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="704"/>
        <source>unknown size</source>
        <translation>unbekannte Größe</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="714"/>
        <source>Saving project…</source>
        <translation>Projekt wird gespeichert…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="718"/>
        <source>Could not save the project: {0}</source>
        <translation>Projekt konnte nicht gespeichert werden: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="722"/>
        <source>Could not save the project:
{0}

{1}

The previous version of the file, if any, is unchanged.</source>
        <translation>Projekt konnte nicht gespeichert werden:
{0}

{1}

Eine vorhandene frühere Fassung der Datei ist unverändert.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="730"/>
        <source>Saved {0}</source>
        <translation>{0} gespeichert</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="436"/>
        <source>Untitled</source>
        <translation>Unbenannt</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="437"/>
        <source>{0}[*] — pyALDIC-3D</source>
        <translation>{0}[*] — pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="482"/>
        <source>New project</source>
        <translation>Neues Projekt</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="491"/>
        <location filename="../../gui/main_window.py" line="510"/>
        <source>Open Project</source>
        <translation>Projekt öffnen</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="493"/>
        <location filename="../../gui/main_window.py" line="648"/>
        <source>pyALDIC-3D project (*.aldic3d)</source>
        <translation>pyALDIC-3D-Projekt (*.aldic3d)</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="646"/>
        <location filename="../../gui/main_window.py" line="720"/>
        <source>Save Project</source>
        <translation>Projekt speichern</translation>
    </message>
</context>
<context>
    <name>ManualParamsDialog</name>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="53"/>
        <source>Manual Camera Parameters</source>
        <translation>Manuelle Kameraparameter</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="61"/>
        <source>Left camera (world frame)</source>
        <translation>Linke Kamera (Weltkoordinaten)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="62"/>
        <source>Right camera</source>
        <translation>Rechte Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="67"/>
        <source>Stereo extrinsics  (X_R = R · X_L + T)</source>
        <translation>Stereo-Extrinsik (X_R = R · X_L + T)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="71"/>
        <source>{0} (deg)</source>
        <translation>{0} (Grad)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="78"/>
        <source>{0} (mm)</source>
        <translation>{0} (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="87"/>
        <source>Euler composition R = Rz·Ry·Rx in degrees (MatchID/OpenCorr convention); distortion order k1, k2, p1, p2, k3 (OpenCV).</source>
        <translation>Euler-Komposition R = Rz·Ry·Rx in Grad (MatchID/OpenCorr-Konvention); Verzeichnungsreihenfolge k1, k2, p1, p2, k3 (OpenCV).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="101"/>
        <source>Save as YAML…</source>
        <translation>Als YAML speichern…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="106"/>
        <source>Cancel</source>
        <translation>Abbrechen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="142"/>
        <source>Baseline |T| = {0:.2f} mm</source>
        <translation>Basislinie |T| = {0:.2f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="147"/>
        <source>Baseline is zero — enter the translation T first.</source>
        <translation>Basislinie ist null — zuerst die Translation T eingeben.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="154"/>
        <source>Save calibration as</source>
        <translation>Kalibrierung speichern unter</translation>
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
        <translation>Netz:</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="40"/>
        <source>Line color and width of the mesh overlay (Show Grid)</source>
        <translation>Linienfarbe und -breite des Netz-Overlays (Gitter anzeigen)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="45"/>
        <source>Mesh overlay line color — click to choose</source>
        <translation>Linienfarbe des Netz-Overlays — zum Auswählen klicken</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="53"/>
        <source>Mesh overlay line width (screen pixels)</source>
        <translation>Linienbreite des Netz-Overlays (Bildschirmpixel)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="79"/>
        <source>Choose mesh line color</source>
        <translation>Netzlinienfarbe wählen</translation>
    </message>
</context>
<context>
    <name>NextStepHint</name>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="49"/>
        <source>Load the left and right camera folders</source>
        <translation>Die Ordner der linken und rechten Kamera laden</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="54"/>
        <source>Calibrate from images or import a calibration</source>
        <translation>Aus Bildern kalibrieren oder eine Kalibrierung importieren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="56"/>
        <source>Draw the ROI on the left camera, frame 1</source>
        <translation>Die ROI auf der linken Kamera, Bild 1, zeichnen</translation>
    </message>
</context>
<context>
    <name>PairActionsMixin</name>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="58"/>
        <source>Removed {0} image pair(s)</source>
        <translation>{0} Bildpaar(e) entfernt</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="69"/>
        <source>Remove Image Pairs</source>
        <translation>Bildpaare entfernen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="72"/>
        <source>Removing {0} pair(s) changes the sequence — the current results will be discarded. Continue?</source>
        <translation>Das Entfernen von {0} Paar(en) ändert die Sequenz — die aktuellen Ergebnisse werden verworfen. Fortfahren?</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="78"/>
        <source>Yes</source>
        <translation>Ja</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="79"/>
        <source>No</source>
        <translation>Nein</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="94"/>
        <source>Folder does not exist: {0}</source>
        <translation>Ordner existiert nicht: {0}</translation>
    </message>
</context>
<context>
    <name>PairBars</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="106"/>
        <source>no solve yet</source>
        <translation>noch keine Lösung</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="128"/>
        <source>worst-camera RMS per pair; dashed = reject threshold</source>
        <translation>schlechtester Kamera-RMS pro Paar; gestrichelt = Ausschlussschwelle</translation>
    </message>
</context>
<context>
    <name>PairListWidget</name>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="25"/>
        <source>Left</source>
        <translation>Links</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="25"/>
        <source>Right</source>
        <translation>Rechts</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="70"/>
        <source>Remove {0} selected pair(s)</source>
        <translation>{0} ausgewählte(s) Paar(e) entfernen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="73"/>
        <source>Reveal in Explorer</source>
        <translation>Im Explorer anzeigen</translation>
    </message>
</context>
<context>
    <name>PreviewTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="120"/>
        <source>Open this tab to render a preview.</source>
        <translation>Diesen Reiter öffnen, um eine Vorschau zu rendern.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="128"/>
        <source>Field</source>
        <translation>Feld</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="135"/>
        <source>Frame</source>
        <translation>Bild</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="144"/>
        <source>Camera</source>
        <translation>Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="148"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="226"/>
        <source>Left</source>
        <translation>Links</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="149"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="225"/>
        <source>Right</source>
        <translation>Rechts</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="180"/>
        <source>FIELD APPEARANCE</source>
        <translation>FELDDARSTELLUNG</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="185"/>
        <source>Colormap</source>
        <translation>Farbskala</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="187"/>
        <source>Auto</source>
        <translation>Auto</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="188"/>
        <source>Auto range</source>
        <translation>Auto-Bereich</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="191"/>
        <source>Range</source>
        <translation>Bereich</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="197"/>
        <source>Min</source>
        <translation>Min</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="198"/>
        <source>Max</source>
        <translation>Max</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="205"/>
        <source>Opacity</source>
        <translation>Deckkraft</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="207"/>
        <source>Apply to all fields</source>
        <translation>Auf alle Felder anwenden</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="210"/>
        <source>Apply this field&apos;s colormap, opacity and auto-range to every enabled field (each field keeps its own min/max).</source>
        <translation>Colormap, Deckkraft und Auto-Bereich dieses Felds auf alle aktivierten Felder anwenden (jedes Feld behält sein eigenes Min/Max).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="220"/>
        <source>COLORBAR STYLE</source>
        <translation>FARBLEISTEN-STIL</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="227"/>
        <source>Top</source>
        <translation>Oben</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="228"/>
        <source>Bottom</source>
        <translation>Unten</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="232"/>
        <source>Position</source>
        <translation>Position</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="238"/>
        <source>Font size</source>
        <translation>Schriftgröße</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="244"/>
        <source>Font family</source>
        <translation>Schriftart</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="252"/>
        <source>Bar thickness</source>
        <translation>Balkendicke</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="255"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="274"/>
        <source>Black</source>
        <translation>Schwarz</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="255"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="274"/>
        <source>White</source>
        <translation>Weiß</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="258"/>
        <source>Background</source>
        <translation>Hintergrund</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="266"/>
        <source>Add a blank border around the exported content, as a fraction of the long edge (0 = none).</source>
        <translation>Fügt einen leeren Rand um den exportierten Inhalt hinzu, als Anteil der langen Kante (0 = keiner).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="271"/>
        <source>Margin</source>
        <translation>Rand</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="277"/>
        <source>Margin color</source>
        <translation>Randfarbe</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="279"/>
        <source>Refresh preview</source>
        <translation>Vorschau aktualisieren</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="531"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="545"/>
        <source>Preview failed: </source>
        <translation>Vorschau fehlgeschlagen: </translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="430"/>
        <source>Enable a field on the Images tab to preview.</source>
        <translation>Aktivieren Sie ein Feld im Reiter „Images“ für die Vorschau.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="549"/>
        <source>No data for this field/frame.</source>
        <translation>Keine Daten für dieses Feld/Bild.</translation>
    </message>
</context>
<context>
    <name>Progress</name>
    <message>
        <location filename="../../gui/progress_text.py" line="30"/>
        <source>Preparing: checking the images and building the mesh</source>
        <translation>Vorbereitung: Bilder prüfen und Netz aufbauen</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="33"/>
        <source>Preparing: initial guess for the left camera</source>
        <translation>Vorbereitung: Startschätzung der linken Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="36"/>
        <source>Preparing: mesh and initial guess for the right camera</source>
        <translation>Vorbereitung: Netz und Startschätzung der rechten Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="39"/>
        <source>Preparing: estimating the stereo offset</source>
        <translation>Vorbereitung: Stereo-Versatz schätzen</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="42"/>
        <location filename="../../gui/progress_text.py" line="53"/>
        <source>tracking complete</source>
        <translation>Verfolgung abgeschlossen</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="43"/>
        <source>normalizing images</source>
        <translation>Bilder normieren</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="46"/>
        <location filename="../../gui/progress_text.py" line="49"/>
        <source>composing displacements</source>
        <translation>Verschiebungen zusammensetzen</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="52"/>
        <source>assembling results</source>
        <translation>Ergebnisse zusammenstellen</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="62"/>
        <source>Left camera</source>
        <translation>Linke Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="64"/>
        <source>Right camera</source>
        <translation>Rechte Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="66"/>
        <source>{0}: {1}</source>
        <translation>{0}: {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="74"/>
        <source>tracking frame {0} of {1}</source>
        <translation>Bild {0} von {1} wird verfolgt</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="80"/>
        <source>verifying frame {0} of {1} (keeping the frames tracked before the stop)</source>
        <translation>Bild {0} von {1} wird geprüft (die vor dem Stopp verfolgten Bilder bleiben)</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="85"/>
        <source>verifying frame {0} of {1}</source>
        <translation>Bild {0} von {1} wird geprüft</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="89"/>
        <source>assembling frame {0} of {1}</source>
        <translation>Bild {0} von {1} wird zusammengestellt</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="94"/>
        <source>strain: frame {0} of {1}</source>
        <translation>Dehnung: Bild {0} von {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="99"/>
        <source>Preparing: matching the two cameras at {0} nodes</source>
        <translation>Vorbereitung: beide Kameras an {0} Knoten zuordnen</translation>
    </message>
</context>
<context>
    <name>ProgressRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="156"/>
        <source>Cancel</source>
        <translation>Abbrechen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="173"/>
        <source>Exporting…</source>
        <translation>Exportiere…</translation>
    </message>
</context>
<context>
    <name>ROIToolbar</name>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="75"/>
        <source>+ Add</source>
        <translation>+ Hinzufügen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="77"/>
        <source>Add region to the Region of Interest (Polygon / Rectangle / Circle)</source>
        <translation>Region zum Interessenbereich hinzufügen (Polygon / Rechteck / Kreis)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="81"/>
        <source>Cut</source>
        <translation>Ausschneiden</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="83"/>
        <source>Cut region from the Region of Interest (Polygon / Rectangle / Circle)</source>
        <translation>Region aus dem Interessenbereich ausschneiden (Polygon / Rechteck / Kreis)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="87"/>
        <source>+ Refine</source>
        <translation>+ Verfeinern</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="90"/>
        <source>Paint extra mesh-refinement zones with a brush
(on the LEFT camera, frame 1 — the reference mesh geometry)</source>
        <translation>Zusätzliche Netzverfeinerungszonen mit einem Pinsel malen
(auf der LINKEN Kamera, Frame 1 — die Referenznetz-Geometrie)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="110"/>
        <source>Import</source>
        <translation>Importieren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="111"/>
        <source>Import mask from image file</source>
        <translation>Maske aus Bilddatei importieren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="120"/>
        <source>Save</source>
        <translation>Speichern</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="121"/>
        <source>Save current mask to PNG file</source>
        <translation>Aktuelle Maske als PNG-Datei speichern</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="126"/>
        <source>Invert</source>
        <translation>Invertieren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="127"/>
        <source>Invert the Region of Interest mask</source>
        <translation>Maske des Interessenbereichs invertieren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="132"/>
        <source>Clear</source>
        <translation>Leeren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="133"/>
        <source>Clear all Region of Interest masks</source>
        <translation>Alle Masken des Interessenbereichs leeren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="159"/>
        <source>Polygon</source>
        <translation>Polygon</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="163"/>
        <source>Rectangle</source>
        <translation>Rechteck</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="167"/>
        <source>Circle</source>
        <translation>Kreis</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="171"/>
        <source>Circle (3-point)</source>
        <translation>Kreis (3 Punkte)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="185"/>
        <source>Radius</source>
        <translation>Radius</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="202"/>
        <source>Paint</source>
        <translation>Malen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="206"/>
        <source>Erase</source>
        <translation>Radieren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="215"/>
        <source>Clear Brush</source>
        <translation>Pinsel leeren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="247"/>
        <source>Import Mask Image</source>
        <translation>Maskenbild importieren</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="249"/>
        <source>Images (*.png *.bmp *.tif *.tiff *.jpg *.jpeg);;All Files (*)</source>
        <translation>Bilder (*.png *.bmp *.tif *.tiff *.jpg *.jpeg);;Alle Dateien (*)</translation>
    </message>
</context>
<context>
    <name>RefUpdateSection3D</name>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="55"/>
        <source>Reference Update</source>
        <translation>Referenz-Update</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="60"/>
        <source>Every Frame</source>
        <translation>Jeder Frame</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="61"/>
        <source>Every N Frames</source>
        <translation>Alle N Frames</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="62"/>
        <source>Custom Frames</source>
        <translation>Benutzerdefiniert</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="65"/>
        <source>How often the incremental reference frame advances.
Every Frame (default): frame k matches against k−1 — tracks
large accumulated deformation, but drift can accumulate.
Every N Frames: the reference advances only every N frames —
less drift, needs correlation to survive N frames of motion.
Custom Frames: reference updates exactly at the listed frames.</source>
        <translation>Wie oft der inkrementelle Referenzframe weiterrückt.
Jeder Frame (Standard): Frame k wird gegen k−1 gematcht — verfolgt
große akkumulierte Verformung, Drift kann sich aufbauen.
Alle N Frames: die Referenz rückt nur alle N Frames vor — weniger
Drift, aber die Korrelation muss N Frames Bewegung überstehen.
Benutzerdefiniert: die Referenz wird genau an den gelisteten Frames
aktualisiert.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="78"/>
        <source>Update every</source>
        <translation>Update alle</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="85"/>
        <source> frames</source>
        <translation> Frames</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="87"/>
        <source>Reference-update interval N: frames k use the last reference at i·N &lt; k</source>
        <translation>Referenz-Update-Intervall N: Frame k nutzt die letzte Referenz bei i·N &lt; k</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="93"/>
        <source>e.g. 5, 10, 20 (0-based frame indices)</source>
        <translation>z. B. 5, 10, 20 (0-basierte Frame-Indizes)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="96"/>
        <source>Comma-separated 0-based frame indices that become reference
frames (frame 0 always is one). The last frame cannot be a
reference.</source>
        <translation>Kommagetrennte 0-basierte Frame-Indizes, die Referenzframes werden
(Frame 0 ist immer einer). Der letzte Frame kann keine Referenz sein.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="141"/>
        <source>Enter comma-separated 0-based frame numbers, e.g. 5, 10, 20</source>
        <translation>Kommagetrennte 0-basierte Frame-Nummern eingeben, z. B. 5, 10, 20</translation>
    </message>
</context>
<context>
    <name>RightSidebar3D</name>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="99"/>
        <source>Run 3D Analysis</source>
        <translation>3D-Analyse starten</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="105"/>
        <location filename="../../gui/panels/right_sidebar.py" line="456"/>
        <source>Run the full stereo correspondence + triangulation pipeline on the loaded image pairs (F5).</source>
        <translation>Führt die vollständige Pipeline aus Stereokorrespondenz + Triangulation auf den geladenen Bildpaaren aus (F5).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="112"/>
        <source>Cancel</source>
        <translation>Abbrechen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="127"/>
        <source>Export Results</source>
        <translation>Ergebnisse exportieren</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="135"/>
        <source>Open Strain Window</source>
        <translation>Dehnungsfenster öffnen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="148"/>
        <source>Parameters changed since this result — re-run to update</source>
        <translation>Parameter seit diesem Ergebnis geändert — zum Aktualisieren erneut ausführen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="156"/>
        <source>PROGRESS</source>
        <translation>FORTSCHRITT</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="163"/>
        <location filename="../../gui/panels/right_sidebar.py" line="638"/>
        <source>Ready</source>
        <translation>Bereit</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="168"/>
        <source>ELAPSED  --:--</source>
        <translation>VERSTRICHEN  --:--</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="171"/>
        <source>REMAINING  --:--</source>
        <translation>VERBLEIBEND  --:--</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="177"/>
        <source>FIELD</source>
        <translation>FELD</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="183"/>
        <source>Show on deformed frame</source>
        <translation>Auf deformiertem Frame anzeigen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="187"/>
        <source>When checked, overlay results on the deformed (current) frame instead of the reference frame</source>
        <translation>Wenn aktiviert, werden die Ergebnisse auf dem deformierten (aktuellen) Frame statt auf dem Referenzframe überlagert</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="196"/>
        <source>Camera</source>
        <translation>Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="200"/>
        <source>Left</source>
        <translation>Links</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="203"/>
        <source>Show the LEFT camera&apos;s images (the reference view: ROI, seed and mesh live here). Default.</source>
        <translation>Zeigt die Bilder der LINKEN Kamera (Referenzansicht: ROI, Startpunkt und Netz leben hier). Standard.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="207"/>
        <source>Right</source>
        <translation>Rechts</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="210"/>
        <source>Show the RIGHT camera&apos;s images with the field warped onto them — a cross-check that the stereo match is sound.</source>
        <translation>Zeigt die Bilder der RECHTEN Kamera mit dem darauf verzerrten Feld — ein Gegencheck, dass der Stereoabgleich stimmt.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="226"/>
        <source>VISUALIZATION</source>
        <translation>VISUALISIERUNG</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="229"/>
        <source>Colormap</source>
        <translation>Farbskala</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="237"/>
        <source>Colormap for the field overlay and the 3D surface. Default turbo (perceptually ordered, high contrast); pick RdBu_r or coolwarm for signed fields centered on zero.</source>
        <translation>Farbskala für die Feld-Überlagerung und die 3D-Oberfläche. Standard: turbo (wahrnehmungsgeordnet, kontraststark); für vorzeichenbehaftete Felder um Null RdBu_r oder coolwarm wählen.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="246"/>
        <source>Auto range</source>
        <translation>Auto-Bereich</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="250"/>
        <source>Rescale the color range to each frame&apos;s data range (2–98 percentile of the visible values). Default on; uncheck to type fixed Min/Max bounds that hold across frames.</source>
        <translation>Farbbereich an den Datenbereich jedes Frames anpassen (2–98-Perzentil der sichtbaren Werte). Standard: an; abwählen, um feste Min/Max-Grenzen einzugeben, die über alle Frames gelten.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="262"/>
        <source>Min</source>
        <translation>Min</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="270"/>
        <source>Lower color-range bound (only with Auto range off)</source>
        <translation>Untere Grenze des Farbbereichs (nur bei ausgeschaltetem Auto-Bereich)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="271"/>
        <source>Upper color-range bound (only with Auto range off)</source>
        <translation>Obere Grenze des Farbbereichs (nur bei ausgeschaltetem Auto-Bereich)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="277"/>
        <source>Max</source>
        <translation>Max</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="283"/>
        <source>Opacity</source>
        <translation>Deckkraft</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="290"/>
        <source>Overlay opacity (0 = transparent, 100 = opaque)</source>
        <translation>Deckkraft der Überlagerung (0 = transparent, 100 = deckend)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="297"/>
        <source>UNITS</source>
        <translation>EINHEITEN</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="304"/>
        <source>LOG</source>
        <translation>PROTOKOLL</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="313"/>
        <source>All messages</source>
        <translation>Alle Meldungen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="314"/>
        <source>Info</source>
        <translation>Info</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="315"/>
        <source>Warnings + errors</source>
        <translation>Warnungen + Fehler</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="316"/>
        <source>Errors only</source>
        <translation>Nur Fehler</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="319"/>
        <source>Show only log messages of this severity</source>
        <translation>Nur Protokollmeldungen dieser Stufe anzeigen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="322"/>
        <source>Save…</source>
        <translation>Speichern…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="327"/>
        <source>Save the full log to a text file</source>
        <translation>Das vollständige Protokoll als Textdatei speichern</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="330"/>
        <source>Clear</source>
        <translation>Leeren</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="335"/>
        <source>Clear the log console (messages are not recoverable)</source>
        <translation>Protokollkonsole leeren (Meldungen sind nicht wiederherstellbar)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="419"/>
        <source>Save log</source>
        <translation>Protokoll speichern</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="419"/>
        <source>Text files (*.txt)</source>
        <translation>Textdateien (*.txt)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="430"/>
        <source>Log saved to {0}</source>
        <translation>Protokoll gespeichert unter {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="452"/>
        <location filename="../../gui/panels/right_sidebar.py" line="468"/>
        <source>Not ready — {0}</source>
        <translation>Nicht bereit — {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="472"/>
        <source>Ready to run. No starting point: the stereo offset is found automatically and frame 1 is seeded by FFT.</source>
        <translation>Bereit zum Start. Kein Startpunkt: Der Stereo-Versatz wird automatisch bestimmt, Bild 1 per FFT initialisiert.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="477"/>
        <source>Ready to run.</source>
        <translation>Bereit zur Ausführung.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="512"/>
        <source>Export displacement and strain results to NPZ / MAT / CSV</source>
        <translation>Verschiebungs- und Dehnungsergebnisse als NPZ / MAT / CSV exportieren</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="516"/>
        <source>Compute and visualize strain in a separate post-processing window. Requires displacement results from a completed Run.</source>
        <translation>Dehnung in einem separaten Nachbearbeitungsfenster berechnen und visualisieren. Benötigt Verschiebungsergebnisse eines abgeschlossenen Laufs.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="522"/>
        <source>Available after the running analysis finishes.</source>
        <translation>Verfügbar, sobald die laufende Analyse abgeschlossen ist.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="524"/>
        <source>Run an analysis first — there are no results yet.</source>
        <translation>Führen Sie zuerst eine Analyse aus — es gibt noch keine Ergebnisse.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="542"/>
        <source>Not ready: {0}</source>
        <translation>Nicht bereit: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="559"/>
        <source>Starting 3D analysis…</source>
        <translation>3D-Analyse wird gestartet…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="578"/>
        <source>Cancelling — finishing current frame…</source>
        <translation>Abbruch läuft — aktueller Frame wird abgeschlossen…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="579"/>
        <source>Cancelling…</source>
        <translation>Wird abgebrochen…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="604"/>
        <source>Stopped early — partial results kept</source>
        <translation>Vorzeitig gestoppt — Teilergebnisse behalten</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="597"/>
        <source>Analysis complete</source>
        <translation>Analyse abgeschlossen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="427"/>
        <location filename="../../gui/panels/right_sidebar.py" line="616"/>
        <source>Failed: {0}</source>
        <translation>Fehlgeschlagen: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="118"/>
        <source>Cancel the current analysis. Frames computed so far are kept as a partial result; only when nothing was computed yet does the run return to IDLE.</source>
        <translation>Bricht die aktuelle Analyse ab. Bereits berechnete Frames werden als Teilergebnis behalten; nur wenn noch nichts berechnet wurde, kehrt der Lauf in den Leerlauf zurück.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="615"/>
        <source>Analysis failed</source>
        <translation>Analyse fehlgeschlagen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="620"/>
        <source>Analysis Failed</source>
        <translation>Analyse fehlgeschlagen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="622"/>
        <source>The analysis stopped with an error:

{0}

The log has the details.</source>
        <translation>Die Analyse wurde mit einem Fehler beendet:

{0}

Einzelheiten stehen im Protokoll.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="641"/>
        <source>Run cancelled</source>
        <translation>Lauf abgebrochen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="556"/>
        <location filename="../../gui/panels/right_sidebar.py" line="639"/>
        <location filename="../../gui/panels/right_sidebar.py" line="648"/>
        <source>ELAPSED  {0}</source>
        <translation>VERSTRICHEN  {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="557"/>
        <location filename="../../gui/panels/right_sidebar.py" line="596"/>
        <location filename="../../gui/panels/right_sidebar.py" line="640"/>
        <location filename="../../gui/panels/right_sidebar.py" line="654"/>
        <source>REMAINING  {0}</source>
        <translation>VERBLEIBEND  {0}</translation>
    </message>
</context>
<context>
    <name>RunSummaryMixin</name>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="25"/>
        <source>Analysis complete</source>
        <translation>Analyse abgeschlossen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="41"/>
        <source>Stopped early at frame {0}/{1} — kept {2} computed frames (later frames are empty)</source>
        <translation>Vorzeitig gestoppt bei Frame {0}/{1} — {2} berechnete Frames behalten (spätere Frames sind leer)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="47"/>
        <source>Run interrupted: {0}</source>
        <translation>Lauf unterbrochen: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="51"/>
        <source>Frame-1 stereo match: {0}/{1} points matched ({2}%)</source>
        <translation>Stereo-Zuordnung Frame 1: {0}/{1} Punkte zugeordnet ({2} %)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="59"/>
        <source>Camera {0}: validity gate removed {1} node-frames (correlation vs frame 1 failed)</source>
        <translation>Kamera {0}: Validitätsgate entfernte {1} Knoten-Frames (Korrelation mit Frame 1 fehlgeschlagen)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="66"/>
        <source>Frame {0}: only {1}% of points valid</source>
        <translation>Frame {0}: nur {1} % der Punkte gültig</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="73"/>
        <source>Quality gate (ZNSSD) removed {0} positions</source>
        <translation>Qualitätsgate (ZNSSD) entfernte {0} Positionen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="74"/>
        <source>Reprojection gate removed {0} positions</source>
        <translation>Reprojektionsgate entfernte {0} Positionen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="75"/>
        <source>3D outlier filter removed {0} positions</source>
        <translation>3D-Ausreißerfilter entfernte {0} Positionen</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="89"/>
        <source>Validity falls from {0}% (frame 1) to {1}%: tracking every frame against frame 1 cannot follow large deformation. Try WORKFLOW TYPE &gt; Incremental.</source>
        <translation>Die Gültigkeit fällt von {0} % (Bild 1) auf {1} %: Jedes Bild gegen Bild 1 zu verfolgen, hält großen Verformungen nicht stand. WORKFLOW-TYP &gt; Inkrementell versuchen.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="95"/>
        <source>Validity falls from {0}% (frame 1) to {1}%: if the valid region changes during the test (cracks, failure), import per-frame masks (REGION OF INTEREST).</source>
        <translation>Die Gültigkeit fällt von {0} % (Bild 1) auf {1} %: Ändert sich der gültige Bereich im Versuch (Risse, Versagen), Masken pro Bild importieren (INTERESSENBEREICH).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="103"/>
        <source>No valid points in ANY frame — the run produced an empty result. Check ROI, masks and seeding (details above).</source>
        <translation>Keine gültigen Punkte in IRGENDEINEM Frame — der Lauf lieferte ein leeres Ergebnis. Prüfen Sie ROI, Masken und Startpunkt (Details oben).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="111"/>
        <source>Analysis complete — {0} frames, median validity {1}%, {2} frame(s) below {3}% (see above)</source>
        <translation>Analyse abgeschlossen — {0} Frames, mediane Validität {1} %, {2} Frame(s) unter {3} % (siehe oben)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="124"/>
        <source>Analysis complete — {0} frames, median validity {1}%</source>
        <translation>Analyse abgeschlossen — {0} Bilder, mittlere Gültigkeit {1} %</translation>
    </message>
</context>
<context>
    <name>RunWarnings</name>
    <message>
        <location filename="../../gui/warning_text.py" line="24"/>
        <source>No Starting Point placed: frame 1 is seeded by an FFT search (place a point for large first-frame motion)</source>
        <translation>Kein Startpunkt gesetzt: Bild 1 wird per FFT-Suche initialisiert (bei großer Bewegung im ersten Bild einen Punkt setzen)</translation>
    </message>
    <message>
        <location filename="../../gui/warning_text.py" line="32"/>
        <source>FFT search range reduced from {0} to {1} px to fit the {2} × {3} px images</source>
        <translation>FFT-Suchbereich von {0} auf {1} px verkleinert, passend zu den {2} × {3} px großen Bildern</translation>
    </message>
</context>
<context>
    <name>ShortcutsDialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="74"/>
        <source>Keyboard Shortcuts</source>
        <translation>Tastenkürzel</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="86"/>
        <source>Run the 3D analysis</source>
        <translation>3D-Analyse starten</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="87"/>
        <source>Fit the image to the viewport</source>
        <translation>Bild in den Viewport einpassen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="88"/>
        <source>Zoom in / out</source>
        <translation>Vergrößern / Verkleinern</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="89"/>
        <source>Previous / next frame</source>
        <translation>Vorheriges / nächstes Bild</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="90"/>
        <source>Play / pause (on the canvas: hold to pan)</source>
        <translation>Wiedergabe / Pause (auf der Leinwand: halten zum Verschieben)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="91"/>
        <source>New project</source>
        <translation>Neues Projekt</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="92"/>
        <source>Open a project</source>
        <translation>Projekt öffnen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="93"/>
        <source>Save the project</source>
        <translation>Projekt speichern</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="94"/>
        <source>Save the project as…</source>
        <translation>Projekt speichern unter…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="95"/>
        <source>Cancel the active drawing tool</source>
        <translation>Aktives Zeichenwerkzeug abbrechen</translation>
    </message>
</context>
<context>
    <name>StrainFieldSelector3D</name>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="46"/>
        <source>εxx — normal strain along the strain frame&apos;s x axis</source>
        <translation>εxx — Normaldehnung entlang der x-Achse des Dehnungskoordinatensystems</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="47"/>
        <source>εyy — normal strain along the strain frame&apos;s y axis</source>
        <translation>εyy — Normaldehnung entlang der y-Achse des Dehnungskoordinatensystems</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="48"/>
        <source>εxy — in-plane shear strain (tensor component)</source>
        <translation>εxy — Schubdehnung in der Ebene (Tensorkomponente)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="49"/>
        <source>ε₁ — major principal strain (largest in-plane eigenvalue)</source>
        <translation>ε₁ — größte Hauptdehnung (größter Eigenwert in der Ebene)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="50"/>
        <source>ε₂ — minor principal strain (smallest in-plane eigenvalue)</source>
        <translation>ε₂ — kleinste Hauptdehnung (kleinster Eigenwert in der Ebene)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="51"/>
        <source>γ max — maximum shear strain, (ε₁ − ε₂) / 2</source>
        <translation>γ max — maximale Schubdehnung, (ε₁ − ε₂) / 2</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="52"/>
        <source>von Mises — equivalent strain (plane-stress invariant)</source>
        <translation>von Mises — Vergleichsdehnung (Invariante im ebenen Spannungszustand)</translation>
    </message>
</context>
<context>
    <name>StrainNavigator3D</name>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="52"/>
        <source>Previous frame (←)</source>
        <translation>Vorheriger Frame (←)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="59"/>
        <location filename="../../gui/widgets/strain_navigator.py" line="128"/>
        <source>Play animation (Space)</source>
        <translation>Animation abspielen (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="66"/>
        <source>Next frame (→)</source>
        <translation>Nächster Frame (→)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="75"/>
        <source>Playback speed (frames per second). Default 2 fps.</source>
        <translation>Wiedergabegeschwindigkeit (Frames pro Sekunde). Standard 2 fps.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="79"/>
        <location filename="../../gui/widgets/strain_navigator.py" line="198"/>
        <source>FRAME 0/0</source>
        <translation>FRAME 0/0</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="181"/>
        <source>Pause animation (Space)</source>
        <translation>Animation pausieren (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="196"/>
        <source>FRAME {0}/{1}</source>
        <translation>FRAME {0}/{1}</translation>
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
        <translation>Seitenlänge (in Pixeln) des quadratischen Fensters um jeden Knoten, in dem der lokale Verschiebungsgradient gefittet wird (die virtuelle Dehnungsmessstelle).

• Größeres Fenster → glattere Dehnung, geringere räumliche Auflösung.
• Kleineres Fenster → schärfere Dehnung, mehr Rauschen.
• Muss mindestens 3×3 Knoten umfassen: ≥ 2 × Knotenabstand + 1 px verwenden.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="89"/>
        <source>Strain window</source>
        <translation>VSG-Fenster</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="101"/>
        <source>Number of mesh nodes per axis inside the square strain window — the local plane fit uses every valid node in it. The mm size maps the pixel window through the median 3D spacing of adjacent nodes on the reference surface.</source>
        <translation>Anzahl der Netzknoten pro Achse innerhalb des quadratischen VSG-Fensters — die lokale Ebenenanpassung verwendet jeden gültigen Knoten darin. Die mm-Größe rechnet das Pixelfenster über den Median des 3D-Abstands benachbarter Knoten auf der Referenzoberfläche um.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="119"/>
        <source>Green-Lagrange (default)</source>
        <translation>Green-Lagrange (Standard)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="120"/>
        <source>Infinitesimal</source>
        <translation>Infinitesimal</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="124"/>
        <source>Almansi (Eulerian, true tensor)</source>
        <translation>Almansi (Euler, echter Tensor)</translation>
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
        <translation>Finite-Dehnungs-Maß aus demselben Verschiebungsgradienten-Fit, im
selben Tangentialsystem:
Green-Lagrange E = ½(FᵀF − I) — finite Dehnung, Referenzkonfiguration
(Standard).
Infinitesimal e = ½(∇u + ∇uᵀ) — Linearisierung kleiner Dehnungen.
Almansi (Euler, echter Tensor) e = ½(I − F⁻ᵀF⁻¹) — der EXAKTE finite
Dehnungstensor in der verformten Konfiguration. Dies ist NICHT die
linearisierte achsenweise „Euler-Almansi“-Formel der 2D-App
(1/(1−∂u/∂x)−1, …), die bei 10 % Dehnung um ~22 % abweicht.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="139"/>
        <source>Strain type</source>
        <translation>Dehnungstyp</translation>
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
        <translation>Blendet unzuverlässige Dehnung nahe ungültigen oder fehlenden Knoten
aus, wo das Dehnungsfenster einseitig den Halt verliert und der lokale
Ebenen-Fit unzuverlässig wird.
Koeffizient × Fensterradius = Breite des beschnittenen Bandes (in px
auf dem Referenzgitter).
0,00 = alle Knoten behalten (kein Beschnitt) · 0,70 = empfohlen ·
1,00 = am strengsten. Die Verschiebung bleibt unberührt.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="161"/>
        <source>Trim low-confidence edges</source>
        <translation>Ränder mit geringer Konfidenz beschneiden</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="188"/>
        <source>Off</source>
        <translation>Aus</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="189"/>
        <source>Light (σ = 0.5 × step)</source>
        <translation>Leicht (σ = 0,5 × step)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="190"/>
        <source>Medium (σ = 1 × step)</source>
        <translation>Mittel (σ = 1 × step)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="191"/>
        <source>Strong (σ = 2 × step) ⚠</source>
        <translation>Stark (σ = 2 × step) ⚠</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="197"/>
        <source>Gaussian smoothing of the displacement field before the gradient fit.
σ is the kernel width; step = DIC node spacing.
  Light  (0.5 × step): subtle, preserves fine features.
  Medium (1 × step): balanced, for noisy data.
  Strong (2 × step) ⚠: aggressive, may blur real gradients.</source>
        <translation>Gauß-Glättung des Verschiebungsfelds vor dem Gradienten-Fit.
σ ist die Kernbreite; step = DIC-Knotenabstand.
  Leicht (0,5 × step): dezent, erhält feine Merkmale.
  Mittel (1 × step): ausgewogen, für verrauschte Daten.
  Stark (2 × step) ⚠: aggressiv, kann echte Gradienten verwischen.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="204"/>
        <source>Strain field smoothing</source>
        <translation>Dehnungsfeldglättung</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="208"/>
        <source>Surface tangent plane</source>
        <translation>Tangentialebene der Oberfläche</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="209"/>
        <source>Left camera frame</source>
        <translation>Koordinatensystem der linken Kamera</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="210"/>
        <source>Custom (3 points)</source>
        <translation>Benutzerdefiniert (3 Punkte)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="213"/>
        <source>Per-node tangent plane fitted to the reference surface: z is the surface normal pointing toward the camera, x is the left-camera +X projected onto the plane, y = z × x. The right default for curved specimens.</source>
        <translation>Pro Knoten an die Referenzfläche gefittete Tangentialebene: z ist die zur Kamera zeigende Flächennormale, x die Projektion der +X-Achse der linken Kamera auf die Ebene, y = z × x. Der richtige Standard für gekrümmte Proben.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="219"/>
        <source>Report strain in the fixed left-camera (world) axes. Meaningful for flat specimens aligned with the image plane.</source>
        <translation>Dehnung in den festen Achsen der linken Kamera (Weltkoordinaten) angeben. Sinnvoll für ebene, zur Bildebene ausgerichtete Proben.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="223"/>
        <source>A fixed specimen frame built from 3 picked points on the reference image: Origin, a point along +X, and a point on the +Y side.</source>
        <translation>Ein festes Proben-Koordinatensystem aus 3 im Referenzbild gewählten Punkten: Ursprung, ein Punkt entlang +X und ein Punkt auf der +Y-Seite.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="241"/>
        <source>Coordinate system</source>
        <translation>Koordinatensystem</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="246"/>
        <source>Pick 3 points…</source>
        <translation>3 Punkte wählen…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="251"/>
        <source>Click three points on the reference image: the Origin, a point along +X, then a point on the +Y side. Each click snaps to the nearest valid mesh node. Enabled only for Custom (3 points).</source>
        <translation>Klicken Sie drei Punkte auf dem Referenzbild an: den Ursprung, einen Punkt entlang +X, dann einen Punkt auf der +Y-Seite. Jeder Klick rastet am nächsten gültigen Netzknoten ein. Nur bei „Benutzerdefiniert (3 Punkte)“ aktiv.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="307"/>
        <source>Trimmed: {0} nodes ({1}%)</source>
        <translation>Beschnitten: {0} Knoten ({1}%)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="315"/>
        <source>Crack-aware: ROI barrier honored (mesh, strain, render)</source>
        <translation>Rissbewusst: ROI-Barriere berücksichtigt (Netz, Dehnung, Rendering)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="405"/>
        <source>Strain window ≈ {0}×{1} nodes</source>
        <translation>VSG-Fenster ≈ {0}×{1} Knoten</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="409"/>
        <source>≈ {0} × {1} mm</source>
        <translation>≈ {0} × {1} mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="419"/>
        <source>⚠ Window radius ({0} px) &lt; node spacing ({1} px); the plane fit needs a 3×3 node gauge. Use ≥ {2} px.</source>
        <translation>⚠ Fensterradius ({0} px) &lt; Knotenabstand ({1} px); der Ebenen-Fit braucht eine 3×3-Knoten-Messstelle. ≥ {2} px verwenden.</translation>
    </message>
</context>
<context>
    <name>StrainRenderMixin</name>
    <message>
        <location filename="../../gui/strain_canvas.py" line="230"/>
        <source>Could not draw the overlay: {0}</source>
        <translation>Overlay konnte nicht gezeichnet werden: {0}</translation>
    </message>
</context>
<context>
    <name>StrainVizPanel3D</name>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="35"/>
        <source>Show on deformed frame</source>
        <translation>Auf deformiertem Frame anzeigen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="39"/>
        <source>When checked, overlay results on the deformed (current) frame instead of the reference frame</source>
        <translation>Wenn aktiviert, werden die Ergebnisse auf dem deformierten (aktuellen) Frame statt auf dem Referenzframe überlagert</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="49"/>
        <source>Colormap for the strain overlay. Default turbo; pick RdBu_r or coolwarm for signed strain centered on zero.</source>
        <translation>Farbskala für die Dehnungsüberlagerung. Standard: turbo; für vorzeichenbehaftete Dehnung um Null RdBu_r oder coolwarm wählen.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="53"/>
        <source>Colormap</source>
        <translation>Farbskala</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="55"/>
        <source>Auto range</source>
        <translation>Auto-Bereich</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="59"/>
        <source>Rescale the color range to each frame&apos;s data range (2–98 percentile of the visible values). Default on; uncheck to type fixed Min/Max bounds that hold across frames.</source>
        <translation>Farbbereich an den Datenbereich jedes Frames anpassen (2–98-Perzentil der sichtbaren Werte). Standard: an; abwählen, um feste Min/Max-Grenzen einzugeben, die über alle Frames gelten.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="74"/>
        <source>Lower color-range bound (only with Auto range off)</source>
        <translation>Untere Grenze des Farbbereichs (nur bei ausgeschaltetem Auto-Bereich)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="75"/>
        <source>Upper color-range bound (only with Auto range off)</source>
        <translation>Obere Grenze des Farbbereichs (nur bei ausgeschaltetem Auto-Bereich)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="82"/>
        <source>Min</source>
        <translation>Min</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="84"/>
        <source>Max</source>
        <translation>Max</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="93"/>
        <source>Overlay opacity (0 = transparent, 100 = opaque)</source>
        <translation>Deckkraft der Überlagerung (0 = transparent, 100 = deckend)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="94"/>
        <source>Opacity</source>
        <translation>Deckkraft</translation>
    </message>
</context>
<context>
    <name>StrainWindow3D</name>
    <message>
        <location filename="../../gui/strain_window.py" line="111"/>
        <source>Strain Post-Processing</source>
        <translation>Dehnungs-Nachbearbeitung</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="151"/>
        <source>STRAIN PARAMETERS</source>
        <translation>DEHNUNGSPARAMETER</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="161"/>
        <source>Compute Strain</source>
        <translation>Dehnung berechnen</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="167"/>
        <source>Export Results</source>
        <translation>Ergebnisse exportieren</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="171"/>
        <location filename="../../gui/strain_window.py" line="680"/>
        <source>Export displacement and strain results to NPZ / MAT / CSV</source>
        <translation>Verschiebungs- und Dehnungsergebnisse als NPZ / MAT / CSV exportieren</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="190"/>
        <source>Cancel</source>
        <translation>Abbrechen</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="192"/>
        <source>Stop the strain computation at the next frame.</source>
        <translation>Die Dehnungsberechnung beim nächsten Frame anhalten.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="201"/>
        <source>FIELD</source>
        <translation>FELD</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="207"/>
        <source>VISUALIZATION</source>
        <translation>VISUALISIERUNG</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="211"/>
        <source>LOG</source>
        <translation>PROTOKOLL</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="334"/>
        <source>Computation Running</source>
        <translation>Berechnung läuft</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="335"/>
        <source>A strain computation is running — cancel it and close?</source>
        <translation>Eine Dehnungsberechnung läuft — abbrechen und schließen?</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="340"/>
        <source>Yes</source>
        <translation>Ja</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="341"/>
        <source>No</source>
        <translation>Nein</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="401"/>
        <location filename="../../gui/strain_window.py" line="466"/>
        <location filename="../../gui/strain_window.py" line="580"/>
        <source>Strain compute failed: {0}</source>
        <translation>Dehnungsberechnung fehlgeschlagen: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="413"/>
        <location filename="../../gui/strain_window.py" line="543"/>
        <source>Run 3D analysis first — no results to post-process.</source>
        <translation>Zuerst die 3D-Analyse ausführen — keine Ergebnisse zur Nachbearbeitung.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="416"/>
        <location filename="../../gui/strain_window.py" line="554"/>
        <location filename="../../gui/strain_window.py" line="582"/>
        <source>Click Origin, then +X, then +Y on the image</source>
        <translation>Klicken Sie im Bild auf den Ursprung, dann +X, dann +Y</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="423"/>
        <source>Computing strain…</source>
        <translation>Dehnung wird berechnet…</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="440"/>
        <source>Cancelling…</source>
        <translation>Wird abgebrochen…</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="445"/>
        <source>Computing strain… {0}%</source>
        <translation>Dehnung wird berechnet… {0}%</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="457"/>
        <source>Complete</source>
        <translation>Abgeschlossen</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="471"/>
        <source>Strain computation cancelled.</source>
        <translation>Dehnungsberechnung abgebrochen.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="476"/>
        <source>Strain computation complete.</source>
        <translation>Dehnungsberechnung abgeschlossen.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="481"/>
        <source>⚠ Params changed -- click Compute Strain</source>
        <translation>⚠ Parameter geändert — „Dehnung berechnen“ klicken</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="565"/>
        <source>No valid point near the click — pick on the result field</source>
        <translation>Kein gültiger Punkt nahe dem Klick — auf dem Ergebnisfeld wählen</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="573"/>
        <location filename="../../gui/strain_window.py" line="590"/>
        <source>Picked {0}/3 points</source>
        <translation>{0}/3 Punkte gewählt</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="592"/>
        <source>x→{0}  y→{1}  z→{2}</source>
        <translation>x→{0}  y→{1}  z→{2}</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="603"/>
        <source>O</source>
        <translation>O</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="603"/>
        <source>+X</source>
        <translation>+X</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="603"/>
        <source>+Y</source>
        <translation>+Y</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="665"/>
        <source>Run a 3D analysis first — strain needs displacement results.</source>
        <translation>Führen Sie zuerst eine 3D-Analyse aus — die Dehnung braucht Verschiebungsergebnisse.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="669"/>
        <source>Pick the 3 specimen-frame points first (Origin, +X, +Y).</source>
        <translation>Wählen Sie zuerst die 3 Punkte des Probenkoordinatensystems (Ursprung, +X, +Y).</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="674"/>
        <source>Compute Green-Lagrange surface strain from the displacement field with the parameters above.</source>
        <translation>Green-Lagrange-Oberflächendehnung aus dem Verschiebungsfeld mit den obigen Parametern berechnen.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="684"/>
        <source>Run an analysis first — there are no results yet.</source>
        <translation>Führen Sie zuerst eine Analyse aus — es gibt noch keine Ergebnisse.</translation>
    </message>
</context>
<context>
    <name>UnitsSection3D</name>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="37"/>
        <source>Display unit for displacement and velocity values (colorbar,
3D scalar bar). Display only — the data and every export stay
in millimetres. Strain is dimensionless and unaffected.</source>
        <translation>Anzeigeeinheit für Verschiebungs- und Geschwindigkeitswerte
(Farbbalken, 3D-Skalarbalken). Nur Anzeige — Daten und alle Exporte
bleiben in Millimetern. Dehnung ist dimensionslos und unberührt.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="42"/>
        <source>Display unit</source>
        <translation>Anzeigeeinheit</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="49"/>
        <source>not set (per frame)</source>
        <translation>nicht gesetzt (pro Bild)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="54"/>
        <source>Acquisition frame rate. Used only by the Velocity field:
velocity = |D(k) − D(k−1)| × frame rate, shown in the
display unit per second. Leave it at &apos;not set&apos; to see the
velocity per frame.</source>
        <translation>Aufnahme-Bildrate. Nur für das Geschwindigkeitsfeld:
Geschwindigkeit = |D(k) − D(k−1)| × Bildrate, in der
Anzeigeeinheit pro Sekunde. Auf 'nicht gesetzt' lassen, um die
Geschwindigkeit pro Bild zu sehen.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="60"/>
        <source>Frame rate</source>
        <translation>Bildrate</translation>
    </message>
</context>
<context>
    <name>View3D</name>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="129"/>
        <source>3D view — run an analysis to see the reconstructed surface.</source>
        <translation>3D-Ansicht — führen Sie eine Analyse aus, um die rekonstruierte Oberfläche zu sehen.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="170"/>
        <location filename="../../gui/widgets/view3d.py" line="259"/>
        <source>3D view unavailable: {0}</source>
        <translation>3D-Ansicht nicht verfügbar: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="232"/>
        <source>Starting the 3D view…</source>
        <translation>3D-Ansicht wird gestartet…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="264"/>
        <source>No valid 3D points in this frame — nothing to display.</source>
        <translation>Keine gültigen 3D-Punkte in diesem Frame — nichts anzuzeigen.</translation>
    </message>
</context>
<context>
    <name>View3DTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="72"/>
        <source>Field</source>
        <translation>Feld</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="84"/>
        <source>Colormap</source>
        <translation>Farbskala</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="93"/>
        <source>Resolution</source>
        <translation>Auflösung</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="106"/>
        <source>Auto range</source>
        <translation>Auto-Bereich</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="109"/>
        <source>Like the 3D view: each frame&apos;s 2–98 percentile of the values inside the ROI. Untick to use a fixed Min/Max for every frame.</source>
        <translation>Wie in der 3D-Ansicht: pro Frame das 2–98-Perzentil der Werte innerhalb der ROI. Abwählen, um für alle Frames feste Min/Max-Werte zu verwenden.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="116"/>
        <source>Min</source>
        <translation>Min</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="122"/>
        <source>Max</source>
        <translation>Max</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="135"/>
        <source>Frame sequence</source>
        <translation>Bildsequenz</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="138"/>
        <source>Per-frame image sequence (PNG)</source>
        <translation>Bildsequenz pro Frame (PNG)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="143"/>
        <source>Animation</source>
        <translation>Animation</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="150"/>
        <source>Frames per second</source>
        <translation>Bilder pro Sekunde</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="157"/>
        <source>Frame step</source>
        <translation>Bildschritt</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="171"/>
        <source>Turntable</source>
        <translation>Rundumdrehung</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="176"/>
        <source>Turntable (360° orbit at frame {0})</source>
        <translation>Rundumdrehung (360°-Orbit bei Bild {0})</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="179"/>
        <source>Orbit frames</source>
        <translation>Orbit-Bilder</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="204"/>
        <source>Export 3D View</source>
        <translation>3D-Ansicht exportieren</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="262"/>
        <source>GIF timing has 1/100 s steps: {0} fps will play at {1} fps. Choose MP4 for faster playback.</source>
        <translation>GIF-Bildzeiten haben 1/100-s-Schritte: {0} fps werden mit {1} fps abgespielt. Für schnellere Wiedergabe MP4 wählen.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="275"/>
        <source>Choose an output folder first.</source>
        <translation>Bitte zuerst einen Ausgabeordner wählen.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="281"/>
        <source>Nothing selected to export.</source>
        <translation>Nichts zum Exportieren ausgewählt.</translation>
    </message>
</context>
<context>
    <name>ZoomBar</name>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="60"/>
        <source>Fit</source>
        <translation>Anpassen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="61"/>
        <source>Fit image to viewport</source>
        <translation>Bild an den Ansichtsbereich anpassen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="68"/>
        <source>Current zoom — click to reset to 100% (1:1 pixels).
Wheel: zoom · Right/middle drag: pan · Space: pan mode</source>
        <translation>Aktueller Zoom — Klick setzt auf 100 % (1:1 Pixel) zurück.
Rad: Zoom · Rechts-/Mittelklick-Ziehen: Verschieben · Leertaste: Verschiebemodus</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="74"/>
        <source>Zoom in</source>
        <translation>Vergrößern</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="78"/>
        <source>Zoom out</source>
        <translation>Verkleinern</translation>
    </message>
</context>
<context>
    <name>dialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="24"/>
        <source>Close</source>
        <translation>Schließen</translation>
    </message>
</context>
</TS>
