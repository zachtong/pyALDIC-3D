"""Display-unit conversion helpers (Q1/Q2) — pure functions, no Qt.

The 3D pipeline is metric-native: every displacement/velocity number is mm on
the wire (data, session, exports — CSV headers say ``_mm``). The unit selected
in the UNITS sidebar section converts values at the DISPLAY layer only: canvas
colorbar, 3D scalar bar, and the value ranges the auto-range writes back.
Strain is dimensionless and never converted (2D physical-units contract).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# Display units and their mm -> unit factors (order = combo order).
UNIT_OPTIONS: tuple[str, ...] = ("µm", "mm", "cm", "m")
UNIT_FACTORS: dict[str, float] = {"µm": 1000.0, "mm": 1.0, "cm": 0.1, "m": 0.001}
DEFAULT_UNIT = "mm"

# Field ids that carry mm displacement (converted); velocity carries mm/s.
DISPLACEMENT_UNIT_FIELDS = frozenset({"U", "V", "W", "mag"})
VELOCITY_FIELD = "velocity"

# Strain ids shown by the main canvas when a strain result exists (labels are
# math notation, not translated prose; moved here from canvas_area for reuse).
STRAIN_LABELS = {
    "exx": "εxx",
    "eyy": "εyy",
    "exy": "εxy",
    "e1": "ε₁",
    "e2": "ε₂",
    "max_shear": "γ max",
    "von_mises": "von Mises",
}


def unit_factor(unit: str) -> float:
    """mm -> ``unit`` multiplier (1.0 for unknown units, i.e. stay mm)."""
    return UNIT_FACTORS.get(unit, 1.0)


def field_display_factor(field: str, unit: str) -> float:
    """Scale factor applied to ``field``'s raw (mm-native) values for display."""
    if field in DISPLACEMENT_UNIT_FIELDS or field == VELOCITY_FIELD:
        return unit_factor(unit)
    return 1.0  # strain and anything else: dimensionless / untouched


def field_label(field: str, unit: str) -> str:
    """Colorbar / scalar-bar label for ``field`` in the current display unit."""
    if field == "mag":
        return f"|D| ({unit})"
    if field == VELOCITY_FIELD:
        return f"|V| ({unit}/s)"
    if field in DISPLACEMENT_UNIT_FIELDS:
        return f"{field} ({unit})"
    return STRAIN_LABELS.get(field, field)


def display_field_key(field: str, unit: str, frame_rate: float) -> str:
    """Viz-cache key suffix — display scaling changes the rendered VALUES.

    The dense-field interp cache is keyed by field name; a unit switch (and,
    for velocity, a frame-rate edit) changes the value array, so both are part
    of the key. Unscaled fields (strain) keep their bare id.
    """
    if field == VELOCITY_FIELD:
        return f"{field}@{unit}@{frame_rate:g}"
    if field in DISPLACEMENT_UNIT_FIELDS:
        return f"{field}@{unit}"
    return field


def velocity_magnitude(
    disp_k: NDArray[np.float64], disp_prev: NDArray[np.float64] | None
) -> NDArray[np.float64]:
    """Per-node ``|D_k - D_{k-1}|`` in mm/frame; all-NaN when no predecessor."""
    disp_k = np.asarray(disp_k, dtype=np.float64)
    if disp_prev is None:
        return np.full(disp_k.shape[0], np.nan, dtype=np.float64)
    return np.linalg.norm(disp_k - np.asarray(disp_prev, dtype=np.float64), axis=1)
