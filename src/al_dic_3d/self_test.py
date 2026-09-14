"""Prove an installation -- above all a frozen bundle -- actually works.

    al-dic-3d self-test [--json REPORT]
    pyaldic3d-cli.exe self-test            (the gate in packaging/build_installer.ps1)

A launch-only check is close to worthless for a frozen bundle: the application
guards optional pieces (QtSvg, the translation catalogs, numba, the FFmpeg DLL,
matplotlib behind the colorbar) with fallbacks, so a bundle that lost them
still opens a window and looks fine. Each check below targets one such silent
fallback; the last one runs a real stereo correlation end to end against the
analytic ground truth of :mod:`al_dic_3d.synthetic`. (Port of the 2D 0.8.0
``--self-test`` design, as a CLI sub-command.)

Output contract -- packaging/build_installer.ps1 and
.github/workflows/build-exe.yml rely on it:

* one line per check: ``[ok] name: detail``, ``[FAIL] name: detail`` or
  ``[skip] name: reason``; an unexpected exception's traceback follows its
  line, indented, and a summary line closes the run;
* exit code 0 when every check passed (skips count as passes), 1 otherwise;
* ``--json PATH`` also writes a UTF-8 JSON report;
* stdout is ASCII-only: the build pipes it through a Windows legacy code page
  from a working directory named ``self-test 自检 été``, so non-ASCII text in
  a detail is backslash-escaped and a UnicodeEncodeError can never escape;
* ``ALDIC3D_SELFTEST_SKIP_GL=1`` skips only the OpenGL/VTK render check
  (hosted CI runners have no OpenGL 3.2 context).

Importable without a display: heavy imports are lazy inside each check, and
the Qt checks build their own ``QApplication`` (offscreen when no display is
available).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
import traceback
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

# Non-ASCII *and* a space: each has broken file I/O on Windows on its own.
NON_ASCII_DIR = "试样 été 1"
SKIP_GL_ENV = "ALDIC3D_SELFTEST_SKIP_GL"
# A source string per catalog that every shipped locale must translate
# (al_dic_3d: the Run button; al_dic: the 2D Run button, same catalog set).
PROBE_3D = ("RightSidebar3D", "Run 3D Analysis")
PROBE_2D = ("RightSidebar", "Run DIC Analysis")
# The mini stereo run: small enough for seconds once compiled, big enough for
# the engine's batched kernels (>= 50 nodes). Tolerances are the synthetic
# parity gate's (about 1.6x the accuracy observed on this scene).
MINI_SCENE = {"img": 240, "n_frames": 3, "seed": 7}
MINI_TOL = {"coverage_min": 0.95, "disp_median_mm": 0.08, "disp_p90_mm": 0.12}

_STATUSES = ("ok", "FAIL", "skip")
_SCRATCH: Path | None = None  # per-run temp root (see _scratch_root)
_APP = None  # keeps the self-test's QApplication alive


class CheckFailed(Exception):
    """A check did not pass; the message is the report detail."""


class CheckSkipped(Exception):
    """A check does not apply here; the message is the reason."""


@dataclass(frozen=True)
class CheckResult:
    """One check's outcome (``status`` is ``"ok"``, ``"FAIL"`` or ``"skip"``)."""

    name: str
    status: str
    detail: str
    seconds: float
    traceback: str = ""

    @property
    def passed(self) -> bool:
        return self.status != "FAIL"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def ascii_safe(text: str) -> str:
    """``text`` with every non-ASCII character backslash-escaped."""
    return text.encode("ascii", "backslashreplace").decode("ascii")


def _scratch(name: str) -> Path:
    """A fresh ``<run temp>/<name>/试样 été 1`` folder for one check."""
    root = _SCRATCH if _SCRATCH is not None else Path(tempfile.mkdtemp(prefix="aldic3d-selftest-"))
    folder = root / name / NON_ASCII_DIR
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _display_available() -> bool:
    if os.environ.get("QT_QPA_PLATFORM"):
        return True  # the caller chose a platform explicitly
    if sys.platform in ("win32", "darwin"):
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _qapp():
    """The running ``QApplication``, or a new one (offscreen without a display)."""
    global _APP
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        if not _display_available():
            os.environ["QT_QPA_PLATFORM"] = "offscreen"
        app = QApplication(["al-dic-3d-self-test"])
    if not isinstance(app, QApplication):
        raise CheckFailed("a non-GUI QCoreApplication is already running")
    _APP = app
    return app


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_packaged_data() -> str:
    """Every data file the app resolves next to its modules is in the bundle."""
    import al_dic.gui.icons as icons_mod
    import al_dic.gui.theme as theme_mod

    import al_dic_3d.i18n as i18n

    missing = [
        f"al_dic_3d_{loc}.qm" for loc in i18n.TARGET_LOCALES if not i18n.compiled_qm(loc).is_file()
    ]
    for loc in i18n.TARGET_LOCALES:
        qm = i18n.al_dic_compiled_qm(loc)
        if qm is None or not qm.is_file():
            missing.append(f"al_dic_{loc}.qm")
    if missing:
        raise CheckFailed(
            f"missing translation catalogs: {', '.join(missing)} (the bundle must carry "
            "al_dic_3d/i18n/compiled and al_dic/i18n/compiled)"
        )
    arrows_dir = Path(theme_mod.__file__).parent / "arrows"
    arrows = sorted(p.name for p in arrows_dir.glob("*.svg")) if arrows_dir.is_dir() else []
    if len(arrows) < 4:
        raise CheckFailed(f"expected 4 spin-box arrow SVGs in {arrows_dir}, found {arrows}")
    icon_dir = Path(icons_mod.__file__).parent / "assets" / "icon"
    icons = ("pyALDIC.ico", "pyALDIC-256.png", "pyALDIC.svg")
    absent = [n for n in icons if not (icon_dir / n).is_file()]
    if absent:
        raise CheckFailed(f"missing icon assets in {icon_dir}: {absent}")
    n = len(i18n.TARGET_LOCALES)
    return f"{n} al_dic_3d + {n} al_dic catalogs, {len(arrows)} arrows, {len(icons)} icons"


def check_qt_and_icons() -> str:
    """QtSvg is present and the icon functions return real pixmaps."""
    from PySide6.QtCore import qVersion

    app = _qapp()
    from al_dic.gui import icons

    if not getattr(icons, "_HAS_SVG", False):
        raise CheckFailed(
            "PySide6.QtSvg is missing: every toolbar icon degrades to an empty QIcon "
            "without raising"
        )
    for fn in (icons.icon_app, icons.icon_play, icons.icon_zoom_in):
        icon = fn()
        if icon.isNull() or icon.pixmap(32, 32).isNull():
            raise CheckFailed(f"{fn.__name__}() produced a null icon")
    sizes = [s.width() for s in icons.icon_app().availableSizes()][:4]
    return f"Qt {qVersion()} ({app.platformName()}), QtSvg live, app icon sizes {sizes}"


def check_gui_imports() -> str:
    """The GUI modules and their lazily imported dependencies are bundled."""
    import importlib

    _qapp()
    modules = (
        "al_dic_3d.gui.main_window",
        "al_dic_3d.gui.strain_window",
        "al_dic_3d.gui.dialogs.export_dialog",
        "pyvistaqt",
    )
    for name in modules:
        importlib.import_module(name)
    return f"{len(modules)} modules import"


def check_all_locales() -> str:
    """Every shipped locale loads AND changes the text (loading alone proves nothing)."""
    from PySide6.QtCore import QCoreApplication

    from al_dic_3d.i18n import LOCALES, install_translators

    app = _qapp()
    untranslated: list[str] = []
    try:
        for loc in LOCALES:
            install_translators(app, locale=loc)
            for context, source in (PROBE_3D, PROBE_2D):
                text = QCoreApplication.translate(context, source)
                if (loc == "en") != (text == source):
                    untranslated.append(f"{loc}/{context}")
    finally:
        install_translators(app, locale="en")
    if untranslated:
        raise CheckFailed(
            f"catalogs did not translate the probe strings: {untranslated}; the .qm "
            "files are missing or stale in the bundle"
        )
    return f"{len(LOCALES)} locales load and translate (al_dic_3d + al_dic)"


def check_numba() -> str:
    """numba is present, the JIT cache is usable and the kernels are real dispatchers."""
    from al_dic_3d._numba_compat import HAS_NUMBA, JIT_CACHE

    if not HAS_NUMBA:
        raise CheckFailed("numba is not importable: the solver and strain kernels fall back")
    from al_dic.solver import numba_kernels as nk

    from al_dic_3d.strain3d import kernels

    for label, fn in (
        ("strain3d _fit_kernel", getattr(kernels, "_fit_kernel", None)),
        ("al_dic icgn_6dof_parallel", getattr(nk, "icgn_6dof_parallel", None)),
    ):
        module = type(fn).__module__
        if not module.startswith("numba"):
            raise CheckFailed(f"{label} is {module}, a pass-through stub, not a numba dispatcher")
    import numba

    started = time.perf_counter()
    kernels.warmup()  # compiles (or cache-loads) a parallel=True kernel
    compile_s = time.perf_counter() - started
    try:
        layer = numba.threading_layer()
    except ValueError:
        layer = "unresolved"
    if layer == "workqueue" and sys.platform == "win32" and getattr(sys, "frozen", False):
        raise CheckFailed(
            "numba fell back to the 'workqueue' threading layer: the OpenMP runtime "
            "(vcomp140.dll) is missing from the bundle"
        )
    note = (
        f"cache={JIT_CACHE}, threads={numba.get_num_threads()}, layer={layer}, "
        f"strain kernel ready in {compile_s:.1f} s"
    )
    if not JIT_CACHE:
        note += " (WARNING: JIT cache unusable, every launch recompiles)"
    return note


def check_hashing() -> str:
    """sha256 is correct: the draft's result signature (staleness hint) depends on it."""
    import hashlib

    import numpy as np

    from al_dic_3d.project.draft import ProjectDraft

    abc = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"  # FIPS 180-2
    digests = {hashlib.sha256(b"abc").hexdigest(), hashlib.new("sha256", b"abc").hexdigest()}
    if digests != {abc}:
        raise CheckFailed("hashlib sha256 returns a wrong digest for the FIPS test vector")
    mask = np.zeros((16, 16), dtype=bool)
    mask[3:9, 4:12] = True
    edited = mask.copy()
    edited[0, 0] = True
    a = ProjectDraft(winsize=32, roi=(4, 11, 3, 8), roi_mask_array=mask)
    b = ProjectDraft(winsize=32, roi=(4, 11, 3, 8), roi_mask_array=mask.copy())
    c = ProjectDraft(winsize=48, roi=(4, 11, 3, 8), roi_mask_array=mask)
    d = ProjectDraft(winsize=32, roi=(4, 11, 3, 8), roi_mask_array=edited)
    sig = a.result_signature()
    if sig != b.result_signature():
        raise CheckFailed("the draft result signature is not deterministic")
    if sig in (c.result_signature(), d.result_signature()):
        raise CheckFailed("the draft result signature ignores a result-changing edit")
    return f"sha256 test vector ok, draft signature {sig[:16]}..."


def check_image_io_non_ascii() -> str:
    """Images and calibration YAML survive a non-ASCII path with a space in it."""
    import numpy as np

    from al_dic_3d.pathsafe import (
        filestorage_read,
        filestorage_write,
        imread_unicode,
        imwrite_unicode,
    )

    root = _scratch("image_io")
    rng = np.random.default_rng(1)
    img8 = (rng.random((48, 64)) * 255).astype(np.uint8)
    img16 = (rng.random((48, 64)) * 65535).astype(np.uint16)
    written = []
    for name, img, lossless in (
        ("图像 8bit.png", img8, True),
        ("图像 16bit.tif", img16, True),
        ("图像.jpg", img8, False),
    ):
        path = root / name
        imwrite_unicode(path, img)
        back = imread_unicode(path)
        if back is None or back.shape != img.shape:
            raise CheckFailed(f"could not read back {path.suffix} written to a non-ASCII folder")
        if lossless and not np.array_equal(back, img):
            raise CheckFailed(f"{path.suffix} round trip changed the pixels")
        written.append(f"{path.suffix} {path.stat().st_size}B")
    K = np.array([[1500.0, 0.0, 319.5], [0.0, 1500.0, 239.5], [0.0, 0.0, 1.0]])
    yml = root / "标定 calib.yml"
    with filestorage_write(yml) as fs:
        fs.write("cameraMatrix1", K)
    fs = filestorage_read(yml)
    try:
        back_k = fs.getNode("cameraMatrix1").mat()
    finally:
        fs.release()
    if back_k is None or not np.allclose(back_k, K):
        raise CheckFailed("calibration YAML round trip (cv2.FileStorage) failed")
    return ", ".join(written) + ", yaml ok"


def check_video_and_gif() -> str:
    """MP4 and GIF through the exporters' own writer (``StreamingAnimWriter``).

    MP4 needs OpenCV's FFmpeg backend; GIF is streamed through Pillow. Going
    through the real writer checks what an export does, including that an
    unopenable encoder raises instead of reporting success.
    """
    import numpy as np

    from al_dic_3d.export.animation import StreamingAnimWriter

    root = _scratch("video")
    frames = [np.full((48, 64, 3), v, np.uint8) for v in (40, 120, 200)]
    sizes = {}
    for fmt in ("mp4", "gif"):
        try:
            writer = StreamingAnimWriter(fmt, root, "动画 anim", 10, (48, 64))
        except OSError as exc:
            raise CheckFailed(
                f"the {fmt.upper()} writer could not open: {exc} (for MP4 the FFmpeg "
                "backend opencv_videoio_ffmpeg*.dll is probably missing)"
            ) from exc
        for frame in frames:
            writer.append(frame)
        writer.close()
        out = writer.out
        if not out.is_file() or out.stat().st_size == 0:
            raise CheckFailed(f"the {fmt.upper()} writer opened but wrote nothing")
        sizes[fmt] = out.stat().st_size
    return f"mp4 {sizes['mp4']}B, gif {sizes['gif']}B"


def check_colorbar() -> str:
    """matplotlib renders the export colorbar (attach_colorbar hides its failures)."""
    import numpy as np

    from al_dic_3d.export.colorbar import (
        ColorbarStyle,
        _render_bar,
        attach_colorbar,
        colorbar_label,
    )

    label = colorbar_label("exx")  # a Greek glyph: exercises the bundled fonts
    try:
        bar = _render_bar(120, 60, "vertical", "turbo", 0.0, 1.0, label, 9.0, "black", 100)
    except Exception as exc:  # noqa: BLE001 - report exactly what broke
        raise CheckFailed(f"colorbar rendering raised {type(exc).__name__}: {exc}") from exc
    if bar.shape != (120, 60, 3) or float(np.asarray(bar).std()) < 1.0:
        raise CheckFailed("the colorbar rendered blank (matplotlib Agg or mpl-data missing?)")
    img = np.full((80, 120, 3), 90, np.uint8)
    out = np.asarray(attach_colorbar(img, ColorbarStyle(), "turbo", 0.0, 1.0, label, 100))
    if out.shape == img.shape and np.array_equal(out, img):
        raise CheckFailed("attach_colorbar returned the image unchanged")
    return f"{img.shape[1]}x{img.shape[0]} -> {out.shape[1]}x{out.shape[0]}"


def check_session_roundtrip() -> str:
    """A ``.aldic3d`` project with results survives save + load in a non-ASCII folder."""
    import numpy as np

    from al_dic_3d.matching.contracts import INVALID, TRACKED, CorrespondenceSet
    from al_dic_3d.project import AppState3D, ProjectDraft, load_session, save_session
    from al_dic_3d.reconstruct import Reconstruction3D
    from al_dic_3d.runner import RunResult

    root = _scratch("session")
    rng = np.random.default_rng(5)
    nf, n = 2, 6
    xl = rng.random((nf, n, 2)) * 100.0
    xl[1, 0] = np.nan  # NaN = invalid must survive the round trip
    source = np.full((nf, n), TRACKED, dtype=np.uint8)
    source[1, 0] = INVALID
    pts = rng.random((nf, n, 3)) * 10.0
    pts[1, 0] = np.nan
    cs = CorrespondenceSet("track_both", xl, xl + 3.0, rng.random((nf, n)), source)
    rec = Reconstruction3D(pts, pts - pts[0], rng.random((nf, n)), source.copy())
    result = RunResult("track_both", xl[0].copy(), cs, rec, meta={"n_frames": nf})
    mask = np.zeros((32, 32), dtype=bool)
    mask[4:20, 6:28] = True
    draft = ProjectDraft(
        calibration_file=root / "标定.yml",
        left=[str(root / "左 000.png"), str(root / "左 001.png")],
        right=[str(root / "右 000.png"), str(root / "右 001.png")],
        roi=(6, 27, 4, 19),
        roi_mask_array=mask,
        winsize=24,
        seed_points=[(10.0, 12.0)],
    )
    view = {"display_field": "W", "note": "été 试样"}
    path = save_session(
        AppState3D(draft=draft, result=result, view_state=view), root / "项目 été.aldic3d"
    )
    back = load_session(path)
    problems = []
    if back.draft.left != draft.left or back.draft.calibration_file != draft.calibration_file:
        problems.append("draft paths")
    if (
        back.draft.roi != draft.roi
        or back.draft.winsize != 24
        or back.draft.seed_points != [(10.0, 12.0)]
    ):
        problems.append("draft parameters")
    if back.draft.roi_mask_array is None or not np.array_equal(back.draft.roi_mask_array, mask):
        problems.append("ROI mask")
    if back.view_state != view:
        problems.append("view state")
    got = back.result
    if got is None or not (
        np.array_equal(got.correspondence.xL, xl, equal_nan=True)
        and np.array_equal(got.reconstruction.points, pts, equal_nan=True)
        and np.array_equal(got.reconstruction.source, source)
    ):
        problems.append("result arrays")
    if problems:
        raise CheckFailed(f"session round trip changed: {', '.join(problems)}")
    return f"{path.stat().st_size} B bundle, {n} points x {nf} frames, mask + NaN preserved"


def check_render3d_offscreen() -> str:
    """VTK renders offscreen through pyvista (skipped with ALDIC3D_SELFTEST_SKIP_GL=1)."""
    if os.environ.get(SKIP_GL_ENV, "").strip().lower() in ("1", "true", "yes", "on"):
        raise CheckSkipped(f"{SKIP_GL_ENV}=1 (no OpenGL context on this machine)")
    import numpy as np
    import pyvista as pv
    from vtkmodules.vtkCommonCore import vtkVersion

    plotter = pv.Plotter(off_screen=True, window_size=(160, 120))
    try:
        sphere = pv.Sphere(theta_resolution=24, phi_resolution=24)
        sphere["height"] = sphere.points[:, 2]
        plotter.add_mesh(sphere, scalars="height", cmap="turbo", show_scalar_bar=False)
        plotter.set_background("black")
        window = plotter.render_window.GetClassName()
        img = np.asarray(plotter.screenshot(return_img=True))
    finally:
        plotter.close()
    if img.ndim != 3 or img.shape[:2] != (120, 160):
        raise CheckFailed(f"offscreen render returned a {img.shape} image")
    if float(img.std()) < 5.0:
        raise CheckFailed("the offscreen render is blank")
    return f"VTK {vtkVersion.GetVTKVersion()} ({window}), {img.shape[1]}x{img.shape[0]} image"


def check_mini_stereo() -> str:
    """A real stereo run end to end on a tiny synthetic scene, against ground truth."""
    from dataclasses import replace

    import numpy as np

    from al_dic_3d import synthetic
    from al_dic_3d.runner import load_config, run_pipeline

    root = _scratch("mini_stereo")
    scene = synthetic.build_scene(root, **MINI_SCENE)
    cfg = replace(load_config(synthetic.write_config(root, scene)), compute_strain=True)
    result = run_pipeline(cfg)
    acc = synthetic.accuracy_summary(result, scene)
    problems = []
    if not acc["coverage_min"] >= MINI_TOL["coverage_min"]:
        problems.append(f"coverage {acc['coverage_min']:.1%} < {MINI_TOL['coverage_min']:.0%}")
    for key, what in (("disp_median_mm", "median"), ("disp_p90_mm", "p90")):
        if not acc[key] <= MINI_TOL[key]:
            problems.append(f"3D displacement error {what} {acc[key]:.4f} mm > {MINI_TOL[key]} mm")
    strain = getattr(result, "strain", None)
    exx = None if strain is None else np.asarray(strain.exx[-1], dtype=np.float64)
    if exx is None or float(np.isfinite(exx).mean()) < 0.5:
        problems.append("no surface strain on the last frame")
    if problems:
        raise CheckFailed("; ".join(problems))
    return (
        f"{int(acc['n_points'])} points x {int(acc['n_frames'])} frames, coverage "
        f"{acc['coverage_min']:.0%}, 3D displacement error median "
        f"{acc['disp_median_mm'] * 1000:.0f} um (p90 {acc['disp_p90_mm'] * 1000:.0f} um), strain ok"
    )


CHECKS: list[tuple[str, Callable[[], str]]] = [
    ("packaged_data", check_packaged_data),
    ("qt_and_icons", check_qt_and_icons),
    ("gui_imports", check_gui_imports),
    ("all_locales", check_all_locales),
    ("numba", check_numba),
    ("hashing", check_hashing),
    ("image_io_non_ascii", check_image_io_non_ascii),
    ("video_and_gif", check_video_and_gif),
    ("colorbar", check_colorbar),
    ("session_roundtrip", check_session_roundtrip),
    ("render3d_offscreen", check_render3d_offscreen),
    ("mini_stereo", check_mini_stereo),  # slowest last, so failures surface sooner
]


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def run_check(name: str, fn: Callable[[], str]) -> CheckResult:
    """Run one check; never raises (except on KeyboardInterrupt)."""
    started = time.perf_counter()
    trace = ""
    try:
        detail, status = str(fn()), "ok"
    except CheckSkipped as exc:
        detail, status = str(exc), "skip"
    except CheckFailed as exc:
        detail, status = str(exc), "FAIL"
    except Exception as exc:  # noqa: BLE001 - every failure is a report line
        detail, status = f"{type(exc).__name__}: {exc}", "FAIL"
        trace = traceback.format_exc()
    return CheckResult(name, status, detail, round(time.perf_counter() - started, 2), trace)


def format_line(result: CheckResult) -> str:
    """The single ASCII report line for ``result``."""
    parts = [ln.strip() for ln in str(result.detail).splitlines() if ln.strip()]
    return ascii_safe(f"[{result.status}] {result.name}: {' | '.join(parts) or '-'}")


def _emit(line: str) -> None:
    """Print one ASCII line; a missing or broken stdout never fails the self-test."""
    stream = sys.stdout
    if stream is None:
        return
    try:
        stream.write(ascii_safe(line) + "\n")
        stream.flush()
    except (OSError, ValueError, UnicodeError):
        pass


@contextmanager
def _escaping_std_streams() -> Iterator[None]:
    """Make stray non-ASCII library output encoding-safe while the checks run."""
    restore = []
    for stream in (sys.stdout, sys.stderr):
        errors = getattr(stream, "errors", None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None or errors in (None, "backslashreplace"):
            continue
        try:
            reconfigure(errors="backslashreplace")
            restore.append((stream, errors))
        except (OSError, ValueError, AttributeError):
            pass
    try:
        yield
    finally:
        for stream, errors in restore:
            try:
                stream.reconfigure(errors=errors)
            except (OSError, ValueError, AttributeError):
                pass


@contextmanager
def _scratch_root() -> Iterator[Path]:
    """A per-run temp folder for every check's files, removed afterwards."""
    global _SCRATCH
    previous = _SCRATCH
    root = Path(tempfile.mkdtemp(prefix="aldic3d-selftest-"))
    _SCRATCH = root
    try:
        yield root
    finally:
        _SCRATCH = previous
        shutil.rmtree(root, ignore_errors=True)


def _write_report(path: str | Path, results: Sequence[CheckResult], seconds: float) -> None:
    import platform

    from al_dic_3d import __version__

    report = {
        "app": "al-dic-3d",
        "version": __version__,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "frozen": bool(getattr(sys, "frozen", False)),
        "passed": all(r.passed for r in results),
        "seconds": round(seconds, 2),
        "checks": [asdict(r) for r in results],
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def run_self_test(
    json_path: str | Path | None = None,
    checks: Sequence[tuple[str, Callable[[], str]]] | None = None,
) -> int:
    """Run the checks, print the report, optionally write JSON; return the exit code."""
    from al_dic_3d import __version__

    selected = list(CHECKS if checks is None else checks)
    started = time.perf_counter()
    results: list[CheckResult] = []
    with _escaping_std_streams():
        kind = "frozen" if getattr(sys, "frozen", False) else "source"
        _emit(f"al-dic-3d {__version__} self-test ({kind}, Python {sys.version.split()[0]})")
        with _scratch_root():
            for name, fn in selected:
                result = run_check(name, fn)
                results.append(result)
                _emit(format_line(result))
                for line in result.traceback.rstrip().splitlines()[-15:]:
                    _emit("    " + line)
        elapsed = time.perf_counter() - started
        if json_path is not None:
            try:
                _write_report(json_path, results, elapsed)
            except OSError as exc:
                # Counted like a check, so the summary never says "0 failed"
                # above a failing exit code.
                failed = CheckResult("json_report", "FAIL", f"cannot write {json_path}: {exc}", 0.0)
                results.append(failed)
                _emit(format_line(failed))
        counts = {s: sum(r.status == s for r in results) for s in _STATUSES}
        _emit(
            f"self-test: {counts['ok']} passed, {counts['skip']} skipped, "
            f"{counts['FAIL']} failed in {elapsed:.1f} s"
        )
    return 0 if counts["FAIL"] == 0 else 1


__all__ = [
    "CHECKS",
    "MINI_TOL",
    "NON_ASCII_DIR",
    "SKIP_GL_ENV",
    "CheckFailed",
    "CheckResult",
    "CheckSkipped",
    "ascii_safe",
    "format_line",
    "run_check",
    "run_self_test",
]
