"""Backup verification: snapshot a project, checksum-verify it, and dry-run restore."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKUPS_DIR = "backups"
MANIFEST_NAME = "manifest.json"
DATA_DIR = "data"


@dataclass(frozen=True)
class Backup:
    """A created, checksum-verified backup snapshot."""

    id: str
    slug: str
    path: Path
    file_count: int
    status: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["path"] = str(self.path)
        return data


@dataclass(frozen=True)
class VerifyResult:
    """Outcome of verifying a backup against its manifest checksums."""

    backup_id: str
    status: str
    checked: int
    mismatches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RestoreResult:
    """Outcome of a (possibly dry-run) restore."""

    backup_id: str
    status: str
    restored: bool
    files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BackupManager:
    """Create, verify, and restore project backups, storing them outside the project tree."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.backups_root = self.root / BACKUPS_DIR / slug

    def create(self) -> Backup:
        backup_id = self._next_id()
        backup_path = self.backups_root / backup_id
        data_root = backup_path / DATA_DIR
        checksums: dict[str, str] = {}
        for source in sorted(self.project_root.rglob("*")) if self.project_root.exists() else []:
            if not source.is_file():
                continue
            rel = source.relative_to(self.project_root).as_posix()
            target = data_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            checksums[rel] = _checksum(target)
        manifest = {
            "id": backup_id,
            "slug": self.slug,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "checksums": checksums,
        }
        backup_path.mkdir(parents=True, exist_ok=True)
        (backup_path / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        verify = self.verify(backup_id)
        return Backup(
            id=backup_id,
            slug=self.slug,
            path=backup_path,
            file_count=len(checksums),
            status=verify.status,
            created_at=manifest["created_at"],
        )

    def verify(self, backup_id: str) -> VerifyResult:
        manifest = self._manifest(backup_id)
        data_root = self.backups_root / backup_id / DATA_DIR
        mismatches: list[str] = []
        for rel, expected in manifest["checksums"].items():
            path = data_root / rel
            if not path.exists() or _checksum(path) != expected:
                mismatches.append(rel)
        status = "verified" if not mismatches else "corrupted"
        return VerifyResult(backup_id=backup_id, status=status, checked=len(manifest["checksums"]), mismatches=mismatches)

    def restore(self, backup_id: str, *, dry_run: bool = True) -> RestoreResult:
        manifest = self._manifest(backup_id)
        data_root = self.backups_root / backup_id / DATA_DIR
        files = sorted(manifest["checksums"].keys())
        if dry_run:
            return RestoreResult(backup_id=backup_id, status="dry_run", restored=False, files=files)
        for rel in files:
            target = self.project_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(data_root / rel, target)
        return RestoreResult(backup_id=backup_id, status="restored", restored=True, files=files)

    def list(self) -> list[Backup]:
        backups: list[Backup] = []
        if not self.backups_root.exists():
            return backups
        for path in sorted(self.backups_root.iterdir()):
            manifest_path = path / MANIFEST_NAME
            if not manifest_path.exists():
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            backups.append(
                Backup(
                    id=manifest["id"],
                    slug=self.slug,
                    path=path,
                    file_count=len(manifest["checksums"]),
                    status="present",
                    created_at=manifest.get("created_at", ""),
                )
            )
        return backups

    # -- reserved interfaces (scheduled / remote backup) -----------------

    def schedule(self, interval: str) -> dict[str, Any]:
        """Reserved interface for scheduled backups; records the requested cadence."""
        config = {"slug": self.slug, "interval": interval, "enabled": True}
        path = self.backups_root / "schedule.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        return config

    def remote_target(self, uri: str | None = None) -> dict[str, Any]:
        """Reserved interface for optional remote backup targets."""
        return {"slug": self.slug, "remote": uri or "", "configured": bool(uri)}

    # -- internals -------------------------------------------------------

    def _manifest(self, backup_id: str) -> dict[str, Any]:
        manifest_path = self.backups_root / backup_id / MANIFEST_NAME
        if not manifest_path.exists():
            raise ValueError(f"backup {backup_id!r} not found")
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def _next_id(self) -> str:
        existing = [path.name for path in self.backups_root.glob("backup_*")] if self.backups_root.exists() else []
        numbers = [int(name.rsplit("_", 1)[1]) for name in existing if name.rsplit("_", 1)[1].isdigit()]
        return f"backup_{(max(numbers) + 1) if numbers else 1:03d}"


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = ["BACKUPS_DIR", "Backup", "BackupManager", "RestoreResult", "VerifyResult"]
