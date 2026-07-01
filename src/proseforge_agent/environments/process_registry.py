"""Long-running process registry for terminal lifecycle operations."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ProcessEntry:
    process_id: str
    command_summary: str
    environment_id: str
    status: str
    created_at: str
    updated_at: str
    output_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProcessReadResult:
    process_id: str
    output: str
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FakeProcessBackend:
    """Fake process backend for deterministic lifecycle tests."""

    def __init__(self, *, output: str | None = None) -> None:
        self.output = output

    def start(self, command: list[str] | str) -> str:
        return self.output if self.output is not None else (" ".join(command) if isinstance(command, list) else str(command))


class ProcessRegistry:
    """Persist and manage typed process lifecycle records."""

    def __init__(self, *, root: str | Path, backend: FakeProcessBackend | None = None, output_limit: int = 4096) -> None:
        self.root = Path(root)
        self.backend = backend or FakeProcessBackend()
        self.output_limit = max(0, output_limit)
        self.process_dir = self.root / "processes"

    def start(self, *, command: list[str] | str, environment_id: str) -> ProcessEntry:
        process_id = f"proc-{uuid4().hex[:12]}"
        now = _now()
        summary = " ".join(command) if isinstance(command, list) else str(command)
        output = self.backend.start(command)
        entry = ProcessEntry(
            process_id=process_id,
            command_summary=summary,
            environment_id=environment_id,
            status="running",
            created_at=now,
            updated_at=now,
            output_ref=f"processes/{process_id}.out",
        )
        self._write_entry(entry)
        self._output_path(process_id).write_text(output, encoding="utf-8")
        return entry

    def read(self, process_id: str) -> ProcessReadResult:
        output = self._output_path(process_id).read_text(encoding="utf-8")
        redacted = _redact_output(output)
        truncated = len(redacted) > self.output_limit
        return ProcessReadResult(process_id=process_id, output=redacted[: self.output_limit], truncated=truncated)

    def interrupt(self, process_id: str) -> ProcessEntry:
        return self._set_status(process_id, "interrupted")

    def close(self, process_id: str) -> ProcessEntry:
        return self._set_status(process_id, "closed")

    def cleanup_stale(self) -> list[ProcessEntry]:
        return []

    def list(self) -> list[ProcessEntry]:
        if not self.process_dir.exists():
            return []
        entries = [self._entry_from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in self.process_dir.glob("*.json")]
        return sorted(entries, key=lambda item: item.created_at)

    def _set_status(self, process_id: str, status: str) -> ProcessEntry:
        entry = self._load_entry(process_id)
        updated = ProcessEntry(
            process_id=entry.process_id,
            command_summary=entry.command_summary,
            environment_id=entry.environment_id,
            status=status,
            created_at=entry.created_at,
            updated_at=_now(),
            output_ref=entry.output_ref,
        )
        self._write_entry(updated)
        return updated

    def _load_entry(self, process_id: str) -> ProcessEntry:
        return self._entry_from_dict(json.loads((self.process_dir / f"{process_id}.json").read_text(encoding="utf-8")))

    def _write_entry(self, entry: ProcessEntry) -> None:
        self.process_dir.mkdir(parents=True, exist_ok=True)
        (self.process_dir / f"{entry.process_id}.json").write_text(
            json.dumps(entry.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _output_path(self, process_id: str) -> Path:
        self.process_dir.mkdir(parents=True, exist_ok=True)
        return self.process_dir / f"{process_id}.out"

    @staticmethod
    def _entry_from_dict(payload: dict[str, Any]) -> ProcessEntry:
        return ProcessEntry(
            process_id=str(payload["process_id"]),
            command_summary=str(payload["command_summary"]),
            environment_id=str(payload["environment_id"]),
            status=str(payload["status"]),
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
            output_ref=str(payload.get("output_ref", "")),
        )


def _redact_output(text: str) -> str:
    return re.sub(
        r"(?i)\b(token|secret|password|api_key)=([^\s]+)",
        lambda match: f"{match.group(1)}=[redacted]",
        text,
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


__all__ = ["FakeProcessBackend", "ProcessEntry", "ProcessReadResult", "ProcessRegistry"]
