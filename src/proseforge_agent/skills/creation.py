"""Autonomous skill candidate creation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .install import SkillInstallPlan


@dataclass(frozen=True)
class SkillCandidate:
    """Reviewable skill candidate proposed from trace evidence."""

    id: str
    trigger: str
    purpose: str
    instructions: str
    source_trace_ids: list[str]
    redaction_status: str = "clean"
    approval_state: str = "pending"
    enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "trigger": self.trigger,
            "purpose": self.purpose,
            "instructions": self.instructions,
            "source_trace_ids": self.source_trace_ids,
            "redaction_status": self.redaction_status,
            "approval_state": self.approval_state,
            "enabled": self.enabled,
        }


class SkillCandidateStore:
    """JSON-backed store for proposed skills."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "candidates.json"

    def propose_from_trace(
        self,
        trigger: str,
        purpose: str,
        instructions: str,
        source_trace_ids: list[str],
    ) -> SkillCandidate:
        candidate_id = _candidate_id(trigger, purpose)
        safe_instructions, redacted = _redact(instructions)
        existing = self.get(candidate_id)
        if existing is not None:
            traces = sorted(set(existing.source_trace_ids) | set(source_trace_ids))
            candidate = SkillCandidate(
                id=existing.id,
                trigger=existing.trigger,
                purpose=existing.purpose,
                instructions=existing.instructions,
                source_trace_ids=traces,
                redaction_status=existing.redaction_status,
                approval_state=existing.approval_state,
                enabled=existing.enabled,
            )
        else:
            candidate = SkillCandidate(
                id=candidate_id,
                trigger=trigger,
                purpose=purpose,
                instructions=safe_instructions,
                source_trace_ids=list(source_trace_ids),
                redaction_status="redacted" if redacted else "clean",
            )
        self._save(candidate)
        return candidate

    def approve(self, candidate_id: str, *, dry_run: bool = True) -> SkillInstallPlan:
        candidate = self._require(candidate_id)
        plan = SkillInstallPlan(
            skill_id=candidate.id,
            version="0.1.0",
            status="planned" if dry_run else "approved",
            source="candidate",
            checksum=f"sha256:{hashlib.sha256(candidate.instructions.encode('utf-8')).hexdigest()}",
            requested_permissions=["read_only"],
            files=["SKILL.md"],
            rollback_plan={"action": "disable", "target": candidate.id},
            dry_run=dry_run,
        )
        if not dry_run:
            self._save(_replace_candidate(candidate, approval_state="approved", enabled=False))
        return plan

    def reject(self, candidate_id: str) -> SkillCandidate:
        candidate = self._require(candidate_id)
        rejected = _replace_candidate(candidate, approval_state="rejected", enabled=False)
        self._save(rejected)
        return rejected

    def get(self, candidate_id: str) -> SkillCandidate | None:
        return {candidate.id: candidate for candidate in self.list()}.get(candidate_id)

    def list(self) -> list[SkillCandidate]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [_candidate_from_dict(item) for item in payload.get("candidates", [])]

    def _require(self, candidate_id: str) -> SkillCandidate:
        candidate = self.get(candidate_id)
        if candidate is None:
            raise KeyError(f"unknown skill candidate: {candidate_id}")
        return candidate

    def _save(self, candidate: SkillCandidate) -> None:
        records = {item.id: item for item in self.list()}
        records[candidate.id] = candidate
        self.path.write_text(
            json.dumps({"candidates": [item.to_dict() for item in sorted(records.values(), key=lambda value: value.id)]}, indent=2),
            encoding="utf-8",
        )


def _candidate_id(trigger: str, purpose: str) -> str:
    digest = hashlib.sha256(f"{trigger}\n{purpose}".encode("utf-8")).hexdigest()[:12]
    return f"candidate-{digest}"


def _redact(text: str) -> tuple[str, bool]:
    pattern = re.compile(r"(?i)(token|secret|api_key|password)=\S+")
    return pattern.sub(r"\1=[redacted]", text), bool(pattern.search(text))


def _candidate_from_dict(payload: dict[str, Any]) -> SkillCandidate:
    return SkillCandidate(
        id=str(payload["id"]),
        trigger=str(payload["trigger"]),
        purpose=str(payload["purpose"]),
        instructions=str(payload["instructions"]),
        source_trace_ids=[str(item) for item in payload.get("source_trace_ids", [])],
        redaction_status=str(payload.get("redaction_status", "clean")),
        approval_state=str(payload.get("approval_state", "pending")),
        enabled=bool(payload.get("enabled", False)),
    )


def _replace_candidate(candidate: SkillCandidate, **updates: Any) -> SkillCandidate:
    data = candidate.to_dict()
    data.update(updates)
    return _candidate_from_dict(data)


__all__ = ["SkillCandidate", "SkillCandidateStore"]
