"""Run-time warnings reach the console log as user-facing, translated text.

Fix batch V (H2 / M10): a seedless run logged "init_guess='seed' but no seed
point was placed — falling back to FFT seeding." — code names, in English.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import warnings

import pytest

pytest.importorskip("PySide6")

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.run_worker import RunWorker  # noqa: E402
from al_dic_3d.gui.warning_text import warning_text  # noqa: E402

NO_SEED = "init_guess='seed' but no seed point was placed — falling back to FFT seeding."


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def test_the_seed_fallback_reads_as_a_user_message(qapp):
    text = warning_text(NO_SEED)
    assert "init_guess" not in text
    assert text.startswith("No Starting Point placed")


def test_the_fft_clamp_names_its_numbers(qapp):
    text = warning_text("Auto-scaled FFT search region: 48 -> 26 (image 200x300)")
    assert text == "FFT search range reduced from 48 to 26 px to fit the 300 × 200 px images"


def test_other_warnings_are_shown_unchanged(qapp):
    other = "seed propagation failed (boom) — falling back to FFT seeding."
    assert warning_text(other) == other


def test_the_run_worker_logs_the_user_text(qapp):
    class _Controller:
        def run(self, progress, stop):
            warnings.warn(NO_SEED, UserWarning, stacklevel=1)

    worker = RunWorker(_Controller())
    logged: list[tuple[str, str]] = []
    worker.log.connect(lambda text, level: logged.append((text, level)))
    worker.run()  # synchronously, on this thread
    assert logged == [(warning_text(NO_SEED), "warning")]
