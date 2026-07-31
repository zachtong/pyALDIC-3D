"""pyALDIC-3D: stereo / multi-camera Digital Image Correlation.

An **independent application** (import package ``al_dic_3d``, distribution
``al-dic-3d``, CLI ``al-dic-3d``, session format ``.aldic3d``) built on top of
the pyALDIC-2D platform, which it consumes as a **pinned, read-only library**
(``al-dic==0.7.*``). It is NOT a "3D mode" inside the 2D app.

The full stereo-DIC pipeline is implemented: built-in stereo calibration (plus
six import formats), pluggable stereo/temporal correspondence strategies,
DLT triangulation to mm-world 3D displacement, crack-aware tracking, and
surface Green-Lagrange strain — with a PySide6 GUI, a headless ``al-dic-3d run``
CLI, and NPZ/MAT/CSV/PLY/VTU export. See ``docs/user-guide/`` for the manual,
``docs/architecture/`` for the technical baseline, and ``docs/DEPENDS_ON_2D.md``
for the 2D coupling ledger.
"""

# Single source of truth for the version. pyproject.toml reads it back via
# hatchling's dynamic-version hook ([tool.hatch.version] path = this file), so
# the distribution version and ``al_dic_3d.__version__`` can never drift.
__version__ = "1.1.0"

__all__ = ["__version__"]
