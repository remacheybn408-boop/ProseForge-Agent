"""Skill revision candidates and provenance history."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from ..agent.permissions import PERMISSION_LEVELS


_ORDER = {name: index for index, name in enumerate(PERMISSION_LEVELS)}


@dataclass(frozen=True)
class SkillRevisionCandidate:
    """Reviewable patch proposal for a skill."""

    id: str
    skill_id: str
    base_version: str
    proposed_version: str
    diff: str
    evidence_refs: list[str]
    risk_flags: list[str]
    approval_state: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "skill_id": self.skill_id,
            "base_version": self.base_version,
            "proposed_version": self.proposed_version,
            "diff": self.diff,
            "evidence_refs": self.evidence_refs,
            "risk_flags": self.risk_flags,
            "approval_state": self.approval_state,
        }


class SkillRevisionStore:
    """JSON-backed revision proposal store."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "revision_candidates.json"

    def propose(
        self,
        skill_id: str,
        base_version: str,
        proposed_instructions: str,
        evidence_refs: list[str],
        *,
        requested_permissions: list[str] | None = None,
        base_permissions: list[str] | None = None,
    ) -> SkillRevisionCandidate:
        requested_permissions = requested_permissions or ["read_only"]
        base_permissions = base_permissions or ["read_only"]
        risk_flags = []
        if _max_permission(requested_permissions) > _max_permission(base_permissions):
            risk_flags.append("permission_escalation")
        candidate = SkillRevisionCandidate(
            id=_revision_id(skill_id, base_version, proposed_instructions),
            skill_id=skill_id,
            base_version=base_version,
            proposed_version=_bump_patch(base_version),
            diff=f"--- {skill_id}@{base_version}\n+++ {skill_id}@{_bump_patch(base_version)}\n+{proposed_instructions}",
            evidence_refs=list(dict.fromkeys(evidence_refs)),
            risk_flags=risk_flags,
            approval_state="blocked" if risk_flags else "pending",
        )
        self._save(candidate)
        return candidate

    def approve(self, candidate_id: str) -> SkillRevisionCandidate:
        candidate = self._require(candidate_id)
        approved = _replace(candidate, approval_state="approved")
        self._save(approved)
        return approved

    def reject(self, candidate_id: str) -> SkillRevisionCandidate:
        candidate = self._require(candidate_id)
        rejected = _replace(candidate, approval_state="rejected")
        self._save(rejected)
        return rejected

    def history(self, skill_id: str) -> list[SkillRevisionCandidate]:
        return [candidate for candidate in self.list() if candidate.skill_id == skill_id]

    def list(self) -> list[SkillRevisionCandidate]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [_from_dict(item) for item in payload.get("revisions", [])]

    def _require(self, candidate_id: str) -> SkillRevisionCandidate:
        for candidate in self.list():
            if candidate.id == candidate_id:
                return candidate
        raise KeyError(f"unknown revision candidate: {candidate_id}")

    def _save(self, candidate: SkillRevisionCandidate) -> None:
        records = {item.id: item for item in self.list()}
        records[candidate.id] = candidate
        self.path.write_text(
            json.dumps({"revisions": [item.to_dict() for item in sorted(records.values(), key=lambda value: value.id)]}, indent=2),
            encoding="utf-8",
        )


def _max_permission(permissions: list[str]) -> int:
    return max((_ORDER.get(permission, -1) for permission in permissions), default=-1)


def _bump_patch(version: str) -> str:
    major, minor, patch = (int(part) for part in version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def _revision_id(skill_id: str, base_version: str, instructions: str) -> str:
    digest = hashlib.sha256(f"{skill_id}\n{base_version}\n{instructions}".encode("utf-8")).hexdigest()[:12]
    return f"revision-{digest}"


def _from_dict(payload: dict[str, Any]) -> SkillRevisionCandidate:
    return SkillRevisionCandidate(
        id=str(payload["id"]),
        skill_id=str(payload["skill_id"]),
        base_version=str(payload["base_version"]),
        proposed_version=str(payload["proposed_version"]),
        diff=str(payload["diff"]),
        evidence_refs=[str(item) for item in payload.get("evidence_refs", [])],
        risk_flags=[str(item) for item in payload.get("risk_flags", [])],
        approval_state=str(payload.get("approval_state", "pending")),
    )


def _replace(candidate: SkillRevisionCandidate, **updates: Any) -> SkillRevisionCandidate:
    data = candidate.to_dict()
    data.update(updates)
    return _from_dict(data)


__all__ = ["SkillRevisionCandidate", "SkillRevisionStore"]
