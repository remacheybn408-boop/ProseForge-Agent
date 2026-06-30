"""Publishing metadata management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PUBLISHING_NAME = "publishing.yaml"


DEFAULT_METADATA: dict[str, Any] = {
    "title": "",
    "subtitle": "",
    "author": "",
    "pen_name": "",
    "summary": "",
    "keywords": [],
    "copyright": "",
    "ai_usage_statement": "",
    "platform_profiles": {},
}


@dataclass(frozen=True)
class PublishingMetadata:
    """Loaded publishing metadata plus path."""

    path: Path
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"path": str(self.path), "data": dict(self.data)}


class PublishingMetadataStore:
    """Create, edit, load, and validate publishing metadata."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.path = self.root / "projects" / slug / PUBLISHING_NAME

    def init(self, **fields) -> PublishingMetadata:
        data = dict(DEFAULT_METADATA)
        data.update({key: value for key, value in fields.items() if value is not None})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return PublishingMetadata(self.path, data)

    def edit(self, **fields) -> PublishingMetadata:
        data = self.load().data if self.path.exists() else dict(DEFAULT_METADATA)
        data.update({key: value for key, value in fields.items() if value is not None})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return PublishingMetadata(self.path, data)

    def load(self) -> PublishingMetadata:
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        data = dict(DEFAULT_METADATA)
        data.update(payload or {})
        return PublishingMetadata(self.path, data)

    def validate(self) -> dict[str, Any]:
        metadata = self.load().data
        errors = []
        for key in ("title", "author"):
            if not metadata.get(key):
                errors.append(f"{key} missing")
        if metadata.get("keywords") is not None and not isinstance(metadata.get("keywords"), list):
            errors.append("keywords must be a list")
        if metadata.get("platform_profiles") is not None and not isinstance(metadata.get("platform_profiles"), dict):
            errors.append("platform_profiles must be a mapping")
        return {"status": "ok" if not errors else "invalid", "errors": errors, "path": str(self.path)}


__all__ = ["PUBLISHING_NAME", "PublishingMetadata", "PublishingMetadataStore"]
