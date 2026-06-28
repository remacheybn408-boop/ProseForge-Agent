"""Upgrade migrations with backup and rollback."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from ..errors import ConfigurationError


@dataclass(frozen=True)
class MigrationResult:
    """Outcome of a migration attempt."""

    backup_path: Path
    migrated_files: list[str]
    from_version: str
    to_version: str
    warnings: list[str] = field(default_factory=list)
    rollback_steps: list[str] = field(default_factory=list)
    status: str = "migrated"


class MigrationRunner:
    """Run versioned workspace migrations after creating a backup."""

    def __init__(self, root: str | Path, *, fail_after_backup: bool = False) -> None:
        self.root = Path(root)
        self.fail_after_backup = fail_after_backup

    def run(self, from_version: str, to_version: str) -> MigrationResult:
        if from_version == to_version:
            return MigrationResult(
                backup_path=self.root / "backups" / f"noop-{from_version}",
                migrated_files=[],
                from_version=from_version,
                to_version=to_version,
                status="noop",
            )
        if (from_version, to_version) != ("1", "2"):
            raise ConfigurationError(f"unsupported migration {from_version} -> {to_version}")

        backup_path = self.root / "backups" / f"backup-{from_version}-to-{to_version}"
        self._backup_to(backup_path)
        try:
            if self.fail_after_backup:
                raise RuntimeError("forced migration failure")
            version_file = self.root / "schema-version.txt"
            version_file.write_text(to_version, encoding="utf-8")
            return MigrationResult(
                backup_path=backup_path,
                migrated_files=[str(version_file.relative_to(self.root)).replace("\\", "/")],
                from_version=from_version,
                to_version=to_version,
            )
        except Exception as exc:  # noqa: BLE001 - restore then report rollback
            self._restore_from(backup_path)
            return MigrationResult(
                backup_path=backup_path,
                migrated_files=[],
                from_version=from_version,
                to_version=to_version,
                warnings=[str(exc)],
                rollback_steps=["restore backup", "leave original workspace in place"],
                status="rolled_back",
            )

    def _backup_to(self, backup_path: Path) -> None:
        if backup_path.exists():
            shutil.rmtree(backup_path)
        backup_path.mkdir(parents=True, exist_ok=True)
        for child in self.root.iterdir():
            if child.name == "backups":
                continue
            target = backup_path / child.name
            if child.is_dir():
                shutil.copytree(child, target)
            else:
                shutil.copy2(child, target)

    def _restore_from(self, backup_path: Path) -> None:
        for child in list(self.root.iterdir()):
            if child.name == "backups":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        for child in backup_path.iterdir():
            target = self.root / child.name
            if child.is_dir():
                shutil.copytree(child, target)
            else:
                shutil.copy2(child, target)


__all__ = ["MigrationResult", "MigrationRunner"]
