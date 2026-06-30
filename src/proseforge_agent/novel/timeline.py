"""Timeline event storage and consistency checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


TIMELINE_NAME = "timeline.yaml"


@dataclass(frozen=True)
class TimelineEvent:
    """One ordered story timeline event."""

    id: str
    title: str
    absolute_date: str = ""
    relative_date: str = ""
    story_day: int | None = None
    order: int = 0
    parallel: bool = False
    characters: list[str] = field(default_factory=list)
    location: str = ""
    causes: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    chapter_id: str = ""
    scene_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TimelineEvent":
        return cls(
            id=str(payload.get("id") or ""),
            title=str(payload.get("title") or ""),
            absolute_date=str(payload.get("absolute_date") or ""),
            relative_date=str(payload.get("relative_date") or ""),
            story_day=_optional_int(payload.get("story_day")),
            order=int(payload.get("order") or 0),
            parallel=bool(payload.get("parallel", False)),
            characters=[str(item) for item in payload.get("characters", [])],
            location=str(payload.get("location") or ""),
            causes=[str(item) for item in payload.get("causes", [])],
            effects=[str(item) for item in payload.get("effects", [])],
            chapter_id=str(payload.get("chapter_id") or ""),
            scene_id=str(payload.get("scene_id") or ""),
        )


class TimelineEngine:
    """Manage event order, parallel events, and character location conflicts."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.path = self.project_root / TIMELINE_NAME

    def add_event(
        self,
        *,
        id: str,
        title: str,
        absolute_date: str = "",
        relative_date: str = "",
        story_day: int | None = None,
        order: int = 0,
        parallel: bool = False,
        characters: list[str] | None = None,
        location: str = "",
        causes: list[str] | None = None,
        effects: list[str] | None = None,
        chapter_id: str = "",
        scene_id: str = "",
    ) -> TimelineEvent:
        event = TimelineEvent(
            id=id,
            title=title,
            absolute_date=absolute_date,
            relative_date=relative_date,
            story_day=story_day,
            order=order,
            parallel=parallel,
            characters=list(characters or []),
            location=location,
            causes=list(causes or []),
            effects=list(effects or []),
            chapter_id=chapter_id,
            scene_id=scene_id,
        )
        events = [item for item in self._events() if item.id != event.id]
        events.append(event)
        self._write(events)
        return event

    def view(self) -> list[TimelineEvent]:
        return sorted(self._events(), key=_sort_key)

    def check(self) -> list[dict[str, Any]]:
        events = self.view()
        conflicts: list[dict[str, Any]] = []
        conflicts.extend(_character_location_conflicts(events))
        conflicts.extend(_missing_causal_links(events, len(conflicts)))
        return conflicts

    def _events(self) -> list[TimelineEvent]:
        if not self.path.exists():
            return []
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return [TimelineEvent.from_dict(item) for item in payload.get("events", [])]

    def _write(self, events: list[TimelineEvent]) -> None:
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(
                {"events": [event.to_dict() for event in events]},
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )


def _character_location_conflicts(events: list[TimelineEvent]) -> list[dict[str, Any]]:
    slots: dict[tuple[int | None, int, str], dict[str, Any]] = {}
    for event in events:
        if not event.location:
            continue
        for character in event.characters:
            key = (event.story_day, event.order, character)
            slot = slots.setdefault(
                key,
                {
                    "character": character,
                    "story_day": event.story_day,
                    "order": event.order,
                    "locations": [],
                    "events": [],
                },
            )
            if event.location not in slot["locations"]:
                slot["locations"].append(event.location)
            slot["events"].append(event.id)
    conflicts = []
    for slot in slots.values():
        if len(slot["locations"]) > 1:
            conflicts.append(
                {
                    "id": f"timeline_conflict_{len(conflicts) + 1:03d}",
                    "type": "character_location",
                    **slot,
                }
            )
    return conflicts


def _missing_causal_links(events: list[TimelineEvent], offset: int) -> list[dict[str, Any]]:
    ids = {event.id for event in events}
    conflicts: list[dict[str, Any]] = []
    for event in events:
        missing_causes = [item for item in event.causes if item not in ids]
        missing_effects = [item for item in event.effects if item not in ids]
        if missing_causes or missing_effects:
            conflicts.append(
                {
                    "id": f"timeline_conflict_{offset + len(conflicts) + 1:03d}",
                    "type": "missing_causal_link",
                    "event": event.id,
                    "missing_causes": missing_causes,
                    "missing_effects": missing_effects,
                }
            )
    return conflicts


def _sort_key(event: TimelineEvent) -> tuple[int, int, str]:
    story_day = event.story_day if event.story_day is not None else 999999
    return (story_day, event.order, event.id)


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


__all__ = ["TIMELINE_NAME", "TimelineEngine", "TimelineEvent"]
