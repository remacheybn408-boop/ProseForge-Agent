"""Explicit canon bible management."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml


BIBLE_SECTIONS: dict[str, str] = {
    "character": "characters",
    "characters": "characters",
    "location": "locations",
    "locations": "locations",
    "faction": "factions",
    "factions": "factions",
    "item": "items",
    "items": "items",
    "rule": "rules",
    "rules": "rules",
    "worldbuilding": "worldbuilding",
    "terminology": "terminology",
}


class CanonBibleManager:
    """Manage explicit, frozen, snapshot-able canon bible files."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.bible_root = self.project_root / "bible"

    def add(self, section: str, entry: dict[str, Any]) -> dict[str, Any]:
        if self._frozen():
            return {"status": "frozen", "section": _section(section)}
        name = _section(section)
        entries = self.list(name)
        if not entry.get("id"):
            entry = {"id": f"{name}_{len(entries) + 1:03d}", **entry}
        entries = [item for item in entries if item.get("id") != entry["id"]]
        entries.append(dict(entry))
        self._write(name, entries)
        return {"status": "ok", "section": name, "id": entry["id"]}

    def list(self, section: str) -> list[dict[str, Any]]:
        name = _section(section)
        path = self._path(name)
        if not path.exists():
            return []
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return list(payload.get(name, []))

    def freeze(self) -> dict[str, Any]:
        self.bible_root.mkdir(parents=True, exist_ok=True)
        (self.bible_root / ".frozen").write_text("true\n", encoding="utf-8")
        return {"status": "ok", "frozen": True}

    def snapshot(self) -> dict[str, Any]:
        payload = {name: self.list(name) for name in sorted(set(BIBLE_SECTIONS.values()))}
        digest = hashlib.sha256(yaml.safe_dump(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
        snapshot_id = f"bible_snapshot_{digest}"
        path = self.project_root / "bible" / "snapshots" / f"{snapshot_id}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return {"status": "ok", "id": snapshot_id, "path": str(path.relative_to(self.root))}

    def evidence(self, query: str) -> list[dict[str, Any]]:
        needle = query.lower()
        matches: list[dict[str, Any]] = []
        for section in sorted(set(BIBLE_SECTIONS.values())):
            for item in self.list(section):
                haystack = yaml.safe_dump(item, allow_unicode=True).lower()
                if needle in haystack:
                    matches.append({"section": section, "item": item})
        return matches

    def _write(self, section: str, entries: list[dict[str, Any]]) -> None:
        self.bible_root.mkdir(parents=True, exist_ok=True)
        self._path(section).write_text(
            yaml.safe_dump({section: entries}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def _path(self, section: str) -> Path:
        return self.bible_root / f"{section}.yaml"

    def _frozen(self) -> bool:
        return (self.bible_root / ".frozen").exists()


def _section(value: str) -> str:
    normalized = (value or "").lower().strip()
    if normalized not in BIBLE_SECTIONS:
        raise ValueError(f"unknown bible section {value!r}")
    return BIBLE_SECTIONS[normalized]


__all__ = ["BIBLE_SECTIONS", "CanonBibleManager"]
