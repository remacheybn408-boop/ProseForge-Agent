"""Plugin manifest parsing and validation."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from ..errors import ConfigurationError

_REQUIRED_FIELDS = ("id", "name", "version", "description", "entrypoint")
_PLUGIN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


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
        plugin_id = validate_plugin_id(str(plugin["id"]))
        return cls(
            id=plugin_id,
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


def validate_plugin_id(plugin_id: str) -> str:
    """Return a path-safe plugin id or raise a configuration error."""
    value = str(plugin_id).strip()
    if (
        not value
        or not _PLUGIN_ID_RE.fullmatch(value)
        or ".." in value
        or "/" in value
        or "\\" in value
        or ":" in value
    ):
        raise ConfigurationError(f"unsafe plugin id: {plugin_id}")
    return value


__all__ = ["PluginManifest", "validate_plugin_id"]
