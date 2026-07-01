"""Skill specification parsing and discovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

import yaml

from ..agent.permissions import PERMISSION_LEVELS


REQUIRED_FIELDS = ("name", "description", "triggers", "version", "permissions", "files", "provenance")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


class SkillValidationError(ValueError):
    """Raised when a local skill does not match the specification."""


@dataclass(frozen=True)
class SkillRecord:
    """Validated local skill specification."""

    name: str
    description: str
    triggers: tuple[str, ...]
    version: str
    permissions: tuple[str, ...]
    files: tuple[str, ...]
    provenance: dict[str, Any]
    path: Path
    enabled: bool = True
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "triggers": list(self.triggers),
            "version": self.version,
            "permissions": list(self.permissions),
            "files": list(self.files),
            "provenance": self.provenance,
            "path": str(self.path),
            "enabled": self.enabled,
            "warnings": list(self.warnings),
        }


class SkillRegistry:
    """Discover and validate local SKILL.md records."""

    @classmethod
    def discover(cls, paths: list[str | Path]) -> list[SkillRecord]:
        records: list[SkillRecord] = []
        seen: set[str] = set()
        for raw_path in paths:
            path = Path(raw_path)
            if not path.exists():
                continue
            if path.is_file() and path.name == "SKILL.md":
                skill_files = [path]
            elif path.is_dir() and (path / "SKILL.md").exists():
                skill_files = [path / "SKILL.md"]
            elif path.is_dir():
                skill_files = sorted(path.glob("*/SKILL.md"))
            else:
                skill_files = []
            for skill_file in skill_files:
                record = cls._parse(skill_file)
                if record.name in seen:
                    raise SkillValidationError(f"duplicate skill name: {record.name}")
                seen.add(record.name)
                records.append(record)
        return records

    @staticmethod
    def _parse(path: Path) -> SkillRecord:
        frontmatter = _frontmatter(path.read_text(encoding="utf-8"))
        missing = [field for field in REQUIRED_FIELDS if field not in frontmatter]
        if missing:
            raise SkillValidationError(f"{path}: missing required field(s): {', '.join(missing)}")

        name = str(frontmatter["name"])
        description = str(frontmatter["description"])
        triggers = tuple(str(item) for item in frontmatter.get("triggers") or [])
        version = str(frontmatter["version"])
        permissions = tuple(str(item) for item in frontmatter.get("permissions") or [])
        files = tuple(str(item) for item in frontmatter.get("files") or [])
        provenance = dict(frontmatter.get("provenance") or {})
        enabled = bool(frontmatter.get("enabled", True))

        if not triggers:
            raise SkillValidationError(f"{path}: triggers must not be empty")
        if not VERSION_RE.match(version):
            raise SkillValidationError(f"{path}: version must be semver-like")
        unknown_permissions = [permission for permission in permissions if permission not in PERMISSION_LEVELS]
        if unknown_permissions:
            raise SkillValidationError(f"{path}: unknown permission(s): {', '.join(unknown_permissions)}")
        root = path.parent.resolve()
        for item in files:
            candidate = (root / item).resolve()
            if candidate != root and root not in candidate.parents:
                raise SkillValidationError(f"{path}: file path escapes skill directory: {item}")

        return SkillRecord(
            name=name,
            description=description,
            triggers=triggers,
            version=version,
            permissions=permissions,
            files=files,
            provenance=provenance,
            path=path.parent,
            enabled=enabled,
        )


def _frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        raise SkillValidationError("SKILL.md must start with YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SkillValidationError("SKILL.md frontmatter is not closed")
    data = yaml.safe_load(parts[1]) or {}
    if not isinstance(data, dict):
        raise SkillValidationError("SKILL.md frontmatter must be a mapping")
    return data


__all__ = ["SkillRecord", "SkillRegistry", "SkillValidationError"]
