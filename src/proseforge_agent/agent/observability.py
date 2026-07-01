"""Observer hooks and telemetry export (Task 181).

Observer hooks are read-only. They report what happened with correlation ids
and sanitized payloads. They must not mutate requests, tool arguments, or
runtime behavior. Observer callback failures are fail-open: the failure is
recorded on the registry and the next observer is still invoked.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .events import _redact


OBSERVER_SCHEMA_VERSION = 1

FAMILY_SESSION = "session"
FAMILY_TURN = "turn"
FAMILY_PROVIDER_REQUEST = "provider_request"
FAMILY_TOOL_CALL = "tool_call"
FAMILY_APPROVAL = "approval"
FAMILY_SUBAGENT = "subagent"
FAMILY_JOB = "job"

_FAMILIES = frozenset(
    {
        FAMILY_SESSION,
        FAMILY_TURN,
        FAMILY_PROVIDER_REQUEST,
        FAMILY_TOOL_CALL,
        FAMILY_APPROVAL,
        FAMILY_SUBAGENT,
        FAMILY_JOB,
    }
)


@dataclass(frozen=True)
class ObserverEvent:
    """One observer event with correlation ids and a sanitized payload."""

    family: str
    name: str
    session_id: str
    turn_id: str
    task_id: str
    correlation_id: str
    timestamp: str
    status: str
    payload: dict[str, Any] = field(default_factory=dict)
    schema_version: int = OBSERVER_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ObserverCallback = Callable[[ObserverEvent], None]


class ObserverRegistry:
    """Fan-out observer callbacks with fail-open error handling."""

    def __init__(self) -> None:
        self._callbacks: list[ObserverCallback] = []
        self._failures: list[dict[str, str]] = []

    def register(self, callback: ObserverCallback) -> None:
        self._callbacks.append(callback)

    def failures(self) -> list[dict[str, str]]:
        return list(self._failures)

    def emit(self, event: ObserverEvent) -> ObserverEvent:
        if event.family not in _FAMILIES:
            raise ValueError(f"unknown observer family {event.family!r}")
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as exc:
                self._failures.append(
                    {"callback": getattr(callback, "__name__", repr(callback)), "error": str(exc)}
                )
        return event

    def _build(
        self,
        *,
        family: str,
        name: str,
        session_id: str,
        turn_id: str = "",
        task_id: str = "",
        correlation_id: str | None = None,
        status: str = "ok",
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> ObserverEvent:
        return ObserverEvent(
            family=family,
            name=name,
            session_id=session_id,
            turn_id=turn_id,
            task_id=task_id,
            correlation_id=correlation_id or f"{session_id}:{turn_id}:{name}",
            timestamp=timestamp or datetime.now(UTC).isoformat(),
            status=status,
            payload=_redact(payload or {}),
        )

    def emit_session_started(
        self,
        *,
        session_id: str,
        task_id: str = "",
        correlation_id: str | None = None,
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> ObserverEvent:
        return self.emit(
            self._build(
                family=FAMILY_SESSION,
                name="session.started",
                session_id=session_id,
                task_id=task_id,
                correlation_id=correlation_id,
                payload=payload,
                timestamp=timestamp,
            )
        )

    def emit_session_ended(
        self,
        *,
        session_id: str,
        task_id: str = "",
        correlation_id: str | None = None,
        status: str = "ok",
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> ObserverEvent:
        return self.emit(
            self._build(
                family=FAMILY_SESSION,
                name="session.ended",
                session_id=session_id,
                task_id=task_id,
                correlation_id=correlation_id,
                status=status,
                payload=payload,
                timestamp=timestamp,
            )
        )

    def emit_turn_started(
        self,
        *,
        session_id: str,
        turn_id: str,
        task_id: str = "",
        correlation_id: str | None = None,
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> ObserverEvent:
        return self.emit(
            self._build(
                family=FAMILY_TURN,
                name="turn.started",
                session_id=session_id,
                turn_id=turn_id,
                task_id=task_id,
                correlation_id=correlation_id,
                payload=payload,
                timestamp=timestamp,
            )
        )

    def emit_provider_request(
        self,
        *,
        name: str,
        session_id: str,
        turn_id: str = "",
        task_id: str = "",
        correlation_id: str | None = None,
        status: str = "ok",
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> ObserverEvent:
        return self.emit(
            self._build(
                family=FAMILY_PROVIDER_REQUEST,
                name=name,
                session_id=session_id,
                turn_id=turn_id,
                task_id=task_id,
                correlation_id=correlation_id,
                status=status,
                payload=payload,
                timestamp=timestamp,
            )
        )

    def emit_tool_call(
        self,
        *,
        name: str,
        session_id: str,
        turn_id: str = "",
        task_id: str = "",
        correlation_id: str | None = None,
        status: str = "ok",
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> ObserverEvent:
        return self.emit(
            self._build(
                family=FAMILY_TOOL_CALL,
                name=name,
                session_id=session_id,
                turn_id=turn_id,
                task_id=task_id,
                correlation_id=correlation_id,
                status=status,
                payload=payload,
                timestamp=timestamp,
            )
        )

    def emit_approval(
        self,
        *,
        session_id: str,
        turn_id: str = "",
        task_id: str = "",
        correlation_id: str | None = None,
        status: str = "granted",
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> ObserverEvent:
        return self.emit(
            self._build(
                family=FAMILY_APPROVAL,
                name="approval.decision",
                session_id=session_id,
                turn_id=turn_id,
                task_id=task_id,
                correlation_id=correlation_id,
                status=status,
                payload=payload,
                timestamp=timestamp,
            )
        )

    def emit_subagent(
        self,
        *,
        name: str,
        session_id: str,
        turn_id: str = "",
        task_id: str = "",
        correlation_id: str | None = None,
        status: str = "ok",
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> ObserverEvent:
        return self.emit(
            self._build(
                family=FAMILY_SUBAGENT,
                name=name,
                session_id=session_id,
                turn_id=turn_id,
                task_id=task_id,
                correlation_id=correlation_id,
                status=status,
                payload=payload,
                timestamp=timestamp,
            )
        )

    def emit_job(
        self,
        *,
        name: str,
        session_id: str,
        turn_id: str = "",
        task_id: str = "",
        correlation_id: str | None = None,
        status: str = "ok",
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> ObserverEvent:
        return self.emit(
            self._build(
                family=FAMILY_JOB,
                name=name,
                session_id=session_id,
                turn_id=turn_id,
                task_id=task_id,
                correlation_id=correlation_id,
                status=status,
                payload=payload,
                timestamp=timestamp,
            )
        )


class TelemetryStore:
    """Append-only JSONL telemetry with deterministic, filterable export."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def record(self, event: ObserverEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            events.append(json.loads(line))
        return events

    def export(
        self,
        out_path: str | Path,
        *,
        format: str = "jsonl",
        redact: bool = True,
        families: Iterable[str] | None = None,
        since: str | None = None,
    ) -> int:
        if format != "jsonl":
            raise ValueError(f"unsupported telemetry export format {format!r}")

        family_filter = set(families) if families else None
        events = self.read()
        filtered = []
        for event in events:
            if family_filter is not None and event.get("family") not in family_filter:
                continue
            if since is not None and str(event.get("timestamp", "")) < since:
                continue
            payload = _redact(event.get("payload", {})) if redact else event.get("payload", {})
            event = {**event, "payload": payload}
            filtered.append(event)

        filtered.sort(key=lambda item: (str(item.get("timestamp", "")), str(item.get("correlation_id", ""))))

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="\n") as handle:
            for event in filtered:
                handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
                handle.write("\n")
        return len(filtered)


__all__ = [
    "FAMILY_APPROVAL",
    "FAMILY_JOB",
    "FAMILY_PROVIDER_REQUEST",
    "FAMILY_SESSION",
    "FAMILY_SUBAGENT",
    "FAMILY_TOOL_CALL",
    "FAMILY_TURN",
    "OBSERVER_SCHEMA_VERSION",
    "ObserverCallback",
    "ObserverEvent",
    "ObserverRegistry",
    "TelemetryStore",
]
