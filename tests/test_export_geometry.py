"""Geometry exports (Batch E1): quad connectivity, PLY frames, VTU series, params.

Built on a small synthetic ``RunResult`` (frozen contract objects, no pipeline
run) so the writers' behavior — NaN handling, naming, cancellation, ParaView
round-trip — is exercised fast and deterministically.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path

import numpy as np
import pytest

from al_dic_3d.export import (
    export_params,
    export_ply_frames,
    frame_tag,
    make_prefix,
    make_timestamp,
)
from al_dic_3d.export.vtu import export_vtu_series
from al_dic_3d.matching.contracts import CorrespondenceSet
from al_dic_3d.reconstruct import Reconstruction3D
from al_dic_3d.runner import RunResult
from al_dic_3d.strain3d import STRAIN_FIELDS, StrainResult3D
from al_dic_3d.viz3d import as_vtk_faces, build_quad_connectivity, filter_cells_finite

NX, NY, STEP = 5, 4, 16.0  # regular reference grid -> (NX-1)*(NY-1) = 12 quads
HOLE = 1 * NX + 2  # interior node (ix=2, iy=1) -> touches 4 quads


def _grid(nx: int = NX, ny: int = NY, step: float = STEP) -> np.ndarray:
    xs = 100.0 + step * np.arange(nx)
    ys = 50.0 + step * np.arange(ny)
    gx, gy = np.meshgrid(xs, ys)  # row-major over y, matching iy * nx + ix
    return np.column_stack([gx.ravel(), gy.ravel()])


def make_result(n_frames: int = 3, *, hole: int | None = None, with_strain: bool = True):
    """A minimal, internally-consistent RunResult on a regular grid."""
    ref = _grid()
    n_pts = ref.shape[0]
    points = np.empty((n_frames, n_pts, 3))
    for k in range(n_frames):
        points[k, :, 0] = ref[:, 0] * 0.1 + 0.10 * k
        points[k, :, 1] = ref[:, 1] * 0.1 - 0.05 * k
        points[k, :, 2] = 800.0 + 0.25 * k
    source = np.zeros((n_frames, n_pts), dtype=np.uint8)
    if hole is not None:
        points[:, hole, :] = np.nan
        source[:, hole] = 3  # INVALID
    displacement = points - points[0]
    reproj = np.full((n_frames, n_pts), 2e-6)

    rec = Reconstruction3D(
        points=points, displacement=displacement, reproj_error=reproj, source=source
    )
    xL = np.broadcast_to(ref, (n_frames, n_pts, 2)).copy()
    cs = CorrespondenceSet(
        strategy="track_both",
        xL=xL,
        xR=xL + np.array([40.0, 0.0]),
        quality=np.zeros((n_frames, n_pts)),
        source=source.copy(),
    )
    strain = None
    if with_strain:
        strain = StrainResult3D(
            **{
                name: np.full((n_frames, n_pts), 1e-3 * (i + 1))
                for i, name in enumerate(STRAIN_FIELDS)
            }
        )
    return RunResult(
        strategy="track_both",
        ref_coords=ref,
        correspondence=cs,
        reconstruction=rec,
        strain=strain,
        meta={"strategy": "track_both", "n_frames": n_frames, "n_pts": n_pts},
    )


# --- connectivity builder ------------------------------------------------------


def test_quad_connectivity_regular_grid():
    ref = _grid()
    cells = build_quad_connectivity(ref)
    assert cells.shape == ((NX - 1) * (NY - 1), 4)
    assert cells.min() >= 0 and cells.max() < ref.shape[0]
    # Corners are counter-clockwise unit squares of the lattice.
    for q in cells:
        assert np.allclose(ref[q[1]] - ref[q[0]], [STEP, 0.0])
        assert np.allclose(ref[q[2]] - ref[q[1]], [0.0, STEP])
        assert np.allclose(ref[q[3]] - ref[q[2]], [-STEP, 0.0])


def test_quad_connectivity_missing_node_drops_its_cells():
    ref = np.delete(_grid(), HOLE, axis=0)  # node absent from the coords entirely
    cells = build_quad_connectivity(ref)
    assert cells.shape == (12 - 4, 4)
    assert cells.max() < ref.shape[0]


def test_quad_connectivity_tolerates_off_lattice_nodes():
    extra = np.array([[100.0 + STEP / 2, 50.0 + STEP / 2]])  # refined half-step node
    cells = build_quad_connectivity(np.vstack([_grid(), extra]))
    assert cells.shape == (12, 4)
    assert NX * NY not in cells  # the off-lattice node joins no quad


def test_quad_connectivity_degenerate_inputs():
    assert build_quad_connectivity(np.empty((0, 2))).shape == (0, 4)
    assert build_quad_connectivity(_grid(2, 1)).shape == (0, 4)  # single row: no lattice in y
    line = np.column_stack([np.arange(6.0), np.zeros(6)])
    assert build_quad_connectivity(line).shape == (0, 4)


def test_filter_cells_finite_drops_nan_touching_cells():
    result = make_result(hole=HOLE)
    cells = build_quad_connectivity(result.ref_coords)
    kept = filter_cells_finite(cells, result.reconstruction.points[0])
    assert kept.shape == (12 - 4, 4)
    assert HOLE not in kept
    assert filter_cells_finite(np.empty((0, 4), dtype=np.int64), np.zeros((1, 3))).size == 0


def test_as_vtk_faces_layout():
    cells = np.array([[0, 1, 2, 3], [4, 5, 6, 7]])
    faces = as_vtk_faces(cells)
    assert faces.tolist() == [4, 0, 1, 2, 3, 4, 4, 5, 6, 7]
    assert as_vtk_faces(np.empty((0, 4), dtype=np.int64)).size == 0


# --- PLY -----------------------------------------------------------------------


def _split_ply(path: Path) -> tuple[list[str], bytes]:
    blob = path.read_bytes()
    head, _, body = blob.partition(b"end_header\n")
    return head.decode("ascii").splitlines(), body


def test_ply_binary_roundtrip_drops_invalid(tmp_path):
    result = make_result(hole=HOLE)
    paths = export_ply_frames(tmp_path, "t", "20260101000000", result, ["U", "mag", "exx"])
    assert [p.name for p in paths] == ["frame_1.ply", "frame_2.ply", "frame_3.ply"]
    assert paths[0].parent.name == "t_ply_20260101000000"

    header, body = _split_ply(paths[1])
    n_valid = result.reconstruction.n_pts - 1
    assert "format binary_little_endian 1.0" in header
    assert f"element vertex {n_valid}" in header
    for prop in ("float x", "float y", "float z", "float u", "float mag", "float exx"):
        assert f"property {prop}" in header
    assert not any("valid" in line for line in header)

    dtype = [(n, "<f4") for n in ("x", "y", "z", "u", "mag", "exx")]
    rows = np.frombuffer(body, dtype=dtype)
    assert rows.shape == (n_valid,)
    valid = np.isfinite(result.reconstruction.points[1]).all(axis=1)
    assert np.allclose(rows["x"], result.reconstruction.points[1][valid, 0], atol=1e-4)
    assert np.allclose(rows["u"], result.reconstruction.displacement[1][valid, 0], atol=1e-6)
    assert np.isfinite(rows["mag"]).all()


def test_ply_ascii_keeps_invalid_with_flag(tmp_path):
    result = make_result(n_frames=2, hole=HOLE)
    paths = export_ply_frames(
        tmp_path, "t", "20260101000001", result, ["U"], binary=False, drop_invalid=False
    )
    header, body = _split_ply(paths[0])
    n_pts = result.reconstruction.n_pts
    assert "format ascii 1.0" in header
    assert f"element vertex {n_pts}" in header
    assert "property uchar valid" in header
    table = np.genfromtxt(body.decode("ascii").splitlines())
    assert table.shape == (n_pts, 5)  # x y z u valid
    assert table[HOLE, 4] == 0 and np.isnan(table[HOLE, 0])
    assert table[:, 4].sum() == n_pts - 1


def test_ply_stop_event_and_progress(tmp_path):
    result = make_result()
    stop = threading.Event()
    stop.set()
    assert export_ply_frames(tmp_path, "t", "20260101000002", result, ["U"], stop_event=stop) == []

    seen: list[float] = []
    export_ply_frames(
        tmp_path, "t", "20260101000003", result, ["U"], progress_cb=lambda f, m: seen.append(f)
    )
    assert seen == pytest.approx([1 / 3, 2 / 3, 1.0])


# --- VTU -----------------------------------------------------------------------


def test_vtu_series_roundtrip(tmp_path):
    pv = pytest.importorskip("pyvista")
    result = make_result(hole=HOLE)
    written = export_vtu_series(tmp_path, "t", "20260101000000", result, ["U", "W", "exx"])
    frames, pvd = written[:-1], written[-1]
    assert len(frames) == 3 and pvd.name == "t.pvd"

    for k, path in enumerate(frames):
        grid = pv.read(str(path))
        assert grid.n_points == result.reconstruction.n_pts  # NaN invalids kept, ids stable
        assert grid.n_cells == 12 - 4  # cells touching the NaN node dropped
        for key in ("U", "W", "exx", "reproj_error", "source"):
            assert key in grid.point_data
        finite = np.isfinite(grid.points).all(axis=1)
        assert np.allclose(grid.points[finite], result.reconstruction.points[k][finite], atol=1e-9)

    pvd_text = pvd.read_text(encoding="utf-8")
    stamps = re.findall(r'timestep="(\d+)".*?file="([^"]+)"', pvd_text)
    assert [int(t) for t, _ in stamps] == [0, 1, 2]
    assert [f for _, f in stamps] == [p.name for p in frames]


def test_vtu_missing_pyvista_message(tmp_path, monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "pyvista", None)  # forces ImportError on import
    with pytest.raises(ImportError, match=r"al-dic-3d\[viz3d\]"):
        export_vtu_series(tmp_path, "t", "20260101000000", make_result(), ["U"])


# --- params JSON + naming utilities ---------------------------------------------


def test_export_params_sanitizes_values(tmp_path):
    result = make_result()
    extra = {
        "winsize": np.int64(32),
        "calibration_file": Path("C:/data/calib.yml"),
        "roi": (0, 10, 0, 20),
        "roi_mask_array": np.zeros((4, 4)),
        "output_dir": None,
    }
    path = export_params(tmp_path, "t", "20260101000000", result, extra)
    assert path.name == "t_parameters_20260101000000.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["export_timestamp"] == "20260101000000"
    assert data["n_frames"] == 3 and data["n_pts"] == NX * NY
    assert data["strategy"] == "track_both" and data["has_strain"] is True
    assert data["winsize"] == 32  # np.int64 unboxed
    assert data["calibration_file"].endswith("calib.yml")  # Path -> str
    assert data["roi"] == [0, 10, 0, 20]
    assert data["roi_mask_array"] is None  # ndarray dropped
    assert data["output_dir"] is None


def test_naming_utilities_and_timestamp_non_collision(tmp_path):
    assert re.fullmatch(r"\d{14}", make_timestamp())
    assert frame_tag(0, 10) == "frame_01" and frame_tag(99, 100) == "frame_100"
    assert make_prefix(None) == "dic3d"
    assert make_prefix(Path("data set*2")) == "data_set_2"

    # Distinct timestamps -> distinct folders: nothing is overwritten.
    result = make_result(n_frames=2)
    a = export_ply_frames(tmp_path, "t", "20260101000000", result, ["U"])
    b = export_ply_frames(tmp_path, "t", "20260101000001", result, ["U"])
    assert a[0].parent != b[0].parent
    assert all(p.exists() for p in a + b)
