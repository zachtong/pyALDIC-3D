"""pyALDIC-3D's own Qt widgets (image canvas, ...).

New 3D widgets; generic 2D widgets are reused directly from ``al_dic.gui.widgets``
(ledgered in docs/DEPENDS_ON_2D.md).
"""

from al_dic_3d.gui.widgets.image_view import ImageView, load_gray_image

__all__ = ["ImageView", "load_gray_image"]
