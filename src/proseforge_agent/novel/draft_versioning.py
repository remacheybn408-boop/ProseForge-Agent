"""Draft version control: per-chapter versions, diff, branches, and approval-gated rollback."""

from __future__ import annotations

import difflib
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSIONS_DIR = "versions"
REGISTRY_NAME = "registry.json"


@dataclass(frozen=True)
class DraftVersion:
    """One immutable draft version of a chapter."""

    id: str
    chapter: str
    checksum: str
    provider: str
    prompt: str
    branch: str
    parent: str
    path: Path

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["path"] = str(self.path)
        return data


@dataclass(frozen=True)
class DiffResult:
    """Unified diff between two versions."""

    version_a: str
    version_b: str
    changed: bool
    diff: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RollbackResult:
    """Outcome of an approval-gated rollback."""

    chapter: str
    to: str
    status: str
    approved: bool
    checksum: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Branch:
    """A named branch forked from an existing version."""

    name: str
    chapter: str
    base_version: str
    head_version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DraftVersionStore:
    """Track chapter draft versions so the agent can never lose recoverable work."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.versions_root = self.project_root / VERSIONS_DIR
        self.registry_path = self.versions_root / REGISTRY_NAME

    def commit(
        self,
        chapter: str,
        text: str,
        *,
        provider: str | None = None,
        prompt: str | None = None,
        branch: str = "main",
    ) -> DraftVersion:
        registry = self._load()
        registry["counter"] += 1
        version_id = f"draft_v{registry['counter']}"
        checksum = _checksum(text)
        rel = f"{chapter}/{version_id}.md"
        path = self.versions_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        parent = self._branch_head(registry, chapter, branch)
        registry["versions"][version_id] = {
            "chapter": chapter,
            "checksum": checksum,
            "provider": provider or "",
            "prompt": prompt or "",
            "branch": branch,
            "parent": parent,
            "path": rel,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        registry["branches"][f"{chapter}:{branch}"] = {"head": version_id, "base": parent}
        self._save(registry)
        return self._version(version_id, registry["versions"][version_id])

    def list_versions(self, chapter: str) -> list[DraftVersion]:
        registry = self._load()
        entries = [
            (version_id, entry)
            for version_id, entry in registry["versions"].items()
            if entry["chapter"] == chapter
        ]
        entries.sort(key=lambda item: _version_number(item[0]))
        return [self._version(version_id, entry) for version_id, entry in entries]

    def diff(self, version_a: str, version_b: str) -> DiffResult:
        registry = self._load()
        text_a = self._read_version(registry, version_a)
        text_b = self._read_version(registry, version_b)
        diff_lines = difflib.unified_diff(
            text_a.splitlines(),
            text_b.splitlines(),
            fromfile=version_a,
            tofile=version_b,
            lineterm="",
        )
        diff_text = "\n".join(diff_lines)
        return DiffResult(version_a=version_a, version_b=version_b, changed=text_a != text_b, diff=diff_text)

    def rollback(self, chapter: str, *, to: str, approve: bool = False) -> RollbackResult:
        registry = self._load()
        entry = registry["versions"].get(to)
        if entry is None or entry["chapter"] != chapter:
            raise ValueError(f"version {to!r} not found for chapter {chapter!r}")
        if not approve:
            return RollbackResult(chapter=chapter, to=to, status="pending_approval", approved=False, checksum=entry["checksum"])
        text = self._read_version(registry, to)
        chapter_path = self.project_root / "chapters" / f"{chapter}.md"
        chapter_path.parent.mkdir(parents=True, exist_ok=True)
        chapter_path.write_text(text, encoding="utf-8")
        return RollbackResult(chapter=chapter, to=to, status="rolled_back", approved=True, checksum=entry["checksum"])

    def branch(self, chapter: str, *, name: str, from_version: str | None = None) -> Branch:
        registry = self._load()
        base_id = from_version or self._branch_head(registry, chapter, "main")
        if not base_id:
            raise ValueError(f"chapter {chapter!r} has no version to branch from")
        if base_id not in registry["versions"]:
            raise ValueError(f"version {base_id!r} not found")
        base_text = self._read_version(registry, base_id)
        head = self.commit(chapter, base_text, provider="branch", prompt=f"branch:{name}", branch=name)
        return Branch(name=name, chapter=chapter, base_version=base_id, head_version=head.id)

    # -- internals -------------------------------------------------------

    def _load(self) -> dict[str, Any]:
        if self.registry_path.exists():
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        return {"counter": 0, "versions": {}, "branches": {}}

    def _save(self, registry: dict[str, Any]) -> None:
        self.versions_root.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")

    def _branch_head(self, registry: dict[str, Any], chapter: str, branch: str) -> str:
        return registry["branches"].get(f"{chapter}:{branch}", {}).get("head", "")

    def _read_version(self, registry: dict[str, Any], version_id: str) -> str:
        entry = registry["versions"].get(version_id)
        if entry is None:
            raise ValueError(f"version {version_id!r} not found")
        return (self.versions_root / entry["path"]).read_text(encoding="utf-8")

    def _version(self, version_id: str, entry: dict[str, Any]) -> DraftVersion:
        return DraftVersion(
            id=version_id,
            chapter=entry["chapter"],
            checksum=entry["checksum"],
            provider=entry["provider"],
            prompt=entry["prompt"],
            branch=entry["branch"],
            parent=entry["parent"],
            path=self.versions_root / entry["path"],
        )


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _version_number(version_id: str) -> int:
    try:
        return int(version_id.rsplit("_v", 1)[1])
    except (IndexError, ValueError):
        return 0


__all__ = [
    "VERSIONS_DIR",
    "REGISTRY_NAME",
    "Branch",
    "DiffResult",
    "DraftVersion",
    "DraftVersionStore",
    "RollbackResult",
]
