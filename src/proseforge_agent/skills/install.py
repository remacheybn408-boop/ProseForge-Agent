"""Skill install/update dry-run planning."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..agent.permissions import PERMISSION_LEVELS
from ..errors import ConfigurationError
from .hub import FakeSkillHubClient, SkillHubPackage


_ORDER = {name: index for index, name in enumerate(PERMISSION_LEVELS)}
_SAFE_SKILL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


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
        _safe_skill_id(skill_id)
        package = self.hub.get(skill_id)
        safe_id = _safe_skill_id(package.skill_id)
        status, reason = _permission_status(package, permission_ceiling)
        plan = self._plan(package, status=status, reason=reason, dry_run=dry_run, source=source or package.source)
        if dry_run or status != "planned":
            return plan
        target = self._target_for(safe_id)
        target.mkdir(parents=True, exist_ok=True)
        for name, content in package.files.items():
            file_path = _contained_file(target, name)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return self._plan(package, status="installed", reason="", dry_run=False, source=source or package.source)

    def update_all(self, *, dry_run: bool = True, use_offline_cache: bool = False) -> list[SkillInstallPlan]:
        source = "offline-cache" if use_offline_cache else "fake-hub"
        return [
            self.install(package.skill_id, dry_run=dry_run, source=source)
            for package in self.hub.list()
        ]

    def _target_for(self, skill_id: str) -> Path:
        safe_id = _safe_skill_id(skill_id)
        root = self.root.resolve()
        target = (self.root / safe_id).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ConfigurationError(f"unsafe skill id: {skill_id}") from exc
        return target

    def _plan(
        self,
        package: SkillHubPackage,
        *,
        status: str,
        reason: str,
        dry_run: bool,
        source: str,
    ) -> SkillInstallPlan:
        safe_id = _safe_skill_id(package.skill_id)
        target = self._target_for(safe_id)
        for name in package.files:
            _contained_file(target, name)
        return SkillInstallPlan(
            skill_id=safe_id,
            version=package.version,
            status=status,
            source=source,
            checksum=package.checksum,
            requested_permissions=list(package.permissions),
            files=sorted(package.files),
            rollback_plan={"action": "remove", "target": safe_id},
            reason=reason,
            dry_run=dry_run,
        )


def _permission_status(package: SkillHubPackage, ceiling: str) -> tuple[str, str]:
    ceiling_rank = _ORDER.get(ceiling, -1)
    for permission in package.permissions:
        if _ORDER.get(permission, 999) > ceiling_rank:
            return "blocked", f"{package.skill_id} requires {permission}, ceiling is {ceiling}"
    return "planned", ""


def _safe_skill_id(skill_id: str) -> str:
    value = str(skill_id).strip()
    if (
        not value
        or not _SAFE_SKILL_ID_RE.fullmatch(value)
        or ".." in value
        or "/" in value
        or "\\" in value
        or ":" in value
    ):
        raise ConfigurationError(f"unsafe skill id: {skill_id}")
    return value


def _contained_file(root: Path, name: str) -> Path:
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ConfigurationError(f"unsafe skill file: {name}")
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ConfigurationError(f"unsafe skill file: {name}") from exc
    return target


__all__ = ["SkillInstallPlan", "SkillInstaller"]
