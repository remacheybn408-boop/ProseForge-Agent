"""Fake skill hub client for install and sync planning."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any


@dataclass(frozen=True)
class SkillHubPackage:
    """Package metadata returned by a skill hub."""

    skill_id: str
    name: str
    version: str
    description: str
    permissions: list[str]
    files: dict[str, str]
    source: str = "fake-hub"

    @property
    def checksum(self) -> str:
        digest = hashlib.sha256()
        for name in sorted(self.files):
            digest.update(name.encode("utf-8"))
            digest.update(self.files[name].encode("utf-8"))
        return f"sha256:{digest.hexdigest()}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "permissions": self.permissions,
            "files": sorted(self.files),
            "source": self.source,
            "checksum": self.checksum,
        }


class FakeSkillHubClient:
    """Deterministic local hub with no network side effects."""

    def __init__(self) -> None:
        self._packages = {
            "demo-skill": SkillHubPackage(
                skill_id="demo-skill",
                name="demo-skill",
                version="1.0.0",
                description="Demo local skill package.",
                permissions=["read_only"],
                files={"SKILL.md": _skill_markdown("demo-skill", "read_only")},
            ),
            "writer-skill": SkillHubPackage(
                skill_id="writer-skill",
                name="writer-skill",
                version="1.0.0",
                description="Writer helper skill package.",
                permissions=["draft_write"],
                files={"SKILL.md": _skill_markdown("writer-skill", "draft_write")},
            ),
        }

    def search(self, query: str) -> list[SkillHubPackage]:
        needle = query.lower()
        return [
            package
            for package in sorted(self._packages.values(), key=lambda item: item.skill_id)
            if needle in package.skill_id.lower() or needle in package.description.lower()
        ]

    def get(self, skill_id: str) -> SkillHubPackage:
        if skill_id not in self._packages:
            raise KeyError(f"unknown skill package: {skill_id}")
        return self._packages[skill_id]

    def list(self) -> list[SkillHubPackage]:
        return [self._packages[name] for name in sorted(self._packages)]


def _skill_markdown(name: str, permission: str) -> str:
    return f"""---
name: {name}
description: Demo skill package.
triggers:
  - demo
version: 1.0.0
permissions:
  - {permission}
files:
  - SKILL.md
provenance:
  source: fake-hub
---

# {name}
"""


__all__ = ["FakeSkillHubClient", "SkillHubPackage"]
