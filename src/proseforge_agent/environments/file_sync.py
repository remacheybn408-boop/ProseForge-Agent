"""Scoped remote file sync plans."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


_SECRET_NAMES = {".env", "secrets.yaml", "secrets.yml", "credentials.json"}


@dataclass(frozen=True)
class FileSyncPlan:
    root: str
    destination: str
    dry_run: bool
    includes: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)
    redactions: list[str] = field(default_factory=list)
    operations: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FileSyncPlanner:
    """Build deterministic, scoped file sync plans."""

    def __init__(self, *, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def plan(self, *, includes: list[str], destination: str, dry_run: bool = True) -> FileSyncPlan:
        accepted: list[str] = []
        excludes: list[str] = []
        redactions: list[str] = []
        operations: list[dict[str, str]] = []
        for item in includes:
            candidate = (self.root / item).resolve()
            if candidate != self.root and self.root not in candidate.parents:
                redactions.append(item)
                continue
            if Path(item).name in _SECRET_NAMES or "secret" in item.lower():
                excludes.append(item)
                continue
            relative = candidate.relative_to(self.root).as_posix()
            accepted.append(relative)
            operations.append({"action": "upload", "source": relative, "destination": f"{destination.rstrip('/')}/{relative}"})
        return FileSyncPlan(
            root=str(self.root),
            destination=destination,
            dry_run=dry_run,
            includes=accepted,
            excludes=excludes,
            redactions=redactions,
            operations=operations,
        )


__all__ = ["FileSyncPlan", "FileSyncPlanner"]
