"""Relationship graph storage and exports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


RELATIONSHIP_GRAPH_NAME = "relationships.yaml"
RELATION_TYPES = {
    "friend",
    "enemy",
    "family",
    "lover",
    "rival",
    "mentor",
    "faction_member",
    "hidden_relation",
}


@dataclass(frozen=True)
class RelationshipEdge:
    """One typed relation between characters, factions, or organizations."""

    source: str
    target: str
    type: str
    evidence: list[str] = field(default_factory=list)
    status: str = "active"
    note: str = ""

    @property
    def id(self) -> str:
        return f"{self.source}->{self.target}:{self.type}"

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, **asdict(self)}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RelationshipEdge":
        return cls(
            source=str(payload.get("source") or ""),
            target=str(payload.get("target") or ""),
            type=str(payload.get("type") or ""),
            evidence=[str(item) for item in payload.get("evidence", [])],
            status=str(payload.get("status") or "active"),
            note=str(payload.get("note") or ""),
        )


class RelationshipGraph:
    """Manage relationship edges and graph exports."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.path = self.project_root / RELATIONSHIP_GRAPH_NAME

    def add_relation(
        self,
        *,
        source: str,
        target: str,
        type: str,
        evidence: list[str] | None = None,
        status: str = "active",
        note: str = "",
    ) -> RelationshipEdge:
        if type not in RELATION_TYPES:
            raise ValueError(f"unknown relation type {type!r}")
        edge = RelationshipEdge(
            source=source,
            target=target,
            type=type,
            evidence=list(evidence or []),
            status=status,
            note=note,
        )
        edges = [item for item in self._edges() if item.id != edge.id]
        edges.append(edge)
        self._write(edges)
        return edge

    def list(self) -> list[RelationshipEdge]:
        return sorted(self._edges(), key=lambda item: (item.source, item.target, item.type))

    def graph(self, *, format: str = "json") -> dict[str, Any] | str:
        edges = self.list()
        nodes = sorted({edge.source for edge in edges} | {edge.target for edge in edges})
        payload = {"nodes": nodes, "edges": [edge.to_dict() for edge in edges]}
        if format == "json":
            return payload
        if format == "markdown":
            lines = ["# Relationship Graph", "", "## Relations"]
            lines.extend(f"- {edge.source} -> {edge.target}: {edge.type}" for edge in edges)
            return "\n".join(lines) + "\n"
        if format == "dot":
            lines = ["digraph relationships {"]
            lines.extend(f'  "{edge.source}" -> "{edge.target}" [label="{edge.type}"];' for edge in edges)
            lines.append("}")
            return "\n".join(lines) + "\n"
        raise ValueError(f"unknown graph format {format!r}")

    def evidence(self, query: str = "") -> list[dict[str, Any]]:
        needle = query.lower()
        results: list[dict[str, Any]] = []
        for edge in self.list():
            text = f"{edge.source} is {edge.type} with {edge.target}"
            haystack = f"{text} {' '.join(edge.evidence)} {edge.note}".lower()
            if not needle or needle in haystack:
                results.append(
                    {
                        "id": edge.id,
                        "type": "relationship",
                        "text": text,
                        "relation": edge.to_dict(),
                    }
                )
        return results

    def _edges(self) -> list[RelationshipEdge]:
        if not self.path.exists():
            return []
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return [RelationshipEdge.from_dict(item) for item in payload.get("relations", [])]

    def _write(self, edges: list[RelationshipEdge]) -> None:
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(
                {"relations": [edge.to_dict() for edge in edges]},
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )


__all__ = ["RELATIONSHIP_GRAPH_NAME", "RELATION_TYPES", "RelationshipEdge", "RelationshipGraph"]
