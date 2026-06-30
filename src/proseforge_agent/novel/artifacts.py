"""Artifact dependency graph for novel project outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


GRAPH_NAME = "artifacts.graph.yaml"


@dataclass(frozen=True)
class ArtifactRecord:
    """One artifact node and its generation metadata."""

    id: str
    type: str
    depends_on: list[str] = field(default_factory=list)
    generated: list[str] = field(default_factory=list)
    checksum: str = ""
    created_at: str = ""
    provider: str = ""
    prompt_version: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if not payload["created_at"]:
            payload["created_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ArtifactRecord":
        return cls(
            id=str(payload["id"]),
            type=str(payload["type"]),
            depends_on=list(payload.get("depends_on") or []),
            generated=list(payload.get("generated") or []),
            checksum=str(payload.get("checksum") or ""),
            created_at=str(payload.get("created_at") or ""),
            provider=str(payload.get("provider") or ""),
            prompt_version=str(payload.get("prompt_version") or ""),
        )


class ArtifactGraphStore:
    """Append-only artifact graph stored per novel project."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.path = self.root / "projects" / slug / GRAPH_NAME

    def add(self, record: ArtifactRecord) -> dict[str, Any]:
        records = self.list()
        if any(existing.id == record.id for existing in records):
            return {"status": "duplicate", "id": record.id}
        records.append(record)
        self._write(records)
        return {"status": "ok", "id": record.id}

    def list(self) -> list[ArtifactRecord]:
        if not self.path.exists():
            return []
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return [ArtifactRecord.from_dict(item) for item in payload.get("artifacts", [])]

    def trace(self, artifact_id: str) -> list[str]:
        records = {record.id: record for record in self.list()}
        if artifact_id not in records:
            return []
        seen: set[str] = set()
        ordered: list[str] = []

        def visit(node_id: str) -> None:
            if node_id in seen:
                return
            seen.add(node_id)
            record = records.get(node_id)
            if record is not None:
                for dependency in record.depends_on:
                    visit(dependency)
            ordered.append(node_id)

        visit(artifact_id)
        return ordered

    def edges(self) -> list[tuple[str, str]]:
        edges: list[tuple[str, str]] = []
        for record in self.list():
            for dependency in record.depends_on:
                edges.append((dependency, record.id))
            for generated in record.generated:
                edges.append((record.id, generated))
        return edges

    def _write(self, records: list[ArtifactRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"artifacts": [record.to_dict() for record in records]}
        self.path.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )


__all__ = ["GRAPH_NAME", "ArtifactGraphStore", "ArtifactRecord"]
