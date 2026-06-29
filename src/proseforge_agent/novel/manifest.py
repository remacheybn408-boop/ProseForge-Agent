"""Novel project manifest management."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


MANIFEST_NAME = "project.manifest.yaml"


@dataclass(frozen=True)
class NovelProjectManifest:
    """Loaded project manifest plus its path."""

    path: Path
    project: dict[str, Any]
    structure: dict[str, Any] = field(default_factory=dict)
    assets: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": dict(self.project),
            "structure": dict(self.structure),
            "assets": dict(self.assets),
            "metadata": dict(self.metadata),
        }


class NovelProjectStore:
    """Create, load, and validate per-novel project manifests."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def init_project(
        self,
        *,
        slug: str,
        title: str | None = None,
        author: str | None = None,
        language: str = "zh-CN",
    ) -> NovelProjectManifest:
        path = self.path_for(slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            return self.load(slug)
        manifest = NovelProjectManifest(
            path=path,
            project={
                "slug": slug,
                "title": title or slug.replace("_", " ").title(),
                "author": author or "",
                "language": language,
            },
            structure={"volumes": [], "acts": [], "chapters": [], "scenes": []},
            assets={
                "drafts": [],
                "exports": [],
                "bible": [],
                "rules": [],
                "timeline": [],
            },
            metadata={},
        )
        path.write_text(
            yaml.safe_dump(manifest.to_dict(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return manifest

    def load(self, slug: str) -> NovelProjectManifest:
        path = self.path_for(slug)
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return NovelProjectManifest(
            path=path,
            project=dict(payload.get("project") or {}),
            structure=dict(payload.get("structure") or {}),
            assets=dict(payload.get("assets") or {}),
            metadata=dict(payload.get("metadata") or {}),
        )

    def validate(self, slug: str) -> dict[str, Any]:
        errors: list[str] = []
        path = self.path_for(slug)
        if not path.exists():
            return {"status": "invalid", "errors": ["manifest missing"], "path": str(path)}
        manifest = self.load(slug)
        for key in ("slug", "title", "language"):
            if not manifest.project.get(key):
                errors.append(f"project.{key} missing")
        if manifest.project.get("slug") != slug:
            errors.append("project.slug does not match requested slug")
        for key in ("volumes", "acts", "chapters", "scenes"):
            if key not in manifest.structure:
                errors.append(f"structure.{key} missing")
        for key in ("drafts", "exports", "bible", "rules", "timeline"):
            if key not in manifest.assets:
                errors.append(f"assets.{key} missing")
        return {"status": "ok" if not errors else "invalid", "errors": errors, "path": str(path)}

    def path_for(self, slug: str) -> Path:
        return self.root / "projects" / slug / MANIFEST_NAME


__all__ = ["MANIFEST_NAME", "NovelProjectManifest", "NovelProjectStore"]
