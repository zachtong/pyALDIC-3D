"""Concrete correspondence strategies.

Importing this package registers every built-in strategy (via the
``@register_strategy`` decorator) so :func:`al_dic_3d.matching.get_strategy` can
resolve them by name. Downstream modules must NOT import these classes directly —
they consume only the ``CorrespondenceSet`` contract (architecture invariant,
enforced by ``tests/test_architecture.py``).
"""

from al_dic_3d.matching.strategies.track_both import TrackBothStrategy

__all__ = ["TrackBothStrategy"]
