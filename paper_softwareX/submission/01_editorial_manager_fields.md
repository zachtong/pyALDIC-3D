# Editorial Manager — copy-paste field sheet (SoftwareX)

Submission portal: <https://www.editorialmanager.com/softx>
Corresponding / submitting author: **Jin Yang** (jin.yang@austin.utexas.edu)

Paste each block into the matching Editorial Manager (EM) field. Everything
below is taken verbatim from the manuscript so the system record and the PDF
agree.

---

## 1. Article type

**Original Software Publication**
(Choose this at the "Article Type" step. *Not* "Software Update" — that is only
for software already published in SoftwareX. Note that although the companion
2D manuscript is under review elsewhere, pyALDIC-3D is an independent software
contribution with its own repository, PyPI distribution and Zenodo DOI, so this
is an Original Software Publication, not an update to it.)

## 2. Title

```
pyALDIC-3D: An Open-Source, GUI-Based Stereo Digital Image Correlation Application with Built-In Calibration, Crack-Aware Surface Strain and Independent Result Verification
```

## 3. Abstract  (≈115 words; limit is 250)

```
We present pyALDIC-3D, an open-source, cross-platform desktop application for stereo digital image correlation that covers the whole measurement chain - camera calibration, stereo and temporal correspondence, triangulation and finite-strain surface analysis - in a single tool. It is the first implementation of the Augmented Lagrangian DIC formulation for stereo outside MATLAB, and adds three capabilities rarely found together: quality-controlled built-in calibration; crack-aware strain, which measures discontinuous fields instead of smoothing across them; and an independent re-verification of every shipped displacement that exposes silent solver failures. Agreement with the published MATLAB reference implementation is 1.3/1.0/6.0 um in U/V/W. pyALDIC-3D is BSD-3-Clause licensed and openly available at https://github.com/zachtong/pyALDIC-3D.
```

## 4. Keywords  (6; enter one per keyword box)

```
stereo digital image correlation
3D-DIC
camera calibration
discontinuous deformation
surface strain
open-source scientific software
```

## 5. Authors  (enter in this order; mark author 2 as corresponding)

| # | Given name | Family name | Email | Affiliation(s) | ORCID | Corresponding |
|---|------------|-------------|-------|----------------|-------|---------------|
| 1 | Zixiang | Tong | zachtong@utexas.edu | A | 0009-0008-6807-0757 | no |
| 2 | Jin | Yang | jin.yang@austin.utexas.edu | A, B | — | **YES** |

**Affiliation A:** Department of Aerospace Engineering and Engineering Mechanics, The University of Texas at Austin, Austin, TX 78712, USA
**Affiliation B:** Texas Materials Institute, The University of Texas at Austin, Austin, TX 78712, USA

> Corresponding-author contact (EM requires full details): Jin Yang,
> jin.yang@austin.utexas.edu, Department of Aerospace Engineering and
> Engineering Mechanics, The University of Texas at Austin, Austin, TX 78712,
> USA. Phone: __________ (JY to fill).

## 6. CRediT author-contribution roles  (EM has a per-author CRediT step)

- **Zixiang Tong:** Conceptualization; Methodology; Software; Validation; Formal analysis; Investigation; Data curation; Visualization; Writing – original draft; Writing – review & editing.
- **Jin Yang:** Conceptualization; Methodology; Supervision; Resources; Funding acquisition; Project administration; Writing – review & editing.

## 7. Funding  (EM Funder-Registry step + the funding statement)

Funders and grant numbers to enter:

- **U.S. National Science Foundation (NSF)** — grant numbers **2232428, 2441460, 2452029**
- **Semiconductor Research Corporation (SRC)** — Pilot Seed Gift (no grant number)

Statement (paste if a free-text funding box is offered):

```
This work was supported by the U.S. National Science Foundation [grant numbers 2232428, 2441460, 2452029] and the Semiconductor Research Corporation (Pilot Seed Gift). Z. Tong acknowledges the University Graduate Continuing Fellowship, the Graduate Excellence Fellowship, and the Professional Development Award from the University of Texas at Austin Cockrell School of Engineering.
```

## 8. Declaration of competing interests  (declarations tool + uploaded Word doc)

```
The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.
```

(Also provided as `02_declaration_of_competing_interest.txt` → save as .docx and upload.)

## 9. Data availability statement  (EM data step)

```
Runnable worked examples, their configuration files and the scripts that regenerate every reported figure are distributed with the source repository and archived on Zenodo. The Stereo-DIC Challenge and DIC Challenge 2.0 materials used for validation are distributed by the International Digital Image Correlation Society. Experimental images acquired by the authors are released under the same license as the code.
```

## 10. Declaration of generative AI  (EM may ask a yes/no + statement)

Answer: **Yes**, AI-assisted tools were used; the statement below is also
printed in the manuscript (section before the references):

```
During the preparation of this work the authors used Anthropic Claude to polish manuscript text, to generate schematic explanatory figures via matplotlib code, and to format LaTeX tables. After using this tool, the authors reviewed and edited the content as needed and take full responsibility for the content of the publication.
```

## 11. Software / code details (asked in the OSP workflow; also in the metadata tables)

- Repository (open access, GitHub): `https://github.com/zachtong/pyALDIC-3D`
- Executable / PyPI (v1.1.0): `https://pypi.org/project/al-dic-3d/1.1.0/` (`pip install al-dic-3d`)
- Standalone Windows installer: GitHub Releases page (no Python required)
- Permanent archive (Zenodo concept DOI): `https://doi.org/10.5281/zenodo.21696564`
- License: **BSD 3-Clause** (OSI-approved)
- Software version described: **v1.1.0**
- User manual: `https://github.com/zachtong/pyALDIC-3D/tree/main/docs/user-guide`
- README.md + LICENSE + CITATION.cff present at repo root; source under `src/`. ✓

## 12. Suggested reviewers  (optional)

Left to JY. Useful expertise areas: stereo-DIC and photogrammetric calibration,
the iDICs / SEM DIC Challenge community, and open-source scientific software
(SoftwareX / JOSS reviewers). EM also lets you add opposed reviewers.

## 13. Related submissions to disclose

The companion 2D manuscript (pyALDIC, preprint arXiv:2607.22755) is under
review. pyALDIC-3D is an **independent** software contribution — separate
repository, separate PyPI distribution (`al-dic-3d`), separate project format
(`.aldic3d`), separate Zenodo concept DOI — and the 2D platform is consumed as
a pinned read-only library and cited as prior art. Disclose the relationship in
the cover letter (already done) if EM asks about related work.

## 14. Preprint on SSRN  (EM asks yes/no)

Optional, no effect on the editorial process. JY's call — a preprint gives an
early DOI. A Zenodo software archive exists regardless.
