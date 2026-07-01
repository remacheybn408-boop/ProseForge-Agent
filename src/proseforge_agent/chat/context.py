"""Persistent active chat/project context."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ActiveContext:
    """Current default project/session selection."""

    project: str | None = None
    session: str | None = None
    pinned_sessions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class ActiveContextStore:
    """YAML-backed active context state under the agent workspace."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root / "active_context.yaml"

    def current(self) -> ActiveContext:
        if not self.path.exists():
            return ActiveContext()
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        data = payload.get("active_context") or {}
        return ActiveContext(
            project=data.get("project"),
            session=data.get("session"),
            pinned_sessions=list(data.get("pinned_sessions") or []),
        )

    def switch(self, *, project: str | None = None, session: str | None = None) -> ActiveContext:
        current = self.current()
        updated = ActiveContext(
            project=project if project is not None else current.project,
            session=session if session is not None else current.session,
            pinned_sessions=list(current.pinned_sessions),
        )
        self._write(updated)
        return updated

    def pin(self, *, session: str) -> ActiveContext:
        current = self.current()
        pinned = list(current.pinned_sessions)
        if session not in pinned:
            pinned.append(session)
        updated = ActiveContext(project=current.project, session=current.session, pinned_sessions=pinned)
        self._write(updated)
        return updated

    def _write(self, context: ActiveContext) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"active_context": context.to_dict()}
        self.path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=True), encoding="utf-8")


__all__ = ["ActiveContext", "ActiveContextStore"]
