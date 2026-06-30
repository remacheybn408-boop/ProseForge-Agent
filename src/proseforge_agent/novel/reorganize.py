"""Non-destructive chapter reorganization."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .artifacts import ArtifactGraphStore, ArtifactRecord
from .manifest import MANIFEST_NAME


class ChapterReorganizer:
    """Move, split, merge, and renumber chapter records in a manifest."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug

    def move(self, chapter_id: str, *, to_volume: str | None = None, after: str | None = None) -> dict[str, Any]:
        payload = self._load()
        chapters = list(payload.get("structure", {}).get("chapters", []))
        chapter = _take(chapters, chapter_id)
        if chapter is None:
            return {"status": "missing", "chapter": chapter_id}
        if to_volume:
            chapter["volume_id"] = to_volume
        index = _after_index(chapters, after) if after else len(chapters)
        chapters.insert(index, chapter)
        payload.setdefault("structure", {})["chapters"] = chapters
        self._write(payload)
        self._log(f"move {chapter_id} to_volume={to_volume or ''} after={after or ''}")
        self._artifact("chapter_move", f"reorg_move_{chapter_id}", [chapter_id])
        return {"status": "ok", "chapter": chapter_id, "to_volume": to_volume, "after": after}

    def split(self, chapter_id: str, *, at_scene: str) -> dict[str, Any]:
        payload = self._load()
        structure = payload.setdefault("structure", {})
        chapters = list(structure.get("chapters", []))
        if not any(chapter.get("id") == chapter_id for chapter in chapters):
            chapters.append({"id": chapter_id, "title": chapter_id})
        new_id = f"{chapter_id}_part_2"
        if not any(chapter.get("id") == new_id for chapter in chapters):
            index = _after_index(chapters, chapter_id)
            chapters.insert(index, {"id": new_id, "title": f"{chapter_id} part 2", "split_from": chapter_id, "at_scene": at_scene})
        structure["chapters"] = chapters
        self._write(payload)
        self._log(f"split {chapter_id} at {at_scene}")
        self._artifact("chapter_split", f"reorg_split_{chapter_id}", [chapter_id, at_scene])
        return {"status": "ok", "chapter": chapter_id, "new_chapter": new_id, "at_scene": at_scene}

    def merge(self, left: str, right: str, *, into: str) -> dict[str, Any]:
        payload = self._load()
        chapters = list(payload.get("structure", {}).get("chapters", []))
        merged = None
        kept: list[dict[str, Any]] = []
        for chapter in chapters:
            if chapter.get("id") == into:
                merged = dict(chapter)
                merged["merged_from"] = [left, right]
                kept.append(merged)
            elif chapter.get("id") not in {left, right}:
                kept.append(chapter)
        if merged is None:
            kept.append({"id": into, "title": into, "merged_from": [left, right]})
        payload.setdefault("structure", {})["chapters"] = kept
        self._write(payload)
        self._log(f"merge {left} {right} into {into}")
        self._artifact("chapter_merge", f"reorg_merge_{into}", [left, right])
        return {"status": "ok", "into": into, "merged_from": [left, right]}

    def renumber(self) -> dict[str, Any]:
        payload = self._load()
        structure = payload.setdefault("structure", {})
        chapters = list(structure.get("chapters", []))
        mapping: dict[str, str] = {}
        for index, chapter in enumerate(chapters, start=1):
            old = str(chapter.get("id"))
            new = f"ch_{index:03d}"
            mapping[old] = new
            chapter["id"] = new
        for scene in structure.get("scenes", []) or []:
            old_chapter = scene.get("chapter_id")
            if old_chapter in mapping:
                scene["chapter_id"] = mapping[old_chapter]
        structure["chapters"] = chapters
        self._write(payload)
        self._log(f"renumber {mapping}")
        self._artifact("chapter_renumber", "reorg_renumber", list(mapping))
        return {"status": "ok", "mapping": mapping}

    def _load(self) -> dict[str, Any]:
        path = self.project_root / MANIFEST_NAME
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
        return payload or {"project": {"slug": self.slug}, "structure": {"chapters": [], "scenes": []}}

    def _write(self, payload: dict[str, Any]) -> None:
        path = self.project_root / MANIFEST_NAME
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def _log(self, line: str) -> None:
        path = self.project_root / "reorg.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{stamp} {line}\n")

    def _artifact(self, artifact_type: str, artifact_id: str, depends_on: list[str]) -> None:
        ArtifactGraphStore(self.root, slug=self.slug).add(
            ArtifactRecord(
                id=artifact_id,
                type=artifact_type,
                depends_on=depends_on,
                provider="local",
                prompt_version="chapter-reorg-v1",
            )
        )


def _take(chapters: list[dict[str, Any]], chapter_id: str) -> dict[str, Any] | None:
    for index, chapter in enumerate(chapters):
        if chapter.get("id") == chapter_id:
            return chapters.pop(index)
    return None


def _after_index(chapters: list[dict[str, Any]], after: str | None) -> int:
    if not after:
        return len(chapters)
    for index, chapter in enumerate(chapters):
        if chapter.get("id") == after:
            return index + 1
    return len(chapters)


__all__ = ["ChapterReorganizer"]
