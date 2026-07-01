"""Plugin discovery from local directories and registry indexes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from ..errors import ConfigurationError
from .manifest import PluginManifest


@dataclass(frozen=True)
class DiscoveredPlugin:
    """A discovered plugin entry."""

    id: str
    name: str
    version: str
    source: str
    path: str = ""
    manifest: PluginManifest | None = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        if self.manifest is not None:
            payload["manifest"] = self.manifest.to_dict()
        return payload


class PluginDiscovery:
    """Discover installed and registry-listed plugins."""

    def __init__(self, *, local_dirs: list[str | Path] | None = None, registry_index: str | Path | None = None) -> None:
        self.local_dirs = [Path(path) for path in (local_dirs or [])]
        self.registry_index = Path(registry_index) if registry_index is not None else None

    def discover(self) -> list[DiscoveredPlugin]:
        plugins: list[DiscoveredPlugin] = []
        plugins.extend(self._discover_local())
        plugins.extend(self._discover_registry())
        return sorted(_dedupe(plugins), key=lambda item: item.id)

    def info(self, plugin_id: str) -> DiscoveredPlugin:
        for plugin in self.discover():
            if plugin.id == plugin_id:
                return plugin
        raise ConfigurationError(f"plugin not found: {plugin_id}")

    def _discover_local(self) -> list[DiscoveredPlugin]:
        found: list[DiscoveredPlugin] = []
        for root in self.local_dirs:
            if not root.exists():
                continue
            for manifest_path in sorted(root.glob("*/plugin.yaml")):
                manifest = PluginManifest.load(manifest_path)
                found.append(
                    DiscoveredPlugin(
                        id=manifest.id,
                        name=manifest.name,
                        version=manifest.version,
                        source="local",
                        path=str(manifest_path.parent),
                        manifest=manifest,
                    )
                )
        return found

    def _discover_registry(self) -> list[DiscoveredPlugin]:
        if self.registry_index is None or not self.registry_index.exists():
            return []
        payload = json.loads(self.registry_index.read_text(encoding="utf-8-sig"))
        return [
            DiscoveredPlugin(
                id=str(item["id"]),
                name=str(item.get("name", item["id"])),
                version=str(item.get("version", "")),
                source="registry",
            )
            for item in payload.get("plugins", [])
        ]


def _dedupe(plugins: list[DiscoveredPlugin]) -> list[DiscoveredPlugin]:
    by_id: dict[str, DiscoveredPlugin] = {}
    for plugin in plugins:
        by_id.setdefault(plugin.id, plugin)
    return list(by_id.values())


__all__ = ["DiscoveredPlugin", "PluginDiscovery"]
