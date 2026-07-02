"""Local plugin install/update/remove manager."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from ..errors import ConfigurationError
from .manifest import PluginManifest, validate_plugin_id


@dataclass(frozen=True)
class PluginActionResult:
    """Result of a plugin management action."""

    plugin_id: str
    status: str
    path: str = ""
    backup_path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class PluginManager:
    """Manage local plugin installations under an agent root."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.plugins_dir = self.root / "plugins"
        self.state_path = self.plugins_dir / "plugins.json"

    def install(self, source: str | Path) -> PluginActionResult:
        manifest = PluginManifest.load(Path(source) / "plugin.yaml")
        target = self._target_for(manifest.id)
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
        self._set_enabled(manifest.id, True)
        return PluginActionResult(plugin_id=manifest.id, status="installed", path=str(target))

    def update(self, source: str | Path) -> PluginActionResult:
        manifest = PluginManifest.load(Path(source) / "plugin.yaml")
        target = self._target_for(manifest.id)
        backup_path = ""
        if target.exists():
            backup_root = self.plugins_dir / ".backups"
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / f"{manifest.id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
            shutil.copytree(target, backup)
            shutil.rmtree(target)
            backup_path = str(backup)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
        self._set_enabled(manifest.id, True)
        return PluginActionResult(plugin_id=manifest.id, status="updated", path=str(target), backup_path=backup_path)

    def enable(self, plugin_id: str) -> PluginActionResult:
        self._require_installed(plugin_id)
        safe_id = validate_plugin_id(plugin_id)
        self._set_enabled(safe_id, True)
        return PluginActionResult(plugin_id=safe_id, status="enabled", path=str(self._target_for(safe_id)))

    def disable(self, plugin_id: str) -> PluginActionResult:
        self._require_installed(plugin_id)
        safe_id = validate_plugin_id(plugin_id)
        self._set_enabled(safe_id, False)
        return PluginActionResult(plugin_id=safe_id, status="disabled", path=str(self._target_for(safe_id)))

    def remove(self, plugin_id: str) -> PluginActionResult:
        safe_id = validate_plugin_id(plugin_id)
        target = self._require_installed(safe_id)
        shutil.rmtree(target)
        state = self._state()
        state.pop(safe_id, None)
        self._write_state(state)
        return PluginActionResult(plugin_id=safe_id, status="removed")

    def _require_installed(self, plugin_id: str) -> Path:
        safe_id = validate_plugin_id(plugin_id)
        target = self._target_for(safe_id)
        if not (target / "plugin.yaml").exists():
            raise ConfigurationError(f"plugin not installed: {safe_id}")
        return target

    def _set_enabled(self, plugin_id: str, enabled: bool) -> None:
        plugin_id = validate_plugin_id(plugin_id)
        state = self._state()
        state[plugin_id] = {"enabled": enabled}
        self._write_state(state)

    def _target_for(self, plugin_id: str) -> Path:
        safe_id = validate_plugin_id(plugin_id)
        base = self.plugins_dir.resolve()
        target = (self.plugins_dir / safe_id).resolve()
        try:
            target.relative_to(base)
        except ValueError as exc:
            raise ConfigurationError(f"unsafe plugin id: {plugin_id}") from exc
        return target

    def _state(self) -> dict:
        if not self.state_path.exists():
            return {}
        return json.loads(self.state_path.read_text(encoding="utf-8-sig"))

    def _write_state(self, state: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = ["PluginActionResult", "PluginManager"]
