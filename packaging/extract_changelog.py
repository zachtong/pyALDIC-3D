"""Print one version's section of CHANGELOG.md, for use as GitHub release notes.

    python packaging/extract_changelog.py 1.2.0              # or v1.2.0
    python packaging/extract_changelog.py 1.2.0 -o notes.md  # write a file
    python packaging/extract_changelog.py Unreleased         # preview

Prints the body of the ``## [1.2.0] ...`` section (its heading excluded), with
HTML comments and subsections left empty by them removed, followed by the
section's compare link when the file defines one (``[1.2.0]: https://...``).

Exit status 0 on success; 1 when the file has no non-empty section for that
version, so a caller can fall back to GitHub's generated notes -- which is what
``.github/workflows/publish.yml`` does.

Standard library only: it runs on a bare ``ubuntu-latest`` runner before
anything is installed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"

# "## [1.2.0] — 2026-08-01", "## [1.2.0] - 2026-08-01", "## 1.2.0", "## [Unreleased]".
# "### ..." never matches: the character after "##" must be whitespace.
_SECTION = re.compile(r"^##\s+\[?(?P<name>[^\]\s]+)\]?(?:\s.*)?$")
_SUBSECTION = re.compile(r"^###\s")
_LINK_REF = re.compile(r"^\[(?P<name>[^\]]+)\]:\s*(?P<url>\S+)\s*$")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def normalize_version(raw: str) -> str:
    """``" v1.2.0 "`` -> ``"1.2.0"``; lower-cased so ``Unreleased`` matches any case."""
    name = raw.strip()
    if name[:1] in ("v", "V") and name[1:2].isdigit():
        name = name[1:]
    return name.lower()


def _is_boundary(line: str) -> bool:
    """A line that ends a section: the next ``## `` heading or a link reference."""
    return bool(_SECTION.match(line) or _LINK_REF.match(line))


def _drop_empty_subsections(lines: list[str]) -> list[str]:
    """Remove ``### Heading`` blocks that have no content left."""
    kept: list[str] = []
    block: list[str] | None = None
    for line in [*lines, "### <end>"]:
        if _SUBSECTION.match(line):
            if block is not None and any(item.strip() for item in block[1:]):
                kept.extend(block)
            block = [line]
        elif block is not None:
            block.append(line)
        else:
            kept.append(line)
    return kept


def extract_section(text: str, version: str) -> str | None:
    """Return the cleaned body of *version*'s section, or None if absent or empty."""
    wanted = normalize_version(version)
    lines = text.splitlines()
    start = next(
        (
            i + 1
            for i, line in enumerate(lines)
            if (m := _SECTION.match(line)) and normalize_version(m.group("name")) == wanted
        ),
        None,
    )
    if start is None:
        return None
    # The section ends at the next "## " heading or at the link references.
    boundaries = (j for j in range(start, len(lines)) if _is_boundary(lines[j]))
    end = next(boundaries, len(lines))
    body = _COMMENT.sub("", "\n".join(lines[start:end]))
    body = "\n".join(_drop_empty_subsections(body.splitlines()))
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body or None


def compare_link(text: str, version: str) -> str | None:
    """The ``[version]: url`` reference for *version*, when it is a compare URL."""
    wanted = normalize_version(version)
    for line in text.splitlines():
        m = _LINK_REF.match(line)
        if m and normalize_version(m.group("name")) == wanted and "/compare/" in m.group("url"):
            return m.group("url")
    return None


def release_notes(text: str, version: str) -> str | None:
    """Section body plus its compare link, ready to use as a release body."""
    body = extract_section(text, version)
    if body is None:
        return None
    link = compare_link(text, version)
    return f"{body}\n\n**Full Changelog**: {link}\n" if link else f"{body}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print one version's CHANGELOG.md section (GitHub release notes)."
    )
    parser.add_argument("version", help="version to extract: 1.2.0, v1.2.0 or Unreleased")
    parser.add_argument(
        "--changelog",
        type=Path,
        default=DEFAULT_CHANGELOG,
        help="changelog file (default: CHANGELOG.md at the repository root)",
    )
    parser.add_argument("-o", "--output", type=Path, help="write the notes here, not to stdout")
    args = parser.parse_args(argv)

    try:
        text = args.changelog.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"extract_changelog: cannot read {args.changelog}: {exc}", file=sys.stderr)
        return 1
    notes = release_notes(text, args.version)
    if notes is None:
        print(
            f"extract_changelog: {args.changelog} has no non-empty section for {args.version!r}",
            file=sys.stderr,
        )
        return 1
    if args.output is not None:
        args.output.write_text(notes, encoding="utf-8")
    else:
        sys.stdout.buffer.write(notes.encode("utf-8"))
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
