"""Non-destructive setup repair and backup helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


WORKSPACE_DIRS: tuple[str, ...] = (
    "projects",
    "drafts",
    "exports",
    "logs",
    "cache",
    "tmp",
    "backups",
)


def ensure_workspace(workspace_path: str | Path) -> list[Path]:
    root = Path(workspace_path)
    root.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for name in WORKSPACE_DIRS:
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory)
    return created


def backup_config(config_path: str | Path) -> Path | None:
    path = Path(config_path)
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{stamp}")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup


__all__ = ["WORKSPACE_DIRS", "backup_config", "ensure_workspace"]
