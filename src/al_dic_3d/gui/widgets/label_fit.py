"""Size a column of row labels from their text (fix batch V, finding H5).

The sidebars used fixed 88 / 96 px label widths, which cut labels off in
English ("Refinement Leve", "Show Gr") and more in German ("Tracking-Modu").
:func:`fit_labels` gives every label of a column the width of the widest
text in the current language and font, within bounds, and lets anything
wider than the upper bound wrap onto a second line instead of being cut.
"""

from __future__ import annotations

from collections.abc import Iterable

# Narrowest label column (the old fixed width) and the widest one before a
# label wraps; the sidebar still has to leave room for its spin boxes.
MIN_LABEL_PX = 88
MAX_LABEL_PX = 132
_PAD_PX = 6


def fit_labels(labels: Iterable, min_px: int = MIN_LABEL_PX, max_px: int = MAX_LABEL_PX) -> int:
    """Give ``labels`` one shared width from their widest text; return it."""
    labels = [lb for lb in labels if lb is not None]
    if not labels:
        return min_px
    widest = max(lb.fontMetrics().horizontalAdvance(lb.text()) for lb in labels) + _PAD_PX
    width = max(min_px, min(max_px, widest))
    for lb in labels:
        lb.setWordWrap(True)
        lb.setFixedWidth(width)
    return width
