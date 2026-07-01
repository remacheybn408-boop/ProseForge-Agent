"""Skill install/update dry-run planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..agent.permissions import PERMISSION_LEVELS
from .hub import FakeSkillHubClient, SkillHubPackage


_ORDER = {name: index for index, name in enumerate(PERMISSION_LEVELS)}


@dataclass(frozen=True)
class SkillInstallPlan:
    """Reviewable install/update/remove plan for a skill package."""

    skill_id: str
    version: str
    status: str
    source: str
    checksum: str
    requested_permissions: list[str]
    files: list[str]
    rollback_plan: dict[str, Any]
    reason: str = ""
    dry_run: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "status": self.status,
            "source": self.source,
            "checksum": self.checksum,
            "requested_permissions": self.requested_permissions,
            "files": self.files,
            "rollback_plan": self.rollback_plan,
            "reason": self.reason,
            "dry_run": self.dry_run,
        }


class SkillInstaller:
    """Build install and sync plans without executing skill code."""

    def __init__(self, root: str | Path, hub: FakeSkillHubClient | None = None) -> None:
        self.root = Path(root)
        self.hub = hub or FakeSkillHubClient()

    def install(
        self,
        skill_id: str,
        *,
        dry_run: bool = True,
        permission_ceiling: str = "read_only",
        source: str | None = None,
    ) -> SkillInstallPlan:
        package = self.hub.get(skill_id)
        status, reason = _permission_status(package, permission_ceiling)
        plan = self._plan(package, status=status, reason=reason, dry_run=dry_run, source=source or package.source)
        if dry_run or status != "planned":
            return plan
        target = self.root / package.skill_id
        target.mkdir(parents=True, exist_ok=True)
        for name, content in package.files.items():
            (target / name).write_text(content, encoding="utf-8")
        return self._plan(package, status="installed", reason="", dry_run=False, source=source or package.source)

    def update_all(self, *, dry_run: bool = True, use_offline_cache: bool = False) -> list[SkillInstallPlan]:
        source = "offline-cache" if use_offline_cache else "fake-hub"
        return [
            self.install(package.skill_id, dry_run=dry_run, source=source)
            for package in self.hub.list()
        ]

    def _plan(
        self,
        package: SkillHubPackage,
        *,
        status: str,
        reason: str,
        dry_run: bool,
        source: str,
    ) -> SkillInstallPlan:
        return SkillInstallPlan(
            skill_id=package.skill_id,
            version=package.version,
            status=status,
            source=source,
            checksum=package.checksum,
            requested_permissions=list(package.permissions),
            files=sorted(package.files),
            rollback_plan={"action": "remove", "target": package.skill_id},
            reason=reason,
            dry_run=dry_run,
        )


def _permission_status(package: SkillHubPackage, ceiling: str) -> tuple[str, str]:
    ceiling_rank = _ORDER.get(ceiling, -1)
    for permission in package.permissions:
        if _ORDER.get(permission, 999) > ceiling_rank:
            return "blocked", f"{package.skill_id} requires {permission}, ceiling is {ceiling}"
    return "planned", ""


__all__ = ["SkillInstallPlan", "SkillInstaller"]
