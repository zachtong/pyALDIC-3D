<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="sd_PK">
<context>
    <name>AboutDialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="36"/>
        <source>About pyALDIC-3D</source>
        <translation>Acerca de pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="47"/>
        <source>Version {0}</source>
        <translation>Versión {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="52"/>
        <source>Stereo (3D) digital image correlation — full-field displacement and surface strain from a calibrated camera pair.</source>
        <translation>Correlación de imágenes digitales estéreo (3D): desplazamientos de campo completo y deformaciones superficiales a partir de un par de cámaras calibrado.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="63"/>
        <source>Citation: Zenodo DOI pending release.</source>
        <translation>Cita: DOI de Zenodo pendiente de publicación.</translation>
    </message>
</context>
<context>
    <name>AdvancedSection3D</name>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="38"/>
        <source>Track Both</source>
        <translation>Seguir ambas cámaras</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="39"/>
        <source>Stereo Each Frame</source>
        <translation>Estéreo en cada fotograma</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="40"/>
        <source>Reference Direct</source>
        <translation>Referencia directa</translation>
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
        <translation>Cómo se propagan las correspondencias estéreo en el tiempo.
Seguir ambas cámaras (por defecto): emparejar estéreo una sola vez en el fotograma 1 y luego seguir cada cámara temporalmente — lo más rápido, una sola resolución estéreo.
Estéreo en cada fotograma: re-emparejar estéreo en cada fotograma — robusto cuando el seguimiento temporal deriva, más lento.
Referencia directa: emparejar cada fotograma directamente con el fotograma 1 en ambas cámaras — sin acumulación de deriva, solo movimientos pequeños.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="52"/>
        <source>Strategy</source>
        <translation>Estrategia</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="59"/>
        <source>1 = single global pass (fastest), 3 = default, 5+ = diminishing returns</source>
        <translation>1 = pasada única (más rápido), 3 = predeterminado, 5+ = rendimientos decrecientes</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="61"/>
        <source>AL-DIC Iterations</source>
        <translation>Iteraciones AL-DIC</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="63"/>
        <source>Only affects AL-DIC solver. Ignored by Local DIC.</source>
        <translation>Solo afecta al solucionador AL-DIC. Local DIC lo ignora.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="69"/>
        <source>Parallel camera tracking</source>
        <translation>Seguimiento de cámaras en paralelo</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="72"/>
        <source>Track both cameras concurrently — modest speedup (the solver already uses all cores), doubles peak memory</source>
        <translation>Seguir ambas cámaras en paralelo — mejora limitada (el solucionador ya usa todos los núcleos), memoria pico duplicada</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="79"/>
        <source>Auto-expand FFT search on clipped peaks</source>
        <translation>Ampliar automáticamente la búsqueda FFT con picos recortados</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="83"/>
        <source>When the temporal FFT integer peak lands on the search-region
boundary, retry with a larger region (engine default on).
Disable for strictly bounded runtimes; then Temporal Search
must cover the largest per-frame motion by itself.</source>
        <translation>Si el pico entero de la FFT temporal cae en el borde de la región de
búsqueda, se reintenta con una región mayor (activado por defecto).
Desactívelo para tiempos de ejecución estrictamente acotados; entonces
la búsqueda temporal debe cubrir por sí sola el mayor movimiento por
fotograma.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="92"/>
        <source>Result checks</source>
        <translation>Comprobaciones de resultados</translation>
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
        <translation>Comprobación de seguimiento: cada punto seguido debe parecerse
aún a su subconjunto del fotograma 1 (desajuste de correlación, 0 = perfecto, 4 = peor).
Los puntos por debajo del 60 % de este valor pasan siempre; los que
llegan hasta él pasan si sus vecinos coinciden; el resto se descarta
como seguimiento fallido. Por defecto 1,0 (correlación 0,5). Súbalo
(p. ej. 1,5) para deformaciones muy grandes y bájelo para resultados
más estrictos; 0 desactiva la comprobación.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="109"/>
        <source>Tracking check</source>
        <translation>Comprobación de seguimiento</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="114"/>
        <source>Stereo check: a left/right match is kept only if its
correlation mismatch is at most this value. Default 0.6
(correlation 0.7); 0 turns the check off.</source>
        <translation>Comprobación estéreo: un emparejamiento izquierda/derecha solo se
conserva si su desajuste de correlación no supera este valor. Por defecto 0,6
(correlación 0,7); 0 desactiva la comprobación.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="119"/>
        <source>Stereo check</source>
        <translation>Comprobación estéreo</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="124"/>
        <source>Epipolar limit: a left/right match must lie within this many
pixels of the line the calibration predicts. Default 2 px;
raise it only for a poor calibration; 0 turns the check off.</source>
        <translation>Límite epipolar: un emparejamiento izquierda/derecha debe quedar a menos
de estos píxeles de la línea que predice la calibración. Por defecto 2 px;
súbalo solo con una calibración deficiente; 0 desactiva la comprobación.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="130"/>
        <source>Epipolar limit</source>
        <translation>Límite epipolar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="140"/>
        <source>off</source>
        <translation>desactivado</translation>
    </message>
</context>
<context>
    <name>AnimationTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="57"/>
        <source>Fields</source>
        <translation>Campos</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="77"/>
        <source>Format</source>
        <translation>Formato</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="84"/>
        <source>Frames per second</source>
        <translation>Fotogramas por segundo</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="91"/>
        <source>Frame step</source>
        <translation>Paso de fotogramas</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="92"/>
        <source>Keep every Nth frame (1 = all)</source>
        <translation>Conservar un fotograma de cada N (1 = todos)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="99"/>
        <source>Resolution (long edge)</source>
        <translation>Resolución (borde largo)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="119"/>
        <source>Include colorbar</source>
        <translation>Incluir barra de color</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="124"/>
        <source>Background</source>
        <translation>Fondo</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="138"/>
        <source>Export Animation</source>
        <translation>Exportar animación</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="149"/>
        <source>Load an image sequence first (open the project in the main window).</source>
        <translation>Cargue primero una secuencia de imágenes (abra el proyecto en la ventana principal).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="158"/>
        <source>GIF timing has 1/100 s steps: {0} fps will play at {1} fps. Choose MP4 for faster playback.</source>
        <translation>La temporización GIF tiene pasos de 1/100 s: {0} fps se reproducirán a {1} fps. Elija MP4 para una reproducción más rápida.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="178"/>
        <source>Choose an output folder first.</source>
        <translation>Elija primero una carpeta de salida.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="182"/>
        <source>No fields enabled.</source>
        <translation>Ningún campo activado.</translation>
    </message>
</context>
<context>
    <name>Application</name>
    <message>
        <location filename="../../gui/app.py" line="288"/>
        <source>pyALDIC-3D has hit an error</source>
        <translation>pyALDIC-3D ha encontrado un error</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="289"/>
        <source>An unexpected error occurred. The application may not behave correctly from here on, so saving your project and restarting is recommended.</source>
        <translation>Se ha producido un error inesperado. Es posible que la aplicación no funcione correctamente a partir de ahora, por lo que se recomienda guardar el proyecto y reiniciar.</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="299"/>
        <source>Details were written to {0}</source>
        <translation>Los detalles se han guardado en {0}</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="348"/>
        <source>Preparing compute kernels in the background…</source>
        <translation>Preparando los núcleos de cálculo en segundo plano…</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="361"/>
        <source>Compute kernels ready ({0} s).</source>
        <translation>Núcleos de cálculo listos ({0} s).</translation>
    </message>
</context>
<context>
    <name>BackgroundRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="638"/>
        <source>Original (frame 1 background)</source>
        <translation>Original (fotograma 1 como fondo)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="639"/>
        <source>Deformed (current frame background)</source>
        <translation>Deformado (fotograma actual como fondo)</translation>
    </message>
</context>
<context>
    <name>CalibrationDialog</name>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="92"/>
        <source>Stereo Calibration</source>
        <translation>Calibración estéreo</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="131"/>
        <source>CALIBRATION IMAGE PAIRS</source>
        <translation>PARES DE IMÁGENES DE CALIBRACIÓN</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="134"/>
        <source>Add left images…</source>
        <translation>Añadir imágenes izquierdas…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="136"/>
        <source>Add right images…</source>
        <translation>Añadir imágenes derechas…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="138"/>
        <source>Clear</source>
        <translation>Limpiar</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="140"/>
        <source>Save detections…</source>
        <translation>Guardar detecciones…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="143"/>
        <source>Load detections…</source>
        <translation>Cargar detecciones…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="150"/>
        <source>No images loaded</source>
        <translation>Ninguna imagen cargada</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="158"/>
        <source>Left</source>
        <translation>Izquierda</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="159"/>
        <source>Right</source>
        <translation>Derecha</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="160"/>
        <source>Points</source>
        <translation>Puntos</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="161"/>
        <source>RMS L/R</source>
        <translation>RMS I/D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="162"/>
        <source>Max E</source>
        <translation>Error máx</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="163"/>
        <source>Status</source>
        <translation>Estado</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="174"/>
        <source>SELECTED PAIR (L | R)</source>
        <translation>PAR SELECCIONADO (I | D)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="175"/>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="408"/>
        <source>select a pair to preview detected points</source>
        <translation>seleccione un par para previsualizar los puntos detectados</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="182"/>
        <source>Click to enlarge the annotated detection</source>
        <translation>Haga clic para ampliar la detección anotada</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="186"/>
        <source>PER-PAIR REPROJECTION ERROR</source>
        <translation>ERROR DE REPROYECCIÓN POR PAR</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="191"/>
        <source>Reject threshold (px)</source>
        <translation>Umbral de rechazo (px)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="200"/>
        <source>Recalibrate</source>
        <translation>Recalibrar</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="212"/>
        <source>CALIBRATION BOARD</source>
        <translation>TABLERO DE CALIBRACIÓN</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="220"/>
        <source>Chessboard</source>
        <translation>Tablero de ajedrez</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="221"/>
        <source>ChArUco</source>
        <translation>ChArUco</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="222"/>
        <source>Circle grid</source>
        <translation>Malla de puntos</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="223"/>
        <source>Coded dot target (3 ring markers)</source>
        <translation>Objetivo de puntos codificado (3 marcadores anulares)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="225"/>
        <source>Type</source>
        <translation>Tipo</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="230"/>
        <source>Columns x Rows</source>
        <translation>Columnas × Filas</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="237"/>
        <source>Square size (mm)</source>
        <translation>Tamaño de casilla (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="242"/>
        <source>Marker size (mm)</source>
        <translation>Tamaño de marcador (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="247"/>
        <source>Dot pitch (mm)</source>
        <translation>Paso de puntos (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="252"/>
        <source>Dot diameter (mm)</source>
        <translation>Diámetro de punto (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="256"/>
        <source>Asymmetric grid</source>
        <translation>Malla asimétrica</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="258"/>
        <source>Board printed with OpenCV &lt; 4.7</source>
        <translation>Tablero impreso con OpenCV &lt; 4.7</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="262"/>
        <source>Print board… (1:1 PDF)</source>
        <translation>Imprimir tablero… (PDF 1:1)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="266"/>
        <source>SOLVER OPTIONS</source>
        <translation>OPCIONES DEL SOLVER</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="267"/>
        <source>Jointly refine intrinsics (advanced)</source>
        <translation>Refinar intrínsecos conjuntamente (avanzado)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="268"/>
        <source>Estimate tangential distortion p1/p2</source>
        <translation>Estimar distorsión tangencial p1/p2</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="269"/>
        <source>Fix k3 = 0 (low-distortion lens)</source>
        <translation>Fijar k3 = 0 (lente de baja distorsión)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="270"/>
        <source>Release-object method (printed boards)</source>
        <translation>Método release-object (tableros impresos)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="271"/>
        <source>Dot eccentricity correction</source>
        <translation>Corrección de excentricidad de puntos</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="273"/>
        <source>Joint bundle adjustment (robust, uses mono views)</source>
        <translation>Ajuste de haces (robusto, usa vistas mono)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="274"/>
        <source>Optimize board shape (printed boards)</source>
        <translation>Optimizar la forma del tablero (tableros impresos)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="289"/>
        <source>Calibrate</source>
        <translation>Calibrar</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="300"/>
        <source>RESULT</source>
        <translation>RESULTADO</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="301"/>
        <source>No calibration yet</source>
        <translation>Aún sin calibración</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="306"/>
        <source>Verify with board images…</source>
        <translation>Verificar con imágenes del tablero…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="318"/>
        <source>Accept &amp;&amp; Save…</source>
        <translation>Aceptar &amp;&amp; Guardar…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="324"/>
        <source>Cancel</source>
        <translation>Cancelar</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="383"/>
        <source>Choose {0} calibration images</source>
        <translation>Elegir imágenes de calibración {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="385"/>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="717"/>
        <source>Images (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)</source>
        <translation>Imágenes (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="430"/>
        <source>{0} left / {1} right images</source>
        <translation>{0} imágenes izquierdas / {1} derechas</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="440"/>
        <source>Load equal, &gt;= 3 left/right image sets first.</source>
        <translation>Cargue primero conjuntos iguales (al menos 3) de imágenes izquierda/derecha.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="471"/>
        <source>Working… {0}</source>
        <translation>Procesando… {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="480"/>
        <source>Calibration failed: {0}</source>
        <translation>Falló la calibración: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="505"/>
        <source>used</source>
        <translation>usada</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="507"/>
        <source>L: {0}</source>
        <translation>I: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="509"/>
        <source>R: {0}</source>
        <translation>D: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="525"/>
        <source>Stereo RMS {0:.3f} px | epipolar {1:.3f} px</source>
        <translation>RMS estéreo {0:.3f} px | epipolar {1:.3f} px</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="528"/>
        <source>Baseline {0:.2f} mm | pairs {1}/{2}</source>
        <translation>Línea base {0:.2f} mm | pares {1}/{2}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="531"/>
        <source>fx {0:.1f}  fy {1:.1f}  cx {2:.1f}  cy {3:.1f}</source>
        <translation>fx {0:.1f}  fy {1:.1f}  cx {2:.1f}  cy {3:.1f}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="534"/>
        <source>Coverage L {0:.0%} / R {1:.0%} | tilt {2:.0f}-{3:.0f}°</source>
        <translation>Cobertura I {0:.0%} / D {1:.0%} | inclinación {2:.0f}-{3:.0f}°</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="543"/>
        <source>Bundle adjustment: RMS {0:.3f} -&gt; {1:.3f} px ({2:.0f} mono views)</source>
        <translation>Ajuste de haces: RMS {0:.3f} -&gt; {1:.3f} px ({2:.0f} vistas mono)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="549"/>
        <source>Board flatness: z-range {0:.3f} mm</source>
        <translation>Planitud del tablero: rango z {0:.3f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="552"/>
        <source>Warning: {0}</source>
        <translation>Advertencia: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="690"/>
        <source>Save board PDF</source>
        <translation>Guardar PDF del tablero</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="692"/>
        <source>PDF (*.pdf)</source>
        <translation>PDF (*.pdf)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="703"/>
        <source>Board PDF written: {0}</source>
        <translation>PDF del tablero escrito: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="719"/>
        <source>Choose LEFT verification image</source>
        <translation>Elegir imagen de verificación IZQUIERDA</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="724"/>
        <source>Choose RIGHT verification image</source>
        <translation>Elegir imagen de verificación DERECHA</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="733"/>
        <source>Verification failed: {0}</source>
        <translation>Falló la verificación: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="739"/>
        <source>Verify: pitch {0:.4f} mm vs {1:g} mm — scale error {2:.3%}, plane RMS {3:.4f} mm</source>
        <translation>Verificación: paso {0:.4f} mm frente a {1:g} mm — error de escala {2:.3%}, RMS del plano {3:.4f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="753"/>
        <source>Save calibration as</source>
        <translation>Guardar calibración como</translation>
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
        <translation>Cámara {0}: el tablero solo alcanzó el {1:.0%} del radio de las esquinas de la imagen. Más allá, el modelo de lente es una suposición: dos ajustes igual de buenos difieren allí hasta {2:.2f} px. Añada vistas con el tablero cerca de las esquinas de la imagen, mantenga la región de interés dentro de la zona cubierta o, con una lente de baja distorsión, fije k3.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="57"/>
        <source>Camera {0}: the board reached {1:.0%} of the image-corner radius; the lens model is fitted only inside that radius.</source>
        <translation>Cámara {0}: el tablero alcanzó el {1:.0%} del radio de las esquinas de la imagen; el modelo de lente solo se ajusta dentro de ese radio.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="40"/>
        <source>Camera {0}: the board reached {1:.0%} of the image-corner radius. Beyond it the lens model is a guess: two equally good fits differ by up to {2:.2f} px there. With k3 fixed, the corners are right only if the lens has no k3 distortion: add views with the board near the image corners, or keep the region of interest inside the covered area.</source>
        <translation>Cámara {0}: el tablero solo alcanzó el {1:.0%} del radio de las esquinas de la imagen. Más allá, el modelo de lente es una suposición: dos ajustes igual de buenos difieren allí hasta {2:.2f} px. Con k3 fijado, las esquinas solo son correctas si la lente no tiene distorsión k3: añada vistas con el tablero cerca de las esquinas de la imagen o mantenga la región de interés dentro de la zona cubierta.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="63"/>
        <source>Camera {0}: the residuals follow a pattern the lens model does not explain (binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model fits), although the board shape is already optimised. A lens the model cannot describe, a board that bends differently from view to view, or detector bias can cause this.</source>
        <translation>Cámara {0}: los residuos siguen un patrón que el modelo de lente no explica (exceso por celda {1:.1f}, campo ajustado {2:.1f} × ruido; cerca de 1 cuando el modelo encaja), aunque la forma del tablero ya está optimizada. Puede deberse a una lente que el modelo no describe, a un tablero que se curva de forma distinta en cada vista o a un sesgo del detector.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="72"/>
        <source>Camera {0}: the residuals follow a pattern the lens model does not explain (binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model fits). Often the board is the cause (not flat, or its points not exactly where the board description puts them): tick Joint bundle adjustment and Optimize board shape. A lens the model cannot describe or detector bias can also cause this.</source>
        <translation>Cámara {0}: los residuos siguen un patrón que el modelo de lente no explica (exceso por celda {1:.1f}, campo ajustado {2:.1f} × ruido; cerca de 1 cuando el modelo encaja). A menudo la causa es el tablero (no es plano, o sus puntos no están exactamente donde indica su descripción): marque «Ajuste de haces» y «Optimizar la forma del tablero». Una lente que el modelo no describe o un sesgo del detector también pueden causarlo.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="82"/>
        <source>Camera {0}: the extrapolation check was skipped (too few usable views).</source>
        <translation>Cámara {0}: se omitió la comprobación de extrapolación (demasiado pocas vistas utilizables).</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="88"/>
        <source>Camera {0}: the lens-model check was skipped: the points fill only {1} image cells.</source>
        <translation>Cámara {0}: se omitió la comprobación del modelo de lente: los puntos solo ocupan {1} celdas de la imagen.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="103"/>
        <source>Warning: {0}</source>
        <translation>Advertencia: {0}</translation>
    </message>
</context>
<context>
    <name>CalibrationSection3D</name>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="50"/>
        <source>Calibrate from images…</source>
        <translation>Calibrar desde imágenes…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="54"/>
        <source>Run the built-in stereo calibrator on your target photos
(checkerboard / ChArUco / dot grid). Writes an opencv_yaml
file and loads it — the recommended path when you have
calibration images.</source>
        <translation>Ejecuta el calibrador estéreo integrado sobre sus fotos del patrón (tablero / ChArUco / rejilla de puntos).
Escribe un archivo opencv_yaml y lo carga — la vía recomendada cuando dispone de imágenes de calibración.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="65"/>
        <source>Format</source>
        <translation>Formato</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="74"/>
        <source>File format of the calibration to import. Default opencv_yaml
(written by the built-in calibrator). Pick the format matching
your source: dice (DICe XML), matchid (MatchID .caldat),
opencorr (OpenCorr CSV), mmc (MultiDIC/MMC .mat), matlabcv
(MATLAB stereoParams .mat).</source>
        <translation>Formato del archivo de calibración a importar. Por defecto opencv_yaml
(escrito por el calibrador integrado). Elija el formato de su fuente:
dice (DICe XML), matchid (MatchID .caldat), opencorr (OpenCorr CSV),
mmc (MultiDIC/MMC .mat), matlabcv (MATLAB stereoParams .mat).</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="85"/>
        <source>Import calibration…</source>
        <translation>Importar calibración…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="88"/>
        <source>Load an existing stereo calibration file in the selected
Format. The status line below shows fx / fy and the baseline
as a sanity check.</source>
        <translation>Cargar un archivo de calibración estéreo existente en el formato seleccionado.
La línea de estado inferior muestra fx / fy y la línea base como comprobación de cordura.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="96"/>
        <source>Manual parameters…</source>
        <translation>Parámetros manuales…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="99"/>
        <source>Type intrinsics and extrinsics by hand (fx, fy, cx, cy,
distortion, R, T) — the fallback when no calibration file
exists. Writes an opencv_yaml file and loads it.</source>
        <translation>Escriba a mano los parámetros intrínsecos y extrínsecos (fx, fy, cx, cy, distorsión, R, T)
— el recurso cuando no existe ningún archivo de calibración. Escribe un archivo opencv_yaml y lo carga.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="107"/>
        <source>No calibration loaded</source>
        <translation>Ninguna calibración cargada</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="151"/>
        <source>Choose calibration file</source>
        <translation>Elegir archivo de calibración</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="153"/>
        <source>Calibration files (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)</source>
        <translation>Archivos de calibración (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="171"/>
        <source>Error: {0}</source>
        <translation>Error: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="179"/>
        <source>{0}
fx {1:.0f}  fy {2:.0f}  |  baseline {3:.1f} mm</source>
        <translation>{0}
fx {1:.0f}  fy {2:.0f}  |  línea base {3:.1f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="185"/>
        <source>calibration loaded: baseline {0:.1f} mm</source>
        <translation>calibración cargada: línea base {0:.1f} mm</translation>
    </message>
</context>
<context>
    <name>CameraDropZone</name>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="76"/>
        <source>{0} frames</source>
        <translation>{0} fotogramas</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="103"/>
        <source>Click to pick this camera&apos;s image folder, or drag the folder here. Both cameras need the same number of frames.</source>
        <translation>Haga clic para elegir la carpeta de imágenes de esta cámara o arrastre la carpeta aquí. Ambas cámaras deben tener el mismo número de fotogramas.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="114"/>
        <source>Select image folder</source>
        <translation>Seleccionar carpeta de imágenes</translation>
    </message>
</context>
<context>
    <name>CameraRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="606"/>
        <source>Camera</source>
        <translation>Cámara</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="610"/>
        <source>Left</source>
        <translation>Izquierda</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="611"/>
        <source>Right</source>
        <translation>Derecha</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="612"/>
        <source>Left + Right</source>
        <translation>Izquierda + Derecha</translation>
    </message>
</context>
<context>
    <name>CanvasArea3D</name>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="92"/>
        <source>Fit</source>
        <translation>Ajustar</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="95"/>
        <source>Fit the image to the viewport (Ctrl+0)</source>
        <translation>Ajustar la imagen a la vista (Ctrl+0)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="102"/>
        <source>Current zoom — click to reset to 100% (1:1 pixels).
Wheel: zoom · Right/middle drag: pan · Space: pan mode</source>
        <translation>Zoom actual — haga clic para restablecer al 100 % (píxeles 1:1).
Rueda: zoom · Arrastre con botón derecho/central: desplazar · Espacio: modo desplazamiento</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="109"/>
        <source>Zoom in (Ctrl+=)</source>
        <translation>Acercar (Ctrl+=)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="113"/>
        <source>Zoom out (Ctrl+-)</source>
        <translation>Alejar (Ctrl+-)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="118"/>
        <source>Show Grid</source>
        <translation>Mostrar cuadrícula</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="121"/>
        <source>Show the computational mesh preview on the reference view
(left camera, frame 1). Rebuilt live from the current Subset
Step / refinement settings — what you see is the run&apos;s mesh.
Default on; turn off to declutter the canvas.</source>
        <translation>Muestra la vista previa de la malla de cálculo sobre la vista de referencia
(cámara izquierda, fotograma 1). Se reconstruye en vivo con el paso de subset
y los ajustes de refinado — la malla mostrada es la de la ejecución.
Activado por defecto; desactívelo para despejar el lienzo.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="134"/>
        <source>Hovering a mesh node shows its correlation subset window
(the Subset Size box). Needs Show Grid. Use it to judge
whether the subset spans enough speckle texture.</source>
        <translation>Al pasar el cursor sobre un nodo de la malla se muestra su ventana de subset
de correlación (el cuadro Tamaño de subset). Requiere «Mostrar cuadrícula». Útil para
juzgar si el subset abarca suficiente textura de moteado.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="147"/>
        <source>Switch the canvas to the reconstructed 3D surface (colored by
the selected field, with the camera frusta). Uncheck to return
to the 2D image view. Requires results.</source>
        <translation>Cambia el lienzo a la superficie 3D reconstruida (coloreada según el campo
seleccionado, con los conos de las cámaras). Desmarque para volver a la vista de
imagen 2D. Requiere resultados.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="131"/>
        <source>Show Subset</source>
        <translation>Mostrar subconjunto</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="144"/>
        <source>3D View</source>
        <translation>Vista 3D</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="323"/>
        <source>Load images before importing an ROI mask</source>
        <translation>Cargue las imágenes antes de importar una máscara ROI</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="328"/>
        <source>Could not import the mask: {0}</source>
        <translation>No se pudo importar la máscara: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="331"/>
        <source>ROI mask imported from {0}</source>
        <translation>Máscara ROI importada desde {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="336"/>
        <source>No ROI mask to save — draw one first</source>
        <translation>No hay máscara ROI que guardar — dibuje una primero</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="344"/>
        <source>Save Mask</source>
        <translation>Guardar máscara</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="344"/>
        <source>PNG image (*.png)</source>
        <translation>Imagen PNG (*.png)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="351"/>
        <source>Could not save the mask: {0}</source>
        <translation>No se pudo guardar la máscara: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="354"/>
        <source>ROI mask saved to {0}</source>
        <translation>Máscara ROI guardada en {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="540"/>
        <source>Analysis produced no valid points — nothing to display. See the log.</source>
        <translation>El análisis no produjo puntos válidos — nada que mostrar. Consulte el registro.</translation>
    </message>
</context>
<context>
    <name>CanvasRenderMixin</name>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="67"/>
        <source>Could not map the ROI into the right camera: {0}</source>
        <translation>No se pudo trasladar la ROI a la cámara derecha: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="204"/>
        <source>3D view — run an analysis to see the reconstructed surface.</source>
        <translation>Vista 3D — ejecute un análisis para ver la superficie reconstruida.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="211"/>
        <source>Selected field is not available.</source>
        <translation>El campo seleccionado no está disponible.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="396"/>
        <source>Could not draw the overlay: {0}</source>
        <translation>No se pudo dibujar la superposición: {0}</translation>
    </message>
</context>
<context>
    <name>CanvasToolsMixin</name>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="55"/>
        <source>Starting points cleared</source>
        <translation>Puntos de inicio borrados</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="81"/>
        <source>Starting points are placed on the LEFT camera, frame 1 — switch there to add a point</source>
        <translation>Los puntos de inicio se colocan en la cámara IZQUIERDA, fotograma 1 — cambie a esa vista para añadir uno</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="92"/>
        <source>Starting point {0} placed at ({1}, {2})</source>
        <translation>Punto de inicio {0} colocado en ({1}, {2})</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="112"/>
        <source>Starting point removed at ({0}, {1})</source>
        <translation>Punto de inicio en ({0}, {1}) eliminado</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="169"/>
        <source>Fit</source>
        <translation>Ajustar</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="171"/>
        <source>Zoom to 100%</source>
        <translation>Zoom al 100 %</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="174"/>
        <source>Copy image to clipboard</source>
        <translation>Copiar la imagen al portapapeles</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="177"/>
        <source>Clear ROI</source>
        <translation>Borrar la ROI</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="180"/>
        <source>Clear seed points</source>
        <translation>Borrar los puntos de inicio</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="190"/>
        <source>Canvas image copied to the clipboard</source>
        <translation>Imagen del lienzo copiada al portapapeles</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="205"/>
        <source>1. Drop the left/right camera folders in the sidebar
2. Calibrate or import calibration
3. Draw the ROI and Run</source>
        <translation>1. Suelte las carpetas de las cámaras izquierda/derecha en la barra lateral
2. Calibre o importe una calibración
3. Dibuje la ROI y ejecute</translation>
    </message>
</context>
<context>
    <name>ConfigOverlay3D</name>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="39"/>
        <source>Mode</source>
        <translation>Modo</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="40"/>
        <source>Solver</source>
        <translation>Solucionador</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="41"/>
        <source>Init</source>
        <translation>Estimación inicial</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="42"/>
        <source>Subset</source>
        <translation>Subconjunto</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="79"/>
        <source>AL-DIC ({0} iter)</source>
        <translation>AL-DIC ({0} iter.)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="94"/>
        <source>FFT (no starting point)</source>
        <translation>FFT (sin punto de inicio)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="81"/>
        <source>Local DIC</source>
        <translation>Local DIC</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="84"/>
        <source>Starting Point</source>
        <translation>Punto de inicio</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="85"/>
        <source>Previous frame</source>
        <translation>Fotograma anterior</translation>
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
        <translation>Acumulativo</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="75"/>
        <source>Incremental</source>
        <translation>Incremental</translation>
    </message>
</context>
<context>
    <name>ConsoleLog3D</name>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="41"/>
        <source>Copy all</source>
        <translation>Copiar todo</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="44"/>
        <source>Save log to file…</source>
        <translation>Guardar el registro en un archivo…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="46"/>
        <source>Clear</source>
        <translation>Limpiar</translation>
    </message>
</context>
<context>
    <name>DataTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="50"/>
        <source>Format</source>
        <translation>Formato</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="52"/>
        <source>NumPy archive (.npz)</source>
        <translation>Archivo NumPy (.npz)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="54"/>
        <source>MATLAB (.mat)</source>
        <translation>MATLAB (.mat)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="56"/>
        <source>CSV (one file per frame)</source>
        <translation>CSV (un archivo por fotograma)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="57"/>
        <source>PLY point clouds (per frame)</source>
        <translation>Nubes de puntos PLY (por fotograma)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="58"/>
        <source>VTU mesh series (ParaView)</source>
        <translation>Serie de mallas VTU (ParaView)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="61"/>
        <source>✓ Parameters file (JSON) always exported</source>
        <translation>✓ Archivo de parámetros (JSON) siempre exportado</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="68"/>
        <source>Displacement</source>
        <translation>Desplazamiento</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="72"/>
        <source>Strain</source>
        <translation>Deformación</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="79"/>
        <source>3D points, reprojection error, and source flags are always exported.</source>
        <translation>Los puntos 3D, el error de reproyección y los indicadores de origen siempre se exportan.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="88"/>
        <source>Export Data</source>
        <translation>Exportar datos</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="105"/>
        <source>Select:</source>
        <translation>Selección:</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="108"/>
        <source>All</source>
        <translation>Todos</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="109"/>
        <source>None</source>
        <translation>Ninguno</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="158"/>
        <source>Choose an output folder first.</source>
        <translation>Elija primero una carpeta de salida.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="189"/>
        <source>Wrote: {0}</source>
        <translation>Escrito: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="193"/>
        <source>Export cancelled — kept: {0}</source>
        <translation>Exportación cancelada — conservado: {0}</translation>
    </message>
</context>
<context>
    <name>DetectionFilesMixin</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="215"/>
        <source>Save detections</source>
        <translation>Guardar detecciones</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="217"/>
        <location filename="../../gui/dialogs/calibration_support.py" line="238"/>
        <source>NumPy detections (*.npz)</source>
        <translation>Detecciones NumPy (*.npz)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="231"/>
        <source>Detections saved: {0}</source>
        <translation>Detecciones guardadas: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="236"/>
        <source>Load detections</source>
        <translation>Cargar detecciones</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="260"/>
        <source>Loaded {0} detection pairs — Recalibrate re-solves without re-detecting</source>
        <translation>{0} pares de detecciones cargados — Recalibrar resuelve sin volver a detectar</translation>
    </message>
</context>
<context>
    <name>DetectionZoomDialog</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="274"/>
        <source>Detection preview — pair {0}</source>
        <translation>Vista previa de detección — par {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="283"/>
        <source>Wheel: zoom · Right/middle drag: pan</source>
        <translation>Rueda: zoom · Arrastre con botón derecho/central: desplazar</translation>
    </message>
</context>
<context>
    <name>ExportDialog</name>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="139"/>
        <source>Export Results</source>
        <translation>Exportar resultados</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="146"/>
        <source>OUTPUT FOLDER</source>
        <translation>CARPETA DE SALIDA</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="149"/>
        <source>Select output folder…</source>
        <translation>Seleccionar carpeta de salida…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="151"/>
        <source>Browse…</source>
        <translation>Examinar…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="152"/>
        <source>Choose the folder all exports are written into</source>
        <translation>Elegir la carpeta donde se escriben todas las exportaciones</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="155"/>
        <source>Open Folder</source>
        <translation>Abrir carpeta</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="156"/>
        <source>Open the output folder in the file explorer</source>
        <translation>Abrir la carpeta de salida en el explorador de archivos</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="168"/>
        <source>Data</source>
        <translation>Datos</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="169"/>
        <source>Images</source>
        <translation>Imágenes</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="170"/>
        <source>Animation</source>
        <translation>Animación</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="171"/>
        <source>Preview &amp; Colorbar</source>
        <translation>Vista previa y barra de color</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="172"/>
        <source>3D View</source>
        <translation>Vista 3D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="176"/>
        <source>Numeric results: field-selective NPZ / MAT / CSV tables plus PLY / VTU meshes for external tools.</source>
        <translation>Resultados numéricos: tablas NPZ / MAT / CSV selectivas por campo, más mallas PLY / VTU para herramientas externas.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="180"/>
        <source>Rendered per-camera field overlays as PNG images, one per frame, using the Preview &amp; Colorbar style.</source>
        <translation>Superposiciones de campo renderizadas por cámara como imágenes PNG, una por fotograma, con el estilo de «Vista previa y barra de color».</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="184"/>
        <source>GIF / MP4 animations of the field overlay across frames, using the Preview &amp; Colorbar style.</source>
        <translation>Animaciones GIF / MP4 de la superposición de campo a lo largo de los fotogramas, con el estilo de «Vista previa y barra de color».</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="188"/>
        <source>WYSIWYG style source: the colorbar and margins configured here are used by every Images / Animation export.</source>
        <translation>Fuente de estilo WYSIWYG: la barra de color y los márgenes configurados aquí se usan en cada exportación de imágenes / animaciones.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="461"/>
        <source>Export Running</source>
        <translation>Exportación en curso</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="462"/>
        <source>An export is still running — cancel it and close?</source>
        <translation>Una exportación sigue en curso: ¿cancelarla y cerrar?</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="465"/>
        <source>Yes</source>
        <translation>Sí</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="466"/>
        <source>No</source>
        <translation>No</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="498"/>
        <source>Folder does not exist: {0}</source>
        <translation>La carpeta no existe: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="204"/>
        <source>Close</source>
        <translation>Cerrar</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="192"/>
        <source>Offscreen renders of the 3D surface as images, a deforming animation or a turntable, from your current 3D view.</source>
        <translation>Renderizados fuera de pantalla de la superficie 3D como imágenes, animación de deformación o rotación orbital, desde su vista 3D actual.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="485"/>
        <source>Choose output folder</source>
        <translation>Elegir carpeta de salida</translation>
    </message>
</context>
<context>
    <name>ExportTabBase</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="250"/>
        <source>Cancelling…</source>
        <translation>Cancelando…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="287"/>
        <source>Export cancelled — {0} file(s) kept</source>
        <translation>Exportación cancelada — {0} archivo(s) conservado(s)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="289"/>
        <source>(the unfinished animation was deleted)</source>
        <translation>(la animación inacabada se eliminó)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="296"/>
        <source>Nothing was written: no data to draw for {0}.</source>
        <translation>No se escribió nada: no hay datos que dibujar para {0}.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="299"/>
        <source>Nothing was written — the export produced no files.</source>
        <translation>No se escribió nada — la exportación no produjo archivos.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="307"/>
        <source>{0} frame(s) had no data to draw ({1})</source>
        <translation>{0} fotograma(s) sin datos que dibujar ({1})</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="313"/>
        <source>no data for {0}</source>
        <translation>sin datos para {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="317"/>
        <source>the right-camera ROI could not be derived; the tracked area was used</source>
        <translation>no se pudo derivar la ROI de la cámara derecha; se usó el área seguida</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="278"/>
        <source>Error: {0}</source>
        <translation>Error: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="282"/>
        <source>Wrote {0} file(s)</source>
        <translation>{0} archivo(s) escritos</translation>
    </message>
</context>
<context>
    <name>ExportTabs</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="625"/>
        <source>Full resolution</source>
        <translation>Resolución completa</translation>
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
        <translation>Rango automático</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="436"/>
        <source>Opacity</source>
        <translation>Opacidad</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="437"/>
        <source>Field opacity (0 = transparent, 1 = fully opaque)</source>
        <translation>Opacidad del campo (0 = transparente, 1 = completamente opaco)</translation>
    </message>
</context>
<context>
    <name>FieldSelector3D</name>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="47"/>
        <source>DISPLACEMENT</source>
        <translation>DESPLAZAMIENTO</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="69"/>
        <source>U — world-frame displacement along X (left camera&apos;s +X, image right), in mm</source>
        <translation>U — desplazamiento en el sistema mundial según X (+X de la cámara izquierda, derecha de la imagen), en mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="72"/>
        <source>V — world-frame displacement along Y (left camera&apos;s +Y, image down), in mm</source>
        <translation>V — desplazamiento en el sistema mundial según Y (+Y de la cámara izquierda, abajo en la imagen), en mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="75"/>
        <source>W — world-frame displacement along Z (left camera&apos;s optical axis, toward the scene): out-of-plane motion, in mm</source>
        <translation>W — desplazamiento en el sistema mundial según Z (eje óptico de la cámara izquierda, hacia la escena): movimiento fuera del plano, en mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="78"/>
        <source>|D| — displacement magnitude √(U²+V²+W²), in mm</source>
        <translation>|D| — magnitud del desplazamiento √(U²+V²+W²), en mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="80"/>
        <location filename="../../gui/widgets/field_selector.py" line="107"/>
        <source>Velocity — per-node speed |D(k) − D(k−1)| × frame rate, in the display unit per second. Depends on the frame rate set in the UNITS section; frame 1 has no predecessor (empty).</source>
        <translation>Velocidad — rapidez por nodo |D(k) − D(k−1)| × velocidad de fotogramas, en la unidad de visualización por segundo. Depende de la velocidad de fotogramas configurada en la sección UNITS; el fotograma 1 no tiene predecesor (vacío).</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="103"/>
        <source>Run an analysis first — velocity needs results.</source>
        <translation>Ejecute primero un análisis — la velocidad necesita resultados.</translation>
    </message>
</context>
<context>
    <name>FrameMasksSection3D</name>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="65"/>
        <source>Per-frame masks</source>
        <translation>Máscaras por fotograma</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="69"/>
        <source>Optional: one mask image per frame (non-zero = valid), for
specimens whose valid region changes, e.g. a crack or a
boundary that moves. Without them the ROI of frame 1 is used
for every frame.</source>
        <translation>Opcional: una imagen de máscara por fotograma (distinto de cero = válido),
para probetas cuya región válida cambia, p. ej. una grieta o un
borde que se mueve. Sin ellas, la ROI del fotograma 1 se usa
para todos los fotogramas.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="83"/>
        <source>Import…</source>
        <translation>Importar…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="84"/>
        <source>Choose the folder holding this camera&apos;s mask images</source>
        <translation>Elegir la carpeta con las imágenes de máscara de esta cámara</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="87"/>
        <source>Clear</source>
        <translation>Limpiar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="97"/>
        <source>Left</source>
        <translation>Izquierda</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="97"/>
        <source>Right</source>
        <translation>Derecha</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="104"/>
        <source>{0}: {1} masks</source>
        <translation>{0}: {1} máscaras</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="106"/>
        <source>{0}: none</source>
        <translation>{0}: ninguna</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="114"/>
        <source>Choose the mask folder</source>
        <translation>Elegir la carpeta de máscaras</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="128"/>
        <source>Masks not imported for the {0} camera: {1}</source>
        <translation>No se importaron máscaras para la cámara {0}: {1}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="142"/>
        <source>{0} camera: {1} per-frame masks from {2}</source>
        <translation>Cámara {0}: {1} máscaras por fotograma de {2}</translation>
    </message>
</context>
<context>
    <name>FrameNavigator3D</name>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="45"/>
        <source>Previous frame (←)</source>
        <translation>Fotograma anterior (←)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="52"/>
        <location filename="../../gui/widgets/frame_navigator.py" line="160"/>
        <source>Play animation (Space)</source>
        <translation>Reproducir animación (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="59"/>
        <source>Next frame (→)</source>
        <translation>Fotograma siguiente (→)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="68"/>
        <source>Playback speed (frames per second). Default 2 fps.</source>
        <translation>Velocidad de reproducción (fotogramas por segundo). Por defecto 2 fps.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="153"/>
        <source>Pause animation (Space)</source>
        <translation>Pausar animación (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="175"/>
        <source>FRAME {0}/{1}</source>
        <translation>FOTOGRAMA {0}/{1}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="177"/>
        <source>FRAME 0/0</source>
        <translation>FOTOGRAMA 0/0</translation>
    </message>
</context>
<context>
    <name>FrameRangeRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="656"/>
        <source>All frames</source>
        <translation>Todos los fotogramas</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="660"/>
        <source>From frame</source>
        <translation>Desde fotograma</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="670"/>
        <source>to</source>
        <translation>a</translation>
    </message>
</context>
<context>
    <name>ImageCanvas3D</name>
    <message>
        <location filename="../../gui/widgets/image_view.py" line="762"/>
        <source>The three points are nearly in a line — spread them around the edge</source>
        <translation>Los tres puntos están casi alineados — repártalos por el borde</translation>
    </message>
</context>
<context>
    <name>ImagesTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="55"/>
        <source>Fields</source>
        <translation>Campos</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="75"/>
        <source>Format</source>
        <translation>Formato</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="84"/>
        <source>JPEG quality</source>
        <translation>Calidad JPEG</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="91"/>
        <source>Resolution (long edge)</source>
        <translation>Resolución (borde largo)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="100"/>
        <source>Include colorbar</source>
        <translation>Incluir barra de color</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="105"/>
        <source>Background</source>
        <translation>Fondo</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="119"/>
        <source>Export Images</source>
        <translation>Exportar imágenes</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="130"/>
        <source>Load an image sequence first (open the project in the main window).</source>
        <translation>Cargue primero una secuencia de imágenes (abra el proyecto en la ventana principal).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="156"/>
        <source>Choose an output folder first.</source>
        <translation>Elija primero una carpeta de salida.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="160"/>
        <source>No fields enabled.</source>
        <translation>Ningún campo activado.</translation>
    </message>
</context>
<context>
    <name>InitGuessSection3D</name>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="112"/>
        <source>Clear</source>
        <translation>Limpiar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="74"/>
        <source>Starting Points</source>
        <translation>Puntos de inicio</translation>
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
        <translation>Haga clic en uno o más puntos en la cámara IZQUIERDA, fotograma 1 — al menos
uno por cada región ROI conexa. El vecindario de cada punto se empareja
automáticamente en la cámara derecha (desplazamiento estéreo) y en el
fotograma 2 (semilla de movimiento); luego se propaga un campo de deformación
de primer orden a cada nodo de la malla — sin ajustar parámetros de búsqueda.
Ideal para líneas base anchas, grandes movimientos iniciales o campos
discontinuos. Sin punto colocado, la ejecución recurre a la FFT.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="94"/>
        <location filename="../../gui/widgets/init_guess_section.py" line="191"/>
        <source>Place points…</source>
        <translation>Colocar puntos…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="98"/>
        <source>Enter placement mode on the canvas. Left-click the LEFT camera,
frame 1 to ADD a point; right-click removes the nearest; Esc exits.</source>
        <translation>Modo de colocación en el lienzo. Clic izquierdo en la cámara IZQUIERDA,
fotograma 1 para AÑADIR un punto; clic derecho elimina el más cercano; Esc sale.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="103"/>
        <source>Auto-place</source>
        <translation>Colocación automática</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="106"/>
        <source>Place one Starting Point automatically, deep inside the ROI on
the LEFT camera, frame 1. Add more by hand for disconnected
regions or strongly varying motion.</source>
        <translation>Coloca automáticamente un punto de inicio en el interior de la ROI
de la cámara IZQUIERDA, fotograma 1. Añada más a mano para regiones
inconexas o movimientos muy variables.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="113"/>
        <source>Remove all Starting Points</source>
        <translation>Eliminar todos los puntos de inicio</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="122"/>
        <source>FFT (cross-correlation)</source>
        <translation>FFT (correlación cruzada)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="125"/>
        <source>Full-grid cross-correlation seeds frame 1 (and every reference
switch in incremental mode); later frames warm-start from the
previous solution. Robust default — the search radius is the
Temporal Search parameter.</source>
        <translation>La correlación cruzada de rejilla completa siembra el fotograma 1 (y
cada cambio de referencia en modo incremental); los fotogramas
posteriores parten de la solución anterior. Valor predeterminado
robusto — el radio de búsqueda es el parámetro «Búsqueda temporal».</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="134"/>
        <source>Previous frame</source>
        <translation>Fotograma anterior</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="137"/>
        <source>Start every frame from the previous frame&apos;s solution — no
cross-correlation at all. Fastest; can silently freeze on large
motion or decorrelation — the validity gate will flag affected
frames.</source>
        <translation>Cada fotograma parte de la solución del fotograma anterior — sin
ninguna correlación cruzada. Lo más rápido; puede congelarse en
silencio con movimientos grandes o descorrelación — la puerta de
validez marcará los fotogramas afectados.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="191"/>
        <source>Placing… (click to exit)</source>
        <translation>Colocando… (clic para salir)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="233"/>
        <source>No point placed: the run finds the stereo offset from probe patches and seeds frame 1 by FFT. Place a point (or Auto-place) for large first-frame motion.</source>
        <translation>Sin punto colocado: la ejecución obtiene el desplazamiento estéreo con parches de sondeo e inicializa el fotograma 1 con FFT. Coloque un punto (o colocación automática) si el movimiento del primer fotograma es grande.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="240"/>
        <location filename="../../gui/widgets/init_guess_section.py" line="273"/>
        <source>{0} point(s) placed</source>
        <translation>{0} punto(s) colocado(s)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="276"/>
        <source>{0} point(s) · {1}/{2} regions ready</source>
        <translation>{0} punto(s) · {1}/{2} regiones listas</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="283"/>
        <source>{0} point(s) · {1}/{2} regions seeded — rest auto-seeded at run</source>
        <translation>{0} punto(s) · {1}/{2} regiones sembradas — el resto se siembra automáticamente al ejecutar</translation>
    </message>
</context>
<context>
    <name>Issues</name>
    <message>
        <location filename="../../gui/issue_text.py" line="27"/>
        <source>left camera</source>
        <translation>cámara izquierda</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="28"/>
        <source>right camera</source>
        <translation>cámara derecha</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="36"/>
        <source>calibration file not set</source>
        <translation>archivo de calibración no establecido</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="39"/>
        <source>left/right sequences not set</source>
        <translation>secuencias izquierda/derecha no establecidas</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="42"/>
        <source>need at least 2 frames</source>
        <translation>se necesitan al menos 2 fotogramas</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="43"/>
        <source>ROI not set</source>
        <translation>ROI no establecida</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="44"/>
        <source>ROI is empty (xmin&lt;xmax, ymin&lt;ymax required)</source>
        <translation>ROI vacía (se requiere xmin&lt;xmax, ymin&lt;ymax)</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="47"/>
        <source>left and right sequences use the same image files</source>
        <translation>las secuencias izquierda y derecha usan los mismos archivos de imagen</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="63"/>
        <source>sequence length mismatch: {0} vs {1}</source>
        <translation>longitudes de secuencia distintas: {0} frente a {1}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="67"/>
        <source>calibration file cannot be read: {0}</source>
        <translation>no se puede leer el archivo de calibración: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="71"/>
        <source>{0}: image not readable: {1}</source>
        <translation>{0}: imagen ilegible: {1}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="75"/>
        <source>{0}: frame sizes differ ({1} vs {2})</source>
        <translation>{0}: tamaños de fotograma distintos ({1} frente a {2})</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="79"/>
        <source>ROI mask is {0} but the images are {1}: redraw or import it again</source>
        <translation>la máscara ROI mide {0} pero las imágenes miden {1}: vuelva a dibujarla o importarla</translation>
    </message>
</context>
<context>
    <name>LeftSidebar3D</name>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="82"/>
        <source>IMAGES</source>
        <translation>IMÁGENES</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="89"/>
        <source>Drop LEFT camera
folder or click</source>
        <translation>Suelte la carpeta de la cámara
IZQUIERDA o haga clic</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="90"/>
        <source>Drop RIGHT camera
folder or click</source>
        <translation>Suelte la carpeta de la cámara
DERECHA o haga clic</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="95"/>
        <source>Natural Sort (1, 2, …, 10)</source>
        <translation>Orden natural (1, 2, …, 10)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="98"/>
        <source>Sort file names numerically (img2 before img10). Default on; turn off for strict alphabetical order. Applies to the next folder load.</source>
        <translation>Ordena los nombres de archivo numéricamente (img2 antes de img10). Activado por defecto; desactívelo para un orden estrictamente alfabético. Se aplica en la próxima carga de carpeta.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="116"/>
        <location filename="../../gui/panels/left_sidebar.py" line="687"/>
        <source>No images loaded</source>
        <translation>Ninguna imagen cargada</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="142"/>
        <source>CALIBRATION</source>
        <translation>CALIBRACIÓN</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="146"/>
        <source>WORKFLOW TYPE</source>
        <translation>TIPO DE FLUJO</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="153"/>
        <source>INITIAL GUESS</source>
        <translation>ESTIMACIÓN INICIAL</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="157"/>
        <source>REGION OF INTEREST</source>
        <translation>REGIÓN DE INTERÉS</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="161"/>
        <source>PARAMETERS</source>
        <translation>PARÁMETROS</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="165"/>
        <source>ADVANCED</source>
        <translation>AVANZADO</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="231"/>
        <source>Incremental: each frame is compared to the previous reference frame.
Suitable for large accumulated deformation, required for large rotations.

Accumulative: every frame is compared to frame 1.
Accurate for small, monotonic deformation only.</source>
        <translation>Incremental: cada fotograma se compara con el fotograma de referencia anterior.
Adecuado para grandes deformaciones acumuladas; obligatorio en grandes rotaciones.

Acumulativo: cada fotograma se compara con el fotograma 1.
Preciso solo para deformaciones pequeñas y monótonas.</translation>
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
        <translation>Local DIC: Coincidencia de subconjuntos independiente (IC-GN). Rápido,
conserva detalles locales nítidos. Ideal para pequeñas
deformaciones o imágenes de alta calidad.

AL-DIC: Lagrangiano aumentado con regularización
FEM global. Impone compatibilidad de desplazamientos
entre subconjuntos. Ideal para grandes deformaciones, imágenes
con ruido o cuando la precisión de la deformación es importante.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="261"/>
        <source>Solver</source>
        <translation>Solucionador</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="335"/>
        <location filename="../../gui/panels/left_sidebar.py" line="359"/>
        <source>bbox: not set</source>
        <translation>cuadro delimitador: sin definir</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="362"/>
        <source>bbox: {0}–{1}, {2}–{3} px</source>
        <translation>cuadro delimitador: {0}–{1}, {2}–{3} px</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="382"/>
        <source>IC-GN subset window size in pixels (odd number). Default 33.
Larger = more robust on sparse speckle, smoother fields;
smaller = finer spatial detail but noisier. The subset must
span several speckles.</source>
        <translation>Tamaño de la ventana de subset IC-GN en píxeles (impar). Por defecto 33.
Mayor = más robusto con moteado disperso, campos más suaves; menor = más detalle espacial pero más ruido.
El subset debe abarcar varias motas.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="226"/>
        <source>Accumulative</source>
        <translation>Acumulativo</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="227"/>
        <source>Incremental</source>
        <translation>Incremental</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="238"/>
        <source>Tracking Mode</source>
        <translation>Modo de seguimiento</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="317"/>
        <source>Draw on the LEFT camera, frame 1 — all later frames and the right camera follow from it.</source>
        <translation>Dibuje en la cámara IZQUIERDA, fotograma 1 — los fotogramas posteriores y la cámara derecha se derivan de él.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="388"/>
        <source>Subset Size</source>
        <translation>Tamaño del subconjunto</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="396"/>
        <source>Node spacing in pixels (power of 2). Default 16. Smaller =
denser measurement grid and longer runs; larger = faster but
coarser fields. Typically ¼–½ of the Subset Size.</source>
        <translation>Separación de nodos en píxeles (potencia de 2). Por defecto 16. Menor = malla de medición
más densa y ejecuciones más largas; mayor = más rápido pero campos más gruesos.
Típicamente ¼–½ del tamaño del subset.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="401"/>
        <source>Subset Step</source>
        <translation>Paso del subconjunto</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="407"/>
        <source>Stereo Search</source>
        <translation>Búsqueda estéreo</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="420"/>
        <source>Temporal Search</source>
        <translation>Búsqueda temporal</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="426"/>
        <source>Mesh refinement</source>
        <translation>Refinamiento de malla</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="433"/>
        <source>Refine at mask boundaries (holes)</source>
        <translation>Refinar en bordes de máscara (huecos)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="436"/>
        <source>Quadtree-subdivide mesh elements crossing interior mask
holes so the mesh hugs the hole edges. Default off (uniform
grid); enable when the ROI mask has cut-outs whose rims you
care about.</source>
        <translation>Subdivisión quadtree de los elementos de malla que cruzan agujeros internos de la máscara,
para que la malla se ciña a sus bordes. Por defecto desactivado (malla uniforme); actívelo
cuando la máscara de la ROI tenga recortes cuyos bordes importen.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="443"/>
        <source>Refine at ROI edges</source>
        <translation>Refinar en bordes de la ROI</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="446"/>
        <source>Quadtree-subdivide mesh elements along the outer ROI
boundary. Default off; enable for curved / irregular ROI
outlines where the uniform grid staircases.</source>
        <translation>Subdivisión quadtree de los elementos de malla a lo largo del borde exterior de la ROI.
Por defecto desactivado; actívelo con contornos de ROI curvos / irregulares donde la malla uniforme escalona.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="458"/>
        <source>How aggressively refined elements shrink: the minimum element
is step / 2^level. Default 1 (light); 3 is heavy — finer
boundary detail but many more nodes and a slower run.</source>
        <translation>Cuánto se reducen los elementos refinados: el elemento mínimo es paso / 2^nivel.
Por defecto 1 (ligero); 3 es intenso — más detalle en el borde pero muchos más nodos y una ejecución más lenta.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="463"/>
        <source>Refinement Level</source>
        <translation>Nivel de refinamiento</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="575"/>
        <source>NCC search half-width (pixels) around each node for the
left-to-right stereo match. Set larger than the largest
expected stereo disparity.</source>
        <translation>Semiancho de búsqueda NCC (píxeles) alrededor de cada nodo para la
correspondencia estéreo izquierda-derecha. Ajústelo por encima de la
mayor disparidad estéreo esperada.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="580"/>
        <source>Half-width (pixels) of the temporal FFT integer search that seeds
each per-frame match. Set comfortably larger than the expected
inter-frame motion; with Auto-expand on (default) the engine can
still grow the search past this on a boundary-clipped peak.</source>
        <translation>Semiancho (píxeles) de la búsqueda entera de FFT temporal que
inicializa cada emparejamiento por fotograma. Ajústelo bastante por
encima del movimiento esperado entre fotogramas; con la expansión
automática activada (predeterminado), el motor puede ampliar la
búsqueda más allá de este valor cuando un pico llega al borde.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="596"/>
        <source>Current images: the engine starts the FFT search clamped to
{0} px (max(10, min(H, W) / 4 - subset)); Auto-expand can grow
it to {1} px (max(32, min(H, W) / 2)) on clipped peaks.</source>
        <translation>Imágenes actuales: el motor limita al inicio la búsqueda FFT a
{0} px (max(10, min(H, W) / 4 - subconjunto)); ante un pico recortado,
la expansión automática puede aumentarla a {1} px
(max(32, min(H, W) / 2)).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="618"/>
        <source>Inactive with the current Initial Guess / Tracking Mode: the
temporal FFT runs only when Initial Guess = FFT, or at reference
switches in Incremental mode; in Accumulative + Starting Point /
Previous frame no FFT runs, so this control has no effect.</source>
        <translation>Sin efecto con la estimación inicial / el modo de seguimiento
actuales: la FFT temporal solo se ejecuta si la estimación inicial =
FFT, o en los cambios de referencia en modo incremental. En acumulativo
+ Punto inicial / Fotograma anterior no se ejecuta ninguna FFT, así que
este control no tiene efecto.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="592"/>
        <source>Current images: values above {0} px cannot widen the search
(the window is clamped at the image borders).</source>
        <translation>Imágenes actuales: por encima de {0} px la búsqueda ya no se amplía
(la ventana se recorta en los bordes de la imagen).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="267"/>
        <source>Extra filters (correlation, outliers)</source>
        <translation>Filtros adicionales (correlación, valores atípicos)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="270"/>
        <source>Post-run filters: drop points whose correlation (ZNSSD),
reprojection error or 3D-outlier distance is too poor.
Default off (keep every tracked point); enable for noisy
data when a few bad points pollute the fields. The log
reports how many points each filter removed.</source>
        <translation>Filtros tras la ejecución: descartan los puntos cuya correlación (ZNSSD),
error de reproyección o distancia de valor atípico 3D es demasiado mala.
Desactivados por defecto (se conservan todos los puntos seguidos);
actívelos con datos ruidosos cuando unos pocos puntos malos ensucian los campos.
El registro indica cuántos puntos quitó cada filtro.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="634"/>
        <source>No images found in {0}</source>
        <translation>No se encontraron imágenes en {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="642"/>
        <source>left camera</source>
        <translation>cámara izquierda</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="642"/>
        <source>right camera</source>
        <translation>cámara derecha</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="645"/>
        <source>This folder holds both cameras ({0}): using its {1} images for the {2}</source>
        <translation>Esta carpeta contiene ambas cámaras ({0}): se usan sus {1} imágenes para la {2}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="656"/>
        <source>{0}: {1} images from {2}</source>
        <translation>{0}: {1} imágenes de {2}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="692"/>
        <source>Paired: {0} frames per camera</source>
        <translation>Emparejado: {0} fotogramas por cámara</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="698"/>
        <source>Mismatch: {0} left vs {1} right</source>
        <translation>Discrepancia: {0} izquierda frente a {1} derecha</translation>
    </message>
</context>
<context>
    <name>MainMenuMixin</name>
    <message>
        <location filename="../../gui/main_menu.py" line="58"/>
        <source>&amp;File</source>
        <translation>&amp;Archivo</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="60"/>
        <source>New Project</source>
        <translation>Nuevo proyecto</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="66"/>
        <source>Open Project…</source>
        <translation>Abrir proyecto…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="73"/>
        <source>Recent Projects</source>
        <translation>Proyectos recientes</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="79"/>
        <source>Save Project</source>
        <translation>Guardar proyecto</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="84"/>
        <source>Save Project As…</source>
        <translation>Guardar proyecto como…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="94"/>
        <source>Associate .aldic3d files with pyALDIC-3D…</source>
        <translation>Asociar archivos .aldic3d con pyALDIC-3D…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="97"/>
        <source>Register .aldic3d so double-clicking a project file opens pyALDIC-3D (current user only, no admin rights needed).</source>
        <translation>Registra .aldic3d para que al hacer doble clic en un archivo de proyecto se abra pyALDIC-3D (solo el usuario actual, sin permisos de administrador).</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="105"/>
        <source>Quit</source>
        <translation>Salir</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="113"/>
        <source>&amp;Help</source>
        <translation>A&amp;yuda</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="114"/>
        <source>User Guide</source>
        <translation>Guía del usuario</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="118"/>
        <source>Keyboard Shortcuts</source>
        <translation>Atajos de teclado</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="121"/>
        <source>About pyALDIC-3D</source>
        <translation>Acerca de pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="132"/>
        <source>&amp;Settings</source>
        <translation>&amp;Configuración</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="133"/>
        <location filename="../../gui/main_menu.py" line="180"/>
        <source>Language</source>
        <translation>Idioma</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="157"/>
        <location filename="../../gui/main_menu.py" line="163"/>
        <source>File Association</source>
        <translation>Asociación de archivos</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="158"/>
        <source>Could not register the .aldic3d association: {0}</source>
        <translation>No se pudo registrar la asociación .aldic3d: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="165"/>
        <source>Done — double-clicking a .aldic3d file now opens it in pyALDIC-3D (registered for the current user).</source>
        <translation>Listo — al hacer doble clic en un archivo .aldic3d ahora se abre en pyALDIC-3D (registrado para el usuario actual).</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="174"/>
        <source>The interface language changes to {0} after pyALDIC-3D restarts.</source>
        <translation>El idioma de la interfaz cambiará a {0} al reiniciar pyALDIC-3D.</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="188"/>
        <source>Could not open a web browser. The user guide is at {0}</source>
        <translation>No se pudo abrir un navegador web. La guía del usuario está en {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="214"/>
        <source>(not reachable)</source>
        <translation>(no accesible)</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="220"/>
        <source>No recent projects</source>
        <translation>No hay proyectos recientes</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="224"/>
        <source>Clear list</source>
        <translation>Vaciar la lista</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="232"/>
        <source>The project file is not reachable right now: {0}</source>
        <translation>El archivo del proyecto no está accesible ahora: {0}</translation>
    </message>
</context>
<context>
    <name>MainWindow3D</name>
    <message>
        <location filename="../../gui/main_window.py" line="143"/>
        <source>pyALDIC-3D ready</source>
        <translation>pyALDIC-3D listo</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="184"/>
        <source>Run an analysis first — there are no results to post-process</source>
        <translation>Ejecute primero un análisis: no hay resultados que posprocesar</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="216"/>
        <source>Strain window available — open it from the sidebar</source>
        <translation>Ventana de deformación disponible: ábrala desde la barra lateral</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="278"/>
        <location filename="../../gui/main_window.py" line="296"/>
        <source>Analysis Running</source>
        <translation>Análisis en ejecución</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="279"/>
        <source>An analysis is running — cancel it and quit?</source>
        <translation>Hay un análisis en ejecución — ¿cancelarlo y salir?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="284"/>
        <location filename="../../gui/main_window.py" line="300"/>
        <location filename="../../gui/main_window.py" line="677"/>
        <source>Yes</source>
        <translation>Sí</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="285"/>
        <location filename="../../gui/main_window.py" line="301"/>
        <location filename="../../gui/main_window.py" line="678"/>
        <source>No</source>
        <translation>No</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="297"/>
        <source>An analysis is running — cancel it and switch projects?</source>
        <translation>Hay un análisis en curso: ¿cancelarlo y cambiar de proyecto?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="331"/>
        <source>Unsaved Changes</source>
        <translation>Cambios sin guardar</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="332"/>
        <source>The project has unsaved changes. Save them before continuing?</source>
        <translation>El proyecto tiene cambios sin guardar. ¿Guardarlos antes de continuar?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="339"/>
        <source>Save</source>
        <translation>Guardar</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="340"/>
        <source>Discard</source>
        <translation>Descartar</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="341"/>
        <location filename="../../gui/main_window.py" line="593"/>
        <location filename="../../gui/main_window.py" line="679"/>
        <source>Cancel</source>
        <translation>Cancelar</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="362"/>
        <source>Switched to left camera, frame 1 for ROI editing</source>
        <translation>Se cambió a la cámara izquierda, fotograma 1, para editar la ROI</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="367"/>
        <source>Load images first, then draw the region of interest</source>
        <translation>Cargue primero las imágenes y después dibuje la región de interés</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="380"/>
        <source>Load images first, then place a starting point</source>
        <translation>Cargue primero las imágenes y después coloque un punto de inicio</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="398"/>
        <source>Starting points are already placed; clear them to auto-place</source>
        <translation>Ya hay puntos de inicio colocados; límpielos para la colocación automática</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="404"/>
        <source>Draw the ROI first: the point is placed inside it</source>
        <translation>Dibuje primero la ROI: el punto se coloca dentro de ella</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="411"/>
        <source>Starting point placed automatically at ({0:.0f}, {1:.0f})</source>
        <translation>Punto de inicio colocado automáticamente en ({0:.0f}, {1:.0f})</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="419"/>
        <source>Load images first, then use the brush</source>
        <translation>Cargue primero las imágenes y después use el pincel</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="506"/>
        <source>Loading project…</source>
        <translation>Cargando el proyecto…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="508"/>
        <source>Could not open the project: {0}</source>
        <translation>No se pudo abrir el proyecto: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="511"/>
        <source>Could not open the project:
{0}

{1}</source>
        <translation>No se pudo abrir el proyecto:
{0}

{1}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="523"/>
        <source>Opened {0}</source>
        <translation>{0} abierto</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="546"/>
        <source>Open cancelled: {0}</source>
        <translation>Apertura cancelada: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="553"/>
        <source>Camera {0}: {1} image(s) not found (was {2}). Results stay viewable and exportable; running again needs the images.</source>
        <translation>Cámara {0}: no se encuentran {1} imagen(es) (antes en {2}). Los resultados se pueden ver y exportar; para volver a ejecutar se necesitan las imágenes.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="560"/>
        <source>Relocated {0} camera-{1} images: {2} -&gt; {3}</source>
        <translation>{0} imágenes de la cámara {1} reubicadas: {2} -&gt; {3}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="567"/>
        <source>Calibration file found at {0}</source>
        <translation>Archivo de calibración encontrado en {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="572"/>
        <source>The calibration file was not found; using the copy saved in the project: {0}</source>
        <translation>No se encontró el archivo de calibración; se usa la copia guardada en el proyecto: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="583"/>
        <source>Images Not Found</source>
        <translation>Imágenes no encontradas</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="586"/>
        <source>Some of this project&apos;s images cannot be found. Open it anyway? Results stay viewable and exportable; running again needs the images.</source>
        <translation>No se encuentran algunas imágenes de este proyecto. ¿Abrirlo de todos modos? Los resultados se pueden ver y exportar; para volver a ejecutarlo se necesitan las imágenes.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="592"/>
        <source>Open anyway</source>
        <translation>Abrir de todos modos</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="601"/>
        <location filename="../../gui/main_window.py" line="611"/>
        <source>Locate Images</source>
        <translation>Localizar imágenes</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="603"/>
        <source>The selected folder does not contain this project&apos;s camera {0} frames. Pick the folder holding the original image files, or cancel to abort opening.</source>
        <translation>La carpeta seleccionada no contiene los fotogramas de la cámara {0} de este proyecto. Elija la carpeta con los archivos de imagen originales, o cancele para abortar la apertura.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="613"/>
        <source>The image folder saved with this project was not found:
{0}

Select the folder that now contains the camera {1} frames (file names must match).</source>
        <translation>No se encontró la carpeta de imágenes guardada con este proyecto:
{0}

Seleccione la carpeta que ahora contiene los fotogramas de la cámara {1} (los nombres de archivo deben coincidir).</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="620"/>
        <source>Locate images for camera {0}</source>
        <translation>Localizar imágenes de la cámara {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="662"/>
        <source>Include Results?</source>
        <translation>¿Incluir resultados?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="663"/>
        <source>Include the analysis results in this project file?</source>
        <translation>¿Incluir los resultados del análisis en este archivo de proyecto?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="666"/>
        <source>Including results (about {0} uncompressed) lets you reopen the project without recomputing. Choose No to save a small configuration-only file for sharing.</source>
        <translation>Incluir los resultados (aprox. {0} sin comprimir) permite reabrir el proyecto sin recalcular. Elija No para guardar un archivo pequeño de solo configuración, fácil de compartir.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="704"/>
        <source>unknown size</source>
        <translation>tamaño desconocido</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="714"/>
        <source>Saving project…</source>
        <translation>Guardando el proyecto…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="718"/>
        <source>Could not save the project: {0}</source>
        <translation>No se pudo guardar el proyecto: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="722"/>
        <source>Could not save the project:
{0}

{1}

The previous version of the file, if any, is unchanged.</source>
        <translation>No se pudo guardar el proyecto:
{0}

{1}

La versión anterior del archivo, si existe, no ha cambiado.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="730"/>
        <source>Saved {0}</source>
        <translation>{0} guardado</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="436"/>
        <source>Untitled</source>
        <translation>Sin título</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="437"/>
        <source>{0}[*] — pyALDIC-3D</source>
        <translation>{0}[*] — pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="482"/>
        <source>New project</source>
        <translation>Nuevo proyecto</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="491"/>
        <location filename="../../gui/main_window.py" line="510"/>
        <source>Open Project</source>
        <translation>Abrir proyecto</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="493"/>
        <location filename="../../gui/main_window.py" line="648"/>
        <source>pyALDIC-3D project (*.aldic3d)</source>
        <translation>Proyecto pyALDIC-3D (*.aldic3d)</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="646"/>
        <location filename="../../gui/main_window.py" line="720"/>
        <source>Save Project</source>
        <translation>Guardar proyecto</translation>
    </message>
</context>
<context>
    <name>ManualParamsDialog</name>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="53"/>
        <source>Manual Camera Parameters</source>
        <translation>Parámetros manuales de cámara</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="61"/>
        <source>Left camera (world frame)</source>
        <translation>Cámara izquierda (sistema mundo)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="62"/>
        <source>Right camera</source>
        <translation>Cámara derecha</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="67"/>
        <source>Stereo extrinsics  (X_R = R · X_L + T)</source>
        <translation>Extrínsecos estéreo (X_R = R · X_L + T)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="71"/>
        <source>{0} (deg)</source>
        <translation>{0} (grados)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="78"/>
        <source>{0} (mm)</source>
        <translation>{0} (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="87"/>
        <source>Euler composition R = Rz·Ry·Rx in degrees (MatchID/OpenCorr convention); distortion order k1, k2, p1, p2, k3 (OpenCV).</source>
        <translation>Composición de Euler R = Rz·Ry·Rx en grados (convención MatchID/OpenCorr); orden de distorsión k1, k2, p1, p2, k3 (OpenCV).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="101"/>
        <source>Save as YAML…</source>
        <translation>Guardar como YAML…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="106"/>
        <source>Cancel</source>
        <translation>Cancelar</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="142"/>
        <source>Baseline |T| = {0:.2f} mm</source>
        <translation>Línea base |T| = {0:.2f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="147"/>
        <source>Baseline is zero — enter the translation T first.</source>
        <translation>La línea base es cero — introduzca primero la traslación T.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="154"/>
        <source>Save calibration as</source>
        <translation>Guardar calibración como</translation>
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
        <translation>Malla:</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="40"/>
        <source>Line color and width of the mesh overlay (Show Grid)</source>
        <translation>Color y grosor de las líneas de la malla (Mostrar cuadrícula)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="45"/>
        <source>Mesh overlay line color — click to choose</source>
        <translation>Color de línea de la malla — clic para elegir</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="53"/>
        <source>Mesh overlay line width (screen pixels)</source>
        <translation>Grosor de línea de la malla (píxeles de pantalla)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="79"/>
        <source>Choose mesh line color</source>
        <translation>Elegir color de línea de la malla</translation>
    </message>
</context>
<context>
    <name>NextStepHint</name>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="49"/>
        <source>Load the left and right camera folders</source>
        <translation>Cargue las carpetas de las cámaras izquierda y derecha</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="54"/>
        <source>Calibrate from images or import a calibration</source>
        <translation>Calibre a partir de imágenes o importe una calibración</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="56"/>
        <source>Draw the ROI on the left camera, frame 1</source>
        <translation>Dibuje la ROI en la cámara izquierda, fotograma 1</translation>
    </message>
</context>
<context>
    <name>PairActionsMixin</name>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="58"/>
        <source>Removed {0} image pair(s)</source>
        <translation>Se quitaron {0} par(es) de imágenes</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="69"/>
        <source>Remove Image Pairs</source>
        <translation>Eliminar pares de imágenes</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="72"/>
        <source>Removing {0} pair(s) changes the sequence — the current results will be discarded. Continue?</source>
        <translation>Eliminar {0} par(es) cambia la secuencia: los resultados actuales se descartarán. ¿Continuar?</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="78"/>
        <source>Yes</source>
        <translation>Sí</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="79"/>
        <source>No</source>
        <translation>No</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="94"/>
        <source>Folder does not exist: {0}</source>
        <translation>La carpeta no existe: {0}</translation>
    </message>
</context>
<context>
    <name>PairBars</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="106"/>
        <source>no solve yet</source>
        <translation>aún sin solución</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="128"/>
        <source>worst-camera RMS per pair; dashed = reject threshold</source>
        <translation>RMS de la peor cámara por par; discontinua = umbral de rechazo</translation>
    </message>
</context>
<context>
    <name>PairListWidget</name>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="25"/>
        <source>Left</source>
        <translation>Izquierda</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="25"/>
        <source>Right</source>
        <translation>Derecha</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="70"/>
        <source>Remove {0} selected pair(s)</source>
        <translation>Eliminar los {0} par(es) seleccionados</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="73"/>
        <source>Reveal in Explorer</source>
        <translation>Mostrar en el Explorador</translation>
    </message>
</context>
<context>
    <name>PreviewTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="120"/>
        <source>Open this tab to render a preview.</source>
        <translation>Abre esta pestaña para generar una vista previa.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="128"/>
        <source>Field</source>
        <translation>Campo</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="135"/>
        <source>Frame</source>
        <translation>Fotograma</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="144"/>
        <source>Camera</source>
        <translation>Cámara</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="148"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="226"/>
        <source>Left</source>
        <translation>Izquierda</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="149"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="225"/>
        <source>Right</source>
        <translation>Derecha</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="180"/>
        <source>FIELD APPEARANCE</source>
        <translation>APARIENCIA DEL CAMPO</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="185"/>
        <source>Colormap</source>
        <translation>Mapa de colores</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="187"/>
        <source>Auto</source>
        <translation>Auto</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="188"/>
        <source>Auto range</source>
        <translation>Rango automático</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="191"/>
        <source>Range</source>
        <translation>Rango</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="197"/>
        <source>Min</source>
        <translation>Mín</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="198"/>
        <source>Max</source>
        <translation>Máx</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="205"/>
        <source>Opacity</source>
        <translation>Opacidad</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="207"/>
        <source>Apply to all fields</source>
        <translation>Aplicar a todos los campos</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="210"/>
        <source>Apply this field&apos;s colormap, opacity and auto-range to every enabled field (each field keeps its own min/max).</source>
        <translation>Aplica el colormap, la opacidad y el rango automático de este campo a todos los campos activados (cada campo conserva su propio mín/máx).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="220"/>
        <source>COLORBAR STYLE</source>
        <translation>ESTILO DE BARRA DE COLOR</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="227"/>
        <source>Top</source>
        <translation>Arriba</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="228"/>
        <source>Bottom</source>
        <translation>Abajo</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="232"/>
        <source>Position</source>
        <translation>Posición</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="238"/>
        <source>Font size</source>
        <translation>Tamaño de fuente</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="244"/>
        <source>Font family</source>
        <translation>Fuente</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="252"/>
        <source>Bar thickness</source>
        <translation>Grosor de la barra</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="255"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="274"/>
        <source>Black</source>
        <translation>Negro</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="255"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="274"/>
        <source>White</source>
        <translation>Blanco</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="258"/>
        <source>Background</source>
        <translation>Fondo</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="266"/>
        <source>Add a blank border around the exported content, as a fraction of the long edge (0 = none).</source>
        <translation>Añade un borde en blanco alrededor del contenido exportado, como fracción del borde largo (0 = ninguna).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="271"/>
        <source>Margin</source>
        <translation>Margen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="277"/>
        <source>Margin color</source>
        <translation>Color del margen</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="279"/>
        <source>Refresh preview</source>
        <translation>Actualizar vista previa</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="531"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="545"/>
        <source>Preview failed: </source>
        <translation>Error en la vista previa: </translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="430"/>
        <source>Enable a field on the Images tab to preview.</source>
        <translation>Active un campo en la pestaña Images para la vista previa.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="549"/>
        <source>No data for this field/frame.</source>
        <translation>No hay datos para este campo/fotograma.</translation>
    </message>
</context>
<context>
    <name>Progress</name>
    <message>
        <location filename="../../gui/progress_text.py" line="30"/>
        <source>Preparing: checking the images and building the mesh</source>
        <translation>Preparando: comprobando las imágenes y creando la malla</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="33"/>
        <source>Preparing: initial guess for the left camera</source>
        <translation>Preparando: estimación inicial de la cámara izquierda</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="36"/>
        <source>Preparing: mesh and initial guess for the right camera</source>
        <translation>Preparando: malla y estimación inicial de la cámara derecha</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="39"/>
        <source>Preparing: estimating the stereo offset</source>
        <translation>Preparando: estimando el desplazamiento estéreo</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="42"/>
        <location filename="../../gui/progress_text.py" line="53"/>
        <source>tracking complete</source>
        <translation>seguimiento completado</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="43"/>
        <source>normalizing images</source>
        <translation>normalizando imágenes</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="46"/>
        <location filename="../../gui/progress_text.py" line="49"/>
        <source>composing displacements</source>
        <translation>componiendo desplazamientos</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="52"/>
        <source>assembling results</source>
        <translation>ensamblando resultados</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="62"/>
        <source>Left camera</source>
        <translation>Cámara izquierda</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="64"/>
        <source>Right camera</source>
        <translation>Cámara derecha</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="66"/>
        <source>{0}: {1}</source>
        <translation>{0}: {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="74"/>
        <source>tracking frame {0} of {1}</source>
        <translation>siguiendo el fotograma {0} de {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="80"/>
        <source>verifying frame {0} of {1} (keeping the frames tracked before the stop)</source>
        <translation>verificando el fotograma {0} de {1} (se conservan los fotogramas seguidos antes de la parada)</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="85"/>
        <source>verifying frame {0} of {1}</source>
        <translation>verificando el fotograma {0} de {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="89"/>
        <source>assembling frame {0} of {1}</source>
        <translation>ensamblando el fotograma {0} de {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="94"/>
        <source>strain: frame {0} of {1}</source>
        <translation>deformación: fotograma {0} de {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="99"/>
        <source>Preparing: matching the two cameras at {0} nodes</source>
        <translation>Preparando: emparejando las dos cámaras en {0} nodos</translation>
    </message>
</context>
<context>
    <name>ProgressRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="156"/>
        <source>Cancel</source>
        <translation>Cancelar</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="173"/>
        <source>Exporting…</source>
        <translation>Exportando…</translation>
    </message>
</context>
<context>
    <name>ROIToolbar</name>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="75"/>
        <source>+ Add</source>
        <translation>+ Añadir</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="77"/>
        <source>Add region to the Region of Interest (Polygon / Rectangle / Circle)</source>
        <translation>Añadir región a la región de interés (Polígono / Rectángulo / Círculo)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="81"/>
        <source>Cut</source>
        <translation>Recortar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="83"/>
        <source>Cut region from the Region of Interest (Polygon / Rectangle / Circle)</source>
        <translation>Recortar región de la región de interés (Polígono / Rectángulo / Círculo)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="87"/>
        <source>+ Refine</source>
        <translation>+ Refinar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="90"/>
        <source>Paint extra mesh-refinement zones with a brush
(on the LEFT camera, frame 1 — the reference mesh geometry)</source>
        <translation>Pintar zonas adicionales de refinamiento de malla con un pincel
(en la cámara IZQUIERDA, fotograma 1 — la geometría de la malla de referencia)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="110"/>
        <source>Import</source>
        <translation>Importar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="111"/>
        <source>Import mask from image file</source>
        <translation>Importar máscara desde archivo de imagen</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="120"/>
        <source>Save</source>
        <translation>Guardar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="121"/>
        <source>Save current mask to PNG file</source>
        <translation>Guardar la máscara actual en archivo PNG</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="126"/>
        <source>Invert</source>
        <translation>Invertir</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="127"/>
        <source>Invert the Region of Interest mask</source>
        <translation>Invertir la máscara de la región de interés</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="132"/>
        <source>Clear</source>
        <translation>Limpiar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="133"/>
        <source>Clear all Region of Interest masks</source>
        <translation>Limpiar todas las máscaras de región de interés</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="159"/>
        <source>Polygon</source>
        <translation>Polígono</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="163"/>
        <source>Rectangle</source>
        <translation>Rectángulo</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="167"/>
        <source>Circle</source>
        <translation>Círculo</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="171"/>
        <source>Circle (3-point)</source>
        <translation>Círculo (3 puntos)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="185"/>
        <source>Radius</source>
        <translation>Radio</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="202"/>
        <source>Paint</source>
        <translation>Pintar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="206"/>
        <source>Erase</source>
        <translation>Borrar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="215"/>
        <source>Clear Brush</source>
        <translation>Limpiar pincel</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="247"/>
        <source>Import Mask Image</source>
        <translation>Importar imagen de máscara</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="249"/>
        <source>Images (*.png *.bmp *.tif *.tiff *.jpg *.jpeg);;All Files (*)</source>
        <translation>Imágenes (*.png *.bmp *.tif *.tiff *.jpg *.jpeg);;Todos los archivos (*)</translation>
    </message>
</context>
<context>
    <name>RefUpdateSection3D</name>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="55"/>
        <source>Reference Update</source>
        <translation>Actualización de referencia</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="60"/>
        <source>Every Frame</source>
        <translation>Cada fotograma</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="61"/>
        <source>Every N Frames</source>
        <translation>Cada N fotogramas</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="62"/>
        <source>Custom Frames</source>
        <translation>Fotogramas personalizados</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="65"/>
        <source>How often the incremental reference frame advances.
Every Frame (default): frame k matches against k−1 — tracks
large accumulated deformation, but drift can accumulate.
Every N Frames: the reference advances only every N frames —
less drift, needs correlation to survive N frames of motion.
Custom Frames: reference updates exactly at the listed frames.</source>
        <translation>Con qué frecuencia avanza el fotograma de referencia en modo
incremental.
Cada fotograma (predeterminado): el fotograma k se compara con k−1 —
sigue grandes deformaciones acumuladas, pero la deriva puede
acumularse.
Cada N fotogramas: la referencia solo avanza cada N fotogramas —
menos deriva, pero la correlación debe sobrevivir a N fotogramas de
movimiento.
Fotogramas personalizados: la referencia se actualiza exactamente en
los fotogramas listados.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="78"/>
        <source>Update every</source>
        <translation>Actualizar cada</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="85"/>
        <source> frames</source>
        <translation> fotogramas</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="87"/>
        <source>Reference-update interval N: frames k use the last reference at i·N &lt; k</source>
        <translation>Intervalo de actualización N: el fotograma k usa la última referencia con i·N &lt; k</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="93"/>
        <source>e.g. 5, 10, 20 (0-based frame indices)</source>
        <translation>p. ej. 5, 10, 20 (índices de fotograma desde 0)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="96"/>
        <source>Comma-separated 0-based frame indices that become reference
frames (frame 0 always is one). The last frame cannot be a
reference.</source>
        <translation>Índices de fotograma desde 0, separados por comas, que se convierten
en fotogramas de referencia (el fotograma 0 siempre lo es). El último
fotograma no puede ser referencia.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="141"/>
        <source>Enter comma-separated 0-based frame numbers, e.g. 5, 10, 20</source>
        <translation>Introduzca números de fotograma desde 0 separados por comas, p. ej. 5, 10, 20</translation>
    </message>
</context>
<context>
    <name>RightSidebar3D</name>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="99"/>
        <source>Run 3D Analysis</source>
        <translation>Ejecutar análisis 3D</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="105"/>
        <location filename="../../gui/panels/right_sidebar.py" line="456"/>
        <source>Run the full stereo correspondence + triangulation pipeline on the loaded image pairs (F5).</source>
        <translation>Ejecuta el pipeline completo de correspondencia estéreo + triangulación sobre los pares de imágenes cargados (F5).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="112"/>
        <source>Cancel</source>
        <translation>Cancelar</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="127"/>
        <source>Export Results</source>
        <translation>Exportar resultados</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="135"/>
        <source>Open Strain Window</source>
        <translation>Abrir ventana de deformación</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="148"/>
        <source>Parameters changed since this result — re-run to update</source>
        <translation>Parámetros modificados desde este resultado — vuelva a ejecutar para actualizar</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="156"/>
        <source>PROGRESS</source>
        <translation>PROGRESO</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="163"/>
        <location filename="../../gui/panels/right_sidebar.py" line="638"/>
        <source>Ready</source>
        <translation>Listo</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="168"/>
        <source>ELAPSED  --:--</source>
        <translation>TRANSCURRIDO  --:--</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="171"/>
        <source>REMAINING  --:--</source>
        <translation>RESTANTE  --:--</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="177"/>
        <source>FIELD</source>
        <translation>CAMPO</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="183"/>
        <source>Show on deformed frame</source>
        <translation>Mostrar en fotograma deformado</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="187"/>
        <source>When checked, overlay results on the deformed (current) frame instead of the reference frame</source>
        <translation>Si está activado, los resultados se superponen sobre el fotograma deformado (actual) en lugar del fotograma de referencia</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="196"/>
        <source>Camera</source>
        <translation>Cámara</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="200"/>
        <source>Left</source>
        <translation>Izquierda</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="203"/>
        <source>Show the LEFT camera&apos;s images (the reference view: ROI, seed and mesh live here). Default.</source>
        <translation>Muestra las imágenes de la cámara IZQUIERDA (vista de referencia: la ROI, el punto inicial y la malla viven aquí). Por defecto.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="207"/>
        <source>Right</source>
        <translation>Derecha</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="210"/>
        <source>Show the RIGHT camera&apos;s images with the field warped onto them — a cross-check that the stereo match is sound.</source>
        <translation>Muestra las imágenes de la cámara DERECHA con el campo proyectado sobre ellas — una verificación cruzada de que el emparejamiento estéreo es sólido.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="226"/>
        <source>VISUALIZATION</source>
        <translation>VISUALIZACIÓN</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="229"/>
        <source>Colormap</source>
        <translation>Mapa de colores</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="237"/>
        <source>Colormap for the field overlay and the 3D surface. Default turbo (perceptually ordered, high contrast); pick RdBu_r or coolwarm for signed fields centered on zero.</source>
        <translation>Mapa de color para la superposición de campo y la superficie 3D. Por defecto turbo (perceptualmente ordenado, alto contraste); elija RdBu_r o coolwarm para campos con signo centrados en cero.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="246"/>
        <source>Auto range</source>
        <translation>Rango automático</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="250"/>
        <source>Rescale the color range to each frame&apos;s data range (2–98 percentile of the visible values). Default on; uncheck to type fixed Min/Max bounds that hold across frames.</source>
        <translation>Ajustar el rango de colores al rango de datos de cada fotograma (percentiles 2–98 de los valores visibles). Activado por defecto; desmarque para escribir límites Mín/Máx fijos que se mantienen en todos los fotogramas.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="262"/>
        <source>Min</source>
        <translation>Mín</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="270"/>
        <source>Lower color-range bound (only with Auto range off)</source>
        <translation>Límite inferior del rango de color (solo con el rango automático desactivado)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="271"/>
        <source>Upper color-range bound (only with Auto range off)</source>
        <translation>Límite superior del rango de color (solo con el rango automático desactivado)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="277"/>
        <source>Max</source>
        <translation>Máx</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="283"/>
        <source>Opacity</source>
        <translation>Opacidad</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="290"/>
        <source>Overlay opacity (0 = transparent, 100 = opaque)</source>
        <translation>Opacidad de la superposición (0 = transparente, 100 = opaco)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="297"/>
        <source>UNITS</source>
        <translation>UNIDADES</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="304"/>
        <source>LOG</source>
        <translation>REGISTRO</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="313"/>
        <source>All messages</source>
        <translation>Todos los mensajes</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="314"/>
        <source>Info</source>
        <translation>Información</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="315"/>
        <source>Warnings + errors</source>
        <translation>Avisos + errores</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="316"/>
        <source>Errors only</source>
        <translation>Solo errores</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="319"/>
        <source>Show only log messages of this severity</source>
        <translation>Mostrar solo los mensajes de esta gravedad</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="322"/>
        <source>Save…</source>
        <translation>Guardar…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="327"/>
        <source>Save the full log to a text file</source>
        <translation>Guardar el registro completo en un archivo de texto</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="330"/>
        <source>Clear</source>
        <translation>Limpiar</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="335"/>
        <source>Clear the log console (messages are not recoverable)</source>
        <translation>Limpiar la consola de registro (los mensajes no se pueden recuperar)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="419"/>
        <source>Save log</source>
        <translation>Guardar registro</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="419"/>
        <source>Text files (*.txt)</source>
        <translation>Archivos de texto (*.txt)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="430"/>
        <source>Log saved to {0}</source>
        <translation>Registro guardado en {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="452"/>
        <location filename="../../gui/panels/right_sidebar.py" line="468"/>
        <source>Not ready — {0}</source>
        <translation>No está listo — {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="472"/>
        <source>Ready to run. No starting point: the stereo offset is found automatically and frame 1 is seeded by FFT.</source>
        <translation>Listo para ejecutar. Sin punto de inicio: el desplazamiento estéreo se encuentra automáticamente y el fotograma 1 se inicializa con FFT.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="477"/>
        <source>Ready to run.</source>
        <translation>Listo para ejecutar.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="512"/>
        <source>Export displacement and strain results to NPZ / MAT / CSV</source>
        <translation>Exportar resultados de desplazamiento y deformación a NPZ / MAT / CSV</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="516"/>
        <source>Compute and visualize strain in a separate post-processing window. Requires displacement results from a completed Run.</source>
        <translation>Calcular y visualizar la deformación en una ventana de post-procesado separada. Requiere resultados de desplazamiento de una ejecución completada.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="522"/>
        <source>Available after the running analysis finishes.</source>
        <translation>Disponible cuando termine el análisis en curso.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="524"/>
        <source>Run an analysis first — there are no results yet.</source>
        <translation>Ejecute primero un análisis — todavía no hay resultados.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="542"/>
        <source>Not ready: {0}</source>
        <translation>No está listo: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="559"/>
        <source>Starting 3D analysis…</source>
        <translation>Iniciando análisis 3D…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="578"/>
        <source>Cancelling — finishing current frame…</source>
        <translation>Cancelando — terminando el fotograma actual…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="579"/>
        <source>Cancelling…</source>
        <translation>Cancelando…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="604"/>
        <source>Stopped early — partial results kept</source>
        <translation>Detenido antes de tiempo — se conservaron los resultados parciales</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="597"/>
        <source>Analysis complete</source>
        <translation>Análisis completado</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="427"/>
        <location filename="../../gui/panels/right_sidebar.py" line="616"/>
        <source>Failed: {0}</source>
        <translation>Fallo: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="118"/>
        <source>Cancel the current analysis. Frames computed so far are kept as a partial result; only when nothing was computed yet does the run return to IDLE.</source>
        <translation>Cancela el análisis actual. Los fotogramas ya calculados se conservan como resultado parcial; solo cuando aún no se ha calculado nada, la ejecución vuelve al estado inactivo.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="615"/>
        <source>Analysis failed</source>
        <translation>El análisis falló</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="620"/>
        <source>Analysis Failed</source>
        <translation>Análisis fallido</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="622"/>
        <source>The analysis stopped with an error:

{0}

The log has the details.</source>
        <translation>El análisis se detuvo con un error:

{0}

El registro tiene los detalles.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="641"/>
        <source>Run cancelled</source>
        <translation>Ejecución cancelada</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="556"/>
        <location filename="../../gui/panels/right_sidebar.py" line="639"/>
        <location filename="../../gui/panels/right_sidebar.py" line="648"/>
        <source>ELAPSED  {0}</source>
        <translation>TRANSCURRIDO  {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="557"/>
        <location filename="../../gui/panels/right_sidebar.py" line="596"/>
        <location filename="../../gui/panels/right_sidebar.py" line="640"/>
        <location filename="../../gui/panels/right_sidebar.py" line="654"/>
        <source>REMAINING  {0}</source>
        <translation>RESTANTE  {0}</translation>
    </message>
</context>
<context>
    <name>RunSummaryMixin</name>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="25"/>
        <source>Analysis complete</source>
        <translation>Análisis completado</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="41"/>
        <source>Stopped early at frame {0}/{1} — kept {2} computed frames (later frames are empty)</source>
        <translation>Detenido antes de tiempo en el fotograma {0}/{1} — se conservaron {2} fotogramas calculados (los fotogramas posteriores están vacíos)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="47"/>
        <source>Run interrupted: {0}</source>
        <translation>Ejecución interrumpida: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="51"/>
        <source>Frame-1 stereo match: {0}/{1} points matched ({2}%)</source>
        <translation>Emparejamiento estéreo del fotograma 1: {0}/{1} puntos emparejados ({2} %)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="59"/>
        <source>Camera {0}: validity gate removed {1} node-frames (correlation vs frame 1 failed)</source>
        <translation>Cámara {0}: la puerta de validez eliminó {1} nodos-fotograma (falló la correlación con el fotograma 1)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="66"/>
        <source>Frame {0}: only {1}% of points valid</source>
        <translation>Fotograma {0}: solo el {1}% de los puntos es válido</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="73"/>
        <source>Quality gate (ZNSSD) removed {0} positions</source>
        <translation>La puerta de calidad (ZNSSD) eliminó {0} posiciones</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="74"/>
        <source>Reprojection gate removed {0} positions</source>
        <translation>La puerta de reproyección eliminó {0} posiciones</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="75"/>
        <source>3D outlier filter removed {0} positions</source>
        <translation>El filtro de valores atípicos 3D eliminó {0} posiciones</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="89"/>
        <source>Validity falls from {0}% (frame 1) to {1}%: tracking every frame against frame 1 cannot follow large deformation. Try WORKFLOW TYPE &gt; Incremental.</source>
        <translation>La validez cae del {0} % (fotograma 1) al {1} %: comparar cada fotograma con el fotograma 1 no sigue deformaciones grandes. Pruebe TIPO DE FLUJO &gt; Incremental.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="95"/>
        <source>Validity falls from {0}% (frame 1) to {1}%: if the valid region changes during the test (cracks, failure), import per-frame masks (REGION OF INTEREST).</source>
        <translation>La validez cae del {0} % (fotograma 1) al {1} %: si la región válida cambia durante el ensayo (grietas, rotura), importe máscaras por fotograma (REGIÓN DE INTERÉS).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="103"/>
        <source>No valid points in ANY frame — the run produced an empty result. Check ROI, masks and seeding (details above).</source>
        <translation>Ningún punto válido en NINGÚN fotograma — la ejecución produjo un resultado vacío. Revise la ROI, las máscaras y el punto de inicio (detalles arriba).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="111"/>
        <source>Analysis complete — {0} frames, median validity {1}%, {2} frame(s) below {3}% (see above)</source>
        <translation>Análisis completado — {0} fotogramas, validez mediana {1}%, {2} fotograma(s) por debajo del {3}% (ver arriba)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="124"/>
        <source>Analysis complete — {0} frames, median validity {1}%</source>
        <translation>Análisis completado: {0} fotogramas, validez mediana {1} %</translation>
    </message>
</context>
<context>
    <name>RunWarnings</name>
    <message>
        <location filename="../../gui/warning_text.py" line="24"/>
        <source>No Starting Point placed: frame 1 is seeded by an FFT search (place a point for large first-frame motion)</source>
        <translation>Sin punto de inicio: el fotograma 1 se inicializa con una búsqueda FFT (coloque un punto si el movimiento del primer fotograma es grande)</translation>
    </message>
    <message>
        <location filename="../../gui/warning_text.py" line="32"/>
        <source>FFT search range reduced from {0} to {1} px to fit the {2} × {3} px images</source>
        <translation>Rango de búsqueda FFT reducido de {0} a {1} px para las imágenes de {2} × {3} px</translation>
    </message>
</context>
<context>
    <name>ShortcutsDialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="74"/>
        <source>Keyboard Shortcuts</source>
        <translation>Atajos de teclado</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="86"/>
        <source>Run the 3D analysis</source>
        <translation>Ejecutar el análisis 3D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="87"/>
        <source>Fit the image to the viewport</source>
        <translation>Ajustar la imagen a la vista</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="88"/>
        <source>Zoom in / out</source>
        <translation>Acercar / alejar</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="89"/>
        <source>Previous / next frame</source>
        <translation>Fotograma anterior / siguiente</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="90"/>
        <source>Play / pause (on the canvas: hold to pan)</source>
        <translation>Reproducir / pausar (en el lienzo: mantener para desplazar)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="91"/>
        <source>New project</source>
        <translation>Nuevo proyecto</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="92"/>
        <source>Open a project</source>
        <translation>Abrir un proyecto</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="93"/>
        <source>Save the project</source>
        <translation>Guardar el proyecto</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="94"/>
        <source>Save the project as…</source>
        <translation>Guardar el proyecto como…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="95"/>
        <source>Cancel the active drawing tool</source>
        <translation>Cancelar la herramienta de dibujo activa</translation>
    </message>
</context>
<context>
    <name>StrainFieldSelector3D</name>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="46"/>
        <source>εxx — normal strain along the strain frame&apos;s x axis</source>
        <translation>εxx — deformación normal según el eje x del sistema de deformación</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="47"/>
        <source>εyy — normal strain along the strain frame&apos;s y axis</source>
        <translation>εyy — deformación normal según el eje y del sistema de deformación</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="48"/>
        <source>εxy — in-plane shear strain (tensor component)</source>
        <translation>εxy — deformación cortante en el plano (componente tensorial)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="49"/>
        <source>ε₁ — major principal strain (largest in-plane eigenvalue)</source>
        <translation>ε₁ — deformación principal mayor (mayor autovalor en el plano)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="50"/>
        <source>ε₂ — minor principal strain (smallest in-plane eigenvalue)</source>
        <translation>ε₂ — deformación principal menor (menor autovalor en el plano)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="51"/>
        <source>γ max — maximum shear strain, (ε₁ − ε₂) / 2</source>
        <translation>γ max — deformación cortante máxima, (ε₁ − ε₂) / 2</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="52"/>
        <source>von Mises — equivalent strain (plane-stress invariant)</source>
        <translation>von Mises — deformación equivalente (invariante de tensión plana)</translation>
    </message>
</context>
<context>
    <name>StrainNavigator3D</name>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="52"/>
        <source>Previous frame (←)</source>
        <translation>Fotograma anterior (←)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="59"/>
        <location filename="../../gui/widgets/strain_navigator.py" line="128"/>
        <source>Play animation (Space)</source>
        <translation>Reproducir animación (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="66"/>
        <source>Next frame (→)</source>
        <translation>Fotograma siguiente (→)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="75"/>
        <source>Playback speed (frames per second). Default 2 fps.</source>
        <translation>Velocidad de reproducción (fotogramas por segundo). Por defecto 2 fps.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="79"/>
        <location filename="../../gui/widgets/strain_navigator.py" line="198"/>
        <source>FRAME 0/0</source>
        <translation>FOTOGRAMA 0/0</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="181"/>
        <source>Pause animation (Space)</source>
        <translation>Pausar animación (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="196"/>
        <source>FRAME {0}/{1}</source>
        <translation>FOTOGRAMA {0}/{1}</translation>
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
        <translation>Longitud del lado, en píxeles, de la ventana cuadrada alrededor de cada nodo usada para ajustar el gradiente de desplazamiento local (la galga de deformación virtual).

• Ventana más grande → deformación más suave, menor resolución espacial.
• Ventana más pequeña → deformación más nítida, más ruido.
• Debe abarcar al menos 3×3 nodos: use ≥ 2 × espaciado de nodos + 1 px.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="89"/>
        <source>Strain window</source>
        <translation>Ventana VSG</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="101"/>
        <source>Number of mesh nodes per axis inside the square strain window — the local plane fit uses every valid node in it. The mm size maps the pixel window through the median 3D spacing of adjacent nodes on the reference surface.</source>
        <translation>Número de nodos de la malla por eje dentro de la ventana de deformación cuadrada — el ajuste de plano local usa todos los nodos válidos que contiene. El tamaño en mm convierte la ventana de píxeles mediante la mediana del espaciado 3D de los nodos adyacentes en la superficie de referencia.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="119"/>
        <source>Green-Lagrange (default)</source>
        <translation>Green-Lagrange (predeterminado)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="120"/>
        <source>Infinitesimal</source>
        <translation>Infinitesimal</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="124"/>
        <source>Almansi (Eulerian, true tensor)</source>
        <translation>Almansi (euleriano, tensor exacto)</translation>
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
        <translation>Medida de deformación finita derivada del MISMO ajuste del gradiente
de desplazamiento, en el mismo sistema tangente:
Green-Lagrange E = ½(FᵀF − I) — deformación finita, configuración de
referencia (predeterminado).
Infinitesimal e = ½(∇u + ∇uᵀ) — linealización de pequeñas deformaciones.
Almansi (euleriano, tensor exacto) e = ½(I − F⁻ᵀF⁻¹) — el tensor de
deformación finita EXACTO en la configuración deformada. NO es la
fórmula «Euler-Almansi» linealizada por eje de la app 2D
(1/(1−∂u/∂x)−1, …), que difiere ~22 % con 10 % de deformación.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="139"/>
        <source>Strain type</source>
        <translation>Tipo de deformación</translation>
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
        <translation>Oculta la deformación poco fiable cerca de nodos inválidos o ausentes,
donde la ventana de deformación pierde apoyo por un lado y el ajuste
de plano local deja de ser fiable.
Coeficiente × radio de ventana = anchura de la banda recortada (en px,
sobre la malla de referencia).
0,00 = conservar todos los nodos (sin recorte) · 0,70 = recomendado ·
1,00 = el más estricto. El desplazamiento nunca se ve afectado.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="161"/>
        <source>Trim low-confidence edges</source>
        <translation>Recortar bordes de baja confianza</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="188"/>
        <source>Off</source>
        <translation>Desactivado</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="189"/>
        <source>Light (σ = 0.5 × step)</source>
        <translation>Ligero (σ = 0,5 × step)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="190"/>
        <source>Medium (σ = 1 × step)</source>
        <translation>Medio (σ = 1 × step)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="191"/>
        <source>Strong (σ = 2 × step) ⚠</source>
        <translation>Fuerte (σ = 2 × step) ⚠</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="197"/>
        <source>Gaussian smoothing of the displacement field before the gradient fit.
σ is the kernel width; step = DIC node spacing.
  Light  (0.5 × step): subtle, preserves fine features.
  Medium (1 × step): balanced, for noisy data.
  Strong (2 × step) ⚠: aggressive, may blur real gradients.</source>
        <translation>Suavizado gaussiano del campo de desplazamiento antes del ajuste del gradiente.
σ es el ancho del núcleo; step = espaciado de nodos DIC.
  Ligero (0,5 × step): sutil, preserva detalles finos.
  Medio (1 × step): equilibrado, para datos ruidosos.
  Fuerte (2 × step) ⚠: agresivo, puede difuminar gradientes reales.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="204"/>
        <source>Strain field smoothing</source>
        <translation>Suavizado del campo de deformación</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="208"/>
        <source>Surface tangent plane</source>
        <translation>Plano tangente a la superficie</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="209"/>
        <source>Left camera frame</source>
        <translation>Sistema de la cámara izquierda</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="210"/>
        <source>Custom (3 points)</source>
        <translation>Personalizado (3 puntos)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="213"/>
        <source>Per-node tangent plane fitted to the reference surface: z is the surface normal pointing toward the camera, x is the left-camera +X projected onto the plane, y = z × x. The right default for curved specimens.</source>
        <translation>Plano tangente ajustado nodo a nodo a la superficie de referencia: z es la normal de la superficie orientada hacia la cámara, x la proyección del +X de la cámara izquierda sobre el plano, y = z × x. El valor predeterminado adecuado para probetas curvas.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="219"/>
        <source>Report strain in the fixed left-camera (world) axes. Meaningful for flat specimens aligned with the image plane.</source>
        <translation>Expresar la deformación en los ejes fijos de la cámara izquierda (mundo). Adecuado para probetas planas alineadas con el plano de imagen.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="223"/>
        <source>A fixed specimen frame built from 3 picked points on the reference image: Origin, a point along +X, and a point on the +Y side.</source>
        <translation>Un sistema de referencia fijo de la probeta construido a partir de 3 puntos elegidos en la imagen de referencia: el origen, un punto a lo largo de +X y un punto del lado +Y.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="241"/>
        <source>Coordinate system</source>
        <translation>Sistema de coordenadas</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="246"/>
        <source>Pick 3 points…</source>
        <translation>Elegir 3 puntos…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="251"/>
        <source>Click three points on the reference image: the Origin, a point along +X, then a point on the +Y side. Each click snaps to the nearest valid mesh node. Enabled only for Custom (3 points).</source>
        <translation>Haga clic en tres puntos de la imagen de referencia: el origen, un punto a lo largo de +X y un punto del lado +Y. Cada clic se ajusta al nodo de malla válido más cercano. Solo activo en «Personalizado (3 puntos)».</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="307"/>
        <source>Trimmed: {0} nodes ({1}%)</source>
        <translation>Recortados: {0} nodos ({1}%)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="315"/>
        <source>Crack-aware: ROI barrier honored (mesh, strain, render)</source>
        <translation>Consciente de fisuras: barrera ROI respetada (malla, deformación, renderizado)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="405"/>
        <source>Strain window ≈ {0}×{1} nodes</source>
        <translation>Ventana VSG ≈ {0}×{1} nodos</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="409"/>
        <source>≈ {0} × {1} mm</source>
        <translation>≈ {0} × {1} mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="419"/>
        <source>⚠ Window radius ({0} px) &lt; node spacing ({1} px); the plane fit needs a 3×3 node gauge. Use ≥ {2} px.</source>
        <translation>⚠ Radio de ventana ({0} px) &lt; espaciado de nodos ({1} px); el ajuste de plano requiere una galga de 3×3 nodos. Use ≥ {2} px.</translation>
    </message>
</context>
<context>
    <name>StrainRenderMixin</name>
    <message>
        <location filename="../../gui/strain_canvas.py" line="230"/>
        <source>Could not draw the overlay: {0}</source>
        <translation>No se pudo dibujar la superposición: {0}</translation>
    </message>
</context>
<context>
    <name>StrainVizPanel3D</name>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="35"/>
        <source>Show on deformed frame</source>
        <translation>Mostrar en fotograma deformado</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="39"/>
        <source>When checked, overlay results on the deformed (current) frame instead of the reference frame</source>
        <translation>Si está activado, los resultados se superponen sobre el fotograma deformado (actual) en lugar del fotograma de referencia</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="49"/>
        <source>Colormap for the strain overlay. Default turbo; pick RdBu_r or coolwarm for signed strain centered on zero.</source>
        <translation>Mapa de color para la superposición de deformación. Por defecto turbo; elija RdBu_r o coolwarm para deformaciones con signo centradas en cero.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="53"/>
        <source>Colormap</source>
        <translation>Mapa de colores</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="55"/>
        <source>Auto range</source>
        <translation>Rango automático</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="59"/>
        <source>Rescale the color range to each frame&apos;s data range (2–98 percentile of the visible values). Default on; uncheck to type fixed Min/Max bounds that hold across frames.</source>
        <translation>Ajustar el rango de colores al rango de datos de cada fotograma (percentiles 2–98 de los valores visibles). Activado por defecto; desmarque para escribir límites Mín/Máx fijos que se mantienen en todos los fotogramas.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="74"/>
        <source>Lower color-range bound (only with Auto range off)</source>
        <translation>Límite inferior del rango de color (solo con el rango automático desactivado)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="75"/>
        <source>Upper color-range bound (only with Auto range off)</source>
        <translation>Límite superior del rango de color (solo con el rango automático desactivado)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="82"/>
        <source>Min</source>
        <translation>Mín</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="84"/>
        <source>Max</source>
        <translation>Máx</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="93"/>
        <source>Overlay opacity (0 = transparent, 100 = opaque)</source>
        <translation>Opacidad de la superposición (0 = transparente, 100 = opaco)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="94"/>
        <source>Opacity</source>
        <translation>Opacidad</translation>
    </message>
</context>
<context>
    <name>StrainWindow3D</name>
    <message>
        <location filename="../../gui/strain_window.py" line="111"/>
        <source>Strain Post-Processing</source>
        <translation>Post-procesado de deformación</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="151"/>
        <source>STRAIN PARAMETERS</source>
        <translation>PARÁMETROS DE DEFORMACIÓN</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="161"/>
        <source>Compute Strain</source>
        <translation>Calcular deformación</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="167"/>
        <source>Export Results</source>
        <translation>Exportar resultados</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="171"/>
        <location filename="../../gui/strain_window.py" line="680"/>
        <source>Export displacement and strain results to NPZ / MAT / CSV</source>
        <translation>Exportar resultados de desplazamiento y deformación a NPZ / MAT / CSV</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="190"/>
        <source>Cancel</source>
        <translation>Cancelar</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="192"/>
        <source>Stop the strain computation at the next frame.</source>
        <translation>Detener el cálculo de deformación en el siguiente fotograma.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="201"/>
        <source>FIELD</source>
        <translation>CAMPO</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="207"/>
        <source>VISUALIZATION</source>
        <translation>VISUALIZACIÓN</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="211"/>
        <source>LOG</source>
        <translation>REGISTRO</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="334"/>
        <source>Computation Running</source>
        <translation>Cálculo en ejecución</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="335"/>
        <source>A strain computation is running — cancel it and close?</source>
        <translation>Hay un cálculo de deformación en ejecución — ¿cancelarlo y cerrar?</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="340"/>
        <source>Yes</source>
        <translation>Sí</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="341"/>
        <source>No</source>
        <translation>No</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="401"/>
        <location filename="../../gui/strain_window.py" line="466"/>
        <location filename="../../gui/strain_window.py" line="580"/>
        <source>Strain compute failed: {0}</source>
        <translation>Fallo en el cálculo de deformación: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="413"/>
        <location filename="../../gui/strain_window.py" line="543"/>
        <source>Run 3D analysis first — no results to post-process.</source>
        <translation>Ejecute primero el análisis 3D — no hay resultados para posprocesar.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="416"/>
        <location filename="../../gui/strain_window.py" line="554"/>
        <location filename="../../gui/strain_window.py" line="582"/>
        <source>Click Origin, then +X, then +Y on the image</source>
        <translation>Haga clic en el origen, luego +X, luego +Y en la imagen</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="423"/>
        <source>Computing strain…</source>
        <translation>Calculando deformación…</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="440"/>
        <source>Cancelling…</source>
        <translation>Cancelando…</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="445"/>
        <source>Computing strain… {0}%</source>
        <translation>Calculando deformación… {0}%</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="457"/>
        <source>Complete</source>
        <translation>Completado</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="471"/>
        <source>Strain computation cancelled.</source>
        <translation>Cálculo de deformación cancelado.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="476"/>
        <source>Strain computation complete.</source>
        <translation>Cálculo de deformación completado.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="481"/>
        <source>⚠ Params changed -- click Compute Strain</source>
        <translation>⚠ Parámetros modificados — haga clic en «Calcular deformación»</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="565"/>
        <source>No valid point near the click — pick on the result field</source>
        <translation>No hay un punto válido cerca del clic — elija sobre el campo de resultados</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="573"/>
        <location filename="../../gui/strain_window.py" line="590"/>
        <source>Picked {0}/3 points</source>
        <translation>{0}/3 puntos elegidos</translation>
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
        <translation>Ejecute primero un análisis 3D — la deformación necesita resultados de desplazamiento.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="669"/>
        <source>Pick the 3 specimen-frame points first (Origin, +X, +Y).</source>
        <translation>Elija primero los 3 puntos del sistema de la probeta (origen, +X, +Y).</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="674"/>
        <source>Compute Green-Lagrange surface strain from the displacement field with the parameters above.</source>
        <translation>Calcular la deformación superficial de Green-Lagrange a partir del campo de desplazamiento con los parámetros anteriores.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="684"/>
        <source>Run an analysis first — there are no results yet.</source>
        <translation>Ejecute primero un análisis — todavía no hay resultados.</translation>
    </message>
</context>
<context>
    <name>UnitsSection3D</name>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="37"/>
        <source>Display unit for displacement and velocity values (colorbar,
3D scalar bar). Display only — the data and every export stay
in millimetres. Strain is dimensionless and unaffected.</source>
        <translation>Unidad de visualización de los valores de desplazamiento y velocidad
(barra de color, barra escalar 3D). Solo visualización — los datos y
todas las exportaciones permanecen en milímetros. La deformación es
adimensional y no se ve afectada.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="42"/>
        <source>Display unit</source>
        <translation>Unidad de visualización</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="49"/>
        <source>not set (per frame)</source>
        <translation>sin definir (por fotograma)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="54"/>
        <source>Acquisition frame rate. Used only by the Velocity field:
velocity = |D(k) − D(k−1)| × frame rate, shown in the
display unit per second. Leave it at &apos;not set&apos; to see the
velocity per frame.</source>
        <translation>Velocidad de adquisición. Solo la usa el campo Velocidad:
velocidad = |D(k) − D(k−1)| × velocidad de fotogramas, en la
unidad de visualización por segundo. Déjela en «sin definir» para ver la
velocidad por fotograma.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="60"/>
        <source>Frame rate</source>
        <translation>Velocidad de fotogramas</translation>
    </message>
</context>
<context>
    <name>View3D</name>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="129"/>
        <source>3D view — run an analysis to see the reconstructed surface.</source>
        <translation>Vista 3D — ejecute un análisis para ver la superficie reconstruida.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="170"/>
        <location filename="../../gui/widgets/view3d.py" line="259"/>
        <source>3D view unavailable: {0}</source>
        <translation>Vista 3D no disponible: {0}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="232"/>
        <source>Starting the 3D view…</source>
        <translation>Iniciando la vista 3D…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="264"/>
        <source>No valid 3D points in this frame — nothing to display.</source>
        <translation>No hay puntos 3D válidos en este fotograma — nada que mostrar.</translation>
    </message>
</context>
<context>
    <name>View3DTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="72"/>
        <source>Field</source>
        <translation>Campo</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="84"/>
        <source>Colormap</source>
        <translation>Mapa de colores</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="93"/>
        <source>Resolution</source>
        <translation>Resolución</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="106"/>
        <source>Auto range</source>
        <translation>Rango automático</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="109"/>
        <source>Like the 3D view: each frame&apos;s 2–98 percentile of the values inside the ROI. Untick to use a fixed Min/Max for every frame.</source>
        <translation>Como la vista 3D: en cada fotograma, los percentiles 2–98 de los valores dentro de la ROI. Desmarque para usar un Mín/Máx fijo en todos los fotogramas.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="116"/>
        <source>Min</source>
        <translation>Mín</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="122"/>
        <source>Max</source>
        <translation>Máx</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="135"/>
        <source>Frame sequence</source>
        <translation>Secuencia de fotogramas</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="138"/>
        <source>Per-frame image sequence (PNG)</source>
        <translation>Secuencia de imágenes por fotograma (PNG)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="143"/>
        <source>Animation</source>
        <translation>Animación</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="150"/>
        <source>Frames per second</source>
        <translation>Fotogramas por segundo</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="157"/>
        <source>Frame step</source>
        <translation>Paso de fotogramas</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="171"/>
        <source>Turntable</source>
        <translation>Rotación orbital</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="176"/>
        <source>Turntable (360° orbit at frame {0})</source>
        <translation>Rotación orbital (360° en el fotograma {0})</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="179"/>
        <source>Orbit frames</source>
        <translation>Fotogramas de órbita</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="204"/>
        <source>Export 3D View</source>
        <translation>Exportar vista 3D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="262"/>
        <source>GIF timing has 1/100 s steps: {0} fps will play at {1} fps. Choose MP4 for faster playback.</source>
        <translation>La temporización GIF tiene pasos de 1/100 s: {0} fps se reproducirán a {1} fps. Elija MP4 para una reproducción más rápida.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="275"/>
        <source>Choose an output folder first.</source>
        <translation>Elija primero una carpeta de salida.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="281"/>
        <source>Nothing selected to export.</source>
        <translation>No hay nada seleccionado para exportar.</translation>
    </message>
</context>
<context>
    <name>ZoomBar</name>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="60"/>
        <source>Fit</source>
        <translation>Ajustar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="61"/>
        <source>Fit image to viewport</source>
        <translation>Ajustar la imagen a la vista</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="68"/>
        <source>Current zoom — click to reset to 100% (1:1 pixels).
Wheel: zoom · Right/middle drag: pan · Space: pan mode</source>
        <translation>Zoom actual — haga clic para restablecer al 100 % (píxeles 1:1).
Rueda: zoom · Arrastre con botón derecho/central: desplazar · Espacio: modo desplazamiento</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="74"/>
        <source>Zoom in</source>
        <translation>Acercar</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="78"/>
        <source>Zoom out</source>
        <translation>Alejar</translation>
    </message>
</context>
<context>
    <name>dialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="24"/>
        <source>Close</source>
        <translation>Cerrar</translation>
    </message>
</context>
</TS>
