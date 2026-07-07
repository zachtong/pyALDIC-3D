"""Calibration-board specifications, object points, and board-image synthesis.

Four board families (D12), all frozen dataclasses:

- :class:`ChessboardSpec` — classic checkerboard (inner corners), detected with
  ``findChessboardCornersSB``;
- :class:`CharucoSpec` — ChArUco board (OpenCV 4.7+ object-oriented API), the
  only family whose corners carry globally unique IDs out of the box;
- :class:`CircleGridSpec` — plain symmetric/asymmetric dot grid
  (``findCirclesGrid``);
- :class:`CodedCircleGridSpec` — DIC-style dot target with three concentric-ring
  fiducial dots that pin the target frame (custom detector in ``detect.py``),
  so partial views index correctly like ChArUco.

Every spec knows its full object-point lattice in millimetres (board plane
``z = 0``) indexed by integer point ids, and can render itself to an image (for
printing and for the synthetic parity gate). Lengths are mm; rendering scale is
pixels-per-mm. Qt-free; cv2 imported lazily (module import needs only numpy).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

# Rendered boards get a white quiet border of one square/pitch around the
# pattern — findChessboardCornersSB requires it and dot detection benefits.
_ARUCO_DICT_DEFAULT = "DICT_5X5_1000"


def _grid_object_points(rows: int, cols: int, pitch_x: float, pitch_y: float) -> NDArray:
    """Row-major ``(rows*cols, 3)`` lattice ``(col*pitch_x, row*pitch_y, 0)`` in mm."""
    jj, ii = np.meshgrid(np.arange(cols, dtype=np.float64), np.arange(rows, dtype=np.float64))
    return np.column_stack(
        [jj.ravel() * pitch_x, ii.ravel() * pitch_y, np.zeros(rows * cols)]
    ).astype(np.float64)


@dataclass(frozen=True)
class ChessboardSpec:
    """Checkerboard with ``cols x rows`` INNER corners and ``square_size`` mm squares.

    Use ``rows != cols`` (both directions distinct) so the 180-degree orientation
    ambiguity can be canonicalized deterministically (see ``detect.py``).
    """

    cols: int  # inner corners per row  (OpenCV patternSize[0])
    rows: int  # inner corners per column (OpenCV patternSize[1])
    square_size: float  # mm

    def __post_init__(self) -> None:
        if self.cols < 3 or self.rows < 3:
            raise ValueError(f"chessboard needs >=3x3 inner corners, got {self.cols}x{self.rows}")
        if self.square_size <= 0:
            raise ValueError(f"square_size must be positive, got {self.square_size}")

    @property
    def pattern_size(self) -> tuple[int, int]:
        return (self.cols, self.rows)

    def object_points(self) -> NDArray[np.float64]:
        """``(cols*rows, 3)`` corner lattice in mm, OpenCV row-major corner order."""
        return _grid_object_points(self.rows, self.cols, self.square_size, self.square_size)

    def render(self, px_per_mm: float = 8.0) -> NDArray[np.uint8]:
        """Synthesize the board image (white quiet border of one square)."""
        sq = max(2, int(round(self.square_size * px_per_mm)))
        ny, nx = self.rows + 1, self.cols + 1  # squares
        tiles = (np.indices((ny, nx)).sum(axis=0) % 2).astype(np.uint8)
        board = np.kron(tiles, np.ones((sq, sq), dtype=np.uint8)) * 235 + 20
        return np.pad(board, sq, constant_values=255)

    def origin_px(self, px_per_mm: float = 8.0) -> tuple[float, float]:
        """Pixel position of object-point (0,0,0) inside :meth:`render` output.

        Square blocks are pixel-aligned, so the geometric corner between blocks
        lies half a pixel before the next block's first pixel CENTER.
        """
        sq = max(2, int(round(self.square_size * px_per_mm)))
        return (2.0 * sq - 0.5, 2.0 * sq - 0.5)  # border (1 sq) + first square


@dataclass(frozen=True)
class CharucoSpec:
    """ChArUco board: ``squares_x x squares_y`` chessboard squares with ArUco markers.

    ``square_size`` / ``marker_size`` in mm. ``legacy_pattern`` must be True for
    boards printed with OpenCV < 4.7 generators (pattern algorithm changed for
    even row counts — opencv issue #23152).
    """

    squares_x: int
    squares_y: int
    square_size: float  # mm
    marker_size: float  # mm
    dictionary: str = _ARUCO_DICT_DEFAULT
    legacy_pattern: bool = False
    min_corners: int = 8

    def __post_init__(self) -> None:
        if self.squares_x < 3 or self.squares_y < 3:
            raise ValueError(f"charuco needs >=3x3 squares, got {self.squares_x}x{self.squares_y}")
        if not 0 < self.marker_size < self.square_size:
            raise ValueError(
                f"need 0 < marker_size < square_size, got {self.marker_size}/{self.square_size}"
            )

    def board(self):
        """The lazily-built ``cv2.aruco.CharucoBoard`` (4.7+ OO API)."""
        import cv2

        dic = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, self.dictionary))
        board = cv2.aruco.CharucoBoard(
            (self.squares_x, self.squares_y), self.square_size, self.marker_size, dic
        )
        if self.legacy_pattern:
            board.setLegacyPattern(True)
        return board

    def object_points(self) -> NDArray[np.float64]:
        """All interior chessboard corners in mm, indexed by ChArUco corner id."""
        return np.asarray(self.board().getChessboardCorners(), dtype=np.float64)

    def render(self, px_per_mm: float = 8.0) -> NDArray[np.uint8]:
        """Synthesize the board image (quiet border of one square)."""
        sq = max(2, int(round(self.square_size * px_per_mm)))
        size = (self.squares_x * sq, self.squares_y * sq)
        img = self.board().generateImage(size, marginSize=0, borderBits=1)
        return np.pad(img, sq, constant_values=255)

    def origin_px(self, px_per_mm: float = 8.0) -> tuple[float, float]:
        """Pixel position of the board-frame origin (0,0,0) in :meth:`render`.

        Unlike :class:`ChessboardSpec` (origin = first INTERIOR corner), the
        ChArUco object frame originates at the board's OUTER corner —
        ``getChessboardCorners()`` places interior corners starting at
        ``(square_size, square_size)``. The outer corner sits right after the
        quiet border, half a pixel before its first pixel center.
        """
        sq = max(2, int(round(self.square_size * px_per_mm)))
        return (sq - 0.5, sq - 0.5)  # quiet border only


@dataclass(frozen=True)
class CircleGridSpec:
    """Plain dot grid for ``cv2.findCirclesGrid``.

    Symmetric: ``cols x rows`` dots with pitch ``spacing`` mm both ways.
    Asymmetric: OpenCV sample convention — object point ``((2*col + row%2), row)
    * spacing`` (``spacing`` = half the within-row pitch = diagonal half-pitch).

    NOTE circle centers carry a systematic perspective/distortion eccentricity
    bias (opencv issue #7312) growing with dot size and tilt; the solver reports
    a warning when ``dot_diameter/spacing`` is large. Prefer chessboard/ChArUco
    when accuracy is critical.
    """

    cols: int
    rows: int
    spacing: float  # mm (see docstring for the asymmetric meaning)
    asymmetric: bool = False
    dot_diameter: float | None = None  # mm, used for rendering + blob sizing hints
    dark_dots: bool = True
    clustering: bool = False  # CALIB_CB_CLUSTERING (robust to perspective, needs clean bg)

    def __post_init__(self) -> None:
        if self.cols < 3 or self.rows < 3:
            raise ValueError(f"circle grid needs >=3x3 dots, got {self.cols}x{self.rows}")
        if self.spacing <= 0:
            raise ValueError(f"spacing must be positive, got {self.spacing}")

    @property
    def pattern_size(self) -> tuple[int, int]:
        return (self.cols, self.rows)

    @property
    def dot_mm(self) -> float:
        return self.dot_diameter if self.dot_diameter else 0.5 * self.spacing

    def object_points(self) -> NDArray[np.float64]:
        if not self.asymmetric:
            return _grid_object_points(self.rows, self.cols, self.spacing, self.spacing)
        jj, ii = np.meshgrid(
            np.arange(self.cols, dtype=np.float64), np.arange(self.rows, dtype=np.float64)
        )
        x = (2.0 * jj + (ii % 2)) * self.spacing
        y = ii * self.spacing
        return np.column_stack([x.ravel(), y.ravel(), np.zeros(x.size)]).astype(np.float64)

    def render(self, px_per_mm: float = 8.0) -> NDArray[np.uint8]:
        return _render_dots(self.object_points(), self.dot_mm, self.spacing, px_per_mm, {})

    def origin_px(self, px_per_mm: float = 8.0) -> tuple[float, float]:
        m = self.spacing * px_per_mm
        return (m, m)


@dataclass(frozen=True)
class CodedCircleGridSpec:
    """Symmetric dot grid with three concentric-ring fiducial dots (DIC targets).

    The three fiducials sit at grid positions ``fiducials`` = ((row, col), ...)
    forming an asymmetric triangle (all three pairwise grid distances distinct)
    so the detector can solve the correspondence unambiguously and recover the
    target frame even from partial views. Fiducial centers are ordinary grid
    dots wearing an extra concentric ring; every dot (fiducials included) is a
    calibration point.
    """

    cols: int
    rows: int
    spacing: float  # mm pitch, both directions
    dot_diameter: float | None = None  # mm; default 0.5 * spacing
    fiducials: tuple[tuple[int, int], ...] = field(default=())
    dark_dots: bool = True

    def __post_init__(self) -> None:
        if self.cols < 5 or self.rows < 5:
            raise ValueError(f"coded grid needs >=5x5 dots, got {self.cols}x{self.rows}")
        if self.spacing <= 0:
            raise ValueError(f"spacing must be positive, got {self.spacing}")
        fid = self.fiducials or self._default_fiducials()
        object.__setattr__(self, "fiducials", tuple((int(r), int(c)) for r, c in fid))
        if len(self.fiducials) != 3:
            raise ValueError(f"exactly 3 fiducials required, got {len(self.fiducials)}")
        for r, c in self.fiducials:
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                raise ValueError(f"fiducial {(r, c)} outside {self.rows}x{self.cols} grid")
        d = [
            (r1 - r2) ** 2 + (c1 - c2) ** 2
            for i, (r1, c1) in enumerate(self.fiducials)
            for r2, c2 in self.fiducials[i + 1 :]
        ]
        if len(set(d)) != 3:
            raise ValueError(
                f"fiducial triangle must have 3 distinct side lengths, got {sorted(d)}"
            )

    def _default_fiducials(self) -> tuple[tuple[int, int], ...]:
        """An asymmetric L around the grid center (side lengths 2, 3, sqrt(13))."""
        rc, cc = self.rows // 2, self.cols // 2
        return ((rc, cc - 1), (rc, cc + 2), (rc - 2, cc - 1))

    @property
    def dot_mm(self) -> float:
        return self.dot_diameter if self.dot_diameter else 0.5 * self.spacing

    def point_id(self, row: int, col: int) -> int:
        return row * self.cols + col

    @property
    def fiducial_ids(self) -> tuple[int, int, int]:
        r = tuple(self.point_id(rr, cc) for rr, cc in self.fiducials)
        return (r[0], r[1], r[2])

    def object_points(self) -> NDArray[np.float64]:
        return _grid_object_points(self.rows, self.cols, self.spacing, self.spacing)

    def render(self, px_per_mm: float = 8.0) -> NDArray[np.uint8]:
        rings = {self.point_id(r, c) for r, c in self.fiducials}
        return _render_dots(self.object_points(), self.dot_mm, self.spacing, px_per_mm, rings)

    def origin_px(self, px_per_mm: float = 8.0) -> tuple[float, float]:
        m = self.spacing * px_per_mm
        return (m, m)


BoardSpec = ChessboardSpec | CharucoSpec | CircleGridSpec | CodedCircleGridSpec


def _render_dots(
    obj_mm: NDArray[np.float64],
    dot_mm: float,
    spacing_mm: float,
    px_per_mm: float,
    ring_ids: set[int],
) -> NDArray[np.uint8]:
    """Draw dots (dark on white) with sub-pixel anti-aliased circles.

    Fiducials in ``ring_ids`` get a concentric annulus at 1.7-2.3x the dot
    radius. Margin = one pitch. Object (0,0) lands at pixel (margin, margin).
    """
    import cv2

    margin = spacing_mm * px_per_mm
    w = int(round(obj_mm[:, 0].max() * px_per_mm + 2 * margin)) + 1
    h = int(round(obj_mm[:, 1].max() * px_per_mm + 2 * margin)) + 1
    img = np.full((h, w), 255, dtype=np.uint8)
    shift = 4
    s = 1 << shift
    r_dot = 0.5 * dot_mm * px_per_mm
    for i, (x, y, _z) in enumerate(obj_mm):
        cx = int(round((x * px_per_mm + margin) * s))
        cy = int(round((y * px_per_mm + margin) * s))
        if i in ring_ids:  # annulus: outer dark disc, then white gap, then the dot
            cv2.circle(img, (cx, cy), int(round(2.3 * r_dot * s)), 20, -1, cv2.LINE_AA, shift)
            cv2.circle(img, (cx, cy), int(round(1.7 * r_dot * s)), 255, -1, cv2.LINE_AA, shift)
        cv2.circle(img, (cx, cy), int(round(r_dot * s)), 20, -1, cv2.LINE_AA, shift)
    return img
