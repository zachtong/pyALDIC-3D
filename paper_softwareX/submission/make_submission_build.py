"""Build the SoftwareX submission files from the working pyALDIC-3D manuscript.

Mirrors the 2D repo's ``paper_softwareX/submission/make_submission_build.py``.
It produces, in ``submission/build/``:

  * ``draft_softwareX_3D.pdf`` -- the manuscript PDF to upload, with every
    ``\\jy{}`` / ``\\zt{}`` review note hidden (the macros are redefined to
    swallow their argument in the BUILD COPY only; the working ``.tex`` is never
    modified, so the marked-up review copy is preserved).
  * ``pyALDIC-3D_softwareX_latex_source.zip`` -- the LaTeX source archive to
    upload (clean ``.tex`` + ``.bbl`` + ``reference.bib`` + the figure files).

Two guards specific to this manuscript, because both are currently unmet:

  1. **Placeholder figures.** Every ``figs/*.pdf`` is a grey placeholder emitted
     by ``repro/make_placeholder_figs.py``. The build REFUSES to run while any
     included figure still carries the ``PLACEHOLDER`` marker, unless you pass
     ``--allow-placeholders`` (useful for layout checks, never for submission).
  2. **Unresolved TODO markers.** The build refuses if an unresolved ``\\todo{}``
     macro call is still present in the manuscript body.

It also reports the figure count against the SoftwareX limit of six.

Usage (from anywhere)::

    python paper_softwareX/submission/make_submission_build.py
    python paper_softwareX/submission/make_submission_build.py --allow-placeholders

Requires ``pdflatex`` and ``bibtex`` on PATH. Optionally uses PyMuPDF (``fitz``)
to double-check that no review marks survived.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent          # paper_softwareX/submission
PAPER = HERE.parent                             # paper_softwareX
TEX_NAME = "draft_softwareX_3D"
TEX = PAPER / f"{TEX_NAME}.tex"
BIB = PAPER / "reference.bib"
FIGDIR = PAPER / "figs"
BUILD = HERE / "build"
ZIP_NAME = "pyALDIC-3D_softwareX_latex_source.zip"

#: SoftwareX Guide for Authors: an Original Software Publication may carry at
#: most this many figures.
MAX_FIGURES = 6

HIDE_MARKS = (
    "% --- submission build: hide JY/ZT review marks ---\n"
    "\\renewcommand{\\jy}[1]{}\n"
    "\\renewcommand{\\zt}[1]{}\n"
)

INCLUDE_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
TODO_RE = re.compile(r"\\todo\{")


def run(cmd: list[str]) -> None:
    print("  $", " ".join(cmd))
    res = subprocess.run(cmd, cwd=BUILD, capture_output=True, text=True)
    if res.returncode != 0:
        tail = "\n".join((res.stdout or res.stderr).splitlines()[-25:])
        sys.exit(f"\nCommand failed ({res.returncode}):\n{tail}")


def included_figures(src: str) -> list[str]:
    """Figure paths referenced by \\includegraphics, in document order."""
    return [m.group(1).strip() for m in INCLUDE_RE.finditer(src)]


def is_placeholder(path: Path) -> bool:
    """True when the PDF was emitted by repro/make_placeholder_figs.py."""
    try:
        head = path.read_bytes()
    except OSError:
        return False
    return b"PLACEHOLDER" in head[:200_000]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="build even though figures are still placeholders (layout checks only)",
    )
    args = ap.parse_args()

    if not TEX.exists():
        sys.exit(f"Manuscript not found: {TEX}")
    src = TEX.read_text(encoding="utf-8")

    # 0. pre-flight guards -------------------------------------------------
    todos = len(TODO_RE.findall(src)) - src.count("\\newcommand{\\todo}")
    if todos > 0:
        sys.exit(f"{todos} unresolved \\todo{{}} marker(s) in the manuscript -- resolve them first.")

    figures = included_figures(src)
    if not figures:
        sys.exit("No \\includegraphics found -- is this the right manuscript?")
    print(f"Figures referenced: {len(figures)}")
    if len(figures) > MAX_FIGURES:
        print(
            f"  ! SoftwareX allows at most {MAX_FIGURES} figures; this manuscript has "
            f"{len(figures)}. See figs/README.md for the planned merge."
        )

    missing = [f for f in figures if not (PAPER / f).exists()]
    if missing:
        sys.exit("Missing figure file(s):\n  " + "\n  ".join(missing))

    placeholders = [f for f in figures if is_placeholder(PAPER / f)]
    if placeholders:
        msg = "Placeholder figure(s) still in use:\n  " + "\n  ".join(placeholders)
        if not args.allow_placeholders:
            sys.exit(
                msg
                + "\n\nReplace them (see figs/README.md), or pass --allow-placeholders "
                "for a layout-only build. NEVER submit a build with placeholders."
            )
        print("  ! " + msg.replace("\n  ", "\n    "))

    # 1. fresh build dir with the review marks hidden ----------------------
    if BUILD.exists():
        shutil.rmtree(BUILD)
    (BUILD / "figs").mkdir(parents=True)

    if "\\begin{document}" not in src:
        sys.exit("Could not find \\begin{document} to insert the mark-hiding block.")
    if "\\newcommand{\\jy}" not in src or "\\newcommand{\\zt}" not in src:
        print("  ! warning: \\jy/\\zt \\newcommand not found; marks may already be gone.")
    clean = src.replace("\\begin{document}", HIDE_MARKS + "\\begin{document}", 1)
    (BUILD / f"{TEX_NAME}.tex").write_text(clean, encoding="utf-8")

    # 2. copy bibliography and every referenced figure ---------------------
    shutil.copy2(BIB, BUILD / BIB.name)
    for fig in figures:
        dest = BUILD / fig
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PAPER / fig, dest)

    # 3. compile: pdflatex, bibtex, pdflatex x2 ----------------------------
    print("Compiling submission PDF...")
    run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"{TEX_NAME}.tex"])
    run(["bibtex", TEX_NAME])
    run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"{TEX_NAME}.tex"])
    run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"{TEX_NAME}.tex"])

    pdf = BUILD / f"{TEX_NAME}.pdf"
    if not pdf.exists():
        sys.exit("Compilation produced no PDF.")

    # 4. best-effort check that no review marks survived -------------------
    marks_ok = None
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf)
        text = "".join(page.get_text() for page in doc)
        hits = text.count("[[JY:") + text.count("[[ZT:") + text.count("[TODO:")
        marks_ok = hits == 0
        print(f"Review-mark check: {'CLEAN' if marks_ok else f'FOUND {hits} mark(s)!'}")
    except Exception:
        print(
            "Review-mark check: (install PyMuPDF for an automatic check) -- please "
            "verify visually that no [[JY:]]/[[ZT:]]/[TODO:] text appears."
        )

    # 5. zip the LaTeX source ---------------------------------------------
    zip_path = BUILD / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(BUILD / f"{TEX_NAME}.tex", f"{TEX_NAME}.tex")
        z.write(BUILD / f"{TEX_NAME}.bbl", f"{TEX_NAME}.bbl")
        z.write(BUILD / BIB.name, BIB.name)
        for fig in figures:
            z.write(BUILD / fig, fig)

    print("\nDone.")
    print(f"  Manuscript PDF : {pdf}")
    print(f"  Source zip     : {zip_path}")
    if placeholders:
        print("  !! Built WITH placeholder figures -- layout check only, do NOT upload.")
    if marks_ok is False:
        print("  !! Review marks detected in the PDF -- do NOT upload; investigate.")


if __name__ == "__main__":
    main()
