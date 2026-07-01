"""Local skill usage analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class SkillUsageRecord:
    """One redacted skill usage record."""

    skill_id: str
    version: str
    trigger: str
    outcome: str
    duration_ms: int
    private_input: str = ""
    errors: list[str] = field(default_factory=list)
    trace_refs: list[str] = field(default_factory=list)
    redaction_applied: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "trigger": self.trigger,
            "outcome": self.outcome,
            "duration_ms": self.duration_ms,
            "private_input": self.private_input,
            "errors": self.errors,
            "trace_refs": self.trace_refs,
            "redaction_applied": self.redaction_applied,
        }


class SkillUsageStore:
    """Append-only local JSONL usage store."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "usage.jsonl"

    def record(
        self,
        skill_id: str,
        version: str,
        trigger: str,
        outcome: str,
        duration_ms: int,
        private_input: str = "",
        errors: list[str] | None = None,
        trace_refs: list[str] | None = None,
    ) -> SkillUsageRecord:
        safe_input, redacted = _redact(private_input)
        record = SkillUsageRecord(
            skill_id=skill_id,
            version=version,
            trigger=trigger,
            outcome=outcome,
            duration_ms=duration_ms,
            private_input=safe_input,
            errors=list(errors or []),
            trace_refs=list(trace_refs or []),
            redaction_applied=redacted,
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
        return record

    def list(self, skill_id: str | None = None) -> list[SkillUsageRecord]:
        if not self.path.exists():
            return []
        records = [_from_dict(json.loads(line)) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if skill_id is None:
            return records
        return [record for record in records if record.skill_id == skill_id]

    def summary(self, skill_id: str | None = None) -> dict[str, Any]:
        records = self.list(skill_id)
        return {
            "skill_id": skill_id,
            "total": len(records),
            "failures": sum(1 for record in records if record.outcome == "failure"),
            "average_duration_ms": int(sum(record.duration_ms for record in records) / len(records)) if records else 0,
        }


def _redact(text: str) -> tuple[str, bool]:
    pattern = re.compile(r"(?i)(token|secret|api_key|password)=\S+")
    return pattern.sub(r"\1=[redacted]", text), bool(pattern.search(text))


def _from_dict(payload: dict[str, Any]) -> SkillUsageRecord:
    return SkillUsageRecord(
        skill_id=str(payload["skill_id"]),
        version=str(payload["version"]),
        trigger=str(payload["trigger"]),
        outcome=str(payload["outcome"]),
        duration_ms=int(payload["duration_ms"]),
        private_input=str(payload.get("private_input", "")),
        errors=[str(item) for item in payload.get("errors", [])],
        trace_refs=[str(item) for item in payload.get("trace_refs", [])],
        redaction_applied=bool(payload.get("redaction_applied", False)),
    )


__all__ = ["SkillUsageRecord", "SkillUsageStore"]
