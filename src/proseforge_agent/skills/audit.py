"""Privacy-preserving skill safety audit checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SkillAuditFinding:
    """One local audit finding for a skill."""

    code: str
    skill_id: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "skill_id": self.skill_id,
            "severity": self.severity,
            "message": self.message,
        }


class SkillSafetyAuditor:
    """Run deterministic local safety checks against skill metadata."""

    def audit(self, skills: list[dict[str, Any]]) -> list[SkillAuditFinding]:
        findings: list[SkillAuditFinding] = []
        for skill in skills:
            name = str(skill.get("name") or skill.get("id") or "unknown")
            version = str(skill.get("version") or "0.0.0")
            instructions = str(skill.get("instructions") or "")
            if not bool(skill.get("enabled", True)):
                findings.append(SkillAuditFinding("disabled_skill", name, "info", "skill is disabled"))
            if "ignore previous instructions" in instructions.lower():
                findings.append(SkillAuditFinding("unsafe_instruction", name, "high", "skill contains unsafe instruction text"))
            if version.startswith("0."):
                findings.append(SkillAuditFinding("stale_version", name, "medium", "skill version is pre-1.0"))
        return findings


__all__ = ["SkillAuditFinding", "SkillSafetyAuditor"]
