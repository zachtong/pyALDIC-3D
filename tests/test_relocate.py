"""Qt-free tests for session image auto-relocation (R1.1, 2D c103981 idea).

Covers the candidate search (same-name subfolder, deeper suffixes, the session
dir itself, the unique-subdir scan), the all-names validation, the prompt
fallback with retry/cancel semantics, and the draft rewrite incl. best-effort
mask relocation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from al_dic_3d.project.draft import ProjectDraft
from al_dic_3d.project.relocate import (
    RelocationCancelled,
    find_relocated_dir,
    relocate_draft_images,
    resolve_in_dir,
    sequence_missing,
)


def _make_frames(directory: Path, names: list[str]) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    out = []
    for name in names:
        p = directory / name
        p.write_bytes(b"png")
        out.append(str(p))
    return out


NAMES = ["f_0001.png", "f_0002.png", "f_0003.png"]
OLD = Path("C:/gone/proj/data/left")  # never exists on disk
OLD_PATHS = [str(OLD / n) for n in NAMES]


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


def test_sequence_missing(tmp_path):
    live = _make_frames(tmp_path / "seq", NAMES)
    assert not sequence_missing(live)
    assert not sequence_missing([])  # empty draft: nothing to relocate
    assert sequence_missing(live + [str(tmp_path / "seq" / "nope.png")])


def test_resolve_in_dir_requires_every_name(tmp_path):
    d = tmp_path / "imgs"
    _make_frames(d, NAMES[:2])  # third frame absent
    assert resolve_in_dir(OLD_PATHS, d) is None
    _make_frames(d, NAMES[2:])
    resolved = resolve_in_dir(OLD_PATHS, d)
    assert resolved == [str(d / n) for n in NAMES]  # order preserved
    assert resolve_in_dir(OLD_PATHS, tmp_path / "missing") is None


# ---------------------------------------------------------------------------
# Auto-find candidates
# ---------------------------------------------------------------------------


def test_find_same_named_subfolder_under_session_dir(tmp_path):
    _make_frames(tmp_path / "left", NAMES)
    assert find_relocated_dir(OLD_PATHS, tmp_path) == tmp_path / "left"


def test_find_deeper_suffix_under_session_dir(tmp_path):
    _make_frames(tmp_path / "data" / "left", NAMES)
    assert find_relocated_dir(OLD_PATHS, tmp_path) == tmp_path / "data" / "left"


def test_find_flat_session_dir(tmp_path):
    _make_frames(tmp_path, NAMES)
    assert find_relocated_dir(OLD_PATHS, tmp_path) == tmp_path


def test_find_renamed_subfolder_via_unique_scan(tmp_path):
    _make_frames(tmp_path / "frames_cam0", NAMES)
    assert find_relocated_dir(OLD_PATHS, tmp_path) == tmp_path / "frames_cam0"


def test_ambiguous_subfolder_scan_refuses(tmp_path):
    # L and R folders holding the SAME basenames: picking either would be a
    # silent wrong guess — the scan must refuse and defer to the prompt.
    _make_frames(tmp_path / "cam0", NAMES)
    _make_frames(tmp_path / "cam1", NAMES)
    assert find_relocated_dir(OLD_PATHS, tmp_path) is None


def test_find_nothing_returns_none(tmp_path):
    assert find_relocated_dir(OLD_PATHS, tmp_path) is None
    assert find_relocated_dir([], tmp_path) is None


# ---------------------------------------------------------------------------
# Draft relocation end-to-end
# ---------------------------------------------------------------------------


def test_relocate_noop_when_paths_still_exist(tmp_path):
    left = _make_frames(tmp_path / "L", NAMES)
    right = _make_frames(tmp_path / "R", ["r_" + n for n in NAMES])
    draft = ProjectDraft(left=list(left), right=list(right))
    moves = relocate_draft_images(draft, tmp_path / "s.aldic3d")
    assert moves == []
    assert draft.left == left and draft.right == right


def test_relocate_moved_project_both_cameras(tmp_path):
    # Whole project moved: session + same-named image folders live together.
    new_left = _make_frames(tmp_path / "left", NAMES)
    new_right = _make_frames(tmp_path / "right", ["r_" + n for n in NAMES])
    draft = ProjectDraft(
        left=[str(Path("C:/gone/proj/left") / n) for n in NAMES],
        right=[str(Path("C:/gone/proj/right") / ("r_" + n)) for n in NAMES],
    )
    moves = relocate_draft_images(draft, tmp_path / "proj.aldic3d")
    assert draft.left == new_left and draft.right == new_right
    assert [m.camera for m in moves] == ["L", "R"]
    assert moves[0].n_files == len(NAMES)
    assert moves[0].new_dir == str(tmp_path / "left")


def test_relocate_prompt_fallback_and_retry(tmp_path):
    good = tmp_path / "elsewhere"
    _make_frames(good, NAMES)
    bad = tmp_path / "bad"
    bad.mkdir()
    draft = ProjectDraft(left=list(OLD_PATHS), right=[])
    calls: list[tuple[str, bool]] = []

    def cb(camera: str, old_dir: str, is_retry: bool) -> str:
        calls.append((camera, is_retry))
        return str(bad) if len(calls) == 1 else str(good)

    session = tmp_path / "far" / "s.aldic3d"
    session.parent.mkdir()
    moves = relocate_draft_images(draft, session, locate_dir_cb=cb)
    assert draft.left == [str(good / n) for n in NAMES]
    # First prompt is not a retry; the second (after the bad pick) is.
    assert calls == [("L", False), ("L", True)]
    assert len(moves) == 1 and moves[0].camera == "L"


def test_relocate_cancel_raises(tmp_path):
    draft = ProjectDraft(left=list(OLD_PATHS), right=[])
    with pytest.raises(RelocationCancelled, match="camera L"):
        relocate_draft_images(draft, tmp_path / "s.aldic3d", locate_dir_cb=lambda *a: None)


def test_relocate_without_callback_raises(tmp_path):
    draft = ProjectDraft(left=list(OLD_PATHS), right=[])
    with pytest.raises(RelocationCancelled):
        relocate_draft_images(draft, tmp_path / "s.aldic3d")


def test_relocate_prompt_attempts_bounded(tmp_path):
    bad = tmp_path / "bad"
    bad.mkdir()
    draft = ProjectDraft(left=list(OLD_PATHS), right=[])
    calls: list[str] = []

    def cb(camera: str, old_dir: str, is_retry: bool) -> str:
        calls.append(camera)
        return str(bad)  # always invalid: must not loop forever

    with pytest.raises(RelocationCancelled):
        relocate_draft_images(draft, tmp_path / "s.aldic3d", locate_dir_cb=cb)
    assert len(calls) == 5  # _MAX_PROMPT_ATTEMPTS


def test_relocate_masks_best_effort_auto_only(tmp_path):
    _make_frames(tmp_path / "left", NAMES)
    mask_names = ["m_0001.png", "m_0002.png", "m_0003.png"]
    _make_frames(tmp_path / "masks", mask_names)
    lost_names = ["q_0001.png", "q_0002.png", "q_0003.png"]  # exist nowhere
    draft = ProjectDraft(
        left=list(OLD_PATHS),
        right=[],
        left_masks=[str(Path("C:/gone/proj/masks") / n) for n in mask_names],
        right_masks=[str(Path("C:/gone/proj/nowhere") / n) for n in lost_names],
    )
    relocate_draft_images(draft, tmp_path / "s.aldic3d")
    assert draft.left == [str(tmp_path / "left" / n) for n in NAMES]
    assert draft.left_masks == [str(tmp_path / "masks" / n) for n in mask_names]
    # Unresolvable masks stay untouched (best effort, never a prompt/abort).
    assert draft.right_masks == [str(Path("C:/gone/proj/nowhere") / n) for n in lost_names]
