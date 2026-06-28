"""Chat memory preference candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .transcript import append_jsonl


@dataclass(frozen=True)
class MemoryCandidate:
    """A proposed preference awaiting review before becoming durable memory."""

    id: str
    text: str
    scope: str
    kind: str = "preference"
    status: str = "candidate"
    project_slug: str | None = None
    reason: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ChatMemoryExtractor:
    """Extract durable preference candidates from chat turns."""

    def extract(self, text: str, *, project_slug: str | None = None) -> list[MemoryCandidate]:
        if not self._looks_like_preference(text):
            return []
        scope = self._scope(text, project_slug)
        return [
            MemoryCandidate(
                id=f"memcand_{uuid4().hex[:12]}",
                text=text,
                scope=scope,
                project_slug=project_slug if scope == "project" else None,
                reason="user stated a durable preference",
                created_at=datetime.now(UTC).isoformat(),
            )
        ]

    def write_candidates(
        self,
        root: Path | str,
        text: str,
        *,
        project_slug: str | None = None,
    ) -> list[MemoryCandidate]:
        candidates = self.extract(text, project_slug=project_slug)
        root_path = Path(root)
        for candidate in candidates:
            append_jsonl(self._queue_path(root_path, candidate), candidate.to_dict())
        return candidates

    @staticmethod
    def _looks_like_preference(text: str) -> bool:
        normalized = text.lower()
        return any(token in normalized for token in ("remember", "prefer", "default")) or any(
            token in text for token in ("以后", "默认", "偏好")
        )

    @staticmethod
    def _scope(text: str, project_slug: str | None) -> str:
        if project_slug and ("这个项目" in text or "本项目" in text or "project" in text.lower()):
            return "project"
        return "global"

    @staticmethod
    def _queue_path(root: Path, candidate: MemoryCandidate) -> Path:
        base = root / "memory_candidates"
        if candidate.scope == "project" and candidate.project_slug:
            return base / "projects" / f"{candidate.project_slug}.jsonl"
        return base / "global.jsonl"


def render_memory_candidates(candidates: list[MemoryCandidate]) -> list[str]:
    """Render candidate queues for terminal reports."""
    if not candidates:
        return ["(none)"]
    lines = []
    for candidate in candidates:
        project = f":{candidate.project_slug}" if candidate.project_slug else ""
        lines.append(f"{candidate.scope}{project} -> {candidate.status} {candidate.id}: {candidate.text}")
    return lines


__all__ = ["ChatMemoryExtractor", "MemoryCandidate", "render_memory_candidates"]
