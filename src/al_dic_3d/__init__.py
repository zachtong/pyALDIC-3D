"""pyALDIC-3D: stereo / multi-camera Digital Image Correlation.

An **independent application** (import package ``al_dic_3d``, distribution
``al-dic-3d``, CLI ``al-dic-3d``, session format ``.aldic3d``) built on top of
the pyALDIC-2D platform, which it consumes as a **pinned, read-only library**
(``al-dic==0.6.*``). It is NOT a "3D mode" inside the 2D app.

The stereo/temporal-correlation algorithms are not implemented yet; this is the
Phase 0 scaffold. See ``docs/architecture/`` (start with ``00_INDEX.md``) for the
technical baseline, and ``docs/DEPENDS_ON_2D.md`` for the 2D coupling ledger.
"""

# Single source of truth for the version. pyproject.toml reads it back via
# hatchling's dynamic-version hook ([tool.hatch.version] path = this file), so
# the distribution version and ``al_dic_3d.__version__`` can never drift.
__version__ = "0.1.0.dev0"

__all__ = ["__version__"]
