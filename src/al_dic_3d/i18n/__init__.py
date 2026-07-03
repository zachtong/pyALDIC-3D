"""i18n — translation catalogs and runtime loading.

pyALDIC-3D's own ``.ts`` / ``.qm`` catalogs. At runtime, both the ``al-dic`` and
``al-dic-3d`` ``QTranslator`` instances are installed so reused 2D widgets and
new 3D UI are translated from their respective catalogs.

The full 8-locale contract (en, zh_CN, zh_TW, ja, ko, de, fr, es) is ported from
the 2D repo at Phase 4 — see CLAUDE.md "Engineering rules".

Layer: presentation (GUI).  Lands: Phase 4.  Spec: docs/architecture/01 §B.1.
"""
