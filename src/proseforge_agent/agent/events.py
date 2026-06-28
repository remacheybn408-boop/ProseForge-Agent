"""Append-only agent event bus and background jobs."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


_SENSITIVE_KEY_PARTS = ("api_key", "token", "secret", "password", "authorization")


@dataclass(frozen=True)
class EventRecord:
    """One append-only event bus record."""

    event_type: str
    payload: dict[str, Any]
    created_at: str
    trace_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventBus:
    """Append-only JSONL event bus with payload redaction."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def emit(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        *,
        trace_id: str | None = None,
    ) -> EventRecord:
        record = EventRecord(
            event_type=event_type,
            payload=_redact(payload or {}),
            created_at=datetime.now(UTC).isoformat(),
            trace_id=trace_id or f"trace-{uuid4().hex[:12]}",
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return record


@dataclass(frozen=True)
class JobResult:
    """Outcome of a background job attempt."""

    job_name: str
    status: str
    allowed: bool
    provider: str = ""
    dry_run: bool = False
    data: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BackgroundJobRunner:
    """Run a small allow-list of background maintenance jobs."""

    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        allowed_jobs: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] | None = None,
    ) -> None:
        self._event_bus = event_bus
        self._allowed_jobs = allowed_jobs or {"memory-index": _memory_index_job}

    def run(self, job_name: str, *, provider: str = "fake", dry_run: bool = False) -> JobResult:
        handler = self._allowed_jobs.get(job_name)
        if handler is None:
            result = JobResult(
                job_name=job_name,
                status="denied",
                allowed=False,
                provider=provider,
                dry_run=dry_run,
                reason="job is not in the allow-list",
            )
            self._emit("background_job.denied", result)
            return result

        payload = {"job_name": job_name, "provider": provider, "dry_run": dry_run}
        if dry_run:
            result = JobResult(
                job_name=job_name,
                status="dry_run",
                allowed=True,
                provider=provider,
                dry_run=True,
                data=payload,
            )
            self._emit("background_job.dry_run", result)
            return result

        data = handler(payload)
        result = JobResult(
            job_name=job_name,
            status="ok",
            allowed=True,
            provider=provider,
            dry_run=False,
            data=data,
        )
        self._emit("background_job.completed", result)
        return result

    def _emit(self, event_type: str, result: JobResult) -> None:
        if self._event_bus is not None:
            self._event_bus.emit(event_type, result.to_dict())


def _memory_index_job(payload: dict[str, Any]) -> dict[str, Any]:
    return {"indexed": 0, "provider": payload.get("provider", "fake")}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _SENSITIVE_KEY_PARTS):
                redacted[key] = "[redacted]"
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


__all__ = ["BackgroundJobRunner", "EventBus", "EventRecord", "JobResult"]
