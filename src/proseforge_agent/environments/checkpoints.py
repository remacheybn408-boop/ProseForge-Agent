"""Execution environment checkpoints."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EnvironmentCheckpoint:
    checkpoint_id: str
    backend_id: str
    project_refs: list[str]
    artifact_refs: list[str]
    created_at: str
    restore_plan: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        backend_id: str,
        project_refs: list[str],
        artifact_refs: list[str],
        root: str | Path,
    ) -> "EnvironmentCheckpoint":
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        return cls(
            checkpoint_id=f"checkpoint-{backend_id}-{timestamp}",
            backend_id=backend_id,
            project_refs=list(project_refs),
            artifact_refs=list(artifact_refs),
            created_at=datetime.now(UTC).isoformat(),
            restore_plan=["restore checkpoint metadata", "sync artifact refs", f"resume backend {backend_id}"],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = ["EnvironmentCheckpoint"]
