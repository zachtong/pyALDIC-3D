"""Generate reports/phase0_scaffold.pdf — the Phase 0 (scaffold) visual report.

Per CLAUDE.md, every phase ends with a matplotlib ``PdfPages`` report under
``reports/`` (gitignored). This one documents the scaffold AND self-verifies the
Phase 0 gate live (import / CLI --help / pytest) so the PDF cannot claim green
without proof.

Run (after ``pip install -e ".[dev]"``):
    python tools/phase0_report.py
"""

from __future__ import annotations

import datetime
import importlib
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "reports" / "phase0_scaffold.pdf"

INK = "#1a1a2e"
GREEN = "#1b7a3d"
RED = "#b02a2a"
ACCENT = "#2d5f8a"
MUTED = "#666666"

SUBMODULES = [
    ("project", "StereoProject + .aldic3d session envelope", "data", "P4-5"),
    ("calibration", "CameraIntrinsics/StereoRig, 6 importers, undistort", "Qt-free", "P1"),
    ("sequence", "StereoSequence: dual FrameProvider + masks + pairing", "Qt-free", "P1"),
    ("matching", "CorrespondenceStrategy protocol + strategies", "Qt-free", "P1-2"),
    ("reconstruct", "DLT triangulation, reproj error, D = P^k - P^1", "Qt-free", "P1"),
    ("strain3d", "plane-fit surface strain, 3D smooth/outlier", "Qt-free", "P3"),
    ("export", "PLY/VTU/CSV/MAT/video (reuse 2D primitives)", "Qt-free", "P5"),
    ("viz3d", "pyvista/pyvistaqt scene (behind [viz3d] extra)", "GUI", "P4"),
    ("gui", "MainWindow/AppState3D/controllers", "GUI", "P4"),
    ("i18n", "own .ts/.qm; dual QTranslator (al-dic + al-dic-3d)", "GUI", "P4"),
]

LAYOUT_TREE = """\
pyALDIC-3D/
└── src/al_dic_3d/
    ├── __init__.py      # __version__ (hatchling dynamic-version source)
    ├── __main__.py      # python -m al_dic_3d
    ├── cli.py           # console script: al-dic-3d
    ├── py.typed
    ├── project/         calibration/   sequence/    matching/
    ├── reconstruct/     strain3d/      export/      viz3d/
    └── gui/             i18n/
"""


def run_gate() -> list[tuple[str, bool, str]]:
    """Execute the three Phase 0 gate checks live. Returns (label, ok, detail)."""
    results: list[tuple[str, bool, str]] = []

    # 1. import al_dic_3d + every submodule
    try:
        pkg = importlib.import_module("al_dic_3d")
        for name, *_ in SUBMODULES:
            importlib.import_module(f"al_dic_3d.{name}")
        results.append(("import al_dic_3d (+ 10 modules)", True, f"v{pkg.__version__}"))
    except Exception as exc:  # noqa: BLE001
        results.append(("import al_dic_3d (+ 10 modules)", False, str(exc)))

    # 2. al-dic-3d --help  (via the real module entry point)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "al_dic_3d", "--help"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        ok = proc.returncode == 0 and "al-dic-3d" in proc.stdout
        results.append(("al-dic-3d --help", ok, f"exit {proc.returncode}"))
    except Exception as exc:  # noqa: BLE001
        results.append(("al-dic-3d --help", False, str(exc)))

    # 3. pytest
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-m", "not perf"],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
            cwd=str(REPO),
        )
        tail = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        summary = tail[-1] if tail else "(no output)"
        results.append(("pytest test suite", proc.returncode == 0, summary[:60]))
    except Exception as exc:  # noqa: BLE001
        results.append(("pytest test suite", False, str(exc)))

    return results


def _new_page(pdf: PdfPages):
    fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    return fig, ax


def _header(ax, title: str, subtitle: str = "") -> None:
    ax.add_patch(plt.Rectangle((0, 0.935), 1, 0.065, color=ACCENT, transform=ax.transAxes))
    ax.text(
        0.06,
        0.958,
        title,
        fontsize=17,
        fontweight="bold",
        color="white",
        transform=ax.transAxes,
        va="center",
    )
    if subtitle:
        ax.text(
            0.94,
            0.958,
            subtitle,
            fontsize=9,
            color="white",
            alpha=0.85,
            transform=ax.transAxes,
            va="center",
            ha="right",
        )


def page_title(pdf: PdfPages, gate: list[tuple[str, bool, str]], today: str) -> None:
    fig, ax = _new_page(pdf)
    ax.text(
        0.06, 0.86, "pyALDIC-3D", fontsize=34, fontweight="bold", color=INK, transform=ax.transAxes
    )
    ax.text(
        0.06, 0.815, "Phase 0 — Project Scaffold", fontsize=18, color=ACCENT, transform=ax.transAxes
    )
    ax.text(0.06, 0.785, f"Generated: {today}", fontsize=10, color=MUTED, transform=ax.transAxes)

    summary = (
        "Independent stereo-DIC application scaffolded on top of the pyALDIC-2D\n"
        "platform, consumed as a pinned, read-only library (al-dic==0.6.*). This\n"
        "phase ships structure only — no stereo/temporal algorithms. Deliverables:\n"
        "src-layout package (10 §B.1 modules), pyproject (dist al-dic-3d, CLI\n"
        "al-dic-3d), coupling ledger (docs/DEPENDS_ON_2D.md), pytest + ruff +\n"
        "pre-commit + CI, and git init."
    )
    ax.text(
        0.06,
        0.70,
        summary,
        fontsize=11,
        color=INK,
        transform=ax.transAxes,
        va="top",
        linespacing=1.6,
    )

    all_ok = all(ok for _, ok, _ in gate)
    banner = GREEN if all_ok else RED
    verdict = "GATE: PASS" if all_ok else "GATE: FAIL"
    ax.add_patch(
        plt.Rectangle((0.06, 0.46), 0.88, 0.09, color=banner, alpha=0.12, transform=ax.transAxes)
    )
    ax.text(
        0.10,
        0.505,
        verdict,
        fontsize=20,
        fontweight="bold",
        color=banner,
        transform=ax.transAxes,
        va="center",
    )
    ax.text(
        0.10,
        0.475,
        "import works · al-dic-3d --help runs · test suite green",
        fontsize=10,
        color=MUTED,
        transform=ax.transAxes,
        va="center",
    )

    y = 0.40
    for label, ok, detail in gate:
        mark, col = ("PASS", GREEN) if ok else ("FAIL", RED)
        ax.text(
            0.10,
            y,
            mark,
            fontsize=11,
            fontweight="bold",
            color=col,
            transform=ax.transAxes,
            family="monospace",
        )
        ax.text(0.22, y, label, fontsize=11, color=INK, transform=ax.transAxes)
        ax.text(0.94, y, detail, fontsize=9, color=MUTED, transform=ax.transAxes, ha="right")
        y -= 0.045

    ax.text(
        0.06,
        0.08,
        "docs/architecture/ (start at 00_INDEX.md) is the binding "
        "baseline; on conflict the arch docs win.",
        fontsize=8.5,
        color=MUTED,
        transform=ax.transAxes,
        style="italic",
    )
    pdf.savefig(fig)
    plt.close(fig)


def page_layout(pdf: PdfPages) -> None:
    fig, ax = _new_page(pdf)
    _header(ax, "Package layout", "src/al_dic_3d — 01 §B.1")
    ax.text(
        0.06,
        0.90,
        LAYOUT_TREE,
        fontsize=9.5,
        color=INK,
        transform=ax.transAxes,
        va="top",
        family="monospace",
        linespacing=1.5,
    )

    ax.text(
        0.06,
        0.66,
        "Module responsibilities",
        fontsize=13,
        fontweight="bold",
        color=ACCENT,
        transform=ax.transAxes,
    )
    rows = [[n, resp, layer, ph] for n, resp, layer, ph in SUBMODULES]
    tbl = ax.table(
        cellText=rows,
        colLabels=["module", "responsibility", "layer", "phase"],
        colWidths=[0.14, 0.58, 0.13, 0.10],
        cellLoc="left",
        loc="upper left",
        bbox=[0.06, 0.10, 0.88, 0.52],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.2)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#d9d9d9")
        if r == 0:
            cell.set_facecolor(ACCENT)
            cell.set_text_props(color="white", fontweight="bold")
        else:
            layer = rows[r - 1][2]
            if c == 2 and layer == "Qt-free":
                cell.set_text_props(color=GREEN, fontweight="bold")
    pdf.savefig(fig)
    plt.close(fig)


def page_deps(pdf: PdfPages) -> None:
    fig, ax = _new_page(pdf)
    _header(ax, "Dependencies & toolchain")

    deps = [
        ("numpy>=1.24", "arrays"),
        ("scipy>=1.10", "interpolation / linear algebra"),
        ("opencv-python-headless>=4.7", "image ops (headless; no display)"),
        ("al-dic==0.6.*", "pinned read-only 2D engine (D11)"),
        ("[viz3d] pyvista, pyvistaqt", "optional 3D visualization (lazy)"),
        ("[dev] pytest, ruff, pre-commit", "test + lint + hooks"),
    ]
    ax.text(
        0.06,
        0.90,
        "Runtime & optional dependencies",
        fontsize=13,
        fontweight="bold",
        color=ACCENT,
        transform=ax.transAxes,
    )
    y = 0.855
    for pkg, why in deps:
        ax.text(0.08, y, pkg, fontsize=10, color=INK, transform=ax.transAxes, family="monospace")
        ax.text(0.56, y, why, fontsize=9.5, color=MUTED, transform=ax.transAxes)
        y -= 0.042

    ax.text(
        0.06,
        0.55,
        "How al-dic==0.6.* is satisfied",
        fontsize=13,
        fontweight="bold",
        color=ACCENT,
        transform=ax.transAxes,
    )
    model = (
        "CI / users   ->  resolves from PyPI (al-dic 0.6.0 is published)\n"
        "development  ->  pip install -e ../pyALDIC   (sibling repo, editable,\n"
        "                 reports 0.6.0 -> satisfies the same ==0.6.* pin)\n\n"
        "Either way the 2D repo is never modified. docs/DEPENDS_ON_2D.md records\n"
        "exactly which al_dic symbols 3D imports (empty at Phase 0)."
    )
    ax.text(
        0.08,
        0.50,
        model,
        fontsize=9.5,
        color=INK,
        transform=ax.transAxes,
        va="top",
        family="monospace",
        linespacing=1.6,
    )

    ax.text(
        0.06,
        0.24,
        "Quality gates (CI: .github/workflows/ci.yml)",
        fontsize=13,
        fontweight="bold",
        color=ACCENT,
        transform=ax.transAxes,
    )
    gates = (
        "· CI (mirrors 2D): Python matrix 3.10 / 3.11 / 3.12\n"
        "· CI gate: import al_dic_3d  ·  al-dic-3d --help  ·  pytest\n"
        "· pre-commit (pinned): ruff lint + format + hygiene hooks\n"
        "  (lint stays in pre-commit, not CI; i18n hooks deferred to P4)"
    )
    ax.text(
        0.08,
        0.195,
        gates,
        fontsize=9.5,
        color=INK,
        transform=ax.transAxes,
        va="top",
        linespacing=1.7,
    )
    pdf.savefig(fig)
    plt.close(fig)


def page_status(pdf: PdfPages, gate: list[tuple[str, bool, str]]) -> None:
    fig, ax = _new_page(pdf)
    _header(ax, "Gate verification & next steps")

    ax.text(
        0.06,
        0.90,
        "Live gate results",
        fontsize=13,
        fontweight="bold",
        color=ACCENT,
        transform=ax.transAxes,
    )
    y = 0.855
    for label, ok, detail in gate:
        mark, col = ("PASS", GREEN) if ok else ("FAIL", RED)
        ax.text(
            0.08,
            y,
            mark,
            fontsize=11,
            fontweight="bold",
            color=col,
            transform=ax.transAxes,
            family="monospace",
        )
        ax.text(0.20, y, label, fontsize=10.5, color=INK, transform=ax.transAxes)
        ax.text(0.94, y, detail, fontsize=8.5, color=MUTED, transform=ax.transAxes, ha="right")
        y -= 0.05

    ax.text(
        0.06,
        0.60,
        "Invariants locked in by this scaffold",
        fontsize=13,
        fontweight="bold",
        color=ACCENT,
        transform=ax.transAxes,
    )
    inv = (
        "· Compute modules (calibration/sequence/matching/reconstruct/strain3d/\n"
        "  export) are Qt-free; the whole chain must run headless.\n"
        "· 2D engine consumed read-only; every al_dic import logged in the ledger.\n"
        "· Frozen dataclasses, NaN = invalid, float64 (enforced when modules land).\n"
        "· Version has one source of truth (hatchling reads __init__.py)."
    )
    ax.text(
        0.08, 0.555, inv, fontsize=9.5, color=INK, transform=ax.transAxes, va="top", linespacing=1.6
    )

    ax.text(
        0.06,
        0.30,
        "Next: Phase 1 — headless stereo MVP",
        fontsize=13,
        fontweight="bold",
        color=ACCENT,
        transform=ax.transAxes,
    )
    nxt = (
        "calibration + sequence + matching (protocol + track_both/S1, acc only)\n"
        "+ reconstruct + CLI + COORDINATES.md. Gate: synthetic triangulation\n"
        "closes to um; MATLAB checkpoint parity (2D field <=1e-6 px); Challenge\n"
        "sample; PDF report. Do NOT start P1 until this gate is signed off."
    )
    ax.text(
        0.08, 0.255, nxt, fontsize=9.5, color=INK, transform=ax.transAxes, va="top", linespacing=1.6
    )
    pdf.savefig(fig)
    plt.close(fig)


def main() -> int:
    today = datetime.date.today().isoformat()
    gate = run_gate()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(OUT) as pdf:
        page_title(pdf, gate, today)
        page_layout(pdf)
        page_deps(pdf)
        page_status(pdf, gate)
    ok = all(g[1] for g in gate)
    print(f"wrote {OUT}  (gate: {'PASS' if ok else 'FAIL'})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
