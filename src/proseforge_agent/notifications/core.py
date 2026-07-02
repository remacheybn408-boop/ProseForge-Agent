"""Notification event center and dispatcher."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True)
class NotificationEvent:
    """One user-visible notification event."""

    event_type: str
    title: str
    message: str
    severity: str = "info"
    payload: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"note_{uuid4().hex[:12]}")
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class NotificationChannel(Protocol):
    """A delivery channel for notifications."""

    name: str

    def send(self, event: NotificationEvent) -> dict:
        """Send one event and return a structured channel result."""


@dataclass(frozen=True)
class NotificationDispatchResult:
    """Result of dispatching a notification."""

    event_id: str
    channel_results: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class NotificationDispatcher:
    """Append-only notification center plus optional channel fanout."""

    def __init__(self, root: str | Path, *, channels: list[NotificationChannel] | None = None) -> None:
        self.root = Path(root)
        self.channels = list(channels or [])
        self.events_path = self.root / "notifications" / "events.jsonl"

    def dispatch(self, event: NotificationEvent) -> NotificationDispatchResult:
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        channel_results = []
        for channel in self.channels:
            try:
                channel_results.append(channel.send(event))
            except Exception as exc:  # noqa: BLE001 - one channel must not block fanout.
                channel_results.append({"channel": channel.name, "status": "failed", "error": str(exc)})
        return NotificationDispatchResult(event_id=event.id, channel_results=channel_results)

    def list_events(self) -> list[NotificationEvent]:
        if not self.events_path.exists():
            return []
        events = []
        for line in self.events_path.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                events.append(_event_from_dict(json.loads(line)))
        return events


def _event_from_dict(payload: dict) -> NotificationEvent:
    return NotificationEvent(
        event_type=str(payload["event_type"]),
        title=str(payload.get("title", "")),
        message=str(payload.get("message", "")),
        severity=str(payload.get("severity", "info")),
        payload=dict(payload.get("payload") or {}),
        id=str(payload.get("id", f"note_{uuid4().hex[:12]}")),
        created_at=str(payload.get("created_at", "")),
    )


__all__ = [
    "NotificationChannel",
    "NotificationDispatchResult",
    "NotificationDispatcher",
    "NotificationEvent",
]
