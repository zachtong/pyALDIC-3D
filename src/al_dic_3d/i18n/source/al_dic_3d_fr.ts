<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="sd_PK">
<context>
    <name>AboutDialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="36"/>
        <source>About pyALDIC-3D</source>
        <translation>À propos de pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="47"/>
        <source>Version {0}</source>
        <translation>Version {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="52"/>
        <source>Stereo (3D) digital image correlation — full-field displacement and surface strain from a calibrated camera pair.</source>
        <translation>Corrélation d'images numériques stéréo (3D) — déplacements plein champ et déformations de surface à partir d'une paire de caméras étalonnée.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="63"/>
        <source>Citation: Zenodo DOI pending release.</source>
        <translation>Citation : DOI Zenodo en attente de publication.</translation>
    </message>
</context>
<context>
    <name>AdvancedSection3D</name>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="38"/>
        <source>Track Both</source>
        <translation>Suivre les deux caméras</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="39"/>
        <source>Stereo Each Frame</source>
        <translation>Stéréo à chaque image</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="40"/>
        <source>Reference Direct</source>
        <translation>Référence directe</translation>
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
        <translation>Comment les correspondances stéréo se propagent dans le temps.
Suivre les deux caméras (défaut) : appariement stéréo une seule fois à l'image 1, puis suivi temporel dans chaque caméra — le plus rapide, une seule résolution stéréo.
Stéréo à chaque image : ré-appariement stéréo à chaque image — robuste quand le suivi temporel dérive, plus lent.
Référence directe : chaque image appariée directement à l'image 1 dans les deux caméras — pas d'accumulation de dérive, petits mouvements uniquement.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="52"/>
        <source>Strategy</source>
        <translation>Stratégie</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="59"/>
        <source>1 = single global pass (fastest), 3 = default, 5+ = diminishing returns</source>
        <translation>1 = passe unique (le plus rapide), 3 = par défaut, 5+ = rendement décroissant</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="61"/>
        <source>AL-DIC Iterations</source>
        <translation>Itérations AL-DIC</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="63"/>
        <source>Only affects AL-DIC solver. Ignored by Local DIC.</source>
        <translation>N'affecte que le solveur AL-DIC. Ignoré par Local DIC.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="69"/>
        <source>Parallel camera tracking</source>
        <translation>Suivi des caméras en parallèle</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="72"/>
        <source>Track both cameras concurrently — modest speedup (the solver already uses all cores), doubles peak memory</source>
        <translation>Suivre les deux caméras en parallèle — gain limité (le solveur utilise déjà tous les cœurs), mémoire de pointe doublée</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="79"/>
        <source>Auto-expand FFT search on clipped peaks</source>
        <translation>Étendre automatiquement la recherche FFT sur pics tronqués</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="83"/>
        <source>When the temporal FFT integer peak lands on the search-region
boundary, retry with a larger region (engine default on).
Disable for strictly bounded runtimes; then Temporal Search
must cover the largest per-frame motion by itself.</source>
        <translation>Si le pic entier de la FFT temporelle tombe sur la limite de la zone
de recherche, réessaie avec une zone plus grande (activé par défaut).
Désactivez pour des temps d'exécution strictement bornés ; la
recherche temporelle doit alors couvrir seule le plus grand mouvement
par image.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="92"/>
        <source>Result checks</source>
        <translation>Contrôles des résultats</translation>
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
        <translation>Contrôle du suivi : chaque point suivi doit encore ressembler à
sa fenêtre de l'image 1 (écart de corrélation, 0 = parfait, 4 = pire).
Les points sous 60 % de cette valeur passent toujours ; ceux jusqu'à
elle passent si leurs voisins concordent ; les autres sont écartés
comme suivis échoués. Par défaut 1,0 (corrélation 0,5). Augmentez-la
(p. ex. 1,5) pour de très grandes déformations, baissez-la pour des
résultats plus stricts ; 0 désactive le contrôle.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="109"/>
        <source>Tracking check</source>
        <translation>Contrôle du suivi</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="114"/>
        <source>Stereo check: a left/right match is kept only if its
correlation mismatch is at most this value. Default 0.6
(correlation 0.7); 0 turns the check off.</source>
        <translation>Contrôle stéréo : un appariement gauche/droite n'est gardé que si
son écart de corrélation ne dépasse pas cette valeur. Par défaut 0,6
(corrélation 0,7) ; 0 désactive le contrôle.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="119"/>
        <source>Stereo check</source>
        <translation>Contrôle stéréo</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="124"/>
        <source>Epipolar limit: a left/right match must lie within this many
pixels of the line the calibration predicts. Default 2 px;
raise it only for a poor calibration; 0 turns the check off.</source>
        <translation>Limite épipolaire : un appariement gauche/droite doit se trouver à moins
de ce nombre de pixels de la droite prévue par l'étalonnage. Par défaut 2 px ;
augmentez-la seulement pour un étalonnage médiocre ; 0 désactive le contrôle.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="130"/>
        <source>Epipolar limit</source>
        <translation>Limite épipolaire</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/advanced_section.py" line="140"/>
        <source>off</source>
        <translation>désactivé</translation>
    </message>
</context>
<context>
    <name>AnimationTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="57"/>
        <source>Fields</source>
        <translation>Champs</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="77"/>
        <source>Format</source>
        <translation>Format</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="84"/>
        <source>Frames per second</source>
        <translation>Images par seconde</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="91"/>
        <source>Frame step</source>
        <translation>Pas d'image</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="92"/>
        <source>Keep every Nth frame (1 = all)</source>
        <translation>Conserver une image sur N (1 = toutes)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="99"/>
        <source>Resolution (long edge)</source>
        <translation>Résolution (bord long)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="119"/>
        <source>Include colorbar</source>
        <translation>Inclure la barre de couleur</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="124"/>
        <source>Background</source>
        <translation>Arrière-plan</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="138"/>
        <source>Export Animation</source>
        <translation>Exporter l'animation</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="149"/>
        <source>Load an image sequence first (open the project in the main window).</source>
        <translation>Chargez d'abord une séquence d'images (ouvrez le projet dans la fenêtre principale).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="158"/>
        <source>GIF timing has 1/100 s steps: {0} fps will play at {1} fps. Choose MP4 for faster playback.</source>
        <translation>La temporisation GIF a des pas de 1/100 s : {0} fps seront lus à {1} fps. Choisissez MP4 pour une lecture plus rapide.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="178"/>
        <source>Choose an output folder first.</source>
        <translation>Choisissez d'abord un dossier de sortie.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/animation_tab.py" line="182"/>
        <source>No fields enabled.</source>
        <translation>Aucun champ activé.</translation>
    </message>
</context>
<context>
    <name>Application</name>
    <message>
        <location filename="../../gui/app.py" line="288"/>
        <source>pyALDIC-3D has hit an error</source>
        <translation>pyALDIC-3D a rencontré une erreur</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="289"/>
        <source>An unexpected error occurred. The application may not behave correctly from here on, so saving your project and restarting is recommended.</source>
        <translation>Une erreur inattendue s'est produite. L'application risque de ne plus fonctionner correctement ; il est recommandé d'enregistrer votre projet et de redémarrer.</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="299"/>
        <source>Details were written to {0}</source>
        <translation>Les détails ont été enregistrés dans {0}</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="348"/>
        <source>Preparing compute kernels in the background…</source>
        <translation>Préparation des noyaux de calcul en arrière-plan…</translation>
    </message>
    <message>
        <location filename="../../gui/app.py" line="361"/>
        <source>Compute kernels ready ({0} s).</source>
        <translation>Noyaux de calcul prêts ({0} s).</translation>
    </message>
</context>
<context>
    <name>BackgroundRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="638"/>
        <source>Original (frame 1 background)</source>
        <translation>Original (image 1 en arrière-plan)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="639"/>
        <source>Deformed (current frame background)</source>
        <translation>Déformé (image actuelle en arrière-plan)</translation>
    </message>
</context>
<context>
    <name>CalibrationDialog</name>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="92"/>
        <source>Stereo Calibration</source>
        <translation>Étalonnage stéréo</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="131"/>
        <source>CALIBRATION IMAGE PAIRS</source>
        <translation>PAIRES D'IMAGES D'ÉTALONNAGE</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="134"/>
        <source>Add left images…</source>
        <translation>Ajouter des images gauches…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="136"/>
        <source>Add right images…</source>
        <translation>Ajouter des images droites…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="138"/>
        <source>Clear</source>
        <translation>Effacer</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="140"/>
        <source>Save detections…</source>
        <translation>Enregistrer les détections…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="143"/>
        <source>Load detections…</source>
        <translation>Charger les détections…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="150"/>
        <source>No images loaded</source>
        <translation>Aucune image chargée</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="158"/>
        <source>Left</source>
        <translation>Gauche</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="159"/>
        <source>Right</source>
        <translation>Droite</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="160"/>
        <source>Points</source>
        <translation>Points</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="161"/>
        <source>RMS L/R</source>
        <translation>RMS G/D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="162"/>
        <source>Max E</source>
        <translation>Erreur max</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="163"/>
        <source>Status</source>
        <translation>Statut</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="174"/>
        <source>SELECTED PAIR (L | R)</source>
        <translation>PAIRE SÉLECTIONNÉE (G | D)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="175"/>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="408"/>
        <source>select a pair to preview detected points</source>
        <translation>sélectionnez une paire pour prévisualiser les points détectés</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="182"/>
        <source>Click to enlarge the annotated detection</source>
        <translation>Cliquer pour agrandir la détection annotée</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="186"/>
        <source>PER-PAIR REPROJECTION ERROR</source>
        <translation>ERREUR DE REPROJECTION PAR PAIRE</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="191"/>
        <source>Reject threshold (px)</source>
        <translation>Seuil de rejet (px)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="200"/>
        <source>Recalibrate</source>
        <translation>Réétalonner</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="212"/>
        <source>CALIBRATION BOARD</source>
        <translation>MIRE D'ÉTALONNAGE</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="220"/>
        <source>Chessboard</source>
        <translation>Damier</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="221"/>
        <source>ChArUco</source>
        <translation>ChArUco</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="222"/>
        <source>Circle grid</source>
        <translation>Grille de points</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="223"/>
        <source>Coded dot target (3 ring markers)</source>
        <translation>Cible à points codée (3 marqueurs annulaires)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="225"/>
        <source>Type</source>
        <translation>Type</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="230"/>
        <source>Columns x Rows</source>
        <translation>Colonnes × Lignes</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="237"/>
        <source>Square size (mm)</source>
        <translation>Taille de case (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="242"/>
        <source>Marker size (mm)</source>
        <translation>Taille de marqueur (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="247"/>
        <source>Dot pitch (mm)</source>
        <translation>Pas des points (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="252"/>
        <source>Dot diameter (mm)</source>
        <translation>Diamètre des points (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="256"/>
        <source>Asymmetric grid</source>
        <translation>Grille asymétrique</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="258"/>
        <source>Board printed with OpenCV &lt; 4.7</source>
        <translation>Mire imprimée avec OpenCV &lt; 4.7</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="262"/>
        <source>Print board… (1:1 PDF)</source>
        <translation>Imprimer la mire… (PDF 1:1)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="266"/>
        <source>SOLVER OPTIONS</source>
        <translation>OPTIONS DU SOLVEUR</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="267"/>
        <source>Jointly refine intrinsics (advanced)</source>
        <translation>Raffiner conjointement les intrinsèques (avancé)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="268"/>
        <source>Estimate tangential distortion p1/p2</source>
        <translation>Estimer la distorsion tangentielle p1/p2</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="269"/>
        <source>Fix k3 = 0 (low-distortion lens)</source>
        <translation>Fixer k3 = 0 (objectif à faible distorsion)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="270"/>
        <source>Release-object method (printed boards)</source>
        <translation>Méthode release-object (mires imprimées)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="271"/>
        <source>Dot eccentricity correction</source>
        <translation>Correction d'excentricité des points</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="273"/>
        <source>Joint bundle adjustment (robust, uses mono views)</source>
        <translation>Ajustement de faisceaux (robuste, exploite les vues mono)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="274"/>
        <source>Optimize board shape (printed boards)</source>
        <translation>Optimiser la forme de la mire (mires imprimées)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="289"/>
        <source>Calibrate</source>
        <translation>Étalonner</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="300"/>
        <source>RESULT</source>
        <translation>RÉSULTAT</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="301"/>
        <source>No calibration yet</source>
        <translation>Pas encore d'étalonnage</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="306"/>
        <source>Verify with board images…</source>
        <translation>Vérifier avec des images de mire…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="318"/>
        <source>Accept &amp;&amp; Save…</source>
        <translation>Accepter &amp;&amp; Enregistrer…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="324"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="383"/>
        <source>Choose {0} calibration images</source>
        <translation>Choisir les images d'étalonnage {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="385"/>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="717"/>
        <source>Images (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)</source>
        <translation>Images (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="430"/>
        <source>{0} left / {1} right images</source>
        <translation>{0} images gauches / {1} droites</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="440"/>
        <source>Load equal, &gt;= 3 left/right image sets first.</source>
        <translation>Chargez d'abord des jeux gauche/droite égaux (au moins 3).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="471"/>
        <source>Working… {0}</source>
        <translation>Traitement… {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="480"/>
        <source>Calibration failed: {0}</source>
        <translation>Échec de l'étalonnage : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="505"/>
        <source>used</source>
        <translation>utilisée</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="507"/>
        <source>L: {0}</source>
        <translation>G : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="509"/>
        <source>R: {0}</source>
        <translation>D : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="525"/>
        <source>Stereo RMS {0:.3f} px | epipolar {1:.3f} px</source>
        <translation>RMS stéréo {0:.3f} px | épipolaire {1:.3f} px</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="528"/>
        <source>Baseline {0:.2f} mm | pairs {1}/{2}</source>
        <translation>Ligne de base {0:.2f} mm | paires {1}/{2}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="531"/>
        <source>fx {0:.1f}  fy {1:.1f}  cx {2:.1f}  cy {3:.1f}</source>
        <translation>fx {0:.1f}  fy {1:.1f}  cx {2:.1f}  cy {3:.1f}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="534"/>
        <source>Coverage L {0:.0%} / R {1:.0%} | tilt {2:.0f}-{3:.0f}°</source>
        <translation>Couverture G {0:.0%} / D {1:.0%} | inclinaison {2:.0f}-{3:.0f}°</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="543"/>
        <source>Bundle adjustment: RMS {0:.3f} -&gt; {1:.3f} px ({2:.0f} mono views)</source>
        <translation>Ajustement de faisceaux : RMS {0:.3f} -&gt; {1:.3f} px ({2:.0f} vues mono)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="549"/>
        <source>Board flatness: z-range {0:.3f} mm</source>
        <translation>Planéité de la mire : plage z {0:.3f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="552"/>
        <source>Warning: {0}</source>
        <translation>Avertissement : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="690"/>
        <source>Save board PDF</source>
        <translation>Enregistrer le PDF de la mire</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="692"/>
        <source>PDF (*.pdf)</source>
        <translation>PDF (*.pdf)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="703"/>
        <source>Board PDF written: {0}</source>
        <translation>PDF de la mire écrit : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="719"/>
        <source>Choose LEFT verification image</source>
        <translation>Choisir l'image de vérification GAUCHE</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="724"/>
        <source>Choose RIGHT verification image</source>
        <translation>Choisir l'image de vérification DROITE</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="733"/>
        <source>Verification failed: {0}</source>
        <translation>Échec de la vérification : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="739"/>
        <source>Verify: pitch {0:.4f} mm vs {1:g} mm — scale error {2:.3%}, plane RMS {3:.4f} mm</source>
        <translation>Vérification : pas {0:.4f} mm contre {1:g} mm — erreur d'échelle {2:.3%}, RMS plan {3:.4f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_dialog.py" line="753"/>
        <source>Save calibration as</source>
        <translation>Enregistrer l'étalonnage sous</translation>
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
        <translation>Caméra {0} : la mire n'a atteint que {1:.0%} du rayon des coins de l'image. Au-delà, le modèle d'objectif est une supposition : deux ajustements aussi bons y diffèrent jusqu'à {2:.2f} px. Ajoutez des vues avec la mire près des coins de l'image, gardez la région d'intérêt dans la zone couverte ou, pour un objectif à faible distorsion, fixez k3.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="57"/>
        <source>Camera {0}: the board reached {1:.0%} of the image-corner radius; the lens model is fitted only inside that radius.</source>
        <translation>Caméra {0} : la mire a atteint {1:.0%} du rayon des coins de l'image ; le modèle d'objectif n'est ajusté qu'à l'intérieur de ce rayon.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="40"/>
        <source>Camera {0}: the board reached {1:.0%} of the image-corner radius. Beyond it the lens model is a guess: two equally good fits differ by up to {2:.2f} px there. With k3 fixed, the corners are right only if the lens has no k3 distortion: add views with the board near the image corners, or keep the region of interest inside the covered area.</source>
        <translation>Caméra {0} : la mire n'a atteint que {1:.0%} du rayon des coins de l'image. Au-delà, le modèle d'objectif est une supposition : deux ajustements aussi bons y diffèrent jusqu'à {2:.2f} px. Avec k3 fixé, les coins ne sont justes que si l'objectif n'a pas de distorsion k3 : ajoutez des vues avec la mire près des coins de l'image ou gardez la région d'intérêt dans la zone couverte.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="63"/>
        <source>Camera {0}: the residuals follow a pattern the lens model does not explain (binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model fits), although the board shape is already optimised. A lens the model cannot describe, a board that bends differently from view to view, or detector bias can cause this.</source>
        <translation>Caméra {0} : les résidus suivent un motif que le modèle d'objectif n'explique pas (excès par cellule {1:.1f}, champ ajusté {2:.1f} × bruit ; environ 1 quand le modèle convient), bien que la forme de la mire soit déjà optimisée. Un objectif que le modèle ne sait pas décrire, une mire qui se courbe différemment d'une vue à l'autre ou un biais du détecteur peuvent en être la cause.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="72"/>
        <source>Camera {0}: the residuals follow a pattern the lens model does not explain (binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model fits). Often the board is the cause (not flat, or its points not exactly where the board description puts them): tick Joint bundle adjustment and Optimize board shape. A lens the model cannot describe or detector bias can also cause this.</source>
        <translation>Caméra {0} : les résidus suivent un motif que le modèle d'objectif n'explique pas (excès par cellule {1:.1f}, champ ajusté {2:.1f} × bruit ; environ 1 quand le modèle convient). Souvent la mire en est la cause (pas plane, ou ses points pas exactement là où sa description les place) : cochez « Ajustement de faisceaux » et « Optimiser la forme de la mire ». Un objectif que le modèle ne sait pas décrire ou un biais du détecteur peuvent aussi en être la cause.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="82"/>
        <source>Camera {0}: the extrapolation check was skipped (too few usable views).</source>
        <translation>Caméra {0} : la vérification d'extrapolation a été ignorée (trop peu de vues utilisables).</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="88"/>
        <source>Camera {0}: the lens-model check was skipped: the points fill only {1} image cells.</source>
        <translation>Caméra {0} : la vérification du modèle d'objectif a été ignorée : les points ne remplissent que {1} cellules de l'image.</translation>
    </message>
    <message>
        <location filename="../../gui/calibration_findings.py" line="103"/>
        <source>Warning: {0}</source>
        <translation>Avertissement : {0}</translation>
    </message>
</context>
<context>
    <name>CalibrationSection3D</name>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="50"/>
        <source>Calibrate from images…</source>
        <translation>Étalonner depuis des images…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="54"/>
        <source>Run the built-in stereo calibrator on your target photos
(checkerboard / ChArUco / dot grid). Writes an opencv_yaml
file and loads it — the recommended path when you have
calibration images.</source>
        <translation>Exécute l'étalonneur stéréo intégré sur vos photos de mire (damier / ChArUco / grille de points).
Écrit un fichier opencv_yaml et le charge — la voie recommandée quand vous avez des images d'étalonnage.</translation>
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
        <translation>Format du fichier d'étalonnage à importer. Par défaut opencv_yaml
(écrit par l'étalonneur intégré). Choisissez le format correspondant à votre source :
dice (DICe XML), matchid (MatchID .caldat), opencorr (OpenCorr CSV),
mmc (MultiDIC/MMC .mat), matlabcv (MATLAB stereoParams .mat).</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="85"/>
        <source>Import calibration…</source>
        <translation>Importer l'étalonnage…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="88"/>
        <source>Load an existing stereo calibration file in the selected
Format. The status line below shows fx / fy and the baseline
as a sanity check.</source>
        <translation>Charger un fichier d'étalonnage stéréo existant au format sélectionné.
La ligne d'état ci-dessous affiche fx / fy et la ligne de base comme contrôle de cohérence.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="96"/>
        <source>Manual parameters…</source>
        <translation>Paramètres manuels…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="99"/>
        <source>Type intrinsics and extrinsics by hand (fx, fy, cx, cy,
distortion, R, T) — the fallback when no calibration file
exists. Writes an opencv_yaml file and loads it.</source>
        <translation>Saisir les paramètres intrinsèques et extrinsèques à la main (fx, fy, cx, cy, distorsion, R, T)
— la solution de repli sans fichier d'étalonnage. Écrit un fichier opencv_yaml et le charge.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="107"/>
        <source>No calibration loaded</source>
        <translation>Aucun étalonnage chargé</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="151"/>
        <source>Choose calibration file</source>
        <translation>Choisir le fichier d'étalonnage</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="153"/>
        <source>Calibration files (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)</source>
        <translation>Fichiers d'étalonnage (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="171"/>
        <source>Error: {0}</source>
        <translation>Erreur : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="179"/>
        <source>{0}
fx {1:.0f}  fy {2:.0f}  |  baseline {3:.1f} mm</source>
        <translation>{0}
fx {1:.0f}  fy {2:.0f}  |  base {3:.1f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/calibration_section.py" line="185"/>
        <source>calibration loaded: baseline {0:.1f} mm</source>
        <translation>étalonnage chargé : base {0:.1f} mm</translation>
    </message>
</context>
<context>
    <name>CameraDropZone</name>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="76"/>
        <source>{0} frames</source>
        <translation>{0} images</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="103"/>
        <source>Click to pick this camera&apos;s image folder, or drag the folder here. Both cameras need the same number of frames.</source>
        <translation>Cliquez pour choisir le dossier d'images de cette caméra, ou faites-y glisser le dossier. Les deux caméras doivent avoir le même nombre d'images.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/camera_drop_zone.py" line="114"/>
        <source>Select image folder</source>
        <translation>Sélectionner le dossier d'images</translation>
    </message>
</context>
<context>
    <name>CameraRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="606"/>
        <source>Camera</source>
        <translation>Caméra</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="610"/>
        <source>Left</source>
        <translation>Gauche</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="611"/>
        <source>Right</source>
        <translation>Droite</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="612"/>
        <source>Left + Right</source>
        <translation>Gauche + Droite</translation>
    </message>
</context>
<context>
    <name>CanvasArea3D</name>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="92"/>
        <source>Fit</source>
        <translation>Ajuster</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="95"/>
        <source>Fit the image to the viewport (Ctrl+0)</source>
        <translation>Ajuster l'image à la vue (Ctrl+0)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="102"/>
        <source>Current zoom — click to reset to 100% (1:1 pixels).
Wheel: zoom · Right/middle drag: pan · Space: pan mode</source>
        <translation>Zoom actuel — cliquez pour revenir à 100 % (pixels 1:1).
Molette : zoom · Glisser droit/central : déplacement · Espace : mode déplacement</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="109"/>
        <source>Zoom in (Ctrl+=)</source>
        <translation>Zoom avant (Ctrl+=)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="113"/>
        <source>Zoom out (Ctrl+-)</source>
        <translation>Zoom arrière (Ctrl+-)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="118"/>
        <source>Show Grid</source>
        <translation>Afficher la grille</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="121"/>
        <source>Show the computational mesh preview on the reference view
(left camera, frame 1). Rebuilt live from the current Subset
Step / refinement settings — what you see is the run&apos;s mesh.
Default on; turn off to declutter the canvas.</source>
        <translation>Affiche l'aperçu du maillage de calcul sur la vue de référence
(caméra gauche, image 1). Reconstruit en direct à partir du pas de subset
et des réglages de raffinement — le maillage affiché est celui de l'exécution.
Activé par défaut ; désactivez pour alléger le canevas.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="134"/>
        <source>Hovering a mesh node shows its correlation subset window
(the Subset Size box). Needs Show Grid. Use it to judge
whether the subset spans enough speckle texture.</source>
        <translation>Survoler un nœud du maillage affiche sa fenêtre de subset de corrélation
(la boîte Taille du subset). Nécessite « Afficher la grille ». Utile pour juger
si le subset couvre assez de texture de mouchetis.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="147"/>
        <source>Switch the canvas to the reconstructed 3D surface (colored by
the selected field, with the camera frusta). Uncheck to return
to the 2D image view. Requires results.</source>
        <translation>Bascule le canevas vers la surface 3D reconstruite (colorée selon le champ
sélectionné, avec les cônes des caméras). Décochez pour revenir à la vue image 2D.
Nécessite des résultats.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="131"/>
        <source>Show Subset</source>
        <translation>Afficher l'imagette</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="144"/>
        <source>3D View</source>
        <translation>Vue 3D</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="323"/>
        <source>Load images before importing an ROI mask</source>
        <translation>Chargez les images avant d'importer un masque ROI</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="328"/>
        <source>Could not import the mask: {0}</source>
        <translation>Impossible d'importer le masque : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="331"/>
        <source>ROI mask imported from {0}</source>
        <translation>Masque ROI importé depuis {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="336"/>
        <source>No ROI mask to save — draw one first</source>
        <translation>Aucun masque ROI à enregistrer — dessinez-en un d'abord</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="344"/>
        <source>Save Mask</source>
        <translation>Enregistrer le masque</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="344"/>
        <source>PNG image (*.png)</source>
        <translation>Image PNG (*.png)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="351"/>
        <source>Could not save the mask: {0}</source>
        <translation>Impossible d'enregistrer le masque : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="354"/>
        <source>ROI mask saved to {0}</source>
        <translation>Masque ROI enregistré dans {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_area.py" line="540"/>
        <source>Analysis produced no valid points — nothing to display. See the log.</source>
        <translation>L'analyse n'a produit aucun point valide — rien à afficher. Voir le journal.</translation>
    </message>
</context>
<context>
    <name>CanvasRenderMixin</name>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="67"/>
        <source>Could not map the ROI into the right camera: {0}</source>
        <translation>Impossible de reporter la ROI sur la caméra droite : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="204"/>
        <source>3D view — run an analysis to see the reconstructed surface.</source>
        <translation>Vue 3D — lancez une analyse pour voir la surface reconstruite.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="211"/>
        <source>Selected field is not available.</source>
        <translation>Le champ sélectionné n'est pas disponible.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_render.py" line="396"/>
        <source>Could not draw the overlay: {0}</source>
        <translation>Impossible de dessiner la superposition : {0}</translation>
    </message>
</context>
<context>
    <name>CanvasToolsMixin</name>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="55"/>
        <source>Starting points cleared</source>
        <translation>Points de départ effacés</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="81"/>
        <source>Starting points are placed on the LEFT camera, frame 1 — switch there to add a point</source>
        <translation>Les points de départ se placent sur la caméra GAUCHE, image 1 — basculez-y pour ajouter un point</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="92"/>
        <source>Starting point {0} placed at ({1}, {2})</source>
        <translation>Point de départ {0} placé en ({1}, {2})</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="112"/>
        <source>Starting point removed at ({0}, {1})</source>
        <translation>Point de départ en ({0}, {1}) supprimé</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="169"/>
        <source>Fit</source>
        <translation>Ajuster</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="171"/>
        <source>Zoom to 100%</source>
        <translation>Zoomer à 100 %</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="174"/>
        <source>Copy image to clipboard</source>
        <translation>Copier l'image dans le presse-papiers</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="177"/>
        <source>Clear ROI</source>
        <translation>Effacer la ROI</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="180"/>
        <source>Clear seed points</source>
        <translation>Effacer les points de départ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="190"/>
        <source>Canvas image copied to the clipboard</source>
        <translation>Image du canevas copiée dans le presse-papiers</translation>
    </message>
    <message>
        <location filename="../../gui/panels/canvas_tools.py" line="205"/>
        <source>1. Drop the left/right camera folders in the sidebar
2. Calibrate or import calibration
3. Draw the ROI and Run</source>
        <translation>1. Déposez les dossiers des caméras gauche/droite dans la barre latérale
2. Étalonnez ou importez un étalonnage
3. Dessinez la ROI et lancez</translation>
    </message>
</context>
<context>
    <name>ConfigOverlay3D</name>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="39"/>
        <source>Mode</source>
        <translation>Mode</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="40"/>
        <source>Solver</source>
        <translation>Solveur</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="41"/>
        <source>Init</source>
        <translation>Estimation initiale</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="42"/>
        <source>Subset</source>
        <translation>Imagette</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="79"/>
        <source>AL-DIC ({0} iter)</source>
        <translation>AL-DIC ({0} itér.)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="94"/>
        <source>FFT (no starting point)</source>
        <translation>FFT (aucun point de départ)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="81"/>
        <source>Local DIC</source>
        <translation>Local DIC</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="84"/>
        <source>Starting Point</source>
        <translation>Point de départ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="85"/>
        <source>Previous frame</source>
        <translation>Image précédente</translation>
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
        <translation>Cumulatif</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/config_overlay.py" line="75"/>
        <source>Incremental</source>
        <translation>Incrémental</translation>
    </message>
</context>
<context>
    <name>ConsoleLog3D</name>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="41"/>
        <source>Copy all</source>
        <translation>Tout copier</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="44"/>
        <source>Save log to file…</source>
        <translation>Enregistrer le journal dans un fichier…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/console_log3d.py" line="46"/>
        <source>Clear</source>
        <translation>Effacer</translation>
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
        <translation>Archive NumPy (.npz)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="54"/>
        <source>MATLAB (.mat)</source>
        <translation>MATLAB (.mat)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="56"/>
        <source>CSV (one file per frame)</source>
        <translation>CSV (un fichier par image)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="57"/>
        <source>PLY point clouds (per frame)</source>
        <translation>Nuages de points PLY (un par image)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="58"/>
        <source>VTU mesh series (ParaView)</source>
        <translation>Série de maillages VTU (ParaView)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="61"/>
        <source>✓ Parameters file (JSON) always exported</source>
        <translation>✓ Fichier de paramètres (JSON) toujours exporté</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="68"/>
        <source>Displacement</source>
        <translation>Déplacement</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="72"/>
        <source>Strain</source>
        <translation>Déformation</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="79"/>
        <source>3D points, reprojection error, and source flags are always exported.</source>
        <translation>Les points 3D, l'erreur de reprojection et les indicateurs de source sont toujours exportés.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="88"/>
        <source>Export Data</source>
        <translation>Exporter les données</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="105"/>
        <source>Select:</source>
        <translation>Sélection :</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="108"/>
        <source>All</source>
        <translation>Tout</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="109"/>
        <source>None</source>
        <translation>Aucun</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="158"/>
        <source>Choose an output folder first.</source>
        <translation>Choisissez d'abord un dossier de sortie.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="189"/>
        <source>Wrote: {0}</source>
        <translation>Écrit : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/data_tab.py" line="193"/>
        <source>Export cancelled — kept: {0}</source>
        <translation>Export annulé — conservé : {0}</translation>
    </message>
</context>
<context>
    <name>DetectionFilesMixin</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="215"/>
        <source>Save detections</source>
        <translation>Enregistrer les détections</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="217"/>
        <location filename="../../gui/dialogs/calibration_support.py" line="238"/>
        <source>NumPy detections (*.npz)</source>
        <translation>Détections NumPy (*.npz)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="231"/>
        <source>Detections saved: {0}</source>
        <translation>Détections enregistrées : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="236"/>
        <source>Load detections</source>
        <translation>Charger les détections</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="260"/>
        <source>Loaded {0} detection pairs — Recalibrate re-solves without re-detecting</source>
        <translation>{0} paires de détections chargées — Réétalonner résout sans redétection</translation>
    </message>
</context>
<context>
    <name>DetectionZoomDialog</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="274"/>
        <source>Detection preview — pair {0}</source>
        <translation>Aperçu de détection — paire {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="283"/>
        <source>Wheel: zoom · Right/middle drag: pan</source>
        <translation>Molette : zoom · Glisser bouton droit/central : déplacement</translation>
    </message>
</context>
<context>
    <name>ExportDialog</name>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="139"/>
        <source>Export Results</source>
        <translation>Exporter les résultats</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="146"/>
        <source>OUTPUT FOLDER</source>
        <translation>DOSSIER DE SORTIE</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="149"/>
        <source>Select output folder…</source>
        <translation>Sélectionner le dossier de sortie…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="151"/>
        <source>Browse…</source>
        <translation>Parcourir…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="152"/>
        <source>Choose the folder all exports are written into</source>
        <translation>Choisir le dossier où tous les exports sont écrits</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="155"/>
        <source>Open Folder</source>
        <translation>Ouvrir le dossier</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="156"/>
        <source>Open the output folder in the file explorer</source>
        <translation>Ouvrir le dossier de sortie dans l'explorateur de fichiers</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="168"/>
        <source>Data</source>
        <translation>Données</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="169"/>
        <source>Images</source>
        <translation>Images</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="170"/>
        <source>Animation</source>
        <translation>Animation</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="171"/>
        <source>Preview &amp; Colorbar</source>
        <translation>Aperçu et barre de couleur</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="172"/>
        <source>3D View</source>
        <translation>Vue 3D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="176"/>
        <source>Numeric results: field-selective NPZ / MAT / CSV tables plus PLY / VTU meshes for external tools.</source>
        <translation>Résultats numériques : tableaux NPZ / MAT / CSV sélectifs par champ, plus maillages PLY / VTU pour outils externes.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="180"/>
        <source>Rendered per-camera field overlays as PNG images, one per frame, using the Preview &amp; Colorbar style.</source>
        <translation>Superpositions de champ rendues par caméra en images PNG, une par image, avec le style « Aperçu et barre de couleurs ».</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="184"/>
        <source>GIF / MP4 animations of the field overlay across frames, using the Preview &amp; Colorbar style.</source>
        <translation>Animations GIF / MP4 de la superposition de champ au fil des images, avec le style « Aperçu et barre de couleurs ».</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="188"/>
        <source>WYSIWYG style source: the colorbar and margins configured here are used by every Images / Animation export.</source>
        <translation>Source de style WYSIWYG : la barre de couleurs et les marges configurées ici sont utilisées par chaque export d'images / d'animations.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="461"/>
        <source>Export Running</source>
        <translation>Export en cours</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="462"/>
        <source>An export is still running — cancel it and close?</source>
        <translation>Un export est encore en cours — l'annuler et fermer ?</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="465"/>
        <source>Yes</source>
        <translation>Oui</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="466"/>
        <source>No</source>
        <translation>Non</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="498"/>
        <source>Folder does not exist: {0}</source>
        <translation>Le dossier n'existe pas : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="204"/>
        <source>Close</source>
        <translation>Fermer</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="192"/>
        <source>Offscreen renders of the 3D surface as images, a deforming animation or a turntable, from your current 3D view.</source>
        <translation>Rendus hors écran de la surface 3D en images, animation de déformation ou rotation orbitale, depuis votre vue 3D actuelle.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_dialog.py" line="485"/>
        <source>Choose output folder</source>
        <translation>Choisir le dossier de sortie</translation>
    </message>
</context>
<context>
    <name>ExportTabBase</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="250"/>
        <source>Cancelling…</source>
        <translation>Annulation…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="287"/>
        <source>Export cancelled — {0} file(s) kept</source>
        <translation>Export annulé — {0} fichier(s) conservé(s)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="289"/>
        <source>(the unfinished animation was deleted)</source>
        <translation>(l'animation inachevée a été supprimée)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="296"/>
        <source>Nothing was written: no data to draw for {0}.</source>
        <translation>Rien n'a été écrit : aucune donnée à afficher pour {0}.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="299"/>
        <source>Nothing was written — the export produced no files.</source>
        <translation>Rien n'a été écrit — l'export n'a produit aucun fichier.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="307"/>
        <source>{0} frame(s) had no data to draw ({1})</source>
        <translation>{0} image(s) sans donnée à afficher ({1})</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="313"/>
        <source>no data for {0}</source>
        <translation>aucune donnée pour {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="317"/>
        <source>the right-camera ROI could not be derived; the tracked area was used</source>
        <translation>la ROI de la caméra droite n'a pas pu être déduite ; la zone suivie a été utilisée</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="278"/>
        <source>Error: {0}</source>
        <translation>Erreur : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="282"/>
        <source>Wrote {0} file(s)</source>
        <translation>{0} fichier(s) écrit(s)</translation>
    </message>
</context>
<context>
    <name>ExportTabs</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="625"/>
        <source>Full resolution</source>
        <translation>Résolution native</translation>
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
        <translation>Plage automatique</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="436"/>
        <source>Opacity</source>
        <translation>Opacité</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="437"/>
        <source>Field opacity (0 = transparent, 1 = fully opaque)</source>
        <translation>Opacité du champ (0 = transparent, 1 = opaque)</translation>
    </message>
</context>
<context>
    <name>FieldSelector3D</name>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="47"/>
        <source>DISPLACEMENT</source>
        <translation>DÉPLACEMENT</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="69"/>
        <source>U — world-frame displacement along X (left camera&apos;s +X, image right), in mm</source>
        <translation>U — déplacement dans le repère monde selon X (+X de la caméra gauche, vers la droite de l'image), en mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="72"/>
        <source>V — world-frame displacement along Y (left camera&apos;s +Y, image down), in mm</source>
        <translation>V — déplacement dans le repère monde selon Y (+Y de la caméra gauche, vers le bas de l'image), en mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="75"/>
        <source>W — world-frame displacement along Z (left camera&apos;s optical axis, toward the scene): out-of-plane motion, in mm</source>
        <translation>W — déplacement dans le repère monde selon Z (axe optique de la caméra gauche, vers la scène) : mouvement hors plan, en mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="78"/>
        <source>|D| — displacement magnitude √(U²+V²+W²), in mm</source>
        <translation>|D| — norme du déplacement √(U²+V²+W²), en mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="80"/>
        <location filename="../../gui/widgets/field_selector.py" line="107"/>
        <source>Velocity — per-node speed |D(k) − D(k−1)| × frame rate, in the display unit per second. Depends on the frame rate set in the UNITS section; frame 1 has no predecessor (empty).</source>
        <translation>Vitesse — vitesse par nœud |D(k) − D(k−1)| × cadence, dans l'unité d'affichage par seconde. Dépend de la cadence définie dans la section UNITS ; l'image 1 n'a pas de prédécesseur (vide).</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/field_selector.py" line="103"/>
        <source>Run an analysis first — velocity needs results.</source>
        <translation>Exécutez d'abord une analyse — la vitesse nécessite des résultats.</translation>
    </message>
</context>
<context>
    <name>FrameMasksSection3D</name>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="65"/>
        <source>Per-frame masks</source>
        <translation>Masques par image</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="69"/>
        <source>Optional: one mask image per frame (non-zero = valid), for
specimens whose valid region changes, e.g. a crack or a
boundary that moves. Without them the ROI of frame 1 is used
for every frame.</source>
        <translation>Facultatif : une image de masque par image (non nul = valide), pour
les éprouvettes dont la région valide change, p. ex. une fissure ou
un bord qui se déplace. Sans eux, la ROI de l'image 1 sert
pour toutes les images.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="83"/>
        <source>Import…</source>
        <translation>Importer…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="84"/>
        <source>Choose the folder holding this camera&apos;s mask images</source>
        <translation>Choisir le dossier contenant les masques de cette caméra</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="87"/>
        <source>Clear</source>
        <translation>Effacer</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="97"/>
        <source>Left</source>
        <translation>Gauche</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="97"/>
        <source>Right</source>
        <translation>Droite</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="104"/>
        <source>{0}: {1} masks</source>
        <translation>{0} : {1} masques</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="106"/>
        <source>{0}: none</source>
        <translation>{0} : aucun</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="114"/>
        <source>Choose the mask folder</source>
        <translation>Choisir le dossier des masques</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="128"/>
        <source>Masks not imported for the {0} camera: {1}</source>
        <translation>Masques non importés pour la caméra {0} : {1}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_masks_section.py" line="142"/>
        <source>{0} camera: {1} per-frame masks from {2}</source>
        <translation>Caméra {0} : {1} masques par image depuis {2}</translation>
    </message>
</context>
<context>
    <name>FrameNavigator3D</name>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="45"/>
        <source>Previous frame (←)</source>
        <translation>Image précédente (←)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="52"/>
        <location filename="../../gui/widgets/frame_navigator.py" line="160"/>
        <source>Play animation (Space)</source>
        <translation>Lire l'animation (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="59"/>
        <source>Next frame (→)</source>
        <translation>Image suivante (→)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="68"/>
        <source>Playback speed (frames per second). Default 2 fps.</source>
        <translation>Vitesse de lecture (images par seconde). Par défaut 2 fps.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="153"/>
        <source>Pause animation (Space)</source>
        <translation>Pause (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="175"/>
        <source>FRAME {0}/{1}</source>
        <translation>IMAGE {0}/{1}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/frame_navigator.py" line="177"/>
        <source>FRAME 0/0</source>
        <translation>IMAGE 0/0</translation>
    </message>
</context>
<context>
    <name>FrameRangeRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="656"/>
        <source>All frames</source>
        <translation>Toutes les images</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="660"/>
        <source>From frame</source>
        <translation>De l'image</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="670"/>
        <source>to</source>
        <translation>à</translation>
    </message>
</context>
<context>
    <name>ImageCanvas3D</name>
    <message>
        <location filename="../../gui/widgets/image_view.py" line="762"/>
        <source>The three points are nearly in a line — spread them around the edge</source>
        <translation>Les trois points sont presque alignés — répartissez-les sur le bord</translation>
    </message>
</context>
<context>
    <name>ImagesTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="55"/>
        <source>Fields</source>
        <translation>Champs</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="75"/>
        <source>Format</source>
        <translation>Format</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="84"/>
        <source>JPEG quality</source>
        <translation>Qualité JPEG</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="91"/>
        <source>Resolution (long edge)</source>
        <translation>Résolution (bord long)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="100"/>
        <source>Include colorbar</source>
        <translation>Inclure la barre de couleur</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="105"/>
        <source>Background</source>
        <translation>Arrière-plan</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="119"/>
        <source>Export Images</source>
        <translation>Exporter les images</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="130"/>
        <source>Load an image sequence first (open the project in the main window).</source>
        <translation>Chargez d'abord une séquence d'images (ouvrez le projet dans la fenêtre principale).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="156"/>
        <source>Choose an output folder first.</source>
        <translation>Choisissez d'abord un dossier de sortie.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/images_tab.py" line="160"/>
        <source>No fields enabled.</source>
        <translation>Aucun champ activé.</translation>
    </message>
</context>
<context>
    <name>InitGuessSection3D</name>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="112"/>
        <source>Clear</source>
        <translation>Effacer</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="74"/>
        <source>Starting Points</source>
        <translation>Points de départ</translation>
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
        <translation>Cliquez un ou plusieurs points sur la caméra GAUCHE, image 1 — au moins un
par région ROI connexe. Le voisinage de chaque point est apparié
automatiquement dans la caméra droite (décalage stéréo) et dans l'image 2
(amorce de mouvement), puis un champ de déformation du premier ordre est
propagé à chaque nœud du maillage — aucun réglage de recherche nécessaire.
Idéal pour les larges bases stéréo, les grands mouvements initiaux ou les
champs discontinus. Sans point placé, l'exécution retombe sur la FFT.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="94"/>
        <location filename="../../gui/widgets/init_guess_section.py" line="191"/>
        <source>Place points…</source>
        <translation>Placer des points…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="98"/>
        <source>Enter placement mode on the canvas. Left-click the LEFT camera,
frame 1 to ADD a point; right-click removes the nearest; Esc exits.</source>
        <translation>Mode placement sur le canevas. Clic gauche sur la caméra GAUCHE, image 1
pour AJOUTER un point ; clic droit supprime le plus proche ; Échap quitte.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="103"/>
        <source>Auto-place</source>
        <translation>Placement auto</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="106"/>
        <source>Place one Starting Point automatically, deep inside the ROI on
the LEFT camera, frame 1. Add more by hand for disconnected
regions or strongly varying motion.</source>
        <translation>Place automatiquement un point de départ au cœur de la ROI de la
caméra GAUCHE, image 1. Ajoutez-en d'autres à la main pour des
régions disjointes ou un mouvement très variable.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="113"/>
        <source>Remove all Starting Points</source>
        <translation>Supprimer tous les points de départ</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="122"/>
        <source>FFT (cross-correlation)</source>
        <translation>FFT (corrélation croisée)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="125"/>
        <source>Full-grid cross-correlation seeds frame 1 (and every reference
switch in incremental mode); later frames warm-start from the
previous solution. Robust default — the search radius is the
Temporal Search parameter.</source>
        <translation>La corrélation croisée sur toute la grille amorce l'image 1 (et
chaque changement de référence en mode incrémental) ; les images
suivantes repartent de la solution précédente. Défaut robuste — le
rayon de recherche est le paramètre « Recherche temporelle ».</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="134"/>
        <source>Previous frame</source>
        <translation>Image précédente</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="137"/>
        <source>Start every frame from the previous frame&apos;s solution — no
cross-correlation at all. Fastest; can silently freeze on large
motion or decorrelation — the validity gate will flag affected
frames.</source>
        <translation>Chaque image démarre de la solution de l'image précédente — aucune
corrélation croisée. Le plus rapide ; peut se figer silencieusement en
cas de grand mouvement ou de décorrélation — le contrôle de validité
signalera les images touchées.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="191"/>
        <source>Placing… (click to exit)</source>
        <translation>Placement… (cliquez pour sortir)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="233"/>
        <source>No point placed: the run finds the stereo offset from probe patches and seeds frame 1 by FFT. Place a point (or Auto-place) for large first-frame motion.</source>
        <translation>Aucun point placé : l'exécution trouve le décalage stéréo à partir de fenêtres sondes et initialise l'image 1 par FFT. Placez un point (ou placement auto) si le mouvement de la première image est grand.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="240"/>
        <location filename="../../gui/widgets/init_guess_section.py" line="273"/>
        <source>{0} point(s) placed</source>
        <translation>{0} point(s) placé(s)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="276"/>
        <source>{0} point(s) · {1}/{2} regions ready</source>
        <translation>{0} point(s) · {1}/{2} régions prêtes</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/init_guess_section.py" line="283"/>
        <source>{0} point(s) · {1}/{2} regions seeded — rest auto-seeded at run</source>
        <translation>{0} point(s) · {1}/{2} régions amorcées — le reste est amorcé automatiquement à l'exécution</translation>
    </message>
</context>
<context>
    <name>Issues</name>
    <message>
        <location filename="../../gui/issue_text.py" line="27"/>
        <source>left camera</source>
        <translation>caméra gauche</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="28"/>
        <source>right camera</source>
        <translation>caméra droite</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="36"/>
        <source>calibration file not set</source>
        <translation>fichier d'étalonnage non défini</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="39"/>
        <source>left/right sequences not set</source>
        <translation>séquences gauche/droite non définies</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="42"/>
        <source>need at least 2 frames</source>
        <translation>au moins 2 images sont nécessaires</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="43"/>
        <source>ROI not set</source>
        <translation>ROI non définie</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="44"/>
        <source>ROI is empty (xmin&lt;xmax, ymin&lt;ymax required)</source>
        <translation>ROI vide (xmin&lt;xmax et ymin&lt;ymax requis)</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="47"/>
        <source>left and right sequences use the same image files</source>
        <translation>les séquences gauche et droite utilisent les mêmes fichiers image</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="63"/>
        <source>sequence length mismatch: {0} vs {1}</source>
        <translation>longueurs de séquences différentes : {0} contre {1}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="67"/>
        <source>calibration file cannot be read: {0}</source>
        <translation>fichier d'étalonnage illisible : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="71"/>
        <source>{0}: image not readable: {1}</source>
        <translation>{0} : image illisible : {1}</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="75"/>
        <source>{0}: frame sizes differ ({1} vs {2})</source>
        <translation>{0} : tailles d'image différentes ({1} contre {2})</translation>
    </message>
    <message>
        <location filename="../../gui/issue_text.py" line="79"/>
        <source>ROI mask is {0} but the images are {1}: redraw or import it again</source>
        <translation>le masque ROI fait {0} mais les images font {1} : redessinez-le ou importez-le à nouveau</translation>
    </message>
</context>
<context>
    <name>LeftSidebar3D</name>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="82"/>
        <source>IMAGES</source>
        <translation>IMAGES</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="89"/>
        <source>Drop LEFT camera
folder or click</source>
        <translation>Déposez le dossier caméra
GAUCHE ou cliquez</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="90"/>
        <source>Drop RIGHT camera
folder or click</source>
        <translation>Déposez le dossier caméra
DROITE ou cliquez</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="95"/>
        <source>Natural Sort (1, 2, …, 10)</source>
        <translation>Tri naturel (1, 2, …, 10)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="98"/>
        <source>Sort file names numerically (img2 before img10). Default on; turn off for strict alphabetical order. Applies to the next folder load.</source>
        <translation>Trie les noms de fichiers numériquement (img2 avant img10). Activé par défaut ; désactivez pour un ordre strictement alphabétique. S'applique au prochain chargement de dossier.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="116"/>
        <location filename="../../gui/panels/left_sidebar.py" line="687"/>
        <source>No images loaded</source>
        <translation>Aucune image chargée</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="142"/>
        <source>CALIBRATION</source>
        <translation>ÉTALONNAGE</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="146"/>
        <source>WORKFLOW TYPE</source>
        <translation>TYPE DE FLUX</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="153"/>
        <source>INITIAL GUESS</source>
        <translation>ESTIMATION INITIALE</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="157"/>
        <source>REGION OF INTEREST</source>
        <translation>RÉGION D'INTÉRÊT</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="161"/>
        <source>PARAMETERS</source>
        <translation>PARAMÈTRES</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="165"/>
        <source>ADVANCED</source>
        <translation>AVANCÉ</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="231"/>
        <source>Incremental: each frame is compared to the previous reference frame.
Suitable for large accumulated deformation, required for large rotations.

Accumulative: every frame is compared to frame 1.
Accurate for small, monotonic deformation only.</source>
        <translation>Incrémental : chaque image est comparée à l'image de référence précédente.
Adapté aux grandes déformations cumulées, requis pour les grandes rotations.

Cumulatif : chaque image est comparée à l'image 1.
Précis uniquement pour les petites déformations monotones.</translation>
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
        <translation>Local DIC : Appariement d'imagettes indépendant (IC-GN). Rapide,
préserve les détails locaux. Idéal pour les petites
déformations ou les images de haute qualité.

AL-DIC : Lagrangien augmenté avec régularisation
FEM globale. Impose la compatibilité des déplacements
entre imagettes. Idéal pour les grandes déformations, les images
bruitées ou lorsque la précision de la déformation est importante.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="261"/>
        <source>Solver</source>
        <translation>Solveur</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="335"/>
        <location filename="../../gui/panels/left_sidebar.py" line="359"/>
        <source>bbox: not set</source>
        <translation>boîte englobante : non définie</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="362"/>
        <source>bbox: {0}–{1}, {2}–{3} px</source>
        <translation>boîte englobante : {0}–{1}, {2}–{3} px</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="382"/>
        <source>IC-GN subset window size in pixels (odd number). Default 33.
Larger = more robust on sparse speckle, smoother fields;
smaller = finer spatial detail but noisier. The subset must
span several speckles.</source>
        <translation>Taille de la fenêtre de subset IC-GN en pixels (impair). Par défaut 33.
Plus grand = plus robuste sur mouchetis clairsemé, champs plus lisses ; plus petit = détails spatiaux plus fins mais plus de bruit.
Le subset doit couvrir plusieurs mouchetures.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="226"/>
        <source>Accumulative</source>
        <translation>Cumulatif</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="227"/>
        <source>Incremental</source>
        <translation>Incrémental</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="238"/>
        <source>Tracking Mode</source>
        <translation>Mode de suivi</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="317"/>
        <source>Draw on the LEFT camera, frame 1 — all later frames and the right camera follow from it.</source>
        <translation>Dessinez sur la caméra GAUCHE, image 1 — toutes les images suivantes et la caméra droite en découlent.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="388"/>
        <source>Subset Size</source>
        <translation>Taille d'imagette</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="396"/>
        <source>Node spacing in pixels (power of 2). Default 16. Smaller =
denser measurement grid and longer runs; larger = faster but
coarser fields. Typically ¼–½ of the Subset Size.</source>
        <translation>Espacement des nœuds en pixels (puissance de 2). Par défaut 16. Plus petit = grille de mesure
plus dense et exécutions plus longues ; plus grand = plus rapide mais champs plus grossiers.
Typiquement ¼–½ de la taille du subset.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="401"/>
        <source>Subset Step</source>
        <translation>Pas d'imagette</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="407"/>
        <source>Stereo Search</source>
        <translation>Recherche stéréo</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="420"/>
        <source>Temporal Search</source>
        <translation>Recherche temporelle</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="426"/>
        <source>Mesh refinement</source>
        <translation>Raffinement du maillage</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="433"/>
        <source>Refine at mask boundaries (holes)</source>
        <translation>Raffiner aux limites du masque (trous)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="436"/>
        <source>Quadtree-subdivide mesh elements crossing interior mask
holes so the mesh hugs the hole edges. Default off (uniform
grid); enable when the ROI mask has cut-outs whose rims you
care about.</source>
        <translation>Subdivision quadtree des éléments de maillage traversant les trous internes du masque,
pour que le maillage épouse leurs bords. Désactivé par défaut (grille uniforme) ; à activer
quand le masque de ROI comporte des découpes dont les bords vous importent.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="443"/>
        <source>Refine at ROI edges</source>
        <translation>Raffiner aux bords de la ROI</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="446"/>
        <source>Quadtree-subdivide mesh elements along the outer ROI
boundary. Default off; enable for curved / irregular ROI
outlines where the uniform grid staircases.</source>
        <translation>Subdivision quadtree des éléments de maillage le long de la frontière externe de la ROI.
Désactivé par défaut ; à activer pour des contours de ROI courbes / irréguliers où la grille uniforme fait des marches.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="458"/>
        <source>How aggressively refined elements shrink: the minimum element
is step / 2^level. Default 1 (light); 3 is heavy — finer
boundary detail but many more nodes and a slower run.</source>
        <translation>Intensité du raffinement des éléments : l'élément minimal vaut pas / 2^niveau.
Par défaut 1 (léger) ; 3 est fort — détails de bord plus fins mais beaucoup plus de nœuds et une exécution plus lente.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="463"/>
        <source>Refinement Level</source>
        <translation>Niveau de raffinage</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="575"/>
        <source>NCC search half-width (pixels) around each node for the
left-to-right stereo match. Set larger than the largest
expected stereo disparity.</source>
        <translation>Demi-largeur de recherche NCC (pixels) autour de chaque nœud pour
l'appariement stéréo gauche-droite. À régler au-dessus de la plus
grande disparité stéréo attendue.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="580"/>
        <source>Half-width (pixels) of the temporal FFT integer search that seeds
each per-frame match. Set comfortably larger than the expected
inter-frame motion; with Auto-expand on (default) the engine can
still grow the search past this on a boundary-clipped peak.</source>
        <translation>Demi-largeur (pixels) de la recherche entière FFT temporelle qui
initialise chaque appariement d'image. À régler nettement au-dessus
du mouvement attendu entre images ; avec l'extension automatique
activée (par défaut), le moteur peut agrandir la recherche au-delà de
cette valeur lorsqu'un pic atteint le bord.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="596"/>
        <source>Current images: the engine starts the FFT search clamped to
{0} px (max(10, min(H, W) / 4 - subset)); Auto-expand can grow
it to {1} px (max(32, min(H, W) / 2)) on clipped peaks.</source>
        <translation>Images actuelles : le moteur limite au départ la recherche FFT à
{0} px (max(10, min(H, W) / 4 - sous-ensemble)) ; sur un pic écrêté,
l'extension automatique peut la porter à {1} px
(max(32, min(H, W) / 2)).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="618"/>
        <source>Inactive with the current Initial Guess / Tracking Mode: the
temporal FFT runs only when Initial Guess = FFT, or at reference
switches in Incremental mode; in Accumulative + Starting Point /
Previous frame no FFT runs, so this control has no effect.</source>
        <translation>Sans effet avec l'estimation initiale / le mode de suivi actuels :
la FFT temporelle ne s'exécute que si l'estimation initiale = FFT, ou
aux changements de référence en mode incrémental. En cumulatif + Point
de départ / Image précédente, aucune FFT ne s'exécute, ce réglage n'a
donc aucun effet.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="592"/>
        <source>Current images: values above {0} px cannot widen the search
(the window is clamped at the image borders).</source>
        <translation>Images actuelles : au-delà de {0} px la recherche ne s'élargit plus
(la fenêtre est tronquée aux bords de l'image).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="267"/>
        <source>Extra filters (correlation, outliers)</source>
        <translation>Filtres supplémentaires (corrélation, valeurs aberrantes)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="270"/>
        <source>Post-run filters: drop points whose correlation (ZNSSD),
reprojection error or 3D-outlier distance is too poor.
Default off (keep every tracked point); enable for noisy
data when a few bad points pollute the fields. The log
reports how many points each filter removed.</source>
        <translation>Filtres après exécution : écartent les points dont la corrélation (ZNSSD),
l'erreur de reprojection ou la distance d'aberration 3D est trop mauvaise.
Désactivés par défaut (tous les points suivis sont gardés) ; activez-les
sur des données bruitées quand quelques mauvais points polluent les champs.
Le journal indique combien de points chaque filtre a retirés.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="634"/>
        <source>No images found in {0}</source>
        <translation>Aucune image trouvée dans {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="642"/>
        <source>left camera</source>
        <translation>caméra gauche</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="642"/>
        <source>right camera</source>
        <translation>caméra droite</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="645"/>
        <source>This folder holds both cameras ({0}): using its {1} images for the {2}</source>
        <translation>Ce dossier contient les deux caméras ({0}) : ses {1} images sont utilisées pour la {2}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="656"/>
        <source>{0}: {1} images from {2}</source>
        <translation>{0} : {1} images depuis {2}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="692"/>
        <source>Paired: {0} frames per camera</source>
        <translation>Appairé : {0} images par caméra</translation>
    </message>
    <message>
        <location filename="../../gui/panels/left_sidebar.py" line="698"/>
        <source>Mismatch: {0} left vs {1} right</source>
        <translation>Discordance : {0} à gauche contre {1} à droite</translation>
    </message>
</context>
<context>
    <name>MainMenuMixin</name>
    <message>
        <location filename="../../gui/main_menu.py" line="58"/>
        <source>&amp;File</source>
        <translation>&amp;Fichier</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="60"/>
        <source>New Project</source>
        <translation>Nouveau projet</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="66"/>
        <source>Open Project…</source>
        <translation>Ouvrir le projet…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="73"/>
        <source>Recent Projects</source>
        <translation>Projets récents</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="79"/>
        <source>Save Project</source>
        <translation>Enregistrer le projet</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="84"/>
        <source>Save Project As…</source>
        <translation>Enregistrer le projet sous…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="94"/>
        <source>Associate .aldic3d files with pyALDIC-3D…</source>
        <translation>Associer les fichiers .aldic3d à pyALDIC-3D…</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="97"/>
        <source>Register .aldic3d so double-clicking a project file opens pyALDIC-3D (current user only, no admin rights needed).</source>
        <translation>Enregistre .aldic3d pour qu'un double-clic sur un fichier projet ouvre pyALDIC-3D (utilisateur actuel uniquement, aucun droit administrateur requis).</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="105"/>
        <source>Quit</source>
        <translation>Quitter</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="113"/>
        <source>&amp;Help</source>
        <translation>&amp;Aide</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="114"/>
        <source>User Guide</source>
        <translation>Guide de l'utilisateur</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="118"/>
        <source>Keyboard Shortcuts</source>
        <translation>Raccourcis clavier</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="121"/>
        <source>About pyALDIC-3D</source>
        <translation>À propos de pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="132"/>
        <source>&amp;Settings</source>
        <translation>&amp;Paramètres</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="133"/>
        <location filename="../../gui/main_menu.py" line="180"/>
        <source>Language</source>
        <translation>Langue</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="157"/>
        <location filename="../../gui/main_menu.py" line="163"/>
        <source>File Association</source>
        <translation>Association de fichiers</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="158"/>
        <source>Could not register the .aldic3d association: {0}</source>
        <translation>Impossible d'enregistrer l'association .aldic3d : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="165"/>
        <source>Done — double-clicking a .aldic3d file now opens it in pyALDIC-3D (registered for the current user).</source>
        <translation>Terminé — un double-clic sur un fichier .aldic3d l'ouvre désormais dans pyALDIC-3D (enregistré pour l'utilisateur actuel).</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="174"/>
        <source>The interface language changes to {0} after pyALDIC-3D restarts.</source>
        <translation>La langue de l'interface passe à {0} au redémarrage de pyALDIC-3D.</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="188"/>
        <source>Could not open a web browser. The user guide is at {0}</source>
        <translation>Impossible d'ouvrir un navigateur web. Le guide de l'utilisateur se trouve ici : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="214"/>
        <source>(not reachable)</source>
        <translation>(inaccessible)</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="220"/>
        <source>No recent projects</source>
        <translation>Aucun projet récent</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="224"/>
        <source>Clear list</source>
        <translation>Vider la liste</translation>
    </message>
    <message>
        <location filename="../../gui/main_menu.py" line="232"/>
        <source>The project file is not reachable right now: {0}</source>
        <translation>Le fichier de projet est inaccessible pour le moment : {0}</translation>
    </message>
</context>
<context>
    <name>MainWindow3D</name>
    <message>
        <location filename="../../gui/main_window.py" line="143"/>
        <source>pyALDIC-3D ready</source>
        <translation>pyALDIC-3D prêt</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="184"/>
        <source>Run an analysis first — there are no results to post-process</source>
        <translation>Lancez d'abord une analyse — il n'y a aucun résultat à post-traiter</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="216"/>
        <source>Strain window available — open it from the sidebar</source>
        <translation>Fenêtre de déformation disponible — ouvrez-la depuis la barre latérale</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="278"/>
        <location filename="../../gui/main_window.py" line="296"/>
        <source>Analysis Running</source>
        <translation>Analyse en cours</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="279"/>
        <source>An analysis is running — cancel it and quit?</source>
        <translation>Une analyse est en cours — l'annuler et quitter ?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="284"/>
        <location filename="../../gui/main_window.py" line="300"/>
        <location filename="../../gui/main_window.py" line="677"/>
        <source>Yes</source>
        <translation>Oui</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="285"/>
        <location filename="../../gui/main_window.py" line="301"/>
        <location filename="../../gui/main_window.py" line="678"/>
        <source>No</source>
        <translation>Non</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="297"/>
        <source>An analysis is running — cancel it and switch projects?</source>
        <translation>Une analyse est en cours — l'annuler et changer de projet ?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="331"/>
        <source>Unsaved Changes</source>
        <translation>Modifications non enregistrées</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="332"/>
        <source>The project has unsaved changes. Save them before continuing?</source>
        <translation>Le projet comporte des modifications non enregistrées. Les enregistrer avant de continuer ?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="339"/>
        <source>Save</source>
        <translation>Enregistrer</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="340"/>
        <source>Discard</source>
        <translation>Abandonner</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="341"/>
        <location filename="../../gui/main_window.py" line="593"/>
        <location filename="../../gui/main_window.py" line="679"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="362"/>
        <source>Switched to left camera, frame 1 for ROI editing</source>
        <translation>Passage à la caméra gauche, image 1, pour l'édition de la ROI</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="367"/>
        <source>Load images first, then draw the region of interest</source>
        <translation>Chargez d'abord les images, puis dessinez la région d'intérêt</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="380"/>
        <source>Load images first, then place a starting point</source>
        <translation>Chargez d'abord les images, puis placez un point de départ</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="398"/>
        <source>Starting points are already placed; clear them to auto-place</source>
        <translation>Des points de départ sont déjà placés ; effacez-les pour le placement automatique</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="404"/>
        <source>Draw the ROI first: the point is placed inside it</source>
        <translation>Dessinez d'abord la ROI : le point est placé à l'intérieur</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="411"/>
        <source>Starting point placed automatically at ({0:.0f}, {1:.0f})</source>
        <translation>Point de départ placé automatiquement en ({0:.0f}, {1:.0f})</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="419"/>
        <source>Load images first, then use the brush</source>
        <translation>Chargez d'abord les images, puis utilisez le pinceau</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="506"/>
        <source>Loading project…</source>
        <translation>Chargement du projet…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="508"/>
        <source>Could not open the project: {0}</source>
        <translation>Impossible d'ouvrir le projet : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="511"/>
        <source>Could not open the project:
{0}

{1}</source>
        <translation>Impossible d'ouvrir le projet :
{0}

{1}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="523"/>
        <source>Opened {0}</source>
        <translation>{0} ouvert</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="546"/>
        <source>Open cancelled: {0}</source>
        <translation>Ouverture annulée : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="553"/>
        <source>Camera {0}: {1} image(s) not found (was {2}). Results stay viewable and exportable; running again needs the images.</source>
        <translation>Caméra {0} : {1} image(s) introuvable(s) (auparavant {2}). Les résultats restent consultables et exportables ; une nouvelle exécution nécessite les images.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="560"/>
        <source>Relocated {0} camera-{1} images: {2} -&gt; {3}</source>
        <translation>{0} images de la caméra {1} relocalisées : {2} -&gt; {3}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="567"/>
        <source>Calibration file found at {0}</source>
        <translation>Fichier d'étalonnage trouvé : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="572"/>
        <source>The calibration file was not found; using the copy saved in the project: {0}</source>
        <translation>Fichier d'étalonnage introuvable ; utilisation de la copie enregistrée dans le projet : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="583"/>
        <source>Images Not Found</source>
        <translation>Images introuvables</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="586"/>
        <source>Some of this project&apos;s images cannot be found. Open it anyway? Results stay viewable and exportable; running again needs the images.</source>
        <translation>Certaines images de ce projet sont introuvables. L'ouvrir quand même ? Les résultats restent consultables et exportables ; une nouvelle exécution nécessite les images.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="592"/>
        <source>Open anyway</source>
        <translation>Ouvrir quand même</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="601"/>
        <location filename="../../gui/main_window.py" line="611"/>
        <source>Locate Images</source>
        <translation>Localiser les images</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="603"/>
        <source>The selected folder does not contain this project&apos;s camera {0} frames. Pick the folder holding the original image files, or cancel to abort opening.</source>
        <translation>Le dossier sélectionné ne contient pas les images de la caméra {0} de ce projet. Choisissez le dossier contenant les fichiers d'images d'origine, ou annulez pour interrompre l'ouverture.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="613"/>
        <source>The image folder saved with this project was not found:
{0}

Select the folder that now contains the camera {1} frames (file names must match).</source>
        <translation>Le dossier d'images enregistré avec ce projet est introuvable :
{0}

Sélectionnez le dossier qui contient désormais les images de la caméra {1} (les noms de fichiers doivent correspondre).</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="620"/>
        <source>Locate images for camera {0}</source>
        <translation>Localiser les images de la caméra {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="662"/>
        <source>Include Results?</source>
        <translation>Inclure les résultats ?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="663"/>
        <source>Include the analysis results in this project file?</source>
        <translation>Inclure les résultats d'analyse dans ce fichier projet ?</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="666"/>
        <source>Including results (about {0} uncompressed) lets you reopen the project without recomputing. Choose No to save a small configuration-only file for sharing.</source>
        <translation>Inclure les résultats (environ {0} non compressés) permet de rouvrir le projet sans recalcul. Choisissez Non pour enregistrer un petit fichier de configuration seule, facile à partager.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="704"/>
        <source>unknown size</source>
        <translation>taille inconnue</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="714"/>
        <source>Saving project…</source>
        <translation>Enregistrement du projet…</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="718"/>
        <source>Could not save the project: {0}</source>
        <translation>Impossible d'enregistrer le projet : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="722"/>
        <source>Could not save the project:
{0}

{1}

The previous version of the file, if any, is unchanged.</source>
        <translation>Impossible d'enregistrer le projet :
{0}

{1}

La version précédente du fichier, s'il y en a une, est intacte.</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="730"/>
        <source>Saved {0}</source>
        <translation>{0} enregistré</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="436"/>
        <source>Untitled</source>
        <translation>Sans titre</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="437"/>
        <source>{0}[*] — pyALDIC-3D</source>
        <translation>{0}[*] — pyALDIC-3D</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="482"/>
        <source>New project</source>
        <translation>Nouveau projet</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="491"/>
        <location filename="../../gui/main_window.py" line="510"/>
        <source>Open Project</source>
        <translation>Ouvrir le projet</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="493"/>
        <location filename="../../gui/main_window.py" line="648"/>
        <source>pyALDIC-3D project (*.aldic3d)</source>
        <translation>Projet pyALDIC-3D (*.aldic3d)</translation>
    </message>
    <message>
        <location filename="../../gui/main_window.py" line="646"/>
        <location filename="../../gui/main_window.py" line="720"/>
        <source>Save Project</source>
        <translation>Enregistrer le projet</translation>
    </message>
</context>
<context>
    <name>ManualParamsDialog</name>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="53"/>
        <source>Manual Camera Parameters</source>
        <translation>Paramètres caméra manuels</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="61"/>
        <source>Left camera (world frame)</source>
        <translation>Caméra gauche (repère monde)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="62"/>
        <source>Right camera</source>
        <translation>Caméra droite</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="67"/>
        <source>Stereo extrinsics  (X_R = R · X_L + T)</source>
        <translation>Extrinsèques stéréo (X_R = R · X_L + T)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="71"/>
        <source>{0} (deg)</source>
        <translation>{0} (deg)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="78"/>
        <source>{0} (mm)</source>
        <translation>{0} (mm)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="87"/>
        <source>Euler composition R = Rz·Ry·Rx in degrees (MatchID/OpenCorr convention); distortion order k1, k2, p1, p2, k3 (OpenCV).</source>
        <translation>Composition d'Euler R = Rz·Ry·Rx en degrés (convention MatchID/OpenCorr) ; ordre de distorsion k1, k2, p1, p2, k3 (OpenCV).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="101"/>
        <source>Save as YAML…</source>
        <translation>Enregistrer en YAML…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="106"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="142"/>
        <source>Baseline |T| = {0:.2f} mm</source>
        <translation>Ligne de base |T| = {0:.2f} mm</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="147"/>
        <source>Baseline is zero — enter the translation T first.</source>
        <translation>La ligne de base est nulle — saisissez d'abord la translation T.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/manual_params_dialog.py" line="154"/>
        <source>Save calibration as</source>
        <translation>Enregistrer l'étalonnage sous</translation>
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
        <translation>Maillage :</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="40"/>
        <source>Line color and width of the mesh overlay (Show Grid)</source>
        <translation>Couleur et épaisseur des lignes du maillage (Afficher la grille)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="45"/>
        <source>Mesh overlay line color — click to choose</source>
        <translation>Couleur des lignes du maillage — cliquez pour choisir</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="53"/>
        <source>Mesh overlay line width (screen pixels)</source>
        <translation>Épaisseur des lignes du maillage (pixels écran)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/mesh_appearance.py" line="79"/>
        <source>Choose mesh line color</source>
        <translation>Choisir la couleur des lignes du maillage</translation>
    </message>
</context>
<context>
    <name>NextStepHint</name>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="49"/>
        <source>Load the left and right camera folders</source>
        <translation>Chargez les dossiers des caméras gauche et droite</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="54"/>
        <source>Calibrate from images or import a calibration</source>
        <translation>Étalonnez à partir d'images ou importez un étalonnage</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/next_step_hint.py" line="56"/>
        <source>Draw the ROI on the left camera, frame 1</source>
        <translation>Dessinez la ROI sur la caméra gauche, image 1</translation>
    </message>
</context>
<context>
    <name>PairActionsMixin</name>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="58"/>
        <source>Removed {0} image pair(s)</source>
        <translation>{0} paire(s) d'images retirée(s)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="69"/>
        <source>Remove Image Pairs</source>
        <translation>Supprimer des paires d'images</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="72"/>
        <source>Removing {0} pair(s) changes the sequence — the current results will be discarded. Continue?</source>
        <translation>Supprimer {0} paire(s) modifie la séquence — les résultats actuels seront perdus. Continuer ?</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="78"/>
        <source>Yes</source>
        <translation>Oui</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="79"/>
        <source>No</source>
        <translation>Non</translation>
    </message>
    <message>
        <location filename="../../gui/panels/pair_actions.py" line="94"/>
        <source>Folder does not exist: {0}</source>
        <translation>Le dossier n'existe pas : {0}</translation>
    </message>
</context>
<context>
    <name>PairBars</name>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="106"/>
        <source>no solve yet</source>
        <translation>pas encore de solution</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/calibration_support.py" line="128"/>
        <source>worst-camera RMS per pair; dashed = reject threshold</source>
        <translation>RMS caméra la plus défavorable par paire ; pointillés = seuil de rejet</translation>
    </message>
</context>
<context>
    <name>PairListWidget</name>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="25"/>
        <source>Left</source>
        <translation>Gauche</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="25"/>
        <source>Right</source>
        <translation>Droite</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="70"/>
        <source>Remove {0} selected pair(s)</source>
        <translation>Supprimer les {0} paire(s) sélectionnée(s)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/pair_list.py" line="73"/>
        <source>Reveal in Explorer</source>
        <translation>Afficher dans l'explorateur</translation>
    </message>
</context>
<context>
    <name>PreviewTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="120"/>
        <source>Open this tab to render a preview.</source>
        <translation>Ouvrez cet onglet pour générer un aperçu.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="128"/>
        <source>Field</source>
        <translation>Champ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="135"/>
        <source>Frame</source>
        <translation>Image</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="144"/>
        <source>Camera</source>
        <translation>Caméra</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="148"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="226"/>
        <source>Left</source>
        <translation>Gauche</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="149"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="225"/>
        <source>Right</source>
        <translation>Droite</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="180"/>
        <source>FIELD APPEARANCE</source>
        <translation>APPARENCE DU CHAMP</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="185"/>
        <source>Colormap</source>
        <translation>Palette</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="187"/>
        <source>Auto</source>
        <translation>Auto</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="188"/>
        <source>Auto range</source>
        <translation>Plage automatique</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="191"/>
        <source>Range</source>
        <translation>Plage</translation>
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
        <translation>Opacité</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="207"/>
        <source>Apply to all fields</source>
        <translation>Appliquer à tous les champs</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="210"/>
        <source>Apply this field&apos;s colormap, opacity and auto-range to every enabled field (each field keeps its own min/max).</source>
        <translation>Applique la colormap, l'opacité et l'auto-plage de ce champ à tous les champs activés (chaque champ garde ses propres min/max).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="220"/>
        <source>COLORBAR STYLE</source>
        <translation>STYLE DE BARRE DE COULEUR</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="227"/>
        <source>Top</source>
        <translation>Haut</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="228"/>
        <source>Bottom</source>
        <translation>Bas</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="232"/>
        <source>Position</source>
        <translation>Position</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="238"/>
        <source>Font size</source>
        <translation>Taille de police</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="244"/>
        <source>Font family</source>
        <translation>Police</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="252"/>
        <source>Bar thickness</source>
        <translation>Épaisseur de la barre</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="255"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="274"/>
        <source>Black</source>
        <translation>Noir</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="255"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="274"/>
        <source>White</source>
        <translation>Blanc</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="258"/>
        <source>Background</source>
        <translation>Arrière-plan</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="266"/>
        <source>Add a blank border around the exported content, as a fraction of the long edge (0 = none).</source>
        <translation>Ajoute une bordure vide autour du contenu exporté, en fraction du bord long (0 = aucune).</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="271"/>
        <source>Margin</source>
        <translation>Marge</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="277"/>
        <source>Margin color</source>
        <translation>Couleur de marge</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="279"/>
        <source>Refresh preview</source>
        <translation>Actualiser l'aperçu</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="531"/>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="545"/>
        <source>Preview failed: </source>
        <translation>Échec de l'aperçu : </translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="430"/>
        <source>Enable a field on the Images tab to preview.</source>
        <translation>Activez un champ dans l'onglet Images pour l'aperçu.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/preview_tab.py" line="549"/>
        <source>No data for this field/frame.</source>
        <translation>Aucune donnée pour ce champ/cette image.</translation>
    </message>
</context>
<context>
    <name>Progress</name>
    <message>
        <location filename="../../gui/progress_text.py" line="30"/>
        <source>Preparing: checking the images and building the mesh</source>
        <translation>Préparation : vérification des images et construction du maillage</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="33"/>
        <source>Preparing: initial guess for the left camera</source>
        <translation>Préparation : estimation initiale de la caméra gauche</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="36"/>
        <source>Preparing: mesh and initial guess for the right camera</source>
        <translation>Préparation : maillage et estimation initiale de la caméra droite</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="39"/>
        <source>Preparing: estimating the stereo offset</source>
        <translation>Préparation : estimation du décalage stéréo</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="42"/>
        <location filename="../../gui/progress_text.py" line="53"/>
        <source>tracking complete</source>
        <translation>suivi terminé</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="43"/>
        <source>normalizing images</source>
        <translation>normalisation des images</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="46"/>
        <location filename="../../gui/progress_text.py" line="49"/>
        <source>composing displacements</source>
        <translation>composition des déplacements</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="52"/>
        <source>assembling results</source>
        <translation>assemblage des résultats</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="62"/>
        <source>Left camera</source>
        <translation>Caméra gauche</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="64"/>
        <source>Right camera</source>
        <translation>Caméra droite</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="66"/>
        <source>{0}: {1}</source>
        <translation>{0} : {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="74"/>
        <source>tracking frame {0} of {1}</source>
        <translation>suivi de l'image {0} sur {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="80"/>
        <source>verifying frame {0} of {1} (keeping the frames tracked before the stop)</source>
        <translation>vérification de l'image {0} sur {1} (conservation des images suivies avant l'arrêt)</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="85"/>
        <source>verifying frame {0} of {1}</source>
        <translation>vérification de l'image {0} sur {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="89"/>
        <source>assembling frame {0} of {1}</source>
        <translation>assemblage de l'image {0} sur {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="94"/>
        <source>strain: frame {0} of {1}</source>
        <translation>déformation : image {0} sur {1}</translation>
    </message>
    <message>
        <location filename="../../gui/progress_text.py" line="99"/>
        <source>Preparing: matching the two cameras at {0} nodes</source>
        <translation>Préparation : appariement des deux caméras sur {0} nœuds</translation>
    </message>
</context>
<context>
    <name>ProgressRow</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="156"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/common.py" line="173"/>
        <source>Exporting…</source>
        <translation>Exportation…</translation>
    </message>
</context>
<context>
    <name>ROIToolbar</name>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="75"/>
        <source>+ Add</source>
        <translation>+ Ajouter</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="77"/>
        <source>Add region to the Region of Interest (Polygon / Rectangle / Circle)</source>
        <translation>Ajouter une région à la région d'intérêt (Polygone / Rectangle / Cercle)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="81"/>
        <source>Cut</source>
        <translation>Découper</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="83"/>
        <source>Cut region from the Region of Interest (Polygon / Rectangle / Circle)</source>
        <translation>Découper une région de la région d'intérêt (Polygone / Rectangle / Cercle)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="87"/>
        <source>+ Refine</source>
        <translation>+ Raffiner</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="90"/>
        <source>Paint extra mesh-refinement zones with a brush
(on the LEFT camera, frame 1 — the reference mesh geometry)</source>
        <translation>Peindre des zones de raffinage de maillage supplémentaires au pinceau
(sur la caméra GAUCHE, image 1 — la géométrie du maillage de référence)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="110"/>
        <source>Import</source>
        <translation>Importer</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="111"/>
        <source>Import mask from image file</source>
        <translation>Importer le masque depuis un fichier image</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="120"/>
        <source>Save</source>
        <translation>Enregistrer</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="121"/>
        <source>Save current mask to PNG file</source>
        <translation>Enregistrer le masque actuel en PNG</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="126"/>
        <source>Invert</source>
        <translation>Inverser</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="127"/>
        <source>Invert the Region of Interest mask</source>
        <translation>Inverser le masque de la région d'intérêt</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="132"/>
        <source>Clear</source>
        <translation>Effacer</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="133"/>
        <source>Clear all Region of Interest masks</source>
        <translation>Effacer tous les masques de région d'intérêt</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="159"/>
        <source>Polygon</source>
        <translation>Polygone</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="163"/>
        <source>Rectangle</source>
        <translation>Rectangle</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="167"/>
        <source>Circle</source>
        <translation>Cercle</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="171"/>
        <source>Circle (3-point)</source>
        <translation>Cercle (3 points)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="185"/>
        <source>Radius</source>
        <translation>Rayon</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="202"/>
        <source>Paint</source>
        <translation>Peindre</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="206"/>
        <source>Erase</source>
        <translation>Effacer</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="215"/>
        <source>Clear Brush</source>
        <translation>Effacer le pinceau</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="247"/>
        <source>Import Mask Image</source>
        <translation>Importer une image de masque</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/roi_toolbar.py" line="249"/>
        <source>Images (*.png *.bmp *.tif *.tiff *.jpg *.jpeg);;All Files (*)</source>
        <translation>Images (*.png *.bmp *.tif *.tiff *.jpg *.jpeg);;Tous les fichiers (*)</translation>
    </message>
</context>
<context>
    <name>RefUpdateSection3D</name>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="55"/>
        <source>Reference Update</source>
        <translation>Mise à jour de la référence</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="60"/>
        <source>Every Frame</source>
        <translation>Chaque image</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="61"/>
        <source>Every N Frames</source>
        <translation>Toutes les N images</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="62"/>
        <source>Custom Frames</source>
        <translation>Images personnalisées</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="65"/>
        <source>How often the incremental reference frame advances.
Every Frame (default): frame k matches against k−1 — tracks
large accumulated deformation, but drift can accumulate.
Every N Frames: the reference advances only every N frames —
less drift, needs correlation to survive N frames of motion.
Custom Frames: reference updates exactly at the listed frames.</source>
        <translation>Fréquence d'avancement de l'image de référence en mode incrémental.
Chaque image (défaut) : l'image k est appariée à k−1 — suit de grandes
déformations cumulées, mais la dérive peut s'accumuler.
Toutes les N images : la référence n'avance que toutes les N images —
moins de dérive, mais la corrélation doit survivre à N images de
mouvement.
Images personnalisées : la référence est mise à jour exactement aux
images listées.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="78"/>
        <source>Update every</source>
        <translation>Mettre à jour toutes les</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="85"/>
        <source> frames</source>
        <translation> images</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="87"/>
        <source>Reference-update interval N: frames k use the last reference at i·N &lt; k</source>
        <translation>Intervalle de mise à jour N : l'image k utilise la dernière référence avec i·N &lt; k</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="93"/>
        <source>e.g. 5, 10, 20 (0-based frame indices)</source>
        <translation>ex. 5, 10, 20 (indices d'image base 0)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="96"/>
        <source>Comma-separated 0-based frame indices that become reference
frames (frame 0 always is one). The last frame cannot be a
reference.</source>
        <translation>Indices d'image base 0, séparés par des virgules, qui deviennent des
images de référence (l'image 0 en est toujours une). La dernière image
ne peut pas être une référence.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/ref_update_section.py" line="141"/>
        <source>Enter comma-separated 0-based frame numbers, e.g. 5, 10, 20</source>
        <translation>Saisissez des numéros d'image base 0 séparés par des virgules, ex. 5, 10, 20</translation>
    </message>
</context>
<context>
    <name>RightSidebar3D</name>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="99"/>
        <source>Run 3D Analysis</source>
        <translation>Lancer l'analyse 3D</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="105"/>
        <location filename="../../gui/panels/right_sidebar.py" line="456"/>
        <source>Run the full stereo correspondence + triangulation pipeline on the loaded image pairs (F5).</source>
        <translation>Exécute le pipeline complet de correspondance stéréo + triangulation sur les paires d'images chargées (F5).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="112"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="127"/>
        <source>Export Results</source>
        <translation>Exporter les résultats</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="135"/>
        <source>Open Strain Window</source>
        <translation>Ouvrir la fenêtre de déformation</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="148"/>
        <source>Parameters changed since this result — re-run to update</source>
        <translation>Paramètres modifiés depuis ce résultat — relancez pour mettre à jour</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="156"/>
        <source>PROGRESS</source>
        <translation>PROGRESSION</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="163"/>
        <location filename="../../gui/panels/right_sidebar.py" line="638"/>
        <source>Ready</source>
        <translation>Prêt</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="168"/>
        <source>ELAPSED  --:--</source>
        <translation>ÉCOULÉ  --:--</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="171"/>
        <source>REMAINING  --:--</source>
        <translation>RESTANT  --:--</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="177"/>
        <source>FIELD</source>
        <translation>CHAMP</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="183"/>
        <source>Show on deformed frame</source>
        <translation>Afficher sur l'image déformée</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="187"/>
        <source>When checked, overlay results on the deformed (current) frame instead of the reference frame</source>
        <translation>Lorsque cette option est activée, les résultats sont superposés sur l'image déformée (actuelle) au lieu de l'image de référence</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="196"/>
        <source>Camera</source>
        <translation>Caméra</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="200"/>
        <source>Left</source>
        <translation>Gauche</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="203"/>
        <source>Show the LEFT camera&apos;s images (the reference view: ROI, seed and mesh live here). Default.</source>
        <translation>Affiche les images de la caméra GAUCHE (vue de référence : ROI, point de départ et maillage y résident). Par défaut.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="207"/>
        <source>Right</source>
        <translation>Droite</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="210"/>
        <source>Show the RIGHT camera&apos;s images with the field warped onto them — a cross-check that the stereo match is sound.</source>
        <translation>Affiche les images de la caméra DROITE avec le champ projeté dessus — une contre-vérification de la validité de l'appariement stéréo.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="226"/>
        <source>VISUALIZATION</source>
        <translation>VISUALISATION</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="229"/>
        <source>Colormap</source>
        <translation>Palette</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="237"/>
        <source>Colormap for the field overlay and the 3D surface. Default turbo (perceptually ordered, high contrast); pick RdBu_r or coolwarm for signed fields centered on zero.</source>
        <translation>Palette de couleurs pour la superposition de champ et la surface 3D. Par défaut turbo (perceptuellement ordonnée, contrastée) ; choisissez RdBu_r ou coolwarm pour les champs signés centrés sur zéro.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="246"/>
        <source>Auto range</source>
        <translation>Plage automatique</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="250"/>
        <source>Rescale the color range to each frame&apos;s data range (2–98 percentile of the visible values). Default on; uncheck to type fixed Min/Max bounds that hold across frames.</source>
        <translation>Ajuster la plage de couleurs à la plage de données de chaque image (percentiles 2–98 des valeurs visibles). Activé par défaut ; décochez pour saisir des bornes Min/Max fixes valables pour toutes les images.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="262"/>
        <source>Min</source>
        <translation>Min</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="270"/>
        <source>Lower color-range bound (only with Auto range off)</source>
        <translation>Borne inférieure de la plage de couleurs (uniquement avec la plage auto désactivée)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="271"/>
        <source>Upper color-range bound (only with Auto range off)</source>
        <translation>Borne supérieure de la plage de couleurs (uniquement avec la plage auto désactivée)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="277"/>
        <source>Max</source>
        <translation>Max</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="283"/>
        <source>Opacity</source>
        <translation>Opacité</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="290"/>
        <source>Overlay opacity (0 = transparent, 100 = opaque)</source>
        <translation>Opacité de la superposition (0 = transparent, 100 = opaque)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="297"/>
        <source>UNITS</source>
        <translation>UNITÉS</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="304"/>
        <source>LOG</source>
        <translation>JOURNAL</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="313"/>
        <source>All messages</source>
        <translation>Tous les messages</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="314"/>
        <source>Info</source>
        <translation>Infos</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="315"/>
        <source>Warnings + errors</source>
        <translation>Avertissements + erreurs</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="316"/>
        <source>Errors only</source>
        <translation>Erreurs seulement</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="319"/>
        <source>Show only log messages of this severity</source>
        <translation>N'afficher que les messages de cette gravité</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="322"/>
        <source>Save…</source>
        <translation>Enregistrer…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="327"/>
        <source>Save the full log to a text file</source>
        <translation>Enregistrer le journal complet dans un fichier texte</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="330"/>
        <source>Clear</source>
        <translation>Effacer</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="335"/>
        <source>Clear the log console (messages are not recoverable)</source>
        <translation>Effacer la console de journal (messages non récupérables)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="419"/>
        <source>Save log</source>
        <translation>Enregistrer le journal</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="419"/>
        <source>Text files (*.txt)</source>
        <translation>Fichiers texte (*.txt)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="430"/>
        <source>Log saved to {0}</source>
        <translation>Journal enregistré dans {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="452"/>
        <location filename="../../gui/panels/right_sidebar.py" line="468"/>
        <source>Not ready — {0}</source>
        <translation>Non prêt — {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="472"/>
        <source>Ready to run. No starting point: the stereo offset is found automatically and frame 1 is seeded by FFT.</source>
        <translation>Prêt à lancer. Aucun point de départ : le décalage stéréo est trouvé automatiquement et l'image 1 est initialisée par FFT.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="477"/>
        <source>Ready to run.</source>
        <translation>Prêt à lancer.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="512"/>
        <source>Export displacement and strain results to NPZ / MAT / CSV</source>
        <translation>Exporter les résultats de déplacement et de déformation en NPZ / MAT / CSV</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="516"/>
        <source>Compute and visualize strain in a separate post-processing window. Requires displacement results from a completed Run.</source>
        <translation>Calculer et visualiser la déformation dans une fenêtre de post-traitement séparée. Nécessite des résultats de déplacement d'une exécution terminée.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="522"/>
        <source>Available after the running analysis finishes.</source>
        <translation>Disponible une fois l'analyse en cours terminée.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="524"/>
        <source>Run an analysis first — there are no results yet.</source>
        <translation>Lancez d'abord une analyse — il n'y a pas encore de résultats.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="542"/>
        <source>Not ready: {0}</source>
        <translation>Non prêt : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="559"/>
        <source>Starting 3D analysis…</source>
        <translation>Démarrage de l'analyse 3D…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="578"/>
        <source>Cancelling — finishing current frame…</source>
        <translation>Annulation — finalisation de l'image en cours…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="579"/>
        <source>Cancelling…</source>
        <translation>Annulation…</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="604"/>
        <source>Stopped early — partial results kept</source>
        <translation>Arrêt anticipé — résultats partiels conservés</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="597"/>
        <source>Analysis complete</source>
        <translation>Analyse terminée</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="427"/>
        <location filename="../../gui/panels/right_sidebar.py" line="616"/>
        <source>Failed: {0}</source>
        <translation>Échec : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="118"/>
        <source>Cancel the current analysis. Frames computed so far are kept as a partial result; only when nothing was computed yet does the run return to IDLE.</source>
        <translation>Annule l'analyse en cours. Les images déjà calculées sont conservées comme résultat partiel ; ce n'est que si rien n'a encore été calculé que l'exécution revient à l'état inactif.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="615"/>
        <source>Analysis failed</source>
        <translation>Échec de l'analyse</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="620"/>
        <source>Analysis Failed</source>
        <translation>Échec de l'analyse</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="622"/>
        <source>The analysis stopped with an error:

{0}

The log has the details.</source>
        <translation>L'analyse s'est arrêtée sur une erreur :

{0}

Le journal donne les détails.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="641"/>
        <source>Run cancelled</source>
        <translation>Exécution annulée</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="556"/>
        <location filename="../../gui/panels/right_sidebar.py" line="639"/>
        <location filename="../../gui/panels/right_sidebar.py" line="648"/>
        <source>ELAPSED  {0}</source>
        <translation>ÉCOULÉ  {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/right_sidebar.py" line="557"/>
        <location filename="../../gui/panels/right_sidebar.py" line="596"/>
        <location filename="../../gui/panels/right_sidebar.py" line="640"/>
        <location filename="../../gui/panels/right_sidebar.py" line="654"/>
        <source>REMAINING  {0}</source>
        <translation>RESTANT  {0}</translation>
    </message>
</context>
<context>
    <name>RunSummaryMixin</name>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="25"/>
        <source>Analysis complete</source>
        <translation>Analyse terminée</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="41"/>
        <source>Stopped early at frame {0}/{1} — kept {2} computed frames (later frames are empty)</source>
        <translation>Arrêt anticipé à l'image {0}/{1} — {2} images calculées conservées (les images suivantes sont vides)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="47"/>
        <source>Run interrupted: {0}</source>
        <translation>Exécution interrompue : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="51"/>
        <source>Frame-1 stereo match: {0}/{1} points matched ({2}%)</source>
        <translation>Appariement stéréo image 1 : {0}/{1} points appariés ({2} %)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="59"/>
        <source>Camera {0}: validity gate removed {1} node-frames (correlation vs frame 1 failed)</source>
        <translation>Caméra {0} : le contrôle de validité a supprimé {1} nœuds-images (corrélation avec l'image 1 échouée)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="66"/>
        <source>Frame {0}: only {1}% of points valid</source>
        <translation>Image {0} : seulement {1} % de points valides</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="73"/>
        <source>Quality gate (ZNSSD) removed {0} positions</source>
        <translation>Le contrôle qualité (ZNSSD) a supprimé {0} positions</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="74"/>
        <source>Reprojection gate removed {0} positions</source>
        <translation>Le contrôle de reprojection a supprimé {0} positions</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="75"/>
        <source>3D outlier filter removed {0} positions</source>
        <translation>Le filtre de points aberrants 3D a supprimé {0} positions</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="89"/>
        <source>Validity falls from {0}% (frame 1) to {1}%: tracking every frame against frame 1 cannot follow large deformation. Try WORKFLOW TYPE &gt; Incremental.</source>
        <translation>La validité chute de {0} % (image 1) à {1} % : comparer chaque image à l'image 1 ne suit pas les grandes déformations. Essayez TYPE DE FLUX &gt; Incrémental.</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="95"/>
        <source>Validity falls from {0}% (frame 1) to {1}%: if the valid region changes during the test (cracks, failure), import per-frame masks (REGION OF INTEREST).</source>
        <translation>La validité chute de {0} % (image 1) à {1} % : si la région valide change pendant l'essai (fissures, rupture), importez des masques par image (RÉGION D'INTÉRÊT).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="103"/>
        <source>No valid points in ANY frame — the run produced an empty result. Check ROI, masks and seeding (details above).</source>
        <translation>Aucun point valide dans AUCUNE image — l'exécution a produit un résultat vide. Vérifiez la ROI, les masques et le point de départ (détails ci-dessus).</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="111"/>
        <source>Analysis complete — {0} frames, median validity {1}%, {2} frame(s) below {3}% (see above)</source>
        <translation>Analyse terminée — {0} images, validité médiane {1} %, {2} image(s) sous {3} % (voir ci-dessus)</translation>
    </message>
    <message>
        <location filename="../../gui/panels/run_summary.py" line="124"/>
        <source>Analysis complete — {0} frames, median validity {1}%</source>
        <translation>Analyse terminée — {0} images, validité médiane {1} %</translation>
    </message>
</context>
<context>
    <name>RunWarnings</name>
    <message>
        <location filename="../../gui/warning_text.py" line="24"/>
        <source>No Starting Point placed: frame 1 is seeded by an FFT search (place a point for large first-frame motion)</source>
        <translation>Aucun point de départ placé : l'image 1 est initialisée par une recherche FFT (placez un point si le mouvement de la première image est grand)</translation>
    </message>
    <message>
        <location filename="../../gui/warning_text.py" line="32"/>
        <source>FFT search range reduced from {0} to {1} px to fit the {2} × {3} px images</source>
        <translation>Plage de recherche FFT réduite de {0} à {1} px pour les images de {2} × {3} px</translation>
    </message>
</context>
<context>
    <name>ShortcutsDialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="74"/>
        <source>Keyboard Shortcuts</source>
        <translation>Raccourcis clavier</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="86"/>
        <source>Run the 3D analysis</source>
        <translation>Lancer l'analyse 3D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="87"/>
        <source>Fit the image to the viewport</source>
        <translation>Ajuster l'image à la fenêtre</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="88"/>
        <source>Zoom in / out</source>
        <translation>Zoom avant / arrière</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="89"/>
        <source>Previous / next frame</source>
        <translation>Image précédente / suivante</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="90"/>
        <source>Play / pause (on the canvas: hold to pan)</source>
        <translation>Lecture / pause (sur le canevas : maintenir pour déplacer)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="91"/>
        <source>New project</source>
        <translation>Nouveau projet</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="92"/>
        <source>Open a project</source>
        <translation>Ouvrir un projet</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="93"/>
        <source>Save the project</source>
        <translation>Enregistrer le projet</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="94"/>
        <source>Save the project as…</source>
        <translation>Enregistrer le projet sous…</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="95"/>
        <source>Cancel the active drawing tool</source>
        <translation>Annuler l'outil de dessin actif</translation>
    </message>
</context>
<context>
    <name>StrainFieldSelector3D</name>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="46"/>
        <source>εxx — normal strain along the strain frame&apos;s x axis</source>
        <translation>εxx — déformation normale selon l'axe x du repère de déformation</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="47"/>
        <source>εyy — normal strain along the strain frame&apos;s y axis</source>
        <translation>εyy — déformation normale selon l'axe y du repère de déformation</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="48"/>
        <source>εxy — in-plane shear strain (tensor component)</source>
        <translation>εxy — déformation de cisaillement dans le plan (composante tensorielle)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="49"/>
        <source>ε₁ — major principal strain (largest in-plane eigenvalue)</source>
        <translation>ε₁ — déformation principale majeure (plus grande valeur propre dans le plan)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="50"/>
        <source>ε₂ — minor principal strain (smallest in-plane eigenvalue)</source>
        <translation>ε₂ — déformation principale mineure (plus petite valeur propre dans le plan)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="51"/>
        <source>γ max — maximum shear strain, (ε₁ − ε₂) / 2</source>
        <translation>γ max — cisaillement maximal, (ε₁ − ε₂) / 2</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_field_selector.py" line="52"/>
        <source>von Mises — equivalent strain (plane-stress invariant)</source>
        <translation>von Mises — déformation équivalente (invariant en contraintes planes)</translation>
    </message>
</context>
<context>
    <name>StrainNavigator3D</name>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="52"/>
        <source>Previous frame (←)</source>
        <translation>Image précédente (←)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="59"/>
        <location filename="../../gui/widgets/strain_navigator.py" line="128"/>
        <source>Play animation (Space)</source>
        <translation>Lire l'animation (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="66"/>
        <source>Next frame (→)</source>
        <translation>Image suivante (→)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="75"/>
        <source>Playback speed (frames per second). Default 2 fps.</source>
        <translation>Vitesse de lecture (images par seconde). Par défaut 2 fps.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="79"/>
        <location filename="../../gui/widgets/strain_navigator.py" line="198"/>
        <source>FRAME 0/0</source>
        <translation>IMAGE 0/0</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="181"/>
        <source>Pause animation (Space)</source>
        <translation>Pause (Space)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_navigator.py" line="196"/>
        <source>FRAME {0}/{1}</source>
        <translation>IMAGE {0}/{1}</translation>
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
        <translation>Longueur du côté, en pixels, de la fenêtre carrée autour de chaque nœud utilisée pour ajuster le gradient de déplacement local (la jauge de déformation virtuelle).

• Fenêtre plus grande → déformation plus lisse, résolution spatiale plus faible.
• Fenêtre plus petite → déformation plus nette, plus de bruit.
• Doit couvrir au moins 3×3 nœuds : utilisez ≥ 2 × espacement des nœuds + 1 px.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="89"/>
        <source>Strain window</source>
        <translation>Fenêtre VSG</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="101"/>
        <source>Number of mesh nodes per axis inside the square strain window — the local plane fit uses every valid node in it. The mm size maps the pixel window through the median 3D spacing of adjacent nodes on the reference surface.</source>
        <translation>Nombre de nœuds du maillage par axe dans la fenêtre de déformation carrée — l'ajustement de plan local utilise tous les nœuds valides qu'elle contient. La taille en mm convertit la fenêtre en pixels via la médiane de l'espacement 3D des nœuds adjacents sur la surface de référence.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="119"/>
        <source>Green-Lagrange (default)</source>
        <translation>Green-Lagrange (défaut)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="120"/>
        <source>Infinitesimal</source>
        <translation>Infinitésimal</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="124"/>
        <source>Almansi (Eulerian, true tensor)</source>
        <translation>Almansi (eulérien, tenseur exact)</translation>
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
        <translation>Mesure de déformation finie issue du MÊME ajustement du gradient de
déplacement, dans le même repère tangent :
Green-Lagrange E = ½(FᵀF − I) — déformation finie, configuration de
référence (par défaut).
Infinitesimal e = ½(∇u + ∇uᵀ) — linéarisation des petites déformations.
Almansi (eulérien, tenseur exact) e = ½(I − F⁻ᵀF⁻¹) — le tenseur de
déformation finie EXACT dans la configuration déformée. Ce n'est PAS la
formule « Euler-Almansi » linéarisée par axe de l'app 2D
(1/(1−∂u/∂x)−1, …), qui diffère d'environ 22 % à 10 % de déformation.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="139"/>
        <source>Strain type</source>
        <translation>Type de déformation</translation>
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
        <translation>Masque la déformation peu fiable près des nœuds invalides ou
manquants, où la fenêtre de déformation perd son appui d'un côté et
l'ajustement de plan local devient peu fiable.
Coefficient × rayon de fenêtre = largeur de la bande rognée (en px,
sur la grille de référence).
0,00 = conserver tous les nœuds (aucun rognage) · 0,70 = recommandé ·
1,00 = le plus strict. Le déplacement n'est jamais affecté.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="161"/>
        <source>Trim low-confidence edges</source>
        <translation>Rogner les bords peu fiables</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="188"/>
        <source>Off</source>
        <translation>Désactivé</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="189"/>
        <source>Light (σ = 0.5 × step)</source>
        <translation>Léger (σ = 0,5 × step)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="190"/>
        <source>Medium (σ = 1 × step)</source>
        <translation>Moyen (σ = 1 × step)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="191"/>
        <source>Strong (σ = 2 × step) ⚠</source>
        <translation>Fort (σ = 2 × step) ⚠</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="197"/>
        <source>Gaussian smoothing of the displacement field before the gradient fit.
σ is the kernel width; step = DIC node spacing.
  Light  (0.5 × step): subtle, preserves fine features.
  Medium (1 × step): balanced, for noisy data.
  Strong (2 × step) ⚠: aggressive, may blur real gradients.</source>
        <translation>Lissage gaussien du champ de déplacement avant l'ajustement du gradient.
σ est la largeur du noyau ; step = espacement des nœuds DIC.
  Léger (0,5 × step) : subtil, préserve les détails fins.
  Moyen (1 × step) : équilibré, pour données bruitées.
  Fort (2 × step) ⚠ : agressif, peut estomper les vrais gradients.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="204"/>
        <source>Strain field smoothing</source>
        <translation>Lissage du champ de déformation</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="208"/>
        <source>Surface tangent plane</source>
        <translation>Plan tangent à la surface</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="209"/>
        <source>Left camera frame</source>
        <translation>Repère de la caméra gauche</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="210"/>
        <source>Custom (3 points)</source>
        <translation>Personnalisé (3 points)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="213"/>
        <source>Per-node tangent plane fitted to the reference surface: z is the surface normal pointing toward the camera, x is the left-camera +X projected onto the plane, y = z × x. The right default for curved specimens.</source>
        <translation>Plan tangent ajusté nœud par nœud à la surface de référence : z est la normale à la surface orientée vers la caméra, x la projection du +X de la caméra gauche sur le plan, y = z × x. Le bon choix par défaut pour les éprouvettes courbes.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="219"/>
        <source>Report strain in the fixed left-camera (world) axes. Meaningful for flat specimens aligned with the image plane.</source>
        <translation>Exprimer la déformation dans les axes fixes de la caméra gauche (monde). Pertinent pour les éprouvettes planes alignées avec le plan image.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="223"/>
        <source>A fixed specimen frame built from 3 picked points on the reference image: Origin, a point along +X, and a point on the +Y side.</source>
        <translation>Un repère éprouvette fixe construit à partir de 3 points choisis sur l'image de référence : l'origine, un point le long de +X et un point du côté +Y.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="241"/>
        <source>Coordinate system</source>
        <translation>Système de coordonnées</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="246"/>
        <source>Pick 3 points…</source>
        <translation>Choisir 3 points…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="251"/>
        <source>Click three points on the reference image: the Origin, a point along +X, then a point on the +Y side. Each click snaps to the nearest valid mesh node. Enabled only for Custom (3 points).</source>
        <translation>Cliquez trois points sur l'image de référence : l'origine, un point le long de +X, puis un point du côté +Y. Chaque clic s'accroche au nœud de maillage valide le plus proche. Actif uniquement en « Personnalisé (3 points) ».</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="307"/>
        <source>Trimmed: {0} nodes ({1}%)</source>
        <translation>Rognés : {0} nœuds ({1}%)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="315"/>
        <source>Crack-aware: ROI barrier honored (mesh, strain, render)</source>
        <translation>Sensible aux fissures : barrière ROI respectée (maillage, déformation, rendu)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="405"/>
        <source>Strain window ≈ {0}×{1} nodes</source>
        <translation>Fenêtre VSG ≈ {0}×{1} nœuds</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="409"/>
        <source>≈ {0} × {1} mm</source>
        <translation>≈ {0} × {1} mm</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_param_panel.py" line="419"/>
        <source>⚠ Window radius ({0} px) &lt; node spacing ({1} px); the plane fit needs a 3×3 node gauge. Use ≥ {2} px.</source>
        <translation>⚠ Rayon de fenêtre ({0} px) &lt; espacement des nœuds ({1} px) ; l'ajustement de plan requiert une jauge de 3×3 nœuds. Utilisez ≥ {2} px.</translation>
    </message>
</context>
<context>
    <name>StrainRenderMixin</name>
    <message>
        <location filename="../../gui/strain_canvas.py" line="230"/>
        <source>Could not draw the overlay: {0}</source>
        <translation>Impossible de dessiner la superposition : {0}</translation>
    </message>
</context>
<context>
    <name>StrainVizPanel3D</name>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="35"/>
        <source>Show on deformed frame</source>
        <translation>Afficher sur l'image déformée</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="39"/>
        <source>When checked, overlay results on the deformed (current) frame instead of the reference frame</source>
        <translation>Lorsque cette option est activée, les résultats sont superposés sur l'image déformée (actuelle) au lieu de l'image de référence</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="49"/>
        <source>Colormap for the strain overlay. Default turbo; pick RdBu_r or coolwarm for signed strain centered on zero.</source>
        <translation>Palette de couleurs pour la superposition de déformation. Par défaut turbo ; choisissez RdBu_r ou coolwarm pour une déformation signée centrée sur zéro.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="53"/>
        <source>Colormap</source>
        <translation>Palette</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="55"/>
        <source>Auto range</source>
        <translation>Plage automatique</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="59"/>
        <source>Rescale the color range to each frame&apos;s data range (2–98 percentile of the visible values). Default on; uncheck to type fixed Min/Max bounds that hold across frames.</source>
        <translation>Ajuster la plage de couleurs à la plage de données de chaque image (percentiles 2–98 des valeurs visibles). Activé par défaut ; décochez pour saisir des bornes Min/Max fixes valables pour toutes les images.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="74"/>
        <source>Lower color-range bound (only with Auto range off)</source>
        <translation>Borne inférieure de la plage de couleurs (uniquement avec la plage auto désactivée)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="75"/>
        <source>Upper color-range bound (only with Auto range off)</source>
        <translation>Borne supérieure de la plage de couleurs (uniquement avec la plage auto désactivée)</translation>
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
        <translation>Opacité de la superposition (0 = transparent, 100 = opaque)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_viz_panel.py" line="94"/>
        <source>Opacity</source>
        <translation>Opacité</translation>
    </message>
</context>
<context>
    <name>StrainWindow3D</name>
    <message>
        <location filename="../../gui/strain_window.py" line="111"/>
        <source>Strain Post-Processing</source>
        <translation>Post-traitement de la déformation</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="151"/>
        <source>STRAIN PARAMETERS</source>
        <translation>PARAMÈTRES DE DÉFORMATION</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="161"/>
        <source>Compute Strain</source>
        <translation>Calculer la déformation</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="167"/>
        <source>Export Results</source>
        <translation>Exporter les résultats</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="171"/>
        <location filename="../../gui/strain_window.py" line="680"/>
        <source>Export displacement and strain results to NPZ / MAT / CSV</source>
        <translation>Exporter les résultats de déplacement et de déformation en NPZ / MAT / CSV</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="190"/>
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="192"/>
        <source>Stop the strain computation at the next frame.</source>
        <translation>Arrêter le calcul de la déformation à l'image suivante.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="201"/>
        <source>FIELD</source>
        <translation>CHAMP</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="207"/>
        <source>VISUALIZATION</source>
        <translation>VISUALISATION</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="211"/>
        <source>LOG</source>
        <translation>JOURNAL</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="334"/>
        <source>Computation Running</source>
        <translation>Calcul en cours</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="335"/>
        <source>A strain computation is running — cancel it and close?</source>
        <translation>Un calcul de déformation est en cours — l'annuler et fermer ?</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="340"/>
        <source>Yes</source>
        <translation>Oui</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="341"/>
        <source>No</source>
        <translation>Non</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="401"/>
        <location filename="../../gui/strain_window.py" line="466"/>
        <location filename="../../gui/strain_window.py" line="580"/>
        <source>Strain compute failed: {0}</source>
        <translation>Échec du calcul de déformation : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="413"/>
        <location filename="../../gui/strain_window.py" line="543"/>
        <source>Run 3D analysis first — no results to post-process.</source>
        <translation>Exécutez d'abord l'analyse 3D — aucun résultat à post-traiter.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="416"/>
        <location filename="../../gui/strain_window.py" line="554"/>
        <location filename="../../gui/strain_window.py" line="582"/>
        <source>Click Origin, then +X, then +Y on the image</source>
        <translation>Cliquez sur l'origine, puis +X, puis +Y sur l'image</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="423"/>
        <source>Computing strain…</source>
        <translation>Calcul de la déformation…</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="440"/>
        <source>Cancelling…</source>
        <translation>Annulation…</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="445"/>
        <source>Computing strain… {0}%</source>
        <translation>Calcul de la déformation… {0}%</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="457"/>
        <source>Complete</source>
        <translation>Terminé</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="471"/>
        <source>Strain computation cancelled.</source>
        <translation>Calcul de la déformation annulé.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="476"/>
        <source>Strain computation complete.</source>
        <translation>Calcul de déformation terminé.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="481"/>
        <source>⚠ Params changed -- click Compute Strain</source>
        <translation>⚠ Paramètres modifiés — cliquez sur « Calculer la déformation »</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="565"/>
        <source>No valid point near the click — pick on the result field</source>
        <translation>Aucun point valide près du clic — choisissez sur le champ résultat</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="573"/>
        <location filename="../../gui/strain_window.py" line="590"/>
        <source>Picked {0}/3 points</source>
        <translation>{0}/3 points choisis</translation>
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
        <translation>Lancez d'abord une analyse 3D — la déformation nécessite des résultats de déplacement.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="669"/>
        <source>Pick the 3 specimen-frame points first (Origin, +X, +Y).</source>
        <translation>Choisissez d'abord les 3 points du repère éprouvette (origine, +X, +Y).</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="674"/>
        <source>Compute Green-Lagrange surface strain from the displacement field with the parameters above.</source>
        <translation>Calculer la déformation surfacique de Green-Lagrange à partir du champ de déplacement avec les paramètres ci-dessus.</translation>
    </message>
    <message>
        <location filename="../../gui/strain_window.py" line="684"/>
        <source>Run an analysis first — there are no results yet.</source>
        <translation>Lancez d'abord une analyse — il n'y a pas encore de résultats.</translation>
    </message>
</context>
<context>
    <name>UnitsSection3D</name>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="37"/>
        <source>Display unit for displacement and velocity values (colorbar,
3D scalar bar). Display only — the data and every export stay
in millimetres. Strain is dimensionless and unaffected.</source>
        <translation>Unité d'affichage des valeurs de déplacement et de vitesse (barre de
couleurs, barre scalaire 3D). Affichage uniquement — les données et
tous les exports restent en millimètres. La déformation est
adimensionnelle et non affectée.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="42"/>
        <source>Display unit</source>
        <translation>Unité d'affichage</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="49"/>
        <source>not set (per frame)</source>
        <translation>non défini (par image)</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="54"/>
        <source>Acquisition frame rate. Used only by the Velocity field:
velocity = |D(k) − D(k−1)| × frame rate, shown in the
display unit per second. Leave it at &apos;not set&apos; to see the
velocity per frame.</source>
        <translation>Fréquence d'acquisition. Utilisée seulement par le champ Vitesse :
vitesse = |D(k) − D(k−1)| × fréquence, affichée dans l'unité
d'affichage par seconde. Laissez « non défini » pour voir la
vitesse par image.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/units_section.py" line="60"/>
        <source>Frame rate</source>
        <translation>Fréquence d'images</translation>
    </message>
</context>
<context>
    <name>View3D</name>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="129"/>
        <source>3D view — run an analysis to see the reconstructed surface.</source>
        <translation>Vue 3D — lancez une analyse pour voir la surface reconstruite.</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="170"/>
        <location filename="../../gui/widgets/view3d.py" line="259"/>
        <source>3D view unavailable: {0}</source>
        <translation>Vue 3D indisponible : {0}</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="232"/>
        <source>Starting the 3D view…</source>
        <translation>Démarrage de la vue 3D…</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/view3d.py" line="264"/>
        <source>No valid 3D points in this frame — nothing to display.</source>
        <translation>Aucun point 3D valide dans cette image — rien à afficher.</translation>
    </message>
</context>
<context>
    <name>View3DTab</name>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="72"/>
        <source>Field</source>
        <translation>Champ</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="84"/>
        <source>Colormap</source>
        <translation>Palette</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="93"/>
        <source>Resolution</source>
        <translation>Résolution</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="106"/>
        <source>Auto range</source>
        <translation>Plage automatique</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="109"/>
        <source>Like the 3D view: each frame&apos;s 2–98 percentile of the values inside the ROI. Untick to use a fixed Min/Max for every frame.</source>
        <translation>Comme la vue 3D : pour chaque image, les percentiles 2–98 des valeurs dans la ROI. Décochez pour utiliser un Min/Max fixe pour toutes les images.</translation>
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
        <translation>Séquence d'images</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="138"/>
        <source>Per-frame image sequence (PNG)</source>
        <translation>Séquence d'images (PNG, une par image)</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="143"/>
        <source>Animation</source>
        <translation>Animation</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="150"/>
        <source>Frames per second</source>
        <translation>Images par seconde</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="157"/>
        <source>Frame step</source>
        <translation>Pas d'image</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="171"/>
        <source>Turntable</source>
        <translation>Rotation orbitale</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="176"/>
        <source>Turntable (360° orbit at frame {0})</source>
        <translation>Rotation orbitale (360° à l'image {0})</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="179"/>
        <source>Orbit frames</source>
        <translation>Images d'orbite</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="204"/>
        <source>Export 3D View</source>
        <translation>Exporter la vue 3D</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="262"/>
        <source>GIF timing has 1/100 s steps: {0} fps will play at {1} fps. Choose MP4 for faster playback.</source>
        <translation>La temporisation GIF a des pas de 1/100 s : {0} fps seront lus à {1} fps. Choisissez MP4 pour une lecture plus rapide.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="275"/>
        <source>Choose an output folder first.</source>
        <translation>Choisissez d'abord un dossier de sortie.</translation>
    </message>
    <message>
        <location filename="../../gui/dialogs/export_tabs/view3d_tab.py" line="281"/>
        <source>Nothing selected to export.</source>
        <translation>Rien à exporter n'est sélectionné.</translation>
    </message>
</context>
<context>
    <name>ZoomBar</name>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="60"/>
        <source>Fit</source>
        <translation>Ajuster</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="61"/>
        <source>Fit image to viewport</source>
        <translation>Ajuster l'image à la vue</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="68"/>
        <source>Current zoom — click to reset to 100% (1:1 pixels).
Wheel: zoom · Right/middle drag: pan · Space: pan mode</source>
        <translation>Zoom actuel — cliquez pour revenir à 100 % (pixels 1:1).
Molette : zoom · Glisser droit/central : déplacement · Espace : mode déplacement</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="74"/>
        <source>Zoom in</source>
        <translation>Zoom avant</translation>
    </message>
    <message>
        <location filename="../../gui/widgets/strain_support.py" line="78"/>
        <source>Zoom out</source>
        <translation>Zoom arrière</translation>
    </message>
</context>
<context>
    <name>dialog</name>
    <message>
        <location filename="../../gui/dialogs/about_dialog.py" line="24"/>
        <source>Close</source>
        <translation>Fermer</translation>
    </message>
</context>
</TS>
