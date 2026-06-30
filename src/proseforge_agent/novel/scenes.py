"""Scene-level local writing workflow."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .artifacts import ArtifactGraphStore, ArtifactRecord
from .manifest import MANIFEST_NAME


@dataclass(frozen=True)
class SceneRecord:
    """One scene's workflow state."""

    id: str
    chapter_id: str
    goal: str = ""
    location: str = ""
    characters: list[str] = field(default_factory=list)
    conflict: str = ""
    emotional_tone: str = ""
    output_file: Path = Path()
    status: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["output_file"] = str(self.output_file)
        return payload


class SceneWorkflow:
    """Draft, review, rewrite, and merge scenes without external providers."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug

    def draft(
        self,
        *,
        chapter_id: str,
        scene_id: str,
        goal: str = "",
        location: str = "",
        characters: list[str] | None = None,
        conflict: str = "",
        emotional_tone: str = "",
    ) -> SceneRecord:
        path = self.project_root / "scenes" / chapter_id / f"{scene_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        record = SceneRecord(
            id=scene_id,
            chapter_id=chapter_id,
            goal=goal or f"Draft scene {scene_id}",
            location=location,
            characters=list(characters or []),
            conflict=conflict,
            emotional_tone=emotional_tone,
            output_file=path,
            status="drafted",
        )
        path.write_text(_render_scene(record), encoding="utf-8")
        self._upsert_scene(record)
        ArtifactGraphStore(self.root, slug=self.slug).add(
            ArtifactRecord(id=f"scene_{scene_id}_draft", type="scene_draft", provider="local", prompt_version="scene-v1")
        )
        return record

    def review(self, *, scene_id: str) -> SceneRecord:
        record = self._load_scene(scene_id)
        reviewed = self._replace(record, status="reviewed")
        review_path = reviewed.output_file.with_suffix(".review.md")
        review_path.write_text(f"# Review {scene_id}\nstatus: reviewed\n", encoding="utf-8")
        self._upsert_scene(reviewed)
        ArtifactGraphStore(self.root, slug=self.slug).add(
            ArtifactRecord(
                id=f"scene_{scene_id}_review",
                type="scene_review",
                depends_on=[f"scene_{scene_id}_draft"],
                provider="local",
                prompt_version="scene-v1",
            )
        )
        return reviewed

    def rewrite(self, *, scene_id: str) -> SceneRecord:
        record = self._load_scene(scene_id)
        rewritten = self._replace(record, status="rewritten")
        rewritten.output_file.write_text(
            rewritten.output_file.read_text(encoding="utf-8").rstrip() + "\n\n[rewrite pass complete]\n",
            encoding="utf-8",
        )
        self._upsert_scene(rewritten)
        ArtifactGraphStore(self.root, slug=self.slug).add(
            ArtifactRecord(
                id=f"scene_{scene_id}_rewrite",
                type="scene_rewrite",
                depends_on=[f"scene_{scene_id}_review"],
                provider="local",
                prompt_version="scene-v1",
            )
        )
        return rewritten

    def merge(self, *, chapter_id: str) -> Path:
        scenes = [scene for scene in self._scenes() if scene.chapter_id == chapter_id]
        scenes.sort(key=lambda scene: scene.id)
        chapter_path = self.project_root / "chapters" / f"{chapter_id}.md"
        chapter_path.parent.mkdir(parents=True, exist_ok=True)
        parts = []
        for scene in scenes:
            parts.append(f"<!-- {scene.id} -->\n" + scene.output_file.read_text(encoding="utf-8").strip())
        chapter_path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
        ArtifactGraphStore(self.root, slug=self.slug).add(
            ArtifactRecord(
                id=f"chapter_{chapter_id}_merged",
                type="chapter_draft",
                depends_on=[f"scene_{scene.id}_rewrite" for scene in scenes],
                provider="local",
                prompt_version="scene-v1",
            )
        )
        return chapter_path

    def _scenes(self) -> list[SceneRecord]:
        manifest = self._load_manifest()
        return [_scene_from_dict(item) for item in manifest.get("structure", {}).get("scenes", [])]

    def _load_scene(self, scene_id: str) -> SceneRecord:
        for scene in self._scenes():
            if scene.id == scene_id:
                return scene
        raise KeyError(f"scene {scene_id!r} not found")

    def _upsert_scene(self, record: SceneRecord) -> None:
        manifest = self._load_manifest()
        structure = dict(manifest.get("structure") or {})
        scenes = [item for item in structure.get("scenes", []) if item.get("id") != record.id]
        scenes.append(record.to_dict())
        structure["scenes"] = scenes
        manifest["structure"] = structure
        self._write_manifest(manifest)

    def _load_manifest(self) -> dict[str, Any]:
        path = self.project_root / MANIFEST_NAME
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("project: {}\nstructure:\n  scenes: []\n", encoding="utf-8")
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def _write_manifest(self, payload: dict[str, Any]) -> None:
        path = self.project_root / MANIFEST_NAME
        path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    @staticmethod
    def _replace(record: SceneRecord, **changes) -> SceneRecord:
        data = record.to_dict()
        data.update(changes)
        data["output_file"] = Path(data["output_file"])
        return _scene_from_dict(data)


def _render_scene(record: SceneRecord) -> str:
    return "\n".join(
        [
            f"# {record.id}",
            f"goal: {record.goal}",
            f"location: {record.location}",
            f"characters: {', '.join(record.characters)}",
            f"conflict: {record.conflict}",
            f"emotional_tone: {record.emotional_tone}",
            "",
            f"Scene draft for {record.id}.",
        ]
    ) + "\n"


def _scene_from_dict(payload: dict[str, Any]) -> SceneRecord:
    return SceneRecord(
        id=str(payload["id"]),
        chapter_id=str(payload.get("chapter_id") or ""),
        goal=str(payload.get("goal") or ""),
        location=str(payload.get("location") or ""),
        characters=list(payload.get("characters") or []),
        conflict=str(payload.get("conflict") or ""),
        emotional_tone=str(payload.get("emotional_tone") or ""),
        output_file=Path(str(payload.get("output_file") or "")),
        status=str(payload.get("status") or "planned"),
    )


__all__ = ["SceneRecord", "SceneWorkflow"]
