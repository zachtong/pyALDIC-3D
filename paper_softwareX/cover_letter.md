# Cover Letter — pyALDIC-3D submission to SoftwareX

**To:** The Editors-in-Chief, *SoftwareX*
**From:** Zixiang Tong (first author) and Jin Yang (corresponding author)
**Date:** [to be filled at submission]

---

Dear Editors,

We are pleased to submit our manuscript titled **"pyALDIC-3D: An Open-Source, GUI-Based Stereo Digital Image Correlation Application with Built-In Calibration, Crack-Aware Surface Strain and Independent Result Verification"** for consideration as an Original Software Publication in *SoftwareX*.

**Software summary.** pyALDIC-3D is an open-source, cross-platform desktop application for stereo (two-camera) Digital Image Correlation that spans the entire measurement chain — camera calibration, stereo and temporal correspondence, DLT triangulation, and finite-strain surface analysis — in a single tool. It is the first implementation of the Augmented Lagrangian (local–global) DIC formulation of Yang & Bhattacharya (Experimental Mechanics, 2019) for stereo outside MATLAB, and contributes four things beyond that algorithmic base:

1. **A complete, accessible stereo pipeline.** Calibration through 3D strain in one BSD-3-Clause, pip-installable application (plus a one-click Windows installer for users with no Python, and a headless TOML-driven CLI), localised in eight languages. Calibration is performed *inside* the tool — four board families including a coded circular-target detector developed for this work, six third-party calibration import formats, robust bundle adjustment, and quantitative quality control with an independent metric-scale verification.
2. **Crack-aware stereo DIC.** A thin barrier cut into the region of interest propagates through the whole chain: it cuts the correlation mesh, is carried into the second camera through the frame-1 stereo correspondence, excludes cross-barrier neighbours from the strain plane fit, and blanks the rendering — so a discontinuous field is *measured* rather than smoothed across.
3. **Verification by construction.** Every shipped cumulative displacement is re-verified against the reference frame by an independent zero-normalised correlation criterion that the solver never optimised, and every discarded point is counted and reported. We argue in the manuscript that this is a methodological point about trustworthy full-field measurement software, not merely a feature: conventional defences (correlation residual, convergence flag, finiteness) are all statements the solver makes about itself, and we show they miss real, silent failures.
4. **Engineering for real experimental campaigns.** Millimetre-native output, lazy image streaming that holds a 150-frame × 12 Mpx run to 5.68 GB of resident memory, partial results retained on cancellation, single-file session persistence, and Numba-accelerated kernels.

**Fit with *SoftwareX* scope.** *SoftwareX* publishes scientific software that solves a defined problem and is reusable by the community. pyALDIC-3D matches this scope closely:

1. **Reproducibility and access.** Stereo-DIC has in practice been gated behind either a commercial licence or a MATLAB licence plus a chain of separate tools. pyALDIC-3D removes both barriers with a single-command, cross-platform, open-source install.
2. **Community standards alignment.** The author team co-edited the iDICs *Good Practices Guide for Digital Image Correlation* (1st ed. 2018; 2nd ed. 2025). Parameter naming, ROI conventions, calibration QC reporting and strain-gauge terminology follow those recommendations, including the guide's position that a low reprojection residual is necessary but not sufficient — hence the independent metric-scale verification in the calibrator.
3. **Validation depth.** The manuscript reports agreement with the published MATLAB 3D-Stereo-ALDIC reference implementation on Stereo-DIC Challenge Sample 3 (median |difference| 1.3 / 1.0 / 6.0 µm in U / V / W, regression slopes ≈ 1.0), plus community benchmarks (Stereo-DIC Challenge 1.0 exact-truth sets recovered to 0.1–0.3 µm; DIC Challenge 2.0 Task 1 agreeing with DICe to 0.003–0.015 px with axial strain 0.269 % against the published 0.26 % anchor) and calibration validated against a physical coded target (baseline within +0.06 % of an independent DICe calibration; 7 mm board pitch recovered as 7.0005 mm).
4. **Engineering completeness.** 687 unit and integration tests run in continuous integration across three operating systems and two Python versions; the package ships a 14-chapter user guide, a runnable quickstart dataset, and a permanent Zenodo archive.

**Relationship to prior work — stated explicitly.** The AL-DIC algorithm is prior work (Yang & Bhattacharya, 2019), as is its adaptive-mesh treatment of complex geometry (Yang et al., 2022) and its stereo extension, which was developed and validated in MATLAB by Tong et al. (Experimental Mechanics, 2025). pyALDIC-3D is a from-scratch Python application that takes that work as its mathematical reference and contributes the calibration stage, the crack-aware chain, the verification gate, the interface and the distribution. The manuscript is careful to distinguish algorithmic novelty (which belongs to the prior papers) from the implementation, accessibility and methodological contributions that are the substance of this submission.

**Relationship to our 2D SoftwareX submission.** A companion manuscript describing the pyALDIC 2D platform is under review (preprint arXiv:2607.22755). pyALDIC-3D is an **independent** software contribution, not a supplement: it is a separate repository, a separate PyPI distribution (`al-dic-3d`), a separate project file format (`.aldic3d`), and it has its own Zenodo concept DOI. The 2D platform is consumed as a pinned, read-only library and is cited as prior art. The present manuscript stands alone and can be reviewed without reference to the 2D one.

**Code archive.** The version described in the manuscript, v1.1.0, is permanently archived on Zenodo (concept DOI 10.5281/zenodo.21696564, which always resolves to the latest archived version) and published on PyPI as `al-dic-3d`. The repository (<https://github.com/zachtong/pyALDIC-3D>) is public, BSD-3-Clause, with README, LICENSE, `src/`, tests, and a full user guide.

**Author contributions and conflict of interest.** Z. Tong is the principal developer and wrote the manuscript. J. Yang is the project lead, supervised the algorithmic design, and co-authored the AL-DIC method on which the software builds. There are no conflicts of interest, and no significant financial support for this work that could have influenced its outcome.

**Suggested reviewers.** We would be grateful if you could consider reviewers with expertise in stereo digital image correlation, photogrammetric calibration, and open-source scientific software. We are happy to supply candidates upon request and to note any conflicts of interest.

We confirm that this work has not been published previously, is not under consideration elsewhere, and that all listed authors have approved the submission.

Thank you for considering this manuscript. We look forward to your editorial decision.

Sincerely,

**Zixiang Tong** (first author)
Department of Aerospace Engineering and Engineering Mechanics
The University of Texas at Austin
ORCID: 0009-0008-6807-0757
Email: zachtong@utexas.edu

**Jin Yang** (corresponding author)
Department of Aerospace Engineering and Engineering Mechanics
Texas Materials Institute
The University of Texas at Austin
Email: jin.yang@austin.utexas.edu
