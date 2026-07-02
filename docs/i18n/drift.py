"""README translation drift checker (Task 193).

Compares the H1-H3 header *structure* (level sequence) of the source README
and a translation. Header text is intentionally NOT compared — translations
localize the header text — so drift means a structural divergence: a section
added on one side but not the other, or a heading level that changed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_HEADER_RE = re.compile(r"^(#{1,3})\s+(.*\S)\s*$")


@dataclass
class DriftReport:
    matched: int
    extra_in_source: list[str] = field(default_factory=list)
    extra_in_translation: list[str] = field(default_factory=list)


def _headers(path: Path) -> list[tuple[int, str]]:
    headers: list[tuple[int, str]] = []
    in_fence = False
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = _HEADER_RE.match(line)
        if match:
            headers.append((len(match.group(1)), match.group(2)))
    return headers


def compare_readmes(english: str | Path, translation: str | Path) -> DriftReport:
    source = _headers(english)
    target = _headers(translation)

    extra_source: list[str] = []
    extra_translation: list[str] = []
    matched = 0
    limit = min(len(source), len(target))
    for index in range(limit):
        if source[index][0] == target[index][0]:
            matched += 1
        else:
            extra_source.append(f"L{source[index][0]}: {source[index][1]}")
            extra_translation.append(f"L{target[index][0]}: {target[index][1]}")

    extra_source.extend(f"L{level}: {text}" for level, text in source[limit:])
    extra_translation.extend(f"L{level}: {text}" for level, text in target[limit:])

    return DriftReport(
        matched=matched,
        extra_in_source=extra_source,
        extra_in_translation=extra_translation,
    )


__all__ = ["DriftReport", "compare_readmes"]
