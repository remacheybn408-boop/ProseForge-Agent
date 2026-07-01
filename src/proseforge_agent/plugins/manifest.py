"""Plugin manifest parsing and validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from ..errors import ConfigurationError

_REQUIRED_FIELDS = ("id", "name", "version", "description", "entrypoint")


@dataclass(frozen=True)
class PluginManifest:
    """Parsed ProseForge Agent plugin manifest."""

    id: str
    name: str
    version: str
    description: str
    entrypoint: str
    permissions: list[str] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    compatible: dict[str, str] = field(default_factory=dict)
    path: str = ""

    @classmethod
    def load(cls, path: str | Path) -> "PluginManifest":
        manifest_path = Path(path)
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        plugin = payload.get("plugin") or {}
        missing = [field for field in _REQUIRED_FIELDS if not plugin.get(field)]
        if missing:
            raise ConfigurationError(f"missing required plugin field: {', '.join(missing)}")
        dependencies = plugin.get("dependencies") or {}
        return cls(
            id=str(plugin["id"]),
            name=str(plugin["name"]),
            version=str(plugin["version"]),
            description=str(plugin["description"]),
            entrypoint=str(plugin["entrypoint"]),
            permissions=[str(item) for item in plugin.get("permissions") or []],
            dependencies={str(key): [str(item) for item in value or []] for key, value in dependencies.items()},
            compatible={str(key): str(value) for key, value in (plugin.get("compatible") or {}).items()},
            path=str(manifest_path),
        )

    def to_dict(self) -> dict:
        return asdict(self)


__all__ = ["PluginManifest"]
