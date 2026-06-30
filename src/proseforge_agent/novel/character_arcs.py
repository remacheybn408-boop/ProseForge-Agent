"""Character arc tracking and reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


CHARACTER_ARCS_NAME = "character_arcs.yaml"


@dataclass(frozen=True)
class CharacterArc:
    """One character's long-form emotional and narrative arc."""

    character_id: str
    desire: str = ""
    fear: str = ""
    flaw: str = ""
    belief: str = ""
    turning_points: list[dict[str, str]] = field(default_factory=list)
    relationship_changes: list[dict[str, str]] = field(default_factory=list)
    chapter_appearances: list[str] = field(default_factory=list)
    arc_status: str = "introduced"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CharacterArc":
        return cls(
            character_id=str(payload.get("character_id") or ""),
            desire=str(payload.get("desire") or ""),
            fear=str(payload.get("fear") or ""),
            flaw=str(payload.get("flaw") or ""),
            belief=str(payload.get("belief") or ""),
            turning_points=[dict(item) for item in payload.get("turning_points", [])],
            relationship_changes=[dict(item) for item in payload.get("relationship_changes", [])],
            chapter_appearances=[str(item) for item in payload.get("chapter_appearances", [])],
            arc_status=str(payload.get("arc_status") or "introduced"),
        )


class CharacterArcTracker:
    """Initialize, update, and report character arcs."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.path = self.project_root / CHARACTER_ARCS_NAME

    def init_arc(
        self,
        *,
        character_id: str,
        desire: str = "",
        fear: str = "",
        flaw: str = "",
        belief: str = "",
        arc_status: str = "introduced",
    ) -> CharacterArc:
        existing = self._find(character_id)
        arc = CharacterArc(
            character_id=character_id,
            desire=desire or (existing.desire if existing else ""),
            fear=fear or (existing.fear if existing else ""),
            flaw=flaw or (existing.flaw if existing else ""),
            belief=belief or (existing.belief if existing else ""),
            turning_points=existing.turning_points if existing else [],
            relationship_changes=existing.relationship_changes if existing else [],
            chapter_appearances=existing.chapter_appearances if existing else [],
            arc_status=arc_status or (existing.arc_status if existing else "introduced"),
        )
        self._upsert(arc)
        return arc

    def update_arc(
        self,
        *,
        character_id: str,
        desire: str = "",
        fear: str = "",
        flaw: str = "",
        belief: str = "",
        turning_points: list[dict[str, str]] | None = None,
        relationship_changes: list[dict[str, str]] | None = None,
        chapter_appearances: list[str] | None = None,
        arc_status: str = "",
    ) -> CharacterArc:
        existing = self._find(character_id) or CharacterArc(character_id=character_id)
        arc = CharacterArc(
            character_id=character_id,
            desire=desire or existing.desire,
            fear=fear or existing.fear,
            flaw=flaw or existing.flaw,
            belief=belief or existing.belief,
            turning_points=[*existing.turning_points, *list(turning_points or [])],
            relationship_changes=[*existing.relationship_changes, *list(relationship_changes or [])],
            chapter_appearances=_unique([*existing.chapter_appearances, *list(chapter_appearances or [])]),
            arc_status=arc_status or existing.arc_status,
        )
        self._upsert(arc)
        return arc

    def report(self) -> dict[str, Any]:
        arcs = sorted(self._arcs(), key=lambda item: item.character_id)
        return {
            "characters": [arc.to_dict() for arc in arcs],
            "summary": [
                (
                    f"{arc.character_id}: {arc.arc_status}, "
                    f"{len(arc.turning_points)} turning points, "
                    f"{len(arc.chapter_appearances)} appearances"
                )
                for arc in arcs
            ],
        }

    def _find(self, character_id: str) -> CharacterArc | None:
        return next((arc for arc in self._arcs() if arc.character_id == character_id), None)

    def _upsert(self, arc: CharacterArc) -> None:
        arcs = [item for item in self._arcs() if item.character_id != arc.character_id]
        arcs.append(arc)
        self._write(arcs)

    def _arcs(self) -> list[CharacterArc]:
        if not self.path.exists():
            return []
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return [CharacterArc.from_dict(item) for item in payload.get("characters", [])]

    def _write(self, arcs: list[CharacterArc]) -> None:
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(
                {"characters": [arc.to_dict() for arc in arcs]},
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


__all__ = ["CHARACTER_ARCS_NAME", "CharacterArc", "CharacterArcTracker"]
