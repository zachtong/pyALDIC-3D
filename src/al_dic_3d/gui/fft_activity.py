"""When the temporal-FFT knobs actually bite (A4-1 honesty helper) — Qt-free.

The 3D layer ALWAYS hands the 2D engine an external frame-1 mesh, so the engine
runs its FFT integer search ONLY when it has no ``U0`` to warm-start from
(``need_fft = dic_mesh is None or current_U0 is None``; pyALDIC
``core/pipeline.py``). Two selections make ``current_U0`` None on that path:

* ``init_guess == "fft"`` passes ``U0 = None`` — FFT seeds frame 1 (and every
  reference switch).
* ``reference_mode == "incremental"`` makes every frame a reference switch,
  which clears the sibling warm start and forces FFT regardless of
  ``init_guess`` (the passed ``U0`` only ever seeds frame 1). The ``every_n`` /
  ``custom`` reference-update policies live only inside incremental mode, so
  they are covered by the mode check.

In ``accumulative`` + ``seed`` / ``previous`` a non-None ``U0`` is supplied and
the per-frame FFT force / periodic ``fft_reset`` are BOTH gated
``and not mesh_is_external`` — so no FFT ever runs and the ``fft_search`` /
``fft_auto_expand`` controls are inert no-ops. The GUI greys them out in that
state so they can never masquerade as large-motion protection they do not give.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from al_dic_3d.project.draft import ProjectDraft


def fft_controls_active(draft: ProjectDraft) -> bool:
    """True when ``fft_search`` / ``fft_auto_expand`` can affect the run.

    See the module docstring for the engine conditions. Equivalent to: FFT
    seeding is selected, or the reference switches (incremental mode) force it.
    """
    return draft.init_guess == "fft" or draft.reference_mode == "incremental"
